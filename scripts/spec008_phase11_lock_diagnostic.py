"""Reproduz em fixture o lifecycle de lock da Fase 11 com traceback por estágio."""

from __future__ import annotations

import argparse
import json
import shutil
import traceback
from pathlib import Path

from backend.cutover.infrastructure import (
    OperationalPointer,
    _atomic_create,
    acquire_maintenance_lock,
    sha256_file,
)
from scripts.spec008_phase11_stabilization import (
    RUNTIME_MANIFEST,
    _sidecars,
    _start_write_enabled,
    _technical_persistence_after_shutdown,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    source = args.source.resolve(strict=True)
    root = args.root.resolve(strict=False)
    root.mkdir(parents=True, exist_ok=False)
    generations = root / "generations"
    manifests = root / "runtime-manifests"
    generations.mkdir()
    manifests.mkdir()
    fixture = generations / "canonical-fixture.db"
    shutil.copyfile(source, fixture)
    shutil.copyfile(
        repository / "docs" / "audit" / f"runtime-manifest-{RUNTIME_MANIFEST}.json",
        manifests / f"runtime-manifest-{RUNTIME_MANIFEST}.json",
    )
    pointer = OperationalPointer(
        2, "canonical", str(fixture), sha256_file(fixture),
        "backend-models-v2-credential-reset", RUNTIME_MANIFEST,
        "0" * 64,
    )
    _atomic_create(root / "operational-pointer.json", pointer.bytes())
    result: dict = {"fixture": str(fixture), "before": sha256_file(fixture)}
    try:
        result["runtime"] = _start_write_enabled(repository, root, fixture)
        result["technical_persistence"] = _technical_persistence_after_shutdown(fixture)
        result["after_runtime"] = sha256_file(fixture)
        result["sidecars_after_runtime"] = _sidecars(fixture)
        from backend.database import session as database_session
        result["pool_status_after_shutdown"] = database_session.engine.pool.status()
        lock = acquire_maintenance_lock(
            root / "maintenance.lock", "phase11-lock-diagnostic", databases=(fixture,)
        )
        try:
            result["backup_window"] = "PASS"
        finally:
            lock.release()
        result["result"] = "NO_REPRODUCTION"
    except Exception as exc:
        result.update({
            "result": "REPRODUCED", "failure_type": type(exc).__name__,
            "failure_message": str(exc), "traceback": traceback.format_exc(),
            "after_failure": sha256_file(fixture), "sidecars_after_failure": _sidecars(fixture),
        })
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
