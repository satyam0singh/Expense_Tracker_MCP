"""Expense schemas."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from expense_tracker.core.constants import Currency, PaymentMethod
from expense_tracker.schemas.base import BaseResponse, BaseSchema
from expense_tracker.schemas.category import CategoryResponse, SubcategoryResponse


class ExpenseCreate(BaseSchema):
    """Schema for creating a new expense."""

    title: str = Field(min_length=2, max_length=255, description="Short description of the expense")
    amount: Decimal = Field(gt=0, decimal_places=2, description="Expense amount (must be positive)")
    currency: Currency = Field(default=Currency.INR, description="ISO currency code")
    
    # Can provide either UUIDs or names. The service layer will resolve names to UUIDs.
    category_id: uuid.UUID | None = Field(default=None, description="Category UUID")
    category_name: str | None = Field(default=None, description="Category name (alternative to category_id)")
    
    subcategory_id: uuid.UUID | None = Field(default=None, description="Subcategory UUID")
    subcategory_name: str | None = Field(default=None, description="Subcategory name (alternative to subcategory_id)")
    
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH, description="How the expense was paid")
    expense_date: date | None = Field(default=None, description="Date of expense. Defaults to today.")
    notes: str | None = Field(default=None, description="Optional detailed notes")

    @field_validator("expense_date", mode="before")
    def set_default_date(cls, v: Any) -> Any:
        """Set default date to today if not provided."""
        if v is None:
            return date.today()
        return v


class ExpenseUpdate(BaseSchema):
    """Schema for updating an existing expense."""

    title: str | None = Field(default=None, min_length=2, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    currency: Currency | None = Field(default=None)
    category_id: uuid.UUID | None = Field(default=None)
    subcategory_id: uuid.UUID | None = Field(default=None)
    payment_method: PaymentMethod | None = Field(default=None)
    expense_date: date | None = Field(default=None)
    notes: str | None = Field(default=None)


class ExpenseResponse(BaseResponse):
    """Schema for an expense response. Includes related category/subcategory if eagerly loaded."""

    user_id: uuid.UUID
    title: str
    amount: Decimal
    currency: str
    payment_method: str
    expense_date: date
    notes: str | None = None
    
    # Eagerly loaded relationships
    category_id: uuid.UUID
    category: CategoryResponse | None = None
    subcategory_id: uuid.UUID | None = None
    subcategory: SubcategoryResponse | None = None
