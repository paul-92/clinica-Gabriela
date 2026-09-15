import hashlib
import sqlite3

import pytest

from backend.migration.manifests import ExecutionManifest, SnapshotManifest
from backend.migration.storage import load_stored_manifest
from scripts.spec008_phase1 import run_phase1


def _database(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO sample VALUES (1, ?)", (value,))


def _checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase1_preserves_sources_and_validates_isolated_restores(tmp_path):
    repository = tmp_path / "repository"
    desktop = repository / "data" / "clinica_psicologia.db"
    backend = repository / "backend" / "data" / "clinica_api.db"
    _database(desktop, "desktop ficticio")
    _database(backend, "backend ficticio")
    before = (_checksum(desktop), _checksum(backend))

    artifact_root = tmp_path / "protected" / "execution-1"
    report = run_phase1(repository, artifact_root, "execution-1")

    assert report["phase1_gate"] == "PASS"
    assert (_checksum(desktop), _checksum(backend)) == before
    assert not tuple(artifact_root.glob("*.restore-test.db"))
    assert len(report["snapshots"]) == 2
    for label in ("desktop_legacy", "backend_legacy"):
        load_stored_manifest(
            artifact_root / f"{label}.snapshot-manifest.json", SnapshotManifest
        )
    load_stored_manifest(artifact_root / "execution-manifest.json", ExecutionManifest)


def test_phase1_rejects_artifacts_inside_repository(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    with pytest.raises(ValueError, match="fora da pasta"):
        run_phase1(repository, repository / "artifacts", "execution-1")


def test_inventory_connections_are_closed_before_restore_cleanup(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    desktop = repository / "data" / "clinica_psicologia.db"
    backend = repository / "backend" / "data" / "clinica_api.db"
    _database(desktop, "desktop ficticio")
    _database(backend, "backend ficticio")

    report = run_phase1(repository, tmp_path / "protected", "execution-2")

    assert report["phase1_gate"] == "PASS"
    assert not tuple((tmp_path / "protected").glob("*.restore-test.db"))
