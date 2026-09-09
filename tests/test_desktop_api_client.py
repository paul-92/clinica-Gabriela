import json
import socket
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from app.api.client import (
    ApiTimeoutError,
    BackendUnavailableError,
    DesktopApiClient,
    ForbiddenError,
    InvalidApiResponseError,
    InvalidCredentialsError,
    InvalidSessionError,
)
from backend.config import RuntimeSettings


IDENTITY = {
    "id": 7,
    "name": "Usuario Teste",
    "username": "usuario.teste",
    "role": "reception",
    "active": True,
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class QueueOpener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return FakeResponse(response)


@pytest.fixture
def settings():
    root = Path("unused-test-data").resolve()
    return RuntimeSettings(root, root / "api.db", "127.0.0.2", 8765, False)


def logged_client(settings, final_response=IDENTITY):
    opener = QueueOpener(
        {"access_token": "jwt-em-memoria", "token_type": "bearer", "user": IDENTITY},
        IDENTITY,
        final_response,
    )
    client = DesktopApiClient(settings, timeout=1.25, opener=opener)
    identity = client.login("usuario.teste", "senha-temporaria")
    return client, opener, identity


def http_error(status):
    return HTTPError("http://local", status, "erro", {}, None)


def test_login_bem_sucedido(settings):
    client, opener, identity = logged_client(settings)

    request, timeout = opener.requests[0]
    assert request.full_url == "http://127.0.0.2:8765/auth/login"
    assert json.loads(request.data) == {
        "username": "usuario.teste",
        "password": "senha-temporaria",
    }
    assert timeout == 1.25
    assert identity.username == "usuario.teste"
    assert client.session.authenticated is True


def test_auth_me_e_consultado_apos_login(settings):
    client, opener, identity = logged_client(settings)

    request, _ = opener.requests[1]
    assert request.full_url.endswith("/auth/me")
    assert identity == client.session.identity


def test_bearer_e_enviado_em_request_autenticada(settings):
    client, opener, _ = logged_client(settings, {"items": []})

    client.get("/patients")

    request, _ = opener.requests[2]
    assert request.get_header("Authorization") == "Bearer jwt-em-memoria"


def test_credenciais_invalidas(settings):
    client = DesktopApiClient(settings, opener=QueueOpener(http_error(401)))

    with pytest.raises(InvalidCredentialsError):
        client.login("incorreto", "incorreta")

    assert client.session.authenticated is False


def test_token_expirado_ou_invalido_limpa_sessao(settings):
    client, opener, _ = logged_client(settings, http_error(401))

    with pytest.raises(InvalidSessionError):
        client.get("/patients")

    assert client.session.identity is None
    assert client.session.authenticated is False


def test_falha_em_auth_me_nao_deixa_estado_provisorio(settings):
    opener = QueueOpener(
        {"access_token": "jwt-provisorio", "token_type": "bearer", "user": IDENTITY},
        http_error(401),
    )
    client = DesktopApiClient(settings, opener=opener)

    with pytest.raises(InvalidSessionError):
        client.login("usuario.teste", "senha-temporaria")

    assert client.session.identity is None
    assert client.session.authenticated is False
    with pytest.raises(InvalidSessionError):
        client.session.authorization_header()


def test_403_e_traduzido(settings):
    client, _, _ = logged_client(settings, http_error(403))

    with pytest.raises(ForbiddenError):
        client.post("/admin", {})


def test_backend_indisponivel(settings):
    client = DesktopApiClient(
        settings, opener=QueueOpener(URLError(ConnectionRefusedError()))
    )

    with pytest.raises(BackendUnavailableError):
        client.login("usuario", "senha")


@pytest.mark.parametrize(
    "failure", [socket.timeout(), TimeoutError(), URLError(socket.timeout())]
)
def test_timeout(settings, failure):
    client = DesktopApiClient(settings, opener=QueueOpener(failure))

    with pytest.raises(ApiTimeoutError):
        client.login("usuario", "senha")


def test_resposta_json_invalida(settings):
    client = DesktopApiClient(settings, opener=QueueOpener(b"nao-e-json"))

    with pytest.raises(InvalidApiResponseError):
        client.login("usuario", "senha")


def test_logout_limpa_completamente_sessao_e_token(settings):
    client, _, _ = logged_client(settings)

    client.logout()

    assert client.session.identity is None
    assert client.session.authenticated is False
    with pytest.raises(InvalidSessionError):
        client.session.authorization_header()


def test_credencial_e_token_nao_sao_persistidos(settings, monkeypatch):
    file_writes = []
    monkeypatch.setattr(
        "builtins.open",
        lambda *args, **kwargs: file_writes.append((args, kwargs)),
    )
    client, _, _ = logged_client(settings)

    assert "senha-temporaria" not in repr(client.__dict__)
    assert "jwt-em-memoria" not in repr(client.__dict__)
    assert file_writes == []
