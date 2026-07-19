"""Analytics MCP Tools.

Registers endpoints for querying spending analytics and trends.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastmcp import FastMCP

from expense_tracker.core.exceptions import AppException
from expense_tracker.database.session import get_session
from expense_tracker.services.analytics_service import AnalyticsService
from expense_tracker.utils.datetime_utils import get_month_range, parse_month
from expense_tracker.utils.response import error_response, success_response

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def register_analytics_tools(mcp: FastMCP) -> None:
    """Register analytics-related tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    analytics_service = AnalyticsService()

    @mcp.tool()
    async def analyze_spending(month: str | None = None) -> dict[str, Any]:
        """Get a high-level summary of spending for a given month.
        
        Args:
            month: The target month in YYYY-MM format. Defaults to current month.
        """
        from datetime import date
        try:
            async with get_session() as session:
                target_month = parse_month(month) if month else date.today()
                start_date, end_date = get_month_range(target_month.year, target_month.month)
                
                summary = await analytics_service.get_spending_summary(
                    session,
                    start_date=start_date,
                    end_date=end_date,
                    user_id=SYSTEM_USER_ID,
                )
                
                return success_response(
                    data=summary,
                    message="Spending summary generated successfully."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def get_category_breakdown(month: str | None = None) -> dict[str, Any]:
        """Get a breakdown of spending by category for a given month.
        
        Args:
            month: The target month in YYYY-MM format. Defaults to current month.
        """
        from datetime import date
        try:
            async with get_session() as session:
                target_month = parse_month(month) if month else date.today()
                start_date, end_date = get_month_range(target_month.year, target_month.month)
                
                breakdown = await analytics_service.get_category_breakdown(
                    session,
                    start_date=start_date,
                    end_date=end_date,
                    user_id=SYSTEM_USER_ID,
                )
                
                return success_response(
                    data=breakdown,
                    message="Category breakdown generated successfully."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def get_spending_trends(months: int = 6) -> dict[str, Any]:
        """Get monthly spending totals for trend analysis over the last N months.
        
        Args:
            months: Number of months to look back. Defaults to 6.
        """
        try:
            async with get_session() as session:
                trends = await analytics_service.get_spending_trends(
                    session,
                    user_id=SYSTEM_USER_ID,
                    months=months,
                )
                
                return success_response(
                    data=trends,
                    message=f"Spending trends for the last {months} months generated."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")
