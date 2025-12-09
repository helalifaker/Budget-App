#!/usr/bin/env python3
"""
Test response serialization to isolate the JSON conversion error.
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
from app.schemas.configuration import BudgetVersionCreate, BudgetVersionResponse
from app.services.configuration_service import ConfigurationService


async def test_response_serialization():
    """Test serializing the response to JSON."""
    print("=" * 80)
    print("DEBUG: Testing Response Serialization")
    print("=" * 80)

    # Initialize database
    await init_db()

    # Get database session
    async for db in get_db():
        try:
            # Create mock request
            mock_request = SimpleNamespace()
            mock_request.state = SimpleNamespace()
            mock_request.state.user_id = None

            # Create request data
            version_data = BudgetVersionCreate(
                name="Test Budget",
                fiscal_year=2026,
                academic_year="2025-2026",
                notes="Test",
                parent_version_id=None,
            )

            # Create service
            config_service = ConfigurationService(db)

            # Call endpoint function
            print("\n1. Calling endpoint function...")
            result = await create_budget_version(
                version_data=version_data,
                request=mock_request,
                config_service=config_service,
            )
            print(f"   ✅ Endpoint returned: {result}")
            print(f"   Type: {type(result)}")

            # Try to serialize using Pydantic's response model
            print("\n2. Serializing with BudgetVersionResponse schema...")
            print(f"   Input object type: {type(result)}")
            print(f"   Input object: {result}")

            # This is what FastAPI does internally
            response_model = BudgetVersionResponse.model_validate(result)
            print(f"   ✅ Pydantic validation successful")
            print(f"   Response model: {response_model}")

            # Convert to dict (this is where JSON serialization happens)
            print("\n3. Converting to dict...")
            response_dict = response_model.model_dump()
            print(f"   ✅ Dict conversion successful")
            print(f"   Dict keys: {list(response_dict.keys())}")

            # Convert to JSON string
            print("\n4. Converting to JSON string...")
            import json
            json_str = json.dumps(response_dict, default=str)
            print(f"   ✅ JSON serialization successful")
            print(f"   JSON length: {len(json_str)} characters")
            print(f"   JSON preview: {json_str[:200]}...")

            print("\n" + "=" * 80)
            print("RESPONSE SERIALIZATION WORKS CORRECTLY!")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ ERROR during serialization:")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            print("\n   Full Stack Trace:")
            print("-" * 80)
            traceback.print_exc()
            print("-" * 80)

            # Analyze the stack trace
            print("\n   Analyzing error location...")
            tb = sys.exc_info()[2]
            while tb is not None:
                frame = tb.tb_frame
                code = frame.f_code
                print(f"   Frame: {code.co_filename}:{tb.tb_lineno} in {code.co_name}")
                # Print local variables that are integers
                for var_name, var_value in frame.f_locals.items():
                    if isinstance(var_value, int):
                        print(f"     - Int variable: {var_name} = {var_value}")
                    if var_name in ['self', 'obj', 'value', 'data']:
                        print(f"     - Key variable: {var_name} = {type(var_value)} = {str(var_value)[:100]}")
                tb = tb.tb_next

            sys.exit(1)

        break


if __name__ == "__main__":
    asyncio.run(test_response_serialization())
