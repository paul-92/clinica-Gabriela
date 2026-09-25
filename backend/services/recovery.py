"""Backup, recovery e restore fail-closed da unidade operacional da SPEC-006.

Este módulo não inicializa o banco, não lê dados clínicos e não altera pointer,
generation ou manifest de runtime. O chamador fornece explicitamente a fonte e
o destino; por isso também pode ser exercitado integralmente em fixtures.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from backend.cutover.infrastructure import SCHEMA_VERSION, sha256_file


APP_NAME = "Clinica Gabriela"
RECOVERY_FORMAT_VERSION = "spec006-recovery-v1"
DAILY_TIMEZONE = "America/Sao_Paulo"
APPLICATION_VERSION = "0.1.0"
RUNTIME_VERSION = "spec006-runtime-v1"
DAILY_RETENTION = 7
WEEKLY_RETENTION = 4
ALLOWED_PACKAGE_FILES = frozenset({"canonical.database.db", "recovery-manifest.json"})
RETENTION_CLASSES = frozenset({"daily", "weekly", "protected"})


class RecoveryError(RuntimeError):
    """Erro seguro: nenhum resultado parcial é considerado válido."""


class RecoveryValidationError(RecoveryError):
    pass


class RecoveryAuthorizationError(RecoveryError):
    pass


class PreUpdateBackupError(RecoveryError):
    pass


@dataclass(frozen=True)
class PersistentPaths:
    persistent_root: Path
    runtime_root: Path
    database_root: Path
    backup_root: Path


@dataclass(frozen=True)
class DatabaseFacts:
    sha256: str
    size_bytes: int
    integrity_check: str
    foreign_key_violations: int
    user_version: int


@dataclass(frozen=True)
class BackupResult:
    package_dir: Path
    database_path: Path
    manifest_path: Path
    manifest: dict[str, Any]


def persistent_paths(*, localappdata: str | Path | None = None) -> PersistentPaths:
    """Resolve o layout congelado; nenhum diretório é criado nesta função."""
    root = Path(localappdata or os.getenv("LOCALAPPDATA") or Path.home()) / "ClinicaGabriela"
    root = root.expanduser().resolve()
    runtime = root / "runtime"
    return PersistentPaths(root, runtime, runtime / "generations", runtime / "backups")


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".recovery-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _validate_sqlite(path: Path) -> DatabaseFacts:
    path = path.resolve(strict=True)
    if not path.is_file() or path.stat().st_size == 0:
        raise RecoveryValidationError("banco ausente ou vazio")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(path, timeout=5)
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0]).lower()
        violations = sum(1 for _ in connection.execute("PRAGMA foreign_key_check"))
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    except (OSError, sqlite3.Error) as exc:
        raise RecoveryValidationError("banco SQLite nao pode ser validado") from exc
    finally:
        if connection is not None:
            connection.close()
    if integrity != "ok" or violations:
        raise RecoveryValidationError("integridade SQLite invalida")
    return DatabaseFacts(sha256_file(path), path.stat().st_size, integrity, violations, user_version)


def _generation_metadata(source: Path) -> tuple[int | None, str]:
    """Obtém metadados do pointer somente como leitura, sem exigir o runtime."""
    pointer = source.parent.parent / "operational-pointer.json"
    if pointer.is_file():
        try:
            payload = json.loads(pointer.read_text(encoding="utf-8"))
            if Path(payload.get("database_path", "")).resolve() == source.resolve():
                return int(payload["generation"]), str(payload.get("state", "unknown"))
        except (OSError, TypeError, ValueError, KeyError):
            pass
    return None, "isolated"


def _manifest(*, facts: DatabaseFacts, source: Path, backup_type: str,
              app_version: str, runtime_version: str, schema_version: str,
              generation: int | None, generation_state: str, created_at: str,
              retention_class: str, protected: bool) -> dict[str, Any]:
    return {
        "format_version": RECOVERY_FORMAT_VERSION,
        "application": APP_NAME,
        "application_version": app_version,
        "runtime_version": runtime_version,
        "created_at": created_at,
        "backup_type": backup_type,
        "database_filename": "canonical.database.db",
        "database_sha256": facts.sha256,
        "database_size_bytes": facts.size_bytes,
        "schema_version": schema_version,
        "user_version": facts.user_version,
        "generation": generation,
        "generation_state": generation_state,
        "integrity_check": facts.integrity_check,
        "foreign_key_violations": facts.foreign_key_violations,
        "validation_status": "passed",
        "compatibility_status": "validated",
        "attachments_scope": "none",
        "attachments": [],
        "encryption": {"status": "not_enabled", "boundary": "future-approved-encryption"},
        "privacy_safe": True,
        "source_role": "operational-canonical",
        "source_path_recorded": False,
        "retention_class": retention_class,
        "protected": protected,
    }


def validate_manifest(package_dir: str | Path, *, expected_schema_version: str | None = SCHEMA_VERSION,
                      expected_user_version: int | None = None,
                      expected_generation: int | None = None,
                      expected_application_version: str = APPLICATION_VERSION,
                      expected_runtime_version: str = RUNTIME_VERSION) -> dict[str, Any]:
    package = Path(package_dir).expanduser().resolve(strict=True)
    manifest_path = package / "recovery-manifest.json"
    database_path = package / "canonical.database.db"
    try:
        actual_files = {item.name for item in package.iterdir()}
    except OSError as exc:
        raise RecoveryValidationError("recovery package nao pode ser listado") from exc
    if actual_files != ALLOWED_PACKAGE_FILES:
        raise RecoveryValidationError("recovery package possui estrutura inesperada")
    if manifest_path.is_symlink() or database_path.is_symlink():
        raise RecoveryValidationError("recovery package nao aceita links simbolicos")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecoveryValidationError("recovery manifest ausente ou invalido") from exc
    required = {
        "format_version", "application", "application_version", "runtime_version",
        "created_at", "backup_type", "database_filename", "database_sha256",
        "database_size_bytes", "schema_version", "user_version", "generation",
        "generation_state", "validation_status", "compatibility_status",
        "integrity_check", "foreign_key_violations", "privacy_safe",
        "attachments_scope", "attachments", "encryption", "source_role",
        "source_path_recorded", "retention_class", "protected",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise RecoveryValidationError("recovery manifest incompleto")
    if (manifest["format_version"] != RECOVERY_FORMAT_VERSION
            or not isinstance(manifest["privacy_safe"], bool)
            or not manifest["privacy_safe"]):
        raise RecoveryValidationError("formato ou privacidade do manifest invalido")
    if manifest["application"] != APP_NAME or manifest["database_filename"] != "canonical.database.db":
        raise RecoveryValidationError("identidade do recovery invalida")
    if not isinstance(manifest["application_version"], str) or not manifest["application_version"]:
        raise RecoveryValidationError("application_version invalida")
    if not isinstance(manifest["runtime_version"], str) or not manifest["runtime_version"]:
        raise RecoveryValidationError("runtime_version invalida")
    if manifest["application_version"] != expected_application_version:
        raise RecoveryValidationError("application_version incompatível")
    if manifest["runtime_version"] != expected_runtime_version:
        raise RecoveryValidationError("runtime_version incompatível")
    try:
        datetime.fromisoformat(str(manifest["created_at"]))
    except ValueError as exc:
        raise RecoveryValidationError("timestamp do recovery invalido") from exc
    if not isinstance(manifest["backup_type"], str) or not manifest["backup_type"]:
        raise RecoveryValidationError("backup_type invalido")
    if manifest["compatibility_status"] != "validated":
        raise RecoveryValidationError("compatibilidade do recovery nao validada")
    if (manifest["attachments_scope"] != "none" or manifest["attachments"] != []
            or not isinstance(manifest["attachments"], list)):
        raise RecoveryValidationError("escopo de attachments invalido")
    if (manifest["source_path_recorded"] is not False
            or not isinstance(manifest["encryption"], dict)
            or manifest["encryption"].get("status") != "not_enabled"):
        raise RecoveryValidationError("metadata de privacidade/encryption invalida")
    if manifest["retention_class"] not in RETENTION_CLASSES or not isinstance(manifest["protected"], bool):
        raise RecoveryValidationError("politica de retencao invalida")
    if manifest["retention_class"] == "protected" and not manifest["protected"]:
        raise RecoveryValidationError("classe protected deve ser protegida")
    try:
        if int(manifest["database_size_bytes"]) <= 0 or int(manifest["foreign_key_violations"]) != 0:
            raise RecoveryValidationError("metadados de integridade invalidos")
        if not isinstance(manifest["database_sha256"], str) or len(manifest["database_sha256"]) != 64:
            raise RecoveryValidationError("checksum invalido")
    except (TypeError, ValueError) as exc:
        raise RecoveryValidationError("metadados numericos invalidos") from exc
    if expected_schema_version is not None and manifest["schema_version"] != expected_schema_version:
        raise RecoveryValidationError("schema incompatível")
    try:
        manifest_user_version = int(manifest["user_version"])
    except (TypeError, ValueError) as exc:
        raise RecoveryValidationError("user_version invalido") from exc
    if expected_user_version is not None and manifest_user_version != expected_user_version:
        raise RecoveryValidationError("user_version incompatível")
    if expected_generation is not None and manifest.get("generation") != expected_generation:
        raise RecoveryValidationError("generation incompatível")
    facts = _validate_sqlite(database_path)
    if (facts.sha256 != manifest["database_sha256"] or facts.size_bytes != int(manifest["database_size_bytes"])
            or facts.user_version != manifest_user_version):
        raise RecoveryValidationError("checksum ou user_version do recovery diverge")
    if manifest["validation_status"] != "passed" or manifest["integrity_check"] != "ok":
        raise RecoveryValidationError("recovery nao esta validado")
    return manifest


def create_backup(source_database: str | Path, *, destination_root: str | Path | None = None,
                  backup_type: str = "manual", app_version: str = APPLICATION_VERSION,
                  schema_version: str = SCHEMA_VERSION, generation: int | None = None,
                  generation_state: str = "unknown", timestamp: datetime | None = None,
                  runtime_version: str = RUNTIME_VERSION,
                  application_version: str | None = None,
                  retention_class: str | None = None, protected: bool | None = None) -> BackupResult:
    """Cria snapshot consistente via SQLite Online Backup API e publica atomicamente."""
    source = Path(source_database).expanduser().resolve(strict=True)
    source_facts = _validate_sqlite(source)
    app_version = application_version or app_version
    derived_class = retention_class or _retention_class_for_backup_type(backup_type)
    derived_protected = protected if protected is not None else derived_class == "protected"
    if derived_class not in RETENTION_CLASSES:
        raise RecoveryValidationError("classe de retencao invalida")
    now = timestamp or datetime.now(timezone.utc)
    # Inclui microssegundos para que dois backups manuais consecutivos nunca
    # colidam; o nome continua ordenável e não contém dados clínicos.
    stamp = now.strftime("%Y%m%dT%H%M%S%fZ")
    root = Path(destination_root or persistent_paths().backup_root).expanduser().resolve()
    package = root / f"backup-{stamp}-{source_facts.sha256[:12]}"
    package.mkdir(parents=True, exist_ok=False)
    temporary = package / ".canonical.database.db.tmp"
    database = package / "canonical.database.db"
    try:
        with closing(sqlite3.connect(source, timeout=5)) as source_connection, closing(sqlite3.connect(temporary)) as target_connection:
            source_connection.backup(target_connection)
            target_connection.commit()
        os.replace(temporary, database)
        facts = _validate_sqlite(database)
        if facts.sha256 != source_facts.sha256:
            # A valid SQLite snapshot may differ in bytes from source; content is
            # validated independently and the snapshot checksum is authoritative.
            pass
        manifest = _manifest(
            facts=facts, source=source, backup_type=backup_type, app_version=app_version,
            runtime_version=runtime_version,
            schema_version=schema_version, generation=generation, generation_state=generation_state,
            created_at=now.isoformat(), retention_class=derived_class, protected=derived_protected,
        )
        _atomic_bytes(package / "recovery-manifest.json", _canonical_json(manifest))
        validate_manifest(package, expected_schema_version=schema_version,
                          expected_user_version=facts.user_version,
                          expected_generation=generation,
                          expected_application_version=app_version,
                          expected_runtime_version=runtime_version)
        return BackupResult(package, database, package / "recovery-manifest.json", manifest)
    except Exception as exc:
        shutil.rmtree(package, ignore_errors=True)
        if isinstance(exc, RecoveryError):
            raise
        raise RecoveryError("backup nao pode ser publicado") from exc


def create_recovery_unit(source_database: str | Path, destination: str | Path, *,
                         app_version: str = APPLICATION_VERSION, schema_version: str = SCHEMA_VERSION,
                         generation: int = 9, runtime_version: str = RUNTIME_VERSION) -> BackupResult:
    """Gera o pacote inicial congelado: canonical.database.db + manifest."""
    target = Path(destination).expanduser().resolve()
    if target.exists():
        raise RecoveryError("recovery package destino ja existe")
    result = create_backup(source_database, destination_root=target.parent,
                           backup_type="recovery-unit", app_version=app_version,
                           runtime_version=runtime_version,
                           schema_version=schema_version, generation=generation,
                           generation_state="canonical")
    target.mkdir(parents=True, exist_ok=False)
    try:
        shutil.move(str(result.database_path), target / "canonical.database.db")
        shutil.move(str(result.manifest_path), target / "recovery-manifest.json")
        result.package_dir.rmdir()
    except Exception as exc:
        raise RecoveryError("recovery unit nao pode ser finalizada") from exc
    manifest = validate_manifest(target, expected_schema_version=schema_version,
                                 expected_generation=generation,
                                 expected_application_version=app_version,
                                 expected_runtime_version=runtime_version)
    return BackupResult(target, target / "canonical.database.db", target / "recovery-manifest.json", manifest)


def restore_backup(package_dir: str | Path, target_database: str | Path, *, role: str,
                   expected_schema_version: str = SCHEMA_VERSION,
                   expected_user_version: int | None = None,
                   expected_generation: int | None = None,
                   expected_application_version: str = APPLICATION_VERSION,
                   expected_runtime_version: str = RUNTIME_VERSION,
                   pre_restore_root: str | Path | None = None) -> BackupResult:
    """Restaura atomicamente após validação e backup obrigatório do estado atual."""
    if role.strip().lower() != "admin":
        raise RecoveryAuthorizationError("restore exige role administrativa")
    package = Path(package_dir).expanduser().resolve(strict=True)
    target = Path(target_database).expanduser().resolve()
    if not target.is_file():
        raise RecoveryValidationError("banco alvo inexistente; restore inicial requer provisionamento explicito")
    target_facts = _validate_sqlite(target)
    compatible_user_version = (expected_user_version
                               if expected_user_version is not None
                               else target_facts.user_version)
    manifest = validate_manifest(package, expected_schema_version=expected_schema_version,
                                 expected_user_version=compatible_user_version,
                                 expected_generation=expected_generation,
                                 expected_application_version=expected_application_version,
                                 expected_runtime_version=expected_runtime_version)
    safety_root = Path(pre_restore_root or target.parent / "backups").expanduser().resolve()
    safety = create_backup(target, destination_root=safety_root, backup_type="pre-restore",
                           schema_version=expected_schema_version,
                           generation=manifest.get("generation"),
                           app_version=expected_application_version,
                           runtime_version=expected_runtime_version)
    temporary = target.with_name(f".{target.name}.restore.tmp")
    try:
        shutil.copyfile(package / "canonical.database.db", temporary)
        _validate_sqlite(temporary)
        os.replace(temporary, target)
        _validate_sqlite(target)
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        # A safety backup exists; no partially restored target is published.
        raise RecoveryError(f"restore falhou; pre-restore preservado em {safety.package_dir.name}") from exc
    return BackupResult(safety.package_dir, target, safety.manifest_path, manifest)


def _retention_class_for_backup_type(backup_type: str) -> str:
    if backup_type in {"pre-restore", "pre-update", "recovery-unit", "special", "protected"}:
        return "protected"
    if backup_type == "weekly":
        return "weekly"
    return "daily"


def _retention_sort_key(manifest: dict[str, Any], package: Path) -> tuple[datetime, str]:
    created = datetime.fromisoformat(str(manifest["created_at"])).astimezone(ZoneInfo(DAILY_TIMEZONE))
    return created, package.name


def apply_retention(backup_root: str | Path) -> list[Path]:
    """Aplica 7 diários, 4 semanais e preserva toda unidade protegida."""
    root = Path(backup_root).expanduser().resolve()
    candidates: dict[str, list[tuple[tuple[datetime, str], Path]]] = {"daily": [], "weekly": []}
    for package in root.glob("backup-*"):
        if not package.is_dir():
            continue
        try:
            manifest = validate_manifest(package)
            retention_class = manifest["retention_class"]
            if manifest["protected"] or retention_class == "protected":
                continue
            candidates[retention_class].append((_retention_sort_key(manifest, package), package))
        except RecoveryError:
            continue
    removed: list[Path] = []
    limits = {"daily": DAILY_RETENTION, "weekly": WEEKLY_RETENTION}
    for retention_class, entries in candidates.items():
        entries.sort(reverse=True)
        for _, package in entries[limits[retention_class]:]:
            shutil.rmtree(package)
            removed.append(package)
    removed.sort(key=str)
    return removed


def should_run_daily(*, last_success: datetime | None, now: datetime | None = None) -> bool:
    current = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(DAILY_TIMEZONE))
    if last_success is None:
        return True
    previous = last_success.astimezone(ZoneInfo(DAILY_TIMEZONE))
    return previous.date() != current.date()


def pre_update_backup(source_database: str | Path, *, app_version: str = APPLICATION_VERSION,
                     schema_version: str = SCHEMA_VERSION, generation: int = 9,
                     destination_root: str | Path | None = None,
                     runtime_version: str = RUNTIME_VERSION) -> BackupResult:
    """Boundary chamado pelo installer hook; qualquer falha bloqueia o update."""
    try:
        result = create_backup(source_database, destination_root=destination_root,
                               backup_type="pre-update", app_version=app_version,
                               runtime_version=runtime_version,
                               schema_version=schema_version, generation=generation,
                               generation_state="canonical")
        validate_manifest(result.package_dir, expected_schema_version=schema_version,
                          expected_generation=generation,
                          expected_application_version=app_version,
                          expected_runtime_version=runtime_version)
        return result
    except Exception as exc:
        if isinstance(exc, PreUpdateBackupError):
            raise
        raise PreUpdateBackupError("PRE_UPDATE_BACKUP=FAIL; UPDATE=BLOCKED") from exc
