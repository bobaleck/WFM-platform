from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.models.integration_settings import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(120), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(64), default="manager", nullable=False)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    supervisor_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    personnel_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    inn: Mapped[str | None] = mapped_column(String(12), unique=True, nullable=True)
    snils: Mapped[str | None] = mapped_column(String(32), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    position: Mapped[str | None] = mapped_column(String(160))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(64), default="full_time", nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), default="Europe/Moscow", nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    external_1c_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onec_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    onec_status_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    onec_last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    onec_last_check_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    onec_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    onec_active_cards_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    onec_dismissed_cards_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dismissal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    naumen_uuid: Mapped[str | None] = mapped_column(String(80), nullable=True)
    naumen_login: Mapped[str | None] = mapped_column(String(160), nullable=True)
    naumen_project_uuid: Mapped[str | None] = mapped_column(String(80), nullable=True)
    naumen_project_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    naumen_status: Mapped[str] = mapped_column(String(40), default="not_linked", nullable=False)
    naumen_status_label: Mapped[str] = mapped_column(String(80), default="Не сопоставлен", nullable=False)
    naumen_last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    naumen_last_check_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    naumen_last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    naumen_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class EmployeeProjectAccess(Base):
    __tablename__ = "employee_project_access"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("naumen_projects.id"), nullable=False)
    can_work: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class EmployeeTeamMembership(Base):
    __tablename__ = "employee_team_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("naumen_projects.id"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class QueueSkill(Base):
    __tablename__ = "queue_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    min_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Queue(Base):
    __tablename__ = "queues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    queue_uuid: Mapped[str | None] = mapped_column(String(80), nullable=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(64), default="voice", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    service_level_target: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    target_answer_time_sec: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    source_system: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class WorkloadInterval(Base):
    __tablename__ = "workload_intervals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)
    offered_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    handled_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    abandoned_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_handle_time_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_level_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    source_system: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    import_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    import_type: Mapped[str] = mapped_column(String(80), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="processing", nullable=False)
    rows_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_success: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_message: Mapped[str | None] = mapped_column(Text)


class ImportError(Base):
    __tablename__ = "import_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class EmployeeImportBatch(Base):
    __tablename__ = "employee_import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="processing", nullable=False)
    rows_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_message: Mapped[str | None] = mapped_column(Text)


class EmployeeImportError(Base):
    __tablename__ = "employee_import_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("employee_import_batches.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    field: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class OneCStatusCheckRun(Base):
    __tablename__ = "onec_status_check_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_type: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="running", nullable=False)
    started_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    employees_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    employees_checked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    employees_working: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    employees_dismissed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    employees_not_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    employees_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class OneCStatusCheckError(Base):
    __tablename__ = "onec_status_check_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("onec_status_check_runs.id"), nullable=False)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class StaffingRequirement(Base):
    __tablename__ = "staffing_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)
    required_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    planned_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gap_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    calculation_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class PlanningSettings(Base):
    __tablename__ = "planning_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_occupancy: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    default_interval_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    min_agents_per_queue: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_hours_per_employee_per_week: Mapped[int] = mapped_column(Integer, default=40, nullable=False)
    min_rest_hours_between_shifts: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    max_consecutive_work_days: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    preferred_shift_balance_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekend_balance_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    skill_priority_weight: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    fairness_weight: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    coverage_weight: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    shrinkage_percent: Mapped[float] = mapped_column(Float, default=25, nullable=False)
    service_level_target: Mapped[float] = mapped_column(Float, default=80, nullable=False)
    average_patience_sec: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(40), default="mvp", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ScheduleRule(Base):
    __tablename__ = "schedule_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    break_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    paid_hours: Mapped[float] = mapped_column(Float, default=8.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    shift_id: Mapped[int] = mapped_column(ForeignKey("shifts.id"), nullable=False)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="planned", nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ScheduleCoverage(Base):
    __tablename__ = "schedule_coverage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)
    required_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    planned_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confirmed_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gap_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coverage_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ScheduleGenerationRun(Base):
    __tablename__ = "schedule_generation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="ok", nullable=False)
    created_assignments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_assignments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coverage_gaps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warnings_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class ScheduleRecommendation(Base):
    __tablename__ = "schedule_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generation_run_id: Mapped[int | None] = mapped_column(ForeignKey("schedule_generation_runs.id"))
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    recommendation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(40), default="warning", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class Absence(Base):
    __tablename__ = "absences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    absence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="planned", nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class KpiSnapshot(Base):
    __tablename__ = "kpi_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)
    service_level_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    average_speed_answer_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_handle_time_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    occupancy_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    utilization_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    abandonment_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class ActualWorkInterval(Base):
    __tablename__ = "actual_work_intervals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    actual_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class NaumenOperator(Base):
    __tablename__ = "naumen_operators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    naumen_uuid: Mapped[str] = mapped_column(String(80), nullable=False)
    project_uuid: Mapped[str | None] = mapped_column(String(80), nullable=True)
    partner_uuid: Mapped[str | None] = mapped_column(String(80), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_last_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    normalized_first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    normalized_middle_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    login: Mapped[str | None] = mapped_column(String(160), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    substate: Mapped[str | None] = mapped_column(String(80), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class EmployeeDailyStat(Base):
    __tablename__ = "employee_daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_system: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    handled_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offered_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_handle_time_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_level_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    occupancy_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    adherence_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    login_time_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    productive_time_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    not_ready_time_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class EmployeeIntervalStat(Base):
    __tablename__ = "employee_interval_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    queue_id: Mapped[int | None] = mapped_column(ForeignKey("queues.id"), nullable=True)
    source_system: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    handled_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_handle_time_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_level_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    occupancy_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class EmployeeAttendanceFact(Base):
    __tablename__ = "employee_attendance_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_shift_id: Mapped[int | None] = mapped_column(ForeignKey("shifts.id"), nullable=True)
    planned_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    planned_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    source_system: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    actor_username: Mapped[str | None] = mapped_column(String(160))
    actor: Mapped[str] = mapped_column(String(160), default="system", nullable=False)
    action: Mapped[str] = mapped_column(String(160), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(160), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80))
    details_json: Mapped[str | None] = mapped_column(Text)
    details: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class ExportLog(Base):
    __tablename__ = "export_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    report_type: Mapped[str] = mapped_column(String(120), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    rows_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
