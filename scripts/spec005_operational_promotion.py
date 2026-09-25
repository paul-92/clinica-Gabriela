"""SPEC-005 promotion reconstructed from the frozen contract and cutover primitives.

Run ``preflight`` first. It writes reviewable Evidence in docs/audit only. ``execute``
requires that exact Evidence and fails closed before touching operational files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.cutover.infrastructure import (
    AclPolicy, OperationalPointer, SCHEMA_VERSION, _atomic_create,
    _canonical_bytes, _sqlite_validate, acquire_maintenance_lock,
    atomic_swap_pointer, create_final_backup, directory_acl_fingerprint,
    freeze_runtime, promote_candidate, read_pointer, rollback_pointer,
    sha256_file, verify_runtime_manifest,
)
from backend.cutover.spec005_execution_identity import verify_manifest

E011 = ROOT / "docs/audit/spec005-20260924-e011-execution-evidence.json"
E012 = ROOT / "docs/audit/spec005-20260924-e012-independent-quality-review.md"
PLAN = ROOT / "docs/audit/spec005-20260924-promotion-orchestrator-reconstructed.md"
PREFLIGHT = ROOT / "docs/audit/spec005-20260924-promotion-preflight-v2.json"
SOURCE_POINTER = "d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a"
SOURCE_MANIFEST = "cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519"
SOURCE_DB = "1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8"
CANDIDATE = "bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb"
MIGRATION_MANIFEST = "90754472d5c15012e1caecf73cec272f3339bb6bc22ef2f6b1c3bb6b3b77649c"
ACL = "5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _db(path: Path, expected_hash: str, version: int) -> dict:
    _assert(sha256_file(path) == expected_hash, "SHA do banco diverge")
    validation = _sqlite_validate(path)
    uri = "file:" + path.resolve(strict=True).as_posix() + "?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as connection:
        observed = connection.execute("PRAGMA user_version").fetchone()[0]
    _assert(observed == version, "user_version diverge")
    return {**validation, "user_version": observed}


def _runtime() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "ClinicaGabriela" / "runtime"


def _source(runtime: Path) -> tuple[OperationalPointer, Path, Path]:
    pointer_path = runtime / "operational-pointer.json"
    _assert(sha256_file(pointer_path) == SOURCE_POINTER, "pointer Generation 8 diverge")
    pointer = read_pointer(pointer_path)
    _assert(pointer.generation == 8 and pointer.state == "canonical", "Generation 8 nao e authoritative")
    _assert(pointer.runtime_manifest_checksum_sha256 == SOURCE_MANIFEST and
            pointer.database_checksum_sha256 == SOURCE_DB and
            pointer.schema_version == SCHEMA_VERSION, "envelope da fonte diverge")
    manifest = runtime / "runtime-manifests" / f"runtime-manifest-{SOURCE_MANIFEST}.json"
    _assert(sha256_file(manifest) == SOURCE_MANIFEST, "manifest da fonte diverge")
    entries = _load(manifest)["entries"]
    _assert(len(entries) == 128 and len({e["path"] for e in entries}) == 128,
            "inventario da fonte diverge")
    source = Path(pointer.database_path).resolve(strict=True)
    _db(source, SOURCE_DB, 5)
    _assert(not (runtime / "maintenance.lock").exists(), "maintenance lock inesperado")
    return pointer, source, manifest


def _code_files(source_manifest: Path) -> list[str]:
    previous = {entry["path"] for entry in _load(source_manifest)["entries"]}
    current = {p.relative_to(ROOT).as_posix() for base in ("app", "backend")
               for p in (ROOT / base).rglob("*.py")}
    current.update({"main.py", "requirements.txt", "scripts/spec005_operational_promotion.py"})
    current.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "scripts").glob("*.py"))
    current.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "scripts").glob("*.ps1"))
    selected = previous | current
    missing = sorted(relative for relative in selected if not (ROOT / relative).is_file())
    _assert(not missing, "arquivo historico do inventario runtime ausente")
    return sorted(selected)


def _code_digest(files: list[str]) -> str:
    return hashlib.sha256(_canonical_bytes({relative: sha256_file(ROOT / relative)
                                            for relative in files})).hexdigest()


def inspect(runtime: Path) -> dict:
    _assert(PLAN.is_file() and E011.is_file() and E012.is_file(), "Evidence obrigatoria ausente")
    e011 = _load(E011)
    review = E012.read_text(encoding="utf-8")
    _assert("QUALITY_GATE_PASS" in review and "11/11" in review and "12/12" in review,
            "E012 PASS nao comprovado")
    _assert("BLOCKERS=0; MAJORS=0" in review, "E012 findings divergem")
    _assert("HUMAN de promocao: GRANTED" in PLAN.read_text(encoding="utf-8") or
            "Autoridade HUMAN de promoção: GRANTED" in PLAN.read_text(encoding="utf-8"),
            "autorizacao HUMAN posterior ausente")
    _assert(e011["candidate_sha256"] == CANDIDATE and
            e011["source_identity_sha256"] == "4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe",
            "E011 identity diverge")
    _assert(e011["migration_manifest_sha256"] == MIGRATION_MANIFEST and
            e011["transformation_identity"] == "3dfcdd7c719a89fed15a7f15da0757adfc09ae2a592ddc4d16dcd412f2223035",
            "transformation identity diverge")
    verify_manifest(ROOT, ROOT / "docs/audit/spec005-20260924-e011-migration-execution-manifest-v9.json",
                    MIGRATION_MANIFEST)
    candidate = Path(e011["candidate_path"]).resolve(strict=True)
    _db(candidate, CANDIDATE, 5)
    pointer, source, manifest = _source(runtime)
    snapshot = Path(e011["snapshot_path"]).resolve(strict=True)
    _db(snapshot, SOURCE_DB, 5)
    _assert(directory_acl_fingerprint(runtime / "generations") == ACL, "ACL aprovada diverge")
    _assert(candidate.drive.casefold() == (runtime / "generations").drive.casefold(),
            "candidate em volume diferente")
    _assert(shutil.disk_usage(runtime).free > 8 * (source.stat().st_size + candidate.stat().st_size),
            "espaco livre insuficiente")
    for relative in _code_files(manifest):
        _assert((ROOT / relative).is_file(), "runtime code incompleto")
    _assert(not (runtime / "generations" / f"canonical-spec005-v1-{CANDIDATE[:12]}.db").exists(),
            "Generation destino ja existe")
    return {"schema_version": "spec005-promotion-preflight-v1",
            "result": "PASS", "authorization": "HUMAN_GRANTED_IN_CURRENT_SESSION",
            "e012": "CLOSED_QUALITY_GATE_PASS_INDEPENDENTLY_VERIFIED",
            "candidate_sha256": CANDIDATE, "candidate_path": str(candidate),
            "candidate_validation": _db(candidate, CANDIDATE, 5),
            "source_generation": pointer.generation, "source_pointer_sha256": SOURCE_POINTER,
            "source_runtime_manifest_sha256": SOURCE_MANIFEST,
            "source_database_sha256": SOURCE_DB, "source_validation": _db(source, SOURCE_DB, 5),
            "source_snapshot_sha256": sha256_file(snapshot),
            "migration_manifest_sha256": MIGRATION_MANIFEST,
            "transformation_identity": e011["transformation_identity"],
            "acl_fingerprint_sha256": ACL, "maintenance_lock": "absent",
            "runtime_file_count": len(_code_files(manifest)),
            "runtime_code_digest": _code_digest(_code_files(manifest)),
            "plan_sha256": sha256_file(PLAN), "e012_sha256": sha256_file(E012),
            "e011_sha256": sha256_file(E011), "privacy_safe": True}


def _smoke(runtime: Path, database: Path) -> dict:
    os.environ.update({"CLINICA_RUNTIME_ROOT": str(runtime),
                       "CLINICA_OPERATIONAL_POINTER": str(runtime / "operational-pointer.json"),
                       "CLINICA_MAINTENANCE_LOCK": str(runtime / "maintenance.lock"),
                       "CLINICA_RUNTIME_CODE_ROOT": str(ROOT),
                       "BACKEND_VERIFY_READ_ONLY": "true", "BACKEND_RELOAD": "false",
                       "AUTH_SECRET": "spec005-promotion-read-only-smoke-key-32bytes"})
    for name in ("BACKEND_DATABASE_PATH", "BACKEND_DATA_DIR", "CLINICA_RUNTIME_MANIFEST_DIR"):
        os.environ.pop(name, None)
    from fastapi.testclient import TestClient
    from backend.main import create_app
    from backend.api.routes.auth import get_current_user
    from backend.database import session
    import backend.main as backend_main
    backend_main.license_status = lambda: {"valid": True}
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, role="admin", psychologist_id=None)
    before = sha256_file(database)
    with TestClient(app) as client:
        _assert(Path(session.DATABASE_PATH).resolve() == database.resolve(), "startup abriu DB errado")
        health = client.get("/health")
        finance = client.get("/finance/payments", params={"regime": "accrual", "start_year": 2026,
                                                        "start_month": 7, "end_year": 2026, "end_month": 8})
        guard = client.post("/finance/payments", json={})
        _assert((health.status_code, finance.status_code, guard.status_code) == (200, 200, 503),
                "smoke API/finance/write guard falhou")
    _assert(sha256_file(database) == before, "smoke alterou banco")
    return {"startup": "PASS", "health": "PASS", "finance": "PASS",
            "write_guard": "PASS", "database_unchanged": True}


def execute(runtime: Path) -> dict:
    _assert(PREFLIGHT.is_file(), "preflight Evidence ausente")
    recorded = _load(PREFLIGHT)
    _assert(recorded == inspect(runtime), "preflight Evidence ou estado diverge")
    execution = "spec005-promotion-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence = runtime / "evidence" / f"{execution}.json"
    source = Path(read_pointer(runtime / "operational-pointer.json").database_path)
    candidate = Path(recorded["candidate_path"])
    manifest = None
    promoted = None
    pointer_after = None
    stage = "PRE_FIRST_MUTATION"
    lock = None
    result = {"execution_reference": execution, "preflight_sha256": sha256_file(PREFLIGHT),
              "candidate_sha256": CANDIDATE, "source_generation": 8,
              "source_pointer_sha256": SOURCE_POINTER, "privacy_safe": True}
    try:
        # First operational mutation: lock. The runtime freeze follows under quiescence.
        lock = acquire_maintenance_lock(runtime / "maintenance.lock", execution, databases=(source,))
        stage = "MAINTENANCE_LOCK_ACQUIRED"
        _assert(sha256_file(runtime / "operational-pointer.json") == SOURCE_POINTER and
                sha256_file(source) == SOURCE_DB, "fonte mudou sob lock")
        files = _code_files(runtime / "runtime-manifests" / f"runtime-manifest-{SOURCE_MANIFEST}.json")
        manifest, manifest_hash = freeze_runtime(ROOT, files, runtime / "runtime-manifests")
        verify_runtime_manifest(ROOT, manifest, manifest_hash)
        result["new_runtime_manifest_sha256"] = manifest_hash
        stage = "RUNTIME_MANIFEST_CREATED"
        backup_dir = runtime / "backups" / f"{execution}-generation-8"
        backup_manifest = create_final_backup({"generation_8": source}, backup_dir,
                                             execution_reference=execution, lock=lock)
        result["final_backup_manifest_sha256"] = sha256_file(backup_manifest)
        _db(backup_dir / "generation_8.backup.db", SOURCE_DB, 5)
        stage = "FINAL_BACKUP_VERIFIED"
        promoted = promote_candidate(candidate, runtime / "generations", "spec005-v1",
                                     expected_checksum=CANDIDATE, acl_policy=AclPolicy(ACL), lock=lock)
        _db(promoted, CANDIDATE, 5)
        result["new_generation_database_sha256"] = CANDIDATE
        stage = "GENERATION_9_CREATED"
        _assert(sha256_file(runtime / "operational-pointer.json") == SOURCE_POINTER,
                "pointer mudou antes do CAS")
        new = OperationalPointer(9, "canonical", str(promoted), CANDIDATE, SCHEMA_VERSION,
                                 manifest_hash, SOURCE_POINTER)
        pointer_after = atomic_swap_pointer(runtime / "operational-pointer.json", new,
                                            expected_current_checksum=SOURCE_POINTER, lock=lock,
                                            history_dir=runtime / "pointer-history")
        result["pointer_after_sha256"] = pointer_after
        stage = "POINTER_SWITCHED"
        result["smoke"] = _smoke(runtime, promoted)
        stage = "POST_SWITCH_SMOKE_PASS"
    except Exception as exc:
        result.update({"result": "FAIL", "stop_stage": stage,
                       "error_type": type(exc).__name__, "error": str(exc)[:250]})
        if pointer_after is not None and lock is not None:
            try:
                result["recovery_pointer_sha256"] = rollback_pointer(
                    runtime / "operational-pointer.json", SOURCE_POINTER,
                    expected_current_checksum=pointer_after, lock=lock,
                    history_dir=runtime / "pointer-history")
                result["recovery"] = "FORWARD_POINTER_ROLLBACK_TO_GENERATION_8_DATABASE"
            except Exception as recovery_exc:
                result["recovery"] = "BLOCKED"
                result["recovery_error"] = str(recovery_exc)[:250]
        _atomic_create(evidence, _canonical_bytes(result))
        raise
    finally:
        if lock is not None:
            lock.release()

    try:
        _assert(sha256_file(runtime / "operational-pointer.json") == pointer_after,
                "pointer mudou apos smoke")
        _db(promoted, CANDIDATE, 5)
        stabilization = runtime / "backups" / f"{execution}-generation-9-stabilized"
        second = acquire_maintenance_lock(runtime / "maintenance.lock", execution + "-stabilization",
                                          databases=(promoted,))
        try:
            stable_manifest = create_final_backup({"generation_9": promoted}, stabilization,
                                                  execution_reference=execution + "-stabilization", lock=second)
        finally:
            second.release()
        result["stabilized_backup_manifest_sha256"] = sha256_file(stable_manifest)
        _db(stabilization / "generation_9.backup.db", CANDIDATE, 5)
        _source_db = Path(read_pointer(runtime / "operational-pointer.json").database_path)
        _assert(_source_db.resolve() == promoted.resolve(), "pointer final aponta outro DB")
        _assert(sha256_file(runtime / "operational-pointer.json") == pointer_after,
                "pointer final diverge")
        verify_runtime_manifest(ROOT, manifest, manifest_hash)
        result.update({"result": "PROMOTED_PENDING_FINAL_INDEPENDENT_OPERATIONAL_VERIFICATION",
                       "generation_after": 9, "rollback_readiness": "SOURCE_AND_FINAL_BACKUPS_VERIFIED",
                       "stabilization": "PASS"})
    except Exception as exc:
        result.update({"result": "FAIL_AFTER_SWITCH", "stop_stage": "STABILIZATION",
                       "error_type": type(exc).__name__, "error": str(exc)[:250]})
        recovery_lock = None
        try:
            recovery_lock = acquire_maintenance_lock(runtime / "maintenance.lock",
                                                     execution + "-recovery", databases=(source, promoted))
            result["recovery_pointer_sha256"] = rollback_pointer(
                runtime / "operational-pointer.json", SOURCE_POINTER,
                expected_current_checksum=pointer_after, lock=recovery_lock,
                history_dir=runtime / "pointer-history")
            result["recovery"] = "FORWARD_POINTER_ROLLBACK_TO_GENERATION_8_DATABASE"
        except Exception as recovery_exc:
            result["recovery"] = "BLOCKED"
            result["recovery_error"] = str(recovery_exc)[:250]
        finally:
            if recovery_lock is not None:
                recovery_lock.release()
        _atomic_create(evidence, _canonical_bytes(result))
        raise
    _atomic_create(evidence, _canonical_bytes(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "execute"))
    args = parser.parse_args()
    runtime = _runtime().resolve(strict=True)
    if args.mode == "preflight":
        payload = inspect(runtime)
        _atomic_create(PREFLIGHT, _canonical_bytes(payload))
        print(json.dumps(payload, sort_keys=True))
    else:
        print(json.dumps(execute(runtime), sort_keys=True))


if __name__ == "__main__":
    main()
