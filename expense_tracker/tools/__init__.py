"""MCP Tools.

This package contains the presentation layer of the application.
It exposes FastMCP tool endpoints that validate inputs, invoke the
underlying business services, and return standardized JSON responses.

Tools are grouped by domain (expenses, budgets, analytics, etc.)
and are registered with the main FastMCP server via the `register_tools()`
function in each module.
"""
