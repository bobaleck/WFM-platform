from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.onec.service import OneCService, get_or_create_onec_settings, update_settings_check_state
from app.integrations.naumen.client import NaumenClientError
from app.integrations.naumen.service import (
    base_url_has_endpoint_path,
    client_from_settings,
    missing_settings_fields,
    normalize_base_url,
    sync_partners,
    sync_pending,
)
from app.models.integration_settings import NaumenPartner, NaumenProject, NaumenSyncError, NaumenSyncRun, UserPreference, UserProjectAccess
from app.models.wfm import AuditLog, User
from app.schemas.integration import (
    IntegrationSettingsPayload,
    IntegrationSettingsResponse,
    NaumenProjectSyncRequest,
    NaumenPartnerSyncRequest,
    NaumenSettingsPayload,
    NaumenSettingsResponse,
    NaumenSyncRequest,
    NaumenSyncRunDetail,
    NaumenSyncRunOut,
    OneCEmployeeStatusRequest,
    OneCSettingsPayload,
    OneCSettingsResponse,
    CurrentProjectIn,
    ProjectCheckIn,
    ProjectIn,
    ProjectOut,
    ProjectUpdate,
    PartnerOut,
    PartnerUpdate,
    CurrentContextIn,
)
from app.services.integration_settings import (
    get_or_create_naumen_settings,
    get_or_create_settings,
    is_configured,
    naumen_configured,
    naumen_settings_response,
    to_response,
    update_naumen_settings,
    onec_settings_response,
    update_onec_settings,
    update_settings,
)

router = APIRouter(tags=["integration"])
legacy_router = APIRouter(prefix="/api/v1/integration", tags=["integration"])
naumen_router = APIRouter(prefix="/api/v1/integrations/naumen", tags=["naumen-integration"])
onec_router = APIRouter(prefix="/api/v1/integrations/onec", tags=["onec-integration"])
projects_router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
contours_router = APIRouter(prefix="/api/v1/contours", tags=["contours"])


def write_audit(db: Session, action: str, request: Request, details: str | None = None) -> None:
    user = getattr(request.state, "user", None)
    db.add(AuditLog(
        actor_user_id=getattr(user, "id", None),
        actor_username=getattr(user, "username", None),
        actor=getattr(user, "username", None) or "system",
        action=action,
        entity_type="integration",
        entity_id="naumen",
        details=details,
        details_json=details,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    ))


def current_user(request: Request) -> User | None:
    return getattr(request.state, "user", None)


def is_admin_user(user: User | None) -> bool:
    return bool(user and (user.is_superuser or user.role == "admin"))


def accessible_projects_query(db: Session, user: User | None):
    query = db.query(NaumenProject).filter(NaumenProject.is_active.is_(True))
    if is_admin_user(user):
        return query
    if not user:
        return query.filter(False)
    ids = [
        row.naumen_project_id
        for row in db.query(UserProjectAccess).filter(UserProjectAccess.user_id == user.id, UserProjectAccess.can_view.is_(True)).all()
    ]
    return query.filter(NaumenProject.id.in_(ids)) if ids else query.filter(False)


def user_has_project_access(db: Session, user: User | None, project_id: int | None) -> bool:
    if project_id is None:
        return True
    if is_admin_user(user):
        return True
    if not user:
        return False
    return db.query(UserProjectAccess).filter(
        UserProjectAccess.user_id == user.id,
        UserProjectAccess.naumen_project_id == project_id,
        UserProjectAccess.can_view.is_(True),
    ).first() is not None


def default_project_for_user(db: Session, user: User | None) -> NaumenProject | None:
    preference = db.query(UserPreference).filter(UserPreference.user_id == user.id).first() if user else None
    if preference and preference.selected_project_id and user_has_project_access(db, user, preference.selected_project_id):
        selected = db.get(NaumenProject, preference.selected_project_id)
        if selected and selected.is_active:
            return selected
    query = accessible_projects_query(db, user)
    return query.filter(NaumenProject.is_default.is_(True)).first() or query.order_by(NaumenProject.id).first()


def default_partner_for_user(db: Session, user: User | None) -> NaumenPartner | None:
    preference = db.query(UserPreference).filter(UserPreference.user_id == user.id).first() if user else None
    if preference and getattr(preference, "selected_partner_id", None):
        selected = db.get(NaumenPartner, preference.selected_partner_id)
        if selected and selected.is_active:
            return selected
    return (
        db.query(NaumenPartner)
        .filter(NaumenPartner.is_active.is_(True))
        .order_by(NaumenPartner.is_default.desc(), NaumenPartner.id)
        .first()
    )


@legacy_router.get("/settings", response_model=IntegrationSettingsResponse)
def read_settings(db: Session = Depends(get_db)) -> IntegrationSettingsResponse:
    return to_response(get_or_create_settings(db))


@legacy_router.post("/settings", response_model=IntegrationSettingsResponse)
def save_settings(payload: IntegrationSettingsPayload, db: Session = Depends(get_db)) -> IntegrationSettingsResponse:
    return to_response(update_settings(db, payload))


@legacy_router.post("/test")
def test_integration(db: Session = Depends(get_db)) -> dict[str, str]:
    item = get_or_create_settings(db)
    if not is_configured(item):
        return {"status": "not_configured", "message": "Настройки интеграции сохранены не полностью или интеграция выключена"}
    return {"status": "stub", "message": "Настройки найдены. Реальная проверка подключения будет включена на следующем этапе."}


@legacy_router.get("/status")
def integration_status(db: Session = Depends(get_db)) -> dict[str, str | bool]:
    item = get_or_create_settings(db)
    return {
        "provider": item.provider,
        "display_name": item.display_name,
        "enabled": item.enabled,
        "configured": is_configured(item),
        "connection_check": "stub",
    }


@naumen_router.get("/settings", response_model=NaumenSettingsResponse)
def read_naumen_settings(db: Session = Depends(get_db)) -> NaumenSettingsResponse:
    return naumen_settings_response(get_or_create_naumen_settings(db))


@naumen_router.put("/settings", response_model=NaumenSettingsResponse)
def save_naumen_settings(payload: NaumenSettingsPayload, request: Request, db: Session = Depends(get_db)) -> NaumenSettingsResponse:
    item = update_naumen_settings(db, payload)
    write_audit(db, "naumen_settings_update", request, details=f"auth_mode={item.auth_mode}; enabled={item.enabled}")
    db.commit()
    return naumen_settings_response(item)


@naumen_router.post("/check")
def check_naumen(request: Request, db: Session = Depends(get_db)) -> dict:
    item = get_or_create_naumen_settings(db)
    missing = missing_settings_fields(item)
    if missing:
        status = "not_configured"
        message = "Настройки подключения заполнены не полностью"
        http_status = None
        endpoint = None
        items_count = None
    elif base_url_has_endpoint_path(item.base_url):
        status = "invalid_settings"
        message = "Адрес Naumen должен быть корневым адресом, например https://host:8443, без /api/v2 и endpoint path"
        http_status = None
        endpoint = None
        items_count = None
    else:
        client = client_from_settings(item)
        try:
            result = client.check_connection()
            status = "ok"
            message = result.get("message") or "Подключение проверено через список партнёров Naumen"
            http_status = result.get("http_status")
            endpoint = result.get("endpoint")
            items_count = result.get("items_count")
        except NaumenClientError as exc:
            status = "error"
            message = str(exc)
            http_status = exc.http_status
            endpoint = exc.endpoint
            items_count = None
    item.last_check_status = status
    item.last_check_message = message
    item.last_check_http_status = http_status
    item.last_check_endpoint = endpoint
    item.last_check_at = datetime.utcnow()
    write_audit(db, "naumen_connection_check", request, details=status)
    db.commit()
    return {
        "status": status,
        "message": message,
        "enabled": item.enabled,
        "missing_fields": missing if status == "not_configured" else [],
        "checked_endpoint": endpoint,
        "http_status": http_status,
        "items_count": items_count,
        "endpoint": endpoint,
    }


@naumen_router.post("/diagnose")
def diagnose_naumen(request: Request, db: Session = Depends(get_db)) -> dict:
    item = get_or_create_naumen_settings(db)
    missing = missing_settings_fields(item)
    base_url_valid = not base_url_has_endpoint_path(item.base_url)
    normalized = normalize_base_url(item.base_url)
    endpoint = f"/api/{getattr(item, 'api_version', 'v2')}/partners/" if getattr(item, "api_version", "v2") in {"v2", "current"} else None
    result = {
        "settings_valid": not missing,
        "missing_fields": missing,
        "base_url_valid": base_url_valid,
        "base_url_normalized": normalized,
        "api_version": getattr(item, "api_version", "v2"),
        "auth_mode": item.auth_mode,
        "username_present": bool(item.username),
        "secret_present": bool(item.api_key_encrypted if item.auth_mode == "api_key" else item.basic_password_encrypted),
        "api_key_present": bool(item.api_key_encrypted),
        "basic_password_present": bool(item.basic_password_encrypted),
        "will_check": "partners",
        "checked_endpoint": endpoint,
        "computed_url_safe": None,
        "http_status": None,
        "items_count": None,
        "status": "not_configured" if missing else "pending",
        "message": "Настройки подключения заполнены не полностью" if missing else "Диагностика подготовлена",
    }
    if normalized and endpoint:
        result["computed_url_safe"] = f"{normalized}{endpoint}"
    if missing:
        return result
    if not base_url_valid:
        result["status"] = "invalid_settings"
        result["message"] = "Адрес Naumen должен быть корневым адресом, без /api/v2 и endpoint path"
        return result
    client = client_from_settings(item)
    try:
        checked = client.check_connection()
        result.update({
            "http_status": checked.get("http_status"),
            "items_count": checked.get("items_count"),
            "checked_endpoint": checked.get("endpoint"),
            "computed_url_safe": client.build_safe_url("/partners/"),
            "status": "ok",
            "message": checked.get("message"),
        })
    except NaumenClientError as exc:
        result.update({
            "http_status": exc.http_status,
            "checked_endpoint": exc.endpoint,
            "status": "error",
            "message": str(exc),
        })
    write_audit(db, "naumen_connection_diagnose", request, details=str(result["status"]))
    db.commit()
    return result


@onec_router.get("/settings", response_model=OneCSettingsResponse)
def read_onec_settings(db: Session = Depends(get_db)) -> OneCSettingsResponse:
    return onec_settings_response(get_or_create_onec_settings(db))


@onec_router.put("/settings", response_model=OneCSettingsResponse)
def save_onec_settings(payload: OneCSettingsPayload, request: Request, db: Session = Depends(get_db)) -> OneCSettingsResponse:
    item = update_onec_settings(db, payload)
    write_audit(db, "onec_settings_update", request, details=f"connection_mode={item.connection_mode}; enabled={item.enabled}")
    db.commit()
    return onec_settings_response(item)


@onec_router.post("/check")
def check_onec(request: Request, db: Session = Depends(get_db)) -> dict:
    item = get_or_create_onec_settings(db)
    result = OneCService(item).check_connection()
    update_settings_check_state(item, result)
    write_audit(db, "onec_connection_check", request, details=str(result.get("status")))
    db.commit()
    return result


@onec_router.post("/diagnose")
def diagnose_onec(request: Request, db: Session = Depends(get_db)) -> dict:
    item = get_or_create_onec_settings(db)
    result = OneCService(item).diagnose()
    update_settings_check_state(item, result)
    write_audit(db, "onec_connection_diagnose", request, details=str(result.get("status")))
    db.commit()
    return result


@onec_router.post("/check-employee-status")
def check_onec_employee_status(payload: OneCEmployeeStatusRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    status = OneCService(get_or_create_onec_settings(db)).check_employee_status_by_inn(payload.inn)
    write_audit(db, "onec_employee_status_check", request, details=f"inn_present={bool(payload.inn)}; status={status.status}")
    db.commit()
    return status.__dict__


@onec_router.post("/diagnose-employee-lookup")
def diagnose_onec_employee_lookup(payload: OneCEmployeeStatusRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    result = OneCService(get_or_create_onec_settings(db)).diagnose_employee_lookup(payload.inn)
    write_audit(db, "onec_employee_lookup_diagnose", request, details=f"inn_present={bool(payload.inn)}; status={result.get('status')}")
    db.commit()
    return result


def run_sync(sync_type: str, payload: NaumenSyncRequest, request: Request, db: Session) -> dict:
    item = get_or_create_naumen_settings(db)
    if payload.project_id and not user_has_project_access(db, current_user(request), payload.project_id):
        raise HTTPException(status_code=403, detail="Нет доступа к проекту")
    result = sync_pending(db, item, sync_type=sync_type, dry_run=payload.dry_run, project_id=payload.project_id)
    write_audit(db, f"naumen_sync_{sync_type}", request, details=f"status={result['status']}; dry_run={payload.dry_run}")
    db.commit()
    return result


@naumen_router.post("/sync/employees")
def sync_employees(payload: NaumenSyncRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    return run_sync("employees", payload, request, db)


@naumen_router.post("/sync/departments")
def sync_departments(payload: NaumenSyncRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    return run_sync("departments", payload, request, db)


@naumen_router.post("/sync/project-agents")
def sync_project_agents(payload: NaumenProjectSyncRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    result = run_sync("project_agents", payload, request, db)
    result["project_uuid"] = payload.project_uuid
    return result


@naumen_router.post("/sync/project-schedule")
def sync_project_schedule(payload: NaumenProjectSyncRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    result = run_sync("project_schedule", payload, request, db)
    result["project_uuid"] = payload.project_uuid
    return result


@naumen_router.get("/partners", response_model=list[PartnerOut])
def list_partners(db: Session = Depends(get_db)) -> list[NaumenPartner]:
    return db.query(NaumenPartner).order_by(NaumenPartner.is_default.desc(), NaumenPartner.id).all()


@naumen_router.post("/partners/sync")
def sync_naumen_partners(payload: NaumenPartnerSyncRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    item = get_or_create_naumen_settings(db)
    result = sync_partners(db, item, dry_run=payload.dry_run)
    write_audit(db, "naumen_sync_partners", request, details=f"status={result['status']}; dry_run={payload.dry_run}")
    db.commit()
    return result


@naumen_router.post("/partners/{partner_id}/default", response_model=PartnerOut)
def set_default_partner(partner_id: int, request: Request, db: Session = Depends(get_db)) -> NaumenPartner:
    partner = db.get(NaumenPartner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Партнёр Naumen не найден")
    db.query(NaumenPartner).update({"is_default": False})
    partner.is_default = True
    partner.is_active = True
    partner.updated_at = datetime.utcnow()
    write_audit(db, "naumen_partner_default", request, details=f"partner_id={partner_id}")
    db.commit()
    db.refresh(partner)
    return partner


@naumen_router.put("/partners/{partner_id}", response_model=PartnerOut)
def update_partner(partner_id: int, payload: PartnerUpdate, request: Request, db: Session = Depends(get_db)) -> NaumenPartner:
    partner = db.get(NaumenPartner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Партнёр Naumen не найден")
    if payload.title is not None:
        partner.title = payload.title
    if payload.is_active is not None:
        partner.is_active = payload.is_active
    if payload.is_default is not None:
        if payload.is_default:
            db.query(NaumenPartner).update({"is_default": False})
        partner.is_default = payload.is_default
    partner.updated_at = datetime.utcnow()
    write_audit(db, "naumen_partner_update", request, details=f"partner_id={partner_id}")
    db.commit()
    db.refresh(partner)
    return partner


@projects_router.get("", response_model=list[ProjectOut])
def list_projects(request: Request, db: Session = Depends(get_db)) -> list[NaumenProject]:
    return accessible_projects_query(db, current_user(request)).order_by(NaumenProject.is_default.desc(), NaumenProject.id).all()


@projects_router.post("/check")
def check_project(payload: ProjectCheckIn, request: Request, db: Session = Depends(get_db)) -> dict:
    settings = get_or_create_naumen_settings(db)
    if not naumen_configured(settings):
        return {"status": "not_configured", "message": "Настройки Naumen неполные или интеграция выключена", "project_uuid": payload.project_uuid}
    client = client_from_settings(settings)
    try:
        data = client.get_project(payload.project_uuid)
        project = data if isinstance(data, dict) else {}
        write_audit(db, "naumen_project_check", request, details=f"project_uuid={payload.project_uuid}; status=ok")
        db.commit()
        return {
            "status": "ok",
            "project_uuid": payload.project_uuid,
            "title": project.get("title") or project.get("name") or payload.project_uuid,
            "partner_uuid": project.get("partner") or project.get("partnerUuid"),
            "state": project.get("state"),
            "data_channel": project.get("dataChannel"),
            "cluster_id": project.get("clusterId"),
            "http_status": client.last_http_status,
            "endpoint": client.last_endpoint,
            "message": "Проект найден через GET /projects/{uuid}",
        }
    except NaumenClientError as exc:
        write_audit(db, "naumen_project_check", request, details=f"project_uuid={payload.project_uuid}; error={exc}")
        db.commit()
        return {"status": "error", "project_uuid": payload.project_uuid, "http_status": exc.http_status, "endpoint": exc.endpoint, "message": str(exc)}


@projects_router.post("", response_model=ProjectOut)
def create_project(payload: ProjectIn, request: Request, db: Session = Depends(get_db)) -> NaumenProject:
    if payload.is_default:
        db.query(NaumenProject).update({"is_default": False})
    existing = db.query(NaumenProject).filter(NaumenProject.project_uuid == payload.project_uuid).first()
    if existing:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        project = existing
    else:
        project = NaumenProject(**payload.model_dump())
        db.add(project)
    write_audit(db, "naumen_project_save", request, details=f"project_uuid={payload.project_uuid}")
    db.commit()
    db.refresh(project)
    return project


@projects_router.get("/current", response_model=ProjectOut | None)
def current_project(request: Request, db: Session = Depends(get_db)) -> NaumenProject | None:
    return default_project_for_user(db, current_user(request))


@projects_router.put("/current", response_model=ProjectOut | None)
def set_current_project(payload: CurrentProjectIn, request: Request, db: Session = Depends(get_db)) -> NaumenProject | None:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    if payload.project_id is not None and not user_has_project_access(db, user, payload.project_id):
        raise HTTPException(status_code=403, detail="Нет доступа к проекту")
    preference = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if not preference:
        preference = UserPreference(user_id=user.id)
        db.add(preference)
    preference.selected_project_id = payload.project_id
    preference.updated_at = datetime.utcnow()
    db.commit()
    return default_project_for_user(db, user)


@projects_router.get("/current-context")
def current_context(request: Request, db: Session = Depends(get_db)) -> dict | None:
    user = current_user(request)
    project = default_project_for_user(db, user)
    if project:
        return {"context_type": "project", "id": project.id, "title": project.title, "uuid": project.project_uuid}
    partner = default_partner_for_user(db, user)
    if partner:
        return {"context_type": "partner", "id": partner.id, "title": partner.title, "uuid": partner.partner_uuid}
    return None


@projects_router.put("/current-context")
def set_current_context(payload: CurrentContextIn, request: Request, db: Session = Depends(get_db)) -> dict | None:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    preference = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if not preference:
        preference = UserPreference(user_id=user.id)
        db.add(preference)
    if payload.id is None:
        preference.selected_project_id = None
        preference.selected_partner_id = None
    elif payload.context_type == "project":
        if not user_has_project_access(db, user, payload.id):
            raise HTTPException(status_code=403, detail="Нет доступа к проекту")
        preference.selected_project_id = payload.id
        preference.selected_partner_id = None
    elif payload.context_type == "partner":
        partner = db.get(NaumenPartner, payload.id)
        if not partner or not partner.is_active:
            raise HTTPException(status_code=404, detail="Партнёр Naumen не найден")
        preference.selected_project_id = None
        preference.selected_partner_id = payload.id
    preference.updated_at = datetime.utcnow()
    db.commit()
    return current_context(request, db)


@projects_router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, request: Request, db: Session = Depends(get_db)) -> NaumenProject:
    project = db.get(NaumenProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    if payload.title is not None:
        project.title = payload.title
    if payload.is_active is not None:
        project.is_active = payload.is_active
    if payload.is_default is not None:
        if payload.is_default:
            db.query(NaumenProject).update({"is_default": False})
        project.is_default = payload.is_default
    project.updated_at = datetime.utcnow()
    write_audit(db, "naumen_project_update", request, details=f"project_id={project_id}")
    db.commit()
    db.refresh(project)
    return project


@projects_router.delete("/{project_id}")
def delete_project(project_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    project = db.get(NaumenProject, project_id)
    if project:
        project.is_active = False
        project.updated_at = datetime.utcnow()
        write_audit(db, "naumen_project_disable", request, details=f"project_id={project_id}")
        db.commit()
    return {"status": "disabled", "id": project_id}


@naumen_router.get("/sync-runs", response_model=list[NaumenSyncRunOut])
def sync_runs(db: Session = Depends(get_db)) -> list[NaumenSyncRun]:
    return db.query(NaumenSyncRun).order_by(NaumenSyncRun.started_at.desc()).limit(100).all()


@naumen_router.get("/sync-runs/{run_id}", response_model=NaumenSyncRunDetail)
def sync_run_detail(run_id: int, db: Session = Depends(get_db)) -> NaumenSyncRunDetail:
    run = db.get(NaumenSyncRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Запуск синхронизации не найден")
    errors = db.query(NaumenSyncError).filter(NaumenSyncError.sync_run_id == run_id).order_by(NaumenSyncError.id).all()
    base = NaumenSyncRunOut.model_validate(run).model_dump()
    return NaumenSyncRunDetail(**base, errors=errors)


def contour_payload(project: NaumenProject) -> dict:
    return {
        "id": project.id,
        "name": project.title,
        "description": project.state,
        "is_active": project.is_active,
        "is_default": project.is_default,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@contours_router.get("")
def list_contours(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    return [contour_payload(item) for item in accessible_projects_query(db, current_user(request)).order_by(NaumenProject.is_default.desc(), NaumenProject.id).all()]


@contours_router.post("")
def create_contour(payload: dict, request: Request, db: Session = Depends(get_db)) -> dict:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Название контура обязательно")
    if payload.get("is_default"):
        db.query(NaumenProject).update({"is_default": False})
    item = NaumenProject(
        project_uuid=uuid4().hex,
        title=name,
        state=str(payload.get("description") or "") or None,
        is_active=bool(payload.get("is_active", True)),
        is_default=bool(payload.get("is_default", False)),
        data_channel="manual",
    )
    db.add(item)
    write_audit(db, "contour_create", request, details=f"contour={name}")
    db.commit()
    db.refresh(item)
    return contour_payload(item)


@contours_router.get("/current")
def get_current_contour(request: Request, db: Session = Depends(get_db)) -> dict | None:
    current = current_project(request, db)
    return contour_payload(current) if current else None


@contours_router.put("/current")
def set_current_contour(payload: dict, request: Request, db: Session = Depends(get_db)) -> dict | None:
    selected = set_current_project(CurrentProjectIn(project_id=payload.get("id") or payload.get("contour_id")), request, db)
    return contour_payload(selected) if selected else None


@contours_router.put("/{contour_id}")
def update_contour(contour_id: int, payload: dict, request: Request, db: Session = Depends(get_db)) -> dict:
    item = db.get(NaumenProject, contour_id)
    if not item:
        raise HTTPException(status_code=404, detail="Контур не найден")
    if "name" in payload and str(payload.get("name") or "").strip():
        item.title = str(payload["name"]).strip()
    if "description" in payload:
        item.state = str(payload.get("description") or "") or None
    if "is_active" in payload:
        item.is_active = bool(payload["is_active"])
    if payload.get("is_default"):
        db.query(NaumenProject).update({"is_default": False})
        item.is_default = True
    item.updated_at = datetime.utcnow()
    write_audit(db, "contour_update", request, details=f"contour_id={contour_id}")
    db.commit()
    db.refresh(item)
    return contour_payload(item)


@contours_router.post("/{contour_id}/archive")
def archive_contour(contour_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    item = db.get(NaumenProject, contour_id)
    if not item:
        raise HTTPException(status_code=404, detail="Контур не найден")
    item.is_active = False
    item.is_default = False
    item.updated_at = datetime.utcnow()
    write_audit(db, "contour_archive", request, details=f"contour_id={contour_id}")
    db.commit()
    return {"status": "archived", "id": contour_id}


router.include_router(legacy_router)
router.include_router(naumen_router)
router.include_router(onec_router)
router.include_router(projects_router)
router.include_router(contours_router)
