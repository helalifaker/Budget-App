"""
Enrollment Calibration Engine

Pure calculation functions for deriving enrollment projection rates
from historical data using weighted analysis.

Key concepts:
- Weighted progression: 70% N-1 + 30% N-2 (configurable)
- Cycle-based retention: MAT/ELEM 96%, COLL 97%, LYC 93%
- Lateral rate = weighted_progression - retention_rate
- All grades use percentage-based lateral (unified model)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TypedDict

from app.engine.enrollment.projection.projection_engine import GRADE_SEQUENCE, GRADE_TO_CYCLE
from app.engine.enrollment.projection.projection_models import (
    CYCLE_RETENTION_RATES,
    ENTRY_POINT_GRADES,
    UNIFIED_LATERAL_DEFAULTS,
    EngineEffectiveRates,
)


class HistoricalEnrollmentYear(TypedDict):
    """Historical enrollment data for a single school year."""

    fiscal_year: int  # e.g., 2025 for 2024/2025 school year
    grades: dict[str, int]  # grade_code -> student_count


@dataclass(frozen=True)
class GradeProgressionData:
    """Raw progression data for a single grade transition."""

    grade_code: str
    from_year: int
    to_year: int
    prev_grade_students: int  # Students in previous grade at from_year
    current_grade_students: int  # Students in this grade at to_year
    progression_rate: Decimal  # current / prev (can be > 1.0)


@dataclass(frozen=True)
class GradeCalibrationResult:
    """Calibrated rates for a single grade."""

    grade_code: str
    cycle_code: str
    is_entry_point: bool

    # Calculated from historical data
    weighted_progression: Decimal  # 70% N-1 + 30% N-2
    base_retention: Decimal  # From CYCLE_RETENTION_RATES
    derived_lateral_rate: Decimal  # max(0, weighted_progression - retention)

    # Individual year progressions (for transparency)
    progression_n1: Decimal | None  # N-1 progression (e.g., 2024→2025)
    progression_n2: Decimal | None  # N-2 progression (e.g., 2023→2024)

    # Source metadata
    weight_n1: Decimal
    weight_n2: Decimal

    @property
    def effective_progression(self) -> Decimal:
        """Total progression: retention × (1 + lateral)."""
        return self.base_retention * (Decimal("1") + self.derived_lateral_rate)


@dataclass(frozen=True)
class CalibrationResult:
    """Complete calibration result for all grades."""

    grades: dict[str, GradeCalibrationResult]
    calibration_years: list[int]  # [2025, 2024] for example
    weight_n1: Decimal
    weight_n2: Decimal

    def to_effective_rates(self) -> dict[str, EngineEffectiveRates]:
        """Convert calibration results to engine-compatible effective rates."""
        return {
            grade: EngineEffectiveRates(
                grade_code=grade,
                retention_rate=result.base_retention,
                lateral_entry_rate=result.derived_lateral_rate,
            )
            for grade, result in self.grades.items()
        }


def calculate_grade_progression(
    grade: str,
    prev_grade: str,
    from_year_data: HistoricalEnrollmentYear,
    to_year_data: HistoricalEnrollmentYear,
) -> GradeProgressionData | None:
    """
    Calculate progression rate for a grade transition.

    Progression = students_in_grade(to_year) / students_in_prev_grade(from_year)

    Returns None if previous grade had 0 students (cannot calculate rate).
    """
    prev_students = from_year_data["grades"].get(prev_grade, 0)
    current_students = to_year_data["grades"].get(grade, 0)

    if prev_students == 0:
        return None

    progression = Decimal(current_students) / Decimal(prev_students)

    return GradeProgressionData(
        grade_code=grade,
        from_year=from_year_data["fiscal_year"],
        to_year=to_year_data["fiscal_year"],
        prev_grade_students=prev_students,
        current_grade_students=current_students,
        progression_rate=progression.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
    )


def calculate_weighted_progression(
    progression_n1: Decimal | None,
    progression_n2: Decimal | None,
    weight_n1: Decimal = Decimal("0.70"),
    weight_n2: Decimal = Decimal("0.30"),
) -> Decimal | None:
    """
    Calculate weighted average progression from two years.

    Default weights: 70% N-1 + 30% N-2

    Returns:
        Weighted progression, or None if no data available.
        If only one year available, returns that year's value.
    """
    if progression_n1 is not None and progression_n2 is not None:
        weighted = (progression_n1 * weight_n1) + (progression_n2 * weight_n2)
        return weighted.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    elif progression_n1 is not None:
        return progression_n1
    elif progression_n2 is not None:
        return progression_n2
    else:
        return None


def derive_lateral_rate(
    weighted_progression: Decimal,
    retention_rate: Decimal,
) -> Decimal:
    """
    Derive lateral entry rate from weighted progression and retention.

    Formula: lateral_rate = weighted_progression - retention_rate

    If weighted_progression < retention_rate (attrition case),
    lateral_rate is capped at 0 (we don't model negative lateral).

    Example:
        weighted_progression = 1.323 (132.3%)
        retention_rate = 0.96
        lateral_rate = 1.323 - 0.96 = 0.363 (36.3%)
    """
    raw_lateral = weighted_progression - retention_rate
    # Cap at 0 - no negative lateral rates
    lateral = max(raw_lateral, Decimal("0"))
    return lateral.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def calibrate_grade(
    grade: str,
    historical_data: list[HistoricalEnrollmentYear],
    weight_n1: Decimal = Decimal("0.70"),
    weight_n2: Decimal = Decimal("0.30"),
) -> GradeCalibrationResult | None:
    """
    Calibrate rates for a single grade from historical data.

    Requires at least 2 consecutive years of data for N-1 calculation.
    Ideally 3 years for N-1 + N-2 weighted average.

    Args:
        grade: Grade code (e.g., "MS", "CE1", "6EME")
        historical_data: List of historical enrollment by year (most recent first)
        weight_n1: Weight for most recent transition (default 0.70)
        weight_n2: Weight for previous transition (default 0.30)

    Returns:
        GradeCalibrationResult with derived rates, or None if insufficient data.
    """
    # Sort by fiscal year descending (most recent first)
    sorted_data = sorted(historical_data, key=lambda x: x["fiscal_year"], reverse=True)

    if len(sorted_data) < 2:
        return None  # Need at least 2 years for one transition

    # Get previous grade in sequence
    grade_idx = GRADE_SEQUENCE.index(grade) if grade in GRADE_SEQUENCE else -1
    if grade_idx <= 0:
        return None  # PS has no previous grade, or unknown grade

    prev_grade = GRADE_SEQUENCE[grade_idx - 1]
    cycle_code = GRADE_TO_CYCLE.get(grade, "ELEM")

    # Calculate N-1 progression (most recent transition)
    progression_n1_data = calculate_grade_progression(
        grade, prev_grade, sorted_data[1], sorted_data[0]
    )
    progression_n1 = progression_n1_data.progression_rate if progression_n1_data else None

    # Calculate N-2 progression (previous transition) if data available
    progression_n2: Decimal | None = None
    if len(sorted_data) >= 3:
        progression_n2_data = calculate_grade_progression(
            grade, prev_grade, sorted_data[2], sorted_data[1]
        )
        progression_n2 = progression_n2_data.progression_rate if progression_n2_data else None

    # Calculate weighted progression
    weighted_progression = calculate_weighted_progression(
        progression_n1, progression_n2, weight_n1, weight_n2
    )

    if weighted_progression is None:
        return None

    # Get base retention for this grade's cycle
    base_retention = CYCLE_RETENTION_RATES.get(cycle_code, Decimal("0.96"))

    # Derive lateral rate
    derived_lateral = derive_lateral_rate(weighted_progression, base_retention)

    # Check if entry point
    is_entry_point = grade in ENTRY_POINT_GRADES

    return GradeCalibrationResult(
        grade_code=grade,
        cycle_code=cycle_code,
        is_entry_point=is_entry_point,
        weighted_progression=weighted_progression,
        base_retention=base_retention,
        derived_lateral_rate=derived_lateral,
        progression_n1=progression_n1,
        progression_n2=progression_n2,
        weight_n1=weight_n1,
        weight_n2=weight_n2,
    )


def calibrate_from_historical(
    historical_data: list[HistoricalEnrollmentYear],
    weight_n1: Decimal = Decimal("0.70"),
    weight_n2: Decimal = Decimal("0.30"),
) -> CalibrationResult:
    """
    Calibrate all grades from historical enrollment data.

    This is the main entry point for calibration. It calculates weighted
    progression rates for all grades and derives lateral entry rates.

    Args:
        historical_data: List of historical enrollment by year
            (at least 2 years required, 3+ recommended for weighted average)
        weight_n1: Weight for most recent transition (default 0.70)
        weight_n2: Weight for previous transition (default 0.30)

    Returns:
        CalibrationResult with rates for all grades that could be calculated.
        Grades without sufficient data will use defaults.
    """
    calibrated_grades: dict[str, GradeCalibrationResult] = {}
    calibration_years = sorted(
        [d["fiscal_year"] for d in historical_data], reverse=True
    )

    # Skip PS (index 0) - it's the entry grade with no previous
    for grade in GRADE_SEQUENCE[1:]:
        result = calibrate_grade(grade, historical_data, weight_n1, weight_n2)

        if result is not None:
            calibrated_grades[grade] = result
        else:
            # Fall back to defaults
            cycle_code = GRADE_TO_CYCLE.get(grade, "ELEM")
            defaults = UNIFIED_LATERAL_DEFAULTS.get(grade, {})
            base_retention = CYCLE_RETENTION_RATES.get(cycle_code, Decimal("0.96"))
            default_lateral = defaults.get("lateral_rate", Decimal("0"))

            calibrated_grades[grade] = GradeCalibrationResult(
                grade_code=grade,
                cycle_code=cycle_code,
                is_entry_point=grade in ENTRY_POINT_GRADES,
                weighted_progression=base_retention + default_lateral,
                base_retention=base_retention,
                derived_lateral_rate=default_lateral,
                progression_n1=None,
                progression_n2=None,
                weight_n1=weight_n1,
                weight_n2=weight_n2,
            )

    return CalibrationResult(
        grades=calibrated_grades,
        calibration_years=calibration_years[:3],  # Keep max 3 years
        weight_n1=weight_n1,
        weight_n2=weight_n2,
    )


def get_default_effective_rates() -> dict[str, EngineEffectiveRates]:
    """
    Get default effective rates from UNIFIED_LATERAL_DEFAULTS.

    Use this when no historical data is available for calibration.
    Returns rates for all grades except PS.
    """
    rates: dict[str, EngineEffectiveRates] = {}

    for grade in GRADE_SEQUENCE[1:]:  # Skip PS
        defaults = UNIFIED_LATERAL_DEFAULTS.get(grade, {})
        cycle_code = GRADE_TO_CYCLE.get(grade, "ELEM")

        retention = defaults.get(
            "retention_rate", CYCLE_RETENTION_RATES.get(cycle_code, Decimal("0.96"))
        )
        lateral = defaults.get("lateral_rate", Decimal("0"))

        rates[grade] = EngineEffectiveRates(
            grade_code=grade,
            retention_rate=retention,
            lateral_entry_rate=lateral,
        )

    return rates


def compare_with_defaults(
    calibrated: CalibrationResult,
) -> dict[str, dict[str, Decimal]]:
    """
    Compare calibrated rates with defaults for analysis.

    Returns a dict with comparison data for each grade.
    """
    comparisons: dict[str, dict[str, Decimal]] = {}

    for grade, result in calibrated.grades.items():
        defaults = UNIFIED_LATERAL_DEFAULTS.get(grade, {})
        default_lateral = defaults.get("lateral_rate", Decimal("0"))
        default_retention = defaults.get(
            "retention_rate", CYCLE_RETENTION_RATES.get(result.cycle_code, Decimal("0.96"))
        )

        comparisons[grade] = {
            "calibrated_lateral": result.derived_lateral_rate,
            "default_lateral": default_lateral,
            "lateral_diff": result.derived_lateral_rate - default_lateral,
            "calibrated_retention": result.base_retention,
            "default_retention": default_retention,
            "calibrated_progression": result.weighted_progression,
            "default_progression": default_retention + default_lateral,
        }

    return comparisons
