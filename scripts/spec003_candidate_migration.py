"""Cria backup, candidato migrado e Evidence privacy-safe da SPEC-003."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# O executor recebe a origem explicitamente e não deve resolver nem validar o pointer
# operacional durante imports de infraestrutura.
os.environ["CLINICA_OPERATIONAL_POINTER"] = str(PROJECT_ROOT / ".spec003-explicit-source")

from backend.migration.spec003 import SPEC003_USER_VERSION, migrate_spec003


TABLES = (
    "patients", "psychologists", "appointments", "clinical_records",
    "payments", "expenses", "users",
)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _readonly(path):
    return sqlite3.connect(f"file:{Path(path).resolve().as_posix()}?mode=ro&immutable=1", uri=True)


def _counts(path):
    with _readonly(path) as connection:
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in TABLES}


def _backup(source, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb"):
        pass
    try:
        with _readonly(source) as source_connection, sqlite3.connect(destination) as target:
            source_connection.backup(target)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def build_candidate(source, output_dir):
    source = Path(source).resolve(strict=True)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    backup = output / "generation-2-pre-spec003.backup.db"
    candidate = output / "generation-3-spec003-candidate.db"
    evidence_path = output / "spec003-candidate-evidence.json"
    if any(path.exists() for path in (backup, candidate, evidence_path)):
        raise FileExistsError("destino de Evidence/candidato ja existe")

    before_hash = sha256_file(source)
    before_counts = _counts(source)
    _backup(source, backup)
    _backup(source, candidate)
    migrate_spec003(candidate)
    after_hash = sha256_file(source)
    if after_hash != before_hash:
        raise RuntimeError("origem operacional foi alterada")
    after_counts = _counts(candidate)
    if after_counts != before_counts:
        raise RuntimeError("contagens de dominio divergiram")
    with _readonly(candidate) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        legacy = connection.execute("SELECT COUNT(*) FROM clinical_records WHERE status='legacy_preserved'").fetchone()[0]
        unknown = connection.execute("SELECT COUNT(*) FROM clinical_records WHERE author_status='author_unknown'").fetchone()[0]
        invalid_cpf = connection.execute("SELECT COUNT(*) FROM patients WHERE cpf_status='legacy_unverified'").fetchone()[0]
        crp_review = connection.execute("SELECT COUNT(*) FROM psychologists WHERE crp_status='review'").fetchone()[0]
    evidence = {
        "spec": "SPEC-003",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "privacy_safe": True,
        "source_unchanged": True,
        "source_sha256": before_hash,
        "backup_sha256": sha256_file(backup),
        "candidate_sha256": sha256_file(candidate),
        "counts_before": before_counts,
        "counts_after": after_counts,
        "user_version": user_version,
        "expected_user_version": SPEC003_USER_VERSION,
        "integrity_check": integrity,
        "foreign_key_violations": violations,
        "legacy_preserved_count": legacy,
        "author_unknown_count": unknown,
        "legacy_unverified_cpf_count": invalid_cpf,
        "crp_review_count": crp_review,
        "pointer_switched": False,
        "operational_migration_executed": False,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build_candidate(args.source, args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
