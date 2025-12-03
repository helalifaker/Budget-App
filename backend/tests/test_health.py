from app.main import app
from httpx import AsyncClient


async def test_live_health() -> None:
    """Test liveness probe returns ok status."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


async def test_ready_health() -> None:
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
