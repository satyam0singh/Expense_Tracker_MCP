"""Budget MCP Tools.

Registers endpoints for managing monthly budgets.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastmcp import FastMCP

from expense_tracker.core.exceptions import AppException
from expense_tracker.database.session import get_session
from expense_tracker.schemas.budget import BudgetCreate, BudgetUpdate
from expense_tracker.services.budget_service import BudgetService
from expense_tracker.utils.datetime_utils import parse_month
from expense_tracker.utils.response import error_response, success_response

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def register_budget_tools(mcp: FastMCP) -> None:
    """Register budget-related tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    budget_service = BudgetService()

    @mcp.tool()
    async def set_budget(
        category_name: str,
        amount: float,
        month: str | None = None,
        currency: str = "INR",
    ) -> dict[str, Any]:
        """Set a monthly budget for a specific category.
        
        Args:
            category_name: The category to budget for (e.g., 'food').
            amount: The budget amount.
            month: The target month in YYYY-MM format. Defaults to current month.
            currency: ISO 3-letter currency code (default: INR).
        """
        try:
            async with get_session() as session:
                data = BudgetCreate(
                    category_name=category_name,
                    budget_amount=amount,  # type: ignore[arg-type]
                    month=month,  # type: ignore[arg-type]
                    currency=currency,  # type: ignore[arg-type]
                )
                
                budget = await budget_service.create_budget(
                    session, user_id=SYSTEM_USER_ID, data=data
                )
                
                return success_response(
                    data={"budget_id": str(budget.id)},
                    message=f"Budget of {budget.budget_amount} {budget.currency} set for {category_name}."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def update_budget(
        budget_id: str,
        amount: float,
    ) -> dict[str, Any]:
        """Update an existing budget amount.
        
        Args:
            budget_id: The UUID of the budget.
            amount: The new budget amount.
        """
        try:
            async with get_session() as session:
                data = BudgetUpdate(budget_amount=amount)  # type: ignore[arg-type]
                budget = await budget_service.update_budget(
                    session,
                    budget_id=uuid.UUID(budget_id),
                    user_id=SYSTEM_USER_ID,
                    data=data,
                )
                return success_response(
                    message=f"Budget updated to {budget.budget_amount} {budget.currency}."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def get_budget_status(month: str | None = None) -> dict[str, Any]:
        """Get the status of all budgets for a given month.
        
        Shows budget amount, spent amount, remaining amount, and alert status
        (e.g., '75% used', 'Budget exceeded').
        
        Args:
            month: The target month in YYYY-MM format. Defaults to current month.
        """
        from datetime import date
        try:
            async with get_session() as session:
                target_month = parse_month(month) if month else date.today()
                
                status_list = await budget_service.get_budgets_for_month(
                    session,
                    user_id=SYSTEM_USER_ID,
                    month=target_month,
                )
                
                return success_response(
                    data=status_list,
                    message=f"Retrieved {len(status_list)} budgets for {target_month.strftime('%B %Y')}."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")
