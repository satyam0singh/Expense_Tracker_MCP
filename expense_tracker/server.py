"""Expense Tracker MCP Server Bootstrap.

Initializes FastMCP, sets up the database engine, seeds defaults,
and registers all tool domains. Exposes the `main()` entrypoint.
"""

from __future__ import annotations

import asyncio
import sys
import uuid

from fastmcp import FastMCP

from expense_tracker.core.config import get_settings
from expense_tracker.core.logging import get_logger, setup_logging
from expense_tracker.database.models.user import User
from expense_tracker.database.session import dispose_engine, get_session, init_engine
from expense_tracker.services.category_service import CategoryService
from expense_tracker.tools.analytics_tools import register_analytics_tools
from expense_tracker.tools.budget_tools import register_budget_tools
from expense_tracker.tools.category_tools import register_category_tools
from expense_tracker.tools.credit_card_tools import register_credit_card_tools
from expense_tracker.tools.expense_tools import register_expense_tools
from expense_tracker.tools.report_tools import register_report_tools

# Single-user system default for prototype and local use
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def seed_database() -> None:
    """Seed the database with default data if missing.

    Ensures the system user and default category taxonomy exist.
    """
    logger = get_logger("expense_tracker.seed")
    logger.info("seeding_database")

    async with get_session() as session:
        # Seed System User
        user = await session.get(User, SYSTEM_USER_ID)
        if user is None:
            user = User(
                id=SYSTEM_USER_ID,
                username="system",
                email="system@expensetracker.local",
                display_name="System User",
            )
            session.add(user)
            logger.info("system_user_created")

        # Seed Categories
        category_service = CategoryService()
        result = await category_service.initialize_default_categories(session)
        logger.info("categories_seeded", **result)


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance.

    Returns:
        The configured FastMCP server.
    """
    settings = get_settings()
    
    mcp = FastMCP(
        settings.app_name,
        dependencies=["expense-tracker-mcp-server"],
    )

    # Register all domains
    register_expense_tools(mcp)
    register_category_tools(mcp)
    register_budget_tools(mcp)
    register_analytics_tools(mcp)
    register_credit_card_tools(mcp)
    register_report_tools(mcp)

    return mcp


async def _run_server_async(mcp: FastMCP) -> None:
    """Run the server lifecycle (startup, run, shutdown)."""
    logger = get_logger("expense_tracker.server")
    
    try:
        # Startup
        await init_engine()
        
        # We assume migrations have been run. Seed data.
        await seed_database()
        
        # Run MCP server (blocks until shutdown)
        logger.info("server_starting", app_name=mcp.name)
        await mcp.run_stdio_async()
        
    except KeyboardInterrupt:
        logger.info("server_interrupted")
    except Exception as exc:
        logger.exception("server_error", error=str(exc))
        sys.exit(1)
    finally:
        # Shutdown
        logger.info("server_shutting_down")
        await dispose_engine()


def main() -> None:
    """Entry point for the console script."""
    # 1. Setup structured logging first
    setup_logging()
    
    # 2. Create server and register tools
    mcp = create_server()
    
    # 3. Run async event loop
    # We use asyncio.run() because FastMCP handles its own loop internally when using run_stdio_async,
    # but we need to orchestrate the database lifecycle around it.
    asyncio.run(_run_server_async(mcp))


if __name__ == "__main__":
    main()
