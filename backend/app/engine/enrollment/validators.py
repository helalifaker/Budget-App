"""
Enrollment Engine - Validators

Business rule validators for enrollment projections.
All validators are pure functions that raise exceptions on validation failure.

Business Rules:
--------------
1. Total school capacity: 1,875 students maximum
2. Growth rates: Conservative (0-2%), Base (3-5%), Optimistic (6-8%)
3. Custom growth rates: -50% to +100% allowed
4. Attrition rates: 0% to 50% allowed
5. Retention rates: 50% to 100% allowed
"""

from decimal import Decimal
from typing import Optional

from app.engine.enrollment.models import (
    EnrollmentGrowthScenario,
    EnrollmentProjectionResult,
)


# EFIR School Capacity (from specifications)
EFIR_MAX_CAPACITY = 1875  # Maximum total enrollment


class CapacityExceededError(Exception):
    """Raised when projected enrollment exceeds school capacity."""

    pass


class InvalidGrowthRateError(Exception):
    """Raised when growth rate is outside allowed range."""

    pass


def validate_capacity(
    projected_enrollment: int,
    capacity_limit: int = EFIR_MAX_CAPACITY,
) -> None:
    """
    Validate that projected enrollment does not exceed school capacity.

    Business Rule: EFIR has a maximum capacity of ~1,875 students.

    Args:
        projected_enrollment: Total projected student count
        capacity_limit: Maximum capacity (default: 1,875)

    Raises:
        CapacityExceededError: If projected enrollment exceeds capacity

    Example:
        >>> validate_capacity(1850)  # OK
        >>> validate_capacity(1900)  # Raises CapacityExceededError
        Traceback (most recent call last):
        ...
        CapacityExceededError: Projected enrollment 1900 exceeds capacity 1875
    """
    if projected_enrollment > capacity_limit:
        raise CapacityExceededError(
            f"Projected enrollment {projected_enrollment} exceeds capacity {capacity_limit}"
        )


def validate_total_capacity(
    projection_results: list[EnrollmentProjectionResult],
    capacity_limit: int = EFIR_MAX_CAPACITY,
) -> tuple[bool, Optional[int], Optional[int]]:
    """
    Validate total enrollment across all levels doesn't exceed capacity.

    Checks all years in the projections to find if any year exceeds capacity.

    Args:
        projection_results: List of projection results for all levels
        capacity_limit: Maximum capacity (default: 1,875)

    Returns:
        Tuple of (capacity_exceeded, year_exceeded, total_enrollment)
        - capacity_exceeded: True if any year exceeds capacity
        - year_exceeded: First year where capacity is exceeded (None if OK)
        - total_enrollment: Total enrollment in the year that exceeded (None if OK)

    Example:
        >>> # Assume projections total to 1,850 in all years
        >>> exceeded, year, total = validate_total_capacity([proj1, proj2, proj3])
        >>> exceeded
        False
        >>> # Assume projections total to 1,920 in year 5
        >>> exceeded, year, total = validate_total_capacity([proj1, proj2, proj3])
        >>> exceeded
        True
        >>> year
        5
        >>> total
        1920
    """
    if not projection_results:
        return (False, None, None)

    # Get all years from first projection
    years = [p.year for p in projection_results[0].projections]

    # Check each year
    for year in years:
        year_total = 0
        for result in projection_results:
            # Find projection for this year
            year_proj = next((p for p in result.projections if p.year == year), None)
            if year_proj:
                year_total += year_proj.projected_enrollment

        # Check if this year exceeds capacity
        if year_total > capacity_limit:
            return (True, year, year_total)

    return (False, None, None)


def validate_growth_rate(
    growth_rate: Decimal,
    scenario: Optional[EnrollmentGrowthScenario] = None,
) -> None:
    """
    Validate growth rate is within allowed range for scenario.

    Business Rules:
    - Conservative: 0% to 2% (0.00 to 0.02)
    - Base: 3% to 5% (0.03 to 0.05)
    - Optimistic: 6% to 8% (0.06 to 0.08)
    - Custom: -50% to +100% (-0.50 to 1.00)

    Args:
        growth_rate: Annual growth rate as decimal (e.g., 0.04 = 4%)
        scenario: Optional scenario to validate against specific ranges

    Raises:
        InvalidGrowthRateError: If growth rate is outside allowed range

    Example:
        >>> validate_growth_rate(Decimal("0.04"), EnrollmentGrowthScenario.BASE)  # OK
        >>> validate_growth_rate(Decimal("0.10"), EnrollmentGrowthScenario.BASE)  # Raises
        Traceback (most recent call last):
        ...
        InvalidGrowthRateError: Growth rate 0.10 outside base range (0.03 to 0.05)
    """
    # Check absolute bounds (custom growth rate range)
    if growth_rate < Decimal("-0.50") or growth_rate > Decimal("1.00"):
        raise InvalidGrowthRateError(
            f"Growth rate {growth_rate} must be between -0.50 and 1.00 "
            f"(-50% to +100%)"
        )

    # Check scenario-specific ranges
    if scenario == EnrollmentGrowthScenario.CONSERVATIVE:
        if not (Decimal("0.00") <= growth_rate <= Decimal("0.02")):
            raise InvalidGrowthRateError(
                f"Growth rate {growth_rate} outside conservative range (0.00 to 0.02)"
            )
    elif scenario == EnrollmentGrowthScenario.BASE:
        if not (Decimal("0.03") <= growth_rate <= Decimal("0.05")):
            raise InvalidGrowthRateError(
                f"Growth rate {growth_rate} outside base range (0.03 to 0.05)"
            )
    elif scenario == EnrollmentGrowthScenario.OPTIMISTIC:
        if not (Decimal("0.06") <= growth_rate <= Decimal("0.08")):
            raise InvalidGrowthRateError(
                f"Growth rate {growth_rate} outside optimistic range (0.06 to 0.08)"
            )


def validate_retention_rate(retention_rate: Decimal) -> None:
    """
    Validate retention rate is within allowed range.

    Business Rule: Retention rates must be between 50% and 100%.
    (Below 50% retention indicates serious problems)

    Args:
        retention_rate: Student retention rate (0.50 to 1.00)

    Raises:
        ValueError: If retention rate is outside allowed range

    Example:
        >>> validate_retention_rate(Decimal("0.95"))  # OK
        >>> validate_retention_rate(Decimal("0.30"))  # Raises
        Traceback (most recent call last):
        ...
        ValueError: Retention rate 0.30 must be between 0.50 and 1.00
    """
    if not (Decimal("0.50") <= retention_rate <= Decimal("1.00")):
        raise ValueError(
            f"Retention rate {retention_rate} must be between 0.50 and 1.00 "
            f"(50% to 100%)"
        )


def validate_attrition_rate(attrition_rate: Decimal) -> None:
    """
    Validate attrition rate is within allowed range.

    Business Rule: Attrition rates must be between 0% and 50%.
    (Above 50% attrition indicates catastrophic loss)

    Args:
        attrition_rate: Student attrition rate (0.00 to 0.50)

    Raises:
        ValueError: If attrition rate is outside allowed range

    Example:
        >>> validate_attrition_rate(Decimal("0.05"))  # OK
        >>> validate_attrition_rate(Decimal("0.60"))  # Raises
        Traceback (most recent call last):
        ...
        ValueError: Attrition rate 0.60 must be between 0.00 and 0.50
    """
    if not (Decimal("0.00") <= attrition_rate <= Decimal("0.50")):
        raise ValueError(
            f"Attrition rate {attrition_rate} must be between 0.00 and 0.50 "
            f"(0% to 50%)"
        )
