import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import write_audit
from app.models.integration_settings import Base
from app.models.wfm import AuditLog

PROJECT_ROOT = Path("/opt/wfm-naumen")


def test_open_source_audit_file_exists():
    text = (PROJECT_ROOT / "docs/open-source-audit.md").read_text(encoding="utf-8")
    assert "кастомной WFM-платформой" in text
    assert "Frappe HR" in text


def test_dependency_inventory_file_exists():
    text = (PROJECT_ROOT / "docs/dependency-inventory.md").read_text(encoding="utf-8")
    assert "Backend" in text
    assert "Frontend" in text


def test_alembic_config_exists():
    assert (PROJECT_ROOT / "backend/alembic.ini").exists()
    assert (PROJECT_ROOT / "backend/alembic/env.py").exists()
    assert (PROJECT_ROOT / "backend/alembic/versions/20260526_0001_baseline.py").exists()


def test_backup_restore_healthcheck_scripts_exist_and_executable():
    for relative in ["scripts/backup-db.sh", "scripts/restore-db.sh", "scripts/healthcheck.sh"]:
        path = PROJECT_ROOT / relative
        assert path.exists()
        assert os.access(path, os.X_OK)


def test_restore_requires_confirm():
    result = subprocess.run(
        [str(PROJECT_ROOT / "scripts/restore-db.sh")],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "--confirm" in result.stderr


def test_healthcheck_returns_success_when_services_are_healthy():
    if shutil.which("docker") is None:
        pytest.skip("docker CLI is not available in the backend test container")
    result = subprocess.run(
        [str(PROJECT_ROOT / "scripts/healthcheck.sh")],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_production_checklist_exists():
    text = (PROJECT_ROOT / "docs/production-checklist.md").read_text(encoding="utf-8")
    assert "JWT_SECRET" in text
    assert "TLS" in text


def test_version_endpoint_still_works():
    with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/version", timeout=5) as response:
        body = response.read().decode("utf-8")
    assert response.status == 200
    assert '"version":"0.1.0"' in body


def test_protected_route_still_requires_auth():
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/api/v1/employees", timeout=5)
    except urllib.error.HTTPError as exc:
        assert exc.code == 401
    else:
        raise AssertionError("protected route did not require auth")


def test_audit_log_still_works():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    write_audit(db, "stage6_test", details="ok")
    row = db.query(AuditLog).one()
    assert row.action == "stage6_test"
    assert row.actor == "anonymous"
