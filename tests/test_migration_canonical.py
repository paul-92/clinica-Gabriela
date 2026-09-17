import sqlite3

import pytest

from backend.migration import (
    EXPECTED_TABLES,
    CanonicalCreationError,
    CanonicalDatabaseNotFoundError,
    CanonicalDestinationExistsError,
    CanonicalUnsafePathError,
    SourceDatabase,
    create_sqlite_snapshot,
    create_temporary_canonical_database,
    open_canonical_connection,
)
from scripts.sqlite_inventory import DEFAULT_BACKEND_DB, DEFAULT_DESKTOP_DB


def source_snapshots(tmp_path):
    artifacts = []
    sources = []
    for label, name in (
        (SourceDatabase.DESKTOP_LEGACY, "desktop"),
        (SourceDatabase.BACKEND_LEGACY, "backend"),
    ):
        source = tmp_path / f"{name}-source.db"
        with sqlite3.connect(source) as connection:
            connection.execute("CREATE TABLE fixture (id INTEGER PRIMARY KEY)")
        artifact = create_sqlite_snapshot(
            source,
            tmp_path / f"{name}-snapshot.db",
            source_label=label,
            snapshot_reference=f"snapshot://fixture/{name}-canonical-input",
        )
        sources.append(source)
        artifacts.append(artifact)
    return tuple(sources), tuple(artifacts)


def test_create_valid_empty_canonical_database_with_expected_schema(tmp_path):
    _, snapshots = source_snapshots(tmp_path)
    destination = tmp_path / "candidate" / "canonical-temporary.db"

    result = create_temporary_canonical_database(
        destination, source_snapshots=snapshots
    )

    assert result.path == destination.resolve()
    assert result.tables == tuple(sorted(EXPECTED_TABLES))
    assert result.row_count == 0
    assert result.foreign_keys_enabled is True
    assert result.foreign_key_violations == 0
    assert result.integrity_check_passed is True
    assert len(result.schema_checksum_sha256) == 64


def test_primary_keys_unique_constraints_and_foreign_keys_are_preserved(tmp_path):
    _, snapshots = source_snapshots(tmp_path)
    destination = tmp_path / "canonical-temporary.db"
    create_temporary_canonical_database(destination, source_snapshots=snapshots)

    with open_canonical_connection(destination) as connection:
        patient_columns = connection.execute("PRAGMA table_info(patients)").fetchall()
        assert [row[1] for row in patient_columns if row[5]] == ["id"]
        patient_indexes = connection.execute("PRAGMA index_list(patients)").fetchall()
        unique_patient_columns = {
            tuple(
                row[2]
                for row in connection.execute(f'PRAGMA index_info("{index[1]}")')
            )
            for index in patient_indexes
            if index[2]
        }
        assert ("cpf",) in unique_patient_columns
        appointment_fks = connection.execute("PRAGMA foreign_key_list(appointments)").fetchall()
        assert {(row[3], row[2], row[4]) for row in appointment_fks} == {
            ("patient_id", "patients", "id"),
            ("psychologist_id", "psychologists", "id"),
            ("original_appointment_id", "appointments", "id"),
        }


def test_payments_appointment_is_nullable_and_foreign_keys_enforced(tmp_path):
    _, snapshots = source_snapshots(tmp_path)
    destination = tmp_path / "canonical-temporary.db"
    create_temporary_canonical_database(destination, source_snapshots=snapshots)

    with open_canonical_connection(destination) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        columns = {
            row[1]: row for row in connection.execute("PRAGMA table_info(payments)")
        }
        assert columns["appointment_id"][3] == 0
        payment_fks = connection.execute("PRAGMA foreign_key_list(payments)").fetchall()
        assert ("appointment_id", "appointments", "id") in {
            (row[3], row[2], row[4]) for row in payment_fks
        }


def test_open_requires_existing_database_and_never_creates_file(tmp_path):
    missing = tmp_path / "missing-canonical.db"
    with pytest.raises(CanonicalDatabaseNotFoundError):
        open_canonical_connection(missing)
    assert not missing.exists()


def test_created_canonical_database_can_be_opened_without_overwrite(tmp_path):
    _, snapshots = source_snapshots(tmp_path)
    destination = tmp_path / "canonical-temporary.db"
    create_temporary_canonical_database(destination, source_snapshots=snapshots)
    before = destination.read_bytes()

    with open_canonical_connection(destination) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert set(EXPECTED_TABLES) == {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='table'"
            )
        }

    assert destination.read_bytes() == before


def test_existing_destination_is_rejected_and_preserved(tmp_path):
    _, snapshots = source_snapshots(tmp_path)
    destination = tmp_path / "existing.db"
    destination.write_bytes(b"preserve-existing-fixture")

    with pytest.raises(CanonicalDestinationExistsError):
        create_temporary_canonical_database(destination, source_snapshots=snapshots)

    assert destination.read_bytes() == b"preserve-existing-fixture"


@pytest.mark.parametrize("operational", [DEFAULT_DESKTOP_DB, DEFAULT_BACKEND_DB])
def test_operational_database_paths_are_rejected_without_access(tmp_path, operational):
    _, snapshots = source_snapshots(tmp_path)
    with pytest.raises(CanonicalUnsafePathError):
        create_temporary_canonical_database(operational, source_snapshots=snapshots)


@pytest.mark.parametrize("operational", [DEFAULT_DESKTOP_DB, DEFAULT_BACKEND_DB])
def test_open_rejects_operational_database_before_sqlite_access(
    tmp_path, operational, monkeypatch
):
    def forbidden_connect(*args, **kwargs):
        raise AssertionError("sqlite3.connect nao deveria ser chamado")

    monkeypatch.setattr("backend.migration.canonical.sqlite3.connect", forbidden_connect)
    with pytest.raises(CanonicalUnsafePathError):
        open_canonical_connection(operational)


def test_descendant_of_operational_directory_is_rejected(tmp_path):
    _, snapshots = source_snapshots(tmp_path)
    destination = DEFAULT_BACKEND_DB.parent / "isolated" / "candidate.db"
    with pytest.raises(CanonicalUnsafePathError):
        create_temporary_canonical_database(destination, source_snapshots=snapshots)
    with pytest.raises(CanonicalUnsafePathError):
        open_canonical_connection(destination)
    assert not destination.exists()


def test_snapshot_cannot_be_reused_as_destination(tmp_path):
    _, snapshots = source_snapshots(tmp_path)
    protected = snapshots[0].path
    before = protected.read_bytes()
    with pytest.raises(CanonicalUnsafePathError):
        create_temporary_canonical_database(protected, source_snapshots=snapshots)
    assert protected.read_bytes() == before


def test_creation_failure_removes_only_created_candidate(tmp_path, monkeypatch):
    sources, snapshots = source_snapshots(tmp_path)
    protected = (*sources, *(artifact.path for artifact in snapshots))
    before = {path: path.read_bytes() for path in protected}
    destination = tmp_path / "partial-candidate.db"

    def fail_schema(*args, **kwargs):
        raise RuntimeError("controlled schema fixture failure")

    monkeypatch.setattr("backend.migration.canonical.Base.metadata.create_all", fail_schema)
    with pytest.raises(CanonicalCreationError):
        create_temporary_canonical_database(destination, source_snapshots=snapshots)

    assert not destination.exists()
    assert {path: path.read_bytes() for path in protected} == before


def test_import_and_result_construction_have_no_filesystem_side_effects(tmp_path):
    before = list(tmp_path.iterdir())
    __import__("backend.migration.canonical")
    assert list(tmp_path.iterdir()) == before == []
