import os
from dataclasses import dataclass
from pathlib import Path


AUTH_SECRET_ENV = "AUTH_SECRET"
BACKEND_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class RuntimeSettings:
    data_dir: Path
    database_path: Path
    host: str
    port: int
    reload: bool


def get_runtime_settings() -> RuntimeSettings:
    data_dir = Path(os.getenv("BACKEND_DATA_DIR", BACKEND_ROOT / "data")).expanduser().resolve()
    database_path = Path(
        os.getenv("BACKEND_DATABASE_PATH", data_dir / "clinica_api.db")
    ).expanduser().resolve()
    host = os.getenv("BACKEND_HOST", "127.0.0.1").strip() or "127.0.0.1"
    try:
        port = int(os.getenv("BACKEND_PORT", "8000"))
    except ValueError as exc:
        raise RuntimeError("BACKEND_PORT deve ser um numero inteiro.") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("BACKEND_PORT deve estar entre 1 e 65535.")
    reload_enabled = os.getenv("BACKEND_RELOAD", "true").strip().lower() in {
        "1", "true", "yes", "on",
    }
    return RuntimeSettings(data_dir, database_path, host, port, reload_enabled)


def get_auth_secret() -> str:
    secret = os.getenv(AUTH_SECRET_ENV)

    if not secret:
        raise RuntimeError(
            f"{AUTH_SECRET_ENV} environment variable is required"
        )

    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError(
            f"{AUTH_SECRET_ENV} must contain at least 32 bytes"
        )

    return secret
