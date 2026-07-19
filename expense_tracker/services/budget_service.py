"""Budget Service.

Handles business logic for budgets, including budget creation,
updating, and computing real-time status.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.constants import AuditAction
from expense_tracker.core.exceptions import DuplicateError
from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.budget import Budget
from expense_tracker.repositories.budget_repository import BudgetRepository
from expense_tracker.repositories.expense_repository import ExpenseRepository
from expense_tracker.schemas.budget import BudgetCreate, BudgetUpdate
from expense_tracker.services.base import BaseService
from expense_tracker.services.category_service import CategoryService
from expense_tracker.utils.datetime_utils import get_month_range

logger = get_logger(__name__)


class BudgetService(BaseService):
    """Service for managing monthly budgets."""

    def __init__(
        self,
        budget_repo: BudgetRepository | None = None,
        expense_repo: ExpenseRepository | None = None,
        category_service: CategoryService | None = None,
    ) -> None:
        """Initialize the budget service.

        Args:
            budget_repo: Optional BudgetRepository.
            expense_repo: Optional ExpenseRepository.
            category_service: Optional CategoryService.
        """
        super().__init__()
        self.repo = budget_repo or BudgetRepository()
        self.expense_repo = expense_repo or ExpenseRepository()
        self.category_service = category_service or CategoryService()

    async def create_budget(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        data: BudgetCreate,
    ) -> Budget:
        """Create a new budget for a category and month.

        Automatically calculates spent_amount based on existing expenses.

        Args:
            session: The async database session.
            user_id: The UUID of the user.
            data: Budget creation data.

        Returns:
            The created Budget.

        Raises:
            DuplicateError: If a budget for this category and month already exists.
        """
        # 1. Resolve category
        category_id = await self.category_service.resolve_category_id(
            session,
            category_id=data.category_id,
            category_name=data.category_name,
        )

        # month is guaranteed to be a date object (1st of the month) by Pydantic
        month: date = data.month  # type: ignore[assignment]

        # 2. Check for duplicates
        exists = await self.repo.exists_for_category_and_month(
            session,
            category_id=category_id,
            month=month,
            user_id=user_id,
        )
        if exists:
            msg = f"Budget for category {category_id} in {month.isoformat()} already exists."
            raise DuplicateError(msg)

        # 3. Calculate initial spent_amount from existing expenses
        start_date, end_date = get_month_range(month.year, month.month)
        spent_amount = await self.expense_repo.get_total_for_category_and_period(
            session,
            category_id=category_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
        )

        # 4. Create budget
        budget = await self.repo.create(
            session,
            user_id=user_id,
            category_id=category_id,
            month=month,
            budget_amount=data.budget_amount,
            spent_amount=spent_amount,
            currency=data.currency.value,
        )

        # 5. Audit
        await self._audit(
            session=session,
            entity_type="Budget",
            entity_id=budget.id,
            action=AuditAction.CREATE,
            changes={
                "budget_amount": float(budget.budget_amount),
                "category_id": str(category_id),
                "month": month.isoformat(),
            },
            user_id=user_id,
        )

        return budget

    async def update_budget(
        self,
        session: AsyncSession,
        budget_id: uuid.UUID,
        user_id: uuid.UUID,
        data: BudgetUpdate,
    ) -> Budget:
        """Update an existing budget.

        Args:
            session: The async database session.
            budget_id: The budget UUID.
            user_id: The UUID of the user.
            data: Budget update data.

        Returns:
            The updated Budget.
        """
        # 1. Verify existence
        budget = await self.repo.get_by_id_or_raise(session, budget_id)

        # 2. Extract updates
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return budget

        # Capture before state for audit
        before_state = {"budget_amount": float(budget.budget_amount)}

        # 3. Update
        updated_budget = await self.repo.update(session, budget_id, **update_data)

        # 4. Audit
        after_state = {"budget_amount": float(updated_budget.budget_amount)}
        await self._audit(
            session=session,
            entity_type="Budget",
            entity_id=budget_id,
            action=AuditAction.UPDATE,
            changes={"before": before_state, "after": after_state},
            user_id=user_id,
        )

        return updated_budget

    async def get_budgets_for_month(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        month: date,
    ) -> list[dict[str, Any]]:
        """Get all budgets for a month with computed status.

        Args:
            session: The async database session.
            user_id: The UUID of the user.
            month: The first day of the target month.

        Returns:
            List of dicts with budget data and status indicators.
        """
        # Ensure it's the 1st of the month
        target_month = date(month.year, month.month, 1)
        return await self.repo.get_budgets_with_status(
            session, month=target_month, user_id=user_id
        )

    async def sync_budget_spending(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        expense_date: date,
    ) -> None:
        """Recompute the spent_amount for a budget.

        Called by ExpenseService when an expense is added, edited, or deleted.

        Args:
            session: The async database session.
            user_id: The UUID of the user.
            category_id: The category UUID.
            expense_date: The date of the expense (determines which month's budget to update).
        """
        # 1. Find the target month (1st of the month)
        month = date(expense_date.year, expense_date.month, 1)

        # 2. Get the budget
        budget = await self.repo.get_by_category_and_month(
            session,
            category_id=category_id,
            month=month,
            user_id=user_id,
        )

        if not budget:
            # No budget exists for this category/month. Nothing to sync.
            return

        # 3. Calculate actual total spent in this month for this category
        start_date, end_date = get_month_range(month.year, month.month)
        new_spent_amount = await self.expense_repo.get_total_for_category_and_period(
            session,
            category_id=category_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
        )

        # 4. Update if changed
        if budget.spent_amount != new_spent_amount:
            old_spent = budget.spent_amount
            await self.repo.update_spent_amount(session, budget.id, new_spent_amount)

            # We don't typically audit automatic system updates to reduce noise,
            # but we'll log it at debug level.
            logger.debug(
                "budget_sync_completed",
                budget_id=str(budget.id),
                old_spent=float(old_spent),
                new_spent=float(new_spent_amount),
            )
