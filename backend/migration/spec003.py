"""Migration forward-only da SPEC-003; nunca executada automaticamente no startup."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


SPEC003_USER_VERSION = 3


class Spec003MigrationError(RuntimeError):
    pass


def _valid_cpf(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 11 or len(set(digits)) == 1:
        return 0
    for position in (9, 10):
        total = sum(int(digits[index]) * (position + 1 - index) for index in range(position))
        digit = (total * 10) % 11
        if digit == 10:
            digit = 0
        if digit != int(digits[position]):
            return 0
    return 1


def migrate_spec003(path: str | Path) -> None:
    """Migra uma cópia/candidata existente, preservando IDs e conteúdo."""
    database = Path(path).resolve(strict=True)
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=rw", uri=True)
    connection.create_function("is_valid_cpf", 1, _valid_cpf)
    try:
        if connection.execute("PRAGMA user_version").fetchone()[0] >= SPEC003_USER_VERSION:
            _validate(connection)
            return
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("BEGIN IMMEDIATE")
        _rebuild_patients(connection)
        _rebuild_psychologists(connection)
        _extend_appointments(connection)
        _extend_clinical_records(connection)
        _create_spec003_tables(connection)
        connection.execute(f"PRAGMA user_version={SPEC003_USER_VERSION}")
        if list(connection.execute("PRAGMA foreign_key_check")):
            raise Spec003MigrationError("foreign_key_check falhou")
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise Spec003MigrationError("integrity_check falhou")
        connection.commit()
        connection.execute("PRAGMA foreign_keys=ON")
        _validate(connection)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _columns(connection, table):
    return {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}


def _rebuild_patients(connection):
    if "cpf_status" in _columns(connection, "patients"):
        return
    connection.execute("""CREATE TABLE patients_spec003 (
        id INTEGER NOT NULL PRIMARY KEY, full_name VARCHAR(160) NOT NULL,
        cpf VARCHAR(11), cpf_status VARCHAR(30) NOT NULL DEFAULT 'not_provided',
        birth_date DATE, phone VARCHAR(30) NOT NULL, email VARCHAR(120) NOT NULL,
        address VARCHAR(255) NOT NULL, emergency_contact VARCHAR(160) NOT NULL,
        notes TEXT, active BOOLEAN NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, version INTEGER NOT NULL DEFAULT 1,
        UNIQUE (cpf))""")
    connection.execute("""INSERT INTO patients_spec003
        (id,full_name,cpf,cpf_status,birth_date,phone,email,address,emergency_contact,notes,active,created_at,updated_at,version)
        SELECT id,full_name,cpf,CASE WHEN is_valid_cpf(cpf)=1 THEN 'verified' ELSE 'legacy_unverified' END,
        birth_date,phone,email,address,emergency_contact,notes,active,created_at,created_at,1 FROM patients""")
    connection.execute("DROP TABLE patients")
    connection.execute("ALTER TABLE patients_spec003 RENAME TO patients")
    connection.execute("CREATE INDEX ix_patients_full_name ON patients(full_name)")


def _rebuild_psychologists(connection):
    if "crp_status" in _columns(connection, "psychologists"):
        return
    connection.execute("""CREATE TABLE psychologists_spec003 (
        id INTEGER NOT NULL PRIMARY KEY, full_name VARCHAR(160) NOT NULL,
        crp VARCHAR(40), crp_region VARCHAR(8), crp_number VARCHAR(20),
        crp_status VARCHAR(30) NOT NULL DEFAULT 'provisional', phone VARCHAR(30) NOT NULL,
        email VARCHAR(120) NOT NULL, specialty VARCHAR(120) NOT NULL, active BOOLEAN NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        version INTEGER NOT NULL DEFAULT 1, CONSTRAINT uq_psychologist_crp_identity UNIQUE(crp_region,crp_number))""")
    connection.execute("""INSERT INTO psychologists_spec003
        (id,full_name,crp,crp_region,crp_number,crp_status,phone,email,specialty,active,created_at,updated_at,version)
        SELECT id,full_name,crp,NULL,NULL,'review',phone,email,specialty,active,created_at,created_at,1 FROM psychologists""")
    connection.execute("DROP TABLE psychologists")
    connection.execute("ALTER TABLE psychologists_spec003 RENAME TO psychologists")
    connection.execute("CREATE INDEX ix_psychologists_full_name ON psychologists(full_name)")


def _extend_clinical_records(connection):
    additions = {
        "author_user_id": "INTEGER REFERENCES users(id)",
        "author_status": "VARCHAR(30) NOT NULL DEFAULT 'author_unknown'",
        "appointment_id": "INTEGER REFERENCES appointments(id)",
        "updated_at": "DATETIME",
        "finalized_at": "DATETIME",
        "status": "VARCHAR(30) NOT NULL DEFAULT 'legacy_preserved'",
        "version": "INTEGER NOT NULL DEFAULT 1",
    }
    existing = _columns(connection, "clinical_records")
    for name, definition in additions.items():
        if name not in existing:
            connection.execute(f'ALTER TABLE clinical_records ADD COLUMN "{name}" {definition}')
    connection.execute("""UPDATE clinical_records SET status='legacy_preserved',
        author_status='author_unknown', author_user_id=NULL, appointment_id=NULL,
        updated_at=COALESCE(updated_at,created_at), version=COALESCE(version,1)""")


def _extend_appointments(connection):
    existing = _columns(connection, "appointments")
    if "updated_at" not in existing:
        connection.execute("ALTER TABLE appointments ADD COLUMN updated_at DATETIME")
    if "version" not in existing:
        connection.execute("ALTER TABLE appointments ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
    connection.execute("UPDATE appointments SET version=COALESCE(version,1)")


def _create_spec003_tables(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS clinical_record_revisions (
        id INTEGER NOT NULL PRIMARY KEY, clinical_record_id INTEGER NOT NULL REFERENCES clinical_records(id),
        previous_revision_id INTEGER REFERENCES clinical_record_revisions(id),
        author_user_id INTEGER NOT NULL REFERENCES users(id), psychologist_id INTEGER NOT NULL REFERENCES psychologists(id),
        reason TEXT NOT NULL, content_snapshot TEXT NOT NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    connection.execute("CREATE INDEX IF NOT EXISTS ix_clinical_record_revisions_clinical_record_id ON clinical_record_revisions(clinical_record_id)")
    connection.execute("""CREATE TABLE IF NOT EXISTS clinical_record_audit_events (
        id INTEGER NOT NULL PRIMARY KEY, record_reference INTEGER NOT NULL,
        actor_user_id INTEGER NOT NULL REFERENCES users(id), event_type VARCHAR(40) NOT NULL,
        occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    connection.execute("CREATE INDEX IF NOT EXISTS ix_clinical_record_audit_events_record_reference ON clinical_record_audit_events(record_reference)")


def _validate(connection):
    required = {"cpf_status", "version", "updated_at"}
    if not required <= _columns(connection, "patients"):
        raise Spec003MigrationError("schema patients incompleto")
    if not {"crp_region", "crp_number", "crp_status", "version"} <= _columns(connection, "psychologists"):
        raise Spec003MigrationError("schema psychologists incompleto")
    if not {"status", "author_status", "appointment_id", "version"} <= _columns(connection, "clinical_records"):
        raise Spec003MigrationError("schema clinical_records incompleto")
    if not {"updated_at", "version"} <= _columns(connection, "appointments"):
        raise Spec003MigrationError("schema appointments incompleto")
    if list(connection.execute("PRAGMA foreign_key_check")):
        raise Spec003MigrationError("foreign_key_check falhou")
    if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise Spec003MigrationError("integrity_check falhou")
