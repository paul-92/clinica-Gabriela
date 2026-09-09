from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.api.routes import (
    appointments,
    auth,
    clinical_records,
    dashboard,
    finance,
    license,
    patients,
    psychologists,
    settings,
)
from backend.database.seed import seed_database
from backend.database.migrations import run_light_migrations
from backend.database.session import configure_database, init_db
from backend.config import get_runtime_settings
from app.utils.license import license_status


def bootstrap_backend(settings=None):
    runtime_settings = settings or get_runtime_settings()
    runtime_settings.data_dir.mkdir(parents=True, exist_ok=True)
    runtime_settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    database = configure_database(runtime_settings)
    init_db(database.engine)
    run_light_migrations(database.engine)
    seed_database(database.session_factory)
    return database


@asynccontextmanager
async def lifespan(_app):
    database = bootstrap_backend()
    try:
        yield
    finally:
        database.engine.dispose()


def create_app(*, lifespan_context=lifespan) -> FastAPI:

    app = FastAPI(
        title="Marilia Gabriela Gaspar API",
        version="0.1.0",
        description="Backend FastAPI com SQLite para sistema de atendimento psicologico.",
        lifespan=lifespan_context,
    )

    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "ok"}

    @app.middleware("http")
    async def license_guard(request: Request, call_next):
        public_paths = {"/health", "/license/status", "/docs", "/openapi.json", "/redoc"}
        if request.url.path not in public_paths:
            status = license_status()
            if not status["valid"]:
                return JSONResponse(status_code=403, content={"detail": status})
        return await call_next(request)

    app.include_router(auth.router)
    app.include_router(license.router)
    app.include_router(dashboard.router)
    app.include_router(patients.router)
    app.include_router(psychologists.router)
    app.include_router(appointments.router)
    app.include_router(clinical_records.router)
    app.include_router(finance.router)
    app.include_router(settings.router)
    return app


app = create_app()


def main():
    import uvicorn

    settings = get_runtime_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


if __name__ == "__main__":
    main()
