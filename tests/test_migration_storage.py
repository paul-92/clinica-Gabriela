from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.migration import (
    ExecutionManifest,
    ExecutionStatus,
    ManifestAlreadyExistsError,
    ManifestChecksumMismatchError,
    ManifestDurabilityError,
    ManifestInvalidContentError,
    ManifestNotFoundError,
    ManifestPersistenceError,
    ManifestUnexpectedTypeError,
    ManifestValidationStatus,
    RemapLifecycle,
    RemapManifest,
    canonical_json,
    load_stored_manifest,
    manifest_checksum,
    save_manifest,
)


NOW = datetime(2026, 2, 1, tzinfo=timezone.utc)


def remap(version="remap-fixture-v1"):
    return RemapManifest(manifest_version=version, lifecycle=RemapLifecycle.DRAFT, entries=())


def execution():
    return ExecutionManifest(
        execution_id="execution-fixture-001",
        created_at=NOW,
        tool_version="tool-v1",
        plan_version="plan-v1",
        rule_version="rules-v1",
        status=ExecutionStatus.PLANNED,
        source_snapshot_references=("snapshot://fixture/a", "snapshot://fixture/b"),
        validation_status=ManifestValidationStatus.PENDING,
    )


def test_save_load_round_trip_and_deterministic_bytes(tmp_path):
    original = remap()
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    checksum = save_manifest(first, original)
    save_manifest(second, original)

    assert first.read_bytes() == second.read_bytes() == canonical_json(original).encode("utf-8")
    assert checksum == manifest_checksum(original)
    assert load_stored_manifest(first, RemapManifest) == original


def test_expected_checksum_is_accepted_and_mismatch_rejected(tmp_path):
    path = tmp_path / "manifest.json"
    checksum = save_manifest(path, remap())
    assert load_stored_manifest(path, RemapManifest, expected_checksum=checksum) == remap()

    with pytest.raises(ManifestChecksumMismatchError):
        load_stored_manifest(path, RemapManifest, expected_checksum="0" * 64)


@pytest.mark.parametrize("content", [b"not-json", b"[]", b'{"broken":'])
def test_invalid_json_or_structure_is_rejected(tmp_path, content):
    path = tmp_path / "invalid.json"
    path.write_bytes(content)
    with pytest.raises(ManifestInvalidContentError):
        load_stored_manifest(path, RemapManifest)


def test_tampered_or_noncanonical_file_is_rejected(tmp_path):
    path = tmp_path / "manifest.json"
    save_manifest(path, remap())
    path.write_bytes(path.read_bytes().replace(b"remap-fixture-v1", b"remap-fixture-v2"))
    with pytest.raises(ManifestChecksumMismatchError):
        load_stored_manifest(path, RemapManifest, expected_checksum=manifest_checksum(remap()))

    path.write_text(canonical_json(remap()).replace(",", ", "), encoding="utf-8")
    with pytest.raises(ManifestInvalidContentError, match="serializacao canonica"):
        load_stored_manifest(path, RemapManifest)


def test_unexpected_type_and_missing_file_are_controlled(tmp_path):
    path = tmp_path / "execution.json"
    save_manifest(path, execution())
    with pytest.raises(ManifestUnexpectedTypeError):
        load_stored_manifest(path, RemapManifest)
    with pytest.raises(ManifestUnexpectedTypeError):
        load_stored_manifest(path, dict)  # type: ignore[arg-type]
    with pytest.raises(ManifestNotFoundError):
        load_stored_manifest(tmp_path / "missing.json", RemapManifest)


def test_overwrite_policy_preserves_or_replaces_existing_file(tmp_path):
    path = tmp_path / "manifest.json"
    original = remap()
    replacement = remap("remap-fixture-v2")
    save_manifest(path, original)

    with pytest.raises(ManifestAlreadyExistsError):
        save_manifest(path, replacement)
    assert load_stored_manifest(path, RemapManifest) == original

    save_manifest(path, replacement, overwrite=True)
    assert load_stored_manifest(path, RemapManifest) == replacement


def test_failure_before_atomic_promotion_preserves_destination_and_cleans_temp(tmp_path, monkeypatch):
    path = tmp_path / "manifest.json"
    original = remap()
    save_manifest(path, original)

    def fail_replace(source, destination):
        raise OSError("controlled fixture failure")

    monkeypatch.setattr("backend.migration.storage.os.replace", fail_replace)
    with pytest.raises(ManifestPersistenceError):
        save_manifest(path, remap("remap-fixture-v2"), overwrite=True)

    assert load_stored_manifest(path, RemapManifest) == original
    assert [item.name for item in tmp_path.iterdir()] == ["manifest.json"]


def test_overwrite_false_race_preserves_competing_file_and_cleans_temp(tmp_path, monkeypatch):
    path = tmp_path / "manifest.json"
    competing = remap("remap-competing-v1")

    def competing_link(source, destination):
        Path(destination).write_bytes(canonical_json(competing).encode("utf-8"))
        raise FileExistsError("controlled fixture race")

    monkeypatch.setattr("backend.migration.storage.os.link", competing_link)
    with pytest.raises(ManifestAlreadyExistsError):
        save_manifest(path, remap())

    assert load_stored_manifest(path, RemapManifest) == competing
    assert [item.name for item in tmp_path.iterdir()] == ["manifest.json"]


def test_directory_fsync_failure_reports_promoted_but_unconfirmed_durability(
    tmp_path, monkeypatch
):
    path = tmp_path / "manifest.json"
    original = remap()
    replacement = remap("remap-fixture-v2")
    save_manifest(path, original)

    def fail_directory_fsync(directory):
        raise OSError("controlled fixture durability failure")

    monkeypatch.setattr(
        "backend.migration.storage._fsync_directory", fail_directory_fsync
    )
    with pytest.raises(ManifestDurabilityError) as error:
        save_manifest(path, replacement, overwrite=True)

    assert error.value.destination_promoted is True
    assert load_stored_manifest(path, RemapManifest) == replacement
    assert path.read_bytes() == canonical_json(replacement).encode("utf-8")
    assert [item.name for item in tmp_path.iterdir()] == ["manifest.json"]


def test_parent_creation_is_explicit(tmp_path):
    path = tmp_path / "nested" / "manifest.json"
    with pytest.raises(ManifestPersistenceError):
        save_manifest(path, remap())
    save_manifest(path, remap(), create_parents=True)
    assert path.is_file()


def test_import_has_no_filesystem_side_effects(tmp_path):
    before = list(tmp_path.iterdir())
    __import__("backend.migration.storage")
    assert list(tmp_path.iterdir()) == before == []


def test_fixtures_use_only_technical_fictitious_values():
    serialized = canonical_json(execution()).casefold()
    forbidden = ("cpf", "password", "token", "clinical_notes", "patient_name")
    assert not any(term in serialized for term in forbidden)
