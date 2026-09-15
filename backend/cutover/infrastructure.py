"""Primitivas fail-closed de cutover, sem executar cutover automaticamente."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = "backend-models-v2-credential-reset"


class CutoverError(RuntimeError):
    pass


class MaintenanceLockError(CutoverError):
    pass


class PointerError(CutoverError):
    pass


class PromotionError(CutoverError):
    pass


class BackupError(CutoverError):
    pass


class RuntimeFreezeError(CutoverError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _atomic_create(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    # O nome final pode ser content-addressed e longo. Repeti-lo no temporario
    # excede MAX_PATH em raizes pytest profundas no Windows.
    descriptor, name = tempfile.mkstemp(prefix=".create-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CutoverError("destino imutavel ja existe") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(data).hexdigest()


def _atomic_replace(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".replace-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(data).hexdigest()


@dataclass
class MaintenanceLock:
    path: Path
    execution_reference: str
    token: str
    _database_locks: dict[Path, sqlite3.Connection]

    def assert_held(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise MaintenanceLockError("maintenance lock ausente ou invalido") from exc
        if payload.get("execution_reference") != self.execution_reference or payload.get("token") != self.token:
            raise MaintenanceLockError("maintenance lock pertence a outro owner")

    def release(self) -> None:
        self.assert_held()
        for connection in self._database_locks.values():
            try:
                connection.rollback()
            finally:
                connection.close()
        self._database_locks.clear()
        self.path.unlink()

    def locked_connection(self, path: Path) -> sqlite3.Connection:
        self.assert_held()
        resolved = path.resolve(strict=True)
        try:
            return self._database_locks[resolved]
        except KeyError as exc:
            raise MaintenanceLockError("fonte nao esta sob lock SQLite exclusivo") from exc


def acquire_maintenance_lock(path: Path, execution_reference: str, *,
                             databases: Iterable[Path] = ()) -> MaintenanceLock:
    path = path.resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    token = os.urandom(32).hex()
    payload = {
        "format_version": "1.0",
        "execution_reference": execution_reference,
        "pid": os.getpid(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "token": token,
    }
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise MaintenanceLockError("maintenance lock ja adquirido") from exc
    database_locks: dict[Path, sqlite3.Connection] = {}
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical_bytes(payload))
            stream.flush()
            os.fsync(stream.fileno())
        for database in databases:
            resolved = database.resolve(strict=True)
            if any((resolved.parent / (resolved.name + suffix)).exists()
                   for suffix in ("-wal", "-shm", "-journal")):
                raise MaintenanceLockError("fonte possui sidecar antes da quiescencia")
            connection = sqlite3.connect(resolved, timeout=0, isolation_level=None)
            try:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA locking_mode=EXCLUSIVE")
                connection.execute("BEGIN EXCLUSIVE")
            except Exception:
                connection.close()
                raise MaintenanceLockError("nao foi possivel adquirir lock SQLite exclusivo")
            database_locks[resolved] = connection
    except Exception:
        for connection in database_locks.values():
            connection.rollback()
            connection.close()
        path.unlink(missing_ok=True)
        raise
    return MaintenanceLock(path, execution_reference, token, database_locks)


def maintenance_active(path: Path) -> bool:
    return path.is_file()


@dataclass(frozen=True)
class OperationalPointer:
    generation: int
    state: str
    database_path: str
    database_checksum_sha256: str
    schema_version: str
    runtime_manifest_checksum_sha256: str
    previous_pointer_checksum_sha256: str | None = None

    def validate(self) -> None:
        if self.generation < 1 or self.state not in {"legacy", "canonical"}:
            raise PointerError("ponteiro possui estado invalido")
        database = Path(self.database_path)
        if not database.is_absolute() or not database.is_file():
            raise PointerError("banco apontado deve existir em caminho absoluto")
        if sha256_file(database) != self.database_checksum_sha256:
            raise PointerError("checksum do banco apontado diverge")
        if self.schema_version != SCHEMA_VERSION:
            raise PointerError("schema do ponteiro diverge")
        for value in (self.database_checksum_sha256, self.runtime_manifest_checksum_sha256):
            if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise PointerError("checksum do ponteiro invalido")

    def bytes(self) -> bytes:
        self.validate()
        return _canonical_bytes(asdict(self))

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.bytes()).hexdigest()


def read_pointer(path: Path) -> OperationalPointer:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pointer = OperationalPointer(**payload)
        pointer.validate()
        return pointer
    except (OSError, ValueError, TypeError) as exc:
        raise PointerError("ponteiro ausente, corrompido ou invalido") from exc


def initialize_pointer(path: Path, pointer: OperationalPointer) -> str:
    if pointer.generation != 1 or pointer.previous_pointer_checksum_sha256 is not None:
        raise PointerError("ponteiro inicial deve ser geracao 1 sem predecessor")
    return _atomic_create(path, pointer.bytes())


def atomic_swap_pointer(path: Path, new: OperationalPointer, *,
                        expected_current_checksum: str, lock: MaintenanceLock,
                        history_dir: Path) -> str:
    lock.assert_held()
    current = read_pointer(path)
    if current.checksum != expected_current_checksum:
        raise PointerError("ponteiro mudou desde a validacao")
    if new.generation != current.generation + 1 or new.previous_pointer_checksum_sha256 != current.checksum:
        raise PointerError("cadeia ou geracao do novo ponteiro invalida")
    history_dir.mkdir(parents=True, exist_ok=True)
    _atomic_create(history_dir / f"pointer-{current.checksum}.json", current.bytes())
    return _atomic_replace(path, new.bytes())


def rollback_pointer(path: Path, previous_checksum: str, *,
                     expected_current_checksum: str, lock: MaintenanceLock,
                     history_dir: Path) -> str:
    lock.assert_held()
    current = read_pointer(path)
    if current.checksum != expected_current_checksum:
        raise PointerError("ponteiro atual diverge; rollback recusado")
    history = history_dir / f"pointer-{previous_checksum}.json"
    previous = read_pointer(history)
    rollback = OperationalPointer(
        generation=current.generation + 1,
        state=previous.state,
        database_path=previous.database_path,
        database_checksum_sha256=previous.database_checksum_sha256,
        schema_version=previous.schema_version,
        runtime_manifest_checksum_sha256=previous.runtime_manifest_checksum_sha256,
        previous_pointer_checksum_sha256=current.checksum,
    )
    _atomic_create(history_dir / f"pointer-{current.checksum}.json", current.bytes())
    return _atomic_replace(path, rollback.bytes())


@dataclass(frozen=True)
class AclPolicy:
    """Fingerprint exato aprovado externamente; nenhuma ACL e inferida."""

    fingerprint: str

    def validate(self) -> None:
        if len(self.fingerprint) != 64 or any(c not in "0123456789abcdef" for c in self.fingerprint):
            raise PromotionError("fingerprint ACL aprovado obrigatorio")


def directory_acl_fingerprint(path: Path) -> str:
    path = path.resolve(strict=True)
    if os.name == "nt":
        completed = subprocess.run(
            ["icacls", str(path)], capture_output=True, check=False
        )
        if completed.returncode:
            raise PromotionError("ACL do destino nao pode ser lida")
        payload = completed.stdout
    else:
        stat = path.stat()
        payload = f"{stat.st_uid}:{stat.st_gid}:{stat.st_mode}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _sqlite_validate(path: Path) -> dict:
    uri = "file:" + path.resolve().as_posix() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        violations = sum(1 for _ in connection.execute("PRAGMA foreign_key_check"))
    sidecars = sum((path.parent / (path.name + suffix)).exists()
                   for suffix in ("-wal", "-shm", "-journal"))
    if integrity != "ok" or violations or sidecars:
        raise CutoverError("SQLite nao esta apto para operacao controlada")
    return {"integrity_check": integrity, "foreign_key_violations": violations,
            "sidecars_pending": sidecars}


def promote_candidate(candidate: Path, destination_dir: Path, version: str, *,
                      expected_checksum: str, acl_policy: AclPolicy,
                      lock: MaintenanceLock) -> Path:
    lock.assert_held()
    candidate = candidate.resolve(strict=True)
    destination_dir = destination_dir.resolve(strict=True)
    acl_policy.validate()
    if directory_acl_fingerprint(destination_dir) != acl_policy.fingerprint:
        raise PromotionError("ACL do destino diverge da politica aprovada")
    if candidate.drive.casefold() != destination_dir.drive.casefold():
        raise PromotionError("promocao exige mesmo volume")
    if sha256_file(candidate) != expected_checksum:
        raise PromotionError("checksum do candidato diverge")
    _sqlite_validate(candidate)
    target = destination_dir / f"canonical-{version}-{expected_checksum[:12]}.db"
    if target.exists():
        raise PromotionError("destino versionado ja existe")
    descriptor, name = tempfile.mkstemp(prefix=".canonical.", suffix=".tmp", dir=destination_dir)
    os.close(descriptor)
    temporary = Path(name)
    try:
        shutil.copyfile(candidate, temporary)
        with temporary.open("r+b") as stream:
            os.fsync(stream.fileno())
        if sha256_file(temporary) != expected_checksum:
            raise PromotionError("copia de promocao diverge")
        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            raise PromotionError("concorrencia detectada na promocao") from exc
        _sqlite_validate(target)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
    return target


def create_final_backup(sources: dict[str, Path], destination: Path, *,
                        execution_reference: str, lock: MaintenanceLock) -> Path:
    lock.assert_held()
    destination = destination.resolve(strict=False)
    destination.mkdir(parents=True, exist_ok=False)
    entries = []
    try:
        for role, source in sorted(sources.items()):
            source = source.resolve(strict=True)
            lock.locked_connection(source)
            before = sha256_file(source)
            wal = source.parent / (source.name + "-wal")
            shm = source.parent / (source.name + "-shm")
            if (wal.exists() and wal.stat().st_size != 0) or (shm.exists() and not wal.exists()):
                raise BackupError("sidecar nao vazio ou incoerente durante lock")
            backup = destination / f"{role}.backup.db"
            shutil.copyfile(source, backup)
            with backup.open("r+b") as stream:
                os.fsync(stream.fileno())
            validation = _sqlite_validate(backup)
            if sha256_file(source) != before:
                raise BackupError("fonte mudou durante backup")
            entries.append({"role": role, "source_checksum_sha256": before,
                            "backup_checksum_sha256": sha256_file(backup),
                            "size_bytes": backup.stat().st_size, **validation})
        manifest = {"format_version": "1.0", "execution_reference": execution_reference,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "entries": entries, "privacy_safe": True}
        _atomic_create(destination / "final-backup-manifest.json", _canonical_bytes(manifest))
        return destination / "final-backup-manifest.json"
    except Exception:
        raise


def freeze_runtime(root: Path, relative_files: Iterable[str], destination: Path) -> tuple[Path, str]:
    root = root.resolve(strict=True)
    entries = []
    for relative in sorted(set(relative_files)):
        path = (root / relative).resolve(strict=True)
        if root not in path.parents or not path.is_file():
            raise RuntimeFreezeError("arquivo do runtime fora da raiz")
        entries.append({"path": relative.replace("\\", "/"),
                        "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    if not entries:
        raise RuntimeFreezeError("freeze de runtime vazio")
    payload = {"format_version": "1.0", "schema_version": SCHEMA_VERSION,
               "entries": entries, "privacy_safe": True}
    data = _canonical_bytes(payload)
    checksum = hashlib.sha256(data).hexdigest()
    target = destination / f"runtime-manifest-{checksum}.json"
    _atomic_create(target, data)
    return target, checksum


def verify_runtime_manifest(root: Path, manifest: Path, expected_checksum: str) -> None:
    root = root.resolve(strict=True)
    manifest = manifest.resolve(strict=True)
    if sha256_file(manifest) != expected_checksum:
        raise RuntimeFreezeError("checksum do manifest de runtime diverge")
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload["schema_version"] != SCHEMA_VERSION or not payload["entries"]:
            raise RuntimeFreezeError("manifest de runtime invalido")
        for entry in payload["entries"]:
            path = (root / entry["path"]).resolve(strict=True)
            if root not in path.parents or sha256_file(path) != entry["sha256"]:
                raise RuntimeFreezeError("runtime local diverge do manifest congelado")
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise RuntimeFreezeError("manifest de runtime nao pode ser validado") from exc
