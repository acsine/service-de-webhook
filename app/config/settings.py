from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import field_validator

class Settings(BaseSettings):
    # App Settings
    ENV: str = "production"
    SECRET_KEY: str = "placeholder_secret_key_change_me"
    ENCRYPTION_KEY: str = "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYQ==" # 32 bytes base64
    FRONTEND_URL: str = "http://localhost:3000"

    # Database Settings
    DATABASE_URL: str = ""
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Settings
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email / Notification Settings
    NOTIFICATION_SERVICE_URL: str = "https://notification-app-jm3r.vercel.app/v1/notification/send-email/"
    DEFAULT_FROM_EMAIL: str = "fomocaleb2@gmail.com"
    DEFAULT_FROM_NAME: str = "Thaborsolition Webhook"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
