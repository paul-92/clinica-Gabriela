"""Estabilização write-enabled pós-cutover da SPEC-008 sem dados de domínio sintéticos."""

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
    _atomic_create,
    _sqlite_validate,
    acquire_maintenance_lock,
    create_final_backup,
    directory_acl_fingerprint,
    read_pointer,
    sha256_file,
    verify_runtime_manifest,
)


CANONICAL_INITIAL = "96b27238c038eaf16a7027cd2bb717a3a153bcc5899211e308c8fe5d079c8a46"
POINTER = "55604e3881535b8891cdea020980f41a8168f7b5e00edc08c9a3160b9dea960b"
RUNTIME_MANIFEST = "d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398"
ROOT_ACL = "f58389254ac21f4890d95ad00ed1039fd0820183855e90a33ea9715f7c05b5f0"
GENERATIONS_ACL = "5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91"
GENERATION1 = "d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757"
PRECUTOVER_BACKUP = "922eb91aaa5b0a498ffdd535949a0ad0e99892c5bacc8c83f2d648873e2881a3"
BOUNDARY = "7ff7e402ddd990f4e8a9f17c7fb6fb63ba375f7fc9b9bba9959ad24060ee5ba8"
TECHNICAL_MARKER = 1101


def _json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _sidecars(path: Path) -> list[str]:
    return [suffix for suffix in ("-wal", "-shm", "-journal")
            if Path(str(path) + suffix).exists()]


def _preconditions(repository: Path, runtime: Path) -> tuple[Path, object]:
    pointer = read_pointer(runtime / "operational-pointer.json")
    canonical = Path(pointer.database_path).resolve(strict=True)
    generation1 = runtime / "generations" / "generation-0001-d0123c58c57f.db"
    precutover = runtime / "backups" / "spec008-phase10-20260915T004517Z" / "final-backup-manifest.json"
    if pointer.generation != 2 or pointer.state != "canonical" or pointer.checksum != POINTER:
        raise RuntimeError("pointer canonical diverge")
    if sha256_file(canonical) != CANONICAL_INITIAL or pointer.database_checksum_sha256 != CANONICAL_INITIAL:
        raise RuntimeError("generation 2 inicial diverge")
    if sha256_file(generation1) != GENERATION1:
        raise RuntimeError("generation 1 nao preservada")
    if sha256_file(precutover) != PRECUTOVER_BACKUP:
        raise RuntimeError("backup pre-cutover nao preservado")
    if directory_acl_fingerprint(runtime) != ROOT_ACL:
        raise RuntimeError("ACL da raiz diverge")
    if directory_acl_fingerprint(runtime / "generations") != GENERATIONS_ACL:
        raise RuntimeError("ACL de generations diverge")
    manifest = runtime / "runtime-manifests" / f"runtime-manifest-{RUNTIME_MANIFEST}.json"
    verify_runtime_manifest(repository, manifest, RUNTIME_MANIFEST)
    validation = _sqlite_validate(canonical)
    if validation["integrity_check"] != "ok" or validation["foreign_key_violations"]:
        raise RuntimeError("generation 2 invalida")
    if _sidecars(canonical):
        raise RuntimeError("sidecar pendente antes da estabilizacao")
    return canonical, pointer


def _start_write_enabled(repository: Path, runtime: Path, canonical: Path) -> dict:
    os.environ.update({
        "CLINICA_RUNTIME_ROOT": str(runtime),
        "CLINICA_OPERATIONAL_POINTER": str(runtime / "operational-pointer.json"),
        "CLINICA_MAINTENANCE_LOCK": str(runtime / "maintenance.lock"),
        "CLINICA_RUNTIME_MANIFEST_DIR": str(runtime / "runtime-manifests"),
        "CLINICA_RUNTIME_CODE_ROOT": str(repository),
        "BACKEND_VERIFY_READ_ONLY": "false",
        "BACKEND_RELOAD": "false",
        "AUTH_SECRET": "spec008-phase11-controlled-write-enabled",
    })
    os.environ.pop("BACKEND_DATABASE_PATH", None)
    os.environ.pop("BACKEND_DATA_DIR", None)

    from fastapi.testclient import TestClient
    import backend.main as backend_main
    from app.utils.cutover_guard import assert_legacy_desktop_allowed
    from backend.api.dependencies import require_admin, require_psychologist
    from backend.api.routes.auth import get_current_user
    from backend.database import session as database_session
    from backend.models.user import User
    from backend.utils.security import DISABLED_CREDENTIAL_V1

    try:
        assert_legacy_desktop_allowed()
    except RuntimeError as exc:
        if "bloqueado apos promocao canonica" not in str(exc):
            raise
        desktop_guard = "PASS"
    else:
        raise RuntimeError("desktop legado nao foi bloqueado")

    backend_main.license_status = lambda: {"valid": True}
    app = backend_main.create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role="admin")
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(role="admin")
    app.dependency_overrides[require_psychologist] = lambda: SimpleNamespace(role="psychologist")
    with TestClient(app) as client:
        if Path(database_session.DATABASE_PATH).resolve() != canonical:
            raise RuntimeError("runtime write-enabled abriu banco incorreto")
        if client.get("/health").status_code != 200:
            raise RuntimeError("health write-enabled falhou")
        endpoints = (
            "/patients", "/psychologists", "/appointments", "/clinical-records",
            "/finance/payments", "/finance/expenses", "/finance/summary", "/settings",
        )
        statuses = {path: client.get(path).status_code for path in endpoints}
        if any(value != 200 for value in statuses.values()):
            raise RuntimeError("GET funcional falhou")
        # 422 comprova passagem pelo guard write-enabled sem inserir dado de domínio.
        if client.post("/patients", json={}).status_code != 422:
            raise RuntimeError("write guard permaneceu read-only")
        if client.post("/auth/login", json={"username": "phase11-probe", "password": "invalid"}).status_code != 401:
            raise RuntimeError("autenticacao write-enabled diverge")
        with database_session.SessionLocal() as db:
            users = db.query(User).all()
            if not users or any(not user.password_reset_required for user in users):
                raise RuntimeError("password_reset_required diverge")
            if any(user.password_hash != DISABLED_CREDENTIAL_V1 for user in users):
                raise RuntimeError("credenciais desabilitadas divergem")

    return {
        "startup": "PASS", "health": "PASS", "critical_reads": "PASS",
        "write_guard_enabled": "PASS", "invalid_domain_write_rejected": "PASS",
        "authentication": "PASS_BLOCKED_BY_RESET_AND_DISABLED_CREDENTIAL",
        "password_reset_required": "PASS", "desktop_legacy_guard": desktop_guard,
        "runtime_database_path": str(canonical),
    }


def _technical_persistence_after_shutdown(canonical: Path) -> dict:
    """Exige que o runtime esteja encerrado antes de trocar o journal mode."""
    connection = sqlite3.connect(canonical, timeout=0)
    try:
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
        if connection.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() != "wal":
            raise RuntimeError("WAL nao ativado")
        connection.execute(f"PRAGMA user_version={TECHNICAL_MARKER}")
        connection.commit()
    finally:
        connection.close()
    reopened = sqlite3.connect(canonical, timeout=0)
    try:
        if reopened.execute("PRAGMA user_version").fetchone()[0] != TECHNICAL_MARKER:
            raise RuntimeError("marcador tecnico nao persistiu")
        reopened.execute("PRAGMA user_version=0")
        reopened.commit()
        checkpoint = list(reopened.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
        final_mode = reopened.execute("PRAGMA journal_mode=DELETE").fetchone()[0].lower()
    finally:
        reopened.close()
    if checkpoint != [0, 0, 0] or final_mode != "delete" or _sidecars(canonical):
        raise RuntimeError("checkpoint/finalizacao WAL diverge")
    return {
        "result": "PASS_USER_VERSION_0_TO_1101_TO_0",
        "busy_timeout_ms": busy_timeout,
        "wal_checkpoint": checkpoint,
        "journal_mode_final": final_mode,
    }


def run(repository: Path, runtime: Path) -> dict:
    repository = repository.resolve(strict=True)
    runtime = runtime.resolve(strict=True)
    canonical, pointer = _preconditions(repository, runtime)
    initial = {
        "sha256": sha256_file(canonical), "size_bytes": canonical.stat().st_size,
        "mtime_ns": canonical.stat().st_mtime_ns, "pointer_sha256": pointer.checksum,
    }
    execution = "spec008-phase11-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = runtime / "evidence" / execution
    evidence_dir.mkdir(exist_ok=False)
    boundary_path = evidence_dir / "rollback-boundary.json"
    _atomic_create(boundary_path, _json_bytes({
        "format_version": "1.0", "execution_reference": execution,
        "boundary": "NO_SILENT_ROLLBACK_AFTER_CANONICAL_WRITE",
        "canonical_initial_state": initial,
        "failure_policy": "preserve_generation_2_and_escalate_human",
        "privacy_safe": True,
    }))
    writes_exist = False
    try:
        # Conservador: o bootstrap write-enabled pode produzir escrita antes de retornar.
        # A partir daqui nunca classificamos uma falha como segura para rollback cego.
        writes_exist = True
        runtime_result = _start_write_enabled(repository, runtime, canonical)
        runtime_result["technical_persistence"] = _technical_persistence_after_shutdown(canonical)
        postwrite_checksum = sha256_file(canonical)
        validation = _sqlite_validate(canonical)
        if _sidecars(canonical):
            raise RuntimeError("sidecar permaneceu apos checkpoint")

        backup_dir = runtime / "backups" / execution
        lock = acquire_maintenance_lock(
            runtime / "maintenance.lock", execution, databases=(canonical,)
        )
        try:
            backup_manifest = create_final_backup(
                {"canonical_generation_2": canonical}, backup_dir,
                execution_reference=execution, lock=lock,
            )
        finally:
            lock.release()
        backup_checksum = sha256_file(backup_manifest)
        restore = evidence_dir / "canonical-backup-restore-validation.db"
        shutil.copyfile(backup_dir / "canonical_generation_2.backup.db", restore)
        restore_validation = _sqlite_validate(restore)
        if sha256_file(restore) != postwrite_checksum:
            raise RuntimeError("restore isolado diverge do backup canonico")
        provenance = backup_dir / "canonical-backup-provenance.json"
        provenance_checksum = _atomic_create(provenance, _json_bytes({
            "format_version": "1.0", "execution_reference": execution,
            "generation": 2, "pointer_checksum_sha256": pointer.checksum,
            "canonical_initial_checksum_sha256": initial["sha256"],
            "canonical_backup_checksum_sha256": postwrite_checksum,
            "backup_manifest_checksum_sha256": backup_checksum,
            "rollback_boundary_checksum_sha256": sha256_file(boundary_path),
            "privacy_safe": True,
        }))
        samples = []
        for _ in range(3):
            sample_validation = _sqlite_validate(canonical)
            samples.append({"sha256": sha256_file(canonical), **sample_validation})
        if any(sample["sha256"] != postwrite_checksum for sample in samples):
            raise RuntimeError("generation 2 mudou durante monitoramento")
        result = {
            "format_version": "1.0", "result": "STABILIZATION_PASS",
            "execution_reference": execution, "generation": 2,
            "pointer_checksum_sha256": pointer.checksum,
            "canonical_initial": initial,
            "canonical_postwrite_checksum_sha256": postwrite_checksum,
            "new_canonical_writes_exist": True,
            "runtime": runtime_result, "sqlite": validation,
            "sidecars_pending": _sidecars(canonical),
            "backup_manifest": str(backup_manifest),
            "backup_manifest_checksum_sha256": backup_checksum,
            "backup_database_checksum_sha256": postwrite_checksum,
            "backup_provenance": str(provenance),
            "backup_provenance_checksum_sha256": provenance_checksum,
            "restore_path": str(restore), "restore": restore_validation,
            "rollback_boundary": "NO_SILENT_POINTER_ROLLBACK",
            "monitoring_samples": samples,
            "generation_1_checksum_sha256": sha256_file(runtime / "generations" / "generation-0001-d0123c58c57f.db"),
            "precutover_backup_manifest_checksum_sha256": sha256_file(runtime / "backups" / "spec008-phase10-20260915T004517Z" / "final-backup-manifest.json"),
            "privacy_safe": True,
        }
    except Exception as exc:
        result = {
            "format_version": "1.0",
            "result": "STABILIZATION_REVIEW_REQUIRED" if writes_exist else "STABILIZATION_BLOCKED",
            "execution_reference": execution,
            "new_canonical_writes_exist": writes_exist,
            "rollback_boundary": "NO_SILENT_POINTER_ROLLBACK" if writes_exist else "PRE_WRITE",
            "failure_type": type(exc).__name__, "failure_message": str(exc),
            "canonical_preserved": True, "privacy_safe": True,
        }
    evidence_path = evidence_dir / "stabilization-result.json"
    evidence_checksum = _atomic_create(evidence_path, _json_bytes(result))
    return {**result, "evidence_path": str(evidence_path),
            "evidence_checksum_sha256": evidence_checksum}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.repository, args.runtime), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
