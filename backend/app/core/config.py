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
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./civicfix.db")
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

    # Supabase & Async Pipeline Settings
    SUPABASE_URL: str = os.getenv(
        "SUPABASE_URL", "https://tywmyjecafmpufdfxbus.supabase.co"
    )
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv(
        "SUPABASE_PUBLISHABLE_KEY", "sb_publishable_dSoVH6SAgzYJ7dWeo_drOg_UCcqNmuw"
    )
    SUPABASE_SECRET_KEY: str = os.getenv(
        "SUPABASE_SECRET_KEY", "dev-placeholder-secret-key-not-for-production"
    )
    SUPABASE_JWKS_URL: str = os.getenv(
        "SUPABASE_JWKS_URL",
        "https://tywmyjecafmpufdfxbus.supabase.co/auth/v1/.well-known/jwks.json",
    )
    # Feature flag to switch between async 202 ingestion and legacy synchronous pipeline
    NEXT_PUBLIC_ASYNC_REPORTS: bool = os.getenv(
        "NEXT_PUBLIC_ASYNC_REPORTS", "true"
    ).lower() in ("true", "1", "yes")
    REPORTS_RATE_LIMIT_PER_MINUTE: int = int(
        os.getenv("REPORTS_RATE_LIMIT_PER_MINUTE", "10")
    )
    PROOFS_SIGNED_URL_EXPIRY_SECONDS: int = int(
        os.getenv("PROOFS_SIGNED_URL_EXPIRY_SECONDS", "900")
    )

    # Database Read Replica Setting
    DATABASE_REPLICA_URL: Optional[str] = os.getenv("DATABASE_REPLICA_URL", None)

    # Redis Scaling, Caching & Rate Limiting Settings
    LIMITS_REDIS_URL: str = os.getenv(
        "LIMITS_REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379/1")
    )
    QUEUE_REDIS_URL: str = os.getenv(
        "QUEUE_REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    CACHE_REDIS_URL: str = os.getenv(
        "CACHE_REDIS_URL",
        os.getenv(
            "LIMITS_REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379/1")
        ),
    )
    MAP_CACHE_TTL_SECONDS: int = int(os.getenv("MAP_CACHE_TTL_SECONDS", "30"))
    STATS_CACHE_TTL_SECONDS: int = int(os.getenv("STATS_CACHE_TTL_SECONDS", "60"))
    GEMINI_DAILY_BUDGET: int = int(os.getenv("GEMINI_DAILY_BUDGET", "500"))
    REPORTS_RATE_LIMIT_SIGNED_IN: int = int(
        os.getenv("REPORTS_RATE_LIMIT_SIGNED_IN", "10")
    )
    REPORTS_RATE_LIMIT_ANONYMOUS: int = int(
        os.getenv("REPORTS_RATE_LIMIT_ANONYMOUS", "3")
    )
    REPORTS_RATE_LIMIT_WINDOW_SECONDS: int = int(
        os.getenv("REPORTS_RATE_LIMIT_WINDOW_SECONDS", "3600")
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
