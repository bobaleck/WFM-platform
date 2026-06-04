from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.integration import router as integration_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.wfm import router as wfm_router
from app.core.config import settings
from app.core.rbac import rbac_middleware
from app.db.seed import ensure_auth_defaults, seed_demo_data
from app.db.session import SessionLocal, engine
from app.db.migration_state import ensure_alembic_stamp
from app.db.schema import ensure_stage4_schema, ensure_stage9_schema
from app.models.integration_settings import Base
import app.models.wfm  # noqa: F401

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await rbac_middleware(request, call_next)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

if settings.app_env == "development":
    Base.metadata.create_all(bind=engine)
    ensure_stage4_schema(engine)
    ensure_stage9_schema(engine)
ensure_alembic_stamp(engine)
with SessionLocal() as db:
    ensure_auth_defaults(db)
if settings.demo_seed:
    with SessionLocal() as db:
        seed_demo_data(db)
app.include_router(integration_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(wfm_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/api/v1/version")
def version() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "environment": settings.app_env,
            "external_source": "manual",
            "onec_integration": "gateway_http",
    }


@app.get("/api/v1/modules")
def modules() -> dict[str, list[str]]:
    return {
        "modules": [
            "employees",
            "teams",
            "skills",
            "queues",
            "workload",
            "staffing_requirements",
            "schedules",
            "absences",
            "kpi_reports",
            "integrations_1c",
            "manual_contours",
        ]
    }


@app.get("/api/v1/health/db")
def db_health() -> dict[str, str]:
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "database"}
