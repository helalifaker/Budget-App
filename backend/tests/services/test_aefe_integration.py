"""
Unit tests for AEFE Integration Service
"""

import io
import uuid

import pandas as pd
import pytest
from app.services.aefe_integration import (
    AEFEDataError,
    AEFEIntegrationService,
    InvalidFileFormatError,
)
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def aefe_service(db_session: AsyncSession):
    """Create AEFE integration service instance."""
    return AEFEIntegrationService(db_session)


class TestAEFEFileParsing:
    """Tests for AEFE Excel file parsing."""

    async def test_parse_aefe_file_success(self, aefe_service):
        """Test successful parsing of AEFE Excel file."""
        # Create valid Excel file
        data = {
            "Teacher Name": ["Marie Dupont", "Jean Martin", "Sophie Bernard"],
            "Category": ["Detached", "Funded", "Detached"],
            "Cycle": ["Maternelle", "Elementaire", "Secondary"],
            "PRRD Rate": [41863.0, 0.0, 41863.0],
        }

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        excel_bytes = output.getvalue()

        positions = await aefe_service.parse_aefe_file(excel_bytes, "positions.xlsx")

        assert len(positions) == 3
        assert positions[0]["teacher_name"] == "Marie Dupont"
        assert positions[0]["category"] == "Detached"
        assert positions[0]["prrd_rate"] == 41863.0
        assert positions[0]["is_aefe_funded"] is False

        assert positions[1]["is_aefe_funded"] is True  # Funded category

    async def test_parse_aefe_file_invalid_category(self, aefe_service):
        """Test parsing with invalid category."""
        data = {
            "Teacher Name": ["Test Teacher"],
            "Category": ["InvalidCategory"],
            "Cycle": ["Maternelle"],
            "PRRD Rate": [41863.0],
        }

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        excel_bytes = output.getvalue()

        with pytest.raises(AEFEDataError):
            await aefe_service.parse_aefe_file(excel_bytes, "positions.xlsx")

    async def test_parse_aefe_file_negative_prrd(self, aefe_service):
        """Test parsing with negative PRRD rate."""
        data = {
            "Teacher Name": ["Test Teacher"],
            "Category": ["Detached"],
            "Cycle": ["Maternelle"],
            "PRRD Rate": [-1000.0],
        }

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        excel_bytes = output.getvalue()

        with pytest.raises(AEFEDataError):
            await aefe_service.parse_aefe_file(excel_bytes, "positions.xlsx")

    async def test_parse_aefe_file_wrong_format(self, aefe_service):
        """Test parsing non-Excel file."""
        with pytest.raises(InvalidFileFormatError):
            await aefe_service.parse_aefe_file(b"not excel content", "file.txt")


class TestAEFEImport:
    """Tests for AEFE position import."""

    async def test_import_positions_success(self, aefe_service):
        """Test successful position import."""
        # Create valid Excel file
        data = {
            "Teacher Name": ["Marie Dupont"],
            "Category": ["Detached"],
            "Cycle": ["Maternelle"],
            "PRRD Rate": [41863.0],
        }

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        excel_bytes = output.getvalue()

        file = UploadFile(
            filename="positions.xlsx",
            file=io.BytesIO(excel_bytes),
        )

        log_id, records_imported = await aefe_service.import_positions(file=file)

        assert isinstance(log_id, uuid.UUID)
        assert records_imported == 1


class TestAEFEPositionSummary:
    """Tests for position summary functionality."""

    async def test_get_position_summary(self, aefe_service):
        """Test getting position summary."""
        summary = await aefe_service.get_position_summary()

        assert "positions" in summary
        assert "total_positions" in summary
        assert "total_aefe_funded" in summary
        assert "total_prrd_contribution" in summary

        assert isinstance(summary["total_positions"], int)
        assert isinstance(summary["total_aefe_funded"], int)
        assert isinstance(summary["total_prrd_contribution"], float)

    async def test_get_positions_list(self, aefe_service):
        """Test getting positions list."""
        positions = await aefe_service.get_positions_list()

        assert isinstance(positions, list)
        assert len(positions) > 0

        for position in positions:
            assert "category" in position
            assert "cycle" in position
            assert "prrd_rate" in position
            assert "is_aefe_funded" in position


class TestAEFETemplate:
    """Tests for template export."""

    async def test_export_positions_template(self, aefe_service):
        """Test exporting position template."""
        excel_bytes, filename = await aefe_service.export_positions_template()

        assert isinstance(excel_bytes, bytes)
        assert filename.endswith(".xlsx")

        # Verify template can be parsed
        df = pd.read_excel(io.BytesIO(excel_bytes))
        assert "Teacher Name" in df.columns
        assert "Category" in df.columns
        assert "Cycle" in df.columns
        assert "PRRD Rate" in df.columns


class TestAEFECategories:
    """Tests for AEFE category validation."""

    def test_valid_categories(self):
        """Test valid AEFE categories."""
        from app.services.aefe_integration import AEFE_CATEGORIES

        assert "Detached" in AEFE_CATEGORIES
        assert "Funded" in AEFE_CATEGORIES
        assert "Resident" in AEFE_CATEGORIES

    def test_valid_cycles(self):
        """Test valid cycles."""
        from app.services.aefe_integration import VALID_CYCLES

        assert "Maternelle" in VALID_CYCLES
        assert "Elementaire" in VALID_CYCLES
        assert "Secondary" in VALID_CYCLES
