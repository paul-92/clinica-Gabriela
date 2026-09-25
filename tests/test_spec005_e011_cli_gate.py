"""Gate E011: casos fail-closed e boundary sem executar migracao."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

from scripts import spec005_candidate_migration as cli


def _gate_variant(tmp_path, **changes):
    data = json.loads(cli.GATE_PATH.read_bytes())
    data.update(changes)
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_gate_is_pinned_and_authorization_is_required(tmp_path):
    assert cli.verify_e011_gate()["human_e011_reconfirmation"] == "GRANTED"
    with pytest.raises(ValueError):
        cli.verify_e011_gate(tmp_path / "missing.json")
    for change in ({"quality_gate_result": "QUALITY_GATE_FAIL"},
                   {"major01_status": "OPEN"},
                   {"human_e011_reconfirmation": "MISSING"},
                   {"e012_authorized": True},
                   {"promotion_authorized": True}):
        path, digest = _gate_variant(tmp_path, **change)
        with pytest.raises(ValueError):
            cli.verify_e011_gate(path, digest)
    tampered, _ = _gate_variant(tmp_path, human_e011_reconfirmation="GRANTED")
    with pytest.raises(ValueError):
        cli.verify_e011_gate(tampered)


def test_cli_has_no_unbound_path_and_pending_identity_blocks(tmp_path, monkeypatch):
    output = tmp_path / "candidate.db"
    monkeypatch.setattr(sys, "argv", ["e011", "--source", str(tmp_path / "source.db"),
                                      "--output", str(output)])
    with pytest.raises(SystemExit):
        cli.main()
    assert not output.exists()
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(json.dumps({"status": "PENDING_INDEPENDENT_IDENTITY_REREVIEW"}), encoding="utf-8")
    args = ["e011", "--source", str(tmp_path / "source.db"), "--output", str(output),
            "--identity-manifest", "identity.json", "--migration-manifest", "migration.json",
            "--migration-manifest-sha256", "a" * 64, "--pointer", "pointer.json",
            "--runtime-manifest-dir", "manifests", "--binding-checkpoint", str(checkpoint),
            "--binding-sha256", hashlib.sha256(checkpoint.read_bytes()).hexdigest()]
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit):
        cli.main()
    assert not output.exists()


def test_self_fabricated_pass_stops_before_execution_boundary(tmp_path, monkeypatch):
    from backend.cutover.spec005_execution_identity import canonical_bytes

    source = json.loads((cli.ROOT / "docs/audit/spec005-20260924-d00512-binding-checkpoint.json").read_bytes())["source_identity"]
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    manifest_sha = "a" * 64
    transformation_sha = "b" * 64
    review = tmp_path / "review.json"
    review.write_text(json.dumps({"result": "PASS", "migration_manifest_sha256": manifest_sha,
        "transformation_identity": transformation_sha,
        "source_identity_sha256": "4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe"}), encoding="utf-8")
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_bytes(canonical_bytes({
        "status": "E011_IDENTITY_INDEPENDENTLY_VERIFIED",
        "e011_authorization_gate_sha256": cli.GATE_SHA256,
        "contract_identity": "SPEC-005/D005-09+D005-10+D005-11+D005-12",
        "source_identity": source, "migration_manifest_sha256": manifest_sha,
        "transformation_identity": transformation_sha,
        "independent_identity_review_artifact": "review.json",
        "independent_identity_review_sha256": hashlib.sha256(review.read_bytes()).hexdigest(),
    }))
    monkeypatch.setattr(cli, "verify_manifest", lambda *args: manifest_sha)
    monkeypatch.setattr(cli, "verify_persisted_source", lambda *args, **kwargs: source)
    monkeypatch.setattr(cli, "bind_transformation", lambda *args, **kwargs: transformation_sha)
    import backend.migration.spec005 as migration
    class BoundaryReached(Exception):
        pass
    monkeypatch.setattr(migration, "migrate_finance_candidate", lambda *args, **kwargs: (_ for _ in ()).throw(BoundaryReached()))
    output = tmp_path / "candidate.db"
    monkeypatch.setattr(sys, "argv", ["e011", "--source", str(tmp_path / "source.db"),
        "--output", str(output), "--identity-manifest", "identity.json",
        "--migration-manifest", "migration.json", "--migration-manifest-sha256", manifest_sha,
        "--pointer", "pointer.json", "--runtime-manifest-dir", "manifests",
        "--binding-checkpoint", str(checkpoint),
        "--binding-sha256", hashlib.sha256(checkpoint.read_bytes()).hexdigest()])
    with pytest.raises(SystemExit):
        cli.main()
    assert not output.exists()
