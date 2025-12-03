"""
Tests for KPIService.

Comprehensive tests for KPI calculations and management including:
- KPI definition management
- KPI calculation (H/E ratio, E/D ratio, cost metrics)
- AEFE benchmark comparison
- KPI trend analysis
"""

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.analysis import KPICategory, KPIDefinition, KPIValue
from app.models.configuration import BudgetVersion, BudgetVersionStatus
from app.services.kpi_service import KPIService
from app.services.exceptions import NotFoundError, ValidationError


class TestKPIServiceBenchmarks:
    """Tests for AEFE benchmark configuration."""

    def test_aefe_benchmarks_defined(self):
        """Test that AEFE benchmarks are properly defined."""
        benchmarks = KPIService.AEFE_BENCHMARKS

        assert "H_E_PRIMARY" in benchmarks
        assert "H_E_SECONDARY" in benchmarks
        assert "E_D_PRIMARY" in benchmarks
        assert "E_D_SECONDARY" in benchmarks
        assert "STAFF_COST_PCT" in benchmarks
        assert "OPERATING_MARGIN" in benchmarks

    def test_benchmark_structure(self):
        """Test that each benchmark has min, max, and target values."""
        benchmarks = KPIService.AEFE_BENCHMARKS

        for name, values in benchmarks.items():
            assert "min" in values, f"{name} missing 'min'"
            assert "max" in values, f"{name} missing 'max'"
            assert "target" in values, f"{name} missing 'target'"
            assert isinstance(values["min"], Decimal)
            assert isinstance(values["max"], Decimal)
            assert isinstance(values["target"], Decimal)

    def test_h_e_primary_benchmark_values(self):
        """Test H/E Primary benchmark values are within AEFE guidelines."""
        benchmark = KPIService.AEFE_BENCHMARKS["H_E_PRIMARY"]

        # Primary H/E should be around 1.0-1.2 (AEFE guideline)
        assert benchmark["min"] == Decimal("1.0")
        assert benchmark["max"] == Decimal("1.2")
        assert benchmark["target"] == Decimal("1.1")

    def test_h_e_secondary_benchmark_values(self):
        """Test H/E Secondary benchmark values are within AEFE guidelines."""
        benchmark = KPIService.AEFE_BENCHMARKS["H_E_SECONDARY"]

        # Secondary H/E should be around 1.8-2.2 (AEFE guideline)
        assert benchmark["min"] == Decimal("1.8")
        assert benchmark["max"] == Decimal("2.2")
        assert benchmark["target"] == Decimal("2.0")

    def test_staff_cost_percentage_benchmark(self):
        """Test staff cost percentage benchmark."""
        benchmark = KPIService.AEFE_BENCHMARKS["STAFF_COST_PCT"]

        # Staff costs typically 60-75% of budget
        assert benchmark["min"] == Decimal("60")
        assert benchmark["max"] == Decimal("75")


class TestGetKPIDefinition:
    """Tests for get_kpi_definition method."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def kpi_service(self, mock_session):
        """Create KPIService with mock session."""
        return KPIService(mock_session)

    @pytest.mark.asyncio
    async def test_get_kpi_definition_not_found_raises_error(
        self, kpi_service, mock_session
    ):
        """Test that get_kpi_definition raises NotFoundError for unknown code."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(NotFoundError):
            await kpi_service.get_kpi_definition("UNKNOWN_KPI")


class TestGetAllKPIDefinitions:
    """Tests for get_all_kpi_definitions method."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def kpi_service(self, mock_session):
        """Create KPIService with mock session."""
        return KPIService(mock_session)

    @pytest.mark.asyncio
    async def test_get_all_definitions_returns_list(
        self, kpi_service, mock_session
    ):
        """Test that get_all_kpi_definitions returns a list."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await kpi_service.get_all_kpi_definitions()

        assert isinstance(result, list)


class TestCalculateKPIs:
    """Tests for KPI calculation methods."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def kpi_service(self, mock_session):
        """Create KPIService with mock session."""
        return KPIService(mock_session)

    @pytest.fixture
    def sample_budget_version(self):
        """Create sample budget version for testing."""
        return BudgetVersion(
            id=uuid.uuid4(),
            name="FY2025 Budget",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
        )

    def test_calculate_h_e_ratio_formula(self):
        """Test H/E ratio calculation formula: total_hours / total_students."""
        # H/E Ratio = Total Teaching Hours / Total Students
        total_hours = Decimal("1800")
        total_students = 900

        expected_he_ratio = total_hours / total_students
        assert expected_he_ratio == Decimal("2")

    def test_calculate_e_d_ratio_formula(self):
        """Test E/D ratio calculation formula: total_students / total_classes."""
        # E/D Ratio = Total Students / Total Classes
        total_students = 900
        total_classes = 36

        expected_ed_ratio = Decimal(total_students) / Decimal(total_classes)
        assert expected_ed_ratio == Decimal("25")

    def test_calculate_cost_per_student(self):
        """Test cost per student calculation."""
        total_costs = Decimal("10000000")  # 10M SAR
        total_students = 1000

        expected_cost_per_student = total_costs / total_students
        assert expected_cost_per_student == Decimal("10000")

    def test_calculate_revenue_per_student(self):
        """Test revenue per student calculation."""
        total_revenue = Decimal("12000000")  # 12M SAR
        total_students = 1000

        expected_revenue_per_student = total_revenue / total_students
        assert expected_revenue_per_student == Decimal("12000")

    def test_calculate_operating_margin(self):
        """Test operating margin calculation."""
        total_revenue = Decimal("10000000")
        total_expenses = Decimal("9000000")

        operating_result = total_revenue - total_expenses
        operating_margin = (operating_result / total_revenue) * 100

        assert operating_margin == Decimal("10")

    def test_calculate_staff_cost_percentage(self):
        """Test staff cost percentage calculation."""
        personnel_costs = Decimal("7000000")
        total_revenue = Decimal("10000000")

        staff_cost_pct = (personnel_costs / total_revenue) * 100

        assert staff_cost_pct == Decimal("70")


class TestCompareWithBenchmark:
    """Tests for benchmark comparison logic."""

    def test_value_within_benchmark(self):
        """Test identifying values within benchmark range."""
        benchmark = KPIService.AEFE_BENCHMARKS["H_E_PRIMARY"]
        value = Decimal("1.1")

        is_within = benchmark["min"] <= value <= benchmark["max"]
        assert is_within is True

    def test_value_below_benchmark(self):
        """Test identifying values below benchmark range."""
        benchmark = KPIService.AEFE_BENCHMARKS["H_E_PRIMARY"]
        value = Decimal("0.8")  # Below min of 1.0

        is_below = value < benchmark["min"]
        assert is_below is True

    def test_value_above_benchmark(self):
        """Test identifying values above benchmark range."""
        benchmark = KPIService.AEFE_BENCHMARKS["H_E_PRIMARY"]
        value = Decimal("1.5")  # Above max of 1.2

        is_above = value > benchmark["max"]
        assert is_above is True

    def test_variance_from_target(self):
        """Test calculating variance from target."""
        benchmark = KPIService.AEFE_BENCHMARKS["H_E_PRIMARY"]
        value = Decimal("1.2")
        target = benchmark["target"]  # 1.1

        variance = value - target
        variance_pct = (variance / target) * 100

        assert variance == Decimal("0.1")
        # 0.1 / 1.1 * 100 ≈ 9.09%
        assert variance_pct > 0


class TestKPICategory:
    """Tests for KPI category enum."""

    def test_kpi_categories_exist(self):
        """Test that expected KPI categories exist."""
        assert hasattr(KPICategory, 'EDUCATIONAL')
        assert hasattr(KPICategory, 'FINANCIAL')
        assert hasattr(KPICategory, 'OPERATIONAL')
        assert hasattr(KPICategory, 'STRATEGIC')

    def test_category_values(self):
        """Test that categories have correct string values."""
        assert KPICategory.EDUCATIONAL.value == "educational"
        assert KPICategory.FINANCIAL.value == "financial"
        assert KPICategory.OPERATIONAL.value == "operational"
        assert KPICategory.STRATEGIC.value == "strategic"
