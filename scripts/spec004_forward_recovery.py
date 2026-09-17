"""Forward-only continuation after SPEC-004 switched to Generation 6."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.cutover.infrastructure import (
    OperationalPointer,
    _atomic_create,
    _canonical_bytes,
    acquire_maintenance_lock,
    atomic_swap_pointer,
    create_final_backup,
    read_pointer,
    sha256_file,
)
from scripts.spec004_operational_promotion import (
    CANDIDATE_DATABASE,
    DATABASE_SCHEMA_VERSION,
    SCHEMA_VERSION,
    _default_read_only_smoke,
    _validate_database,
    freeze,
)


GENERATION6_POINTER = "83651be4de74615ddc7d5858e9bc8b6a3ffc763cc7a4c72feeaab5abba3f5076"
GENERATION6_MANIFEST = "a35805987eba03127853164d9ddd90c71bc3ae25631b1237626f0b73979a7a08"


def run(repository: Path, runtime: Path) -> dict:
    repository = repository.resolve(strict=True)
    runtime = runtime.resolve(strict=True)
    pointer_path = runtime / "operational-pointer.json"
    if sha256_file(pointer_path) != GENERATION6_POINTER:
        raise RuntimeError("pointer Generation 6 diverge do recovery aprovado")
    current = read_pointer(pointer_path)
    database = Path(current.database_path).resolve(strict=True)
    if (current.generation != 6 or current.state != "canonical"
            or current.database_checksum_sha256 != CANDIDATE_DATABASE
            or current.runtime_manifest_checksum_sha256 != GENERATION6_MANIFEST):
        raise RuntimeError("envelope Generation 6 diverge")
    validation_before = _validate_database(database, CANDIDATE_DATABASE, 4)
    for suffix in ("-wal", "-shm", "-journal"):
        if Path(str(database) + suffix).exists():
            raise RuntimeError("sidecar impede forward recovery")
    manifest, manifest_checksum, runtime_commit = freeze(repository, runtime)
    execution = "spec004-forward-recovery-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_path = runtime / "evidence" / f"{execution}.json"
    backup_before = runtime / "backups" / f"{execution}-generation-6"
    lock = acquire_maintenance_lock(runtime / "maintenance.lock", execution,
                                    databases=(database,))
    switched = False
    try:
        backup_manifest = create_final_backup(
            {"generation_6": database}, backup_before,
            execution_reference=execution, lock=lock,
        )
        repaired = OperationalPointer(
            generation=7, state="canonical", database_path=str(database),
            database_checksum_sha256=CANDIDATE_DATABASE,
            schema_version=SCHEMA_VERSION,
            runtime_manifest_checksum_sha256=manifest_checksum,
            previous_pointer_checksum_sha256=GENERATION6_POINTER,
        )
        pointer_after = atomic_swap_pointer(
            pointer_path, repaired, expected_current_checksum=GENERATION6_POINTER,
            lock=lock, history_dir=runtime / "pointer-history",
        )
        switched = True
        smoke = _default_read_only_smoke(repository, runtime, database)
    except Exception:
        if switched:
            _atomic_create(evidence_path, _canonical_bytes({
                "format_version": "1.0-spec004", "result": "FORWARD_RECOVERY_POST_SWITCH_FAILURE",
                "execution_reference": execution, "policy": "NO_SILENT_POINTER_ROLLBACK",
                "privacy_safe": True,
            }))
        raise
    finally:
        lock.release()

    backup_after = runtime / "backups" / f"{execution}-generation-7-stabilized"
    stabilization_lock = acquire_maintenance_lock(
        runtime / "maintenance.lock", execution + "-stabilization", databases=(database,)
    )
    try:
        stabilized_manifest = create_final_backup(
            {"generation_7": database}, backup_after,
            execution_reference=execution + "-stabilization", lock=stabilization_lock,
        )
    finally:
        stabilization_lock.release()
    restore_dir = runtime / "evidence" / execution
    restore_dir.mkdir(parents=True, exist_ok=False)
    restore = restore_dir / "isolated-restore-validation.db"
    shutil.copyfile(backup_after / "generation_7.backup.db", restore)
    restore_validation = _validate_database(restore, CANDIDATE_DATABASE, 4)
    final_pointer = read_pointer(pointer_path)
    result = {
        "format_version": "1.0-spec004-forward-recovery",
        "result": "SPEC004_PROMOTION_STABILIZED",
        "execution_reference": execution,
        "runtime_integration_commit": runtime_commit,
        "database_schema_version": DATABASE_SCHEMA_VERSION,
        "generation_before": 6,
        "generation_after": final_pointer.generation,
        "pointer_before_sha256": GENERATION6_POINTER,
        "pointer_after_sha256": pointer_after,
        "runtime_manifest_sha256": manifest_checksum,
        "candidate_sha256": CANDIDATE_DATABASE,
        "validation_before": validation_before,
        "pre_recovery_backup_manifest_sha256": sha256_file(backup_manifest),
        "stabilized_backup_manifest_sha256": sha256_file(stabilized_manifest),
        "restore_sha256": sha256_file(restore),
        "restore_validation": restore_validation,
        "smoke": smoke,
        "rollback_policy": "NO_SILENT_POINTER_ROLLBACK",
        "privacy_safe": True,
    }
    checksum = _atomic_create(evidence_path, _canonical_bytes(result))
    return {**result, "evidence_path": str(evidence_path), "evidence_sha256": checksum}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.repository, args.runtime), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
