from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.routes import appointments, auth
from backend.database.session import Base, get_db
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.settings import ClinicSettings
from backend.models.user import User
from backend.utils.security import hash_password


SECRET = "spec004-remediation-auth-secret-32-bytes"


@pytest.fixture()
def api(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", SECRET)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    from backend.models import appointment, clinical_record, finance, patient, psychologist, settings, user  # noqa: F401
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    patient_row = Patient(full_name="Paciente API", active=True)
    own_psy = Psychologist(full_name="Psi Propria", crp="06/11111", crp_region="06", crp_number="11111", crp_status="apt", active=True)
    other_psy = Psychologist(full_name="Psi Outra", crp="06/22222", crp_region="06", crp_number="22222", crp_status="apt", active=True)
    db.add_all([patient_row, own_psy, other_psy, ClinicSettings(timezone_name="America/Sao_Paulo")]); db.commit()
    users = [
        User(name="Admin API", username="admin-api", password_hash=hash_password("senha123"), role="admin", active=True),
        User(name="Reception API", username="reception-api", password_hash=hash_password("senha123"), role="reception", active=True),
        User(name="Psi API", username="psychologist-api", password_hash=hash_password("senha123"), role="psychologist", active=True, psychologist_id=own_psy.id),
        User(name="Psi sem vinculo", username="unlinked-api", password_hash=hash_password("senha123"), role="psychologist", active=True),
    ]
    db.add_all(users); db.commit()
    ids = patient_row.id, own_psy.id, other_psy.id
    db.close()
    app = FastAPI(); app.include_router(auth.router); app.include_router(appointments.router)
    def database():
        session = Session()
        try: yield session
        finally: session.close()
    app.dependency_overrides[get_db] = database
    client = TestClient(app)
    def token(username):
        response = client.post("/auth/login", json={"username": username, "password": "senha123"})
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    yield client, token, *ids
    client.close(); engine.dispose()


def appointment_payload(patient_id, psychologist_id, days=30):
    return {"patient_id": patient_id, "psychologist_id": psychologist_id,
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(),
            "duration_minutes": 50, "status": "scheduled", "notes": ""}


def create_as_admin(client, token, patient_id, psychologist_id, days):
    response = client.post("/appointments", headers=token("admin-api"),
                           json=appointment_payload(patient_id, psychologist_id, days))
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize("username,own_expected,other_expected", [
    ("admin-api", 201, 201), ("reception-api", 201, 201),
    ("psychologist-api", 201, 403), ("unlinked-api", 403, 403),
])
def test_create_matrix_uses_real_login(api, username, own_expected, other_expected):
    client, token, patient_id, own_id, other_id = api
    assert client.post("/appointments", headers=token(username), json=appointment_payload(patient_id, own_id, 40)).status_code == own_expected
    assert client.post("/appointments", headers=token(username), json=appointment_payload(patient_id, other_id, 41)).status_code == other_expected


@pytest.mark.parametrize("action,username,expected", [
    ("cancel", "admin-api", 200), ("cancel", "reception-api", 200), ("cancel", "psychologist-api", 200),
    ("done", "admin-api", 200), ("done", "reception-api", 403), ("done", "psychologist-api", 200),
    ("no-show", "admin-api", 200), ("no-show", "reception-api", 200), ("no-show", "psychologist-api", 200),
])
def test_transition_matrix_uses_real_login(api, action, username, expected):
    client, token, patient_id, own_id, _ = api
    item = create_as_admin(client, token, patient_id, own_id, 50 + hash((action, username)) % 100)
    response = client.post(f"/appointments/{item['id']}/{action}", headers={**token(username), "If-Match": f'"{item["version"]}"'}, json={"reason": "motivo sintetico"})
    assert response.status_code == expected


def test_edit_reschedule_other_agenda_and_exceptional_matrix(api):
    client, token, patient_id, own_id, other_id = api
    own = create_as_admin(client, token, patient_id, own_id, 200)
    patch = client.patch(f"/appointments/{own['id']}", headers={**token("psychologist-api"), "If-Match": '"1"'}, json={"notes": "ajuste"})
    assert patch.status_code == 200
    other = create_as_admin(client, token, patient_id, other_id, 201)
    assert client.patch(f"/appointments/{other['id']}", headers={**token("psychologist-api"), "If-Match": '"1"'}, json={"notes": "negado"}).status_code == 403
    own2 = create_as_admin(client, token, patient_id, own_id, 202)
    rescheduled = client.post(f"/appointments/{own2['id']}/reschedule", headers={**token("psychologist-api"), "If-Match": '"1"'}, json={**appointment_payload(patient_id, own_id, 203), "reason": "remarcacao"})
    assert rescheduled.status_code == 201
    closed = create_as_admin(client, token, patient_id, own_id, 204)
    done = client.post(f"/appointments/{closed['id']}/done", headers={**token("admin-api"), "If-Match": '"1"'}, json={"reason": "feito"}).json()
    for username in ("reception-api", "psychologist-api", "unlinked-api"):
        response = client.post(f"/appointments/{closed['id']}/exceptional-correction", headers={**token(username), "If-Match": f'"{done["version"]}"'}, json={"target_status": "scheduled", "reason": "correcao"})
        assert response.status_code == 403
    response = client.post(f"/appointments/{closed['id']}/exceptional-correction", headers={**token("admin-api"), "If-Match": f'"{done["version"]}"'}, json={"target_status": "scheduled", "reason": "correcao"})
    assert response.status_code == 200
