import json
import os
import time
import urllib.error
import urllib.request

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.integrations.naumen.client import NaumenClient
from app.integrations.naumen import service as naumen_service
from app.models.integration_settings import Base, NaumenConnectionSettings, NaumenPartner

pytestmark = pytest.mark.skip(reason="Legacy Naumen stage tests отключены: Naumen удалён из рабочего API на этапе 9.1")


BASE_URL = "http://127.0.0.1:8000"


def request_json(path: str, token: str | None = None, method: str = "GET", payload: dict | None = None):
    body = json.dumps(payload or {}).encode("utf-8") if method in {"POST", "PUT"} else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method, headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def token(username: str = "admin", password: str | None = None) -> str:
    payload = {"username": username, "password": password or os.getenv("ADMIN_PASSWORD", "Admin12345!")}
    return request_json("/api/v1/auth/login", method="POST", payload=payload)["access_token"]


def create_project(admin_token: str, uuid: str, title: str):
    return request_json("/api/v1/projects", admin_token, "POST", {
        "project_uuid": uuid,
        "title": title,
        "partner_uuid": None,
        "state": "active",
        "data_channel": "voice",
        "cluster_id": 0,
        "is_active": True,
        "is_default": False,
    })


def test_naumen_client_builds_versioned_urls_and_auth_headers():
    api = NaumenClient(base_url="http://naumen.local", api_version="v2", auth_mode="api_key", username="u", api_key="k")
    assert api.build_url("/employees", {"removed": "false"}) == "http://naumen.local/api/v2/employees?removed=false"
    assert api.build_headers()["Username"] == "u"
    assert api.build_headers()["X-API-Key"] == "k"
    current = NaumenClient(base_url="http://naumen.local", api_version="current", auth_mode="basic", username="u", basic_password="p")
    assert current.build_url("/projects/abc") == "http://naumen.local/api/current/projects/abc"
    assert current.build_headers()["Authorization"].startswith("Basic ")


def test_naumen_client_get_partners_builds_expected_endpoint(monkeypatch):
    seen = {}

    def fake_get_json(self, endpoint, params=None):
        seen["endpoint"] = self._api_path(endpoint)
        return {"items": [{"uuid": "p1", "title": "Партнёр"}]}

    monkeypatch.setattr(NaumenClient, "_get_json", fake_get_json)
    api = NaumenClient(base_url="http://naumen.local", api_version="v2", auth_mode="api_key", username="u", api_key="k")
    assert api.get_partners()["items"][0]["title"] == "Партнёр"
    assert seen["endpoint"] == "/api/v2/partners/"
    current = NaumenClient(base_url="http://naumen.local", api_version="current", auth_mode="api_key", username="u", api_key="k")
    current.get_partners()
    assert seen["endpoint"] == "/api/current/partners/"


def test_naumen_check_connection_uses_partners(monkeypatch):
    endpoints = []

    def fake_get_json(self, endpoint, params=None):
        endpoints.append(endpoint)
        self.last_endpoint = self._api_path(endpoint)
        self.last_http_status = 200
        return {"items": [{"uuid": "p1", "title": "Партнёр"}]}

    monkeypatch.setattr(NaumenClient, "_get_json", fake_get_json)
    api = NaumenClient(base_url="http://naumen.local", api_version="v2", auth_mode="api_key", username="u", api_key="k")
    result = api.check_connection()
    assert endpoints == ["/partners/"]
    assert result["endpoint"] == "/api/v2/partners/"
    assert result["items_count"] == 1


def test_invalid_base_url_with_api_path_is_blocked():
    assert naumen_service.base_url_has_endpoint_path("https://host:8443/api/v2")
    assert naumen_service.base_url_has_endpoint_path("https://host:8443/catalogs/items")
    assert not naumen_service.base_url_has_endpoint_path("https://host:8443")


def test_partners_dry_run_does_not_save(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    settings = NaumenConnectionSettings(
        base_url="http://naumen.local",
        api_version="v2",
        auth_mode="api_key",
        username="u",
        api_key_encrypted="stored",
        enabled=True,
    )

    class FakeClient:
        last_endpoint = "/api/v2/partners/"
        last_http_status = 200

        def get_partners(self):
            return {"items": [{"uuid": "p1", "title": "Партнёр"}]}

    monkeypatch.setattr(naumen_service, "client_from_settings", lambda _: FakeClient())
    result = naumen_service.sync_partners(db, settings, dry_run=True)
    assert result["rows_received"] == 1
    assert db.query(NaumenPartner).count() == 0


def test_partners_sync_saves_and_updates(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    settings = NaumenConnectionSettings(
        base_url="http://naumen.local",
        api_version="v2",
        auth_mode="api_key",
        username="u",
        api_key_encrypted="stored",
        enabled=True,
    )

    class FakeClient:
        last_endpoint = "/api/v2/partners/"
        last_http_status = 200

        def get_partners(self):
            return {"items": [{"uuid": "p1", "title": "Партнёр 1"}]}

    monkeypatch.setattr(naumen_service, "client_from_settings", lambda _: FakeClient())
    created = naumen_service.sync_partners(db, settings, dry_run=False)
    updated = naumen_service.sync_partners(db, settings, dry_run=False)
    assert created["rows_created"] == 1
    assert updated["rows_updated"] == 1
    assert db.query(NaumenPartner).filter(NaumenPartner.partner_uuid == "p1").one().title == "Партнёр 1"


def test_project_check_validates_uuid_and_not_configured():
    admin = token()
    request_json("/api/v1/integrations/naumen/settings", admin, "PUT", {
        "base_url": "",
        "api_version": "v2",
        "auth_mode": "api_key",
        "username": "",
        "api_key": "",
        "basic_password": "",
        "request_timeout_seconds": 10,
        "verify_ssl": True,
        "enabled": False,
    })
    try:
        request_json("/api/v1/projects/check", admin, "POST", {"project_uuid": "short"})
    except urllib.error.HTTPError as exc:
        assert exc.code == 422
    result = request_json("/api/v1/projects/check", admin, "POST", {"project_uuid": "a" * 32})
    assert result["status"] == "not_configured"


def test_admin_projects_current_and_user_project_access():
    admin = token()
    first = create_project(admin, "1" * 32, "Проект 1")
    second = create_project(admin, "2" * 32, "Проект 2")
    request_json(f"/api/v1/projects/{first['id']}", admin, "PUT", {"is_default": True})
    assert len(request_json("/api/v1/projects", admin)) >= 2
    current = request_json("/api/v1/projects/current", admin)
    assert current["id"] in {first["id"], second["id"]}
    selected = request_json("/api/v1/projects/current", admin, "PUT", {"project_id": first["id"]})
    assert selected["id"] == first["id"]

    roles = request_json("/api/v1/roles", admin)
    role = next(item for item in roles if item["code"] == "readonly")
    suffix = str(int(time.time() * 1000))
    username = f"stage8_user_{suffix}"
    password = "Stage8Pass!"
    request_json("/api/v1/users", admin, "POST", {
        "email": f"{username}@local",
        "username": username,
        "full_name": "Stage 8 User",
        "role_id": role["id"],
        "is_active": True,
        "is_superuser": False,
        "password": password,
        "project_ids": [first["id"]],
        "can_sync_project_ids": [],
    })
    user_token = token(username, password)
    user_projects = request_json("/api/v1/projects", user_token)
    assert [item["id"] for item in user_projects] == [first["id"]]
    try:
        request_json(f"/api/v1/employees?project_id={second['id']}", user_token)
    except urllib.error.HTTPError as exc:
        assert exc.code == 403
    else:
        raise AssertionError("project access was not enforced")


def test_integration_settings_masks_secret_and_export_requires_auth():
    admin = token()
    result = request_json("/api/v1/integrations/naumen/settings", admin, "PUT", {
        "base_url": "http://naumen.local",
        "api_version": "v2",
        "auth_mode": "api_key",
        "username": "api-user",
        "api_key": "stage8-secret",
        "basic_password": "",
        "request_timeout_seconds": 10,
        "verify_ssl": True,
        "enabled": True,
    })
    assert "stage8-secret" not in json.dumps(result)
    assert result["api_key_masked"]
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/v1/reports/executive-summary.csv", timeout=10)
    except urllib.error.HTTPError as exc:
        assert exc.code == 401
    req = urllib.request.Request(f"{BASE_URL}/api/v1/reports/executive-summary.csv", headers={"Authorization": f"Bearer {admin}"})
    with urllib.request.urlopen(req, timeout=10) as response:
        assert response.status == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
