import pytest

from app.utils.initial_admin import get_initial_admin_config


def test_initial_admin_is_not_created_without_environment(monkeypatch):
    monkeypatch.delenv("INITIAL_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("INITIAL_ADMIN_PASSWORD", raising=False)
    assert get_initial_admin_config() is None


def test_initial_admin_comes_from_environment(monkeypatch):
    monkeypatch.setenv("INITIAL_ADMIN_USERNAME", "admin_local")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "senha-forte-123")
    config = get_initial_admin_config()
    assert config["username"] == "admin_local"
    assert config["password"] == "senha-forte-123"


@pytest.mark.parametrize("password", ["", "curta"])
def test_initial_admin_rejects_incomplete_or_weak_credentials(monkeypatch, password):
    monkeypatch.setenv("INITIAL_ADMIN_USERNAME", "admin_local")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", password)
    with pytest.raises(RuntimeError):
        get_initial_admin_config()
