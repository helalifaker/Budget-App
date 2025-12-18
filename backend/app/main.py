"""
EFIR Budget Planning Application - Main FastAPI Application.

This is the entry point for the FastAPI backend server.
"""

import asyncio
import errno
import os
from typing import Any

import httpx
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy import text

from app.api.v1 import (
    admin_router,
    analysis_router,
    calculations_router,
    capex_router,
    class_structure_router,
    class_structure_router,
    configuration_router,
    consolidation_router,
    costs_router,
    dhg_router,
    distributions_router,
    enrollment_router,
    enrollment_projection_router,
    enrollment_settings_router,
    export_router,
    historical_router,
    impact_router,
    orchestration_router,
    organization_router,
    revenue_router,
    strategic_router,
    workforce_router,
    writeback_router,
)
from app.core.cache import initialize_cache, validate_redis_config
from app.core.logging import LoggingMiddleware, logger
from app.database import DATABASE_URL, engine, init_db
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.metrics import RequestMetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.routes import health
from app.services.exceptions import ServiceException

# =============================================================================
# Sentry Error Filtering
# =============================================================================
# These errors are transient/expected and should not be reported to Sentry:
# - CancelledError: Client disconnected before response (normal browser behavior)
# - BrokenPipeError: Client closed connection (errno 32)
# - ConnectionResetError: Connection reset by peer
# - ConnectionAbortedError: Connection aborted by client
# - TimeoutError from asyncio: Request cancelled due to client disconnect

SENTRY_IGNORED_EXCEPTIONS = (
    "CancelledError",
    "BrokenPipeError",
    "ConnectionResetError",
    "ConnectionAbortedError",
)


def sentry_before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """
    Filter out transient errors before sending to Sentry.

    These errors are expected behavior and not actionable:
    - Client disconnects (CancelledError, BrokenPipe, ConnectionReset)
    - These create noise in Sentry without providing debugging value

    Returns:
        event dict to send, or None to drop the event
    """
    if "exc_info" in hint:
        exc_type, exc_value, _ = hint["exc_info"]
        exc_name = exc_type.__name__

        # Filter out known transient exceptions
        if exc_name in SENTRY_IGNORED_EXCEPTIONS:
            return None

        # Also filter asyncio.CancelledError (different module path)
        if exc_name == "CancelledError":
            return None

        # Filter OSError with errno 32 (EPIPE - Broken pipe)
        if isinstance(exc_value, OSError) and getattr(exc_value, "errno", None) == errno.EPIPE:
            return None

        # Filter "connection was closed" errors from asyncpg
        exc_message = str(exc_value).lower()
        if "connection was closed" in exc_message:
            return None
        if "cancelled" in exc_message and "cancel scope" in exc_message:
            return None

    return event


# Initialize Sentry before FastAPI app creation
if os.getenv("SENTRY_DSN_BACKEND"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN_BACKEND"),
        environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=0.1,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        release=os.getenv("GIT_COMMIT_SHA", "dev"),
        # Enable performance monitoring
        enable_tracing=True,
        # Send default PII (Personally Identifiable Information)
        send_default_pii=False,
        # Filter out transient/expected errors
        before_send=sentry_before_send,  # type: ignore[arg-type]
    )


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="EFIR Budget Planning API",
        version="0.1.0",
        description="REST API for EFIR School Budget Planning Application",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    # Test bypass: ONLY enable when explicitly requested via environment variables
    # NOTE: We intentionally do NOT check "pytest" in sys.modules because:
    # - IDEs (VSCode) pre-load pytest for test discovery
    # - This caused all production auth to be bypassed (role="planner" for everyone)
    # Instead, conftest.py sets PYTEST_RUNNING=1 explicitly during test runs
    is_pytest_running = os.getenv("PYTEST_RUNNING", "").lower() in ("1", "true")
    is_pytest_current_test = os.getenv("PYTEST_CURRENT_TEST") is not None
    skip_auth_env = os.getenv("SKIP_AUTH_FOR_TESTS", "false").lower() == "true"
    app.state.skip_auth_for_tests = is_pytest_running or is_pytest_current_test or skip_auth_env

    skip_rate_limit_env = os.getenv("SKIP_RATE_LIMIT_FOR_TESTS", "false").lower() == "true"
    app.state.skip_rate_limit_for_tests = (
        is_pytest_running or is_pytest_current_test or skip_rate_limit_env
    )

    # Log the auth bypass status for debugging
    logger.info(
        "auth_bypass_config",
        skip_auth_for_tests=app.state.skip_auth_for_tests,
        is_pytest_running=is_pytest_running,
        is_pytest_current_test=is_pytest_current_test,
        skip_auth_env=skip_auth_env,
    )

    # Log environment variable status on startup (structured logging)
    supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
    supabase_url = os.getenv("SUPABASE_URL", "")
    logger.info(
        "startup_config",
        jwt_configured=bool(supabase_jwt_secret),
        jwt_secret_length=len(supabase_jwt_secret) if supabase_jwt_secret else 0,
        supabase_url=supabase_url or "NOT SET",
    )

    # CORS middleware should wrap authentication so preflight checks hit it first
    # Get allowed origins from environment variable, with sensible defaults
    allowed_origins_str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000"
    )
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

    # Add production domain if configured
    production_domain = os.getenv("PRODUCTION_FRONTEND_URL")
    if production_domain and production_domain not in allowed_origins:
        allowed_origins.append(production_domain)

    # Always allow Vercel deployments for staging
    if "https://*.vercel.app" not in allowed_origins:
        allowed_origins.append("https://*.vercel.app")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # RBAC middleware (enforces role-based access control)
    # TEMPORARILY DISABLED FOR DEBUGGING
    # app.add_middleware(RBACMiddleware)

    # Authentication middleware (validates JWT tokens)
    app.add_middleware(AuthenticationMiddleware)

    # Rate limiting middleware (protects against abuse)
    # Only enable in production or when explicitly configured
    if os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true":
        app.add_middleware(RateLimitMiddleware)

    # Metrics middleware (increments Prometheus counter)
    app.add_middleware(RequestMetricsMiddleware)

    # Logging middleware (adds correlation IDs and structured logging)
    # Must be added last so it wraps every request once the stack is built
    app.add_middleware(LoggingMiddleware)

    # Include routers under /api/v1 prefix
    from fastapi import APIRouter
    v1_router = APIRouter(prefix="/api/v1")

    v1_router.include_router(admin_router)
    v1_router.include_router(calculations_router)
    v1_router.include_router(capex_router)
    v1_router.include_router(class_structure_router)
    v1_router.include_router(configuration_router)
    v1_router.include_router(costs_router)
    v1_router.include_router(dhg_router)
    v1_router.include_router(distributions_router)
    v1_router.include_router(analysis_router)
    v1_router.include_router(consolidation_router)
    v1_router.include_router(strategic_router)
    v1_router.include_router(workforce_router)
    v1_router.include_router(writeback_router)
    v1_router.include_router(export_router)
    v1_router.include_router(historical_router)
    v1_router.include_router(enrollment_settings_router)
    v1_router.include_router(enrollment_router)
    v1_router.include_router(enrollment_projection_router)
    v1_router.include_router(impact_router)
    v1_router.include_router(orchestration_router)
    v1_router.include_router(organization_router)
    v1_router.include_router(revenue_router)
    
    # Mount the v1 router
    app.include_router(v1_router)

    # Health check remains at root for infrastructure monitoring
    app.include_router(health.router)

    return app


app = create_app()


# Client disconnect errors - expected behavior, not application errors
# These occur when clients close connections before server responds (e.g., CORS preflight)
CLIENT_DISCONNECT_ERRORS = (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)


def is_client_disconnect_error(exc: Exception) -> bool:
    """
    Check if exception is due to client disconnecting.

    These are expected behaviors, not application errors:
    - BrokenPipeError: Client closed connection (errno 32)
    - ConnectionResetError: Connection reset by peer
    - ConnectionAbortedError: Connection aborted

    Returns:
        True if this is a client disconnect error that should be silently ignored
    """
    if isinstance(exc, CLIENT_DISCONNECT_ERRORS):
        return True
    # Also check for OSError with errno 32 (EPIPE - Broken pipe)
    if isinstance(exc, OSError) and getattr(exc, "errno", None) == errno.EPIPE:
        return True
    return False


# Service-layer exceptions: return structured error with correct status code
@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    """
    Handle service-layer exceptions with their declared HTTP status codes.

    IMPORTANT: Explicitly adds CORS headers to ensure browser can read error responses.
    """
    origin = request.headers.get("origin", "*")

    allowed_origins_str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )
    allowed_origins = [o.strip() for o in allowed_origins_str.split(",")]

    production_domain = os.getenv("PRODUCTION_FRONTEND_URL")
    if production_domain:
        allowed_origins.append(production_domain)
    if "https://*.vercel.app" not in allowed_origins:
        allowed_origins.append("https://*.vercel.app")

    is_allowed = origin in allowed_origins or "*" in allowed_origins
    cors_origin = origin if is_allowed else allowed_origins[0]

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_type": type(exc).__name__,
            "details": exc.details,
        },
        headers={
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
            "Access-Control-Allow-Headers": "authorization, content-type",
        },
    )


# Global exception handler to catch and log all exceptions with full stack trace
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that catches ALL exceptions.

    This handler provides detailed debugging information including:
    - Full stack trace
    - Request details
    - Exception type and message

    IMPORTANT: Explicitly adds CORS headers to ensure browser can read error responses.

    Client disconnect errors (BrokenPipeError, ConnectionResetError) are silently
    ignored as they are expected behavior when clients close connections early.
    """
    # Silently ignore client disconnect errors - these are expected behavior
    # Client already disconnected, so we can't send a meaningful response anyway
    if is_client_disconnect_error(exc):
        # Return HTTP 499 (Client Closed Request) - nginx convention
        # This helps distinguish client-side disconnects from server errors in monitoring
        return Response(status_code=499)

    # Log the exception with structured data
    logger.error(
        "unhandled_exception",
        exc_info=True,
        error_type=type(exc).__name__,
        error_message=str(exc),
        request_url=str(request.url),
        request_method=request.method,
    )

    # Get the origin from the request headers for CORS
    origin = request.headers.get("origin", "*")

    # Validate origin against allowed origins
    allowed_origins_str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000"
    )
    allowed_origins = [o.strip() for o in allowed_origins_str.split(",")]

    # Add production and Vercel origins
    production_domain = os.getenv("PRODUCTION_FRONTEND_URL")
    if production_domain:
        allowed_origins.append(production_domain)
    if "https://*.vercel.app" not in allowed_origins:
        allowed_origins.append("https://*.vercel.app")

    # Check if origin is allowed (or use * for wildcard patterns)
    is_allowed = origin in allowed_origins or "*" in allowed_origins
    cors_origin = origin if is_allowed else allowed_origins[0]

    # Return error response with explicit CORS headers
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {type(exc).__name__}: {exc!s}",
            "error_type": type(exc).__name__,
        },
        headers={
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
            "Access-Control-Allow-Headers": "authorization, content-type",
        },
    )


@app.on_event("startup")
async def startup_event():
    """Initialize services and run health checks before accepting requests."""
    logger.info("application_startup_begin")

    # 1. Validate Redis configuration
    config_errors = validate_redis_config()
    if config_errors:
        logger.warning("redis_config_validation_failed", errors=config_errors)
        if os.getenv("REDIS_REQUIRED", "false").lower() == "true":
            raise ValueError(f"Invalid Redis configuration: {'; '.join(config_errors)}")

    # 2. Initialize database schema for SQLite
    # For PostgreSQL, use Alembic migrations instead
    if DATABASE_URL.startswith("sqlite"):
        try:
            await init_db()
            logger.info("database_schema_initialized", database="SQLite")
        except Exception as exc:
            logger.error(
                "database_schema_initialization_failed",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

    # 3. Check database connectivity
    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=10.0,
            )
        db_type = "SQLite" if DATABASE_URL.startswith("sqlite") else "Supabase PostgreSQL"
        logger.info("database_health_check_success", host=db_type)
    except TimeoutError:
        logger.error("database_health_check_timeout", timeout=10.0)
    except Exception as exc:
        logger.error(
            "database_health_check_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )

    # 4. Load in-memory reference data cache
    # This caches immutable data (cycles, levels, scenarios) for zero-latency lookups
    # Performance impact: -200-300ms per calculation
    try:
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.core.reference_cache import reference_cache

        async with AsyncSession(engine) as session:
            await reference_cache.load(session)
        logger.info("reference_cache_initialization_success")
    except Exception as exc:
        logger.warning(
            "reference_cache_initialization_failed",
            error=str(exc),
            message="Application will fallback to database queries",
        )
        # Don't raise - this is a performance optimization, not a requirement

    # 5. Initialize Redis cache
    try:
        cache_initialized = await initialize_cache()
        if cache_initialized:
            logger.info("cache_initialization_success")
        else:
            logger.warning(
                "cache_disabled_or_unavailable",
                message="Application will run with degraded caching",
            )
    except Exception as exc:
        logger.error("cache_initialization_failed_critical", error=str(exc))
        raise  # Re-raise if REDIS_REQUIRED=true

    # 6. Check Supabase Auth API (non-blocking)
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{supabase_url}/auth/v1/health")
                logger.info("supabase_auth_check_success", status=response.status_code)
        except Exception as exc:
            logger.warning(
                "supabase_auth_check_failed",
                error=str(exc),
                message="Auth endpoints may be unavailable",
            )

    logger.info("application_startup_complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    logger.info("application_shutdown_begin")

    # Close Redis client
    try:
        from app.core.cache import close_redis_client

        await close_redis_client()
        logger.info("redis_client_closed")
    except Exception as exc:
        logger.warning("redis_client_close_failed", error=str(exc))

    logger.info("application_shutdown_complete")


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Welcome message with API information
    """
    return {
        "message": "EFIR Budget Planning API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
