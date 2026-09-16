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
    maintenance_lock_path: Path | None = None
    pointer_path: Path | None = None
    verify_read_only: bool = False


def get_runtime_settings() -> RuntimeSettings:
    local_root = Path(os.getenv(
        "CLINICA_RUNTIME_ROOT",
        Path(os.getenv("LOCALAPPDATA", BACKEND_ROOT.parent)) / "ClinicaGabriela" / "runtime",
    )).expanduser().resolve()
    pointer_path = Path(os.getenv(
        "CLINICA_OPERATIONAL_POINTER", local_root / "operational-pointer.json"
    )).expanduser().resolve()
    maintenance_lock_path = Path(os.getenv(
        "CLINICA_MAINTENANCE_LOCK", local_root / "maintenance.lock"
    )).expanduser().resolve()
    explicit_database = os.getenv("BACKEND_DATABASE_PATH")
    explicit_data_dir = os.getenv("BACKEND_DATA_DIR")
    if explicit_database:
        database_path = Path(explicit_database).expanduser().resolve()
    elif pointer_path.exists():
        from backend.cutover.infrastructure import read_pointer, verify_runtime_manifest

        pointer = read_pointer(pointer_path)
        manifest_dir = Path(os.getenv(
            "CLINICA_RUNTIME_MANIFEST_DIR", pointer_path.parent / "runtime-manifests"
        )).expanduser().resolve()
        code_root = Path(os.getenv(
            "CLINICA_RUNTIME_CODE_ROOT", BACKEND_ROOT.parent
        )).expanduser().resolve()
        verify_runtime_manifest(
            code_root,
            manifest_dir / f"runtime-manifest-{pointer.runtime_manifest_checksum_sha256}.json",
            pointer.runtime_manifest_checksum_sha256,
        )
        database_path = Path(pointer.database_path).resolve()
    else:
        fallback_dir = Path(explicit_data_dir).expanduser() if explicit_data_dir else BACKEND_ROOT / "data"
        database_path = (fallback_dir / "clinica_api.db").resolve()
    data_dir = Path(explicit_data_dir or database_path.parent).expanduser().resolve()
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
    verify_read_only = os.getenv("BACKEND_VERIFY_READ_ONLY", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }
    return RuntimeSettings(
        data_dir, database_path, host, port, reload_enabled,
        maintenance_lock_path, pointer_path, verify_read_only,
    )


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
