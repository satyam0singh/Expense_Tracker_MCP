"""Analytics Service.

Handles business logic for generating spending insights,
category breakdowns, and trend data.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.logging import get_logger
from expense_tracker.repositories.expense_repository import ExpenseRepository
from expense_tracker.services.base import BaseService

logger = get_logger(__name__)


class AnalyticsService(BaseService):
    """Service for generating analytics and spending insights."""

    def __init__(self, expense_repo: ExpenseRepository | None = None) -> None:
        """Initialize the analytics service.

        Args:
            expense_repo: Optional ExpenseRepository.
        """
        super().__init__()
        self.expense_repo = expense_repo or ExpenseRepository()

    async def get_spending_summary(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get a high-level summary of spending for a period.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: The UUID of the user.

        Returns:
            Dict containing total spend, daily average, and highest expense.
        """
        daily_totals = await self.expense_repo.get_daily_totals(
            session, start_date=start_date, end_date=end_date, user_id=user_id
        )

        total_spend = sum(day["total"] for day in daily_totals)
        days_in_range = (end_date - start_date).days + 1
        daily_avg = total_spend / days_in_range if days_in_range > 0 else 0

        highest_expenses = await self.expense_repo.get_highest_expenses(
            session, start_date=start_date, end_date=end_date, user_id=user_id, limit=1
        )
        highest = highest_expenses[0] if highest_expenses else None

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days_in_range,
            },
            "total_spend": float(total_spend),
            "daily_average": float(daily_avg),
            "highest_expense": {
                "title": highest.title,
                "amount": float(highest.amount),
                "date": highest.expense_date.isoformat(),
                "category": highest.category.name if highest.category else "unknown",
            } if highest else None,
        }

    async def get_category_breakdown(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        user_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Get spending aggregated by category for a period.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: The UUID of the user.

        Returns:
            List of dicts with category name, total, and percentage.
        """
        return await self.expense_repo.get_summary_by_category(
            session, start_date=start_date, end_date=end_date, user_id=user_id
        )

    async def get_spending_trends(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        months: int = 6,
    ) -> list[dict[str, Any]]:
        """Get monthly spending totals for trend analysis.

        Args:
            session: The async database session.
            user_id: The UUID of the user.
            months: Number of months to look back.

        Returns:
            List of dicts with month, total, and count.
        """
        return await self.expense_repo.get_monthly_totals(
            session, months=months, user_id=user_id
        )
