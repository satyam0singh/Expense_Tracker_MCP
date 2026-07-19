import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date

from expense_tracker.tools.report_tools import register_report_tools
from expense_tracker.core.exceptions import ValidationError

@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    tools = {}
    def tool_decorator():
        def wrapper(func):
            tools[func.__name__] = func
            return func
        return wrapper
    mcp.tool = tool_decorator
    mcp.registered_tools = tools
    return mcp

@pytest.fixture
def mock_session_cm():
    session = AsyncMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm

@pytest.mark.asyncio
@patch('expense_tracker.tools.report_tools.get_session')
@patch('expense_tracker.tools.report_tools.ReportService')
async def test_export_csv_success(mock_report_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_report_service = mock_report_service_class.return_value
    mock_report_service.generate_csv_report = AsyncMock(return_value="date,amount\n2023-01-01,100")
    
    register_report_tools(mock_mcp)
    export_csv = mock_mcp.registered_tools['export_csv']
    
    response = await export_csv(month="2026-07")
    
    assert response["status"] == "success"
    assert response["data"]["csv"] == "date,amount\n2023-01-01,100"
    mock_report_service.generate_csv_report.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.report_tools.get_session')
@patch('expense_tracker.tools.report_tools.ReportService')
async def test_export_csv_error(mock_report_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_report_service = mock_report_service_class.return_value
    mock_report_service.generate_csv_report = AsyncMock(side_effect=ValidationError("Invalid"))
    
    register_report_tools(mock_mcp)
    export_csv = mock_mcp.registered_tools['export_csv']
    
    response = await export_csv(month="2026-07")
    assert response["status"] == "error"

@pytest.mark.asyncio
@patch('expense_tracker.tools.report_tools.get_session')
@patch('expense_tracker.tools.report_tools.ReportService')
async def test_export_excel_success(mock_report_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_report_service = mock_report_service_class.return_value
    mock_report_service.generate_excel_report = AsyncMock(return_value=b"excel_bytes")
    
    register_report_tools(mock_mcp)
    export_excel = mock_mcp.registered_tools['export_excel']
    
    response = await export_excel()
    
    assert response["status"] == "success"
    assert "excel_base64" in response["data"]
    mock_report_service.generate_excel_report.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.report_tools.get_session')
@patch('expense_tracker.tools.report_tools.ReportService')
async def test_export_pdf_success(mock_report_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    
    mock_report_service = mock_report_service_class.return_value
    mock_report_service.generate_pdf_report = AsyncMock(return_value=b"pdf_bytes")
    
    register_report_tools(mock_mcp)
    export_pdf = mock_mcp.registered_tools['export_pdf']
    
    response = await export_pdf()
    
    assert response["status"] == "success"
    assert "pdf_base64" in response["data"]
    mock_report_service.generate_pdf_report.assert_called_once()

@pytest.mark.asyncio
@patch('expense_tracker.tools.report_tools.get_session')
@patch('expense_tracker.tools.report_tools.ReportService')
async def test_export_pdf_internal_error(mock_report_service_class, mock_get_session, mock_mcp, mock_session_cm):
    mock_get_session.return_value = mock_session_cm
    mock_report_service = mock_report_service_class.return_value
    mock_report_service.generate_pdf_report = AsyncMock(side_effect=Exception("Database down"))
    
    register_report_tools(mock_mcp)
    export_pdf = mock_mcp.registered_tools['export_pdf']
    
    response = await export_pdf()
    assert response["status"] == "error"
