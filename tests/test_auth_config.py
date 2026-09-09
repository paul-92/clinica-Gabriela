import os

import pytest

from backend.config import get_auth_secret


def test_auth_secret_is_loaded_from_environment(monkeypatch):
    monkeypatch.setenv(
        "AUTH_SECRET",
        "segredo-de-autenticacao-com-mais-de-32-bytes",
    )

    assert get_auth_secret() == (
        "segredo-de-autenticacao-com-mais-de-32-bytes"
    )


def test_auth_secret_is_required(monkeypatch):
    monkeypatch.delenv("AUTH_SECRET", raising=False)

    with pytest.raises(RuntimeError):
        get_auth_secret()


def test_auth_secret_requires_minimum_length(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "curto")

    with pytest.raises(RuntimeError):
        get_auth_secret()
