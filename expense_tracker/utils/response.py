"""Standardized MCP response builders.

All MCP tools should use these functions to construct their return
values, ensuring a consistent response envelope across the entire API.

Response Envelope:
    {
        "status": "success" | "error",
        "data": { ... } | null,
        "message": "Human-readable message",
        "error": {                          # Only present on error
            "code": "VALIDATION_ERROR",
            "message": "...",
            "details": { ... }
        }
    }
"""

from __future__ import annotations

from typing import Any

from expense_tracker.core.exceptions import AppException


def success_response(
    data: Any = None,
    message: str = "Operation completed successfully.",
) -> dict[str, Any]:
    """Build a standardized success response for MCP tools.

    Args:
        data: The response payload (dict, list, or scalar).
        message: Human-readable success message.

    Returns:
        Dictionary with status="success", data, and message.
    """
    response: dict[str, Any] = {
        "status": "success",
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return response


def error_response(
    error: AppException | str,
    code: str = "INTERNAL_ERROR",
) -> dict[str, Any]:
    """Build a standardized error response for MCP tools.

    Args:
        error: An AppException instance or a plain error message string.
        code: Error code to use when error is a plain string.

    Returns:
        Dictionary with status="error" and structured error details.
    """
    if isinstance(error, AppException):
        return {
            "status": "error",
            "error": error.to_dict(),
        }
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": str(error),
        },
    }


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Results retrieved successfully.",
) -> dict[str, Any]:
    """Build a standardized paginated response for MCP tools.

    Args:
        items: List of items for the current page.
        total: Total number of matching items across all pages.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        message: Human-readable message.

    Returns:
        Dictionary with pagination metadata and items.
    """
    return {
        "status": "success",
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        },
    }
