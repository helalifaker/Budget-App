"""
Unit Tests for Enrollment Engine

Tests for enrollment projection calculations using the pure function pattern.
Target Coverage: 95%+

Test Categories:
1. Enrollment projection calculations (simple growth)
2. Retention model calculations
3. Attrition calculations
4. Multi-level totals
5. Capacity validation
6. Growth rate validation
7. Edge cases and error handling
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.engine.enrollment import (
    EnrollmentGrowthScenario,
    EnrollmentInput,
    EnrollmentProjection,
    EnrollmentProjectionResult,
    RetentionModel,
    apply_retention_model,
    calculate_attrition,
    calculate_enrollment_projection,
    validate_capacity,
    validate_growth_rate,
)
from app.engine.enrollment.calculator import (
    SCENARIO_GROWTH_RATES,
    calculate_multi_level_total,
)
from app.engine.enrollment.validators import (
    CapacityExceededError,
    InvalidGrowthRateError,
    validate_attrition_rate,
    validate_retention_rate,
    validate_total_capacity,
)


class TestEnrollmentProjectionCalculations:
    """Test enrollment projection calculations with growth scenarios."""

    def test_base_scenario_5_year_projection(self):
        """Test 5-year projection with base case scenario (4% growth)."""
        # Real EFIR data: 6ème French students
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="6EME",
            nationality="French",
            current_enrollment=120,
            growth_scenario=EnrollmentGrowthScenario.BASE,
            years_to_project=5,
        )

        result = calculate_enrollment_projection(input_data)

        # Verify result structure
        assert result.level_code == "6EME"
        assert result.nationality == "French"
        assert result.base_enrollment == 120
        assert result.scenario == EnrollmentGrowthScenario.BASE
        assert len(result.projections) == 5

        # Verify year 1 (base year - no growth)
        year1 = result.projections[0]
        assert year1.year == 1
        assert year1.projected_enrollment == 120
        assert year1.growth_rate_applied == Decimal("0.00")
        assert year1.cumulative_growth == Decimal("0.00")

        # Verify year 2 (first growth: 120 × 1.04 = 124)
        year2 = result.projections[1]
        assert year2.year == 2
        assert year2.projected_enrollment == 124  # 120 × 1.04 = 124.8 → 124 (truncated)
        assert year2.growth_rate_applied == Decimal("0.04")

        # Verify year 5 (compound: 120 × 1.04^4 ≈ 140)
        year5 = result.projections[4]
        assert year5.year == 5
        assert 139 <= year5.projected_enrollment <= 141  # Allow rounding variance

        # Verify total growth
        assert result.total_growth_students == year5.projected_enrollment - 120

    def test_conservative_scenario(self):
        """Test conservative scenario (1% growth)."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="5EME",
            nationality="Saudi",
            current_enrollment=100,
            growth_scenario=EnrollmentGrowthScenario.CONSERVATIVE,
            years_to_project=3,
        )

        result = calculate_enrollment_projection(input_data)

        # Conservative growth: 100 × 1.01^2 = 102 (year 3)
        year3 = result.projections[2]
        assert 102 <= year3.projected_enrollment <= 103

    def test_optimistic_scenario(self):
        """Test optimistic scenario (7% growth)."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="TERMINALE",
            nationality="Other",
            current_enrollment=80,
            growth_scenario=EnrollmentGrowthScenario.OPTIMISTIC,
            years_to_project=4,
        )

        result = calculate_enrollment_projection(input_data)

        # Optimistic growth: 80 × 1.07^3 ≈ 98 (year 4)
        year4 = result.projections[3]
        assert 97 <= year4.projected_enrollment <= 99

    def test_custom_growth_rate(self):
        """Test custom growth rate overrides scenario."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="CP",
            nationality="French",
            current_enrollment=150,
            growth_scenario=EnrollmentGrowthScenario.BASE,  # Will be overridden
            custom_growth_rate=Decimal("0.10"),  # 10% custom growth
            years_to_project=2,
        )

        result = calculate_enrollment_projection(input_data)

        # Custom 10% growth: 150 × 1.10 = 165 (year 2)
        year2 = result.projections[1]
        assert year2.projected_enrollment == 165

    def test_negative_growth_rate(self):
        """Test negative growth (enrollment decline)."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="CE1",
            nationality="French",
            current_enrollment=100,
            custom_growth_rate=Decimal("-0.05"),  # -5% decline
            years_to_project=3,
        )

        result = calculate_enrollment_projection(input_data)

        # Negative growth: 100 × 0.95^2 ≈ 90 (year 3)
        year3 = result.projections[2]
        assert 89 <= year3.projected_enrollment <= 91

    def test_zero_growth(self):
        """Test zero growth (stable enrollment)."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="CM2",
            nationality="Saudi",
            current_enrollment=110,
            custom_growth_rate=Decimal("0.00"),  # No growth
            years_to_project=5,
        )

        result = calculate_enrollment_projection(input_data)

        # All years should remain at 110
        for projection in result.projections:
            assert projection.projected_enrollment == 110


class TestRetentionModelCalculations:
    """Test retention and attrition modeling."""

    def test_apply_retention_model(self):
        """Test retention model calculation."""
        # Example: 95% retention, 5% attrition, 25 new students
        retention_model = RetentionModel(
            level_id=uuid4(),
            retention_rate=Decimal("0.95"),
            attrition_rate=Decimal("0.05"),
            new_student_intake=25,
        )

        next_year = apply_retention_model(120, retention_model)

        # (120 × 0.95) + 25 = 114 + 25 = 139
        assert next_year == 139

    def test_retention_model_no_new_intake(self):
        """Test retention model with no new students."""
        retention_model = RetentionModel(
            level_id=uuid4(),
            retention_rate=Decimal("0.90"),
            attrition_rate=Decimal("0.10"),
            new_student_intake=0,
        )

        next_year = apply_retention_model(100, retention_model)

        # (100 × 0.90) + 0 = 90
        assert next_year == 90

    def test_retention_model_ensures_non_negative(self):
        """Test retention model never returns negative enrollment."""
        # Use minimum valid retention (50%) to test low retention scenario
        retention_model = RetentionModel(
            level_id=uuid4(),
            retention_rate=Decimal("0.50"),
            attrition_rate=Decimal("0.50"),
            new_student_intake=5,
        )

        # (50 × 0.50) + 5 = 25 + 5 = 30
        next_year = apply_retention_model(50, retention_model)
        assert next_year == 30

        # Edge case: zero starting enrollment
        next_year = apply_retention_model(0, retention_model)
        assert next_year == 5  # Only new intake

    def test_calculate_attrition(self):
        """Test attrition calculation."""
        # 120 students, 5% attrition = 6 students leaving
        students_leaving = calculate_attrition(120, Decimal("0.05"))
        assert students_leaving == 6

        # 100 students, 10% attrition = 10 students leaving
        students_leaving = calculate_attrition(100, Decimal("0.10"))
        assert students_leaving == 10

    def test_attrition_invalid_rate(self):
        """Test attrition calculation with invalid rate."""
        # Above 50% attrition is not allowed
        with pytest.raises(ValueError, match="must be between 0 and 0.50"):
            calculate_attrition(120, Decimal("0.60"))

        # Negative attrition is not allowed
        with pytest.raises(ValueError, match="must be between 0 and 0.50"):
            calculate_attrition(120, Decimal("-0.10"))


class TestMultiLevelTotals:
    """Test multi-level enrollment calculations."""

    def test_calculate_multi_level_total(self):
        """Test summing enrollment across multiple levels."""
        # Create projections for 3 levels
        level1_result = EnrollmentProjectionResult(
            level_id=uuid4(),
            level_code="6EME",
            nationality="French",
            base_enrollment=120,
            scenario=EnrollmentGrowthScenario.BASE,
            projections=[
                EnrollmentProjection(
                    year=1,
                    projected_enrollment=120,
                    growth_rate_applied=Decimal("0.00"),
                    cumulative_growth=Decimal("0.00"),
                ),
                EnrollmentProjection(
                    year=2,
                    projected_enrollment=125,
                    growth_rate_applied=Decimal("0.04"),
                    cumulative_growth=Decimal("0.04"),
                ),
            ],
            total_growth_students=5,
            total_growth_percent=Decimal("0.04"),
        )

        level2_result = EnrollmentProjectionResult(
            level_id=uuid4(),
            level_code="5EME",
            nationality="French",
            base_enrollment=115,
            scenario=EnrollmentGrowthScenario.BASE,
            projections=[
                EnrollmentProjection(
                    year=1,
                    projected_enrollment=115,
                    growth_rate_applied=Decimal("0.00"),
                    cumulative_growth=Decimal("0.00"),
                ),
                EnrollmentProjection(
                    year=2,
                    projected_enrollment=120,
                    growth_rate_applied=Decimal("0.04"),
                    cumulative_growth=Decimal("0.04"),
                ),
            ],
            total_growth_students=5,
            total_growth_percent=Decimal("0.04"),
        )

        totals = calculate_multi_level_total([level1_result, level2_result])

        # Year 1: 120 + 115 = 235
        assert totals[1] == 235

        # Year 2: 125 + 120 = 245
        assert totals[2] == 245

    def test_calculate_multi_level_total_empty_list(self):
        """Test multi-level total with empty list."""
        totals = calculate_multi_level_total([])
        assert totals == {}


class TestCapacityValidation:
    """Test capacity validation and constraints."""

    def test_validate_capacity_success(self):
        """Test capacity validation passes when under limit."""
        validate_capacity(1850, capacity_limit=1875)  # OK
        validate_capacity(1875, capacity_limit=1875)  # Exactly at limit is OK

    def test_validate_capacity_exceeded(self):
        """Test capacity validation fails when exceeded."""
        with pytest.raises(CapacityExceededError, match="exceeds capacity"):
            validate_capacity(1900, capacity_limit=1875)

    def test_validate_total_capacity_across_levels(self):
        """Test total capacity validation across all levels."""
        # Create projections that exceed capacity in year 3
        level1 = EnrollmentProjectionResult(
            level_id=uuid4(),
            level_code="6EME",
            nationality="French",
            base_enrollment=900,
            scenario=EnrollmentGrowthScenario.BASE,
            projections=[
                EnrollmentProjection(
                    year=1,
                    projected_enrollment=900,
                    growth_rate_applied=Decimal("0.00"),
                    cumulative_growth=Decimal("0.00"),
                ),
                EnrollmentProjection(
                    year=2,
                    projected_enrollment=936,
                    growth_rate_applied=Decimal("0.04"),
                    cumulative_growth=Decimal("0.04"),
                ),
                EnrollmentProjection(
                    year=3,
                    projected_enrollment=974,
                    growth_rate_applied=Decimal("0.04"),
                    cumulative_growth=Decimal("0.0816"),
                ),
            ],
            total_growth_students=74,
            total_growth_percent=Decimal("0.0816"),
        )

        level2 = EnrollmentProjectionResult(
            level_id=uuid4(),
            level_code="5EME",
            nationality="French",
            base_enrollment=900,
            scenario=EnrollmentGrowthScenario.BASE,
            projections=[
                EnrollmentProjection(
                    year=1,
                    projected_enrollment=900,
                    growth_rate_applied=Decimal("0.00"),
                    cumulative_growth=Decimal("0.00"),
                ),
                EnrollmentProjection(
                    year=2,
                    projected_enrollment=936,
                    growth_rate_applied=Decimal("0.04"),
                    cumulative_growth=Decimal("0.04"),
                ),
                EnrollmentProjection(
                    year=3,
                    projected_enrollment=974,
                    growth_rate_applied=Decimal("0.04"),
                    cumulative_growth=Decimal("0.0816"),
                ),
            ],
            total_growth_students=74,
            total_growth_percent=Decimal("0.0816"),
        )

        # Year 3: 974 + 974 = 1948 > 1875 (exceeds capacity)
        exceeded, year, total = validate_total_capacity([level1, level2], capacity_limit=1875)

        assert exceeded is True
        assert year == 3  # First year that exceeds (year 3)
        assert total == 1948  # 974 + 974

    def test_validate_total_capacity_within_limit(self):
        """Test total capacity validation when within limits."""
        level1 = EnrollmentProjectionResult(
            level_id=uuid4(),
            level_code="6EME",
            nationality="French",
            base_enrollment=600,
            scenario=EnrollmentGrowthScenario.BASE,
            projections=[
                EnrollmentProjection(
                    year=1,
                    projected_enrollment=600,
                    growth_rate_applied=Decimal("0.00"),
                    cumulative_growth=Decimal("0.00"),
                ),
            ],
            total_growth_students=0,
            total_growth_percent=Decimal("0.00"),
        )

        level2 = EnrollmentProjectionResult(
            level_id=uuid4(),
            level_code="5EME",
            nationality="French",
            base_enrollment=500,
            scenario=EnrollmentGrowthScenario.BASE,
            projections=[
                EnrollmentProjection(
                    year=1,
                    projected_enrollment=500,
                    growth_rate_applied=Decimal("0.00"),
                    cumulative_growth=Decimal("0.00"),
                ),
            ],
            total_growth_students=0,
            total_growth_percent=Decimal("0.00"),
        )

        # Total: 600 + 500 = 1100 < 1875 (OK)
        exceeded, year, total = validate_total_capacity([level1, level2], capacity_limit=1875)

        assert exceeded is False
        assert year is None
        assert total is None

    def test_validate_total_capacity_empty_projections(self):
        """Test total capacity validation with empty projection list."""
        # Empty list should return (False, None, None) - no capacity exceeded
        exceeded, year, total = validate_total_capacity([], capacity_limit=1875)

        assert exceeded is False
        assert year is None
        assert total is None


class TestGrowthRateValidation:
    """Test growth rate validation."""

    def test_validate_growth_rate_conservative(self):
        """Test conservative scenario growth rate validation."""
        # Valid conservative rates (0% to 2%)
        validate_growth_rate(Decimal("0.00"), EnrollmentGrowthScenario.CONSERVATIVE)
        validate_growth_rate(Decimal("0.01"), EnrollmentGrowthScenario.CONSERVATIVE)
        validate_growth_rate(Decimal("0.02"), EnrollmentGrowthScenario.CONSERVATIVE)

        # Invalid conservative rate (above 2%)
        with pytest.raises(InvalidGrowthRateError, match="conservative range"):
            validate_growth_rate(Decimal("0.03"), EnrollmentGrowthScenario.CONSERVATIVE)

    def test_validate_growth_rate_base(self):
        """Test base scenario growth rate validation."""
        # Valid base rates (3% to 5%)
        validate_growth_rate(Decimal("0.03"), EnrollmentGrowthScenario.BASE)
        validate_growth_rate(Decimal("0.04"), EnrollmentGrowthScenario.BASE)
        validate_growth_rate(Decimal("0.05"), EnrollmentGrowthScenario.BASE)

        # Invalid base rate (below 3%)
        with pytest.raises(InvalidGrowthRateError, match="base range"):
            validate_growth_rate(Decimal("0.02"), EnrollmentGrowthScenario.BASE)

    def test_validate_growth_rate_optimistic(self):
        """Test optimistic scenario growth rate validation."""
        # Valid optimistic rates (6% to 8%)
        validate_growth_rate(Decimal("0.06"), EnrollmentGrowthScenario.OPTIMISTIC)
        validate_growth_rate(Decimal("0.07"), EnrollmentGrowthScenario.OPTIMISTIC)
        validate_growth_rate(Decimal("0.08"), EnrollmentGrowthScenario.OPTIMISTIC)

        # Invalid optimistic rate (above 8%)
        with pytest.raises(InvalidGrowthRateError, match="optimistic range"):
            validate_growth_rate(Decimal("0.09"), EnrollmentGrowthScenario.OPTIMISTIC)

    def test_validate_growth_rate_custom_range(self):
        """Test custom growth rate range (-50% to +100%)."""
        # Valid custom rates
        validate_growth_rate(Decimal("-0.50"))  # -50% (minimum)
        validate_growth_rate(Decimal("0.00"))  # 0%
        validate_growth_rate(Decimal("0.50"))  # 50%
        validate_growth_rate(Decimal("1.00"))  # 100% (maximum)

        # Invalid custom rates
        with pytest.raises(InvalidGrowthRateError, match="between -0.50 and 1.00"):
            validate_growth_rate(Decimal("-0.51"))  # Below minimum

        with pytest.raises(InvalidGrowthRateError, match="between -0.50 and 1.00"):
            validate_growth_rate(Decimal("1.01"))  # Above maximum


class TestRetentionAttritionValidation:
    """Test retention and attrition rate validation."""

    def test_validate_retention_rate_valid(self):
        """Test valid retention rates (50% to 100%)."""
        validate_retention_rate(Decimal("0.50"))  # 50% (minimum)
        validate_retention_rate(Decimal("0.75"))  # 75%
        validate_retention_rate(Decimal("0.95"))  # 95%
        validate_retention_rate(Decimal("1.00"))  # 100% (maximum)

    def test_validate_retention_rate_invalid(self):
        """Test invalid retention rates."""
        # Below 50% retention
        with pytest.raises(ValueError, match="must be between 0.50 and 1.00"):
            validate_retention_rate(Decimal("0.40"))

        # Above 100% retention (impossible)
        with pytest.raises(ValueError, match="must be between 0.50 and 1.00"):
            validate_retention_rate(Decimal("1.10"))

    def test_validate_attrition_rate_valid(self):
        """Test valid attrition rates (0% to 50%)."""
        validate_attrition_rate(Decimal("0.00"))  # 0% (minimum)
        validate_attrition_rate(Decimal("0.05"))  # 5%
        validate_attrition_rate(Decimal("0.25"))  # 25%
        validate_attrition_rate(Decimal("0.50"))  # 50% (maximum)

    def test_validate_attrition_rate_invalid(self):
        """Test invalid attrition rates."""
        # Negative attrition
        with pytest.raises(ValueError, match="must be between 0.00 and 0.50"):
            validate_attrition_rate(Decimal("-0.05"))

        # Above 50% attrition (catastrophic)
        with pytest.raises(ValueError, match="must be between 0.00 and 0.50"):
            validate_attrition_rate(Decimal("0.60"))


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""

    def test_zero_students_enrollment(self):
        """Test enrollment projection with zero students."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="6EME",
            nationality="French",
            current_enrollment=0,  # Zero students
            growth_scenario=EnrollmentGrowthScenario.BASE,
            years_to_project=3,
        )

        result = calculate_enrollment_projection(input_data)

        # All projections should remain at 0
        for projection in result.projections:
            assert projection.projected_enrollment == 0

    def test_single_year_projection(self):
        """Test projection for just 1 year (base year only)."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="CP",
            nationality="French",
            current_enrollment=100,
            growth_scenario=EnrollmentGrowthScenario.BASE,
            years_to_project=1,
        )

        result = calculate_enrollment_projection(input_data)

        assert len(result.projections) == 1
        assert result.projections[0].projected_enrollment == 100
        assert result.total_growth_students == 0

    def test_maximum_years_projection(self):
        """Test projection for maximum 10 years."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="TERMINALE",
            nationality="Other",
            current_enrollment=90,
            growth_scenario=EnrollmentGrowthScenario.OPTIMISTIC,
            years_to_project=10,
        )

        result = calculate_enrollment_projection(input_data)

        assert len(result.projections) == 10
        # 7% growth over 10 years: 90 × 1.07^9 ≈ 165
        year10 = result.projections[9]
        assert 164 <= year10.projected_enrollment <= 166


class TestScenarioGrowthRates:
    """Test scenario growth rate mappings."""

    def test_scenario_growth_rates_mapping(self):
        """Test that scenario growth rates are correctly defined."""
        assert SCENARIO_GROWTH_RATES[EnrollmentGrowthScenario.CONSERVATIVE] == Decimal("0.01")
        assert SCENARIO_GROWTH_RATES[EnrollmentGrowthScenario.BASE] == Decimal("0.04")
        assert SCENARIO_GROWTH_RATES[EnrollmentGrowthScenario.OPTIMISTIC] == Decimal("0.07")

    def test_custom_growth_overrides_scenario(self):
        """Test that custom growth rate overrides scenario rate."""
        input_data = EnrollmentInput(
            level_id=uuid4(),
            level_code="6EME",
            nationality="French",
            current_enrollment=100,
            growth_scenario=EnrollmentGrowthScenario.CONSERVATIVE,  # Would be 1%
            custom_growth_rate=Decimal("0.10"),  # But use 10% instead
            years_to_project=2,
        )

        result = calculate_enrollment_projection(input_data)

        # Year 2 should use 10% growth, not 1%
        year2 = result.projections[1]
        assert year2.projected_enrollment == 110  # 100 × 1.10
        assert year2.growth_rate_applied == Decimal("0.10")
