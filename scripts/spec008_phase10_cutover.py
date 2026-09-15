"""Executa o cutover real aprovado da SPEC-008 com rollback fail-closed."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from backend.cutover.infrastructure import (
    AclPolicy,
    OperationalPointer,
    _atomic_create,
    _sqlite_validate,
    acquire_maintenance_lock,
    atomic_swap_pointer,
    create_final_backup,
    directory_acl_fingerprint,
    promote_candidate,
    read_pointer,
    rollback_pointer,
    sha256_file,
    verify_runtime_manifest,
)


BASELINE = "d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757"
CANDIDATE = "96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46"
ROOT_ACL = "f58389254ac21f4890d95ad00ed1039fd0820183855e90a33ea9715f7c05b5f0"
GENERATIONS_ACL = "5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91"
RUNTIME_MANIFEST = "d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398"
FREEZE = "468517df633e482d0e1c8bb3a292da230e1b97f29c01e72c771367efa7dc3a2f"
REMAP = "f8dfcddb1947ac4d1d14519424342a015712d71609110cb3392ff3780ab82876"
SCHEMA = "backend-models-v2-credential-reset"


def _sidecars(path: Path) -> list[str]:
    return [suffix for suffix in ("-wal", "-shm", "-journal")
            if Path(str(path) + suffix).exists()]


def _assert_frozen(repository: Path, phase: Path, runtime: Path,
                   candidate: Path, generation1: Path, pointer_path: Path) -> OperationalPointer:
    if directory_acl_fingerprint(runtime) != ROOT_ACL:
        raise RuntimeError("ACL da raiz runtime diverge")
    if directory_acl_fingerprint(runtime / "generations") != GENERATIONS_ACL:
        raise RuntimeError("ACL do destino de promocao diverge")
    if sha256_file(generation1) != BASELINE:
        raise RuntimeError("generation 1 diverge do baseline sucessor")
    if sha256_file(candidate) != CANDIDATE:
        raise RuntimeError("candidato verified-v2 diverge")
    pointer = read_pointer(pointer_path)
    if pointer.generation != 1 or pointer.state != "legacy" or pointer.database_checksum_sha256 != BASELINE:
        raise RuntimeError("pointer inicial diverge")
    if Path(pointer.database_path).resolve() != generation1.resolve():
        raise RuntimeError("pointer inicial nao aponta para generation 1")
    freeze_path = phase / "reconciliation-freeze-manifest-v7.json"
    remap_path = phase / "remap-manifest-verified-v2.json"
    if sha256_file(freeze_path) != FREEZE:
        raise RuntimeError("freeze v7 diverge")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("freeze_reference") != "spec008-20260911-phase1-001-freeze-v7" or freeze.get("status") != "frozen":
        raise RuntimeError("freeze v7 invalido")
    if sha256_file(remap_path) != REMAP:
        raise RuntimeError("RemapManifest diverge")
    remap = json.loads(remap_path.read_text(encoding="utf-8"))
    if remap.get("lifecycle") != "verified" or not remap.get("manifest_version", "").endswith("verified-v2"):
        raise RuntimeError("RemapManifest nao esta verified-v2")
    manifest = runtime / "runtime-manifests" / f"runtime-manifest-{RUNTIME_MANIFEST}.json"
    verify_runtime_manifest(repository, manifest, RUNTIME_MANIFEST)
    for database in (generation1, candidate):
        _sqlite_validate(database)
        if _sidecars(database):
            raise RuntimeError(f"sidecar pendente: {database}")
    return pointer


def _smoke(repository: Path, runtime: Path, expected_database: Path) -> dict:
    os.environ.update({
        "CLINICA_RUNTIME_ROOT": str(runtime),
        "CLINICA_OPERATIONAL_POINTER": str(runtime / "operational-pointer.json"),
        "CLINICA_MAINTENANCE_LOCK": str(runtime / "maintenance.lock"),
        "CLINICA_RUNTIME_MANIFEST_DIR": str(runtime / "runtime-manifests"),
        "CLINICA_RUNTIME_CODE_ROOT": str(repository),
        "BACKEND_VERIFY_READ_ONLY": "true",
        "BACKEND_RELOAD": "false",
        "AUTH_SECRET": "spec008-cutover-read-only-verification-only",
    })
    os.environ.pop("BACKEND_DATABASE_PATH", None)
    os.environ.pop("BACKEND_DATA_DIR", None)

    from fastapi.testclient import TestClient
    import backend.main as backend_main
    from backend.api.dependencies import require_admin, require_psychologist
    from backend.api.routes.auth import get_current_user
    from backend.database import session as database_session
    from backend.models.user import User
    from backend.services.auth_service import AuthService
    from backend.utils.security import DISABLED_CREDENTIAL_V1

    backend_main.license_status = lambda: {"valid": True}
    app = backend_main.create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role="admin")
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(role="admin")
    app.dependency_overrides[require_psychologist] = lambda: SimpleNamespace(role="psychologist")
    before = sha256_file(expected_database)
    with TestClient(app) as client:
        effective = Path(database_session.DATABASE_PATH).resolve()
        if effective != expected_database.resolve():
            raise RuntimeError("runtime abriu banco diferente da generation promovida")
        health = client.get("/health")
        if health.status_code != 200 or health.json().get("status") != "ok":
            raise RuntimeError("health falhou")
        endpoints = (
            "/patients", "/psychologists", "/appointments",
            "/clinical-records", "/finance/payments", "/finance/expenses",
            "/finance/summary", "/settings",
        )
        statuses = {path: client.get(path).status_code for path in endpoints}
        if any(status != 200 for status in statuses.values()):
            raise RuntimeError("smoke GET falhou: " + json.dumps(statuses, sort_keys=True))
        if client.post("/patients", json={}).status_code != 503:
            raise RuntimeError("write probe nao foi bloqueado")
        if client.post("/auth/login", json={"username": "cutover-probe", "password": "invalid"}).status_code != 503:
            raise RuntimeError("login mutavel nao foi bloqueado no modo read-only")
        with database_session.SessionLocal() as db:
            users = db.query(User).all()
            if not users or any(not user.password_reset_required for user in users):
                raise RuntimeError("password_reset_required diverge")
            if any(user.password_hash != DISABLED_CREDENTIAL_V1 for user in users):
                raise RuntimeError("credencial desabilitada diverge")
            auth = AuthService(db)
            if any(auth.authenticate(user.username, "invalid-cutover-probe") is not None for user in users):
                raise RuntimeError("autenticacao deveria permanecer bloqueada")
    if sha256_file(expected_database) != before:
        raise RuntimeError("smoke read-only alterou a generation promovida")
    return {
        "startup": "PASS", "health": "PASS", "critical_gets": "PASS",
        "write_guard": "PASS", "authentication_blocked": "PASS",
        "password_reset_required": "PASS", "disabled_credentials": "PASS",
        "database_path": str(expected_database.resolve()), "database_unchanged": True,
    }


def run(repository: Path, runtime: Path, phase: Path,
        backend_legacy: Path, desktop_legacy: Path) -> dict:
    repository = repository.resolve(strict=True)
    runtime = runtime.resolve(strict=True)
    phase = phase.resolve(strict=True)
    backend_legacy = backend_legacy.resolve(strict=True)
    desktop_legacy = desktop_legacy.resolve(strict=True)
    candidate = (phase / "canonical-candidate-v1.db").resolve(strict=True)
    generation1 = (runtime / "generations" / "generation-0001-d0123c58c57f.db").resolve(strict=True)
    pointer_path = runtime / "operational-pointer.json"
    old = _assert_frozen(repository, phase, runtime, candidate, generation1, pointer_path)
    execution = "spec008-phase10-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = runtime / "backups" / execution
    evidence_path = runtime / "evidence" / f"{execution}-cutover.json"
    promoted = None
    switched_checksum = None
    backup_manifest = None
    lock = acquire_maintenance_lock(
        runtime / "maintenance.lock", execution,
        databases=(generation1, backend_legacy, desktop_legacy),
    )
    try:
        backup_manifest = create_final_backup(
            {"generation_1": generation1, "backend_legacy": backend_legacy,
             "desktop_legacy": desktop_legacy},
            backup_dir, execution_reference=execution, lock=lock,
        )
        backup_payload = json.loads(backup_manifest.read_text(encoding="utf-8"))
        if len(backup_payload.get("entries", [])) != 3 or any(
            entry["integrity_check"] != "ok" or entry["foreign_key_violations"]
            for entry in backup_payload["entries"]
        ):
            raise RuntimeError("backup final nao validado")

        # Revalidação imediatamente anterior à promoção, ainda sob locks exclusivos.
        current = _assert_frozen(repository, phase, runtime, candidate, generation1, pointer_path)
        if current.checksum != old.checksum:
            raise RuntimeError("pointer mudou durante a janela")
        for legacy in (backend_legacy, desktop_legacy):
            if _sidecars(legacy):
                raise RuntimeError("sidecar legado inesperado durante lock")

        promoted = promote_candidate(
            candidate, runtime / "generations", "verified-v2",
            expected_checksum=CANDIDATE,
            acl_policy=AclPolicy(GENERATIONS_ACL),
            lock=lock,
        )
        new = OperationalPointer(
            generation=2,
            state="canonical",
            database_path=str(promoted.resolve()),
            database_checksum_sha256=CANDIDATE,
            schema_version=SCHEMA,
            runtime_manifest_checksum_sha256=RUNTIME_MANIFEST,
            previous_pointer_checksum_sha256=old.checksum,
        )
        switched_checksum = atomic_swap_pointer(
            pointer_path, new, expected_current_checksum=old.checksum,
            lock=lock, history_dir=runtime / "pointer-history",
        )
        smoke = _smoke(repository, runtime, promoted)
        final_pointer = read_pointer(pointer_path)
        validation = _sqlite_validate(promoted)
        if (final_pointer.checksum != switched_checksum
                or final_pointer.database_checksum_sha256 != CANDIDATE
                or Path(final_pointer.database_path).resolve() != promoted.resolve()
                or sha256_file(promoted) != CANDIDATE):
            raise RuntimeError("verify final diverge")
        if sha256_file(generation1) != BASELINE:
            raise RuntimeError("generation 1 mudou durante cutover")
        result = {
            "format_version": "1.0", "result": "CUTOVER_ACCEPTED",
            "execution_reference": execution,
            "sequence": ["QUIESCE", "FINAL_BACKUP", "REVALIDATE", "PROMOTE",
                         "SWITCH", "START", "HEALTH", "SMOKE", "VERIFY"],
            "generation_before": 1, "generation_after": 2,
            "pointer_before_sha256": old.checksum,
            "pointer_after_sha256": final_pointer.checksum,
            "backup_manifest": str(backup_manifest),
            "backup_manifest_sha256": sha256_file(backup_manifest),
            "promoted_database": str(promoted),
            "promoted_checksum_sha256": sha256_file(promoted),
            "runtime_manifest_checksum_sha256": RUNTIME_MANIFEST,
            "smoke": smoke, "sqlite": validation,
            "legacy_generation_checksum_sha256": sha256_file(generation1),
            "rollback_available": True, "cutover_writes_enabled": False,
            "privacy_safe": True,
        }
        evidence_checksum = _atomic_create(evidence_path, (json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + "\n").encode("utf-8"))
        return {**result, "evidence_path": str(evidence_path),
                "evidence_checksum_sha256": evidence_checksum}
    except Exception as failure:
        rollback = {"required": promoted is not None or switched_checksum is not None}
        if switched_checksum is not None:
            rollback_checksum = rollback_pointer(
                pointer_path, old.checksum,
                expected_current_checksum=switched_checksum,
                lock=lock, history_dir=runtime / "pointer-history",
            )
            rollback["pointer_checksum_sha256"] = rollback_checksum
        if backup_manifest is not None:
            restored = backup_dir / "rollback-restored-generation-1.db"
            shutil.copyfile(backup_dir / "generation_1.backup.db", restored)
            rollback["restore_path"] = str(restored)
            rollback["restore_validation"] = _sqlite_validate(restored)
            rollback["restore_checksum_sha256"] = sha256_file(restored)
        if switched_checksum is not None:
            rollback["health"] = _smoke(repository, runtime, generation1)["health"]
        rollback["final_pointer_state"] = read_pointer(pointer_path).state
        rollback["failure_type"] = type(failure).__name__
        rollback["failure_message"] = str(failure)
        result = {
            "format_version": "1.0", "result": "CUTOVER_ROLLED_BACK",
            "execution_reference": execution, "rollback": rollback,
            "backup_manifest": str(backup_manifest) if backup_manifest else None,
            "backup_manifest_sha256": sha256_file(backup_manifest) if backup_manifest else None,
            "promoted_database": str(promoted) if promoted else None,
            "privacy_safe": True,
        }
        evidence_checksum = _atomic_create(evidence_path, (json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + "\n").encode("utf-8"))
        return {**result, "evidence_path": str(evidence_path),
                "evidence_checksum_sha256": evidence_checksum}
    finally:
        lock.release()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--phase", type=Path, required=True)
    parser.add_argument("--backend-legacy", type=Path, required=True)
    parser.add_argument("--desktop-legacy", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.repository, args.runtime, args.phase,
                         args.backend_legacy, args.desktop_legacy),
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
