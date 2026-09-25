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

import pytest

from tests.support.factories import (
    make_synthetic_appointment,
    make_synthetic_patient,
    make_synthetic_user,
)
from tests.support.runtime_guard import assert_isolated_path
from tests.support.runtime_guard import canonicalize_sqlite_target


_TEST_RUNTIME_ROOT = Path(tempfile.mkdtemp(prefix="clinica-gabriela-pytest-"))
_ORIGINAL_ENV = {
    name: os.environ.get(name)
    for name in ("BACKEND_DATA_DIR", "BACKEND_DATABASE_PATH")
}
_OPERATIONAL_DATABASE = (
    Path(__file__).resolve().parents[1] / "backend" / "data" / "clinica_api.db"
).resolve()
_ORIGINAL_SQLITE_CONNECT = sqlite3.connect
_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolved_sqlite_target(database) -> tuple[Path | None, str]:
    target, raw, _ = canonicalize_sqlite_target(database)
    return target, raw


def _guarded_sqlite_connect(database, *args, **kwargs):
    target, raw, is_file_uri = canonicalize_sqlite_target(database)
    if is_file_uri and target is None:
        raise RuntimeError("A suíte recusou uma file URI malformada.")
    explicitly_immutable_read_only = "mode=ro" in raw and "immutable=1" in raw
    same_operational_target = target is not None and os.path.normcase(str(target)) == os.path.normcase(str(_OPERATIONAL_DATABASE))
    if same_operational_target and not explicitly_immutable_read_only:
        raise RuntimeError(
            "A suíte recusou abertura write-capable do banco operacional real."
        )
    return _ORIGINAL_SQLITE_CONNECT(database, *args, **kwargs)

os.environ["BACKEND_DATA_DIR"] = str(_TEST_RUNTIME_ROOT)
os.environ["BACKEND_DATABASE_PATH"] = str(_TEST_RUNTIME_ROOT / "clinica_api.test.db")
sqlite3.connect = _guarded_sqlite_connect


def pytest_configure(config) -> None:
    """Valida a barreira mínima antes da coleta da suíte."""

    del config
    assert_isolated_path(
        Path(os.environ["BACKEND_DATABASE_PATH"]),
        _TEST_RUNTIME_ROOT,
        _PROJECT_ROOT,
    )


@pytest.fixture(scope="session")
def isolated_test_root() -> Path:
    """Raiz temporária compartilhada apenas por estado sintético da sessão."""

    return _TEST_RUNTIME_ROOT


@pytest.fixture
def isolated_database_path(isolated_test_root: Path) -> Path:
    path = isolated_test_root / "fixture.db"
    return assert_isolated_path(path, isolated_test_root, _PROJECT_ROOT)


@pytest.fixture
def synthetic_user():
    return make_synthetic_user()


@pytest.fixture
def synthetic_patient():
    return make_synthetic_patient()


@pytest.fixture
def synthetic_appointment():
    return make_synthetic_appointment()


def pytest_unconfigure(config) -> None:
    del config
    sqlite3.connect = _ORIGINAL_SQLITE_CONNECT
    for name, value in _ORIGINAL_ENV.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    shutil.rmtree(_TEST_RUNTIME_ROOT, ignore_errors=True)
