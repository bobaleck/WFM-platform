from __future__ import annotations

import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class OneCClientError(Exception):
    def __init__(self, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.http_status = http_status


class OneCGatewayClient:
    def __init__(self, gateway_url: str, timeout: int = 30, verify_tls: bool = True, gateway_token: str | None = None) -> None:
        self.gateway_url = gateway_url.rstrip("/") + "/"
        self.timeout = timeout
        self.verify_tls = verify_tls
        self.gateway_token = gateway_token

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body or {}).encode("utf-8") if body is not None else None
        request = Request(
            urljoin(self.gateway_url, path.lstrip("/")),
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        if self.gateway_token:
            request.add_header("Authorization", f"Bearer {self.gateway_token}")
        context = None if self.verify_tls else ssl._create_unverified_context()
        try:
            with urlopen(request, timeout=self.timeout, context=context) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            raise OneCClientError(f"Gateway вернул HTTP {exc.code}", exc.code) from exc
        except URLError as exc:
            raise OneCClientError("Не удалось подключиться к 1С Gateway") from exc
        except json.JSONDecodeError as exc:
            raise OneCClientError("Gateway вернул некорректный JSON") from exc

    def health(self) -> dict:
        return self._request("GET", "/health")

    def check_connection(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/1c/check-connection", payload)

    def check_employee_status(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/1c/check-employee-status", payload)

    def diagnose_employee_lookup(self, inn: str) -> dict:
        return self._request("POST", "/api/v1/1c/diagnose-employee-lookup", {"inn": inn})
