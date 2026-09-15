import sqlite3

import pytest
from sqlalchemy import text

from backend.config import RuntimeSettings
from backend.cutover.infrastructure import acquire_maintenance_lock, create_final_backup
from backend.database.session import create_database_runtime
from scripts.spec008_phase11_stabilization import _technical_persistence_after_shutdown


def _database(path):
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
        connection.execute(
            "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))"
        )
        connection.execute("INSERT INTO parent VALUES (1)")
        connection.execute("INSERT INTO child VALUES (1, 1)")
        connection.commit()


def test_shutdown_checkpoint_then_backup_window_is_deterministic(tmp_path):
    database = tmp_path / "canonical.db"
    _database(database)
    settings = RuntimeSettings(tmp_path, database, "127.0.0.1", 8000, False)
    runtime = create_database_runtime(settings)
    with runtime.session_factory() as session:
        assert session.execute(text("SELECT COUNT(*) FROM child")).scalar_one() == 1
    runtime.engine.dispose()

    persistence = _technical_persistence_after_shutdown(database)
    assert persistence["wal_checkpoint"] == [0, 0, 0]
    assert persistence["journal_mode_final"] == "delete"
    assert not any(tmp_path.glob("canonical.db-*"))

    lock = acquire_maintenance_lock(
        tmp_path / "maintenance.lock", "phase11-regression", databases=(database,)
    )
    try:
        manifest = create_final_backup(
            {"canonical_generation_2": database}, tmp_path / "backup",
            execution_reference="phase11-regression", lock=lock,
        )
    finally:
        lock.release()
    assert manifest.is_file()
    with sqlite3.connect(f"file:{(tmp_path / 'backup' / 'canonical_generation_2.backup.db').as_posix()}?mode=ro&immutable=1", uri=True) as restored:
        assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert list(restored.execute("PRAGMA foreign_key_check")) == []


def test_technical_checkpoint_fails_closed_with_competing_writer(tmp_path):
    database = tmp_path / "canonical.db"
    _database(database)
    competing = sqlite3.connect(database, timeout=0, isolation_level=None)
    competing.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            _technical_persistence_after_shutdown(database)
    finally:
        competing.rollback()
        competing.close()

    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro&immutable=1", uri=True) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert list(connection.execute("PRAGMA foreign_key_check")) == []
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
