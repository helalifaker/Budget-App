"""
Role-Based Access Control (RBAC) middleware.

Enforces permissions based on user roles:
- admin: Full access to all resources
- manager: Can approve budgets, manage configurations
- planner: Can create and edit budgets (default role)
- viewer: Read-only access
"""

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
    ]

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
        if any(request.url.path.startswith(path) for path in self.ADMIN_ONLY_PATHS):
            return JSONResponse(
                status_code=403,
                content={"detail": "Admin access required"},
            )

        # Check manager paths
        if any(request.url.path.startswith(path) for path in self.MANAGER_PATHS):
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
