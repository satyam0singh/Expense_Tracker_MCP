"""Report Service.

Handles generating data exports (CSV, Excel) for expenses.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.logging import get_logger
from expense_tracker.repositories.expense_repository import ExpenseRepository
from expense_tracker.services.base import BaseService

logger = get_logger(__name__)


class ReportService(BaseService):
    """Service for generating expense reports and data exports."""

    def __init__(self, expense_repo: ExpenseRepository | None = None) -> None:
        """Initialize the report service.

        Args:
            expense_repo: Optional ExpenseRepository.
        """
        super().__init__()
        self.expense_repo = expense_repo or ExpenseRepository()

    async def generate_csv_report(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        user_id: uuid.UUID,
    ) -> str:
        """Generate a CSV report of expenses for a date range.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: The UUID of the user.

        Returns:
            CSV file content as a string.
        """
        # We need all records, so limit=10000 (practical limit for CSV export via MCP)
        # For a truly massive export, this would be paginated and written to a file.
        expenses, _ = await self.expense_repo.find_by_date_range(
            session=session,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            limit=10000, 
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Date",
            "Category",
            "Subcategory",
            "Title",
            "Amount",
            "Currency",
            "Payment Method",
            "Notes"
        ])

        # Rows
        for expense in expenses:
            category_name = expense.category.display_name if expense.category else ""
            subcategory_name = expense.subcategory.display_name if expense.subcategory else ""
            
            writer.writerow([
                expense.expense_date.isoformat(),
                category_name,
                subcategory_name,
                expense.title,
                f"{expense.amount:.2f}",
                expense.currency,
                expense.payment_method,
                expense.notes or ""
            ])

        return output.getvalue()

    # Excel and PDF report generation will be implemented in Phase 6.
