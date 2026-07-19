import pytest
import uuid
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from datetime import date

from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.schemas.expense import ExpenseCreate
from expense_tracker.core.constants import Currency
from expense_tracker.database.models.expense import Expense

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
@patch('expense_tracker.services.expense_service.ExpenseRepository')
@patch('expense_tracker.services.expense_service.BudgetService')
@patch('expense_tracker.services.expense_service.CategoryService')
async def test_create_expense_service_unit(mock_category_service, mock_budget_service, mock_expense_repo_class, mock_session):
    # Setup mocks
    mock_category_instance = mock_category_service.return_value
    mock_category_instance.resolve_category_id = AsyncMock(return_value=uuid.uuid4())
    mock_category_instance.resolve_subcategory_id = AsyncMock(return_value=None)
    
    mock_budget_instance = mock_budget_service.return_value
    mock_budget_instance.sync_budget_spending = AsyncMock(return_value=None)
    
    mock_repo = mock_expense_repo_class.return_value
    
    expense_service = ExpenseService(
        repo=mock_repo,
        category_service=mock_category_instance,
        budget_service=mock_budget_instance
    )
    
    # Mock _audit to prevent coroutine warnings
    expense_service._audit = AsyncMock(return_value=None)
    
    mock_expense = Expense(
        id=uuid.uuid4(),
        title="Lunch",
        amount=Decimal("15.00"),
        currency=Currency.USD.value
    )
    mock_repo.create = AsyncMock(return_value=mock_expense)

    user_id = uuid.uuid4()
    category_id = uuid.uuid4()
    
    expense_data = ExpenseCreate(
        title="Lunch",
        amount=Decimal("15.00"),
        currency=Currency.USD,
        category_id=category_id,
        expense_date=date.today()
    )

    result = await expense_service.create_expense(
        session=mock_session,
        user_id=user_id,
        data=expense_data
    )

    assert result.title == "Lunch"
    assert result.amount == Decimal("15.00")
    assert mock_repo.create.called
