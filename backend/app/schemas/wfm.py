from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TeamIn(BaseModel):
    project_id: int | None = None
    name: str
    description: str | None = None
    supervisor_name: str | None = None
    is_active: bool = True


class TeamOut(TeamIn, OrmModel):
    id: int


class SkillIn(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class SkillOut(SkillIn, OrmModel):
    id: int


class QueueIn(BaseModel):
    project_id: int | None = None
    name: str
    channel: str = "voice"
    description: str | None = None
    service_level_target: float = 80
    target_answer_time_sec: int = 20
    is_active: bool = True


class QueueOut(QueueIn, OrmModel):
    id: int


class QueueSkillIn(BaseModel):
    skill_id: int
    min_level: int = Field(default=1, ge=1, le=5)
    is_required: bool = True


class QueueSkillOut(QueueSkillIn, OrmModel):
    id: int
    queue_id: int
    skill_name: str | None = None


class EmployeeIn(BaseModel):
    project_id: int | None = None
    project_ids: list[int] = []
    personnel_number: str | None = None
    full_name: str
    inn: str | None = Field(default=None, pattern="^[0-9]{12}$")
    birth_date: date | None = None
    email: str | None = None
    phone: str | None = None
    position: str | None = None
    team_id: int | None = None
    employment_type: str = "full_time"
    timezone: str = "Europe/Moscow"
    source_type: str = "manual"
    external_1c_id: str | None = None
    employment_status: str = "unknown"
    hire_date: date | None = None
    dismissal_date: date | None = None
    comment: str | None = None
    naumen_uuid: str | None = None
    naumen_project_uuid: str | None = None
    naumen_project_title: str | None = None
    is_active: bool = True


class EmployeeOut(EmployeeIn, OrmModel):
    id: int
    team_name: str | None = None
    onec_status: str | None = None
    onec_status_label: str | None = None
    onec_last_checked_at: datetime | None = None
    onec_last_check_message: str | None = None
    onec_metadata: str | None = None
    naumen_status: str = "not_linked"
    naumen_status_label: str = "Не сопоставлен"
    naumen_last_checked_at: datetime | None = None
    naumen_last_check_message: str | None = None
    naumen_last_sync_at: datetime | None = None
    skill_ids: list[int] = []
    project_id: int | None = None
    project_ids: list[int] = []
    project_names: list[str] = []


class EmployeeNaumenLinkIn(BaseModel):
    naumen_uuid: str | None = None


class EmployeeSkillsIn(BaseModel):
    skill_ids: list[int] = []


class TeamEmployeesIn(BaseModel):
    employee_ids: list[int] = []


class SkillEmployeesIn(BaseModel):
    employee_ids: list[int] = []


class NaumenOperatorOut(OrmModel):
    id: int
    project_id: int | None = None
    naumen_uuid: str
    project_uuid: str | None = None
    partner_uuid: str | None = None
    full_name: str | None = None
    login: str | None = None
    email: str | None = None
    phone: str | None = None
    state: str | None = None
    substate: str | None = None
    last_seen_at: datetime | None = None


class EmployeeCheckAllIn(BaseModel):
    only_active: bool = True


class WorkloadIn(BaseModel):
    project_id: int | None = None
    interval_start: datetime
    interval_end: datetime
    queue_id: int
    offered_contacts: int = 0
    handled_contacts: int = 0
    abandoned_contacts: int = 0
    average_handle_time_sec: int = 0
    service_level_percent: float = 0


class WorkloadOut(WorkloadIn, OrmModel):
    id: int
    queue_name: str | None = None


class StaffingIn(BaseModel):
    interval_start: datetime
    interval_end: datetime
    queue_id: int
    required_agents: int = 0
    planned_agents: int = 0
    gap_agents: int = 0
    calculation_note: str | None = None


class StaffingOut(StaffingIn, OrmModel):
    id: int
    queue_name: str | None = None


class ImportBatchOut(OrmModel):
    id: int
    import_type: str
    filename: str
    status: str
    rows_total: int
    rows_success: int
    rows_failed: int
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None


class ImportErrorOut(OrmModel):
    id: int
    batch_id: int
    row_number: int
    error_message: str
    raw_data: str | None = None
    created_at: datetime


class ImportBatchDetail(ImportBatchOut):
    errors: list[ImportErrorOut] = []


class PlanningSettingsIn(BaseModel):
    target_occupancy: float = Field(default=0.85, ge=0.1, le=1)
    default_interval_minutes: int = Field(default=30, ge=5, le=240)
    min_agents_per_queue: int = Field(default=1, ge=0, le=1000)
    max_hours_per_employee_per_week: int = Field(default=40, ge=1, le=100)
    min_rest_hours_between_shifts: int = Field(default=12, ge=0, le=48)
    max_consecutive_work_days: int = Field(default=5, ge=1, le=14)
    preferred_shift_balance_enabled: bool = True
    weekend_balance_enabled: bool = True
    skill_priority_weight: int = Field(default=50, ge=0, le=1000)
    fairness_weight: int = Field(default=30, ge=0, le=1000)
    coverage_weight: int = Field(default=100, ge=0, le=1000)
    shrinkage_percent: float = Field(default=25, ge=0, le=95)
    service_level_target: float = Field(default=80, ge=0, le=100)
    average_patience_sec: int = Field(default=20, ge=0, le=3600)
    calculation_method: str = "mvp"


class PlanningSettingsOut(PlanningSettingsIn, OrmModel):
    id: int


class CalculateStaffingIn(BaseModel):
    date_from: date
    date_to: date


class CalculateStaffingOut(BaseModel):
    status: str
    calculated_intervals: int
    date_from: date
    date_to: date


class ScheduleRuleIn(BaseModel):
    name: str
    value: str
    description: str | None = None
    is_active: bool = True


class ScheduleRuleOut(ScheduleRuleIn, OrmModel):
    id: int


class ShiftIn(BaseModel):
    project_id: int | None = None
    name: str
    start_time: time
    end_time: time
    break_minutes: int = 60
    paid_hours: float = 8
    is_active: bool = True


class ShiftOut(ShiftIn, OrmModel):
    id: int


class ScheduleIn(BaseModel):
    project_id: int | None = None
    work_date: date
    employee_id: int
    shift_id: int
    queue_id: int
    status: str = "planned"
    note: str | None = None


class ScheduleOut(ScheduleIn, OrmModel):
    id: int
    employee_name: str | None = None
    shift_name: str | None = None
    queue_name: str | None = None
    confirmed_at: datetime | None = None
    published_at: datetime | None = None
    cancelled_at: datetime | None = None


class GenerateDraftIn(BaseModel):
    date_from: date
    date_to: date
    queue_id: int | None = None


class GenerateDraftOut(BaseModel):
    status: str
    created_assignments: int
    updated_assignments: int = 0
    skipped_assignments: int = 0
    coverage_gaps: int = 0
    skill_gaps: int = 0
    fairness_notes: list[str] = []
    warnings: list[str] = []
    coverage_note: str = "Черновой график создан по MVP-алгоритму"


class DateRangeIn(BaseModel):
    date_from: date
    date_to: date
    queue_id: int | None = None


class CoverageOut(OrmModel):
    id: int
    interval_start: datetime
    interval_end: datetime
    queue_id: int
    queue_name: str | None = None
    required_agents: int
    planned_agents: int
    confirmed_agents: int
    published_agents: int
    gap_agents: int
    coverage_percent: float


class CoverageRecalcOut(BaseModel):
    status: str
    recalculated_intervals: int


class ScheduleRecommendationOut(OrmModel):
    id: int
    generation_run_id: int | None = None
    work_date: date
    queue_id: int
    queue_name: str | None = None
    employee_id: int | None = None
    employee_name: str | None = None
    recommendation_type: str
    message: str
    severity: str
    created_at: datetime


class ActualWorkIn(BaseModel):
    work_date: date
    employee_id: int
    queue_id: int
    interval_start: datetime
    interval_end: datetime
    status: str = "unknown"
    actual_minutes: int = Field(default=0, ge=0)
    source: str = "manual"


class ActualWorkOut(ActualWorkIn, OrmModel):
    id: int
    employee_name: str | None = None
    queue_name: str | None = None


class PlanFactOut(BaseModel):
    planned_assignments: int
    published_assignments: int
    actual_worked_intervals: int
    absence_count: int
    adherence_percent: float
    planned_hours: float
    actual_hours: float
    gap_hours: float
    rows: list[dict[str, Any]] = []


class AbsenceIn(BaseModel):
    project_id: int | None = None
    employee_id: int
    absence_type: str
    date_from: date
    date_to: date
    status: str = "planned"
    comment: str | None = None


class AbsenceOut(AbsenceIn, OrmModel):
    id: int
    employee_name: str | None = None


class SummaryOut(BaseModel):
    total_employees: int
    active_teams: int
    queues: int
    shifts: int
    week_assignments: int
    average_service_level: float
    average_aht: float
    staffing_gap: int
    kpi: dict[str, Any]
    staffing_by_queue: list[dict[str, Any]] = []
    planned_coverage: list[dict[str, Any]] = []
    recent_imports: list[dict[str, Any]] = []
    today_schedules: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, Any]] = []
    recent_generations: list[dict[str, Any]] = []
    plan_fact: dict[str, Any] = {}
