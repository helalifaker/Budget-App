"""
Enrollment Engine - Calculator Functions

Pure calculation functions for enrollment projections.
All functions are stateless with no side effects.

Formulas:
---------
Simple Growth Model:
    projected_enrollment = current_enrollment × (1 + growth_rate) ^ years

Retention Model:
    next_year_enrollment = (current_enrollment × retention_rate) + new_intake

Attrition:
    students_leaving = current_enrollment × attrition_rate
"""

from decimal import Decimal

from app.engine.enrollment.projection.models import (
    EnrollmentGrowthScenario,
    EnrollmentInput,
    EnrollmentProjection,
    EnrollmentProjectionResult,
    RetentionModel,
)

# Growth rate mappings by scenario
SCENARIO_GROWTH_RATES: dict[EnrollmentGrowthScenario, Decimal] = {
    EnrollmentGrowthScenario.CONSERVATIVE: Decimal("0.01"),  # 1% (0-2% range)
    EnrollmentGrowthScenario.BASE: Decimal("0.04"),  # 4% (3-5% range)
    EnrollmentGrowthScenario.OPTIMISTIC: Decimal("0.07"),  # 7% (6-8% range)
}


def calculate_enrollment_projection(
    enrollment_input: EnrollmentInput,
) -> EnrollmentProjectionResult:
    """
    Calculate multi-year enrollment projection using compound growth.

    Formula:
        projected_enrollment = current_enrollment × (1 + growth_rate) ^ years

    Args:
        enrollment_input: Enrollment input with current enrollment and growth parameters

    Returns:
        EnrollmentProjectionResult with year-by-year projections

    Example:
        >>> input_data = EnrollmentInput(
        ...     level_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     level_code="6EME",
        ...     nationality="French",
        ...     current_enrollment=120,
        ...     growth_scenario=EnrollmentGrowthScenario.BASE,
        ...     years_to_project=5
        ... )
        >>> result = calculate_enrollment_projection(input_data)
        >>> result.projections[4].projected_enrollment  # Year 5
        146  # 120 × (1.04)^4 ≈ 146 students
    """
    # Determine growth rate to use
    if enrollment_input.custom_growth_rate is not None:
        growth_rate = enrollment_input.custom_growth_rate
    else:
        growth_rate = SCENARIO_GROWTH_RATES.get(
            enrollment_input.growth_scenario,  # type: ignore
            Decimal("0.04"),  # Default to base case
        )

    # Calculate year-by-year projections
    projections: list[EnrollmentProjection] = []
    current_enrollment = enrollment_input.current_enrollment

    for year in range(1, enrollment_input.years_to_project + 1):
        # Year 1 is the base year (no growth)
        if year == 1:
            projected = current_enrollment
            cumulative_growth = Decimal("0.00")
        else:
            # Apply compound growth: enrollment × (1 + rate)^(year - 1)
            growth_factor = (Decimal("1") + growth_rate) ** (year - 1)
            projected = int(current_enrollment * growth_factor)
            cumulative_growth = growth_factor - Decimal("1")

        projections.append(
            EnrollmentProjection(
                year=year,
                projected_enrollment=projected,
                growth_rate_applied=growth_rate if year > 1 else Decimal("0.00"),
                cumulative_growth=cumulative_growth,
            )
        )

    # Calculate total growth from year 1 to final year
    final_enrollment = projections[-1].projected_enrollment
    total_growth_students = final_enrollment - current_enrollment
    total_growth_percent = projections[-1].cumulative_growth

    return EnrollmentProjectionResult(
        level_id=enrollment_input.level_id,
        level_code=enrollment_input.level_code,
        nationality=enrollment_input.nationality,
        base_enrollment=current_enrollment,
        scenario=enrollment_input.growth_scenario or EnrollmentGrowthScenario.BASE,
        projections=projections,
        total_growth_students=total_growth_students,
        total_growth_percent=total_growth_percent,
        capacity_exceeded=False,  # Capacity check done by validator
    )


def apply_retention_model(
    current_enrollment: int,
    retention_model: RetentionModel,
) -> int:
    """
    Calculate next year's enrollment using retention modeling.

    Formula:
        next_year = (current × retention_rate) + new_intake - attrition

    Where:
        attrition = current × attrition_rate
        retention = current × retention_rate

    Args:
        current_enrollment: Current year student count
        retention_model: Retention parameters (retention rate, new intake)

    Returns:
        Projected enrollment for next year

    Example:
        >>> from uuid import UUID
        >>> model = RetentionModel(
        ...     level_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     retention_rate=Decimal("0.95"),
        ...     attrition_rate=Decimal("0.05"),
        ...     new_student_intake=25
        ... )
        >>> apply_retention_model(120, model)
        139  # (120 × 0.95) + 25 = 114 + 25 = 139 students
    """
    retained_students = int(current_enrollment * retention_model.retention_rate)
    next_year_enrollment = retained_students + retention_model.new_student_intake

    return max(0, next_year_enrollment)  # Ensure non-negative


def calculate_attrition(
    current_enrollment: int,
    attrition_rate: Decimal,
) -> int:
    """
    Calculate number of students expected to leave (attrition).

    Formula:
        students_leaving = current_enrollment × attrition_rate

    Args:
        current_enrollment: Current student count
        attrition_rate: Attrition rate (0.00 to 0.50, i.e., 0% to 50%)

    Returns:
        Number of students expected to leave

    Example:
        >>> calculate_attrition(120, Decimal("0.05"))
        6  # 120 × 0.05 = 6 students leaving
    """
    if not (Decimal("0.00") <= attrition_rate <= Decimal("0.50")):
        raise ValueError(f"Attrition rate must be between 0 and 0.50, got {attrition_rate}")

    students_leaving = int(current_enrollment * attrition_rate)
    return students_leaving


def calculate_multi_level_total(
    projections: list[EnrollmentProjectionResult],
) -> dict[int, int]:
    """
    Calculate total enrollment across all levels for each year.

    Args:
        projections: List of projection results for all levels

    Returns:
        Dictionary mapping year to total enrollment across all levels

    Example:
        >>> # Assume we have projections for 6EME (120→146) and 5EME (115→140)
        >>> totals = calculate_multi_level_total([result_6eme, result_5eme])
        >>> totals[1]
        235  # Year 1: 120 + 115 = 235 students
        >>> totals[5]
        286  # Year 5: 146 + 140 = 286 students
    """
    year_totals: dict[int, int] = {}

    # Get all years from first projection (assume all have same years)
    if not projections:
        return year_totals

    years = [p.year for p in projections[0].projections]

    # Sum enrollment for each year across all levels
    for year in years:
        year_total = 0
        for projection_result in projections:
            # Find projection for this year
            year_projection = next(
                (p for p in projection_result.projections if p.year == year),
                None,
            )
            if year_projection:
                year_total += year_projection.projected_enrollment

        year_totals[year] = year_total

    return year_totals
