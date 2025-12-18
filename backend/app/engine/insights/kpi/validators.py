"""
KPI Engine - Validators

Business rule validators for KPI calculations.
All validators are pure functions that raise exceptions on validation failure.

Validation Rules:
-----------------
1. Division by zero: Denominators must be positive
2. Ratio bounds: Ratios should be within reasonable ranges
3. Data consistency: Secondary students ≤ total students, personnel costs ≤ total costs
4. Capacity constraints: Current students ≤ max capacity
"""

from decimal import Decimal

from .models import KPIInput, KPIResult


class InvalidKPIInputError(Exception):
    """Raised when KPI input data is invalid or inconsistent."""

    pass


class InvalidRatioBoundsError(Exception):
    """Raised when calculated ratio is outside reasonable bounds."""

    pass


def validate_kpi_input(kpi_input: KPIInput) -> None:
    """
    Validate KPI input data for consistency and business rules.

    Business Rules:
    1. All denominators must be positive (no division by zero)
    2. Secondary students ≤ total students
    3. Personnel costs ≤ total costs
    4. Current students ≤ max capacity
    5. If DHG hours provided, secondary students must be > 0

    Args:
        kpi_input: KPI input data to validate

    Raises:
        InvalidKPIInputError: If input data violates business rules

    Example:
        >>> from uuid import UUID
        >>> from decimal import Decimal
        >>> valid_input = KPIInput(
        ...     total_students=1850,
        ...     secondary_students=650,
        ...     max_capacity=1850,
        ...     total_teacher_fte=Decimal("154.2"),
        ...     total_revenue=Decimal("83272500"),
        ...     total_costs=Decimal("74945250"),
        ...     personnel_costs=Decimal("52461675")
        ... )
        >>> validate_kpi_input(valid_input)  # OK, no exception
        >>> invalid_input = KPIInput(
        ...     total_students=1850,
        ...     secondary_students=2000,  # More than total!
        ...     max_capacity=1850,
        ...     total_teacher_fte=Decimal("154.2"),
        ...     total_revenue=Decimal("83272500"),
        ...     total_costs=Decimal("74945250"),
        ...     personnel_costs=Decimal("52461675")
        ... )
        >>> validate_kpi_input(invalid_input)  # Raises InvalidKPIInputError
        Traceback (most recent call last):
        ...
        InvalidKPIInputError: Secondary students (2000) cannot exceed total students (1850)
    """
    # 1. Check denominators are positive (prevent division by zero)
    if kpi_input.total_students <= 0:
        raise InvalidKPIInputError(
            f"Total students must be positive, got {kpi_input.total_students}"
        )

    if kpi_input.total_teacher_fte <= 0:
        raise InvalidKPIInputError(
            f"Total teacher FTE must be positive, got {kpi_input.total_teacher_fte}"
        )

    if kpi_input.max_capacity <= 0:
        raise InvalidKPIInputError(
            f"Max capacity must be positive, got {kpi_input.max_capacity}"
        )

    if kpi_input.total_revenue < 0:
        raise InvalidKPIInputError(
            f"Total revenue cannot be negative, got {kpi_input.total_revenue}"
        )

    if kpi_input.total_costs < 0:
        raise InvalidKPIInputError(
            f"Total costs cannot be negative, got {kpi_input.total_costs}"
        )

    if kpi_input.personnel_costs < 0:
        raise InvalidKPIInputError(
            f"Personnel costs cannot be negative, got {kpi_input.personnel_costs}"
        )

    # 2. Check secondary students ≤ total students
    if kpi_input.secondary_students > kpi_input.total_students:
        raise InvalidKPIInputError(
            f"Secondary students ({kpi_input.secondary_students}) cannot exceed "
            f"total students ({kpi_input.total_students})"
        )

    # 3. Check personnel costs ≤ total costs
    if kpi_input.personnel_costs > kpi_input.total_costs:
        raise InvalidKPIInputError(
            f"Personnel costs ({kpi_input.personnel_costs}) cannot exceed "
            f"total costs ({kpi_input.total_costs})"
        )

    # 4. Check current students ≤ max capacity (allow slight overage for planning)
    if kpi_input.total_students > kpi_input.max_capacity * Decimal("1.05"):
        raise InvalidKPIInputError(
            f"Total students ({kpi_input.total_students}) significantly exceeds "
            f"max capacity ({kpi_input.max_capacity})"
        )

    # 5. If DHG hours provided, secondary students must be positive
    if kpi_input.dhg_hours_total is not None:
        if kpi_input.dhg_hours_total < 0:
            raise InvalidKPIInputError(
                f"DHG hours cannot be negative, got {kpi_input.dhg_hours_total}"
            )
        if kpi_input.secondary_students <= 0:
            raise InvalidKPIInputError(
                "Secondary students must be positive when DHG hours are provided"
            )


def validate_ratio_bounds(
    kpi_result: KPIResult,
    min_value: Decimal | None = None,
    max_value: Decimal | None = None,
) -> None:
    """
    Validate that a calculated KPI ratio is within reasonable bounds.

    Used for sanity checking calculation results to detect data errors
    or calculation bugs.

    Args:
        kpi_result: Calculated KPI result to validate
        min_value: Minimum acceptable value (inclusive)
        max_value: Maximum acceptable value (inclusive)

    Raises:
        InvalidRatioBoundsError: If ratio is outside bounds

    Example:
        >>> from decimal import Decimal
        >>> ratio_result = KPIResult(
        ...     kpi_type=KPIType.STUDENT_TEACHER_RATIO,
        ...     value=Decimal("12.0"),
        ...     target_value=Decimal("12.0"),
        ...     unit="ratio",
        ...     variance_from_target=Decimal("0.0"),
        ...     performance_status="on_target"
        ... )
        >>> validate_ratio_bounds(ratio_result, Decimal("5.0"), Decimal("20.0"))  # OK
        >>> validate_ratio_bounds(ratio_result, Decimal("15.0"), Decimal("20.0"))  # Raises
        Traceback (most recent call last):
        ...
        InvalidRatioBoundsError: student_teacher_ratio value 12.0 is below minimum 15.0
    """
    if min_value is not None and kpi_result.value < min_value:
        raise InvalidRatioBoundsError(
            f"{kpi_result.kpi_type} value {kpi_result.value} is below minimum {min_value}"
        )

    if max_value is not None and kpi_result.value > max_value:
        raise InvalidRatioBoundsError(
            f"{kpi_result.kpi_type} value {kpi_result.value} exceeds maximum {max_value}"
        )


def validate_student_teacher_ratio(ratio_result: KPIResult) -> None:
    """
    Validate student-teacher ratio is within reasonable educational bounds.

    Business Rule: Student-teacher ratio should be between 5:1 and 25:1.
    Below 5 indicates extremely small classes (expensive).
    Above 25 indicates very large classes (quality concern).

    Args:
        ratio_result: Calculated student-teacher ratio

    Raises:
        InvalidRatioBoundsError: If ratio is outside reasonable bounds

    Example:
        >>> ratio = KPIResult(
        ...     kpi_type=KPIType.STUDENT_TEACHER_RATIO,
        ...     value=Decimal("30.0"),  # Too high!
        ...     target_value=Decimal("12.0"),
        ...     unit="ratio",
        ...     variance_from_target=Decimal("18.0"),
        ...     performance_status="above_target"
        ... )
        >>> validate_student_teacher_ratio(ratio)
        Traceback (most recent call last):
        ...
        InvalidRatioBoundsError: student_teacher_ratio value 30.0 exceeds maximum 25.0
    """
    validate_ratio_bounds(ratio_result, min_value=Decimal("5.0"), max_value=Decimal("25.0"))


def validate_he_ratio_secondary(ratio_result: KPIResult) -> None:
    """
    Validate H/E ratio (Heures/Élève) is within French system norms.

    Business Rule: H/E ratio should be between 1.0 and 2.0 for secondary.
    Below 1.0 indicates insufficient teaching hours (curriculum gaps).
    Above 2.0 indicates excessive hours (inefficiency or small classes).

    Args:
        ratio_result: Calculated H/E ratio

    Raises:
        InvalidRatioBoundsError: If ratio is outside reasonable bounds

    Example:
        >>> he_ratio = KPIResult(
        ...     kpi_type=KPIType.HE_RATIO_SECONDARY,
        ...     value=Decimal("1.35"),
        ...     target_value=Decimal("1.35"),
        ...     unit="ratio",
        ...     variance_from_target=Decimal("0.0"),
        ...     performance_status="on_target"
        ... )
        >>> validate_he_ratio_secondary(he_ratio)  # OK
    """
    validate_ratio_bounds(ratio_result, min_value=Decimal("1.0"), max_value=Decimal("2.0"))


def validate_margin_percentage(margin_result: KPIResult) -> None:
    """
    Validate profit margin percentage is within reasonable business bounds.

    Business Rule: Margin should be between -20% and +30%.
    Below -20% indicates severe financial distress.
    Above +30% may indicate excessive pricing (for a school).

    Args:
        margin_result: Calculated margin percentage

    Raises:
        InvalidRatioBoundsError: If margin is outside reasonable bounds

    Example:
        >>> margin = KPIResult(
        ...     kpi_type=KPIType.MARGIN_PERCENTAGE,
        ...     value=Decimal("-25.0"),  # Severe loss!
        ...     target_value=Decimal("10.0"),
        ...     unit="%",
        ...     variance_from_target=Decimal("-35.0"),
        ...     performance_status="below_target"
        ... )
        >>> validate_margin_percentage(margin)
        Traceback (most recent call last):
        ...
        InvalidRatioBoundsError: margin_percentage value -25.0 is below minimum -20.0
    """
    validate_ratio_bounds(margin_result, min_value=Decimal("-20.0"), max_value=Decimal("30.0"))


def validate_staff_cost_ratio(ratio_result: KPIResult) -> None:
    """
    Validate staff cost ratio is within typical educational organization bounds.

    Business Rule: Personnel costs should be between 50% and 90% of total costs.
    Below 50% may indicate understaffing or excessive non-personnel costs.
    Above 90% may indicate financial stress or insufficient infrastructure investment.

    Args:
        ratio_result: Calculated staff cost ratio

    Raises:
        InvalidRatioBoundsError: If ratio is outside reasonable bounds

    Example:
        >>> staff_ratio = KPIResult(
        ...     kpi_type=KPIType.STAFF_COST_RATIO,
        ...     value=Decimal("70.0"),
        ...     target_value=Decimal("70.0"),
        ...     unit="%",
        ...     variance_from_target=Decimal("0.0"),
        ...     performance_status="on_target"
        ... )
        >>> validate_staff_cost_ratio(staff_ratio)  # OK
    """
    validate_ratio_bounds(ratio_result, min_value=Decimal("50.0"), max_value=Decimal("90.0"))


def validate_capacity_utilization(utilization_result: KPIResult) -> None:
    """
    Validate capacity utilization is within operational bounds.

    Business Rule: Utilization should be between 60% and 105%.
    Below 60% indicates severe underutilization (financial inefficiency).
    Above 105% indicates overcrowding (safety/quality concern).

    Args:
        utilization_result: Calculated capacity utilization

    Raises:
        InvalidRatioBoundsError: If utilization is outside reasonable bounds

    Example:
        >>> utilization = KPIResult(
        ...     kpi_type=KPIType.CAPACITY_UTILIZATION,
        ...     value=Decimal("92.5"),
        ...     target_value=Decimal("92.5"),
        ...     unit="%",
        ...     variance_from_target=Decimal("0.0"),
        ...     performance_status="on_target"
        ... )
        >>> validate_capacity_utilization(utilization)  # OK
    """
    validate_ratio_bounds(
        utilization_result, min_value=Decimal("60.0"), max_value=Decimal("105.0")
    )
