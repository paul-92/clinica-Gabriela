"""Executa o dry-run agregado da Fase 3 sobre um pacote congelado."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from backend.migration.dry_run import run_snapshot_dry_run
from backend.migration.manifests import SnapshotManifest
from backend.migration.snapshot import validate_sqlite_snapshot
from backend.migration.storage import load_stored_manifest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_phase3(artifact_root: Path, execution_reference: str) -> dict:
    root = artifact_root.resolve(strict=True)
    freeze_path = root / "reconciliation-freeze-manifest.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("execution_id") != execution_reference:
        raise ValueError("freeze pertence a outra execucao")
    for binding in freeze.get("artifacts", []):
        artifact = root / binding["artifact_reference"]
        if _sha256(artifact) != binding["checksum_sha256"]:
            raise ValueError("artefato diverge do freeze")

    validated = []
    for label in ("desktop_legacy", "backend_legacy"):
        manifest = load_stored_manifest(
            root / f"{label}.snapshot-manifest.json", SnapshotManifest
        )
        validated.append(
            validate_sqlite_snapshot(root / f"{label}.snapshot.db", manifest)
        )
    report = run_snapshot_dry_run(
        validated[0], validated[1], execution_reference=execution_reference
    )
    payload = report.model_dump(mode="json")
    encoded = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    destination = root / "dry-run-report.json"
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "execution_reference": execution_reference,
        "gate": report.gate.value,
        "review_count": report.review_count,
        "block_count": report.block_count,
        "reasons": list(report.reasons),
        "report_checksum_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--execution-reference", required=True)
    args = parser.parse_args()
    print(json.dumps(run_phase3(args.artifact_root, args.execution_reference), sort_keys=True))


if __name__ == "__main__":
    main()
