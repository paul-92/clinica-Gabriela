from types import SimpleNamespace

import pytest

from app.api.client import (
    ApiTimeoutError,
    BackendUnavailableError,
    DesktopIdentity,
    DesktopSession,
    ForbiddenError,
    InvalidApiResponseError,
    InvalidCredentialsError,
    InvalidSessionError,
)
from app.views.login_view import LoginView
from app.views.main_view import MainView


IDENTITY = DesktopIdentity(7, "Usuario Teste", "usuario.teste", "reception", True)


class FakeEntry:
    def __init__(self, value):
        self.value = value
        self.deleted = False

    def get(self):
        return self.value

    def delete(self, start, end):
        self.value = ""
        self.deleted = True


class FakeClient:
    def __init__(self, result=IDENTITY, error=None):
        self.session = DesktopSession()
        self.result = result
        self.error = error
        self.calls = []

    def login(self, username, password):
        self.calls.append((username, password))
        if self.error:
            raise self.error
        self.session.begin_authentication("token-apenas-memoria")
        self.session.complete_authentication(self.result)
        return self.result


def make_view(client):
    view = LoginView.__new__(LoginView)
    view.api_client = client
    view.username = FakeEntry("usuario.teste")
    view.password = FakeEntry("senha-secreta")
    view.root = SimpleNamespace(destroy=lambda: None)
    return view


def test_login_tkinter_bem_sucedido_usa_api_e_identidade(monkeypatch):
    client = FakeClient()
    opened = []
    monkeypatch.setattr(
        "app.views.login_view.MainView",
        lambda identity, session: SimpleNamespace(
            mainloop=lambda: opened.append((identity, session))
        ),
    )
    view = make_view(client)

    view._login()

    assert client.calls == [("usuario.teste", "senha-secreta")]
    assert opened == [(IDENTITY, client.session)]
    assert client.session.identity == IDENTITY


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (InvalidCredentialsError(), "Usuario ou senha invalidos."),
        (BackendUnavailableError(), "Nao foi possivel conectar ao backend local."),
        (ApiTimeoutError(), "O backend demorou demais para responder."),
        (InvalidSessionError(), "A sessao nao e valida. Tente entrar novamente."),
        (ForbiddenError(), "Acesso negado pelo backend."),
        (InvalidApiResponseError(), "O backend retornou uma resposta inesperada."),
    ],
)
def test_erros_controlados_recebem_mensagem_segura(monkeypatch, error, message):
    shown = []
    monkeypatch.setattr(
        "app.views.login_view.messagebox.showerror",
        lambda title, text: shown.append((title, text)),
    )
    view = make_view(FakeClient(error=error))

    view._login()

    assert shown == [("Login", message)]
    assert "token" not in message.lower()
    assert "traceback" not in message.lower()


@pytest.mark.parametrize("error", [None, InvalidCredentialsError()])
def test_senha_nao_fica_retida_apos_tentativa(monkeypatch, error):
    monkeypatch.setattr("app.views.login_view.messagebox.showerror", lambda *args: None)
    monkeypatch.setattr(
        "app.views.login_view.MainView",
        lambda *args: SimpleNamespace(mainloop=lambda: None),
    )
    view = make_view(FakeClient(error=error))

    view._login()

    assert view.password.value == ""
    assert view.password.deleted is True


def test_logout_ao_fechar_janela_limpa_sessao():
    session = DesktopSession()
    session.begin_authentication("token-apenas-memoria")
    session.complete_authentication(IDENTITY)
    view = MainView.__new__(MainView)
    view.desktop_session = session
    destroyed = []
    view.destroy = lambda: destroyed.append(True)

    view._close_session()

    assert session.authenticated is False
    assert session.identity is None
    assert destroyed == [True]


def test_login_view_nao_importa_fluxo_sqlite_legado():
    import app.views.login_view as login_module

    source_names = set(login_module.LoginView._login.__code__.co_names)
    assert "AuthController" not in vars(login_module)
    assert "controller" not in source_names
