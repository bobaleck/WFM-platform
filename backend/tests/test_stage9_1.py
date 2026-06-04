import json
import os
import threading
import urllib.error
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from time import time


BASE_URL = "http://127.0.0.1:8000"


def request_json(path: str, token: str | None = None, method: str = "GET", payload: dict | None = None):
    body = json.dumps(payload or {}).encode("utf-8") if method in {"POST", "PUT"} else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method, headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def admin_token() -> str:
    payload = {"username": os.getenv("ADMIN_USERNAME", "admin"), "password": os.getenv("ADMIN_PASSWORD", "Admin12345!")}
    return request_json("/api/v1/auth/login", method="POST", payload=payload)["access_token"]


def test_version_is_manual_and_naumen_api_available_as_operator_integration():
    version = request_json("/api/v1/version")
    assert version["external_source"] == "manual"
    token = admin_token()
    settings = request_json("/api/v1/integrations/naumen/settings", token)
    assert settings["enabled"] in {True, False}


def test_onec_settings_do_not_return_password_and_direct_com_linux_is_unsupported():
    token = admin_token()
    settings = request_json("/api/v1/integrations/onec/settings", token)
    assert "password" not in settings
    assert "password_encrypted" not in settings
    assert "password_saved" in settings
    assert "gateway_token_saved" in settings
    request_json("/api/v1/integrations/onec/settings", token, "PUT", {
        **settings,
        "connection_mode": "direct_com",
        "password": "",
    })
    result = request_json("/api/v1/integrations/onec/diagnose", token, "POST", {})
    assert result["status"] == "unsupported"
    assert result["direct_com_available"] is False
    assert "password" not in result
    assert "gateway_token" not in result


def test_onec_password_is_not_cleared_by_empty_value_and_gateway_url_is_required():
    token = admin_token()
    saved = request_json("/api/v1/integrations/onec/settings", token, "PUT", {
        "connection_mode": "gateway_http",
        "gateway_url": "",
        "gateway_token": "gateway-secret",
        "infobase_type": "server",
        "onec_server": "1c-server.local",
        "onec_database": "TSS_MAIN",
        "onec_cluster": "",
        "onec_username": "onec-user",
        "password": "onec-password",
        "request_timeout_seconds": 10,
        "enabled": True,
        "verify_tls": True,
        "auto_disable_dismissed": False,
        "check_on_employee_create": False,
        "enable_weekly_1c_status_check": True,
        "weekly_1c_status_check_day": "SUN",
        "weekly_1c_status_check_time": "03:00",
        "onec_check_batch_size": 50,
        "onec_check_pause_ms": 200,
    })
    assert saved["password_saved"] is True
    assert saved["gateway_token_saved"] is True
    updated = request_json("/api/v1/integrations/onec/settings", token, "PUT", {
        **saved,
        "password": "",
        "gateway_token": "",
    })
    assert updated["password_saved"] is True
    assert updated["gateway_token_saved"] is True
    result = request_json("/api/v1/integrations/onec/check", token, "POST", {})
    assert result["status"] == "not_configured"
    assert result["message"] == "Укажите внутренний адрес Windows Gateway."


def test_onec_missing_server_and_file_fields_are_reported():
    token = admin_token()
    base_payload = {
        "connection_mode": "gateway_http",
        "gateway_url": "http://1c-gateway.local:8088",
        "gateway_token": "",
        "infobase_type": "server",
        "onec_server": "",
        "onec_database": "",
        "onec_cluster": "",
        "file_base_path": "",
        "onec_username": "onec-user",
        "password": "",
        "request_timeout_seconds": 10,
        "enabled": True,
        "verify_tls": True,
        "auto_disable_dismissed": False,
        "check_on_employee_create": False,
        "enable_weekly_1c_status_check": True,
        "weekly_1c_status_check_day": "SUN",
        "weekly_1c_status_check_time": "03:00",
        "onec_check_batch_size": 50,
        "onec_check_pause_ms": 200,
    }
    request_json("/api/v1/integrations/onec/settings", token, "PUT", base_payload)
    result = request_json("/api/v1/integrations/onec/check", token, "POST", {})
    assert result["status"] == "not_configured"
    assert "onec_server" in result["missing_fields"]
    assert "onec_database" in result["missing_fields"]

    request_json("/api/v1/integrations/onec/settings", token, "PUT", {
        **base_payload,
        "infobase_type": "file",
        "onec_server": "ignored",
        "onec_database": "ignored",
        "file_base_path": "",
    })
    file_result = request_json("/api/v1/integrations/onec/check", token, "POST", {})
    assert file_result["status"] == "not_configured"
    assert "file_base_path" in file_result["missing_fields"]


def test_onec_check_connection_calls_gateway_check_connection():
    token = admin_token()
    captured = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            captured["path"] = self.path
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            captured["body"] = json.loads(body.decode("utf-8"))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "ok", "service": "1c-gateway"}).encode("utf-8"))

        def log_message(self, *_args):
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request_json("/api/v1/integrations/onec/settings", token, "PUT", {
            "connection_mode": "gateway_http",
            "gateway_url": f"http://127.0.0.1:{server.server_port}",
            "gateway_token": "",
            "infobase_type": "server",
            "onec_server": "1c-server.local",
            "onec_database": "TSS_MAIN",
            "onec_cluster": "",
            "file_base_path": "",
            "onec_username": "onec-user",
            "password": "onec-password",
            "request_timeout_seconds": 10,
            "enabled": True,
            "verify_tls": True,
            "auto_disable_dismissed": False,
            "check_on_employee_create": False,
            "enable_weekly_1c_status_check": True,
            "weekly_1c_status_check_day": "SUN",
            "weekly_1c_status_check_time": "03:00",
            "onec_check_batch_size": 50,
            "onec_check_pause_ms": 200,
        })
        result = request_json("/api/v1/integrations/onec/check", token, "POST", {})
        assert result["status"] == "ok"
        assert captured["path"] == "/api/v1/1c/check-connection"
        assert captured["body"]["server"] == "1c-server.local"
        assert captured["body"]["database"] == "TSS_MAIN"
        assert captured["body"]["password"] == "onec-password"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_app_settings_and_contours_work():
    token = admin_token()
    saved = request_json("/api/v1/settings/app", token, "PUT", {"company_name": "Телесейлз Сервис", "system_name": "WFM-платформа"})
    assert saved["company_name"] == "Телесейлз Сервис"
    contours = request_json("/api/v1/contours", token)
    assert isinstance(contours, list)


def test_workload_template_returns_xlsx():
    token = admin_token()
    req = urllib.request.Request(f"{BASE_URL}/api/v1/workload/template.xlsx", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as response:
        assert response.read(2) == b"PK"


def test_stage9_4_employees_are_visible_through_project_access_and_skills_are_global():
    token = admin_token()
    employees = request_json("/api/v1/employees", token)
    assert len(employees) >= 1
    assert all(item.get("project_ids") for item in employees)
    skills = request_json("/api/v1/skills", token)
    names = {item["name"] for item in skills}
    assert {"РГ", "РО", "Холодные звонки", "Чаты"}.issubset(names)
    assert all("project_id" not in item for item in skills)


def test_stage9_4_employee_template_has_no_snils_or_naumen_login():
    token = admin_token()
    req = urllib.request.Request(f"{BASE_URL}/api/v1/employees/import/template.xlsx", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as response:
        workbook_bytes = response.read()
    with zipfile.ZipFile(BytesIO(workbook_bytes)) as archive:
        xml_text = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml")
        )
    assert "СНИЛС" not in xml_text
    assert "Логин Naumen" not in xml_text
    assert "Проекты/контуры" in xml_text


def configure_onec_gateway(token: str, gateway_url: str):
    return request_json("/api/v1/integrations/onec/settings", token, "PUT", {
        "connection_mode": "gateway_http",
        "gateway_url": gateway_url,
        "gateway_token": "",
        "infobase_type": "server",
        "onec_server": "1c-server.local",
        "onec_database": "TSS_MAIN",
        "onec_cluster": "",
        "file_base_path": "",
        "onec_username": "onec-user",
        "password": "onec-password",
        "request_timeout_seconds": 5,
        "enabled": True,
        "verify_tls": True,
        "auto_disable_dismissed": False,
        "check_on_employee_create": False,
        "enable_weekly_1c_status_check": True,
        "weekly_1c_status_check_day": "SUN",
        "weekly_1c_status_check_time": "03:00",
        "onec_check_batch_size": 50,
        "onec_check_pause_ms": 200,
    })


def create_test_employee(token: str, inn_suffix: int) -> dict:
    inn = f"990000{inn_suffix:06d}"[-12:]
    return request_json("/api/v1/employees", token, "POST", {
        "personnel_number": f"TST-{inn}-{int(time() * 1000)}",
        "full_name": f"Тестовый Сотрудник {inn_suffix}",
        "inn": inn,
        "email": f"test-{inn_suffix}@example.local",
        "phone": "",
        "position": "Оператор",
        "employment_status": "working",
        "is_active": True,
    })


def run_mock_gateway(handler_cls):
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_stage9_7_gateway_health_is_not_employee_check_success():
    token = admin_token()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "test-listener"}).encode("utf-8"))

        def do_POST(self):
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error"}).encode("utf-8"))

        def log_message(self, *_args):
            return

    server, thread = run_mock_gateway(Handler)
    try:
        configure_onec_gateway(token, f"http://127.0.0.1:{server.server_port}")
        employee = create_test_employee(token, int(time()) % 900000)
        result = request_json(f"/api/v1/employees/{employee['id']}/check-1c-status", token, "POST", {})
        assert result["employee"]["onec_status"] == "gateway_invalid"
        assert "метод сверки сотрудника не реализован" in result["employee"]["onec_last_check_message"]
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_stage9_7_gateway_business_statuses_are_saved():
    token = admin_token()
    responses = [
        {"status": "working", "status_label": "Работает", "found": True, "active_cards_count": 1, "dismissed_cards_count": 0, "gateway_version": "2026-06-02.2"},
        {"status": "dismissed", "status_label": "Уволен", "found": True, "active_cards_count": 0, "dismissed_cards_count": 2, "gateway_version": "2026-06-02.2"},
        {"status": "not_found", "status_label": "Не найден", "found": False, "active_cards_count": 0, "dismissed_cards_count": 0, "gateway_version": "2026-06-02.2"},
    ]
    state = {"index": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            captured = json.loads(body.decode("utf-8"))
            assert self.path == "/api/v1/1c/check-employee-status"
            assert captured["inn"]
            assert captured["server"] == "1c-server.local"
            assert captured["database"] == "TSS_MAIN"
            assert captured["username"] == "onec-user"
            assert captured["password"] == "onec-password"
            payload = responses[state["index"]]
            state["index"] = min(state["index"] + 1, len(responses) - 1)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        def log_message(self, *_args):
            return

    server, thread = run_mock_gateway(Handler)
    try:
        configure_onec_gateway(token, f"http://127.0.0.1:{server.server_port}")
        for expected in ["working", "dismissed", "not_found"]:
            employee = create_test_employee(token, (int(time()) + state["index"]) % 900000)
            result = request_json(f"/api/v1/employees/{employee['id']}/check-1c-status", token, "POST", {})
            assert result["employee"]["onec_status"] == expected
            assert result["employee"]["onec_status"] != "ok"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_stage9_7_found_person_without_cards_is_diagnostic_status():
    token = admin_token()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "not_found",
                "status_label": "Не найден",
                "found": True,
                "message": "Физлицо найдено, но карточки сотрудников не найдены.",
                "active_cards_count": 0,
                "dismissed_cards_count": 0,
                "lookup_strategy_used": None,
                "gateway_version": "2026-06-02.1",
            }).encode("utf-8"))

        def log_message(self, *_args):
            return

    server, thread = run_mock_gateway(Handler)
    try:
        configure_onec_gateway(token, f"http://127.0.0.1:{server.server_port}")
        employee = create_test_employee(token, int(time()) % 900000)
        result = request_json(f"/api/v1/employees/{employee['id']}/check-1c-status", token, "POST", {})
        assert result["employee"]["onec_status"] == "not_found_person_cards"
        assert result["employee"]["onec_status_label"] == "Карточки сотрудника не найдены"
        assert "Gateway устарел" in result["employee"]["onec_last_check_message"]
        assert "onec_active_cards_count" not in result["employee"]
        assert "onec_dismissed_cards_count" not in result["employee"]
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_stage9_8_employee_archive_restore_and_hard_delete_requires_archive():
    token = admin_token()
    employee = create_test_employee(token, int(time()) % 900000)
    try:
        request_json(f"/api/v1/employees/{employee['id']}/hard-delete", token, "DELETE", {})
        assert False, "active employee hard delete must fail"
    except urllib.error.HTTPError as exc:
        assert exc.code == 409
    request_json(f"/api/v1/employees/{employee['id']}/archive", token, "POST", {})
    archived = request_json("/api/v1/employees?archived=true", token)
    assert any(item["id"] == employee["id"] for item in archived)
    request_json(f"/api/v1/employees/{employee['id']}/restore", token, "POST", {})
    active = request_json("/api/v1/employees", token)
    assert any(item["id"] == employee["id"] for item in active)
