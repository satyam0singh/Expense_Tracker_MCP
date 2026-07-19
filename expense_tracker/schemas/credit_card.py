"""CreditCard schemas."""

import uuid
from datetime import date
from decimal import Decimal

from pydantic import Field, StringConstraints

from expense_tracker.core.constants import CardNetwork, Currency
from expense_tracker.schemas.base import BaseResponse, BaseSchema


class CreditCardCreate(BaseSchema):
    """Schema for creating a new credit card."""

    card_name: str = Field(min_length=2, max_length=100, description="User-assigned name (e.g. 'HDFC Regalia')")
    card_network: CardNetwork = Field(default=CardNetwork.OTHER, description="Card network")
    last_four_digits: str = Field(pattern=r"^\d{4}$", description="Last 4 digits of the card")
    credit_limit: Decimal = Field(gt=0, decimal_places=2, description="Total credit limit")
    used_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, description="Current outstanding balance")
    billing_cycle_day: int = Field(ge=1, le=31, default=1, description="Day of month for billing cycle start")
    currency: Currency = Field(default=Currency.INR, description="ISO currency code")


class CreditCardUpdate(BaseSchema):
    """Schema for updating an existing credit card."""

    card_name: str | None = Field(default=None, min_length=2, max_length=100)
    card_network: CardNetwork | None = Field(default=None)
    credit_limit: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    billing_cycle_day: int | None = Field(default=None, ge=1, le=31)
    is_active: bool | None = Field(default=None)


class CreditCardUsageUpdate(BaseSchema):
    """Schema for recording a payment or charge against a card."""

    amount: Decimal = Field(gt=0, decimal_places=2, description="Amount to add/subtract")
    is_payment: bool = Field(default=False, description="True if making a payment, False if adding a charge")


class CreditCardResponse(BaseResponse):
    """Schema for a credit card response."""

    user_id: uuid.UUID
    card_name: str
    card_network: str
    last_four_digits: str
    credit_limit: Decimal
    used_amount: Decimal
    billing_cycle_day: int
    due_date: date | None = None
    is_active: bool
    currency: str
    
    # Computed fields (available on the ORM model)
    available_limit: Decimal | None = None
    utilization_pct: float | None = None
