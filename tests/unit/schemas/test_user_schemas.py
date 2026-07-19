import pytest
from pydantic import ValidationError

from expense_tracker.schemas.user import UserCreate

def test_user_create_valid():
    """Test creating a valid user."""
    user = UserCreate(
        username="johndoe",
        email="john@example.com",
        display_name="John Doe",
        password="securepassword123"
    )
    assert user.username == "johndoe"
    assert user.email == "john@example.com"

def test_user_create_invalid_email():
    """Test that an invalid email raises a validation error."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username="johndoe",
            email="not-an-email",
            display_name="John Doe",
            password="securepassword123"
        )
    assert "email" in str(exc_info.value).lower()

def test_user_create_empty_username():
    """Test that an empty username is not allowed."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username="",
            email="john@example.com",
            display_name="John Doe",
            password="securepassword123"
        )
    assert "username" in str(exc_info.value).lower()

def test_user_create_short_password():
    """Test that password too short raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username="johndoe",
            email="john@example.com",
            password="short"
        )
    assert "password" in str(exc_info.value).lower()
