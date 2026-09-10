"""Inventario estrutural, estritamente read-only, de bancos SQLite.

O modulo nao importa os runtimes SQLAlchemy da aplicacao para evitar qualquer
inicializacao, migration ou seed acidental.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESKTOP_DB = PROJECT_ROOT / "data" / "clinica_psicologia.db"
DEFAULT_BACKEND_DB = PROJECT_ROOT / "backend" / "data" / "clinica_api.db"

_DENIED_ACTIONS = {
    getattr(sqlite3, name)
    for name in (
        "SQLITE_CREATE_INDEX", "SQLITE_CREATE_TABLE", "SQLITE_CREATE_TEMP_INDEX",
        "SQLITE_CREATE_TEMP_TABLE", "SQLITE_CREATE_TEMP_TRIGGER",
        "SQLITE_CREATE_TEMP_VIEW", "SQLITE_CREATE_TRIGGER", "SQLITE_CREATE_VIEW",
        "SQLITE_DELETE", "SQLITE_DROP_INDEX", "SQLITE_DROP_TABLE",
        "SQLITE_DROP_TEMP_INDEX", "SQLITE_DROP_TEMP_TABLE",
        "SQLITE_DROP_TEMP_TRIGGER", "SQLITE_DROP_TEMP_VIEW", "SQLITE_DROP_TRIGGER",
        "SQLITE_DROP_VIEW", "SQLITE_INSERT", "SQLITE_REINDEX", "SQLITE_UPDATE",
        "SQLITE_ALTER_TABLE", "SQLITE_CREATE_VTABLE", "SQLITE_DROP_VTABLE",
        "SQLITE_ATTACH", "SQLITE_DETACH", "SQLITE_TRANSACTION", "SQLITE_SAVEPOINT",
    )
    if hasattr(sqlite3, name)
}


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _readonly_connection(path: Path) -> sqlite3.Connection:
    resolved = path.expanduser().resolve(strict=True)
    uri_path = quote(resolved.as_posix(), safe="/:")
    connection = sqlite3.connect(f"file:{uri_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.set_authorizer(
        lambda action, _arg1, _arg2, _database, _source: (
            sqlite3.SQLITE_DENY if action in _DENIED_ACTIONS else sqlite3.SQLITE_OK
        )
    )
    return connection


def _rows(connection: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(sql).fetchall()]


def _unique_definitions(indexes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"name": index["name"], "columns": index["columns"], "origin": index["origin"]}
        for index in indexes
        if index["unique"]
    ]


def inventory_database(path: str | Path) -> dict[str, Any]:
    """Coleta somente metadados, agregados e faixas de IDs de um SQLite."""
    requested = Path(path).expanduser()
    absolute = requested.resolve(strict=False)
    result: dict[str, Any] = {
        "path": str(absolute),
        "exists": absolute.is_file(),
        "size_bytes": absolute.stat().st_size if absolute.is_file() else None,
        "database": {},
        "tables": {},
    }
    if not result["exists"]:
        return result

    with _readonly_connection(absolute) as connection:
        result["database"] = {
            "sqlite_version": sqlite3.sqlite_version,
            "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
            "application_id": connection.execute("PRAGMA application_id").fetchone()[0],
            "encoding": connection.execute("PRAGMA encoding").fetchone()[0],
            "page_size": connection.execute("PRAGMA page_size").fetchone()[0],
            "page_count": connection.execute("PRAGMA page_count").fetchone()[0],
            "foreign_keys_enabled": bool(connection.execute("PRAGMA foreign_keys").fetchone()[0]),
            "query_only": bool(connection.execute("PRAGMA query_only").fetchone()[0]),
        }
        table_names = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for table_name in table_names:
            quoted = _quote_identifier(table_name)
            columns = _rows(connection, f"PRAGMA table_xinfo({quoted})")
            foreign_keys = _rows(connection, f"PRAGMA foreign_key_list({quoted})")
            raw_indexes = _rows(connection, f"PRAGMA index_list({quoted})")
            indexes = []
            for index in raw_indexes:
                index_name = index["name"]
                index_columns = [
                    row["name"]
                    for row in _rows(
                        connection, f"PRAGMA index_xinfo({_quote_identifier(index_name)})"
                    )
                    if row["key"] and row["name"] is not None
                ]
                indexes.append(
                    {
                        "name": index_name,
                        "unique": bool(index["unique"]),
                        "origin": index["origin"],
                        "partial": bool(index["partial"]),
                        "columns": index_columns,
                    }
                )
            primary_key = [
                column["name"]
                for column in sorted(columns, key=lambda item: item["pk"])
                if column["pk"]
            ]
            id_columns = [
                column["name"]
                for column in columns
                if column["pk"] and "INT" in (column["type"] or "").upper()
            ]
            id_ranges = {}
            for column_name in id_columns:
                quoted_column = _quote_identifier(column_name)
                minimum, maximum = connection.execute(
                    f"SELECT MIN({quoted_column}), MAX({quoted_column}) FROM {quoted}"
                ).fetchone()
                id_ranges[column_name] = {"min": minimum, "max": maximum}
            result["tables"][table_name] = {
                "columns": columns,
                "primary_key": primary_key,
                "foreign_keys": foreign_keys,
                "indexes": indexes,
                "unique_constraints": _unique_definitions(indexes),
                "row_count": connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0],
                "id_ranges": id_ranges,
                "indicators": {
                    "without_rowid": bool(
                        connection.execute(
                            "SELECT instr(upper(sql), 'WITHOUT ROWID') > 0 "
                            "FROM sqlite_schema WHERE type='table' AND name=?",
                            (table_name,),
                        ).fetchone()[0]
                    ),
                    "composite_primary_key": len(primary_key) > 1,
                    "foreign_key_count": len(foreign_keys),
                    "index_count": len(indexes),
                },
            }
    return result


def _column_signature(column: dict[str, Any]) -> tuple[Any, ...]:
    return (
        column["name"], column["type"], bool(column["notnull"]), column["dflt_value"],
        column["pk"], column["hidden"],
    )


def _constraint_signature(table: dict[str, Any]) -> dict[str, Any]:
    return {
        "primary_key": table["primary_key"],
        "foreign_keys": sorted(
            (fk["from"], fk["table"], fk["to"], fk["on_update"], fk["on_delete"])
            for fk in table["foreign_keys"]
        ),
        "unique_columns": sorted(tuple(item["columns"]) for item in table["unique_constraints"]),
    }


def compare_inventories(desktop: dict[str, Any], backend: dict[str, Any]) -> dict[str, Any]:
    desktop_tables = set(desktop["tables"])
    backend_tables = set(backend["tables"])
    shared = sorted(desktop_tables & backend_tables)
    schema_differences = {}
    constraint_differences = {}
    count_differences = {}
    id_range_conflicts = {}
    for name in shared:
        left = desktop["tables"][name]
        right = backend["tables"][name]
        left_columns = [_column_signature(column) for column in left["columns"]]
        right_columns = [_column_signature(column) for column in right["columns"]]
        if left_columns != right_columns:
            schema_differences[name] = {"desktop": left_columns, "backend": right_columns}
        left_constraints = _constraint_signature(left)
        right_constraints = _constraint_signature(right)
        if left_constraints != right_constraints:
            constraint_differences[name] = {
                "desktop": left_constraints, "backend": right_constraints,
            }
        if left["row_count"] != right["row_count"]:
            count_differences[name] = {
                "desktop": left["row_count"], "backend": right["row_count"],
                "delta_backend_minus_desktop": right["row_count"] - left["row_count"],
            }
        for column in sorted(set(left["id_ranges"]) & set(right["id_ranges"])):
            l_range = left["id_ranges"][column]
            r_range = right["id_ranges"][column]
            if None not in (l_range["min"], l_range["max"], r_range["min"], r_range["max"]):
                overlap = max(l_range["min"], r_range["min"]) <= min(l_range["max"], r_range["max"])
                if overlap:
                    id_range_conflicts[f"{name}.{column}"] = {
                        "desktop": l_range, "backend": r_range,
                        "overlap": True,
                        "note": "Faixas sobrepostas; identidade dos registros nao foi inspecionada.",
                    }
    history_signals = []
    if desktop.get("database", {}).get("user_version") != backend.get("database", {}).get("user_version"):
        history_signals.append("user_version divergente")
    if schema_differences or constraint_differences:
        history_signals.append("estrutura divergente")
    if count_differences:
        history_signals.append("contagens divergentes")
    if id_range_conflicts:
        history_signals.append("faixas de IDs sobrepostas")
    return {
        "tables_in_both": shared,
        "desktop_only_tables": sorted(desktop_tables - backend_tables),
        "backend_only_tables": sorted(backend_tables - desktop_tables),
        "schema_differences": schema_differences,
        "constraint_differences": constraint_differences,
        "count_differences": count_differences,
        "possible_id_range_conflicts": id_range_conflicts,
        "divergent_history_signals": history_signals,
    }


def build_report(desktop_path: str | Path, backend_path: str | Path) -> dict[str, Any]:
    desktop = inventory_database(desktop_path)
    backend = inventory_database(backend_path)
    return {
        "desktop": desktop,
        "backend": backend,
        "comparison": compare_inventories(desktop, backend),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desktop", type=Path, default=DEFAULT_DESKTOP_DB)
    parser.add_argument("--backend", type=Path, default=DEFAULT_BACKEND_DB)
    args = parser.parse_args()
    print(json.dumps(build_report(args.desktop, args.backend), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
