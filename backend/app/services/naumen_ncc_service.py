from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.integrations.ncc_client import NccConfigurationError, NccQueryError, NccReadOnlyClient, ncc_configured, validate_period
from app.models.integration_settings import NaumenPartner, NaumenProject, NaumenSyncRun
from app.models.wfm import Employee, NaumenOperator, Queue, WorkloadInterval, utcnow


CUSTOMERS_SQL = """
WITH active_projects AS (
    SELECT 'incoming' as project_type, partneruuid as partner_uuid, partnername as partner_name, uuid as project_uuid
    FROM mv_incoming_call_project
    WHERE removed = false AND state = 'Активный'
    UNION ALL
    SELECT 'outcoming' as project_type, partneruuid as partner_uuid, partnername as partner_name, uuid as project_uuid
    FROM mv_outcoming_call_project
    WHERE removed = false AND state = 'Активный'
)
SELECT
    p.uuid as customer_uuid,
    p.partnername as customer_name,
    p.partnertypetitle as customer_type,
    p.conditiontitle as customer_condition,
    p.responsiblemanagertitle as responsible_manager,
    COUNT(ap.project_uuid) as active_projects_count,
    COUNT(ap.project_uuid) FILTER (WHERE ap.project_type = 'incoming') as active_incoming_projects_count,
    COUNT(ap.project_uuid) FILTER (WHERE ap.project_type = 'outcoming') as active_outcoming_projects_count
FROM active_projects ap
LEFT JOIN mv_partner p ON p.uuid = ap.partner_uuid
WHERE p.removed = false AND p.conditiontitle = 'Активный'
GROUP BY p.uuid, p.partnername, p.partnertypetitle, p.conditiontitle, p.responsiblemanagertitle
ORDER BY p.partnername
"""

PROJECTS_SQL = """
SELECT project_type, project_uuid, project_title, project_state
FROM (
    SELECT 'incoming' as project_type, uuid as project_uuid, title as project_title, state as project_state, partneruuid as partner_uuid
    FROM mv_incoming_call_project
    WHERE removed = false AND state = 'Активный'
    UNION ALL
    SELECT 'outcoming' as project_type, uuid as project_uuid, title as project_title, state as project_state, partneruuid as partner_uuid
    FROM mv_outcoming_call_project
    WHERE removed = false AND state = 'Активный'
) projects
WHERE partner_uuid = %(partner_uuid)s
ORDER BY project_type, project_title
"""

QUEUES_SQL = """
SELECT uuid as queue_uuid, title as queue_name, datachannel as data_channel, servicelevelparameter as target_sl, calllimit as answer_sec, state as state
FROM mv_incoming_call_project
WHERE partneruuid = %(partner_uuid)s AND removed = false AND state = 'Активный'
ORDER BY title
"""

LOAD_SQL = """
SELECT
    date_trunc('hour', que.enqueued_time) as interval_start,
    icp.uuid as queue_uuid,
    icp.title as queue_name,
    COUNT(*) as offered,
    COUNT(*) FILTER (WHERE que.final_stage = 'operator') as handled,
    COUNT(*) FILTER (WHERE COALESCE(que.final_stage, '') <> 'operator') as lost,
    ROUND(AVG(EXTRACT(EPOCH FROM (cl.ended - cl.connected))) FILTER (
        WHERE que.final_stage = 'operator' AND cl.connected IS NOT NULL AND cl.ended IS NOT NULL
    )::numeric, 2) as aht_sec,
    CASE
        WHEN MAX(icp.calllimit) > 0 THEN ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE que.final_stage = 'operator' AND que.unblocked_time_duration <= icp.calllimit * 1000
            ) / NULLIF(COUNT(*), 0), 2)
        ELSE NULL
    END as sl_percent
FROM queued_calls_ms que
JOIN mv_incoming_call_project icp ON icp.uuid = que.project_id
LEFT JOIN call_legs cl ON cl.session_id = que.session_id AND cl.leg_id = que.next_leg_id
WHERE icp.partneruuid = %(partner_uuid)s
  AND icp.removed = false
  AND icp.state = 'Активный'
  AND que.enqueued_time >= %(begin_date)s::timestamp
  AND que.enqueued_time < %(end_date)s::timestamp
GROUP BY date_trunc('hour', que.enqueued_time), icp.uuid, icp.title
ORDER BY interval_start, queue_name
"""

EMPLOYEES_SQL = """
WITH active_queues AS (
    SELECT uuid as project_uuid, title as queue_name, datachannel as data_channel, servicelevelparameter as target_sl, calllimit as answer_sec
    FROM mv_incoming_call_project
    WHERE partneruuid = %(partner_uuid)s AND removed = false AND state = 'Активный'
),
handled_calls AS (
    SELECT
        COALESCE(cl.dst_id, cl.dst_abonent) as operator_login,
        aq.queue_name as queue_name,
        aq.answer_sec as answer_sec,
        que.session_id as session_id,
        que.enqueued_time as enqueued_time,
        que.unblocked_time_duration / 1000.0 as actual_answer_sec,
        EXTRACT(EPOCH FROM (cl.ended - cl.connected)) as talk_sec
    FROM queued_calls_ms que
    JOIN active_queues aq ON aq.project_uuid = que.project_id
    LEFT JOIN call_legs cl ON cl.session_id = que.session_id AND cl.leg_id = que.next_leg_id
    WHERE que.final_stage = 'operator'
      AND que.enqueued_time >= %(begin_date)s::timestamp
      AND que.enqueued_time < %(end_date)s::timestamp
      AND COALESCE(cl.dst_id, cl.dst_abonent) IS NOT NULL
),
operator_call_metrics AS (
    SELECT
        operator_login as login,
        COUNT(*) as handled_calls_count,
        COUNT(DISTINCT queue_name) as queues_count,
        STRING_AGG(DISTINCT queue_name, '; ' ORDER BY queue_name) as queues,
        MIN(enqueued_time) as first_handled_at,
        MAX(enqueued_time) as last_handled_at,
        ROUND(AVG(actual_answer_sec)::numeric, 2) as avg_answer_sec,
        ROUND(AVG(talk_sec)::numeric, 2) as avg_talk_sec,
        ROUND(SUM(talk_sec)::numeric, 2) as total_talk_sec,
        ROUND(MAX(talk_sec)::numeric, 2) as max_talk_sec,
        ROUND(100.0 * COUNT(*) FILTER (WHERE actual_answer_sec <= answer_sec) / NULLIF(COUNT(*), 0), 2) as sl_percent
    FROM handled_calls
    GROUP BY operator_login
),
employee_skills AS (
    SELECT
        login,
        COUNT(*) as skills_count,
        COUNT(*) FILTER (WHERE active = true) as active_skills_count,
        STRING_AGG(DISTINCT CONCAT(title, ' [', code, '] lvl ', minlevel, '-', maxlevel, ', weight ', weight, ', active=', active::text), '; ' ORDER BY CONCAT(title, ' [', code, '] lvl ', minlevel, '-', maxlevel, ', weight ', weight, ', active=', active::text)) as skills
    FROM mv_skill_relation
    WHERE login IN (SELECT login FROM operator_call_metrics)
    GROUP BY login
),
status_summary AS (
    SELECT
        login,
        COUNT(*) as status_events_count,
        STRING_AGG(DISTINCT status, '; ' ORDER BY status) as statuses_seen,
        ROUND(SUM(duration)::numeric, 2) as total_status_duration,
        ROUND(SUM(duration) FILTER (WHERE status = 'normal')::numeric, 2) as normal_status_duration,
        ROUND(SUM(duration) FILTER (WHERE status <> 'normal')::numeric, 2) as non_normal_status_duration
    FROM status_changes
    WHERE login IN (SELECT login FROM operator_call_metrics)
      AND entered >= %(begin_date)s::timestamp
      AND entered < %(end_date)s::timestamp
    GROUP BY login
)
SELECT
    em.uuid as employee_uuid,
    ocm.login as login,
    em.title as employee_title,
    op.name as operator_name,
    em.removed as removed,
    em.creationdate as creation_date,
    em.removaldate as removal_date,
    em.ou as ou_uuid,
    em.outitle as ou_title,
    em.firstname as first_name,
    em.middlename as middle_name,
    em.lastname as last_name,
    em.email as email,
    em.internalphonenumber as internal_phone_number,
    em.workphonenumber as work_phone_number,
    em.mobilephonenumber as mobile_phone_number,
    em.dateofbirth as date_of_birth,
    em.post as post,
    em.department as department,
    em.timezone as timezone,
    em.cluster_id as cluster_id,
    ocm.queues_count as queues_count,
    ocm.queues as queues,
    ocm.handled_calls_count as handled_calls_count,
    ocm.first_handled_at as first_handled_at,
    ocm.last_handled_at as last_handled_at,
    ocm.avg_answer_sec as avg_answer_sec,
    ocm.avg_talk_sec as avg_talk_sec,
    ocm.total_talk_sec as total_talk_sec,
    ocm.max_talk_sec as max_talk_sec,
    ocm.sl_percent as sl_percent,
    COALESCE(es.skills_count, 0) as skills_count,
    COALESCE(es.active_skills_count, 0) as active_skills_count,
    es.skills as skills,
    COALESCE(ss.status_events_count, 0) as status_events_count,
    ss.statuses_seen as statuses_seen,
    ss.total_status_duration as total_status_duration,
    ss.normal_status_duration as normal_status_duration,
    ss.non_normal_status_duration as non_normal_status_duration
FROM operator_call_metrics ocm
LEFT JOIN mv_employee em ON em.login = ocm.login
LEFT JOIN operators op ON op.login = ocm.login
LEFT JOIN employee_skills es ON es.login = ocm.login
LEFT JOIN status_summary ss ON ss.login = ocm.login
ORDER BY ocm.handled_calls_count DESC, ocm.login
"""

OPERATOR_WORKLOAD_SQL = """
WITH handled_calls AS (
    SELECT date_trunc('hour', que.enqueued_time) as interval_start, icp.uuid as queue_uuid, icp.title as queue_name,
           COALESCE(cl.dst_id, cl.dst_abonent, 'unknown') as operator_login,
           EXTRACT(EPOCH FROM (cl.ended - cl.connected)) as talk_sec
    FROM queued_calls_ms que
    JOIN mv_incoming_call_project icp ON icp.uuid = que.project_id
    LEFT JOIN call_legs cl ON cl.session_id = que.session_id AND cl.leg_id = que.next_leg_id
    WHERE icp.partneruuid = %(partner_uuid)s AND icp.removed = false AND icp.state = 'Активный'
      AND que.final_stage = 'operator'
      AND que.enqueued_time >= %(begin_date)s::timestamp
      AND que.enqueued_time < %(end_date)s::timestamp
)
SELECT interval_start, queue_uuid, queue_name, operator_login, COUNT(*) as handled,
       ROUND(AVG(talk_sec)::numeric, 2) as aht_sec, ROUND(SUM(talk_sec)::numeric, 2) as talk_sec_total
FROM handled_calls
GROUP BY interval_start, queue_uuid, queue_name, operator_login
ORDER BY interval_start, queue_name, operator_login
"""

FORECAST_PROFILE_SQL = """
WITH hourly_load AS (
    SELECT date_trunc('hour', que.enqueued_time) as interval_start, icp.uuid as queue_uuid, icp.title as queue_name,
           COUNT(*) as offered,
           COUNT(*) FILTER (WHERE que.final_stage = 'operator') as handled,
           COUNT(*) FILTER (WHERE COALESCE(que.final_stage, '') <> 'operator') as lost,
           ROUND(AVG(EXTRACT(EPOCH FROM (cl.ended - cl.connected))) FILTER (
               WHERE que.final_stage = 'operator' AND cl.connected IS NOT NULL AND cl.ended IS NOT NULL
           )::numeric, 2) as aht,
           CASE WHEN MAX(icp.calllimit) > 0 THEN ROUND(100.0 * COUNT(*) FILTER (
               WHERE que.final_stage = 'operator' AND que.unblocked_time_duration <= icp.calllimit * 1000
           ) / NULLIF(COUNT(*), 0), 2) ELSE NULL END as sl
    FROM queued_calls_ms que
    JOIN mv_incoming_call_project icp ON icp.uuid = que.project_id
    LEFT JOIN call_legs cl ON cl.session_id = que.session_id AND cl.leg_id = que.next_leg_id
    WHERE icp.partneruuid = %(partner_uuid)s AND icp.removed = false AND icp.state = 'Активный'
      AND que.enqueued_time >= %(begin_date)s::timestamp
      AND que.enqueued_time < %(end_date)s::timestamp
    GROUP BY date_trunc('hour', que.enqueued_time), icp.uuid, icp.title
)
SELECT EXTRACT(ISODOW FROM interval_start)::int as weekday_num,
       CASE EXTRACT(ISODOW FROM interval_start)::int
           WHEN 1 THEN 'Понедельник' WHEN 2 THEN 'Вторник' WHEN 3 THEN 'Среда' WHEN 4 THEN 'Четверг'
           WHEN 5 THEN 'Пятница' WHEN 6 THEN 'Суббота' WHEN 7 THEN 'Воскресенье' END as weekday_name,
       EXTRACT(HOUR FROM interval_start)::int as hour_num,
       queue_uuid, queue_name,
       ROUND(AVG(offered)::numeric, 2) as avg_offered,
       ROUND(AVG(handled)::numeric, 2) as avg_handled,
       ROUND(AVG(lost)::numeric, 2) as avg_lost,
       ROUND(AVG(aht)::numeric, 2) as avg_aht_sec,
       ROUND(AVG(sl)::numeric, 2) as avg_sl_percent
FROM hourly_load
GROUP BY EXTRACT(ISODOW FROM interval_start)::int, EXTRACT(HOUR FROM interval_start)::int, queue_uuid, queue_name
ORDER BY weekday_num, hour_num, queue_name
"""


def normalize_name(value: str | None) -> str:
    value = (value or "").lower().replace("ё", "е")
    return re.sub(r"\s+", " ", value).strip()


def default_period() -> tuple[str, str]:
    end = date.today() + timedelta(days=1)
    begin = end - timedelta(days=7)
    return begin.isoformat(), end.isoformat()


class NaumenNccService:
    def __init__(self, db: Session):
        self.db = db

    def status(self, check: bool = True) -> dict:
        if not ncc_configured():
            return {"configured": False, "reachable": False, "status": "not_configured", "message": "Интеграция Naumen/NCC не настроена"}
        if not check:
            return {"configured": True, "reachable": None, "status": "configured", "message": "Параметры Naumen/NCC заполнены"}
        try:
            reachable = NccReadOnlyClient().ping()
            return {"configured": True, "reachable": reachable, "status": "ok" if reachable else "error", "message": "Подключение к Naumen/NCC доступно" if reachable else "Naumen/NCC не ответил"}
        except (NccConfigurationError, NccQueryError):
            return {"configured": True, "reachable": False, "status": "error", "message": "Naumen/NCC недоступен или не настроен"}

    def customers(self) -> list[dict]:
        return NccReadOnlyClient().fetch_all(CUSTOMERS_SQL)

    def projects(self, partner_uuid: str) -> list[dict]:
        return NccReadOnlyClient().fetch_all(PROJECTS_SQL, {"partner_uuid": partner_uuid})

    def queues(self, partner_uuid: str) -> list[dict]:
        return NccReadOnlyClient().fetch_all(QUEUES_SQL, {"partner_uuid": partner_uuid})

    def load(self, partner_uuid: str, begin: str, end: str) -> list[dict]:
        period = validate_period(begin, end)
        return NccReadOnlyClient().fetch_all(LOAD_SQL, {"partner_uuid": partner_uuid, **period.params})

    def employees(self, partner_uuid: str, begin: str, end: str) -> list[dict]:
        period = validate_period(begin, end)
        return NccReadOnlyClient().fetch_all(EMPLOYEES_SQL, {"partner_uuid": partner_uuid, **period.params})

    def operator_workload(self, partner_uuid: str, begin: str, end: str) -> list[dict]:
        period = validate_period(begin, end)
        return NccReadOnlyClient().fetch_all(OPERATOR_WORKLOAD_SQL, {"partner_uuid": partner_uuid, **period.params})

    def forecast_profile(self, partner_uuid: str, begin: str, end: str) -> list[dict]:
        period = validate_period(begin, end)
        return NccReadOnlyClient().fetch_all(FORECAST_PROFILE_SQL, {"partner_uuid": partner_uuid, **period.params})

    def sync_contour(self, contour: NaumenProject, begin: str, end: str) -> dict:
        partner_uuid = contour.naumen_customer_uuid or contour.partner_uuid
        if not partner_uuid:
            return {"status": "not_configured", "message": "Для контура не указан UUID Naumen/NCC. Используйте ручной режим.", "rows_by_type": {}}
        period = validate_period(begin, end)
        run = NaumenSyncRun(sync_type="ncc_sync", project_id=contour.id, partner_uuid=partner_uuid, period_begin=period.begin, period_end=period.end, status="running")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        rows_by_type: dict[str, int] = {}
        try:
            customer_rows = self.customers()
            rows_by_type["customers"] = len(customer_rows)
            project_rows = self.projects(partner_uuid)
            rows_by_type["projects"] = len(project_rows)
            queue_rows = self.queues(partner_uuid)
            rows_by_type["queues"] = self._save_queues(contour, partner_uuid, queue_rows)
            load_rows = self.load(partner_uuid, begin, end)
            rows_by_type["load"] = self._save_load(contour, partner_uuid, load_rows, run.id)
            employee_rows = self.employees(partner_uuid, begin, end)
            rows_by_type["employees"] = self._save_operators(contour, partner_uuid, employee_rows, run.id)
            operator_rows = self.operator_workload(partner_uuid, begin, end)
            rows_by_type["operator_workload"] = self._save_operator_workload(contour, partner_uuid, operator_rows, run.id)
            forecast_rows = self.forecast_profile(partner_uuid, begin, end)
            rows_by_type["forecast_profile"] = self._save_forecast(contour, partner_uuid, forecast_rows, run.id)
            run.status = "success"
            run.rows_received = sum(rows_by_type.values())
            run.rows_created = run.rows_received
            run.rows_customers = rows_by_type["customers"]
            run.rows_projects = rows_by_type["projects"]
            run.rows_queues = rows_by_type["queues"]
            run.rows_load = rows_by_type["load"]
            run.rows_employees = rows_by_type["employees"]
            run.rows_operator_workload = rows_by_type["operator_workload"]
            run.rows_forecast_profile = rows_by_type["forecast_profile"]
        except Exception as exc:
            run.status = "error"
            run.error_message = "Синхронизация Naumen/NCC завершилась ошибкой"
            self.db.commit()
            raise exc
        run.rows_by_type = json.dumps(rows_by_type, ensure_ascii=False)
        run.finished_at = utcnow()
        contour.partner_uuid = partner_uuid
        contour.naumen_customer_uuid = partner_uuid
        contour.manual_stats_enabled = False
        contour.last_sync_at = utcnow()
        self.db.commit()
        return {"status": run.status, "run_id": run.id, "rows_by_type": rows_by_type, "message": "Синхронизация Naumen/NCC завершена"}

    def _save_queues(self, contour: NaumenProject, partner_uuid: str, rows: list[dict]) -> int:
        saved = 0
        for row in rows:
            queue_uuid = str(row.get("queue_uuid") or "")
            if not queue_uuid:
                continue
            self.db.execute(text("""
                INSERT INTO ncc_queues
                (contour_id, partner_uuid, queue_uuid, queue_name, data_channel, target_sl, answer_sec, state, imported_at)
                VALUES (:contour_id, :partner_uuid, :queue_uuid, :queue_name, :data_channel, :target_sl, :answer_sec, :state, CURRENT_TIMESTAMP)
                ON CONFLICT (contour_id, queue_uuid) DO UPDATE SET
                    partner_uuid = EXCLUDED.partner_uuid,
                    queue_name = EXCLUDED.queue_name,
                    data_channel = EXCLUDED.data_channel,
                    target_sl = EXCLUDED.target_sl,
                    answer_sec = EXCLUDED.answer_sec,
                    state = EXCLUDED.state,
                    imported_at = CURRENT_TIMESTAMP
            """), {
                "contour_id": contour.id,
                "partner_uuid": partner_uuid,
                "queue_uuid": queue_uuid,
                "queue_name": row.get("queue_name"),
                "data_channel": row.get("data_channel"),
                "target_sl": float(row.get("target_sl") or 80),
                "answer_sec": int(row.get("answer_sec") or 20),
                "state": row.get("state"),
            })
            queue = self.db.query(Queue).filter(Queue.project_id == contour.id, Queue.queue_uuid == queue_uuid).first()
            if not queue:
                name = self._unique_queue_name(str(row.get("queue_name") or queue_uuid), contour.id)
                queue = Queue(project_id=contour.id, queue_uuid=queue_uuid, name=name)
                self.db.add(queue)
            desired_name = str(row.get("queue_name") or queue.name)
            if queue.name != desired_name and self.db.query(Queue).filter(Queue.name == desired_name, Queue.id != queue.id).first() is None:
                queue.name = desired_name
            queue.channel = str(row.get("data_channel") or "voice")
            queue.service_level_target = float(row.get("target_sl") or 80)
            queue.target_answer_time_sec = int(row.get("answer_sec") or 20)
            queue.is_active = True
            queue.source_system = "ncc"
            saved += 1
        self.db.flush()
        return saved

    def _unique_queue_name(self, base_name: str, contour_id: int) -> str:
        candidate = base_name.strip() or f"Очередь {contour_id}"
        if self.db.query(Queue).filter(Queue.name == candidate).first() is None:
            return candidate
        suffix = 2
        while True:
            candidate = f"{base_name} ({contour_id}-{suffix})"
            if self.db.query(Queue).filter(Queue.name == candidate).first() is None:
                return candidate
            suffix += 1

    def _queue_by_uuid(self, contour_id: int, queue_uuid: str) -> Queue | None:
        return self.db.query(Queue).filter(Queue.project_id == contour_id, Queue.queue_uuid == queue_uuid).first()

    def _save_load(self, contour: NaumenProject, partner_uuid: str, rows: list[dict], run_id: int) -> int:
        saved = 0
        for row in rows:
            offered = int(row.get("offered") or 0)
            handled = int(row.get("handled") or 0)
            lost = int(row.get("lost") or 0)
            lost_rate = round(lost / offered * 100, 2) if offered else 0
            self.db.execute(text("""
                INSERT INTO ncc_load_intervals
                (contour_id, partner_uuid, interval_start, queue_uuid, queue_name, offered, handled, lost, lost_rate, aht_sec, sl_percent, import_run_id)
                VALUES (:contour_id, :partner_uuid, :interval_start, :queue_uuid, :queue_name, :offered, :handled, :lost, :lost_rate, :aht_sec, :sl_percent, :import_run_id)
                ON CONFLICT (contour_id, interval_start, queue_uuid) DO UPDATE SET
                    partner_uuid = EXCLUDED.partner_uuid,
                    queue_name = EXCLUDED.queue_name,
                    offered = EXCLUDED.offered,
                    handled = EXCLUDED.handled,
                    lost = EXCLUDED.lost,
                    lost_rate = EXCLUDED.lost_rate,
                    aht_sec = EXCLUDED.aht_sec,
                    sl_percent = EXCLUDED.sl_percent,
                    import_run_id = EXCLUDED.import_run_id
            """), {
                "contour_id": contour.id,
                "partner_uuid": partner_uuid,
                "interval_start": row.get("interval_start"),
                "queue_uuid": row.get("queue_uuid"),
                "queue_name": row.get("queue_name"),
                "offered": offered,
                "handled": handled,
                "lost": lost,
                "lost_rate": lost_rate,
                "aht_sec": float(row.get("aht_sec") or 0),
                "sl_percent": float(row.get("sl_percent") or 0),
                "import_run_id": run_id,
            })
            queue = self._queue_by_uuid(contour.id, str(row.get("queue_uuid") or ""))
            if not queue:
                continue
            interval_start = row["interval_start"]
            interval_end = interval_start + timedelta(hours=1)
            item = self.db.query(WorkloadInterval).filter(
                WorkloadInterval.project_id == contour.id,
                WorkloadInterval.queue_id == queue.id,
                WorkloadInterval.interval_start == interval_start,
            ).first()
            if not item:
                item = WorkloadInterval(project_id=contour.id, queue_id=queue.id, interval_start=interval_start, interval_end=interval_end)
                self.db.add(item)
            item.offered_contacts = offered
            item.handled_contacts = handled
            item.abandoned_contacts = lost
            item.average_handle_time_sec = int(float(row.get("aht_sec") or 0))
            item.service_level_percent = float(row.get("sl_percent") or 0)
            item.source_system = "ncc"
            item.import_run_id = run_id
            saved += 1
        self.db.flush()
        return saved

    def _save_operators(self, contour: NaumenProject, partner_uuid: str, rows: list[dict], run_id: int) -> int:
        saved = 0
        for row in rows:
            login = str(row.get("login") or "").strip()
            employee_uuid = str(row.get("employee_uuid") or login).strip()
            if not employee_uuid and not login:
                continue
            self.db.execute(text("""
                INSERT INTO ncc_employees
                (contour_id, partner_uuid, employee_uuid, login, employee_title, operator_name, ou_title, post, department, queues_count, queues,
                 handled_calls_count, avg_answer_sec, avg_talk_sec, total_talk_sec, sl_percent, skills, statuses_seen, first_handled_at, last_handled_at, import_run_id)
                VALUES (:contour_id, :partner_uuid, :employee_uuid, :login, :employee_title, :operator_name, :ou_title, :post, :department, :queues_count, :queues,
                 :handled_calls_count, :avg_answer_sec, :avg_talk_sec, :total_talk_sec, :sl_percent, :skills, :statuses_seen, :first_handled_at, :last_handled_at, :import_run_id)
                ON CONFLICT (contour_id, employee_uuid, login) DO UPDATE SET
                    partner_uuid = EXCLUDED.partner_uuid,
                    employee_title = EXCLUDED.employee_title,
                    operator_name = EXCLUDED.operator_name,
                    ou_title = EXCLUDED.ou_title,
                    post = EXCLUDED.post,
                    department = EXCLUDED.department,
                    queues_count = EXCLUDED.queues_count,
                    queues = EXCLUDED.queues,
                    handled_calls_count = EXCLUDED.handled_calls_count,
                    avg_answer_sec = EXCLUDED.avg_answer_sec,
                    avg_talk_sec = EXCLUDED.avg_talk_sec,
                    total_talk_sec = EXCLUDED.total_talk_sec,
                    sl_percent = EXCLUDED.sl_percent,
                    skills = EXCLUDED.skills,
                    statuses_seen = EXCLUDED.statuses_seen,
                    first_handled_at = EXCLUDED.first_handled_at,
                    last_handled_at = EXCLUDED.last_handled_at,
                    import_run_id = EXCLUDED.import_run_id
            """), {
                "contour_id": contour.id,
                "partner_uuid": partner_uuid,
                "employee_uuid": employee_uuid,
                "login": login or None,
                "employee_title": row.get("employee_title"),
                "operator_name": row.get("operator_name"),
                "ou_title": row.get("ou_title"),
                "post": row.get("post"),
                "department": row.get("department"),
                "queues_count": int(row.get("queues_count") or 0),
                "queues": row.get("queues"),
                "handled_calls_count": int(row.get("handled_calls_count") or 0),
                "avg_answer_sec": row.get("avg_answer_sec"),
                "avg_talk_sec": row.get("avg_talk_sec"),
                "total_talk_sec": row.get("total_talk_sec"),
                "sl_percent": row.get("sl_percent"),
                "skills": row.get("skills"),
                "statuses_seen": row.get("statuses_seen"),
                "first_handled_at": row.get("first_handled_at"),
                "last_handled_at": row.get("last_handled_at"),
                "import_run_id": run_id,
            })
            full_name = str(row.get("employee_title") or row.get("operator_name") or " ".join(filter(None, [row.get("last_name"), row.get("first_name"), row.get("middle_name")])) or login)
            operator = self.db.query(NaumenOperator).filter(NaumenOperator.project_id == contour.id, NaumenOperator.naumen_uuid == employee_uuid).first()
            if not operator:
                operator = NaumenOperator(project_id=contour.id, naumen_uuid=employee_uuid)
                self.db.add(operator)
            parts = normalize_name(full_name).split(" ")
            operator.project_uuid = contour.project_uuid
            operator.partner_uuid = contour.naumen_customer_uuid or contour.partner_uuid
            operator.full_name = full_name
            operator.normalized_last_name = parts[0] if len(parts) > 0 else None
            operator.normalized_first_name = parts[1] if len(parts) > 1 else None
            operator.normalized_middle_name = parts[2] if len(parts) > 2 else None
            operator.login = login or None
            operator.email = row.get("email")
            operator.phone = row.get("mobile_phone_number") or row.get("work_phone_number") or row.get("internal_phone_number")
            operator.state = "Удалён" if row.get("removed") else "Активен"
            operator.skills = row.get("skills")
            operator.raw_data = json.dumps(row, ensure_ascii=False, default=str)
            operator.metrics_data = json.dumps({
                "operator_name": row.get("operator_name"),
                "queues": row.get("queues"),
                "handled_calls_count": row.get("handled_calls_count"),
                "avg_answer_sec": row.get("avg_answer_sec"),
                "avg_talk_sec": row.get("avg_talk_sec"),
                "total_talk_sec": row.get("total_talk_sec"),
                "sl_percent": row.get("sl_percent"),
                "first_handled_at": row.get("first_handled_at"),
                "last_handled_at": row.get("last_handled_at"),
                "statuses_seen": row.get("statuses_seen"),
            }, ensure_ascii=False, default=str)
            operator.last_seen_at = utcnow()
            saved += 1
        self.db.flush()
        return saved

    def _save_operator_workload(self, contour: NaumenProject, partner_uuid: str, rows: list[dict], run_id: int) -> int:
        self.db.execute(text("DELETE FROM ncc_operator_interval_stats WHERE project_id = :project_id AND import_run_id = :run_id"), {"project_id": contour.id, "run_id": run_id})
        self.db.execute(text("DELETE FROM ncc_operator_workload WHERE contour_id = :contour_id"), {"contour_id": contour.id})
        for row in rows:
            self.db.execute(text("""
                INSERT INTO ncc_operator_workload
                (contour_id, partner_uuid, interval_start, queue_uuid, queue_name, operator_login, handled, aht_sec, talk_sec_total, import_run_id)
                VALUES (:contour_id, :partner_uuid, :interval_start, :queue_uuid, :queue_name, :operator_login, :handled, :aht_sec, :talk_sec_total, :import_run_id)
            """), {"contour_id": contour.id, "partner_uuid": partner_uuid, "import_run_id": run_id, **row})
            self.db.execute(text("""
                INSERT INTO ncc_operator_interval_stats
                (project_id, partner_uuid, interval_start, queue_uuid, queue_name, operator_login, handled, aht_sec, talk_sec_total, import_run_id)
                VALUES (:project_id, :partner_uuid, :interval_start, :queue_uuid, :queue_name, :operator_login, :handled, :aht_sec, :talk_sec_total, :import_run_id)
            """), {"project_id": contour.id, "partner_uuid": partner_uuid, "import_run_id": run_id, **row})
        return len(rows)

    def _save_forecast(self, contour: NaumenProject, partner_uuid: str, rows: list[dict], run_id: int) -> int:
        self.db.execute(text("DELETE FROM ncc_forecast_profiles WHERE project_id = :project_id AND import_run_id = :run_id"), {"project_id": contour.id, "run_id": run_id})
        for row in rows:
            self.db.execute(text("""
                INSERT INTO ncc_forecast_profile
                (contour_id, partner_uuid, weekday_num, weekday_name, hour_num, queue_uuid, queue_name, avg_offered, avg_handled, avg_lost, avg_aht_sec, avg_sl_percent, import_run_id)
                VALUES (:contour_id, :partner_uuid, :weekday_num, :weekday_name, :hour_num, :queue_uuid, :queue_name, :avg_offered, :avg_handled, :avg_lost, :avg_aht_sec, :avg_sl_percent, :import_run_id)
                ON CONFLICT (contour_id, weekday_num, hour_num, queue_uuid) DO UPDATE SET
                    partner_uuid = EXCLUDED.partner_uuid,
                    queue_name = EXCLUDED.queue_name,
                    avg_offered = EXCLUDED.avg_offered,
                    avg_handled = EXCLUDED.avg_handled,
                    avg_lost = EXCLUDED.avg_lost,
                    avg_aht_sec = EXCLUDED.avg_aht_sec,
                    avg_sl_percent = EXCLUDED.avg_sl_percent,
                    import_run_id = EXCLUDED.import_run_id
            """), {"contour_id": contour.id, "partner_uuid": partner_uuid, "import_run_id": run_id, **row})
            self.db.execute(text("""
                INSERT INTO ncc_forecast_profiles
                (project_id, partner_uuid, weekday_num, weekday_name, hour_num, queue_uuid, queue_name, avg_offered, avg_handled, avg_lost, avg_aht_sec, avg_sl_percent, import_run_id)
                VALUES (:project_id, :partner_uuid, :weekday_num, :weekday_name, :hour_num, :queue_uuid, :queue_name, :avg_offered, :avg_handled, :avg_lost, :avg_aht_sec, :avg_sl_percent, :import_run_id)
            """), {"project_id": contour.id, "partner_uuid": partner_uuid, "import_run_id": run_id, **row})
        return len(rows)

    def match_employee(self, employee: Employee, contour: NaumenProject, begin: str, end: str) -> dict:
        partner_uuid = contour.naumen_customer_uuid or contour.partner_uuid
        if not partner_uuid:
            return {"status": "check_error", "message": "Для активного контура не указан UUID Naumen/NCC"}
        rows = self.employees(partner_uuid, begin, end)
        normalized = normalize_name(employee.full_name)
        by_uuid = [row for row in rows if employee.naumen_uuid and row.get("employee_uuid") == employee.naumen_uuid]
        if len(by_uuid) == 1:
            return {"status": "linked", "message": "Сотрудник сопоставлен по сохранённому UUID Naumen.", "operator": by_uuid[0]}
        matches = [row for row in rows if normalize_name(str(row.get("employee_title") or row.get("operator_name") or "")) == normalized]
        if len(matches) == 1:
            return {"status": "linked", "message": "Сотрудник сопоставлен с Naumen/NCC по ФИО.", "operator": matches[0]}
        if len(matches) > 1:
            return {"status": "mismatch", "message": "Найдено несколько операторов Naumen/NCC с таким ФИО. Требуется ручной выбор.", "candidates": matches}
        return {"status": "not_found", "message": "Сотрудник не найден в Naumen/NCC за выбранный период."}
