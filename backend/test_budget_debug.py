import asyncio
import os
os.environ["PYTEST_RUNNING"] = "true"

from app.database import get_db
from app.services.configuration_service import ConfigurationService

async def test_create():
    async for db in get_db():
        service = ConfigurationService(db)
        try:
            version = await service.create_budget_version(
                name="Test",
                fiscal_year=2026,
                academic_year="2025-2026",
                notes="Test",
                user_id=None,
            )
            print(f"Success: {version}")
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()
        break

asyncio.run(test_create())
