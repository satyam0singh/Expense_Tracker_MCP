"""Expense repository — data access for expense records.

Extends BaseRepository with expense-specific queries: date range
filtering, full-text search, category aggregation, daily totals,
and spending trend analysis.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, String, case, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.category import Category
from expense_tracker.database.models.expense import Expense
from expense_tracker.database.models.subcategory import Subcategory
from expense_tracker.repositories.base import BaseRepository

logger = get_logger(__name__)


class ExpenseRepository(BaseRepository[Expense]):
    """Repository for expense data access.

    Provides domain-specific queries beyond standard CRUD,
    including search, date filtering, and aggregation.
    """

    def __init__(self) -> None:
        """Initialize with the Expense model."""
        super().__init__(Expense)

    # ── Queries ──────────────────────────────────────────────

    async def find_by_date_range(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        *,
        user_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        payment_method: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """Find expenses within an inclusive date range with optional filters.

        Args:
            session: The async database session.
            start_date: Start of the date range (inclusive).
            end_date: End of the date range (inclusive).
            user_id: Optional filter by user.
            category_id: Optional filter by category.
            payment_method: Optional filter by payment method.
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            Tuple of (expenses, total_count).
        """
        base_stmt = select(Expense).where(
            Expense.deleted_at.is_(None),
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        )
        count_stmt = (
            select(func.count())
            .select_from(Expense)
            .where(
                Expense.deleted_at.is_(None),
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        )

        if user_id is not None:
            base_stmt = base_stmt.where(Expense.user_id == user_id)
            count_stmt = count_stmt.where(Expense.user_id == user_id)

        if category_id is not None:
            base_stmt = base_stmt.where(Expense.category_id == category_id)
            count_stmt = count_stmt.where(Expense.category_id == category_id)

        if payment_method is not None:
            base_stmt = base_stmt.where(Expense.payment_method == payment_method)
            count_stmt = count_stmt.where(Expense.payment_method == payment_method)

        # Total count
        total = (await session.execute(count_stmt)).scalar_one()

        # Paginated results with eager-loaded relationships
        base_stmt = (
            base_stmt.options(
                joinedload(Expense.category),
                joinedload(Expense.subcategory),
            )
            .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(base_stmt)
        items = list(result.unique().scalars().all())

        return items, total

    async def search(
        self,
        session: AsyncSession,
        query: str,
        *,
        user_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """Search expenses by title and notes using case-insensitive matching.

        Args:
            session: The async database session.
            query: The search query string.
            user_id: Optional filter by user.
            start_date: Optional start of date range.
            end_date: Optional end of date range.
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            Tuple of (matching expenses, total_count).
        """
        search_pattern = f"%{query}%"

        # Build base filter conditions
        conditions = [
            Expense.deleted_at.is_(None),
            or_(
                Expense.title.ilike(search_pattern),
                Expense.notes.ilike(search_pattern),
            ),
        ]

        if user_id is not None:
            conditions.append(Expense.user_id == user_id)
        if start_date is not None:
            conditions.append(Expense.expense_date >= start_date)
        if end_date is not None:
            conditions.append(Expense.expense_date <= end_date)

        # Count
        count_stmt = (
            select(func.count()).select_from(Expense).where(*conditions)
        )
        total = (await session.execute(count_stmt)).scalar_one()

        # Results
        stmt = (
            select(Expense)
            .where(*conditions)
            .options(
                joinedload(Expense.category),
                joinedload(Expense.subcategory),
            )
            .order_by(Expense.expense_date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        items = list(result.unique().scalars().all())

        return items, total

    async def find_by_category(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        *,
        user_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """Find all expenses for a specific category.

        Args:
            session: The async database session.
            category_id: The category UUID to filter by.
            user_id: Optional filter by user.
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            Tuple of (expenses, total_count).
        """
        conditions: list[Any] = [
            Expense.deleted_at.is_(None),
            Expense.category_id == category_id,
        ]
        if user_id is not None:
            conditions.append(Expense.user_id == user_id)

        count_stmt = (
            select(func.count()).select_from(Expense).where(*conditions)
        )
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = (
            select(Expense)
            .where(*conditions)
            .options(joinedload(Expense.category))
            .order_by(Expense.expense_date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        items = list(result.unique().scalars().all())

        return items, total

    # ── Aggregation Queries ──────────────────────────────────

    async def get_summary_by_category(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Aggregate expenses by category within a date range.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: Optional filter by user.

        Returns:
            List of dicts with category_name, total, count, and percentage.
        """
        conditions: list[Any] = [
            Expense.deleted_at.is_(None),
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        ]
        if user_id is not None:
            conditions.append(Expense.user_id == user_id)

        stmt = (
            select(
                Category.name.label("category_name"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            )
            .join(Category, Expense.category_id == Category.id)
            .where(*conditions)
            .group_by(Category.name)
            .order_by(func.sum(Expense.amount).desc())
        )

        result = await session.execute(stmt)
        rows = result.all()

        # Calculate grand total for percentage
        grand_total = sum(row.total for row in rows) if rows else Decimal("0")

        summaries = []
        for row in rows:
            pct = (
                float(row.total / grand_total * 100)
                if grand_total > 0
                else 0.0
            )
            summaries.append({
                "category_name": row.category_name,
                "total": float(row.total),
                "count": row.count,
                "percentage": round(pct, 2),
            })

        return summaries

    async def get_daily_totals(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Get total spending per day within a date range.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: Optional filter by user.

        Returns:
            List of dicts with date, total, and count.
        """
        conditions: list[Any] = [
            Expense.deleted_at.is_(None),
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        ]
        if user_id is not None:
            conditions.append(Expense.user_id == user_id)

        stmt = (
            select(
                Expense.expense_date.label("date"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            )
            .where(*conditions)
            .group_by(Expense.expense_date)
            .order_by(Expense.expense_date.asc())
        )

        result = await session.execute(stmt)
        return [
            {
                "date": str(row.date),
                "total": float(row.total),
                "count": row.count,
            }
            for row in result.all()
        ]

    async def get_monthly_totals(
        self,
        session: AsyncSession,
        months: int = 6,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Get total spending per month for the last N months.

        Used for spending trend analysis.

        Args:
            session: The async database session.
            months: Number of months to look back.
            user_id: Optional filter by user.

        Returns:
            List of dicts with month, total, and count.
        """
        from expense_tracker.utils.datetime_utils import get_past_months_range

        start_date, end_date = get_past_months_range(months)

        conditions: list[Any] = [
            Expense.deleted_at.is_(None),
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        ]
        if user_id is not None:
            conditions.append(Expense.user_id == user_id)

        # Extract year-month for grouping
        year_col = func.extract("year", Expense.expense_date)
        month_col = func.extract("month", Expense.expense_date)

        stmt = (
            select(
                year_col.label("year"),
                month_col.label("month"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            )
            .where(*conditions)
            .group_by(year_col, month_col)
            .order_by(year_col.asc(), month_col.asc())
        )

        result = await session.execute(stmt)
        return [
            {
                "month": f"{int(row.year)}-{int(row.month):02d}",
                "total": float(row.total),
                "count": row.count,
            }
            for row in result.all()
        ]

    async def get_total_for_category_and_period(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        start_date: date,
        end_date: date,
        *,
        user_id: uuid.UUID | None = None,
    ) -> Decimal:
        """Get total spending for a category within a date range.

        Used by BudgetService to compute spent_amount.

        Args:
            session: The async database session.
            category_id: The category to aggregate.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: Optional filter by user.

        Returns:
            Total amount spent, or Decimal("0") if no expenses.
        """
        conditions: list[Any] = [
            Expense.deleted_at.is_(None),
            Expense.category_id == category_id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        ]
        if user_id is not None:
            conditions.append(Expense.user_id == user_id)

        stmt = select(func.coalesce(func.sum(Expense.amount), 0)).where(
            *conditions
        )
        result = await session.execute(stmt)
        return Decimal(str(result.scalar_one()))

    async def get_highest_expenses(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        *,
        user_id: uuid.UUID | None = None,
        limit: int = 10,
    ) -> list[Expense]:
        """Get the highest expenses within a date range.

        Args:
            session: The async database session.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            user_id: Optional filter by user.
            limit: Maximum number of results.

        Returns:
            List of expenses ordered by amount descending.
        """
        conditions: list[Any] = [
            Expense.deleted_at.is_(None),
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        ]
        if user_id is not None:
            conditions.append(Expense.user_id == user_id)

        stmt = (
            select(Expense)
            .where(*conditions)
            .options(joinedload(Expense.category))
            .order_by(Expense.amount.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())
