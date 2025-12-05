"""
Rate limiting middleware for EFIR Budget Planning Application.

Implements sliding window rate limiting using Redis for distributed enforcement.
Provides different rate limits based on endpoint sensitivity and user role.
"""

import os
import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.logging import logger

# Rate limit configuration (requests per window)
RATE_LIMITS = {
    # Default limits (per minute)
    "default": {"requests": 100, "window": 60},
    # Strict limits for expensive operations
    "calculations": {"requests": 30, "window": 60},
    "consolidation": {"requests": 20, "window": 60},
    "export": {"requests": 10, "window": 60},
    # Relaxed limits for read operations
    "read": {"requests": 200, "window": 60},
}

# Role-based multipliers (higher = more requests allowed)
ROLE_MULTIPLIERS = {
    "admin": 3.0,
    "finance_director": 2.0,
    "hr": 1.5,
    "academic": 1.5,
    "viewer": 1.0,
}

# Paths that map to rate limit categories
PATH_CATEGORIES = {
    "/api/v1/calculations/": "calculations",
    "/api/v1/consolidation/": "consolidation",
    "/api/v1/analysis/export": "export",
    "/api/v1/planning/": "default",
    "/api/v1/configuration/": "read",
    "/health": "read",
}

# Environment flag to enable/disable rate limiting
_testing = os.getenv("PYTEST_CURRENT_TEST") is not None
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true" and not _testing
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true" and not _testing


def get_client_identifier(request: Request) -> str:
    """
    Get unique client identifier for rate limiting.

    Uses authenticated user ID if available, otherwise falls back to IP address.

    Args:
        request: FastAPI request object

    Returns:
        Client identifier string
    """
    # Use authenticated user_id from auth middleware
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"

    return f"ip:{request.client.host if request.client else 'unknown'}"


def get_rate_limit_category(path: str) -> str:
    """
    Determine rate limit category for a request path.

    Args:
        path: Request path

    Returns:
        Rate limit category name
    """
    for prefix, category in PATH_CATEGORIES.items():
        if path.startswith(prefix):
            return category
    return "default"


def get_user_role(request: Request) -> str:
    """
    Get user role from request state.

    Args:
        request: FastAPI request object

    Returns:
        User role string or "viewer" as default
    """
    role = getattr(request.state, "user_role", None)
    if isinstance(role, str) and role:
        return role.lower()

    user = getattr(request.state, "user", None)
    if user and hasattr(user, "role"):
        return user.role.lower()

    return "viewer"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    Features:
    - Redis-backed for distributed rate limiting
    - Role-based rate limit multipliers
    - Path-based rate limit categories
    - Graceful degradation when Redis unavailable
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or 429 Too Many Requests
        """
        # Skip if rate limiting disabled or flagged off for this app
        if (
            getattr(request.app.state, "skip_rate_limit_for_tests", False)
            or not RATE_LIMIT_ENABLED
            or os.getenv("DISABLE_RATE_LIMITING", "false").lower() == "true"
        ):
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/ready", "/health/live"]:
            return await call_next(request)

        # Get rate limit parameters
        client_id = get_client_identifier(request)
        category = get_rate_limit_category(request.url.path)
        user_role = get_user_role(request)

        # Calculate effective rate limit
        base_limit = RATE_LIMITS.get(category, RATE_LIMITS["default"])
        multiplier = ROLE_MULTIPLIERS.get(user_role, 1.0)
        max_requests = int(base_limit["requests"] * multiplier)
        window = base_limit["window"]

        # Check rate limit
        is_allowed, current_count, reset_time = await self._check_rate_limit(
            client_id=client_id,
            category=category,
            max_requests=max_requests,
            window=window,
        )

        if not is_allowed:
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                category=category,
                current_count=current_count,
                max_requests=max_requests,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": reset_time,
                    "limit": max_requests,
                    "window": window,
                },
                headers={
                    "Retry-After": str(reset_time),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_time),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - current_count))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_time)

        return response

    async def _check_rate_limit(
        self,
        client_id: str,
        category: str,
        max_requests: int,
        window: int,
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit using sliding window.

        Args:
            client_id: Unique client identifier
            category: Rate limit category
            max_requests: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, current_count, seconds_until_reset)
        """
        if not REDIS_ENABLED:
            # Graceful degradation: allow all requests if Redis unavailable
            return True, 0, window

        try:
            from app.core.cache import get_redis_client

            client = await get_redis_client()
            key = f"rate_limit:{category}:{client_id}"
            now = int(time.time())

            # Use Redis pipeline for atomic operations
            async with client.pipeline(transaction=True) as pipe:
                # Remove expired entries
                pipe.zremrangebyscore(key, 0, now - window)
                # Add current request
                pipe.zadd(key, {str(now): now})
                # Count requests in window
                pipe.zcard(key)
                # Set expiry on key
                pipe.expire(key, window)
                results = await pipe.execute()

            current_count = results[2]
            reset_time = window - (now % window)

            is_allowed = current_count <= max_requests
            return is_allowed, current_count, reset_time

        except Exception as e:
            logger.error("rate_limit_check_failed", error=str(e), client_id=client_id)
            # Graceful degradation: allow request on error
            return True, 0, window


def rate_limit(
    requests: int = 100,
    window: int = 60,
    key_func: Callable[[Request], str] | None = None,
) -> Callable:
    """
    Decorator for endpoint-specific rate limiting.

    Args:
        requests: Maximum requests allowed
        window: Time window in seconds
        key_func: Optional custom function to generate rate limit key

    Returns:
        Decorator function

    Example:
        @router.post("/calculate")
        @rate_limit(requests=10, window=60)
        async def calculate(request: Request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find request in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            if request is None:
                return await func(*args, **kwargs)

            # Get client identifier
            if key_func:
                client_id = key_func(request)
            else:
                client_id = get_client_identifier(request)

            # Check rate limit
            middleware = RateLimitMiddleware(None)  # type: ignore
            is_allowed, _current_count, reset_time = await middleware._check_rate_limit(
                client_id=client_id,
                category="decorator",
                max_requests=requests,
                window=window,
            )

            if not is_allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": reset_time,
                    },
                    headers={"Retry-After": str(reset_time)},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
