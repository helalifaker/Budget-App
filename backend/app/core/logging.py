"""
Structured logging configuration using structlog.

This module configures structured logging with JSON output for production,
correlation IDs for request tracing, and proper log level management.
"""

import logging
import uuid
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def configure_logging() -> structlog.BoundLogger:
    """
    Configure structlog with production-grade settings.

    Returns:
        Configured structlog logger instance
    """
    # Configure stdlib logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
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
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
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

        # Bind correlation ID and request metadata to context
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
            client_host=request.client.host if request.client else None,
        )

        # Log request start
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

            # Log successful completion
            logger.info(
                "request_completed",
                status_code=response.status_code,
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Log request failure
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
