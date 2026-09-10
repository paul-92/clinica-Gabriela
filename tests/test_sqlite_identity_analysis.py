import json
import sqlite3
from pathlib import Path

import pytest

from scripts.sqlite_identity_analysis import analyze_identity
from scripts.sqlite_inventory import _readonly_connection


SCHEMA = """
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, username TEXT UNIQUE, password_hash TEXT);
CREATE TABLE patients (id INTEGER PRIMARY KEY, full_name TEXT, cpf TEXT UNIQUE, phone TEXT, notes TEXT);
CREATE TABLE psychologists (id INTEGER PRIMARY KEY, full_name TEXT, crp TEXT UNIQUE, email TEXT);
CREATE TABLE appointments (id INTEGER PRIMARY KEY, patient_id INTEGER, psychologist_id INTEGER,
 scheduled_at TEXT, notes TEXT, FOREIGN KEY(patient_id) REFERENCES patients(id),
 FOREIGN KEY(psychologist_id) REFERENCES psychologists(id));
CREATE TABLE clinic_settings (id INTEGER PRIMARY KEY, clinic_name TEXT, address TEXT);
"""


def _database(path: Path, statements: list[tuple[str, tuple]]) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        for sql, parameters in statements:
            connection.execute(sql, parameters)


def _fixtures(tmp_path: Path) -> tuple[Path, Path]:
    desktop, backend = tmp_path / "desktop.db", tmp_path / "backend.db"
    common = [
        ("INSERT INTO psychologists VALUES (?, ?, ?, ?)", (1, "Profissional Sigiloso", "CRP-100", "sigilo@example.test")),
    ]
    _database(desktop, common + [
        ("INSERT INTO users VALUES (?, ?, ?, ?)", (1, "Pessoa A", "mesmo", "HASH-SECRETO-A")),
        ("INSERT INTO users VALUES (?, ?, ?, ?)", (2, "Pessoa B", "desktop-conflito", "HASH-SECRETO-B")),
        ("INSERT INTO users VALUES (?, ?, ?, ?)", (3, "Pessoa C", "id-diferente", "HASH-SECRETO-C")),
        ("INSERT INTO users VALUES (?, ?, ?, ?)", (4, "Pessoa D", "somente-desktop", "HASH-SECRETO-D")),
        ("INSERT INTO patients VALUES (?, ?, ?, ?, ?)", (1, "Paciente Secreto", "111.222.333-44", "11999999999", "CONTEUDO CLINICO")),
        ("INSERT INTO appointments VALUES (?, ?, ?, ?, ?)", (1, 1, 1, "2026-01-01 10:00", "NOTA CLINICA")),
        ("INSERT INTO clinic_settings VALUES (?, ?, ?)", (1, "Clinica Secreta", "Endereco Secreto")),
    ])
    _database(backend, common + [
        ("INSERT INTO users VALUES (?, ?, ?, ?)", (1, "Pessoa A", "mesmo", "HASH-SECRETO-A")),
        ("INSERT INTO users VALUES (?, ?, ?, ?)", (2, "Pessoa X", "backend-conflito", "HASH-SECRETO-X")),
        ("INSERT INTO users VALUES (?, ?, ?, ?)", (30, "Pessoa C", "id-diferente", "HASH-SECRETO-C")),
        ("INSERT INTO users VALUES (?, ?, ?, ?)", (5, "Pessoa E", "somente-backend", "HASH-SECRETO-E")),
        ("INSERT INTO patients VALUES (?, ?, ?, ?, ?)", (9, "Paciente Secreto", "11122233344", "11999999999", "CONTEUDO CLINICO")),
        ("INSERT INTO appointments VALUES (?, ?, ?, ?, ?)", (8, 9, 1, "2026-01-01 10:00", "NOTA CLINICA")),
        ("INSERT INTO clinic_settings VALUES (?, ?, ?)", (1, "Outra Clinica", "Outro Endereco")),
    ])
    return desktop, backend


def test_classifications_and_fk_matching(tmp_path):
    desktop, backend = _fixtures(tmp_path)
    report = analyze_identity(desktop, backend)

    users = report["tables"]["users"]
    assert users["same_id"] == 2
    assert users["probable_same_entity"] == 2
    assert users["conflicts"] == 1
    assert users["desktop_only"] == 1
    assert users["backend_only"] == 1
    assert users["pk_collisions"] == 1
    assert users["equivalent_with_different_ids"] == 1
    assert users["same_id_same_identity"] == 1
    assert users["same_id_different_identity"] == 1
    assert users["same_identity_different_id"] == 1
    assert users["same_id_different_identity"] == users["pk_collisions"]
    assert users["same_identity_different_id"] == users["equivalent_with_different_ids"]
    assert users["probable_same_entity"] == (
        users["same_id_same_identity"] + users["same_identity_different_id"]
    )
    assert report["metric_semantics"]["orthogonality"] == (
        "correspondencias por identidade e colisoes de PK sao eixos independentes"
    )
    assert report["tables"]["clinic_settings"]["inconclusive"] == 1
    assert report["tables"]["appointments"]["probable_same_entity"] == 1
    assert report["tables"]["appointments"]["equivalent_with_different_ids"] == 1
    assert report["tables"]["appointments"]["relevant_foreign_keys"]


def test_report_never_contains_pii_secrets_or_fingerprints(tmp_path):
    desktop, backend = _fixtures(tmp_path)
    serialized = json.dumps(analyze_identity(desktop, backend), ensure_ascii=False)
    forbidden = [
        "Paciente Secreto", "111.222.333-44", "11122233344", "11999999999",
        "sigilo@example.test", "Endereco Secreto", "CONTEUDO CLINICO",
        "NOTA CLINICA", "HASH-SECRETO", "id-diferente", "desktop-conflito",
    ]
    assert all(value not in serialized for value in forbidden)
    assert report_has_no_hash_like_values(json.loads(serialized))


def report_has_no_hash_like_values(value):
    if isinstance(value, dict):
        return all(report_has_no_hash_like_values(item) for item in value.values())
    if isinstance(value, list):
        return all(report_has_no_hash_like_values(item) for item in value)
    return not (isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value))


def test_read_only_and_missing_database_safety(tmp_path):
    desktop, backend = _fixtures(tmp_path)
    before = (desktop.stat().st_mtime_ns, backend.stat().st_mtime_ns)
    analyze_identity(desktop, backend)
    assert before == (desktop.stat().st_mtime_ns, backend.stat().st_mtime_ns)
    with _readonly_connection(desktop) as connection:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("UPDATE users SET username='forbidden'")

    missing = tmp_path / "missing.db"
    report = analyze_identity(desktop, missing)
    assert report["status"] == "incomplete_missing_database"
    assert not missing.exists()
