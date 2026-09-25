"""Identidades independentes da fonte operacional e do migrador D005-11.

Este módulo só lê a fonte e o código. Build escreve exclusivamente um manifesto
em destino explícito; verify e preflight não escrevem qualquer artefato.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

from backend.cutover.infrastructure import CutoverError, SCHEMA_VERSION, read_pointer, sha256_file, verify_runtime_manifest


SCHEMA = "spec005-migration-execution-v1"
CONTRACT = "SPEC-005/D005-09+D005-10+D005-11"
TRANSFORMATION_CONTRACT = "SPEC-005/D005-09+D005-10+D005-11+D005-12"
HISTORICAL_RECOVERY = "PARTIAL_111_OF_128"
ENTRYPOINTS = ("scripts/spec005_candidate_migration.py", "scripts/spec005_d00511_identity.py",
               "backend/migration/spec005.py", "backend/cutover/spec005_execution_identity.py",
               "scripts/spec005_provision_e011_review.py")


class IdentityBlock(ValueError):
    """Uma identidade ou seu vínculo não foi comprovado."""


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def _module_file(root: Path, module: str) -> Path | None:
    base = root.joinpath(*module.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def inventory(root: Path) -> list[str]:
    """Fecha imports Python locais a partir dos entrypoints, inclusive packages."""
    root = root.resolve(strict=True)
    pending = list(ENTRYPOINTS)
    seen: set[str] = set()
    while pending:
        relative = pending.pop()
        if relative in seen:
            continue
        path = (root / relative).resolve(strict=True)
        if root not in path.parents or path.suffix != ".py":
            raise IdentityBlock("dependência fora da raiz ou não Python")
        seen.add(relative)
        try:
            tree = ast.parse(path.read_bytes(), filename=relative)
        except (SyntaxError, OSError) as exc:
            raise IdentityBlock("dependência Python inválida") from exc
        parts = Path(relative).with_suffix("").parts
        package = parts if parts[-1] == "__init__" else parts[:-1]
        modules: list[tuple[str, bool]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend((alias.name, True) for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    prefix = package[:len(package) - node.level + 1]
                    base = ".".join((*prefix, *(node.module.split(".") if node.module else ())))
                else:
                    base = node.module or ""
                modules.append((base, True))
                modules.extend((base + "." + alias.name, False) for alias in node.names)
        for module, required in modules:
            if not module.startswith(("backend.", "scripts.")) and module not in {"backend", "scripts"}:
                continue
            file = _module_file(root, module)
            if file is not None:
                pending.append(file.relative_to(root).as_posix())
            elif required and module != "scripts":
                raise IdentityBlock("dependência local ausente")
            # `from package import symbol`: symbol pode ser atributo, não módulo.
            components = module.split(".")
            for count in range(1, len(components)):
                init = root.joinpath(*components[:count], "__init__.py")
                if init.is_file():
                    pending.append(init.relative_to(root).as_posix())
    return sorted(seen)


def _payload(root: Path) -> dict:
    return {"schema_version": SCHEMA, "contract_identity": TRANSFORMATION_CONTRACT,
            "decision_identity": "D005-12/1", "entrypoints": list(ENTRYPOINTS),
            "entries": [{"path": relative, "sha256": sha256_file(root / relative)}
                        for relative in inventory(root)]}


def build_manifest(root: Path, destination: Path) -> str:
    """Cria uma baseline uma única vez; destino existente nunca é substituído."""
    root = root.resolve(strict=True)
    destination = destination.resolve(strict=False)
    if root == destination or root in destination.parents and destination.suffix == ".py":
        raise IdentityBlock("destino de manifesto inválido")
    data = canonical_bytes(_payload(root))
    with destination.open("xb") as stream:
        stream.write(data)
    return hashlib.sha256(data).hexdigest()


def verify_manifest(root: Path, manifest: Path, expected_sha256: str) -> str:
    """Compara bytes do manifesto e closure recalculada; não regenera baseline."""
    try:
        raw = manifest.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise IdentityBlock("hash do manifesto migrador diverge")
        recorded = json.loads(raw)
        if raw != canonical_bytes(recorded) or recorded != _payload(root.resolve(strict=True)):
            raise IdentityBlock("código, dependência ou contrato migrador diverge")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise IdentityBlock("manifesto migrador não verificável") from exc
    return expected_sha256


def verify_source(pointer_path: Path, manifest_dir: Path, historical_code_root: Path,
                  snapshot: Path, expected_pointer_sha256: str) -> dict:
    """Prova a Generation apontada usando a baseline histórica, nunca o código novo."""
    try:
        if sha256_file(pointer_path) != expected_pointer_sha256:
            raise IdentityBlock("pointer diverge")
        pointer = read_pointer(pointer_path)
        if pointer.state != "canonical" or pointer.generation != 8:
            raise IdentityBlock("Generation não canônica")
        manifest = manifest_dir / f"runtime-manifest-{pointer.runtime_manifest_checksum_sha256}.json"
        verify_runtime_manifest(historical_code_root, manifest, pointer.runtime_manifest_checksum_sha256)
        if sha256_file(snapshot) != pointer.database_checksum_sha256:
            raise IdentityBlock("snapshot diverge do banco apontado")
        db = Path(pointer.database_path)
        if any(Path(str(db) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise IdentityBlock("sidecar pendente")
        if (pointer_path.parent / "maintenance.lock").exists():
            raise IdentityBlock("maintenance lock presente")
        uri = "file:" + quote(snapshot.resolve(strict=True).as_posix(), safe="/:") + "?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise IdentityBlock("integridade da fonte falhou")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise IdentityBlock("FK da fonte falhou")
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        return {"source_generation": pointer.generation, "pointer_sha256": expected_pointer_sha256,
                "runtime_manifest_sha256": pointer.runtime_manifest_checksum_sha256,
                "database_sha256": pointer.database_checksum_sha256,
                "schema_identity": pointer.schema_version, "user_version": user_version,
                "integrity_check": "ok", "foreign_key_violations": 0}
    except (OSError, ValueError, sqlite3.Error, CutoverError) as exc:
        raise IdentityBlock("identidade operacional não verificável") from exc


def verify_persisted_source(pointer_path: Path, manifest_dir: Path, snapshot: Path, *,
                            expected_pointer_sha256: str, expected_manifest_sha256: str,
                            expected_database_sha256: str, expected_generation: int = 8) -> dict:
    """D005-12: prove persisted artifacts without claiming a 128/128 code freeze."""
    try:
        if sha256_file(pointer_path) != expected_pointer_sha256:
            raise IdentityBlock("pointer diverge")
        pointer = read_pointer(pointer_path)
        if (pointer.generation != expected_generation or pointer.state != "canonical"
                or pointer.schema_version != SCHEMA_VERSION
                or pointer.runtime_manifest_checksum_sha256 != expected_manifest_sha256
                or pointer.database_checksum_sha256 != expected_database_sha256):
            raise IdentityBlock("identidade da Generation diverge")
        manifest = manifest_dir / f"runtime-manifest-{expected_manifest_sha256}.json"
        if sha256_file(manifest) != expected_manifest_sha256:
            raise IdentityBlock("manifest operacional diverge")
        payload = json.loads(manifest.read_bytes())
        entries = payload["entries"]
        if (payload["schema_version"] != SCHEMA_VERSION or len(entries) != 128
                or len({entry["path"] for entry in entries}) != 128
                or any(len(entry["sha256"]) != 64 for entry in entries)):
            raise IdentityBlock("inventario historico invalido")
        database = Path(pointer.database_path)
        if (sha256_file(database) != expected_database_sha256
                or sha256_file(snapshot) != expected_database_sha256):
            raise IdentityBlock("banco apontado ou snapshot diverge")
        if any(Path(str(database) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise IdentityBlock("sidecar pendente")
        if (pointer_path.parent / "maintenance.lock").exists():
            raise IdentityBlock("maintenance lock presente")
        uri = "file:" + quote(database.resolve(strict=True).as_posix(), safe="/:") + "?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise IdentityBlock("integridade da fonte falhou")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise IdentityBlock("FK da fonte falhou")
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        return {"authority": "PERSISTED_OPERATIONAL_SOURCE_IDENTITY/D005-12",
                "source_generation": pointer.generation, "source_state": pointer.state,
                "pointer_sha256": expected_pointer_sha256,
                "runtime_manifest_sha256": expected_manifest_sha256,
                "database_sha256": expected_database_sha256,
                "schema_identity": pointer.schema_version, "user_version": user_version,
                "integrity_check": "ok", "foreign_key_violations": 0,
                "historical_runtime_bytes_verification": HISTORICAL_RECOVERY,
                "historical_runtime_baseline_recovery": "PARTIAL"}
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error, CutoverError) as exc:
        raise IdentityBlock("identidade operacional persistida nao verificavel") from exc


def bind_transformation(source: dict, migration_sha256: str, *,
                        expected_source: dict, expected_migration_sha256: str,
                        expected_transformation_sha256: str | None = None,
                        expected_contract_identity: str | None = None,
                        e011_authorization_gate_sha256: str | None = None) -> str:
    if source != expected_source or migration_sha256 != expected_migration_sha256:
        raise IdentityBlock("binding source/migration diverge")
    if len(migration_sha256) != 64 or any(c not in "0123456789abcdef" for c in migration_sha256):
        raise IdentityBlock("identidade migradora inválida")
    if source.get("authority") == "PERSISTED_OPERATIONAL_SOURCE_IDENTITY/D005-12":
        if (source.get("historical_runtime_bytes_verification") != HISTORICAL_RECOVERY
                or source.get("historical_runtime_baseline_recovery") != "PARTIAL"):
            raise IdentityBlock("alegacao historica inconsistente")
        contract = TRANSFORMATION_CONTRACT
        decisions = ["D005-09", "D005-10", "D005-11", "D005-12"]
        if e011_authorization_gate_sha256 is not None:
            if (len(e011_authorization_gate_sha256) != 64 or
                    any(c not in "0123456789abcdef" for c in e011_authorization_gate_sha256)):
                raise IdentityBlock("gate E011 invalido")
            decisions.append("D005-13")
    elif "historical_runtime_bytes_verification" not in source:
        contract = CONTRACT
        decisions = ["D005-09", "D005-10", "D005-11"]
    else:
        raise IdentityBlock("autoridade da fonte invalida")
    if expected_contract_identity is not None and expected_contract_identity != contract:
        raise IdentityBlock("identidade do contrato diverge")
    payload = {"schema_version": "spec005-transformation-v1", "contract_identity": contract,
               "decisions": decisions, "source": source,
               "migration_manifest_sha256": migration_sha256}
    if e011_authorization_gate_sha256 is not None:
        payload["e011_authorization_gate_sha256"] = e011_authorization_gate_sha256
    result = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    if expected_transformation_sha256 is not None and result != expected_transformation_sha256:
        raise IdentityBlock("identidade da transformação diverge")
    return result
