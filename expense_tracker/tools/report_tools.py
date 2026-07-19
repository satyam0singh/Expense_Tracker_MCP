"""Report MCP Tools.

Registers endpoints for generating data exports.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastmcp import FastMCP

from expense_tracker.core.constants import get_system_user_id
from expense_tracker.core.exceptions import AppException
from expense_tracker.database.session import get_session
from expense_tracker.services.report_service import ReportService
from expense_tracker.utils.datetime_utils import get_month_range, parse_month
from expense_tracker.utils.response import error_response, success_response

SYSTEM_USER_ID = get_system_user_id()


def register_report_tools(mcp: FastMCP) -> None:
    """Register report-related tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    report_service = ReportService()

    @mcp.tool()
    async def export_csv(month: str | None = None) -> dict[str, Any]:
        """Generate a CSV export of expenses for a given month.
        
        Args:
            month: The target month in YYYY-MM format. Defaults to current month.
        """
        from datetime import date
        try:
            async with get_session() as session:
                target_month = parse_month(month) if month else date.today()
                start_date, end_date = get_month_range(target_month.year, target_month.month)
                
                csv_data = await report_service.generate_csv_report(
                    session,
                    start_date=start_date,
                    end_date=end_date,
                    user_id=SYSTEM_USER_ID,
                )
                
                return success_response(
                    data={"csv": csv_data},
                    message=f"CSV export generated for {target_month.strftime('%B %Y')}."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def export_excel(month: str | None = None) -> dict[str, Any]:
        """Generate an Excel export of expenses for a given month.
        
        Args:
            month: The target month in YYYY-MM format. Defaults to current month.
        """
        import base64
        from datetime import date
        try:
            async with get_session() as session:
                target_month = parse_month(month) if month else date.today()
                start_date, end_date = get_month_range(target_month.year, target_month.month)
                
                excel_bytes = await report_service.generate_excel_report(
                    session,
                    start_date=start_date,
                    end_date=end_date,
                    user_id=SYSTEM_USER_ID,
                )
                
                # MCP transfers binary data as base64 strings
                b64_data = base64.b64encode(excel_bytes).decode("utf-8")
                
                return success_response(
                    data={"excel_base64": b64_data},
                    message=f"Excel export generated for {target_month.strftime('%B %Y')}."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def export_pdf(month: str | None = None) -> dict[str, Any]:
        """Generate a PDF export of expenses for a given month.
        
        Args:
            month: The target month in YYYY-MM format. Defaults to current month.
        """
        import base64
        from datetime import date
        try:
            async with get_session() as session:
                target_month = parse_month(month) if month else date.today()
                start_date, end_date = get_month_range(target_month.year, target_month.month)
                
                pdf_bytes = await report_service.generate_pdf_report(
                    session,
                    start_date=start_date,
                    end_date=end_date,
                    user_id=SYSTEM_USER_ID,
                )
                
                b64_data = base64.b64encode(pdf_bytes).decode("utf-8")
                
                return success_response(
                    data={"pdf_base64": b64_data},
                    message=f"PDF export generated for {target_month.strftime('%B %Y')}."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")
