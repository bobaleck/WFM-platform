from __future__ import annotations

from dataclasses import dataclass


STATUS_LABELS = {
    "not_checked": "Не проверялся",
    "working": "Работает",
    "dismissed": "Уволен",
    "not_found": "Не найден",
    "not_found_person_cards": "Карточки сотрудника не найдены",
    "check_error": "Ошибка сверки",
    "gateway_unavailable": "Gateway недоступен",
    "gateway_invalid": "Gateway некорректен",
    "gateway_timeout": "Таймаут Gateway",
    "onec_connection_error": "Ошибка подключения к 1С",
    "error": "Ошибка сверки",
}

BUSINESS_STATUSES = {
    "working",
    "dismissed",
    "not_found",
    "not_found_person_cards",
    "check_error",
    "gateway_unavailable",
    "gateway_invalid",
    "gateway_timeout",
    "onec_connection_error",
}


@dataclass
class OneCEmployeeStatus:
    status: str
    status_label: str
    found: bool
    inn: str
    full_name: str | None = None
    active_cards_count: int = 0
    dismissed_cards_count: int = 0
    last_hire_date: str | None = None
    last_dismissal_date: str | None = None
    organization: str | None = None
    message: str = ""
    raw_summary: dict | None = None
    lookup_strategy_used: str | None = None
    cards: list | None = None
    query_warnings: list | None = None
    query_errors: list | None = None
    gateway_version: str | None = None
    gateway_warning: str | None = None

    @classmethod
    def from_gateway(cls, inn: str, payload: dict) -> "OneCEmployeeStatus":
        status = str(payload.get("status") or "check_error")
        if status == "error":
            status = "check_error"
        if status == "ok":
            status = "check_error"
        message = str(payload.get("message") or "")
        found = bool(payload.get("found", status in {"working", "dismissed"}))
        if status == "not_found" and found and "карточ" in message.lower():
            status = "not_found_person_cards"
        if status not in BUSINESS_STATUSES:
            status = "gateway_invalid"
        gateway_version = str(payload.get("gateway_version") or "") or None
        gateway_warning = None
        if gateway_version and gateway_version < "2026-06-02.2":
            gateway_warning = "Gateway устарел. Обновите gateway.ps1 на Windows Server."
        return cls(
            status=status,
            status_label=STATUS_LABELS.get(status, status) if status == "not_found_person_cards" else str(payload.get("status_label") or STATUS_LABELS.get(status, status)),
            found=found,
            inn=str(payload.get("inn") or inn),
            full_name=payload.get("full_name"),
            active_cards_count=int(payload.get("active_cards_count") or 0),
            dismissed_cards_count=int(payload.get("dismissed_cards_count") or 0),
            last_hire_date=payload.get("last_hire_date"),
            last_dismissal_date=payload.get("last_dismissal_date"),
            organization=payload.get("organization"),
            message=(gateway_warning + " " if gateway_warning else "") + (message or ""),
            raw_summary=payload.get("raw_summary") if isinstance(payload.get("raw_summary"), dict) else payload,
            lookup_strategy_used=payload.get("lookup_strategy_used"),
            cards=payload.get("cards") if isinstance(payload.get("cards"), list) else [],
            query_warnings=payload.get("query_warnings") if isinstance(payload.get("query_warnings"), list) else [],
            query_errors=payload.get("query_errors") if isinstance(payload.get("query_errors"), list) else [],
            gateway_version=gateway_version,
            gateway_warning=gateway_warning,
        )

    @classmethod
    def error(cls, inn: str, message: str) -> "OneCEmployeeStatus":
        return cls(status="check_error", status_label=STATUS_LABELS["check_error"], found=False, inn=inn, message=message)

    @classmethod
    def gateway_unavailable(cls, inn: str) -> "OneCEmployeeStatus":
        return cls(status="gateway_unavailable", status_label=STATUS_LABELS["gateway_unavailable"], found=False, inn=inn, message="Windows Gateway недоступен.")

    @classmethod
    def gateway_invalid(cls, inn: str, message: str) -> "OneCEmployeeStatus":
        return cls(status="gateway_invalid", status_label=STATUS_LABELS["gateway_invalid"], found=False, inn=inn, message=message)
