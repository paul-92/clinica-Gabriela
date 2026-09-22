import subprocess
import sys
from pathlib import Path

import pytest

from app.controllers.finance_controller import FinanceController
from app.repositories.finance_repository import FinanceRepository, LegacyFinanceAuthorityDisabled
from app.services.finance_service import FinanceService


class FakeCanonicalApi:
    def __init__(self):
        self.paths = []

    def get(self, path):
        self.paths.append(path)
        return {
            "regime": "cash",
            "start": "2031-01-01",
            "end": "2031-02-01",
            "income_cents": 123,
            "receivable_cents": 0,
            "expense_cents": 23,
            "balance_cents": 100,
        }


def test_e009_tkinter_finance_reads_canonical_api_only():
    api = FakeCanonicalApi()
    result = FinanceController(api).summary()

    assert result["income_cents"] == 123
    assert len(api.paths) == 1
    assert api.paths[0].startswith("/finance/summary?start=")
    assert "regime=cash" in api.paths[0]


def test_e009_default_desktop_import_path_does_not_activate_legacy_finance_model():
    repository = Path(__file__).resolve().parents[1]
    code = (
        "import sys; import main; "
        "assert 'app.models.finance' not in sys.modules; "
        "assert 'app.services.finance_service' not in sys.modules; "
        "assert 'app.repositories.finance_repository' not in sys.modules"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=repository, capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr


def test_e009_legacy_seed_and_schema_activation_have_no_financial_write_path():
    repository = Path(__file__).resolve().parents[1]
    seed_source = (repository / "app" / "database" / "seed.py").read_text(encoding="utf-8")
    session_source = (repository / "app" / "database" / "session.py").read_text(encoding="utf-8")

    assert "app.models.finance" not in seed_source
    assert "Payment(" not in seed_source
    assert "Expense(" not in seed_source
    assert "finance," not in session_source


def test_e009_legacy_repository_and_calculator_are_explicitly_disabled():
    with pytest.raises(LegacyFinanceAuthorityDisabled):
        FinanceRepository(object())
    with pytest.raises(LegacyFinanceAuthorityDisabled):
        FinanceService(object())
