"""
Skolengo Integration Service

This service handles integration with Skolengo student information system for enrollment data.
Supports both file-based import/export (CSV) and API-based synchronization.

Workflow:
1. Export: Generate CSV file with enrollment data from budget
2. Import: Parse CSV/Excel file with actual enrollment
3. Sync: Connect to Skolengo API and fetch actual enrollment
4. Compare: Calculate variances between budget and actual enrollment
"""

import csv
import io
import uuid
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integrations import IntegrationLog, IntegrationSettings
from app.services.exceptions import IntegrationError

# Level mapping: Skolengo level name → EFIR level code
SKOLENGO_TO_EFIR_LEVELS = {
    # Maternelle
    "Maternelle-PS": "PS",
    "Maternelle-MS": "MS",
    "Maternelle-GS": "GS",
    # Élémentaire
    "Elementaire-CP": "CP",
    "Elementaire-CE1": "CE1",
    "Elementaire-CE2": "CE2",
    "Elementaire-CM1": "CM1",
    "Elementaire-CM2": "CM2",
    # Collège
    "College-6eme": "6ème",
    "College-5eme": "5ème",
    "College-4eme": "4ème",
    "College-3eme": "3ème",
    # Lycée
    "Lycee-2nde": "2nde",
    "Lycee-1ere": "1ère",
    "Lycee-Terminale": "Terminale",
}

# Reverse mapping for export
EFIR_TO_SKOLENGO_LEVELS = {v: k for k, v in SKOLENGO_TO_EFIR_LEVELS.items()}


class SkolengoConnectionError(IntegrationError):
    """Raised when Skolengo connection fails."""

    pass


class SkolengoDataError(IntegrationError):
    """Raised when Skolengo data is invalid."""

    pass


class InvalidFileFormatError(IntegrationError):
    """Raised when uploaded file format is invalid."""

    pass


class SkolengoIntegrationService:
    """Service for integrating with Skolengo student information system."""

    def __init__(self, db: AsyncSession):
        """
        Initialize Skolengo integration service.

        Args:
            db: Database session
        """
        self.db = db

    async def export_enrollment(
        self, budget_version_id: uuid.UUID
    ) -> tuple[bytes, str]:
        """
        Export enrollment data to CSV format for Skolengo.

        Args:
            budget_version_id: Budget version ID

        Returns:
            Tuple of (csv_bytes, filename)

        Raises:
            SkolengoDataError: If enrollment data cannot be exported
        """
        try:
            # TODO: Fetch enrollment data from enrollment_plans table
            # For now, generate sample data
            enrollment_data = [
                {"level": "PS", "nationality": "French", "count": 15},
                {"level": "MS", "nationality": "French", "count": 18},
                {"level": "GS", "nationality": "French", "count": 20},
                {"level": "CP", "nationality": "French", "count": 22},
                {"level": "CP", "nationality": "Saudi", "count": 8},
            ]

            # Convert to Skolengo format
            skolengo_data = []
            for record in enrollment_data:
                efir_level = record["level"]
                skolengo_level = EFIR_TO_SKOLENGO_LEVELS.get(efir_level, efir_level)

                skolengo_data.append(
                    {
                        "Level": skolengo_level,
                        "Nationality": record["nationality"],
                        "Count": record["count"],
                    }
                )

            # Generate CSV
            output = io.StringIO()
            fieldnames = ["Level", "Nationality", "Count"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(skolengo_data)

            csv_bytes = output.getvalue().encode("utf-8")
            filename = f"enrollment_export_{budget_version_id}_{uuid.uuid4().hex[:8]}.csv"

            # Log export
            log = IntegrationLog(
                integration_type="skolengo",
                action="export_enrollment",
                status="success",
                records_processed=len(skolengo_data),
                records_failed=0,
                metadata_json={
                    "budget_version_id": str(budget_version_id),
                    "filename": filename,
                },
            )
            self.db.add(log)
            await self.db.commit()

            return csv_bytes, filename

        except Exception as e:
            raise SkolengoDataError(
                f"Failed to export enrollment data: {e!s}"
            ) from e

    async def import_enrollment(
        self,
        budget_version_id: uuid.UUID,
        file: UploadFile,
        user_id: uuid.UUID | None = None,
    ) -> tuple[uuid.UUID, int]:
        """
        Import enrollment data from uploaded file.

        Args:
            budget_version_id: Budget version ID
            file: Uploaded file (CSV or Excel)
            user_id: User performing import

        Returns:
            Tuple of (log_id, records_imported)

        Raises:
            InvalidFileFormatError: If file format is invalid
            SkolengoDataError: If data is invalid
        """
        records_imported = 0
        records_failed = 0
        error_messages: list[str] = []

        try:
            # Read file content
            content = await file.read()

            # Determine file type and parse
            if file.filename and file.filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            elif file.filename and (
                file.filename.endswith(".xlsx") or file.filename.endswith(".xls")
            ):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise InvalidFileFormatError(
                    "File must be CSV or Excel format (.csv, .xlsx, .xls)"
                )

            # Validate columns
            required_columns = {"Level", "Nationality", "Count"}
            if not required_columns.issubset(df.columns):
                raise InvalidFileFormatError(
                    f"File must contain columns: {', '.join(required_columns)}"
                )

            # Process each row
            for idx, row in df.iterrows():
                try:
                    skolengo_level = str(row["Level"]).strip()
                    nationality = str(row["Nationality"]).strip()
                    count = int(row["Count"])

                    # Map Skolengo level to EFIR level
                    SKOLENGO_TO_EFIR_LEVELS.get(
                        skolengo_level, skolengo_level
                    )

                    # Validate nationality
                    if nationality not in ["French", "Saudi", "Other"]:
                        raise ValueError(f"Invalid nationality: {nationality}")

                    # Validate count
                    if count < 0:
                        raise ValueError("Count cannot be negative")

                    # TODO: Insert/update in enrollment_plans table
                    # For now, just count as imported
                    records_imported += 1

                except Exception as e:
                    records_failed += 1
                    error_messages.append(f"Row {idx + 2}: {e!s}")

            # Create integration log
            log = IntegrationLog(
                integration_type="skolengo",
                action="import_enrollment",
                status="success" if records_failed == 0 else "partial",
                records_processed=records_imported,
                records_failed=records_failed,
                error_message="\n".join(error_messages) if error_messages else None,
                metadata_json={
                    "budget_version_id": str(budget_version_id),
                    "filename": file.filename,
                },
                created_by_id=user_id,
            )

            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            return log.id, records_imported

        except InvalidFileFormatError:
            raise
        except Exception as e:
            # Log failure
            log = IntegrationLog(
                integration_type="skolengo",
                action="import_enrollment",
                status="failed",
                records_processed=0,
                records_failed=0,
                error_message=str(e),
                metadata_json={
                    "budget_version_id": str(budget_version_id),
                    "filename": file.filename if file.filename else "unknown",
                },
                created_by_id=user_id,
            )

            self.db.add(log)
            await self.db.commit()

            raise SkolengoDataError(
                f"Failed to import enrollment data: {e!s}"
            ) from e

    async def sync_enrollment(
        self, budget_version_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> tuple[uuid.UUID, int]:
        """
        Sync enrollment via Skolengo API.

        Args:
            budget_version_id: Budget version ID
            user_id: User performing sync

        Returns:
            Tuple of (log_id, records_synced)

        Raises:
            SkolengoConnectionError: If API connection fails
            SkolengoDataError: If data is invalid
        """
        # Get Skolengo settings
        stmt = select(IntegrationSettings).where(
            IntegrationSettings.integration_type == "skolengo",
            IntegrationSettings.is_active == True,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            raise SkolengoConnectionError(
                "Skolengo integration is not configured or not active"
            )

        # Extract API credentials
        config = settings.config
        api_url = config.get("api_url")
        api_key = config.get("api_key")

        if not all([api_url, api_key]):
            raise SkolengoConnectionError("Skolengo API credentials are incomplete")

        try:
            # TODO: Implement actual API call to Skolengo
            # For now, simulate API response
            records_synced = 0

            # Mock API data
            api_enrollment_data = [
                {"level": "Maternelle-PS", "nationality": "French", "count": 16},
                {"level": "Maternelle-MS", "nationality": "French", "count": 19},
            ]

            # Process API data (similar to import_enrollment)
            for record in api_enrollment_data:
                skolengo_level = record["level"]
                SKOLENGO_TO_EFIR_LEVELS.get(skolengo_level, skolengo_level)

                # TODO: Update enrollment_plans table
                records_synced += 1

            # Create integration log
            log = IntegrationLog(
                integration_type="skolengo",
                action="sync_enrollment",
                status="success",
                records_processed=records_synced,
                records_failed=0,
                metadata_json={
                    "budget_version_id": str(budget_version_id),
                    "api_url": api_url,
                },
                created_by_id=user_id,
            )

            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            # Update last sync timestamp
            settings.last_sync_at = pd.Timestamp.now()
            await self.db.commit()

            return log.id, records_synced

        except Exception as e:
            # Log failure
            log = IntegrationLog(
                integration_type="skolengo",
                action="sync_enrollment",
                status="failed",
                records_processed=0,
                records_failed=0,
                error_message=str(e),
                metadata_json={
                    "budget_version_id": str(budget_version_id),
                },
                created_by_id=user_id,
            )

            self.db.add(log)
            await self.db.commit()

            raise SkolengoConnectionError(f"API sync failed: {e!s}") from e

    async def compare_enrollments(
        self, budget_version_id: uuid.UUID
    ) -> dict[str, Any]:
        """
        Compare budget vs actual enrollment and calculate variances.

        Args:
            budget_version_id: Budget version ID

        Returns:
            Dictionary with variances by level and nationality
        """
        # TODO: Fetch budget enrollment from enrollment_plans table
        # TODO: Fetch actual enrollment from recent import/sync
        # For now, return mock variance data

        variances = [
            {
                "level": "PS",
                "nationality": "French",
                "budget": 15,
                "actual": 16,
                "variance": 1,
                "variance_percent": 6.67,
            },
            {
                "level": "MS",
                "nationality": "French",
                "budget": 18,
                "actual": 19,
                "variance": 1,
                "variance_percent": 5.56,
            },
            {
                "level": "GS",
                "nationality": "French",
                "budget": 20,
                "actual": 18,
                "variance": -2,
                "variance_percent": -10.00,
            },
        ]

        total_budget = sum(v["budget"] for v in variances)
        total_actual = sum(v["actual"] for v in variances)
        total_variance = total_actual - total_budget

        return {
            "variances": variances,
            "total_budget": total_budget,
            "total_actual": total_actual,
            "total_variance": total_variance,
        }

    async def save_settings(
        self,
        api_url: str,
        api_key: str,
        auto_sync_enabled: bool = False,
        auto_sync_interval_minutes: int | None = None,
    ) -> IntegrationSettings:
        """
        Save Skolengo API settings.

        Args:
            api_url: Skolengo API URL
            api_key: Skolengo API key
            auto_sync_enabled: Enable automatic syncing
            auto_sync_interval_minutes: Sync interval in minutes

        Returns:
            IntegrationSettings object
        """
        # Check if settings exist
        stmt = select(IntegrationSettings).where(
            IntegrationSettings.integration_type == "skolengo"
        )
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings:
            # Update existing
            settings.config = {
                "api_url": api_url,
                "api_key": api_key,
            }
            settings.auto_sync_enabled = auto_sync_enabled
            settings.auto_sync_interval_minutes = auto_sync_interval_minutes
        else:
            # Create new
            settings = IntegrationSettings(
                integration_type="skolengo",
                config={
                    "api_url": api_url,
                    "api_key": api_key,
                },
                is_active=True,
                auto_sync_enabled=auto_sync_enabled,
                auto_sync_interval_minutes=auto_sync_interval_minutes,
            )
            self.db.add(settings)

        await self.db.commit()
        await self.db.refresh(settings)

        return settings
