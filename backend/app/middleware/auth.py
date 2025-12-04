"""
Authentication middleware for JWT validation with Supabase.

Validates Supabase JWT tokens and extracts user information.
"""

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
        # Optional app-level toggle for test environments
        if getattr(request.app.state, "skip_auth_for_tests", False):
            request.state.user_role = "planner"
            request.state.user_id = "00000000-0000-0000-0000-000000000001"
            return await call_next(request)

        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip authentication for public path prefixes
        for prefix in self.PUBLIC_PATH_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        # Extract authorization header
        import logging
        logger = logging.getLogger(__name__)

        # Try both lowercase and capitalized header names
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

        if not auth_header:
            logger.warning(f"❌ Authorization header missing for {request.url.path}")
            print(f"[AUTH] Auth header missing/invalid for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing"},
            )

        # Validate Bearer token format
        if not auth_header.startswith("Bearer "):
            logger.warning(f"❌ Invalid Authorization header format for {request.url.path}")
            print(f"[AUTH] Invalid header format (prefix only): {auth_header[:20]}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format. Expected: Bearer <token>"},
            )

        token = auth_header.split(" ", 1)[1]
        logger.info(
            f"📥 JWT token received for {request.url.path}, "
            f"length: {len(token)}, preview: {token[:20]}..."
        )
        print(f"[AUTH] Token received, length: {len(token)}, prefix: {token[:20]}...")

        # Verify JWT token
        payload = verify_supabase_jwt(token)
        if not payload:
            logger.warning(
                f"JWT verification failed for {request.url.path}. "
                f"Check backend logs for details."
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        user_id = payload.get("sub")
        if not user_id:
            logger.error(f"JWT payload missing 'sub' field. Payload keys: {payload.keys()}")
            print("[AUTH] ERROR: JWT payload missing 'sub' field")
            return JSONResponse(
                status_code=401,
                content={"detail": "JWT token missing user ID"},
            )

        logger.info(
            f"JWT verification successful for {request.url.path}, user: {user_id}"
        )
        print(f"[AUTH] ✅ JWT verified, user_id: {user_id}, type: {type(user_id)}")

        # Add user information to request state
        request.state.user_id = user_id
        request.state.user_email = payload.get("email", "")
        request.state.user_role = payload.get("role", "planner")
        request.state.user_metadata = payload.get("user_metadata", {})

        return await call_next(request)
