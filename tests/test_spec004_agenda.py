from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from backend.config import RuntimeSettings
from backend.database.session import create_database_runtime, init_db
from backend.models.appointment import Appointment, AppointmentEvent
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.settings import ClinicSettings
from backend.models.user import User
from backend.services.appointment_service import AppointmentService
from concurrent.futures import ThreadPoolExecutor


@pytest.fixture()
def agenda(tmp_path):
    settings = RuntimeSettings(tmp_path, tmp_path / "agenda.db", "127.0.0.1", 8000, False)
    runtime = create_database_runtime(settings)
    init_db(runtime.engine)
    session = runtime.session_factory()
    patient = Patient(full_name="Paciente Ficticio", active=True)
    psychologist = Psychologist(full_name="Profissional Ficticio", crp="06/12345",
        crp_region="06", crp_number="12345", crp_status="apt", active=True)
    session.add_all([patient, psychologist, ClinicSettings(timezone_name="America/Sao_Paulo")]); session.commit()
    admin = User(name="Admin Ficticio", username="admin-spec004", password_hash="disabled",
        role="admin", active=True)
    reception = User(name="Recepcao Ficticia", username="rec-spec004", password_hash="disabled",
        role="reception", active=True)
    own = User(name="Psi Ficticio", username="psi-spec004", password_hash="disabled",
        role="psychologist", active=True, psychologist_id=psychologist.id)
    session.add_all([admin, reception, own]); session.commit()
    yield session, patient, psychologist, admin, reception, own
    session.close(); runtime.engine.dispose()


def payload(patient, psychologist, hour=9, minute=0, duration=60):
    return {"patient_id": patient.id, "psychologist_id": psychologist.id,
        "scheduled_at": datetime.now(timezone.utc).replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=2),
        "duration_minutes": duration, "status": "scheduled", "notes": ""}


def test_intervals_duration_and_status_contract(agenda):
    db, patient, psychologist, admin, *_ = agenda
    service = AppointmentService(db)
    first = service.create_appointment(payload(patient, psychologist), admin)
    with pytest.raises(HTTPException) as overlap:
        service.create_appointment(payload(patient, psychologist, 9, 30), admin)
    assert overlap.value.status_code == 409
    assert service.create_appointment(payload(patient, psychologist, 10), admin).id
    for invalid in (0, -1):
        with pytest.raises(HTTPException) as duration:
            service.create_appointment(payload(patient, psychologist, 12, duration=invalid), admin)
        assert duration.value.status_code == 422
    with pytest.raises(HTTPException) as invalid_status:
        service.create_appointment({**payload(patient, psychologist, 13), "status": "rescheduled"}, admin)
    assert invalid_status.value.status_code == 422
    assert first.version == 1


def test_authorization_transitions_etag_and_events(agenda):
    db, patient, psychologist, admin, reception, own = agenda
    service = AppointmentService(db)
    item = service.create_appointment(payload(patient, psychologist), reception)
    with pytest.raises(HTTPException) as forbidden:
        service.transition(item.id, "done", reception, item.version, "")
    assert forbidden.value.status_code == 403
    done = service.transition(item.id, "done", own, item.version, "")
    with pytest.raises(HTTPException) as closed:
        service.transition(done.id, "scheduled", admin, done.version, "")
    assert closed.value.status_code == 409
    with pytest.raises(HTTPException) as stale:
        service.update_appointment(done.id, {"notes": "x"}, admin, expected_version=1)
    assert stale.value.status_code == 412
    assert db.query(AppointmentEvent).filter_by(appointment_id=item.id, event_type="done").count() == 1


def test_atomic_reschedule_preserves_original_and_successor(agenda):
    db, patient, psychologist, admin, *_ = agenda
    service = AppointmentService(db)
    original = service.create_appointment(payload(patient, psychologist), admin)
    successor = service.reschedule(original.id, payload(patient, psychologist, 11), admin,
        original.version, "ajuste operacional")
    db.refresh(original)
    assert original.status == "canceled"
    assert successor.original_appointment_id == original.id
    event = db.query(AppointmentEvent).filter_by(appointment_id=original.id, event_type="rescheduled").one()
    assert event.successor_appointment_id == successor.id


def test_psychologist_without_material_link_is_denied(agenda):
    db, patient, psychologist, _admin, *_ = agenda
    unlinked = User(name="Sem Vinculo", username="sem-vinculo", password_hash="disabled",
        role="psychologist", active=True)
    db.add(unlinked); db.commit()
    with pytest.raises(HTTPException) as denied:
        AppointmentService(db).create_appointment(payload(patient, psychologist), unlinked)
    assert denied.value.status_code == 403


def test_real_sqlite_connections_prevent_double_booking(tmp_path):
    settings = RuntimeSettings(tmp_path, tmp_path / "race.db", "127.0.0.1", 8000, False)
    runtime = create_database_runtime(settings); init_db(runtime.engine)
    setup = runtime.session_factory()
    patient = Patient(full_name="Paciente Concorrencia", active=True)
    psychologist = Psychologist(full_name="Psi Concorrencia", crp="06/67890", crp_region="06", crp_number="67890", crp_status="apt", active=True)
    admin = User(name="Admin Concorrencia", username="admin-race", password_hash="disabled", role="admin", active=True)
    setup.add_all([patient, psychologist, admin, ClinicSettings(timezone_name="America/Sao_Paulo")]); setup.commit()
    values = payload(patient, psychologist); ids = patient.id, psychologist.id, admin.id
    setup.close()

    def reserve():
        db = runtime.session_factory()
        try:
            actor = db.get(User, ids[2])
            return ("ok", AppointmentService(db).create_appointment(dict(values), actor).id)
        except HTTPException as exc:
            return ("error", exc.status_code)
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: reserve(), range(2)))
    assert sorted(result[0] for result in results) == ["error", "ok"]
    verify = runtime.session_factory()
    assert verify.query(Appointment).count() == 1
    verify.close(); runtime.engine.dispose()


def test_reschedule_commit_failure_rolls_back_everything(agenda, monkeypatch):
    db, patient, psychologist, admin, *_ = agenda
    service = AppointmentService(db)
    original = service.create_appointment(payload(patient, psychologist), admin)
    original_id, version = original.id, original.version
    real_commit = db.commit
    monkeypatch.setattr(db, "commit", lambda: (_ for _ in ()).throw(RuntimeError("fault injection")))
    with pytest.raises(RuntimeError, match="fault injection"):
        service.reschedule(original_id, payload(patient, psychologist, 11), admin, version, "motivo ficticio")
    monkeypatch.setattr(db, "commit", real_commit)
    db.expire_all()
    assert db.get(Appointment, original_id).status == "scheduled"
    assert db.query(Appointment).count() == 1
    assert db.query(AppointmentEvent).filter_by(event_type="rescheduled").count() == 0
