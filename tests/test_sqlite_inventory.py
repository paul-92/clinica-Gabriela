import json
import sqlite3
from pathlib import Path

import pytest

from scripts.sqlite_inventory import (
    _readonly_connection,
    build_report,
    inventory_database,
)


def _create_database(path: Path, *, extra_column: bool = False, rows: int = 1) -> None:
    with sqlite3.connect(path) as connection:
        suffix = ", legacy_code TEXT" if extra_column else ""
        connection.execute(
            f"CREATE TABLE patients (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE{suffix})"
        )
        connection.execute(
            "CREATE TABLE appointments ("
            "id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL, "
            "FOREIGN KEY(patient_id) REFERENCES patients(id))"
        )
        connection.execute("CREATE INDEX ix_appointments_patient ON appointments(patient_id)")
        for number in range(1, rows + 1):
            connection.execute(
                "INSERT INTO patients(id, name) VALUES (?, ?)",
                (number, f"SEGREDO-{number}"),
            )


def test_connection_is_really_read_only(tmp_path):
    database = tmp_path / "readonly.db"
    _create_database(database)
    with _readonly_connection(database) as connection:
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("INSERT INTO patients(id, name) VALUES (99, 'proibido')")
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("CREATE TABLE forbidden (id INTEGER)")


def test_missing_database_is_not_created(tmp_path):
    missing = tmp_path / "missing.db"
    report = inventory_database(missing)
    assert report["exists"] is False
    assert not missing.exists()


def test_report_does_not_contain_record_values(tmp_path):
    database = tmp_path / "privacy.db"
    _create_database(database)
    serialized = json.dumps(inventory_database(database), ensure_ascii=False)
    assert "SEGREDO-1" not in serialized
    assert '"row_count": 1' in serialized


def test_comparison_of_fictitious_databases(tmp_path):
    desktop = tmp_path / "desktop.db"
    backend = tmp_path / "backend.db"
    _create_database(desktop, extra_column=True, rows=2)
    _create_database(backend, rows=3)

    comparison = build_report(desktop, backend)["comparison"]

    assert comparison["tables_in_both"] == ["appointments", "patients"]
    assert "patients" in comparison["schema_differences"]
    assert comparison["count_differences"]["patients"] == {
        "desktop": 2,
        "backend": 3,
        "delta_backend_minus_desktop": 1,
    }
    assert comparison["possible_id_range_conflicts"]["patients.id"]["overlap"] is True
