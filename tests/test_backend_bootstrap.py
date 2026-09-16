import asyncio
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from backend.config import RuntimeSettings, get_runtime_settings
from backend.database.session import configure_database, get_db
import backend.main as backend_main
from backend.main import bootstrap_backend, create_app
from backend.models.patient import Patient


def test_suite_default_database_is_isolated_from_operational_database():
    repository = Path(__file__).resolve().parents[1]
    operational = (repository / "backend" / "data" / "clinica_api.db").resolve()

    assert get_runtime_settings().database_path != operational
    assert operational not in get_runtime_settings().database_path.parents


def test_suite_fails_closed_before_write_capable_open_of_operational_database():
    repository = Path(__file__).resolve().parents[1]
    operational = repository / "backend" / "data" / "clinica_api.db"

    with pytest.raises(RuntimeError, match="banco operacional real"):
        sqlite3.connect(operational)


def test_runtime_settings_accept_explicit_environment_overrides(monkeypatch, tmp_path):
    data_dir = tmp_path / "dados"
    database_path = tmp_path / "bancos" / "teste.db"
    monkeypatch.setenv("BACKEND_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BACKEND_DATABASE_PATH", str(database_path))
    monkeypatch.setenv("BACKEND_HOST", "127.0.0.2")
    monkeypatch.setenv("BACKEND_PORT", "8123")
    monkeypatch.setenv("BACKEND_RELOAD", "false")

    settings = get_runtime_settings()

    assert settings.data_dir == data_dir.resolve()
    assert settings.database_path == database_path.resolve()
    assert settings.host == "127.0.0.2"
    assert settings.port == 8123
    assert settings.reload is False


@pytest.mark.parametrize("port", ["abc", "0", "65536"])
def test_runtime_settings_rejects_invalid_port(monkeypatch, port):
    monkeypatch.setenv("BACKEND_PORT", port)
    with pytest.raises(RuntimeError):
        get_runtime_settings()


def test_importing_backend_main_does_not_create_database(tmp_path):
    data_dir = tmp_path / "nao_criar"
    env = os.environ.copy()
    env["BACKEND_DATA_DIR"] = str(data_dir)
    env.pop("BACKEND_DATABASE_PATH", None)
    env["CLINICA_RUNTIME_ROOT"] = str(tmp_path / "runtime-isolado")

    result = subprocess.run(
        [sys.executable, "-c", "import backend.main"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not data_dir.exists()


def test_create_app_is_separate_from_bootstrap(monkeypatch, tmp_path):
    data_dir = tmp_path / "sem_bootstrap"
    monkeypatch.setenv("BACKEND_DATA_DIR", str(data_dir))
    monkeypatch.delenv("BACKEND_DATABASE_PATH", raising=False)
    monkeypatch.setenv("CLINICA_RUNTIME_ROOT", str(tmp_path / "runtime-isolado"))

    app = create_app(lifespan_context=None)

    assert app is not None
    assert not data_dir.exists()


def test_bootstrap_is_idempotent_with_temporary_database(monkeypatch, tmp_path):
    monkeypatch.delenv("INITIAL_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("INITIAL_ADMIN_PASSWORD", raising=False)
    settings = RuntimeSettings(
        data_dir=tmp_path / "dados",
        database_path=tmp_path / "dados" / "backend.db",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )

    second = None
    try:
        first = bootstrap_backend(settings)
        first.engine.dispose()
        second = bootstrap_backend(settings)
        tables = set(inspect(second.engine).get_table_names())
        user_columns = {
            column["name"] for column in inspect(second.engine).get_columns("users")
        }
        with second.session_factory() as session:
            patient_count = session.query(Patient).count()

        assert settings.database_path.exists()
        assert {
            "users", "patients", "psychologists", "appointments",
            "clinical_records", "payments", "expenses", "clinic_settings",
        } <= tables
        assert patient_count == 1
        assert "password_reset_required" in user_columns
    finally:
        if second is not None:
            second.engine.dispose()
        configure_database(get_runtime_settings())


def test_normal_app_startup_runs_bootstrap(monkeypatch, tmp_path):
    original_settings = get_runtime_settings()
    data_dir = tmp_path / "startup"
    monkeypatch.setenv("BACKEND_DATA_DIR", str(data_dir))
    monkeypatch.delenv("BACKEND_DATABASE_PATH", raising=False)
    monkeypatch.setenv("CLINICA_RUNTIME_ROOT", str(tmp_path / "runtime-isolado"))
    monkeypatch.delenv("INITIAL_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("INITIAL_ADMIN_PASSWORD", raising=False)

    try:
        with TestClient(create_app()) as client:
            response = client.get("/health")

        assert response.status_code == 200
        assert (data_dir / "clinica_api.db").exists()
    finally:
        configure_database(original_settings)


def test_database_cannot_be_reconfigured_while_request_session_is_active(tmp_path):
    original_settings = get_runtime_settings()
    first_settings = RuntimeSettings(
        tmp_path / "primeiro", tmp_path / "primeiro" / "db.sqlite",
        "127.0.0.1", 8000, False,
    )
    second_settings = RuntimeSettings(
        tmp_path / "segundo", tmp_path / "segundo" / "db.sqlite",
        "127.0.0.1", 8001, False,
    )
    first_settings.data_dir.mkdir(parents=True)
    dependency = None
    second = None
    try:
        configure_database(first_settings)
        dependency = get_db()
        next(dependency)

        with pytest.raises(RuntimeError, match="sessoes ativas"):
            configure_database(second_settings)

        dependency.close()
        dependency = None
        second = configure_database(second_settings)
    finally:
        if dependency is not None:
            dependency.close()
        if second is not None:
            second.engine.dispose()
        configure_database(original_settings)


def test_lifespan_disposes_exactly_the_runtime_it_started(monkeypatch):
    class EngineSpy:
        def __init__(self):
            self.dispose_calls = 0

        def dispose(self):
            self.dispose_calls += 1

    started_engine = EngineSpy()
    unrelated_engine = EngineSpy()
    monkeypatch.setattr(
        backend_main,
        "bootstrap_backend",
        lambda: type("Runtime", (), {"engine": started_engine})(),
    )

    async def run_lifespan():
        async with backend_main.lifespan(None):
            pass

    asyncio.run(run_lifespan())

    assert started_engine.dispose_calls == 1
    assert unrelated_engine.dispose_calls == 0
