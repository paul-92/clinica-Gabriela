"""Analise privacy-safe e read-only de identidade entre os SQLite legados."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.sqlite_inventory import (
        DEFAULT_BACKEND_DB,
        DEFAULT_DESKTOP_DB,
        _quote_identifier,
        _readonly_connection,
        inventory_database,
    )
except ModuleNotFoundError:  # Execucao direta: python scripts/sqlite_identity_analysis.py
    from sqlite_inventory import (  # type: ignore[no-redef]
        DEFAULT_BACKEND_DB,
        DEFAULT_DESKTOP_DB,
        _quote_identifier,
        _readonly_connection,
        inventory_database,
    )


TABLE_ORDER = (
    "users", "patients", "psychologists", "clinic_settings", "appointments",
    "clinical_records", "payments", "expenses",
)

STRATEGIES = {
    "users": {
        "kind": "natural_key",
        "identity": ["username"],
        "confidence": "alta",
        "description": "username normalizado e fingerprinted",
        "foreign_keys": [],
    },
    "patients": {
        "kind": "natural_key",
        "identity": ["cpf"],
        "confidence": "alta",
        "description": "CPF normalizado para digitos e fingerprinted",
        "foreign_keys": [],
    },
    "psychologists": {
        "kind": "natural_key",
        "identity": ["crp"],
        "confidence": "alta",
        "description": "CRP normalizado e fingerprinted",
        "foreign_keys": [],
    },
    "clinic_settings": {
        "kind": "singleton",
        "identity": [],
        "confidence": "inconclusiva",
        "description": "sem chave natural; PK igual nao prova identidade",
        "foreign_keys": [],
    },
    "appointments": {
        "kind": "relational_composite",
        "identity": ["patient_id", "psychologist_id", "scheduled_at"],
        "confidence": "heuristica",
        "description": "identidades dos pais via FK + horario agendado",
        "foreign_keys": ["patient_id -> patients.id", "psychologist_id -> psychologists.id"],
    },
    "clinical_records": {
        "kind": "relational_composite",
        "identity": ["patient_id", "psychologist_id", "appointment_date"],
        "confidence": "heuristica",
        "description": "identidades dos pais via FK + data do atendimento",
        "foreign_keys": ["patient_id -> patients.id", "psychologist_id -> psychologists.id"],
    },
    "payments": {
        "kind": "relational_composite",
        "identity": ["patient_id", "appointment_id", "due_date", "amount"],
        "confidence": "heuristica",
        "description": "identidade do paciente, agendamento relacionado, vencimento e valor",
        "foreign_keys": ["patient_id -> patients.id", "appointment_id -> appointments.id"],
    },
    "expenses": {
        "kind": "composite",
        "identity": ["expense_date", "amount", "description", "category"],
        "confidence": "heuristica",
        "description": "data, valor e fingerprints de descricao/categoria",
        "foreign_keys": [],
    },
}

SENSITIVE_FIELDS = {
    "name", "full_name", "username", "password_hash", "cpf", "crp", "phone",
    "email", "address", "emergency_contact", "notes", "clinic_name", "description",
    "payment_method", "main_complaint", "session_goals", "observed_mood",
    "clinical_evolution", "interventions", "referrals", "next_steps", "private_notes",
    "clinical_hypotheses", "therapeutic_plan", "future_attachments",
}


class EphemeralFingerprinter:
    def __init__(self, key: bytes | None = None) -> None:
        self._key = key or os.urandom(32)

    @staticmethod
    def normalize(value: Any, digits_only: bool = False) -> str:
        if value is None:
            return ""
        text = unicodedata.normalize("NFKC", str(value)).strip().casefold()
        return "".join(character for character in text if character.isdigit()) if digits_only else " ".join(text.split())

    def value(self, table: str, field: str, value: Any, *, digits_only: bool = False) -> str | None:
        normalized = self.normalize(value, digits_only)
        if not normalized:
            return None
        message = f"spec008:{table}:{field}:{normalized}".encode("utf-8")
        return hmac.new(self._key, message, hashlib.sha256).hexdigest()

    def composite(self, table: str, parts: list[Any]) -> str | None:
        if any(part is None or part == "" for part in parts):
            return None
        message = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        return hmac.new(self._key, f"spec008:{table}:".encode() + message, hashlib.sha256).hexdigest()


def _read_tables(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.expanduser().resolve(strict=False).is_file():
        return {}
    tables: dict[str, list[dict[str, Any]]] = {}
    with _readonly_connection(path) as connection:
        available = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        for table in TABLE_ORDER:
            if table not in available:
                continue
            quoted = _quote_identifier(table)
            tables[table] = [dict(row) for row in connection.execute(f"SELECT * FROM {quoted}")]
    return tables


def _base_identity_maps(
    tables: dict[str, list[dict[str, Any]]], fp: EphemeralFingerprinter,
) -> dict[str, dict[Any, str | None]]:
    definitions = {"users": ("username", False), "patients": ("cpf", True), "psychologists": ("crp", False)}
    maps = {}
    for table, (field, digits_only) in definitions.items():
        maps[table] = {
            row["id"]: fp.value(table, field, row.get(field), digits_only=digits_only)
            for row in tables.get(table, [])
        }
    return maps


def _identity_builder(
    table: str,
    tables: dict[str, list[dict[str, Any]]],
    fp: EphemeralFingerprinter,
    base_maps: dict[str, dict[Any, str | None]],
) -> Callable[[dict[str, Any]], str | None]:
    if table == "users":
        return lambda row: fp.value(table, "username", row.get("username"))
    if table == "patients":
        return lambda row: fp.value(table, "cpf", row.get("cpf"), digits_only=True)
    if table == "psychologists":
        return lambda row: fp.value(table, "crp", row.get("crp"))
    if table == "clinic_settings":
        return lambda _row: None
    if table in {"appointments", "clinical_records"}:
        date_field = "scheduled_at" if table == "appointments" else "appointment_date"
        return lambda row: fp.composite(table, [
            base_maps.get("patients", {}).get(row.get("patient_id")),
            base_maps.get("psychologists", {}).get(row.get("psychologist_id")),
            fp.normalize(row.get(date_field)),
        ])
    if table == "payments":
        appointment_rows = {row["id"]: row for row in tables.get("appointments", [])}
        appointment_key = _identity_builder("appointments", tables, fp, base_maps)
        return lambda row: fp.composite(table, [
            base_maps.get("patients", {}).get(row.get("patient_id")),
            appointment_key(appointment_rows[row["appointment_id"]]) if row.get("appointment_id") in appointment_rows else "sem-agendamento",
            fp.normalize(row.get("due_date")), fp.normalize(row.get("amount")),
        ])
    if table == "expenses":
        return lambda row: fp.composite(table, [
            fp.normalize(row.get("expense_date")), fp.normalize(row.get("amount")),
            fp.value(table, "description", row.get("description")),
            fp.value(table, "category", row.get("category")),
        ])
    return lambda _row: None


def _difference_types(
    table: str,
    left: dict[str, Any],
    right: dict[str, Any],
    fp: EphemeralFingerprinter,
) -> list[str]:
    ignored = {"id"}
    differences = []
    for field in sorted((set(left) | set(right)) - ignored):
        if field in SENSITIVE_FIELDS:
            left_value = fp.value(table, field, left.get(field))
            right_value = fp.value(table, field, right.get(field))
            differs = left_value != right_value
        else:
            differs = left.get(field) != right.get(field)
        if differs:
            differences.append(f"campo_divergente:{field}")
    return differences


def _reconcile_table(
    table: str,
    left_rows: list[dict[str, Any]],
    right_rows: list[dict[str, Any]],
    left_key: Callable[[dict[str, Any]], str | None],
    right_key: Callable[[dict[str, Any]], str | None],
    fp: EphemeralFingerprinter,
) -> dict[str, Any]:
    left_by_id = {row["id"]: row for row in left_rows}
    right_by_id = {row["id"]: row for row in right_rows}
    same_ids = set(left_by_id) & set(right_by_id)
    left_keys = {row["id"]: left_key(row) for row in left_rows}
    right_keys = {row["id"]: right_key(row) for row in right_rows}
    left_groups: dict[str, list[Any]] = defaultdict(list)
    right_groups: dict[str, list[Any]] = defaultdict(list)
    for record_id, key in left_keys.items():
        if key is not None:
            left_groups[key].append(record_id)
    for record_id, key in right_keys.items():
        if key is not None:
            right_groups[key].append(record_id)

    matched_left: set[Any] = set()
    matched_right: set[Any] = set()
    probable = 0
    inconclusive = 0
    divergence_types: Counter[str] = Counter()
    different_id_matches = 0
    same_id_same_identity = sum(
        left_keys[record_id] is not None
        and left_keys[record_id] == right_keys[record_id]
        for record_id in same_ids
    )
    for key in set(left_groups) & set(right_groups):
        left_ids, right_ids = left_groups[key], right_groups[key]
        if len(left_ids) == len(right_ids) == 1:
            left_id, right_id = left_ids[0], right_ids[0]
            matched_left.add(left_id)
            matched_right.add(right_id)
            probable += 1
            different_id_matches += int(left_id != right_id)
            divergence_types.update(
                _difference_types(table, left_by_id[left_id], right_by_id[right_id], fp)
            )
        else:
            matched_left.update(left_ids)
            matched_right.update(right_ids)
            inconclusive += max(len(left_ids), len(right_ids))
            divergence_types["chave_de_correspondencia_ambigua"] += 1

    pk_collisions = 0
    conflicts = 0
    for record_id in same_ids:
        left_identity, right_identity = left_keys[record_id], right_keys[record_id]
        if left_identity is not None and right_identity is not None and left_identity != right_identity:
            pk_collisions += 1
            conflicts += 1
            divergence_types["mesma_pk_identidade_diferente"] += 1
            matched_left.add(record_id)
            matched_right.add(record_id)
        elif record_id not in matched_left and record_id not in matched_right:
            inconclusive += 1
            divergence_types["mesma_pk_sem_prova_de_identidade"] += 1
            matched_left.add(record_id)
            matched_right.add(record_id)

    desktop_only = len([row for row in left_rows if row["id"] not in matched_left])
    backend_only = len([row for row in right_rows if row["id"] not in matched_right])
    missing_identity = sum(key is None for key in left_keys.values()) + sum(key is None for key in right_keys.values())
    if missing_identity:
        divergence_types["identificador_necessario_ausente"] += missing_identity
    return {
        "same_id": len(same_ids),
        "probable_same_entity": probable,
        "conflicts": conflicts,
        "desktop_only": desktop_only,
        "backend_only": backend_only,
        "inconclusive": inconclusive,
        "pk_collisions": pk_collisions,
        "equivalent_with_different_ids": different_id_matches,
        "same_id_same_identity": same_id_same_identity,
        "same_id_different_identity": pk_collisions,
        "same_identity_different_id": different_id_matches,
        "divergence_types": dict(sorted(divergence_types.items())),
        "relevant_foreign_keys": STRATEGIES[table]["foreign_keys"],
    }


def analyze_identity(desktop_path: str | Path, backend_path: str | Path) -> dict[str, Any]:
    desktop_path, backend_path = Path(desktop_path), Path(backend_path)
    desktop_inventory = inventory_database(desktop_path)
    backend_inventory = inventory_database(backend_path)
    report: dict[str, Any] = {
        "desktop": {"path": desktop_inventory["path"], "exists": desktop_inventory["exists"]},
        "backend": {"path": backend_inventory["path"], "exists": backend_inventory["exists"]},
        "privacy": {
            "record_values_included": False,
            "fingerprints_included": False,
            "fingerprints_ephemeral": True,
        },
        "metric_semantics": {
            "pk_collisions": (
                "o mesmo valor numerico de PK esta ocupado por identidades diferentes"
            ),
            "equivalent_with_different_ids": (
                "a mesma identidade foi encontrada nos dois bancos sob PKs diferentes"
            ),
            "same_id_same_identity": (
                "o mesmo valor numerico de PK corresponde a mesma identidade"
            ),
            "same_id_different_identity": (
                "o mesmo valor numerico de PK corresponde a identidades diferentes"
            ),
            "same_identity_different_id": (
                "a mesma identidade corresponde a valores numericos de PK diferentes"
            ),
            "orthogonality": (
                "correspondencias por identidade e colisoes de PK sao eixos independentes"
            ),
        },
        "strategies": STRATEGIES,
        "tables": {},
    }
    if not desktop_inventory["exists"] or not backend_inventory["exists"]:
        report["status"] = "incomplete_missing_database"
        return report

    fp = EphemeralFingerprinter()
    desktop_tables = _read_tables(desktop_path)
    backend_tables = _read_tables(backend_path)
    desktop_maps = _base_identity_maps(desktop_tables, fp)
    backend_maps = _base_identity_maps(backend_tables, fp)
    for table in TABLE_ORDER:
        if table not in desktop_tables and table not in backend_tables:
            continue
        report["tables"][table] = _reconcile_table(
            table,
            desktop_tables.get(table, []),
            backend_tables.get(table, []),
            _identity_builder(table, desktop_tables, fp, desktop_maps),
            _identity_builder(table, backend_tables, fp, backend_maps),
            fp,
        )
    report["status"] = "completed_read_only"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desktop", type=Path, default=DEFAULT_DESKTOP_DB)
    parser.add_argument("--backend", type=Path, default=DEFAULT_BACKEND_DB)
    args = parser.parse_args()
    print(json.dumps(analyze_identity(args.desktop, args.backend), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
