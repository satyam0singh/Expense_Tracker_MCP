"""Budget schemas."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from expense_tracker.core.constants import Currency
from expense_tracker.schemas.base import BaseResponse, BaseSchema
from expense_tracker.schemas.category import CategoryResponse


class BudgetCreate(BaseSchema):
    """Schema for creating a new budget."""

    budget_amount: Decimal = Field(gt=0, decimal_places=2, description="Planned spending limit")
    currency: Currency = Field(default=Currency.INR, description="ISO currency code")
    
    # Can provide either UUID or name
    category_id: uuid.UUID | None = Field(default=None, description="Category UUID")
    category_name: str | None = Field(default=None, description="Category name (alternative to category_id)")
    
    month: date | None = Field(default=None, description="First day of the budget month. Defaults to current month start.")

    @field_validator("month", mode="before")
    def set_default_month(cls, v: Any) -> Any:
        """Set default month to the 1st of the current month if not provided."""
        if v is None:
            today = date.today()
            return date(today.year, today.month, 1)
        # Ensure it's the 1st of the month
        if isinstance(v, str):
            try:
                # If they passed '2026-07', turn it into '2026-07-01'
                if len(v) == 7:
                    v = f"{v}-01"
                d = date.fromisoformat(v)
                return date(d.year, d.month, 1)
            except ValueError:
                pass
        elif isinstance(v, date):
            return date(v.year, v.month, 1)
        return v


class BudgetUpdate(BaseSchema):
    """Schema for updating an existing budget."""

    budget_amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)


class BudgetResponse(BaseResponse):
    """Schema for a budget response."""

    user_id: uuid.UUID
    category_id: uuid.UUID
    month: date
    budget_amount: Decimal
    spent_amount: Decimal
    currency: str
    
    # Computed fields (added by schema or repository)
    remaining: Decimal | None = None
    percentage_used: float | None = None
    
    category: CategoryResponse | None = None


class BudgetStatusResponse(BaseSchema):
    """Schema for a budget status response with alerts."""

    budget_id: uuid.UUID
    category: str
    month: date
    budget_amount: Decimal
    spent_amount: Decimal
    remaining: Decimal
    percentage_used: float
    currency: str
    alert: str | None = None
