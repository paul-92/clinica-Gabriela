import json
import sqlite3
from pathlib import Path

import pytest

from scripts.sqlite_integrity_audit import audit_database, build_report
from scripts.sqlite_inventory import _readonly_connection


def _database(path: Path, *, orphan: bool) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                cpf TEXT NOT NULL
            );
            CREATE TABLE psychologists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER NOT NULL,
                psychologist_id INTEGER NOT NULL,
                previous_appointment_id INTEGER NULL,
                private_notes TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(id),
                FOREIGN KEY(psychologist_id) REFERENCES psychologists(id),
                FOREIGN KEY(previous_appointment_id) REFERENCES appointments(id)
            );
            """
        )
        connection.execute("INSERT INTO patients VALUES (1, 'PACIENTE-SECRETO', 'CPF-SECRETO')")
        connection.execute("INSERT INTO psychologists VALUES (10, 'PROFISSIONAL-SECRETO')")
        connection.execute(
            "INSERT INTO appointments VALUES (100, 1, 10, NULL, 'CONTEUDO-CLINICO-SECRETO')"
        )
        if orphan:
            connection.execute(
                "INSERT INTO appointments VALUES (101, 999, 888, 777, 'OUTRO-SEGREDO')"
            )


def test_valid_orphan_null_multiple_relations_and_foreign_key_check(tmp_path):
    database = tmp_path / "integrity.db"
    _database(database, orphan=True)

    report = audit_database(database)

    assert report["status"] == "completed_read_only"
    assert report["summary"]["relationship_count"] == 3
    assert report["summary"]["total_orphan_references"] == 3
    assert report["foreign_key_check"]["violation_count"] == 3
    assert len(report["foreign_key_check"]["by_relationship"]) == 3
    for relationship in report["relationships"]:
        assert (
            relationship["valid_references"]
            + relationship["orphan_references"]
            + relationship["null_references"]
            == relationship["total_child_records"]
        )
    optional = next(
        item for item in report["relationships"]
        if item["child_columns"] == ["previous_appointment_id"]
    )
    assert optional["null_allowed_by_schema"] is True
    assert optional["null_references"] == 1
    assert optional["orphan_references"] == 1


def test_database_without_violations(tmp_path):
    database = tmp_path / "valid.db"
    _database(database, orphan=False)
    report = audit_database(database)

    assert report["summary"]["total_orphan_references"] == 0
    assert report["foreign_key_check"]["violation_count"] == 0
    assert report["foreign_key_check"]["by_relationship"] == []


def test_report_is_privacy_safe_and_contains_no_record_ids(tmp_path):
    desktop, backend = tmp_path / "desktop.db", tmp_path / "backend.db"
    _database(desktop, orphan=True)
    _database(backend, orphan=False)
    serialized = json.dumps(build_report(desktop, backend), ensure_ascii=False)

    forbidden = [
        "PACIENTE-SECRETO", "CPF-SECRETO", "PROFISSIONAL-SECRETO",
        "CONTEUDO-CLINICO-SECRETO", "OUTRO-SEGREDO", "999", "888", "777",
        '"rowid"', '"primary_key_values"', '"foreign_key_values"',
    ]
    assert all(value not in serialized for value in forbidden)


def test_read_only_missing_database_and_timestamps(tmp_path):
    database = tmp_path / "readonly.db"
    _database(database, orphan=True)
    before = database.stat().st_mtime_ns
    audit_database(database)
    assert database.stat().st_mtime_ns == before

    with _readonly_connection(database) as connection:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("DELETE FROM appointments")

    missing = tmp_path / "missing.db"
    report = audit_database(missing)
    assert report["exists"] is False
    assert report["status"] == "missing"
    assert not missing.exists()
