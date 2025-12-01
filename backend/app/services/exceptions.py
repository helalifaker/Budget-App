"""
Custom exceptions for the service layer.

Provides structured error handling across all services with proper HTTP status codes.
"""

from typing import Any


class ServiceException(Exception):
    """Base exception for all service layer errors."""

    def __init__(self, message: str, status_code: int = 500, details: dict[str, Any] | None = None):
        """
        Initialize service exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            details: Additional error context
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(ServiceException):
    """Resource not found error (HTTP 404)."""

    def __init__(self, resource: str, identifier: str | None = None, details: dict[str, Any] | None = None):
        """
        Initialize not found error.

        Args:
            resource: Resource type (e.g., 'BudgetVersion', 'ClassSizeParam')
            identifier: Resource identifier (e.g., ID, name)
            details: Additional error context
        """
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status_code=404, details=details)


class ValidationError(ServiceException):
    """Data validation error (HTTP 400)."""

    def __init__(self, message: str, field: str | None = None, details: dict[str, Any] | None = None):
        """
        Initialize validation error.

        Args:
            message: Validation error message
            field: Field name that failed validation
            details: Additional error context
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message, status_code=400, details=error_details)


class ConflictError(ServiceException):
    """Resource conflict error (HTTP 409)."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """
        Initialize conflict error.

        Args:
            message: Conflict error message
            details: Additional error context
        """
        super().__init__(message, status_code=409, details=details)


class UnauthorizedError(ServiceException):
    """Authentication error (HTTP 401)."""

    def __init__(self, message: str = "Authentication required", details: dict[str, Any] | None = None):
        """
        Initialize unauthorized error.

        Args:
            message: Authentication error message
            details: Additional error context
        """
        super().__init__(message, status_code=401, details=details)


class ForbiddenError(ServiceException):
    """Authorization error (HTTP 403)."""

    def __init__(self, message: str = "Insufficient permissions", details: dict[str, Any] | None = None):
        """
        Initialize forbidden error.

        Args:
            message: Authorization error message
            details: Additional error context
        """
        super().__init__(message, status_code=403, details=details)


class BusinessRuleError(ServiceException):
    """Business rule violation error (HTTP 422)."""

    def __init__(self, rule: str, message: str, details: dict[str, Any] | None = None):
        """
        Initialize business rule error.

        Args:
            rule: Business rule name/code
            message: Rule violation message
            details: Additional error context
        """
        error_details = details or {}
        error_details["rule"] = rule
        super().__init__(message, status_code=422, details=error_details)
