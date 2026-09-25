"""Entrypoint E011: gate persistido, identidades e candidato isolado."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from backend.cutover.spec005_execution_identity import (
    bind_transformation, verify_manifest, verify_persisted_source,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "docs/audit/spec005-20260924-e011-authorization-gate.json"
GATE_SHA256 = "b331a7f4511b17967a2f77bffbf5c0e4eff7fc18e5e7bbe8d2eccc377fd40ff8"
AUTHORITY_RELATIVE = Path("docs/audit/spec005-e011-independent-review-authority.json")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_independent_review(checkpoint: dict, gate: dict, root: Path = ROOT) -> None:
    """Resolve a autoridade canonica, sem path ou digest escolhido pelo E011 caller.

    O registro e provisionado em outra fase, por criacao exclusiva. A protecao
    contra um usuario que controla todo o filesystem nao e alegada.
    """
    root = root.resolve(strict=True)
    authority = json.loads((root / AUTHORITY_RELATIVE).read_bytes())
    digest = authority["review_sha256"]
    if (authority.get("schema_version") != "spec005-e011-review-authority-v1"
            or not isinstance(digest, str) or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)):
        raise ValueError("registro canonico de revisao invalido")
    relative = Path("docs/audit") / f"spec005-e011-review-{digest}.json"
    if authority.get("review_artifact") != relative.as_posix():
        raise ValueError("artifact de revisao nao canonico")
    review_path = (root / relative).resolve(strict=True)
    if root not in review_path.parents:
        raise ValueError("artifact fora do repositorio")
    raw = review_path.read_bytes()
    if _sha(raw) != digest:
        raise ValueError("artifact de revisao alterado")
    review = json.loads(raw)
    required = {
        "schema_version": "spec005-e011-independent-review-v1",
        "specification": "SPEC-005", "execution_item": "E011",
        "quality_gate_result": "QUALITY_GATE_PASS",
        "blocker01_status": "CLOSED_BY_INDEPENDENT_REVIEW",
        "source_identity_sha256": gate["source_identity_sha256"],
        "migration_manifest_version": checkpoint["migration_manifest_version"],
        "migration_manifest_sha256": checkpoint["migration_manifest_sha256"],
        "transformation_identity": checkpoint["transformation_identity"],
        "contract_identity": checkpoint["contract_identity"],
    }
    if any(review.get(key) != value for key, value in required.items()):
        raise ValueError("subject ou estado de revisao diverge")
    if (checkpoint.get("independent_identity_review_artifact") != relative.as_posix()
            or checkpoint.get("independent_identity_review_sha256") != digest
            or checkpoint.get("source_identity_sha256") != gate["source_identity_sha256"]):
        raise ValueError("checkpoint diverge da autoridade canonica")


def verify_e011_gate(path: Path = GATE_PATH, expected_sha256: str = GATE_SHA256,
                     root: Path = ROOT) -> dict:
    """Confere Evidence fixada no CLI e o parecer independente referenciado."""
    try:
        raw = path.read_bytes()
        if _sha(raw) != expected_sha256:
            raise ValueError("SHA do gate E011 diverge")
        gate = json.loads(raw)
        required = {
            "schema_version": "spec005-e011-authorization-gate-v1",
            "specification": "SPEC-005", "execution_item": "E011",
            "quality_gate_result": "QUALITY_GATE_PASS",
            "major01_status": "CLOSED_BY_INDEPENDENT_REREVIEW",
            "d00513_independent_review": "PASS",
            "d00513_status": "INDEPENDENTLY_VERIFIED",
            "human_e011_reconfirmation": "GRANTED",
            "human_authorization_text": "Reconfirmo e autorizo a execução da E011.",
            "source_authority": "PERSISTED_OPERATIONAL_SOURCE_IDENTITY/D005-12",
            "source_identity_sha256": "4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe",
            "e012_authorized": False, "promotion_authorized": False,
        }
        if any(gate.get(key) != value for key, value in required.items()):
            raise ValueError("estado do gate E011 invalido")
        review = (root / gate["independent_review_artifact"]).resolve(strict=True)
        if root.resolve(strict=True) not in review.parents:
            raise ValueError("parecer fora do repositorio")
        if _sha(review.read_bytes()) != gate["independent_review_sha256"]:
            raise ValueError("parecer independente diverge")
        if len(gate["human_authorization_attachment_sha256"]) != 64:
            raise ValueError("proveniencia HUMAN invalida")
        return gate
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError("Evidence E011 nao verificavel") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Migracao financeira SPEC-005 em candidato isolado")
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--identity-manifest")
    parser.add_argument("--migration-manifest", type=Path)
    parser.add_argument("--migration-manifest-sha256")
    parser.add_argument("--source-authority", choices=("historical", "persisted"), default="persisted")
    parser.add_argument("--pointer", type=Path)
    parser.add_argument("--runtime-manifest-dir", type=Path)
    parser.add_argument("--binding-checkpoint", type=Path)
    parser.add_argument("--binding-sha256")
    args = parser.parse_args()
    if not all((args.identity_manifest, args.migration_manifest, args.migration_manifest_sha256,
                args.pointer, args.runtime_manifest_dir, args.binding_checkpoint, args.binding_sha256)):
        parser.error("E011 exige identidade legada e preflight completo")
    if args.source_authority != "persisted":
        parser.error("E011 exige autoridade operacional persistida D005-12")
    try:
        gate = verify_e011_gate()
        raw = args.binding_checkpoint.read_bytes()
        if _sha(raw) != args.binding_sha256:
            raise ValueError("checkpoint E011 diverge")
        checkpoint = json.loads(raw)
        if (checkpoint.get("status") != "E011_IDENTITY_INDEPENDENTLY_VERIFIED"
                or checkpoint.get("e011_authorization_gate_sha256") != GATE_SHA256
                or checkpoint.get("contract_identity") != "SPEC-005/D005-09+D005-10+D005-11+D005-12"):
            raise ValueError("identidade E011 ainda nao revisada independentemente")
        verify_independent_review(checkpoint, gate, ROOT)
        migration_sha = verify_manifest(ROOT, args.migration_manifest, args.migration_manifest_sha256)
        expected = checkpoint["source_identity"]
        source = verify_persisted_source(
            args.pointer, args.runtime_manifest_dir, Path(args.source),
            expected_pointer_sha256=expected["pointer_sha256"],
            expected_manifest_sha256=expected["runtime_manifest_sha256"],
            expected_database_sha256=expected["database_sha256"],
            expected_generation=expected["source_generation"])
        if _sha((json.dumps(source, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":")) + "\n").encode()) != gate["source_identity_sha256"]:
            raise ValueError("identidade da fonte diverge")
        bind_transformation(source, migration_sha, expected_source=expected,
                            expected_migration_sha256=checkpoint["migration_manifest_sha256"],
                            expected_transformation_sha256=checkpoint["transformation_identity"],
                            expected_contract_identity=checkpoint["contract_identity"],
                            e011_authorization_gate_sha256=GATE_SHA256)
        if migration_sha != checkpoint["migration_manifest_sha256"]:
            raise ValueError("identidade migradora E011 diverge")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(f"preflight E011 bloqueado: {exc}")
    from backend.migration.spec005 import migrate_finance_candidate
    evidence = migrate_finance_candidate(args.source, args.output,
                                         identity_manifest=args.identity_manifest,
                                         persisted_source_expectations=checkpoint["source_identity"])
    print(json.dumps(evidence.to_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
