"""
Authentication middleware for JWT validation with Supabase.

Validates Supabase JWT tokens and extracts user information.
"""

import os
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import verify_supabase_jwt


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating Supabase JWT tokens.

    Extracts the Authorization header, validates the JWT token,
    and adds user information to the request state.

    Protected routes require a valid JWT token.
    Public routes (health check, docs) are exempted.
    """

    PUBLIC_PATHS = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    PUBLIC_PATH_PREFIXES = [
        "/health",  # All health endpoints (/health/live, /health/ready)
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and validate authentication.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in the chain

        Returns:
            Response from the next handler or authentication error
        """
        # Test environments use dependency overrides; skip auth when configured
        if os.getenv("DISABLE_AUTH_FOR_TESTS", "false").lower() == "true" or os.getenv(
            "PYTEST_CURRENT_TEST"
        ):
            # Provide a synthetic planner identity so downstream middleware has a role
            request.state.user_role = "planner"
            request.state.user_id = "test-user"
            return await call_next(request)

        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip authentication for public path prefixes
        for prefix in self.PUBLIC_PATH_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        # Extract authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing"},
            )

        # Validate Bearer token format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format. Expected: Bearer <token>"},
            )

        token = parts[1]

        # Verify JWT token
        payload = verify_supabase_jwt(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        # Add user information to request state
        request.state.user_id = payload.get("sub")
        request.state.user_email = payload.get("email")
        request.state.user_role = payload.get("role", "planner")
        request.state.user_metadata = payload.get("user_metadata", {})

        return await call_next(request)
