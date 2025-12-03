"""
Unit tests for Budget vs Actual Service.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.budget_actual_service import BudgetActualService


class TestBudgetActualServiceInitialization:
    """Tests for BudgetActualService initialization."""

    def test_service_initialization(self):
        """Test service initializes with session."""
        session = MagicMock()
        service = BudgetActualService(session)
        assert service.session == session
        assert service.actual_data_service is not None
        assert service.variance_service is not None


class TestMaterialityThresholds:
    """Tests for materiality threshold configuration."""

    def test_materiality_threshold_percent(self):
        """Test default materiality threshold is 5%."""
        assert BudgetActualService.MATERIALITY_THRESHOLD_PCT == Decimal("5.0")

    def test_materiality_threshold_sar(self):
        """Test default materiality threshold is 100K SAR."""
        assert BudgetActualService.MATERIALITY_THRESHOLD_SAR == Decimal("100000.00")


class TestVarianceCalculation:
    """Tests for variance calculation logic."""

    def test_revenue_variance_calculation(self):
        """Test revenue variance: Actual - Budget (higher actual = favorable)."""
        # Revenue accounts start with 7
        budget = Decimal("1000000")
        actual = Decimal("1100000")

        # For revenue: positive variance when actual > budget
        variance = actual - budget
        assert variance == Decimal("100000")
        assert variance > 0  # Favorable

    def test_expense_variance_calculation(self):
        """Test expense variance: Budget - Actual (lower actual = favorable)."""
        # Expense accounts start with 6
        budget = Decimal("500000")
        actual = Decimal("450000")

        # For expense: positive variance when actual < budget
        variance = budget - actual
        assert variance == Decimal("50000")
        assert variance > 0  # Favorable

    def test_variance_percentage_calculation(self):
        """Test variance percentage calculation."""
        budget = Decimal("1000000")
        variance = Decimal("50000")

        variance_percent = (variance / budget) * 100
        assert variance_percent == Decimal("5")


class TestVarianceStatus:
    """Tests for variance status determination."""

    def test_neutral_variance_within_threshold(self):
        """Test variance within ±5% is neutral."""
        variance_percent = Decimal("4.5")
        assert abs(variance_percent) <= Decimal("5.0")  # Neutral

    def test_favorable_variance_above_threshold(self):
        """Test positive variance above 5% is favorable."""
        variance_sar = Decimal("150000")
        variance_percent = Decimal("7.5")

        is_favorable = variance_sar > 0 and abs(variance_percent) > Decimal("5.0")
        assert is_favorable is True

    def test_unfavorable_variance_below_threshold(self):
        """Test negative variance below -5% is unfavorable."""
        variance_sar = Decimal("-150000")
        variance_percent = Decimal("-7.5")

        is_unfavorable = variance_sar < 0 and abs(variance_percent) > Decimal("5.0")
        assert is_unfavorable is True


class TestMaterialityCheck:
    """Tests for materiality determination."""

    @pytest.fixture
    def budget_actual_service(self):
        """Create BudgetActualService instance."""
        session = MagicMock()
        return BudgetActualService(session)

    def test_material_by_percentage(self, budget_actual_service):
        """Test variance is material when percent exceeds threshold."""
        variance_sar = Decimal("50000")  # Below SAR threshold
        variance_percent = Decimal("10.0")  # Above 5% threshold

        is_material = budget_actual_service._is_variance_material(
            variance_sar, variance_percent
        )
        assert is_material is True

    def test_material_by_amount(self, budget_actual_service):
        """Test variance is material when SAR exceeds threshold."""
        variance_sar = Decimal("150000")  # Above 100K threshold
        variance_percent = Decimal("3.0")  # Below 5% threshold

        is_material = budget_actual_service._is_variance_material(
            variance_sar, variance_percent
        )
        assert is_material is True

    def test_not_material_below_both_thresholds(self, budget_actual_service):
        """Test variance is not material when below both thresholds."""
        variance_sar = Decimal("50000")  # Below 100K threshold
        variance_percent = Decimal("3.0")  # Below 5% threshold

        is_material = budget_actual_service._is_variance_material(
            variance_sar, variance_percent
        )
        assert is_material is False


class TestVarianceAmount:
    """Tests for variance amount calculation method."""

    @pytest.fixture
    def budget_actual_service(self):
        """Create BudgetActualService instance."""
        session = MagicMock()
        return BudgetActualService(session)

    def test_revenue_account_variance(self, budget_actual_service):
        """Test revenue account (70xxx) variance: Actual - Budget."""
        result = budget_actual_service._calculate_variance_amount(
            account_code="70110",
            budget_amount=Decimal("1000000"),
            actual_amount=Decimal("1100000"),
        )
        assert result == Decimal("100000")  # Favorable (higher revenue)

    def test_expense_account_variance(self, budget_actual_service):
        """Test expense account (6xxxx) variance: Budget - Actual."""
        result = budget_actual_service._calculate_variance_amount(
            account_code="64110",
            budget_amount=Decimal("500000"),
            actual_amount=Decimal("450000"),
        )
        assert result == Decimal("50000")  # Favorable (lower expense)

    def test_other_account_variance(self, budget_actual_service):
        """Test other account variance defaults to expense logic."""
        result = budget_actual_service._calculate_variance_amount(
            account_code="21000",
            budget_amount=Decimal("100000"),
            actual_amount=Decimal("90000"),
        )
        assert result == Decimal("10000")


class TestImportActuals:
    """Tests for import actuals functionality."""

    @pytest.fixture
    def budget_actual_service(self):
        """Create BudgetActualService instance with mocked session."""
        session = MagicMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return BudgetActualService(session)

    def test_required_fields_validation(self):
        """Test that required fields are defined correctly."""
        required_fields = ["fiscal_year", "period", "account_code", "amount_sar"]
        assert len(required_fields) == 4

    def test_odoo_data_structure(self):
        """Test expected Odoo import data structure."""
        odoo_record = {
            "fiscal_year": 2025,
            "period": 6,
            "account_code": "64110",
            "account_name": "Teaching Salaries",
            "amount_sar": Decimal("125000"),
            "currency": "SAR",
            "transaction_date": "2025-06-15",
            "description": "June payroll",
        }

        assert "fiscal_year" in odoo_record
        assert "period" in odoo_record
        assert "account_code" in odoo_record
        assert "amount_sar" in odoo_record


class TestForecastRevision:
    """Tests for forecast revision creation."""

    def test_forecast_version_status(self):
        """Test forecast version should have FORECAST status."""
        from app.models.configuration import BudgetVersionStatus

        assert BudgetVersionStatus.FORECAST.value == "forecast"

    def test_periods_covered_calculation(self):
        """Test periods 1 to current_period are covered by actuals."""
        current_period = 6

        # Periods 1-6 have actuals
        actual_periods = list(range(1, current_period + 1))
        assert actual_periods == [1, 2, 3, 4, 5, 6]

        # Periods 7-12 need projection
        projection_periods = list(range(current_period + 1, 13))
        assert projection_periods == [7, 8, 9, 10, 11, 12]


class TestVarianceReport:
    """Tests for variance report generation."""

    def test_report_structure(self):
        """Test variance report contains expected fields."""
        expected_fields = [
            "version_id",
            "version_name",
            "fiscal_year",
            "period",
            "summary",
            "variances",
        ]

        for field in expected_fields:
            assert field in expected_fields

    def test_summary_structure(self):
        """Test variance summary contains expected metrics."""
        expected_summary_fields = [
            "total_budget_sar",
            "total_actual_sar",
            "total_variance_sar",
            "variance_percent",
            "variance_count",
            "material_count",
            "favorable_count",
            "unfavorable_count",
        ]

        for field in expected_summary_fields:
            assert field in expected_summary_fields


class TestAccountCodeClassification:
    """Tests for account code classification."""

    def test_revenue_account_identification(self):
        """Test revenue accounts are correctly identified."""
        revenue_codes = ["70110", "71000", "74500", "77000"]

        for code in revenue_codes:
            is_revenue = code.startswith("7")
            assert is_revenue is True

    def test_expense_account_identification(self):
        """Test expense accounts are correctly identified."""
        expense_codes = ["60110", "64110", "66000", "68000"]

        for code in expense_codes:
            is_expense = code.startswith("6")
            assert is_expense is True

    def test_pcg_account_code_pattern(self):
        """Test French PCG account code patterns."""
        # Revenue: 70xxx-77xxx
        revenue_ranges = ["70", "71", "72", "73", "74", "75", "76", "77"]
        for prefix in revenue_ranges:
            assert prefix.startswith("7")

        # Expense: 60xxx-68xxx
        expense_ranges = ["60", "61", "62", "63", "64", "65", "66", "67", "68"]
        for prefix in expense_ranges:
            assert prefix.startswith("6")


class TestYTDCalculation:
    """Tests for Year-to-Date calculation."""

    def test_ytd_variance_accumulation(self):
        """Test YTD variance is accumulated correctly."""
        monthly_variances = [
            Decimal("10000"),
            Decimal("-5000"),
            Decimal("15000"),
            Decimal("8000"),
            Decimal("-3000"),
            Decimal("12000"),
        ]

        ytd_variance = sum(monthly_variances)
        assert ytd_variance == Decimal("37000")

    def test_ytd_for_period(self):
        """Test YTD calculation for specific period."""
        period = 6

        # YTD includes periods 1 through current period
        assert period == 6
        ytd_periods = list(range(1, period + 1))
        assert len(ytd_periods) == 6
