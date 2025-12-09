"""
Comprehensive tests for Redis cache initialization.

Tests cover all scenarios including successful initialization, timeouts,
connection errors, graceful degradation, and configuration validation.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import redis.asyncio as redis
from app.core.cache import (
    _get_initialization_lock,
    get_cache_status,
    initialize_cache,
    validate_redis_config,
)


@pytest.fixture(autouse=True)
def reset_cache_state():
    """Reset cache initialization state before each test."""
    import app.core.cache as cache_module

    cache_module._cache_initialized = False
    cache_module._cache_initialization_error = None
    cache_module._cache_initialization_lock = None
    yield
    # Cleanup after test
    cache_module._cache_initialized = False
    cache_module._cache_initialization_error = None
    cache_module._cache_initialization_lock = None


class TestInitializationLock:
    """Test suite for _get_initialization_lock function."""

    def test_creates_lock_on_first_call(self):
        """Test that _get_initialization_lock creates a new lock on first call."""
        import app.core.cache as cache_module

        # Ensure lock doesn't exist
        cache_module._cache_initialization_lock = None

        lock = _get_initialization_lock()

        assert isinstance(lock, asyncio.Lock)
        assert cache_module._cache_initialization_lock is lock

    def test_returns_same_lock_on_subsequent_calls(self):
        """Test that _get_initialization_lock returns the same lock on subsequent calls."""
        lock1 = _get_initialization_lock()
        lock2 = _get_initialization_lock()

        assert lock1 is lock2


class TestInitializeCache:
    """Test suite for initialize_cache function."""

    @pytest.mark.asyncio
    async def test_initialization_skipped_when_redis_disabled(self):
        """Test that initialization is skipped when REDIS_ENABLED=false."""
        with patch("app.core.cache.REDIS_ENABLED", False):
            result = await initialize_cache()

            assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_if_already_initialized(self):
        """Test that initialize_cache returns True if cache already initialized."""
        import app.core.cache as cache_module

        cache_module._cache_initialized = True

        with patch("app.core.cache.REDIS_ENABLED", True):
            result = await initialize_cache()

            assert result is True

    @pytest.mark.asyncio
    async def test_successful_initialization(self):
        """Test successful Redis cache initialization."""
        import app.core.cache as cache_module

        # Force REDIS_ENABLED to True by modifying module state directly
        original_enabled = cache_module.REDIS_ENABLED
        cache_module.REDIS_ENABLED = True

        try:
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis_client.close = AsyncMock()

            # redis.from_url is a SYNC function that returns a Redis client
            # Do NOT use async here - it's a synchronous factory function
            with (
                patch("app.core.cache.cache.setup") as mock_setup,
                patch("app.core.cache.redis.from_url", return_value=mock_redis_client),
            ):
                result = await initialize_cache()

                assert result is True
                mock_setup.assert_called_once()
                mock_redis_client.ping.assert_awaited_once()
                mock_redis_client.close.assert_awaited_once()
        finally:
            # Restore original value
            cache_module.REDIS_ENABLED = original_enabled

    @pytest.mark.asyncio
    async def test_timeout_error_with_required_false(self):
        """Test timeout error with REDIS_REQUIRED=false (graceful degradation)."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_REQUIRED", False),
            patch("app.core.cache.cache.setup"),
            patch(
                "app.core.cache.redis.from_url",
                side_effect=TimeoutError("Connection timeout"),
            ),
        ):
            result = await initialize_cache()

            assert result is False
            # Should not raise exception

    @pytest.mark.asyncio
    async def test_timeout_error_with_required_true(self):
        """Test timeout error with REDIS_REQUIRED=true raises RuntimeError."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_REQUIRED", True),
            patch("app.core.cache.cache.setup"),
            patch(
                "app.core.cache.redis.from_url",
                side_effect=TimeoutError("Connection timeout"),
            ),
        ):
            with pytest.raises(RuntimeError, match="Redis connection timeout"):
                await initialize_cache()

    @pytest.mark.asyncio
    async def test_connection_error_with_required_false(self):
        """Test connection refused with REDIS_REQUIRED=false (graceful degradation)."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_REQUIRED", False),
            patch("app.core.cache.cache.setup"),
            patch(
                "app.core.cache.redis.from_url",
                side_effect=redis.ConnectionError("Connection refused"),
            ),
        ):
            result = await initialize_cache()

            assert result is False
            # Should not raise exception

    @pytest.mark.asyncio
    async def test_connection_error_with_required_true(self):
        """Test connection refused with REDIS_REQUIRED=true raises RuntimeError."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_REQUIRED", True),
            patch("app.core.cache.cache.setup"),
            patch(
                "app.core.cache.redis.from_url",
                side_effect=redis.ConnectionError("Connection refused"),
            ),
        ):
            with pytest.raises(RuntimeError, match="Redis connection failed"):
                await initialize_cache()

    @pytest.mark.asyncio
    async def test_generic_exception_with_required_false(self):
        """Test generic exception with REDIS_REQUIRED=false (graceful degradation)."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_REQUIRED", False),
            patch("app.core.cache.cache.setup"),
            patch(
                "app.core.cache.redis.from_url",
                side_effect=ValueError("Unexpected error"),
            ),
        ):
            result = await initialize_cache()

            assert result is False
            # Should not raise exception

    @pytest.mark.asyncio
    async def test_generic_exception_with_required_true(self):
        """Test generic exception with REDIS_REQUIRED=true raises RuntimeError."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_REQUIRED", True),
            patch("app.core.cache.cache.setup"),
            patch(
                "app.core.cache.redis.from_url",
                side_effect=ValueError("Unexpected error"),
            ),
        ):
            with pytest.raises(RuntimeError, match="Redis initialization failed"):
                await initialize_cache()

    @pytest.mark.asyncio
    async def test_ping_timeout_with_required_false(self):
        """Test ping timeout with REDIS_REQUIRED=false (graceful degradation)."""
        import app.core.cache as cache_module

        # Force module-level values
        original_enabled = cache_module.REDIS_ENABLED
        original_required = cache_module.REDIS_REQUIRED
        cache_module.REDIS_ENABLED = True
        cache_module.REDIS_REQUIRED = False

        try:
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis_client.close = AsyncMock()

            # asyncio.wait_for raises TimeoutError when ping times out
            async def timeout_wait_for(coro, timeout):
                # Close the coroutine to avoid warning
                coro.close() if hasattr(coro, "close") else None
                raise TimeoutError("Ping timeout")

            with (
                patch("app.core.cache.cache.setup"),
                patch("app.core.cache.redis.from_url", return_value=mock_redis_client),
                patch("asyncio.wait_for", side_effect=timeout_wait_for),
            ):
                result = await initialize_cache()

                assert result is False
        finally:
            cache_module.REDIS_ENABLED = original_enabled
            cache_module.REDIS_REQUIRED = original_required

    @pytest.mark.asyncio
    async def test_idempotent_initialization(self):
        """Test that calling initialize_cache multiple times is safe (idempotent)."""
        import app.core.cache as cache_module

        # Force REDIS_ENABLED to True
        original_enabled = cache_module.REDIS_ENABLED
        cache_module.REDIS_ENABLED = True

        try:
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis_client.close = AsyncMock()

            # redis.from_url is a SYNC function - use return_value, not side_effect
            with (
                patch("app.core.cache.cache.setup") as mock_setup,
                patch("app.core.cache.redis.from_url", return_value=mock_redis_client),
            ):
                # First call
                result1 = await initialize_cache()
                assert result1 is True

                # Second call should return immediately without re-initializing
                result2 = await initialize_cache()
                assert result2 is True

                # Setup should only be called once
                assert mock_setup.call_count == 1
        finally:
            # Restore original value
            cache_module.REDIS_ENABLED = original_enabled

    @pytest.mark.asyncio
    async def test_concurrent_initialization_thread_safety(self):
        """Test that concurrent initialization calls are thread-safe."""
        import app.core.cache as cache_module

        # Force REDIS_ENABLED to True
        original_enabled = cache_module.REDIS_ENABLED
        cache_module.REDIS_ENABLED = True

        try:
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis_client.close = AsyncMock()

            call_count = 0

            def sync_from_url(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return mock_redis_client

            with (
                patch("app.core.cache.cache.setup") as mock_setup,
                patch("app.core.cache.redis.from_url", side_effect=sync_from_url),
            ):
                # Launch 5 concurrent initialization attempts
                results = await asyncio.gather(
                    initialize_cache(),
                    initialize_cache(),
                    initialize_cache(),
                    initialize_cache(),
                    initialize_cache(),
                )

                # All should succeed
                assert all(results)

                # Setup should only be called once (thread-safe)
                assert mock_setup.call_count == 1
                assert call_count == 1
        finally:
            cache_module.REDIS_ENABLED = original_enabled


class TestGetCacheStatus:
    """Test suite for get_cache_status function."""

    def test_status_when_redis_disabled(self):
        """Test get_cache_status when REDIS_ENABLED=false."""
        with patch("app.core.cache.REDIS_ENABLED", False):
            status = get_cache_status()

            assert status["status"] == "disabled"
            assert status["enabled"] is False
            assert status["initialized"] is False
            assert "message" in status

    def test_status_when_initialized(self):
        """Test get_cache_status when cache is initialized."""
        import app.core.cache as cache_module

        cache_module._cache_initialized = True

        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_URL", "redis://localhost:6379/0"),
        ):
            status = get_cache_status()

            assert status["status"] == "ok"
            assert status["enabled"] is True
            assert status["initialized"] is True
            assert status["url"] == "redis://localhost:6379/0"

    def test_status_when_initialization_error(self):
        """Test get_cache_status when initialization failed."""
        import app.core.cache as cache_module

        cache_module._cache_initialized = False
        cache_module._cache_initialization_error = ValueError("Test error")

        with patch("app.core.cache.REDIS_ENABLED", True):
            status = get_cache_status()

            assert status["status"] == "error"
            assert status["enabled"] is True
            assert status["initialized"] is False
            assert "error" in status
            assert status["error_type"] == "ValueError"

    def test_status_when_not_yet_initialized(self):
        """Test get_cache_status when cache not yet initialized."""
        import app.core.cache as cache_module

        cache_module._cache_initialized = False
        cache_module._cache_initialization_error = None

        with patch("app.core.cache.REDIS_ENABLED", True):
            status = get_cache_status()

            assert status["status"] == "not_initialized"
            assert status["enabled"] is True
            assert status["initialized"] is False
            assert "message" in status


class TestValidateRedisConfig:
    """Test suite for validate_redis_config function."""

    def test_valid_configuration(self):
        """Test validate_redis_config with valid configuration."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_URL", "redis://localhost:6379/0"),
            patch("app.core.cache.REDIS_CONNECT_TIMEOUT", 5.0),
            patch("app.core.cache.REDIS_SOCKET_TIMEOUT", 5.0),
            patch("app.core.cache.REDIS_REQUIRED", False),
        ):
            errors = validate_redis_config()

            assert len(errors) == 0

    def test_redis_enabled_without_url(self):
        """Test validation error when REDIS_ENABLED=true but REDIS_URL not set."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_URL", ""),
        ):
            errors = validate_redis_config()

            assert len(errors) == 1
            assert "REDIS_URL not set" in errors[0]

    def test_negative_connect_timeout(self):
        """Test validation error when REDIS_CONNECT_TIMEOUT is negative."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_URL", "redis://localhost:6379/0"),
            patch("app.core.cache.REDIS_CONNECT_TIMEOUT", -1.0),
        ):
            errors = validate_redis_config()

            assert any("REDIS_CONNECT_TIMEOUT must be positive" in err for err in errors)

    def test_zero_socket_timeout(self):
        """Test validation error when REDIS_SOCKET_TIMEOUT is zero."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_URL", "redis://localhost:6379/0"),
            patch("app.core.cache.REDIS_SOCKET_TIMEOUT", 0.0),
        ):
            errors = validate_redis_config()

            assert any("REDIS_SOCKET_TIMEOUT must be positive" in err for err in errors)

    def test_required_without_enabled(self):
        """Test validation error when REDIS_REQUIRED=true but REDIS_ENABLED=false."""
        with (
            patch("app.core.cache.REDIS_ENABLED", False),
            patch("app.core.cache.REDIS_REQUIRED", True),
        ):
            errors = validate_redis_config()

            assert any("REDIS_REQUIRED=true requires REDIS_ENABLED=true" in err for err in errors)

    def test_multiple_validation_errors(self):
        """Test multiple validation errors are collected."""
        with (
            patch("app.core.cache.REDIS_ENABLED", True),
            patch("app.core.cache.REDIS_URL", ""),
            patch("app.core.cache.REDIS_CONNECT_TIMEOUT", -1.0),
            patch("app.core.cache.REDIS_SOCKET_TIMEOUT", 0.0),
        ):
            errors = validate_redis_config()

            assert len(errors) == 3
            assert any("REDIS_URL not set" in err for err in errors)
            assert any("REDIS_CONNECT_TIMEOUT" in err for err in errors)
            assert any("REDIS_SOCKET_TIMEOUT" in err for err in errors)
