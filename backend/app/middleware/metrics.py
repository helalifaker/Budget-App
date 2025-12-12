"""
Request metrics middleware.

Provides:
1. HTTP request counter (Prometheus)
2. Request duration histogram (Prometheus)
3. Request timing header (X-Request-Time-Ms)
4. Slow request logging (>1s)

Phase 12 Performance: Added timing metrics for observability
"""

import re
import time

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import logger

# Counter with method/path/status labels for future expansion
HTTP_REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the API",
    ["method", "path", "status"],
)

# Histogram for request duration tracking
# Buckets optimized for API latency: 10ms to 30s
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# Threshold for slow request logging (in seconds)
SLOW_REQUEST_THRESHOLD = 1.0


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP request metrics and timing.

    Features:
    - Increments request counter (method/path/status)
    - Records request duration histogram
    - Adds X-Request-Time-Ms header to responses
    - Logs slow requests (>1s) for investigation
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Start timing
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.perf_counter() - start_time
        duration_ms = round(duration * 1000, 2)

        try:
            path = self._normalize_path(request.url.path)

            # Increment request counter
            HTTP_REQUEST_COUNTER.labels(
                method=request.method,
                path=path,
                status=str(response.status_code),
            ).inc()

            # Record duration histogram
            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                path=path,
            ).observe(duration)

            # Add timing header for frontend debugging
            response.headers["X-Request-Time-Ms"] = str(duration_ms)

            # Log slow requests
            if duration > SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    "slow_request",
                    method=request.method,
                    path=request.url.path,
                    duration_ms=duration_ms,
                    status=response.status_code,
                )

        except Exception:
            # Metrics should never break the request flow
            pass

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Reduce cardinality by masking UUIDs and numeric path segments.
        """
        # Mask UUID-like tokens
        masked = re.sub(
            r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            "/{id}",
            path,
        )
        # Mask pure numeric segments
        masked = re.sub(r"/[0-9]+", "/{id}", masked)
        return masked
