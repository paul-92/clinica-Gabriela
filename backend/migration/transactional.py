"""Primitivas do migrador transacional das Fases 5--8 da SPEC-008."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from backend.migration.manifests import RemapLifecycle, RemapManifest

LOAD_ORDER = ("patients", "psychologists", "users", "clinic_settings", "expenses",
              "appointments", "clinical_records", "payments")


class TransactionalMigrationError(Exception):
    pass


@dataclass(frozen=True)
class ForeignKeySource:
    column: str
    source_table: str
    source_id: int | str | None
    nullable: bool = False


@dataclass(frozen=True)
class LoadRecord:
    source_database: str
    source_table: str
    source_id: int | str
    values: Mapping[str, Any]
    foreign_keys: tuple[ForeignKeySource, ...] = ()


def reserve_canonical_ids(manifest: RemapManifest) -> RemapManifest:
    """Reserva IDs reproduzíveis acima de todas as PKs históricas da tabela."""
    if manifest.lifecycle is not RemapLifecycle.APPROVED:
        raise TransactionalMigrationError("reserva exige manifest approved")
    maxima: dict[str, int] = {}
    for entry in manifest.entries:
        if isinstance(entry.source_id, int):
            maxima[entry.canonical_table] = max(maxima.get(entry.canonical_table, 0), entry.source_id)
    group_keys = {
        (entry.canonical_table, entry.canonical_group_ref or
         f"source:{entry.source_database.value}:{entry.source_table}:{entry.source_id}")
        for entry in manifest.entries
    }
    next_id = {table: maximum + 1 for table, maximum in maxima.items()}
    assigned: dict[tuple[str, str], int] = {}
    for table, group in sorted(group_keys):
        assigned[(table, group)] = next_id.get(table, 1)
        next_id[table] = assigned[(table, group)] + 1
    entries = tuple(entry.model_copy(update={"canonical_id": assigned[(
        entry.canonical_table,
        entry.canonical_group_ref or
        f"source:{entry.source_database.value}:{entry.source_table}:{entry.source_id}",
    )]}) for entry in manifest.entries)
    return manifest.transition_to(RemapLifecycle.RESERVED, entries=entries)


def load_in_global_transaction(connection: sqlite3.Connection, manifest: RemapManifest,
                               records: Iterable[LoadRecord]) -> dict[str, int]:
    """Carrega atomicamente e nunca procura ou infere FKs por dados de negócio."""
    if manifest.lifecycle is not RemapLifecycle.RESERVED:
        raise TransactionalMigrationError("carga exige manifest reserved")
    lookup = {(e.source_database.value, e.source_table, e.source_id):
              (e.canonical_table, e.canonical_id) for e in manifest.entries}
    grouped = {table: [] for table in LOAD_ORDER}
    for record in records:
        if record.source_table not in grouped:
            raise TransactionalMigrationError("tabela fora do contrato de carga")
        grouped[record.source_table].append(record)
    counts = {table: 0 for table in LOAD_ORDER}
    connection.execute("PRAGMA foreign_keys=ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise TransactionalMigrationError("foreign_keys nao habilitado")
    try:
        connection.execute("BEGIN IMMEDIATE")
        for table in LOAD_ORDER:
            for record in grouped[table]:
                mapped = lookup.get((record.source_database, record.source_table, record.source_id))
                if mapped is None or mapped[0] != table:
                    raise TransactionalMigrationError("registro ausente do mapa explicito")
                values = dict(record.values)
                values["id"] = mapped[1]
                for fk in record.foreign_keys:
                    if fk.source_id is None and fk.nullable:
                        values[fk.column] = None
                        continue
                    parent = lookup.get((record.source_database, fk.source_table, fk.source_id))
                    if parent is None:
                        raise TransactionalMigrationError("FK sem pai no mapa explicito")
                    values[fk.column] = parent[1]
                columns = tuple(values)
                quoted = ",".join(f'"{column}"' for column in columns)
                placeholders = ",".join("?" for _ in columns)
                connection.execute(f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})',
                                   tuple(values[column] for column in columns))
                counts[table] += 1
        if list(connection.execute("PRAGMA foreign_key_check")):
            raise TransactionalMigrationError("foreign_key_check falhou")
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise TransactionalMigrationError("integrity_check falhou")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return counts
