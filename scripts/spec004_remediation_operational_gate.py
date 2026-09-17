"""Operational gate forward-only da remediação SPEC-004 (Generation 7 -> 8)."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.cutover.infrastructure import (
    AclPolicy, OperationalPointer, SCHEMA_VERSION, _atomic_create,
    acquire_maintenance_lock, atomic_swap_pointer, create_final_backup,
    directory_acl_fingerprint, promote_candidate, read_pointer, sha256_file,
    verify_runtime_manifest,
)

SOURCE_COMMIT = "0832eccd03e9bcb64f02b2944e9ecedd721596af"
EXPECTED_POINTER = "9d3300076994702b6e60d48c9c16cb0bcd5e6a38ed290e55aa663bbf2a104ba2"
EXPECTED_DATABASE = "7f4412c6fefccbccce5fa511e35a21bd88eec97447ffbe4787fc2c2101939a07"
EXPECTED_MANIFEST = "b2ff5b733b344b2916733acd62bfb3c05b108ca6b86c6564d96fdcc06b57b20d"
EXPECTED_CANDIDATE = "1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8"
EXPECTED_FREEZE = "41236c2f285bf8ba7260e34abc6b139a51ab5e1687282e74ff4a2d35e96ed852"


def canonical_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def load_migration():
    path = ROOT / "backend" / "migration" / "spec004_remediation.py"
    spec = importlib.util.spec_from_file_location("spec004_remediation_operational", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.migrate_spec004_remediation


def validate_database(path: Path, version: int, expected_hash: str | None = None) -> dict:
    if expected_hash and sha256_file(path) != expected_hash:
        raise RuntimeError("checksum do banco diverge")
    uri = "file:" + path.resolve().as_posix() + "?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as db:
        result = {
            "sha256": sha256_file(path),
            "user_version": db.execute("PRAGMA user_version").fetchone()[0],
            "integrity_check": db.execute("PRAGMA integrity_check").fetchone()[0],
            "foreign_key_violations": len(list(db.execute("PRAGMA foreign_key_check"))),
            "appointments": db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
            "events": db.execute("SELECT COUNT(*) FROM appointment_events").fetchone()[0],
        }
        indexes = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='index'")}
        triggers = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    if result["user_version"] != version or result["integrity_check"] != "ok" or result["foreign_key_violations"]:
        raise RuntimeError("validacao SQLite falhou")
    if version == 5 and (
        "ux_appointments_original_successor" not in indexes
        or not {"spec004_events_no_update", "spec004_events_no_delete", "spec004_reschedule_event_guard"} <= triggers
    ):
        raise RuntimeError("schema v5 incompleto")
    return result


def runtime_files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.splitlines()
    selected = [p for p in tracked if p in {"main.py", "requirements.txt"}
                or (p.startswith("backend/") and p.endswith(".py"))
                or (p.startswith("app/") and p.endswith(".py"))
                or p in {"scripts/run_api.ps1", "scripts/run_all.ps1",
                         "scripts/spec004_remediation_candidate.py"}]
    return sorted(selected)


def freeze_and_manifest(runtime: Path) -> tuple[Path, str, str]:
    entries = []
    source_entries = []
    for relative in runtime_files():
        active = (ROOT / relative).read_bytes()
        source = subprocess.run(["git", "show", f"{SOURCE_COMMIT}:{relative}"], cwd=ROOT,
                                capture_output=True, check=True).stdout
        if active.replace(b"\r\n", b"\n") != source.replace(b"\r\n", b"\n"):
            raise RuntimeError(f"checkout ativo diverge semanticamente do commit: {relative}")
        entries.append({"path": relative, "sha256": hashlib.sha256(active).hexdigest(),
                        "size_bytes": len(active), "source_sha256": hashlib.sha256(source).hexdigest()})
        source_entries.append({"path": relative, "sha256": hashlib.sha256(source).hexdigest(),
                               "size_bytes": len(source)})
    authorized = {"format_version": "1.0-spec004-remediation", "source_commit": SOURCE_COMMIT,
                  "predecessor_generation": 7, "migration": "backend/migration/spec004_remediation.py",
                  "entries": source_entries, "privacy_safe": True}
    if hashlib.sha256(canonical_bytes(authorized)).hexdigest() != EXPECTED_FREEZE:
        raise RuntimeError("freeze autorizado nao foi reproduzido")
    payload = {**authorized, "entries": entries, "schema_version": SCHEMA_VERSION,
               "candidate_database_sha256": EXPECTED_CANDIDATE,
               "authorized_freeze_sha256": EXPECTED_FREEZE}
    data = canonical_bytes(payload)
    checksum = hashlib.sha256(data).hexdigest()
    path = runtime / "runtime-manifests" / f"runtime-manifest-{checksum}.json"
    _atomic_create(path, data)
    verify_runtime_manifest(ROOT, path, checksum)
    return path, checksum, EXPECTED_FREEZE


def default_smoke(port: int, *, read_only: bool) -> dict:
    env = os.environ.copy()
    for name in ("CLINICA_OPERATIONAL_POINTER", "CLINICA_RUNTIME_CODE_ROOT",
                 "CLINICA_RUNTIME_ROOT", "CLINICA_RUNTIME_MANIFEST_DIR",
                 "BACKEND_DATABASE_PATH", "BACKEND_DATA_DIR"):
        env.pop(name, None)
    env.update({"AUTH_SECRET": "spec004-operational-gate-secret-32-bytes",
                "BACKEND_PORT": str(port), "BACKEND_RELOAD": "false",
                "BACKEND_VERIFY_READ_ONLY": "true" if read_only else "false"})
    process = subprocess.Popen([sys.executable, "-m", "backend.main"], cwd=ROOT, env=env,
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"backend default encerrou: {process.returncode}")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=.5) as response:
                    if response.status == 200 and json.loads(response.read()).get("status") == "ok":
                        return {"launcher": "python -m backend.main", "health": "PASS",
                                "forbidden_overrides_absent": True, "read_only": read_only}
            except OSError:
                time.sleep(.1)
        raise RuntimeError("health default timeout")
    finally:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(timeout=8)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve(strict=True)
    pointer_path = runtime / "operational-pointer.json"
    if sha256_file(pointer_path) != EXPECTED_POINTER:
        raise RuntimeError("pointer predecessor diverge")
    predecessor = read_pointer(pointer_path)
    if (predecessor.generation, predecessor.state, predecessor.database_checksum_sha256,
            predecessor.runtime_manifest_checksum_sha256) != (7, "canonical", EXPECTED_DATABASE, EXPECTED_MANIFEST):
        raise RuntimeError("envelope predecessor diverge")
    predecessor_db = Path(predecessor.database_path).resolve(strict=True)
    pre = validate_database(predecessor_db, 4, EXPECTED_DATABASE)
    if (runtime / "maintenance.lock").exists() or any(Path(str(predecessor_db) + s).exists() for s in ("-wal", "-shm", "-journal")):
        raise RuntimeError("lock ou sidecar residual")
    if shutil.disk_usage(runtime).free < predecessor_db.stat().st_size * 12:
        raise RuntimeError("espaco insuficiente")
    candidate = runtime / "candidates" / f"spec004-remediation-v5-{EXPECTED_CANDIDATE[:12]}.db"
    if candidate.exists():
        validate_database(candidate, 5, EXPECTED_CANDIDATE)
    else:
        shutil.copy2(predecessor_db, candidate)
        load_migration()(candidate)
    candidate_validation = validate_database(candidate, 5, EXPECTED_CANDIDATE)
    if (candidate_validation["appointments"], candidate_validation["events"]) != (pre["appointments"], pre["events"]):
        raise RuntimeError("contagens divergiram")
    manifest_path, manifest_checksum, freeze_checksum = freeze_and_manifest(runtime)
    execution = "spec004-remediation-operational-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    lock = acquire_maintenance_lock(runtime / "maintenance.lock", execution, databases=(predecessor_db,))
    activated = False
    try:
        backup_dir = runtime / "backups" / f"{execution}-generation-7"
        backup_manifest = create_final_backup({"generation_7": predecessor_db}, backup_dir,
                                              execution_reference=execution, lock=lock)
        restored = backup_dir / "restore-isolated.db"
        shutil.copy2(backup_dir / "generation_7.backup.db", restored)
        restore_validation = validate_database(restored, 4, EXPECTED_DATABASE)
        promoted = promote_candidate(candidate, runtime / "generations", "spec004-remediation-v5",
                                     expected_checksum=EXPECTED_CANDIDATE,
                                     acl_policy=AclPolicy(directory_acl_fingerprint(runtime / "generations")), lock=lock)
        new_pointer = OperationalPointer(8, "canonical", str(promoted), EXPECTED_CANDIDATE,
                                         SCHEMA_VERSION, manifest_checksum, predecessor.checksum)
        pointer_checksum = atomic_swap_pointer(pointer_path, new_pointer,
                                               expected_current_checksum=EXPECTED_POINTER,
                                               lock=lock, history_dir=runtime / "pointer-history")
        activated = True
        read_only_smoke = default_smoke(8766, read_only=True)
    finally:
        lock.release()
    if not activated:
        raise RuntimeError("ativacao nao concluida")
    write_smoke = default_smoke(8767, read_only=False)
    promoted_db = Path(read_pointer(pointer_path).database_path)
    for suffix in ("-wal", "-shm", "-journal"):
        if Path(str(promoted_db) + suffix).exists():
            raise RuntimeError("sidecar residual apos smoke")
    stabilized = validate_database(promoted_db, 5)
    stabilization_lock = acquire_maintenance_lock(runtime / "maintenance.lock", execution + "-stabilized",
                                                  databases=(promoted_db,))
    try:
        stabilized_dir = runtime / "backups" / f"{execution}-generation-8-stabilized"
        stabilized_manifest = create_final_backup({"generation_8": promoted_db}, stabilized_dir,
                                                  execution_reference=execution + "-stabilized",
                                                  lock=stabilization_lock)
        stabilized_restore = stabilized_dir / "restore-isolated.db"
        shutil.copy2(stabilized_dir / "generation_8.backup.db", stabilized_restore)
        stabilized_restore_validation = validate_database(stabilized_restore, 5, stabilized["sha256"])
    finally:
        stabilization_lock.release()
    evidence = {"result": "READY_FOR_SPEC004_SECOND_INDEPENDENT_QUALITY_REVIEW",
                "execution": execution, "source_commit": SOURCE_COMMIT,
                "predecessor": pre, "candidate": candidate_validation,
                "generation": 8, "pointer_sha256": pointer_checksum,
                "runtime_manifest_sha256": manifest_checksum, "runtime_manifest": str(manifest_path),
                "freeze_sha256": freeze_checksum, "backup_manifest": str(backup_manifest),
                "restore": restore_validation, "read_only_smoke": read_only_smoke,
                "write_smoke": write_smoke, "stabilized": stabilized,
                "stabilized_backup_manifest": str(stabilized_manifest),
                "stabilized_restore": stabilized_restore_validation, "privacy_safe": True}
    data = canonical_bytes(evidence)
    checksum = hashlib.sha256(data).hexdigest()
    evidence_path = runtime / "evidence" / f"spec004-remediation-operational-{checksum}.json"
    _atomic_create(evidence_path, data)
    print(json.dumps({**evidence, "evidence_sha256": checksum, "evidence_path": str(evidence_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
