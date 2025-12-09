"""
Unit Tests for KPI Engine

Tests for key performance indicator calculations using the pure function pattern.
Target Coverage: 95%+

Test Categories:
1. Student-Teacher Ratio calculations
2. H/E Ratio (Heures/Élève) calculations
3. Revenue per Student calculations
4. Cost per Student calculations
5. Margin Percentage calculations
6. Staff Cost Ratio calculations
7. Capacity Utilization calculations
8. All KPIs calculation
9. Input validation
10. Ratio bounds validation
11. Edge cases and error handling
"""

from datetime import UTC
from decimal import Decimal
from uuid import uuid4

import pytest
from app.engine.kpi import (
    KPIInput,
    KPIResult,
    KPIType,
    calculate_capacity_utilization,
    calculate_cost_per_student,
    calculate_he_ratio_secondary,
    calculate_margin_percentage,
    calculate_revenue_per_student,
    calculate_staff_cost_ratio,
    calculate_student_teacher_ratio,
    validate_kpi_input,
    validate_ratio_bounds,
)
from app.engine.kpi.calculator import (
    TARGET_HE_RATIO_SECONDARY,
    TARGET_MARGIN_PERCENTAGE,
    TARGET_REVENUE_PER_STUDENT,
    TARGET_STAFF_COST_RATIO,
    TARGET_STUDENT_TEACHER_RATIO,
    calculate_all_kpis,
)
from app.engine.kpi.validators import (
    InvalidKPIInputError,
    InvalidRatioBoundsError,
    validate_capacity_utilization,
    validate_he_ratio_secondary,
    validate_margin_percentage,
    validate_staff_cost_ratio,
    validate_student_teacher_ratio,
)
from pydantic import ValidationError


class TestStudentTeacherRatioCalculations:
    """Test student-teacher ratio calculations."""

    def test_calculate_student_teacher_ratio_on_target(self):
        """Test student-teacher ratio calculation at target (12.0)."""
        # Real EFIR data: 1850 students ÷ 154.2 FTE ≈ 12.0
        result = calculate_student_teacher_ratio(
            total_students=1850, total_teacher_fte=Decimal("154.17")
        )

        assert result.kpi_type == KPIType.STUDENT_TEACHER_RATIO
        assert result.value == Decimal("12.00")
        assert result.target_value == TARGET_STUDENT_TEACHER_RATIO
        assert result.unit == "ratio"
        assert abs(result.variance_from_target) <= Decimal("0.01")
        assert result.performance_status == "on_target"

    def test_calculate_student_teacher_ratio_above_target(self):
        """Test student-teacher ratio above target (worse - overcrowded)."""
        # 1850 students ÷ 120 FTE = 15.42 (above target)
        result = calculate_student_teacher_ratio(
            total_students=1850, total_teacher_fte=Decimal("120.0")
        )

        assert result.value > TARGET_STUDENT_TEACHER_RATIO
        assert result.variance_from_target > 0
        assert result.performance_status == "above_target"

    def test_calculate_student_teacher_ratio_below_target(self):
        """Test student-teacher ratio below target (better - smaller classes)."""
        # 1850 students ÷ 200 FTE = 9.25 (below target)
        result = calculate_student_teacher_ratio(
            total_students=1850, total_teacher_fte=Decimal("200.0")
        )

        assert result.value < TARGET_STUDENT_TEACHER_RATIO
        assert result.variance_from_target < 0
        assert result.performance_status == "below_target"

    def test_student_teacher_ratio_zero_teachers_error(self):
        """Test error when teacher FTE is zero (division by zero)."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_student_teacher_ratio(
                total_students=1850, total_teacher_fte=Decimal("0")
            )


class TestHERatioSecondaryCalculations:
    """Test H/E ratio (Heures/Élève) calculations for secondary."""

    def test_calculate_he_ratio_secondary_on_target(self):
        """Test H/E ratio calculation at target (1.35)."""
        # Real EFIR data: 877.5 DHG hours ÷ 650 students = 1.35
        result = calculate_he_ratio_secondary(
            dhg_hours_total=Decimal("877.5"), secondary_students=650
        )

        assert result.kpi_type == KPIType.HE_RATIO_SECONDARY
        assert result.value == Decimal("1.35")
        assert result.target_value == TARGET_HE_RATIO_SECONDARY
        assert result.unit == "ratio"
        assert result.variance_from_target == Decimal("0.00")
        assert result.performance_status == "on_target"

    def test_calculate_he_ratio_secondary_above_target(self):
        """Test H/E ratio above target (better - more hours per student)."""
        # 1000 hours ÷ 650 students = 1.54 (above target)
        result = calculate_he_ratio_secondary(
            dhg_hours_total=Decimal("1000"), secondary_students=650
        )

        assert result.value > TARGET_HE_RATIO_SECONDARY
        assert result.variance_from_target > 0
        assert result.performance_status == "above_target"

    def test_calculate_he_ratio_secondary_below_target(self):
        """Test H/E ratio below target (worse - fewer hours per student)."""
        # 800 hours ÷ 650 students = 1.23 (below target)
        result = calculate_he_ratio_secondary(
            dhg_hours_total=Decimal("800"), secondary_students=650
        )

        assert result.value < TARGET_HE_RATIO_SECONDARY
        assert result.variance_from_target < 0
        assert result.performance_status == "below_target"

    def test_he_ratio_zero_students_error(self):
        """Test error when secondary students is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_he_ratio_secondary(dhg_hours_total=Decimal("877.5"), secondary_students=0)


class TestRevenuePerStudentCalculations:
    """Test revenue per student calculations."""

    def test_calculate_revenue_per_student_on_target(self):
        """Test revenue per student at target (~45,000 SAR)."""
        # Real EFIR data: 83,272,500 SAR ÷ 1850 students = 45,012 SAR
        result = calculate_revenue_per_student(
            total_revenue=Decimal("83272500"), total_students=1850
        )

        assert result.kpi_type == KPIType.REVENUE_PER_STUDENT
        assert Decimal("44500") <= result.value <= Decimal("45500")
        assert result.target_value == TARGET_REVENUE_PER_STUDENT
        assert result.unit == "SAR"
        assert result.performance_status == "on_target"

    def test_calculate_revenue_per_student_above_target(self):
        """Test revenue per student above target (better - higher revenue)."""
        # 90,000,000 SAR ÷ 1850 students = 48,649 SAR (above target)
        result = calculate_revenue_per_student(
            total_revenue=Decimal("90000000"), total_students=1850
        )

        assert result.value > TARGET_REVENUE_PER_STUDENT
        assert result.variance_from_target > 0
        assert result.performance_status == "above_target"

    def test_calculate_revenue_per_student_below_target(self):
        """Test revenue per student below target (worse - lower revenue)."""
        # 75,000,000 SAR ÷ 1850 students = 40,541 SAR (below target)
        result = calculate_revenue_per_student(
            total_revenue=Decimal("75000000"), total_students=1850
        )

        assert result.value < TARGET_REVENUE_PER_STUDENT
        assert result.variance_from_target < 0
        assert result.performance_status == "below_target"

    def test_revenue_per_student_zero_students_error(self):
        """Test error when total students is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_revenue_per_student(total_revenue=Decimal("83272500"), total_students=0)


class TestCostPerStudentCalculations:
    """Test cost per student calculations."""

    def test_calculate_cost_per_student(self):
        """Test cost per student calculation (no target)."""
        # Real EFIR data: 74,945,250 SAR ÷ 1850 students = 40,510.95 SAR
        result = calculate_cost_per_student(
            total_costs=Decimal("74945250"), total_students=1850
        )

        assert result.kpi_type == KPIType.COST_PER_STUDENT
        assert Decimal("40500") <= result.value <= Decimal("40520")
        assert result.target_value is None  # No target for this KPI
        assert result.unit == "SAR"
        assert result.variance_from_target is None
        assert result.performance_status is None

    def test_cost_per_student_different_scenarios(self):
        """Test cost per student with different cost levels."""
        # Low cost scenario
        result_low = calculate_cost_per_student(
            total_costs=Decimal("60000000"), total_students=1850
        )
        assert Decimal("32400") <= result_low.value <= Decimal("32500")

        # High cost scenario
        result_high = calculate_cost_per_student(
            total_costs=Decimal("90000000"), total_students=1850
        )
        assert Decimal("48640") <= result_high.value <= Decimal("48650")

    def test_cost_per_student_zero_students_error(self):
        """Test error when total students is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_cost_per_student(total_costs=Decimal("74945250"), total_students=0)


class TestMarginPercentageCalculations:
    """Test profit margin percentage calculations."""

    def test_calculate_margin_percentage_on_target(self):
        """Test margin percentage at target (10%)."""
        # Real EFIR data: (83,272,500 - 74,945,250) / 83,272,500 = 10%
        result = calculate_margin_percentage(
            total_revenue=Decimal("83272500"), total_costs=Decimal("74945250")
        )

        assert result.kpi_type == KPIType.MARGIN_PERCENTAGE
        assert Decimal("9.90") <= result.value <= Decimal("10.10")
        assert result.target_value == TARGET_MARGIN_PERCENTAGE
        assert result.unit == "%"
        assert result.performance_status == "on_target"

    def test_calculate_margin_percentage_above_target(self):
        """Test margin percentage above target (better - higher profit)."""
        # Revenue: 100,000,000, Costs: 80,000,000 → Margin: 20%
        result = calculate_margin_percentage(
            total_revenue=Decimal("100000000"), total_costs=Decimal("80000000")
        )

        assert result.value > TARGET_MARGIN_PERCENTAGE
        assert result.variance_from_target > 0
        assert result.performance_status == "above_target"

    def test_calculate_margin_percentage_below_target(self):
        """Test margin percentage below target (worse - lower profit)."""
        # Revenue: 100,000,000, Costs: 95,000,000 → Margin: 5%
        result = calculate_margin_percentage(
            total_revenue=Decimal("100000000"), total_costs=Decimal("95000000")
        )

        assert result.value < TARGET_MARGIN_PERCENTAGE
        assert result.variance_from_target < 0
        assert result.performance_status == "below_target"

    def test_calculate_margin_percentage_negative(self):
        """Test negative margin (loss scenario)."""
        # Revenue: 100,000,000, Costs: 110,000,000 → Margin: -10%
        result = calculate_margin_percentage(
            total_revenue=Decimal("100000000"), total_costs=Decimal("110000000")
        )

        assert result.value < 0
        assert result.performance_status == "below_target"

    def test_margin_percentage_zero_revenue_error(self):
        """Test error when revenue is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_margin_percentage(total_revenue=Decimal("0"), total_costs=Decimal("1000"))


class TestStaffCostRatioCalculations:
    """Test personnel cost ratio calculations."""

    def test_calculate_staff_cost_ratio_on_target(self):
        """Test staff cost ratio at target (70%)."""
        # Real EFIR data: 52,461,675 / 74,945,250 = 70%
        result = calculate_staff_cost_ratio(
            personnel_costs=Decimal("52461675"), total_costs=Decimal("74945250")
        )

        assert result.kpi_type == KPIType.STAFF_COST_RATIO
        assert Decimal("69.90") <= result.value <= Decimal("70.10")
        assert result.target_value == TARGET_STAFF_COST_RATIO
        assert result.unit == "%"
        assert result.performance_status == "on_target"

    def test_calculate_staff_cost_ratio_above_target(self):
        """Test staff cost ratio above target (may indicate inefficiency)."""
        # Personnel: 80,000,000, Total: 100,000,000 → Ratio: 80%
        result = calculate_staff_cost_ratio(
            personnel_costs=Decimal("80000000"), total_costs=Decimal("100000000")
        )

        assert result.value > TARGET_STAFF_COST_RATIO
        assert result.variance_from_target > 0
        assert result.performance_status == "above_target"

    def test_calculate_staff_cost_ratio_below_target(self):
        """Test staff cost ratio below target (may indicate understaffing)."""
        # Personnel: 60,000,000, Total: 100,000,000 → Ratio: 60%
        result = calculate_staff_cost_ratio(
            personnel_costs=Decimal("60000000"), total_costs=Decimal("100000000")
        )

        assert result.value < TARGET_STAFF_COST_RATIO
        assert result.variance_from_target < 0
        assert result.performance_status == "below_target"

    def test_staff_cost_ratio_zero_total_costs_error(self):
        """Test error when total costs is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_staff_cost_ratio(
                personnel_costs=Decimal("52461675"), total_costs=Decimal("0")
            )


class TestCapacityUtilizationCalculations:
    """Test capacity utilization calculations."""

    def test_calculate_capacity_utilization_on_target(self):
        """Test capacity utilization in target range (90-95%)."""
        # Real EFIR data: 1850 / 1875 = 98.67% (slightly above optimal)
        result = calculate_capacity_utilization(current_students=1850, max_capacity=1875)

        assert result.kpi_type == KPIType.CAPACITY_UTILIZATION
        assert Decimal("98.66") <= result.value <= Decimal("98.68")
        assert result.target_value == Decimal("92.5")  # Midpoint of 90-95%
        assert result.unit == "%"
        assert result.performance_status == "above_target"  # Slightly over optimal

    def test_calculate_capacity_utilization_optimal_range(self):
        """Test capacity utilization in optimal range (90-95%)."""
        # 1700 / 1875 = 90.67% (within optimal range)
        result = calculate_capacity_utilization(current_students=1700, max_capacity=1875)

        assert Decimal("90.0") <= result.value <= Decimal("95.0")
        assert result.performance_status == "on_target"

    def test_calculate_capacity_utilization_underutilized(self):
        """Test capacity utilization below target (underutilized)."""
        # 1200 / 1875 = 64% (underutilized)
        result = calculate_capacity_utilization(current_students=1200, max_capacity=1875)

        assert result.value < Decimal("90.0")
        assert result.performance_status == "below_target"

    def test_calculate_capacity_utilization_overcrowded(self):
        """Test capacity utilization above optimal (overcrowding risk)."""
        # 1900 / 1875 = 101.33% (overcrowded)
        result = calculate_capacity_utilization(current_students=1900, max_capacity=1875)

        assert result.value > Decimal("95.0")
        assert result.performance_status == "above_target"

    def test_capacity_utilization_zero_capacity_error(self):
        """Test error when max capacity is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_capacity_utilization(current_students=1850, max_capacity=0)


class TestCalculateAllKPIs:
    """Test comprehensive KPI calculation."""

    def test_calculate_all_kpis_complete_dataset(self):
        """Test calculating all KPIs from complete input dataset."""
        # Real EFIR data
        kpi_input = KPIInput(
            budget_id=uuid4(),
            total_students=1850,
            secondary_students=650,
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            dhg_hours_total=Decimal("877.5"),
            total_revenue=Decimal("83272500"),
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        result = calculate_all_kpis(kpi_input)

        # Verify all KPIs are calculated
        assert result.budget_id == kpi_input.budget_id
        assert result.calculation_date is not None

        # Educational KPIs
        assert result.student_teacher_ratio is not None
        assert result.student_teacher_ratio.value == Decimal("12.00")

        assert result.he_ratio_secondary is not None
        assert result.he_ratio_secondary.value == Decimal("1.35")

        assert result.capacity_utilization is not None
        assert Decimal("98.66") <= result.capacity_utilization.value <= Decimal("98.68")

        # Financial KPIs
        assert result.revenue_per_student is not None
        assert Decimal("44500") <= result.revenue_per_student.value <= Decimal("45500")

        assert result.cost_per_student is not None
        assert Decimal("40500") <= result.cost_per_student.value <= Decimal("40520")

        assert result.margin_percentage is not None
        assert Decimal("9.90") <= result.margin_percentage.value <= Decimal("10.10")

        assert result.staff_cost_ratio is not None
        assert Decimal("69.90") <= result.staff_cost_ratio.value <= Decimal("70.10")

    def test_calculate_all_kpis_without_dhg_hours(self):
        """Test calculating KPIs when DHG hours not provided."""
        kpi_input = KPIInput(
            total_students=1850,
            secondary_students=650,
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            dhg_hours_total=None,  # Not provided
            total_revenue=Decimal("83272500"),
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        result = calculate_all_kpis(kpi_input)

        # H/E ratio should not be calculated
        assert result.he_ratio_secondary is None

        # All other KPIs should be calculated
        assert result.student_teacher_ratio is not None
        assert result.capacity_utilization is not None
        assert result.revenue_per_student is not None
        assert result.cost_per_student is not None
        assert result.margin_percentage is not None
        assert result.staff_cost_ratio is not None


class TestKPIInputValidation:
    """Test KPI input data validation."""

    def test_validate_kpi_input_valid_data(self):
        """Test validation passes with valid data."""
        valid_input = KPIInput(
            total_students=1850,
            secondary_students=650,
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            total_revenue=Decimal("83272500"),
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        validate_kpi_input(valid_input)  # Should not raise

    def test_validate_kpi_input_zero_students_error(self):
        """Test validation fails with zero students."""
        invalid_input = KPIInput(
            total_students=0,  # Invalid
            secondary_students=0,
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            total_revenue=Decimal("83272500"),
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        with pytest.raises(InvalidKPIInputError, match="must be positive"):
            validate_kpi_input(invalid_input)

    def test_validate_kpi_input_secondary_exceeds_total(self):
        """Test validation fails when secondary students > total students."""
        # Pydantic validator catches this during model construction
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="cannot exceed total students"):
            KPIInput(
                total_students=1850,
                secondary_students=2000,  # More than total!
                max_capacity=1875,
                total_teacher_fte=Decimal("154.17"),
                total_revenue=Decimal("83272500"),
                total_costs=Decimal("74945250"),
                personnel_costs=Decimal("52461675"),
            )

    def test_validate_kpi_input_personnel_exceeds_total_costs(self):
        """Test validation fails when personnel costs > total costs."""
        # Pydantic validator catches this during model construction
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="cannot exceed total costs"):
            KPIInput(
                total_students=1850,
                secondary_students=650,
                max_capacity=1875,
                total_teacher_fte=Decimal("154.17"),
                total_revenue=Decimal("83272500"),
                total_costs=Decimal("74945250"),
                personnel_costs=Decimal("80000000"),  # More than total costs!
            )

    def test_validate_kpi_input_students_exceed_capacity(self):
        """Test validation fails when students significantly exceed capacity."""
        invalid_input = KPIInput(
            total_students=2500,  # Way over capacity (1875 × 1.05 = 1969)
            secondary_students=800,
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            total_revenue=Decimal("83272500"),
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        with pytest.raises(InvalidKPIInputError, match="exceeds.*max capacity"):
            validate_kpi_input(invalid_input)

    def test_validate_kpi_input_dhg_hours_without_students(self):
        """Test validation fails when DHG hours provided but no secondary students."""
        invalid_input = KPIInput(
            total_students=1850,
            secondary_students=0,  # No secondary students
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            dhg_hours_total=Decimal("877.5"),  # But DHG hours provided
            total_revenue=Decimal("83272500"),
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        with pytest.raises(InvalidKPIInputError, match="must be positive when DHG hours"):
            validate_kpi_input(invalid_input)

    def test_validate_kpi_input_zero_teacher_fte_error(self):
        """Test validation fails when teacher FTE is zero."""
        # Pydantic will catch this, so test at model level
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="greater than 0"):
            KPIInput(
                total_students=1850,
                secondary_students=650,
                max_capacity=1875,
                total_teacher_fte=Decimal("0.0"),  # Invalid - zero
                total_revenue=Decimal("83272500"),
                total_costs=Decimal("74945250"),
                personnel_costs=Decimal("52461675"),
            )

    def test_validate_kpi_input_zero_capacity_error(self):
        """Test validation fails when max capacity is zero."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            KPIInput(
                total_students=1850,
                secondary_students=650,
                max_capacity=0,  # Invalid - zero
                total_teacher_fte=Decimal("154.17"),
                total_revenue=Decimal("83272500"),
                total_costs=Decimal("74945250"),
                personnel_costs=Decimal("52461675"),
            )

    def test_validate_kpi_input_negative_revenue_error(self):
        """Test validation fails when revenue is negative."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            KPIInput(
                total_students=1850,
                secondary_students=650,
                max_capacity=1875,
                total_teacher_fte=Decimal("154.17"),
                total_revenue=Decimal("-1000"),  # Invalid - negative
                total_costs=Decimal("74945250"),
                personnel_costs=Decimal("52461675"),
            )

    def test_validate_kpi_input_negative_costs_error(self):
        """Test validation fails when total costs are negative."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            KPIInput(
                total_students=1850,
                secondary_students=650,
                max_capacity=1875,
                total_teacher_fte=Decimal("154.17"),
                total_revenue=Decimal("83272500"),
                total_costs=Decimal("-1000"),  # Invalid - negative
                personnel_costs=Decimal("52461675"),
            )

    def test_validate_kpi_input_negative_personnel_costs_error(self):
        """Test validation fails when personnel costs are negative."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            KPIInput(
                total_students=1850,
                secondary_students=650,
                max_capacity=1875,
                total_teacher_fte=Decimal("154.17"),
                total_revenue=Decimal("83272500"),
                total_costs=Decimal("74945250"),
                personnel_costs=Decimal("-1000"),  # Invalid - negative
            )

    def test_validate_kpi_input_negative_dhg_hours_error(self):
        """Test validation fails when DHG hours are negative."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            KPIInput(
                total_students=1850,
                secondary_students=650,
                max_capacity=1875,
                total_teacher_fte=Decimal("154.17"),
                dhg_hours_total=Decimal("-50"),  # Invalid - negative
                total_revenue=Decimal("83272500"),
                total_costs=Decimal("74945250"),
                personnel_costs=Decimal("52461675"),
            )


class TestRatioBoundsValidation:
    """Test ratio bounds validation."""

    def test_validate_ratio_bounds_within_range(self):
        """Test ratio bounds validation passes when within range."""
        ratio_result = KPIResult(
            kpi_type=KPIType.STUDENT_TEACHER_RATIO,
            value=Decimal("12.0"),
            target_value=Decimal("12.0"),
            unit="ratio",
            variance_from_target=Decimal("0.0"),
            performance_status="on_target",
        )

        validate_ratio_bounds(ratio_result, min_value=Decimal("5.0"), max_value=Decimal("25.0"))

    def test_validate_ratio_bounds_below_minimum(self):
        """Test ratio bounds validation fails when below minimum."""
        ratio_result = KPIResult(
            kpi_type=KPIType.STUDENT_TEACHER_RATIO,
            value=Decimal("3.0"),  # Below minimum
            target_value=Decimal("12.0"),
            unit="ratio",
            variance_from_target=Decimal("-9.0"),
            performance_status="below_target",
        )

        with pytest.raises(InvalidRatioBoundsError, match="below minimum"):
            validate_ratio_bounds(ratio_result, min_value=Decimal("5.0"))

    def test_validate_ratio_bounds_above_maximum(self):
        """Test ratio bounds validation fails when above maximum."""
        ratio_result = KPIResult(
            kpi_type=KPIType.STUDENT_TEACHER_RATIO,
            value=Decimal("30.0"),  # Above maximum
            target_value=Decimal("12.0"),
            unit="ratio",
            variance_from_target=Decimal("18.0"),
            performance_status="above_target",
        )

        with pytest.raises(InvalidRatioBoundsError, match="exceeds maximum"):
            validate_ratio_bounds(ratio_result, max_value=Decimal("25.0"))

    def test_validate_student_teacher_ratio_bounds(self):
        """Test student-teacher ratio specific bounds (5-25)."""
        # Valid ratio
        valid_ratio = KPIResult(
            kpi_type=KPIType.STUDENT_TEACHER_RATIO,
            value=Decimal("12.0"),
            target_value=Decimal("12.0"),
            unit="ratio",
            variance_from_target=Decimal("0.0"),
            performance_status="on_target",
        )
        validate_student_teacher_ratio(valid_ratio)

        # Invalid ratio (too high)
        invalid_ratio = KPIResult(
            kpi_type=KPIType.STUDENT_TEACHER_RATIO,
            value=Decimal("30.0"),
            target_value=Decimal("12.0"),
            unit="ratio",
            variance_from_target=Decimal("18.0"),
            performance_status="above_target",
        )
        with pytest.raises(InvalidRatioBoundsError):
            validate_student_teacher_ratio(invalid_ratio)

    def test_validate_he_ratio_secondary_bounds(self):
        """Test H/E ratio specific bounds (1.0-2.0)."""
        # Valid ratio
        valid_ratio = KPIResult(
            kpi_type=KPIType.HE_RATIO_SECONDARY,
            value=Decimal("1.35"),
            target_value=Decimal("1.35"),
            unit="ratio",
            variance_from_target=Decimal("0.0"),
            performance_status="on_target",
        )
        validate_he_ratio_secondary(valid_ratio)

        # Invalid ratio (too high)
        invalid_ratio = KPIResult(
            kpi_type=KPIType.HE_RATIO_SECONDARY,
            value=Decimal("2.5"),
            target_value=Decimal("1.35"),
            unit="ratio",
            variance_from_target=Decimal("1.15"),
            performance_status="above_target",
        )
        with pytest.raises(InvalidRatioBoundsError):
            validate_he_ratio_secondary(invalid_ratio)

    def test_validate_margin_percentage_bounds(self):
        """Test margin percentage specific bounds (-20% to 30%)."""
        # Valid margin
        valid_margin = KPIResult(
            kpi_type=KPIType.MARGIN_PERCENTAGE,
            value=Decimal("10.0"),
            target_value=Decimal("10.0"),
            unit="%",
            variance_from_target=Decimal("0.0"),
            performance_status="on_target",
        )
        validate_margin_percentage(valid_margin)

        # Invalid margin (too low)
        invalid_margin = KPIResult(
            kpi_type=KPIType.MARGIN_PERCENTAGE,
            value=Decimal("-25.0"),
            target_value=Decimal("10.0"),
            unit="%",
            variance_from_target=Decimal("-35.0"),
            performance_status="below_target",
        )
        with pytest.raises(InvalidRatioBoundsError):
            validate_margin_percentage(invalid_margin)

    def test_validate_staff_cost_ratio_bounds(self):
        """Test staff cost ratio specific bounds (50%-90%)."""
        # Valid ratio
        valid_ratio = KPIResult(
            kpi_type=KPIType.STAFF_COST_RATIO,
            value=Decimal("70.0"),
            target_value=Decimal("70.0"),
            unit="%",
            variance_from_target=Decimal("0.0"),
            performance_status="on_target",
        )
        validate_staff_cost_ratio(valid_ratio)

        # Invalid ratio (too high)
        invalid_ratio = KPIResult(
            kpi_type=KPIType.STAFF_COST_RATIO,
            value=Decimal("95.0"),
            target_value=Decimal("70.0"),
            unit="%",
            variance_from_target=Decimal("25.0"),
            performance_status="above_target",
        )
        with pytest.raises(InvalidRatioBoundsError):
            validate_staff_cost_ratio(invalid_ratio)

    def test_validate_capacity_utilization_bounds(self):
        """Test capacity utilization specific bounds (60%-105%)."""
        # Valid utilization
        valid_util = KPIResult(
            kpi_type=KPIType.CAPACITY_UTILIZATION,
            value=Decimal("92.5"),
            target_value=Decimal("92.5"),
            unit="%",
            variance_from_target=Decimal("0.0"),
            performance_status="on_target",
        )
        validate_capacity_utilization(valid_util)

        # Invalid utilization (too high - severe overcrowding)
        invalid_util = KPIResult(
            kpi_type=KPIType.CAPACITY_UTILIZATION,
            value=Decimal("110.0"),
            target_value=Decimal("92.5"),
            unit="%",
            variance_from_target=Decimal("17.5"),
            performance_status="above_target",
        )
        with pytest.raises(InvalidRatioBoundsError):
            validate_capacity_utilization(invalid_util)


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""

    def test_kpi_calculations_with_minimal_values(self):
        """Test KPI calculations with minimal valid values."""
        kpi_input = KPIInput(
            total_students=1,
            secondary_students=0,
            max_capacity=10,
            total_teacher_fte=Decimal("0.1"),
            total_revenue=Decimal("1000"),
            total_costs=Decimal("900"),
            personnel_costs=Decimal("500"),
        )

        result = calculate_all_kpis(kpi_input)

        # All KPIs should calculate (except H/E ratio without secondary students)
        assert result.student_teacher_ratio is not None
        assert result.he_ratio_secondary is None  # No secondary students
        assert result.capacity_utilization is not None
        assert result.revenue_per_student is not None
        assert result.cost_per_student is not None
        assert result.margin_percentage is not None
        assert result.staff_cost_ratio is not None

    def test_kpi_calculations_with_large_values(self):
        """Test KPI calculations with very large values."""
        kpi_input = KPIInput(
            total_students=10000,
            secondary_students=4000,
            max_capacity=12000,
            total_teacher_fte=Decimal("800.0"),
            dhg_hours_total=Decimal("5400.0"),
            total_revenue=Decimal("500000000"),
            total_costs=Decimal("450000000"),
            personnel_costs=Decimal("315000000"),
        )

        result = calculate_all_kpis(kpi_input)

        # All KPIs should calculate successfully
        assert result.student_teacher_ratio is not None
        assert result.he_ratio_secondary is not None
        assert result.capacity_utilization is not None
        assert result.revenue_per_student is not None
        assert result.cost_per_student is not None
        assert result.margin_percentage is not None
        assert result.staff_cost_ratio is not None


class TestKPIEdgeCases100PercentCoverage:
    """Additional edge cases for 100% KPI calculator coverage."""

    def test_kpi_calculation_with_zero_revenue_all_kpis(self):
        """Test all KPI calculations when revenue is exactly zero."""
        kpi_input = KPIInput(
            total_students=1850,
            secondary_students=650,
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            total_revenue=Decimal("0.00"),  # Zero revenue!
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        result = calculate_all_kpis(kpi_input)

        # Revenue per student should be 0
        assert result.revenue_per_student.value == Decimal("0.00")

        # Margin percentage calculation requires positive revenue
        # Should handle gracefully
        assert result.margin_percentage is not None

    def test_kpi_precision_very_large_numbers_billions(self):
        """Test KPI calculations with billions in revenue."""
        kpi_input = KPIInput(
            total_students=10000,
            secondary_students=4000,
            max_capacity=12000,
            total_teacher_fte=Decimal("800.0"),
            dhg_hours_total=Decimal("5400.0"),
            total_revenue=Decimal("5000000000"),  # 5 billion SAR
            total_costs=Decimal("4500000000"),    # 4.5 billion SAR
            personnel_costs=Decimal("3150000000"), # 3.15 billion SAR
        )

        result = calculate_all_kpis(kpi_input)

        # Revenue per student: 5B ÷ 10,000 = 500,000 SAR
        assert result.revenue_per_student.value == Decimal("500000.00")

        # Cost per student: 4.5B ÷ 10,000 = 450,000 SAR
        assert result.cost_per_student.value == Decimal("450000.00")

    def test_kpi_performance_status_exact_boundaries(self):
        """Test performance status at exact target boundaries."""
        # Exactly on target for student-teacher ratio
        result = calculate_student_teacher_ratio(
            total_students=1850,
            total_teacher_fte=Decimal("154.166667")  # Exactly 12.00 ratio
        )

        assert result.value == Decimal("12.00")
        assert result.performance_status == "on_target"

    def test_calculate_all_kpis_partial_data_minimal_fields(self):
        """Test calculating KPIs with only minimal required fields."""
        kpi_input = KPIInput(
            total_students=100,
            secondary_students=0,  # No secondary students
            max_capacity=150,
            total_teacher_fte=Decimal("10.0"),
            dhg_hours_total=None,  # Not provided
            total_revenue=Decimal("1000000"),
            total_costs=Decimal("900000"),
            personnel_costs=Decimal("600000"),
        )

        result = calculate_all_kpis(kpi_input)

        # H/E ratio should be None (no DHG hours)
        assert result.he_ratio_secondary is None

        # All other KPIs should be calculated
        assert result.student_teacher_ratio is not None
        assert result.capacity_utilization is not None
        assert result.revenue_per_student is not None

    def test_kpi_variance_sign_consistency_all_directions(self):
        """Test variance signs are consistent across all KPIs."""
        # Above target
        above = calculate_student_teacher_ratio(
            total_students=1850,
            total_teacher_fte=Decimal("120.0")  # 15.42 ratio > 12.00 target
        )
        assert above.variance_from_target > 0
        assert above.performance_status == "above_target"

        # Below target
        below = calculate_student_teacher_ratio(
            total_students=1850,
            total_teacher_fte=Decimal("200.0")  # 9.25 ratio < 12.00 target
        )
        assert below.variance_from_target < 0
        assert below.performance_status == "below_target"

        # On target (within tolerance)
        on_target = calculate_student_teacher_ratio(
            total_students=1850,
            total_teacher_fte=Decimal("154.17")  # ~12.00 ratio
        )
        assert abs(on_target.variance_from_target) <= Decimal("0.01")

    def test_margin_percentage_extreme_loss_10x_costs(self):
        """Test margin percentage with costs 10x higher than revenue."""
        result = calculate_margin_percentage(
            total_revenue=Decimal("10000000"),
            total_costs=Decimal("100000000"),  # 10x higher!
        )

        # Margin: (10M - 100M) / 10M = -9.00 = -900%
        assert result.value == Decimal("-900.00")
        assert result.value < 0  # Loss
        assert result.performance_status == "below_target"

    def test_staff_cost_ratio_zero_personnel_costs(self):
        """Test staff cost ratio when personnel costs are zero."""
        result = calculate_staff_cost_ratio(
            personnel_costs=Decimal("0.00"),  # Zero personnel costs
            total_costs=Decimal("100000"),
        )

        # Ratio: 0 / 100,000 = 0%
        assert result.value == Decimal("0.00")
        assert result.performance_status == "below_target"  # Far below 70%

    def test_capacity_utilization_over_200_percent_severe_overcrowding(self):
        """Test capacity utilization in severe overcrowding (>200%)."""
        result = calculate_capacity_utilization(
            current_students=4000,  # More than 2x capacity
            max_capacity=1875,
        )

        # Utilization: 4000 / 1875 = 213.33%
        assert result.value > Decimal("200.00")
        assert result.performance_status == "above_target"

    def test_kpi_calculation_date_timezone_utc(self):
        """Test that calculation_date is set correctly."""
        kpi_input = KPIInput(
            total_students=1850,
            secondary_students=650,
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            total_revenue=Decimal("83272500"),
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        result = calculate_all_kpis(kpi_input)

        # Should have a calculation date
        assert result.calculation_date is not None
        # Should be recent (within last minute)
        from datetime import datetime
        now = datetime.now(UTC)
        assert (now - result.calculation_date).total_seconds() < 60

    def test_kpi_result_immutability_frozen_models(self):
        """Test that KPI results cannot be modified after creation."""
        result = KPIResult(
            kpi_type=KPIType.STUDENT_TEACHER_RATIO,
            value=Decimal("12.0"),
            target_value=Decimal("12.0"),
            unit="ratio",
            variance_from_target=Decimal("0.0"),
            performance_status="on_target",
        )

        # Pydantic frozen models should prevent modification
        with pytest.raises(ValidationError):
            result.value = Decimal("15.0")

    def test_he_ratio_secondary_with_zero_hours(self):
        """Test H/E ratio calculation when DHG hours is zero."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_he_ratio_secondary(
                dhg_hours_total=Decimal("0.00"),  # Zero hours
                secondary_students=650,
            )

    def test_all_kpis_serialization_to_dict(self):
        """Test that all KPI results can be serialized to dict."""
        kpi_input = KPIInput(
            total_students=1850,
            secondary_students=650,
            max_capacity=1875,
            total_teacher_fte=Decimal("154.17"),
            total_revenue=Decimal("83272500"),
            total_costs=Decimal("74945250"),
            personnel_costs=Decimal("52461675"),
        )

        result = calculate_all_kpis(kpi_input)

        # Should be able to convert to dict
        data_dict = result.model_dump()

        assert "student_teacher_ratio" in data_dict
        assert "capacity_utilization" in data_dict
        assert "margin_percentage" in data_dict
