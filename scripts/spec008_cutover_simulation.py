"""Simula cutover e rollback apenas em uma raiz explicitamente não operacional."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from backend.cutover.infrastructure import (
    AclPolicy,
    OperationalPointer,
    acquire_maintenance_lock,
    atomic_swap_pointer,
    create_final_backup,
    directory_acl_fingerprint,
    freeze_runtime,
    initialize_pointer,
    promote_candidate,
    read_pointer,
    rollback_pointer,
    sha256_file,
)


RUNTIME_FILES = (
    "backend/config.py", "backend/main.py", "backend/supervisor.py",
    "backend/database/session.py", "backend/cutover/infrastructure.py",
    "backend/cutover/__init__.py", "backend/services/appointment_service.py",
    "backend/repositories/appointment_repository.py", "app/utils/cutover_guard.py",
    "main.py", "scripts/run_api.ps1", "scripts/run_all.ps1", "requirements.txt",
)


def _pointer(database: Path, runtime_checksum: str, generation: int, state: str,
             previous: str | None = None) -> OperationalPointer:
    return OperationalPointer(
        generation, state, str(database.resolve()), sha256_file(database),
        "backend-models-v2-credential-reset", runtime_checksum, previous,
    )


def _sqlite_verify(path: Path) -> dict:
    connection = sqlite3.connect("file:" + path.resolve().as_posix() + "?mode=ro&immutable=1", uri=True)
    try:
        return {
            "integrity_check": connection.execute("PRAGMA integrity_check").fetchone()[0],
            "foreign_key_violations": sum(1 for _ in connection.execute("PRAGMA foreign_key_check")),
            "table_count": connection.execute(
                "SELECT COUNT(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchone()[0],
        }
    finally:
        connection.close()


def _start_health_smoke(root: Path, pointer_path: Path, lock_path: Path) -> dict:
    names = (
        "CLINICA_OPERATIONAL_POINTER", "CLINICA_MAINTENANCE_LOCK",
        "BACKEND_VERIFY_READ_ONLY", "BACKEND_RELOAD", "AUTH_SECRET",
        "BACKEND_DATABASE_PATH", "BACKEND_DATA_DIR",
    )
    previous = {name: os.environ.get(name) for name in names}
    database = Path(read_pointer(pointer_path).database_path).resolve()
    resolved_root = root.resolve()
    if database != resolved_root and resolved_root not in database.parents:
        raise RuntimeError("smoke recusou banco fora da raiz isolada")
    try:
        os.environ["CLINICA_OPERATIONAL_POINTER"] = str(pointer_path)
        os.environ["CLINICA_MAINTENANCE_LOCK"] = str(lock_path)
        os.environ["BACKEND_VERIFY_READ_ONLY"] = "true"
        os.environ["BACKEND_RELOAD"] = "false"
        os.environ["AUTH_SECRET"] = "spec008-simulation-secret-only-0001"
        os.environ.pop("BACKEND_DATABASE_PATH", None)
        os.environ.pop("BACKEND_DATA_DIR", None)
        import backend.main as backend_main

        before = sha256_file(database)
        with TestClient(backend_main.create_app()) as client:
            health = client.get("/health")
            write_probe = client.post("/patients", json={})
        return {
            "start": "PASS", "health": "PASS" if health.status_code == 200 else "FAIL",
            "smoke_read_only": "PASS" if write_probe.status_code == 503 else "FAIL",
            "database_unchanged": before == sha256_file(database),
            **_sqlite_verify(database),
        }
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def run(repository: Path, candidate: Path, root: Path, evidence: Path) -> dict:
    repository = repository.resolve(strict=True)
    candidate = candidate.resolve(strict=True)
    root = root.resolve(strict=False)
    if root.exists():
        raise RuntimeError("raiz de simulacao deve ser nova")
    root.mkdir(parents=True)
    if repository == root or root in repository.parents:
        raise RuntimeError("raiz de simulacao invalida")

    manifests = root / "runtime-manifests"
    runtime_manifest, runtime_checksum = freeze_runtime(
        repository, RUNTIME_FILES, manifests
    )
    candidate_copy = root / "candidate-copy.db"
    legacy_desktop = root / "legacy-desktop-copy.db"
    legacy_backend = root / "legacy-backend-copy.db"
    shutil.copyfile(candidate, candidate_copy)
    shutil.copyfile(candidate, legacy_desktop)
    shutil.copyfile(candidate, legacy_backend)
    expected = sha256_file(candidate)
    if sha256_file(candidate_copy) != expected:
        raise RuntimeError("rehydration checksum mismatch")

    runtime_dir = root / "runtime"
    canonical_dir = root / "canonical"
    canonical_dir.mkdir()
    pointer_path = runtime_dir / "operational-pointer.json"
    old = _pointer(legacy_backend, runtime_checksum, 1, "legacy")
    initialize_pointer(pointer_path, old)
    lock = acquire_maintenance_lock(
        runtime_dir / "maintenance.lock", "spec008-simulation-nominal",
        databases=(legacy_desktop, legacy_backend),
    )
    try:
        backup_manifest = create_final_backup(
            {"desktop_legacy": legacy_desktop, "backend_legacy": legacy_backend},
            root / "final-backup", execution_reference="spec008-simulation-nominal", lock=lock,
        )
        revalidate = _sqlite_verify(candidate_copy)
        promoted = promote_candidate(
            candidate_copy, canonical_dir, "verified-v2", expected_checksum=expected,
            acl_policy=AclPolicy(directory_acl_fingerprint(canonical_dir)), lock=lock,
        )
        canonical_pointer = _pointer(promoted, runtime_checksum, 2, "canonical", old.checksum)
        atomic_swap_pointer(pointer_path, canonical_pointer,
                            expected_current_checksum=old.checksum, lock=lock,
                            history_dir=runtime_dir / "history")
        nominal_runtime = _start_health_smoke(root, pointer_path, lock.path)
        if not all((nominal_runtime["health"] == "PASS",
                    nominal_runtime["smoke_read_only"] == "PASS",
                    nominal_runtime["database_unchanged"],
                    nominal_runtime["integrity_check"] == "ok",
                    nominal_runtime["foreign_key_violations"] == 0)):
            raise RuntimeError("nominal verification failed: " + json.dumps(
                nominal_runtime, sort_keys=True
            ))
        nominal = {
            "sequence": ["QUIESCE", "FINAL_BACKUP", "REVALIDATE", "PROMOTE", "START",
                         "HEALTH", "SMOKE", "VERIFY", "ACCEPT"],
            "gate": "PASS", "backup_manifest_checksum_sha256": sha256_file(backup_manifest),
            "runtime": nominal_runtime, "revalidate": revalidate,
        }
    finally:
        lock.release()

    # Segunda execução independente com falha injetada antes de writes.
    failure_root = root / "failure-path"
    failure_runtime = failure_root / "runtime"
    failure_canonical = failure_root / "canonical"
    failure_canonical.mkdir(parents=True)
    failure_legacy = failure_root / "legacy-copy.db"
    failure_candidate = failure_root / "candidate-copy.db"
    (failure_root / "runtime-manifests").mkdir(parents=True)
    shutil.copyfile(runtime_manifest, failure_root / "runtime-manifests" / runtime_manifest.name)
    shutil.copyfile(candidate, failure_legacy)
    shutil.copyfile(candidate, failure_candidate)
    failure_pointer_path = failure_runtime / "operational-pointer.json"
    failure_old = _pointer(failure_legacy, runtime_checksum, 1, "legacy")
    initialize_pointer(failure_pointer_path, failure_old)
    failure_lock = acquire_maintenance_lock(
        failure_runtime / "maintenance.lock", "spec008-simulation-failure",
        databases=(failure_legacy,),
    )
    try:
        failure_backup_manifest = create_final_backup(
            {"legacy": failure_legacy}, failure_root / "final-backup",
            execution_reference="spec008-simulation-failure", lock=failure_lock,
        )
        failure_promoted = promote_candidate(
            failure_candidate, failure_canonical, "verified-v2", expected_checksum=expected,
            acl_policy=AclPolicy(directory_acl_fingerprint(failure_canonical)), lock=failure_lock,
        )
        failure_new = _pointer(failure_promoted, runtime_checksum, 2, "canonical", failure_old.checksum)
        current_checksum = atomic_swap_pointer(
            failure_pointer_path, failure_new, expected_current_checksum=failure_old.checksum,
            lock=failure_lock, history_dir=failure_runtime / "history",
        )
        injected_failure = "START_FAILURE_BEFORE_WRITES"
        rollback_pointer(
            failure_pointer_path, failure_old.checksum,
            expected_current_checksum=current_checksum, lock=failure_lock,
            history_dir=failure_runtime / "history",
        )
        restored = failure_root / "restored-legacy.db"
        shutil.copyfile(failure_root / "final-backup" / "legacy.backup.db", restored)
        rolled_back = read_pointer(failure_pointer_path)
        rollback_runtime = _start_health_smoke(failure_root, failure_pointer_path, failure_lock.path)
        failure = {
            "sequence": ["FAIL", "QUIESCE", "ROLLBACK", "RESTORE", "START", "HEALTH", "VERIFY"],
            "gate": "PASS", "injected_failure": injected_failure,
            "pointer_state": rolled_back.state,
            "restored": _sqlite_verify(restored), "runtime": rollback_runtime,
            "backup_manifest_checksum_sha256": sha256_file(failure_backup_manifest),
        }
        if rolled_back.state != "legacy" or rollback_runtime["health"] != "PASS":
            raise RuntimeError("rollback verification failed")
    finally:
        failure_lock.release()

    result = {
        "format_version": "1.0", "scope": "fixtures-only-no-cutover",
        "candidate_checksum_sha256": expected,
        "runtime_manifest_reference": runtime_manifest.name,
        "runtime_manifest_checksum_sha256": runtime_checksum,
        "nominal": nominal, "failure": failure,
        "privacy_safe": True, "cutover_executed": False,
    }
    data = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(data)
    return {"gate": "PASS", "evidence_checksum_sha256": hashlib.sha256(data).hexdigest(),
            "runtime_manifest_checksum_sha256": runtime_checksum, "cutover": "NOT_EXECUTED"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--simulation-root", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.repository, args.candidate, args.simulation_root, args.evidence), sort_keys=True))


if __name__ == "__main__":
    main()
