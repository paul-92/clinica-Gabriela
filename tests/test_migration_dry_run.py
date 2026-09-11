import sqlite3

import pytest

from backend.migration import (
    DryRunGate,
    DryRunInvalidSnapshotError,
    DryRunOperationalPathError,
    SourceDatabase,
    ValidatedSnapshot,
    create_sqlite_snapshot,
    run_snapshot_dry_run,
)
from scripts.sqlite_inventory import DEFAULT_DESKTOP_DB


SENTINELS = (
    "PRIVATE-PATIENT-NAME",
    "PRIVATE-CPF",
    "PRIVATE-CLINICAL-CONTENT",
    "PRIVATE-PASSWORD-HASH",
)


def make_users_database(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT)"
        )
        connection.executemany("INSERT INTO users VALUES (?, ?, ?)", rows)


def snapshots(tmp_path, desktop_rows, backend_rows):
    desktop_source = tmp_path / "desktop-source.db"
    backend_source = tmp_path / "backend-source.db"
    make_users_database(desktop_source, desktop_rows)
    make_users_database(backend_source, backend_rows)
    return snapshot_sources(tmp_path, desktop_source, backend_source)


def snapshot_sources(tmp_path, desktop_source, backend_source):
    desktop = create_sqlite_snapshot(
        desktop_source, tmp_path / "desktop-snapshot.db",
        source_label=SourceDatabase.DESKTOP_LEGACY,
        snapshot_reference="snapshot://fixture/desktop-v1",
    )
    backend = create_sqlite_snapshot(
        backend_source, tmp_path / "backend-snapshot.db",
        source_label=SourceDatabase.BACKEND_LEGACY,
        snapshot_reference="snapshot://fixture/backend-v1",
    )
    return desktop_source, backend_source, desktop, backend


def test_clean_validated_snapshots_produce_aggregate_pass_without_writes(tmp_path):
    sources = snapshots(
        tmp_path,
        [(900001, "fixture-user", SENTINELS[3])],
        [(800001, "fixture-user", SENTINELS[3])],
    )
    desktop_source, backend_source, desktop, backend = sources
    paths = (desktop_source, backend_source, desktop.path, backend.path)
    before = {path: (path.stat().st_size, path.stat().st_mtime_ns, path.read_bytes()) for path in paths}

    report = run_snapshot_dry_run(
        desktop, backend, execution_reference="execution-fixture-pass"
    )

    assert report.gate is DryRunGate.PASS
    assert report.identity.equivalent == 1
    assert report.foreign_keys.orphan_references == 0
    assert report.projected_canonical_counts == {"users": 1}
    assert not (tmp_path / "canonical.db").exists()
    assert {path: (path.stat().st_size, path.stat().st_mtime_ns, path.read_bytes()) for path in paths} == before


def test_dry_run_rejects_unvalidated_value_and_operational_path(tmp_path):
    _, _, desktop, backend = snapshots(tmp_path, [], [])
    with pytest.raises(DryRunInvalidSnapshotError):
        run_snapshot_dry_run(
            desktop.path, backend, execution_reference="execution-fixture-invalid"
        )
    operational = ValidatedSnapshot(path=DEFAULT_DESKTOP_DB, manifest=desktop.manifest)
    with pytest.raises(DryRunOperationalPathError):
        run_snapshot_dry_run(
            operational, backend, execution_reference="execution-fixture-operational"
        )


def test_report_excludes_pii_sentinels_fingerprints_and_individual_ids(tmp_path):
    _, _, desktop, backend = snapshots(
        tmp_path,
        [(900001, SENTINELS[0], SENTINELS[3])],
        [(800001, SENTINELS[0], SENTINELS[2])],
    )
    serialized = run_snapshot_dry_run(
        desktop, backend, execution_reference="execution-fixture-privacy"
    ).model_dump_json()
    assert not any(sentinel in serialized for sentinel in SENTINELS)
    assert "900001" not in serialized
    assert "800001" not in serialized
    assert "fingerprint" not in serialized.casefold()


def test_ambiguous_identity_requires_review(tmp_path):
    _, _, desktop, backend = snapshots(
        tmp_path,
        [(900001, "duplicate-fixture", "hash-a"), (900002, "duplicate-fixture", "hash-b")],
        [(800001, "duplicate-fixture", "hash-c")],
    )
    report = run_snapshot_dry_run(
        desktop, backend, execution_reference="execution-fixture-review"
    )
    assert report.gate is DryRunGate.REVIEW_REQUIRED
    assert report.review_count > 0
    assert "identity_review_pending" in report.reasons


def test_identity_conflict_blocks_dry_run(tmp_path):
    _, _, desktop, backend = snapshots(
        tmp_path,
        [(900001, "desktop-fixture", "hash-a")],
        [(900001, "backend-fixture", "hash-b")],
    )
    report = run_snapshot_dry_run(
        desktop, backend, execution_reference="execution-fixture-block"
    )
    assert report.gate is DryRunGate.BLOCKED
    assert report.block_count > 0
    assert "identity_conflict" in report.reasons


def test_blocked_takes_precedence_over_review_required(tmp_path):
    desktop_source = tmp_path / "desktop-source.db"
    backend_source = tmp_path / "backend-source.db"
    for path, username in (
        (desktop_source, "desktop-conflict"),
        (backend_source, "backend-conflict"),
    ):
        make_users_database(path, [(910001, username, "hash-fixture")])
        with sqlite3.connect(path) as connection:
            connection.execute(
                "CREATE TABLE clinic_settings (id INTEGER PRIMARY KEY, clinic_name TEXT)"
            )
    _, _, desktop, backend = snapshot_sources(
        tmp_path, desktop_source, backend_source
    )

    report = run_snapshot_dry_run(
        desktop, backend, execution_reference="execution-fixture-precedence"
    )

    assert report.block_count > 0
    assert report.review_count > 0
    assert report.gate is DryRunGate.BLOCKED


def test_clinic_settings_requires_review_without_other_block(tmp_path):
    desktop_source = tmp_path / "desktop-source.db"
    backend_source = tmp_path / "backend-source.db"
    for path in (desktop_source, backend_source):
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as connection:
            connection.execute(
                "CREATE TABLE clinic_settings (id INTEGER PRIMARY KEY, clinic_name TEXT)"
            )
    _, _, desktop, backend = snapshot_sources(
        tmp_path, desktop_source, backend_source
    )

    report = run_snapshot_dry_run(
        desktop, backend, execution_reference="execution-fixture-settings-review"
    )

    assert "clinic_settings_review_pending" in report.reasons
    assert report.review_count > 0
    assert report.block_count == 0
    assert report.gate is DryRunGate.REVIEW_REQUIRED


def test_ambiguous_payments_never_pass_or_infer_automatic_deduplication(tmp_path):
    desktop_source = tmp_path / "desktop-source.db"
    backend_source = tmp_path / "backend-source.db"
    payment_id = 920001
    for path, amount in ((desktop_source, 100), (backend_source, 200)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as connection:
            connection.execute(
                "CREATE TABLE payments ("
                "id INTEGER PRIMARY KEY, patient_id INTEGER, appointment_id INTEGER, "
                "due_date TEXT, amount NUMERIC)"
            )
            connection.execute(
                "INSERT INTO payments VALUES (?, ?, NULL, ?, ?)",
                (payment_id, 930001, "2026-03-01", amount),
            )
    _, _, desktop, backend = snapshot_sources(
        tmp_path, desktop_source, backend_source
    )

    report = run_snapshot_dry_run(
        desktop, backend, execution_reference="execution-fixture-payments-review"
    )
    serialized = report.model_dump_json()

    assert report.identity.ambiguities > 0
    assert report.review_count > 0
    assert report.gate is not DryRunGate.PASS
    assert "payments" not in report.projected_canonical_counts
    assert report.identity.equivalent == 0
    assert str(payment_id) not in serialized
    assert "930001" not in serialized


def test_dry_run_module_import_has_no_side_effects(tmp_path):
    before = list(tmp_path.iterdir())
    __import__("backend.migration.dry_run")
    assert list(tmp_path.iterdir()) == before == []
