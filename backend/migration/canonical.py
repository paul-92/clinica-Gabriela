"""Fundacao isolada para um banco canonico temporario, ainda sem carga."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine

from backend.config import BACKEND_ROOT
from backend.database.session import Base
from backend.migration.snapshot import ValidatedSnapshot

# Registra no Base somente o schema vigente da autoridade arquitetural backend.
from backend.models import (  # noqa: F401, E402
    appointment,
    clinical_record,
    finance,
    patient,
    psychologist,
    settings,
    user,
)


PROJECT_ROOT = BACKEND_ROOT.parent
OPERATIONAL_DATABASES = frozenset(
    {
        (PROJECT_ROOT / "data" / "clinica_psicologia.db").resolve(strict=False),
        (BACKEND_ROOT / "data" / "clinica_api.db").resolve(strict=False),
    }
)
OPERATIONAL_DIRECTORIES = frozenset(path.parent for path in OPERATIONAL_DATABASES)
EXPECTED_TABLES = frozenset(
    {
        "users",
        "patients",
        "psychologists",
        "appointments",
        "clinical_records",
        "payments",
        "expenses",
        "clinic_settings",
    }
)
CANONICAL_SCHEMA_VERSION = "backend-models-v1"


class CanonicalDatabaseError(Exception):
    pass


class CanonicalUnsafePathError(CanonicalDatabaseError):
    pass


class CanonicalDestinationExistsError(CanonicalDatabaseError):
    pass


class CanonicalDatabaseNotFoundError(CanonicalDatabaseError):
    pass


class CanonicalCreationError(CanonicalDatabaseError):
    pass


class CanonicalValidationError(CanonicalDatabaseError):
    pass


class CanonicalDatabaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: Path
    schema_version: str
    schema_checksum_sha256: str
    tables: tuple[str, ...]
    row_count: int = Field(ge=0)
    foreign_keys_enabled: bool
    foreign_key_violations: int = Field(ge=0)
    integrity_check_passed: bool


def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def _temporary_engine(path: Path) -> Engine:
    engine = create_engine(f"sqlite:///{path}", future=True)
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def _validated_non_operational_path(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve(strict=False)
    if resolved in OPERATIONAL_DATABASES or any(
        resolved == directory or directory in resolved.parents
        for directory in OPERATIONAL_DIRECTORIES
    ):
        raise CanonicalUnsafePathError("caminho operacional nao permitido")
    return resolved


def open_canonical_connection(path: str | Path) -> sqlite3.Connection:
    """Abre banco existente em mode=rw, sem criacao implicita, com FKs ativas."""
    resolved = _validated_non_operational_path(path)
    uri_path = quote(resolved.as_posix(), safe="/:")
    try:
        connection = sqlite3.connect(f"file:{uri_path}?mode=rw", uri=True)
    except sqlite3.OperationalError as exc:
        if not resolved.is_file():
            raise CanonicalDatabaseNotFoundError(
                "banco canonico existente e obrigatorio"
            ) from exc
        raise CanonicalValidationError("banco canonico nao pode ser aberto") from exc
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise CanonicalValidationError("foreign_keys nao pode ser habilitado")
    except Exception:
        connection.close()
        raise
    return connection


def _schema_signature(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_schema "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    encoded = repr(rows).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _expected_unique_columns(table) -> set[tuple[str, ...]]:
    unique = {(column.name,) for column in table.columns if column.unique}
    unique.update(
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    )
    return unique


def _validate_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    if actual_tables != EXPECTED_TABLES:
        raise CanonicalValidationError("conjunto de tabelas canonicas inesperado")
    for name in sorted(EXPECTED_TABLES):
        expected = Base.metadata.tables[name]
        actual_columns = {column["name"]: column for column in inspector.get_columns(name)}
        if set(actual_columns) != {column.name for column in expected.columns}:
            raise CanonicalValidationError("colunas canonicas inesperadas")
        if any(
            str(actual_columns[column.name]["type"]).upper() != str(column.type).upper()
            for column in expected.columns
        ):
            raise CanonicalValidationError("tipos de colunas canonicas inesperados")
        if any(
            bool(actual_columns[column.name]["nullable"]) != bool(column.nullable)
            for column in expected.columns
            if not column.primary_key
        ):
            raise CanonicalValidationError("nulabilidade canonica inesperada")
        actual_pk = tuple(inspector.get_pk_constraint(name).get("constrained_columns") or ())
        expected_pk = tuple(column.name for column in expected.primary_key.columns)
        if actual_pk != expected_pk:
            raise CanonicalValidationError("chave primaria canonica inesperada")
        actual_unique = {
            tuple(item["column_names"])
            for item in inspector.get_unique_constraints(name)
            if item.get("column_names")
        }
        actual_unique.update(
            tuple(item["column_names"])
            for item in inspector.get_indexes(name)
            if item.get("unique") and item.get("column_names")
        )
        if not _expected_unique_columns(expected) <= actual_unique:
            raise CanonicalValidationError("constraint UNIQUE canonica ausente")
        actual_indexes = {
            (tuple(item["column_names"]), bool(item.get("unique")))
            for item in inspector.get_indexes(name)
            if item.get("column_names")
        }
        expected_indexes = {
            (tuple(column.name for column in index.columns), bool(index.unique))
            for index in expected.indexes
        }
        if not expected_indexes <= actual_indexes:
            raise CanonicalValidationError("indice canonico esperado esta ausente")
        actual_fks = {
            (
                tuple(item["constrained_columns"]),
                item["referred_table"],
                tuple(item["referred_columns"]),
            )
            for item in inspector.get_foreign_keys(name)
        }
        expected_fks = {
            (
                tuple(element.parent.name for element in constraint.elements),
                next(iter(constraint.elements)).column.table.name,
                tuple(element.column.name for element in constraint.elements),
            )
            for constraint in expected.foreign_key_constraints
        }
        if actual_fks != expected_fks:
            raise CanonicalValidationError("chaves estrangeiras canonicas inesperadas")


def _validate_database(path: Path, engine: Engine) -> CanonicalDatabaseResult:
    _validate_schema(engine)
    with closing(open_canonical_connection(path)) as connection:
        tables = tuple(sorted(EXPECTED_TABLES))
        counts = {
            name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            for name in tables
        }
        if any(counts.values()):
            raise CanonicalValidationError("banco canonico temporario nao esta vazio")
        foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        violations = sum(1 for _ in connection.execute("PRAGMA foreign_key_check"))
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        if not foreign_keys_enabled or violations or integrity != ["ok"]:
            raise CanonicalValidationError("validacao SQLite do banco canonico falhou")
        checksum = _schema_signature(connection)
    return CanonicalDatabaseResult(
        path=path,
        schema_version=CANONICAL_SCHEMA_VERSION,
        schema_checksum_sha256=checksum,
        tables=tables,
        row_count=sum(counts.values()),
        foreign_keys_enabled=foreign_keys_enabled,
        foreign_key_violations=violations,
        integrity_check_passed=True,
    )


def create_temporary_canonical_database(
    destination_path: str | Path,
    *,
    source_snapshots: tuple[ValidatedSnapshot, ValidatedSnapshot],
) -> CanonicalDatabaseResult:
    """Cria e valida um banco novo; nao le snapshots nem carrega registros."""
    destination = _validated_non_operational_path(destination_path)
    if (
        len(source_snapshots) != 2
        or any(not isinstance(item, ValidatedSnapshot) for item in source_snapshots)
        or source_snapshots[0].path.resolve(strict=False)
        == source_snapshots[1].path.resolve(strict=False)
    ):
        raise CanonicalValidationError("dois snapshots validados e distintos sao obrigatorios")
    snapshot_paths = {item.path.resolve(strict=False) for item in source_snapshots}
    if destination in snapshot_paths:
        raise CanonicalUnsafePathError("snapshot de origem nao pode ser usado como destino")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb"):
            pass
    except FileExistsError as exc:
        raise CanonicalDestinationExistsError("destino canonico ja existe") from exc
    except OSError as exc:
        raise CanonicalCreationError("destino canonico nao pode ser preparado") from exc

    completed = False
    engine: Engine | None = None
    try:
        engine = _temporary_engine(destination)
        with engine.begin() as connection:
            if connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() != 1:
                raise CanonicalValidationError("foreign_keys nao esta habilitado")
            Base.metadata.create_all(bind=connection)
        result = _validate_database(destination, engine)
        completed = True
        return result
    except CanonicalDatabaseError:
        raise
    except Exception as exc:
        raise CanonicalCreationError("criacao do banco canonico temporario falhou") from exc
    finally:
        if engine is not None:
            engine.dispose()
        if not completed:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass
