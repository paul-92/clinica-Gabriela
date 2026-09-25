"""Identidades separadas D005-11; somente fixtures sintéticas."""

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from backend.cutover.infrastructure import OperationalPointer, SCHEMA_VERSION, freeze_runtime, sha256_file
from backend.cutover.spec005_execution_identity import (
    IdentityBlock, bind_transformation, build_manifest, inventory, verify_manifest, verify_source,
)


ROOT = Path(__file__).resolve().parents[1]


def _migration_fixture(tmp_path):
    root = tmp_path / "code"
    for relative in inventory(ROOT):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    manifest = tmp_path / "migration.json"
    checksum = build_manifest(root, manifest)
    return root, manifest, checksum


def _source_fixture(tmp_path):
    operational = tmp_path / "operational"
    operational.mkdir()
    database = operational / "source.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE synthetic(id INTEGER PRIMARY KEY)")
    snapshot = tmp_path / "snapshot.db"
    shutil.copyfile(database, snapshot)
    old_code = tmp_path / "historical"
    old_code.mkdir()
    (old_code / "old.py").write_bytes(b"SOURCE_BASELINE = 8\r\n")
    _, runtime_sha = freeze_runtime(old_code, ["old.py"], operational / "runtime-manifests")
    pointer_path = operational / "operational-pointer.json"
    pointer = OperationalPointer(8, "canonical", str(database), sha256_file(database), SCHEMA_VERSION, runtime_sha)
    pointer_path.write_bytes(pointer.bytes())
    return pointer_path, operational / "runtime-manifests", old_code, snapshot, sha256_file(pointer_path)


def test_independent_source_migration_and_binding(tmp_path):
    root, manifest, migration_sha = _migration_fixture(tmp_path)
    pointer, manifests, historical, snapshot, pointer_sha = _source_fixture(tmp_path)
    source = verify_source(pointer, manifests, historical, snapshot, pointer_sha)
    assert source["source_generation"] == 8 and source["foreign_key_violations"] == 0
    assert verify_manifest(root, manifest, migration_sha) == migration_sha
    identity = bind_transformation(source, migration_sha, expected_source=source,
                                   expected_migration_sha256=migration_sha)
    assert len(identity) == 64
    assert bind_transformation(source, migration_sha, expected_source=source,
                               expected_migration_sha256=migration_sha,
                               expected_transformation_sha256=identity) == identity
    with pytest.raises(IdentityBlock):
        bind_transformation(source, migration_sha, expected_source={**source, "source_generation": 7},
                            expected_migration_sha256=migration_sha)
    with pytest.raises(IdentityBlock):
        bind_transformation(source, migration_sha, expected_source=source,
                            expected_migration_sha256="0" * 64)
    with pytest.raises(IdentityBlock):
        bind_transformation(source, migration_sha, expected_source=source,
                            expected_migration_sha256=migration_sha,
                            expected_transformation_sha256="0" * 64)


def test_migration_tamper_and_unrelated_change(tmp_path):
    root, manifest, checksum = _migration_fixture(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("unrelated", encoding="utf-8")
    assert verify_manifest(root, manifest, checksum) == checksum
    dependency = root / "backend" / "cutover" / "infrastructure.py"
    original = dependency.read_bytes()
    dependency.write_bytes(original + b"\n# changed\n")
    with pytest.raises(IdentityBlock):
        verify_manifest(root, manifest, checksum)
    dependency.write_bytes(original)
    migration = root / "backend" / "migration" / "spec005.py"
    migration.write_bytes(migration.read_bytes() + b"\n# changed\n")
    with pytest.raises(IdentityBlock):
        verify_manifest(root, manifest, checksum)
    migration.unlink()
    with pytest.raises((IdentityBlock, FileNotFoundError)):
        verify_manifest(root, manifest, checksum)


def test_review_authority_trust_closure_tamper(tmp_path):
    root, manifest, checksum = _migration_fixture(tmp_path)
    participants = {
        "scripts/spec005_provision_e011_review.py",
        "scripts/spec005_candidate_migration.py",
        "backend/cutover/spec005_execution_identity.py",
        "backend/cutover/infrastructure.py",
    }
    entries = {entry["path"] for entry in json.loads(manifest.read_bytes())["entries"]}
    assert participants <= entries
    assert verify_manifest(root, manifest, checksum) == checksum
    for relative in sorted(participants):
        path = root / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\n# isolated tamper\n")
        with pytest.raises(IdentityBlock):
            verify_manifest(root, manifest, checksum)
        path.write_bytes(original)
        assert verify_manifest(root, manifest, checksum) == checksum


def test_manifest_and_closure_tamper(tmp_path):
    root, manifest, checksum = _migration_fixture(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    for change in (
        lambda p: p.update(contract_identity="OTHER"),
        lambda p: p["entries"].pop(),
        lambda p: p["entries"][0].update(path="../outside.py"),
        lambda p: p["entries"][0].update(sha256="0" * 64),
    ):
        altered = json.loads(json.dumps(payload))
        change(altered)
        manifest.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(IdentityBlock):
            verify_manifest(root, manifest, checksum)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IdentityBlock):
        verify_manifest(root, manifest, checksum)
    with pytest.raises(FileExistsError):
        build_manifest(root, manifest)
    entry = root / "backend" / "migration" / "spec005.py"
    entry.write_bytes(entry.read_bytes() + b"\nimport backend.migration.missing_required_dependency\n")
    with pytest.raises(IdentityBlock):
        verify_manifest(root, manifest, checksum)


def test_source_freeze_and_pointer_are_independent(tmp_path):
    pointer, manifests, historical, snapshot, pointer_sha = _source_fixture(tmp_path)
    assert verify_source(pointer, manifests, historical, snapshot, pointer_sha)
    with pytest.raises(IdentityBlock):
        verify_source(pointer, manifests, historical, snapshot, "0" * 64)
    original = (historical / "old.py").read_bytes()
    (historical / "old.py").write_bytes(original + b"# changed")
    with pytest.raises(IdentityBlock):
        verify_source(pointer, manifests, historical, snapshot, pointer_sha)
    (historical / "old.py").write_bytes(original)
    snapshot.write_bytes(snapshot.read_bytes() + b"x")
    with pytest.raises(IdentityBlock):
        verify_source(pointer, manifests, historical, snapshot, pointer_sha)
