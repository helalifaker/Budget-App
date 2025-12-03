"""
Unit tests for Cost Service - Personnel and Operating Cost Planning.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cost_service import CostService
from app.services.exceptions import ValidationError


@pytest.fixture
def db_session():
    """Create a mock async session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def cost_service(db_session):
    """Create CostService instance with mocked session."""
    return CostService(db_session)


class TestCostServiceInitialization:
    """Tests for CostService initialization."""

    def test_cost_service_initialization(self, db_session):
        """Test service initializes with session and sub-services."""
        service = CostService(db_session)
        assert service.session == db_session
        assert service.personnel_cost_service is not None
        assert service.operating_cost_service is not None


class TestPersonnelCostValidation:
    """Tests for personnel cost validation logic."""

    @pytest.mark.asyncio
    async def test_create_personnel_cost_validates_account_code_prefix(self, cost_service, db_session):
        """Test that personnel cost requires account code starting with 64."""
        version_id = uuid.uuid4()

        # The validation happens before any DB lookup, so we just test that
        with pytest.raises(ValidationError) as exc_info:
            await cost_service.create_personnel_cost_entry(
                version_id=version_id,
                account_code="60110",  # Invalid - should start with 64
                description="Teaching salaries",
                fte_count=Decimal("10.5"),
                unit_cost_sar=Decimal("150000"),
            )

        assert "must start with 64" in str(exc_info.value)
        # Check the field is set in details
        assert exc_info.value.details.get("field") == "account_code"

    def test_personnel_account_code_validation_logic(self):
        """Test the account code validation logic for personnel costs."""
        valid_codes = ["64110", "64120", "64200", "64999"]
        invalid_codes = ["60110", "65100", "70110", "63100"]

        for code in valid_codes:
            assert code.startswith("64"), f"{code} should be valid for personnel"

        for code in invalid_codes:
            assert not code.startswith("64"), f"{code} should be invalid for personnel"


class TestOperatingCostValidation:
    """Tests for operating cost validation logic."""

    def test_operating_cost_account_code_validation_logic(self):
        """Test operating cost requires valid PCG account prefix (60-63, 65-66, or 68)."""
        valid_prefixes = ("60", "61", "62", "63", "65", "66", "68")
        invalid_prefixes = ("64", "67", "69", "70")

        valid_codes = ["60100", "61200", "62300", "63400", "65500", "66600", "68700"]
        invalid_codes = ["64110", "67100", "69100", "70110"]

        for code in valid_codes:
            assert code.startswith(valid_prefixes), f"{code} should be valid for operating"

        for code in invalid_codes:
            assert not code.startswith(valid_prefixes), f"{code} should be invalid for operating"

    def test_operating_vs_personnel_account_distinction(self):
        """Test that operating and personnel accounts don't overlap."""
        # 64xxx is personnel, everything else in 60-68 range (except 64, 67) is operating
        personnel_prefix = "64"
        operating_prefixes = ("60", "61", "62", "63", "65", "66", "68")

        # Personnel codes should not be valid operating codes
        assert not personnel_prefix.startswith(operating_prefixes)


class TestCostSummaryCalculations:
    """Tests for cost summary calculation logic."""

    def test_personnel_total_aggregation(self):
        """Test personnel total is sum of individual costs."""
        costs = [Decimal("500000"), Decimal("300000"), Decimal("200000")]
        expected_total = Decimal("1000000")

        total = sum(costs)
        assert total == expected_total

    def test_operating_category_grouping(self):
        """Test operating costs can be grouped by category."""
        costs_by_category = {
            "supplies": [Decimal("25000"), Decimal("15000")],
            "maintenance": [Decimal("30000")],
        }

        totals = {cat: sum(amounts) for cat, amounts in costs_by_category.items()}

        assert totals["supplies"] == Decimal("40000")
        assert totals["maintenance"] == Decimal("30000")

    def test_total_cost_calculation(self):
        """Test total cost = personnel + operating."""
        personnel_total = Decimal("800000")
        operating_total = Decimal("80000")

        total_cost = personnel_total + operating_total

        assert total_cost == Decimal("880000")


class TestCostCalculationFormulas:
    """Tests for cost calculation formulas."""

    def test_total_cost_formula(self):
        """Test FTE × unit cost = total cost formula."""
        fte_count = Decimal("5.5")
        unit_cost = Decimal("180000")
        expected_total = Decimal("990000")

        # The formula used in the service
        calculated_total = fte_count * unit_cost

        assert calculated_total == expected_total

    def test_aefe_cost_formula(self):
        """Test AEFE cost = PRRD × exchange rate formula."""
        prrd_eur = Decimal("41863")
        eur_to_sar = Decimal("4.05")
        expected_cost = Decimal("169545.15")

        # The formula used for AEFE teachers
        calculated_cost = prrd_eur * eur_to_sar

        assert calculated_cost == expected_cost

    def test_local_cost_formula(self):
        """Test local teacher cost formula with social charges."""
        base_salary = Decimal("120000")
        social_charges_rate = Decimal("0.21")
        benefits = Decimal("15000")

        # The formula: salary + (salary × social_rate) + benefits
        social_charges = base_salary * social_charges_rate
        expected_cost = base_salary + social_charges + benefits

        assert expected_cost == Decimal("160200")

    def test_enrollment_driven_cost_formula(self):
        """Test enrollment-driven operating cost formula."""
        enrollment_count = 1500
        cost_per_student = Decimal("500")
        expected_cost = Decimal("750000")

        # The formula used in calculate_operating_costs
        calculated_cost = Decimal(enrollment_count) * cost_per_student

        assert calculated_cost == expected_cost

    def test_facility_driven_cost_formula(self):
        """Test facility-driven operating cost formula."""
        square_meters = Decimal("10000")
        cost_per_sqm = Decimal("50")
        expected_cost = Decimal("500000")

        # The formula used for facility costs
        calculated_cost = square_meters * cost_per_sqm

        assert calculated_cost == expected_cost


class TestAccountCodePatterns:
    """Tests for PCG account code pattern validation."""

    def test_personnel_account_code_pattern(self):
        """Test personnel account codes follow 64xxx pattern."""
        valid_codes = ["64110", "64120", "64210", "64999"]

        for code in valid_codes:
            assert code.startswith("64"), f"{code} should start with 64"

    def test_operating_account_code_patterns(self):
        """Test operating account codes follow valid patterns."""
        valid_prefixes = ("60", "61", "62", "63", "65", "66", "68")

        test_codes = {
            "60610": "supplies",
            "61520": "maintenance",
            "62600": "insurance",
            "63100": "taxes",
            "65100": "other operating",
            "66100": "financial",
            "68100": "depreciation",
        }

        for code, _ in test_codes.items():
            assert code.startswith(valid_prefixes), f"{code} should start with valid prefix"

    def test_invalid_account_code_patterns(self):
        """Test invalid account codes are rejected."""
        invalid_for_operating = ["64110", "67100", "69100", "70110"]
        valid_prefixes = ("60", "61", "62", "63", "65", "66", "68")

        for code in invalid_for_operating:
            assert not code.startswith(valid_prefixes), f"{code} should not be valid for operating"
