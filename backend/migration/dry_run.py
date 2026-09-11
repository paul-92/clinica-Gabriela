"""Dry-run agregado e privacy-safe executado somente sobre snapshots validados."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.migration.manifests import SourceDatabase
from backend.migration.snapshot import ValidatedSnapshot, validate_sqlite_snapshot
from scripts.sqlite_identity_analysis import analyze_identity
from scripts.sqlite_integrity_audit import audit_database
from scripts.sqlite_inventory import (
    DEFAULT_BACKEND_DB,
    DEFAULT_DESKTOP_DB,
    inventory_database,
)


class DryRunError(Exception):
    pass


class DryRunInvalidSnapshotError(DryRunError):
    pass


class DryRunOperationalPathError(DryRunError):
    pass


class DryRunGate(str, Enum):
    PASS = "PASS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


class SnapshotSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_label: SourceDatabase
    snapshot_reference: str
    checksum_sha256: str
    table_count: int = Field(ge=0)
    row_counts: dict[str, int]


class IdentitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    equivalent: int = Field(ge=0)
    desktop_only: int = Field(ge=0)
    backend_only: int = Field(ge=0)
    conflicts: int = Field(ge=0)
    ambiguities: int = Field(ge=0)


class ForeignKeySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    relationships: int = Field(ge=0)
    null_references: int = Field(ge=0)
    valid_references: int = Field(ge=0)
    orphan_references: int = Field(ge=0)
    check_violations: int = Field(ge=0)


class DryRunReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    execution_reference: str
    snapshots: tuple[SnapshotSummary, SnapshotSummary]
    identity: IdentitySummary
    foreign_keys: ForeignKeySummary
    review_count: int = Field(ge=0)
    block_count: int = Field(ge=0)
    projected_canonical_counts: dict[str, int]
    gate: DryRunGate
    reasons: tuple[str, ...]

    @field_validator("execution_reference")
    @classmethod
    def validate_execution_reference(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", value):
            raise ValueError("execution_reference deve ser uma referencia tecnica segura")
        return value


def _reject_operational_path(path: Path) -> None:
    operational = {
        DEFAULT_DESKTOP_DB.resolve(strict=False),
        DEFAULT_BACKEND_DB.resolve(strict=False),
    }
    if path.resolve(strict=False) in operational:
        raise DryRunOperationalPathError("dry-run nao aceita caminho operacional direto")


def run_snapshot_dry_run(
    desktop: ValidatedSnapshot,
    backend: ValidatedSnapshot,
    *,
    execution_reference: str,
) -> DryRunReport:
    """Revalida dois snapshots e reduz diagnosticos existentes a agregados."""
    if not isinstance(desktop, ValidatedSnapshot) or not isinstance(backend, ValidatedSnapshot):
        raise DryRunInvalidSnapshotError("dry-run exige snapshots validados")
    if desktop.manifest.source_label is not SourceDatabase.DESKTOP_LEGACY:
        raise DryRunInvalidSnapshotError("snapshot desktop possui papel inesperado")
    if backend.manifest.source_label is not SourceDatabase.BACKEND_LEGACY:
        raise DryRunInvalidSnapshotError("snapshot backend possui papel inesperado")
    for artifact in (desktop, backend):
        _reject_operational_path(artifact.path)
        try:
            validate_sqlite_snapshot(artifact.path, artifact.manifest)
        except Exception as exc:
            raise DryRunInvalidSnapshotError("snapshot nao passou na revalidacao") from exc

    inventories = {
        SourceDatabase.DESKTOP_LEGACY: inventory_database(desktop.path),
        SourceDatabase.BACKEND_LEGACY: inventory_database(backend.path),
    }
    identity_report = analyze_identity(desktop.path, backend.path)
    integrity_reports = [audit_database(desktop.path), audit_database(backend.path)]

    identity_tables = identity_report.get("tables", {})
    identity = IdentitySummary(
        equivalent=sum(item["probable_same_entity"] for item in identity_tables.values()),
        desktop_only=sum(item["desktop_only"] for item in identity_tables.values()),
        backend_only=sum(item["backend_only"] for item in identity_tables.values()),
        conflicts=sum(item["conflicts"] for item in identity_tables.values()),
        ambiguities=sum(item["inconclusive"] for item in identity_tables.values()),
    )
    foreign_keys = ForeignKeySummary(
        relationships=sum(item["summary"]["relationship_count"] for item in integrity_reports),
        null_references=sum(item["summary"]["total_null_references"] for item in integrity_reports),
        valid_references=sum(item["summary"]["total_valid_references"] for item in integrity_reports),
        orphan_references=sum(item["summary"]["total_orphan_references"] for item in integrity_reports),
        check_violations=sum(item["summary"]["foreign_key_check_violations"] for item in integrity_reports),
    )

    review_count = identity.ambiguities
    if any("clinic_settings" in inventory["tables"] for inventory in inventories.values()):
        review_count += 1
    block_count = identity.conflicts + foreign_keys.orphan_references + foreign_keys.check_violations
    reasons: list[str] = []
    if identity.conflicts:
        reasons.append("identity_conflict")
    if foreign_keys.orphan_references or foreign_keys.check_violations:
        reasons.append("referential_integrity_failure")
    if identity.ambiguities:
        reasons.append("identity_review_pending")
    if any("clinic_settings" in inventory["tables"] for inventory in inventories.values()):
        reasons.append("clinic_settings_review_pending")
    gate = (
        DryRunGate.BLOCKED
        if block_count
        else DryRunGate.REVIEW_REQUIRED
        if review_count
        else DryRunGate.PASS
    )

    projected = {}
    all_tables = set(inventories[SourceDatabase.DESKTOP_LEGACY]["tables"]) | set(
        inventories[SourceDatabase.BACKEND_LEGACY]["tables"]
    )
    for table in sorted(all_tables):
        table_identity = identity_tables.get(table)
        if table_identity and not table_identity["conflicts"] and not table_identity["inconclusive"]:
            left = inventories[SourceDatabase.DESKTOP_LEGACY]["tables"].get(table, {}).get("row_count", 0)
            right = inventories[SourceDatabase.BACKEND_LEGACY]["tables"].get(table, {}).get("row_count", 0)
            projected[table] = left + right - table_identity["probable_same_entity"]

    summaries = tuple(
        SnapshotSummary(
            source_label=artifact.manifest.source_label,
            snapshot_reference=artifact.manifest.snapshot_reference,
            checksum_sha256=artifact.manifest.checksum_sha256,
            table_count=len(inventory["tables"]),
            row_counts={name: table["row_count"] for name, table in inventory["tables"].items()},
        )
        for artifact, inventory in (
            (desktop, inventories[SourceDatabase.DESKTOP_LEGACY]),
            (backend, inventories[SourceDatabase.BACKEND_LEGACY]),
        )
    )
    return DryRunReport(
        execution_reference=execution_reference,
        snapshots=summaries,
        identity=identity,
        foreign_keys=foreign_keys,
        review_count=review_count,
        block_count=block_count,
        projected_canonical_counts=projected,
        gate=gate,
        reasons=tuple(reasons),
    )
