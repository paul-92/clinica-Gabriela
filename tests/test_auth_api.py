import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.routes import auth
from backend.database.session import Base, get_db
from backend.models.user import User
from backend.utils.security import hash_password


TEST_SECRET = "segredo-de-teste-de-autenticacao-com-32-bytes"


def build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    db = Session()

    user = User(
        name="Usuario Teste",
        username="teste",
        password_hash=hash_password("senha123"),
        role="psychologist",
        active=True,
    )

    db.add(user)
    db.commit()
    db.close()

    app = FastAPI()

    def override_get_db():
        test_db = Session()
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth.router)

    return TestClient(app)


def test_login_returns_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)

    client = build_client()

    response = client.post(
        "/auth/login",
        json={
            "username": "teste",
            "password": "senha123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "teste"


def test_login_rejects_invalid_password(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)

    client = build_client()

    response = client.post(
        "/auth/login",
        json={
            "username": "teste",
            "password": "errada",
        },
    )

    assert response.status_code == 401


def test_me_returns_authenticated_user(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)

    client = build_client()

    login = client.post(
        "/auth/login",
        json={
            "username": "teste",
            "password": "senha123",
        },
    )

    token = login.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "teste"


def test_me_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)

    client = build_client()

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)

    client = build_client()

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer token-invalido",
        },
    )

    assert response.status_code == 401
