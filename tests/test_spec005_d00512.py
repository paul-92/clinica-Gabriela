"""D005-12: persisted source authority, without historical code reconstruction."""

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from backend.cutover.infrastructure import OperationalPointer, SCHEMA_VERSION, freeze_runtime, sha256_file
from backend.cutover.spec005_execution_identity import (
    HISTORICAL_RECOVERY, IdentityBlock, bind_transformation, build_manifest,
    inventory, verify_manifest, verify_persisted_source,
)
from backend.migration.spec005 import _verified_operational_source_identity


ROOT = Path(__file__).resolve().parents[1]


def source_fixture(tmp_path, *, foreign_key_failure=False):
    runtime = tmp_path / "runtime"
    runtime.mkdir(parents=True)
    database = runtime / "source.db"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
        db.execute("CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))")
        if foreign_key_failure:
            db.execute("INSERT INTO child VALUES(1, 999)")
        db.execute("PRAGMA user_version=5")
    snapshot = tmp_path / "snapshot.db"
    shutil.copyfile(database, snapshot)
    historical = tmp_path / "historical"
    historical.mkdir()
    paths = []
    for number in range(128):
        name = f"file{number:03}.py"
        (historical / name).write_bytes(f"VALUE = {number}\n".encode())
        paths.append(name)
    manifest, manifest_sha = freeze_runtime(historical, paths, runtime / "runtime-manifests")
    pointer = runtime / "operational-pointer.json"
    identity = OperationalPointer(8, "canonical", str(database), sha256_file(database),
                                  SCHEMA_VERSION, manifest_sha)
    pointer.write_bytes(identity.bytes())
    expected = {"expected_pointer_sha256": sha256_file(pointer),
                "expected_manifest_sha256": manifest_sha,
                "expected_database_sha256": sha256_file(database)}
    return pointer, manifest.parent, snapshot, expected, historical


def verify(fixture):
    pointer, manifests, snapshot, expected, _ = fixture
    return verify_persisted_source(pointer, manifests, snapshot, **expected)


def test_persisted_source_and_binding_with_partial_historical_recovery(tmp_path):
    fixture = source_fixture(tmp_path)
    source = verify(fixture)
    assert source["historical_runtime_bytes_verification"] == HISTORICAL_RECOVERY
    assert source["historical_runtime_baseline_recovery"] == "PARTIAL"
    assert source["user_version"] == 5
    # Historical files are deliberately absent after the manifest was persisted.
    shutil.rmtree(fixture[4])
    assert verify(fixture) == source
    code = tmp_path / "code"
    for relative in inventory(ROOT):
        destination = code / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    manifest = tmp_path / "migration.json"
    migration_sha = build_manifest(code, manifest)
    assert verify_manifest(code, manifest, migration_sha) == migration_sha
    transformation = bind_transformation(source, migration_sha, expected_source=source,
                                         expected_migration_sha256=migration_sha)
    assert len(transformation) == 64
    with pytest.raises(IdentityBlock):
        bind_transformation({**source, "historical_runtime_bytes_verification": "PASS_128_OF_128"},
                            migration_sha, expected_source={**source, "historical_runtime_bytes_verification": "PASS_128_OF_128"},
                            expected_migration_sha256=migration_sha)
    with pytest.raises(IdentityBlock):
        bind_transformation(source, migration_sha, expected_source=source,
                            expected_migration_sha256="0" * 64)
    with pytest.raises(IdentityBlock):
        bind_transformation(source, migration_sha, expected_source=source,
                            expected_migration_sha256=migration_sha,
                            expected_transformation_sha256="0" * 64)
    with pytest.raises(IdentityBlock):
        bind_transformation(source, migration_sha, expected_source=source,
                            expected_migration_sha256=migration_sha,
                            expected_contract_identity="SPEC-005/WRONG")
    (code / "backend" / "cutover" / "spec005_execution_identity.py").write_bytes(b"tampered")
    with pytest.raises(IdentityBlock):
        verify_manifest(code, manifest, migration_sha)


def test_persisted_source_fail_closed_matrix(tmp_path, monkeypatch):
    pointer, manifests, snapshot, expected, _ = source_fixture(tmp_path)
    source = verify_persisted_source(pointer, manifests, snapshot, **expected)
    monkeypatch.setenv("CLINICA_OPERATIONAL_POINTER", str(pointer))
    monkeypatch.setenv("CLINICA_RUNTIME_MANIFEST_DIR", str(manifests))
    assert _verified_operational_source_identity(snapshot, persisted_source_expectations=source) == (
        source["database_sha256"], 8, source["runtime_manifest_sha256"])
    for key in expected:
        altered = {**expected, key: "0" * 64}
        with pytest.raises(IdentityBlock):
            verify_persisted_source(pointer, manifests, snapshot, **altered)
    with pytest.raises(IdentityBlock):
        verify_persisted_source(pointer, manifests, snapshot, **expected, expected_generation=7)
    manifest = manifests / f"runtime-manifest-{expected['expected_manifest_sha256']}.json"
    original_manifest = manifest.read_bytes()
    manifest.write_bytes(original_manifest + b" ")
    with pytest.raises(IdentityBlock):
        verify_persisted_source(pointer, manifests, snapshot, **expected)
    manifest.write_bytes(original_manifest)
    original = pointer.read_bytes()
    payload = json.loads(original)
    payload["schema_version"] = "wrong-schema"
    pointer.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IdentityBlock):
        verify_persisted_source(pointer, manifests, snapshot,
                                **{**expected, "expected_pointer_sha256": sha256_file(pointer)})
    pointer.write_bytes(original)
    snapshot.write_bytes(snapshot.read_bytes() + b"tamper")
    with pytest.raises(IdentityBlock):
        verify_persisted_source(pointer, manifests, snapshot, **expected)


def test_persisted_source_rejects_fk_failure_and_corrupt_database(tmp_path):
    fixture = source_fixture(tmp_path / "fk", foreign_key_failure=True)
    with pytest.raises(IdentityBlock):
        verify(fixture)
    pointer, manifests, snapshot, expected, _ = source_fixture(tmp_path / "corrupt")
    database = pointer.parent / "source.db"
    database.write_bytes(b"not a SQLite database")
    snapshot.write_bytes(database.read_bytes())
    payload = json.loads(pointer.read_bytes())
    payload["database_checksum_sha256"] = sha256_file(database)
    pointer.write_text(json.dumps(payload), encoding="utf-8")
    expected = {**expected, "expected_pointer_sha256": sha256_file(pointer),
                "expected_database_sha256": sha256_file(database)}
    with pytest.raises(IdentityBlock):
        verify_persisted_source(pointer, manifests, snapshot, **expected)
