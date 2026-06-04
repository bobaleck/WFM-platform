from __future__ import annotations

import platform
from datetime import datetime

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.integrations.onec.client import OneCClientError, OneCGatewayClient
from app.integrations.onec.schemas import OneCEmployeeStatus
from app.models.integration_settings import OneCConnectionSettings


def get_or_create_onec_settings(db: Session) -> OneCConnectionSettings:
    item = db.query(OneCConnectionSettings).order_by(OneCConnectionSettings.id).first()
    if item:
        return item
    item = OneCConnectionSettings(connection_mode="gateway_http")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def onec_configured(item: OneCConnectionSettings) -> bool:
    if not item.enabled:
        return False
    if item.connection_mode == "gateway_http":
        return not missing_settings_fields(item)
    return item.connection_mode == "direct_com" and platform.system().lower() == "windows"


def _decrypt(encrypted: str | None) -> str | None:
    if not encrypted:
        return None
    return Fernet(app_settings.integration_secret_key.encode("utf-8")).decrypt(encrypted.encode("utf-8")).decode("utf-8")


def onec_password(item: OneCConnectionSettings) -> str | None:
    return _decrypt(getattr(item, "onec_password_encrypted", None) or item.password_encrypted)


def gateway_token(item: OneCConnectionSettings) -> str | None:
    return _decrypt(getattr(item, "gateway_token_encrypted", None))


def effective_value(item: OneCConnectionSettings, new_name: str, old_name: str) -> str | None:
    return getattr(item, new_name, None) or getattr(item, old_name, None)


def missing_settings_fields(item: OneCConnectionSettings, require_password: bool = True) -> list[str]:
    if item.connection_mode == "direct_com":
        return []
    missing: list[str] = []
    if not item.gateway_url:
        missing.append("gateway_url")
    if not effective_value(item, "onec_username", "username"):
        missing.append("onec_username")
    if require_password and not (getattr(item, "onec_password_encrypted", None) or item.password_encrypted):
        missing.append("onec_password")
    infobase_type = getattr(item, "infobase_type", "server") or "server"
    if infobase_type == "file":
        if not effective_value(item, "file_base_path", "infobase_path"):
            missing.append("file_base_path")
    else:
        if not effective_value(item, "onec_server", "server"):
            missing.append("onec_server")
        if not effective_value(item, "onec_database", "database"):
            missing.append("onec_database")
    return missing


class OneCService:
    def __init__(self, settings: OneCConnectionSettings) -> None:
        self.settings = settings

    def diagnose(self) -> dict:
        server_os = platform.system().lower()
        direct_com_available = server_os == "windows"
        missing = missing_settings_fields(self.settings)
        base_result = {
            "server_os": server_os,
            "connection_mode": self.settings.connection_mode,
            "gateway_url_present": bool(self.settings.gateway_url),
            "gateway_url_safe": self.settings.gateway_url,
            "infobase_type": getattr(self.settings, "infobase_type", "server") or "server",
            "onec_server_present": bool(effective_value(self.settings, "onec_server", "server")),
            "onec_database_present": bool(effective_value(self.settings, "onec_database", "database")),
            "file_base_path_present": bool(effective_value(self.settings, "file_base_path", "infobase_path")),
            "onec_username_present": bool(effective_value(self.settings, "onec_username", "username")),
            "onec_password_present": bool(getattr(self.settings, "onec_password_encrypted", None) or self.settings.password_encrypted),
            "gateway_token_present": bool(getattr(self.settings, "gateway_token_encrypted", None)),
            "direct_com_available": direct_com_available,
            "direct_com_message": "Direct COM недоступен на Linux" if not direct_com_available else "Direct COM доступен на Windows-хосте",
            "settings_valid": not missing,
            "missing_fields": missing,
        }
        if self.settings.connection_mode == "direct_com" and platform.system().lower() != "windows":
            return base_result | {
                "status": "unsupported",
                "message": "Direct COM недоступен на Linux. Используйте Windows 1C Gateway.",
            }
        if self.settings.connection_mode == "gateway_http":
            if not self.settings.gateway_url:
                return base_result | {"status": "not_configured", "message": "Укажите внутренний адрес Windows Gateway."}
            if missing:
                return base_result | {"status": "not_configured", "message": "Заполните параметры подключения к базе 1С."}
            return base_result | {"status": "not_checked", "message": "Настройки заполнены. Нажмите «Проверить подключение» для read-only проверки через Windows Gateway."}
        return base_result | {"status": "unsupported", "message": "Режим подключения не поддерживается."}

    def check_connection(self) -> dict:
        diagnostic = self.diagnose()
        if diagnostic["status"] in {"unsupported", "not_configured"}:
            return diagnostic
        if self.settings.connection_mode != "gateway_http":
            return diagnostic | {"status": "unsupported", "message": "Режим подключения не поддерживается."}
        payload = {
            "infobase_type": getattr(self.settings, "infobase_type", "server") or "server",
            "server": effective_value(self.settings, "onec_server", "server") or "",
            "database": effective_value(self.settings, "onec_database", "database") or "",
            "cluster": effective_value(self.settings, "onec_cluster", "cluster") or "",
            "file_base_path": effective_value(self.settings, "file_base_path", "infobase_path") or "",
            "username": effective_value(self.settings, "onec_username", "username") or "",
            "password": onec_password(self.settings) or "",
        }
        try:
            result = OneCGatewayClient(
                self.settings.gateway_url or "",
                timeout=self.settings.request_timeout_seconds,
                verify_tls=self.settings.verify_tls,
                gateway_token=gateway_token(self.settings),
            ).check_connection(payload)
            return diagnostic | {
                "status": str(result.get("status") or "ok"),
                "message": str(result.get("message") or "Подключение к 1С проверено через Windows Gateway."),
                "gateway": {"status": result.get("status"), "service": result.get("service"), "gateway_version": result.get("gateway_version")},
                "gateway_version": result.get("gateway_version"),
            }
        except OneCClientError:
            return diagnostic | {
                "status": "error",
                "message": "Windows Gateway недоступен. Установите Gateway на Windows-сервере с платформой 1С.",
            }

    def _connection_payload(self) -> dict:
        return {
            "infobase_type": getattr(self.settings, "infobase_type", "server") or "server",
            "server": effective_value(self.settings, "onec_server", "server") or "",
            "database": effective_value(self.settings, "onec_database", "database") or "",
            "cluster": effective_value(self.settings, "onec_cluster", "cluster") or "",
            "file_base_path": effective_value(self.settings, "file_base_path", "infobase_path") or "",
            "username": effective_value(self.settings, "onec_username", "username") or "",
            "password": onec_password(self.settings) or "",
        }

    def check_employee_status_by_inn(self, inn: str) -> OneCEmployeeStatus:
        if not onec_configured(self.settings):
            return OneCEmployeeStatus.error(inn, "Настройки подключения к 1С не заполнены или интеграция выключена.")
        if self.settings.connection_mode == "direct_com" and platform.system().lower() != "windows":
            return OneCEmployeeStatus.error(inn, "Direct COM недоступен на Linux. Используйте Windows 1C Gateway.")
        if self.settings.connection_mode != "gateway_http":
            return OneCEmployeeStatus.error(inn, "Поддержан только режим Windows Gateway.")
        try:
            request_payload = self._connection_payload() | {"inn": inn}
            payload = OneCGatewayClient(
                self.settings.gateway_url or "",
                timeout=self.settings.request_timeout_seconds,
                verify_tls=self.settings.verify_tls,
                gateway_token=gateway_token(self.settings),
            ).check_employee_status(request_payload)
            return OneCEmployeeStatus.from_gateway(inn, payload)
        except OneCClientError as exc:
            if exc.http_status == 404:
                return OneCEmployeeStatus.gateway_invalid(inn, "Gateway доступен, но метод сверки сотрудника не реализован.")
            return OneCEmployeeStatus.gateway_unavailable(inn)

    def diagnose_employee_lookup(self, inn: str) -> dict:
        diagnostic = self.diagnose()
        if diagnostic["status"] in {"unsupported", "not_configured"}:
            return diagnostic
        try:
            result = OneCGatewayClient(
                self.settings.gateway_url or "",
                timeout=self.settings.request_timeout_seconds,
                verify_tls=self.settings.verify_tls,
                gateway_token=gateway_token(self.settings),
            ).diagnose_employee_lookup(inn)
            return {
                "status": str(result.get("status") or "ok"),
                "message": str(result.get("message") or "Диагностика поиска сотрудника выполнена."),
                "inn": inn,
                "gateway_version": result.get("gateway_version"),
                "found_person": result.get("found_person", result.get("found")),
                "cards_found": result.get("cards_found"),
                "lookup_strategy_used": result.get("lookup_strategy_used"),
                "cards": result.get("cards") if isinstance(result.get("cards"), list) else [],
                "query_warnings": result.get("query_warnings") if isinstance(result.get("query_warnings"), list) else [],
                "query_errors": result.get("query_errors") if isinstance(result.get("query_errors"), list) else [],
                "recommendation": result.get("recommendation") or "Если карточки не найдены, обновите gateway.ps1 на Windows Server и повторите диагностику.",
            }
        except OneCClientError as exc:
            if exc.http_status == 404:
                return {
                    "status": "gateway_invalid",
                    "message": "Текущий Gateway не поддерживает диагностику. Обновите gateway.ps1 на Windows Server.",
                    "inn": inn,
                }
            return {
                "status": "gateway_unavailable",
                "message": "Windows Gateway недоступен.",
                "inn": inn,
            }


def update_settings_check_state(item: OneCConnectionSettings, result: dict) -> None:
    item.last_check_status = str(result.get("status") or "error")
    item.last_check_message = str(result.get("message") or "")
    item.last_check_at = datetime.utcnow()
