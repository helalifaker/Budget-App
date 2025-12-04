"""
EFIR Budget Planning Application - Main FastAPI Application.

This is the entry point for the FastAPI backend server.
"""

import os
import sys

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

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
from app.core.logging import LoggingMiddleware
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.metrics import RequestMetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.rbac import RBACMiddleware
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
    app.add_middleware(RBACMiddleware)

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
