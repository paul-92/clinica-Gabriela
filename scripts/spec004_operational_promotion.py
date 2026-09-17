"""Operational freeze, promotion and stabilization for SPEC-004.

The executor is intentionally bound to the approved Generation 5 predecessor and
candidate database. It never mutates an earlier generation and never rolls the
pointer back after a successful compare-and-swap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.cutover.infrastructure import (
    AclPolicy,
    OperationalPointer,
    SCHEMA_VERSION,
    _atomic_create,
    _sqlite_validate,
    acquire_maintenance_lock,
    atomic_swap_pointer,
    create_final_backup,
    directory_acl_fingerprint,
    promote_candidate,
    read_pointer,
    sha256_file,
    verify_runtime_manifest,
)
from backend.migration.spec004 import migrate_spec004


IMPLEMENTATION_PARENT = "19983dc5ec940b65d552bb57eb0f85ee0e9aadba"
APPROVED_CANDIDATE_MANIFEST = "a88ef64c4baf589cd13448669ef80a910a0bcd769e630395e0914ef94ae7d511"
PREDECESSOR_POINTER = "723a28330bce6ebd1821737675651c905f2c5a358cf96db4e8218a908fea65d7"
PREDECESSOR_DATABASE = "143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506"
PREDECESSOR_RUNTIME_MANIFEST = "e7951f3876c03303f3bbfb00354ffcc896bb3e16530d80fb4448f002188171d1"
CANDIDATE_DATABASE = "7f4412c6fefccbccce5fa511e35a21bd88eec97447ffbe4787fc2c2101939a07"
GENERATIONS_ACL = "5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91"
DATABASE_SCHEMA_VERSION = "backend-models-v4-spec004-agenda"


def _canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _git(repository: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=repository, capture_output=True,
                               text=True, check=True)
    return completed.stdout.strip()


def _runtime_files(repository: Path) -> list[str]:
    selected = []
    for relative in _git(repository, "ls-files").splitlines():
        normalized = relative.replace("\\", "/")
        if (
            normalized == "main.py"
            or normalized == "requirements.txt"
            or (normalized.startswith("backend/") and normalized.endswith(".py"))
            or (normalized.startswith("app/") and normalized.endswith(".py"))
            or normalized in {
                "scripts/run_api.ps1",
                "scripts/run_all.ps1",
                "scripts/spec004_candidate_migration.py",
                "scripts/spec004_operational_promotion.py",
            }
        ):
            selected.append(normalized)
    return sorted(selected)


def _clean_extract(repository: Path, commit: str, destination: Path) -> Path:
    archive = destination / "source.tar"
    with archive.open("wb") as stream:
        subprocess.run(["git", "archive", "--format=tar", commit], cwd=repository,
                       stdout=stream, check=True)
    extracted = destination / "source"
    extracted.mkdir()
    shutil.unpack_archive(archive, extracted, format="tar")
    return extracted


def freeze(repository: Path, runtime: Path) -> tuple[Path, str, str]:
    commit = _git(repository, "rev-parse", "HEAD")
    _git(repository, "merge-base", "--is-ancestor", IMPLEMENTATION_PARENT, commit)
    files = _runtime_files(repository)
    with tempfile.TemporaryDirectory(prefix="spec004-freeze-") as temp:
        clean = _clean_extract(repository, commit, Path(temp))
        entries = []
        for relative in files:
            path = (clean / relative).resolve(strict=True)
            entries.append({"path": relative, "sha256": sha256_file(path),
                            "size_bytes": path.stat().st_size})
        payload = {
            "format_version": "1.2-spec004",
            "schema_version": SCHEMA_VERSION,
            "database_schema_version": DATABASE_SCHEMA_VERSION,
            "database_user_version": 4,
            "entries": entries,
            "provenance": {
                "implementation_parent_commit": IMPLEMENTATION_PARENT,
                "runtime_integration_commit": commit,
                "approved_candidate_manifest_sha256": APPROVED_CANDIDATE_MANIFEST,
                "previous_runtime_manifest_sha256": PREDECESSOR_RUNTIME_MANIFEST,
                "candidate_database_sha256": CANDIDATE_DATABASE,
                "migration": "backend/migration/spec004.py",
                "python": sys.version.split()[0],
                "requirements_sha256": sha256_file(clean / "requirements.txt"),
            },
            "privacy_safe": True,
        }
        data = _canonical_bytes(payload)
        checksum = hashlib.sha256(data).hexdigest()
        manifest = runtime / "runtime-manifests" / f"runtime-manifest-{checksum}.json"
        _atomic_create(manifest, data)
        verify_runtime_manifest(clean, manifest, checksum)
    verify_runtime_manifest(repository, manifest, checksum)
    return manifest, checksum, commit


def _validate_database(path: Path, expected_checksum: str, user_version: int) -> dict:
    if sha256_file(path) != expected_checksum:
        raise RuntimeError("checksum do banco diverge")
    validation = _sqlite_validate(path)
    uri = "file:" + path.resolve().as_posix() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        observed_version = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        triggers = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )}
    if observed_version != user_version:
        raise RuntimeError("user_version do banco diverge")
    if user_version == 4 and (
        "appointment_events" not in tables
        or not {"spec004_appointments_insert_guard", "spec004_appointments_update_guard"} <= triggers
    ):
        raise RuntimeError("schema material SPEC-004 incompleto")
    return {**validation, "user_version": observed_version,
            "appointment_events": "appointment_events" in tables}


def _preflight(runtime: Path) -> tuple[OperationalPointer, Path, dict]:
    pointer_path = runtime / "operational-pointer.json"
    if sha256_file(pointer_path) != PREDECESSOR_POINTER:
        raise RuntimeError("pointer predecessor diverge")
    pointer = read_pointer(pointer_path)
    if (pointer.generation != 5 or pointer.state != "canonical"
            or pointer.database_checksum_sha256 != PREDECESSOR_DATABASE
            or pointer.runtime_manifest_checksum_sha256 != PREDECESSOR_RUNTIME_MANIFEST):
        raise RuntimeError("envelope da Generation 5 diverge")
    database = Path(pointer.database_path).resolve(strict=True)
    validation = _validate_database(database, PREDECESSOR_DATABASE, 3)
    previous_manifest = runtime / "runtime-manifests" / (
        f"runtime-manifest-{PREDECESSOR_RUNTIME_MANIFEST}.json"
    )
    if sha256_file(previous_manifest) != PREDECESSOR_RUNTIME_MANIFEST:
        raise RuntimeError("runtime manifest predecessor diverge")
    if (runtime / "maintenance.lock").exists():
        raise RuntimeError("maintenance lock preexistente")
    for suffix in ("-wal", "-shm", "-journal"):
        if Path(str(database) + suffix).exists():
            raise RuntimeError("sidecar inesperado no predecessor")
    if directory_acl_fingerprint(runtime / "generations") != GENERATIONS_ACL:
        raise RuntimeError("ACL do destino de generations diverge")
    if shutil.disk_usage(runtime).free < database.stat().st_size * 8:
        raise RuntimeError("espaco livre insuficiente para gate")
    return pointer, database, validation


def _materialize_candidate(source: Path, destination: Path) -> dict:
    if destination.exists():
        raise RuntimeError("destino do candidato ja existe")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    result = migrate_spec004(destination)
    validation = _validate_database(destination, CANDIDATE_DATABASE, 4)
    if sha256_file(source) != PREDECESSOR_DATABASE:
        raise RuntimeError("predecessor mudou durante materializacao")
    return {**result, **validation, "candidate_sha256": CANDIDATE_DATABASE}


def _default_read_only_smoke(repository: Path, runtime: Path, database: Path) -> dict:
    os.environ.update({
        "CLINICA_RUNTIME_ROOT": str(runtime),
        "CLINICA_OPERATIONAL_POINTER": str(runtime / "operational-pointer.json"),
        "CLINICA_MAINTENANCE_LOCK": str(runtime / "maintenance.lock"),
        "CLINICA_RUNTIME_CODE_ROOT": str(repository),
        "BACKEND_VERIFY_READ_ONLY": "true",
        "BACKEND_RELOAD": "false",
        "AUTH_SECRET": "spec004-operational-read-only-smoke",
    })
    for name in ("BACKEND_DATABASE_PATH", "BACKEND_DATA_DIR", "CLINICA_RUNTIME_MANIFEST_DIR"):
        os.environ.pop(name, None)
    from fastapi.testclient import TestClient
    import backend.main as backend_main
    from backend.api.routes.auth import get_current_user
    from backend.database import session as database_session

    backend_main.license_status = lambda: {"valid": True}
    app = backend_main.create_app()
    actor = SimpleNamespace(id=1, role="admin", psychologist_id=None)
    app.dependency_overrides[get_current_user] = lambda: actor
    before = sha256_file(database)
    with TestClient(app) as client:
        if Path(database_session.DATABASE_PATH).resolve() != database.resolve():
            raise RuntimeError("startup default abriu banco diferente da Generation 6")
        health = client.get("/health")
        agenda = client.get("/appointments")
        write_guard = client.post("/appointments", json={})
        if health.status_code != 200 or agenda.status_code != 200 or write_guard.status_code != 503:
            raise RuntimeError("startup, health, agenda ou write guard falhou")
    if sha256_file(database) != before:
        raise RuntimeError("smoke read-only alterou Generation 6")
    return {"startup": "PASS", "health": "PASS", "agenda": "PASS",
            "authentication_override": "technical_identity_no_credentials",
            "authorization_route": "PASS", "write_guard": "PASS",
            "database_unchanged": True}


def run(repository: Path, runtime: Path) -> dict:
    repository = repository.resolve(strict=True)
    runtime = runtime.resolve(strict=True)
    pointer_path = runtime / "operational-pointer.json"
    predecessor, source, predecessor_validation = _preflight(runtime)
    manifest, manifest_checksum, runtime_commit = freeze(repository, runtime)
    execution = "spec004-promotion-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = runtime / "candidates" / f"{execution}-{CANDIDATE_DATABASE[:12]}.db"
    candidate_validation = _materialize_candidate(source, candidate)
    backup_before = runtime / "backups" / f"{execution}-generation-5"
    evidence_path = runtime / "evidence" / f"{execution}.json"
    lock = acquire_maintenance_lock(runtime / "maintenance.lock", execution,
                                    databases=(source,))
    switched = False
    try:
        if sha256_file(pointer_path) != PREDECESSOR_POINTER or sha256_file(source) != PREDECESSOR_DATABASE:
            raise RuntimeError("predecessor mudou antes da janela exclusiva")
        backup_manifest = create_final_backup(
            {"generation_5": source}, backup_before,
            execution_reference=execution, lock=lock,
        )
        promoted = promote_candidate(
            candidate, runtime / "generations", "spec004-v1",
            expected_checksum=CANDIDATE_DATABASE,
            acl_policy=AclPolicy(GENERATIONS_ACL), lock=lock,
        )
        new_pointer = OperationalPointer(
            generation=6, state="canonical", database_path=str(promoted),
            database_checksum_sha256=CANDIDATE_DATABASE, schema_version=SCHEMA_VERSION,
            runtime_manifest_checksum_sha256=manifest_checksum,
            previous_pointer_checksum_sha256=PREDECESSOR_POINTER,
        )
        pointer_after = atomic_swap_pointer(
            pointer_path, new_pointer, expected_current_checksum=PREDECESSOR_POINTER,
            lock=lock, history_dir=runtime / "pointer-history",
        )
        switched = True
    except Exception:
        if switched:
            _atomic_create(evidence_path, _canonical_bytes({
                "format_version": "1.0", "result": "POST_SWITCH_FAILURE",
                "execution_reference": execution,
                "policy": "NO_SILENT_POINTER_ROLLBACK", "privacy_safe": True,
            }))
        raise
    finally:
        lock.release()

    smoke = _default_read_only_smoke(repository, runtime, promoted)
    promoted_validation = _validate_database(promoted, CANDIDATE_DATABASE, 4)
    backup_after = runtime / "backups" / f"{execution}-generation-6-stabilized"
    backup_lock = acquire_maintenance_lock(runtime / "maintenance.lock", execution + "-stabilization",
                                           databases=(promoted,))
    try:
        stabilized_manifest = create_final_backup(
            {"generation_6": promoted}, backup_after,
            execution_reference=execution + "-stabilization", lock=backup_lock,
        )
    finally:
        backup_lock.release()
    restore_dir = runtime / "evidence" / execution
    restore_dir.mkdir(parents=True, exist_ok=False)
    restore = restore_dir / "isolated-restore-validation.db"
    shutil.copyfile(backup_after / "generation_6.backup.db", restore)
    restore_validation = _validate_database(restore, CANDIDATE_DATABASE, 4)
    final_pointer = read_pointer(pointer_path)
    result = {
        "format_version": "1.0-spec004", "result": "SPEC004_PROMOTION_STABILIZED",
        "execution_reference": execution,
        "provenance": {"runtime_integration_commit": runtime_commit,
                       "implementation_parent_commit": IMPLEMENTATION_PARENT,
                       "approved_candidate_manifest_sha256": APPROVED_CANDIDATE_MANIFEST},
        "generation_before": predecessor.generation,
        "generation_after": final_pointer.generation,
        "pointer_before_sha256": PREDECESSOR_POINTER,
        "pointer_after_sha256": final_pointer.checksum,
        "runtime_manifest": str(manifest),
        "runtime_manifest_sha256": manifest_checksum,
        "candidate_sha256": CANDIDATE_DATABASE,
        "predecessor_validation": predecessor_validation,
        "candidate_validation": candidate_validation,
        "promoted_validation": promoted_validation,
        "pre_promotion_backup_manifest_sha256": sha256_file(backup_manifest),
        "stabilized_backup_manifest_sha256": sha256_file(stabilized_manifest),
        "restore_sha256": sha256_file(restore),
        "restore_validation": restore_validation,
        "smoke": smoke,
        "rollback_policy": "NO_SILENT_POINTER_ROLLBACK",
        "privacy_safe": True,
    }
    evidence_checksum = _atomic_create(evidence_path, _canonical_bytes(result))
    return {**result, "evidence_path": str(evidence_path),
            "evidence_sha256": evidence_checksum}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.repository, args.runtime), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
