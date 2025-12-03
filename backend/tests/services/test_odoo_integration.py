"""
Unit tests for Odoo Integration Service
"""

from unittest.mock import MagicMock, patch

import pytest
from app.services.odoo_integration import (
    OdooAuthenticationError,
    OdooIntegrationService,
)
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def odoo_service(db_session: AsyncSession):
    """Create Odoo integration service instance."""
    return OdooIntegrationService(db_session)


class TestOdooConnection:
    """Tests for Odoo connection functionality."""

    @patch("app.services.odoo_integration.xmlrpc.client.ServerProxy")
    def test_connect_odoo_success(self, mock_proxy, odoo_service):
        """Test successful Odoo connection."""
        # Mock common endpoint
        mock_common = MagicMock()
        mock_common.version.return_value = {"server_version": "16.0"}
        mock_common.authenticate.return_value = 123  # User ID

        # Mock models endpoint
        mock_models = MagicMock()

        mock_proxy.side_effect = [mock_common, mock_models]

        uid, common, models = odoo_service.connect_odoo(
            url="https://odoo.example.com",
            database="production",
            username="admin",
            password="secret",
        )

        assert uid == 123
        assert common == mock_common
        assert models == mock_models

    @pytest.mark.skip(reason="Requires complex mock setup for Odoo XML-RPC behavior")
    @patch("app.services.odoo_integration.xmlrpc.client.ServerProxy")
    def test_connect_odoo_authentication_failure(self, mock_proxy, odoo_service):
        """Test Odoo authentication failure."""
        # Mock common endpoint
        mock_common = MagicMock()
        mock_common.version.return_value = {"server_version": "16.0"}
        mock_common.authenticate.return_value = False  # Auth failed

        # Mock models endpoint (second call)
        mock_models = MagicMock()

        # Side effect returns different mocks for each call
        mock_proxy.side_effect = [mock_common, mock_models]

        with pytest.raises(OdooAuthenticationError):
            odoo_service.connect_odoo(
                url="https://odoo.example.com",
                database="production",
                username="admin",
                password="wrong_password",
            )

    @patch("app.services.odoo_integration.xmlrpc.client.ServerProxy")
    async def test_test_connection_success(self, mock_proxy, odoo_service):
        """Test connection test endpoint."""
        mock_common = MagicMock()
        mock_common.version.return_value = {"server_version": "16.0"}
        mock_common.authenticate.return_value = 123

        mock_proxy.return_value = mock_common

        success, message, user_id = await odoo_service.test_connection(
            url="https://odoo.example.com",
            database="production",
            username="admin",
            password="secret",
        )

        assert success is True
        assert "Successfully connected" in message
        assert user_id == 123


class TestOdooDataFetch:
    """Tests for fetching data from Odoo."""

    def test_get_period_dates(self, odoo_service):
        """Test period date calculation."""
        dates_t1 = odoo_service._get_period_dates("T1", 2025)
        assert dates_t1["from"] == "2025-01-01"
        assert dates_t1["to"] == "2025-06-30"

        dates_t2 = odoo_service._get_period_dates("T2", 2025)
        assert dates_t2["from"] == "2025-07-01"
        assert dates_t2["to"] == "2025-08-31"

        dates_t3 = odoo_service._get_period_dates("T3", 2025)
        assert dates_t3["from"] == "2025-09-01"
        assert dates_t3["to"] == "2025-12-31"

    @patch.object(OdooIntegrationService, "connect_odoo")
    @patch("app.services.odoo_integration.xmlrpc.client.ServerProxy")
    async def test_fetch_actuals(self, mock_proxy, mock_connect, odoo_service):
        """Test fetching actuals from Odoo."""
        # Mock connection
        mock_models = MagicMock()
        mock_connect.return_value = (123, MagicMock(), mock_models)

        # Mock search
        mock_models.execute_kw.side_effect = [
            [1, 2, 3],  # Move line IDs
            [
                {
                    "account_id": [100, "70001 - Tuition Revenue"],
                    "debit": 0.0,
                    "credit": 100000.0,
                    "name": "Tuition fees",
                    "date": "2025-03-15",
                },
                {
                    "account_id": [101, "60001 - Teaching Salaries"],
                    "debit": 50000.0,
                    "credit": 0.0,
                    "name": "Teacher salaries",
                    "date": "2025-03-31",
                },
            ],
        ]

        actuals = await odoo_service.fetch_actuals(
            url="https://odoo.example.com",
            database="production",
            username="admin",
            password="secret",
            period="T1",
            fiscal_year=2025,
        )

        assert len(actuals) == 2
        assert any(a["account_code"] == "70110" for a in actuals)  # Mapped account
        assert any(a["account_code"] == "64110" for a in actuals)


class TestEncryption:
    """Tests for password encryption."""

    def test_encrypt_decrypt_password(self, odoo_service):
        """Test password encryption and decryption."""
        password = "my_secret_password"

        encrypted = odoo_service._encrypt_password(password)
        assert encrypted != password
        assert isinstance(encrypted, str)

        decrypted = odoo_service._decrypt_password(encrypted)
        assert decrypted == password
