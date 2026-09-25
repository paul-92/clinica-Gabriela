import json
import sqlite3
from datetime import datetime, timezone

import pytest

from backend.services.recovery import (
    APPLICATION_VERSION,
    DAILY_TIMEZONE,
    RUNTIME_VERSION,
    RecoveryAuthorizationError,
    RecoveryValidationError,
    apply_retention,
    create_backup,
    create_recovery_unit,
    persistent_paths,
    pre_update_backup,
    restore_backup,
    should_run_daily,
    validate_manifest,
)


def _database(path, value="original"):
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA user_version=5")
        connection.execute("CREATE TABLE records (value TEXT NOT NULL)")
        connection.execute("INSERT INTO records VALUES (?)", (value,))
        connection.commit()
    finally:
        connection.close()


def test_persistent_layout_is_frozen(tmp_path):
    paths = persistent_paths(localappdata=tmp_path)
    assert paths.persistent_root == (tmp_path / "ClinicaGabriela").resolve()
    assert paths.runtime_root == paths.persistent_root / "runtime"
    assert paths.database_root == paths.runtime_root / "generations"
    assert paths.backup_root == paths.runtime_root / "backups"


def test_backup_uses_manifest_and_validates_before_publish(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    result = create_backup(source, destination_root=tmp_path / "backups", generation=9)
    assert result.database_path.name == "canonical.database.db"
    assert result.manifest["privacy_safe"] is True
    assert result.manifest["attachments_scope"] == "none"
    assert result.manifest["encryption"]["status"] == "not_enabled"
    assert result.manifest["application_version"] == APPLICATION_VERSION
    assert result.manifest["runtime_version"] == RUNTIME_VERSION
    assert validate_manifest(result.package_dir, expected_generation=9)["validation_status"] == "passed"
    assert not list(result.package_dir.glob("*.tmp"))


def test_recovery_unit_has_frozen_two_file_shape(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    package = create_recovery_unit(source, tmp_path / "recovery-package", generation=9)
    assert {item.name for item in package.package_dir.iterdir()} == {
        "canonical.database.db", "recovery-manifest.json"
    }
    validate_manifest(package.package_dir, expected_generation=9, expected_user_version=5)


def test_restore_requires_admin_and_mandatory_pre_restore(tmp_path):
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    _database(source, "to-restore")
    _database(target, "current")
    package = create_backup(source, destination_root=tmp_path / "backups", generation=9)
    with pytest.raises(RecoveryAuthorizationError):
        restore_backup(package.package_dir, target, role="reception")
    restore_backup(package.package_dir, target, role="admin", expected_generation=9,
                   pre_restore_root=tmp_path / "pre-restore")
    with sqlite3.connect(target) as connection:
        assert connection.execute("SELECT value FROM records").fetchone()[0] == "to-restore"
    assert list((tmp_path / "pre-restore").glob("backup-*/recovery-manifest.json"))


def test_incompatible_manifest_is_fail_closed(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    package = create_backup(source, destination_root=tmp_path / "backups")
    manifest_path = package.manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "future-schema"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RecoveryValidationError):
        validate_manifest(package.package_dir)


@pytest.mark.parametrize("field", ["runtime_version", "application_version", "schema_version"])
def test_incompatible_manifest_versions_are_fail_closed(tmp_path, field):
    source = tmp_path / "source.db"
    _database(source)
    package = create_backup(source, destination_root=tmp_path / "backups")
    manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
    manifest[field] = "incompatible"
    package.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RecoveryValidationError):
        validate_manifest(package.package_dir)


def test_incompatible_user_version_is_fail_closed(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    package = create_backup(source, destination_root=tmp_path / "backups")
    manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
    manifest["user_version"] = 99
    package.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RecoveryValidationError):
        validate_manifest(package.package_dir)


@pytest.mark.parametrize("field, value", [
    ("runtime_version", "future-runtime"),
    ("application_version", "future-application"),
])
def test_restore_rejects_incompatible_versions_before_pre_restore(tmp_path, field, value):
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    _database(source, "to-restore")
    _database(target, "current")
    package = create_backup(source, destination_root=tmp_path / "backups")
    manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
    manifest[field] = value
    package.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RecoveryValidationError):
        restore_backup(package.package_dir, target, role="admin",
                       pre_restore_root=tmp_path / "pre-restore")
    assert not list((tmp_path / "pre-restore").glob("backup-*/recovery-manifest.json"))


@pytest.mark.parametrize("extra", ["unexpected.txt", "nested"])
def test_recovery_package_rejects_extra_components(tmp_path, extra):
    source = tmp_path / "source.db"
    _database(source)
    package = create_backup(source, destination_root=tmp_path / "backups")
    extra_path = package.package_dir / extra
    extra_path.mkdir() if extra == "nested" else extra_path.write_text("unexpected")
    with pytest.raises(RecoveryValidationError):
        validate_manifest(package.package_dir)


def test_recovery_package_rejects_missing_required_component(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    package = create_backup(source, destination_root=tmp_path / "backups")
    package.manifest_path.unlink()
    with pytest.raises(RecoveryValidationError):
        validate_manifest(package.package_dir)


def test_recovery_package_rejects_database_checksum_tampering(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    package = create_backup(source, destination_root=tmp_path / "backups")
    package.database_path.write_bytes(package.database_path.read_bytes() + b"tampered")
    with pytest.raises(RecoveryValidationError):
        validate_manifest(package.package_dir)


def test_pre_update_failure_blocks_update(tmp_path):
    with pytest.raises(Exception, match="UPDATE=BLOCKED"):
        pre_update_backup(tmp_path / "missing.db", destination_root=tmp_path / "backups")


def test_retention_daily_rotation_keeps_seven(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    root = tmp_path / "backups"
    for index in range(8):
        create_backup(source, destination_root=root,
                      timestamp=datetime(2026, 9, 25, 10, 0, index, tzinfo=timezone.utc),
                      backup_type="daily")
    removed = apply_retention(root)
    assert len(removed) == 1
    assert len(list(root.glob("backup-*/recovery-manifest.json"))) == 7


def test_retention_weekly_rotation_keeps_four(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    root = tmp_path / "backups"
    for index in range(5):
        create_backup(source, destination_root=root,
                      timestamp=datetime(2026, 9, 25, 10, 0, index, tzinfo=timezone.utc),
                      backup_type="weekly")
    removed = apply_retention(root)
    assert len(removed) == 1


def test_retention_coexists_daily_weekly_and_protected(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    root = tmp_path / "backups"
    for index in range(8):
        create_backup(source, destination_root=root,
                      timestamp=datetime(2026, 9, 25, 10, 0, index, tzinfo=timezone.utc),
                      backup_type="daily")
    for index in range(5):
        create_backup(source, destination_root=root,
                      timestamp=datetime(2026, 8, 25, 10, 0, index, tzinfo=timezone.utc),
                      backup_type="weekly")
    protected = create_backup(source, destination_root=root,
                              timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                              backup_type="special")
    removed = apply_retention(root)
    assert len(removed) == 2
    assert protected.package_dir.exists()
    assert len(list(root.glob("backup-*/recovery-manifest.json"))) == 12


def test_retention_uses_sao_paulo_civil_timestamp_and_is_idempotent(tmp_path):
    source = tmp_path / "source.db"
    _database(source)
    root = tmp_path / "backups"
    for index in range(8):
        create_backup(source, destination_root=root,
                      timestamp=datetime(2026, 9, 25, 2, 0, index, tzinfo=timezone.utc),
                      backup_type="daily")
    assert len(apply_retention(root)) == 1
    assert apply_retention(root) == []


def test_daily_boundary_uses_sao_paulo():
    assert DAILY_TIMEZONE == "America/Sao_Paulo"
    previous = datetime(2026, 9, 24, 23, 30, tzinfo=timezone.utc)
    current = datetime(2026, 9, 25, 2, 30, tzinfo=timezone.utc)
    assert should_run_daily(last_success=previous, now=current) is False
    assert should_run_daily(last_success=None, now=current) is True
