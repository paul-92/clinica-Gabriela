"""Cliente HTTP/JWT em memoria para a transicao do desktop Tkinter."""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.config import RuntimeSettings, get_runtime_settings


class DesktopApiError(RuntimeError):
    """Erro controlado ao acessar a API local."""


class InvalidCredentialsError(DesktopApiError):
    pass


class InvalidSessionError(DesktopApiError):
    pass


class ForbiddenError(DesktopApiError):
    pass


class BackendUnavailableError(DesktopApiError):
    pass


class ApiTimeoutError(DesktopApiError):
    pass


class InvalidApiResponseError(DesktopApiError):
    pass


@dataclass(frozen=True)
class DesktopIdentity:
    id: int
    name: str
    username: str
    role: str
    active: bool


class DesktopSession:
    """Estado efemero de autenticacao; nunca persiste token ou identidade."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._identity: DesktopIdentity | None = None

    @property
    def identity(self) -> DesktopIdentity | None:
        return self._identity

    @property
    def authenticated(self) -> bool:
        return self._token is not None and self._identity is not None

    def authorization_header(self) -> str:
        if self._token is None:
            raise InvalidSessionError("Sessao nao autenticada.")
        return f"Bearer {self._token}"

    def begin_authentication(self, token: str) -> None:
        self._token = token
        self._identity = None

    def complete_authentication(self, identity: DesktopIdentity) -> None:
        if self._token is None:
            raise InvalidSessionError("Nao ha autenticacao pendente.")
        self._identity = identity

    def clear(self) -> None:
        self._token = None
        self._identity = None


class DesktopApiClient:
    def __init__(
        self,
        settings: RuntimeSettings | None = None,
        *,
        timeout: float = 5.0,
        opener: Callable[..., Any] = urlopen,
        session: DesktopSession | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("O timeout deve ser maior que zero.")
        runtime = settings or get_runtime_settings()
        self.base_url = f"http://{runtime.host}:{runtime.port}"
        self.timeout = timeout
        self._opener = opener
        self.session = session or DesktopSession()

    def login(self, username: str, password: str) -> DesktopIdentity:
        self.session.clear()
        payload = self._request(
            "POST",
            "/auth/login",
            data={"username": username, "password": password},
            login_request=True,
        )
        token = payload.get("access_token") if isinstance(payload, dict) else None
        token_type = payload.get("token_type") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token or str(token_type).lower() != "bearer":
            raise InvalidApiResponseError("Resposta de login invalida.")

        self.session.begin_authentication(token)
        try:
            identity = self.get_identity()
        except DesktopApiError:
            self.session.clear()
            raise
        return identity

    def get_identity(self) -> DesktopIdentity:
        payload = self.get("/auth/me", authenticated=True)
        identity = self._parse_identity(payload)
        self.session.complete_authentication(identity)
        return identity

    def logout(self) -> None:
        self.session.clear()

    def get(self, path: str, *, authenticated: bool = True) -> Any:
        return self._request("GET", path, authenticated=authenticated)

    def post(
        self, path: str, data: dict[str, Any], *, authenticated: bool = True
    ) -> Any:
        return self._request("POST", path, data=data, authenticated=authenticated)

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        authenticated: bool = False,
        login_request: bool = False,
    ) -> Any:
        headers = {"Accept": "application/json"}
        body = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data).encode("utf-8")
        if authenticated:
            headers["Authorization"] = self.session.authorization_header()
        request = Request(
            f"{self.base_url}/{path.lstrip('/')}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            self._raise_http_error(exc.code, login_request=login_request)
        except (socket.timeout, TimeoutError) as exc:
            raise ApiTimeoutError("Tempo limite excedido ao acessar o backend.") from exc
        except URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                raise ApiTimeoutError("Tempo limite excedido ao acessar o backend.") from exc
            raise BackendUnavailableError("Backend local indisponivel.") from exc
        except OSError as exc:
            raise BackendUnavailableError("Backend local indisponivel.") from exc

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidApiResponseError("Backend retornou JSON invalido.") from exc

    def _raise_http_error(self, status: int, *, login_request: bool) -> None:
        if status == 401:
            self.session.clear()
            if login_request:
                raise InvalidCredentialsError("Usuario ou senha invalidos.")
            raise InvalidSessionError("Token invalido ou expirado.")
        if status == 403:
            raise ForbiddenError("Acesso negado pelo backend.")
        raise InvalidApiResponseError(f"Resposta HTTP inesperada do backend: {status}.")

    @staticmethod
    def _parse_identity(payload: Any) -> DesktopIdentity:
        if not isinstance(payload, dict):
            raise InvalidApiResponseError("Identidade retornada pelo backend e invalida.")
        expected = {
            "id": int,
            "name": str,
            "username": str,
            "role": str,
            "active": bool,
        }
        if any(
            key not in payload
            or not isinstance(payload[key], expected_type)
            or (expected_type is int and isinstance(payload[key], bool))
            for key, expected_type in expected.items()
        ):
            raise InvalidApiResponseError("Identidade retornada pelo backend e invalida.")
        return DesktopIdentity(**{key: payload[key] for key in expected})
