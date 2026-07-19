import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date

from expense_tracker.tools.analytics_tools import register_analytics_tools
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
@patch('expense_tracker.tools.analytics_tools.get_session')
@patch('expense_tracker.tools.analytics_tools.AnalyticsService')
async def test_analyze_spending_success(mock_analytics_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_analytics_service = mock_analytics_service_class.return_value
    mock_analytics_service.get_spending_summary = AsyncMock(return_value={"total": 1000.0})
    
    register_analytics_tools(mock_mcp)
    analyze_spending = mock_mcp.registered_tools['analyze_spending']
    
    response = await analyze_spending(month="2026-07")
    
    assert response["status"] == "success"
    assert response["data"]["total"] == 1000.0
    mock_analytics_service.get_spending_summary.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.analytics_tools.get_session')
@patch('expense_tracker.tools.analytics_tools.AnalyticsService')
async def test_analyze_spending_error(mock_analytics_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_analytics_service = mock_analytics_service_class.return_value
    mock_analytics_service.get_spending_summary = AsyncMock(side_effect=ValidationError("Invalid"))
    
    register_analytics_tools(mock_mcp)
    analyze_spending = mock_mcp.registered_tools['analyze_spending']
    
    response = await analyze_spending(month="2026-07")
    
    assert response["status"] == "error"
    assert "Invalid" in response["error"]["message"]

@pytest.mark.asyncio
@patch('expense_tracker.tools.analytics_tools.get_session')
@patch('expense_tracker.tools.analytics_tools.AnalyticsService')
async def test_get_category_breakdown_success(mock_analytics_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_analytics_service = mock_analytics_service_class.return_value
    mock_analytics_service.get_category_breakdown = AsyncMock(return_value=[{"category": "Food", "amount": 500.0}])
    
    register_analytics_tools(mock_mcp)
    get_category_breakdown = mock_mcp.registered_tools['get_category_breakdown']
    
    response = await get_category_breakdown(month="2026-07")
    
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    mock_analytics_service.get_category_breakdown.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.analytics_tools.get_session')
@patch('expense_tracker.tools.analytics_tools.AnalyticsService')
async def test_get_category_breakdown_internal_error(mock_analytics_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_analytics_service = mock_analytics_service_class.return_value
    mock_analytics_service.get_category_breakdown = AsyncMock(side_effect=Exception("Database down"))
    
    register_analytics_tools(mock_mcp)
    get_category_breakdown = mock_mcp.registered_tools['get_category_breakdown']
    
    response = await get_category_breakdown(month="2026-07")
    
    assert response["status"] == "error"
    assert "Database down" in response["error"]["message"]

@pytest.mark.asyncio
@patch('expense_tracker.tools.analytics_tools.get_session')
@patch('expense_tracker.tools.analytics_tools.AnalyticsService')
async def test_get_spending_trends_success(mock_analytics_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_analytics_service = mock_analytics_service_class.return_value
    mock_analytics_service.get_spending_trends = AsyncMock(return_value=[{"month": "2026-07", "total": 1000.0}])
    
    register_analytics_tools(mock_mcp)
    get_spending_trends = mock_mcp.registered_tools['get_spending_trends']
    
    response = await get_spending_trends(months=6)
    
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    mock_analytics_service.get_spending_trends.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.analytics_tools.get_session')
@patch('expense_tracker.tools.analytics_tools.AnalyticsService')
async def test_get_spending_trends_error(mock_analytics_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_analytics_service = mock_analytics_service_class.return_value
    mock_analytics_service.get_spending_trends = AsyncMock(side_effect=ValidationError("Invalid"))
    
    register_analytics_tools(mock_mcp)
    get_spending_trends = mock_mcp.registered_tools['get_spending_trends']
    
    response = await get_spending_trends(months=6)
    
    assert response["status"] == "error"
    assert "Invalid" in response["error"]["message"]
