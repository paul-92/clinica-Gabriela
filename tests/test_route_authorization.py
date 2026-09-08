from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes import (
    appointments,
    clinical_records,
    dashboard,
    finance,
    patients,
    psychologists,
    settings,
)
from backend.api.routes.auth import get_current_user
from backend.database.session import get_db


def make_user(role: str):
    return SimpleNamespace(
        id=1,
        name="Usuario Teste",
        username=f"teste_{role}",
        role=role,
        active=True,
        created_at=None,
    )


def build_app(user=None):
    app = FastAPI()

    app.include_router(appointments.router)
    app.include_router(clinical_records.router)
    app.include_router(dashboard.router)
    app.include_router(finance.router)
    app.include_router(patients.router)
    app.include_router(psychologists.router)
    app.include_router(settings.router)

    app.dependency_overrides[get_db] = lambda: None

    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user

    return app


@pytest.mark.parametrize(
    "path",
    [
        "/appointments",
        "/clinical-records",
        "/dashboard/summary",
        "/finance/summary",
        "/patients",
        "/psychologists",
        "/settings",
    ],
)
def test_private_routes_require_authentication(path):
    app = build_app()

    with TestClient(app) as client:
        response = client.get(path)

    assert response.status_code == 401


def test_authenticated_user_can_access_patients(monkeypatch):
    monkeypatch.setattr(
        patients.PatientService,
        "list_patients",
        lambda self, *args, **kwargs: [],
    )

    app = build_app(make_user("reception"))

    with TestClient(app) as client:
        response = client.get("/patients")

    assert response.status_code == 200
    assert response.json() == []


def test_reception_cannot_access_clinical_records():
    app = build_app(make_user("reception"))

    with TestClient(app) as client:
        response = client.get("/clinical-records")

    assert response.status_code == 403


def test_admin_does_not_automatically_access_clinical_records():
    app = build_app(make_user("admin"))

    with TestClient(app) as client:
        response = client.get("/clinical-records")

    assert response.status_code == 403


def test_psychologist_can_access_clinical_records(monkeypatch):
    monkeypatch.setattr(
        clinical_records.ClinicalRecordService,
        "list_records",
        lambda self, patient_id=None: [],
    )

    app = build_app(make_user("psychologist"))

    with TestClient(app) as client:
        response = client.get("/clinical-records")

    assert response.status_code == 200
    assert response.json() == []


def test_reception_cannot_access_settings():
    app = build_app(make_user("reception"))

    with TestClient(app) as client:
        response = client.get("/settings")

    assert response.status_code == 403


def test_psychologist_cannot_access_settings():
    app = build_app(make_user("psychologist"))

    with TestClient(app) as client:
        response = client.get("/settings")

    assert response.status_code == 403
