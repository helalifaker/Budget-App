"""
Role-Based Access Control (RBAC) middleware.

Enforces permissions based on user roles:
- admin: Full access to all resources
- manager: Can approve budgets, manage configurations
- planner: Can create and edit budgets (default role)
- viewer: Read-only access
"""

import re
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Middleware for role-based access control.

    Checks user role against endpoint requirements.
    Requires AuthenticationMiddleware to run first.
    """

    # HTTP methods that modify data
    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Paths that require specific roles
    ADMIN_ONLY_PATHS = [
        "/api/v1/users",
        "/api/v1/system",
    ]

    MANAGER_PATHS = [
        "/api/v1/budget-versions/{id}/approve",
        "/api/v1/budget-versions/{id}/submit",
        "/api/v1/budget-versions/{id}/lock",
    ]

    @staticmethod
    def _path_pattern_to_regex(path_pattern: str) -> re.Pattern:
        """
        Convert a path pattern with {param} placeholders to a compiled regex.

        Args:
            path_pattern: Path with placeholders, e.g., "/api/v1/users/{id}/approve"

        Returns:
            Compiled regex pattern that matches paths like "/api/v1/users/123/approve"

        Example:
            pattern = _path_pattern_to_regex("/api/v1/users/{id}/approve")
            pattern.match("/api/v1/users/123/approve")  # True
            pattern.match("/api/v1/users/123/reject")   # False
        """
        # Escape special regex characters, then replace {param} with regex group
        # {id} -> [^/]+ (matches any characters except /)
        regex_pattern = re.escape(path_pattern).replace(r"\{[^}]+\}", "[^/]+")
        # Use a more precise replacement for all {param} patterns
        regex_pattern = re.sub(r"\\{[^}]+\\}", r"[^/]+", re.escape(path_pattern))
        return re.compile(f"^{regex_pattern}$")

    @classmethod
    def _matches_any_pattern(cls, path: str, patterns: list[str]) -> bool:
        """
        Check if path matches any of the given patterns.

        Supports both literal paths and paths with {param} placeholders.

        Args:
            path: Actual request path
            patterns: List of path patterns

        Returns:
            True if path matches any pattern
        """
        for pattern in patterns:
            # If pattern contains {param}, use regex matching
            if "{" in pattern:
                regex = cls._path_pattern_to_regex(pattern)
                if regex.match(path):
                    return True
            # Otherwise use simple string prefix matching
            elif path.startswith(pattern):
                return True
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and enforce RBAC.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in the chain

        Returns:
            Response from the next handler or authorization error
        """
        # Skip RBAC for public paths
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get user role from request state (set by AuthenticationMiddleware)
        user_role = getattr(request.state, "user_role", "viewer")

        # Admin has full access
        if user_role == "admin":
            return await call_next(request)

        # Check admin-only paths
        if self._matches_any_pattern(request.url.path, self.ADMIN_ONLY_PATHS):
            return JSONResponse(
                status_code=403,
                content={"detail": "Admin access required"},
            )

        # Check manager paths
        if self._matches_any_pattern(request.url.path, self.MANAGER_PATHS):
            if user_role not in ["admin", "manager"]:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Manager or admin access required"},
                )

        # Viewers cannot modify data
        if user_role == "viewer" and request.method in self.WRITE_METHODS:
            return JSONResponse(
                status_code=403,
                content={"detail": "Read-only access. Cannot modify data."},
            )

        return await call_next(request)
