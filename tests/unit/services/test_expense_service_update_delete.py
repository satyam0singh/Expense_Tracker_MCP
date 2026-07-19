import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import date

from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.schemas.expense import ExpenseCreate, ExpenseUpdate
from expense_tracker.core.constants import Currency
from expense_tracker.database.models.expense import Expense

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
@patch('expense_tracker.services.expense_service.ExpenseRepository')
@patch('expense_tracker.services.expense_service.BudgetService')
@patch('expense_tracker.services.expense_service.CategoryService')
async def test_update_expense_service_unit(mock_category_service, mock_budget_service, mock_expense_repo_class, mock_session):
    mock_category_instance = mock_category_service.return_value
    mock_budget_instance = mock_budget_service.return_value
    mock_budget_instance.sync_budget_spending = AsyncMock(return_value=None)
    
    mock_repo = mock_expense_repo_class.return_value
    
    expense_service = ExpenseService(
        repo=mock_repo,
        category_service=mock_category_instance,
        budget_service=mock_budget_instance
    )
    
    expense_service._audit = AsyncMock(return_value=None)
    
    expense_id = uuid.uuid4()
    user_id = uuid.uuid4()
    old_category_id = uuid.uuid4()
    new_category_id = uuid.uuid4()
    
    mock_expense = Expense(
        id=expense_id,
        title="Old Lunch",
        amount=Decimal("10.00"),
        currency=Currency.USD.value,
        category_id=old_category_id,
        expense_date=date(2023, 5, 1)
    )
    
    mock_updated_expense = Expense(
        id=expense_id,
        title="New Lunch",
        amount=Decimal("20.00"),
        currency=Currency.USD.value,
        category_id=new_category_id,
        expense_date=date(2023, 6, 1)
    )
    
    mock_repo.get_by_id_or_raise = AsyncMock(return_value=mock_expense)
    mock_repo.update = AsyncMock(return_value=mock_updated_expense)
    
    update_data = ExpenseUpdate(
        title="New Lunch",
        amount=Decimal("20.00"),
        category_id=new_category_id,
        expense_date=date(2023, 6, 1)
    )
    
    result = await expense_service.update_expense(
        session=mock_session,
        expense_id=expense_id,
        user_id=user_id,
        data=update_data
    )
    
    assert result.title == "New Lunch"
    assert result.amount == Decimal("20.00")
    
    # Check if budget was synced twice (because category and month changed)
    assert mock_budget_instance.sync_budget_spending.call_count == 2
    mock_repo.update.assert_called_once()
    expense_service._audit.assert_called_once()


@pytest.mark.asyncio
@patch('expense_tracker.services.expense_service.ExpenseRepository')
@patch('expense_tracker.services.expense_service.BudgetService')
@patch('expense_tracker.services.expense_service.CategoryService')
async def test_delete_expense_service_unit(mock_category_service, mock_budget_service, mock_expense_repo_class, mock_session):
    mock_category_instance = mock_category_service.return_value
    mock_budget_instance = mock_budget_service.return_value
    mock_budget_instance.sync_budget_spending = AsyncMock(return_value=None)
    
    mock_repo = mock_expense_repo_class.return_value
    
    expense_service = ExpenseService(
        repo=mock_repo,
        category_service=mock_category_instance,
        budget_service=mock_budget_instance
    )
    
    expense_service._audit = AsyncMock(return_value=None)
    
    expense_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    mock_expense = Expense(
        id=expense_id,
        title="Old Lunch",
        amount=Decimal("10.00"),
        currency=Currency.USD.value,
        category_id=uuid.uuid4(),
        expense_date=date(2023, 5, 1)
    )
    
    mock_repo.get_by_id_or_raise = AsyncMock(return_value=mock_expense)
    mock_repo.soft_delete = AsyncMock(return_value=True)
    
    await expense_service.delete_expense(
        session=mock_session,
        expense_id=expense_id,
        user_id=user_id
    )
    
    mock_repo.soft_delete.assert_called_once_with(mock_session, expense_id)
    expense_service._audit.assert_called_once()
