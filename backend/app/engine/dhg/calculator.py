"""
DHG Engine - Calculator Functions

Pure calculation functions for DHG (Dotation Horaire Globale) methodology.
All functions are stateless with no side effects.

Formulas:
---------
DHG Hours Calculation:
    total_hours = Σ(number_of_classes × hours_per_subject)

Example (Mathématiques in Collège):
    6ème: 6 classes × 4.5h = 27h
    5ème: 6 classes × 3.5h = 21h
    4ème: 5 classes × 3.5h = 17.5h
    3ème: 4 classes × 3.5h = 14h
    Total: 79.5 hours/week

FTE Calculation:
    simple_fte = total_hours ÷ standard_hours
    rounded_fte = ceil(simple_fte)
    utilization = (simple_fte ÷ rounded_fte) × 100

Standard Hours:
    - Primary (Maternelle + Élémentaire): 24h/week
    - Secondary (Collège + Lycée): 18h/week

HSA (Overtime) Allocation:
    hsa_needed = dhg_hours - (available_fte × standard_hours)
    max_hsa = available_fte × max_hsa_per_teacher
    within_limit = hsa_needed ≤ max_hsa
"""

import math
from decimal import Decimal

from app.engine.dhg.models import (
    DHGHoursResult,
    DHGInput,
    EducationLevel,
    FTECalculationResult,
    HSAAllocation,
    TeacherRequirement,
)

# Standard teaching hours by education level
STANDARD_HOURS: dict[EducationLevel, Decimal] = {
    EducationLevel.PRIMARY: Decimal("24.0"),  # Primary: 24h/week
    EducationLevel.SECONDARY: Decimal("18.0"),  # Secondary: 18h/week
}

# HSA limits
DEFAULT_MAX_HSA_PER_TEACHER = Decimal("4.0")  # 4 hours maximum overtime per teacher
MIN_HSA_PER_TEACHER = Decimal("2.0")  # 2 hours minimum for HSA


def calculate_dhg_hours(dhg_input: DHGInput) -> DHGHoursResult:
    """
    Calculate total DHG hours for a level.

    Formula:
        total_hours = Σ(number_of_classes × hours_per_subject)

    Args:
        dhg_input: DHG input with class count and subject hours

    Returns:
        DHGHoursResult with total hours and subject breakdown

    Example:
        >>> from uuid import uuid4
        >>> from decimal import Decimal
        >>> math_hours = SubjectHours(
        ...     subject_id=uuid4(),
        ...     subject_code="MATH",
        ...     subject_name="Mathématiques",
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     hours_per_week=Decimal("4.5")
        ... )
        >>> fran_hours = SubjectHours(
        ...     subject_id=uuid4(),
        ...     subject_code="FRAN",
        ...     subject_name="Français",
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     hours_per_week=Decimal("5.0")
        ... )
        >>> dhg_input = DHGInput(
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     education_level=EducationLevel.SECONDARY,
        ...     number_of_classes=6,
        ...     subject_hours_list=[math_hours, fran_hours]
        ... )
        >>> result = calculate_dhg_hours(dhg_input)
        >>> result.total_hours
        Decimal('57.0')  # (6 × 4.5) + (6 × 5.0) = 27 + 30 = 57
        >>> result.subject_breakdown["MATH"]
        Decimal('27.0')
    """
    subject_breakdown: dict[str, Decimal] = {}
    total_hours = Decimal("0")

    for subject_hours in dhg_input.subject_hours_list:
        # Calculate hours for this subject: classes × hours_per_week
        subject_total = (
            Decimal(dhg_input.number_of_classes) * subject_hours.hours_per_week
        )
        subject_breakdown[subject_hours.subject_code] = subject_total
        total_hours += subject_total

    return DHGHoursResult(
        level_id=dhg_input.level_id,
        level_code=dhg_input.level_code,
        education_level=dhg_input.education_level,
        number_of_classes=dhg_input.number_of_classes,
        total_hours=total_hours,
        subject_breakdown=subject_breakdown,
    )


def calculate_fte_from_hours(
    dhg_hours_result: DHGHoursResult,
) -> FTECalculationResult:
    """
    Calculate teacher FTE from DHG hours.

    Formula:
        simple_fte = total_hours ÷ standard_hours
        rounded_fte = ceil(simple_fte)
        utilization = (simple_fte ÷ rounded_fte) × 100

    Args:
        dhg_hours_result: DHG hours calculation result

    Returns:
        FTECalculationResult with FTE and utilization

    Example:
        >>> # 96 hours ÷ 18 standard hours = 5.33 FTE → 6 teachers
        >>> dhg_result = DHGHoursResult(
        ...     level_id=uuid4(),
        ...     level_code="6EME",
        ...     education_level=EducationLevel.SECONDARY,
        ...     number_of_classes=6,
        ...     total_hours=Decimal("96.0"),
        ...     subject_breakdown={"MATH": Decimal("96.0")}
        ... )
        >>> fte_result = calculate_fte_from_hours(dhg_result)
        >>> fte_result.simple_fte
        Decimal('5.33')
        >>> fte_result.rounded_fte
        6
        >>> fte_result.fte_utilization
        Decimal('88.83')  # (5.33 ÷ 6) × 100
    """
    # Get standard hours for education level
    standard_hours = STANDARD_HOURS[dhg_hours_result.education_level]

    # Calculate simple FTE (may be fractional)
    simple_fte = dhg_hours_result.total_hours / standard_hours

    # Round up to get actual teachers needed (can't hire fractional teachers)
    rounded_fte = math.ceil(simple_fte)

    # Calculate FTE utilization percentage
    if rounded_fte > 0:
        fte_utilization = (simple_fte / Decimal(rounded_fte)) * Decimal("100")
    else:
        fte_utilization = Decimal("0")

    return FTECalculationResult(
        level_id=dhg_hours_result.level_id,
        level_code=dhg_hours_result.level_code,
        education_level=dhg_hours_result.education_level,
        total_dhg_hours=dhg_hours_result.total_hours,
        standard_hours=standard_hours,
        simple_fte=simple_fte.quantize(Decimal("0.01")),
        rounded_fte=rounded_fte,
        fte_utilization=fte_utilization.quantize(Decimal("0.01")),
    )


def calculate_teacher_requirement(
    subject_code: str,
    subject_name: str,
    dhg_hours_list: list[DHGHoursResult],
    education_level: EducationLevel,
) -> TeacherRequirement:
    """
    Calculate teacher requirement for a subject across all levels.

    Aggregates DHG hours for a subject across multiple levels
    (e.g., Mathématiques across 6ème, 5ème, 4ème, 3ème).

    Args:
        subject_code: Subject code (e.g., "MATH")
        subject_name: Subject name (e.g., "Mathématiques")
        dhg_hours_list: List of DHG hours results for all levels
        education_level: Education level (primary or secondary)

    Returns:
        TeacherRequirement with total FTE needed for this subject

    Example:
        >>> # Mathématiques across Collège
        >>> # 6ème: 27h, 5ème: 21h, 4ème: 17.5h, 3ème: 14h
        >>> # Total: 79.5h ÷ 18h = 4.42 FTE → 5 teachers needed
        >>> dhg_6eme = DHGHoursResult(
        ...     level_id=uuid4(), level_code="6EME",
        ...     education_level=EducationLevel.SECONDARY,
        ...     number_of_classes=6, total_hours=Decimal("27.0"),
        ...     subject_breakdown={"MATH": Decimal("27.0")}
        ... )
        >>> dhg_5eme = DHGHoursResult(
        ...     level_id=uuid4(), level_code="5EME",
        ...     education_level=EducationLevel.SECONDARY,
        ...     number_of_classes=6, total_hours=Decimal("21.0"),
        ...     subject_breakdown={"MATH": Decimal("21.0")}
        ... )
        >>> requirement = calculate_teacher_requirement(
        ...     "MATH", "Mathématiques",
        ...     [dhg_6eme, dhg_5eme],
        ...     EducationLevel.SECONDARY
        ... )
        >>> requirement.total_dhg_hours
        Decimal('48.0')  # 27 + 21
        >>> requirement.rounded_fte
        3  # 48 ÷ 18 = 2.67 → 3 teachers
    """
    # Sum up DHG hours for this subject across all levels
    total_dhg_hours = Decimal("0")
    for dhg_result in dhg_hours_list:
        if subject_code in dhg_result.subject_breakdown:
            total_dhg_hours += dhg_result.subject_breakdown[subject_code]

    # Get standard hours
    standard_hours = STANDARD_HOURS[education_level]

    # Calculate FTE
    simple_fte = total_dhg_hours / standard_hours
    rounded_fte = math.ceil(simple_fte)

    # Calculate HSA if FTE is not whole number
    hsa_hours = None
    if simple_fte != rounded_fte and rounded_fte > 0:
        # Remaining hours that would become HSA
        hours_covered = (rounded_fte - 1) * standard_hours
        hsa_hours = total_dhg_hours - hours_covered

    return TeacherRequirement(
        subject_code=subject_code,
        subject_name=subject_name,
        total_dhg_hours=total_dhg_hours,
        standard_hours=standard_hours,
        simple_fte=simple_fte.quantize(Decimal("0.01")),
        rounded_fte=rounded_fte,
        hsa_hours=hsa_hours.quantize(Decimal("0.01")) if hsa_hours else None,
    )


def calculate_hsa_allocation(
    subject_code: str,
    subject_name: str,
    dhg_hours_needed: Decimal,
    available_fte: int,
    education_level: EducationLevel,
    max_hsa_per_teacher: Decimal = DEFAULT_MAX_HSA_PER_TEACHER,
) -> HSAAllocation:
    """
    Calculate HSA (overtime) allocation for a subject.

    Determines if additional hours can be covered by HSA (overtime)
    or if additional teachers need to be hired.

    Business Rule: Max 2-4 hours HSA per teacher per week.

    Args:
        subject_code: Subject code
        subject_name: Subject name
        dhg_hours_needed: Total DHG hours required
        available_fte: Number of available full-time positions
        education_level: Education level (determines standard hours)
        max_hsa_per_teacher: Maximum HSA hours per teacher (default: 4h)

    Returns:
        HSAAllocation with HSA hours and feasibility

    Example:
        >>> # 96 hours needed, 5 teachers available (90 hours)
        >>> # Need 6 extra hours → 6h ÷ 5 teachers = 1.2h HSA per teacher (OK)
        >>> hsa = calculate_hsa_allocation(
        ...     "MATH", "Mathématiques",
        ...     Decimal("96.0"),
        ...     5,
        ...     EducationLevel.SECONDARY,
        ...     Decimal("4.0")
        ... )
        >>> hsa.hsa_hours_needed
        Decimal('6.0')
        >>> hsa.hsa_within_limit
        True  # 1.2h per teacher < 4h max
    """
    # Get standard hours
    standard_hours = STANDARD_HOURS[education_level]

    # Calculate hours covered by available FTE
    available_hours = Decimal(available_fte) * standard_hours

    # Calculate HSA hours needed
    hsa_hours_needed = dhg_hours_needed - available_hours

    # Ensure HSA hours is non-negative
    hsa_hours_needed = max(Decimal("0"), hsa_hours_needed)

    # Check if HSA is within limit
    if available_fte > 0:
        max_total_hsa = Decimal(available_fte) * max_hsa_per_teacher
        hsa_within_limit = hsa_hours_needed <= max_total_hsa
    else:
        # No available FTE means HSA is not possible
        hsa_within_limit = False

    return HSAAllocation(
        subject_code=subject_code,
        subject_name=subject_name,
        dhg_hours_needed=dhg_hours_needed,
        available_fte=available_fte,
        available_hours=available_hours,
        hsa_hours_needed=hsa_hours_needed.quantize(Decimal("0.01")),
        hsa_within_limit=hsa_within_limit,
        max_hsa_per_teacher=max_hsa_per_teacher,
    )


def calculate_aggregated_dhg_hours(
    dhg_hours_list: list[DHGHoursResult],
) -> Decimal:
    """
    Calculate total aggregated DHG hours across all levels.

    Used for calculating overall H/E ratio and total teacher requirements.

    Args:
        dhg_hours_list: List of DHG hours results for all levels

    Returns:
        Total DHG hours across all levels

    Example:
        >>> dhg_6eme = DHGHoursResult(
        ...     level_id=uuid4(), level_code="6EME",
        ...     education_level=EducationLevel.SECONDARY,
        ...     number_of_classes=6, total_hours=Decimal("96.0"),
        ...     subject_breakdown={}
        ... )
        >>> dhg_5eme = DHGHoursResult(
        ...     level_id=uuid4(), level_code="5EME",
        ...     education_level=EducationLevel.SECONDARY,
        ...     number_of_classes=6, total_hours=Decimal("84.0"),
        ...     subject_breakdown={}
        ... )
        >>> total = calculate_aggregated_dhg_hours([dhg_6eme, dhg_5eme])
        >>> total
        Decimal('180.0')
    """
    total_hours = Decimal("0")
    for dhg_result in dhg_hours_list:
        total_hours += dhg_result.total_hours
    return total_hours
