"""
Tests for Historical Import Service

Tests cover:
- Module detection from column headers
- CSV and Excel file parsing
- Validation logic (valid rows, invalid rows, warnings)
- Import execution with upsert behavior
- Template generation
- Error handling
"""

from __future__ import annotations

import io
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.admin.historical_import_service import (
    DHG_COLUMNS,
    ENROLLMENT_COLUMNS,
    FINANCIAL_COLUMNS,
    HistoricalImportService,
    ImportModule,
    ImportPreviewResult,
    ImportResult,
    ImportResultStatus,
    ImportStatus,
    generate_template,
)


class TestImportModuleEnum:
    """Tests for ImportModule enum."""

    def test_enrollment_module(self):
        """Test enrollment module value."""
        assert ImportModule.ENROLLMENT.value == "enrollment"

    def test_dhg_module(self):
        """Test DHG module value."""
        assert ImportModule.DHG.value == "dhg"

    def test_revenue_module(self):
        """Test revenue module value."""
        assert ImportModule.REVENUE.value == "revenue"

    def test_costs_module(self):
        """Test costs module value."""
        assert ImportModule.COSTS.value == "costs"

    def test_capex_module(self):
        """Test CapEx module value."""
        assert ImportModule.CAPEX.value == "capex"


class TestImportStatusEnum:
    """Tests for ImportStatus enum."""

    def test_valid_status(self):
        """Test valid status value."""
        assert ImportStatus.VALID.value == "valid"

    def test_warning_status(self):
        """Test warning status value."""
        assert ImportStatus.WARNING.value == "warning"

    def test_error_status(self):
        """Test error status value."""
        assert ImportStatus.ERROR.value == "error"


class TestColumnMappings:
    """Tests for column mapping constants."""

    def test_enrollment_columns_required(self):
        """Test enrollment required columns are defined."""
        assert "level_code" in ENROLLMENT_COLUMNS
        assert "student_count" in ENROLLMENT_COLUMNS

    def test_dhg_columns_required(self):
        """Test DHG required columns are defined."""
        assert "subject_code" in DHG_COLUMNS
        assert "fte_count" in DHG_COLUMNS

    def test_financial_columns_required(self):
        """Test financial required columns are defined."""
        assert "account_code" in FINANCIAL_COLUMNS
        assert "annual_amount" in FINANCIAL_COLUMNS

    def test_enrollment_columns_has_alternates(self):
        """Test enrollment columns have alternate names."""
        # Each column should have a list of possible names
        assert isinstance(ENROLLMENT_COLUMNS["level_code"], list)
        assert len(ENROLLMENT_COLUMNS["level_code"]) > 1


class TestTemplateGeneration:
    """Tests for Excel template generation."""

    def test_generate_enrollment_template(self):
        """Test generating enrollment template."""
        template_bytes = generate_template(ImportModule.ENROLLMENT)
        assert isinstance(template_bytes, bytes)
        assert len(template_bytes) > 0

    def test_generate_dhg_template(self):
        """Test generating DHG template."""
        template_bytes = generate_template(ImportModule.DHG)
        assert isinstance(template_bytes, bytes)
        assert len(template_bytes) > 0

    def test_generate_revenue_template(self):
        """Test generating revenue template."""
        template_bytes = generate_template(ImportModule.REVENUE)
        assert isinstance(template_bytes, bytes)
        assert len(template_bytes) > 0

    def test_generate_costs_template(self):
        """Test generating costs template."""
        template_bytes = generate_template(ImportModule.COSTS)
        assert isinstance(template_bytes, bytes)
        assert len(template_bytes) > 0

    def test_generate_capex_template(self):
        """Test generating CapEx template."""
        template_bytes = generate_template(ImportModule.CAPEX)
        assert isinstance(template_bytes, bytes)
        assert len(template_bytes) > 0

    def test_template_is_valid_xlsx(self):
        """Test that generated template is valid xlsx format."""
        from openpyxl import load_workbook

        template_bytes = generate_template(ImportModule.ENROLLMENT)
        wb = load_workbook(io.BytesIO(template_bytes))
        assert wb.active is not None
        # Check headers exist
        headers = [cell.value for cell in wb.active[1]]
        assert "fiscal_year" in headers
        assert "level_code" in headers


class TestImportPreviewResult:
    """Tests for ImportPreviewResult model."""

    def test_preview_result_creation(self):
        """Test creating a preview result."""
        result = ImportPreviewResult(
            fiscal_year=2024,
            detected_module="enrollment",
            total_rows=10,
            valid_rows=8,
            invalid_rows=2,
            warnings=["Row 5: High student count"],
            errors=["Row 8: Missing level_code"],
            sample_data=[{"level_code": "6EME", "student_count": 120}],
            can_import=True,
        )
        assert result.fiscal_year == 2024
        assert result.detected_module == "enrollment"
        assert result.total_rows == 10
        assert result.valid_rows == 8
        assert result.invalid_rows == 2
        assert result.can_import is True

    def test_cannot_import_when_errors(self):
        """Test can_import is False when there are errors."""
        result = ImportPreviewResult(
            fiscal_year=2024,
            detected_module="enrollment",
            total_rows=10,
            valid_rows=5,
            invalid_rows=5,
            warnings=[],
            errors=["Row 1: Error", "Row 2: Error"],
            sample_data=[],
            can_import=False,
        )
        assert result.can_import is False
        assert len(result.errors) == 2


class TestImportResult:
    """Tests for ImportResult model."""

    def test_success_result(self):
        """Test successful import result."""
        result = ImportResult(
            fiscal_year=2024,
            module="enrollment",
            status=ImportResultStatus.SUCCESS,
            imported_count=10,
            updated_count=0,
            skipped_count=0,
            error_count=0,
            message="Import successful",
            errors=[],
        )
        assert result.status == ImportResultStatus.SUCCESS
        assert result.imported_count == 10
        assert result.fiscal_year == 2024
        assert result.module == "enrollment"

    def test_partial_success_result(self):
        """Test partial success import result."""
        result = ImportResult(
            fiscal_year=2024,
            module="enrollment",
            status=ImportResultStatus.PARTIAL,
            imported_count=8,
            updated_count=0,
            skipped_count=2,
            error_count=2,
            message="Import completed with some errors",
            errors=["Row 3: Invalid data", "Row 7: Missing field"],
        )
        assert result.status == ImportResultStatus.PARTIAL
        assert result.imported_count == 8
        assert result.skipped_count == 2

    def test_failed_result(self):
        """Test failed import result."""
        result = ImportResult(
            fiscal_year=2024,
            module="enrollment",
            status=ImportResultStatus.ERROR,
            imported_count=0,
            updated_count=0,
            skipped_count=10,
            error_count=1,
            message="Import failed",
            errors=["Database error"],
        )
        assert result.status == ImportResultStatus.ERROR


class TestHistoricalImportService:
    """Tests for HistoricalImportService class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance with mock session."""
        return HistoricalImportService(mock_session)

    def test_service_initialization(self, mock_session):
        """Test service initialization."""
        service = HistoricalImportService(mock_session)
        assert service.session == mock_session

    def test_parse_csv_content(self, service):
        """Test parsing CSV content."""
        csv_content = b"fiscal_year,level_code,student_count\n2024,6EME,120\n2024,5EME,115"
        rows = service._parse_csv(csv_content)
        assert len(rows) == 2
        assert rows[0]["level_code"] == "6EME"
        assert rows[0]["student_count"] == "120"

    def test_parse_csv_with_bom(self, service):
        """Test parsing CSV with BOM marker."""
        csv_content = b"\xef\xbb\xbffiscal_year,level_code,student_count\n2024,6EME,120"
        rows = service._parse_csv(csv_content)
        assert len(rows) == 1
        # BOM should be stripped from first header
        assert "fiscal_year" in rows[0]

    def test_detect_enrollment_module(self, service):
        """Test detecting enrollment module from rows."""
        rows = [{"level_code": "6EME", "student_count": "120"}]
        module = service._detect_module(rows)
        assert module == ImportModule.ENROLLMENT

    def test_detect_dhg_module(self, service):
        """Test detecting DHG module from rows."""
        rows = [{"subject_code": "MATH", "fte_count": "2.5"}]
        module = service._detect_module(rows)
        assert module == ImportModule.DHG

    def test_detect_financial_module_revenue(self, service):
        """Test detecting revenue module from account codes."""
        rows = [{"account_code": "70100", "annual_amount": "1000000"}]
        module = service._detect_module(rows)
        assert module == ImportModule.REVENUE

    def test_detect_financial_module_costs(self, service):
        """Test detecting costs module from account codes."""
        rows = [{"account_code": "60100", "annual_amount": "500000"}]
        module = service._detect_module(rows)
        assert module == ImportModule.COSTS

    def test_detect_default_to_enrollment(self, service):
        """Test default module detection when empty."""
        rows = []
        module = service._detect_module(rows)
        assert module == ImportModule.ENROLLMENT

    def test_validate_enrollment_record_valid(self, service):
        """Test validating a valid enrollment record."""
        row = {"level_code": "6EME", "student_count": "120"}
        result = service._validate_record(row, 1, 2024, ImportModule.ENROLLMENT)
        assert result.status == ImportStatus.VALID
        assert result.dimension_code == "6EME"
        assert result.value == 120

    def test_validate_enrollment_record_missing_level(self, service):
        """Test validating enrollment record with missing level code."""
        row = {"level_code": "", "student_count": "120"}
        result = service._validate_record(row, 1, 2024, ImportModule.ENROLLMENT)
        assert result.status == ImportStatus.ERROR
        assert "level_code" in result.message.lower()

    def test_validate_enrollment_record_invalid_count(self, service):
        """Test validating enrollment record with invalid student count."""
        row = {"level_code": "6EME", "student_count": "abc"}
        result = service._validate_record(row, 1, 2024, ImportModule.ENROLLMENT)
        assert result.status == ImportStatus.ERROR

    def test_validate_dhg_record_valid(self, service):
        """Test validating a valid DHG record."""
        row = {"subject_code": "MATH", "fte_count": "2.5"}
        result = service._validate_record(row, 1, 2024, ImportModule.DHG)
        assert result.status == ImportStatus.VALID
        assert result.dimension_code == "MATH"
        assert result.value == Decimal("2.5")

    def test_validate_financial_record_valid(self, service):
        """Test validating a valid financial record."""
        row = {"account_code": "70100", "annual_amount": "1000000"}
        result = service._validate_record(row, 1, 2024, ImportModule.REVENUE)
        assert result.status == ImportStatus.VALID
        assert result.dimension_code == "70100"

    def test_validate_financial_record_with_commas(self, service):
        """Test validating financial record with comma-formatted numbers."""
        row = {"account_code": "70100", "annual_amount": "1,000,000"}
        result = service._validate_record(row, 1, 2024, ImportModule.REVENUE)
        assert result.status == ImportStatus.VALID
        assert result.value == Decimal("1000000")

    def test_validate_financial_record_warning_wrong_prefix(self, service):
        """Test validation warns when account code prefix doesn't match module."""
        row = {"account_code": "60100", "annual_amount": "1000000"}
        result = service._validate_record(row, 1, 2024, ImportModule.REVENUE)
        assert result.status == ImportStatus.WARNING
        assert "7xxxx" in result.message

    def test_create_enrollment_record(self, service):
        """Test creating enrollment record."""
        row = {"level_code": "6EME", "student_count": "120"}
        record = service._create_record(row, 2024, ImportModule.ENROLLMENT)
        assert record is not None
        assert record.fiscal_year == 2024
        assert record.module_code == "enrollment"
        assert record.dimension_type == "level"
        assert record.dimension_code == "6EME"
        assert record.annual_count == 120

    def test_create_dhg_record(self, service):
        """Test creating DHG record."""
        row = {"subject_code": "MATH", "fte_count": "2.5"}
        record = service._create_record(row, 2024, ImportModule.DHG)
        assert record is not None
        assert record.fiscal_year == 2024
        assert record.module_code == "dhg"
        assert record.dimension_type == "subject"
        assert record.dimension_code == "MATH"
        assert record.annual_fte == Decimal("2.5")

    def test_create_revenue_record(self, service):
        """Test creating revenue record."""
        row = {"account_code": "70100", "annual_amount": "1000000"}
        record = service._create_record(row, 2024, ImportModule.REVENUE)
        assert record is not None
        assert record.fiscal_year == 2024
        assert record.module_code == "revenue"
        assert record.dimension_type == "account_code"
        assert record.dimension_code == "70100"
        assert record.annual_amount_sar == Decimal("1000000")

    def test_create_record_with_missing_data(self, service):
        """Test creating record with missing required data returns None."""
        row = {"level_code": "", "student_count": ""}
        record = service._create_record(row, 2024, ImportModule.ENROLLMENT)
        assert record is None

    @pytest.mark.asyncio
    async def test_preview_import_success(self, service):
        """Test successful preview import."""
        csv_content = b"fiscal_year,level_code,student_count\n2024,6EME,120\n2024,5EME,115"

        result = await service.preview_import(
            file_content=csv_content,
            filename="test.csv",
            fiscal_year=2024,
        )

        assert isinstance(result, ImportPreviewResult)
        assert result.fiscal_year == 2024
        assert result.detected_module == "enrollment"
        assert result.total_rows == 2
        assert result.valid_rows == 2
        assert result.can_import is True
        assert len(result.sample_data) == 2

    @pytest.mark.asyncio
    async def test_preview_import_with_errors(self, service):
        """Test preview import with validation errors."""
        csv_content = b"fiscal_year,level_code,student_count\n2024,6EME,abc\n2024,,115"

        result = await service.preview_import(
            file_content=csv_content,
            filename="test.csv",
            fiscal_year=2024,
        )

        assert isinstance(result, ImportPreviewResult)
        assert result.invalid_rows > 0
        assert result.can_import is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_preview_import_unsupported_format(self, service):
        """Test preview import with unsupported file format."""
        result = await service.preview_import(
            file_content=b"random content",
            filename="test.txt",
            fiscal_year=2024,
        )

        assert isinstance(result, ImportPreviewResult)
        assert result.total_rows == 0
        assert result.can_import is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_import_data_success(self, service, mock_session):
        """Test successful data import."""
        csv_content = b"fiscal_year,level_code,student_count\n2024,6EME,120\n2024,5EME,115"

        result = await service.import_data(
            file_content=csv_content,
            filename="test.csv",
            fiscal_year=2024,
            overwrite=False,
        )

        assert isinstance(result, ImportResult)
        assert result.status == ImportResultStatus.SUCCESS
        assert result.fiscal_year == 2024
        assert result.module == "enrollment"
        assert result.imported_count == 2
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_import_data_with_overwrite(self, service, mock_session):
        """Test import with overwrite option."""
        csv_content = b"fiscal_year,level_code,student_count\n2024,6EME,120"

        # Mock the delete operation
        mock_session.execute.return_value = MagicMock(rowcount=5)

        result = await service.import_data(
            file_content=csv_content,
            filename="test.csv",
            fiscal_year=2024,
            overwrite=True,
        )

        assert result.status == ImportResultStatus.SUCCESS
        assert result.updated_count == 5

    @pytest.mark.asyncio
    async def test_import_data_database_error(self, service, mock_session):
        """Test import handling database errors."""
        csv_content = b"fiscal_year,level_code,student_count\n2024,6EME,120"

        # Make commit fail
        mock_session.commit.side_effect = Exception("Database error")

        result = await service.import_data(
            file_content=csv_content,
            filename="test.csv",
            fiscal_year=2024,
        )

        assert result.status == ImportResultStatus.ERROR
        assert "Database error" in result.message
        mock_session.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_import_data_empty_file(self, service, mock_session):
        """Test import with empty file."""
        csv_content = b"fiscal_year,level_code,student_count\n"

        result = await service.import_data(
            file_content=csv_content,
            filename="test.csv",
            fiscal_year=2024,
        )

        assert result.status == ImportResultStatus.ERROR
        assert "No data" in result.message

    @pytest.mark.asyncio
    async def test_import_data_unsupported_format(self, service, mock_session):
        """Test import with unsupported file format."""
        result = await service.import_data(
            file_content=b"random content",
            filename="test.txt",
            fiscal_year=2024,
        )

        assert result.status == ImportResultStatus.ERROR
        assert "Unsupported" in result.message


class TestGetColumnValue:
    """Tests for _get_column_value helper."""

    @pytest.fixture
    def service(self):
        """Create service with mock session."""
        return HistoricalImportService(AsyncMock())

    def test_get_exact_column(self, service):
        """Test getting value from exact column name."""
        row = {"level_code": "6EME"}
        value = service._get_column_value(row, ["level_code"])
        assert value == "6EME"

    def test_get_alternate_column(self, service):
        """Test getting value from alternate column name."""
        row = {"level": "6EME"}
        value = service._get_column_value(row, ["level_code", "level"])
        assert value == "6EME"

    def test_get_missing_column(self, service):
        """Test getting value when column is missing."""
        row = {"other": "value"}
        value = service._get_column_value(row, ["level_code", "level"])
        assert value is None

    def test_get_column_strips_whitespace(self, service):
        """Test that column values are stripped of whitespace."""
        row = {"level_code": "  6EME  "}
        value = service._get_column_value(row, ["level_code"])
        assert value == "6EME"

    def test_get_column_empty_string(self, service):
        """Test getting empty string returns None."""
        row = {"level_code": ""}
        value = service._get_column_value(row, ["level_code"])
        assert value is None

    def test_get_column_case_insensitive(self, service):
        """Test column lookup is case insensitive."""
        row = {"Level_Code": "6EME"}
        value = service._get_column_value(row, ["level_code"])
        assert value == "6EME"
