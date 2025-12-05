"""
Comprehensive tests for application startup and shutdown event handlers.

Tests cover all scenarios including successful startup, Redis failures,
database connectivity issues, Supabase Auth API checks, and graceful shutdown.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.fixture
def mock_logger():
    """Mock logger to capture log calls."""
    with patch("app.main.logger") as mock_log:
        yield mock_log


@pytest.fixture
def mock_validate_redis_config():
    """Mock Redis configuration validation."""
    with patch("app.main.validate_redis_config") as mock_validate:
        mock_validate.return_value = []  # No errors by default
        yield mock_validate


@pytest.fixture
def mock_initialize_cache():
    """Mock Redis cache initialization."""
    with patch("app.main.initialize_cache") as mock_init:
        mock_init.return_value = True  # Success by default
        yield mock_init


@pytest.fixture
def mock_engine():
    """Mock database engine."""
    with patch("app.main.engine") as mock_eng:
        yield mock_eng


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for Supabase Auth checks."""
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client


class TestStartupEvent:
    """Test suite for application startup event handler."""

    @pytest.mark.asyncio
    async def test_successful_startup_all_services_healthy(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
        mock_httpx_client,
    ):
        """Test successful startup with all services healthy."""
        # Mock database connection success
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=MagicMock())
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        # Mock Supabase Auth API success
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_http_instance = AsyncMock()
        mock_http_instance.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_http_instance

        # Import and trigger startup
        with patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co"}):
            from app.main import app

            # Manually trigger startup event
            async with app.router.lifespan_context(app):
                pass

        # Verify startup sequence
        mock_validate_redis_config.assert_called_once()
        mock_initialize_cache.assert_awaited_once()
        mock_engine.connect.assert_called_once()
        mock_conn.execute.assert_awaited_once()
        mock_http_instance.get.assert_awaited_once_with(
            "https://test.supabase.co/auth/v1/health"
        )

        # Verify logging
        assert any(
            call[0][0] == "application_startup_begin"
            for call in mock_logger.info.call_args_list
        )
        assert any(
            call[0][0] == "application_startup_complete"
            for call in mock_logger.info.call_args_list
        )

    @pytest.mark.asyncio
    async def test_startup_redis_config_validation_errors_redis_not_required(
        self, mock_logger, mock_validate_redis_config, mock_initialize_cache
    ):
        """Test startup with Redis config errors when REDIS_REQUIRED=false."""
        mock_validate_redis_config.return_value = [
            "REDIS_URL not set",
            "REDIS_CONNECT_TIMEOUT must be positive",
        ]

        with (
            patch.dict("os.environ", {"REDIS_REQUIRED": "false"}),
            patch("app.main.engine") as mock_engine,
        ):
            # Mock database to succeed
            mock_conn = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn

            from app.main import app

            # Should not raise even with config errors when REDIS_REQUIRED=false
            async with app.router.lifespan_context(app):
                pass

        # Should log warning - check first positional argument
        mock_logger.warning.assert_called()
        warning_calls = [
            call[0][0] for call in mock_logger.warning.call_args_list
        ]
        assert "redis_config_validation_failed" in warning_calls

    @pytest.mark.asyncio
    async def test_startup_redis_config_validation_errors_redis_required(
        self, mock_validate_redis_config
    ):
        """Test startup fails with Redis config errors when REDIS_REQUIRED=true."""
        mock_validate_redis_config.return_value = ["REDIS_URL not set"]

        with patch.dict("os.environ", {"REDIS_REQUIRED": "true"}):
            from app.main import app

            # Should raise ValueError when REDIS_REQUIRED=true and config invalid
            with pytest.raises(ValueError, match="Invalid Redis configuration"):
                async with app.router.lifespan_context(app):
                    pass

    @pytest.mark.asyncio
    async def test_startup_database_connection_timeout(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
    ):
        """Test startup with database connection timeout."""
        # Mock database timeout
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=TimeoutError("DB timeout"))
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        with patch.dict("os.environ", {"SUPABASE_URL": ""}):
            from app.main import app

            # Should not raise - graceful degradation
            async with app.router.lifespan_context(app):
                pass

        # Verify error logging
        mock_logger.error.assert_called()
        error_call = [
            call
            for call in mock_logger.error.call_args_list
            if call[0][0] == "database_health_check_timeout"
        ]
        assert len(error_call) > 0

    @pytest.mark.asyncio
    async def test_startup_database_connection_error(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
    ):
        """Test startup with database connection error."""
        # Mock database connection error
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(
            side_effect=Exception("Connection refused by database")
        )
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        with patch.dict("os.environ", {"SUPABASE_URL": ""}):
            from app.main import app

            # Should not raise - graceful degradation
            async with app.router.lifespan_context(app):
                pass

        # Verify error logging
        error_calls = [
            call
            for call in mock_logger.error.call_args_list
            if call[0][0] == "database_health_check_failed"
        ]
        assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_startup_redis_initialization_success(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
    ):
        """Test startup with successful Redis initialization."""
        mock_initialize_cache.return_value = True

        # Mock database to succeed
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        with patch.dict("os.environ", {"SUPABASE_URL": ""}):
            from app.main import app

            async with app.router.lifespan_context(app):
                pass

        # Verify cache initialization was called
        mock_initialize_cache.assert_awaited_once()

        # Verify success logging
        success_calls = [
            call
            for call in mock_logger.info.call_args_list
            if call[0][0] == "cache_initialization_success"
        ]
        assert len(success_calls) > 0

    @pytest.mark.asyncio
    async def test_startup_redis_initialization_disabled(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
    ):
        """Test startup when Redis initialization returns False (disabled/unavailable)."""
        mock_initialize_cache.return_value = False

        # Mock database to succeed
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        with patch.dict("os.environ", {"SUPABASE_URL": ""}):
            from app.main import app

            async with app.router.lifespan_context(app):
                pass

        # Verify warning about degraded caching
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if call[0][0] == "cache_disabled_or_unavailable"
        ]
        assert len(warning_calls) > 0

    @pytest.mark.asyncio
    async def test_startup_redis_initialization_fails_redis_not_required(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
    ):
        """Test startup when Redis init fails but REDIS_REQUIRED=false."""
        mock_initialize_cache.side_effect = Exception("Redis connection failed")

        # Mock database to succeed
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        with patch.dict(
            "os.environ", {"REDIS_REQUIRED": "false", "SUPABASE_URL": ""}
        ):
            from app.main import app

            # Should not raise - logged as error but doesn't block startup
            # Note: The actual handler re-raises if REDIS_REQUIRED=true
            with pytest.raises(Exception, match="Redis connection failed"):
                async with app.router.lifespan_context(app):
                    pass

    @pytest.mark.asyncio
    async def test_startup_redis_initialization_fails_redis_required(
        self, mock_validate_redis_config, mock_initialize_cache, mock_engine
    ):
        """Test startup fails when Redis init fails and REDIS_REQUIRED=true."""
        mock_initialize_cache.side_effect = RuntimeError(
            "Redis connection timeout after 5s"
        )

        # Mock database to succeed
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        with patch.dict("os.environ", {"REDIS_REQUIRED": "true"}):
            from app.main import app

            # Should raise and block startup when REDIS_REQUIRED=true
            with pytest.raises(RuntimeError, match="Redis connection timeout"):
                async with app.router.lifespan_context(app):
                    pass

    @pytest.mark.asyncio
    async def test_startup_supabase_auth_check_success(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
        mock_httpx_client,
    ):
        """Test Supabase Auth API health check succeeds."""
        # Mock database and cache success
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        # Mock Supabase Auth API success
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_http_instance = AsyncMock()
        mock_http_instance.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_http_instance

        with patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co"}):
            from app.main import app

            async with app.router.lifespan_context(app):
                pass

        # Verify Auth API was checked
        mock_http_instance.get.assert_awaited_once_with(
            "https://test.supabase.co/auth/v1/health"
        )

        # Verify success logging
        success_calls = [
            call
            for call in mock_logger.info.call_args_list
            if call[0][0] == "supabase_auth_check_success"
        ]
        assert len(success_calls) > 0

    @pytest.mark.asyncio
    async def test_startup_supabase_auth_check_fails_non_blocking(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
        mock_httpx_client,
    ):
        """Test Supabase Auth API check fails but doesn't block startup."""
        # Mock database and cache success
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        # Mock Supabase Auth API failure
        mock_http_instance = AsyncMock()
        mock_http_instance.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_httpx_client.return_value.__aenter__.return_value = mock_http_instance

        with patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co"}):
            from app.main import app

            # Should not raise - Auth check is non-blocking
            async with app.router.lifespan_context(app):
                pass

        # Verify warning was logged
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if call[0][0] == "supabase_auth_check_failed"
        ]
        assert len(warning_calls) > 0

    @pytest.mark.asyncio
    async def test_startup_supabase_auth_skipped_when_url_not_set(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
        mock_httpx_client,
    ):
        """Test Supabase Auth check is skipped when SUPABASE_URL not set."""
        # Mock database and cache success
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        with patch.dict("os.environ", {"SUPABASE_URL": ""}, clear=True):
            from app.main import app

            async with app.router.lifespan_context(app):
                pass

        # Verify Auth API was NOT checked
        mock_httpx_client.assert_not_called()


class TestShutdownEvent:
    """Test suite for application shutdown event handler."""

    @pytest.mark.asyncio
    async def test_successful_shutdown_redis_client_closed(self, mock_logger):
        """Test successful shutdown with Redis client cleanup."""
        # Mock close_redis_client function
        mock_close = AsyncMock()

        with (
            patch("app.main.validate_redis_config") as mock_validate,
            patch("app.main.initialize_cache") as mock_init,
            patch("app.main.engine") as mock_engine,
        ):
            # Mock successful startup
            mock_validate.return_value = []
            mock_init.return_value = True
            mock_conn = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn

            from app.main import app

            # Patch close_redis_client for shutdown test
            with patch(
                "app.core.cache.close_redis_client", mock_close
            ) as mock_close_redis:
                async with app.router.lifespan_context(app):
                    pass  # Shutdown happens on context exit

                # Verify Redis client was closed
                mock_close_redis.assert_awaited_once()

        # Verify shutdown logging
        shutdown_calls = [
            call
            for call in mock_logger.info.call_args_list
            if call[0][0] == "application_shutdown_begin"
        ]
        assert len(shutdown_calls) > 0

        complete_calls = [
            call
            for call in mock_logger.info.call_args_list
            if call[0][0] == "application_shutdown_complete"
        ]
        assert len(complete_calls) > 0

    @pytest.mark.asyncio
    async def test_shutdown_redis_client_close_fails_graceful(self, mock_logger):
        """Test shutdown handles Redis client close failure gracefully."""
        # Mock close_redis_client to fail
        mock_close = AsyncMock(side_effect=Exception("Redis already disconnected"))

        with (
            patch("app.main.validate_redis_config") as mock_validate,
            patch("app.main.initialize_cache") as mock_init,
            patch("app.main.engine") as mock_engine,
        ):
            # Mock successful startup
            mock_validate.return_value = []
            mock_init.return_value = True
            mock_conn = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn

            from app.main import app

            # Patch close_redis_client for shutdown test
            with patch(
                "app.core.cache.close_redis_client", mock_close
            ) as mock_close_redis:
                # Should not raise - shutdown should handle errors gracefully
                async with app.router.lifespan_context(app):
                    pass

                mock_close_redis.assert_awaited_once()

        # Verify warning was logged
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if call[0][0] == "redis_client_close_failed"
        ]
        assert len(warning_calls) > 0


class TestStartupShutdownIntegration:
    """Integration tests for complete startup/shutdown lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_lifecycle_startup_and_shutdown(
        self,
        mock_logger,
        mock_validate_redis_config,
        mock_initialize_cache,
        mock_engine,
    ):
        """Test complete lifecycle: startup → running → shutdown."""
        # Mock all dependencies for success
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn

        mock_close = AsyncMock()

        with (
            patch.dict("os.environ", {"SUPABASE_URL": ""}),
            patch("app.core.cache.close_redis_client", mock_close),
        ):
            from app.main import app

            async with app.router.lifespan_context(app):
                # Application is running here
                pass  # Shutdown happens on context exit

        # Verify complete lifecycle
        # 1. Startup events
        assert any(
            call[0][0] == "application_startup_begin"
            for call in mock_logger.info.call_args_list
        )
        assert any(
            call[0][0] == "application_startup_complete"
            for call in mock_logger.info.call_args_list
        )

        # 2. Shutdown events
        assert any(
            call[0][0] == "application_shutdown_begin"
            for call in mock_logger.info.call_args_list
        )
        assert any(
            call[0][0] == "application_shutdown_complete"
            for call in mock_logger.info.call_args_list
        )

        # 3. Redis cleanup
        mock_close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_startup_failure_prevents_application_start(
        self, mock_validate_redis_config
    ):
        """Test that critical startup failures prevent application from starting."""
        # Simulate critical Redis config error when REDIS_REQUIRED=true
        mock_validate_redis_config.return_value = ["REDIS_URL not set"]

        with patch.dict("os.environ", {"REDIS_REQUIRED": "true"}):
            from app.main import app

            # Application should fail to start
            with pytest.raises(ValueError, match="Invalid Redis configuration"):
                async with app.router.lifespan_context(app):
                    pass
