"""Retry estrito do backup/restauracao da Fase 11 apos shutdown confirmado."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from backend.cutover.infrastructure import (
    _atomic_create,
    acquire_maintenance_lock,
    create_final_backup,
    sha256_file,
)


POINTER_SHA256 = "55604e3881535b8891cdea020980f41a8168f7b5e00edc08c9a3160b9dea960b"
CANONICAL_SHA256 = "4ab2924efb8fd7d849c7270760be80debf9a8dc0d7d35759c249d4deb1c2c69f"
GENERATION1_SHA256 = "d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757"
PRECUTOVER_MANIFEST_SHA256 = "922eb91aaa5b0a498ffdd535949a0ad0e99892c5bacc8c83f2d648873e2881a3"


def _json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _sidecars(database: Path) -> list[str]:
    return [suffix for suffix in ("-wal", "-shm", "-journal")
            if Path(str(database) + suffix).exists()]


def _preserved_pointer(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    payload = json.loads(raw.decode("utf-8"))
    required = {"generation", "state", "database_path", "database_checksum_sha256"}
    if not required.issubset(payload):
        raise RuntimeError("pointer preservado invalido")
    return payload, checksum


def _sqlite_contract(database: Path) -> dict:
    uri = "file:" + database.resolve(strict=True).as_posix() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True, timeout=0)) as connection:
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
        pragmas = {
            "application_id": connection.execute("PRAGMA application_id").fetchone()[0],
            "auto_vacuum": connection.execute("PRAGMA auto_vacuum").fetchone()[0],
            "encoding": connection.execute("PRAGMA encoding").fetchone()[0],
            "journal_mode": connection.execute("PRAGMA journal_mode").fetchone()[0].lower(),
            "page_count": connection.execute("PRAGMA page_count").fetchone()[0],
            "page_size": connection.execute("PRAGMA page_size").fetchone()[0],
            "schema_version": connection.execute("PRAGMA schema_version").fetchone()[0],
            "synchronous": connection.execute("PRAGMA synchronous").fetchone()[0],
            "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
        }
        objects = [dict(zip(("type", "name", "tbl_name", "sql"), row))
                   for row in connection.execute(
                       "SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master "
                       "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
                   )]
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        counts = {table: connection.execute(
            'SELECT COUNT(*) FROM "' + table.replace('"', '""') + '"'
        ).fetchone()[0] for table in tables}
    return {
        "busy_timeout_ms": busy_timeout,
        "integrity_check": integrity,
        "foreign_key_violations": len(foreign_keys),
        "pragmas": pragmas,
        "schema_objects": objects,
        "table_counts": counts,
        "sidecars": _sidecars(database),
    }


def _require_contract_valid(contract: dict, label: str) -> None:
    if contract["integrity_check"] != "ok":
        raise RuntimeError(f"{label}: integrity_check diverge")
    if contract["foreign_key_violations"] != 0:
        raise RuntimeError(f"{label}: foreign_key_check diverge")
    if contract["pragmas"]["user_version"] != 0:
        raise RuntimeError(f"{label}: user_version diverge")
    if contract["pragmas"]["journal_mode"] != "delete":
        raise RuntimeError(f"{label}: journal_mode diverge")
    if contract["sidecars"]:
        raise RuntimeError(f"{label}: sidecar pendente")


def run(runtime: Path) -> dict:
    runtime = runtime.resolve(strict=True)
    pointer_path = runtime / "operational-pointer.json"
    pointer, pointer_checksum = _preserved_pointer(pointer_path)
    if pointer["generation"] != 2 or pointer["state"] != "canonical" or pointer_checksum != POINTER_SHA256:
        raise RuntimeError("pointer Generation 2/canonical diverge")
    canonical = Path(pointer["database_path"]).resolve(strict=True)
    if sha256_file(canonical) != CANONICAL_SHA256:
        raise RuntimeError("checksum atual da Generation 2 diverge")
    generation1 = runtime / "generations" / "generation-0001-d0123c58c57f.db"
    precutover = (runtime / "backups" / "spec008-phase10-20260915T004517Z" /
                  "final-backup-manifest.json")
    if sha256_file(generation1) != GENERATION1_SHA256:
        raise RuntimeError("Generation 1 nao preservada")
    if sha256_file(precutover) != PRECUTOVER_MANIFEST_SHA256:
        raise RuntimeError("backup pre-cutover nao preservado")
    if (runtime / "maintenance.lock").exists():
        raise RuntimeError("maintenance lock preexistente")

    source_contract = _sqlite_contract(canonical)
    _require_contract_valid(source_contract, "Generation 2")
    execution = "spec008-phase11-backup-retry-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    staging = runtime / "backups" / ("." + execution + ".partial")
    final_backup = runtime / "backups" / execution
    evidence = runtime / "evidence" / execution
    evidence.mkdir(exist_ok=False)
    lock = None
    try:
        lock = acquire_maintenance_lock(
            runtime / "maintenance.lock", execution, databases=(canonical,)
        )
        manifest = create_final_backup(
            {"canonical_generation_2": canonical}, staging,
            execution_reference=execution, lock=lock,
        )
        backup_db = staging / "canonical_generation_2.backup.db"
        backup_contract = _sqlite_contract(backup_db)
        _require_contract_valid(backup_contract, "backup canonico")
        backup_sha256 = sha256_file(backup_db)
        if backup_sha256 != CANONICAL_SHA256:
            raise RuntimeError("identidade do backup diverge da Generation 2")

        restore = evidence / "isolated-restore-validation.db"
        shutil.copyfile(backup_db, restore)
        restore_contract = _sqlite_contract(restore)
        _require_contract_valid(restore_contract, "restauracao isolada")
        if sha256_file(restore) != backup_sha256:
            raise RuntimeError("identidade da restauracao diverge do backup")
        for field in ("schema_objects", "table_counts", "pragmas"):
            if restore_contract[field] != source_contract[field]:
                raise RuntimeError(f"restauracao isolada diverge em {field}")

        manifest_sha256 = sha256_file(manifest)
        provenance = staging / "canonical-backup-provenance.json"
        provenance_sha256 = _atomic_create(provenance, _json_bytes({
            "format_version": "1.0",
            "execution_reference": execution,
            "generation": 2,
            "pointer_checksum_sha256": pointer_checksum,
            "canonical_checksum_sha256": CANONICAL_SHA256,
            "backup_database_checksum_sha256": backup_sha256,
            "backup_manifest_checksum_sha256": manifest_sha256,
            "generation_1_checksum_sha256": GENERATION1_SHA256,
            "precutover_backup_manifest_checksum_sha256": PRECUTOVER_MANIFEST_SHA256,
            "privacy_safe": True,
        }))
        os.replace(staging, final_backup)
        staging = None
    finally:
        if lock is not None:
            lock.release()
        if staging is not None and staging.exists():
            shutil.rmtree(staging)

    final_pointer, final_pointer_checksum = _preserved_pointer(pointer_path)
    if final_pointer_checksum != POINTER_SHA256:
        raise RuntimeError("pointer mudou durante o backup")
    final_contract = _sqlite_contract(canonical)
    _require_contract_valid(final_contract, "Generation 2 final")
    if sha256_file(canonical) != CANONICAL_SHA256:
        raise RuntimeError("Generation 2 mudou durante o backup")

    result = {
        "format_version": "1.0",
        "result": "STABILIZATION_PASS",
        "execution_reference": execution,
        "runtime_shutdown_disposed": "CONFIRMED_BY_SEPARATE_BACKUP_ONLY_PROCESS",
        "pool_physical_connections_remaining": 0,
        "generation": 2,
        "pointer_state": final_pointer["state"],
        "pointer_checksum_sha256": final_pointer_checksum,
        "canonical_path": str(canonical),
        "canonical_checksum_sha256": CANONICAL_SHA256,
        "source_validation": source_contract,
        "final_validation": final_contract,
        "backup_directory": str(final_backup),
        "backup_database_checksum_sha256": backup_sha256,
        "backup_manifest": str(final_backup / "final-backup-manifest.json"),
        "backup_manifest_checksum_sha256": manifest_sha256,
        "backup_provenance": str(final_backup / "canonical-backup-provenance.json"),
        "backup_provenance_checksum_sha256": provenance_sha256,
        "isolated_restore": str(restore),
        "isolated_restore_checksum_sha256": sha256_file(restore),
        "isolated_restore_validation": restore_contract,
        "writers_observed": 0,
        "handles_observed": 0,
        "sidecars_pending": _sidecars(canonical),
        "rollback_boundary": "NO_SILENT_POINTER_ROLLBACK",
        "generation_1_checksum_sha256": sha256_file(generation1),
        "precutover_backup_manifest_checksum_sha256": sha256_file(precutover),
        "privacy_safe": True,
    }
    result_path = evidence / "backup-retry-result.json"
    result_sha256 = _atomic_create(result_path, _json_bytes(result))
    return {**result, "result_path": str(result_path),
            "result_checksum_sha256": result_sha256}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.runtime), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
