import json
import os
import urllib.error
import urllib.request
from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.integration_settings import Base
from app.models.wfm import Queue, ScheduleRecommendation
from app.wfm.scheduler_engine import Candidate, SchedulerSettings, choose_best_candidate, score_candidate


BASE_URL = "http://127.0.0.1:8000"


def http_json(path: str, token: str | None = None):
    request = urllib.request.Request(f"{BASE_URL}{path}")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def admin_token() -> str:
    payload = json.dumps({
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "Admin12345!"),
    }).encode("utf-8")
    request = urllib.request.Request(f"{BASE_URL}/api/v1/auth/login", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))["access_token"]


def test_executive_summary_returns_data():
    data = http_json("/api/v1/reports/executive-summary", admin_token())
    assert "active_employees" in data
    assert "adherence_percent" in data


def test_operations_summary_returns_queue_rows():
    rows = http_json("/api/v1/reports/operations-summary", admin_token())
    assert isinstance(rows, list)
    if rows:
        assert "queue_name" in rows[0]


def test_coverage_gaps_returns_deficit_intervals():
    rows = http_json("/api/v1/reports/coverage-gaps", admin_token())
    assert isinstance(rows, list)
    for row in rows:
        assert row["gap_agents"] > 0


def test_sla_summary_counts_below_target():
    rows = http_json("/api/v1/reports/sla-summary", admin_token())
    assert isinstance(rows, list)
    if rows:
        assert "below_target_intervals" in rows[0]


def test_scheduler_engine_rejects_missing_required_skill():
    settings = SchedulerSettings()
    best = choose_best_candidate(
        [Candidate(employee_id=1, skill_levels={})],
        [(10, 2, True)],
        date(2026, 1, 15),
        datetime(2026, 1, 15, 9),
        8,
        settings,
    )
    assert best is None


def test_scheduler_engine_accounts_for_absence():
    score = score_candidate(
        Candidate(employee_id=1, skill_levels={10: 3}, absences=[(date(2026, 1, 15), date(2026, 1, 16))]),
        [(10, 2, True)],
        date(2026, 1, 15),
        datetime(2026, 1, 15, 9),
        8,
        SchedulerSettings(),
    )
    assert not score.eligible
    assert score.reason == "absence_conflict"


def test_scheduler_engine_fairness_prefers_less_loaded_employee():
    best = choose_best_candidate(
        [
            Candidate(employee_id=1, skill_levels={10: 3}, assignments_count=5),
            Candidate(employee_id=2, skill_levels={10: 3}, assignments_count=0),
        ],
        [(10, 2, True)],
        date(2026, 1, 15),
        datetime(2026, 1, 15, 9),
        8,
        SchedulerSettings(),
    )
    assert best
    assert best.employee_id == 2


def test_scheduler_engine_weekly_hours_limit():
    score = score_candidate(
        Candidate(employee_id=1, skill_levels={10: 3}, weekly_hours=38),
        [(10, 2, True)],
        date(2026, 1, 15),
        datetime(2026, 1, 15, 9),
        8,
        SchedulerSettings(max_weekly_hours=40),
    )
    assert not score.eligible
    assert score.reason == "weekly_hours_limit"


def test_schedule_recommendations_model_creates_deficit_row():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    queue = Queue(name="Тестовая очередь")
    db.add(queue)
    db.flush()
    db.add(ScheduleRecommendation(
        work_date=date(2026, 1, 15),
        queue_id=queue.id,
        recommendation_type="coverage_gap",
        message="Не хватает операторов",
        severity="warning",
    ))
    db.commit()
    assert db.query(ScheduleRecommendation).count() == 1


def test_report_export_writes_export_log():
    token = admin_token()
    request = urllib.request.Request(f"{BASE_URL}/api/v1/reports/executive-summary.csv")
    request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=10) as response:
        assert response.status == 200
    rows = http_json("/api/v1/reports/export-log", token)
    assert any(row["report_type"] == "executive_summary" for row in rows)


def test_protected_reports_require_auth():
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/v1/reports/executive-summary", timeout=10)
    except urllib.error.HTTPError as exc:
        assert exc.code == 401
    else:
        raise AssertionError("reports endpoint did not require auth")
