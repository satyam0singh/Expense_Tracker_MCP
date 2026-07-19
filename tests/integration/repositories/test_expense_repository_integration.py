import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.repositories.expense_repository import ExpenseRepository
from expense_tracker.database.models.expense import Expense
from expense_tracker.core.constants import Currency
from expense_tracker.database.models.category import Category
from tests.conftest import SYSTEM_USER_ID

@pytest.fixture
def expense_repo():
    return ExpenseRepository()

@pytest.mark.asyncio
async def test_expense_repo_create_and_read(session: AsyncSession, expense_repo: ExpenseRepository):
    # 1. Fetch a category (seeded in conftest)
    from sqlalchemy import select
    result = await session.execute(select(Category).where(Category.name == "food"))
    category = result.scalar_one_or_none()
    assert category is not None

    # 2. Create an expense
    expense = await expense_repo.create(
        session,
        user_id=SYSTEM_USER_ID,
        title="Integration Test Lunch",
        amount=Decimal("25.50"),
        currency=Currency.USD.value,
        category_id=category.id,
        expense_date=date.today(),
        payment_method="cash"
    )

    assert expense.id is not None
    
    # 3. Read it back
    fetched = await expense_repo.get_by_id(session, entity_id=expense.id)
    assert fetched is not None
    assert fetched.title == "Integration Test Lunch"
    assert fetched.amount == Decimal("25.50")

@pytest.mark.asyncio
async def test_expense_repo_find_by_date_range(session: AsyncSession, expense_repo: ExpenseRepository):
    # 1. Fetch category
    from sqlalchemy import select
    result = await session.execute(select(Category).where(Category.name == "food"))
    category = result.scalar_one_or_none()

    # 2. Create expenses in different dates
    await expense_repo.create(
        session,
        user_id=SYSTEM_USER_ID,
        title="Old Expense",
        amount=Decimal("10.00"),
        currency=Currency.USD.value,
        category_id=category.id,
        expense_date=date(2023, 1, 1),
        payment_method="cash"
    )
    
    await expense_repo.create(
        session,
        user_id=SYSTEM_USER_ID,
        title="New Expense",
        amount=Decimal("20.00"),
        currency=Currency.USD.value,
        category_id=category.id,
        expense_date=date(2023, 2, 1),
        payment_method="cash"
    )
    
    # 3. Find by date range
    expenses, count = await expense_repo.find_by_date_range(
        session,
        start_date=date(2023, 1, 15),
        end_date=date(2023, 2, 15),
        user_id=SYSTEM_USER_ID
    )
    
    assert count == 1
    assert expenses[0].title == "New Expense"
