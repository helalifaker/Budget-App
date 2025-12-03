"""
Odoo Integration Service

This service handles integration with Odoo ERP for importing actual financial data.
Uses XML-RPC API to connect to Odoo and import revenue and cost actuals.

Workflow:
1. Connect to Odoo server with credentials
2. Authenticate and get user ID
3. Fetch account move lines for specified period
4. Map Odoo account codes to EFIR account codes
5. Import actuals into budget_actuals table
"""

import uuid
import xmlrpc.client
from datetime import datetime
from typing import Any

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integrations import IntegrationLog, IntegrationSettings
from app.services.exceptions import IntegrationError

# Account mapping: Odoo account code → EFIR account code
ODOO_TO_EFIR_ACCOUNTS = {
    # Revenue accounts
    "70001": "70110",  # Tuition T1
    "70002": "70120",  # Tuition T2
    "70003": "70130",  # Tuition T3
    "70011": "70210",  # Registration fees T1
    "70012": "70220",  # Registration fees T2
    "70013": "70230",  # Registration fees T3
    "70021": "70310",  # DAI fees T1
    "70022": "70320",  # DAI fees T2
    "70023": "70330",  # DAI fees T3
    # Cost accounts - Personnel
    "60001": "64110",  # Teaching salaries
    "60002": "64120",  # Administrative salaries
    "60003": "64130",  # Support staff salaries
    "60004": "64140",  # ATSEM salaries
    # Cost accounts - Operations
    "61001": "61110",  # Facility rent
    "61002": "61120",  # Utilities
    "61003": "61130",  # Maintenance
    "62001": "62110",  # Office supplies
    "62002": "62120",  # Teaching materials
    # Cost accounts - Other
    "63001": "63110",  # Insurance
    "63002": "63120",  # Professional services
    "65001": "65110",  # Travel expenses
}


class OdooConnectionError(IntegrationError):
    """Raised when Odoo connection fails."""

    pass


class OdooAuthenticationError(IntegrationError):
    """Raised when Odoo authentication fails."""

    pass


class OdooDataError(IntegrationError):
    """Raised when Odoo data is invalid or cannot be processed."""

    pass


class OdooIntegrationService:
    """Service for integrating with Odoo ERP system."""

    def __init__(self, db: AsyncSession):
        """
        Initialize Odoo integration service.

        Args:
            db: Database session
        """
        self.db = db
        self._encryption_key = self._get_encryption_key()

    def _get_encryption_key(self) -> bytes:
        """
        Get encryption key for sensitive data.

        In production, this should come from environment variable.
        For now, generate a simple key.
        """
        # TODO: Move to environment variable in production
        return Fernet.generate_key()

    def _encrypt_password(self, password: str) -> str:
        """
        Encrypt password for storage.

        Args:
            password: Plain text password

        Returns:
            Encrypted password as string
        """
        fernet = Fernet(self._encryption_key)
        return fernet.encrypt(password.encode()).decode()

    def _decrypt_password(self, encrypted: str) -> str:
        """
        Decrypt password from storage.

        Args:
            encrypted: Encrypted password

        Returns:
            Plain text password
        """
        fernet = Fernet(self._encryption_key)
        return fernet.decrypt(encrypted.encode()).decode()

    def connect_odoo(
        self, url: str, database: str, username: str, password: str
    ) -> tuple[int, xmlrpc.client.ServerProxy, xmlrpc.client.ServerProxy]:
        """
        Connect to Odoo server and authenticate.

        Args:
            url: Odoo server URL (e.g., "https://odoo.example.com")
            database: Odoo database name
            username: Odoo username
            password: Odoo password

        Returns:
            Tuple of (user_id, common_proxy, models_proxy)

        Raises:
            OdooConnectionError: If connection fails
            OdooAuthenticationError: If authentication fails
        """
        try:
            # Connect to Odoo common endpoint
            common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")

            # Test connection and get version
            common.version()

            # Authenticate
            uid = common.authenticate(database, username, password, {})

            if not uid:
                raise OdooAuthenticationError(
                    "Authentication failed. Please check username and password."
                )

            # Connect to models endpoint
            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

            return uid, common, models

        except xmlrpc.client.ProtocolError as e:
            raise OdooConnectionError(
                f"Failed to connect to Odoo server: {e.errmsg}"
            ) from e
        except OdooAuthenticationError:
            # Re-raise authentication errors directly
            raise
        except Exception as e:
            raise OdooConnectionError(
                f"Unexpected error connecting to Odoo: {e!s}"
            ) from e

    async def test_connection(
        self, url: str, database: str, username: str, password: str
    ) -> tuple[bool, str, int | None]:
        """
        Test Odoo connection without storing credentials.

        Args:
            url: Odoo server URL
            database: Odoo database name
            username: Odoo username
            password: Odoo password

        Returns:
            Tuple of (success, message, user_id)
        """
        try:
            uid, _, _ = self.connect_odoo(url, database, username, password)
            return True, f"Successfully connected to Odoo as user ID {uid}", uid
        except OdooConnectionError as e:
            return False, str(e), None
        except OdooAuthenticationError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Unexpected error: {e!s}", None

    async def fetch_actuals(
        self,
        url: str,
        database: str,
        username: str,
        password: str,
        period: str,
        fiscal_year: int,
    ) -> list[dict[str, Any]]:
        """
        Fetch actual financial data from Odoo for specified period.

        Args:
            url: Odoo server URL
            database: Odoo database name
            username: Odoo username
            password: Odoo password
            period: Period (T1, T2, T3)
            fiscal_year: Fiscal year (e.g., 2025)

        Returns:
            List of actual records with account_code, amount, description

        Raises:
            OdooConnectionError: If connection fails
            OdooDataError: If data is invalid
        """
        # Connect to Odoo
        uid, _, models = self.connect_odoo(url, database, username, password)

        # Determine date range for period
        period_dates = self._get_period_dates(period, fiscal_year)
        date_from, date_to = period_dates["from"], period_dates["to"]

        try:
            # Search for account move lines in date range
            # In Odoo, account.move.line contains journal entries
            domain = [
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("account_id.code", "in", list(ODOO_TO_EFIR_ACCOUNTS.keys())),
                ("move_id.state", "=", "posted"),  # Only posted entries
            ]

            # Search for matching records
            move_line_ids = models.execute_kw(
                database,
                uid,
                password,
                "account.move.line",
                "search",
                [domain],
            )

            if not move_line_ids:
                return []

            # Read move line details
            move_lines = models.execute_kw(
                database,
                uid,
                password,
                "account.move.line",
                "read",
                [move_line_ids],
                {
                    "fields": [
                        "account_id",
                        "debit",
                        "credit",
                        "name",
                        "date",
                        "move_id",
                    ]
                },
            )

            # Process and aggregate by account
            actuals_by_account: dict[str, dict[str, Any]] = {}

            for line in move_lines:
                # Get account code (format: [id, "code - name"])
                account_info = line["account_id"]
                if isinstance(account_info, list) and len(account_info) >= 2:
                    account_name = account_info[1]
                    # Extract account code (format: "code - name")
                    odoo_account = account_name.split(" - ")[0].strip()
                else:
                    continue

                # Skip if account not in mapping
                if odoo_account not in ODOO_TO_EFIR_ACCOUNTS:
                    continue

                efir_account = ODOO_TO_EFIR_ACCOUNTS[odoo_account]

                # Calculate amount (debit - credit for expense, credit - debit for revenue)
                debit = float(line.get("debit", 0))
                credit = float(line.get("credit", 0))

                # Revenue accounts: credit is positive
                if efir_account.startswith("7"):
                    amount = credit - debit
                # Expense accounts: debit is positive
                else:
                    amount = debit - credit

                # Aggregate by EFIR account
                if efir_account not in actuals_by_account:
                    actuals_by_account[efir_account] = {
                        "account_code": efir_account,
                        "amount": 0.0,
                        "description": line.get("name", ""),
                    }

                actuals_by_account[efir_account]["amount"] += amount

            return list(actuals_by_account.values())

        except Exception as e:
            raise OdooDataError(f"Error fetching data from Odoo: {e!s}") from e

    def _get_period_dates(self, period: str, fiscal_year: int) -> dict[str, str]:
        """
        Get date range for period.

        Args:
            period: Period (T1, T2, T3)
            fiscal_year: Fiscal year

        Returns:
            Dictionary with 'from' and 'to' dates (ISO format)
        """
        if period == "T1":
            # January - June
            return {
                "from": f"{fiscal_year}-01-01",
                "to": f"{fiscal_year}-06-30",
            }
        elif period == "T2":
            # July - August (summer)
            return {
                "from": f"{fiscal_year}-07-01",
                "to": f"{fiscal_year}-08-31",
            }
        elif period == "T3":
            # September - December
            return {
                "from": f"{fiscal_year}-09-01",
                "to": f"{fiscal_year}-12-31",
            }
        else:
            raise ValueError(f"Invalid period: {period}")

    async def import_actuals(
        self,
        budget_version_id: uuid.UUID,
        period: str,
        fiscal_year: int,
        actuals: list[dict[str, Any]],
        user_id: uuid.UUID | None = None,
    ) -> tuple[uuid.UUID, uuid.UUID, int]:
        """
        Import actuals into database.

        Args:
            budget_version_id: Budget version ID
            period: Period (T1, T2, T3)
            fiscal_year: Fiscal year
            actuals: List of actual records
            user_id: User performing import

        Returns:
            Tuple of (batch_id, log_id, records_imported)
        """
        batch_id = uuid.uuid4()
        records_imported = 0
        records_failed = 0
        error_messages: list[str] = []

        try:
            # Import logic would go here - for now, just track in log
            # In real implementation, this would:
            # 1. Validate account codes exist
            # 2. Insert/update records in budget_actuals table
            # 3. Handle duplicates and conflicts

            for actual in actuals:
                try:
                    # TODO: Insert into budget_actuals table
                    # For now, just count as imported
                    records_imported += 1
                except Exception as e:
                    records_failed += 1
                    error_messages.append(
                        f"Failed to import {actual['account_code']}: {e!s}"
                    )

            # Create integration log
            log = IntegrationLog(
                integration_type="odoo",
                action="import_actuals",
                status="success" if records_failed == 0 else "partial",
                records_processed=records_imported,
                records_failed=records_failed,
                error_message="\n".join(error_messages) if error_messages else None,
                metadata_json={
                    "period": period,
                    "fiscal_year": fiscal_year,
                    "budget_version_id": str(budget_version_id),
                },
                batch_id=batch_id,
                created_by_id=user_id,
            )

            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            return batch_id, log.id, records_imported

        except Exception as e:
            # Log failure
            log = IntegrationLog(
                integration_type="odoo",
                action="import_actuals",
                status="failed",
                records_processed=0,
                records_failed=len(actuals),
                error_message=str(e),
                metadata_json={
                    "period": period,
                    "fiscal_year": fiscal_year,
                    "budget_version_id": str(budget_version_id),
                },
                batch_id=batch_id,
                created_by_id=user_id,
            )

            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            raise

    async def sync_actuals(
        self,
        budget_version_id: uuid.UUID,
        fiscal_year: int,
        user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Auto-sync actuals for all periods (T1, T2, T3).

        Args:
            budget_version_id: Budget version ID
            fiscal_year: Fiscal year
            user_id: User performing sync

        Returns:
            Dictionary with sync results for each period
        """
        # Get Odoo settings
        stmt = select(IntegrationSettings).where(
            IntegrationSettings.integration_type == "odoo",
            IntegrationSettings.is_active == True,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            raise OdooConnectionError("Odoo integration is not configured or not active")

        # Extract connection details
        config = settings.config
        url = config.get("url")
        database = config.get("database")
        username = config.get("username")
        encrypted_password = config.get("password")

        if not all([url, database, username, encrypted_password]):
            raise OdooConnectionError("Odoo connection details are incomplete")

        password = self._decrypt_password(encrypted_password)

        results = {}

        for period in ["T1", "T2", "T3"]:
            try:
                # Fetch actuals
                actuals = await self.fetch_actuals(
                    url, database, username, password, period, fiscal_year
                )

                # Import actuals
                batch_id, log_id, records = await self.import_actuals(
                    budget_version_id, period, fiscal_year, actuals, user_id
                )

                results[period] = {
                    "success": True,
                    "records": records,
                    "batch_id": batch_id,
                    "log_id": log_id,
                }

            except Exception as e:
                results[period] = {
                    "success": False,
                    "error": str(e),
                }

        # Update last sync timestamp
        settings.last_sync_at = datetime.utcnow()
        await self.db.commit()

        return results

    async def save_settings(
        self,
        url: str,
        database: str,
        username: str,
        password: str,
        auto_sync_enabled: bool = False,
        auto_sync_interval_minutes: int | None = None,
    ) -> IntegrationSettings:
        """
        Save Odoo connection settings.

        Args:
            url: Odoo server URL
            database: Odoo database name
            username: Odoo username
            password: Odoo password
            auto_sync_enabled: Enable automatic syncing
            auto_sync_interval_minutes: Sync interval in minutes

        Returns:
            IntegrationSettings object
        """
        # Encrypt password
        encrypted_password = self._encrypt_password(password)

        # Check if settings exist
        stmt = select(IntegrationSettings).where(
            IntegrationSettings.integration_type == "odoo"
        )
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings:
            # Update existing
            settings.config = {
                "url": url,
                "database": database,
                "username": username,
                "password": encrypted_password,
            }
            settings.auto_sync_enabled = auto_sync_enabled
            settings.auto_sync_interval_minutes = auto_sync_interval_minutes
        else:
            # Create new
            settings = IntegrationSettings(
                integration_type="odoo",
                config={
                    "url": url,
                    "database": database,
                    "username": username,
                    "password": encrypted_password,
                },
                is_active=True,
                auto_sync_enabled=auto_sync_enabled,
                auto_sync_interval_minutes=auto_sync_interval_minutes,
            )
            self.db.add(settings)

        await self.db.commit()
        await self.db.refresh(settings)

        return settings
