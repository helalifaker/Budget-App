#!/usr/bin/env python3
"""
Direct test of the create_budget_version endpoint function.
Bypasses FastAPI routing to isolate where the error occurs.
"""
import asyncio
import os
import sys
import traceback
from types import SimpleNamespace

# Set test environment
os.environ["PYTEST_RUNNING"] = "true"
os.environ["SKIP_AUTH_FOR_TESTS"] = "true"

from app.api.v1.configuration import create_budget_version
from app.database import get_db, init_db
from app.schemas.configuration import BudgetVersionCreate
from app.services.configuration_service import ConfigurationService


async def test_endpoint_directly():
    """Test the endpoint function by calling it directly."""
    print("=" * 80)
    print("DEBUG: Testing create_budget_version endpoint function DIRECTLY")
    print("=" * 80)

    # Initialize database
    print("\n1. Initializing database schema...")
    try:
        await init_db()
        print("   ✅ Database initialized")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Get database session
    async for db in get_db():
        try:
            # Create mock request object
            print("\n2. Creating mock Request object...")
            mock_request = SimpleNamespace()
            mock_request.state = SimpleNamespace()
            mock_request.state.user_id = None
            print("   ✅ Mock request created")

            # Create Pydantic request data
            print("\n3. Creating Pydantic request data...")
            version_data = BudgetVersionCreate(
                name="Test Budget 2025-2026",
                fiscal_year=2026,
                academic_year="2025-2026",
                notes="Direct endpoint test",
                parent_version_id=None,
            )
            print(f"   ✅ Request data created: {version_data}")
            print(f"      Type of fiscal_year: {type(version_data.fiscal_year)}")
            print(f"      Value of fiscal_year: {version_data.fiscal_year}")

            # Create service
            print("\n4. Creating ConfigurationService...")
            config_service = ConfigurationService(db)
            print("   ✅ Service created")

            # Call the endpoint function DIRECTLY
            print("\n5. Calling create_budget_version endpoint function...")
            print("   Parameters:")
            print(f"     version_data: {version_data}")
            print(f"     request: {mock_request}")
            print(f"     config_service: {config_service}")

            result = await create_budget_version(
                version_data=version_data,
                request=mock_request,
                config_service=config_service,
            )

            print(f"\n   ✅ SUCCESS: Endpoint returned result")
            print(f"      Type: {type(result)}")
            print(f"      Result: {result}")
            print("\n" + "=" * 80)
            print("ENDPOINT FUNCTION WORKS CORRECTLY!")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ ERROR calling endpoint function:")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            print("\n   Full Stack Trace:")
            print("-" * 80)
            traceback.print_exc()
            print("-" * 80)

            # Try to get more info about where .replace() is being called
            print("\n   Analyzing stack trace for .replace() calls...")
            tb = sys.exc_info()[2]
            while tb is not None:
                frame = tb.tb_frame
                code = frame.f_code
                print(f"   Frame: {code.co_filename}:{tb.tb_lineno} in {code.co_name}")
                # Check local variables for integers
                for var_name, var_value in frame.f_locals.items():
                    if isinstance(var_value, int):
                        print(f"     - Local int variable: {var_name} = {var_value}")
                tb = tb.tb_next

            sys.exit(1)

        break


if __name__ == "__main__":
    asyncio.run(test_endpoint_directly())
