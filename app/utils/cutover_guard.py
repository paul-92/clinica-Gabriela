from pathlib import Path

from backend.config import get_runtime_settings
from backend.cutover.infrastructure import maintenance_active, read_pointer


def assert_legacy_desktop_allowed() -> None:
    settings = get_runtime_settings()
    if settings.maintenance_lock_path and maintenance_active(settings.maintenance_lock_path):
        raise RuntimeError("Desktop legado bloqueado por maintenance lock.")
    pointer_path = settings.pointer_path
    if pointer_path and pointer_path.exists():
        pointer = read_pointer(pointer_path)
        if pointer.state == "canonical":
            raise RuntimeError("Desktop legado bloqueado apos promocao canonica.")
