"""Health check endpoint tests.

Tests for the /health/* endpoints to verify:
- Liveness probe returns correct status
- Readiness probe returns expected structure
"""

from app.main import app
from httpx import ASGITransport, AsyncClient


async def test_live_health() -> None:
    """Test liveness endpoint returns healthy status."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        response = await ac.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "efir-budget-api"


async def test_ready_health() -> None:
    """Test readiness endpoint returns proper structure."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        response = await ac.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    # Status can be "ok" or "degraded" depending on service availability
    assert data["status"] in ("ok", "degraded")
    assert "checks" in data
    assert "timestamp" in data
