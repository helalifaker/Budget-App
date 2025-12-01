"""
EFIR Budget Planning Application - Main FastAPI Application.

This is the entry point for the FastAPI backend server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import configuration, costs_router, planning
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.rbac import RBACMiddleware
from app.routes import health


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

    # CORS middleware
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

    # Authentication middleware (validates JWT tokens)
    app.add_middleware(AuthenticationMiddleware)

    # RBAC middleware (enforces role-based access control)
    app.add_middleware(RBACMiddleware)

    # Include routers
    app.include_router(health.router)
    app.include_router(configuration.router)
    app.include_router(planning.router)
    app.include_router(costs_router)

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
