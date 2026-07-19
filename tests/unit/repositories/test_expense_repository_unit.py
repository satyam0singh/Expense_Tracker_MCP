import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import date

from expense_tracker.repositories.expense_repository import ExpenseRepository
from expense_tracker.database.models.expense import Expense

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_create_expense_unit(mock_session):
    repo = ExpenseRepository()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    user_id = uuid.uuid4()
    category_id = uuid.uuid4()

    expense = await repo.create(
        session=mock_session,
        user_id=user_id,
        title="Coffee",
        amount=Decimal("4.50"),
        currency="USD",
        category_id=category_id,
        payment_method="CASH",
        expense_date=date.today()
    )

    assert expense.title == "Coffee"
    assert expense.amount == Decimal("4.50")
    assert expense.user_id == user_id
    assert mock_session.add.called
    assert mock_session.flush.called
    assert mock_session.refresh.called

@pytest.mark.asyncio
async def test_get_expense_unit(mock_session):
    repo = ExpenseRepository()
    
    mock_result = MagicMock()
    mock_expense = Expense(
        id=uuid.uuid4(),
        title="Coffee",
        amount=Decimal("4.50")
    )
    mock_result.scalar_one_or_none.return_value = mock_expense
    mock_session.execute.return_value = mock_result

    expense_id = mock_expense.id
    user_id = uuid.uuid4()
    
    result = await repo.get_by_id(session=mock_session, entity_id=expense_id)
    
    assert result is not None
    assert result.title == "Coffee"
    assert mock_session.execute.called
