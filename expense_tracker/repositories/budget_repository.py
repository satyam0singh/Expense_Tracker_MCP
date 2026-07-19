"""Budget repository — data access for budget records.

Extends BaseRepository with budget-specific queries: find by month,
find by category+month, and spent amount updates.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.budget import Budget
from expense_tracker.database.models.category import Category
from expense_tracker.repositories.base import BaseRepository

logger = get_logger(__name__)


class BudgetRepository(BaseRepository[Budget]):
    """Repository for budget data access.

    Manages monthly budget records with category-scoped filtering.
    """

    def __init__(self) -> None:
        """Initialize with the Budget model."""
        super().__init__(Budget)

    async def get_by_month(
        self,
        session: AsyncSession,
        month: date,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[Budget]:
        """Get all budgets for a specific month.

        Args:
            session: The async database session.
            month: The first day of the target month.
            user_id: Optional filter by user.

        Returns:
            List of budgets for the month.
        """
        conditions: list[Any] = [
            Budget.deleted_at.is_(None),
            Budget.month == month,
        ]
        if user_id is not None:
            conditions.append(Budget.user_id == user_id)

        stmt = (
            select(Budget)
            .where(*conditions)
            .options(joinedload(Budget.category))
            .order_by(Budget.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_by_category_and_month(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        month: date,
        *,
        user_id: uuid.UUID | None = None,
    ) -> Budget | None:
        """Get a budget for a specific category and month.

        Args:
            session: The async database session.
            category_id: The category UUID.
            month: The first day of the target month.
            user_id: Optional filter by user.

        Returns:
            The budget if found, None otherwise.
        """
        conditions: list[Any] = [
            Budget.deleted_at.is_(None),
            Budget.category_id == category_id,
            Budget.month == month,
        ]
        if user_id is not None:
            conditions.append(Budget.user_id == user_id)

        stmt = (
            select(Budget)
            .where(*conditions)
            .options(joinedload(Budget.category))
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def update_spent_amount(
        self,
        session: AsyncSession,
        budget_id: uuid.UUID,
        spent_amount: Decimal,
    ) -> Budget:
        """Update the spent amount on a budget.

        Args:
            session: The async database session.
            budget_id: The budget UUID.
            spent_amount: The new spent amount.

        Returns:
            The updated budget.
        """
        budget = await self.get_by_id_or_raise(session, budget_id)
        budget.spent_amount = spent_amount  # type: ignore[assignment]
        await session.flush()
        await session.refresh(budget)
        logger.debug(
            "budget_spent_updated",
            budget_id=str(budget_id),
            spent_amount=float(spent_amount),
        )
        return budget

    async def get_budgets_with_status(
        self,
        session: AsyncSession,
        month: date,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Get all budgets for a month with computed status.

        Returns enriched budget data including remaining amount,
        usage percentage, and alert flags.

        Args:
            session: The async database session.
            month: The first day of the target month.
            user_id: Optional filter by user.

        Returns:
            List of dicts with budget data and status indicators.
        """
        budgets = await self.get_by_month(session, month, user_id=user_id)

        status_list = []
        for budget in budgets:
            remaining = budget.remaining
            pct_used = budget.percentage_used
            category_name = budget.category.name if budget.category else "unknown"

            # Determine alert level
            alert = None
            if pct_used >= 100:
                alert = f"Budget exceeded for {category_name}!"
            elif pct_used >= 90:
                alert = f"90% of budget used for {category_name}"
            elif pct_used >= 75:
                alert = f"75% of budget used for {category_name}"

            status_list.append({
                "budget_id": str(budget.id),
                "category": category_name,
                "month": str(budget.month),
                "budget_amount": float(budget.budget_amount),
                "spent_amount": float(budget.spent_amount),
                "remaining": float(remaining),
                "percentage_used": round(pct_used, 2),
                "currency": budget.currency,
                "alert": alert,
            })

        return status_list

    async def exists_for_category_and_month(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        month: date,
        *,
        user_id: uuid.UUID | None = None,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if a budget already exists for a category+month combo.

        Args:
            session: The async database session.
            category_id: The category UUID.
            month: The first day of the target month.
            user_id: Optional filter by user.
            exclude_id: Optional budget ID to exclude (for updates).

        Returns:
            True if a matching budget already exists.
        """
        conditions: list[Any] = [
            Budget.deleted_at.is_(None),
            Budget.category_id == category_id,
            Budget.month == month,
        ]
        if user_id is not None:
            conditions.append(Budget.user_id == user_id)
        if exclude_id is not None:
            conditions.append(Budget.id != exclude_id)

        stmt = (
            select(func.count()).select_from(Budget).where(*conditions)
        )
        result = await session.execute(stmt)
        return result.scalar_one() > 0
