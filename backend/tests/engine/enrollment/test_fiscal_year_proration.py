"""Unit tests for fiscal year proration helpers."""

from decimal import Decimal

from app.engine.enrollment.projection.fiscal_year_proration import (
    calculate_fiscal_year_weighted_enrollment,
    calculate_proration_by_grade,
    get_school_years_for_fiscal_year,
)


def test_get_school_years_for_fiscal_year():
    prev_sy, curr_sy = get_school_years_for_fiscal_year(2026)
    assert prev_sy == "2025/2026"
    assert curr_sy == "2026/2027"


def test_calculate_fiscal_year_weighted_enrollment():
    weighted = calculate_fiscal_year_weighted_enrollment(120, 150)
    assert weighted == Decimal("130.0")


def test_calculate_proration_by_grade_union_and_defaults():
    prev = {"CP": 100}
    curr = {"CP": 120, "CE1": 110}
    results = calculate_proration_by_grade(prev, curr, fiscal_year=2026)
    assert set(results.keys()) == {"CP", "CE1"}
    assert results["CP"]["weighted_enrollment"] == Decimal("106.7")  # (100*8 + 120*4)/12
    assert results["CE1"]["weighted_enrollment"] == Decimal("36.7")  # (0*8 + 110*4)/12

