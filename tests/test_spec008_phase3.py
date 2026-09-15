import hashlib
import json
import sqlite3

from scripts.spec008_phase1 import run_phase1
from scripts.spec008_phase3 import run_phase3


def _database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, cpf TEXT)")


def test_phase3_validates_freeze_and_persists_aggregate_report(tmp_path):
    repository = tmp_path / "repository"
    _database(repository / "data" / "clinica_psicologia.db")
    _database(repository / "backend" / "data" / "clinica_api.db")
    root = tmp_path / "protected"
    run_phase1(repository, root, "execution-1")
    names = (
        "desktop_legacy.snapshot.db",
        "backend_legacy.snapshot.db",
        "desktop_legacy.snapshot-manifest.json",
        "backend_legacy.snapshot-manifest.json",
        "execution-manifest.json",
    )
    freeze = {
        "execution_id": "execution-1",
        "artifacts": [
            {
                "artifact_reference": name,
                "checksum_sha256": hashlib.sha256((root / name).read_bytes()).hexdigest(),
            }
            for name in names
        ],
    }
    (root / "reconciliation-freeze-manifest.json").write_text(
        json.dumps(freeze), encoding="utf-8"
    )

    result = run_phase3(root, "execution-1")

    assert result["gate"] == "PASS"
    assert result["review_count"] == 0
    assert result["block_count"] == 0
    report = json.loads((root / "dry-run-report.json").read_text(encoding="utf-8"))
    assert report["gate"] == "PASS"
