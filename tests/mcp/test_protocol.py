import pytest
from expense_tracker.server import create_server

@pytest.fixture
def mcp_server():
    """Create a configured MCP server instance."""
    return create_server()

def test_mcp_server_initialization(mcp_server):
    assert mcp_server.name == "ExpenseTrackerMCP"

@pytest.mark.asyncio
async def test_mcp_registered_tools(mcp_server):
    """Test that all expected domains are registered as tools."""
    # list_tools() returns a list of Tool objects
    tools = await mcp_server._list_tools()
    
    tool_names = [t.name for t in tools]
    
    # Check for expected tools from each domain
    expected_tools = [
        "add_expense",
        "update_expense",
        "delete_expense",
        "search_expenses",
        "list_categories",
        "set_budget",
        "update_budget",
        "get_budget_status",
        "analyze_spending",
        "get_category_breakdown",
        "get_spending_trends",
        "add_credit_card",
        "record_card_payment",
        "get_active_cards",
        "export_csv",
    ]
    
    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Expected tool {tool_name} to be registered"
