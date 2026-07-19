"""Application configuration using Pydantic Settings.

Loads configuration from environment variables and .env files.
Provides a singleton settings instance via get_settings().

Environment Variables:
    DATABASE_URL: Async PostgreSQL connection string.
    DATABASE_URL_SYNC: Sync PostgreSQL connection string (for Alembic).
    DB_POOL_SIZE: Connection pool size (default: 10).
    DB_MAX_OVERFLOW: Max overflow connections (default: 20).
    DB_POOL_TIMEOUT: Pool timeout in seconds (default: 30).
    APP_NAME: Application name (default: ExpenseTrackerMCP).
    APP_VERSION: Application version (default: 1.0.0).
    DEBUG: Debug mode flag (default: false).
    LOG_LEVEL: Logging level (default: INFO).
    LOG_FORMAT: Log format - 'json' or 'console' (default: json).
    REPORTS_DIR: Directory for generated reports (default: ./reports).
    DEFAULT_CURRENCY: Default currency code (default: INR).
    BACKUP_DIR: Directory for database backups (default: ./backups).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        database_url: Async PostgreSQL connection URL.
        database_url_sync: Sync PostgreSQL connection URL for Alembic.
        db_pool_size: SQLAlchemy connection pool size.
        db_max_overflow: Maximum number of overflow connections.
        db_pool_timeout: Connection pool timeout in seconds.
        app_name: Human-readable application name.
        app_version: Semantic version string.
        debug: Enable debug mode.
        log_level: Minimum log level.
        log_format: Output format for structured logs.
        reports_dir: Directory path for generated report files.
        default_currency: ISO 4217 currency code used as default.
        backup_dir: Directory path for database backup files.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/expense_tracker",
        description="Async PostgreSQL connection URL.",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/expense_tracker",
        description="Sync PostgreSQL connection URL (used by Alembic).",
    )
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=200)
    db_pool_timeout: int = Field(default=30, ge=5, le=120)

    # ── Application ──────────────────────────────────────────
    app_name: str = Field(default="ExpenseTrackerMCP")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # ── Logging ──────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # ── Reports ──────────────────────────────────────────────
    reports_dir: Path = Field(default=Path("./reports"))

    # ── Currency ─────────────────────────────────────────────
    default_currency: str = Field(default="INR")

    # ── Backup ───────────────────────────────────────────────
    backup_dir: Path = Field(default=Path("./backups"))

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Ensure log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in valid_levels:
            msg = f"Invalid log level '{value}'. Must be one of: {valid_levels}"
            raise ValueError(msg)
        return upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, value: str) -> str:
        """Ensure log format is either 'json' or 'console'."""
        lower = value.lower()
        if lower not in {"json", "console"}:
            msg = f"Invalid log format '{value}'. Must be 'json' or 'console'."
            raise ValueError(msg)
        return lower

    @field_validator("default_currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        """Ensure currency is a 3-letter ISO 4217 code."""
        upper = value.upper()
        if len(upper) != 3 or not upper.isalpha():
            msg = f"Invalid currency '{value}'. Must be a 3-letter ISO 4217 code."
            raise ValueError(msg)
        return upper

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance.

    Uses lru_cache to ensure only one instance is created per process.
    Call get_settings.cache_clear() in tests to reset.

    Returns:
        The application settings loaded from environment.
    """
    return Settings()
