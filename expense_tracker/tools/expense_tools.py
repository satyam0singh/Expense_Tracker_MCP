"""Expense MCP Tools.

Registers endpoints for managing expenses.
"""

from __future__ import annotations

from typing import Any
import uuid

from fastmcp import FastMCP

from expense_tracker.core.exceptions import AppException
from expense_tracker.database.session import get_session
from expense_tracker.schemas.expense import ExpenseCreate, ExpenseUpdate
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.utils.response import error_response, success_response

# Fixed system user ID for single-user mode. Multi-user requires auth context.
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def register_expense_tools(mcp: FastMCP) -> None:
    """Register expense-related tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    expense_service = ExpenseService()

    @mcp.tool()
    async def add_expense(
        title: str,
        amount: float,
        category_name: str,
        payment_method: str = "cash",
        currency: str = "INR",
        subcategory_name: str | None = None,
        expense_date: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Add a new expense record and auto-update the corresponding budget.
        
        Args:
            title: Short description of the expense.
            amount: The expense amount (must be positive).
            category_name: The name of the category (e.g., 'food', 'transport').
            payment_method: Payment method (e.g., 'cash', 'credit_card', 'upi').
            currency: ISO 3-letter currency code (default: INR).
            subcategory_name: Optional subcategory name.
            expense_date: Optional date (YYYY-MM-DD). Defaults to today.
            notes: Optional detailed notes.
        """
        try:
            async with get_session() as session:
                data = ExpenseCreate(
                    title=title,
                    amount=amount,  # type: ignore[arg-type]
                    category_name=category_name,
                    payment_method=payment_method,  # type: ignore[arg-type]
                    currency=currency,  # type: ignore[arg-type]
                    subcategory_name=subcategory_name,
                    expense_date=expense_date,  # type: ignore[arg-type]
                    notes=notes,
                )
                expense = await expense_service.create_expense(
                    session, user_id=SYSTEM_USER_ID, data=data
                )
                return success_response(
                    data={"expense_id": str(expense.id)},
                    message=f"Added expense '{expense.title}' for {expense.amount} {expense.currency}."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def update_expense(
        expense_id: str,
        title: str | None = None,
        amount: float | None = None,
        category_name: str | None = None,
        payment_method: str | None = None,
        currency: str | None = None,
        expense_date: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing expense record. Budgets will be re-synced automatically.
        
        Args:
            expense_id: The UUID of the expense to update.
            title: New description.
            amount: New amount.
            category_name: New category name.
            payment_method: New payment method.
            currency: New ISO currency code.
            expense_date: New date (YYYY-MM-DD).
            notes: New notes.
        """
        try:
            async with get_session() as session:
                update_kwargs: dict[str, Any] = {}
                if title is not None: update_kwargs["title"] = title
                if amount is not None: update_kwargs["amount"] = amount
                if payment_method is not None: update_kwargs["payment_method"] = payment_method
                if currency is not None: update_kwargs["currency"] = currency
                if expense_date is not None: update_kwargs["expense_date"] = expense_date
                if notes is not None: update_kwargs["notes"] = notes
                
                # If category_name is provided, we need to resolve it manually since ExpenseUpdate
                # expects category_id. The service layer typically does this, but for simplicity
                # in the tool, we'll resolve it here if passed as name.
                if category_name is not None:
                    cat_id = await expense_service.category_service.resolve_category_id(
                        session, category_name=category_name
                    )
                    update_kwargs["category_id"] = cat_id

                data = ExpenseUpdate(**update_kwargs)
                expense = await expense_service.update_expense(
                    session,
                    expense_id=uuid.UUID(expense_id),
                    user_id=SYSTEM_USER_ID,
                    data=data,
                )
                return success_response(
                    data={"expense_id": str(expense.id)},
                    message="Expense updated successfully."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def delete_expense(expense_id: str) -> dict[str, Any]:
        """Soft-delete an expense record. Budgets will be automatically re-synced.
        
        Args:
            expense_id: The UUID of the expense to delete.
        """
        try:
            async with get_session() as session:
                await expense_service.delete_expense(
                    session,
                    expense_id=uuid.UUID(expense_id),
                    user_id=SYSTEM_USER_ID,
                )
                return success_response(message="Expense deleted successfully.")
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")

    @mcp.tool()
    async def search_expenses(
        query: str,
        start_date: str | None = None,
        end_date: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search expenses by title or notes.
        
        Args:
            query: The search term (case-insensitive).
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            offset: Pagination offset.
            limit: Maximum number of results to return.
        """
        from expense_tracker.utils.datetime_utils import parse_date
        try:
            async with get_session() as session:
                parsed_start = parse_date(start_date) if start_date else None
                parsed_end = parse_date(end_date) if end_date else None
                
                items, total = await expense_service.search_expenses(
                    session,
                    query=query,
                    user_id=SYSTEM_USER_ID,
                    start_date=parsed_start,
                    end_date=parsed_end,
                    offset=offset,
                    limit=limit,
                )
                
                return success_response(
                    data={
                        "items": [
                            {
                                "id": str(item.id),
                                "date": item.expense_date.isoformat(),
                                "title": item.title,
                                "amount": float(item.amount),
                                "category": item.category.name if item.category else None,
                            }
                            for item in items
                        ],
                        "total": total
                    },
                    message=f"Found {total} expenses matching '{query}'."
                )
        except AppException as exc:
            return error_response(exc)
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")
