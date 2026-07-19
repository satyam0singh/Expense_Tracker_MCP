import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal

from expense_tracker.tools.credit_card_tools import register_credit_card_tools
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
@patch('expense_tracker.tools.credit_card_tools.get_session')
@patch('expense_tracker.tools.credit_card_tools.CreditCardService')
async def test_add_credit_card_success(mock_card_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_card = MagicMock()
    mock_card.id = uuid.uuid4()
    mock_card.card_name = "HDFC Regalia"
    
    mock_card_service = mock_card_service_class.return_value
    mock_card_service.create_card = AsyncMock(return_value=mock_card)
    
    register_credit_card_tools(mock_mcp)
    add_credit_card = mock_mcp.registered_tools['add_credit_card']
    
    response = await add_credit_card(card_name="HDFC Regalia", last_four="1234", limit=50000.0)
    
    assert response["status"] == "success"
    assert "card_id" in response["data"]
    mock_card_service.create_card.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.credit_card_tools.get_session')
@patch('expense_tracker.tools.credit_card_tools.CreditCardService')
async def test_add_credit_card_error(mock_card_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_card_service = mock_card_service_class.return_value
    mock_card_service.create_card = AsyncMock(side_effect=ValidationError("Invalid"))
    
    register_credit_card_tools(mock_mcp)
    add_credit_card = mock_mcp.registered_tools['add_credit_card']
    
    response = await add_credit_card(card_name="HDFC Regalia", last_four="1234", limit=100.0)
    assert response["status"] == "error"

@pytest.mark.asyncio
@patch('expense_tracker.tools.credit_card_tools.get_session')
@patch('expense_tracker.tools.credit_card_tools.CreditCardService')
async def test_record_card_payment_success(mock_card_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_card = MagicMock()
    mock_card.available_limit = Decimal("50000.00")
    
    mock_card_service = mock_card_service_class.return_value
    mock_card_service.update_usage = AsyncMock(return_value=mock_card)
    
    register_credit_card_tools(mock_mcp)
    record_card_payment = mock_mcp.registered_tools['record_card_payment']
    
    response = await record_card_payment(card_id=str(uuid.uuid4()), amount=1000.0)
    
    assert response["status"] == "success"
    mock_card_service.update_usage.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.credit_card_tools.get_session')
@patch('expense_tracker.tools.credit_card_tools.CreditCardService')
async def test_get_active_cards_success(mock_card_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_card = MagicMock()
    mock_card.id = uuid.uuid4()
    mock_card.card_name = "HDFC Regalia"
    mock_card.credit_limit = Decimal("50000.00")
    mock_card.used_amount = Decimal("10000.00")
    mock_card.available_limit = Decimal("40000.00")
    mock_card.utilization_pct = 20.0
    
    mock_card_service = mock_card_service_class.return_value
    mock_card_service.get_active_cards = AsyncMock(return_value=[mock_card])
    
    register_credit_card_tools(mock_mcp)
    get_active_cards = mock_mcp.registered_tools['get_active_cards']
    
    response = await get_active_cards()
    
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    mock_card_service.get_active_cards.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.credit_card_tools.get_session')
@patch('expense_tracker.tools.credit_card_tools.CreditCardService')
async def test_get_active_cards_internal_error(mock_card_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_card_service = mock_card_service_class.return_value
    mock_card_service.get_active_cards = AsyncMock(side_effect=Exception("Database down"))
    
    register_credit_card_tools(mock_mcp)
    get_active_cards = mock_mcp.registered_tools['get_active_cards']
    
    response = await get_active_cards()
    assert response["status"] == "error"
