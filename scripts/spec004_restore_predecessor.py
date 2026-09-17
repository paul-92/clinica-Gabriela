"""One-purpose recovery for the interrupted SPEC-004 preflight incident."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.cutover.infrastructure import (
    _atomic_create,
    _atomic_replace,
    _canonical_bytes,
    _sqlite_validate,
    acquire_maintenance_lock,
    sha256_file,
)


EXPECTED_POINTER = "723a28330bce6ebd1821737675651c905f2c5a358cf96db4e8218a908fea65d7"
INCIDENT_DATABASE = "57bd4eb05100d7762c586180d5a6510c92cc0c58f56e52d3b09a1078236a4bee"
RESTORED_DATABASE = "143523964e8dd27eaaa612bbaa330a6523d2931b9889fe9443ca2e4e228bb506"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve(strict=True)
    backup = args.backup.resolve(strict=True)
    pointer_path = runtime / "operational-pointer.json"
    if sha256_file(pointer_path) != EXPECTED_POINTER:
        raise RuntimeError("pointer mudou; recovery recusado")
    payload = json.loads(pointer_path.read_text(encoding="utf-8"))
    database = Path(payload["database_path"]).resolve(strict=True)
    if sha256_file(database) != INCIDENT_DATABASE:
        raise RuntimeError("estado incidente da Generation 5 diverge")
    if sha256_file(backup) != RESTORED_DATABASE:
        raise RuntimeError("backup de recovery diverge do baseline aprovado")
    _sqlite_validate(backup)
    for suffix in ("-wal", "-shm", "-journal"):
        if Path(str(database) + suffix).exists():
            raise RuntimeError("sidecar impede recovery atomico")
    execution = "spec004-preflight-recovery-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lock = acquire_maintenance_lock(runtime / "maintenance.lock", execution, databases=(database,))
    try:
        lock.assert_held()
        _atomic_replace(database, backup.read_bytes())
    finally:
        lock.release()
    validation = _sqlite_validate(database)
    if sha256_file(database) != RESTORED_DATABASE or sha256_file(pointer_path) != EXPECTED_POINTER:
        raise RuntimeError("recovery nao restaurou o envelope aprovado")
    evidence = {
        "format_version": "1.0-spec004-recovery",
        "result": "PREDECESSOR_RESTORED",
        "execution_reference": execution,
        "incident_database_sha256": INCIDENT_DATABASE,
        "restored_database_sha256": RESTORED_DATABASE,
        "pointer_sha256": EXPECTED_POINTER,
        "validation": validation,
        "privacy_safe": True,
    }
    target = runtime / "evidence" / f"{execution}.json"
    checksum = _atomic_create(target, _canonical_bytes(evidence))
    print(json.dumps({**evidence, "evidence_path": str(target),
                      "evidence_sha256": checksum}, sort_keys=True))


if __name__ == "__main__":
    main()
