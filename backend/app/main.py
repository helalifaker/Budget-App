"""
EFIR Budget Planning Application - Main FastAPI Application.

This is the entry point for the FastAPI backend server.
"""

import asyncio
import os
import sys
import traceback

import httpx
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy import text

from app.api.v1 import (
    analysis_router,
    calculations_router,
    configuration_router,
    consolidation_router,
    costs_router,
    export_router,
    planning_router,
    writeback_router,
)
from app.core.cache import initialize_cache, validate_redis_config
from app.core.logging import LoggingMiddleware, logger
from app.database import DATABASE_URL, engine, init_db
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.metrics import RequestMetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.routes import health

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
    # Auto-enable test bypass during pytest runs, otherwise use env var (default: false)
    is_pytest = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
    skip_auth_env = os.getenv("SKIP_AUTH_FOR_TESTS", "false").lower() == "true"
    app.state.skip_auth_for_tests = is_pytest or skip_auth_env
    skip_rate_limit_env = os.getenv("SKIP_RATE_LIMIT_FOR_TESTS", "false").lower() == "true"
    app.state.skip_rate_limit_for_tests = is_pytest or skip_rate_limit_env

    # Debug: Print environment variable status on startup
    supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
    supabase_url = os.getenv("SUPABASE_URL", "")
    print("=" * 60)
    print("[STARTUP] Environment Variables Status:")
    print(f"  SUPABASE_JWT_SECRET configured: {bool(supabase_jwt_secret)}")
    print(f"  SUPABASE_JWT_SECRET length: {len(supabase_jwt_secret) if supabase_jwt_secret else 0}")
    print(f"  SUPABASE_URL: {supabase_url or 'NOT SET'}")
    if supabase_url:
        print(f"  Expected issuer: {supabase_url.rstrip('/')}/auth/v1")
    print("=" * 60)

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

    # Include routers
    app.include_router(health.router)
    app.include_router(calculations_router)
    app.include_router(configuration_router)
    app.include_router(planning_router)
    app.include_router(costs_router)
    app.include_router(analysis_router)
    app.include_router(consolidation_router)
    app.include_router(writeback_router)
    app.include_router(export_router)

    return app


app = create_app()


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
    """
    print("\n" + "="*80)
    print("GLOBAL EXCEPTION HANDLER CAUGHT AN ERROR!")
    print("="*80)
    print(f"Exception Type: {type(exc).__name__}")
    print(f"Exception Message: {exc!s}")
    print(f"\nRequest URL: {request.url}")
    print(f"Request Method: {request.method}")
    print(f"Request Headers: {dict(request.headers)}")
    print("\nFull Stack Trace:")
    print("-"*80)
    traceback.print_exc()
    print("-"*80)
    print("="*80 + "\n")

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

    # 4. Initialize Redis cache
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

    # 5. Check Supabase Auth API (non-blocking)
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
