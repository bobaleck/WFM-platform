from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.core.config import settings
from datetime import datetime

from app.integrations.onec.service import get_or_create_onec_settings, onec_configured
from app.models.integration_settings import IntegrationSettings, NaumenConnectionSettings, OneCConnectionSettings
from app.schemas.integration import IntegrationSettingsPayload, IntegrationSettingsResponse, NaumenSettingsPayload, NaumenSettingsResponse, OneCSettingsPayload, OneCSettingsResponse


def _fernet() -> Fernet:
    if not settings.integration_secret_key:
        raise RuntimeError("INTEGRATION_SECRET_KEY is not configured")
    return Fernet(settings.integration_secret_key.encode("utf-8"))


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    return _fernet().decrypt(encrypted_token.encode("utf-8")).decode("utf-8")


def mask_token(token: str | None) -> str | None:
    if not token:
        return None
    if len(token) <= 8:
        return f"{token[:1]}****{token[-1:]}"
    return f"{token[:4]}****{token[-4:]}"


def get_or_create_settings(db: Session) -> IntegrationSettings:
    item = db.query(IntegrationSettings).filter(IntegrationSettings.provider == "telephony").one_or_none()
    if item:
        return item
    item = IntegrationSettings(provider="telephony", display_name="Naumen")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def is_configured(item: IntegrationSettings) -> bool:
    return bool(item.enabled and item.base_url and item.username and item.api_token_encrypted)


def to_response(item: IntegrationSettings) -> IntegrationSettingsResponse:
    token_masked = None
    if item.api_token_encrypted:
        token_masked = mask_token(decrypt_token(item.api_token_encrypted))
    return IntegrationSettingsResponse(
        provider=item.provider,
        display_name=item.display_name,
        base_url=item.base_url,
        username=item.username,
        api_token_masked=token_masked,
        timeout_seconds=item.timeout_seconds,
        enabled=item.enabled,
        configured=is_configured(item),
    )


def update_settings(db: Session, payload: IntegrationSettingsPayload) -> IntegrationSettings:
    item = get_or_create_settings(db)
    item.display_name = payload.display_name or "Naumen"
    item.base_url = payload.base_url
    item.username = payload.username
    item.timeout_seconds = payload.timeout_seconds
    item.enabled = payload.enabled
    if payload.api_token:
        item.api_token_encrypted = encrypt_token(payload.api_token)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_or_create_naumen_settings(db: Session) -> NaumenConnectionSettings:
    item = db.query(NaumenConnectionSettings).order_by(NaumenConnectionSettings.id).first()
    if item:
        return item
    item = NaumenConnectionSettings()
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def naumen_configured(item: NaumenConnectionSettings) -> bool:
    if not item.enabled or not item.base_url or not item.username:
        return False
    if item.auth_mode == "api_key":
        return bool(item.api_key_encrypted)
    if item.auth_mode == "basic":
        return bool(item.basic_password_encrypted)
    return False


def naumen_settings_response(item: NaumenConnectionSettings) -> NaumenSettingsResponse:
    api_key_masked = mask_token(decrypt_token(item.api_key_encrypted)) if item.api_key_encrypted else None
    password_masked = "********" if item.basic_password_encrypted else None
    return NaumenSettingsResponse(
        base_url=item.base_url,
        api_version=getattr(item, "api_version", "v2"),
        auth_mode=item.auth_mode,
        username=item.username,
        api_key_masked=api_key_masked,
        basic_password_masked=password_masked,
        request_timeout_seconds=item.request_timeout_seconds,
        verify_ssl=item.verify_ssl,
        enabled=item.enabled,
        configured=naumen_configured(item),
        last_check_status=item.last_check_status,
        last_check_message=item.last_check_message,
        last_check_http_status=getattr(item, "last_check_http_status", None),
        last_check_endpoint=getattr(item, "last_check_endpoint", None),
        last_check_at=item.last_check_at,
    )


def update_naumen_settings(db: Session, payload: NaumenSettingsPayload) -> NaumenConnectionSettings:
    item = get_or_create_naumen_settings(db)
    item.base_url = payload.base_url.strip() if payload.base_url else None
    item.api_version = payload.api_version
    item.auth_mode = payload.auth_mode
    item.username = payload.username.strip() if payload.username else None
    item.request_timeout_seconds = payload.request_timeout_seconds
    item.verify_ssl = payload.verify_ssl
    item.enabled = payload.enabled
    item.updated_at = datetime.utcnow()
    if payload.api_key:
        item.api_key_encrypted = encrypt_token(payload.api_key)
    if payload.basic_password:
        item.basic_password_encrypted = encrypt_token(payload.basic_password)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def decrypted_api_key(item: NaumenConnectionSettings) -> str | None:
    return decrypt_token(item.api_key_encrypted) if item.api_key_encrypted else None


def decrypted_basic_password(item: NaumenConnectionSettings) -> str | None:
    return decrypt_token(item.basic_password_encrypted) if item.basic_password_encrypted else None


def onec_settings_response(item: OneCConnectionSettings) -> OneCSettingsResponse:
    onec_server = getattr(item, "onec_server", None) or item.server
    onec_database = getattr(item, "onec_database", None) or item.database
    onec_cluster = getattr(item, "onec_cluster", None) or item.cluster
    file_base_path = getattr(item, "file_base_path", None) or item.infobase_path
    onec_username = getattr(item, "onec_username", None) or item.username
    password_encrypted = getattr(item, "onec_password_encrypted", None) or item.password_encrypted
    return OneCSettingsResponse(
        connection_mode=item.connection_mode,
        gateway_url=item.gateway_url,
        gateway_token_saved=bool(getattr(item, "gateway_token_encrypted", None)),
        infobase_type=getattr(item, "infobase_type", "server") or "server",
        onec_server=onec_server,
        onec_database=onec_database,
        onec_cluster=onec_cluster,
        file_base_path=file_base_path,
        onec_username=onec_username,
        password_saved=bool(password_encrypted),
        infobase_path=item.infobase_path,
        server=item.server,
        database=item.database,
        cluster=item.cluster,
        username=item.username,
        auth_type=item.auth_type,
        request_timeout_seconds=item.request_timeout_seconds,
        enabled=item.enabled,
        verify_tls=item.verify_tls,
        auto_disable_dismissed=item.auto_disable_dismissed,
        check_on_employee_create=item.check_on_employee_create,
        enable_weekly_1c_status_check=item.enable_weekly_1c_status_check,
        weekly_1c_status_check_day=item.weekly_1c_status_check_day,
        weekly_1c_status_check_time=item.weekly_1c_status_check_time,
        onec_check_batch_size=item.onec_check_batch_size,
        onec_check_pause_ms=item.onec_check_pause_ms,
        configured=onec_configured(item),
        last_check_status=item.last_check_status,
        last_check_message=item.last_check_message,
        last_check_at=item.last_check_at,
    )


def update_onec_settings(db: Session, payload: OneCSettingsPayload) -> OneCConnectionSettings:
    item = get_or_create_onec_settings(db)
    item.connection_mode = payload.connection_mode
    item.gateway_url = payload.gateway_url.strip() if payload.gateway_url else None
    item.infobase_type = payload.infobase_type
    item.onec_server = (payload.onec_server or payload.server or "").strip() or None
    item.onec_database = (payload.onec_database or payload.database or "").strip() or None
    item.onec_cluster = (payload.onec_cluster or payload.cluster or "").strip() or None
    item.file_base_path = (payload.file_base_path or payload.infobase_path or "").strip() or None
    item.onec_username = (payload.onec_username or payload.username or "").strip() or None
    item.infobase_path = item.file_base_path
    item.server = item.onec_server
    item.database = item.onec_database
    item.cluster = item.onec_cluster
    item.username = item.onec_username
    item.auth_type = payload.auth_type
    item.request_timeout_seconds = payload.request_timeout_seconds
    item.enabled = payload.enabled
    item.verify_tls = payload.verify_tls
    item.auto_disable_dismissed = payload.auto_disable_dismissed
    item.check_on_employee_create = payload.check_on_employee_create
    item.enable_weekly_1c_status_check = payload.enable_weekly_1c_status_check
    item.weekly_1c_status_check_day = payload.weekly_1c_status_check_day
    item.weekly_1c_status_check_time = payload.weekly_1c_status_check_time
    item.onec_check_batch_size = payload.onec_check_batch_size
    item.onec_check_pause_ms = payload.onec_check_pause_ms
    item.updated_at = datetime.utcnow()
    if payload.gateway_token:
        item.gateway_token_encrypted = encrypt_token(payload.gateway_token)
    if payload.password:
        encrypted_password = encrypt_token(payload.password)
        item.onec_password_encrypted = encrypted_password
        item.password_encrypted = encrypted_password
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def decrypted_onec_password(item: OneCConnectionSettings) -> str | None:
    encrypted = getattr(item, "onec_password_encrypted", None) or item.password_encrypted
    return decrypt_token(encrypted) if encrypted else None


def decrypted_gateway_token(item: OneCConnectionSettings) -> str | None:
    encrypted = getattr(item, "gateway_token_encrypted", None)
    return decrypt_token(encrypted) if encrypted else None
