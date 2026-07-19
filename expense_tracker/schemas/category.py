"""Category and Subcategory schemas."""

import uuid
from typing import Annotated

from pydantic import Field, StringConstraints

from expense_tracker.schemas.base import BaseResponse, BaseSchema


class SubcategoryCreate(BaseSchema):
    """Schema for creating a new subcategory."""

    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, to_lower=True, min_length=2, max_length=50),
    ] = Field(description="Machine-readable unique name (e.g. 'groceries')")
    display_name: str = Field(
        description="Human-readable name (e.g. 'Groceries & Staples')",
        min_length=2,
        max_length=100,
    )
    sort_order: int = Field(default=0, description="Display order")


class SubcategoryUpdate(BaseSchema):
    """Schema for updating an existing subcategory."""

    display_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    sort_order: int | None = Field(default=None)


class SubcategoryResponse(BaseResponse):
    """Schema for a subcategory response."""

    category_id: uuid.UUID
    name: str
    display_name: str
    sort_order: int


class CategoryCreate(BaseSchema):
    """Schema for creating a new category."""

    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, to_lower=True, min_length=2, max_length=50),
    ] = Field(description="Machine-readable unique name (e.g. 'food')")
    display_name: str = Field(
        description="Human-readable name (e.g. 'Food & Dining')",
        min_length=2,
        max_length=100,
    )
    icon: str | None = Field(default=None, max_length=10)
    color: str | None = Field(default=None, max_length=7)
    sort_order: int = Field(default=0)


class CategoryUpdate(BaseSchema):
    """Schema for updating an existing category."""

    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    icon: str | None = Field(default=None, max_length=10)
    color: str | None = Field(default=None, max_length=7)
    sort_order: int | None = Field(default=None)


class CategoryResponse(BaseResponse):
    """Schema for a category response. Includes subcategories if eager loaded."""

    name: str
    display_name: str
    icon: str | None = None
    color: str | None = None
    sort_order: int
    is_system: bool
    subcategories: list[SubcategoryResponse] = Field(default_factory=list)
