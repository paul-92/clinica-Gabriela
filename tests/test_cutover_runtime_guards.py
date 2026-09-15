import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.utils.cutover_guard import assert_legacy_desktop_allowed
from backend.config import RuntimeSettings, get_runtime_settings
from backend.cutover.infrastructure import (
    OperationalPointer,
    acquire_maintenance_lock,
    freeze_runtime,
    sha256_file,
)
from backend.main import bootstrap_backend


def sqlite_database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE fixture (id INTEGER PRIMARY KEY)")
    return path


def test_backend_write_mode_fails_closed_under_maintenance(tmp_path):
    database = sqlite_database(tmp_path / "db.sqlite")
    lock = acquire_maintenance_lock(tmp_path / "maintenance.lock", "execution")
    settings = RuntimeSettings(tmp_path, database, "127.0.0.1", 9999, False,
                               lock.path, tmp_path / "pointer.json", False)
    with pytest.raises(RuntimeError, match="maintenance"):
        bootstrap_backend(settings)
    lock.release()


def test_backend_read_only_verification_requires_lock_and_cannot_write(tmp_path):
    from backend.database.session import create_database_runtime

    database = sqlite_database(tmp_path / "db.sqlite")
    settings = RuntimeSettings(tmp_path, database, "127.0.0.1", 9999, False,
                               tmp_path / "maintenance.lock", tmp_path / "pointer.json", True)
    with pytest.raises(RuntimeError, match="maintenance"):
        bootstrap_backend(settings)
    lock = acquire_maintenance_lock(settings.maintenance_lock_path, "execution")
    runtime = create_database_runtime(settings)
    with runtime.engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM fixture").scalar_one() == 0
        with pytest.raises(Exception):
            connection.exec_driver_sql("INSERT INTO fixture VALUES (1)")
    runtime.engine.dispose()
    lock.release()


def test_config_uses_valid_persistent_pointer_and_fails_on_corruption(tmp_path, monkeypatch):
    database = sqlite_database(tmp_path / "db.sqlite")
    pointer_path = tmp_path / "pointer.json"
    code = tmp_path / "code"
    code.mkdir()
    (code / "app.py").write_text("value = 1\n", encoding="utf-8")
    _, runtime_hash = freeze_runtime(code, ["app.py"], tmp_path / "manifests")
    pointer = OperationalPointer(1, "legacy", str(database.resolve()), sha256_file(database),
                                 "backend-models-v2-credential-reset", runtime_hash)
    pointer_path.write_bytes(pointer.bytes())
    monkeypatch.delenv("BACKEND_DATABASE_PATH", raising=False)
    monkeypatch.setenv("CLINICA_OPERATIONAL_POINTER", str(pointer_path))
    monkeypatch.setenv("CLINICA_RUNTIME_MANIFEST_DIR", str(tmp_path / "manifests"))
    monkeypatch.setenv("CLINICA_RUNTIME_CODE_ROOT", str(code))
    assert get_runtime_settings().database_path == database.resolve()
    pointer_path.write_text("{}", encoding="utf-8")
    with pytest.raises(Exception):
        get_runtime_settings()


def test_desktop_is_blocked_by_maintenance_or_canonical_pointer(tmp_path, monkeypatch):
    database = sqlite_database(tmp_path / "db.sqlite")
    pointer_path = tmp_path / "pointer.json"
    lock_path = tmp_path / "maintenance.lock"
    monkeypatch.setenv("CLINICA_OPERATIONAL_POINTER", str(pointer_path))
    monkeypatch.setenv("CLINICA_MAINTENANCE_LOCK", str(lock_path))
    lock = acquire_maintenance_lock(lock_path, "execution")
    with pytest.raises(RuntimeError, match="maintenance"):
        assert_legacy_desktop_allowed()
    lock.release()
    code = tmp_path / "code"
    code.mkdir()
    (code / "app.py").write_text("value = 1\n", encoding="utf-8")
    _, runtime_hash = freeze_runtime(code, ["app.py"], tmp_path / "manifests")
    monkeypatch.setenv("CLINICA_RUNTIME_MANIFEST_DIR", str(tmp_path / "manifests"))
    monkeypatch.setenv("CLINICA_RUNTIME_CODE_ROOT", str(code))
    pointer = OperationalPointer(1, "canonical", str(database.resolve()), sha256_file(database),
                                 "backend-models-v2-credential-reset", runtime_hash)
    pointer_path.write_bytes(pointer.bytes())
    with pytest.raises(RuntimeError, match="promocao canonica"):
        assert_legacy_desktop_allowed()


def test_read_only_middleware_blocks_writes_before_license(tmp_path, monkeypatch):
    from backend.main import create_app

    database = sqlite_database(tmp_path / "db.sqlite")
    pointer_path = tmp_path / "pointer.json"
    lock_path = tmp_path / "maintenance.lock"
    code = tmp_path / "code"
    code.mkdir()
    (code / "app.py").write_text("value = 1\n", encoding="utf-8")
    _, runtime_hash = freeze_runtime(code, ["app.py"], tmp_path / "manifests")
    pointer = OperationalPointer(1, "canonical", str(database.resolve()), sha256_file(database),
                                 "backend-models-v2-credential-reset", runtime_hash)
    pointer_path.write_bytes(pointer.bytes())
    lock = acquire_maintenance_lock(lock_path, "execution")
    monkeypatch.setenv("CLINICA_OPERATIONAL_POINTER", str(pointer_path))
    monkeypatch.setenv("CLINICA_MAINTENANCE_LOCK", str(lock_path))
    monkeypatch.setenv("CLINICA_RUNTIME_MANIFEST_DIR", str(tmp_path / "manifests"))
    monkeypatch.setenv("CLINICA_RUNTIME_CODE_ROOT", str(code))
    monkeypatch.setenv("BACKEND_VERIFY_READ_ONLY", "true")
    monkeypatch.delenv("BACKEND_DATABASE_PATH", raising=False)
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        response = client.post("/patients", json={})
        assert response.status_code == 503
        assert response.json()["detail"] == "read_only_verification"
    lock.release()


def test_runtime_pointer_fails_closed_when_code_changes(tmp_path, monkeypatch):
    database = sqlite_database(tmp_path / "db.sqlite")
    code = tmp_path / "code"
    code.mkdir()
    source = code / "app.py"
    source.write_text("value = 1\n", encoding="utf-8")
    _, runtime_hash = freeze_runtime(code, ["app.py"], tmp_path / "manifests")
    pointer_path = tmp_path / "pointer.json"
    pointer = OperationalPointer(1, "canonical", str(database.resolve()), sha256_file(database),
                                 "backend-models-v2-credential-reset", runtime_hash)
    pointer_path.write_bytes(pointer.bytes())
    monkeypatch.setenv("CLINICA_OPERATIONAL_POINTER", str(pointer_path))
    monkeypatch.setenv("CLINICA_RUNTIME_MANIFEST_DIR", str(tmp_path / "manifests"))
    monkeypatch.setenv("CLINICA_RUNTIME_CODE_ROOT", str(code))
    monkeypatch.delenv("BACKEND_DATABASE_PATH", raising=False)
    monkeypatch.delenv("BACKEND_DATA_DIR", raising=False)
    source.write_text("value = 2\n", encoding="utf-8")
    with pytest.raises(Exception, match="runtime local diverge"):
        get_runtime_settings()
