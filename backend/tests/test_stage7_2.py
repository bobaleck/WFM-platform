import json
import os
import subprocess
import urllib.error
import urllib.request

import pytest

from app.core.rbac import required_permission
from app.integrations.naumen.client import NaumenClient

pytestmark = pytest.mark.skip(reason="Legacy Naumen stage tests отключены: Naumen удалён из рабочего API на этапе 9.1")


BASE_URL = "http://127.0.0.1:8000"


def admin_token() -> str:
    payload = json.dumps({
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "Admin12345!"),
    }).encode("utf-8")
    request = urllib.request.Request(f"{BASE_URL}/api/v1/auth/login", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))["access_token"]


def http_json(path: str, token: str | None = None, method: str = "GET", payload: dict | None = None):
    body = json.dumps(payload or {}).encode("utf-8") if method in {"POST", "PUT"} else None
    request = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method, headers={"Content-Type": "application/json"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def test_clear_demo_data_requires_confirm():
    result = subprocess.run(["/opt/wfm-naumen/scripts/clear-demo-data.sh"], text=True, capture_output=True, check=False)
    assert result.returncode != 0
    assert "--confirm" in result.stderr


def test_admin_saved_and_business_tables_cleaned():
    token = admin_token()
    users = http_json("/api/v1/users", token)
    assert any(user["username"] == "admin" for user in users)
    assert http_json("/api/v1/employees", token) == []
    assert http_json("/api/v1/teams", token) == []
    assert http_json("/api/v1/queues", token) == []


def test_roles_and_permissions_preserved():
    token = admin_token()
    assert len(http_json("/api/v1/roles", token)) > 0
    assert len(http_json("/api/v1/permissions", token)) > 0


def test_naumen_settings_do_not_return_plain_secret_and_empty_secret_preserves_value():
    token = admin_token()
    first = http_json("/api/v1/integrations/naumen/settings", token, method="PUT", payload={
        "base_url": "http://naumen.local",
        "auth_mode": "api_key",
        "username": "local-user",
        "api_key": "secret-api-key",
        "basic_password": "",
        "request_timeout_seconds": 20,
        "verify_ssl": True,
        "enabled": True,
    })
    assert "secret-api-key" not in json.dumps(first)
    assert first["api_key_masked"]

    second = http_json("/api/v1/integrations/naumen/settings", token, method="PUT", payload={
        "base_url": "http://naumen.local",
        "auth_mode": "api_key",
        "username": "local-user",
        "api_key": "",
        "basic_password": "",
        "request_timeout_seconds": 20,
        "verify_ssl": True,
        "enabled": True,
    })
    assert second["api_key_masked"] == first["api_key_masked"]


def test_naumen_check_returns_not_configured_when_disabled():
    token = admin_token()
    http_json("/api/v1/integrations/naumen/settings", token, method="PUT", payload={
        "base_url": "",
        "auth_mode": "api_key",
        "username": "",
        "api_key": "",
        "basic_password": "",
        "request_timeout_seconds": 30,
        "verify_ssl": True,
        "enabled": False,
    })
    result = http_json("/api/v1/integrations/naumen/check", token, method="POST")
    assert result["status"] == "not_configured"


def test_naumen_client_builds_headers_by_auth_mode():
    api = NaumenClient(base_url="http://local", auth_mode="api_key", username="u", api_key="k")
    assert api.build_headers()["Username"] == "u"
    assert api.build_headers()["X-API-Key"] == "k"

    basic = NaumenClient(base_url="http://local", auth_mode="basic", username="u", basic_password="p")
    assert basic.build_headers()["Authorization"].startswith("Basic ")


def test_employees_sync_dry_run_does_not_save_business_data_and_creates_run():
    token = admin_token()
    before = http_json("/api/v1/employees", token)
    result = http_json("/api/v1/integrations/naumen/sync/employees", token, method="POST", payload={"dry_run": True})
    after = http_json("/api/v1/employees", token)
    assert before == after
    assert result["sync_run_id"] > 0
    assert result["status"] in {"not_configured", "pending"}
    runs = http_json("/api/v1/integrations/naumen/sync-runs", token)
    assert any(run["id"] == result["sync_run_id"] for run in runs)


def test_protected_integration_routes_require_auth():
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/v1/integrations/naumen/settings", timeout=10)
    except urllib.error.HTTPError as exc:
        assert exc.code == 401
    else:
        raise AssertionError("integration settings did not require auth")


def test_settings_manage_permission_is_required_for_put():
    assert required_permission("/api/v1/integrations/naumen/settings", "PUT") == "settings:manage"
    assert required_permission("/api/v1/integrations/naumen/sync/employees", "POST") == "settings:manage"
