from app.main import app
from httpx import AsyncClient


async def test_live_health() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


async def test_ready_health() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    # In test env without DB/Redis, status may be "degraded"
    assert "status" in data
    assert data["status"] in ("ready", "degraded")
