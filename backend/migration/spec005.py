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
from backend.cutover.infrastructure import CutoverError, read_pointer, verify_runtime_manifest
from backend.cutover.spec005_execution_identity import verify_persisted_source
from backend.migration.spec005_identity import (
    CANONICALIZATION_VERSION, file_sha256, row_fingerprint,
)


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
    quarantined_count: int = 0
    source_database_sha256: str = ""
    identity_manifest_sha256: str = ""

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


def _verified_operational_source_identity(source_path: Path,
                                          historical_code_root: Path | None = None,
                                          persisted_source_expectations: dict | None = None) -> tuple[str, int, str]:
    """Vincula um snapshot byte a byte ao pointer e ao freeze operacionais.

    Os caminhos configuráveis são os mesmos usados pelo bootstrap normal. Nenhum
    valor do manifesto legado participa da construção desta identidade.
    """
    default_root = Path(os.getenv("LOCALAPPDATA", PROJECT_ROOT)) / "ClinicaGabriela" / "runtime"
    runtime_root = _resolved(os.getenv("CLINICA_RUNTIME_ROOT", default_root))
    pointer_path = _resolved(os.getenv("CLINICA_OPERATIONAL_POINTER", runtime_root / "operational-pointer.json"))
    manifest_dir = _resolved(os.getenv("CLINICA_RUNTIME_MANIFEST_DIR", pointer_path.parent / "runtime-manifests"))
    if persisted_source_expectations is not None:
        try:
            verified = verify_persisted_source(
                pointer_path, manifest_dir, source_path,
                expected_pointer_sha256=persisted_source_expectations["pointer_sha256"],
                expected_manifest_sha256=persisted_source_expectations["runtime_manifest_sha256"],
                expected_database_sha256=persisted_source_expectations["database_sha256"],
                expected_generation=persisted_source_expectations["source_generation"])
            if verified != persisted_source_expectations:
                raise ValueError("identidade D005-12 divergente")
        except (KeyError, ValueError, OSError) as exc:
            raise Spec005ReviewBlock("REVIEW/BLOCK: identidade D005-12 nao verificada") from exc
        return (verified["database_sha256"], verified["source_generation"],
                verified["runtime_manifest_sha256"])
    code_root = _resolved(historical_code_root) if historical_code_root is not None else _resolved(
        os.getenv("CLINICA_RUNTIME_CODE_ROOT", PROJECT_ROOT))
    try:
        pointer = read_pointer(pointer_path)
        manifest_path = manifest_dir / f"runtime-manifest-{pointer.runtime_manifest_checksum_sha256}.json"
        verify_runtime_manifest(code_root, manifest_path, pointer.runtime_manifest_checksum_sha256)
        if pointer.state != "canonical" or file_sha256(source_path) != pointer.database_checksum_sha256:
            raise ValueError("snapshot não corresponde à Generation verificada")
    except (OSError, ValueError, CutoverError) as exc:
        raise Spec005ReviewBlock("REVIEW/BLOCK: identidade operacional da fonte não verificada") from exc
    return pointer.database_checksum_sha256, pointer.generation, pointer.runtime_manifest_checksum_sha256


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


def _verify_identity_manifest(path, source_sha, payments, expenses, verified_identity=None):
    if path is None:
        return {}, "", {}
    manifest_path = _resolved(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = payload["records"]
        if payload["decision_id"] != "D005-10" or payload["canonicalization_version"] != CANONICALIZATION_VERSION:
            raise ValueError
        if (not isinstance(payload["source_generation"], int) or payload["source_generation"] <= 0
            or not isinstance(payload["source_manifest_sha256"], str)
            or len(payload["source_manifest_sha256"]) != 64):
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Spec005ReviewBlock("REVIEW/BLOCK: manifesto de identidade invalido") from exc
    if verified_identity is None or (
        source_sha, payload["source_generation"], payload["source_manifest_sha256"]
    ) != verified_identity:
        raise Spec005ReviewBlock("REVIEW/BLOCK: proveniência operacional divergente")
    source = {("payment", row["id"]): row for row in payments}
    source.update({("expense", row["id"]): row for row in expenses})
    if len(source) != len(payments) + len(expenses) or not isinstance(entries, list):
        raise Spec005ReviewBlock("REVIEW/BLOCK: identidade da fonte duplicada")
    mapped = {}
    for entry in entries:
        try:
            key = (entry["entity_type"], entry["source_internal_id"])
            if key in mapped or key not in source:
                raise ValueError
            if entry["source_database_sha"] != source_sha:
                raise ValueError
            if entry["source_row_fingerprint"] != row_fingerprint(key[0], source[key]):
                raise ValueError
            if entry["competence_year"] != source[key].get("competence_year") or entry["competence_month"] != source[key].get("competence_month"):
                # A fonte anterior a D005-08 não traz competência explícita.
                if "competence_year" in source[key] or "competence_month" in source[key]:
                    raise ValueError
            if entry["intended_disposition"] not in {"CANONICAL_MIGRATED", "QUARANTINED_UNRESOLVED"}:
                raise ValueError
            if entry["intended_disposition"] == "QUARANTINED_UNRESOLVED" and (
                key[0] != "payment" or source[key].get("status") != "paid"
                or source[key].get("paid_at") is not None
                or entry.get("quarantine_reason") != "PAID_WITH_UNKNOWN_PAID_AT"
            ):
                raise ValueError
            mapped[key] = entry
        except (KeyError, TypeError, ValueError) as exc:
            raise Spec005ReviewBlock("REVIEW/BLOCK: identidade, hash ou disposition divergente") from exc
    if set(mapped) != set(source):
        raise Spec005ReviewBlock("REVIEW/BLOCK: mapeamento incompleto")
    return mapped, file_sha256(manifest_path), payload


def classify_finance_source_read_only(source, identity_manifest, expected_sha256, *,
                                      historical_code_root=None, persisted_source_expectations=None):
    """Classifica fonte real sem candidato, mutation ou exposição de linhas."""
    source_path = _resolved(source)
    if file_sha256(source_path) != expected_sha256:
        raise Spec005ReviewBlock("REVIEW/BLOCK: hash do banco fonte divergente")
    verified_identity = _verified_operational_source_identity(source_path, historical_code_root,
                                                              persisted_source_expectations)
    if verified_identity[0] != expected_sha256:
        raise Spec005ReviewBlock("REVIEW/BLOCK: hash operacional divergente")
    with _read_only_connection(source_path) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise Spec005ReviewBlock("REVIEW/BLOCK: integridade da fonte")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise Spec005ReviewBlock("REVIEW/BLOCK: FK da fonte")
        payments, expenses = _rows(connection, "payments"), _rows(connection, "expenses")
    mapping, mapping_sha, _ = _verify_identity_manifest(identity_manifest, expected_sha256, payments, expenses, verified_identity)
    result = []
    for entity_type, rows in (("payment", payments), ("expense", expenses)):
        for row in rows:
            entry = mapping[(entity_type, row["id"])]
            row["competence_year"] = entry["competence_year"]
            row["competence_month"] = entry["competence_month"]
            _validate_competence(row, entity_type)
            exact_cents(row.get("amount"))
            if entry["intended_disposition"] == "CANONICAL_MIGRATED":
                if entity_type == "payment":
                    _validate_payment(row)
                else:
                    _require_explicit(row, "category", "despesa")
                    if row.get("status") not in (None, "active", "canceled"):
                        raise Spec005ReviewBlock("REVIEW/BLOCK: estado de despesa legado invalido")
            result.append((entity_type, row["id"], entry["intended_disposition"]))
    return {"source_count": len(result), "canonical_count": sum(x[2] == "CANONICAL_MIGRATED" for x in result),
            "quarantine_count": sum(x[2] == "QUARANTINED_UNRESOLVED" for x in result),
            "dispositions": result, "identity_manifest_sha256": mapping_sha}


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
        CREATE TABLE legacy_financial_quarantine (
          id INTEGER PRIMARY KEY,
          source_database_sha256 TEXT NOT NULL,
          source_generation INTEGER NOT NULL,
          source_entity_type TEXT NOT NULL,
          source_record_id INTEGER NOT NULL,
          source_record_sha256 TEXT NOT NULL,
          legacy_status TEXT NOT NULL,
          legacy_amount_text TEXT NOT NULL,
          legacy_currency TEXT NOT NULL DEFAULT 'BRL',
          amount_cents INTEGER NOT NULL,
          competence_year INTEGER NOT NULL,
          competence_month INTEGER NOT NULL,
          reason_code TEXT NOT NULL,
          quarantined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          decision_id TEXT NOT NULL,
          source_manifest_sha256 TEXT NOT NULL,
          mapping_sha256 TEXT NOT NULL,
          migration_execution_id TEXT NOT NULL,
          resolution_state TEXT NOT NULL DEFAULT 'unresolved',
          legacy_row_json TEXT NOT NULL,
          UNIQUE(source_database_sha256,source_entity_type,source_record_id),
          CHECK(length(source_database_sha256)=64 AND length(source_record_sha256)=64),
          CHECK(length(source_manifest_sha256)=64 AND length(mapping_sha256)=64),
          CHECK(source_generation > 0),
          CHECK(source_entity_type IN ('payment','expense')),
          CHECK(source_record_id > 0),
          CHECK(amount_cents > 0),
          CHECK(competence_year BETWEEN 1 AND 9999),
          CHECK(competence_month BETWEEN 1 AND 12),
          CHECK(reason_code='PAID_WITH_UNKNOWN_PAID_AT'),
          CHECK(decision_id='D005-10'),
          CHECK(resolution_state='unresolved')
        );
        CREATE TABLE legacy_financial_quarantine_events (
          id INTEGER PRIMARY KEY,
          quarantine_id INTEGER NOT NULL REFERENCES legacy_financial_quarantine(id) ON DELETE NO ACTION,
          actor TEXT NOT NULL,
          action TEXT NOT NULL,
          evidence_sha256 TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CHECK(length(trim(actor))>0 AND length(trim(action))>0 AND length(evidence_sha256)=64)
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
        CREATE TRIGGER spec005_quarantine_no_update BEFORE UPDATE ON legacy_financial_quarantine
          BEGIN SELECT RAISE(ABORT, 'quarantine is immutable'); END;
        CREATE TRIGGER spec005_quarantine_no_delete BEFORE DELETE ON legacy_financial_quarantine
          BEGIN SELECT RAISE(ABORT, 'quarantine is immutable'); END;
        CREATE TRIGGER spec005_quarantine_events_no_update BEFORE UPDATE ON legacy_financial_quarantine_events
          BEGIN SELECT RAISE(ABORT, 'quarantine events are append-only'); END;
        CREATE TRIGGER spec005_quarantine_events_no_delete BEFORE DELETE ON legacy_financial_quarantine_events
          BEGIN SELECT RAISE(ABORT, 'quarantine events are append-only'); END;
        """
    )


# Projeção semântica: exclui somente timestamps e IDs de evento gerados no destino.
# Inclui cada valor financeiro ou vínculo preservado pelos INSERTs da migração.
_PAYMENT_FIELDS = ("id", "patient_id", "appointment_id", "competence_year", "competence_month",
                   "due_date", "paid_at", "amount_cents", "status", "payment_method", "description",
                   "version", "canceled_at", "reversed_at", "cancellation_reason", "reversal_reason")
_EXPENSE_FIELDS = ("id", "description", "amount_cents", "expense_date", "competence_year",
                   "competence_month", "category_id", "status", "version", "canceled_at", "cancellation_reason")
_QUARANTINE_FIELDS = ("source_database_sha256", "source_generation", "source_entity_type",
                      "source_record_id", "source_record_sha256", "legacy_status", "legacy_amount_text",
                      "legacy_currency", "amount_cents", "competence_year", "competence_month",
                      "reason_code", "decision_id", "source_manifest_sha256", "mapping_sha256",
                      "migration_execution_id", "resolution_state", "legacy_row_json")


def _projection_fingerprint(values: dict) -> str:
    payload = json.dumps(values, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _expected_payment(row: dict) -> dict:
    return {"id": row["id"], "patient_id": row["patient_id"], "appointment_id": row.get("appointment_id"),
            "competence_year": row["competence_year"], "competence_month": row["competence_month"],
            "due_date": row["due_date"], "paid_at": row.get("paid_at"), "amount_cents": row["amount_cents"],
            "status": row["status"], "payment_method": row.get("payment_method") or "",
            "description": row.get("description") or "", "version": row.get("version") or 1,
            "canceled_at": row.get("canceled_at"), "reversed_at": row.get("reversed_at"),
            "cancellation_reason": row.get("cancellation_reason") or "",
            "reversal_reason": row.get("reversal_reason") or ""}


def _expected_expense(row: dict, categories: dict[str, int]) -> dict:
    return {"id": row["id"], "description": row["description"], "amount_cents": row["amount_cents"],
            "expense_date": row["expense_date"], "competence_year": row["competence_year"],
            "competence_month": row["competence_month"],
            "category_id": categories[str(row["category"]).strip()], "status": row.get("status") or "active",
            "version": row.get("version") or 1, "canceled_at": row.get("canceled_at"),
            "cancellation_reason": row.get("cancellation_reason") or ""}


def _expected_quarantine(original: dict, prepared: dict, entry: dict, source_sha: str,
                         mapping_sha: str, mapping_meta: dict) -> dict:
    return {"source_database_sha256": source_sha, "source_generation": mapping_meta["source_generation"],
            "source_entity_type": "payment", "source_record_id": original["id"],
            "source_record_sha256": entry["source_row_fingerprint"], "legacy_status": original["status"],
            "legacy_amount_text": str(original["amount"]), "legacy_currency": "BRL",
            "amount_cents": prepared["amount_cents"], "competence_year": prepared["competence_year"],
            "competence_month": prepared["competence_month"], "reason_code": entry["quarantine_reason"],
            "decision_id": "D005-10", "source_manifest_sha256": mapping_meta["source_manifest_sha256"],
            "mapping_sha256": mapping_sha, "migration_execution_id": source_sha,
            "resolution_state": "unresolved", "legacy_row_json": json.dumps(original, sort_keys=True, ensure_ascii=False)}


def _assert_candidate_reconciliation(connection, payments, expenses, quarantine, original_rows,
                                     source_sha, mapping_sha, mapping_meta):
    categories = {name: index + 1 for index, name in enumerate(sorted({str(r["category"]).strip() for r in expenses}))}
    expected = {("payment", r["id"]): _expected_payment(r) for r in payments
                if r["id"] not in {q[1]["id"] for q in quarantine}}
    expected.update({("expense", r["id"]): _expected_expense(r, categories) for r in expenses})
    actual = {}
    for entity, table, fields in (("payment", "payments", _PAYMENT_FIELDS),
                                  ("expense", "expenses", _EXPENSE_FIELDS)):
        columns = ",".join(fields)
        for row in connection.execute(f"SELECT {columns} FROM {table}"):
            values = dict(zip(fields, row))
            key = (entity, values["id"])
            if key in actual:
                raise Spec005MigrationError("reconciliacao: identidade canonical duplicada")
            actual[key] = values
    expected_quarantine = {}
    for entity, prepared, entry in quarantine:
        key = (entity, prepared["id"])
        expected_quarantine[key] = _expected_quarantine(original_rows[key], prepared, entry,
                                                        source_sha, mapping_sha, mapping_meta)
    actual_quarantine = {}
    for row in connection.execute("SELECT " + ",".join(_QUARANTINE_FIELDS) + " FROM legacy_financial_quarantine"):
        values = dict(zip(_QUARANTINE_FIELDS, row))
        key = (values["source_entity_type"], values["source_record_id"])
        if key in actual_quarantine:
            raise Spec005MigrationError("reconciliacao: identidade quarantine duplicada")
        actual_quarantine[key] = values
    source_keys = set(original_rows)
    if (set(expected) != set(actual) or set(expected_quarantine) != set(actual_quarantine)
        or source_keys != set(actual) | set(actual_quarantine)
        or set(actual) & set(actual_quarantine)):
        raise Spec005MigrationError("reconciliacao: particao de identidades divergente")
    for key, values in expected.items():
        if _projection_fingerprint(values) != _projection_fingerprint(actual[key]):
            raise Spec005MigrationError("reconciliacao: projection canonical divergente")
    for key, values in expected_quarantine.items():
        observed = actual_quarantine[key]
        if (_projection_fingerprint(values) != _projection_fingerprint(observed)
            or json.loads(observed["legacy_row_json"]).get("paid_at") is not None
            or row_fingerprint(key[0], json.loads(observed["legacy_row_json"])) != values["source_record_sha256"]):
            raise Spec005MigrationError("reconciliacao: projection quarantine divergente")
    if sum(v["amount_cents"] for v in actual.values()) + sum(v["amount_cents"] for v in actual_quarantine.values()) != sum(r["amount_cents"] for r in payments + expenses):
        raise Spec005MigrationError("reconciliacao: valor total divergente")


def migrate_finance_candidate(source, output, recovery=None, *, identity_manifest=None,
                              historical_code_root=None, persisted_source_expectations=None) -> FinanceMigrationEvidence:
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
    source_sha = file_sha256(source_path)
    verified_identity = (_verified_operational_source_identity(source_path, historical_code_root,
                                                               persisted_source_expectations)
                         if identity_manifest is not None else None)

    with _read_only_connection(source_path) as source_connection:
        payments = _rows(source_connection, "payments")
        expenses = _rows(source_connection, "expenses")
        mapping, mapping_sha, mapping_meta = _verify_identity_manifest(identity_manifest, source_sha, payments, expenses, verified_identity)
        original_rows = {("payment", row["id"]): dict(row) for row in payments}
        original_rows.update({("expense", row["id"]): dict(row) for row in expenses})
        quarantine = []
        for row in payments:
            entry = mapping.get(("payment", row["id"]))
            if entry and "competence_year" not in row:
                row["competence_year"] = entry["competence_year"]
                row["competence_month"] = entry["competence_month"]
            _validate_competence(row, "cobranca")
            row["amount_cents"] = exact_cents(row.get("amount"))
            if entry and entry["intended_disposition"] == "QUARANTINED_UNRESOLVED":
                quarantine.append(("payment", row, entry))
            else:
                _validate_payment(row)
        for row in expenses:
            entry = mapping.get(("expense", row["id"]))
            if entry and "competence_year" not in row:
                row["competence_year"] = entry["competence_year"]
                row["competence_month"] = entry["competence_month"]
            _validate_competence(row, "despesa")
            _require_explicit(row, "category", "despesa")
            if row.get("status") not in (None, "active", "canceled"):
                raise Spec005ReviewBlock("REVIEW/BLOCK: estado de despesa legado invalido")
            if row.get("status") == "canceled":
                _require_explicit(row, "canceled_at", "despesa cancelada")
                _require_explicit(row, "cancellation_reason", "despesa cancelada")
            row["amount_cents"] = exact_cents(row.get("amount"))
        if identity_manifest is None and any(row.get("status") == "paid" and not row.get("paid_at") for row in payments):
            raise Spec005ReviewBlock("REVIEW/BLOCK: pagamento sem paid_at explicito")

    output_path.parent.mkdir(parents=True, exist_ok=True)
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
            if any(item[1]["id"] == row["id"] for item in quarantine):
                continue
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
        for entity_type, row, entry in quarantine:
            original = original_rows[(entity_type, row["id"])]
            cursor = connection.execute(
                """INSERT INTO legacy_financial_quarantine(
                  source_database_sha256,source_generation,source_entity_type,source_record_id,
                  source_record_sha256,legacy_status,legacy_amount_text,amount_cents,
                  competence_year,competence_month,reason_code,decision_id,
                  source_manifest_sha256,mapping_sha256,migration_execution_id,legacy_row_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (source_sha, mapping_meta["source_generation"], entity_type, row["id"], entry["source_row_fingerprint"],
                 original["status"], str(original["amount"]), row["amount_cents"],
                 row["competence_year"], row["competence_month"], entry["quarantine_reason"],
                 "D005-10", mapping_meta["source_manifest_sha256"],
                 mapping_sha, source_sha, json.dumps(original, sort_keys=True, ensure_ascii=False)),
            )
            connection.execute(
                "INSERT INTO legacy_financial_quarantine_events(quarantine_id,actor,action,evidence_sha256) VALUES(?,?,?,?)",
                (cursor.lastrowid, "D005-10", "QUARANTINED_UNRESOLVED", mapping_sha),
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
            violations or integrity != "ok" or candidate_payment_count != len(payments) - len(quarantine)
            or candidate_expense_count != len(expenses) or null_count != sum(row.get("appointment_id") is None for row in payments if row["id"] not in {q[1]["id"] for q in quarantine})
            or _id_hash(candidate_payments) != _id_hash([row for row in payments if row["id"] not in {q[1]["id"] for q in quarantine}])
            or _id_hash(candidate_expenses) != _id_hash(expenses)
        ):
            raise Spec005MigrationError("reconciliacao do candidato falhou")
        quarantine_rows = [dict(row) for row in connection.execute("SELECT * FROM legacy_financial_quarantine")]
        source_keys = {("payment", row["id"]) for row in payments} | {("expense", row["id"]) for row in expenses}
        canonical_keys = {("payment", row["id"]) for row in candidate_payments} | {("expense", row["id"]) for row in candidate_expenses}
        quarantine_keys = {(row["source_entity_type"], row["source_record_id"]) for row in quarantine_rows}
        canonical_payment_rows = {row["id"]: dict(row) for row in connection.execute("SELECT id,amount_cents,status,competence_year,competence_month FROM payments")}
        canonical_expense_rows = {row["id"]: dict(row) for row in connection.execute("SELECT id,amount_cents,status,competence_year,competence_month FROM expenses")}
        expected_canonical = {
            (entity_type, row["id"]): row
            for entity_type, rows in (("payment", payments), ("expense", expenses))
            for row in rows if (entity_type, row["id"]) not in quarantine_keys
        }
        candidate_by_key = {("payment", key): value for key, value in canonical_payment_rows.items()}
        candidate_by_key.update({("expense", key): value for key, value in canonical_expense_rows.items()})
        canonical_values_match = all(
            candidate_by_key[key]["amount_cents"] == source_row["amount_cents"]
            and candidate_by_key[key]["status"] == (source_row.get("status") or "active")
            and (candidate_by_key[key]["competence_year"], candidate_by_key[key]["competence_month"])
                == (source_row["competence_year"], source_row["competence_month"])
            for key, source_row in expected_canonical.items()
        )
        quarantine_values_match = all(
            row["source_database_sha256"] == source_sha
            and row["amount_cents"] == next(q[1]["amount_cents"] for q in quarantine if (q[0], q[1]["id"]) == (row["source_entity_type"], row["source_record_id"]))
            and row["legacy_status"] == original_rows[(row["source_entity_type"], row["source_record_id"])]["status"]
            and row["mapping_sha256"] == mapping_sha
            for row in quarantine_rows
        )
        if (source_keys != canonical_keys | quarantine_keys or canonical_keys & quarantine_keys
            or len(quarantine_keys) != len(quarantine_rows)
            or not canonical_values_match or not quarantine_values_match
            or sum(row["amount_cents"] for row in quarantine_rows) + payment_total + expense_total
               != sum(row["amount_cents"] for row in payments + expenses)
            or any(row["source_record_sha256"] != row_fingerprint(row["source_entity_type"], original_rows[(row["source_entity_type"], row["source_record_id"])]) for row in quarantine_rows)):
            raise Spec005MigrationError("reconciliacao particionada falhou")
        _assert_candidate_reconciliation(connection, payments, expenses, quarantine, original_rows,
                                         source_sha, mapping_sha, mapping_meta)
    finally:
        connection.close()

    shutil.copy2(output_path, recovery_path)
    with sqlite3.connect(recovery_path) as recovery:
        recovery_integrity = recovery.execute("PRAGMA integrity_check").fetchone()[0]
        recovery_counts = (
            recovery.execute("SELECT COUNT(*) FROM payments").fetchone()[0],
            recovery.execute("SELECT COUNT(*) FROM expenses").fetchone()[0],
        )
    if recovery_integrity != "ok" or recovery_counts != (len(payments) - len(quarantine), len(expenses)):
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
        quarantined_count=len(quarantine),
        source_database_sha256=source_sha,
        identity_manifest_sha256=mapping_sha,
    )
