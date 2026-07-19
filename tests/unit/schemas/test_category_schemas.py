import pytest
from pydantic import ValidationError

from expense_tracker.schemas.category import CategoryCreate, CategoryUpdate

def test_category_create_valid():
    """Test creating a valid category."""
    category = CategoryCreate(name="food", display_name="Food & Dining", color="#FF0000")
    assert category.name == "food"
    
    category_2 = CategoryCreate(name="  Utilities  ", display_name="Utilities", color="#00FF00")
    assert category_2.name == "utilities" # tests strip and lower
    assert category_2.color == "#00FF00"

def test_category_create_empty_name():
    with pytest.raises(ValidationError) as exc_info:
        CategoryCreate(name="", display_name="Empty")
    assert "name" in str(exc_info.value).lower()

def test_category_update_partial():
    update = CategoryUpdate(display_name="Entertainment")
    assert update.display_name == "Entertainment"
    assert update.color is None
