"""Integration tests for services."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.schemas.budget import BudgetCreate
from expense_tracker.schemas.expense import ExpenseCreate
from expense_tracker.services.budget_service import BudgetService
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.services.category_service import CategoryService
from expense_tracker.core.constants import Currency

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_expense_budget_sync(session: AsyncSession):
    """Test that creating an expense automatically updates the budget."""
    expense_service = ExpenseService()
    budget_service = BudgetService()
    category_service = CategoryService()

    # 1. Resolve category
    food_cat_id = await category_service.resolve_category_id(
        session, category_name="food"
    )

    # 2. Create budget
    budget_data = BudgetCreate(
        category_id=food_cat_id,
        budget_amount=Decimal("500.00"),
        month=date.today(),
        currency=Currency.USD,
    )
    budget = await budget_service.create_budget(session, SYSTEM_USER_ID, budget_data)
    
    assert budget.spent_amount == Decimal("0.00")

    # 3. Create expense
    expense_data = ExpenseCreate(
        title="Lunch",
        amount=Decimal("25.50"),
        category_id=food_cat_id,
        currency=Currency.USD,
        expense_date=date.today(),
    )
    expense = await expense_service.create_expense(session, SYSTEM_USER_ID, expense_data)
    
    assert expense.amount == Decimal("25.50")

    # 4. Verify budget was synced
    await session.refresh(budget)
    assert budget.spent_amount == Decimal("25.50")

    # 5. Delete expense and verify sync
    await expense_service.delete_expense(session, expense.id, SYSTEM_USER_ID)
    await session.refresh(budget)
    assert budget.spent_amount == Decimal("0.00")
