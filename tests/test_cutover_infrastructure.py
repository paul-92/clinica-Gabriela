import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from backend.cutover.infrastructure import (
    AclPolicy,
    BackupError,
    MaintenanceLockError,
    OperationalPointer,
    PointerError,
    PromotionError,
    acquire_maintenance_lock,
    atomic_swap_pointer,
    create_final_backup,
    directory_acl_fingerprint,
    freeze_runtime,
    promote_candidate,
    read_pointer,
    rollback_pointer,
    sha256_file,
)


RUNTIME_HASH = "1" * 64


def database(path: Path, value: str = "fixture") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL REFERENCES parent(id))")
        connection.execute("INSERT INTO parent VALUES (1, ?)", (value,))
        connection.execute("INSERT INTO child VALUES (1, 1)")
    return path


def pointer(db: Path, generation=1, state="legacy", previous=None):
    return OperationalPointer(
        generation=generation,
        state=state,
        database_path=str(db.resolve()),
        database_checksum_sha256=sha256_file(db),
        schema_version="backend-models-v2-credential-reset",
        runtime_manifest_checksum_sha256=RUNTIME_HASH,
        previous_pointer_checksum_sha256=previous,
    )


def write_pointer(path: Path, value: OperationalPointer):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.bytes())


def test_maintenance_lock_is_exclusive_and_owner_checked(tmp_path):
    path = tmp_path / "maintenance.lock"
    lock = acquire_maintenance_lock(path, "execution-1")
    with pytest.raises(MaintenanceLockError):
        acquire_maintenance_lock(path, "execution-2")
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(MaintenanceLockError):
        lock.release()


def test_pointer_swap_is_atomic_cas_and_rollback_is_reversible(tmp_path):
    legacy = database(tmp_path / "legacy.db")
    canonical = database(tmp_path / "canonical.db", "canonical")
    path = tmp_path / "runtime" / "pointer.json"
    history = tmp_path / "runtime" / "history"
    old = pointer(legacy)
    write_pointer(path, old)
    lock = acquire_maintenance_lock(tmp_path / "runtime" / "maintenance.lock", "execution-1")
    new = pointer(canonical, 2, "canonical", old.checksum)
    new_checksum = atomic_swap_pointer(
        path, new, expected_current_checksum=old.checksum, lock=lock, history_dir=history
    )
    assert read_pointer(path).state == "canonical"
    assert new_checksum == read_pointer(path).checksum
    with pytest.raises(PointerError):
        atomic_swap_pointer(path, new, expected_current_checksum=old.checksum,
                            lock=lock, history_dir=history)
    rollback_pointer(path, old.checksum, expected_current_checksum=new_checksum,
                     lock=lock, history_dir=history)
    rolled_back = read_pointer(path)
    assert rolled_back.state == "legacy"
    assert Path(rolled_back.database_path) == legacy.resolve()
    assert rolled_back.generation == 3
    lock.release()


def test_pointer_fails_closed_on_database_tamper(tmp_path):
    db = database(tmp_path / "legacy.db")
    path = tmp_path / "pointer.json"
    value = pointer(db)
    write_pointer(path, value)
    with db.open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(PointerError):
        read_pointer(path)


def test_promotion_is_content_addressed_fail_existing_and_acl_bound(tmp_path):
    candidate = database(tmp_path / "source" / "candidate.db")
    destination = tmp_path / "canonical"
    destination.mkdir()
    lock = acquire_maintenance_lock(tmp_path / "maintenance.lock", "execution-1")
    checksum = sha256_file(candidate)
    policy = AclPolicy(directory_acl_fingerprint(destination))
    promoted = promote_candidate(candidate, destination, "verified-v2",
                                 expected_checksum=checksum, acl_policy=policy, lock=lock)
    assert sha256_file(promoted) == checksum
    with pytest.raises(PromotionError):
        promote_candidate(candidate, destination, "verified-v2",
                          expected_checksum=checksum, acl_policy=policy, lock=lock)
    with pytest.raises(PromotionError):
        promote_candidate(candidate, destination, "other",
                          expected_checksum="0" * 64, acl_policy=policy, lock=lock)
    lock.release()


def test_promotion_rejects_sidecars_and_unapproved_acl(tmp_path):
    candidate = database(tmp_path / "candidate.db")
    destination = tmp_path / "canonical"
    destination.mkdir()
    lock = acquire_maintenance_lock(tmp_path / "maintenance.lock", "execution-1")
    (candidate.parent / (candidate.name + "-wal")).write_bytes(b"pending")
    with pytest.raises(Exception):
        promote_candidate(candidate, destination, "v2", expected_checksum=sha256_file(candidate),
                          acl_policy=AclPolicy(directory_acl_fingerprint(destination)), lock=lock)
    (candidate.parent / (candidate.name + "-wal")).unlink()
    with pytest.raises(PromotionError):
        promote_candidate(candidate, destination, "v2", expected_checksum=sha256_file(candidate),
                          acl_policy=AclPolicy("0" * 64), lock=lock)
    lock.release()


def test_final_backup_is_manifested_restorable_and_source_immutable(tmp_path):
    desktop = database(tmp_path / "sources" / "desktop.db", "desktop")
    backend = database(tmp_path / "sources" / "backend.db", "backend")
    before = (sha256_file(desktop), sha256_file(backend))
    lock = acquire_maintenance_lock(tmp_path / "maintenance.lock", "execution-1",
                                    databases=(desktop, backend))
    manifest = create_final_backup(
        {"desktop": desktop, "backend": backend}, tmp_path / "backup",
        execution_reference="execution-1", lock=lock,
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert len(payload["entries"]) == 2
    assert all(entry["integrity_check"] == "ok" for entry in payload["entries"])
    assert before == (sha256_file(desktop), sha256_file(backend))
    for entry in payload["entries"]:
        restored = tmp_path / f"restore-{entry['role']}.db"
        restored.write_bytes((tmp_path / "backup" / f"{entry['role']}.backup.db").read_bytes())
        with sqlite3.connect(restored) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert list(connection.execute("PRAGMA foreign_key_check")) == []
    lock.release()


def test_final_backup_requires_owned_lock_and_rejects_sidecar(tmp_path):
    source = database(tmp_path / "source.db")
    lock = acquire_maintenance_lock(tmp_path / "maintenance.lock", "execution-1",
                                    databases=(source,))
    lock.release()
    with pytest.raises(MaintenanceLockError):
        create_final_backup({"source": source}, tmp_path / "backup", execution_reference="x", lock=lock)
    lock = acquire_maintenance_lock(tmp_path / "maintenance.lock", "execution-1",
                                    databases=(source,))
    (tmp_path / "source.db-shm").write_bytes(b"pending")
    with pytest.raises(BackupError):
        create_final_backup({"source": source}, tmp_path / "backup-2",
                            execution_reference="x", lock=lock)
    lock.release()


def test_runtime_freeze_is_content_addressed_and_immutable(tmp_path):
    root = tmp_path / "runtime"
    root.mkdir()
    (root / "a.py").write_text("a = 1\n", encoding="utf-8")
    (root / "b.py").write_text("b = 2\n", encoding="utf-8")
    destination = tmp_path / "manifests"
    manifest, checksum = freeze_runtime(root, ["a.py", "b.py"], destination)
    assert manifest.name == f"runtime-manifest-{checksum}.json"
    with pytest.raises(Exception):
        freeze_runtime(root, ["a.py", "b.py"], destination)
    (root / "a.py").write_text("a = 3\n", encoding="utf-8")
    second, second_checksum = freeze_runtime(root, ["a.py", "b.py"], destination)
    assert second != manifest and second_checksum != checksum


def test_full_fixture_cutover_and_failure_rollback_path(tmp_path):
    legacy = database(tmp_path / "legacy.db", "legacy")
    candidate = database(tmp_path / "candidate.db", "candidate")
    runtime_dir = tmp_path / "runtime"
    canonical_dir = tmp_path / "canonical"
    canonical_dir.mkdir()
    pointer_path = runtime_dir / "pointer.json"
    old = pointer(legacy)
    write_pointer(pointer_path, old)
    lock = acquire_maintenance_lock(runtime_dir / "maintenance.lock", "execution-sim",
                                    databases=(legacy,))
    create_final_backup({"legacy": legacy}, tmp_path / "final-backup",
                        execution_reference="execution-sim", lock=lock)
    promoted = promote_candidate(
        candidate, canonical_dir, "verified-v2", expected_checksum=sha256_file(candidate),
        acl_policy=AclPolicy(directory_acl_fingerprint(canonical_dir)), lock=lock,
    )
    canonical_pointer = pointer(promoted, 2, "canonical", old.checksum)
    current = atomic_swap_pointer(pointer_path, canonical_pointer,
                                  expected_current_checksum=old.checksum,
                                  lock=lock, history_dir=runtime_dir / "history")
    # Simula FAIL em START/HEALTH/SMOKE antes de writes e executa rollback.
    rollback_pointer(pointer_path, old.checksum, expected_current_checksum=current,
                     lock=lock, history_dir=runtime_dir / "history")
    assert read_pointer(pointer_path).state == "legacy"
    assert sha256_file(legacy) == old.database_checksum_sha256
    lock.release()


def test_sqlite_exclusive_lock_blocks_concurrent_writer(tmp_path):
    source = database(tmp_path / "source.db")
    lock = acquire_maintenance_lock(tmp_path / "maintenance.lock", "execution",
                                    databases=(source,))
    competing = sqlite3.connect(source, timeout=0)
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            competing.execute("INSERT INTO parent VALUES (2, 'blocked')")
            competing.commit()
    finally:
        competing.close()
        lock.release()


def test_maintenance_lock_rejects_preexisting_sidecar(tmp_path):
    source = database(tmp_path / "source.db")
    (tmp_path / "source.db-wal").write_bytes(b"pending")
    with pytest.raises(MaintenanceLockError, match="sidecar"):
        acquire_maintenance_lock(tmp_path / "maintenance.lock", "execution",
                                 databases=(source,))
    assert not (tmp_path / "maintenance.lock").exists()
