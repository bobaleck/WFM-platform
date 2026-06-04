from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.integrations.naumen.client import NaumenClient, NaumenClientError
from app.models.integration_settings import NaumenConnectionSettings, NaumenPartner, NaumenSyncRun
from app.services.integration_settings import decrypted_api_key, decrypted_basic_password, naumen_configured


def client_from_settings(settings: NaumenConnectionSettings) -> NaumenClient:
    return NaumenClient(
        base_url=settings.base_url or "",
        auth_mode=settings.auth_mode,
        username=settings.username or "",
        api_version=getattr(settings, "api_version", "v2"),
        api_key=decrypted_api_key(settings),
        basic_password=decrypted_basic_password(settings),
        timeout_seconds=settings.request_timeout_seconds,
        verify_ssl=settings.verify_ssl,
    )


def missing_settings_fields(settings: NaumenConnectionSettings) -> list[str]:
    missing: list[str] = []
    if not settings.enabled:
        missing.append("enabled")
    if not settings.base_url:
        missing.append("base_url")
    if getattr(settings, "api_version", "v2") not in {"v2", "current"}:
        missing.append("api_version")
    if settings.auth_mode not in {"api_key", "basic"}:
        missing.append("auth_mode")
    if not settings.username:
        missing.append("username")
    if settings.auth_mode == "api_key" and not settings.api_key_encrypted:
        missing.append("api_key")
    if settings.auth_mode == "basic" and not settings.basic_password_encrypted:
        missing.append("basic_password")
    return missing


def normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    return base_url.strip().rstrip("/")


def base_url_has_endpoint_path(base_url: str | None) -> bool:
    normalized = normalize_base_url(base_url)
    if not normalized:
        return False
    parsed = urlparse(normalized)
    return bool(parsed.path and parsed.path not in {"", "/"})


def partners_items(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        items = payload.get("items", [])
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def create_sync_run(
    db: Session,
    sync_type: str,
    status: str,
    error_message: str | None = None,
    project_id: int | None = None,
    rows_received: int = 0,
    rows_created: int = 0,
    rows_updated: int = 0,
    rows_failed: int = 0,
) -> NaumenSyncRun:
    run = NaumenSyncRun(
        sync_type=sync_type,
        project_id=project_id,
        status=status,
        finished_at=datetime.utcnow(),
        rows_received=rows_received,
        rows_created=rows_created,
        rows_updated=rows_updated,
        rows_failed=rows_failed,
        error_message=error_message,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def sync_partners(db: Session, settings: NaumenConnectionSettings, dry_run: bool) -> dict:
    missing = missing_settings_fields(settings)
    if missing:
        run = create_sync_run(db, "partners", "not_configured", "Настройки Naumen неполные")
        return {
            "status": "not_configured",
            "sync_run_id": run.id,
            "dry_run": dry_run,
            "rows_received": 0,
            "rows_created": 0,
            "rows_updated": 0,
            "rows_failed": 0,
            "items": [],
            "message": "Настройки Naumen неполные",
            "missing_fields": missing,
        }
    if base_url_has_endpoint_path(settings.base_url):
        run = create_sync_run(db, "partners", "invalid_settings", "Адрес Naumen должен быть корневым")
        return {
            "status": "invalid_settings",
            "sync_run_id": run.id,
            "dry_run": dry_run,
            "rows_received": 0,
            "rows_created": 0,
            "rows_updated": 0,
            "rows_failed": 0,
            "items": [],
            "message": "Адрес Naumen должен быть корневым адресом, без /api/v2 и endpoint path",
        }

    client = client_from_settings(settings)
    try:
        payload = client.get_partners()
        items = partners_items(payload)
    except NaumenClientError as exc:
        run = create_sync_run(db, "partners", "error", str(exc))
        return {
            "status": "error",
            "sync_run_id": run.id,
            "dry_run": dry_run,
            "rows_received": 0,
            "rows_created": 0,
            "rows_updated": 0,
            "rows_failed": 1,
            "items": [],
            "checked_endpoint": exc.endpoint,
            "http_status": exc.http_status,
            "message": str(exc),
        }

    preview = [
        {"uuid": item.get("uuid"), "title": item.get("title")}
        for item in items[:10]
    ]
    if dry_run:
        run = create_sync_run(db, "partners", "ok", rows_received=len(items))
        return {
            "status": "ok",
            "sync_run_id": run.id,
            "dry_run": True,
            "rows_received": len(items),
            "rows_created": 0,
            "rows_updated": 0,
            "rows_failed": 0,
            "items": preview,
            "checked_endpoint": client.last_endpoint,
            "http_status": client.last_http_status,
            "message": "Список партнёров Naumen проверен без сохранения",
        }

    created = 0
    updated = 0
    now = datetime.utcnow()
    for item in items:
        partner_uuid = str(item.get("uuid") or "").strip()
        title = str(item.get("title") or partner_uuid).strip()
        if not partner_uuid:
            continue
        partner = db.query(NaumenPartner).filter(NaumenPartner.partner_uuid == partner_uuid).first()
        if partner:
            partner.title = title
            partner.is_active = True
            partner.last_sync_at = now
            partner.updated_at = now
            updated += 1
        else:
            db.add(NaumenPartner(partner_uuid=partner_uuid, title=title, last_sync_at=now))
            created += 1
    run = create_sync_run(db, "partners", "ok", rows_received=len(items), rows_created=created, rows_updated=updated)
    return {
        "status": "ok",
        "sync_run_id": run.id,
        "dry_run": False,
        "rows_received": len(items),
        "rows_created": created,
        "rows_updated": updated,
        "rows_failed": 0,
        "items": preview,
        "checked_endpoint": client.last_endpoint,
        "http_status": client.last_http_status,
        "message": "Партнёры Naumen загружены",
    }


def sync_pending(db: Session, settings: NaumenConnectionSettings, sync_type: str, dry_run: bool, project_id: int | None = None) -> dict:
    if not naumen_configured(settings):
        run = create_sync_run(db, sync_type, "not_configured", "Настройки Naumen неполные или интеграция выключена", project_id)
        return {
            "status": "not_configured",
            "sync_run_id": run.id,
            "dry_run": dry_run,
            "rows_received": 0,
            "rows_created": 0,
            "rows_updated": 0,
            "rows_failed": 0,
            "message": "Настройки Naumen неполные или интеграция выключена",
        }
    run = create_sync_run(db, sync_type, "pending", "Read-only endpoint подготовлен; реальная синхронизация запускается только администратором", project_id)
    return {
        "status": "pending",
        "sync_run_id": run.id,
        "dry_run": dry_run,
        "rows_received": 0,
        "rows_created": 0,
        "rows_updated": 0,
        "rows_failed": 0,
        "message": "Endpoint описан/ожидает уточнения, реальные внешние запросы на этом этапе не выполняются",
    }
