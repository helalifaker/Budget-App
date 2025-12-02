"""
Unit tests for Skolengo Integration Service
"""

import io
import uuid

import pandas as pd
import pytest
from app.services.skolengo_integration import (
    InvalidFileFormatError,
    SkolengoIntegrationService,
)
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def skolengo_service(db_session: AsyncSession):
    """Create Skolengo integration service instance."""
    return SkolengoIntegrationService(db_session)


class TestSkolengoExport:
    """Tests for enrollment export functionality."""

    async def test_export_enrollment(self, skolengo_service):
        """Test exporting enrollment to CSV."""
        version_id = uuid.uuid4()

        csv_bytes, filename = await skolengo_service.export_enrollment(version_id)

        assert isinstance(csv_bytes, bytes)
        assert filename.endswith(".csv")
        assert b"Level,Nationality,Count" in csv_bytes

        # Parse CSV to verify content
        df = pd.read_csv(io.BytesIO(csv_bytes))
        assert "Level" in df.columns
        assert "Nationality" in df.columns
        assert "Count" in df.columns


class TestSkolengoImport:
    """Tests for enrollment import functionality."""

    async def test_import_enrollment_csv(self, skolengo_service):
        """Test importing enrollment from CSV file."""
        # Create mock CSV
        csv_content = b"""Level,Nationality,Count
Maternelle-PS,French,15
Maternelle-MS,French,18
Elementaire-CP,Saudi,10
"""

        # Create UploadFile mock
        file = UploadFile(
            filename="enrollment.csv",
            file=io.BytesIO(csv_content),
        )

        version_id = uuid.uuid4()
        log_id, records_imported = await skolengo_service.import_enrollment(
            budget_version_id=version_id,
            file=file,
        )

        assert isinstance(log_id, uuid.UUID)
        assert records_imported == 3

    async def test_import_enrollment_invalid_format(self, skolengo_service):
        """Test importing with invalid file format."""
        # Create file with wrong extension
        file = UploadFile(
            filename="enrollment.txt",
            file=io.BytesIO(b"invalid content"),
        )

        version_id = uuid.uuid4()

        with pytest.raises(InvalidFileFormatError):
            await skolengo_service.import_enrollment(
                budget_version_id=version_id,
                file=file,
            )

    async def test_import_enrollment_missing_columns(self, skolengo_service):
        """Test importing CSV with missing columns."""
        csv_content = b"""Level,Count
PS,15
MS,18
"""

        file = UploadFile(
            filename="enrollment.csv",
            file=io.BytesIO(csv_content),
        )

        version_id = uuid.uuid4()

        with pytest.raises(InvalidFileFormatError):
            await skolengo_service.import_enrollment(
                budget_version_id=version_id,
                file=file,
            )


class TestLevelMapping:
    """Tests for Skolengo to EFIR level mapping."""

    def test_skolengo_to_efir_mapping(self):
        """Test level name mapping."""
        from app.services.skolengo_integration import SKOLENGO_TO_EFIR_LEVELS

        assert SKOLENGO_TO_EFIR_LEVELS["Maternelle-PS"] == "PS"
        assert SKOLENGO_TO_EFIR_LEVELS["Elementaire-CP"] == "CP"
        assert SKOLENGO_TO_EFIR_LEVELS["College-6eme"] == "6ème"
        assert SKOLENGO_TO_EFIR_LEVELS["Lycee-Terminale"] == "Terminale"


class TestEnrollmentComparison:
    """Tests for enrollment variance calculation."""

    async def test_compare_enrollments(self, skolengo_service):
        """Test enrollment comparison and variance calculation."""
        version_id = uuid.uuid4()

        comparison = await skolengo_service.compare_enrollments(version_id)

        assert "variances" in comparison
        assert "total_budget" in comparison
        assert "total_actual" in comparison
        assert "total_variance" in comparison

        # Verify variance structure
        variances = comparison["variances"]
        assert len(variances) > 0

        for variance in variances:
            assert "level" in variance
            assert "nationality" in variance
            assert "budget" in variance
            assert "actual" in variance
            assert "variance" in variance
            assert "variance_percent" in variance
