"""Alembic migration environment configuration.

Configures Alembic to:
1. Read DATABASE_URL_SYNC from application settings (not alembic.ini).
2. Import all ORM models so autogenerate detects schema changes.
3. Support both online (connected) and offline (SQL script) migrations.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Import all models so Alembic's autogenerate can detect them ──
# This import must happen before target_metadata is set.
from expense_tracker.database.base import Base
from expense_tracker.database.models import (  # noqa: F401
    AuditLog,
    Budget,
    Category,
    CreditCard,
    Expense,
    ExpenseAttachment,
    Subcategory,
    User,
)

# Alembic Config object (provides access to alembic.ini values)
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def _get_sync_url() -> str:
    """Get the synchronous database URL from application settings.

    Falls back to the alembic.ini value if settings can't be loaded.

    Returns:
        PostgreSQL connection URL using psycopg (sync driver).
    """
    try:
        from expense_tracker.core.config import get_settings

        return get_settings().database_url_sync
    except Exception:
        # Fallback to alembic.ini if settings aren't available
        url = config.get_main_option("sqlalchemy.url")
        if url is None:
            msg = "No database URL configured in settings or alembic.ini"
            raise RuntimeError(msg)
        return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for generating migration scripts for review or
    applying in restricted environments.
    """
    url = _get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Connects to the database and applies migrations within
    a transaction.
    """
    # Override the URL from alembic.ini with our settings
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_sync_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
