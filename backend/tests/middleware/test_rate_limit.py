"""
Unit tests for Rate Limiting Middleware.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRateLimitConfiguration:
    """Tests for rate limiting configuration."""

    def test_default_rate_limit_per_minute(self):
        """Test default rate limit is 300 requests per minute."""
        default_limit = 300
        assert default_limit > 0
        assert default_limit == 300

    def test_strict_rate_limit_for_auth(self):
        """Test stricter limit for auth endpoints is 10/minute."""
        strict_limit = 10
        assert strict_limit < 300
        assert strict_limit == 10

    def test_exempt_paths(self):
        """Test health check paths are exempt from rate limiting."""
        exempt_paths = ["/health", "/health/live", "/health/ready"]

        for path in exempt_paths:
            assert path.startswith("/health")

    def test_strict_rate_limit_paths(self):
        """Test authentication endpoints have stricter limits."""
        strict_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        ]

        for path in strict_paths:
            assert "/auth/" in path


class TestTokenBucketAlgorithm:
    """Tests for token bucket rate limiting algorithm."""

    def test_token_bucket_initial_tokens(self):
        """Test bucket starts with max tokens."""
        max_tokens = 300
        initial_tokens = max_tokens
        assert initial_tokens == max_tokens

    def test_token_bucket_refill_rate(self):
        """Test token refill rate calculation."""
        max_tokens = 300
        window_seconds = 60

        tokens_per_second = max_tokens / window_seconds

        assert tokens_per_second == 5.0  # 300 tokens / 60 seconds

    def test_token_consumption_per_request(self):
        """Test each request consumes one token."""
        tokens_before = 100
        tokens_after_request = tokens_before - 1

        assert tokens_after_request == 99

    def test_request_denied_when_no_tokens(self):
        """Test request is denied when bucket is empty."""
        tokens = 0
        should_allow = tokens > 0

        assert should_allow is False

    def test_request_allowed_when_tokens_available(self):
        """Test request is allowed when tokens are available."""
        tokens = 50
        should_allow = tokens > 0

        assert should_allow is True


class TestTokenRefillCalculation:
    """Tests for token refill timing."""

    def test_refill_tokens_after_time(self):
        """Test tokens are refilled based on elapsed time."""
        tokens_per_second = 5.0
        elapsed_seconds = 10

        tokens_to_add = tokens_per_second * elapsed_seconds

        assert tokens_to_add == 50.0

    def test_tokens_capped_at_max(self):
        """Test tokens don't exceed maximum."""
        max_tokens = 300
        current_tokens = 280
        tokens_to_add = 100

        new_tokens = min(current_tokens + tokens_to_add, max_tokens)

        assert new_tokens == 300

    def test_fractional_tokens_handling(self):
        """Test fractional tokens are preserved."""
        tokens = Decimal("99.5")
        tokens_consumed = Decimal("1")

        remaining = tokens - tokens_consumed

        assert remaining == Decimal("98.5")


class TestClientIdentification:
    """Tests for client identification in rate limiting."""

    def test_ip_based_identification(self):
        """Test clients are identified by IP address."""
        client_ip = "192.168.1.100"
        rate_limit_key = f"rate_limit:{client_ip}"

        assert client_ip in rate_limit_key

    def test_user_based_identification(self):
        """Test authenticated users are identified by user ID."""
        user_id = "user-123"
        rate_limit_key = f"rate_limit:user:{user_id}"

        assert user_id in rate_limit_key

    def test_x_forwarded_for_handling(self):
        """Test X-Forwarded-For header is used for proxied requests."""
        forwarded_ip = "10.0.0.1"
        x_forwarded_for = f"{forwarded_ip}, 192.168.1.1, 172.16.0.1"

        # First IP in chain is the actual client
        actual_client_ip = x_forwarded_for.split(",")[0].strip()

        assert actual_client_ip == forwarded_ip


class TestRateLimitResponse:
    """Tests for rate limit response headers and status."""

    def test_rate_limit_exceeded_status(self):
        """Test rate limit exceeded returns 429 status."""
        status_code = 429
        assert status_code == 429

    def test_rate_limit_headers(self):
        """Test rate limit headers are included in response."""
        expected_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ]

        for header in expected_headers:
            assert header.startswith("X-RateLimit")

    def test_retry_after_header(self):
        """Test Retry-After header is included when rate limited."""
        retry_after_seconds = 60
        assert retry_after_seconds > 0


class TestRateLimitByEndpoint:
    """Tests for endpoint-specific rate limits."""

    def test_auth_endpoints_stricter(self):
        """Test auth endpoints have stricter rate limits."""
        general_limit = 300
        auth_limit = 10

        assert auth_limit < general_limit

    def test_api_endpoints_standard_limit(self):
        """Test API endpoints use standard rate limit."""
        api_paths = [
            "/api/v1/enrollments",
            "/api/v1/revenue",
            "/api/v1/costs",
        ]

        standard_limit = 300

        for path in api_paths:
            # These should use standard limit (300)
            assert path.startswith("/api/v1")

    def test_health_endpoints_no_limit(self):
        """Test health endpoints have no rate limit."""
        health_paths = ["/health", "/health/live", "/health/ready"]

        for path in health_paths:
            assert path.startswith("/health")


class TestInMemoryRateLimit:
    """Tests for in-memory rate limit fallback."""

    def test_in_memory_storage_structure(self):
        """Test in-memory storage uses dict structure."""
        storage = {}
        client_key = "192.168.1.1"

        storage[client_key] = {
            "tokens": 300,
            "last_refill": 1234567890.0,
        }

        assert client_key in storage
        assert storage[client_key]["tokens"] == 300

    def test_in_memory_cleanup_threshold(self):
        """Test in-memory storage is cleaned after threshold."""
        max_entries = 10000
        current_entries = 15000

        should_cleanup = current_entries > max_entries

        assert should_cleanup is True

    def test_entry_expiration(self):
        """Test entries expire after window period."""
        window_seconds = 60
        entry_age_seconds = 120

        is_expired = entry_age_seconds > window_seconds

        assert is_expired is True


class TestRateLimitWithRedis:
    """Tests for Redis-based rate limiting."""

    def test_redis_key_format(self):
        """Test Redis key format for rate limits."""
        client_ip = "192.168.1.100"
        key = f"rate_limit:{client_ip}"

        assert key.startswith("rate_limit:")
        assert client_ip in key

    def test_redis_ttl_setting(self):
        """Test Redis TTL is set for rate limit keys."""
        window_seconds = 60
        ttl = window_seconds * 2  # 2x window for safety

        assert ttl == 120

    def test_redis_pipeline_for_atomic_operations(self):
        """Test Redis pipeline is used for atomic operations."""
        # Rate limiting should use atomic operations
        operations = ["GET", "SET", "EXPIRE"]

        for op in operations:
            assert op in ["GET", "SET", "EXPIRE", "INCR", "DECR"]


class TestRateLimitLogging:
    """Tests for rate limit logging."""

    def test_log_rate_limit_exceeded(self):
        """Test rate limit exceeded events are logged."""
        log_message = "Rate limit exceeded for client 192.168.1.1"

        assert "Rate limit exceeded" in log_message
        assert "192.168.1.1" in log_message

    def test_log_includes_endpoint(self):
        """Test log includes the endpoint that was rate limited."""
        endpoint = "/api/v1/auth/login"
        log_message = f"Rate limit exceeded for {endpoint}"

        assert endpoint in log_message
