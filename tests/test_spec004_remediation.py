from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from backend.config import RuntimeSettings
from backend.database.session import create_database_runtime, init_db
from backend.models.appointment import AppointmentEvent
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.settings import ClinicSettings
from backend.models.user import User
from backend.services.appointment_service import AppointmentService


@pytest.fixture()
def context(tmp_path):
    runtime = create_database_runtime(RuntimeSettings(tmp_path, tmp_path / "remediation.db", "127.0.0.1", 8000, False))
    init_db(runtime.engine)
    db = runtime.session_factory()
    patient = Patient(full_name="Paciente Sintetico", active=True)
    psychologist = Psychologist(full_name="Profissional Sintetico", crp="06/99999", crp_region="06", crp_number="99999", crp_status="apt", active=True)
    settings = ClinicSettings(timezone_name="America/New_York")
    db.add_all([patient, psychologist, settings]); db.commit()
    admin = User(name="Admin Sintetico", username="admin-remediation", password_hash="disabled", role="admin", active=True)
    reception = User(name="Recepcao Sintetica", username="reception-remediation", password_hash="disabled", role="reception", active=True)
    own = User(name="Psi Sintetico", username="psi-remediation", password_hash="disabled", role="psychologist", active=True, psychologist_id=psychologist.id)
    db.add_all([admin, reception, own]); db.commit()
    yield db, patient, psychologist, admin, reception, own
    db.close(); runtime.engine.dispose()


def values(patient, psychologist, when=None):
    return {"patient_id": patient.id, "psychologist_id": psychologist.id,
            "scheduled_at": when or datetime.now(timezone.utc) + timedelta(days=10),
            "duration_minutes": 50, "status": "scheduled", "notes": ""}


def test_normal_flow_rejects_retroactive_edit_for_every_role(context):
    db, patient, psychologist, admin, reception, own = context
    service = AppointmentService(db)
    for index, actor in enumerate((admin, reception, own)):
        item = service.create_appointment(values(patient, psychologist,
            datetime.now(timezone.utc) + timedelta(days=10 + index)), admin)
        with pytest.raises(HTTPException) as denied:
            service.update_appointment(item.id, {"scheduled_at": datetime.now(timezone.utc) - timedelta(days=1)}, actor, item.version)
        assert denied.value.status_code == 409


def test_timezone_authority_rejects_gap_ambiguity_and_payload_override(context):
    db, patient, psychologist, admin, *_ = context
    service = AppointmentService(db)
    with pytest.raises(HTTPException, match="inexistente"):
        service.create_appointment(values(patient, psychologist, datetime(2030, 3, 10, 2, 30)), admin)
    with pytest.raises(HTTPException, match="ambiguo"):
        service.create_appointment(values(patient, psychologist, datetime(2030, 11, 3, 1, 30)), admin)
    with pytest.raises(HTTPException, match="diverge"):
        service.create_appointment({**values(patient, psychologist), "timezone_name": "UTC"}, admin)
    item = service.create_appointment(values(patient, psychologist, datetime(2030, 3, 11, 9, 0)), admin)
    assert item.timezone_name == "America/New_York"


def test_exceptional_correction_is_admin_only_reasoned_and_append_only(context):
    db, patient, psychologist, admin, reception, own = context
    service = AppointmentService(db)
    item = service.create_appointment(values(patient, psychologist), admin)
    item = service.transition(item.id, "done", admin, item.version, "conclusao")
    for actor in (reception, own):
        with pytest.raises(HTTPException) as denied:
            service.exceptional_correction(item.id, "scheduled", actor, item.version, "correcao")
        assert denied.value.status_code == 403
    with pytest.raises(HTTPException) as no_reason:
        service.exceptional_correction(item.id, "scheduled", admin, item.version, "")
    assert no_reason.value.status_code == 422
    corrected = service.exceptional_correction(item.id, "scheduled", admin, item.version, "erro operacional")
    event = db.query(AppointmentEvent).filter_by(appointment_id=item.id, event_type="exceptional_correction").one()
    assert (corrected.status, event.actor_user_id, event.from_status, event.to_status) == ("scheduled", admin.id, "done", "scheduled")
    with pytest.raises(Exception):
        db.execute(text("UPDATE appointment_events SET reason='alterado' WHERE id=:id"), {"id": event.id}); db.commit()
    db.rollback()
    with pytest.raises(Exception):
        db.execute(text("DELETE FROM appointment_events WHERE id=:id"), {"id": event.id}); db.commit()
    db.rollback()
    assert db.get(AppointmentEvent, event.id).reason == "erro operacional"
