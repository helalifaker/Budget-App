from httpx import AsyncClient
from app.main import app


async def test_live_health() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_health() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
