"""User schemas for data validation."""

from pydantic import ConfigDict, EmailStr, Field

from expense_tracker.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """Base schema for user data."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    display_name: str | None = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseSchema):
    """Schema for updating an existing user."""

    email: EmailStr | None = None
    display_name: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class UserResponse(UserBase):
    """Schema for returning user data."""

    id: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
