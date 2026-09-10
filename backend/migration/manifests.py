"""Modelos e serializacao dos manifests da migracao canonica.

Este modulo e deliberadamente independente do runtime, SQLAlchemy e SQLite. Ele
modela artefatos; nao abre bancos nem executa migracoes.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


FORMAT_VERSION = "1.0"
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_PROVENANCE_TERMS = {
    "address", "clinical", "cpf", "credential", "email", "name", "notes",
    "password", "phone", "secret", "token", "username",
}


class SourceDatabase(str, Enum):
    DESKTOP_LEGACY = "desktop_legacy"
    BACKEND_LEGACY = "backend_legacy"


class MatchStatus(str, Enum):
    EQUIVALENT = "equivalent"
    EXCLUSIVE = "exclusive"
    CONFLICTING_IDENTITY = "conflicting_identity"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class MatchConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class PkRelationStatus(str, Enum):
    NOT_COMPARED = "not_compared"
    SAME_PK_SAME_IDENTITY = "same_pk_same_identity"
    SAME_PK_DIFFERENT_IDENTITY = "same_pk_different_identity"
    DIFFERENT_PK_SAME_IDENTITY = "different_pk_same_identity"
    DIFFERENT_PK_DIFFERENT_IDENTITY = "different_pk_different_identity"
    NO_COUNTERPART = "no_counterpart"


class DecisionClass(str, Enum):
    AUTO = "AUTO"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class DecisionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RemapLifecycle(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    RESERVED = "reserved"
    CONSUMED = "consumed"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"


class IntegrityStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class ExecutionStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    ABORTED = "aborted"
    FAILED = "failed"
    COMPLETED = "completed"


class ManifestValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


def _validate_token(value: str, field_name: str) -> str:
    if not _SAFE_TOKEN.fullmatch(value):
        raise ValueError(f"{field_name} deve ser uma referencia tecnica segura")
    return value


def _validate_sha256(value: str, field_name: str) -> str:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{field_name} deve ser SHA-256 hexadecimal em minusculas")
    return value


class StrictManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)


class Provenance(StrictManifestModel):
    source_database: SourceDatabase
    source_table: str
    historical_reference: str
    snapshot_version: str
    rule_version: str
    match_status: MatchStatus
    match_confidence: MatchConfidence
    decision_class: DecisionClass
    decision_status: DecisionStatus
    canonical_group_ref: str | None = None
    execution_reference: str
    decision_reason_code: str

    @field_validator(
        "source_table", "historical_reference", "snapshot_version", "rule_version",
        "execution_reference", "decision_reason_code",
    )
    @classmethod
    def validate_safe_fields(cls, value: str, info) -> str:
        value = _validate_token(value, info.field_name)
        if info.field_name == "decision_reason_code":
            segments = set(re.split(r"[._:/-]", value.casefold()))
            if segments & _FORBIDDEN_PROVENANCE_TERMS:
                raise ValueError("decision_reason_code nao pode descrever dado sensivel")
        return value

    @field_validator("canonical_group_ref")
    @classmethod
    def validate_optional_group(cls, value: str | None) -> str | None:
        return None if value is None else _validate_token(value, "canonical_group_ref")

    @model_validator(mode="after")
    def validate_identity_state(self) -> "Provenance":
        if self.match_status is MatchStatus.EQUIVALENT and not self.canonical_group_ref:
            raise ValueError("equivalent exige canonical_group_ref")
        if self.match_confidence is MatchConfidence.NONE and self.match_status is MatchStatus.EQUIVALENT:
            raise ValueError("equivalent nao pode ter confidence none")
        return self


SourceId = int | str
CanonicalId = int | str


class RemapEntry(StrictManifestModel):
    source_database: SourceDatabase
    source_table: str
    source_id: SourceId
    canonical_table: str
    canonical_id: CanonicalId | None = None
    match_status: MatchStatus
    match_confidence: MatchConfidence
    pk_relation_status: PkRelationStatus
    decision_class: DecisionClass
    decision_status: DecisionStatus
    canonical_group_ref: str | None = None
    provenance: Provenance

    @field_validator("source_table", "canonical_table")
    @classmethod
    def validate_tables(cls, value: str, info) -> str:
        return _validate_token(value, info.field_name)

    @field_validator("source_id", "canonical_id")
    @classmethod
    def validate_ids(cls, value: SourceId | None, info) -> SourceId | None:
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError(f"{info.field_name} nao aceita boolean")
        if isinstance(value, int):
            if value <= 0:
                raise ValueError(f"{info.field_name} deve ser positivo")
            return value
        return _validate_token(value, info.field_name)

    @field_validator("canonical_group_ref")
    @classmethod
    def validate_group(cls, value: str | None) -> str | None:
        return None if value is None else _validate_token(value, "canonical_group_ref")

    @property
    def logical_key(self) -> tuple[SourceDatabase, str, SourceId]:
        return self.source_database, self.source_table, self.source_id

    @model_validator(mode="after")
    def validate_consistency(self) -> "RemapEntry":
        provenance = self.provenance
        aligned = (
            provenance.source_database == self.source_database
            and provenance.source_table == self.source_table
            and provenance.historical_reference == str(self.source_id)
            and provenance.match_status == self.match_status
            and provenance.match_confidence == self.match_confidence
            and provenance.decision_class == self.decision_class
            and provenance.decision_status == self.decision_status
            and provenance.canonical_group_ref == self.canonical_group_ref
        )
        if not aligned:
            raise ValueError("provenance deve corresponder integralmente ao remap entry")
        if self.decision_class is DecisionClass.BLOCK and self.canonical_id is not None:
            raise ValueError("BLOCK nao pode possuir canonical_id")
        if self.decision_status is DecisionStatus.REJECTED and self.canonical_id is not None:
            raise ValueError("decisao rejeitada nao pode possuir canonical_id")
        uncertain = {
            MatchStatus.AMBIGUOUS,
            MatchStatus.CONFLICTING_IDENTITY,
            MatchStatus.UNRESOLVED,
        }
        if self.match_status in uncertain and self.canonical_id is not None:
            raise ValueError("matching nao resolvido nao pode possuir canonical_id")
        if self.decision_class is DecisionClass.AUTO and self.match_status in uncertain:
            raise ValueError("AUTO exige matching resolvido")
        if self.match_status is MatchStatus.EQUIVALENT and not self.canonical_group_ref:
            raise ValueError("equivalent exige canonical_group_ref")
        if self.match_status is MatchStatus.EXCLUSIVE and self.pk_relation_status is not PkRelationStatus.NO_COUNTERPART:
            raise ValueError("exclusive exige pk_relation_status no_counterpart")
        if self.match_status is MatchStatus.EQUIVALENT and self.pk_relation_status in {
            PkRelationStatus.SAME_PK_DIFFERENT_IDENTITY,
            PkRelationStatus.DIFFERENT_PK_DIFFERENT_IDENTITY,
            PkRelationStatus.NO_COUNTERPART,
        }:
            raise ValueError("estado de PK incompativel com identidade equivalent")
        return self


_ALLOWED_TRANSITIONS = {
    RemapLifecycle.DRAFT: {RemapLifecycle.REVIEWED, RemapLifecycle.SUPERSEDED},
    RemapLifecycle.REVIEWED: {RemapLifecycle.APPROVED, RemapLifecycle.SUPERSEDED},
    RemapLifecycle.APPROVED: {RemapLifecycle.RESERVED, RemapLifecycle.SUPERSEDED},
    RemapLifecycle.RESERVED: {RemapLifecycle.CONSUMED, RemapLifecycle.SUPERSEDED},
    RemapLifecycle.CONSUMED: {RemapLifecycle.VERIFIED, RemapLifecycle.SUPERSEDED},
    RemapLifecycle.VERIFIED: {RemapLifecycle.SUPERSEDED},
    RemapLifecycle.SUPERSEDED: set(),
}


class RemapManifest(StrictManifestModel):
    format_version: Literal["1.0"] = FORMAT_VERSION
    manifest_version: str
    lifecycle: RemapLifecycle = RemapLifecycle.DRAFT
    entries: tuple[RemapEntry, ...]

    @field_validator("manifest_version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        return _validate_token(value, "manifest_version")

    @model_validator(mode="after")
    def validate_manifest(self) -> "RemapManifest":
        keys = [entry.logical_key for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("chave logica duplicada no remap manifest")

        canonical_groups: dict[tuple[str, CanonicalId], list[RemapEntry]] = {}
        for entry in self.entries:
            if entry.canonical_id is not None:
                canonical_groups.setdefault(
                    (entry.canonical_table, entry.canonical_id), []
                ).append(entry)
        for entries in canonical_groups.values():
            if len(entries) > 1 and (
                any(entry.match_status is not MatchStatus.EQUIVALENT for entry in entries)
                or len({entry.canonical_group_ref for entry in entries}) != 1
            ):
                raise ValueError("canonical_id compartilhado exige um unico grupo equivalent")

        gated = {
            RemapLifecycle.APPROVED,
            RemapLifecycle.RESERVED,
            RemapLifecycle.CONSUMED,
            RemapLifecycle.VERIFIED,
        }
        if self.lifecycle in gated:
            if any(entry.decision_class is DecisionClass.BLOCK for entry in self.entries):
                raise ValueError("manifest com BLOCK nao pode avancar para approved")
            if any(entry.decision_status is not DecisionStatus.APPROVED for entry in self.entries):
                raise ValueError("todas as decisoes devem estar approved")
            if any(entry.match_status in {
                MatchStatus.AMBIGUOUS,
                MatchStatus.CONFLICTING_IDENTITY,
                MatchStatus.UNRESOLVED,
            } for entry in self.entries):
                raise ValueError("manifest aprovado nao aceita matching pendente")

        before_reservation = {
            RemapLifecycle.DRAFT,
            RemapLifecycle.REVIEWED,
            RemapLifecycle.APPROVED,
        }
        if self.lifecycle in before_reservation and any(
            entry.canonical_id is not None for entry in self.entries
        ):
            raise ValueError("canonical_id somente pode existir a partir de reserved")
        if self.lifecycle in {
            RemapLifecycle.RESERVED,
            RemapLifecycle.CONSUMED,
            RemapLifecycle.VERIFIED,
        } and any(entry.canonical_id is None for entry in self.entries):
            raise ValueError(f"{self.lifecycle.value} exige canonical_id em todas as entradas")
        return self

    def transition_to(
        self,
        lifecycle: RemapLifecycle,
        *,
        entries: tuple[RemapEntry, ...] | None = None,
    ) -> "RemapManifest":
        if lifecycle not in _ALLOWED_TRANSITIONS[self.lifecycle]:
            raise ValueError(
                f"transicao proibida: {self.lifecycle.value} -> {lifecycle.value}"
            )
        return self.model_copy(
            update={"lifecycle": lifecycle, "entries": entries or self.entries},
            deep=True,
        ).model_validate(
            {
                **self.model_dump(mode="python"),
                "lifecycle": lifecycle,
                "entries": entries or self.entries,
            }
        )


class SnapshotManifest(StrictManifestModel):
    format_version: Literal["1.0"] = FORMAT_VERSION
    source_label: SourceDatabase
    snapshot_reference: str
    checksum_sha256: str
    size_bytes: int = Field(ge=0)
    captured_at: datetime
    schema_version: str
    schema_checksum_sha256: str
    integrity_status: IntegrityStatus
    foreign_key_check_violations: int = Field(ge=0)

    @field_validator("snapshot_reference", "schema_version")
    @classmethod
    def validate_references(cls, value: str, info) -> str:
        return _validate_token(value, info.field_name)

    @field_validator("checksum_sha256", "schema_checksum_sha256")
    @classmethod
    def validate_checksums(cls, value: str, info) -> str:
        return _validate_sha256(value, info.field_name)

    @field_validator("captured_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("captured_at deve possuir timezone")
        return value

    @model_validator(mode="after")
    def validate_integrity(self) -> "SnapshotManifest":
        if self.integrity_status is IntegrityStatus.PASSED and self.foreign_key_check_violations:
            raise ValueError("snapshot passed nao pode possuir violacoes de FK")
        return self


class ExecutionManifest(StrictManifestModel):
    format_version: Literal["1.0"] = FORMAT_VERSION
    execution_id: str
    created_at: datetime
    tool_version: str
    plan_version: str
    rule_version: str
    status: ExecutionStatus
    source_snapshot_references: tuple[str, ...]
    remap_version: str | None = None
    remap_checksum_sha256: str | None = None
    canonical_target_reference: str | None = None
    validation_status: ManifestValidationStatus = ManifestValidationStatus.PENDING

    @field_validator("execution_id", "tool_version", "plan_version", "rule_version")
    @classmethod
    def validate_required_tokens(cls, value: str, info) -> str:
        return _validate_token(value, info.field_name)

    @field_validator("source_snapshot_references")
    @classmethod
    def validate_snapshots(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != 2 or len(set(value)) != 2:
            raise ValueError("execution manifest exige duas referencias de snapshot distintas")
        return tuple(_validate_token(item, "source_snapshot_references") for item in value)

    @field_validator("remap_version", "canonical_target_reference")
    @classmethod
    def validate_optional_tokens(cls, value: str | None, info) -> str | None:
        return None if value is None else _validate_token(value, info.field_name)

    @field_validator("remap_checksum_sha256")
    @classmethod
    def validate_optional_checksum(cls, value: str | None) -> str | None:
        return None if value is None else _validate_sha256(value, "remap_checksum_sha256")

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at deve possuir timezone")
        return value

    @model_validator(mode="after")
    def validate_execution(self) -> "ExecutionManifest":
        if (self.remap_version is None) != (self.remap_checksum_sha256 is None):
            raise ValueError("remap version e checksum devem ser informados juntos")
        if self.status is ExecutionStatus.COMPLETED and (
            self.validation_status is not ManifestValidationStatus.PASSED
            or self.remap_version is None
            or self.canonical_target_reference is None
        ):
            raise ValueError("execucao completed exige remap, destino e validacao passed")
        return self


ManifestModel = RemapManifest | SnapshotManifest | ExecutionManifest
ManifestType = TypeVar("ManifestType", bound=StrictManifestModel)


def canonical_json(manifest: ManifestModel) -> str:
    """Serializa um modelo conhecido em JSON UTF-8 deterministico."""
    if not isinstance(manifest, (RemapManifest, SnapshotManifest, ExecutionManifest)):
        raise TypeError("somente manifests tipados podem ser serializados")
    return json.dumps(
        manifest.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"


def manifest_checksum(manifest: ManifestModel) -> str:
    return hashlib.sha256(canonical_json(manifest).encode("utf-8")).hexdigest()


def write_manifest(path: str | Path, manifest: ManifestModel) -> None:
    Path(path).write_text(canonical_json(manifest), encoding="utf-8", newline="\n")


def load_manifest(path: str | Path, model: type[ManifestType]) -> ManifestType:
    if model not in {RemapManifest, SnapshotManifest, ExecutionManifest}:
        raise TypeError("tipo de manifest nao permitido")
    payload: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest deve conter um objeto JSON")
    return model.model_validate(payload)
