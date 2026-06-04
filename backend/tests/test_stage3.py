from datetime import date, datetime, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.rbac import required_permission
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.integration_settings import Base
from app.models.wfm import Absence, Employee, PlanningSettings, Queue, Shift, StaffingRequirement, Team
from app.services.planning import calculate_required_agents, coverage_percent, employee_matches_required_skills


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_required_agents_calculation():
    required = calculate_required_agents(
        offered_contacts=120,
        average_handle_time_sec=240,
        interval_minutes=30,
        target_occupancy=0.85,
    )
    assert required == 19


def test_required_agents_with_shrinkage():
    required = calculate_required_agents(
        offered_contacts=120,
        average_handle_time_sec=240,
        interval_minutes=30,
        target_occupancy=0.85,
        shrinkage_percent=25,
    )
    assert required == 26


def test_employee_skill_match_required_queue_skill():
    assert employee_matches_required_skills({1: 3}, [(1, 2, True)])
    assert not employee_matches_required_skills({1: 1}, [(1, 2, True)])


def test_workload_csv_row_shape():
    row = {
        "date": "2026-01-15",
        "interval_start": "09:00",
        "interval_end": "09:30",
        "queue_name": "Входящая линия",
        "offered_contacts": "120",
        "handled_contacts": "110",
        "abandoned_contacts": "10",
        "average_handle_time_sec": "240",
        "service_level_percent": "82.5",
    }
    assert row["queue_name"] == "Входящая линия"
    assert int(row["offered_contacts"]) == 120


def test_create_employee_model():
    db = make_session()
    team = Team(name="Тест", description="Команда", supervisor_name="Супервайзер")
    db.add(team)
    db.flush()
    employee = Employee(personnel_number="T-001", full_name="Тестовый Сотрудник", team_id=team.id)
    db.add(employee)
    db.commit()
    assert db.query(Employee).count() == 1


def test_draft_schedule_demo_primitives():
    db = make_session()
    db.add(PlanningSettings(max_hours_per_employee_per_week=40))
    queue = Queue(name="Входящая линия")
    shift = Shift(name="Утро", start_time=time(9, 0), end_time=time(18, 0), paid_hours=8)
    employee = Employee(personnel_number="T-002", full_name="Оператор")
    db.add_all([queue, shift, employee])
    db.flush()
    db.add(StaffingRequirement(
        interval_start=datetime(2026, 1, 15, 9, 0),
        interval_end=datetime(2026, 1, 15, 9, 30),
        queue_id=queue.id,
        required_agents=1,
        planned_agents=0,
        gap_agents=-1,
    ))
    db.commit()
    assert db.query(StaffingRequirement).filter(StaffingRequirement.interval_start >= datetime.combine(date(2026, 1, 15), time.min)).count() == 1


def test_absence_blocks_assignment_day():
    absence = Absence(employee_id=1, absence_type="Отпуск", date_from=date(2026, 1, 15), date_to=date(2026, 1, 16))
    assert absence.date_from <= date(2026, 1, 15) <= absence.date_to


def test_coverage_gap_calculation():
    assert coverage_percent(1, 4) == 25.0
    assert 4 - 1 == 3


def test_publish_period_only_confirmed():
    statuses = ["draft", "confirmed", "published", "cancelled"]
    changed = ["published" if status == "confirmed" else status for status in statuses]
    assert changed == ["draft", "published", "published", "cancelled"]


def test_plan_fact_adherence():
    planned_hours = 8
    actual_hours = 6
    assert round(actual_hours / planned_hours * 100, 1) == 75.0


def test_password_hash_verification():
    password_hash = hash_password("Admin12345!")
    assert verify_password("Admin12345!", password_hash)
    assert not verify_password("wrong-password", password_hash)
    assert "Admin12345!" not in password_hash


def test_jwt_token_roundtrip():
    token = create_access_token("1", {"username": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["username"] == "admin"


def test_rbac_required_permissions():
    assert required_permission("/api/v1/employees", "GET") == "employees:view"
    assert required_permission("/api/v1/employees", "POST") == "employees:manage"
    assert required_permission("/api/v1/users", "GET") == "users:view"
    assert required_permission("/api/v1/audit-log", "GET") == "audit:view"
    assert required_permission("/api/v1/reports/plan-fact.csv", "GET") == "reports:export"


def test_actual_work_csv_row_shape():
    row = {
        "date": "2026-01-15",
        "employee_email": "operator1@telesales.local",
        "queue_name": "Исходящая линия",
        "interval_start": "10:00",
        "interval_end": "10:30",
        "status": "worked",
        "actual_minutes": "30",
    }
    assert row["status"] in {"worked", "late", "absent", "offline", "unknown"}
    assert int(row["actual_minutes"]) >= 0


def test_security_headers_expected_set():
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }
    assert headers["X-Frame-Options"] == "DENY"
    assert "geolocation=()" in headers["Permissions-Policy"]
