"""
Unit Tests for DHG Engine

Tests for DHG (Dotation Horaire Globale) teacher workforce planning calculations.
Target Coverage: 95%+

Test Categories:
1. DHG hours calculations (subject hours × classes)
2. FTE calculations from DHG hours
3. Teacher requirement calculations across levels
4. HSA (overtime) allocation calculations
5. Aggregated DHG hours calculations
6. DHG input validation
7. Subject hours validation
8. HSA limits validation
9. Edge cases and error handling
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.engine.dhg import (
    EducationLevel,
    DHGInput,
    SubjectHours,
    DHGHoursResult,
    FTECalculationResult,
    TeacherRequirement,
    HSAAllocation,
    calculate_dhg_hours,
    calculate_fte_from_hours,
    calculate_teacher_requirement,
    calculate_hsa_allocation,
    validate_dhg_input,
    validate_subject_hours,
    validate_hsa_limits,
)
from app.engine.dhg.calculator import (
    STANDARD_HOURS,
    DEFAULT_MAX_HSA_PER_TEACHER,
    calculate_aggregated_dhg_hours,
)
from app.engine.dhg.validators import (
    InvalidDHGInputError,
    InvalidSubjectHoursError,
    InvalidHSAAllocationError,
    validate_max_hsa_per_teacher,
    validate_education_level_standard_hours,
    validate_fte_non_negative,
    validate_dhg_hours_non_negative,
    validate_subject_hours_list_consistency,
)


class TestDHGHoursCalculations:
    """Test DHG hours calculations for different levels and subjects."""

    def test_calculate_dhg_hours_single_subject(self):
        """Test DHG hours calculation for a single subject."""
        # Real EFIR data: 6ème Mathématiques
        # 6 classes × 4.5h/week = 27 hours
        math_hours = SubjectHours(
            subject_id=uuid4(),
            subject_code="MATH",
            subject_name="Mathématiques",
            level_id=uuid4(),
            level_code="6EME",
            hours_per_week=Decimal("4.5"),
        )

        dhg_input = DHGInput(
            level_id=math_hours.level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            subject_hours_list=[math_hours],
        )

        result = calculate_dhg_hours(dhg_input)

        assert result.level_code == "6EME"
        assert result.education_level == EducationLevel.SECONDARY
        assert result.number_of_classes == 6
        assert result.total_hours == Decimal("27.0")  # 6 × 4.5
        assert result.subject_breakdown["MATH"] == Decimal("27.0")

    def test_calculate_dhg_hours_multiple_subjects(self):
        """Test DHG hours calculation with multiple subjects."""
        # Real EFIR data: 6ème with Mathématiques and Français
        level_id = uuid4()

        math_hours = SubjectHours(
            subject_id=uuid4(),
            subject_code="MATH",
            subject_name="Mathématiques",
            level_id=level_id,
            level_code="6EME",
            hours_per_week=Decimal("4.5"),
        )

        fran_hours = SubjectHours(
            subject_id=uuid4(),
            subject_code="FRAN",
            subject_name="Français",
            level_id=level_id,
            level_code="6EME",
            hours_per_week=Decimal("5.0"),
        )

        dhg_input = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            subject_hours_list=[math_hours, fran_hours],
        )

        result = calculate_dhg_hours(dhg_input)

        # Total: (6 × 4.5) + (6 × 5.0) = 27 + 30 = 57
        assert result.total_hours == Decimal("57.0")
        assert result.subject_breakdown["MATH"] == Decimal("27.0")
        assert result.subject_breakdown["FRAN"] == Decimal("30.0")

    def test_calculate_dhg_hours_collège_complete(self):
        """Test complete Collège DHG calculation (all 4 levels)."""
        # Simulate Mathématiques across all Collège levels
        # 6ème: 6 classes × 4.5h = 27h
        # 5ème: 6 classes × 3.5h = 21h
        # 4ème: 5 classes × 3.5h = 17.5h
        # 3ème: 4 classes × 3.5h = 14h
        # Total: 79.5h

        math_6eme = DHGInput(
            level_id=uuid4(),
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            subject_hours_list=[
                SubjectHours(
                    subject_id=uuid4(),
                    subject_code="MATH",
                    subject_name="Mathématiques",
                    level_id=uuid4(),
                    level_code="6EME",
                    hours_per_week=Decimal("4.5"),
                )
            ],
        )

        result_6eme = calculate_dhg_hours(math_6eme)
        assert result_6eme.total_hours == Decimal("27.0")

    def test_calculate_dhg_hours_zero_classes(self):
        """Test DHG hours calculation with zero classes."""
        level_id = uuid4()

        math_hours = SubjectHours(
            subject_id=uuid4(),
            subject_code="MATH",
            subject_name="Mathématiques",
            level_id=level_id,
            level_code="TERMINALE",
            hours_per_week=Decimal("4.0"),
        )

        dhg_input = DHGInput(
            level_id=level_id,
            level_code="TERMINALE",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=0,  # No classes
            subject_hours_list=[math_hours],
        )

        result = calculate_dhg_hours(dhg_input)

        # 0 classes × 4.0h = 0 hours
        assert result.total_hours == Decimal("0")
        assert result.subject_breakdown["MATH"] == Decimal("0")


class TestFTECalculations:
    """Test FTE calculations from DHG hours."""

    def test_calculate_fte_secondary_exact_division(self):
        """Test FTE calculation with exact division (no remainder)."""
        # 90 hours ÷ 18 standard hours = 5.0 FTE (exact)
        dhg_result = DHGHoursResult(
            level_id=uuid4(),
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            total_hours=Decimal("90.0"),
            subject_breakdown={"MATH": Decimal("90.0")},
        )

        fte_result = calculate_fte_from_hours(dhg_result)

        assert fte_result.education_level == EducationLevel.SECONDARY
        assert fte_result.standard_hours == Decimal("18.0")
        assert fte_result.simple_fte == Decimal("5.00")
        assert fte_result.rounded_fte == 5
        assert fte_result.fte_utilization == Decimal("100.00")  # Perfect utilization

    def test_calculate_fte_secondary_fractional(self):
        """Test FTE calculation with fractional result."""
        # Real EFIR example: 96 hours ÷ 18 = 5.33 FTE → 6 teachers needed
        dhg_result = DHGHoursResult(
            level_id=uuid4(),
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            total_hours=Decimal("96.0"),
            subject_breakdown={"MATH": Decimal("96.0")},
        )

        fte_result = calculate_fte_from_hours(dhg_result)

        assert fte_result.simple_fte == Decimal("5.33")
        assert fte_result.rounded_fte == 6  # Rounded up
        assert Decimal("88.0") <= fte_result.fte_utilization <= Decimal("89.0")

    def test_calculate_fte_primary(self):
        """Test FTE calculation for primary level (24h standard)."""
        # Primary: 72 hours ÷ 24 standard hours = 3.0 FTE
        dhg_result = DHGHoursResult(
            level_id=uuid4(),
            level_code="CP",
            education_level=EducationLevel.PRIMARY,
            number_of_classes=3,
            total_hours=Decimal("72.0"),
            subject_breakdown={},
        )

        fte_result = calculate_fte_from_hours(dhg_result)

        assert fte_result.education_level == EducationLevel.PRIMARY
        assert fte_result.standard_hours == Decimal("24.0")
        assert fte_result.simple_fte == Decimal("3.00")
        assert fte_result.rounded_fte == 3
        assert fte_result.fte_utilization == Decimal("100.00")

    def test_calculate_fte_zero_hours(self):
        """Test FTE calculation with zero DHG hours."""
        dhg_result = DHGHoursResult(
            level_id=uuid4(),
            level_code="TERMINALE",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=0,
            total_hours=Decimal("0"),
            subject_breakdown={},
        )

        fte_result = calculate_fte_from_hours(dhg_result)

        assert fte_result.simple_fte == Decimal("0.00")
        assert fte_result.rounded_fte == 0
        assert fte_result.fte_utilization == Decimal("0.00")


class TestTeacherRequirementCalculations:
    """Test teacher requirement calculations across levels."""

    def test_calculate_teacher_requirement_single_level(self):
        """Test teacher requirement for a subject at one level."""
        dhg_6eme = DHGHoursResult(
            level_id=uuid4(),
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            total_hours=Decimal("27.0"),
            subject_breakdown={"MATH": Decimal("27.0")},
        )

        requirement = calculate_teacher_requirement(
            "MATH",
            "Mathématiques",
            [dhg_6eme],
            EducationLevel.SECONDARY,
        )

        assert requirement.subject_code == "MATH"
        assert requirement.total_dhg_hours == Decimal("27.0")
        assert requirement.standard_hours == Decimal("18.0")
        assert requirement.simple_fte == Decimal("1.50")
        assert requirement.rounded_fte == 2

    def test_calculate_teacher_requirement_multiple_levels(self):
        """Test teacher requirement across multiple Collège levels."""
        # Mathématiques across Collège (6ème to 3ème)
        dhg_6eme = DHGHoursResult(
            level_id=uuid4(),
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            total_hours=Decimal("27.0"),
            subject_breakdown={"MATH": Decimal("27.0")},
        )

        dhg_5eme = DHGHoursResult(
            level_id=uuid4(),
            level_code="5EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            total_hours=Decimal("21.0"),
            subject_breakdown={"MATH": Decimal("21.0")},
        )

        dhg_4eme = DHGHoursResult(
            level_id=uuid4(),
            level_code="4EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=5,
            total_hours=Decimal("17.5"),
            subject_breakdown={"MATH": Decimal("17.5")},
        )

        dhg_3eme = DHGHoursResult(
            level_id=uuid4(),
            level_code="3EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=4,
            total_hours=Decimal("14.0"),
            subject_breakdown={"MATH": Decimal("14.0")},
        )

        requirement = calculate_teacher_requirement(
            "MATH",
            "Mathématiques",
            [dhg_6eme, dhg_5eme, dhg_4eme, dhg_3eme],
            EducationLevel.SECONDARY,
        )

        # Total: 27 + 21 + 17.5 + 14 = 79.5 hours
        assert requirement.total_dhg_hours == Decimal("79.5")
        # 79.5 ÷ 18 = 4.42 FTE → 5 teachers
        assert Decimal("4.41") <= requirement.simple_fte <= Decimal("4.43")
        assert requirement.rounded_fte == 5

    def test_calculate_teacher_requirement_hsa_calculation(self):
        """Test that HSA hours are calculated when FTE is fractional."""
        dhg_result = DHGHoursResult(
            level_id=uuid4(),
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            total_hours=Decimal("96.0"),
            subject_breakdown={"MATH": Decimal("96.0")},
        )

        requirement = calculate_teacher_requirement(
            "MATH",
            "Mathématiques",
            [dhg_result],
            EducationLevel.SECONDARY,
        )

        # 96 ÷ 18 = 5.33 → 6 teachers
        # Hours covered by 5 full-time: 5 × 18 = 90
        # HSA needed: 96 - 90 = 6 hours
        assert requirement.rounded_fte == 6
        assert requirement.hsa_hours == Decimal("6.00")


class TestHSAAllocationCalculations:
    """Test HSA (overtime) allocation calculations."""

    def test_calculate_hsa_allocation_within_limit(self):
        """Test HSA allocation within 4h per teacher limit."""
        # 96 hours needed, 5 teachers available
        # 5 × 18 = 90 hours covered
        # 96 - 90 = 6 hours HSA needed
        # 6h ÷ 5 teachers = 1.2h per teacher (within 4h limit)
        hsa = calculate_hsa_allocation(
            "MATH",
            "Mathématiques",
            Decimal("96.0"),
            5,
            EducationLevel.SECONDARY,
            Decimal("4.0"),
        )

        assert hsa.subject_code == "MATH"
        assert hsa.dhg_hours_needed == Decimal("96.0")
        assert hsa.available_fte == 5
        assert hsa.available_hours == Decimal("90.0")  # 5 × 18
        assert hsa.hsa_hours_needed == Decimal("6.00")
        assert hsa.hsa_within_limit is True

    def test_calculate_hsa_allocation_exceeds_limit(self):
        """Test HSA allocation exceeding 4h per teacher limit."""
        # 115 hours needed, 5 teachers available
        # 5 × 18 = 90 hours covered
        # 115 - 90 = 25 hours HSA needed
        # 25h ÷ 5 teachers = 5h per teacher (exceeds 4h limit)
        hsa = calculate_hsa_allocation(
            "MATH",
            "Mathématiques",
            Decimal("115.0"),
            5,
            EducationLevel.SECONDARY,
            Decimal("4.0"),
        )

        assert hsa.hsa_hours_needed == Decimal("25.00")
        assert hsa.hsa_within_limit is False  # Exceeds limit

    def test_calculate_hsa_allocation_no_hsa_needed(self):
        """Test HSA allocation when hours perfectly match."""
        # 90 hours needed, 5 teachers available
        # 5 × 18 = 90 hours (perfect match, no HSA needed)
        hsa = calculate_hsa_allocation(
            "MATH",
            "Mathématiques",
            Decimal("90.0"),
            5,
            EducationLevel.SECONDARY,
            Decimal("4.0"),
        )

        assert hsa.hsa_hours_needed == Decimal("0.00")
        assert hsa.hsa_within_limit is True

    def test_calculate_hsa_allocation_primary_level(self):
        """Test HSA allocation for primary level (24h standard)."""
        # Primary: 80 hours needed, 3 teachers available
        # 3 × 24 = 72 hours covered
        # 80 - 72 = 8 hours HSA needed
        # 8h ÷ 3 teachers = 2.67h per teacher (within 4h limit)
        hsa = calculate_hsa_allocation(
            "POLY",
            "Enseignant Polyvalent",
            Decimal("80.0"),
            3,
            EducationLevel.PRIMARY,
            Decimal("4.0"),
        )

        assert hsa.available_hours == Decimal("72.0")  # 3 × 24
        assert hsa.hsa_hours_needed == Decimal("8.00")
        assert hsa.hsa_within_limit is True

    def test_calculate_hsa_allocation_zero_available_fte(self):
        """Test HSA allocation with no available positions."""
        hsa = calculate_hsa_allocation(
            "MATH",
            "Mathématiques",
            Decimal("96.0"),
            0,  # No available FTE
            EducationLevel.SECONDARY,
            Decimal("4.0"),
        )

        assert hsa.available_hours == Decimal("0")
        assert hsa.hsa_hours_needed == Decimal("96.00")
        assert hsa.hsa_within_limit is False


class TestAggregatedDHGHours:
    """Test aggregated DHG hours calculations."""

    def test_calculate_aggregated_dhg_hours_multiple_levels(self):
        """Test aggregating DHG hours across multiple levels."""
        dhg_6eme = DHGHoursResult(
            level_id=uuid4(),
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            total_hours=Decimal("96.0"),
            subject_breakdown={},
        )

        dhg_5eme = DHGHoursResult(
            level_id=uuid4(),
            level_code="5EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            total_hours=Decimal("84.0"),
            subject_breakdown={},
        )

        total = calculate_aggregated_dhg_hours([dhg_6eme, dhg_5eme])

        assert total == Decimal("180.0")  # 96 + 84

    def test_calculate_aggregated_dhg_hours_empty_list(self):
        """Test aggregating with empty list."""
        total = calculate_aggregated_dhg_hours([])
        assert total == Decimal("0")


class TestDHGInputValidation:
    """Test DHG input validation."""

    def test_validate_dhg_input_valid(self):
        """Test validation passes with valid input."""
        level_id = uuid4()

        valid_input = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            subject_hours_list=[
                SubjectHours(
                    subject_id=uuid4(),
                    subject_code="MATH",
                    subject_name="Mathématiques",
                    level_id=level_id,
                    level_code="6EME",
                    hours_per_week=Decimal("4.5"),
                )
            ],
        )

        validate_dhg_input(valid_input)  # Should not raise

    def test_validate_dhg_input_too_many_classes(self):
        """Test validation fails with too many classes."""
        level_id = uuid4()

        invalid_input = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=100,  # Too many!
            subject_hours_list=[
                SubjectHours(
                    subject_id=uuid4(),
                    subject_code="MATH",
                    subject_name="Mathématiques",
                    level_id=level_id,
                    level_code="6EME",
                    hours_per_week=Decimal("4.5"),
                )
            ],
        )

        with pytest.raises(InvalidDHGInputError, match="between 0 and 50"):
            validate_dhg_input(invalid_input)

    def test_validate_dhg_input_empty_subject_list(self):
        """Test validation fails with empty subject hours list."""
        invalid_input = DHGInput(
            level_id=uuid4(),
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            subject_hours_list=[],  # Empty!
        )

        with pytest.raises(InvalidDHGInputError, match="cannot be empty"):
            validate_dhg_input(invalid_input)

    def test_validate_dhg_input_mismatched_level_id(self):
        """Test validation fails with mismatched level IDs."""
        level_id_1 = uuid4()
        level_id_2 = uuid4()

        invalid_input = DHGInput(
            level_id=level_id_1,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=6,
            subject_hours_list=[
                SubjectHours(
                    subject_id=uuid4(),
                    subject_code="MATH",
                    subject_name="Mathématiques",
                    level_id=level_id_2,  # Different level!
                    level_code="6EME",
                    hours_per_week=Decimal("4.5"),
                )
            ],
        )

        with pytest.raises(InvalidDHGInputError, match="mismatched level_id"):
            validate_dhg_input(invalid_input)


class TestSubjectHoursValidation:
    """Test subject hours validation."""

    def test_validate_subject_hours_valid(self):
        """Test validation passes with valid hours."""
        valid_hours = SubjectHours(
            subject_id=uuid4(),
            subject_code="MATH",
            subject_name="Mathématiques",
            level_id=uuid4(),
            level_code="6EME",
            hours_per_week=Decimal("4.5"),
        )

        validate_subject_hours(valid_hours)  # Should not raise

    def test_validate_subject_hours_too_high(self):
        """Test validation fails with hours > 10."""
        invalid_hours = SubjectHours(
            subject_id=uuid4(),
            subject_code="MATH",
            subject_name="Mathématiques",
            level_id=uuid4(),
            level_code="6EME",
            hours_per_week=Decimal("15.0"),  # Too many!
        )

        with pytest.raises(InvalidSubjectHoursError, match="between 0 and 10"):
            validate_subject_hours(invalid_hours)

    def test_validate_subject_hours_negative(self):
        """Test validation fails with negative hours."""
        with pytest.raises(ValueError):
            SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",
                subject_name="Mathématiques",
                level_id=uuid4(),
                level_code="6EME",
                hours_per_week=Decimal("-2.0"),  # Negative!
            )


class TestHSALimitsValidation:
    """Test HSA limits validation."""

    def test_validate_hsa_limits_within_limit(self):
        """Test validation passes when HSA is within limit."""
        valid_hsa = HSAAllocation(
            subject_code="MATH",
            subject_name="Mathématiques",
            dhg_hours_needed=Decimal("96.0"),
            available_fte=5,
            available_hours=Decimal("90.0"),
            hsa_hours_needed=Decimal("6.0"),
            hsa_within_limit=True,
            max_hsa_per_teacher=Decimal("4.0"),
        )

        validate_hsa_limits(valid_hsa)  # Should not raise

    def test_validate_hsa_limits_exceeds_limit(self):
        """Test validation fails when HSA exceeds limit."""
        invalid_hsa = HSAAllocation(
            subject_code="MATH",
            subject_name="Mathématiques",
            dhg_hours_needed=Decimal("115.0"),
            available_fte=5,
            available_hours=Decimal("90.0"),
            hsa_hours_needed=Decimal("25.0"),
            hsa_within_limit=False,
            max_hsa_per_teacher=Decimal("4.0"),
        )

        with pytest.raises(InvalidHSAAllocationError, match="exceeds limit"):
            validate_hsa_limits(invalid_hsa)

    def test_validate_max_hsa_per_teacher_valid(self):
        """Test max HSA validation with valid values."""
        validate_max_hsa_per_teacher(Decimal("2.0"))  # Minimum
        validate_max_hsa_per_teacher(Decimal("4.0"))  # Maximum
        validate_max_hsa_per_teacher(Decimal("3.0"))  # Middle

    def test_validate_max_hsa_per_teacher_invalid(self):
        """Test max HSA validation with invalid values."""
        with pytest.raises(ValueError, match="between 2 and 4"):
            validate_max_hsa_per_teacher(Decimal("5.0"))

        with pytest.raises(ValueError, match="between 2 and 4"):
            validate_max_hsa_per_teacher(Decimal("1.0"))


class TestEducationLevelValidation:
    """Test education level and standard hours validation."""

    def test_validate_education_level_standard_hours_secondary(self):
        """Test secondary level has 18h standard."""
        validate_education_level_standard_hours(
            EducationLevel.SECONDARY, Decimal("18.0")
        )

    def test_validate_education_level_standard_hours_primary(self):
        """Test primary level has 24h standard."""
        validate_education_level_standard_hours(
            EducationLevel.PRIMARY, Decimal("24.0")
        )

    def test_validate_education_level_standard_hours_mismatch(self):
        """Test validation fails with mismatched hours."""
        with pytest.raises(ValueError, match="should have 18 hours"):
            validate_education_level_standard_hours(
                EducationLevel.SECONDARY, Decimal("24.0")
            )


class TestFTEAndHoursValidation:
    """Test FTE and hours validation."""

    def test_validate_fte_non_negative_valid(self):
        """Test FTE validation with non-negative values."""
        validate_fte_non_negative(Decimal("0"))
        validate_fte_non_negative(Decimal("5.33"))
        validate_fte_non_negative(Decimal("100.0"))

    def test_validate_fte_non_negative_invalid(self):
        """Test FTE validation fails with negative values."""
        with pytest.raises(ValueError, match="cannot be negative"):
            validate_fte_non_negative(Decimal("-1.0"))

    def test_validate_dhg_hours_non_negative_valid(self):
        """Test DHG hours validation with non-negative values."""
        validate_dhg_hours_non_negative(Decimal("0"))
        validate_dhg_hours_non_negative(Decimal("96.0"))

    def test_validate_dhg_hours_non_negative_invalid(self):
        """Test DHG hours validation fails with negative values."""
        with pytest.raises(ValueError, match="cannot be negative"):
            validate_dhg_hours_non_negative(Decimal("-10.0"))


class TestSubjectHoursListConsistency:
    """Test subject hours list consistency validation."""

    def test_validate_subject_hours_list_consistency_valid(self):
        """Test validation passes with consistent list."""
        level_id = uuid4()

        subject_list = [
            SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",
                subject_name="Mathématiques",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("4.5"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="FRAN",
                subject_name="Français",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("5.0"),
            ),
        ]

        validate_subject_hours_list_consistency(subject_list)

    def test_validate_subject_hours_list_consistency_empty(self):
        """Test validation fails with empty list."""
        with pytest.raises(InvalidSubjectHoursError, match="cannot be empty"):
            validate_subject_hours_list_consistency([])

    def test_validate_subject_hours_list_consistency_mismatched_levels(self):
        """Test validation fails with mismatched level IDs."""
        subject_list = [
            SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",
                subject_name="Mathématiques",
                level_id=uuid4(),  # Different level
                level_code="6EME",
                hours_per_week=Decimal("4.5"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="FRAN",
                subject_name="Français",
                level_id=uuid4(),  # Different level
                level_code="6EME",
                hours_per_week=Decimal("5.0"),
            ),
        ]

        with pytest.raises(InvalidSubjectHoursError, match="same level_id"):
            validate_subject_hours_list_consistency(subject_list)

    def test_validate_subject_hours_list_consistency_duplicates(self):
        """Test validation fails with duplicate subjects."""
        level_id = uuid4()

        subject_list = [
            SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",
                subject_name="Mathématiques",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("4.5"),
            ),
            SubjectHours(
                subject_id=uuid4(),
                subject_code="MATH",  # Duplicate!
                subject_name="Mathématiques",
                level_id=level_id,
                level_code="6EME",
                hours_per_week=Decimal("5.0"),
            ),
        ]

        with pytest.raises(InvalidSubjectHoursError, match="Duplicate subjects"):
            validate_subject_hours_list_consistency(subject_list)


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""

    def test_standard_hours_constants(self):
        """Test that standard hours constants are correct."""
        assert STANDARD_HOURS[EducationLevel.PRIMARY] == Decimal("24.0")
        assert STANDARD_HOURS[EducationLevel.SECONDARY] == Decimal("18.0")

    def test_default_max_hsa_constant(self):
        """Test default max HSA constant."""
        assert DEFAULT_MAX_HSA_PER_TEACHER == Decimal("4.0")

    def test_dhg_calculation_large_values(self):
        """Test DHG calculations with very large values."""
        level_id = uuid4()

        # 50 classes (maximum) × 10h (maximum) = 500 hours
        large_input = DHGInput(
            level_id=level_id,
            level_code="6EME",
            education_level=EducationLevel.SECONDARY,
            number_of_classes=50,
            subject_hours_list=[
                SubjectHours(
                    subject_id=uuid4(),
                    subject_code="MATH",
                    subject_name="Mathématiques",
                    level_id=level_id,
                    level_code="6EME",
                    hours_per_week=Decimal("10.0"),
                )
            ],
        )

        result = calculate_dhg_hours(large_input)
        assert result.total_hours == Decimal("500.0")

        # FTE: 500 ÷ 18 = 27.78 → 28 teachers
        fte_result = calculate_fte_from_hours(result)
        assert fte_result.rounded_fte == 28

    def test_hsa_allocation_boundary_conditions(self):
        """Test HSA allocation at exact boundaries."""
        # Exactly at 4h per teacher limit
        # 20 hours HSA, 5 teachers = 4h per teacher (at limit)
        hsa_exact = calculate_hsa_allocation(
            "MATH",
            "Mathématiques",
            Decimal("110.0"),  # 5 × 18 + 20 = 110
            5,
            EducationLevel.SECONDARY,
            Decimal("4.0"),
        )

        assert hsa_exact.hsa_hours_needed == Decimal("20.00")
        assert hsa_exact.hsa_within_limit is True  # Exactly at limit

        # Just over 4h per teacher limit
        # 21 hours HSA, 5 teachers = 4.2h per teacher (over limit)
        hsa_over = calculate_hsa_allocation(
            "MATH",
            "Mathématiques",
            Decimal("111.0"),  # 5 × 18 + 21 = 111
            5,
            EducationLevel.SECONDARY,
            Decimal("4.0"),
        )

        assert hsa_over.hsa_hours_needed == Decimal("21.00")
        assert hsa_over.hsa_within_limit is False  # Over limit
