"""Prova read-only da fonte Generation 8 com checkout histórico isolado.

Reconstrói apenas arquivos cujo SHA coincide com o manifest operacional. A cópia
temporária é descartada ao sair; não há candidato nem cópia de dados de pacientes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from backend.cutover.infrastructure import sha256_file
from backend.cutover.spec005_execution_identity import verify_source


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_POINTER = "d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a"


def main() -> None:
    runtime = Path(os.environ["LOCALAPPDATA"]) / "ClinicaGabriela" / "runtime"
    pointer = runtime / "operational-pointer.json"
    if sha256_file(pointer) != EXPECTED_POINTER:
        raise RuntimeError("pointer operacional divergente")
    pointer_data = json.loads(pointer.read_text(encoding="utf-8"))
    manifests = runtime / "runtime-manifests"
    manifest = manifests / f"runtime-manifest-{pointer_data['runtime_manifest_checksum_sha256']}.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    commit = payload["source_commit"]
    with tempfile.TemporaryDirectory(prefix="d00511-old-") as name:
        historical = Path(name)
        for entry in payload["entries"]:
            path = entry["path"]
            active = ROOT / path
            current = active.read_bytes() if active.is_file() else b""
            original = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT,
                                      capture_output=True, check=True).stdout
            candidates = (current, original, re.sub(rb"(?<!\r)\n", b"\r\n", original))
            matching = [data for data in candidates if hashlib.sha256(data).hexdigest() == entry["sha256"]]
            if not matching:
                raise RuntimeError(f"baseline histórica não reproduzível: {path}")
            target = historical / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(matching[0])
        source = verify_source(pointer, manifests, historical, Path(pointer_data["database_path"]),
                               EXPECTED_POINTER)
    print(json.dumps({"result": "SOURCE_IDENTITY_PASS", "entry_count": len(payload["entries"]),
                      "source_identity": source}, sort_keys=True))


if __name__ == "__main__":
    main()
