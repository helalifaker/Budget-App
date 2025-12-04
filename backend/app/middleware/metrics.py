"""
Request metrics middleware.

Adds a simple Prometheus counter for HTTP requests.
"""

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
            HTTP_REQUEST_COUNTER.labels(
                method=request.method,
                path=request.url.path,
                status=str(response.status_code),
            ).inc()
        except Exception:
            # Metrics should never break the request flow
            pass
        return response
