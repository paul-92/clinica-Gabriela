from dataclasses import dataclass
from threading import Lock

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import RuntimeSettings, get_runtime_settings


Base = declarative_base()


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        if cursor.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise RuntimeError("Nao foi possivel habilitar Foreign Keys no SQLite.")
    finally:
        cursor.close()


@dataclass(frozen=True)
class DatabaseRuntime:
    engine: object
    session_factory: object


def create_database_runtime(settings: RuntimeSettings) -> DatabaseRuntime:
    if settings.verify_read_only:
        uri_path = settings.database_path.as_posix()
        database_url = f"sqlite:///file:{uri_path}?mode=ro&immutable=1&uri=true"
    else:
        database_url = f"sqlite:///{settings.database_path}"
    runtime_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=False,
        future=True,
    )
    event.listen(runtime_engine, "connect", _enable_sqlite_foreign_keys)
    runtime_sessions = sessionmaker(
        bind=runtime_engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    return DatabaseRuntime(runtime_engine, runtime_sessions)


_default_settings = get_runtime_settings()
_default_runtime = create_database_runtime(_default_settings)
engine = _default_runtime.engine
SessionLocal = _default_runtime.session_factory
DATA_DIR = _default_settings.data_dir
DATABASE_PATH = _default_settings.database_path
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
_runtime_lock = Lock()
_active_sessions = 0


def configure_database(settings: RuntimeSettings) -> DatabaseRuntime:
    global engine, SessionLocal, DATA_DIR, DATABASE_PATH, DATABASE_URL
    with _runtime_lock:
        if _active_sessions:
            raise RuntimeError("Nao e possivel reconfigurar o banco com sessoes ativas.")
        previous_engine = engine
        runtime = create_database_runtime(settings)
        engine = runtime.engine
        SessionLocal = runtime.session_factory
        DATA_DIR = settings.data_dir
        DATABASE_PATH = settings.database_path
        DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    previous_engine.dispose()
    return runtime


def init_db(bind=None):
    from backend.models import (  # noqa: F401
        appointment,
        clinical_record,
        finance,
        patient,
        psychologist,
        settings,
        user,
    )

    Base.metadata.create_all(bind=bind or engine)


def get_db():
    global _active_sessions
    with _runtime_lock:
        sessions = SessionLocal
        _active_sessions += 1
    try:
        db = sessions()
    except Exception:
        with _runtime_lock:
            _active_sessions -= 1
        raise
    try:
        yield db
    finally:
        try:
            db.close()
        finally:
            with _runtime_lock:
                _active_sessions -= 1
