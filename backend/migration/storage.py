"""Persistencia atomica e validacao de manifests de migracao.

O modulo nao escolhe diretorios nem nomes de arquivos. O chamador fornece um
caminho explicito e opta, tambem explicitamente, por criar pais ou sobrescrever
um artefato existente. Nao ha locking distribuido; a criacao sem overwrite usa
um hard link atomico no mesmo diretorio para nao substituir um concorrente.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, TypeVar

from pydantic import ValidationError

from backend.migration.manifests import (
    ExecutionManifest,
    HistoricalProvenanceSupplement,
    ManifestModel,
    RemapManifest,
    SnapshotManifest,
    StrictManifestModel,
    canonical_json,
)


class ManifestStorageError(Exception):
    """Erro base controlado da camada de persistencia."""


class ManifestNotFoundError(ManifestStorageError):
    """O arquivo solicitado nao existe."""


class ManifestAlreadyExistsError(ManifestStorageError):
    """O destino existe e overwrite nao foi autorizado."""


class ManifestChecksumMismatchError(ManifestStorageError):
    """Os bytes lidos nao correspondem ao checksum esperado."""


class ManifestInvalidContentError(ManifestStorageError):
    """O arquivo nao contem um manifest canonico valido."""


class ManifestUnexpectedTypeError(ManifestStorageError):
    """O arquivo ou modelo nao corresponde ao tipo esperado."""


class ManifestPersistenceError(ManifestStorageError):
    """A persistencia atomica nao pode ser concluida."""


class ManifestPostPromotionError(ManifestStorageError):
    """Falha ocorrida depois que o destino ja foi promovido integralmente."""

    destination_promoted = True


class ManifestDurabilityError(ManifestPostPromotionError):
    """O destino foi promovido, mas sua durabilidade nao foi confirmada."""


ManifestType = TypeVar("ManifestType", bound=StrictManifestModel)
_MODEL_SIGNATURES = {
    RemapManifest: frozenset({"manifest_version", "lifecycle", "entries"}),
    SnapshotManifest: frozenset({"source_label", "snapshot_reference", "size_bytes"}),
    ExecutionManifest: frozenset({"execution_id", "created_at", "status"}),
    HistoricalProvenanceSupplement: frozenset({"supplement_version", "freeze_reference", "entries"}),
}


def _validated_model(model: type[ManifestType]) -> type[ManifestType]:
    if model not in _MODEL_SIGNATURES:
        raise ManifestUnexpectedTypeError("tipo de manifest nao permitido")
    return model


def _fsync_directory(directory: Path) -> None:
    """Sincroniza metadados do diretorio quando a plataforma permite."""
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def save_manifest(
    path: str | Path,
    manifest: ManifestModel,
    *,
    overwrite: bool = False,
    create_parents: bool = False,
) -> str:
    """Persiste bytes canonicos atomicamente e retorna seu SHA-256.

    Com ``overwrite=False``, a promocao por hard link falha atomicamente caso o
    destino passe a existir. Com ``overwrite=True``, ``os.replace`` substitui o
    destino atomicamente. O temporario sempre reside no diretorio do destino.
    """
    try:
        data = canonical_json(manifest).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ManifestUnexpectedTypeError("somente manifests tipados podem ser persistidos") from exc

    destination = Path(path)
    parent = destination.parent
    if create_parents:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ManifestPersistenceError("nao foi possivel preparar o diretorio de destino") from exc
    if destination.exists() and not overwrite:
        raise ManifestAlreadyExistsError("manifest de destino ja existe")

    temporary: Path | None = None
    promoted = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=parent
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

        if overwrite:
            os.replace(temporary, destination)
            promoted = True
            temporary = None
        else:
            try:
                os.link(temporary, destination)
            except FileExistsError as exc:
                raise ManifestAlreadyExistsError("manifest de destino ja existe") from exc
            promoted = True
            temporary.unlink()
            temporary = None
    except ManifestAlreadyExistsError:
        raise
    except OSError as exc:
        if promoted:
            raise ManifestPostPromotionError(
                "manifest promovido, mas a finalizacao da operacao falhou"
            ) from exc
        raise ManifestPersistenceError("falha ao persistir manifest atomicamente") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    try:
        _fsync_directory(parent)
    except OSError as exc:
        raise ManifestDurabilityError(
            "manifest promovido, mas a durabilidade do diretorio nao foi confirmada"
        ) from exc

    return hashlib.sha256(data).hexdigest()


def load_stored_manifest(
    path: str | Path,
    model: type[ManifestType],
    *,
    expected_checksum: str | None = None,
) -> ManifestType:
    """Valida integridade, formato canonico e modelo antes de retornar o objeto."""
    expected_model = _validated_model(model)
    source = Path(path)
    try:
        data = source.read_bytes()
    except FileNotFoundError as exc:
        raise ManifestNotFoundError("arquivo de manifest inexistente") from exc
    except OSError as exc:
        raise ManifestInvalidContentError("nao foi possivel ler o arquivo de manifest") from exc

    actual_checksum = hashlib.sha256(data).hexdigest()
    if expected_checksum is not None and actual_checksum != expected_checksum:
        raise ManifestChecksumMismatchError("checksum do manifest diverge do esperado")

    try:
        text = data.decode("utf-8")
        payload: Any = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestInvalidContentError("manifest nao contem JSON UTF-8 valido") from exc
    if not isinstance(payload, dict):
        raise ManifestInvalidContentError("manifest deve conter um objeto JSON")

    detected = [kind for kind, signature in _MODEL_SIGNATURES.items() if signature <= payload.keys()]
    if detected and expected_model not in detected:
        raise ManifestUnexpectedTypeError("tipo do manifest difere do tipo esperado")
    try:
        manifest = expected_model.model_validate(payload)
    except ValidationError as exc:
        raise ManifestInvalidContentError("conteudo do manifest viola o contrato tipado") from exc
    if data != canonical_json(manifest).encode("utf-8"):
        raise ManifestInvalidContentError("arquivo nao usa a serializacao canonica esperada")
    return manifest
