"""
Structured logging configuration using structlog.

This module configures structured logging with JSON output for production,
correlation IDs for request tracing, and proper log level management.

Configuration via environment variables:
    LOG_LEVEL: Set logging verbosity (DEBUG, INFO, WARNING, ERROR). Default: INFO
    LOG_HEALTH_CHECKS: Set to "true" to log health check requests. Default: false
"""

import errno
import logging
import os
import uuid
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Environment configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_HEALTH_CHECKS = os.getenv("LOG_HEALTH_CHECKS", "false").lower() == "true"

# Map string log levels to logging constants
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Get numeric log level (default to INFO if invalid)
NUMERIC_LOG_LEVEL = LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO)

# Health check paths to optionally filter from logs
HEALTH_CHECK_PATHS = frozenset({
    "/",
    "/health",
    "/health/",
    "/health/live",
    "/health/ready",
})

# Client disconnect errors - expected behavior, not application errors
# These occur when clients close connections before server responds
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


def configure_logging() -> structlog.BoundLogger:
    """
    Configure structlog with production-grade settings.

    Respects LOG_LEVEL environment variable (DEBUG, INFO, WARNING, ERROR).
    Default is INFO for clean terminal output.

    Returns:
        Configured structlog logger instance
    """
    # Configure stdlib logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        level=NUMERIC_LOG_LEVEL,
    )

    # Configure structlog processors
    structlog.configure(
        processors=[
            # Add context variables (correlation_id, request path, etc.)
            structlog.contextvars.merge_contextvars,
            # Add log level
            structlog.processors.add_log_level,
            # Add timestamp in ISO format
            structlog.processors.TimeStamper(fmt="iso"),
            # Add exception info
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Render as JSON for structured logging
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(NUMERIC_LOG_LEVEL),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


# Global logger instance
logger = configure_logging()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for request/response logging with correlation IDs.

    Adds a unique correlation ID to each request and logs request start/completion.
    The correlation ID is returned in the X-Correlation-ID response header.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process request with correlation ID and logging.

        Args:
            request: FastAPI request object
            call_next: Next middleware in chain

        Returns:
            Response with X-Correlation-ID header
        """
        # Generate unique correlation ID for this request
        correlation_id = str(uuid.uuid4())

        # Check if this is a health check (skip logging if LOG_HEALTH_CHECKS=false)
        is_health_check = request.url.path in HEALTH_CHECK_PATHS
        should_log = LOG_HEALTH_CHECKS or not is_health_check

        # Bind correlation ID and request metadata to context
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
            client_host=request.client.host if request.client else None,
        )

        # Log request start (skip for health checks if disabled)
        if should_log:
            logger.info(
                "request_started",
                user_agent=request.headers.get("user-agent"),
                content_type=request.headers.get("content-type"),
            )

        try:
            # Process request
            response = await call_next(request)

            # Tests may return mock responses; normalize to Response to avoid shared state
            if not isinstance(response, Response):
                response = Response(
                    content=getattr(response, "body", b""),
                    status_code=getattr(response, "status_code", 200),
                    headers=dict(getattr(response, "headers", {})),
                )

            # Log successful completion (skip for health checks if disabled)
            if should_log:
                logger.info(
                    "request_completed",
                    status_code=response.status_code,
                )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Don't log client disconnect errors as failures - they're expected behavior
            # when clients close connections before server responds (e.g., CORS preflight)
            if not is_client_disconnect_error(exc):
                logger.error(
                    "request_failed",
                    exc_info=True,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            raise

        finally:
            # Clear context variables after request
            structlog.contextvars.clear_contextvars()
