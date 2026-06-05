from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.auth import user_permissions
from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.wfm import User


PUBLIC_PREFIXES = (
    "/health",
    "/api/v1/version",
    "/api/v1/naumen/status",
    "/api/v1/auth/login",
)


RULES: list[tuple[str, tuple[str, ...], str]] = [
    ("/api/v1/auth/me", ("GET",), "dashboard:view"),
    ("/api/v1/auth/change-password", ("POST",), "dashboard:view"),
    ("/api/v1/reports/dashboard-summary", ("GET",), "dashboard:view"),
    ("/api/v1/reports/summary", ("GET",), "dashboard:view"),
    ("/api/v1/reports/executive-summary", ("GET",), "dashboard:view"),
    ("/api/v1/reports/operations-summary", ("GET",), "dashboard:view"),
    ("/api/v1/employees/import", ("GET", "POST"), "employees:import"),
    ("/api/v1/employees/naumen", ("POST",), "employees:sync_naumen|naumen:operators:sync"),
    ("/api/v1/employees/check-all-1c-status", ("POST",), "employees:sync_1c|onec:status-check-all"),
    ("/api/v1/employees/", ("GET",), "employees:view|employees:view_stats"),
    ("/api/v1/employees/", ("PUT",), "employees:manage"),
    ("/api/v1/employees/", ("POST",), "employees:sync_1c|onec:status-check"),
    ("/api/v1/employees", ("GET",), "employees:view"),
    ("/api/v1/employees", ("POST", "PUT", "DELETE"), "employees:manage"),
    ("/api/v1/teams", ("GET",), "teams:view"),
    ("/api/v1/teams", ("POST", "PUT", "DELETE"), "teams:manage"),
    ("/api/v1/skills", ("GET",), "skills:view"),
    ("/api/v1/skills", ("POST", "PUT", "DELETE"), "skills:manage"),
    ("/api/v1/queues", ("GET",), "queues:view"),
    ("/api/v1/queues", ("POST", "PUT", "DELETE"), "queues:manage"),
    ("/api/v1/workload", ("GET",), "workload:view"),
    ("/api/v1/imports/workload-csv", ("POST",), "workload:import"),
    ("/api/v1/imports/actual-work-csv", ("POST",), "actual:import"),
    ("/api/v1/staffing", ("GET",), "staffing:view"),
    ("/api/v1/planning/calculate-staffing", ("POST",), "staffing:calculate"),
    ("/api/v1/planning/settings", ("GET",), "settings:view"),
    ("/api/v1/planning/settings", ("POST", "PUT"), "settings:manage"),
    ("/api/v1/planning/requirements", ("GET",), "staffing:view"),
    ("/api/v1/settings/app", ("GET",), "settings:view"),
    ("/api/v1/settings/app", ("PUT",), "settings:manage"),
    ("/api/v1/contours/current", ("GET", "PUT"), "dashboard:view"),
    ("/api/v1/contours", ("GET",), "dashboard:view"),
    ("/api/v1/contours", ("POST", "PUT"), "settings:manage"),
    ("/api/v1/integrations/onec/settings", ("GET",), "onec:settings:view"),
    ("/api/v1/integrations/onec/settings", ("PUT",), "onec:settings:manage"),
    ("/api/v1/integrations/onec/check", ("POST",), "onec:settings:manage"),
    ("/api/v1/integrations/onec/diagnose", ("POST",), "onec:settings:manage"),
    ("/api/v1/integrations/onec/check-employee-status", ("POST",), "onec:status-check"),
    ("/api/v1/integrations/naumen/settings", ("GET",), "naumen:settings:view"),
    ("/api/v1/integrations/naumen/settings", ("PUT",), "naumen:settings:manage"),
    ("/api/v1/integrations/naumen/check", ("POST",), "naumen:settings:manage"),
    ("/api/v1/integrations/naumen/diagnose", ("POST",), "naumen:settings:view"),
    ("/api/v1/integrations/naumen/partners", ("GET", "POST"), "naumen:operators:sync|naumen:settings:view"),
    ("/api/v1/integrations/naumen/sync", ("GET", "POST"), "naumen:operators:sync"),
    ("/api/v1/naumen/status", ("GET",), "naumen:settings:view|dashboard:view"),
    ("/api/v1/naumen/local", ("GET",), "dashboard:view|workload:view|queues:view|staffing:view|employees:view"),
    ("/api/v1/naumen/customers", ("GET",), "naumen:settings:view|workload:view|dashboard:view"),
    ("/api/v1/naumen/operators", ("GET",), "employees:view|naumen:operators:sync"),
    ("/api/v1/naumen/operators/sync", ("POST",), "naumen:operators:sync"),
    ("/api/v1/projects/current", ("GET", "PUT"), "dashboard:view"),
    ("/api/v1/projects/check", ("POST",), "settings:manage"),
    ("/api/v1/projects", ("GET",), "dashboard:view"),
    ("/api/v1/projects", ("POST", "PUT", "DELETE"), "settings:manage"),
    ("/api/v1/shifts", ("GET",), "shifts:view"),
    ("/api/v1/shifts", ("POST", "PUT", "DELETE"), "shifts:manage"),
    ("/api/v1/schedules/generate-draft", ("POST",), "schedules:generate"),
    ("/api/v1/schedules/confirm-period", ("POST",), "schedules:confirm"),
    ("/api/v1/schedules/publish-period", ("POST",), "schedules:publish"),
    ("/api/v1/schedules", ("GET",), "schedules:view"),
    ("/api/v1/schedules", ("POST", "PUT", "DELETE"), "schedules:manage"),
    ("/api/v1/schedule-recommendations", ("GET",), "schedules:view"),
    ("/api/v1/coverage", ("GET",), "schedules:view"),
    ("/api/v1/absences", ("GET",), "absences:view"),
    ("/api/v1/absences", ("POST", "PUT", "DELETE"), "absences:manage"),
    ("/api/v1/actual-work", ("GET",), "actual:view"),
    ("/api/v1/actual-work", ("POST", "PUT", "DELETE"), "actual:manage"),
    ("/api/v1/reports/export-log", ("GET",), "reports:view"),
    ("/api/v1/reports", ("GET",), "reports:view"),
    ("/api/v1/users", ("GET",), "users:view"),
    ("/api/v1/users", ("POST", "PUT", "DELETE"), "users:manage"),
    ("/api/v1/roles", ("GET",), "users:view"),
    ("/api/v1/permissions", ("GET",), "users:view"),
    ("/api/v1/audit-log", ("GET",), "audit:view"),
    ("/api/v1/health/db", ("GET",), "settings:view"),
]


def required_permission(path: str, method: str) -> str | None:
    if path.endswith(".csv"):
        return "reports:export"
    for prefix, methods, permission in RULES:
        if path.startswith(prefix) and method in methods:
            return permission
    if path.startswith("/api/v1/"):
        return "dashboard:view"
    return None


async def rbac_middleware(request: Request, call_next):
    if not settings.auth_enabled or not request.url.path.startswith("/api/v1/") or request.url.path.startswith(PUBLIC_PREFIXES):
        return await call_next(request)

    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return JSONResponse({"detail": "Требуется авторизация"}, status_code=401)
    payload = decode_access_token(authorization.split(" ", 1)[1])
    if not payload:
        return JSONResponse({"detail": "Недействительный token"}, status_code=401)

    db: Session = SessionLocal()
    try:
        user = db.get(User, int(payload.get("sub", 0)))
        if not user or not user.is_active:
            return JSONResponse({"detail": "Пользователь не активен"}, status_code=401)
        permission = required_permission(request.url.path, request.method)
        permissions = user_permissions(db, user)
        allowed_permissions = permission.split("|") if permission else []
        if allowed_permissions and not user.is_superuser and not any(item in permissions for item in allowed_permissions):
            return JSONResponse({"detail": "Нет доступа"}, status_code=403)
        request.state.user = user
        request.state.permissions = permissions
        request.state.username = user.username
        return await call_next(request)
    finally:
        db.close()
