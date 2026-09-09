import pytest

from app.views.main_view import can_access_module


@pytest.mark.parametrize(
    ("role", "module", "allowed"),
    [
        ("psychologist", "clinical_records", True),
        ("psychologist", "settings", False),
        ("admin", "clinical_records", False),
        ("admin", "settings", True),
        ("reception", "clinical_records", False),
        ("reception", "settings", False),
    ],
)
def test_desktop_module_permissions(role, module, allowed):
    assert can_access_module(role, module) is allowed
