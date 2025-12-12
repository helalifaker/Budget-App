"""
Fiscal Year Proration Calculator

Handles mismatch between school years (Sep–Aug) and fiscal years (Jan–Dec).
Fiscal enrollment = (previous SY × 8/12) + (current SY × 4/12).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TypedDict


class FiscalYearProration(TypedDict):
    fiscal_year: int
    previous_school_year: str
    current_school_year: str
    previous_months: int
    current_months: int
    weighted_enrollment: Decimal


def get_school_years_for_fiscal_year(fiscal_year: int) -> tuple[str, str]:
    """
    Get the two school years that overlap with a fiscal year.

    Example: Fiscal Year 2026
    - Jan–Aug 2026: School Year 2025/2026
    - Sep–Dec 2026: School Year 2026/2027
    """
    previous_school_year = f"{fiscal_year - 1}/{fiscal_year}"
    current_school_year = f"{fiscal_year}/{fiscal_year + 1}"
    return previous_school_year, current_school_year


def calculate_fiscal_year_weighted_enrollment(
    previous_school_year_enrollment: int,
    current_school_year_enrollment: int,
    previous_months: int = 8,
    current_months: int = 4,
) -> Decimal:
    """Calculate weighted average enrollment for fiscal year reporting."""
    total_months = previous_months + current_months
    weighted = (
        (previous_school_year_enrollment * previous_months / total_months)
        + (current_school_year_enrollment * current_months / total_months)
    )
    return Decimal(str(weighted)).quantize(Decimal("0.1"))


def calculate_proration_by_grade(
    previous_enrollment: dict[str, int],
    current_enrollment: dict[str, int],
    fiscal_year: int,
) -> dict[str, FiscalYearProration]:
    """
    Calculate fiscal year proration for all grades.

    Returns a mapping of grade_code → proration breakdown.
    """
    prev_sy, curr_sy = get_school_years_for_fiscal_year(fiscal_year)
    results: dict[str, FiscalYearProration] = {}

    all_grades = set(previous_enrollment.keys()) | set(current_enrollment.keys())
    for grade in all_grades:
        prev_count = previous_enrollment.get(grade, 0)
        curr_count = current_enrollment.get(grade, 0)

        results[grade] = FiscalYearProration(
            fiscal_year=fiscal_year,
            previous_school_year=prev_sy,
            current_school_year=curr_sy,
            previous_months=8,
            current_months=4,
            weighted_enrollment=calculate_fiscal_year_weighted_enrollment(
                prev_count, curr_count
            ),
        )

    return results

