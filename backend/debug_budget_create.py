#!/usr/bin/env python3
"""Debug script to get full stack trace for budget version creation error."""
import asyncio
import os
import sys

# Set test environment to use SQLite
os.environ["PYTEST_RUNNING"] = "true"
os.environ["SKIP_AUTH_FOR_TESTS"] = "true"

from app.database import get_db, init_db
from app.services.configuration_service import ConfigurationService


async def test_create_budget_version():
    """Test budget version creation and print full traceback on error."""
    print("=" * 80)
    print("DEBUG: Testing budget version creation")
    print("=" * 80)

    # Initialize database schema
    print("\n1. Initializing database schema...")
    try:
        await init_db()
        print("   ✅ Database schema initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    async for db in get_db():
        service = ConfigurationService(db)

        try:
            print("\n2. Attempting to create budget version...")
            print(f"     name: 'Test Budget 2025-2026'")
            print(f"     fiscal_year: 2026")
            print(f"     academic_year: '2025-2026'")
            print(f"     notes: 'Debug test'")
            print(f"     user_id: None")

            version = await service.create_budget_version(
                name="Test Budget 2025-2026",
                fiscal_year=2026,
                academic_year="2025-2026",
                notes="Debug test",
                user_id=None,
            )

            print(f"\n   ✅ SUCCESS: Created budget version")
            print(f"      ID: {version.id}")
            print(f"      Name: {version.name}")
            print(f"      Status: {version.status}")
            print("\n" + "=" * 80)
            print("All tests passed!")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ ERROR: {type(e).__name__}: {e}")
            print("\nFull Stack Trace:")
            print("-" * 80)
            import traceback
            traceback.print_exc()
            print("-" * 80)
            sys.exit(1)

        break


if __name__ == "__main__":
    asyncio.run(test_create_budget_version())
