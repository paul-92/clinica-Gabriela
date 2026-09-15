import sqlite3
from datetime import datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from backend.config import RuntimeSettings
from backend.api.versioning import parse_if_match
from backend.database.session import create_database_runtime, init_db
from backend.domain.identifiers import normalize_cpf, normalize_crp
from backend.migration.spec003 import migrate_spec003
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.user import User
from backend.services.clinical_record_service import ClinicalRecordService
from backend.services.patient_service import PatientService
from backend.schemas.patient import PatientCreate, PatientRead, PatientUpdate


def test_cpf_is_optional_normalized_and_validated():
    assert PatientCreate(full_name="Pessoa Ficticia").cpf is None
    assert normalize_cpf("529.982.247-25") == "52998224725"
    with pytest.raises((ValueError, ValidationError)):
        PatientCreate(full_name="Pessoa Ficticia", cpf="123.456.789-00")


def test_legacy_unverified_cpf_remains_readable_without_revalidation():
    patient = PatientRead.model_validate({
        "id": 1,
        "full_name": "Pessoa legada",
        "cpf": "123.456.789-00",
        "cpf_status": "legacy_unverified",
        "version": 1,
    })
    assert patient.cpf == "123.456.789-00"
    assert patient.cpf_status == "legacy_unverified"


def test_patch_distinguishes_absent_from_explicit_null():
    absent = PatientUpdate(full_name="Nome Alterado")
    cleared = PatientUpdate(cpf=None)
    assert "cpf" not in absent.model_dump(exclude_unset=True)
    assert cleared.model_dump(exclude_unset=True)["cpf"] is None


def test_if_match_parser_and_stale_version_return_412(tmp_path):
    assert parse_if_match('"7"') == 7
    settings = RuntimeSettings(tmp_path, tmp_path / "etag.db", "127.0.0.1", 8000, False)
    runtime = create_database_runtime(settings)
    init_db(runtime.engine)
    session = runtime.session_factory()
    try:
        patient = Patient(full_name="Pessoa Ficticia", active=True)
        session.add(patient)
        session.commit()
        with pytest.raises(Exception) as stale:
            PatientService(session).update_patient(
                patient.id, {"phone": "0000-0000"}, expected_version=patient.version + 1
            )
        assert stale.value.status_code == 412
    finally:
        session.close()
        runtime.engine.dispose()


def test_crp_identity_is_deterministic_and_requires_both_parts():
    assert normalize_crp("06", "12.345") == ("06", "12345")
    with pytest.raises(ValueError):
        normalize_crp("06", None)


def test_every_runtime_connection_enables_foreign_keys(tmp_path):
    settings = RuntimeSettings(tmp_path, tmp_path / "runtime.db", "127.0.0.1", 8000, False)
    runtime = create_database_runtime(settings)
    try:
        with runtime.engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    finally:
        runtime.engine.dispose()


def _legacy_database(path):
    with sqlite3.connect(path) as connection:
        connection.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, username TEXT NOT NULL,
          password_hash TEXT NOT NULL, role TEXT NOT NULL, active BOOLEAN NOT NULL,
          password_reset_required BOOLEAN NOT NULL DEFAULT 0, created_at DATETIME);
        CREATE TABLE patients (id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, cpf TEXT NOT NULL UNIQUE,
          birth_date DATE, phone TEXT NOT NULL, email TEXT NOT NULL, address TEXT NOT NULL,
          emergency_contact TEXT NOT NULL, notes TEXT, active BOOLEAN NOT NULL, created_at DATETIME);
        CREATE TABLE psychologists (id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, crp TEXT NOT NULL UNIQUE,
          phone TEXT NOT NULL, email TEXT NOT NULL, specialty TEXT NOT NULL, active BOOLEAN NOT NULL, created_at DATETIME);
        CREATE TABLE appointments (id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id),
          psychologist_id INTEGER NOT NULL REFERENCES psychologists(id), scheduled_at DATETIME NOT NULL,
          duration_minutes INTEGER NOT NULL, status TEXT NOT NULL, notes TEXT);
        CREATE TABLE clinical_records (id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id),
          psychologist_id INTEGER NOT NULL REFERENCES psychologists(id), appointment_date DATETIME NOT NULL,
          main_complaint TEXT, session_goals TEXT, observed_mood TEXT, clinical_evolution TEXT,
          interventions TEXT, referrals TEXT, next_steps TEXT, private_notes TEXT,
          clinical_hypotheses TEXT, therapeutic_plan TEXT, future_attachments TEXT, created_at DATETIME);
        CREATE TABLE payments (id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id),
          appointment_id INTEGER REFERENCES appointments(id), due_date DATE NOT NULL, paid_at DATE,
          amount FLOAT NOT NULL, status TEXT NOT NULL, payment_method TEXT NOT NULL, description TEXT);
        INSERT INTO users VALUES (1,'Usuario Ficticio','usuario','disabled','psychologist',1,1,CURRENT_TIMESTAMP);
        INSERT INTO patients VALUES (7,'Paciente Ficticio','123.456.789-00',NULL,'','','','',NULL,1,CURRENT_TIMESTAMP);
        INSERT INTO psychologists VALUES (9,'Profissional Ficticio','06/12345','','','',1,CURRENT_TIMESTAMP);
        INSERT INTO appointments VALUES (11,7,9,CURRENT_TIMESTAMP,50,'done',NULL);
        INSERT INTO clinical_records VALUES (13,7,9,CURRENT_TIMESTAMP,'demanda','','','evolucao','','','','','','','',CURRENT_TIMESTAMP);
        """)


def test_forward_migration_preserves_legacy_without_inference(tmp_path):
    database = tmp_path / "candidate.db"
    _legacy_database(database)
    migrate_spec003(database)
    with sqlite3.connect(database) as connection:
        patient = connection.execute("SELECT id,cpf,cpf_status,version FROM patients").fetchone()
        record = connection.execute("SELECT id,status,author_user_id,author_status,appointment_id FROM clinical_records").fetchone()
        psychologist = connection.execute("SELECT id,crp,crp_region,crp_number,crp_status FROM psychologists").fetchone()
        assert patient == (7, "123.456.789-00", "legacy_unverified", 1)
        assert record == (13, "legacy_preserved", None, "author_unknown", None)
        assert psychologist == (9, "06/12345", None, None, "review")
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert list(connection.execute("PRAGMA foreign_key_check")) == []


def test_fresh_schema_rejects_orphan_and_has_no_delete_cascade(tmp_path):
    settings = RuntimeSettings(tmp_path, tmp_path / "fresh.db", "127.0.0.1", 8000, False)
    runtime = create_database_runtime(settings)
    try:
        init_db(runtime.engine)
        with runtime.engine.begin() as connection:
            with pytest.raises(Exception):
                connection.execute(text("INSERT INTO appointments (patient_id,psychologist_id,scheduled_at,duration_minutes,status) VALUES (99,88,CURRENT_TIMESTAMP,50,'scheduled')"))
        with sqlite3.connect(settings.database_path) as connection:
            actions = {row[6] for row in connection.execute("PRAGMA foreign_key_list(clinical_records)")}
            assert actions == {"NO ACTION"}
    finally:
        runtime.engine.dispose()


def test_clinical_record_lifecycle_is_immutable_and_rectifiable(tmp_path):
    settings = RuntimeSettings(tmp_path, tmp_path / "lifecycle.db", "127.0.0.1", 8000, False)
    runtime = create_database_runtime(settings)
    init_db(runtime.engine)
    session = runtime.session_factory()
    try:
        user = User(name="Profissional Ficticio", username="psi", password_hash="disabled", role="psychologist", active=True)
        patient = Patient(full_name="Paciente Ficticio", active=True)
        psychologist = Psychologist(full_name="Profissional Ficticio", crp_region="06", crp_number="12345", crp="06/12345", crp_status="apt", active=True)
        session.add_all([user, patient, psychologist])
        session.commit()
        service = ClinicalRecordService(session)
        record = service.create_record({
            "patient_id": patient.id, "psychologist_id": psychologist.id,
            "appointment_id": None, "appointment_date": datetime(2030, 1, 1, 10),
            "clinical_evolution": "conteudo ficticio",
        }, user)
        assert record.status == "draft"
        finalized = service.finalize_record(record.id, record.version, user)
        assert finalized.status == "finalized"
        with pytest.raises(Exception) as immutable:
            service.update_record(record.id, {"clinical_evolution": "sobrescrita"}, finalized.version)
        assert immutable.value.status_code == 409
        revision = service.rectify_record(record.id, {
            "reason": "correcao ficticia", "clinical_evolution": "texto retificado",
        }, user)
        assert revision.previous_revision_id is None
        assert session.get(type(record), record.id).clinical_evolution == "conteudo ficticio"
    finally:
        session.close()
        runtime.engine.dispose()


def test_only_eligible_draft_can_be_deleted_and_audit_has_metadata_only(tmp_path):
    settings = RuntimeSettings(tmp_path, tmp_path / "delete.db", "127.0.0.1", 8000, False)
    runtime = create_database_runtime(settings)
    init_db(runtime.engine)
    session = runtime.session_factory()
    try:
        user = User(name="Profissional Ficticio", username="psi2", password_hash="disabled", role="psychologist", active=True)
        patient = Patient(full_name="Paciente Ficticio", active=True)
        psychologist = Psychologist(full_name="Profissional Ficticio", crp_region="06", crp_number="54321", crp="06/54321", crp_status="apt", active=True)
        session.add_all([user, patient, psychologist]); session.commit()
        service = ClinicalRecordService(session)
        record = service.create_record({"patient_id": patient.id, "psychologist_id": psychologist.id,
            "appointment_date": datetime(2030, 1, 1, 10), "private_notes": "nao copiar"}, user)
        record_id = record.id
        service.delete_draft(record_id, user)
        event = session.execute(text("SELECT record_reference,event_type FROM clinical_record_audit_events")).fetchone()
        assert event == (record_id, "draft_deleted")
        columns = {row[1] for row in sqlite3.connect(settings.database_path).execute("PRAGMA table_info(clinical_record_audit_events)")}
        assert "content_snapshot" not in columns and "private_notes" not in columns
    finally:
        session.close()
        runtime.engine.dispose()
