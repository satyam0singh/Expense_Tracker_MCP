import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date
from decimal import Decimal

from expense_tracker.services.report_service import ReportService
from expense_tracker.database.models.expense import Expense

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def report_service(mock_repo):
    return ReportService(expense_repo=mock_repo)

def create_mock_expenses():
    category = MagicMock()
    category.display_name = "Food"
    subcategory = MagicMock()
    subcategory.display_name = "Groceries"
    
    expense1 = Expense(
        id=uuid.uuid4(),
        expense_date=date(2023, 5, 1),
        title="Supermarket",
        amount=Decimal("150.00"),
        currency="USD",
        payment_method="credit_card",
        notes="Weekly groceries"
    )
    expense1.category = category
    expense1.subcategory = subcategory
    
    expense2 = Expense(
        id=uuid.uuid4(),
        expense_date=date(2023, 5, 5),
        title="Restaurant",
        amount=Decimal("45.50"),
        currency="USD",
        payment_method="cash",
        notes=None
    )
    expense2.category = category
    expense2.subcategory = None
    
    return [expense1, expense2]

@pytest.mark.asyncio
async def test_generate_csv_report(report_service, mock_repo, mock_session):
    mock_repo.find_by_date_range.return_value = (create_mock_expenses(), 2)
    
    start_date = date(2023, 5, 1)
    end_date = date(2023, 5, 31)
    user_id = uuid.uuid4()
    
    csv_content = await report_service.generate_csv_report(mock_session, start_date, end_date, user_id)
    
    assert "Date,Category,Subcategory,Title,Amount,Currency,Payment Method,Notes" in csv_content
    assert "Supermarket" in csv_content
    assert "150.00" in csv_content
    assert "Restaurant" in csv_content

@pytest.mark.asyncio
async def test_generate_excel_report(report_service, mock_repo, mock_session):
    mock_repo.find_by_date_range.return_value = (create_mock_expenses(), 2)
    
    start_date = date(2023, 5, 1)
    end_date = date(2023, 5, 31)
    user_id = uuid.uuid4()
    
    excel_content = await report_service.generate_excel_report(mock_session, start_date, end_date, user_id)
    
    # Excel files start with a specific magic number
    assert excel_content.startswith(b"PK")

@pytest.mark.asyncio
async def test_generate_pdf_report(report_service, mock_repo, mock_session):
    mock_repo.find_by_date_range.return_value = (create_mock_expenses(), 2)
    
    start_date = date(2023, 5, 1)
    end_date = date(2023, 5, 31)
    user_id = uuid.uuid4()
    
    pdf_content = await report_service.generate_pdf_report(mock_session, start_date, end_date, user_id)
    
    # PDF files start with a specific magic number
    assert pdf_content.startswith(b"%PDF")
