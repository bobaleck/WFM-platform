from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IntegrationSettings(Base):
    __tablename__ = "integration_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(64), default="telephony", nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), default="Naumen", nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NaumenConnectionSettings(Base):
    __tablename__ = "naumen_connection_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_version: Mapped[str] = mapped_column(String(32), default="v2", nullable=False)
    auth_mode: Mapped[str] = mapped_column(String(32), default="api_key", nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    basic_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    verify_ssl: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_check_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_check_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_check_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_check_endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class OneCConnectionSettings(Base):
    __tablename__ = "onec_connection_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    connection_mode: Mapped[str] = mapped_column(String(40), default="gateway_http", nullable=False)
    gateway_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gateway_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    infobase_type: Mapped[str] = mapped_column(String(20), default="server", nullable=False)
    onec_server: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onec_database: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onec_cluster: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_base_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    onec_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onec_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    infobase_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    server: Mapped[str | None] = mapped_column(String(255), nullable=True)
    database: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cluster: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_type: Mapped[str] = mapped_column(String(40), default="password", nullable=False)
    request_timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verify_tls: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_disable_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    check_on_employee_create: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enable_weekly_1c_status_check: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_1c_status_check_day: Mapped[str] = mapped_column(String(8), default="SUN", nullable=False)
    weekly_1c_status_check_time: Mapped[str] = mapped_column(String(5), default="03:00", nullable=False)
    onec_check_batch_size: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    onec_check_pause_ms: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    last_check_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_check_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NaumenSyncRun(Base):
    __tablename__ = "naumen_sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sync_type: Mapped[str] = mapped_column(String(80), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rows_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class NaumenPartner(Base):
    __tablename__ = "naumen_partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_uuid: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NaumenSyncError(Base):
    __tablename__ = "naumen_sync_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sync_run_id: Mapped[int] = mapped_column(ForeignKey("naumen_sync_runs.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ExternalMapping(Base):
    __tablename__ = "external_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_system: Mapped[str] = mapped_column(String(80), default="naumen", nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    internal_id: Mapped[str] = mapped_column(String(80), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NaumenProject(Base):
    __tablename__ = "naumen_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_uuid: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    partner_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_partners.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_uuid: Mapped[str | None] = mapped_column(String(80), nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    data_channel: Mapped[str | None] = mapped_column(String(80), nullable=True)
    cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NaumenProjectScheduleRule(Base):
    __tablename__ = "naumen_project_schedule_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("naumen_projects.id"), nullable=False)
    rest_day: Mapped[str | None] = mapped_column(String(80), nullable=True)
    time_from: Mapped[str | None] = mapped_column(String(40), nullable=True)
    time_to: Mapped[str | None] = mapped_column(String(40), nullable=True)
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserProjectAccess(Base):
    __tablename__ = "user_project_access"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    naumen_project_id: Mapped[int] = mapped_column(ForeignKey("naumen_projects.id"), nullable=False)
    can_view: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_sync: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    selected_project_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_projects.id"), nullable=True)
    selected_partner_id: Mapped[int | None] = mapped_column(ForeignKey("naumen_partners.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(40), default="string", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
