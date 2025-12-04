"""
Request metrics middleware.

Adds a simple Prometheus counter for HTTP requests.
"""

import re

from prometheus_client import Counter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Counter with method/path/status labels for future expansion
HTTP_REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the API",
    ["method", "path", "status"],
)


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to increment HTTP request counter."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        try:
            path = self._normalize_path(request.url.path)
            HTTP_REQUEST_COUNTER.labels(
                method=request.method,
                path=path,
                status=str(response.status_code),
            ).inc()
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
