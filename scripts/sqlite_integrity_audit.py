"""Auditoria read-only e privacy-safe de integridade referencial SQLite."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from scripts.sqlite_inventory import (
        DEFAULT_BACKEND_DB,
        DEFAULT_DESKTOP_DB,
        _quote_identifier,
        _readonly_connection,
    )
except ModuleNotFoundError:  # Execucao direta: python scripts/sqlite_integrity_audit.py
    from sqlite_inventory import (  # type: ignore[no-redef]
        DEFAULT_BACKEND_DB,
        DEFAULT_DESKTOP_DB,
        _quote_identifier,
        _readonly_connection,
    )


def _table_names(connection) -> list[str]:
    return [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_schema "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def _table_columns(connection, table: str) -> list[dict[str, Any]]:
    quoted = _quote_identifier(table)
    return [dict(row) for row in connection.execute(f"PRAGMA table_xinfo({quoted})")]


def _foreign_keys(connection, tables: list[str]) -> list[dict[str, Any]]:
    relationships = []
    for child_table in tables:
        quoted_child = _quote_identifier(child_table)
        rows = [
            dict(row)
            for row in connection.execute(f"PRAGMA foreign_key_list({quoted_child})")
        ]
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["id"]].append(row)
        child_columns = {column["name"]: column for column in _table_columns(connection, child_table)}
        for foreign_key_id, parts in sorted(grouped.items()):
            parts.sort(key=lambda part: part["seq"])
            parent_table = parts[0]["table"]
            parent_pk = [
                column["name"]
                for column in sorted(
                    _table_columns(connection, parent_table), key=lambda column: column["pk"]
                )
                if column["pk"]
            ]
            parent_columns = [
                part["to"] if part["to"] is not None else parent_pk[index]
                for index, part in enumerate(parts)
            ]
            source_columns = [part["from"] for part in parts]
            relationships.append(
                {
                    "child_table": child_table,
                    "foreign_key_schema_id": foreign_key_id,
                    "child_columns": source_columns,
                    "parent_table": parent_table,
                    "parent_columns": parent_columns,
                    "on_update": parts[0]["on_update"],
                    "on_delete": parts[0]["on_delete"],
                    "null_allowed_by_schema": any(
                        not bool(child_columns[column]["notnull"]) for column in source_columns
                    ),
                }
            )
    return relationships


def _relationship_counts(connection, relationship: dict[str, Any]) -> dict[str, int]:
    child_table = _quote_identifier(relationship["child_table"])
    parent_table = _quote_identifier(relationship["parent_table"])
    child_columns = relationship["child_columns"]
    parent_columns = relationship["parent_columns"]
    null_predicate = " OR ".join(
        f"child.{_quote_identifier(column)} IS NULL" for column in child_columns
    )
    non_null_predicate = " AND ".join(
        f"child.{_quote_identifier(column)} IS NOT NULL" for column in child_columns
    )
    join_predicate = " AND ".join(
        f"parent.{_quote_identifier(parent)} = child.{_quote_identifier(child)}"
        for child, parent in zip(child_columns, parent_columns)
    )
    total = connection.execute(f"SELECT COUNT(*) FROM {child_table}").fetchone()[0]
    null_references = connection.execute(
        f"SELECT COUNT(*) FROM {child_table} AS child WHERE {null_predicate}"
    ).fetchone()[0]
    valid_references = connection.execute(
        f"SELECT COUNT(*) FROM {child_table} AS child "
        f"WHERE {non_null_predicate} AND EXISTS ("
        f"SELECT 1 FROM {parent_table} AS parent WHERE {join_predicate})"
    ).fetchone()[0]
    non_null_references = total - null_references
    return {
        "total_child_records": total,
        "null_references": null_references,
        "non_null_references": non_null_references,
        "valid_references": valid_references,
        "orphan_references": non_null_references - valid_references,
    }


def audit_database(path: str | Path) -> dict[str, Any]:
    requested = Path(path).expanduser()
    absolute = requested.resolve(strict=False)
    result: dict[str, Any] = {
        "path": str(absolute),
        "exists": absolute.is_file(),
        "status": "missing" if not absolute.is_file() else "pending",
        "relationships": [],
        "summary": {
            "relationship_count": 0,
            "total_null_references": 0,
            "total_valid_references": 0,
            "total_orphan_references": 0,
            "foreign_key_check_violations": 0,
        },
        "foreign_key_check": {"violation_count": 0, "by_relationship": []},
    }
    if not result["exists"]:
        return result

    with _readonly_connection(absolute) as connection:
        tables = _table_names(connection)
        relationships = _foreign_keys(connection, tables)
        check_counts = Counter(
            (row[0], row[3]) for row in connection.execute("PRAGMA foreign_key_check")
        )
        for relationship in relationships:
            counts = _relationship_counts(connection, relationship)
            check_count = check_counts.get(
                (relationship["child_table"], relationship["foreign_key_schema_id"]), 0
            )
            result["relationships"].append(
                {**relationship, **counts, "foreign_key_check_violations": check_count}
            )
        result["foreign_key_check"] = {
            "violation_count": sum(check_counts.values()),
            "by_relationship": [
                {
                    "child_table": relationship["child_table"],
                    "foreign_key_schema_id": relationship["foreign_key_schema_id"],
                    "parent_table": relationship["parent_table"],
                    "violation_count": relationship["foreign_key_check_violations"],
                }
                for relationship in result["relationships"]
                if relationship["foreign_key_check_violations"]
            ],
        }
        result["summary"] = {
            "relationship_count": len(relationships),
            "total_null_references": sum(item["null_references"] for item in result["relationships"]),
            "total_valid_references": sum(item["valid_references"] for item in result["relationships"]),
            "total_orphan_references": sum(item["orphan_references"] for item in result["relationships"]),
            "foreign_key_check_violations": sum(check_counts.values()),
        }
        result["query_only"] = bool(connection.execute("PRAGMA query_only").fetchone()[0])
        result["status"] = "completed_read_only"
    return result


def build_report(desktop_path: str | Path, backend_path: str | Path) -> dict[str, Any]:
    return {
        "privacy": {
            "record_values_included": False,
            "primary_or_foreign_key_values_included": False,
            "fingerprints_included": False,
        },
        "desktop": audit_database(desktop_path),
        "backend": audit_database(backend_path),
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
