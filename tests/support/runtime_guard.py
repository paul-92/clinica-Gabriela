"""Guardas para impedir que fixtures apontem para o runtime operacional."""

from __future__ import annotations

import os
import re
from urllib.parse import unquote, urlsplit
from pathlib import Path


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def operational_roots(project_root: Path) -> tuple[Path, ...]:
    roots = {
        (project_root / "data").resolve(),
        (project_root / "backend" / "data").resolve(),
    }
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        roots.add((Path(local_appdata) / "ClinicaGabriela").resolve())
    return tuple(sorted(roots, key=str))


def assert_isolated_path(path: Path, isolated_root: Path, project_root: Path) -> Path:
    """Retorna o path resolvido ou falha antes de qualquer uso perigoso."""

    resolved_path = path.expanduser().resolve()
    resolved_isolated_root = isolated_root.expanduser().resolve()
    if not _is_within(resolved_path, resolved_isolated_root):
        raise AssertionError(
            f"recurso de teste fora da raiz isolada: {resolved_path}"
        )
    if any(_is_within(resolved_path, root) for root in operational_roots(project_root)):
        raise AssertionError(
            f"recurso de teste aponta para raiz operacional: {resolved_path}"
        )
    return resolved_path


def canonicalize_sqlite_target(database) -> tuple[Path | None, str, bool]:
    """Canonicaliza paths SQLite e file URIs sem acessar o filesystem.

    O terceiro item indica que a entrada era uma URI ``file:``. URI local
    malformada retorna ``None`` para permitir que o caller falhe fechado.
    """

    try:
        raw = os.fspath(database)
    except TypeError:
        return None, "", False
    if isinstance(raw, bytes):
        raw = os.fsdecode(raw)

    if raw in ("", ":memory:"):
        return None, raw, False

    is_file_uri = raw.lower().startswith("file:")
    value = raw
    if is_file_uri:
        try:
            parsed = urlsplit(raw)
            if parsed.scheme.lower() != "file" or parsed.fragment:
                return None, raw, True
            netloc = _strict_unquote(parsed.netloc)
            path = _strict_unquote(parsed.path)
        except ValueError:
            return None, raw, True

        if netloc in ("", "localhost"):
            value = path
        elif len(netloc) == 2 and netloc[1] == ":":
            value = netloc + path
        else:
            value = "\\\\" + netloc + path
        if value.startswith("/") and len(value) > 2 and value[2] == ":":
            value = value[1:]
        if not value:
            return None, raw, True

    try:
        return Path(value).expanduser().resolve(strict=False), raw, is_file_uri
    except (OSError, RuntimeError):
        return None, raw, is_file_uri


def _strict_unquote(value: str) -> str:
    if re.search(r"%(?![0-9A-Fa-f]{2})", value):
        raise ValueError("percent-encoding inválido")
    return unquote(value, encoding="utf-8", errors="strict")
