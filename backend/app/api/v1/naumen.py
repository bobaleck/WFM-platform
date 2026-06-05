from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.ncc_client import NccConfigurationError, NccQueryError, ncc_configured
from app.models.integration_settings import NaumenProject, NaumenSyncRun, UserPreference
from app.services.naumen_ncc_service import NaumenNccService

router = APIRouter(prefix="/api/v1/naumen", tags=["naumen-ncc"])
contours_router = APIRouter(prefix="/api/v1/contours", tags=["naumen-ncc"])


def safe_error(exc: Exception) -> HTTPException:
    if isinstance(exc, NccConfigurationError):
        return HTTPException(status_code=503, detail="Интеграция Naumen/NCC не настроена")
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=502, detail="Naumen/NCC недоступен или вернул ошибку")


def default_period() -> tuple[str, str]:
    end = date.today() + timedelta(days=1)
    begin = end - timedelta(days=7)
    return begin.isoformat(), end.isoformat()


def current_contour(db: Session, request: Request) -> NaumenProject | None:
    user = getattr(request.state, "user", None)
    preference = db.query(UserPreference).filter(UserPreference.user_id == user.id).first() if user else None
    if preference and preference.selected_project_id:
        selected = db.get(NaumenProject, preference.selected_project_id)
        if selected and selected.is_active:
            return selected
    return db.query(NaumenProject).filter(NaumenProject.is_active.is_(True)).order_by(NaumenProject.is_default.desc(), NaumenProject.id).first()


def contour_id_or_404(db: Session, request: Request, contour_id: int | None = None) -> int:
    if contour_id is not None:
        return contour_id
    contour = current_contour(db, request)
    if not contour:
        raise HTTPException(status_code=404, detail="Активный контур не выбран")
    return contour.id


def local_rows(db: Session, sql: str, params: dict) -> list[dict]:
    return [dict(row._mapping) for row in db.execute(text(sql), params).all()]


@router.get("/status")
def ncc_status(check: bool = True, db: Session = Depends(get_db)) -> dict:
    return NaumenNccService(db).status(check=check)


@router.get("/local/status")
def local_ncc_status(request: Request, db: Session = Depends(get_db)) -> dict:
    contour = current_contour(db, request)
    if not contour:
        return {"configured": ncc_configured(), "contour_selected": False, "message": "Активный контур не выбран"}
    partner_uuid = contour.naumen_customer_uuid or contour.partner_uuid
    last_run = db.query(NaumenSyncRun).filter(NaumenSyncRun.project_id == contour.id, NaumenSyncRun.sync_type == "ncc_sync").order_by(NaumenSyncRun.started_at.desc()).first()
    counts = dict(db.execute(text("""
        SELECT
          (SELECT count(*) FROM ncc_queues WHERE contour_id = :contour_id) AS queues,
          (SELECT count(*) FROM ncc_load_intervals WHERE contour_id = :contour_id) AS load,
          (SELECT count(*) FROM ncc_employees WHERE contour_id = :contour_id) AS employees,
          (SELECT count(*) FROM ncc_operator_workload WHERE contour_id = :contour_id) AS operator_workload,
          (SELECT count(*) FROM ncc_forecast_profile WHERE contour_id = :contour_id) AS forecast_profile
    """), {"contour_id": contour.id}).one()._mapping)
    if not partner_uuid:
        message = "Naumen/NCC не настроен для активного контура. Доступен ручной режим."
    elif not any(int(value or 0) for value in counts.values()):
        message = "Данные Naumen за выбранный период не загружены."
    else:
        message = "Локальные данные Naumen/NCC доступны."
    return {
        "configured": ncc_configured(),
        "contour_selected": True,
        "contour_id": contour.id,
        "partner_uuid": partner_uuid,
        "manual_stats_enabled": contour.manual_stats_enabled,
        "last_sync_at": last_run.finished_at if last_run else contour.last_sync_at,
        "last_sync_status": last_run.status if last_run else None,
        "counts": counts,
        "message": message,
    }


@router.get("/local/queues")
def local_queues(request: Request, contour_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    cid = contour_id_or_404(db, request, contour_id)
    rows = local_rows(db, """
        SELECT id, queue_uuid, queue_name, data_channel, target_sl, answer_sec, state, imported_at
        FROM ncc_queues WHERE contour_id = :contour_id ORDER BY queue_name
    """, {"contour_id": cid})
    return {"items": rows, "count": len(rows)}


@router.get("/local/load")
def local_load(request: Request, contour_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    cid = contour_id_or_404(db, request, contour_id)
    rows = local_rows(db, """
        SELECT id, interval_start, queue_uuid, queue_name, offered, handled, lost, lost_rate, aht_sec, sl_percent
        FROM ncc_load_intervals WHERE contour_id = :contour_id ORDER BY interval_start DESC, queue_name LIMIT 1000
    """, {"contour_id": cid})
    totals = dict(db.execute(text("""
        SELECT COALESCE(sum(offered),0) offered, COALESCE(sum(handled),0) handled, COALESCE(sum(lost),0) lost,
               CASE WHEN COALESCE(sum(offered),0) > 0 THEN round(sum(lost)::numeric / sum(offered)::numeric * 100, 2) ELSE 0 END lost_rate,
               round(COALESCE(avg(aht_sec),0)::numeric, 2) aht_sec,
               round(COALESCE(avg(sl_percent),0)::numeric, 2) sl_percent
        FROM ncc_load_intervals WHERE contour_id = :contour_id
    """), {"contour_id": cid}).one()._mapping)
    return {"items": rows, "count": len(rows), "totals": totals}


@router.get("/local/operators")
def local_operators(request: Request, contour_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    cid = contour_id_or_404(db, request, contour_id)
    rows = local_rows(db, """
        SELECT id, employee_uuid, login, employee_title, operator_name, ou_title, post, department, queues_count, queues,
               handled_calls_count, avg_answer_sec, avg_talk_sec, total_talk_sec, sl_percent, skills, statuses_seen, first_handled_at, last_handled_at
        FROM ncc_employees WHERE contour_id = :contour_id ORDER BY handled_calls_count DESC, login LIMIT 1000
    """, {"contour_id": cid})
    return {"items": rows, "count": len(rows)}


@router.get("/local/operator-workload")
def local_operator_workload(request: Request, contour_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    cid = contour_id_or_404(db, request, contour_id)
    rows = local_rows(db, """
        SELECT id, interval_start, queue_uuid, queue_name, operator_login, handled, aht_sec, talk_sec_total
        FROM ncc_operator_workload WHERE contour_id = :contour_id ORDER BY interval_start DESC, queue_name, operator_login LIMIT 1000
    """, {"contour_id": cid})
    return {"items": rows, "count": len(rows)}


@router.get("/local/forecast-profile")
def local_forecast_profile(request: Request, contour_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    cid = contour_id_or_404(db, request, contour_id)
    rows = local_rows(db, """
        SELECT id, weekday_num, weekday_name, hour_num, queue_uuid, queue_name, avg_offered, avg_handled, avg_lost, avg_aht_sec, avg_sl_percent
        FROM ncc_forecast_profile WHERE contour_id = :contour_id ORDER BY weekday_num, hour_num, queue_name LIMIT 1000
    """, {"contour_id": cid})
    return {"items": rows, "count": len(rows)}


@router.get("/customers")
def ncc_customers(db: Session = Depends(get_db)) -> dict:
    try:
        rows = NaumenNccService(db).customers()
        return {"items": rows, "count": len(rows)}
    except (NccConfigurationError, NccQueryError, ValueError) as exc:
        raise safe_error(exc) from exc


@router.get("/customers/{partner_uuid}/projects")
def ncc_customer_projects(partner_uuid: str, db: Session = Depends(get_db)) -> dict:
    try:
        rows = NaumenNccService(db).projects(partner_uuid)
        return {"items": rows, "count": len(rows)}
    except (NccConfigurationError, NccQueryError, ValueError) as exc:
        raise safe_error(exc) from exc


@router.get("/customers/{partner_uuid}/queues")
def ncc_customer_queues(partner_uuid: str, db: Session = Depends(get_db)) -> dict:
    try:
        rows = NaumenNccService(db).queues(partner_uuid)
        return {"items": rows, "count": len(rows)}
    except (NccConfigurationError, NccQueryError, ValueError) as exc:
        raise safe_error(exc) from exc


@router.get("/customers/{partner_uuid}/load")
def ncc_customer_load(partner_uuid: str, begin: str, end: str, interval: str = "hour", db: Session = Depends(get_db)) -> dict:
    if interval != "hour":
        raise HTTPException(status_code=422, detail="Сейчас поддерживается только часовой интервал")
    try:
        rows = NaumenNccService(db).load(partner_uuid, begin, end)
        return {"items": rows, "count": len(rows)}
    except (NccConfigurationError, NccQueryError, ValueError) as exc:
        raise safe_error(exc) from exc


@router.get("/customers/{partner_uuid}/employees")
def ncc_customer_employees(partner_uuid: str, begin: str, end: str, db: Session = Depends(get_db)) -> dict:
    try:
        rows = NaumenNccService(db).employees(partner_uuid, begin, end)
        return {"items": rows, "count": len(rows)}
    except (NccConfigurationError, NccQueryError, ValueError) as exc:
        raise safe_error(exc) from exc


@router.get("/customers/{partner_uuid}/operator-workload")
def ncc_operator_workload(partner_uuid: str, begin: str, end: str, db: Session = Depends(get_db)) -> dict:
    try:
        rows = NaumenNccService(db).operator_workload(partner_uuid, begin, end)
        return {"items": rows, "count": len(rows)}
    except (NccConfigurationError, NccQueryError, ValueError) as exc:
        raise safe_error(exc) from exc


@router.get("/customers/{partner_uuid}/forecast-profile")
def ncc_forecast_profile(partner_uuid: str, begin: str, end: str, db: Session = Depends(get_db)) -> dict:
    try:
        rows = NaumenNccService(db).forecast_profile(partner_uuid, begin, end)
        return {"items": rows, "count": len(rows)}
    except (NccConfigurationError, NccQueryError, ValueError) as exc:
        raise safe_error(exc) from exc


@contours_router.post("/{contour_id}/naumen/sync")
def sync_contour_naumen(contour_id: int, begin: str | None = None, end: str | None = None, db: Session = Depends(get_db)) -> dict:
    contour = db.get(NaumenProject, contour_id)
    if not contour or not contour.is_active:
        raise HTTPException(status_code=404, detail="Рабочий контур не найден")
    if begin is None or end is None:
        begin, end = default_period()
    try:
        return NaumenNccService(db).sync_contour(contour, begin, end)
    except (NccConfigurationError, NccQueryError, ValueError) as exc:
        raise safe_error(exc) from exc
