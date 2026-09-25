"""Revisao E011 em harness sintetico; nenhuma migracao ou fonte real."""

import hashlib
import json
import sys

import pytest

from backend.cutover.spec005_execution_identity import canonical_bytes
from scripts import spec005_candidate_migration as cli
from scripts.spec005_provision_e011_review import provision


SOURCE_SHA = "4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe"
MIGRATION_SHA = "a" * 64
TRANSFORMATION_SHA = "b" * 64
CONTRACT = "SPEC-005/D005-09+D005-10+D005-11+D005-12"


def fixture_subject(tmp_path):
    (tmp_path / "docs/audit").mkdir(parents=True)
    source = json.loads((cli.ROOT / "docs/audit/spec005-20260924-d00512-binding-checkpoint.json").read_bytes())["source_identity"]
    review = {
        "schema_version": "spec005-e011-independent-review-v1",
        "specification": "SPEC-005", "execution_item": "E011",
        "quality_gate_result": "QUALITY_GATE_PASS",
        "blocker01_status": "CLOSED_BY_INDEPENDENT_REVIEW",
        "source_identity_sha256": SOURCE_SHA,
        "migration_manifest_version": "synthetic-v7",
        "migration_manifest_sha256": MIGRATION_SHA,
        "transformation_identity": TRANSFORMATION_SHA,
        "contract_identity": CONTRACT,
    }
    checkpoint = {
        "status": "E011_IDENTITY_INDEPENDENTLY_VERIFIED",
        "e011_authorization_gate_sha256": cli.GATE_SHA256,
        "contract_identity": CONTRACT,
        "source_identity": source,
        "source_identity_sha256": SOURCE_SHA,
        "migration_manifest_version": "synthetic-v7",
        "migration_manifest_sha256": MIGRATION_SHA,
        "transformation_identity": TRANSFORMATION_SHA,
    }
    gate = {"source_identity_sha256": SOURCE_SHA}
    return review, checkpoint, gate


def issue_synthetic(tmp_path, review, checkpoint):
    review_file = tmp_path / "synthetic-review-input.json"
    review_file.write_bytes(canonical_bytes(review))
    digest = provision(tmp_path, review_file)
    relative = f"docs/audit/spec005-e011-review-{digest}.json"
    checkpoint["independent_identity_review_artifact"] = relative
    checkpoint["independent_identity_review_sha256"] = digest
    return tmp_path / relative


def test_a_and_f_self_asserted_pass_without_authority_blocks(tmp_path):
    review, checkpoint, gate = fixture_subject(tmp_path)
    raw = canonical_bytes(review)
    digest = hashlib.sha256(raw).hexdigest()
    relative = f"docs/audit/spec005-e011-review-{digest}.json"
    (tmp_path / relative).write_bytes(raw)
    checkpoint.update(independent_identity_review_artifact=relative,
                      independent_identity_review_sha256=digest)
    with pytest.raises((OSError, ValueError)):
        cli.verify_independent_review(checkpoint, gate, tmp_path)


@pytest.mark.parametrize("label,change", [
    ("B_source", {"source_identity_sha256": "c" * 64}),
    ("C_migration", {"migration_manifest_sha256": "c" * 64}),
    ("D_transformation", {"transformation_identity": "c" * 64}),
    ("G_scope", {"contract_identity": "OTHER"}),
])
def test_subject_mismatches_block(tmp_path, label, change):
    review, checkpoint, gate = fixture_subject(tmp_path)
    issue_synthetic(tmp_path, review, checkpoint)
    checkpoint.update(change)
    with pytest.raises(ValueError):
        cli.verify_independent_review(checkpoint, gate, tmp_path)


def test_e_tampered_review_blocks(tmp_path):
    review, checkpoint, gate = fixture_subject(tmp_path)
    path = issue_synthetic(tmp_path, review, checkpoint)
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError):
        cli.verify_independent_review(checkpoint, gate, tmp_path)


def test_g_authority_for_another_spec_blocks(tmp_path):
    review, checkpoint, gate = fixture_subject(tmp_path)
    review["specification"] = "SPEC-OTHER"
    raw = canonical_bytes(review)
    digest = hashlib.sha256(raw).hexdigest()
    relative = f"docs/audit/spec005-e011-review-{digest}.json"
    (tmp_path / relative).write_bytes(raw)
    (tmp_path / cli.AUTHORITY_RELATIVE).write_bytes(canonical_bytes({
        "schema_version": "spec005-e011-review-authority-v1",
        "review_artifact": relative, "review_sha256": digest}))
    checkpoint.update(independent_identity_review_artifact=relative,
                      independent_identity_review_sha256=digest)
    with pytest.raises(ValueError):
        cli.verify_independent_review(checkpoint, gate, tmp_path)


@pytest.mark.parametrize("state", ["PENDING", "FAIL"])
def test_h_i_nonpassing_authority_blocks(tmp_path, state):
    review, checkpoint, gate = fixture_subject(tmp_path)
    review["quality_gate_result"] = state
    raw = canonical_bytes(review)
    digest = hashlib.sha256(raw).hexdigest()
    relative = f"docs/audit/spec005-e011-review-{digest}.json"
    (tmp_path / relative).write_bytes(raw)
    (tmp_path / cli.AUTHORITY_RELATIVE).write_bytes(canonical_bytes({
        "schema_version": "spec005-e011-review-authority-v1",
        "review_artifact": relative, "review_sha256": digest}))
    checkpoint.update(independent_identity_review_artifact=relative,
                      independent_identity_review_sha256=digest)
    with pytest.raises(ValueError):
        cli.verify_independent_review(checkpoint, gate, tmp_path)


def test_j_synthetic_authority_reaches_prewrite_boundary(tmp_path, monkeypatch):
    review, checkpoint, gate = fixture_subject(tmp_path)
    issue_synthetic(tmp_path, review, checkpoint)
    cp = tmp_path / "checkpoint.json"
    cp.write_bytes(canonical_bytes(checkpoint))
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "verify_e011_gate", lambda: gate)
    monkeypatch.setattr(cli, "verify_manifest", lambda *args: MIGRATION_SHA)
    monkeypatch.setattr(cli, "verify_persisted_source", lambda *args, **kwargs: checkpoint["source_identity"])
    monkeypatch.setattr(cli, "bind_transformation", lambda *args, **kwargs: TRANSFORMATION_SHA)
    # Source hash in the real CLI is independently computed; this fixture uses
    # the actual canonical source structure and checks the same digest.
    import backend.migration.spec005 as migration
    class PrewriteBoundary(Exception):
        pass
    monkeypatch.setattr(migration, "migrate_finance_candidate", lambda *args, **kwargs: (_ for _ in ()).throw(PrewriteBoundary()))
    output = tmp_path / "candidate.db"
    monkeypatch.setattr(sys, "argv", ["e011", "--source", str(tmp_path / "synthetic.db"),
        "--output", str(output), "--identity-manifest", "synthetic-identity.json",
        "--migration-manifest", str(tmp_path / "manifest.json"),
        "--migration-manifest-sha256", MIGRATION_SHA,
        "--pointer", str(tmp_path / "pointer.json"),
        "--runtime-manifest-dir", str(tmp_path),
        "--binding-checkpoint", str(cp),
        "--binding-sha256", hashlib.sha256(cp.read_bytes()).hexdigest()])
    with pytest.raises(PrewriteBoundary):
        cli.main()
    assert not output.exists()
