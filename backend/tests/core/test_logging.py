"""
Tests for logging configuration and middleware.

Covers:
- Logging configuration
- LoggingMiddleware functionality
- Correlation ID generation
- Request/response logging
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.logging import LoggingMiddleware, configure_logging, logger


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_configure_logging_returns_logger(self):
        """Test that configure_logging returns a logger instance."""
        log = configure_logging()
        assert log is not None

    def test_logger_is_configured(self):
        """Test that global logger is configured."""
        assert logger is not None

    @patch("app.core.logging.structlog.configure")
    def test_configure_logging_calls_structlog(self, mock_configure):
        """Test that configure_logging calls structlog.configure."""
        configure_logging()
        mock_configure.assert_called_once()

    @patch("app.core.logging.logging.basicConfig")
    def test_configure_logging_calls_basic_config(self, mock_basic_config):
        """Test that configure_logging calls logging.basicConfig."""
        configure_logging()
        mock_basic_config.assert_called_once()


class TestLoggingMiddleware:
    """Test LoggingMiddleware functionality."""

    @pytest.mark.asyncio
    async def test_middleware_adds_correlation_id(self):
        """Test that middleware adds correlation ID to response."""
        middleware = LoggingMiddleware(MagicMock())

        # Mock request and response
        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers.get = MagicMock(return_value=None)

        response = MagicMock()
        response.status_code = 200
        response.headers = {}

        # Mock call_next
        async def call_next(req):
            return response

        # Process request
        result = await middleware.dispatch(request, call_next)

        # Verify correlation ID was added
        assert "X-Correlation-ID" in result.headers
        assert result.headers["X-Correlation-ID"] is not None
        assert isinstance(result.headers["X-Correlation-ID"], str)

    @pytest.mark.asyncio
    async def test_middleware_generates_unique_correlation_ids(self):
        """Test that each request gets a unique correlation ID."""
        middleware = LoggingMiddleware(MagicMock())

        request1 = MagicMock()
        request1.url.path = "/api/test1"
        request1.method = "GET"
        request1.client.host = "127.0.0.1"
        request1.headers.get = MagicMock(return_value=None)

        request2 = MagicMock()
        request2.url.path = "/api/test2"
        request2.method = "GET"
        request2.client.host = "127.0.0.1"
        request2.headers.get = MagicMock(return_value=None)

        response = MagicMock()
        response.status_code = 200
        response.headers = {}

        async def call_next(req):
            return response

        result1 = await middleware.dispatch(request1, call_next)
        result2 = await middleware.dispatch(request2, call_next)

        # Correlation IDs should be different
        assert result1.headers["X-Correlation-ID"] != result2.headers["X-Correlation-ID"]

    @pytest.mark.asyncio
    async def test_middleware_logs_request_start(self):
        """Test that middleware logs request start."""
        middleware = LoggingMiddleware(MagicMock())

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers.get = MagicMock(return_value="test-agent")

        response = MagicMock()
        response.status_code = 200
        response.headers = {}

        async def call_next(req):
            return response

        with patch("app.core.logging.logger.info") as mock_log:
            await middleware.dispatch(request, call_next)

            # Should log request_started
            log_calls = [str(call) for call in mock_log.call_args_list]
            assert any("request_started" in str(call) for call in mock_log.call_args_list)

    @pytest.mark.asyncio
    async def test_middleware_logs_request_completion(self):
        """Test that middleware logs request completion."""
        middleware = LoggingMiddleware(MagicMock())

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers.get = MagicMock(return_value=None)

        response = MagicMock()
        response.status_code = 200
        response.headers = {}

        async def call_next(req):
            return response

        with patch("app.core.logging.logger.info") as mock_log:
            await middleware.dispatch(request, call_next)

            # Should log request_completed
            assert any("request_completed" in str(call) for call in mock_log.call_args_list)

    @pytest.mark.asyncio
    async def test_middleware_logs_request_failure(self):
        """Test that middleware logs request failures."""
        middleware = LoggingMiddleware(MagicMock())

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers.get = MagicMock(return_value=None)

        async def call_next(req):
            raise ValueError("Test error")

        with patch("app.core.logging.logger.error") as mock_log:
            with pytest.raises(ValueError):
                await middleware.dispatch(request, call_next)

            # Should log request_failed
            assert any("request_failed" in str(call) for call in mock_log.call_args_list)

    @pytest.mark.asyncio
    async def test_middleware_clears_context_vars(self):
        """Test that middleware clears context variables after request."""
        middleware = LoggingMiddleware(MagicMock())

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers.get = MagicMock(return_value=None)

        response = MagicMock()
        response.status_code = 200
        response.headers = {}

        async def call_next(req):
            return response

        with patch("app.core.logging.structlog.contextvars.clear_contextvars") as mock_clear:
            await middleware.dispatch(request, call_next)

            # Should clear context variables
            mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_handles_none_client(self):
        """Test that middleware handles request with None client."""
        middleware = LoggingMiddleware(MagicMock())

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.client = None
        request.headers.get = MagicMock(return_value=None)

        response = MagicMock()
        response.status_code = 200
        response.headers = {}

        async def call_next(req):
            return response

        # Should not raise exception
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_binds_context_vars(self):
        """Test that middleware binds context variables."""
        middleware = LoggingMiddleware(MagicMock())

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "POST"
        request.client.host = "192.168.1.1"
        request.headers.get = MagicMock(return_value="test-agent")

        response = MagicMock()
        response.status_code = 201
        response.headers = {}

        async def call_next(req):
            return response

        with patch("app.core.logging.structlog.contextvars.bind_contextvars") as mock_bind:
            await middleware.dispatch(request, call_next)

            # Should bind context variables
            mock_bind.assert_called_once()
            call_kwargs = mock_bind.call_args[1]
            assert "correlation_id" in call_kwargs
            assert call_kwargs["path"] == "/api/test"
            assert call_kwargs["method"] == "POST"
            assert call_kwargs["client_host"] == "192.168.1.1"

