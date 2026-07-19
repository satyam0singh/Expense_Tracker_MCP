"""Category MCP Tools.

Registers endpoints for querying category taxonomy.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from expense_tracker.database.session import get_session
from expense_tracker.services.category_service import CategoryService
from expense_tracker.utils.response import error_response, success_response


def register_category_tools(mcp: FastMCP) -> None:
    """Register category-related tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    category_service = CategoryService()

    @mcp.tool()
    async def list_categories() -> dict[str, Any]:
        """List all available expense categories and their subcategories.
        
        Returns a hierarchical list of categories, their icons, and subcategories.
        """
        try:
            async with get_session() as session:
                categories = await category_service.get_all_categories(session)
                
                return success_response(
                    data=[
                        {
                            "id": str(c.id),
                            "name": c.name,
                            "display_name": c.display_name,
                            "icon": c.icon,
                            "subcategories": [
                                {
                                    "id": str(s.id),
                                    "name": s.name,
                                    "display_name": s.display_name,
                                }
                                for s in c.subcategories
                            ],
                        }
                        for c in categories
                    ],
                    message=f"Retrieved {len(categories)} categories."
                )
        except Exception as exc:
            return error_response(str(exc), code="INTERNAL_ERROR")
