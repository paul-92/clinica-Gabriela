from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.routes import auth, users
from backend.database.session import Base, get_db
from backend.models.user import User
from backend.utils.security import hash_password


SECRET = "segredo-de-teste-de-autenticacao-com-32-bytes"


def build_client(role="admin", active=True):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    from backend.models import appointment, clinical_record, finance, patient, psychologist, settings, user  # noqa: F401
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    db.add(User(name="Administrador", username="admin", password_hash=hash_password("senha1234"), role=role, active=active))
    db.commit()
    db.close()
    app = FastAPI()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth.router)
    app.include_router(users.router)
    return TestClient(app)


def auth_header(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "senha1234"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_can_list_and_create_without_exposing_hash(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", SECRET)
    client = build_client()
    headers = auth_header(client)
    created = client.post("/users", headers=headers, json={"name": "Recepcao", "username": "recepcao", "password": "senha1234", "role": "reception"})
    assert created.status_code == 201
    assert "password_hash" not in created.json()
    listed = client.get("/users", headers=headers)
    assert listed.status_code == 200
    assert {item["username"] for item in listed.json()} == {"admin", "recepcao"}


def test_users_management_requires_authentication_and_admin(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", SECRET)
    assert build_client().get("/users").status_code == 401
    non_admin = build_client(role="reception")
    assert non_admin.get("/users", headers=auth_header(non_admin)).status_code == 403


def test_user_management_validates_duplicate_payload_and_updates_status(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", SECRET)
    client = build_client()
    headers = auth_header(client)
    invalid = client.post("/users", headers=headers, json={"name": "Invalido", "username": "x", "password": "curta", "role": "root"})
    assert invalid.status_code == 422
    payload = {"name": "Recepcao", "username": "recepcao", "password": "senha1234", "role": "reception"}
    assert client.post("/users", headers=headers, json=payload).status_code == 201
    duplicate = client.post("/users", headers=headers, json=payload)
    assert duplicate.status_code == 409
    updated = client.patch("/users/2", headers=headers, json={"active": False})
    assert updated.status_code == 200
    assert updated.json()["active"] is False


def test_admin_cannot_disable_self(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", SECRET)
    client = build_client()
    response = client.patch("/users/1", headers=auth_header(client), json={"active": False})
    assert response.status_code == 422
