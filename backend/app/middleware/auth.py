"""
Authentication middleware for JWT validation with Supabase.

Validates Supabase JWT tokens and extracts user information.
"""

import os
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import verify_supabase_jwt

# Module-level structured logger
logger = structlog.get_logger(__name__)


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

    def _get_cors_headers(self, request: Request) -> dict[str, str]:
        """
        Generate CORS headers for authentication responses.

        This ensures 401 responses include proper CORS headers so browsers
        don't block them as CORS violations.
        """
        origin = request.headers.get("origin", "")

        # Get allowed origins from environment
        allowed_origins_str = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:3000"
        )
        allowed_origins = [o.strip() for o in allowed_origins_str.split(",")]

        # Add production and Vercel origins
        production_domain = os.getenv("PRODUCTION_FRONTEND_URL")
        if production_domain:
            allowed_origins.append(production_domain)

        # Check if origin is allowed
        cors_origin = origin if origin in allowed_origins else allowed_origins[0]

        return {
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
            "Access-Control-Allow-Headers": "authorization, content-type",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and validate authentication.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in the chain

        Returns:
            Response from the next handler or authentication error
        """
        # Log EVERY request through this middleware
        logger.info(
            "auth_middleware_dispatch",
            path=request.url.path,
            method=request.method,
        )

        # Optional app-level toggle for test environments (E2E mode)
        # Frontend sends actual test user role via X-E2E-User-Role header
        if getattr(request.app.state, "skip_auth_for_tests", False):
            # Read role from custom header (sent by frontend in E2E test mode)
            # This allows different test users to have different roles
            e2e_role = request.headers.get("X-E2E-User-Role", "planner")
            e2e_email = request.headers.get("X-E2E-User-Email", "test@efir.local")
            e2e_user_id = request.headers.get(
                "X-E2E-User-Id", "00000000-0000-0000-0000-000000000001"
            )

            # Normalize role to lowercase for consistent comparison
            request.state.user_role = e2e_role.lower() if e2e_role else "planner"
            request.state.user_id = e2e_user_id
            request.state.user_email = e2e_email

            logger.info(
                "e2e_auth_bypass",
                path=request.url.path,
                role=request.state.user_role,
                email=e2e_email,
                user_id=e2e_user_id,
            )
            return await call_next(request)

        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip authentication for public path prefixes
        for prefix in self.PUBLIC_PATH_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        # Skip authentication for CORS preflight requests
        # Browser sends OPTIONS requests without Authorization header to check CORS policy
        if request.method == "OPTIONS":
            logger.debug("cors_preflight_request", path=request.url.path)
            return await call_next(request)

        # Try both lowercase and capitalized header names
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

        if not auth_header:
            logger.warning("auth_header_missing", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing"},
                headers=self._get_cors_headers(request),
            )

        # Validate Bearer token format
        if not auth_header.startswith("Bearer "):
            logger.warning("auth_header_invalid_format", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format. Expected: Bearer <token>"},
                headers=self._get_cors_headers(request),
            )

        token = auth_header.split(" ", 1)[1]
        # Debug: Log token preview (safe - only first 20 chars) and segment count
        token_segments = token.count(".")
        token_preview = token[:20] + "..." if len(token) > 20 else token
        logger.info(
            "jwt_token_received",
            path=request.url.path,
            token_length=len(token),
            token_segments=token_segments,
            token_preview=token_preview,
            expected_segments=2,  # JWT has 2 dots = 3 segments
        )

        # Verify JWT token
        payload = verify_supabase_jwt(token)
        if not payload:
            logger.warning("jwt_verification_failed", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
                headers=self._get_cors_headers(request),
            )

        user_id = payload.get("sub")
        if not user_id:
            logger.error("jwt_missing_sub_field", payload_keys=list(payload.keys()))
            return JSONResponse(
                status_code=401,
                content={"detail": "JWT token missing user ID"},
                headers=self._get_cors_headers(request),
            )

        print(f"[AUTH] JWT verified: user_id={user_id}")
        logger.info("jwt_verified", path=request.url.path, user_id=str(user_id))

        # Add user information to request state
        request.state.user_id = user_id
        request.state.user_email = payload.get("email", "")

        # Role can be in multiple locations:
        # 1. Directly in payload (custom JWT claim from hook)
        # 2. In app_metadata.role (Supabase standard - but not in JWT by default!)
        # 3. In user_metadata.role (custom setup)
        app_metadata = payload.get("app_metadata", {})
        user_metadata = payload.get("user_metadata", {})

        # DEBUG: Log all potential role sources
        role_from_payload = payload.get("role")
        role_from_app_meta = app_metadata.get("role")
        role_from_user_meta = user_metadata.get("role")

        logger.info(
            "role_extraction_debug",
            role_from_payload=role_from_payload,
            role_from_app_meta=role_from_app_meta,
            role_from_user_meta=role_from_user_meta,
            app_metadata_keys=list(app_metadata.keys()) if app_metadata else [],
            user_metadata_keys=list(user_metadata.keys()) if user_metadata else [],
        )

        role = role_from_payload or role_from_app_meta or role_from_user_meta

        # If no role in JWT, fetch from database
        # (Supabase doesn't include app_metadata in JWT by default)
        logger.info("role_from_jwt_combined", role=role, will_query_db=not bool(role))
        if not role:
            logger.info("role_db_lookup_starting", user_id=str(user_id))
            try:
                import uuid as uuid_module
                from urllib.parse import urlparse

                import asyncpg

                db_url = os.getenv("DATABASE_URL", "")
                is_sqlite = db_url.startswith("sqlite") if db_url else False
                logger.info(
                    "db_url_check",
                    has_url=bool(db_url),
                    is_sqlite=is_sqlite,
                    url_prefix=db_url[:30] if db_url else "EMPTY",
                )
                if db_url and not db_url.startswith("sqlite"):
                    # Parse database URL, handle async driver prefix
                    clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
                    parsed = urlparse(clean_url)

                    logger.info("db_connecting", host=parsed.hostname, port=parsed.port)
                    conn = await asyncpg.connect(
                        host=parsed.hostname,
                        port=parsed.port or 5432,
                        user=parsed.username,
                        password=parsed.password,
                        database=parsed.path.lstrip("/"),
                        statement_cache_size=0,
                    )
                    logger.info("db_connected_successfully")
                    try:
                        # Convert to UUID for asyncpg
                        if isinstance(user_id, uuid_module.UUID):
                            user_uuid = user_id
                        else:
                            user_uuid = uuid_module.UUID(str(user_id))
                        row = await conn.fetchrow(
                            "SELECT raw_app_meta_data->>'role' as role "
                            "FROM auth.users WHERE id = $1",
                            user_uuid
                        )
                        logger.info("db_query_result", row=str(row), user_uuid=str(user_uuid))
                        if row and row["role"]:
                            role = row["role"]
                            logger.info("role_fetched_from_db", role=role)
                        else:
                            logger.warning(
                                "role_not_found_in_db",
                                user_id=str(user_id),
                                row=str(row),
                            )
                    finally:
                        await conn.close()
                else:
                    logger.warning(
                        "db_lookup_skipped",
                        reason="no_valid_db_url",
                        has_url=bool(db_url),
                        is_sqlite=is_sqlite,
                    )
            except Exception as e:
                logger.warning("role_db_lookup_failed", error=str(e), error_type=type(e).__name__)

        # Default to planner if still no role
        role = role or "planner"

        # Normalize role to lowercase for comparison
        if isinstance(role, str):
            role = role.lower()

        # Set the role in request state - this is what dependencies read
        request.state.user_role = role
        request.state.user_metadata = user_metadata

        logger.info(
            "auth_completed_role_set",
            user_id=str(user_id),
            email=request.state.user_email,
            final_role=role,
            role_source="jwt" if role != "planner" else "default",
        )

        return await call_next(request)
