"""Provisiona revisao E011 em fase separada, somente pelo revisor independente.

Nao e chamado/importado pelo executor E011. Criacao exclusiva impede substituir
uma autoridade existente; supersession requer novo ciclo explicito de revisao.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.spec005_candidate_migration import AUTHORITY_RELATIVE


def provision(root: Path, review_file: Path) -> str:
    root = root.resolve(strict=True)
    review = review_file.read_bytes()
    payload = json.loads(review)
    if (payload.get("schema_version") != "spec005-e011-independent-review-v1"
            or payload.get("specification") != "SPEC-005"
            or payload.get("execution_item") != "E011"
            or payload.get("quality_gate_result") != "QUALITY_GATE_PASS"
            or payload.get("blocker01_status") != "CLOSED_BY_INDEPENDENT_REVIEW"):
        raise ValueError("parecer nao aprova E011 ou nao fecha BLOCKER-01")
    for key in ("source_identity_sha256", "migration_manifest_sha256", "transformation_identity"):
        value = payload.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"identidade {key} invalida")
    if not payload.get("migration_manifest_version") or not payload.get("contract_identity"):
        raise ValueError("subject incompleto")
    digest = hashlib.sha256(review).hexdigest()
    relative = Path("docs/audit") / f"spec005-e011-review-{digest}.json"
    authority = {"schema_version": "spec005-e011-review-authority-v1",
                 "review_artifact": relative.as_posix(), "review_sha256": digest}
    target = root / relative
    registry = root / AUTHORITY_RELATIVE
    if registry.exists():
        raise FileExistsError("autoridade canonica ja provisionada; supersession exige novo ciclo")
    with target.open("xb") as stream:
        stream.write(review)
    with registry.open("xb") as stream:
        stream.write((json.dumps(authority, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(description="Provisionamento independente SPEC-005 E011")
    parser.add_argument("--review", required=True, type=Path)
    args = parser.parse_args()
    print(provision(Path(__file__).resolve().parents[1], args.review))


if __name__ == "__main__":
    main()
