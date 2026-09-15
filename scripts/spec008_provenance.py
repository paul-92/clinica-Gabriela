"""Gera o suplemento protegido de provenance temporal da SPEC-008."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from backend.migration.manifests import (
    HistoricalCreatedAtEntry,
    HistoricalProvenanceSupplement,
    RemapManifest,
    SourceDatabase,
)
from backend.migration.storage import load_stored_manifest, save_manifest


def _readonly(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{quote(path.resolve().as_posix(), safe='/:')}?mode=ro", uri=True)


def create_supplement(root: Path) -> str:
    root = root.resolve(strict=True)
    remap_path = root / "remap-manifest-approved-schema-v2.json"
    remap = load_stored_manifest(remap_path, RemapManifest)
    entries: list[HistoricalCreatedAtEntry] = []
    connections = {
        SourceDatabase.DESKTOP_LEGACY: _readonly(root / "desktop_legacy.snapshot.db"),
        SourceDatabase.BACKEND_LEGACY: _readonly(root / "backend_legacy.snapshot.db"),
    }
    try:
        for item in remap.entries:
            if item.source_table not in {"users", "patients", "psychologists"}:
                continue
            row = connections[item.source_database].execute(
                f'SELECT created_at FROM "{item.source_table}" WHERE id = ?',
                (item.source_id,),
            ).fetchone()
            if row is None:
                raise ValueError("entrada do remap ausente no snapshot")
            if row[0] is None:
                continue
            value = str(row[0])
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            entries.append(HistoricalCreatedAtEntry(
                source_database=item.source_database,
                source_table=item.source_table,
                source_id=item.source_id,
                created_at=value,
            ))
    finally:
        for connection in connections.values():
            connection.close()
    supplement = HistoricalProvenanceSupplement(
        supplement_version="spec008-20260911-phase1-001-created-at-v1",
        execution_reference="spec008-20260911-phase1-001",
        freeze_reference="spec008-20260911-phase1-001-freeze-v6",
        remap_version=remap.manifest_version,
        remap_checksum_sha256="342c95a796d4965fa9d46cb610a5f38af9e11c9524385b398fb0958b7956ef6d",
        entries=tuple(entries),
    )
    return save_manifest(root / "historical-provenance-created-at-v1.json", supplement)
