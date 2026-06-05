from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Iterator, Sequence

import psycopg
from psycopg.rows import dict_row

from app.core.config import settings


ALLOWED_TABLES = {
    "mv_partner",
    "mv_incoming_call_project",
    "mv_outcoming_call_project",
    "queued_calls_ms",
    "call_legs",
    "mv_employee",
    "operators",
    "mv_skill_relation",
    "status_changes",
}

ALLOWED_CTES = {
    "active_projects",
    "projects",
    "active_queues",
    "handled_calls",
    "operator_call_metrics",
    "employee_skills",
    "status_summary",
    "hourly_load",
}


class NccConfigurationError(Exception):
    pass


class NccQueryError(Exception):
    pass


@dataclass(frozen=True)
class NccPeriod:
    begin: date
    end: date

    @property
    def params(self) -> dict[str, str]:
        return {"begin_date": self.begin.isoformat(), "end_date": self.end.isoformat()}


def ncc_configured() -> bool:
    return all([settings.ncc_db_host, settings.ncc_db_name, settings.ncc_db_user, settings.ncc_db_password])


def validate_period(begin: str, end: str) -> NccPeriod:
    try:
        begin_date = datetime.strptime(begin, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Период должен быть в формате YYYY-MM-DD") from exc
    if end_date <= begin_date:
        raise ValueError("Дата окончания должна быть позже даты начала")
    if (end_date - begin_date).days > settings.ncc_db_max_period_days:
        raise ValueError(f"Период не должен превышать {settings.ncc_db_max_period_days} дней")
    return NccPeriod(begin_date, end_date)


class NccReadOnlyClient:
    def __init__(self) -> None:
        if not ncc_configured():
            raise NccConfigurationError("Интеграция Naumen/NCC не настроена")

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection]:
        try:
            with psycopg.connect(
                host=settings.ncc_db_host,
                port=settings.ncc_db_port,
                dbname=settings.ncc_db_name,
                user=settings.ncc_db_user,
                password=settings.ncc_db_password,
                connect_timeout=settings.ncc_db_timeout_seconds,
                options="-c default_transaction_read_only=on -c statement_timeout=30000",
                row_factory=dict_row,
            ) as connection:
                yield connection
        except NccConfigurationError:
            raise
        except Exception as exc:
            raise NccQueryError("Не удалось выполнить безопасный read-only запрос к Naumen/NCC") from exc

    def fetch_all(self, sql: str, params: dict | None = None) -> list[dict]:
        self._assert_safe_select(sql)
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or {})
                return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, sql: str, params: dict | None = None) -> dict | None:
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    def ping(self) -> bool:
        row = self.fetch_one("SELECT 1 as ok", {})
        return bool(row and row.get("ok") == 1)

    @staticmethod
    def _assert_safe_select(sql: str) -> None:
        lowered = " ".join(sql.lower().split())
        forbidden = (" insert ", " update ", " delete ", " drop ", " alter ", " truncate ", " create ", " grant ", " revoke ")
        if not lowered.startswith("select") and not lowered.startswith("with"):
            raise NccQueryError("Разрешены только SELECT-запросы")
        if any(token in f" {lowered} " for token in forbidden):
            raise NccQueryError("Запрос содержит запрещённую операцию")
        referenced = {
            match.group(1).split(".")[-1].strip('"')
            for match in re.finditer(r"\b(?:from|join)\s+([a-zA-Z_][\w.\"$]*)", lowered)
        }
        if referenced and not referenced.issubset(ALLOWED_TABLES | ALLOWED_CTES):
            raise NccQueryError("Запрос обращается к неразрешённой таблице NCC")


def safe_rows(rows: Sequence[dict]) -> list[dict]:
    return [dict(row) for row in rows]
