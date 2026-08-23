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
from backend.database.session import init_db
from app.utils.license import license_status


def create_app() -> FastAPI:
    init_db()
    run_light_migrations()
    seed_database()

    app = FastAPI(
        title="Marilia Gabriela Gaspar API",
        version="0.1.0",
        description="Backend FastAPI com SQLite para sistema de atendimento psicologico.",
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
