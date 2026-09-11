"""Criacao e validacao de snapshots SQLite para analise de migracao."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.migration.manifests import IntegrityStatus, SnapshotManifest, SourceDatabase
from scripts.sqlite_inventory import _readonly_connection


class SnapshotError(Exception):
    """Erro base controlado de snapshot."""


class SnapshotSourceNotFoundError(SnapshotError):
    pass


class SnapshotSamePathError(SnapshotError):
    pass


class SnapshotDestinationExistsError(SnapshotError):
    pass


class SnapshotBackupError(SnapshotError):
    pass


class SnapshotSourceChangedError(SnapshotError):
    pass


class SnapshotInvalidError(SnapshotError):
    pass


class SnapshotIntegrityError(SnapshotInvalidError):
    pass


class SnapshotManifestError(SnapshotError):
    pass


@dataclass(frozen=True)
class ValidatedSnapshot:
    path: Path
    manifest: SnapshotManifest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_state(path: Path) -> tuple[int, int, str]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, _sha256(path)


def validate_sqlite_snapshot(
    path: str | Path,
    manifest: SnapshotManifest,
) -> ValidatedSnapshot:
    """Revalida arquivo, checksum, schema e integridade em modo read-only."""
    snapshot = Path(path).expanduser().resolve(strict=False)
    if not snapshot.is_file() or snapshot.stat().st_size <= 0:
        raise SnapshotInvalidError("snapshot ausente ou vazio")
    try:
        checksum = _sha256(snapshot)
        if checksum != manifest.checksum_sha256:
            raise SnapshotInvalidError("checksum do snapshot diverge do manifest")
        with closing(_readonly_connection(snapshot)) as connection:
            integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
            if integrity != ["ok"]:
                raise SnapshotIntegrityError("integrity_check do snapshot falhou")
            schema_rows = connection.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_schema ORDER BY type, name"
            ).fetchall()
            schema_bytes = json.dumps(
                [tuple(row) for row in schema_rows],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            schema_checksum = hashlib.sha256(schema_bytes).hexdigest()
            foreign_key_violations = sum(
                1 for _ in connection.execute("PRAGMA foreign_key_check")
            )
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    except SnapshotError:
        raise
    except (OSError, sqlite3.Error, ValueError) as exc:
        raise SnapshotInvalidError("snapshot nao pode ser validado") from exc

    if schema_checksum != manifest.schema_checksum_sha256:
        raise SnapshotInvalidError("schema do snapshot diverge do manifest")
    if manifest.schema_version != f"sqlite-user-version-{user_version}":
        raise SnapshotInvalidError("versao de schema diverge do manifest")
    if foreign_key_violations != manifest.foreign_key_check_violations:
        raise SnapshotInvalidError("resumo de integridade diverge do manifest")
    if foreign_key_violations:
        raise SnapshotIntegrityError("snapshot possui violacoes de chave estrangeira")
    if manifest.integrity_status is not IntegrityStatus.PASSED:
        raise SnapshotManifestError("manifest nao declara snapshot validado")
    if snapshot.stat().st_size != manifest.size_bytes:
        raise SnapshotInvalidError("tamanho do snapshot diverge do manifest")
    return ValidatedSnapshot(path=snapshot, manifest=manifest)


def create_sqlite_snapshot(
    source_path: str | Path,
    destination_path: str | Path,
    *,
    source_label: SourceDatabase,
    snapshot_reference: str,
) -> ValidatedSnapshot:
    """Cria snapshot novo pela SQLite Backup API e o valida integralmente."""
    source = Path(source_path).expanduser().resolve(strict=False)
    destination = Path(destination_path).expanduser().resolve(strict=False)
    if not source.is_file():
        raise SnapshotSourceNotFoundError("origem SQLite inexistente")
    if source == destination:
        raise SnapshotSamePathError("origem e destino do snapshot devem ser distintos")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb"):
            pass
    except FileExistsError as exc:
        raise SnapshotDestinationExistsError("destino do snapshot ja existe") from exc
    except OSError as exc:
        raise SnapshotBackupError("destino do snapshot nao pode ser preparado") from exc

    created_destination = True
    try:
        before = _source_state(source)
        try:
            with closing(_readonly_connection(source)) as origin, closing(
                sqlite3.connect(destination)
            ) as target:
                origin.backup(target)
        except (OSError, sqlite3.Error) as exc:
            raise SnapshotBackupError("SQLite Backup API nao concluiu o snapshot") from exc
        after = _source_state(source)
        if after != before:
            raise SnapshotSourceChangedError("origem mudou durante a criacao do snapshot")

        size_bytes = destination.stat().st_size
        checksum = _sha256(destination)
        try:
            with closing(_readonly_connection(destination)) as connection:
                integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
                if integrity != ["ok"]:
                    raise SnapshotIntegrityError("integrity_check do snapshot falhou")
                schema_rows = connection.execute(
                    "SELECT type, name, tbl_name, sql FROM sqlite_schema ORDER BY type, name"
                ).fetchall()
                schema_checksum = hashlib.sha256(
                    json.dumps(
                        [tuple(row) for row in schema_rows],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest()
                foreign_key_violations = sum(
                    1 for _ in connection.execute("PRAGMA foreign_key_check")
                )
                user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        except SnapshotError:
            raise
        except (OSError, sqlite3.Error, ValueError) as exc:
            raise SnapshotInvalidError("snapshot criado nao pode ser validado") from exc
        if foreign_key_violations:
            raise SnapshotIntegrityError("snapshot possui violacoes de chave estrangeira")
        try:
            manifest = SnapshotManifest(
                source_label=source_label,
                snapshot_reference=snapshot_reference,
                checksum_sha256=checksum,
                size_bytes=size_bytes,
                captured_at=datetime.now(timezone.utc),
                schema_version=f"sqlite-user-version-{user_version}",
                schema_checksum_sha256=schema_checksum,
                integrity_status=IntegrityStatus.PASSED,
                foreign_key_check_violations=foreign_key_violations,
            )
        except ValueError as exc:
            raise SnapshotManifestError("SnapshotManifest nao pode ser produzido") from exc
        validated = validate_sqlite_snapshot(destination, manifest)
        created_destination = False
        return validated
    finally:
        if created_destination:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass
