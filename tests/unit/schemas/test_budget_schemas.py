import uuid
import pytest
from pydantic import ValidationError
from datetime import date
from decimal import Decimal

from expense_tracker.schemas.budget import BudgetCreate
from expense_tracker.core.constants import Currency

TEST_UUID = uuid.uuid4()

def test_budget_create_valid():
    budget = BudgetCreate(
        category_id=TEST_UUID,
        budget_amount=Decimal("1000.00"),
        month=date.today(),
        currency=Currency.USD
    )
    assert budget.budget_amount == Decimal("1000.00")
    assert budget.currency == Currency.USD

def test_budget_create_negative_amount():
    with pytest.raises(ValidationError) as exc_info:
        BudgetCreate(
            category_id=TEST_UUID,
            budget_amount=Decimal("-50.00"),
            month=date.today(),
            currency=Currency.USD
        )
    assert "budget_amount" in str(exc_info.value).lower()

def test_budget_create_month_none():
    budget = BudgetCreate(
        category_id=TEST_UUID,
        budget_amount=Decimal("1000.00"),
        month=None,
        currency=Currency.USD
    )
    today = date.today()
    assert budget.month == date(today.year, today.month, 1)

def test_budget_create_month_str_ym():
    budget = BudgetCreate(
        category_id=TEST_UUID,
        budget_amount=Decimal("1000.00"),
        month="2026-07",
        currency=Currency.USD
    )
    assert budget.month == date(2026, 7, 1)

def test_budget_create_month_str_ymd():
    budget = BudgetCreate(
        category_id=TEST_UUID,
        budget_amount=Decimal("1000.00"),
        month="2026-07-15",
        currency=Currency.USD
    )
    assert budget.month == date(2026, 7, 1)

def test_budget_create_month_str_invalid():
    with pytest.raises(ValidationError):
        BudgetCreate(
            category_id=TEST_UUID,
            budget_amount=Decimal("1000.00"),
            month="invalid-date",
            currency=Currency.USD
        )
