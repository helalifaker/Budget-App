"""
Test async mocking pattern verification.

This file verifies that our async mocking approach works correctly
before implementing the full test suites.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client with auth override."""
    from app.dependencies.auth import get_current_user

    def mock_get_current_user():
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "test@efir.local"
        user.role = "admin"
        return user

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_async_mock_pattern_works(client):
    """Test that AsyncMock pattern works for service methods."""
    version_id = uuid.uuid4()

    with patch("app.api.v1.export.ConsolidationService") as mock_class:
        # Create AsyncMock instance
        mock_instance = AsyncMock()
        mock_consolidation = MagicMock()
        mock_consolidation.budget_version = MagicMock()
        mock_consolidation.budget_version.name = "Test Budget"
        mock_consolidation.total_revenue = 1000000
        mock_consolidation.total_personnel_costs = 500000
        mock_consolidation.total_operating_costs = 200000
        mock_consolidation.total_capex = 100000
        mock_consolidation.net_result = 200000

        mock_instance.get_consolidation.return_value = mock_consolidation
        mock_class.return_value = mock_instance

        # Make request
        response = client.get(f"/api/v1/export/budget/{version_id}/excel")

        # Verify mock was called
        assert mock_instance.get_consolidation.called
        # Response should be 200 (Excel file) or 501 (if openpyxl not installed)
        assert response.status_code in (200, 501)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
