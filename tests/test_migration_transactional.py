import sqlite3

import pytest

from backend.migration.manifests import (
    DecisionClass, DecisionStatus, MatchConfidence, MatchStatus, PkRelationStatus,
    Provenance, RemapEntry, RemapLifecycle, RemapManifest, SourceDatabase,
)
from backend.migration.transactional import (
    ForeignKeySource, LoadRecord, TransactionalMigrationError,
    load_in_global_transaction, reserve_canonical_ids,
)


def _entry(table, source_id, *, database=SourceDatabase.DESKTOP_LEGACY):
    provenance = Provenance(
        source_database=database, source_table=table,
        historical_reference=str(source_id), snapshot_version="snapshot-v1",
        rule_version="rules-v1", match_status=MatchStatus.EXCLUSIVE,
        match_confidence=MatchConfidence.HIGH, decision_class=DecisionClass.AUTO,
        decision_status=DecisionStatus.APPROVED,
        execution_reference="execution-v1", decision_reason_code="approved-fixture",
    )
    return RemapEntry(
        source_database=database, source_table=table, source_id=source_id,
        canonical_table=table, match_status=MatchStatus.EXCLUSIVE,
        match_confidence=MatchConfidence.HIGH,
        pk_relation_status=PkRelationStatus.NO_COUNTERPART,
        decision_class=DecisionClass.AUTO, decision_status=DecisionStatus.APPROVED,
        provenance=provenance,
    )


def _manifest(*entries):
    return RemapManifest(manifest_version="remap-approved-v1",
                         lifecycle=RemapLifecycle.APPROVED, entries=entries)


def test_reservation_is_reproducible_and_never_reuses_historical_pk():
    approved = _manifest(_entry("patients", 1), _entry("patients", 8))
    first = reserve_canonical_ids(approved)
    second = reserve_canonical_ids(approved)
    assert first == second
    assert [entry.canonical_id for entry in first.entries] == [9, 10]
    assert first.lifecycle is RemapLifecycle.RESERVED


def test_global_load_resolves_fk_from_source_map_and_commits():
    reserved = reserve_canonical_ids(_manifest(
        _entry("patients", 4), _entry("appointments", 2)))
    connection = sqlite3.connect(":memory:")
    connection.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE patients(id INTEGER PRIMARY KEY, label TEXT NOT NULL);
        CREATE TABLE appointments(id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL
          REFERENCES patients(id), label TEXT NOT NULL);
    """)
    counts = load_in_global_transaction(connection, reserved, (
        LoadRecord("desktop_legacy", "appointments", 2, {"label": "a"},
                   (ForeignKeySource("patient_id", "patients", 4),)),
        LoadRecord("desktop_legacy", "patients", 4, {"label": "p"}),
    ))
    assert counts["patients"] == counts["appointments"] == 1
    assert connection.execute("SELECT patient_id FROM appointments").fetchone() == (5,)


def test_failure_rolls_back_roots_and_dependents_together():
    reserved = reserve_canonical_ids(_manifest(
        _entry("patients", 4), _entry("appointments", 2)))
    connection = sqlite3.connect(":memory:")
    connection.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE patients(id INTEGER PRIMARY KEY, label TEXT NOT NULL);
        CREATE TABLE appointments(id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL
          REFERENCES patients(id), label TEXT NOT NULL);
    """)
    with pytest.raises(TransactionalMigrationError, match="FK sem pai"):
        load_in_global_transaction(connection, reserved, (
            LoadRecord("desktop_legacy", "patients", 4, {"label": "p"}),
            LoadRecord("desktop_legacy", "appointments", 2, {"label": "a"},
                       (ForeignKeySource("patient_id", "patients", 999),)),
        ))
    assert connection.execute("SELECT COUNT(*) FROM patients").fetchone() == (0,)
