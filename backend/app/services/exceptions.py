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


class IntegrationError(ServiceException):
    """Integration error with external systems (HTTP 502)."""

    def __init__(self, message: str, integration_type: str | None = None, details: dict[str, Any] | None = None):
        """
        Initialize integration error.

        Args:
            message: Integration error message
            integration_type: Type of integration (odoo, skolengo, aefe)
            details: Additional error context
        """
        error_details = details or {}
        if integration_type:
            error_details["integration_type"] = integration_type
        super().__init__(message, status_code=502, details=error_details)


class VersionConflictError(ServiceException):
    """Optimistic locking version conflict error (HTTP 409).

    Raised when a cell update fails because the cell was modified
    by another user since it was loaded (version mismatch).
    """

    def __init__(
        self,
        resource: str,
        current_version: int,
        provided_version: int,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize version conflict error.

        Args:
            resource: Resource type (e.g., 'PlanningCell')
            current_version: Current version in database
            provided_version: Version provided in the update request
            details: Additional error context
        """
        message = (
            f"{resource} was modified by another user. "
            f"Expected version {provided_version}, but current version is {current_version}. "
            "Please refresh and try again."
        )
        error_details = details or {}
        error_details["current_version"] = current_version
        error_details["provided_version"] = provided_version
        super().__init__(message, status_code=409, details=error_details)


class CellLockedError(ServiceException):
    """Cell is locked and cannot be modified (HTTP 423).

    Raised when attempting to modify a cell that has been locked
    (e.g., after budget approval).
    """

    def __init__(
        self,
        cell_id: str,
        lock_reason: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize cell locked error.

        Args:
            cell_id: ID of the locked cell
            lock_reason: Reason the cell was locked
            details: Additional error context
        """
        message = f"Cell {cell_id} is locked and cannot be modified"
        if lock_reason:
            message = f"{message}: {lock_reason}"
        error_details = details or {}
        error_details["cell_id"] = cell_id
        if lock_reason:
            error_details["lock_reason"] = lock_reason
        super().__init__(message, status_code=423, details=error_details)
