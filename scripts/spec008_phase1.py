"""Executa a Fase 1 da SPEC-008 sem alterar os bancos historicos."""

from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from backend.migration.manifests import ExecutionManifest, ExecutionStatus, SourceDatabase
from backend.migration.snapshot import create_sqlite_snapshot, validate_sqlite_snapshot
from backend.migration.storage import save_manifest
from scripts.sqlite_inventory import _readonly_connection, inventory_database


def _restore_test(snapshot: Path, destination: Path) -> None:
    try:
        with closing(_readonly_connection(snapshot)) as origin, closing(
            sqlite3.connect(destination)
        ) as target:
            origin.backup(target)
        snapshot_inventory = inventory_database(snapshot)
        restored_inventory = inventory_database(destination)
        comparable_snapshot = {
            "database": snapshot_inventory["database"],
            "tables": snapshot_inventory["tables"],
        }
        comparable_restore = {
            "database": restored_inventory["database"],
            "tables": restored_inventory["tables"],
        }
        if comparable_snapshot != comparable_restore:
            raise RuntimeError("inventario restaurado diverge do snapshot")
        with closing(_readonly_connection(destination)) as connection:
            integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
            violations = sum(1 for _ in connection.execute("PRAGMA foreign_key_check"))
        if integrity != ["ok"] or violations:
            raise RuntimeError("restauracao isolada nao passou na integridade")
    finally:
        destination.unlink(missing_ok=True)


def run_phase1(repository: Path, artifact_root: Path, execution_id: str) -> dict:
    repository = repository.resolve()
    artifact_root = artifact_root.resolve()
    if artifact_root == repository or repository in artifact_root.parents:
        raise ValueError("artefatos devem ficar fora da pasta de instalacao")
    artifact_root.mkdir(parents=True, exist_ok=False)

    sources = (
        (
            SourceDatabase.DESKTOP_LEGACY,
            repository / "data" / "clinica_psicologia.db",
            f"{execution_id}-desktop",
        ),
        (
            SourceDatabase.BACKEND_LEGACY,
            repository / "backend" / "data" / "clinica_api.db",
            f"{execution_id}-backend",
        ),
    )
    snapshots = []
    evidence = []
    for source_label, source, reference in sources:
        snapshot_path = artifact_root / f"{source_label.value}.snapshot.db"
        snapshot = create_sqlite_snapshot(
            source,
            snapshot_path,
            source_label=source_label,
            snapshot_reference=reference,
        )
        manifest_checksum = save_manifest(
            artifact_root / f"{source_label.value}.snapshot-manifest.json",
            snapshot.manifest,
        )
        validate_sqlite_snapshot(snapshot_path, snapshot.manifest)
        _restore_test(snapshot_path, artifact_root / f"{source_label.value}.restore-test.db")
        snapshots.append(snapshot)
        evidence.append(
            {
                "source_label": source_label.value,
                "snapshot_reference": reference,
                "snapshot_checksum_sha256": snapshot.manifest.checksum_sha256,
                "manifest_checksum_sha256": manifest_checksum,
                "size_bytes": snapshot.manifest.size_bytes,
                "integrity": "passed",
                "foreign_key_violations": 0,
                "restore_test": "passed",
            }
        )

    execution = ExecutionManifest(
        execution_id=execution_id,
        created_at=datetime.now(timezone.utc),
        tool_version="spec008-foundation-2633612",
        plan_version="spec008-sections-52-54",
        rule_version="spec008-approved-policy-v1",
        status=ExecutionStatus.PLANNED,
        source_snapshot_references=tuple(
            snapshot.manifest.snapshot_reference for snapshot in snapshots
        ),
    )
    execution_checksum = save_manifest(
        artifact_root / "execution-manifest.json", execution
    )
    return {
        "execution_id": execution_id,
        "artifact_root": str(artifact_root),
        "snapshots": evidence,
        "execution_manifest_checksum_sha256": execution_checksum,
        "phase1_gate": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--execution-id", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            run_phase1(args.repository, args.artifact_root, args.execution_id),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
