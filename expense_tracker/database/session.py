"""Async SQLAlchemy engine and session management.

Provides the database engine lifecycle (create/dispose) and an
async session factory. The get_session() context manager should
be used in services and repositories to obtain a session that
auto-commits on success and rolls back on failure.

Usage:
    from expense_tracker.database.session import get_session

    async with get_session() as session:
        result = await session.execute(select(Expense))
        expenses = result.scalars().all()

Engine Lifecycle:
    Call init_engine() at application startup.
    Call dispose_engine() at application shutdown.
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from expense_tracker.core.config import get_settings
from expense_tracker.core.constants import SLOW_QUERY_THRESHOLD_MS
from expense_tracker.core.logging import get_logger

logger = get_logger(__name__)

# Module-level engine and session factory (initialized at startup)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _attach_query_timing(sync_engine: Any) -> None:
    """Attach event listeners to log slow queries.

    Listens to the synchronous engine underlying the async engine
    to measure query execution time and warn on slow queries.

    Args:
        sync_engine: The sync engine from async_engine.sync_engine.
    """

    @event.listens_for(sync_engine, "before_cursor_execute")
    def _before_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        conn.info["query_start_time"] = time.perf_counter()

    @event.listens_for(sync_engine, "after_cursor_execute")
    def _after_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        start_time = conn.info.get("query_start_time")
        if start_time is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            if duration_ms > SLOW_QUERY_THRESHOLD_MS:
                logger.warning(
                    "slow_query_detected",
                    duration_ms=round(duration_ms, 2),
                    statement=statement[:200],
                )


async def init_engine() -> AsyncEngine:
    """Create and configure the async SQLAlchemy engine.

    Reads connection parameters from application settings. Attaches
    slow-query timing listeners. Stores the engine and session factory
    at module level for use by get_session().

    Returns:
        The initialized AsyncEngine.

    Raises:
        RuntimeError: If the engine is already initialized.
    """
    global _engine, _session_factory  # noqa: PLW0603

    if _engine is not None:
        logger.warning("engine_already_initialized")
        return _engine

    settings = get_settings()

    connect_args = {}
    if "asyncpg" in settings.database_url:
        connect_args["statement_cache_size"] = 0

    _engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_pre_ping=True,
        echo=settings.debug,
        connect_args=connect_args,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Attach slow query listener to the underlying sync engine
    _attach_query_timing(_engine.sync_engine)

    logger.info(
        "database_engine_initialized",
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )

    return _engine


async def dispose_engine() -> None:
    """Dispose the async engine and release all connections.

    Call during application shutdown to cleanly close the
    connection pool.
    """
    global _engine, _session_factory  # noqa: PLW0603

    if _engine is not None:
        await _engine.dispose()
        logger.info("database_engine_disposed")
        _engine = None
        _session_factory = None


def get_engine() -> AsyncEngine:
    """Return the current async engine.

    Returns:
        The initialized AsyncEngine.

    Raises:
        RuntimeError: If the engine has not been initialized.
    """
    if _engine is None:
        msg = (
            "Database engine not initialized. "
            "Call init_engine() during application startup."
        )
        raise RuntimeError(msg)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the current session factory.

    Returns:
        The async session factory.

    Raises:
        RuntimeError: If the engine has not been initialized.
    """
    if _session_factory is None:
        msg = (
            "Session factory not initialized. "
            "Call init_engine() during application startup."
        )
        raise RuntimeError(msg)
    return _session_factory


_init_lock = None

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async database session.

    Auto-commits on successful exit, rolls back on exception.
    Sessions should not be long-lived — create one per operation.
    Lazily initializes the engine and seeds the database if not already done.

    Yields:
        An AsyncSession bound to the application engine.

    Raises:
        RuntimeError: If the engine has not been initialized.

    Example:
        async with get_session() as session:
            expense = Expense(title="Lunch", amount=Decimal("250.00"))
            session.add(expense)
            # Auto-commits on exit
    """
    global _session_factory, _init_lock
    if _session_factory is None:
        if _init_lock is None:
            import asyncio
            _init_lock = asyncio.Lock()
        
        async with _init_lock:
            if _session_factory is None:
                await init_engine()
                from expense_tracker.server import seed_database
                await seed_database()

    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
