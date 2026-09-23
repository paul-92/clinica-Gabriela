"""Inicializa exclusivamente o banco apontado pelo ambiente DEV validado."""

from pathlib import Path
import os

from backend.config import get_runtime_settings


def verify_dev_path() -> None:
    root = Path(os.environ["CLINICA_RUNTIME_ROOT"]).resolve()
    expected = root / "backend" / "clinica_dev.db"
    settings = get_runtime_settings()
    if (settings.database_path != expected or settings.data_dir != expected.parent
            or settings.pointer_path != root / "operational-pointer.json"
            or settings.pointer_path.exists()):
        raise RuntimeError("Resolucao de banco DEV invalida")
    if not (root / ".clinica-dev-root").is_file():
        raise RuntimeError("Marcador DEV ausente")


if __name__ == "__main__":
    verify_dev_path()
    from backend.main import bootstrap_backend

    bootstrap_backend()
    print("Banco DEV sintetico criado")
