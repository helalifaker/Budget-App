"""
Tests for rate limiting middleware.

Covers:
- Basic rate limiting enforcement
- Category-based limits
- Role-based multipliers
- Redis fallback behavior
- Rate limit headers
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import Response

from app.middleware.rate_limit import (
    RateLimitMiddleware,
    get_client_identifier,
    get_rate_limit_category,
    get_user_role,
    RATE_LIMITS,
    ROLE_MULTIPLIERS,
)


# ==============================================================================
# Test: Client Identification
# ==============================================================================


class TestClientIdentification:
    """Tests for client identification logic."""

    def test_get_client_identifier_with_user(self):
        """Test identification with authenticated user."""
        request = MagicMock(spec=Request)
        user = MagicMock()
        user.id = "user-123"
        request.state.user = user
        request.headers = {}

        result = get_client_identifier(request)

        assert result == "user:user-123"

    def test_get_client_identifier_with_forwarded_ip(self):
        """Test identification with X-Forwarded-For header."""
        request = MagicMock(spec=Request)
        request.state = MagicMock(spec=[])  # No user attribute
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        result = get_client_identifier(request)

        assert result == "ip:192.168.1.1"

    def test_get_client_identifier_with_direct_ip(self):
        """Test identification with direct client IP."""
        request = MagicMock(spec=Request)
        request.state = MagicMock(spec=[])  # No user attribute
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        result = get_client_identifier(request)

        assert result == "ip:192.168.1.100"


# ==============================================================================
# Test: Category Detection
# ==============================================================================


class TestCategoryDetection:
    """Tests for rate limit category detection."""

    def test_calculations_category(self):
        """Test calculations path detection."""
        assert get_rate_limit_category("/api/v1/calculations/dhg") == "calculations"

    def test_consolidation_category(self):
        """Test consolidation path detection."""
        assert get_rate_limit_category("/api/v1/consolidation/submit") == "consolidation"

    def test_export_category(self):
        """Test export path detection."""
        assert get_rate_limit_category("/api/v1/analysis/export/pdf") == "export"

    def test_default_category(self):
        """Test default category for unknown paths."""
        assert get_rate_limit_category("/api/v1/unknown/path") == "default"

    def test_read_category(self):
        """Test read category for configuration paths."""
        assert get_rate_limit_category("/api/v1/configuration/version") == "read"


# ==============================================================================
# Test: Role Detection
# ==============================================================================


class TestRoleDetection:
    """Tests for user role detection."""

    def test_get_user_role_with_role(self):
        """Test role detection with authenticated user."""
        request = MagicMock(spec=Request)
        user = MagicMock()
        user.role = "ADMIN"
        request.state.user = user

        result = get_user_role(request)

        assert result == "admin"

    def test_get_user_role_default(self):
        """Test default role when no user."""
        request = MagicMock(spec=Request)
        request.state = MagicMock(spec=[])  # No user attribute

        result = get_user_role(request)

        assert result == "viewer"


# ==============================================================================
# Test: Rate Limit Configuration
# ==============================================================================


class TestRateLimitConfiguration:
    """Tests for rate limit configuration."""

    def test_rate_limits_defined(self):
        """Test that required rate limit categories are defined."""
        assert "default" in RATE_LIMITS
        assert "calculations" in RATE_LIMITS
        assert "consolidation" in RATE_LIMITS
        assert "export" in RATE_LIMITS
        assert "read" in RATE_LIMITS

    def test_rate_limits_have_required_keys(self):
        """Test that rate limits have required configuration."""
        for category, config in RATE_LIMITS.items():
            assert "requests" in config, f"{category} missing 'requests'"
            assert "window" in config, f"{category} missing 'window'"
            assert config["requests"] > 0
            assert config["window"] > 0

    def test_role_multipliers_defined(self):
        """Test that role multipliers are defined."""
        assert "admin" in ROLE_MULTIPLIERS
        assert "finance_director" in ROLE_MULTIPLIERS
        assert "viewer" in ROLE_MULTIPLIERS

    def test_admin_has_highest_multiplier(self):
        """Test that admin has highest multiplier."""
        admin_mult = ROLE_MULTIPLIERS["admin"]
        for role, mult in ROLE_MULTIPLIERS.items():
            assert admin_mult >= mult


# ==============================================================================
# Test: Middleware Integration
# ==============================================================================


class TestRateLimitMiddleware:
    """Tests for rate limit middleware integration."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are added to response."""
        with patch("app.middleware.rate_limit.RATE_LIMIT_ENABLED", True):
            with patch("app.middleware.rate_limit.REDIS_ENABLED", False):
                response = client.get("/test")

                assert response.status_code == 200
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers

    def test_health_check_bypasses_rate_limit(self, client):
        """Test that health check endpoints bypass rate limiting."""
        # Health checks should always succeed
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    @patch("app.middleware.rate_limit.RATE_LIMIT_ENABLED", False)
    def test_rate_limit_disabled(self, client):
        """Test behavior when rate limiting is disabled."""
        # Should not add rate limit headers when disabled
        response = client.get("/test")
        assert response.status_code == 200


# ==============================================================================
# Test: Redis Integration
# ==============================================================================


class TestRedisIntegration:
    """Tests for Redis-backed rate limiting."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_disabled(self):
        """Test graceful degradation when Redis disabled."""
        middleware = RateLimitMiddleware(app=None)

        with patch("app.middleware.rate_limit.REDIS_ENABLED", False):
            is_allowed, count, reset = await middleware._check_rate_limit(
                client_id="test-client",
                category="default",
                max_requests=10,
                window=60,
            )

            assert is_allowed is True
            assert count == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error(self):
        """Test graceful degradation on Redis error."""
        middleware = RateLimitMiddleware(app=None)

        with patch("app.middleware.rate_limit.REDIS_ENABLED", True):
            with patch(
                "app.core.cache.get_redis_client",
                side_effect=Exception("Redis connection failed"),
            ):
                is_allowed, count, reset = await middleware._check_rate_limit(
                    client_id="test-client",
                    category="default",
                    max_requests=10,
                    window=60,
                )

                # Should allow request on error
                assert is_allowed is True
