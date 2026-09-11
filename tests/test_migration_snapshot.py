import sqlite3
import pytest

from backend.migration import (
    SnapshotBackupError,
    SnapshotDestinationExistsError,
    SnapshotIntegrityError,
    SnapshotInvalidError,
    SnapshotSamePathError,
    SnapshotSourceChangedError,
    SnapshotSourceNotFoundError,
    SourceDatabase,
    create_sqlite_snapshot,
    load_stored_manifest,
    save_manifest,
    SnapshotManifest,
    validate_sqlite_snapshot,
)


def make_database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version = 7")
        connection.execute(
            "CREATE TABLE fixture_records (id INTEGER PRIMARY KEY, technical_value TEXT)"
        )
        connection.execute(
            "INSERT INTO fixture_records VALUES (?, ?)", (700001, "FIXTURE-VALUE")
        )


def create_fixture_snapshot(tmp_path):
    source = tmp_path / "source.db"
    destination = tmp_path / "snapshot.db"
    make_database(source)
    artifact = create_sqlite_snapshot(
        source,
        destination,
        source_label=SourceDatabase.DESKTOP_LEGACY,
        snapshot_reference="snapshot://fixture/desktop-v1",
    )
    return source, destination, artifact


def test_valid_snapshot_preserves_source_and_produces_manifest(tmp_path):
    source = tmp_path / "source.db"
    destination = tmp_path / "snapshot.db"
    make_database(source)
    before = (source.stat().st_size, source.stat().st_mtime_ns, source.read_bytes())

    artifact = create_sqlite_snapshot(
        source,
        destination,
        source_label=SourceDatabase.DESKTOP_LEGACY,
        snapshot_reference="snapshot://fixture/desktop-v1",
    )

    assert artifact.path == destination.resolve()
    assert artifact.manifest.size_bytes == destination.stat().st_size > 0
    assert len(artifact.manifest.checksum_sha256) == 64
    assert artifact.manifest.schema_version == "sqlite-user-version-7"
    assert validate_sqlite_snapshot(destination, artifact.manifest) == artifact
    assert (source.stat().st_size, source.stat().st_mtime_ns, source.read_bytes()) == before


def test_snapshot_manifest_can_be_saved_and_loaded(tmp_path):
    _, _, artifact = create_fixture_snapshot(tmp_path)
    manifest_path = tmp_path / "snapshot-manifest.json"
    save_manifest(manifest_path, artifact.manifest)
    assert load_stored_manifest(manifest_path, SnapshotManifest) == artifact.manifest


def test_invalid_source_and_destination_contracts(tmp_path):
    source = tmp_path / "source.db"
    make_database(source)
    with pytest.raises(SnapshotSamePathError):
        create_sqlite_snapshot(
            source, source, source_label=SourceDatabase.DESKTOP_LEGACY,
            snapshot_reference="snapshot://fixture/same",
        )
    with pytest.raises(SnapshotSourceNotFoundError):
        create_sqlite_snapshot(
            tmp_path / "missing.db", tmp_path / "new.db",
            source_label=SourceDatabase.DESKTOP_LEGACY,
            snapshot_reference="snapshot://fixture/missing",
        )
    existing = tmp_path / "existing.db"
    existing.write_bytes(b"do-not-replace")
    with pytest.raises(SnapshotDestinationExistsError):
        create_sqlite_snapshot(
            source, existing, source_label=SourceDatabase.DESKTOP_LEGACY,
            snapshot_reference="snapshot://fixture/existing",
        )
    assert existing.read_bytes() == b"do-not-replace"


def test_backup_failure_removes_only_partial_destination(tmp_path, monkeypatch):
    source = tmp_path / "source.db"
    destination = tmp_path / "partial.db"
    make_database(source)

    class FailingOrigin:
        def backup(self, target):
            raise sqlite3.OperationalError("controlled fixture failure")

        def close(self):
            pass

    def failing_readonly(path):
        return FailingOrigin()

    monkeypatch.setattr("backend.migration.snapshot._readonly_connection", failing_readonly)
    with pytest.raises(SnapshotBackupError):
        create_sqlite_snapshot(
            source, destination, source_label=SourceDatabase.DESKTOP_LEGACY,
            snapshot_reference="snapshot://fixture/failure",
        )
    assert source.is_file()
    assert not destination.exists()


def test_source_change_during_snapshot_aborts_and_removes_destination(tmp_path, monkeypatch):
    source = tmp_path / "source.db"
    destination = tmp_path / "snapshot.db"
    make_database(source)
    actual_state = __import__("backend.migration.snapshot", fromlist=["_source_state"])._source_state
    calls = 0

    def changing_state(path):
        nonlocal calls
        calls += 1
        size, mtime, checksum = actual_state(path)
        return size, mtime + int(calls == 2), checksum

    monkeypatch.setattr("backend.migration.snapshot._source_state", changing_state)
    with pytest.raises(SnapshotSourceChangedError):
        create_sqlite_snapshot(
            source, destination, source_label=SourceDatabase.DESKTOP_LEGACY,
            snapshot_reference="snapshot://fixture/source-changed",
        )
    assert source.is_file()
    assert not destination.exists()


def test_corrupted_snapshot_and_failed_integrity_check_are_rejected(tmp_path, monkeypatch):
    _, destination, artifact = create_fixture_snapshot(tmp_path)
    destination.write_bytes(b"corrupted-fixture")
    with pytest.raises(SnapshotInvalidError):
        validate_sqlite_snapshot(destination, artifact.manifest)

    _, valid_destination, valid_artifact = create_fixture_snapshot(tmp_path / "nested")

    class FailedIntegrityConnection:
        def execute(self, sql):
            if sql == "PRAGMA integrity_check":
                return iter([("not-ok",)])
            raise AssertionError("integrity failure must stop validation")

        def close(self):
            pass

    def failed_integrity(path):
        return FailedIntegrityConnection()

    monkeypatch.setattr("backend.migration.snapshot._readonly_connection", failed_integrity)
    with pytest.raises(SnapshotIntegrityError):
        validate_sqlite_snapshot(valid_destination, valid_artifact.manifest)


def test_snapshot_module_import_has_no_side_effects(tmp_path):
    before = list(tmp_path.iterdir())
    __import__("backend.migration.snapshot")
    assert list(tmp_path.iterdir()) == before == []
