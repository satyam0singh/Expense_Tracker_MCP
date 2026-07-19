"""Custom exception hierarchy for the Expense Tracker application.

All application exceptions inherit from AppException, which carries
a machine-readable error code and human-readable message. This allows
MCP tools to return structured error responses without exposing
internal stack traces.

Exception Hierarchy:
    AppException
    ├── ValidationError       — Input validation failures
    ├── NotFoundError         — Entity not found
    ├── DuplicateError        — Unique constraint violation
    ├── DatabaseError         — Database operation failures
    ├── ConfigurationError    — Configuration/environment issues
    ├── ReportError           — Report generation failures
    └── AuthorizationError    — Permission denied (future use)
"""

from __future__ import annotations


class AppException(Exception):
    """Base exception for all application errors.

    Attributes:
        code: Machine-readable error code (e.g., 'NOT_FOUND').
        message: Human-readable error description.
        details: Optional dictionary with additional context.
    """

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: dict[str, object] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, object]:
        """Serialize the exception to a dictionary for MCP responses.

        Returns:
            Dictionary with code, message, and details.
        """
        result: dict[str, object] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(AppException):
    """Raised when input validation fails.

    Examples:
        - Negative expense amount
        - Invalid date format
        - Missing required field
        - Invalid category name
    """

    def __init__(
        self,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class NotFoundError(AppException):
    """Raised when a requested entity does not exist.

    Examples:
        - Expense ID not found
        - Category name not found
        - Budget not found for given month
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: str | None = None,
        message: str | None = None,
    ) -> None:
        default_msg = f"{entity_type} not found"
        if entity_id:
            default_msg = f"{entity_type} with ID '{entity_id}' not found"
        super().__init__(
            message=message or default_msg,
            code="NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": entity_id or ""},
        )


class DuplicateError(AppException):
    """Raised when an operation would create a duplicate entry.

    Examples:
        - Budget already exists for category + month
        - Category name already exists
    """

    def __init__(
        self,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message=message, code="DUPLICATE", details=details)


class DatabaseError(AppException):
    """Raised when a database operation fails unexpectedly.

    Wraps SQLAlchemy or connection errors without exposing internals.
    """

    def __init__(
        self,
        message: str = "A database error occurred. Please try again.",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message=message, code="DATABASE_ERROR", details=details)


class ConfigurationError(AppException):
    """Raised when application configuration is invalid or missing.

    Examples:
        - Missing DATABASE_URL
        - Invalid log level
        - Missing required directory
    """

    def __init__(
        self,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message=message, code="CONFIGURATION_ERROR", details=details)


class ReportError(AppException):
    """Raised when report generation fails.

    Examples:
        - File write permission denied
        - Template rendering error
        - Invalid report format
    """

    def __init__(
        self,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message=message, code="REPORT_ERROR", details=details)


class AuthorizationError(AppException):
    """Raised when the user lacks permission for an operation.

    Reserved for future multi-user/RBAC implementation.
    """

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message=message, code="AUTHORIZATION_ERROR", details=details)
