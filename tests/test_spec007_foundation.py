"""Smoke tests da foundation transversal da SPEC-007."""

from pathlib import Path
import os
from urllib.parse import quote

import pytest


@pytest.mark.unit
@pytest.mark.smoke
def test_foundation_exposes_isolated_synthetic_fixtures(
    isolated_database_path: Path,
    synthetic_user,
    synthetic_patient,
    synthetic_appointment,
):
    assert isolated_database_path.parent.name.startswith("clinica-gabriela-pytest-")
    assert isolated_database_path.suffix == ".db"
    assert synthetic_user.username.endswith(".synthetic")
    assert synthetic_patient.email.endswith("@example.invalid")
    assert synthetic_appointment.status == "scheduled"


@pytest.mark.unit
def test_foundation_rejects_path_outside_isolated_root(
    isolated_test_root: Path,
):
    from tests.support.runtime_guard import assert_isolated_path

    with pytest.raises(AssertionError, match="fora da raiz isolada"):
        assert_isolated_path(
            Path(__file__).resolve(),
            isolated_test_root,
            Path(__file__).resolve().parents[1],
        )


@pytest.mark.unit
@pytest.mark.smoke
def test_runtime_guard_blocks_equivalent_windows_file_uris(monkeypatch):
    import conftest as foundation_conftest

    operational = foundation_conftest._OPERATIONAL_DATABASE
    uri_variants = (
        operational.as_uri(),
        "file://" + str(operational).replace("\\", "/"),
        "file:" + str(operational).replace("\\", "/"),
        "file:/" + str(operational).replace("\\", "/"),
        operational.as_uri().replace("%20", " ").upper(),
        "file:" + quote(str(operational).replace("\\", "/"), safe="/:"),
    )

    def forbidden_connect(*args, **kwargs):
        raise AssertionError("filesystem access should not be reached")

    monkeypatch.setattr(foundation_conftest, "_ORIGINAL_SQLITE_CONNECT", forbidden_connect)
    for database in uri_variants:
        with pytest.raises(RuntimeError):
            foundation_conftest._guarded_sqlite_connect(database)


@pytest.mark.unit
def test_runtime_guard_canonicalizes_path_matrix(monkeypatch):
    import conftest as foundation_conftest
    from tests.support.runtime_guard import canonicalize_sqlite_target

    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root)
    operational = foundation_conftest._OPERATIONAL_DATABASE
    variants = (
        str(operational),
        str(operational).replace("\\", "/"),
        str(operational).upper(),
        str(Path("backend") / "data" / ".." / "data" / "clinica_api.db"),
        "file:" + quote(str(operational).replace("\\", "/"), safe="/:"),
    )
    expected = os.path.normcase(str(operational))
    for database in variants:
        target, _, _ = canonicalize_sqlite_target(database)
        assert target is not None
        assert os.path.normcase(str(target)) == expected


@pytest.mark.unit
def test_runtime_guard_parses_synthetic_unc_uri_without_access():
    from tests.support.runtime_guard import canonicalize_sqlite_target

    target, _, is_file_uri = canonicalize_sqlite_target(
        "file://server/share/Synthetic%20Folder/fixture.db"
    )
    assert target is not None
    assert str(target).lower().endswith("synthetic folder\\fixture.db")
    assert is_file_uri is True


@pytest.mark.unit
def test_runtime_guard_allows_synthetic_path_and_file_uri(isolated_test_root: Path):
    from tests.support.runtime_guard import canonicalize_sqlite_target

    synthetic = isolated_test_root / "Synthetic Folder" / "fixture.db"
    for database in (synthetic, synthetic.as_uri()):
        target, _, is_file_uri = canonicalize_sqlite_target(database)
        assert target == synthetic.resolve()
        assert target.is_relative_to(isolated_test_root.resolve())
        assert is_file_uri is (database == synthetic.as_uri())


@pytest.mark.unit
def test_runtime_guard_fails_closed_for_malformed_file_uri():
    from tests.support.runtime_guard import canonicalize_sqlite_target

    target, _, is_file_uri = canonicalize_sqlite_target("file:///C:/bad/%ZZ.db")
    assert target is None
    assert is_file_uri is True
