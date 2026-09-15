"""Executa as Fases 5--8 sobre o pacote protegido, sem cutover."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from backend.migration.manifests import (
    HistoricalProvenanceSupplement, RemapLifecycle, RemapManifest, SnapshotManifest,
    canonical_json,
)
from backend.migration.snapshot import validate_sqlite_snapshot
from backend.migration.storage import load_stored_manifest, save_manifest
from backend.migration.transactional import (
    ForeignKeySource, LoadRecord, load_in_global_transaction, reserve_canonical_ids,
)

SCHEMA_VERSION = "backend-models-v2-credential-reset"
DISABLED_CREDENTIAL = "!DISABLED_CREDENTIAL:v1!"
FK_COLUMNS = {
    "appointments": (("patient_id", "patients", False), ("psychologist_id", "psychologists", False)),
    "clinical_records": (("patient_id", "patients", False), ("psychologist_id", "psychologists", False)),
    "payments": (("patient_id", "patients", False), ("appointment_id", "appointments", True)),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _save_json(path: Path, payload: dict) -> str:
    data = _json_bytes(payload)
    path.open("xb").write(data)
    return hashlib.sha256(data).hexdigest()


def _source_connections(root: Path):
    result = {}
    for label in ("desktop_legacy", "backend_legacy"):
        uri = "file:" + (root / f"{label}.snapshot.db").as_posix() + "?mode=ro&immutable=1"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        result[label] = connection
    return result


def _records(root: Path, reserved: RemapManifest) -> tuple[LoadRecord, ...]:
    sources = _source_connections(root)
    try:
        rows = {}
        for entry in reserved.entries:
            row = sources[entry.source_database.value].execute(
                f'SELECT * FROM "{entry.source_table}" WHERE id=?', (entry.source_id,)
            ).fetchone()
            if row is None:
                raise RuntimeError("entrada aprovada ausente do snapshot")
            rows[entry.logical_key] = dict(row)
        groups = defaultdict(list)
        for entry in reserved.entries:
            groups[(entry.canonical_table, entry.canonical_id)].append(entry)
        records = []
        for (table, _), entries in sorted(groups.items()):
            entries.sort(key=lambda e: (e.source_database.value, str(e.source_id)))
            representative = entries[0]
            candidates = [rows[e.logical_key] for e in entries]
            ignored = {"id", "created_at", "password_hash", "password_reset_required"}
            ignored.update(column for column, _, _ in FK_COLUMNS.get(table, ()))
            common = set.intersection(*(set(row) for row in candidates)) - ignored
            if any(len({str(row[column]) for row in candidates}) != 1 for column in common):
                raise RuntimeError("grupo equivalente possui divergencia nao congelada")
            values = {column: candidates[0][column] for column in common}
            if "created_at" in set.union(*(set(row) for row in candidates)):
                timestamps = [row.get("created_at") for row in candidates if row.get("created_at")]
                if timestamps:
                    values["created_at"] = min(timestamps)
            if table == "users":
                values["password_hash"] = DISABLED_CREDENTIAL
                values["password_reset_required"] = 1
            fks = tuple(
                ForeignKeySource(column, parent, candidates[0].get(column), nullable)
                for column, parent, nullable in FK_COLUMNS.get(table, ())
            )
            records.append(LoadRecord(
                representative.source_database.value, table, representative.source_id, values, fks
            ))
        return tuple(records)
    finally:
        for connection in sources.values():
            connection.close()


def run(root: Path) -> dict:
    root = root.resolve(strict=True)
    freeze = json.loads((root / "reconciliation-freeze-manifest-v7.json").read_text(encoding="utf-8"))
    if freeze["schema_version"] != SCHEMA_VERSION or freeze["cutover_authorized"]:
        raise RuntimeError("freeze-v7 incompativel")
    for label in ("desktop_legacy", "backend_legacy"):
        manifest = load_stored_manifest(root / f"{label}.snapshot-manifest.json", SnapshotManifest)
        validate_sqlite_snapshot(root / f"{label}.snapshot.db", manifest)
    approved_path = root / "remap-manifest-approved-schema-v2.json"
    approved = load_stored_manifest(approved_path, RemapManifest)
    supplement = load_stored_manifest(root / "historical-provenance-created-at-v1.json", HistoricalProvenanceSupplement)
    if approved.lifecycle is not RemapLifecycle.APPROVED or supplement.remap_checksum_sha256 != _sha256(approved_path):
        raise RuntimeError("remap/supplement incompativel")
    reserved = reserve_canonical_ids(approved).model_copy(update={"manifest_version": approved.manifest_version + "-reserved-v1"})
    reserved_path = root / "remap-manifest-reserved-v1.json"
    reserved_checksum = save_manifest(reserved_path, reserved)
    records = _records(root, reserved)
    candidate = root / "canonical-candidate-v1.db"
    connection = sqlite3.connect(candidate)
    try:
        counts = load_in_global_transaction(connection, reserved, records)
    finally:
        connection.close()
    consumed = reserved.transition_to(RemapLifecycle.CONSUMED).model_copy(
        update={"manifest_version": approved.manifest_version + "-consumed-v1"}
    )
    consumed_checksum = save_manifest(root / "remap-manifest-consumed-v1.json", consumed)
    ro = sqlite3.connect("file:" + candidate.as_posix() + "?mode=ro", uri=True)
    try:
        observed = {table: ro.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in counts}
        fk_violations = len(list(ro.execute("PRAGMA foreign_key_check")))
        integrity = ro.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        ro.close()
    if observed != counts or fk_violations or integrity != "ok":
        raise RuntimeError("validacao final falhou")
    validation = {
        "format_version": "1.0", "execution_reference": "spec008-20260911-phase1-001",
        "scope": "spec008-phases-4-8-no-cutover", "freeze_reference": freeze["freeze_reference"],
        "schema_version": SCHEMA_VERSION, "phases": [5, 6, 7, 8], "gate": "PASS",
        "counts": counts, "foreign_key_violations": 0, "integrity_check": "passed",
        "reserved_manifest_checksum_sha256": reserved_checksum,
        "consumed_manifest_checksum_sha256": consumed_checksum, "cutover_authorized": False,
    }
    validation_checksum = _save_json(root / "phase5-8-validation-report-v1.json", validation)
    verified = consumed.transition_to(RemapLifecycle.VERIFIED).model_copy(
        update={"manifest_version": approved.manifest_version + "-verified-v1"}
    )
    verified_checksum = save_manifest(root / "remap-manifest-verified-v1.json", verified)
    return {"gate": "PASS", "counts": counts, "validation_checksum_sha256": validation_checksum,
            "verified_manifest_checksum_sha256": verified_checksum, "cutover": "NOT_AUTHORIZED"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    print(json.dumps(run(parser.parse_args().artifact_root), sort_keys=True))


if __name__ == "__main__":
    main()
