"""Freeze e promoção operacional fail-closed da SPEC-003.

O pointer Generation 2 possui divergência histórica aceita entre o checksum físico
atual e o campo gravado no JSON. Por isso o predecessor é validado pelo SHA-256 exato
do arquivo, por seus campos esperados e pelo checksum físico independente do banco.
Essa exceção não é usada para ler o novo pointer Generation 3.
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
    _atomic_replace,
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


SPEC003_COMMIT = "00ee65e8dc1541783cf4c798f08b40af6b9fd266"
OPERATIONAL_BASELINE_COMMIT = "ebc8604d5e97230ccfe86ecb65a593fcfddf9fb5"
GENERATION2_POINTER = "55604e3881535b8891cdea020980f41a8168f7b5e00edc08c9a3160b9dea960b"
GENERATION2_DATABASE = "4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f"
CANDIDATE = "143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506"
GENERATIONS_ACL = "5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91"
EXPECTED_COUNTS = {
    "appointments": 2,
    "clinical_records": 2,
    "expenses": 3,
    "patients": 1,
    "payments": 3,
    "psychologists": 1,
    "users": 3,
}
DATABASE_SCHEMA_VERSION = "backend-models-v3-spec003-integrity"


def _canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repository, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _runtime_files(repository: Path) -> list[str]:
    tracked = _git(repository, "ls-files").splitlines()
    selected = []
    for relative in tracked:
        normalized = relative.replace("\\", "/")
        if (
            normalized == "main.py"
            or normalized == "requirements.txt"
            or (normalized.startswith("backend/") and normalized.endswith(".py"))
            or (normalized.startswith("app/") and normalized.endswith(".py"))
            or normalized in {
                "scripts/run_api.ps1",
                "scripts/run_all.ps1",
                "scripts/spec003_candidate_migration.py",
                "scripts/spec003_operational_promotion.py",
            }
        ):
            selected.append(normalized)
    return selected


def freeze(repository: Path, runtime: Path) -> tuple[Path, str, str]:
    runtime_commit = _git(repository, "rev-parse", "HEAD")
    if _git(repository, "status", "--porcelain"):
        raise RuntimeError("runtime code root nao esta limpo")
    _git(repository, "merge-base", "--is-ancestor", SPEC003_COMMIT, runtime_commit)
    _git(repository, "merge-base", "--is-ancestor", OPERATIONAL_BASELINE_COMMIT, runtime_commit)
    provenance = {
        "composition": "ACCEPTED_OPERATIONAL_BASELINE + SPEC003_IMPLEMENTATION_COMMIT",
        "accepted_operational_baseline_commit": OPERATIONAL_BASELINE_COMMIT,
        "spec003_implementation_commit": SPEC003_COMMIT,
        "runtime_integration_commit": runtime_commit,
        "candidate_version": "spec003-v2",
        "candidate_sha256": CANDIDATE,
        "migration": "backend/migration/spec003.py",
        "python": sys.version.split()[0],
        "requirements_sha256": sha256_file(repository / "requirements.txt"),
    }
    entries = []
    for relative in _runtime_files(repository):
        path = (repository / relative).resolve(strict=True)
        entries.append({
            "path": relative,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    payload = {
        "format_version": "1.1-spec003",
        # Compatibilidade temporária com o loader imutável da SPEC-008.
        "schema_version": SCHEMA_VERSION,
        "database_schema_version": DATABASE_SCHEMA_VERSION,
        "database_user_version": 3,
        "entries": entries,
        "provenance": provenance,
        "privacy_safe": True,
    }
    data = _canonical_bytes(payload)
    checksum = hashlib.sha256(data).hexdigest()
    manifest = runtime / "runtime-manifests" / f"runtime-manifest-{checksum}.json"
    _atomic_create(manifest, data)
    verify_runtime_manifest(repository, manifest, checksum)
    return manifest, checksum, runtime_commit


def _accepted_generation2_pointer(pointer_path: Path) -> tuple[dict, bytes, str, Path]:
    raw = pointer_path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if checksum != GENERATION2_POINTER:
        raise RuntimeError("pointer Generation 2 diverge do envelope aprovado")
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("generation") != 2 or payload.get("state") != "canonical":
        raise RuntimeError("pointer Generation 2 possui estado inesperado")
    database = Path(payload["database_path"]).resolve(strict=True)
    if sha256_file(database) != GENERATION2_DATABASE:
        raise RuntimeError("Generation 2 fisica diverge")
    return payload, raw, checksum, database


def _current_pointer(pointer_path: Path) -> tuple[dict, bytes, str, Path, str]:
    raw = pointer_path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if checksum == GENERATION2_POINTER:
        payload, raw, checksum, database = _accepted_generation2_pointer(pointer_path)
        return payload, raw, checksum, database, "PROMOTION"
    pointer = read_pointer(pointer_path)
    database = Path(pointer.database_path).resolve(strict=True)
    if (
        pointer.generation == 3
        and pointer.state == "canonical"
        and pointer.database_checksum_sha256 == CANDIDATE
        and sha256_file(database) == CANDIDATE
    ):
        return json.loads(raw.decode("utf-8")), raw, checksum, database, "FORWARD_RECOVERY"
    raise RuntimeError("pointer nao corresponde ao predecessor aprovado nem ao recovery Generation 3")


def _validate_candidate(candidate: Path) -> dict:
    if sha256_file(candidate) != CANDIDATE:
        raise RuntimeError("candidato v2 diverge")
    validation = _sqlite_validate(candidate)
    uri = "file:" + candidate.resolve().as_posix() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        counts = {
            table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in EXPECTED_COUNTS
        }
    if user_version != 3 or counts != EXPECTED_COUNTS:
        raise RuntimeError("schema ou contagens do candidato divergem")
    return {**validation, "user_version": user_version, "counts": counts}


def _swap_accepted_predecessor(pointer_path: Path, raw: bytes, old_checksum: str,
                               new: OperationalPointer, lock, history_dir: Path) -> str:
    lock.assert_held()
    observed = pointer_path.read_bytes()
    if observed != raw or hashlib.sha256(observed).hexdigest() != old_checksum:
        raise RuntimeError("pointer mudou desde o preflight")
    history_dir.mkdir(parents=True, exist_ok=True)
    _atomic_create(history_dir / f"pointer-{old_checksum}.json", raw)
    return _atomic_replace(pointer_path, new.bytes())


def _read_only_smoke(repository: Path, runtime: Path, database: Path) -> dict:
    os.environ.update({
        "CLINICA_RUNTIME_ROOT": str(runtime),
        "CLINICA_OPERATIONAL_POINTER": str(runtime / "operational-pointer.json"),
        "CLINICA_MAINTENANCE_LOCK": str(runtime / "maintenance.lock"),
        "CLINICA_RUNTIME_MANIFEST_DIR": str(runtime / "runtime-manifests"),
        "CLINICA_RUNTIME_CODE_ROOT": str(repository),
        "BACKEND_VERIFY_READ_ONLY": "true",
        "BACKEND_RELOAD": "false",
        "AUTH_SECRET": "spec003-read-only-runtime-verification-only",
    })
    os.environ.pop("BACKEND_DATABASE_PATH", None)
    os.environ.pop("BACKEND_DATA_DIR", None)
    from fastapi.testclient import TestClient
    import backend.main as backend_main
    from backend.api.dependencies import require_admin, require_psychologist
    from backend.api.routes.auth import get_current_user
    from backend.database import session as database_session

    backend_main.license_status = lambda: {"valid": True}
    app = backend_main.create_app()
    identity = SimpleNamespace(id=1, role="admin")
    app.dependency_overrides[get_current_user] = lambda: identity
    app.dependency_overrides[require_admin] = lambda: identity
    app.dependency_overrides[require_psychologist] = lambda: identity
    before = sha256_file(database)
    with TestClient(app) as client:
        if Path(database_session.DATABASE_PATH).resolve() != database.resolve():
            raise RuntimeError("runtime abriu banco diferente da Generation 3")
        health = client.get("/health")
        endpoints = (
            "/patients", "/psychologists", "/appointments", "/clinical-records",
            "/finance/payments", "/finance/expenses", "/finance/summary", "/settings",
        )
        statuses = {path: client.get(path).status_code for path in endpoints}
        if health.status_code != 200 or any(value != 200 for value in statuses.values()):
            raise RuntimeError("health/smoke read-only falhou")
        if client.post("/patients", json={}).status_code != 503:
            raise RuntimeError("write guard nao bloqueou operacao")
    if sha256_file(database) != before:
        raise RuntimeError("smoke read-only alterou Generation 3")
    return {"startup": "PASS", "health": "PASS", "critical_gets": statuses,
            "write_guard": "PASS", "database_unchanged": True}


def run(repository: Path, runtime: Path, candidate: Path) -> dict:
    repository = repository.resolve(strict=True)
    runtime = runtime.resolve(strict=True)
    candidate = candidate.resolve(strict=True)
    pointer_path = runtime / "operational-pointer.json"
    manifest, runtime_manifest_checksum, runtime_commit = freeze(repository, runtime)
    payload, pointer_raw, pointer_checksum, current_database, mode = _current_pointer(pointer_path)
    candidate_validation = _validate_candidate(candidate)
    if directory_acl_fingerprint(runtime / "generations") != GENERATIONS_ACL:
        raise RuntimeError("ACL do destino de generations diverge")
    if (runtime / "maintenance.lock").exists():
        raise RuntimeError("maintenance lock preexistente")
    for database in (current_database, candidate):
        if any(Path(str(database) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise RuntimeError("sidecar inesperado no preflight")

    execution = "spec003-promotion-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_before = runtime / "backups" / (execution + "-pre-promotion")
    evidence_path = runtime / "evidence" / f"{execution}.json"
    lock = acquire_maintenance_lock(
        runtime / "maintenance.lock", execution, databases=(current_database,)
    )
    switched = False
    try:
        backup_manifest = create_final_backup(
            {f"generation_{payload['generation']}": current_database}, backup_before,
            execution_reference=execution, lock=lock,
        )
        if mode == "PROMOTION":
            promoted = promote_candidate(
                candidate, runtime / "generations", "spec003-v2",
                expected_checksum=CANDIDATE,
                acl_policy=AclPolicy(GENERATIONS_ACL), lock=lock,
            )
        else:
            promoted = current_database
        new_pointer = OperationalPointer(
            generation=payload["generation"] + 1, state="canonical", database_path=str(promoted),
            database_checksum_sha256=CANDIDATE, schema_version=SCHEMA_VERSION,
            runtime_manifest_checksum_sha256=runtime_manifest_checksum,
            previous_pointer_checksum_sha256=pointer_checksum,
        )
        if mode == "PROMOTION":
            new_pointer_checksum = _swap_accepted_predecessor(
                pointer_path, pointer_raw, pointer_checksum, new_pointer, lock,
                runtime / "pointer-history",
            )
        else:
            new_pointer_checksum = atomic_swap_pointer(
                pointer_path, new_pointer, expected_current_checksum=pointer_checksum,
                lock=lock, history_dir=runtime / "pointer-history",
            )
        switched = True
        smoke = _read_only_smoke(repository, runtime, promoted)
    except Exception:
        if switched:
            failure = {
                "format_version": "1.0", "result": "POST_SWITCH_FAILURE",
                "execution_reference": execution,
                "policy": "NO_SILENT_POINTER_ROLLBACK", "privacy_safe": True,
            }
            _atomic_create(evidence_path, _canonical_bytes(failure))
        raise
    finally:
        lock.release()

    backup_after = runtime / "backups" / (execution + "-initial-generation-3")
    backup_lock = acquire_maintenance_lock(
        runtime / "maintenance.lock", execution + "-backup", databases=(promoted,)
    )
    try:
        initial_manifest = create_final_backup(
            {"generation_3": promoted}, backup_after,
            execution_reference=execution + "-backup", lock=backup_lock,
        )
    finally:
        backup_lock.release()
    restore = runtime / "evidence" / execution / "isolated-restore-validation.db"
    restore.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(backup_after / "generation_3.backup.db", restore)
    restore_validation = _sqlite_validate(restore)
    if sha256_file(restore) != CANDIDATE:
        raise RuntimeError("restore isolado diverge da Generation 3")

    final_pointer = read_pointer(pointer_path)
    result = {
        "format_version": "1.0", "result": "SPEC003_PROMOTION_STABILIZED",
        "execution_reference": execution,
        "provenance": {
            "accepted_operational_baseline_commit": OPERATIONAL_BASELINE_COMMIT,
            "spec003_implementation_commit": SPEC003_COMMIT,
            "runtime_integration_commit": runtime_commit,
        },
        "runtime_manifest": str(manifest),
        "runtime_manifest_sha256": runtime_manifest_checksum,
        "pointer_before_sha256": pointer_checksum,
        "pointer_after_sha256": final_pointer.checksum,
        "mode": mode,
        "generation_before": payload["generation"],
        "generation_after": final_pointer.generation,
        "candidate_sha256": CANDIDATE,
        "candidate_validation": candidate_validation,
        "pre_promotion_backup_manifest_sha256": sha256_file(backup_manifest),
        "initial_backup_manifest_sha256": sha256_file(initial_manifest),
        "restore_validation": restore_validation,
        "restore_sha256": sha256_file(restore),
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
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.repository, args.runtime, args.candidate),
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
