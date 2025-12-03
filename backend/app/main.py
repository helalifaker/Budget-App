"""
EFIR Budget Planning Application - Main FastAPI Application.

This is the entry point for the FastAPI backend server.
"""

import os

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
    integrations_router,
    planning_router,
    writeback_router,
)
from app.core.logging import LoggingMiddleware
from app.middleware.auth import AuthenticationMiddleware
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

    # Rate limiting middleware (prevents abuse)
    app.add_middleware(RateLimitMiddleware)

    # RBAC middleware (enforces role-based access control)
    app.add_middleware(RBACMiddleware)

    # Authentication middleware (validates JWT tokens)
    app.add_middleware(AuthenticationMiddleware)

    # CORS middleware should wrap authentication so preflight checks hit it first
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative dev port
            "https://*.vercel.app",   # Vercel deployments
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    app.include_router(integrations_router)
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
