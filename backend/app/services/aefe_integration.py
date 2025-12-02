"""
AEFE Integration Service

This service handles integration with AEFE (Agence pour l'enseignement français à l'étranger)
for importing teacher position data and PRRD (Participation à la Rémunération des Résidents Détachés) rates.

Workflow:
1. Parse AEFE Excel file with position data
2. Validate and extract position information
3. Update teacher_cost_params with PRRD rates
4. Track AEFE-funded vs school-funded positions
5. Provide position summaries by category and cycle
"""

import io
import uuid
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integrations import IntegrationLog
from app.services.exceptions import IntegrationError


class InvalidFileFormatError(IntegrationError):
    """Raised when uploaded file format is invalid."""

    pass


class AEFEDataError(IntegrationError):
    """Raised when AEFE data is invalid."""

    pass


# Expected AEFE position categories
AEFE_CATEGORIES = [
    "Detached",  # AEFE detached teachers (school pays PRRD)
    "Funded",  # AEFE-funded teachers (no school cost)
    "Resident",  # Resident teachers (special status)
]

# Valid cycles
VALID_CYCLES = [
    "Maternelle",
    "Elementaire",
    "Secondary",  # Collège + Lycée
]


class AEFEIntegrationService:
    """Service for integrating with AEFE position data."""

    def __init__(self, db: AsyncSession):
        """
        Initialize AEFE integration service.

        Args:
            db: Database session
        """
        self.db = db

    async def parse_aefe_file(self, file_bytes: bytes, filename: str) -> list[dict[str, Any]]:
        """
        Parse AEFE Excel file and extract position data.

        Expected format:
        - Column A: Teacher Name
        - Column B: Category (Detached, Funded, Resident)
        - Column C: Cycle (Maternelle, Elementaire, Secondary)
        - Column D: PRRD Rate (EUR)

        Args:
            file_bytes: File content as bytes
            filename: Original filename

        Returns:
            List of position dictionaries

        Raises:
            InvalidFileFormatError: If file format is invalid
            AEFEDataError: If data is invalid
        """
        try:
            # Read Excel file
            if filename.endswith(".xlsx") or filename.endswith(".xls"):
                df = pd.read_excel(io.BytesIO(file_bytes))
            else:
                raise InvalidFileFormatError(
                    "File must be Excel format (.xlsx or .xls)"
                )

            # Validate columns
            required_columns = ["Teacher Name", "Category", "Cycle", "PRRD Rate"]
            if not all(col in df.columns for col in required_columns):
                raise InvalidFileFormatError(
                    f"File must contain columns: {', '.join(required_columns)}"
                )

            positions = []

            for idx, row in df.iterrows():
                try:
                    teacher_name = str(row["Teacher Name"]).strip()
                    category = str(row["Category"]).strip()
                    cycle = str(row["Cycle"]).strip()
                    prrd_rate = float(row["PRRD Rate"])

                    # Validate category
                    if category not in AEFE_CATEGORIES:
                        raise ValueError(
                            f"Invalid category '{category}'. Must be one of: {', '.join(AEFE_CATEGORIES)}"
                        )

                    # Validate cycle
                    if cycle not in VALID_CYCLES:
                        raise ValueError(
                            f"Invalid cycle '{cycle}'. Must be one of: {', '.join(VALID_CYCLES)}"
                        )

                    # Validate PRRD rate
                    if prrd_rate < 0:
                        raise ValueError("PRRD rate cannot be negative")

                    # Determine if AEFE-funded (no school cost)
                    is_aefe_funded = category == "Funded"

                    positions.append(
                        {
                            "teacher_name": teacher_name if teacher_name != "nan" else None,
                            "category": category,
                            "cycle": cycle,
                            "prrd_rate": prrd_rate,
                            "is_aefe_funded": is_aefe_funded,
                        }
                    )

                except Exception as e:
                    raise AEFEDataError(f"Error in row {idx + 2}: {e!s}") from e

            if not positions:
                raise AEFEDataError("No valid positions found in file")

            return positions

        except pd.errors.EmptyDataError:
            raise InvalidFileFormatError("File is empty") from None
        except Exception as e:
            if isinstance(e, InvalidFileFormatError | AEFEDataError):
                raise
            raise AEFEDataError(f"Failed to parse AEFE file: {e!s}") from e

    async def import_positions(
        self,
        file: UploadFile,
        user_id: uuid.UUID | None = None,
    ) -> tuple[uuid.UUID, int]:
        """
        Import AEFE positions from uploaded file.

        Args:
            file: Uploaded Excel file
            user_id: User performing import

        Returns:
            Tuple of (log_id, records_imported)

        Raises:
            InvalidFileFormatError: If file format is invalid
            AEFEDataError: If data is invalid
        """
        records_imported = 0
        records_failed = 0
        error_messages: list[str] = []

        try:
            # Read file content
            content = await file.read()

            # Parse file
            positions = await self.parse_aefe_file(
                content, file.filename or "unknown.xlsx"
            )

            # Process each position
            for position in positions:
                try:
                    # TODO: Update teacher_cost_params table with PRRD rates
                    # TODO: Store position allocations
                    # For now, just count as imported
                    records_imported += 1

                except Exception as e:
                    records_failed += 1
                    error_messages.append(
                        f"Failed to import position {position.get('teacher_name', 'Unknown')}: {e!s}"
                    )

            # Create integration log
            log = IntegrationLog(
                integration_type="aefe",
                action="import_positions",
                status="success" if records_failed == 0 else "partial",
                records_processed=records_imported,
                records_failed=records_failed,
                error_message="\n".join(error_messages) if error_messages else None,
                metadata_json={
                    "filename": file.filename,
                    "total_positions": len(positions),
                },
                created_by_id=user_id,
            )

            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            return log.id, records_imported

        except (InvalidFileFormatError, AEFEDataError):
            raise
        except Exception as e:
            # Log failure
            log = IntegrationLog(
                integration_type="aefe",
                action="import_positions",
                status="failed",
                records_processed=0,
                records_failed=0,
                error_message=str(e),
                metadata_json={
                    "filename": file.filename if file.filename else "unknown",
                },
                created_by_id=user_id,
            )

            self.db.add(log)
            await self.db.commit()

            raise AEFEDataError(f"Failed to import positions: {e!s}") from e

    async def get_position_summary(self) -> dict[str, Any]:
        """
        Get summary of AEFE positions by category and cycle.

        Returns:
            Dictionary with position summaries
        """
        # TODO: Query actual position data from database
        # For now, return mock data

        positions = [
            {
                "category": "Detached",
                "cycle": "Maternelle",
                "count": 5,
                "total_prrd": 209315.0,  # 5 × 41,863 EUR
            },
            {
                "category": "Detached",
                "cycle": "Elementaire",
                "count": 8,
                "total_prrd": 334904.0,  # 8 × 41,863 EUR
            },
            {
                "category": "Detached",
                "cycle": "Secondary",
                "count": 12,
                "total_prrd": 502356.0,  # 12 × 41,863 EUR
            },
            {
                "category": "Funded",
                "cycle": "Secondary",
                "count": 3,
                "total_prrd": 0.0,  # AEFE-funded, no cost to school
            },
        ]

        total_positions = sum(p["count"] for p in positions)
        total_aefe_funded = sum(p["count"] for p in positions if p["category"] == "Funded")
        total_prrd_contribution = sum(p["total_prrd"] for p in positions)

        return {
            "positions": positions,
            "total_positions": total_positions,
            "total_aefe_funded": total_aefe_funded,
            "total_prrd_contribution": total_prrd_contribution,
        }

    async def get_positions_list(self) -> list[dict[str, Any]]:
        """
        Get detailed list of all AEFE positions.

        Returns:
            List of position records
        """
        # TODO: Query actual position data from database
        # For now, return mock data

        positions = [
            {
                "teacher_name": "Marie Dupont",
                "category": "Detached",
                "cycle": "Maternelle",
                "prrd_rate": 41863.0,
                "is_aefe_funded": False,
            },
            {
                "teacher_name": "Jean Martin",
                "category": "Detached",
                "cycle": "Elementaire",
                "prrd_rate": 41863.0,
                "is_aefe_funded": False,
            },
            {
                "teacher_name": "Sophie Bernard",
                "category": "Funded",
                "cycle": "Secondary",
                "prrd_rate": 0.0,
                "is_aefe_funded": True,
            },
        ]

        return positions

    async def update_positions(self, positions: list[dict[str, Any]]) -> int:
        """
        Update teacher cost parameters with AEFE position data.

        Args:
            positions: List of position dictionaries

        Returns:
            Number of positions updated
        """
        # TODO: Update teacher_cost_params table
        # This would involve:
        # 1. Finding or creating teacher records
        # 2. Updating PRRD rates
        # 3. Marking AEFE-funded positions (zero cost to school)
        # 4. Tracking position allocations by cycle

        # For now, just return count
        return len(positions)

    async def export_positions_template(self) -> tuple[bytes, str]:
        """
        Export an Excel template for AEFE position import.

        Returns:
            Tuple of (excel_bytes, filename)
        """
        # Create template dataframe
        template_data = {
            "Teacher Name": [
                "Example Teacher 1",
                "Example Teacher 2",
                "Example Teacher 3",
            ],
            "Category": ["Detached", "Funded", "Detached"],
            "Cycle": ["Maternelle", "Elementaire", "Secondary"],
            "PRRD Rate": [41863.0, 0.0, 41863.0],
        }

        df = pd.DataFrame(template_data)

        # Write to Excel bytes
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="AEFE Positions")

        excel_bytes = output.getvalue()
        filename = f"aefe_positions_template_{uuid.uuid4().hex[:8]}.xlsx"

        return excel_bytes, filename
