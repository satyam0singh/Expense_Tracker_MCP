import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import date

from expense_tracker.tools.budget_tools import register_budget_tools, SYSTEM_USER_ID
from expense_tracker.core.exceptions import ValidationError

@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    # Mock the tool decorator to just return the function and save it
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
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_set_budget_success(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_budget = MagicMock()
    mock_budget.id = uuid.uuid4()
    mock_budget.budget_amount = Decimal("1000.00")
    mock_budget.currency = "USD"
    
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.create_budget = AsyncMock(return_value=mock_budget)
    
    register_budget_tools(mock_mcp)
    set_budget = mock_mcp.registered_tools['set_budget']
    
    response = await set_budget(category_name="food", amount=1000.0, month="2026-07", currency="USD")
    
    assert response["status"] == "success"
    assert "budget_id" in response["data"]
    mock_budget_service.create_budget.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_set_budget_error(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.create_budget = AsyncMock(side_effect=ValidationError("Invalid amount"))
    
    register_budget_tools(mock_mcp)
    set_budget = mock_mcp.registered_tools['set_budget']
    
    response = await set_budget(category_name="food", amount=100.0, month="2026-07")
    
    assert response["status"] == "error"
    assert "Invalid amount" in response["error"]["message"]

@pytest.mark.asyncio
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_set_budget_internal_error(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.create_budget = AsyncMock(side_effect=Exception("Database down"))
    
    register_budget_tools(mock_mcp)
    set_budget = mock_mcp.registered_tools['set_budget']
    
    response = await set_budget(category_name="food", amount=100.0)
    
    assert response["status"] == "error"
    assert "Database down" in response["error"]["message"]


@pytest.mark.asyncio
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_update_budget_success(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_budget = MagicMock()
    mock_budget.id = uuid.uuid4()
    mock_budget.budget_amount = Decimal("1500.00")
    mock_budget.currency = "USD"
    
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.update_budget = AsyncMock(return_value=mock_budget)
    
    register_budget_tools(mock_mcp)
    update_budget = mock_mcp.registered_tools['update_budget']
    
    response = await update_budget(budget_id=str(mock_budget.id), amount=1500.0)
    
    assert response["status"] == "success"
    mock_budget_service.update_budget.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_update_budget_error(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.update_budget = AsyncMock(side_effect=ValidationError("Invalid"))
    
    register_budget_tools(mock_mcp)
    update_budget = mock_mcp.registered_tools['update_budget']
    
    response = await update_budget(budget_id=str(uuid.uuid4()), amount=1500.0)
    assert response["status"] == "error"

@pytest.mark.asyncio
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_update_budget_internal_error(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.update_budget = AsyncMock(side_effect=Exception("Database down"))
    
    register_budget_tools(mock_mcp)
    update_budget = mock_mcp.registered_tools['update_budget']
    
    response = await update_budget(budget_id=str(uuid.uuid4()), amount=1500.0)
    assert response["status"] == "error"

@pytest.mark.asyncio
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_get_budget_status_success(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.get_budgets_for_month = AsyncMock(return_value=[{"budget_id": "123"}])
    
    register_budget_tools(mock_mcp)
    get_budget_status = mock_mcp.registered_tools['get_budget_status']
    
    response = await get_budget_status(month="2026-07")
    
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    mock_budget_service.get_budgets_for_month.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_get_budget_status_error(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.get_budgets_for_month = AsyncMock(side_effect=ValidationError("Invalid"))
    
    register_budget_tools(mock_mcp)
    get_budget_status = mock_mcp.registered_tools['get_budget_status']
    
    response = await get_budget_status()
    assert response["status"] == "error"

@pytest.mark.asyncio
@patch('expense_tracker.tools.budget_tools.get_session')
@patch('expense_tracker.tools.budget_tools.BudgetService')
async def test_get_budget_status_internal_error(mock_budget_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_budget_service = mock_budget_service_class.return_value
    mock_budget_service.get_budgets_for_month = AsyncMock(side_effect=Exception("Database down"))
    
    register_budget_tools(mock_mcp)
    get_budget_status = mock_mcp.registered_tools['get_budget_status']
    
    response = await get_budget_status()
    assert response["status"] == "error"
