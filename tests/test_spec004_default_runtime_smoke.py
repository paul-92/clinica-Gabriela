import os
import subprocess
import sys
from pathlib import Path

from backend.cutover.infrastructure import SCHEMA_VERSION, OperationalPointer, freeze_runtime, sha256_file


def test_operational_default_discovers_pointer_manifest_and_database_without_forbidden_overrides(tmp_path):
    repository = Path(__file__).resolve().parents[1]
    localappdata = tmp_path / "localappdata"
    runtime = localappdata / "ClinicaGabriela" / "runtime"
    generations = runtime / "generations"
    generations.mkdir(parents=True)
    database = generations / "candidate-v5.db"
    database.write_bytes(b"runtime-equivalent-database-canary")
    _, manifest_hash = freeze_runtime(repository, ["backend/config.py"], runtime / "runtime-manifests")
    pointer = OperationalPointer(8, "canonical", str(database.resolve()), sha256_file(database),
                                 SCHEMA_VERSION, manifest_hash)
    (runtime / "operational-pointer.json").write_bytes(pointer.bytes())
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(localappdata)
    for forbidden in ("CLINICA_RUNTIME_ROOT", "CLINICA_OPERATIONAL_POINTER", "CLINICA_RUNTIME_CODE_ROOT",
                      "CLINICA_RUNTIME_MANIFEST_DIR", "BACKEND_DATABASE_PATH", "BACKEND_DATA_DIR"):
        env.pop(forbidden, None)
    command = (
        "from backend.config import get_runtime_settings; "
        "s=get_runtime_settings(); "
        "print(s.pointer_path); print(s.database_path)"
    )
    result = subprocess.run([sys.executable, "-c", command], cwd=repository, env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert str((runtime / "operational-pointer.json").resolve()) in result.stdout
    assert str(database.resolve()) in result.stdout
