"""Structured logging configuration using structlog.

Provides JSON-formatted logs with automatic context binding for
request IDs, tool names, and execution timing. Supports both
JSON output (for production/log aggregators) and console output
(for local development).

Usage:
    from expense_tracker.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("expense_created", expense_id=str(expense.id), amount=150.00)

    # With bound context (persists across calls)
    log = logger.bind(request_id="abc-123", tool="add_expense")
    log.info("processing")
    log.info("completed", duration_ms=42)
"""

from __future__ import annotations

import logging
import sys
import time
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from typing import Any
from uuid import uuid4

import structlog

from expense_tracker.core.config import get_settings


def setup_logging() -> None:
    """Configure structlog and stdlib logging for the application.

    Reads LOG_LEVEL and LOG_FORMAT from settings. Call once at
    application startup before any logging occurs.

    JSON format produces machine-parseable output suitable for
    ELK, Datadog, or CloudWatch. Console format produces colored
    human-readable output for local development.
    """
    settings = get_settings()

    # Configure stdlib logging (used by SQLAlchemy, Alembic, etc.)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, settings.log_level),
    )

    # Shared processors for all output formats
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        # Production: JSON output
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Development: Colored console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Apply the formatter to the root handler
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

    # Quiet down noisy loggers
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.debug else logging.WARNING,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A bound structlog logger with context support.
    """
    return structlog.get_logger(name)


def generate_request_id() -> str:
    """Generate a unique request ID for MCP tool invocations.

    Returns:
        A short UUID string suitable for log correlation.
    """
    return uuid4().hex[:12]


@contextmanager
def log_execution(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    **context: Any,
) -> Generator[dict[str, Any], None, None]:
    """Context manager that logs the start and end of an operation with timing.

    Args:
        logger: The structlog logger to use.
        operation: Name of the operation being timed.
        **context: Additional key-value pairs to include in log entries.

    Yields:
        A mutable dictionary where callees can add extra result context
        (e.g., row_count, entity_id) that will be included in the
        completion log entry.

    Example:
        with log_execution(logger, "create_expense", category="food") as ctx:
            expense = repo.create(data)
            ctx["expense_id"] = str(expense.id)
    """
    result_context: dict[str, Any] = {}
    start = time.perf_counter()
    logger.info(f"{operation}.started", **context)
    try:
        yield result_context
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{operation}.completed",
            duration_ms=round(duration_ms, 2),
            **context,
            **result_context,
        )
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            f"{operation}.failed",
            duration_ms=round(duration_ms, 2),
            **context,
            **result_context,
        )
        raise


@asynccontextmanager
async def async_log_execution(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    **context: Any,
) -> AsyncGenerator[dict[str, Any], None]:
    """Async version of log_execution for async operations.

    Args:
        logger: The structlog logger to use.
        operation: Name of the operation being timed.
        **context: Additional key-value pairs to include in log entries.

    Yields:
        A mutable dictionary for additional result context.
    """
    result_context: dict[str, Any] = {}
    start = time.perf_counter()
    logger.info(f"{operation}.started", **context)
    try:
        yield result_context
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{operation}.completed",
            duration_ms=round(duration_ms, 2),
            **context,
            **result_context,
        )
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            f"{operation}.failed",
            duration_ms=round(duration_ms, 2),
            **context,
            **result_context,
        )
        raise
