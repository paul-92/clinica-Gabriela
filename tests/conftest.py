"""Barreira de segurança: a suíte nunca usa bancos operacionais por fallback.

Este arquivo é carregado antes da coleta dos módulos de teste. Assim, os globais de
``backend.database.session`` também nascem apontando para uma raiz descartável.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path


_TEST_RUNTIME_ROOT = Path(tempfile.mkdtemp(prefix="clinica-gabriela-pytest-"))
_ORIGINAL_ENV = {
    name: os.environ.get(name)
    for name in ("BACKEND_DATA_DIR", "BACKEND_DATABASE_PATH")
}
_OPERATIONAL_DATABASE = (
    Path(__file__).resolve().parents[1] / "backend" / "data" / "clinica_api.db"
).resolve()
_ORIGINAL_SQLITE_CONNECT = sqlite3.connect


def _resolved_sqlite_target(database) -> tuple[Path | None, str]:
    try:
        raw = os.fspath(database)
    except TypeError:
        return None, ""
    if isinstance(raw, bytes):
        raw = os.fsdecode(raw)
    value = raw
    if value.startswith("file:"):
        value = value[5:].split("?", 1)[0]
        if value.startswith("/") and len(value) > 2 and value[2] == ":":
            value = value[1:]
    if value == ":memory:" or not value:
        return None, raw
    try:
        return Path(value).expanduser().resolve(strict=False), raw
    except OSError:
        return None, raw


def _guarded_sqlite_connect(database, *args, **kwargs):
    target, raw = _resolved_sqlite_target(database)
    explicitly_immutable_read_only = "mode=ro" in raw and "immutable=1" in raw
    if target == _OPERATIONAL_DATABASE and not explicitly_immutable_read_only:
        raise RuntimeError(
            "A suíte recusou abertura write-capable do banco operacional real."
        )
    return _ORIGINAL_SQLITE_CONNECT(database, *args, **kwargs)

os.environ["BACKEND_DATA_DIR"] = str(_TEST_RUNTIME_ROOT)
os.environ["BACKEND_DATABASE_PATH"] = str(_TEST_RUNTIME_ROOT / "clinica_api.test.db")
sqlite3.connect = _guarded_sqlite_connect


def pytest_unconfigure(config) -> None:
    del config
    sqlite3.connect = _ORIGINAL_SQLITE_CONNECT
    for name, value in _ORIGINAL_ENV.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    shutil.rmtree(_TEST_RUNTIME_ROOT, ignore_errors=True)
