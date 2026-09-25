"""Disposição D005-10 sobre fixtures sintéticas, sem candidato operacional."""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from backend.migration.spec005 import (Spec005MigrationError, Spec005ReviewBlock,
                                      _assert_candidate_reconciliation, _create_target_schema, exact_cents,
                                      migrate_finance_candidate, classify_finance_source_read_only)
from backend.migration.spec005_identity import (
    CANONICALIZATION_VERSION, file_sha256, row_fingerprint, read_rows,
)
from backend.cutover.infrastructure import SCHEMA_VERSION, OperationalPointer, freeze_runtime
from backend.models.finance import LegacyFinancialQuarantine, LegacyFinancialQuarantineEvent


def fixture_source(path):
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE users(id INTEGER PRIMARY KEY);
        CREATE TABLE patients(id INTEGER PRIMARY KEY);
        CREATE TABLE appointments(id INTEGER PRIMARY KEY, patient_id INTEGER REFERENCES patients(id));
        CREATE TABLE payments(id INTEGER PRIMARY KEY,patient_id INTEGER NOT NULL REFERENCES patients(id),
          appointment_id INTEGER REFERENCES appointments(id),due_date DATE NOT NULL,paid_at DATE,
          amount REAL NOT NULL,status TEXT NOT NULL,payment_method TEXT,description TEXT);
        CREATE TABLE expenses(id INTEGER PRIMARY KEY,description TEXT NOT NULL,amount REAL NOT NULL,
          expense_date DATE NOT NULL,category TEXT NOT NULL);
        INSERT INTO patients VALUES(1);
        INSERT INTO payments VALUES(3,1,NULL,'2026-07-06',NULL,180,'pending','','Teste');
        INSERT INTO payments VALUES(4,1,NULL,'2026-07-06',NULL,180,'paid','','Teste');
        INSERT INTO payments VALUES(5,1,NULL,'2026-07-06',NULL,180,'pending','','Teste');
        INSERT INTO expenses VALUES(3,'Teste',1200,'2026-07-06','Operacional');
        INSERT INTO expenses VALUES(4,'Teste',10,'2026-07-06','Operacional');
        INSERT INTO expenses VALUES(5,'Teste',1200,'2026-07-06','Operacional');
        """)


def fixture_manifest(source, path, monkeypatch):
    source_sha = file_sha256(source)
    repository = Path(__file__).resolve().parents[1]
    runtime = source.parent / "runtime"
    pointed_database = runtime / "generations" / "source.db"
    pointed_database.parent.mkdir(parents=True)
    shutil.copyfile(source, pointed_database)
    _, runtime_sha = freeze_runtime(repository, ["backend/config.py"], runtime / "runtime-manifests")
    pointer = OperationalPointer(8, "canonical", str(pointed_database.resolve()), source_sha, SCHEMA_VERSION, runtime_sha)
    (runtime / "operational-pointer.json").write_bytes(pointer.bytes())
    monkeypatch.setenv("CLINICA_OPERATIONAL_POINTER", str(runtime / "operational-pointer.json"))
    monkeypatch.setenv("CLINICA_RUNTIME_MANIFEST_DIR", str(runtime / "runtime-manifests"))
    monkeypatch.setenv("CLINICA_RUNTIME_CODE_ROOT", str(repository))
    with sqlite3.connect(source) as db:
        records = []
        for entity, table in (("payment", "payments"), ("expense", "expenses")):
            for row in read_rows(db, table):
                entry = {
                    "entity_type": entity, "source_internal_id": row["id"],
                    "source_row_fingerprint": row_fingerprint(entity, row),
                    "source_database_sha": source_sha,
                    "competence_year": 2026, "competence_month": 7,
                    "intended_disposition": "QUARANTINED_UNRESOLVED" if (entity, row["id"]) == ("payment", 4) else "CANONICAL_MIGRATED",
                }
                if (entity, row["id"]) == ("payment", 4):
                    entry["quarantine_reason"] = "PAID_WITH_UNKNOWN_PAID_AT"
                records.append(entry)
    payload = {"decision_id": "D005-10", "canonicalization_version": CANONICALIZATION_VERSION,
               "source_generation": 8, "source_manifest_sha256": runtime_sha, "records": records}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def test_d00511_historical_root_independent_of_current_root(tmp_path, monkeypatch):
    source = tmp_path / "source.db"
    manifest = tmp_path / "identity.json"
    fixture_source(source)
    fixture_manifest(source, manifest, monkeypatch)
    historical = tmp_path / "historical"
    (historical / "backend").mkdir(parents=True)
    repository = Path(__file__).resolve().parents[1]
    shutil.copyfile(repository / "backend" / "config.py", historical / "backend" / "config.py")
    monkeypatch.setenv("CLINICA_RUNTIME_CODE_ROOT", str(tmp_path / "wrong-current-root"))
    result = classify_finance_source_read_only(source, manifest, file_sha256(source),
                                                historical_code_root=historical)
    assert (result["canonical_count"], result["quarantine_count"]) == (5, 1)
    with pytest.raises(Spec005ReviewBlock):
        classify_finance_source_read_only(source, manifest, file_sha256(source))


def test_d00510_quarantine_partition_and_query_isolation(tmp_path, monkeypatch):
    source, manifest, candidate = (tmp_path / name for name in ("source.db", "identity.json", "candidate.db"))
    fixture_source(source)
    fixture_manifest(source, manifest, monkeypatch)
    evidence = migrate_finance_candidate(source, candidate, identity_manifest=manifest)
    assert (evidence.source_payment_count, evidence.candidate_payment_count, evidence.quarantined_count) == (3, 2, 1)
    assert evidence.payment_total_cents == 36000
    assert evidence.expense_total_cents == 241000
    assert evidence.foreign_key_violations == 0 and evidence.recovery_check == "ok"
    with sqlite3.connect(candidate) as db:
        assert db.execute("SELECT id FROM payments ORDER BY id").fetchall() == [(3,), (5,)]
        q = db.execute("SELECT source_record_id,legacy_status,competence_year,competence_month,reason_code,resolution_state,legacy_row_json FROM legacy_financial_quarantine").fetchone()
        assert q[:6] == (4, "paid", 2026, 7, "PAID_WITH_UNKNOWN_PAID_AT", "unresolved")
        assert json.loads(q[6])["paid_at"] is None
        assert db.execute("SELECT COUNT(*) FROM legacy_financial_quarantine_events").fetchone()[0] == 1
        assert db.execute("SELECT SUM(amount_cents) FROM payments WHERE status='paid'").fetchone()[0] is None
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM legacy_financial_quarantine")
    with pytest.raises(Exception, match="candidato ja existe"):
        migrate_finance_candidate(source, candidate, identity_manifest=manifest)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "fingerprint", "source_sha", "value"])
def test_d00510_identity_fail_closed_before_candidate(tmp_path, mutation, monkeypatch):
    source, manifest, candidate = (tmp_path / name for name in ("source.db", "identity.json", "candidate.db"))
    fixture_source(source)
    payload = fixture_manifest(source, manifest, monkeypatch)
    if mutation == "missing":
        payload["records"].pop()
    elif mutation == "duplicate":
        payload["records"].append(dict(payload["records"][0]))
    elif mutation == "fingerprint":
        payload["records"][0]["source_row_fingerprint"] = "0" * 64
    elif mutation == "source_sha":
        payload["records"][0]["source_database_sha"] = "0" * 64
    else:
        with sqlite3.connect(source) as db:
            db.execute("UPDATE expenses SET amount=11 WHERE id=4")
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Spec005ReviewBlock, match="REVIEW/BLOCK"):
        migrate_finance_candidate(source, candidate, identity_manifest=manifest)
    assert not candidate.exists()


def test_d00510_fingerprint_independent_of_sql_order_and_sensitive_to_change():
    row = {"id": 4, "status": "paid", "paid_at": None, "amount": 180.0}
    digest = row_fingerprint("payment", row)
    assert digest == row_fingerprint("payment", dict(reversed(list(row.items()))))
    assert digest != row_fingerprint("payment", {**row, "amount": 181.0})


@pytest.mark.parametrize("field", ["source_generation", "source_manifest_sha256", "source_database_sha"])
def test_d00510_false_provenance_blocks_before_candidate(tmp_path, monkeypatch, field):
    source, manifest, candidate = (tmp_path / name for name in ("source.db", "identity.json", "candidate.db"))
    fixture_source(source)
    payload = fixture_manifest(source, manifest, monkeypatch)
    if field == "source_database_sha":
        for record in payload["records"]:
            record[field] = "f" * 64
    else:
        payload[field] = 9 if field == "source_generation" else "f" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Spec005ReviewBlock, match="REVIEW/BLOCK"):
        migrate_finance_candidate(source, candidate, identity_manifest=manifest)
    assert not candidate.exists()


@pytest.mark.parametrize("table,field,value", [
    ("payments", "amount_cents", 18100), ("payments", "status", "paid"),
    ("payments", "competence_month", 8), ("payments", "due_date", "2026-08-06"),
    ("payments", "patient_id", 2), ("payments", "description", "Alterado"),
    ("payments", "id", 30),
    ("expenses", "category_id", 2),
    ("legacy_financial_quarantine", "source_record_id", 99),
    ("legacy_financial_quarantine", "source_record_id", 3),
    ("legacy_financial_quarantine", "source_manifest_sha256", "f" * 64),
    ("legacy_financial_quarantine", "reason_code", "OTHER"),
    ("legacy_financial_quarantine", "legacy_row_json", '{"paid_at":"2026-07-06"}'),
    ("legacy_financial_quarantine", "amount_cents", 18100),
])
def test_d00510_post_load_material_mutation_is_detected(tmp_path, monkeypatch, table, field, value):
    source, manifest, candidate = (tmp_path / name for name in ("source.db", "identity.json", "candidate.db"))
    fixture_source(source)
    payload = fixture_manifest(source, manifest, monkeypatch)
    migrate_finance_candidate(source, candidate, identity_manifest=manifest)
    with sqlite3.connect(source) as db:
        originals = {(entity, r["id"]): r for entity, name in (("payment", "payments"), ("expense", "expenses"))
                     for r in read_rows(db, name)}
    payments = [dict(row) for (entity, _), row in originals.items() if entity == "payment"]
    expenses = [dict(row) for (entity, _), row in originals.items() if entity == "expense"]
    for row in payments + expenses:
        row["competence_year"], row["competence_month"] = 2026, 7
        row["amount_cents"] = exact_cents(row["amount"])
    entry = next(item for item in payload["records"] if (item["entity_type"], item["source_internal_id"]) == ("payment", 4))
    quarantine = [("payment", next(r for r in payments if r["id"] == 4), entry)]
    with sqlite3.connect(candidate) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        if table == "legacy_financial_quarantine":
            db.execute("DROP TRIGGER spec005_quarantine_no_update")
            where = "source_record_id=4"
        else:
            where = "id=3"
        if field == "status":
            db.execute("UPDATE payments SET status='paid', paid_at='2026-07-06' WHERE id=3")
        else:
            db.execute(f"UPDATE {table} SET {field}=? WHERE {where}", (value,))
        db.commit()
        with pytest.raises((Spec005MigrationError, ValueError, StopIteration)):
            _assert_candidate_reconciliation(db, payments, expenses, quarantine, originals,
                                             file_sha256(source), file_sha256(manifest), payload)


def test_d00510_default_bootstrap_freeze_and_provenance(tmp_path, monkeypatch):
    repository = Path(__file__).resolve().parents[1]
    source, manifest = tmp_path / "snapshot.db", tmp_path / "identity.json"
    fixture_source(source)
    payload = fixture_manifest(source, manifest, monkeypatch)
    runtime = tmp_path / "localappdata" / "ClinicaGabriela" / "runtime"
    database = runtime / "generations" / "source.db"
    database.parent.mkdir(parents=True)
    shutil.copyfile(source, database)
    runtime_manifest, runtime_sha = freeze_runtime(repository, ["backend/config.py"], runtime / "runtime-manifests")
    pointer = OperationalPointer(8, "canonical", str(database.resolve()), file_sha256(database),
                                 SCHEMA_VERSION, runtime_sha)
    pointer_path = runtime / "operational-pointer.json"
    pointer_path.write_bytes(pointer.bytes())
    payload["source_manifest_sha256"] = runtime_sha
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    env = os.environ.copy()
    for key in ("CLINICA_RUNTIME_ROOT", "CLINICA_OPERATIONAL_POINTER", "CLINICA_RUNTIME_CODE_ROOT",
                "CLINICA_RUNTIME_MANIFEST_DIR", "BACKEND_DATABASE_PATH", "BACKEND_DATA_DIR"):
        env.pop(key, None)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = ("import sys; from backend.config import get_runtime_settings; "
               "from backend.migration.spec005 import classify_finance_source_read_only; "
               "s=get_runtime_settings(); "
               "r=classify_finance_source_read_only(sys.argv[1],sys.argv[2],sys.argv[3]); "
               "print(s.database_path, r['source_count'], r['quarantine_count'])")
    def invoke():
        return subprocess.run([sys.executable, "-B", "-c", command, str(source), str(manifest), file_sha256(source)],
                              cwd=repository, env=env, capture_output=True, text=True, check=False)
    result = invoke()
    assert result.returncode == 0, result.stderr
    assert "6 1" in result.stdout
    payload["source_manifest_sha256"] = "f" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    assert invoke().returncode != 0
    payload["source_manifest_sha256"] = runtime_sha
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    runtime_manifest.write_bytes(runtime_manifest.read_bytes() + b" ")
    assert "RuntimeFreezeError" in invoke().stderr
    runtime_manifest.write_bytes(runtime_manifest.read_bytes()[:-1])
    wrong_pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    wrong_pointer["database_checksum_sha256"] = "f" * 64
    pointer_path.write_text(json.dumps(wrong_pointer), encoding="utf-8")
    assert invoke().returncode != 0


def test_d00510_quarantine_declarative_constraints_match_migration():
    for model in (LegacyFinancialQuarantine, LegacyFinancialQuarantineEvent):
        with sqlite3.connect(":memory:") as db:
            _create_target_schema(db)
            ddl = db.execute("SELECT sql FROM sqlite_schema WHERE type='table' AND name=?",
                             (model.__tablename__,)).fetchone()[0]
        normalized = lambda value: "".join(str(value).lower().split())
        actual = normalized(ddl)
        for constraint in model.__table__.constraints:
            if hasattr(constraint, "sqltext"):
                assert normalized(constraint.sqltext) in actual
