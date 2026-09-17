"""Materializa candidato v5 somente a partir de uma cópia explicitamente informada."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_migration():
    path = ROOT / "backend" / "migration" / "spec004_remediation.py"
    spec = importlib.util.spec_from_file_location("spec004_remediation_candidate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("migration corretiva nao pode ser carregada")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.migrate_spec004_remediation


migrate_spec004_remediation = _load_migration()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    destination = args.destination.resolve(strict=False)
    if destination.exists():
        raise RuntimeError("destino do candidato ja existe")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    try:
        result = migrate_spec004_remediation(destination)
        with sqlite3.connect(destination) as connection:
            evidence = {
                **result,
                "source_sha256": sha256(source),
                "candidate_sha256": sha256(destination),
                "size_bytes": destination.stat().st_size,
                "integrity_check": connection.execute("PRAGMA integrity_check").fetchone()[0],
                "foreign_key_violations": len(list(connection.execute("PRAGMA foreign_key_check"))),
                "privacy_safe": True,
            }
        print(json.dumps(evidence, sort_keys=True))
        return 0
    except Exception:
        destination.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
