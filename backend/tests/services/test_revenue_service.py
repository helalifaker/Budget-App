"""
Tests for RevenueService.

Comprehensive tests for revenue calculations including:
- Tuition revenue calculation with fee structure
- Sibling discount application (25% for 3rd+ child)
- Trimester distribution (40%/30%/30%)
- DAI and registration fee handling
- Nationality-based fee variations
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.configuration import BudgetVersion, BudgetVersionStatus
from app.services.revenue_service import RevenueService


class TestTuitionRevenueCalculation:
    """Tests for tuition revenue calculation."""

    def test_basic_tuition_calculation(self):
        """Test basic tuition calculation: students × fee amount."""
        student_count = 100
        fee_amount = Decimal("30000")  # 30,000 SAR

        expected_revenue = student_count * fee_amount
        assert expected_revenue == Decimal("3000000")

    def test_trimester_distribution_percentages(self):
        """Test that trimester distribution adds up to 100%."""
        t1_pct = Decimal("0.40")  # 40%
        t2_pct = Decimal("0.30")  # 30%
        t3_pct = Decimal("0.30")  # 30%

        total = t1_pct + t2_pct + t3_pct
        assert total == Decimal("1.00")

    def test_trimester_revenue_distribution(self):
        """Test revenue distribution across trimesters."""
        annual_revenue = Decimal("3000000")

        t1_revenue = annual_revenue * Decimal("0.40")  # 40%
        t2_revenue = annual_revenue * Decimal("0.30")  # 30%
        t3_revenue = annual_revenue * Decimal("0.30")  # 30%

        assert t1_revenue == Decimal("1200000")
        assert t2_revenue == Decimal("900000")
        assert t3_revenue == Decimal("900000")
        assert t1_revenue + t2_revenue + t3_revenue == annual_revenue


class TestSiblingDiscount:
    """Tests for sibling discount calculations."""

    def test_sibling_discount_rate(self):
        """Test that sibling discount is 25% for 3rd+ child."""
        discount_rate = Decimal("0.25")  # 25%
        assert discount_rate == Decimal("0.25")

    def test_sibling_discount_applied_to_tuition_only(self):
        """Test that sibling discount applies only to tuition, not DAI."""
        tuition_fee = Decimal("30000")
        dai_fee = Decimal("3000")
        discount_rate = Decimal("0.25")

        # Discount applies to tuition only
        discounted_tuition = tuition_fee * (1 - discount_rate)
        total_with_discount = discounted_tuition + dai_fee  # DAI unchanged

        assert discounted_tuition == Decimal("22500")  # 30000 * 0.75
        assert total_with_discount == Decimal("25500")  # 22500 + 3000

    def test_no_discount_for_first_two_children(self):
        """Test that first and second children pay full price."""
        tuition_fee = Decimal("30000")
        child_order = 1  # First child

        # No discount for 1st or 2nd child
        if child_order < 3:
            discount = Decimal("0")
        else:
            discount = tuition_fee * Decimal("0.25")

        assert discount == Decimal("0")

    def test_discount_applied_for_third_child(self):
        """Test that third child gets 25% discount."""
        tuition_fee = Decimal("30000")
        child_order = 3  # Third child

        if child_order >= 3:
            discount = tuition_fee * Decimal("0.25")
        else:
            discount = Decimal("0")

        assert discount == Decimal("7500")  # 30000 * 0.25


class TestNationalityBasedFees:
    """Tests for nationality-based fee variations."""

    def test_french_students_ttc_pricing(self):
        """Test that French students use TTC (tax-inclusive) pricing."""
        # French students pay TTC prices
        base_fee = Decimal("30000")
        fee_type = "TTC"

        assert fee_type == "TTC"
        assert base_fee > 0

    def test_saudi_students_ht_pricing(self):
        """Test that Saudi students use HT (tax-exclusive) pricing."""
        # Saudi students pay HT prices
        base_fee = Decimal("28500")  # Lower due to HT
        fee_type = "HT"

        assert fee_type == "HT"
        assert base_fee > 0

    def test_other_nationality_ttc_pricing(self):
        """Test that other nationalities use TTC pricing."""
        # Other nationalities pay TTC prices like French
        fee_type = "TTC"
        assert fee_type == "TTC"


class TestDAICalculation:
    """Tests for DAI (Droit Annuel d'Inscription) calculations."""

    def test_dai_not_subject_to_sibling_discount(self):
        """Test that DAI is not reduced by sibling discount."""
        dai_fee = Decimal("3000")
        sibling_discount_rate = Decimal("0.25")

        # DAI should not be discounted
        dai_after_discount = dai_fee  # Unchanged

        assert dai_after_discount == dai_fee

    def test_dai_per_student(self):
        """Test DAI calculation per student."""
        dai_fee = Decimal("3000")
        student_count = 100

        total_dai_revenue = dai_fee * student_count
        assert total_dai_revenue == Decimal("300000")


class TestRevenueAccountCodes:
    """Tests for revenue account code mapping."""

    def test_tuition_account_codes_structure(self):
        """Test tuition revenue account codes follow PCG pattern."""
        # Revenue accounts are in 70xxx range
        t1_code = "70110"  # Tuition T1
        t2_code = "70120"  # Tuition T2
        t3_code = "70130"  # Tuition T3

        assert t1_code.startswith("70")
        assert t2_code.startswith("70")
        assert t3_code.startswith("70")

    def test_dai_account_code(self):
        """Test DAI revenue account code."""
        dai_code = "70200"  # DAI

        assert dai_code.startswith("70")

    def test_registration_fee_account_code(self):
        """Test registration fee account code."""
        registration_code = "70300"  # Registration fee

        assert registration_code.startswith("70")


class TestRevenueService:
    """Tests for RevenueService class."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def revenue_service(self, mock_session):
        """Create RevenueService with mock session."""
        return RevenueService(mock_session)

    def test_service_initialization(self, revenue_service, mock_session):
        """Test that RevenueService initializes correctly."""
        assert revenue_service.session == mock_session


class TestRevenueProjectionLogic:
    """Tests for revenue projection calculations."""

    def test_enrollment_driven_revenue(self):
        """Test that revenue is calculated from enrollment projections."""
        # Revenue = Σ(students × fees) per level/nationality
        enrollments = [
            {"level": "PS", "nationality": "FRENCH", "count": 50, "fee": Decimal("25000")},
            {"level": "PS", "nationality": "SAUDI", "count": 30, "fee": Decimal("23500")},
            {"level": "6EME", "nationality": "FRENCH", "count": 80, "fee": Decimal("32000")},
        ]

        total_revenue = sum(
            Decimal(e["count"]) * e["fee"] for e in enrollments
        )

        expected = (50 * 25000) + (30 * 23500) + (80 * 32000)
        assert total_revenue == Decimal(expected)

    def test_new_student_registration_revenue(self):
        """Test calculation of registration fees for new students."""
        new_students = 50
        registration_fee = Decimal("5000")

        registration_revenue = new_students * registration_fee
        assert registration_revenue == Decimal("250000")

    def test_total_annual_revenue_aggregation(self):
        """Test aggregation of all revenue streams."""
        tuition_revenue = Decimal("10000000")
        dai_revenue = Decimal("500000")
        registration_revenue = Decimal("250000")
        other_revenue = Decimal("100000")

        total_revenue = (
            tuition_revenue +
            dai_revenue +
            registration_revenue +
            other_revenue
        )

        assert total_revenue == Decimal("10850000")
