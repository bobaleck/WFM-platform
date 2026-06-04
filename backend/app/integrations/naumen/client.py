from __future__ import annotations

import base64
import json
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class NaumenClientError(RuntimeError):
    def __init__(self, message: str, http_status: int | None = None, endpoint: str | None = None) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.endpoint = endpoint


@dataclass
class NaumenClient:
    base_url: str
    auth_mode: str
    username: str
    api_version: str = "v2"
    api_key: str | None = None
    basic_password: str | None = None
    timeout_seconds: int = 30
    verify_ssl: bool = True
    last_endpoint: str | None = None
    last_http_status: int | None = None

    def api_prefix(self) -> str:
        if self.api_version not in {"v2", "current"}:
            raise NaumenClientError("Поддерживаются только Naumen API v2/current")
        return f"/api/{self.api_version}"

    def _api_path(self, endpoint: str) -> str:
        return f"{self.api_prefix()}/{endpoint.lstrip('/')}"

    def build_url(self, endpoint: str, params: dict[str, object] | None = None) -> str:
        path = self._api_path(endpoint)
        query = f"?{urlencode(params)}" if params else ""
        return f"{self.base_url.rstrip('/')}{path}{query}"

    def build_safe_url(self, endpoint: str) -> str:
        return self.build_url(endpoint)

    def build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.auth_mode == "api_key":
            headers["Username"] = self.username
            headers["X-API-Key"] = self.api_key or ""
            return headers
        if self.auth_mode == "basic":
            token = base64.b64encode(f"{self.username}:{self.basic_password or ''}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
            return headers
        raise NaumenClientError("Неподдерживаемый режим авторизации Naumen")

    def _get_json(self, endpoint: str, params: dict[str, object] | None = None) -> Any:
        url = self.build_url(endpoint, params)
        self.last_endpoint = self._api_path(endpoint)
        self.last_http_status = None
        context = None if self.verify_ssl else ssl._create_unverified_context()
        request = Request(url, headers=self.build_headers(), method="GET")
        try:
            with urlopen(request, timeout=self.timeout_seconds, context=context) as response:
                self.last_http_status = response.status
                charset = response.headers.get_content_charset() or "utf-8"
                payload = response.read().decode(charset)
                return json.loads(payload) if payload else {}
        except HTTPError as exc:
            self.last_http_status = exc.code
            messages = {
                401: "Ошибка авторизации Naumen",
                403: "Нет прав на endpoint Naumen",
                404: "Объект или endpoint Naumen не найден",
                501: "Naumen не поддерживает endpoint в текущем режиме назначения операторов",
            }
            raise NaumenClientError(messages.get(exc.code, f"Naumen HTTP {exc.code}"), exc.code, self.last_endpoint) from exc
        except URLError as exc:
            raise NaumenClientError("Timeout или ошибка сетевого обращения к Naumen", None, self.last_endpoint) from exc

    def check_connection(self) -> dict[str, Any]:
        data = self.get_partners()
        items = data.get("items", []) if isinstance(data, dict) else []
        return {
            "status": "ok",
            "message": "Подключение проверено через список партнёров Naumen",
            "http_status": self.last_http_status,
            "endpoint": self.last_endpoint,
            "items_count": len(items) if isinstance(items, list) else 0,
            "data": data,
        }

    def get_partners(self) -> Any:
        return self._get_json("/partners/")

    def get_project(self, project_uuid: str) -> Any:
        return self._get_json(f"/projects/{project_uuid}")

    def get_employees(self, removed: bool = False) -> Any:
        return self._get_json("/employees", {"removed": str(removed).lower()})

    def get_employee(self, employee_login: str) -> Any:
        return self._get_json(f"/employees/{employee_login}")

    def get_departments(self) -> Any:
        return self._get_json("/ous/root/subous")

    def get_project_agents(self, project_uuid: str) -> Any:
        return self._get_json(f"/projects/{project_uuid}/agents")

    def get_available_project_agents(self, project_uuid: str) -> Any:
        return self._get_json(f"/projects/{project_uuid}/agents/available")

    def get_project_schedule(self, project_uuid: str) -> Any:
        return self._get_json(f"/projects/{project_uuid}/schedule")

    def build_call_recording_reference(self, call_uuid: str) -> dict[str, str]:
        return {"status": "pending", "resource": "call_recording", "call_uuid": call_uuid}

    def get_queues(self) -> dict[str, str]:
        return {"status": "pending", "resource": "queues"}

    def get_agents(self) -> Any:
        return self.get_employees()

    def get_calls(self) -> dict[str, str]:
        return {"status": "pending", "resource": "calls"}

    def get_recordings(self) -> dict[str, str]:
        return {"status": "pending", "resource": "recordings"}
