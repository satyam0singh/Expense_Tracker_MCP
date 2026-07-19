"""Expense Service.

Handles business logic for expenses. Orchestrates cross-entity
updates such as syncing budgets when expenses are modified.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.constants import AuditAction
from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.expense import Expense
from expense_tracker.repositories.expense_repository import ExpenseRepository
from expense_tracker.schemas.expense import ExpenseCreate, ExpenseUpdate
from expense_tracker.services.base import BaseService
from expense_tracker.services.budget_service import BudgetService
from expense_tracker.services.category_service import CategoryService

logger = get_logger(__name__)


class ExpenseService(BaseService):
    """Service for managing expenses.

    Responsible for creating, updating, and deleting expenses, and
    triggering budget synchronizations.
    """

    def __init__(
        self,
        repo: ExpenseRepository | None = None,
        category_service: CategoryService | None = None,
        budget_service: BudgetService | None = None,
    ) -> None:
        """Initialize the expense service.

        Args:
            repo: Optional ExpenseRepository.
            category_service: Optional CategoryService.
            budget_service: Optional BudgetService.
        """
        super().__init__()
        self.repo = repo or ExpenseRepository()
        self.category_service = category_service or CategoryService()
        self.budget_service = budget_service or BudgetService()

    async def create_expense(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        data: ExpenseCreate,
    ) -> Expense:
        """Create a new expense and trigger budget sync.

        Args:
            session: The async database session.
            user_id: The UUID of the user.
            data: Expense creation data.

        Returns:
            The created Expense.
        """
        # 1. Resolve category and subcategory
        category_id = await self.category_service.resolve_category_id(
            session,
            category_id=data.category_id,
            category_name=data.category_name,
        )

        subcategory_id = await self.category_service.resolve_subcategory_id(
            session,
            category_id=category_id,
            subcategory_id=data.subcategory_id,
            subcategory_name=data.subcategory_name,
        )

        # 2. Prepare data
        expense_data = data.model_dump(
            exclude={"category_name", "subcategory_name"}
        )
        expense_data.update({
            "user_id": user_id,
            "category_id": category_id,
            "subcategory_id": subcategory_id,
            "currency": data.currency.value,
            "payment_method": data.payment_method.value,
        })

        # 3. Create expense
        expense = await self.repo.create(session, **expense_data)

        # 4. Audit
        await self._audit(
            session=session,
            entity_type="Expense",
            entity_id=expense.id,
            action=AuditAction.CREATE,
            changes={
                "title": expense.title,
                "amount": float(expense.amount),
                "category_id": str(category_id),
            },
            user_id=user_id,
        )

        # 5. Sync budget
        await self.budget_service.sync_budget_spending(
            session=session,
            user_id=user_id,
            category_id=category_id,
            expense_date=expense.expense_date,
        )

        return expense

    async def update_expense(
        self,
        session: AsyncSession,
        expense_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ExpenseUpdate,
    ) -> Expense:
        """Update an existing expense and trigger budget sync.

        Args:
            session: The async database session.
            expense_id: The expense UUID.
            user_id: The UUID of the user.
            data: Expense update data.

        Returns:
            The updated Expense.
        """
        # 1. Verify existence
        expense = await self.repo.get_by_id_or_raise(session, expense_id)

        # Store old values for budget sync and audit
        old_category_id = expense.category_id
        old_date = expense.expense_date
        
        # 2. Extract updates
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return expense

        # Map enum values
        if "currency" in update_data:
            update_data["currency"] = update_data["currency"].value
        if "payment_method" in update_data:
            update_data["payment_method"] = update_data["payment_method"].value

        # Capture before state for audit
        before_state = {k: getattr(expense, k) for k in update_data.keys()}
        for k, v in before_state.items():
            if hasattr(v, 'as_tuple'):  # Decimal check
                before_state[k] = float(v)
            elif isinstance(v, date):
                before_state[k] = v.isoformat()
            elif isinstance(v, uuid.UUID):
                before_state[k] = str(v)

        # 3. Update
        updated_expense = await self.repo.update(session, expense_id, **update_data)

        # 4. Audit
        after_state = {k: getattr(updated_expense, k) for k in update_data.keys()}
        for k, v in after_state.items():
            if hasattr(v, 'as_tuple'):
                after_state[k] = float(v)
            elif isinstance(v, date):
                after_state[k] = v.isoformat()
            elif isinstance(v, uuid.UUID):
                after_state[k] = str(v)

        await self._audit(
            session=session,
            entity_type="Expense",
            entity_id=expense_id,
            action=AuditAction.UPDATE,
            changes={"before": before_state, "after": after_state},
            user_id=user_id,
        )

        # 5. Sync budget(s)
        # If category or date changed, we might need to sync two different budgets
        sync_required = (
            "amount" in update_data
            or "category_id" in update_data
            or "expense_date" in update_data
            or "deleted_at" in update_data
        )
        
        if sync_required:
            # Sync the new category/month
            await self.budget_service.sync_budget_spending(
                session=session,
                user_id=user_id,
                category_id=updated_expense.category_id,
                expense_date=updated_expense.expense_date,
            )
            
            # If category or month changed, also sync the old budget
            month_changed = old_date.year != updated_expense.expense_date.year or old_date.month != updated_expense.expense_date.month
            category_changed = old_category_id != updated_expense.category_id
            
            if category_changed or month_changed:
                await self.budget_service.sync_budget_spending(
                    session=session,
                    user_id=user_id,
                    category_id=old_category_id,
                    expense_date=old_date,
                )

        return updated_expense

    async def delete_expense(
        self,
        session: AsyncSession,
        expense_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Soft-delete an expense and trigger budget sync.

        Args:
            session: The async database session.
            expense_id: The expense UUID.
            user_id: The UUID of the user.

        Returns:
            True if deleted successfully.
        """
        # We fetch it first to get the category and date for budget sync
        expense = await self.repo.get_by_id_or_raise(session, expense_id)
        
        # Soft delete
        await self.repo.soft_delete(session, expense_id)
        
        # Audit
        await self._audit(
            session=session,
            entity_type="Expense",
            entity_id=expense_id,
            action=AuditAction.DELETE,
            user_id=user_id,
        )
        
        # Sync budget
        await self.budget_service.sync_budget_spending(
            session=session,
            user_id=user_id,
            category_id=expense.category_id,
            expense_date=expense.expense_date,
        )
        
        return True

    # ── Search & Analytics ───────────────────────────────────
    
    async def get_expenses(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        user_id: uuid.UUID,
        category_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """Get expenses within a date range."""
        return await self.repo.find_by_date_range(
            session=session,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            category_id=category_id,
            offset=offset,
            limit=limit,
        )

    async def search_expenses(
        self,
        session: AsyncSession,
        query: str,
        user_id: uuid.UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """Search expenses by title or notes."""
        return await self.repo.search(
            session=session,
            query=query,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=limit,
        )
