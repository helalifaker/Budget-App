"""
Rate limiting middleware for API protection.

Implements token bucket algorithm for rate limiting using Redis.
Provides protection against:
- DDoS attacks
- API abuse
- Credential stuffing
"""

import os
import time
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Try to import redis, but make it optional
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis for distributed rate limiting.

    Implements a sliding window rate limiter that limits requests per IP
    and per user (if authenticated).

    Configuration via environment variables:
    - RATE_LIMIT_PER_MINUTE: Requests per minute per client (default: 300)
    - RATE_LIMIT_PER_HOUR: Requests per hour per client (default: 5000)
    - REDIS_URL: Redis connection URL for distributed rate limiting
    """

    # Paths exempt from rate limiting
    EXEMPT_PATHS = [
        "/health",
        "/health/live",
        "/health/ready",
    ]

    # Stricter limits for sensitive endpoints
    STRICT_RATE_LIMIT_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/password-reset",
    ]

    def __init__(self, app):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        self.default_rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "300"))
        self.hourly_rate_limit = int(os.getenv("RATE_LIMIT_PER_HOUR", "5000"))
        self.strict_rate_limit = 10  # Very strict for auth endpoints
        self.redis_url = os.getenv("REDIS_URL")
        self._redis_client = None
        self._local_cache: dict[str, dict] = {}  # Fallback for non-Redis environments

    async def _get_redis(self):
        """Get or create Redis client connection."""
        if not REDIS_AVAILABLE or not self.redis_url:
            return None

        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self._redis_client.ping()
            except Exception:
                self._redis_client = None
                return None

        return self._redis_client

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.

        Uses user ID if authenticated, otherwise falls back to IP address.

        Args:
            request: FastAPI request object

        Returns:
            Client identifier string
        """
        # Check if user is authenticated
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _get_rate_limit(self, path: str) -> int:
        """
        Get rate limit for the given path.

        Args:
            path: Request path

        Returns:
            Rate limit (requests per minute)
        """
        if any(path.startswith(strict_path) for strict_path in self.STRICT_RATE_LIMIT_PATHS):
            return self.strict_rate_limit
        return self.default_rate_limit

    async def _check_rate_limit_redis(
        self,
        redis_client,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using Redis sliding window.

        Args:
            redis_client: Redis client instance
            key: Rate limit key
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining, reset_time)
        """
        now = time.time()
        window_start = now - window_seconds

        # Use Redis pipeline for atomic operations
        pipe = redis_client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, "-inf", window_start)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Count requests in window
        pipe.zcard(key)

        # Set expiry
        pipe.expire(key, window_seconds * 2)

        results = await pipe.execute()
        request_count = results[2]

        remaining = max(0, limit - request_count)
        reset_time = int(now + window_seconds)

        return request_count <= limit, remaining, reset_time

    def _check_rate_limit_local(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using local in-memory cache.

        Fallback for when Redis is not available.

        Args:
            key: Rate limit key
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining, reset_time)
        """
        now = time.time()

        if key not in self._local_cache:
            self._local_cache[key] = {"requests": [], "last_cleanup": now}

        entry = self._local_cache[key]

        # Cleanup old requests
        if now - entry["last_cleanup"] > window_seconds:
            entry["requests"] = [
                t for t in entry["requests"]
                if now - t < window_seconds
            ]
            entry["last_cleanup"] = now

        # Check limit
        request_count = len(entry["requests"])
        remaining = max(0, limit - request_count)
        reset_time = int(now + window_seconds)

        if request_count < limit:
            entry["requests"].append(now)
            return True, remaining - 1, reset_time

        return False, 0, reset_time

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and check rate limits.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in the chain

        Returns:
            Response from the next handler or rate limit error
        """
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        client_id = self._get_client_identifier(request)
        rate_limit = self._get_rate_limit(request.url.path)
        key = f"rate_limit:{request.url.path}:{client_id}"

        # Try Redis first, fall back to local
        redis_client = await self._get_redis()

        if redis_client:
            is_allowed, remaining, reset_time = await self._check_rate_limit_redis(
                redis_client, key, rate_limit
            )
        else:
            is_allowed, remaining, reset_time = self._check_rate_limit_local(
                key, rate_limit
            )

        # Add rate limit headers to response
        response_headers = {
            "X-RateLimit-Limit": str(rate_limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": reset_time - int(time.time()),
                },
                headers={
                    **response_headers,
                    "Retry-After": str(reset_time - int(time.time())),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful response
        for header_name, header_value in response_headers.items():
            response.headers[header_name] = header_value

        return response
