import pytest
import asyncio
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from expense_tracker.database.models.expense import Expense
from expense_tracker.core.constants import Currency
from tests.database.conftest import SYSTEM_USER_ID

@pytest.mark.asyncio
@pytest.mark.postgres
async def test_postgres_transaction_rollback(postgres_engine, postgres_session: AsyncSession):
    """Test that failed transactions are rolled back properly."""
    
    # 1. Start a transaction manually (using a raw session to simulate failure)
    AsyncSessionLocal = sessionmaker(postgres_engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Get a valid category
                from expense_tracker.database.models.category import Category
                result = await session.execute(select(Category).where(Category.name == "food"))
                category = result.scalar_one_or_none()
                
                # Insert a valid expense
                expense_id = uuid.uuid4()
                expense = Expense(
                    id=expense_id,
                    user_id=SYSTEM_USER_ID,
                    title="Will Rollback",
                    amount=Decimal("50.00"),
                    currency=Currency.USD.value,
                    category_id=category.id,
                    expense_date=date.today(),
                    payment_method="cash"
                )
                session.add(expense)
                
                # Force an error (inserting duplicate ID)
                duplicate_expense = Expense(
                    id=expense_id,
                    user_id=SYSTEM_USER_ID,
                    title="Duplicate",
                    amount=Decimal("10.00"),
                    currency=Currency.USD.value,
                    category_id=category.id,
                    expense_date=date.today(),
                    payment_method="cash"
                )
                session.add(duplicate_expense)
                
                # Commit should fail
                await session.flush()
    except Exception:
        # Expected to fail due to IntegrityError
        pass
        
    # Verify the rollback occurred and nothing was saved
    async with AsyncSessionLocal() as check_session:
        result = await check_session.execute(select(Expense).where(Expense.title == "Will Rollback"))
        saved_expense = result.scalar_one_or_none()
        assert saved_expense is None
