from datetime import datetime

from pydantic import BaseModel, Field


class IntegrationSettingsResponse(BaseModel):
    provider: str = "telephony"
    display_name: str = "Naumen"
    base_url: str | None = None
    username: str | None = None
    api_token_masked: str | None = None
    timeout_seconds: int = 30
    enabled: bool = False
    configured: bool = False


class IntegrationSettingsPayload(BaseModel):
    display_name: str = "Naumen"
    base_url: str | None = None
    username: str | None = None
    api_token: str | None = Field(default=None, min_length=0)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    enabled: bool = False


class NaumenSettingsResponse(BaseModel):
    base_url: str | None = None
    api_version: str = "v2"
    auth_mode: str = "api_key"
    username: str | None = None
    api_key_masked: str | None = None
    basic_password_masked: str | None = None
    request_timeout_seconds: int = 30
    verify_ssl: bool = True
    enabled: bool = False
    configured: bool = False
    last_check_status: str | None = None
    last_check_message: str | None = None
    last_check_http_status: int | None = None
    last_check_endpoint: str | None = None
    last_check_at: datetime | None = None


class NaumenSettingsPayload(BaseModel):
    base_url: str | None = None
    api_version: str = Field(default="v2", pattern="^(v2|current)$")
    auth_mode: str = Field(default="api_key", pattern="^(api_key|basic)$")
    username: str | None = None
    api_key: str | None = Field(default=None, min_length=0)
    basic_password: str | None = Field(default=None, min_length=0)
    request_timeout_seconds: int = Field(default=30, ge=1, le=300)
    verify_ssl: bool = True
    enabled: bool = False


class OneCSettingsResponse(BaseModel):
    connection_mode: str = "gateway_http"
    gateway_url: str | None = None
    gateway_token_saved: bool = False
    infobase_type: str = "server"
    onec_server: str | None = None
    onec_database: str | None = None
    onec_cluster: str | None = None
    file_base_path: str | None = None
    onec_username: str | None = None
    password_saved: bool = False
    infobase_path: str | None = None
    server: str | None = None
    database: str | None = None
    cluster: str | None = None
    username: str | None = None
    auth_type: str = "password"
    request_timeout_seconds: int = 30
    enabled: bool = False
    verify_tls: bool = True
    auto_disable_dismissed: bool = False
    check_on_employee_create: bool = False
    enable_weekly_1c_status_check: bool = True
    weekly_1c_status_check_day: str = "SUN"
    weekly_1c_status_check_time: str = "03:00"
    onec_check_batch_size: int = 50
    onec_check_pause_ms: int = 200
    configured: bool = False
    last_check_status: str | None = None
    last_check_message: str | None = None
    last_check_at: datetime | None = None


class OneCSettingsPayload(BaseModel):
    connection_mode: str = Field(default="gateway_http", pattern="^(gateway_http|direct_com)$")
    gateway_url: str | None = None
    gateway_token: str | None = Field(default=None, min_length=0)
    infobase_type: str = Field(default="server", pattern="^(server|file)$")
    onec_server: str | None = None
    onec_database: str | None = None
    onec_cluster: str | None = None
    file_base_path: str | None = None
    onec_username: str | None = None
    password: str | None = Field(default=None, min_length=0)
    infobase_path: str | None = None
    server: str | None = None
    database: str | None = None
    cluster: str | None = None
    username: str | None = None
    auth_type: str = "password"
    request_timeout_seconds: int = Field(default=30, ge=1, le=300)
    enabled: bool = False
    verify_tls: bool = True
    auto_disable_dismissed: bool = False
    check_on_employee_create: bool = False
    enable_weekly_1c_status_check: bool = True
    weekly_1c_status_check_day: str = Field(default="SUN", pattern="^(MON|TUE|WED|THU|FRI|SAT|SUN)$")
    weekly_1c_status_check_time: str = Field(default="03:00", pattern="^[0-2][0-9]:[0-5][0-9]$")
    onec_check_batch_size: int = Field(default=50, ge=1, le=1000)
    onec_check_pause_ms: int = Field(default=200, ge=0, le=60000)


class OneCEmployeeStatusRequest(BaseModel):
    inn: str = Field(min_length=12, max_length=12, pattern="^[0-9]{12}$")


class NaumenSyncRequest(BaseModel):
    dry_run: bool = True
    project_id: int | None = None


class NaumenPartnerSyncRequest(BaseModel):
    dry_run: bool = True


class NaumenProjectSyncRequest(NaumenSyncRequest):
    project_uuid: str = Field(default="", min_length=0, max_length=80)


class NaumenSyncRunOut(BaseModel):
    id: int
    sync_type: str
    project_id: int | None = None
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    rows_received: int = 0
    rows_created: int = 0
    rows_updated: int = 0
    rows_failed: int = 0
    error_message: str | None = None

    model_config = {"from_attributes": True}


class NaumenSyncErrorOut(BaseModel):
    id: int
    sync_run_id: int
    entity_type: str
    external_id: str | None = None
    error_message: str
    raw_data: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NaumenSyncRunDetail(NaumenSyncRunOut):
    errors: list[NaumenSyncErrorOut] = []


class ProjectCheckIn(BaseModel):
    project_uuid: str = Field(min_length=32, max_length=32)


class ProjectIn(BaseModel):
    project_uuid: str = Field(min_length=32, max_length=32)
    title: str
    partner_uuid: str | None = None
    state: str | None = None
    data_channel: str | None = None
    cluster_id: int | None = None
    is_active: bool = True
    is_default: bool = False


class ProjectUpdate(BaseModel):
    title: str | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class ProjectOut(BaseModel):
    id: int
    project_uuid: str
    title: str
    partner_uuid: str | None = None
    state: str | None = None
    data_channel: str | None = None
    cluster_id: int | None = None
    is_active: bool
    is_default: bool
    last_checked_at: datetime | None = None
    last_sync_at: datetime | None = None

    model_config = {"from_attributes": True}


class PartnerUpdate(BaseModel):
    title: str | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class PartnerOut(BaseModel):
    id: int
    partner_uuid: str
    title: str
    is_active: bool
    is_default: bool
    last_sync_at: datetime | None = None

    model_config = {"from_attributes": True}


class CurrentProjectIn(BaseModel):
    project_id: int | None = None


class CurrentContextIn(BaseModel):
    context_type: str | None = Field(default=None, pattern="^(project|partner)$")
    id: int | None = None
