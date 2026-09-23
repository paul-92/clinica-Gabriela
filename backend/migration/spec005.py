"""Migracao financeira SPEC-005, somente para candidato isolado.

Este modulo nunca seleciona nem promove o banco operacional. A origem deve ser um
snapshot/copia e o destino deve ser um arquivo novo fora dos diretorios operacionais.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import quote

from backend.config import BACKEND_ROOT


PROJECT_ROOT = BACKEND_ROOT.parent
OPERATIONAL_DATABASES = frozenset(
    {
        (PROJECT_ROOT / "data" / "clinica_psicologia.db").resolve(strict=False),
        (BACKEND_ROOT / "data" / "clinica_api.db").resolve(strict=False),
    }
)
OPERATIONAL_DIRECTORIES = frozenset(path.parent for path in OPERATIONAL_DATABASES)


class Spec005MigrationError(Exception):
    pass


class Spec005ReviewBlock(Spec005MigrationError):
    pass


@dataclass(frozen=True)
class FinanceMigrationEvidence:
    source_payment_count: int
    source_expense_count: int
    candidate_payment_count: int
    candidate_expense_count: int
    payment_total_cents: int
    expense_total_cents: int
    null_appointment_count: int
    payment_ids_sha256: str
    expense_ids_sha256: str
    foreign_key_violations: int
    integrity_check: str
    recovery_check: str
    operational_migration_executed: bool = False

    def to_dict(self):
        return asdict(self)


def _resolved(path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _operational_runtime_roots() -> frozenset[Path]:
    default_root = (
        Path(os.getenv("LOCALAPPDATA", PROJECT_ROOT)) / "ClinicaGabriela" / "runtime"
    )
    configured_root = Path(os.getenv("CLINICA_RUNTIME_ROOT", default_root))
    return frozenset({_resolved(default_root), _resolved(configured_root)})


def _operational_pointer_paths(runtime_roots: frozenset[Path]) -> frozenset[Path]:
    configured_pointer = os.getenv("CLINICA_OPERATIONAL_POINTER")
    paths = {root / "operational-pointer.json" for root in runtime_roots}
    if configured_pointer:
        paths.add(_resolved(configured_pointer))
    return frozenset(_resolved(path) for path in paths)


def _pointed_operational_databases(pointer_paths: frozenset[Path]) -> frozenset[Path]:
    databases = set()
    for pointer_path in pointer_paths:
        if not pointer_path.is_file():
            continue
        try:
            payload = json.loads(pointer_path.read_text(encoding="utf-8"))
            database_path = payload["database_path"]
            if not isinstance(database_path, str) or not Path(database_path).is_absolute():
                raise ValueError
            databases.add(_resolved(database_path))
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise Spec005MigrationError("ponteiro operacional nao pode ser validado") from exc
    return frozenset(databases)


def _reject_operational(path: Path) -> None:
    resolved = _resolved(path)
    runtime_roots = _operational_runtime_roots()
    pointer_paths = _operational_pointer_paths(runtime_roots)
    protected_files = OPERATIONAL_DATABASES | pointer_paths | _pointed_operational_databases(pointer_paths)
    protected_directories = OPERATIONAL_DIRECTORIES | runtime_roots
    if resolved in protected_files or any(
        resolved == directory or directory in resolved.parents for directory in protected_directories
    ):
        raise Spec005MigrationError("caminho operacional nao permitido")


def _read_only_connection(path: Path) -> sqlite3.Connection:
    uri_path = quote(path.as_posix(), safe="/:")
    return sqlite3.connect(f"file:{uri_path}?mode=ro&immutable=1", uri=True)


def _columns(connection, table):
    return {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}


def _rows(connection, table):
    cursor = connection.execute(f'SELECT * FROM "{table}" ORDER BY id')
    names = [item[0] for item in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def exact_cents(value) -> int:
    if value is None or isinstance(value, bool):
        raise Spec005ReviewBlock("REVIEW/BLOCK: valor monetario ausente ou invalido")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise Spec005ReviewBlock("REVIEW/BLOCK: valor monetario nao deterministico") from exc
    scaled = decimal_value * 100
    if not decimal_value.is_finite() or scaled != scaled.to_integral_value():
        raise Spec005ReviewBlock("REVIEW/BLOCK: valor monetario exige arredondamento")
    cents = int(scaled)
    if cents <= 0:
        raise Spec005ReviewBlock("REVIEW/BLOCK: valor monetario deve ser positivo")
    return cents


def _require_explicit(row, field, resource):
    if field not in row or row[field] in (None, ""):
        raise Spec005ReviewBlock(f"REVIEW/BLOCK: {resource} sem {field} explicito")
    return row[field]


def _validate_payment(row):
    status = row.get("status")
    if status not in {"pending", "paid", "canceled", "reversed"}:
        raise Spec005ReviewBlock("REVIEW/BLOCK: estado financeiro legado invalido")
    paid_at = row.get("paid_at")
    if status in {"paid", "reversed"} and not paid_at:
        raise Spec005ReviewBlock("REVIEW/BLOCK: pagamento sem paid_at explicito")
    if status in {"pending", "canceled"} and paid_at:
        raise Spec005ReviewBlock("REVIEW/BLOCK: paid_at incoerente com estado")
    if status == "canceled" and not row.get("canceled_at"):
        raise Spec005ReviewBlock("REVIEW/BLOCK: cancelamento sem metadados")
    if status == "canceled" and not str(row.get("cancellation_reason") or "").strip():
        raise Spec005ReviewBlock("REVIEW/BLOCK: cancelamento sem motivo")
    if status == "reversed" and not row.get("reversed_at"):
        raise Spec005ReviewBlock("REVIEW/BLOCK: estorno sem metadados")
    if status == "reversed" and not str(row.get("reversal_reason") or "").strip():
        raise Spec005ReviewBlock("REVIEW/BLOCK: estorno sem motivo")


def _validate_competence(row, resource):
    if "competence_date" in row:
        raise Spec005ReviewBlock(
            f"REVIEW/BLOCK: {resource} usa competence_date diario incompatível com D005-08"
        )
    year = _require_explicit(row, "competence_year", resource)
    month = _require_explicit(row, "competence_month", resource)
    if isinstance(year, bool) or not isinstance(year, int) or not 1 <= year <= 9999:
        raise Spec005ReviewBlock(f"REVIEW/BLOCK: {resource} com ano de competencia invalido")
    if isinstance(month, bool) or not isinstance(month, int) or not 1 <= month <= 12:
        raise Spec005ReviewBlock(f"REVIEW/BLOCK: {resource} com mes de competencia invalido")


def _id_hash(rows):
    payload = ",".join(str(row["id"]) for row in rows).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def inventory_finance_snapshot(source) -> dict:
    source_path = _resolved(source)
    _reject_operational(source_path)
    if not source_path.is_file():
        raise Spec005MigrationError("snapshot financeiro inexistente")
    with _read_only_connection(source_path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
        if not {"payments", "expenses"} <= tables:
            raise Spec005MigrationError("tabelas financeiras ausentes")
        payment_rows = _rows(connection, "payments")
        expense_rows = _rows(connection, "expenses")
        return {
            "payment_count": len(payment_rows),
            "expense_count": len(expense_rows),
            "payment_has_explicit_competence": {
                "competence_year", "competence_month"
            } <= _columns(connection, "payments"),
            "expense_has_explicit_competence": {
                "competence_year", "competence_month"
            } <= _columns(connection, "expenses"),
            "payment_has_legacy_daily_competence": "competence_date" in _columns(connection, "payments"),
            "expense_has_legacy_daily_competence": "competence_date" in _columns(connection, "expenses"),
            "null_appointment_count": sum(row.get("appointment_id") is None for row in payment_rows),
            "payment_ids_sha256": _id_hash(payment_rows),
            "expense_ids_sha256": _id_hash(expense_rows),
        }


def _create_target_schema(connection):
    connection.executescript(
        """
        CREATE TABLE expense_categories (
          id INTEGER PRIMARY KEY, name VARCHAR(80) NOT NULL UNIQUE,
          active BOOLEAN NOT NULL DEFAULT 1, version INTEGER NOT NULL DEFAULT 1,
          created_by_user_id INTEGER REFERENCES users(id) ON DELETE NO ACTION,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT ck_expense_categories_name CHECK (length(trim(name)) > 0)
        );
        CREATE TABLE payments (
          id INTEGER PRIMARY KEY,
          patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE NO ACTION,
          appointment_id INTEGER REFERENCES appointments(id) ON DELETE NO ACTION,
          competence_year INTEGER NOT NULL, competence_month INTEGER NOT NULL,
          due_date DATE NOT NULL, paid_at DATE,
          amount_cents INTEGER NOT NULL,
          status VARCHAR(30) NOT NULL DEFAULT 'pending',
          payment_method VARCHAR(50) NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
          version INTEGER NOT NULL DEFAULT 1,
          created_by_user_id INTEGER REFERENCES users(id) ON DELETE NO ACTION,
          canceled_by_user_id INTEGER REFERENCES users(id) ON DELETE NO ACTION,
          reversed_by_user_id INTEGER REFERENCES users(id) ON DELETE NO ACTION,
          canceled_at DATETIME, reversed_at DATETIME,
          cancellation_reason TEXT NOT NULL DEFAULT '', reversal_reason TEXT NOT NULL DEFAULT '',
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT ck_payments_amount_positive CHECK (amount_cents > 0),
          CONSTRAINT ck_payments_competence_year CHECK (competence_year BETWEEN 1 AND 9999),
          CONSTRAINT ck_payments_competence_month CHECK (competence_month BETWEEN 1 AND 12),
          CONSTRAINT ck_payments_status CHECK (status IN ('pending','paid','canceled','reversed')),
          CONSTRAINT ck_payments_lifecycle CHECK (
            (status='pending' AND paid_at IS NULL AND canceled_at IS NULL AND reversed_at IS NULL) OR
            (status='paid' AND paid_at IS NOT NULL AND canceled_at IS NULL AND reversed_at IS NULL) OR
            (status='canceled' AND paid_at IS NULL AND canceled_at IS NOT NULL AND reversed_at IS NULL AND length(trim(cancellation_reason)) > 0) OR
            (status='reversed' AND paid_at IS NOT NULL AND canceled_at IS NULL AND reversed_at IS NOT NULL AND length(trim(reversal_reason)) > 0)
          )
        );
        CREATE TABLE expenses (
          id INTEGER PRIMARY KEY, description VARCHAR(160) NOT NULL,
          amount_cents INTEGER NOT NULL, expense_date DATE NOT NULL,
          competence_year INTEGER NOT NULL, competence_month INTEGER NOT NULL,
          category_id INTEGER NOT NULL REFERENCES expense_categories(id) ON DELETE NO ACTION,
          status VARCHAR(30) NOT NULL DEFAULT 'active', version INTEGER NOT NULL DEFAULT 1,
          created_by_user_id INTEGER REFERENCES users(id) ON DELETE NO ACTION,
          canceled_by_user_id INTEGER REFERENCES users(id) ON DELETE NO ACTION,
          canceled_at DATETIME, cancellation_reason TEXT NOT NULL DEFAULT '',
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT ck_expenses_amount_positive CHECK (amount_cents > 0),
          CONSTRAINT ck_expenses_competence_year CHECK (competence_year BETWEEN 1 AND 9999),
          CONSTRAINT ck_expenses_competence_month CHECK (competence_month BETWEEN 1 AND 12),
          CONSTRAINT ck_expenses_status CHECK (status IN ('active','canceled')),
          CONSTRAINT ck_expenses_lifecycle CHECK (
            (status='active' AND canceled_at IS NULL) OR
            (status='canceled' AND canceled_at IS NOT NULL AND length(trim(cancellation_reason)) > 0)
          )
        );
        CREATE TABLE financial_events (
          id INTEGER PRIMARY KEY, resource_type VARCHAR(32) NOT NULL, resource_id INTEGER NOT NULL,
          actor_user_id INTEGER REFERENCES users(id) ON DELETE NO ACTION,
          event_type VARCHAR(40) NOT NULL, from_status VARCHAR(30), to_status VARCHAR(30),
          reason TEXT NOT NULL DEFAULT '', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT ck_financial_events_resource_type CHECK (resource_type IN ('payment','expense','expense_category')),
          CONSTRAINT ck_financial_events_event_type CHECK (length(trim(event_type)) > 0)
        );
        CREATE INDEX ix_payments_cash_period ON payments(status, paid_at);
        CREATE INDEX ix_payments_accrual_period ON payments(competence_year, competence_month, status);
        CREATE INDEX ix_payments_due_status ON payments(due_date, status);
        CREATE INDEX ix_payments_patient ON payments(patient_id);
        CREATE INDEX ix_payments_appointment ON payments(appointment_id);
        CREATE INDEX ix_expenses_cash_period ON expenses(expense_date, status);
        CREATE INDEX ix_expenses_accrual_period ON expenses(competence_year, competence_month, status);
        CREATE INDEX ix_expenses_category ON expenses(category_id);
        CREATE INDEX ix_financial_events_resource ON financial_events(resource_type, resource_id, created_at);
        CREATE TRIGGER spec005_payments_no_delete BEFORE DELETE ON payments
          BEGIN SELECT RAISE(ABORT, 'payments history is protected'); END;
        CREATE TRIGGER spec005_expenses_no_delete BEFORE DELETE ON expenses
          BEGIN SELECT RAISE(ABORT, 'expenses history is protected'); END;
        CREATE TRIGGER spec005_expense_categories_no_delete BEFORE DELETE ON expense_categories
          BEGIN SELECT RAISE(ABORT, 'expense_categories history is protected'); END;
        CREATE TRIGGER spec005_financial_events_no_update BEFORE UPDATE ON financial_events
          BEGIN SELECT RAISE(ABORT, 'financial_events is append-only'); END;
        CREATE TRIGGER spec005_financial_events_no_delete BEFORE DELETE ON financial_events
          BEGIN SELECT RAISE(ABORT, 'financial_events is append-only'); END;
        """
    )


def migrate_finance_candidate(source, output, recovery=None) -> FinanceMigrationEvidence:
    source_path = _resolved(source)
    output_path = _resolved(output)
    recovery_path = _resolved(
        recovery if recovery is not None else output_path.with_suffix(output_path.suffix + ".recovery-check")
    )
    _reject_operational(source_path)
    _reject_operational(output_path)
    _reject_operational(recovery_path)
    if len({source_path, output_path, recovery_path}) != 3:
        raise Spec005MigrationError("origem, candidato e recovery devem ser distintos")
    if not source_path.is_file():
        raise Spec005MigrationError("snapshot financeiro inexistente")
    if output_path.exists():
        raise Spec005MigrationError("candidato ja existe")
    if recovery_path.exists():
        raise Spec005MigrationError("destino de recovery ja existe")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with _read_only_connection(source_path) as source_connection:
        payments = _rows(source_connection, "payments")
        expenses = _rows(source_connection, "expenses")
        for row in payments:
            _validate_competence(row, "cobranca")
            _validate_payment(row)
            row["amount_cents"] = exact_cents(row.get("amount"))
        for row in expenses:
            _validate_competence(row, "despesa")
            _require_explicit(row, "category", "despesa")
            if row.get("status") not in (None, "active", "canceled"):
                raise Spec005ReviewBlock("REVIEW/BLOCK: estado de despesa legado invalido")
            if row.get("status") == "canceled":
                _require_explicit(row, "canceled_at", "despesa cancelada")
                _require_explicit(row, "cancellation_reason", "despesa cancelada")
            row["amount_cents"] = exact_cents(row.get("amount"))

    shutil.copy2(source_path, output_path)
    connection = sqlite3.connect(output_path)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("ALTER TABLE payments RENAME TO payments_spec005_legacy")
        connection.execute("ALTER TABLE expenses RENAME TO expenses_spec005_legacy")
        _create_target_schema(connection)
        categories = sorted({str(row["category"]).strip() for row in expenses})
        category_ids = {name: index + 1 for index, name in enumerate(categories)}
        connection.executemany(
            "INSERT INTO expense_categories(id,name,active) VALUES(?,?,1)",
            [(category_id, name) for name, category_id in category_ids.items()],
        )
        for row in payments:
            connection.execute(
                """INSERT INTO payments(
                  id,patient_id,appointment_id,competence_year,competence_month,due_date,paid_at,amount_cents,status,
                  payment_method,description,version,canceled_at,reversed_at,cancellation_reason,reversal_reason
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["id"], row["patient_id"], row.get("appointment_id"),
                    row["competence_year"], row["competence_month"],
                    row["due_date"], row.get("paid_at"), row["amount_cents"], row["status"],
                    row.get("payment_method") or "", row.get("description") or "", row.get("version") or 1,
                    row.get("canceled_at"), row.get("reversed_at"), row.get("cancellation_reason") or "",
                    row.get("reversal_reason") or "",
                ),
            )
            connection.execute(
                "INSERT INTO financial_events(resource_type,resource_id,event_type,to_status,reason) VALUES('payment',?,'imported',?,'legacy-forward-only')",
                (row["id"], row["status"]),
            )
        for row in expenses:
            connection.execute(
                """INSERT INTO expenses(
                  id,description,amount_cents,expense_date,competence_year,competence_month,category_id,status,version,
                  canceled_at,cancellation_reason
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["id"], row["description"], row["amount_cents"], row["expense_date"],
                    row["competence_year"], row["competence_month"],
                    category_ids[str(row["category"]).strip()],
                    row.get("status") or "active", row.get("version") or 1, row.get("canceled_at"),
                    row.get("cancellation_reason") or "",
                ),
            )
            connection.execute(
                "INSERT INTO financial_events(resource_type,resource_id,event_type,to_status,reason) VALUES('expense',?,'imported',?,'legacy-forward-only')",
                (row["id"], row.get("status") or "active"),
            )
        connection.execute("DROP TABLE payments_spec005_legacy")
        connection.execute("DROP TABLE expenses_spec005_legacy")
        connection.commit()
        connection.execute("PRAGMA foreign_keys=ON")
        violations = list(connection.execute("PRAGMA foreign_key_check"))
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        candidate_payment_count = connection.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
        candidate_expense_count = connection.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        payment_total = connection.execute("SELECT COALESCE(SUM(amount_cents),0) FROM payments").fetchone()[0]
        expense_total = connection.execute("SELECT COALESCE(SUM(amount_cents),0) FROM expenses").fetchone()[0]
        null_count = connection.execute("SELECT COUNT(*) FROM payments WHERE appointment_id IS NULL").fetchone()[0]
        candidate_payments = [dict(row) for row in connection.execute("SELECT id FROM payments ORDER BY id")]
        candidate_expenses = [dict(row) for row in connection.execute("SELECT id FROM expenses ORDER BY id")]
        if (
            violations or integrity != "ok" or candidate_payment_count != len(payments)
            or candidate_expense_count != len(expenses) or null_count != sum(row.get("appointment_id") is None for row in payments)
            or _id_hash(candidate_payments) != _id_hash(payments) or _id_hash(candidate_expenses) != _id_hash(expenses)
        ):
            raise Spec005MigrationError("reconciliacao do candidato falhou")
    finally:
        connection.close()

    shutil.copy2(output_path, recovery_path)
    with sqlite3.connect(recovery_path) as recovery:
        recovery_integrity = recovery.execute("PRAGMA integrity_check").fetchone()[0]
        recovery_counts = (
            recovery.execute("SELECT COUNT(*) FROM payments").fetchone()[0],
            recovery.execute("SELECT COUNT(*) FROM expenses").fetchone()[0],
        )
    if recovery_integrity != "ok" or recovery_counts != (len(payments), len(expenses)):
        raise Spec005MigrationError("recovery do candidato falhou")

    return FinanceMigrationEvidence(
        source_payment_count=len(payments),
        source_expense_count=len(expenses),
        candidate_payment_count=candidate_payment_count,
        candidate_expense_count=candidate_expense_count,
        payment_total_cents=payment_total,
        expense_total_cents=expense_total,
        null_appointment_count=null_count,
        payment_ids_sha256=_id_hash(candidate_payments),
        expense_ids_sha256=_id_hash(candidate_expenses),
        foreign_key_violations=len(violations),
        integrity_check=integrity,
        recovery_check="ok",
    )
