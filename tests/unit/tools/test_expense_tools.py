import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import date

from expense_tracker.tools.expense_tools import register_expense_tools, SYSTEM_USER_ID
from expense_tracker.core.exceptions import ValidationError

@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    tools = {}
    def tool_decorator():
        def wrapper(func):
            tools[func.__name__] = func
            return func
        return wrapper
    mcp.tool = tool_decorator
    mcp.registered_tools = tools
    return mcp

@pytest.fixture
def mock_session_cm():
    session = AsyncMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm

@pytest.mark.asyncio
@patch('expense_tracker.tools.expense_tools.get_session')
@patch('expense_tracker.tools.expense_tools.ExpenseService')
async def test_add_expense_success(mock_expense_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_expense = MagicMock()
    mock_expense.id = uuid.uuid4()
    mock_expense.title = "Lunch"
    mock_expense.amount = Decimal("20.00")
    mock_expense.currency = "USD"
    
    mock_expense_service = mock_expense_service_class.return_value
    mock_expense_service.create_expense = AsyncMock(return_value=mock_expense)
    
    register_expense_tools(mock_mcp)
    add_expense = mock_mcp.registered_tools['add_expense']
    
    response = await add_expense(
        title="Lunch",
        amount=20.00,
        category_name="Food",
        currency="USD"
    )
    
    assert response["status"] == "success"
    assert "expense_id" in response["data"]
    mock_expense_service.create_expense.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.expense_tools.get_session')
@patch('expense_tracker.tools.expense_tools.ExpenseService')
async def test_add_expense_error(mock_expense_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_expense_service = mock_expense_service_class.return_value
    mock_expense_service.create_expense = AsyncMock(side_effect=ValidationError("Invalid"))
    
    register_expense_tools(mock_mcp)
    add_expense = mock_mcp.registered_tools['add_expense']
    
    response = await add_expense(title="Lunch", amount=20.0, category_name="Food")
    assert response["status"] == "error"

@pytest.mark.asyncio
@patch('expense_tracker.tools.expense_tools.get_session')
@patch('expense_tracker.tools.expense_tools.ExpenseService')
async def test_update_expense_success(mock_expense_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_expense = MagicMock()
    mock_expense.id = uuid.uuid4()
    
    mock_expense_service = mock_expense_service_class.return_value
    mock_expense_service.update_expense = AsyncMock(return_value=mock_expense)
    
    # Mock category service since it is accessed for resolving category name
    mock_cat_service = MagicMock()
    mock_cat_service.resolve_category_id = AsyncMock(return_value=uuid.uuid4())
    mock_expense_service.category_service = mock_cat_service
    
    register_expense_tools(mock_mcp)
    update_expense = mock_mcp.registered_tools['update_expense']
    
    response = await update_expense(
        expense_id=str(mock_expense.id),
        title="Dinner",
        category_name="Dining"
    )
    
    assert response["status"] == "success"
    mock_cat_service.resolve_category_id.assert_called_once()
    mock_expense_service.update_expense.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.expense_tools.get_session')
@patch('expense_tracker.tools.expense_tools.ExpenseService')
async def test_delete_expense_success(mock_expense_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_expense_service = mock_expense_service_class.return_value
    mock_expense_service.delete_expense = AsyncMock(return_value=True)
    
    register_expense_tools(mock_mcp)
    delete_expense = mock_mcp.registered_tools['delete_expense']
    
    response = await delete_expense(expense_id=str(uuid.uuid4()))
    
    assert response["status"] == "success"
    mock_expense_service.delete_expense.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.expense_tools.get_session')
@patch('expense_tracker.tools.expense_tools.ExpenseService')
async def test_search_expenses_success(mock_expense_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_item = MagicMock()
    mock_item.id = uuid.uuid4()
    mock_item.expense_date = date.today()
    mock_item.title = "Coffee"
    mock_item.amount = Decimal("5.00")
    mock_item.category.name = "Food"
    
    mock_expense_service = mock_expense_service_class.return_value
    mock_expense_service.search_expenses = AsyncMock(return_value=([mock_item], 1))
    
    register_expense_tools(mock_mcp)
    search_expenses = mock_mcp.registered_tools['search_expenses']
    
    response = await search_expenses(query="coffee")
    
    assert response["status"] == "success"
    assert response["data"]["total"] == 1
    assert response["data"]["items"][0]["title"] == "Coffee"
