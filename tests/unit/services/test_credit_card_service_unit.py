import pytest
import uuid
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from datetime import date, timedelta

from expense_tracker.services.credit_card_service import CreditCardService
from expense_tracker.schemas.credit_card import CreditCardUpdate, CreditCardUsageUpdate
from expense_tracker.core.exceptions import DuplicateError, ValidationError
from expense_tracker.database.models.credit_card import CreditCard
from expense_tracker.core.constants import Currency

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def credit_card_service(mock_repo):
    service = CreditCardService(repo=mock_repo)
    service._audit = AsyncMock(return_value=None)
    return service

@pytest.mark.asyncio
async def test_update_card_success(credit_card_service, mock_repo, mock_session):
    card_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    mock_card = CreditCard(
        id=card_id,
        card_name="Old Card",
        credit_limit=Decimal("1000.00"),
        used_amount=Decimal("100.00"),
        currency=Currency.USD.value
    )
    
    mock_updated = CreditCard(
        id=card_id,
        card_name="New Card",
        credit_limit=Decimal("2000.00"),
        used_amount=Decimal("100.00"),
        currency=Currency.USD.value
    )
    
    mock_repo.get_by_id_or_raise.return_value = mock_card
    mock_repo.name_exists.return_value = False
    mock_repo.update.return_value = mock_updated
    
    update_data = CreditCardUpdate(
        card_name="New Card",
        credit_limit=Decimal("2000.00")
    )
    
    result = await credit_card_service.update_card(mock_session, card_id, user_id, update_data)
    
    assert result.card_name == "New Card"
    mock_repo.name_exists.assert_called_once()
    mock_repo.update.assert_called_once()
    credit_card_service._audit.assert_called_once()

@pytest.mark.asyncio
async def test_update_card_duplicate_name(credit_card_service, mock_repo, mock_session):
    card_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    mock_card = CreditCard(
        id=card_id,
        card_name="Old Card",
    )
    
    mock_repo.get_by_id_or_raise.return_value = mock_card
    mock_repo.name_exists.return_value = True
    
    update_data = CreditCardUpdate(card_name="Existing Card")
    
    with pytest.raises(DuplicateError):
        await credit_card_service.update_card(mock_session, card_id, user_id, update_data)

@pytest.mark.asyncio
async def test_update_usage_payment_exceeds(credit_card_service, mock_repo, mock_session):
    card_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    mock_card = CreditCard(
        id=card_id,
        used_amount=Decimal("100.00")
    )
    
    mock_repo.get_by_id_or_raise.return_value = mock_card
    
    usage_data = CreditCardUsageUpdate(
        amount=Decimal("150.00"),
        is_payment=True
    )
    
    with pytest.raises(ValidationError):
        await credit_card_service.update_usage(mock_session, card_id, user_id, usage_data)

@pytest.mark.asyncio
async def test_update_usage_success(credit_card_service, mock_repo, mock_session):
    card_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    mock_card = CreditCard(
        id=card_id,
        used_amount=Decimal("100.00")
    )
    
    mock_updated = CreditCard(
        id=card_id,
        used_amount=Decimal("50.00")
    )
    
    mock_repo.get_by_id_or_raise.return_value = mock_card
    mock_repo.update_usage.return_value = mock_updated
    
    usage_data = CreditCardUsageUpdate(
        amount=Decimal("50.00"),
        is_payment=True
    )
    
    result = await credit_card_service.update_usage(mock_session, card_id, user_id, usage_data)
    
    assert result.used_amount == Decimal("50.00")
    mock_repo.update_usage.assert_called_once()
    credit_card_service._audit.assert_called_once()

@pytest.mark.asyncio
async def test_get_active_cards(credit_card_service, mock_repo, mock_session):
    user_id = uuid.uuid4()
    mock_repo.get_active_cards.return_value = []
    
    result = await credit_card_service.get_active_cards(mock_session, user_id)
    assert result == []
    mock_repo.get_active_cards.assert_called_once_with(mock_session, user_id=user_id)

@pytest.mark.asyncio
async def test_get_upcoming_due(credit_card_service, mock_repo, mock_session):
    user_id = uuid.uuid4()
    today = date.today()
    
    mock_cards = [
        CreditCard(
            id=uuid.uuid4(),
            card_name="Card 1",
            used_amount=Decimal("100.00"),
            currency=Currency.USD.value,
            due_date=today + timedelta(days=2)
        ),
        CreditCard(
            id=uuid.uuid4(),
            card_name="Card 2",
            used_amount=Decimal("200.00"),
            currency=Currency.USD.value,
            due_date=today + timedelta(days=6)
        ),
        CreditCard(
            id=uuid.uuid4(),
            card_name="Card 3",
            used_amount=Decimal("300.00"),
            currency=Currency.USD.value,
            due_date=today + timedelta(days=10)
        ),
        CreditCard(
            id=uuid.uuid4(),
            card_name="Card No Due",
            used_amount=Decimal("0.00"),
            currency=Currency.USD.value,
            due_date=None
        )
    ]
    
    mock_repo.get_upcoming_due.return_value = mock_cards
    
    results = await credit_card_service.get_upcoming_due(mock_session, user_id)
    
    assert len(results) == 3
    assert results[0]["alert_level"] == "critical"
    assert results[1]["alert_level"] == "warning"
    assert results[2]["alert_level"] == "info"
