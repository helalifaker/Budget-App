"""
Unit Tests for Revenue Engine

Tests for tuition revenue and fee calculations.
Target Coverage: 95%+

Test Categories:
1. Sibling discount calculations
2. Tuition revenue calculations
3. Trimester distribution calculations
4. Total student revenue calculations
5. Aggregate revenue calculations
6. Revenue by level calculations
7. Revenue by category calculations
8. Tuition input validation
9. Sibling order validation
10. Trimester percentage validation
11. Edge cases and error handling
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.engine.revenue import (
    FeeCategory,
    TrimesterDistribution,
    TuitionInput,
    TuitionRevenue,
    calculate_sibling_discount,
    calculate_total_student_revenue,
    calculate_trimester_distribution,
    calculate_tuition_revenue,
    validate_sibling_order,
    validate_trimester_percentages,
    validate_tuition_input,
)
from app.engine.revenue.calculator import (
    SIBLING_DISCOUNT_RATE,
    SIBLING_DISCOUNT_THRESHOLD,
    TRIMESTER_1_PCT,
    TRIMESTER_2_PCT,
    TRIMESTER_3_PCT,
    calculate_aggregate_revenue,
    calculate_revenue_by_category,
    calculate_revenue_by_level,
)
from app.engine.revenue.validators import (
    InvalidSiblingOrderError,
    InvalidTrimesterPercentagesError,
    validate_discount_rate,
    validate_fee_category,
    validate_fee_non_negative,
    validate_revenue_positive,
    validate_trimester_distribution,
)
from pydantic import ValidationError


class TestSiblingDiscountCalculations:
    """Test sibling discount calculations."""

    def test_calculate_sibling_discount_first_child(self):
        """Test no discount for 1st child (eldest)."""
        discount = calculate_sibling_discount(Decimal("45000"), 1)

        assert discount.sibling_order == 1
        assert discount.discount_applicable is False
        assert discount.discount_rate == Decimal("0")
        assert discount.discount_amount == Decimal("0.00")
        assert discount.net_tuition == Decimal("45000.00")

    def test_calculate_sibling_discount_second_child(self):
        """Test no discount for 2nd child."""
        discount = calculate_sibling_discount(Decimal("45000"), 2)

        assert discount.sibling_order == 2
        assert discount.discount_applicable is False
        assert discount.discount_rate == Decimal("0")
        assert discount.discount_amount == Decimal("0.00")
        assert discount.net_tuition == Decimal("45000.00")

    def test_calculate_sibling_discount_third_child(self):
        """Test 25% discount for 3rd child."""
        # Real EFIR example: 45,000 SAR tuition
        discount = calculate_sibling_discount(Decimal("45000"), 3)

        assert discount.sibling_order == 3
        assert discount.discount_applicable is True
        assert discount.discount_rate == SIBLING_DISCOUNT_RATE  # 0.25
        assert discount.discount_amount == Decimal("11250.00")  # 45000 × 0.25
        assert discount.net_tuition == Decimal("33750.00")  # 45000 - 11250

    def test_calculate_sibling_discount_fourth_child(self):
        """Test 25% discount for 4th child."""
        discount = calculate_sibling_discount(Decimal("45000"), 4)

        assert discount.discount_applicable is True
        assert discount.discount_rate == Decimal("0.25")
        assert discount.discount_amount == Decimal("11250.00")
        assert discount.net_tuition == Decimal("33750.00")

    def test_calculate_sibling_discount_different_tuition_amounts(self):
        """Test sibling discount with different tuition amounts."""
        # Lower tuition (e.g., Maternelle)
        discount_low = calculate_sibling_discount(Decimal("30000"), 3)
        assert discount_low.discount_amount == Decimal("7500.00")  # 30000 × 0.25
        assert discount_low.net_tuition == Decimal("22500.00")

        # Higher tuition (e.g., Terminale)
        discount_high = calculate_sibling_discount(Decimal("50000"), 3)
        assert discount_high.discount_amount == Decimal("12500.00")  # 50000 × 0.25
        assert discount_high.net_tuition == Decimal("37500.00")


class TestTuitionRevenueCalculations:
    """Test tuition revenue calculations."""

    def test_calculate_tuition_revenue_no_discount(self):
        """Test tuition revenue calculation for 1st child (no discount)."""
        input_data = TuitionInput(
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("45000"),
            dai_fee=Decimal("2000"),
            registration_fee=Decimal("1000"),
            sibling_order=1,
        )

        result = calculate_tuition_revenue(input_data)

        assert result.level_code == "6EME"
        assert result.fee_category == FeeCategory.FRENCH_TTC
        assert result.base_tuition == Decimal("45000")
        assert result.base_dai == Decimal("2000")
        assert result.base_registration == Decimal("1000")
        assert result.sibling_discount_amount == Decimal("0.00")
        assert result.sibling_discount_rate == Decimal("0")
        assert result.net_tuition == Decimal("45000.00")
        assert result.net_dai == Decimal("2000")  # No discount on DAI
        assert result.net_registration == Decimal("1000")  # No discount on registration
        assert result.total_revenue == Decimal("48000.00")  # 45000 + 2000 + 1000

    def test_calculate_tuition_revenue_with_discount(self):
        """Test tuition revenue calculation for 3rd child (with discount)."""
        input_data = TuitionInput(
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("45000"),
            dai_fee=Decimal("2000"),
            registration_fee=Decimal("1000"),
            sibling_order=3,  # 3rd child - eligible for discount
        )

        result = calculate_tuition_revenue(input_data)

        assert result.sibling_discount_amount == Decimal("11250.00")
        assert result.sibling_discount_rate == Decimal("0.25")
        assert result.net_tuition == Decimal("33750.00")  # 45000 - 11250
        assert result.net_dai == Decimal("2000")  # DAI NOT discounted
        assert result.net_registration == Decimal("1000")  # Registration NOT discounted
        assert result.total_revenue == Decimal("36750.00")  # 33750 + 2000 + 1000

    def test_calculate_tuition_revenue_saudi_category(self):
        """Test tuition revenue for Saudi nationality (HT category)."""
        input_data = TuitionInput(
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.SAUDI_HT,
            tuition_fee=Decimal("40000"),  # Different pricing for Saudi
            dai_fee=Decimal("2000"),
            registration_fee=Decimal("1000"),
            sibling_order=1,
        )

        result = calculate_tuition_revenue(input_data)

        assert result.fee_category == FeeCategory.SAUDI_HT
        assert result.total_revenue == Decimal("43000.00")  # 40000 + 2000 + 1000

    def test_calculate_tuition_revenue_no_registration_fee(self):
        """Test tuition revenue with no registration fee (returning student)."""
        input_data = TuitionInput(
            level_id=uuid4(),
            level_code="5EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("45000"),
            dai_fee=Decimal("2000"),
            registration_fee=Decimal("0"),  # No registration fee
            sibling_order=2,
        )

        result = calculate_tuition_revenue(input_data)

        assert result.net_registration == Decimal("0")
        assert result.total_revenue == Decimal("47000.00")  # 45000 + 2000 + 0


class TestTrimesterDistributionCalculations:
    """Test trimester distribution calculations."""

    def test_calculate_trimester_distribution_standard(self):
        """Test standard trimester distribution (40%, 30%, 30%)."""
        # Real EFIR example: 45,000 SAR total revenue
        distribution = calculate_trimester_distribution(Decimal("45000"))

        assert distribution.total_revenue == Decimal("45000")
        assert distribution.trimester_1 == Decimal("18000.00")  # 45000 × 0.40
        assert distribution.trimester_2 == Decimal("13500.00")  # 45000 × 0.30
        assert distribution.trimester_3 == Decimal("13500.00")  # 45000 × 0.30
        assert distribution.t1_percentage == TRIMESTER_1_PCT
        assert distribution.t2_percentage == TRIMESTER_2_PCT
        assert distribution.t3_percentage == TRIMESTER_3_PCT

    def test_calculate_trimester_distribution_custom_percentages(self):
        """Test custom trimester distribution percentages."""
        # Custom: 50%, 25%, 25%
        distribution = calculate_trimester_distribution(
            Decimal("60000"),
            t1_pct=Decimal("0.50"),
            t2_pct=Decimal("0.25"),
            t3_pct=Decimal("0.25"),
        )

        assert distribution.trimester_1 == Decimal("30000.00")  # 60000 × 0.50
        assert distribution.trimester_2 == Decimal("15000.00")  # 60000 × 0.25
        assert distribution.trimester_3 == Decimal("15000.00")  # 60000 × 0.25

    def test_calculate_trimester_distribution_invalid_percentages(self):
        """Test validation fails when percentages don't sum to 100%."""
        # Percentages sum to 110% (invalid)
        with pytest.raises(ValueError, match="must sum to 1.00"):
            calculate_trimester_distribution(
                Decimal("45000"),
                t1_pct=Decimal("0.40"),
                t2_pct=Decimal("0.40"),
                t3_pct=Decimal("0.30"),  # Total: 1.10
            )


class TestTotalStudentRevenueCalculations:
    """Test complete student revenue calculations."""

    def test_calculate_total_student_revenue_no_discount(self):
        """Test complete revenue calculation for 1st child."""
        input_data = TuitionInput(
            student_id=uuid4(),
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("45000"),
            dai_fee=Decimal("2000"),
            registration_fee=Decimal("1000"),
            sibling_order=1,
        )

        result = calculate_total_student_revenue(input_data)

        # Verify tuition revenue
        assert result.tuition_revenue.total_revenue == Decimal("48000.00")
        assert result.sibling_discount_applied is False

        # Verify trimester distribution
        assert result.trimester_distribution.trimester_1 == Decimal("19200.00")  # 48000 × 0.40
        assert result.trimester_distribution.trimester_2 == Decimal("14400.00")  # 48000 × 0.30
        assert result.trimester_distribution.trimester_3 == Decimal("14400.00")  # 48000 × 0.30

        assert result.total_annual_revenue == Decimal("48000.00")

    def test_calculate_total_student_revenue_with_discount(self):
        """Test complete revenue calculation for 3rd child."""
        input_data = TuitionInput(
            student_id=uuid4(),
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("45000"),
            dai_fee=Decimal("2000"),
            registration_fee=Decimal("1000"),
            sibling_order=3,  # 3rd child
        )

        result = calculate_total_student_revenue(input_data)

        # Verify tuition revenue with discount
        assert result.tuition_revenue.total_revenue == Decimal("36750.00")
        assert result.sibling_discount_applied is True

        # Verify trimester distribution
        assert result.trimester_distribution.trimester_1 == Decimal("14700.00")  # 36750 × 0.40
        assert result.trimester_distribution.trimester_2 == Decimal("11025.00")  # 36750 × 0.30
        assert result.trimester_distribution.trimester_3 == Decimal("11025.00")  # 36750 × 0.30

        assert result.total_annual_revenue == Decimal("36750.00")


class TestAggregateRevenueCalculations:
    """Test aggregate revenue calculations."""

    def test_calculate_aggregate_revenue_multiple_students(self):
        """Test aggregating revenue across multiple students."""
        student1 = TuitionRevenue(
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            base_tuition=Decimal("45000"),
            base_dai=Decimal("2000"),
            base_registration=Decimal("1000"),
            net_tuition=Decimal("45000"),
            net_dai=Decimal("2000"),
            net_registration=Decimal("1000"),
            total_revenue=Decimal("48000"),
        )

        student2 = TuitionRevenue(
            level_code="5EME",
            fee_category=FeeCategory.FRENCH_TTC,
            base_tuition=Decimal("45000"),
            base_dai=Decimal("2000"),
            base_registration=Decimal("1000"),
            net_tuition=Decimal("33750"),  # With sibling discount
            net_dai=Decimal("2000"),
            net_registration=Decimal("1000"),
            total_revenue=Decimal("36750"),
        )

        student3 = TuitionRevenue(
            level_code="4EME",
            fee_category=FeeCategory.FRENCH_TTC,
            base_tuition=Decimal("45000"),
            base_dai=Decimal("2000"),
            base_registration=Decimal("0"),  # No registration
            net_tuition=Decimal("33750"),  # With sibling discount
            net_dai=Decimal("2000"),
            net_registration=Decimal("0"),
            total_revenue=Decimal("35750"),
        )

        total = calculate_aggregate_revenue([student1, student2, student3])

        # 48000 + 36750 + 35750 = 120,500
        assert total == Decimal("120500")

    def test_calculate_aggregate_revenue_empty_list(self):
        """Test aggregating with empty student list."""
        total = calculate_aggregate_revenue([])
        assert total == Decimal("0")


class TestRevenueByLevelCalculations:
    """Test revenue aggregation by level."""

    def test_calculate_revenue_by_level(self):
        """Test grouping revenue by academic level."""
        revenues = [
            TuitionRevenue(
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("48000"),
            ),
            TuitionRevenue(
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("0"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("0"),
                total_revenue=Decimal("47000"),
            ),
            TuitionRevenue(
                level_code="5EME",
                fee_category=FeeCategory.FRENCH_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("48000"),
            ),
        ]

        by_level = calculate_revenue_by_level(revenues)

        # 6EME: 48000 + 47000 = 95,000
        assert by_level["6EME"] == Decimal("95000")
        # 5EME: 48000
        assert by_level["5EME"] == Decimal("48000")

    def test_calculate_revenue_by_level_empty(self):
        """Test revenue by level with empty list."""
        by_level = calculate_revenue_by_level([])
        assert by_level == {}


class TestRevenueByCategoryCalculations:
    """Test revenue aggregation by fee category."""

    def test_calculate_revenue_by_category(self):
        """Test grouping revenue by fee category (nationality)."""
        revenues = [
            TuitionRevenue(
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("48000"),
            ),
            TuitionRevenue(
                level_code="6EME",
                fee_category=FeeCategory.SAUDI_HT,
                base_tuition=Decimal("40000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("40000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("43000"),
            ),
            TuitionRevenue(
                level_code="5EME",
                fee_category=FeeCategory.OTHER_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("48000"),
            ),
        ]

        by_category = calculate_revenue_by_category(revenues)

        assert by_category[FeeCategory.FRENCH_TTC] == Decimal("48000")
        assert by_category[FeeCategory.SAUDI_HT] == Decimal("43000")
        assert by_category[FeeCategory.OTHER_TTC] == Decimal("48000")


class TestTuitionInputValidation:
    """Test tuition input validation."""

    def test_validate_tuition_input_valid(self):
        """Test validation passes with valid input."""
        valid_input = TuitionInput(
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("45000"),
            dai_fee=Decimal("2000"),
            registration_fee=Decimal("1000"),
            sibling_order=1,
        )

        validate_tuition_input(valid_input)  # Should not raise

    def test_validate_tuition_input_negative_tuition(self):
        """Test validation fails with negative tuition."""
        with pytest.raises(ValueError):
            TuitionInput(
                level_id=uuid4(),
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                tuition_fee=Decimal("-45000"),  # Negative!
                dai_fee=Decimal("2000"),
                registration_fee=Decimal("1000"),
                sibling_order=1,
            )

    def test_validate_tuition_input_invalid_sibling_order(self):
        """Test validation fails with invalid sibling order."""
        with pytest.raises(ValueError):
            TuitionInput(
                level_id=uuid4(),
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                tuition_fee=Decimal("45000"),
                dai_fee=Decimal("2000"),
                registration_fee=Decimal("1000"),
                sibling_order=0,  # Invalid - must be >= 1
            )


class TestTuitionInputValidationErrors:
    """Test tuition input validation error paths."""

    def test_validate_tuition_input_negative_tuition_fee(self):
        """Test validation fails with negative tuition fee."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            TuitionInput(
                level_id=uuid4(),
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                tuition_fee=Decimal("-45000"),  # Invalid - Pydantic catches this
                dai_fee=Decimal("2000"),
                registration_fee=Decimal("1000"),
                sibling_order=1,
            )

    def test_validate_tuition_input_negative_dai_fee(self):
        """Test validation fails with negative DAI fee."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            TuitionInput(
                level_id=uuid4(),
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                tuition_fee=Decimal("45000"),
                dai_fee=Decimal("-2000"),  # Invalid - Pydantic catches this
                registration_fee=Decimal("1000"),
                sibling_order=1,
            )

    def test_validate_tuition_input_negative_registration_fee(self):
        """Test validation fails with negative registration fee."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            TuitionInput(
                level_id=uuid4(),
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                tuition_fee=Decimal("45000"),
                dai_fee=Decimal("2000"),
                registration_fee=Decimal("-1000"),  # Invalid - Pydantic catches this
                sibling_order=1,
            )


class TestTrimesterDistributionValidationErrors:
    """Test trimester distribution validation error paths."""

    def test_validate_trimester_distribution_negative_t1(self):
        """Test validation fails with negative trimester 1 amount."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            TrimesterDistribution(
                total_revenue=Decimal("45000"),
                trimester_1=Decimal("-18000"),  # Invalid - Pydantic catches this
                trimester_2=Decimal("13500"),
                trimester_3=Decimal("13500"),
                t1_percentage=Decimal("0.40"),
                t2_percentage=Decimal("0.30"),
                t3_percentage=Decimal("0.30"),
            )

    def test_validate_trimester_distribution_negative_t2(self):
        """Test validation fails with negative trimester 2 amount."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            TrimesterDistribution(
                total_revenue=Decimal("45000"),
                trimester_1=Decimal("18000"),
                trimester_2=Decimal("-13500"),  # Invalid - Pydantic catches this
                trimester_3=Decimal("13500"),
                t1_percentage=Decimal("0.40"),
                t2_percentage=Decimal("0.30"),
                t3_percentage=Decimal("0.30"),
            )

    def test_validate_trimester_distribution_negative_t3(self):
        """Test validation fails with negative trimester 3 amount."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            TrimesterDistribution(
                total_revenue=Decimal("45000"),
                trimester_1=Decimal("18000"),
                trimester_2=Decimal("13500"),
                trimester_3=Decimal("-13500"),  # Invalid - Pydantic catches this
                t1_percentage=Decimal("0.40"),
                t2_percentage=Decimal("0.30"),
                t3_percentage=Decimal("0.30"),
            )

    def test_validate_trimester_distribution_t1_mismatch(self):
        """Test validation fails when T1 amount doesn't match expected percentage."""
        invalid_distribution = TrimesterDistribution(
            total_revenue=Decimal("45000"),
            trimester_1=Decimal("25000"),  # Should be ~18000 (45000 × 0.40)
            trimester_2=Decimal("13500"),
            trimester_3=Decimal("13500"),
            t1_percentage=Decimal("0.40"),
            t2_percentage=Decimal("0.30"),
            t3_percentage=Decimal("0.30"),
        )

        with pytest.raises(InvalidTrimesterPercentagesError, match="Trimester 1.*doesn't match"):
            validate_trimester_distribution(invalid_distribution)

    def test_validate_trimester_distribution_t2_mismatch(self):
        """Test validation fails when T2 amount doesn't match expected percentage."""
        invalid_distribution = TrimesterDistribution(
            total_revenue=Decimal("45000"),
            trimester_1=Decimal("18000"),
            trimester_2=Decimal("20000"),  # Should be ~13500 (45000 × 0.30)
            trimester_3=Decimal("13500"),
            t1_percentage=Decimal("0.40"),
            t2_percentage=Decimal("0.30"),
            t3_percentage=Decimal("0.30"),
        )

        with pytest.raises(InvalidTrimesterPercentagesError, match="Trimester 2.*doesn't match"):
            validate_trimester_distribution(invalid_distribution)

    def test_validate_trimester_distribution_t3_mismatch(self):
        """Test validation fails when T3 amount doesn't match expected percentage."""
        invalid_distribution = TrimesterDistribution(
            total_revenue=Decimal("45000"),
            trimester_1=Decimal("18000"),
            trimester_2=Decimal("13500"),
            trimester_3=Decimal("20000"),  # Should be ~13500 (45000 × 0.30)
            t1_percentage=Decimal("0.40"),
            t2_percentage=Decimal("0.30"),
            t3_percentage=Decimal("0.30"),
        )

        with pytest.raises(InvalidTrimesterPercentagesError, match="Trimester 3.*doesn't match"):
            validate_trimester_distribution(invalid_distribution)


class TestSiblingOrderValidation:
    """Test sibling order validation."""

    def test_validate_sibling_order_valid_range(self):
        """Test validation passes for valid sibling orders."""
        validate_sibling_order(1)  # Eldest
        validate_sibling_order(3)  # 3rd (discount eligible)
        validate_sibling_order(10)  # Maximum

    def test_validate_sibling_order_below_minimum(self):
        """Test validation fails for sibling order < 1."""
        with pytest.raises(InvalidSiblingOrderError, match="between 1 and 10"):
            validate_sibling_order(0)

    def test_validate_sibling_order_above_maximum(self):
        """Test validation fails for sibling order > 10."""
        with pytest.raises(InvalidSiblingOrderError, match="between 1 and 10"):
            validate_sibling_order(15)


class TestTrimesterPercentageValidation:
    """Test trimester percentage validation."""

    def test_validate_trimester_percentages_standard(self):
        """Test validation passes for standard distribution (40/30/30)."""
        validate_trimester_percentages(
            Decimal("0.40"),
            Decimal("0.30"),
            Decimal("0.30"),
        )

    def test_validate_trimester_percentages_custom(self):
        """Test validation passes for custom distribution."""
        validate_trimester_percentages(
            Decimal("0.50"),
            Decimal("0.25"),
            Decimal("0.25"),
        )

    def test_validate_trimester_percentages_invalid_sum(self):
        """Test validation fails when percentages don't sum to 100%."""
        with pytest.raises(InvalidTrimesterPercentagesError, match="must sum to 1.00"):
            validate_trimester_percentages(
                Decimal("0.40"),
                Decimal("0.40"),
                Decimal("0.40"),  # Total: 1.20
            )

    def test_validate_trimester_distribution_valid(self):
        """Test distribution validation passes."""
        distribution = TrimesterDistribution(
            total_revenue=Decimal("45000"),
            trimester_1=Decimal("18000.00"),
            trimester_2=Decimal("13500.00"),
            trimester_3=Decimal("13500.00"),
            t1_percentage=Decimal("0.40"),
            t2_percentage=Decimal("0.30"),
            t3_percentage=Decimal("0.30"),
        )

        validate_trimester_distribution(distribution)

    def test_validate_trimester_distribution_negative_amount(self):
        """Test validation fails with negative trimester amount."""
        with pytest.raises(ValueError):
            TrimesterDistribution(
                total_revenue=Decimal("45000"),
                trimester_1=Decimal("-18000"),  # Negative!
                trimester_2=Decimal("13500"),
                trimester_3=Decimal("13500"),
            )


class TestAdditionalValidators:
    """Test additional validator functions."""

    def test_validate_fee_non_negative_valid(self):
        """Test fee validation with valid amounts."""
        validate_fee_non_negative(Decimal("0"), "Tuition")
        validate_fee_non_negative(Decimal("45000"), "Tuition")

    def test_validate_fee_non_negative_invalid(self):
        """Test fee validation fails with negative amount."""
        with pytest.raises(ValueError, match="cannot be negative"):
            validate_fee_non_negative(Decimal("-1000"), "DAI")

    def test_validate_fee_category_all_allowed(self):
        """Test fee category validation with all categories allowed."""
        validate_fee_category(FeeCategory.FRENCH_TTC)
        validate_fee_category(FeeCategory.SAUDI_HT)
        validate_fee_category(FeeCategory.OTHER_TTC)

    def test_validate_fee_category_restricted(self):
        """Test fee category validation with restricted list."""
        allowed = [FeeCategory.FRENCH_TTC, FeeCategory.OTHER_TTC]

        validate_fee_category(FeeCategory.FRENCH_TTC, allowed)  # OK

        with pytest.raises(ValueError, match="not in allowed list"):
            validate_fee_category(FeeCategory.SAUDI_HT, allowed)

    def test_validate_discount_rate_valid(self):
        """Test discount rate validation with valid rates."""
        validate_discount_rate(Decimal("0.00"))  # No discount
        validate_discount_rate(Decimal("0.25"))  # Standard sibling
        validate_discount_rate(Decimal("0.50"))  # Maximum

    def test_validate_discount_rate_invalid(self):
        """Test discount rate validation fails outside range."""
        with pytest.raises(ValueError, match="between 0 and 0.50"):
            validate_discount_rate(Decimal("0.75"))  # Too high

    def test_validate_revenue_positive_valid(self):
        """Test revenue validation with positive amounts."""
        validate_revenue_positive(Decimal("45000"))
        validate_revenue_positive(Decimal("0.01"))

    def test_validate_revenue_positive_invalid(self):
        """Test revenue validation fails with non-positive amounts."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_revenue_positive(Decimal("0"))


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""

    def test_sibling_discount_constants(self):
        """Test that sibling discount constants are correct."""
        assert SIBLING_DISCOUNT_THRESHOLD == 3  # 3rd child and above
        assert SIBLING_DISCOUNT_RATE == Decimal("0.25")  # 25%

    def test_trimester_constants(self):
        """Test that trimester constants are correct."""
        assert TRIMESTER_1_PCT == Decimal("0.40")  # 40%
        assert TRIMESTER_2_PCT == Decimal("0.30")  # 30%
        assert TRIMESTER_3_PCT == Decimal("0.30")  # 30%

    def test_tuition_calculation_zero_fees(self):
        """Test tuition calculation with zero fees."""
        input_data = TuitionInput(
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("0"),
            dai_fee=Decimal("0"),
            registration_fee=Decimal("0"),
            sibling_order=1,
        )

        result = calculate_tuition_revenue(input_data)

        assert result.total_revenue == Decimal("0.00")

    def test_trimester_distribution_zero_revenue(self):
        """Test trimester distribution with zero revenue."""
        distribution = calculate_trimester_distribution(Decimal("0"))

        assert distribution.trimester_1 == Decimal("0.00")
        assert distribution.trimester_2 == Decimal("0.00")
        assert distribution.trimester_3 == Decimal("0.00")

    def test_sibling_discount_large_tuition(self):
        """Test sibling discount with very large tuition amount."""
        # 100,000 SAR tuition (e.g., international school premium tier)
        discount = calculate_sibling_discount(Decimal("100000"), 3)

        assert discount.discount_amount == Decimal("25000.00")  # 100000 × 0.25
        assert discount.net_tuition == Decimal("75000.00")

    def test_revenue_calculation_all_fee_categories(self):
        """Test revenue calculations for all fee categories."""
        for category in [FeeCategory.FRENCH_TTC, FeeCategory.SAUDI_HT, FeeCategory.OTHER_TTC]:
            input_data = TuitionInput(
                level_id=uuid4(),
                level_code="6EME",
                fee_category=category,
                tuition_fee=Decimal("45000"),
                dai_fee=Decimal("2000"),
                registration_fee=Decimal("1000"),
                sibling_order=1,
            )

            result = calculate_tuition_revenue(input_data)

            assert result.fee_category == category
            assert result.total_revenue == Decimal("48000.00")

    def test_trimester_distribution_rounding(self):
        """Test trimester distribution handles rounding correctly."""
        # Amount that doesn't divide evenly
        distribution = calculate_trimester_distribution(Decimal("45001"))

        # Should round to 2 decimal places
        assert distribution.trimester_1 == Decimal("18000.40")  # 45001 × 0.40
        assert distribution.trimester_2 == Decimal("13500.30")  # 45001 × 0.30
        assert distribution.trimester_3 == Decimal("13500.30")  # 45001 × 0.30

        # Total should match (within 0.01 rounding difference)
        total = distribution.trimester_1 + distribution.trimester_2 + distribution.trimester_3
        assert abs(total - Decimal("45001")) <= Decimal("0.01")


class TestRevenueEdgeCases100PercentCoverage:
    """Additional edge cases for 100% Revenue calculator coverage."""

    def test_sibling_discount_10th_child_maximum_order(self):
        """Test sibling discount for 10th child (maximum sibling order)."""
        discount = calculate_sibling_discount(Decimal("45000"), 10)

        assert discount.sibling_order == 10
        assert discount.discount_applicable is True
        assert discount.discount_rate == SIBLING_DISCOUNT_RATE  # 0.25
        assert discount.discount_amount == Decimal("11250.00")  # 45000 × 0.25
        assert discount.net_tuition == Decimal("33750.00")

    def test_trimester_distribution_sum_verification_no_rounding_loss(self):
        """Test that trimesters always sum to total with no rounding loss."""
        test_amounts = [
            Decimal("45000"),
            Decimal("45001.33"),  # Odd number
            Decimal("99999.99"),
            Decimal("123456.78"),
        ]

        for amount in test_amounts:
            distribution = calculate_trimester_distribution(amount)

            total = (
                distribution.trimester_1
                + distribution.trimester_2
                + distribution.trimester_3
            )

            # Allow for 0.01 rounding difference
            assert abs(total - amount) <= Decimal("0.01")

    def test_revenue_calculation_all_fees_zero(self):
        """Test revenue calculation with all fees set to zero."""
        input_data = TuitionInput(
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("0"),
            dai_fee=Decimal("0"),
            registration_fee=Decimal("0"),
            sibling_order=1,
        )

        result = calculate_tuition_revenue(input_data)

        assert result.total_revenue == Decimal("0.00")
        assert result.base_tuition == Decimal("0")
        assert result.net_tuition == Decimal("0.00")

    def test_fee_category_enum_validation_all_categories(self):
        """Test that all fee categories are valid."""
        for category in [
            FeeCategory.FRENCH_TTC,
            FeeCategory.SAUDI_HT,
            FeeCategory.OTHER_TTC,
        ]:
            input_data = TuitionInput(
                level_id=uuid4(),
                level_code="6EME",
                fee_category=category,
                tuition_fee=Decimal("45000"),
                dai_fee=Decimal("2000"),
                registration_fee=Decimal("1000"),
                sibling_order=1,
            )

            result = calculate_tuition_revenue(input_data)

            assert result.fee_category == category
            assert result.total_revenue == Decimal("48000.00")

    def test_aggregate_revenue_empty_and_single_student(self):
        """Test aggregate revenue with empty list and single student."""
        # Empty list
        total_empty = calculate_aggregate_revenue([])
        assert total_empty == Decimal("0")

        # Single student
        single_student = TuitionRevenue(
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            base_tuition=Decimal("45000"),
            base_dai=Decimal("2000"),
            base_registration=Decimal("1000"),
            net_tuition=Decimal("45000"),
            net_dai=Decimal("2000"),
            net_registration=Decimal("1000"),
            total_revenue=Decimal("48000"),
        )

        total_single = calculate_aggregate_revenue([single_student])
        assert total_single == Decimal("48000")

    def test_revenue_by_level_unicode_level_codes(self):
        """Test revenue by level with Unicode level codes."""
        revenues = [
            TuitionRevenue(
                level_code="Terminale-ES (Économique & Social)",
                fee_category=FeeCategory.FRENCH_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("48000"),
            ),
            TuitionRevenue(
                level_code="Terminale-ES (Économique & Social)",
                fee_category=FeeCategory.FRENCH_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("0"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("0"),
                total_revenue=Decimal("47000"),
            ),
        ]

        by_level = calculate_revenue_by_level(revenues)

        # Should group by level code (even with Unicode)
        assert "Terminale-ES (Économique & Social)" in by_level
        assert by_level["Terminale-ES (Économique & Social)"] == Decimal("95000")

    def test_revenue_by_category_all_three_simultaneously(self):
        """Test revenue by category with students in all three categories."""
        revenues = [
            TuitionRevenue(
                level_code="6EME",
                fee_category=FeeCategory.FRENCH_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("48000"),
            ),
            TuitionRevenue(
                level_code="6EME",
                fee_category=FeeCategory.SAUDI_HT,
                base_tuition=Decimal("40000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("40000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("43000"),
            ),
            TuitionRevenue(
                level_code="6EME",
                fee_category=FeeCategory.OTHER_TTC,
                base_tuition=Decimal("45000"),
                base_dai=Decimal("2000"),
                base_registration=Decimal("1000"),
                net_tuition=Decimal("45000"),
                net_dai=Decimal("2000"),
                net_registration=Decimal("1000"),
                total_revenue=Decimal("48000"),
            ),
        ]

        by_category = calculate_revenue_by_category(revenues)

        # Should have all three categories
        assert len(by_category) == 3
        assert by_category[FeeCategory.FRENCH_TTC] == Decimal("48000")
        assert by_category[FeeCategory.SAUDI_HT] == Decimal("43000")
        assert by_category[FeeCategory.OTHER_TTC] == Decimal("48000")

    def test_tuition_revenue_precision_all_amounts(self):
        """Test that all amounts maintain exactly 2 decimal precision."""
        input_data = TuitionInput(
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("45000.123456"),  # More than 2 decimals
            dai_fee=Decimal("2000.999"),
            registration_fee=Decimal("1000.555"),
            sibling_order=3,  # With discount
        )

        result = calculate_tuition_revenue(input_data)

        # All amounts should be quantized to 2 decimals
        assert result.base_tuition.as_tuple().exponent == -2
        assert result.base_dai.as_tuple().exponent == -2
        assert result.base_registration.as_tuple().exponent == -2
        assert result.net_tuition.as_tuple().exponent == -2
        assert result.total_revenue.as_tuple().exponent == -2

    def test_sibling_discount_immutability_frozen_model(self):
        """Test that sibling discount results are immutable."""
        from app.engine.revenue.calculator import SiblingDiscount

        discount = SiblingDiscount(
            sibling_order=3,
            discount_applicable=True,
            discount_rate=Decimal("0.25"),
            base_tuition=Decimal("45000.00"),
            discount_amount=Decimal("11250.00"),
            net_tuition=Decimal("33750.00"),
        )

        # Pydantic frozen models should prevent modification
        with pytest.raises(ValidationError):
            discount.sibling_order = 5

    def test_total_student_revenue_consistency_verification(self):
        """Test that tuition revenue + trimester distribution totals match."""
        input_data = TuitionInput(
            student_id=uuid4(),
            level_id=uuid4(),
            level_code="6EME",
            fee_category=FeeCategory.FRENCH_TTC,
            tuition_fee=Decimal("45000"),
            dai_fee=Decimal("2000"),
            registration_fee=Decimal("1000"),
            sibling_order=3,  # With discount
        )

        result = calculate_total_student_revenue(input_data)

        # Tuition revenue total should match trimester distribution total
        assert result.tuition_revenue.total_revenue == result.trimester_distribution.total_revenue

        # Trimester distribution should sum to total (within rounding)
        trimester_sum = (
            result.trimester_distribution.trimester_1
            + result.trimester_distribution.trimester_2
            + result.trimester_distribution.trimester_3
        )

        assert abs(trimester_sum - result.total_annual_revenue) <= Decimal("0.01")

    def test_sibling_discount_rate_and_threshold_constants(self):
        """Test that sibling discount constants are correctly defined."""
        # Constants should be defined
        assert SIBLING_DISCOUNT_THRESHOLD == 3  # 3rd child+
        assert SIBLING_DISCOUNT_RATE == Decimal("0.25")  # 25%

        # Verify constants are used correctly
        discount_2nd = calculate_sibling_discount(Decimal("45000"), 2)
        assert discount_2nd.discount_applicable is False  # Before threshold

        discount_3rd = calculate_sibling_discount(Decimal("45000"), 3)
        assert discount_3rd.discount_applicable is True  # At threshold
        assert discount_3rd.discount_rate == SIBLING_DISCOUNT_RATE
