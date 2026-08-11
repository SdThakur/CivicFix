"""Application Configuration Settings."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings for CivicFix application."""

    PROJECT_NAME: str = "CivicFix Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database settings: defaults to SQLite for portable local execution / testing
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./civicfix.db"
    )
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL

    # Security & Auth
    SECRET_KEY: str = "SUPER_SECRET_KEY_CIVICFIX_2026_PRODUCTION_SECURE_KEY_HASH"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # AI / Triage defaults
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
    AI_DUPLICATE_DISTANCE_METERS: float = 100.0
    AI_DUPLICATE_TIME_DAYS: int = 14
    AI_DUPLICATE_THRESHOLD: float = 0.70

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
