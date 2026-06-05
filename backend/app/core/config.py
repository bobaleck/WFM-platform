import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "wfm-naumen")
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    integration_secret_key: str = os.getenv("INTEGRATION_SECRET_KEY", "")
    demo_seed: bool = os.getenv("DEMO_SEED", "false").lower() == "true"
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@local")
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_full_name: str = os.getenv("ADMIN_FULL_NAME", "Администратор")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "Admin12345!")
    naumen_api_base_url: str = os.getenv("NAUMEN_API_BASE_URL", "")
    naumen_api_token: str = os.getenv("NAUMEN_API_TOKEN", "")
    naumen_api_timeout_seconds: int = int(os.getenv("NAUMEN_API_TIMEOUT_SECONDS", "30"))
    ncc_db_host: str = os.getenv("NCC_DB_HOST", "")
    ncc_db_name: str = os.getenv("NCC_DB_NAME", "")
    ncc_db_user: str = os.getenv("NCC_DB_USER", "")
    ncc_db_password: str = os.getenv("NCC_DB_PASSWORD", "")
    ncc_db_port: int = int(os.getenv("NCC_DB_PORT", "5432"))
    ncc_db_timeout_seconds: int = int(os.getenv("NCC_DB_TIMEOUT_SECONDS", "15"))
    ncc_db_max_period_days: int = int(os.getenv("NCC_DB_MAX_PERIOD_DAYS", "31"))


settings = Settings()
