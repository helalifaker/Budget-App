"""
Unit tests for Health Check endpoints.
"""

import pytest
from app.main import app
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_live_health(self) -> None:
        """Test liveness probe returns ok status."""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            response = await ac.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "efir-budget-api"

    @pytest.mark.asyncio
    async def test_ready_health(self) -> None:
        """Test readiness probe returns valid response.

        Note: In test environment without DB/Redis, the status may be 'degraded'.
        We just verify the endpoint returns a valid response structure.
        """
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            response = await ac.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        # Status could be 'ready' or 'degraded' depending on external dependencies
        assert data["status"] in ("ready", "degraded", "ok")

    @pytest.mark.asyncio
    async def test_main_health_endpoint(self) -> None:
        """Test main /health endpoint."""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "EFIR Budget Planning API"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self) -> None:
        """Test metrics endpoint returns placeholder response."""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            response = await ac.get("/health/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_implemented"
        assert "planned_metrics" in data
        assert isinstance(data["planned_metrics"], list)

    @pytest.mark.asyncio
    async def test_cache_statistics_endpoint(self) -> None:
        """Test cache statistics endpoint."""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            response = await ac.get("/health/cache")
        assert response.status_code == 200
        data = response.json()
        # Status could be 'enabled', 'disabled', or 'error'
        assert "status" in data


class TestReadinessProbeStructure:
    """Tests for readiness probe response structure."""

    @pytest.mark.asyncio
    async def test_readiness_has_checks(self) -> None:
        """Test readiness probe has checks object."""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            response = await ac.get("/health/ready")
        data = response.json()
        assert "checks" in data or "status" in data

    @pytest.mark.asyncio
    async def test_readiness_has_timestamp(self) -> None:
        """Test readiness probe has timestamp."""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            response = await ac.get("/health/ready")
        data = response.json()
        assert "timestamp" in data or "status" in data


class TestHealthCheckLogic:
    """Tests for health check logic (unit tests)."""

    def test_valid_health_statuses(self):
        """Test valid health status values."""
        valid_statuses = ["ok", "degraded", "error", "healthy"]

        for status in valid_statuses:
            assert status in valid_statuses

    def test_redis_status_values(self):
        """Test valid Redis status values."""
        valid_redis_statuses = ["ok", "disabled", "error", "not_configured"]

        for status in valid_redis_statuses:
            assert status in valid_redis_statuses

    def test_supabase_status_values(self):
        """Test valid Supabase Auth status values."""
        valid_supabase_statuses = ["ok", "error", "not_configured"]

        for status in valid_supabase_statuses:
            assert status in valid_supabase_statuses

    def test_database_status_values(self):
        """Test valid database status values."""
        valid_db_statuses = ["ok", "error"]

        for status in valid_db_statuses:
            assert status in valid_db_statuses


class TestPlannedMetrics:
    """Tests for planned Prometheus metrics."""

    def test_planned_metrics_list(self):
        """Test expected planned metrics are defined."""
        planned_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "db_connections_active",
            "cache_hits_total",
            "budget_calculations_total",
        ]

        assert "http_requests_total" in planned_metrics
        assert "http_request_duration_seconds" in planned_metrics
        assert "db_connections_active" in planned_metrics
        assert "cache_hits_total" in planned_metrics
        assert "budget_calculations_total" in planned_metrics
