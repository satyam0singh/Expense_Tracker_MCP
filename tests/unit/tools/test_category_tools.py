import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

from expense_tracker.tools.category_tools import register_category_tools

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
@patch('expense_tracker.tools.category_tools.get_session')
@patch('expense_tracker.tools.category_tools.CategoryService')
async def test_list_categories_success(mock_category_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_category = MagicMock()
    mock_category.id = uuid.uuid4()
    mock_category.name = "food"
    mock_category.display_name = "Food"
    mock_category.icon = "burger"
    
    mock_sub = MagicMock()
    mock_sub.id = uuid.uuid4()
    mock_sub.name = "groceries"
    mock_sub.display_name = "Groceries"
    mock_category.subcategories = [mock_sub]
    
    mock_category_service = mock_category_service_class.return_value
    mock_category_service.get_all_categories = AsyncMock(return_value=[mock_category])
    
    register_category_tools(mock_mcp)
    list_categories = mock_mcp.registered_tools['list_categories']
    
    response = await list_categories()
    
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    assert response["data"][0]["name"] == "food"
    assert response["data"][0]["subcategories"][0]["name"] == "groceries"
    mock_category_service.get_all_categories.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.category_tools.get_session')
@patch('expense_tracker.tools.category_tools.CategoryService')
async def test_list_categories_error(mock_category_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_category_service = mock_category_service_class.return_value
    mock_category_service.get_all_categories = AsyncMock(side_effect=Exception("Database error"))
    
    register_category_tools(mock_mcp)
    list_categories = mock_mcp.registered_tools['list_categories']
    
    response = await list_categories()
    
    assert response["status"] == "error"
    assert "Database error" in response["error"]["message"]
