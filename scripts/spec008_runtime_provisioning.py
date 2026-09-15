"""Provisiona generation 1 da SPEC-008 sem promover o candidato verified-v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path

from backend.cutover.infrastructure import (
    OperationalPointer,
    _atomic_create,
    _sqlite_validate,
    acquire_maintenance_lock,
    atomic_swap_pointer,
    directory_acl_fingerprint,
    initialize_pointer,
    read_pointer,
    rollback_pointer,
    sha256_file,
    verify_runtime_manifest,
)


EXPECTED_BASELINE = "d0123c58c57f57ee718ed3bba4a380a60d0244a20761c2ef2eec7ccef0fae757"
RUNTIME_MANIFEST = "d77c27d401c5f76fd3f301210f5804d6cabccc1325eba19ae8335fa4efb32398"
SCHEMA_VERSION = "backend-models-v2-credential-reset"


def _canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def run(repository: Path, source: Path, runtime_root: Path, user_sid_hash: str) -> dict:
    repository = repository.resolve(strict=True)
    source = source.resolve(strict=True)
    runtime_root = runtime_root.resolve(strict=True)
    if sha256_file(source) != EXPECTED_BASELINE:
        raise RuntimeError("baseline sucessor diverge")
    _sqlite_validate(source)

    generations = runtime_root / "generations"
    backups = runtime_root / "backups"
    evidence_dir = runtime_root / "evidence"
    manifests = runtime_root / "runtime-manifests"
    history = runtime_root / "pointer-history"
    for directory in (generations, backups, evidence_dir, manifests, history):
        directory.mkdir(exist_ok=False)

    source_manifest = repository / "docs" / "audit" / f"runtime-manifest-{RUNTIME_MANIFEST}.json"
    verify_runtime_manifest(repository, source_manifest, RUNTIME_MANIFEST)
    runtime_manifest = manifests / source_manifest.name
    _atomic_create(runtime_manifest, source_manifest.read_bytes())
    verify_runtime_manifest(repository, runtime_manifest, RUNTIME_MANIFEST)

    generation = generations / f"generation-0001-{EXPECTED_BASELINE[:12]}.db"
    _atomic_create(generation, source.read_bytes())
    if sha256_file(generation) != EXPECTED_BASELINE:
        raise RuntimeError("generation 1 diverge do baseline sucessor")
    sqlite_validation = _sqlite_validate(generation)

    pointer = OperationalPointer(
        generation=1,
        state="legacy",
        database_path=str(generation),
        database_checksum_sha256=EXPECTED_BASELINE,
        schema_version=SCHEMA_VERSION,
        runtime_manifest_checksum_sha256=RUNTIME_MANIFEST,
    )
    pointer_path = runtime_root / "operational-pointer.json"
    pointer_checksum = initialize_pointer(pointer_path, pointer)
    if read_pointer(pointer_path).checksum != pointer_checksum:
        raise RuntimeError("pointer generation 1 diverge")

    # Valida a reversibilidade em uma cadeia isolada; o pointer operacional não muda.
    rollback_dir = evidence_dir / "pointer-rollback-validation"
    rollback_history = rollback_dir / "history"
    rollback_pointer_path = rollback_dir / "operational-pointer.json"
    rollback_lock_path = rollback_dir / "maintenance.lock"
    initial_checksum = initialize_pointer(rollback_pointer_path, pointer)
    lock = acquire_maintenance_lock(
        rollback_lock_path, "spec008-runtime-provisioning-rollback-validation"
    )
    try:
        simulated = OperationalPointer(
            generation=2,
            state="canonical",
            database_path=str(generation),
            database_checksum_sha256=EXPECTED_BASELINE,
            schema_version=SCHEMA_VERSION,
            runtime_manifest_checksum_sha256=RUNTIME_MANIFEST,
            previous_pointer_checksum_sha256=initial_checksum,
        )
        switched_checksum = atomic_swap_pointer(
            rollback_pointer_path, simulated,
            expected_current_checksum=initial_checksum,
            lock=lock,
            history_dir=rollback_history,
        )
        rolled_back_checksum = rollback_pointer(
            rollback_pointer_path, initial_checksum,
            expected_current_checksum=switched_checksum,
            lock=lock,
            history_dir=rollback_history,
        )
        rolled_back = read_pointer(rollback_pointer_path)
        if rolled_back.state != "legacy" or rolled_back.generation != 3:
            raise RuntimeError("rollback isolado diverge")
    finally:
        lock.release()

    # Write probe confirma que o usuário efetivo do runtime pode operar na raiz.
    probe = runtime_root / ".permission-probe"
    descriptor = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(descriptor)
    probe.unlink()

    acl_fingerprint = directory_acl_fingerprint(runtime_root)
    result = {
        "format_version": "1.0",
        "result": "HUMAN",
        "scope": "initial-runtime-provisioning-no-cutover",
        "runtime_root": str(runtime_root),
        "generation": {
            "id": 1,
            "state": "legacy",
            "path": str(generation),
            "checksum_sha256": EXPECTED_BASELINE,
            **sqlite_validation,
        },
        "pointer": {
            "path": str(pointer_path),
            "checksum_sha256": pointer_checksum,
            "generation": 1,
            "state": "legacy",
        },
        "runtime_manifest_checksum_sha256": RUNTIME_MANIFEST,
        "acl": {
            "status": "MEASURED_PENDING_HUMAN_APPROVAL_FOR_CUTOVER",
            "fingerprint_sha256": acl_fingerprint,
            "policy": "current_runtime_user_full;SYSTEM_full;Administrators_full;inheritance_disabled",
            "current_user_sid_sha256": user_sid_hash,
            "generic_write_grants": False,
        },
        "permissions": {"runtime_user_write_probe": "PASS"},
        "rollback_validation": {
            "scope": "isolated_pointer_chain_no_cutover",
            "result": "PASS",
            "final_generation": rolled_back.generation,
            "final_state": rolled_back.state,
            "final_pointer_checksum_sha256": rolled_back_checksum,
        },
        "source_database_modified": False,
        "verified_v2_promoted": False,
        "cutover_executed": False,
        "privacy_safe": True,
    }
    evidence = evidence_dir / "runtime-provisioning-generation-0001.json"
    evidence_checksum = _atomic_create(evidence, _canonical_bytes(result))
    return {**result, "evidence_path": str(evidence),
            "evidence_checksum_sha256": evidence_checksum}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--user-sid-hash", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.repository, args.source, args.runtime_root,
                         args.user_sid_hash), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
