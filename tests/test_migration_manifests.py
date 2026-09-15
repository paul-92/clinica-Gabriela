from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.migration import (
    DecisionClass,
    DecisionStatus,
    ExecutionManifest,
    ExecutionStatus,
    IntegrityStatus,
    HistoricalCreatedAtEntry,
    HistoricalProvenanceSupplement,
    ManifestValidationStatus,
    MatchConfidence,
    MatchStatus,
    PkRelationStatus,
    Provenance,
    RemapEntry,
    RemapLifecycle,
    RemapManifest,
    SnapshotManifest,
    SourceDatabase,
    canonical_json,
    load_manifest,
    manifest_checksum,
    write_manifest,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def provenance(
    *,
    source_id=1,
    status=MatchStatus.EXCLUSIVE,
    confidence=MatchConfidence.HIGH,
    decision=DecisionClass.AUTO,
    decision_status=DecisionStatus.APPROVED,
    group=None,
):
    return Provenance(
        source_database=SourceDatabase.DESKTOP_LEGACY,
        source_table="patients",
        historical_reference=str(source_id),
        snapshot_version="snapshot-v1",
        rule_version="rules-v1",
        match_status=status,
        match_confidence=confidence,
        decision_class=decision,
        decision_status=decision_status,
        canonical_group_ref=group,
        execution_reference="execution-test-001",
        decision_reason_code="fixture-approved",
    )


def entry(*, source_id=1, canonical_id=None, **overrides):
    values = {
        "source_database": SourceDatabase.DESKTOP_LEGACY,
        "source_table": "patients",
        "source_id": source_id,
        "canonical_table": "patients",
        "canonical_id": canonical_id,
        "match_status": MatchStatus.EXCLUSIVE,
        "match_confidence": MatchConfidence.HIGH,
        "pk_relation_status": PkRelationStatus.NO_COUNTERPART,
        "decision_class": DecisionClass.AUTO,
        "decision_status": DecisionStatus.APPROVED,
        "canonical_group_ref": None,
    }
    values.update(overrides)
    values["provenance"] = provenance(
        source_id=source_id,
        status=values["match_status"],
        confidence=values["match_confidence"],
        decision=values["decision_class"],
        decision_status=values["decision_status"],
        group=values["canonical_group_ref"],
    )
    return RemapEntry(**values)


def manifest(*entries, lifecycle=RemapLifecycle.DRAFT):
    return RemapManifest(
        manifest_version="remap-v1",
        lifecycle=lifecycle,
        entries=entries,
    )


def test_valid_remap_entry_and_invalid_states_are_rejected():
    assert entry().logical_key == (SourceDatabase.DESKTOP_LEGACY, "patients", 1)

    with pytest.raises(ValidationError, match="AUTO exige matching resolvido"):
        entry(
            match_status=MatchStatus.AMBIGUOUS,
            match_confidence=MatchConfidence.LOW,
            decision_class=DecisionClass.AUTO,
            decision_status=DecisionStatus.PENDING,
            pk_relation_status=PkRelationStatus.NOT_COMPARED,
        )


def test_block_is_not_consumable_and_consumed_requires_canonical_id():
    blocked = entry(
        decision_class=DecisionClass.BLOCK,
        decision_status=DecisionStatus.PENDING,
        match_status=MatchStatus.UNRESOLVED,
        match_confidence=MatchConfidence.NONE,
        pk_relation_status=PkRelationStatus.NOT_COMPARED,
    )
    with pytest.raises(ValidationError, match="BLOCK"):
        manifest(blocked, lifecycle=RemapLifecycle.CONSUMED)
    with pytest.raises(ValidationError, match="exige canonical_id"):
        manifest(entry(), lifecycle=RemapLifecycle.CONSUMED)


def test_duplicate_logical_key_is_rejected():
    with pytest.raises(ValidationError, match="chave logica duplicada"):
        manifest(entry(), entry())


def test_lifecycle_valid_transitions_and_forbidden_skip():
    current = manifest(entry())
    current = current.transition_to(RemapLifecycle.REVIEWED)
    current = current.transition_to(RemapLifecycle.APPROVED)
    reserved_entry = entry(canonical_id=101)
    current = current.transition_to(RemapLifecycle.RESERVED, entries=(reserved_entry,))
    current = current.transition_to(RemapLifecycle.CONSUMED)
    current = current.transition_to(RemapLifecycle.VERIFIED)
    assert current.lifecycle is RemapLifecycle.VERIFIED

    with pytest.raises(ValueError, match="transicao proibida"):
        manifest(entry()).transition_to(RemapLifecycle.APPROVED)


def test_shared_canonical_id_requires_equivalent_group():
    with pytest.raises(ValidationError, match="canonical_id compartilhado"):
        manifest(
            entry(source_id=1, canonical_id=200),
            entry(source_id=2, canonical_id=200),
            lifecycle=RemapLifecycle.RESERVED,
        )


def test_exclusive_preserves_counterpart_pk_provenance():
    preserved = entry(
        match_status=MatchStatus.EXCLUSIVE,
        pk_relation_status=PkRelationStatus.SAME_PK_DIFFERENT_IDENTITY,
        decision_class=DecisionClass.REVIEW,
    )

    assert preserved.match_status is MatchStatus.EXCLUSIVE
    assert preserved.pk_relation_status is PkRelationStatus.SAME_PK_DIFFERENT_IDENTITY


def test_serialization_round_trip_is_deterministic(tmp_path):
    original = manifest(entry())
    path = tmp_path / "remap.json"
    write_manifest(path, original)
    loaded = load_manifest(path, RemapManifest)

    assert loaded == original
    assert path.read_text(encoding="utf-8") == canonical_json(original)
    assert canonical_json(loaded) == canonical_json(original)


def test_checksum_is_stable_and_changes_with_content():
    first = manifest(entry())
    same = manifest(entry())
    changed = RemapManifest(manifest_version="remap-v2", entries=(entry(),))

    assert manifest_checksum(first) == manifest_checksum(same)
    assert manifest_checksum(first) != manifest_checksum(changed)


def test_snapshot_manifest_validates_metadata_and_integrity(tmp_path):
    snapshot = SnapshotManifest(
        source_label=SourceDatabase.DESKTOP_LEGACY,
        snapshot_reference="snapshot://fixture/desktop-v1",
        checksum_sha256=HASH_A,
        size_bytes=128,
        captured_at=NOW,
        schema_version="schema-v1",
        schema_checksum_sha256=HASH_B,
        integrity_status=IntegrityStatus.PASSED,
        foreign_key_check_violations=0,
    )
    path = tmp_path / "snapshot.json"
    write_manifest(path, snapshot)
    assert load_manifest(path, SnapshotManifest) == snapshot

    with pytest.raises(ValidationError, match="violacoes de FK"):
        snapshot.model_copy(
            update={"foreign_key_check_violations": 1}
        ).model_validate(
            {**snapshot.model_dump(), "foreign_key_check_violations": 1}
        )


def test_execution_manifest_validates_completed_gate(tmp_path):
    execution = ExecutionManifest(
        execution_id="execution-test-001",
        created_at=NOW,
        tool_version="migrator-v1",
        plan_version="plan-v1",
        rule_version="rules-v1",
        status=ExecutionStatus.COMPLETED,
        source_snapshot_references=("snapshot://fixture/desktop", "snapshot://fixture/backend"),
        remap_version="remap-v1",
        remap_checksum_sha256=HASH_A,
        canonical_target_reference="canonical://fixture/candidate-v1",
        validation_status=ManifestValidationStatus.PASSED,
    )
    path = tmp_path / "execution.json"
    write_manifest(path, execution)
    assert load_manifest(path, ExecutionManifest) == execution

    with pytest.raises(ValidationError, match="completed exige"):
        ExecutionManifest(
            **{
                **execution.model_dump(),
                "validation_status": ManifestValidationStatus.FAILED,
            }
        )


def test_provenance_forbids_sensitive_or_arbitrary_metadata():
    with pytest.raises(ValidationError, match="dado sensivel"):
        Provenance(
            **{
                **provenance().model_dump(),
                "decision_reason_code": "password-secret",
            }
        )
    with pytest.raises(ValidationError, match="Extra inputs"):
        Provenance(**{**provenance().model_dump(), "clinical_notes": "fixture"})


def test_loading_rejects_unknown_fields_and_arbitrary_types(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(
        canonical_json(manifest(entry())).replace(
            '"manifest_version":"remap-v1"',
            '"unexpected":"value","manifest_version":"remap-v1"',
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="Extra inputs"):
        load_manifest(path, RemapManifest)
    with pytest.raises(TypeError, match="somente manifests tipados"):
        canonical_json({"arbitrary": "object"})  # type: ignore[arg-type]


def test_models_need_only_fictitious_manifest_files(tmp_path):
    assert list(tmp_path.iterdir()) == []
    write_manifest(tmp_path / "manifest.json", manifest(entry()))
    assert [item.name for item in tmp_path.iterdir()] == ["manifest.json"]


def test_historical_provenance_supplement_round_trip(tmp_path):
    supplement = HistoricalProvenanceSupplement(
        supplement_version="created-at-v1",
        execution_reference="execution-test-001",
        freeze_reference="freeze-v1",
        remap_version="remap-v1",
        remap_checksum_sha256=HASH_A,
        entries=(HistoricalCreatedAtEntry(
            source_database=SourceDatabase.DESKTOP_LEGACY,
            source_table="users",
            source_id=1,
            created_at=NOW.isoformat(),
        ),),
    )
    path = tmp_path / "supplement.json"
    write_manifest(path, supplement)
    assert load_manifest(path, HistoricalProvenanceSupplement) == supplement


def test_historical_provenance_rejects_duplicate_and_invalid_timestamp():
    entry = HistoricalCreatedAtEntry(
        source_database=SourceDatabase.DESKTOP_LEGACY,
        source_table="users",
        source_id=1,
        created_at=NOW.isoformat(),
    )
    with pytest.raises(ValidationError, match="duplicada"):
        HistoricalProvenanceSupplement(
            supplement_version="created-at-v1",
            execution_reference="execution-test-001",
            freeze_reference="freeze-v1",
            remap_version="remap-v1",
            remap_checksum_sha256=HASH_A,
            entries=(entry, entry),
        )
    with pytest.raises(ValidationError, match="ISO-8601"):
        entry.model_copy(update={"created_at": "invalid"}).model_validate(
            {**entry.model_dump(), "created_at": "invalid"}
        )
