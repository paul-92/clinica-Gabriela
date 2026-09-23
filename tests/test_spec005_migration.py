import json
import os
import sqlite3
from pathlib import Path

import pytest

from backend.migration.spec005 import (
    Spec005MigrationError,
    Spec005ReviewBlock,
    migrate_finance_candidate,
)


def _legacy_database(
    path, *, amounts=(0.10, 0.20), include_competence=True, daily_competence=False,
    payment_status="pending", paid_at=None,
):
    if daily_competence:
        competence_column = ", competence_date DATE"
    else:
        competence_column = ", competence_year INTEGER, competence_month INTEGER" if include_competence else ""
    with sqlite3.connect(path) as connection:
        connection.executescript(
            f"""
            PRAGMA foreign_keys=ON;
            CREATE TABLE users(id INTEGER PRIMARY KEY);
            CREATE TABLE patients(id INTEGER PRIMARY KEY);
            CREATE TABLE appointments(id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id));
            CREATE TABLE payments(
              id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id),
              appointment_id INTEGER REFERENCES appointments(id), due_date DATE NOT NULL,
              paid_at DATE, amount FLOAT NOT NULL, status TEXT NOT NULL,
              payment_method TEXT, description TEXT{competence_column}
            );
            CREATE TABLE expenses(
              id INTEGER PRIMARY KEY, description TEXT NOT NULL, amount FLOAT NOT NULL,
              expense_date DATE NOT NULL, category TEXT{competence_column}
            );
            INSERT INTO patients(id) VALUES(101);
            INSERT INTO appointments(id,patient_id) VALUES(201,101);
            """
        )
        payment_columns = "id,patient_id,appointment_id,due_date,paid_at,amount,status,payment_method,description"
        payment_values = [301, 101, None, "2031-02-10", paid_at, amounts[0], payment_status, "", "Sintetico A"]
        expense_columns = "id,description,amount,expense_date,category"
        expense_values = [401, "Despesa sintetica", amounts[1], "2031-02-11", "Operacional"]
        if include_competence:
            if daily_competence:
                payment_columns += ",competence_date"
                payment_values.append("2031-02-01")
                expense_columns += ",competence_date"
                expense_values.append("2031-02-01")
            else:
                payment_columns += ",competence_year,competence_month"
                payment_values.extend([2031, 2])
                expense_columns += ",competence_year,competence_month"
                expense_values.extend([2031, 2])
        connection.execute(
            f"INSERT INTO payments({payment_columns}) VALUES({','.join('?' for _ in payment_values)})",
            payment_values,
        )
        connection.execute(
            f"INSERT INTO expenses({expense_columns}) VALUES({','.join('?' for _ in expense_values)})",
            expense_values,
        )


def test_ac002_and_ac011_forward_only_candidate_is_exact_and_preserves_identity(tmp_path):
    source = tmp_path / "snapshot.db"
    output = tmp_path / "candidate.db"
    _legacy_database(source)

    evidence = migrate_finance_candidate(source, output)

    assert evidence.payment_total_cents == 10
    assert evidence.expense_total_cents == 20
    assert evidence.null_appointment_count == 1
    assert evidence.foreign_key_violations == 0
    assert evidence.integrity_check == "ok"
    assert evidence.recovery_check == "ok"
    assert evidence.operational_migration_executed is False
    with sqlite3.connect(output) as connection:
        payment = connection.execute(
            "SELECT id,patient_id,appointment_id,amount_cents,competence_year,competence_month FROM payments"
        ).fetchone()
        assert payment == (301, 101, None, 10, 2031, 2)
        assert "competence_date" not in {
            row[1] for row in connection.execute("PRAGMA table_info(payments)")
        }
        assert connection.execute("SELECT COUNT(*) FROM financial_events").fetchone()[0] == 2


@pytest.mark.parametrize("amount", [1.001, 0, -1])
def test_ac002_migration_fails_closed_without_rounding_or_truncation(tmp_path, amount):
    source = tmp_path / "snapshot.db"
    output = tmp_path / "candidate.db"
    _legacy_database(source, amounts=(amount, 0.20))

    with pytest.raises(Spec005ReviewBlock, match="REVIEW/BLOCK"):
        migrate_finance_candidate(source, output)

    assert not output.exists()


def test_ac003_migration_never_infers_competence(tmp_path):
    source = tmp_path / "snapshot.db"
    output = tmp_path / "candidate.db"
    _legacy_database(source, include_competence=False)

    with pytest.raises(Spec005ReviewBlock, match="competence_year explicito"):
        migrate_finance_candidate(source, output)

    assert not output.exists()


def test_d00508_migration_rejects_legacy_daily_competence_without_fabricating_month(tmp_path):
    source = tmp_path / "snapshot.db"
    output = tmp_path / "candidate.db"
    _legacy_database(source, daily_competence=True)

    with pytest.raises(Spec005ReviewBlock, match="competence_date diario"):
        migrate_finance_candidate(source, output)

    assert not output.exists()


def test_d00508_r2_paid_without_paid_at_remains_review_block(tmp_path):
    source = tmp_path / "snapshot-r2.db"
    output = tmp_path / "candidate-r2.db"
    _legacy_database(source, payment_status="paid", paid_at=None)

    with pytest.raises(Spec005ReviewBlock, match="pagamento sem paid_at explicito"):
        migrate_finance_candidate(source, output)

    assert not output.exists()


def test_d00508_human_decision_records_r1_r6_as_2026_07_and_blocks_r2():
    decision_path = Path(__file__).parents[1] / "docs" / "audit" / "spec005-20260922-human-legacy-data-decision.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    records = {item["review_id"]: item for item in decision["decisions"]}

    assert set(records) == {"R1", "R2", "R3", "R4", "R5", "R6"}
    assert all((item["competence_year"], item["competence_month"]) == (2026, 7) for item in records.values())
    assert records["R2"]["paid_at"] is None
    assert records["R2"]["paid_at_inference_authorized"] is False
    assert records["R2"]["unresolved_treatment"].startswith("REVIEW/BLOCK")


def _assert_rejected_before_mutation(source, output, recovery=None):
    before = {path: path.exists() for path in (output, recovery) if path is not None}
    with pytest.raises(Spec005MigrationError, match="operacional"):
        migrate_finance_candidate(source, output, recovery)
    assert {path: path.exists() for path in before} == before


def test_f001_rejects_real_generation_8_as_source_without_mutation(tmp_path):
    runtime = Path(os.environ["LOCALAPPDATA"]) / "ClinicaGabriela" / "runtime"
    pointer_path = runtime / "operational-pointer.json"
    if not pointer_path.is_file():
        pytest.skip("runtime operacional indisponivel para sentinela read-only")
    pointer_before = pointer_path.read_bytes()
    pointer = json.loads(pointer_before)
    if pointer.get("generation") != 8 or pointer.get("state") != "canonical":
        pytest.skip("sentinela operacional nao esta em Generation 8/canonical")
    generation = Path(pointer["database_path"])
    generation_before = generation.stat().st_mtime_ns
    output = tmp_path / "candidate.db"

    _assert_rejected_before_mutation(generation, output)

    assert pointer_path.read_bytes() == pointer_before
    assert generation.stat().st_mtime_ns == generation_before


def test_f001_rejects_source_under_operational_runtime_before_lookup(tmp_path):
    runtime = Path(os.environ["LOCALAPPDATA"]) / "ClinicaGabriela" / "runtime"
    output = tmp_path / "candidate.db"

    _assert_rejected_before_mutation(runtime / "nao-criar-source.db", output)


def test_f001_rejects_candidate_under_synthetic_runtime_before_mutation(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("CLINICA_RUNTIME_ROOT", str(runtime))
    source = tmp_path / "snapshot.db"
    _legacy_database(source)
    output = runtime / "candidate.db"

    _assert_rejected_before_mutation(source, output)


def test_f001_rejects_recovery_under_synthetic_runtime_before_mutation(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("CLINICA_RUNTIME_ROOT", str(runtime))
    source = tmp_path / "snapshot.db"
    _legacy_database(source)
    output = tmp_path / "candidate.db"
    recovery = runtime / "candidate.recovery.db"

    _assert_rejected_before_mutation(source, output, recovery)


def test_f001_rejects_normalized_relative_alias_into_runtime(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("CLINICA_RUNTIME_ROOT", str(runtime))
    monkeypatch.chdir(tmp_path)
    alias = Path("runtime") / ".." / "runtime" / "alias-source.db"
    output = tmp_path / "candidate.db"

    _assert_rejected_before_mutation(alias, output)
