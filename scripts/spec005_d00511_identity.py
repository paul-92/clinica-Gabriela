"""Build/verify read-only do código e preflight de identidade D005-11.

Nenhum comando cria candidato ou altera runtime operacional.
"""

from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path

from backend.cutover.spec005_execution_identity import (
    bind_transformation, build_manifest, verify_manifest, verify_source, verify_persisted_source,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Identidades separadas SPEC-005 D005-11")
    parser.add_argument("operation", choices=("build", "verify", "preflight"))
    parser.add_argument("--code-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--pointer", type=Path)
    parser.add_argument("--runtime-manifest-dir", type=Path)
    parser.add_argument("--historical-code-root", type=Path)
    parser.add_argument("--source-authority", choices=("historical", "persisted"), default="historical")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--expected-pointer-sha256")
    parser.add_argument("--binding-checkpoint", type=Path)
    parser.add_argument("--binding-sha256")
    args = parser.parse_args()
    if args.operation == "build":
        print(json.dumps({"migration_manifest_sha256": build_manifest(args.code_root, args.manifest)}))
        return
    if not args.manifest_sha256:
        parser.error("--manifest-sha256 é obrigatório para verify/preflight")
    migration_sha = verify_manifest(args.code_root, args.manifest, args.manifest_sha256)
    if args.operation == "verify":
        print(json.dumps({"migration_manifest_sha256": migration_sha, "result": "PASS"}))
        return
    if not all((args.pointer, args.runtime_manifest_dir, args.snapshot,
                args.expected_pointer_sha256, args.binding_checkpoint, args.binding_sha256)):
        parser.error("preflight exige fonte e checkpoint de binding com SHA externo")
    if args.source_authority == "historical" and not args.historical_code_root:
        parser.error("autoridade histórica exige baseline explícita")
    raw = args.binding_checkpoint.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.binding_sha256:
        parser.error("SHA do checkpoint de binding diverge")
    checkpoint = json.loads(raw)
    if checkpoint.get("status") != "PROPOSED_NOT_E011_AUTHORIZATION":
        parser.error("checkpoint de binding inválido")
    if args.source_authority == "persisted":
        if checkpoint.get("contract_identity") != "SPEC-005/D005-09+D005-10+D005-11+D005-12":
            parser.error("contrato D005-12 divergente")
        expected = checkpoint["source_identity"]
        source = verify_persisted_source(
            args.pointer, args.runtime_manifest_dir, args.snapshot,
            expected_pointer_sha256=args.expected_pointer_sha256,
            expected_manifest_sha256=expected["runtime_manifest_sha256"],
            expected_database_sha256=expected["database_sha256"],
            expected_generation=expected["source_generation"])
    else:
        source = verify_source(args.pointer, args.runtime_manifest_dir, args.historical_code_root,
                               args.snapshot, args.expected_pointer_sha256)
    transformation = bind_transformation(
        source, migration_sha, expected_source=checkpoint["source_identity"],
        expected_migration_sha256=checkpoint["migration_manifest_sha256"],
        expected_transformation_sha256=checkpoint["transformation_identity"],
        expected_contract_identity=checkpoint.get("contract_identity"),
    )
    print(json.dumps({"result": "IDENTITY_PREFLIGHT_PASS_NOT_E011_AUTHORIZATION",
                      "source_identity": source, "migration_manifest_sha256": migration_sha,
                      "transformation_identity": transformation}, sort_keys=True))


if __name__ == "__main__":
    main()
