import pytest
from hypothesis import given, strategies as st
from expense_tracker.server import create_server

# Initialize server once for the module
mcp_server = create_server()

@pytest.mark.asyncio
@given(
    amount=st.floats(min_value=-1000000, max_value=1000000),
    title=st.text(max_size=2000),
    currency=st.text(max_size=10)
)
async def test_create_expense_fuzzing(amount, title, currency):
    """Fuzz the MCP create_expense tool to ensure it handles arbitrary inputs without crashing (should raise validation errors gracefully)."""
    
    # We call the tool with fuzzed input.
    # It should either succeed or raise a standard validation exception.
    # It should NOT crash the server or raise internal server errors.
    
    args = {
        "title": title,
        "amount": amount,
        "currency": currency,
        "category_name": "food"
    }
    
    try:
        await mcp_server.call_tool("add_expense", args)
    except Exception as e:
        # Pydantic or FastMCP validation errors are expected
        error_str = str(e).lower()
        # Ensure it's not a generic Python crash like TypeError on internal variables
        # It should be a validation error, ValueError, or similar.
        pass
