"""Inventário read-only dos bytes diretamente disponíveis para o freeze SPEC-005.

Não transforma EOL, não procura preimages e não acessa o banco operacional.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_matrix(root: Path, manifest: Path) -> dict:
    payload = json.loads(manifest.read_bytes())
    commit = payload["source_commit"]
    rows = []
    for entry in sorted(payload["entries"], key=lambda item: item["path"]):
        path = entry["path"]
        expected = entry["sha256"]
        current_path = root / path
        current = current_path.read_bytes() if current_path.is_file() else None
        process = subprocess.run(
            ["git", "show", f"{commit}:{path}"], cwd=root,
            capture_output=True, check=False,
        )
        if process.returncode:
            raise RuntimeError(f"blob histórico não disponível: {path}")
        historical = process.stdout
        current_sha = sha256(current) if current is not None else None
        historical_sha = sha256(historical)
        current_match = current_sha == expected
        historical_match = historical_sha == expected
        if historical_match:
            verified_source = f"git:{commit}:{path}"
            actual_sha = historical_sha
        elif current_match:
            verified_source = f"working_tree:{path}"
            actual_sha = current_sha
        else:
            verified_source = None
            actual_sha = None
        provenance = (
            "SOURCE_COMMIT_AND_CURRENT" if historical_match and current_match else
            "SOURCE_COMMIT_EXACT" if historical_match else
            "CURRENT_BYTE_MATCH_TEMPORAL_UNPROVEN" if current_match else
            "NO_DIRECT_EXACT_SOURCE"
        )
        rows.append({
            "path": path,
            "expected_sha256": expected,
            "recovery_status": "EXACT_RECOVERED" if verified_source else "UNRECOVERED",
            "verified_source": verified_source,
            "actual_sha256": actual_sha,
            "provenance_class": provenance,
            "source_commit_actual_sha256": historical_sha,
            "current_actual_sha256": current_sha,
            "previous_111_status": "NOT_RECORDED_PER_PATH",
        })
    counts = {name: sum(row["provenance_class"] == name for row in rows) for name in
              sorted({row["provenance_class"] for row in rows})}
    return {
        "schema_version": "spec005-historical-recovery-matrix-v1",
        "manifest_sha256": sha256(manifest.read_bytes()),
        "source_commit": commit,
        "method": "direct bytes only: git show and current working tree; no EOL conversion",
        "previous_recovery_result": "111/128 (historical claim; no per-path matrix available)",
        "independent_review_observation": "126/128 (included generated LF-to-CRLF candidates)",
        "direct_exact_count": sum(row["recovery_status"] == "EXACT_RECOVERED" for row in rows),
        "unrecovered_count": sum(row["recovery_status"] == "UNRECOVERED" for row in rows),
        "provenance_counts": counts,
        "entries": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    matrix = build_matrix(args.root.resolve(strict=True), args.manifest.resolve(strict=True))
    data = (json.dumps(matrix, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")
    args.output.write_bytes(data)
    print(json.dumps({"entries": len(matrix["entries"]),
                      "direct_exact": matrix["direct_exact_count"],
                      "unrecovered": matrix["unrecovered_count"],
                      "sha256": sha256(data)}, sort_keys=True))


if __name__ == "__main__":
    main()
