import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from pydantic import ValidationError

from expense_tracker.schemas.expense import ExpenseCreate, ExpenseUpdate
from expense_tracker.core.constants import Currency

TEST_UUID = uuid.uuid4()

def test_expense_create_valid():
    """Test creating a valid expense."""
    expense = ExpenseCreate(
        title="Dinner",
        amount=Decimal("45.50"),
        currency=Currency.USD,
        category_id=TEST_UUID,
        expense_date=date.today(),
        notes="Dinner with friends"
    )
    assert expense.title == "Dinner"
    assert expense.amount == Decimal("45.50")
    assert expense.currency == Currency.USD

def test_expense_create_negative_amount():
    """Test that an expense cannot have a negative amount."""
    with pytest.raises(ValidationError) as exc_info:
        ExpenseCreate(
            title="Dinner",
            amount=Decimal("-10.00"),
            currency=Currency.USD,
            category_id=TEST_UUID,
            expense_date=date.today()
        )
    assert "amount" in str(exc_info.value)

def test_expense_create_zero_amount():
    """Test that an expense cannot have a zero amount."""
    with pytest.raises(ValidationError) as exc_info:
        ExpenseCreate(
            title="Dinner",
            amount=Decimal("0.00"),
            currency=Currency.USD,
            category_id=TEST_UUID,
            expense_date=date.today()
        )
    assert "amount" in str(exc_info.value)

def test_expense_create_future_date():
    """Test that an expense cannot be in the future."""
    future_date = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError) as exc_info:
        ExpenseCreate(
            title="Dinner",
            amount=Decimal("10.00"),
            currency=Currency.USD,
            category_id=TEST_UUID,
            expense_date=future_date
        )
    assert "expense_date" in str(exc_info.value)

def test_expense_create_long_notes():
    """Test that notes cannot exceed 1000 characters."""
    long_notes = "a" * 1001
    with pytest.raises(ValidationError) as exc_info:
        ExpenseCreate(
            title="Dinner",
            amount=Decimal("10.00"),
            currency=Currency.USD,
            category_id=TEST_UUID,
            expense_date=date.today(),
            notes=long_notes
        )
    assert "notes" in str(exc_info.value).lower()

def test_expense_update_partial():
    """Test that partial updates are valid."""
    update = ExpenseUpdate(amount=Decimal("50.00"))
    assert update.amount == Decimal("50.00")
    assert update.title is None
