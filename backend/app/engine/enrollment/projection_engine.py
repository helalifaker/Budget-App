"""
Enrollment Projection Engine (Retention + Lateral Entry)

Pure calculation functions implementing:
- 3 scenarios with defaults
- 4-layer overrides (Scenario → Global → Level → Grade)
- Per-grade capacity clamp (max divisions × class size ceiling)
- School-wide proportional capacity constraint
- Multi-year iterative cohort progression
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.enrollment.projection_models import (
    GlobalOverrides,
    GradeOverride,
    GradeProjection,
    LevelOverride,
    ProjectionInput,
    ProjectionResult,
    ScenarioParams,
)

# Grade order and cycle mapping (aligned with seeded academic_levels)
GRADE_SEQUENCE: list[str] = [
    "PS",
    "MS",
    "GS",
    "CP",
    "CE1",
    "CE2",
    "CM1",
    "CM2",
    "6EME",
    "5EME",
    "4EME",
    "3EME",
    "2NDE",
    "1ERE",
    "TLE",
]

GRADE_TO_CYCLE: dict[str, str] = {
    "PS": "MAT",
    "MS": "MAT",
    "GS": "MAT",
    "CP": "ELEM",
    "CE1": "ELEM",
    "CE2": "ELEM",
    "CM1": "ELEM",
    "CM2": "ELEM",
    "6EME": "COLL",
    "5EME": "COLL",
    "4EME": "COLL",
    "3EME": "COLL",
    "2NDE": "LYC",
    "1ERE": "LYC",
    "TLE": "LYC",
}


def validate_projection_input(input: ProjectionInput) -> list[str]:
    """Validate projection input for engine safety."""
    errors: list[str] = []
    if not input.base_year_enrollment:
        errors.append("base_year_enrollment is empty")
    if input.school_max_capacity <= 0:
        errors.append("school_max_capacity must be positive")
    if any(v < 0 for v in input.base_year_enrollment.values()):
        errors.append("base_year_enrollment contains negative counts")

    unknown_grades = set(input.base_year_enrollment) - set(GRADE_SEQUENCE)
    if unknown_grades:
        errors.append(f"Unknown grade codes in baseline: {sorted(unknown_grades)}")

    unknown_lateral = set(input.base_lateral_entry) - set(GRADE_SEQUENCE)
    if unknown_lateral:
        errors.append(f"Unknown grade codes in base_lateral_entry: {sorted(unknown_lateral)}")

    return errors


def get_effective_retention(
    grade: str,
    scenario: ScenarioParams,
    global_overrides: GlobalOverrides | None,
    grade_overrides: dict[str, GradeOverride] | None,
) -> Decimal:
    """
    Resolve retention rate using override priority.
    Priority: Grade Override > Global Override > Scenario Default
    """
    if grade_overrides and grade in grade_overrides:
        override_val = grade_overrides[grade].retention_rate
        if override_val is not None:
            return override_val

    base_retention = (
        scenario.terminal_retention if grade == "TLE" else scenario.default_retention
    )
    if global_overrides and global_overrides.retention_adjustment is not None:
        adjusted = base_retention + global_overrides.retention_adjustment
        return min(max(adjusted, Decimal("0.0")), Decimal("1.0"))

    return base_retention


def get_effective_lateral_multiplier(
    scenario: ScenarioParams,
    global_overrides: GlobalOverrides | None,
) -> Decimal:
    """Resolve lateral multiplier using override priority."""
    if global_overrides and global_overrides.lateral_multiplier_override is not None:
        return global_overrides.lateral_multiplier_override
    return scenario.lateral_multiplier


def get_effective_class_size(
    grade: str,
    default_class_size: int,
    global_overrides: GlobalOverrides | None,
    level_overrides: dict[str, LevelOverride] | None,
    grade_overrides: dict[str, GradeOverride] | None,
) -> int:
    """Resolve class size ceiling using 4-layer priority."""
    cycle = GRADE_TO_CYCLE.get(grade, "")

    if grade_overrides and grade in grade_overrides:
        v = grade_overrides[grade].class_size_ceiling
        if v is not None:
            return v

    if level_overrides and cycle in level_overrides:
        v = level_overrides[cycle].class_size_ceiling
        if v is not None:
            return v

    if global_overrides and global_overrides.class_size_override is not None:
        return global_overrides.class_size_override

    return default_class_size


def get_effective_max_divisions(
    grade: str,
    level_overrides: dict[str, LevelOverride] | None,
    grade_overrides: dict[str, GradeOverride] | None,
    default_max: int = 8,
) -> int:
    """Resolve max divisions using 4-layer priority."""
    cycle = GRADE_TO_CYCLE.get(grade, "")

    if grade_overrides and grade in grade_overrides:
        v = grade_overrides[grade].max_divisions
        if v is not None:
            return v

    if level_overrides and cycle in level_overrides:
        v = level_overrides[cycle].max_divisions
        if v is not None:
            return v

    return default_max


def get_effective_lateral_entry(
    grade: str,
    base_lateral_entry: dict[str, int],
    lateral_multiplier: Decimal,
    grade_overrides: dict[str, GradeOverride] | None,
) -> int:
    """Calculate effective lateral entry count."""
    if grade_overrides and grade in grade_overrides:
        v = grade_overrides[grade].lateral_entry
        if v is not None:
            return v

    base = base_lateral_entry.get(grade, 0)
    return int(base * float(lateral_multiplier))


def calculate_divisions(students: int, class_size: int, max_divisions: int) -> int:
    """Calculate number of divisions (classes) needed."""
    if students == 0:
        return 0
    divisions = -(-students // class_size)
    return min(divisions, max_divisions)


def project_single_year(input: ProjectionInput) -> dict[str, int]:
    """
    Project enrollment for a single target year.

    Assumes input.base_year_enrollment represents the immediately
    preceding school year. For multi-year projections, call via
    project_multi_year(), which iteratively updates the base.
    """
    result: dict[str, int] = {}
    years_diff = input.target_year - input.base_year

    ps_entry = input.scenario.ps_entry
    if input.global_overrides and input.global_overrides.ps_entry_adjustment:
        ps_entry += input.global_overrides.ps_entry_adjustment

    growth = float(input.scenario.entry_growth_rate)
    result["PS"] = round(ps_entry * ((1 + growth) ** years_diff))

    for i in range(1, len(GRADE_SEQUENCE)):
        grade = GRADE_SEQUENCE[i]
        prev_grade = GRADE_SEQUENCE[i - 1]

        retention = get_effective_retention(
            grade, input.scenario, input.global_overrides, input.grade_overrides
        )
        lateral_mult = get_effective_lateral_multiplier(
            input.scenario, input.global_overrides
        )
        lateral = get_effective_lateral_entry(
            grade, input.base_lateral_entry, lateral_mult, input.grade_overrides
        )

        prev_enrollment = input.base_year_enrollment.get(prev_grade, 0)
        projected = int(prev_enrollment * float(retention)) + lateral

        max_div = get_effective_max_divisions(
            grade, input.level_overrides, input.grade_overrides
        )
        class_size = get_effective_class_size(
            grade,
            input.default_class_size,
            input.global_overrides,
            input.level_overrides,
            input.grade_overrides,
        )
        grade_capacity = max_div * class_size
        result[grade] = min(projected, grade_capacity)

    return result


def apply_capacity_constraint(
    enrollment_by_grade: dict[str, int],
    max_capacity: int,
) -> tuple[dict[str, int], dict[str, int], bool]:
    """Apply school-wide capacity constraint with proportional reduction."""
    total = sum(enrollment_by_grade.values())

    if total <= max_capacity:
        return enrollment_by_grade, {g: 0 for g in enrollment_by_grade}, False

    reduction_factor = max_capacity / total
    adjusted: dict[str, int] = {}
    reductions: dict[str, int] = {}

    for grade, students in enrollment_by_grade.items():
        adjusted_count = round(students * reduction_factor)
        adjusted[grade] = adjusted_count
        reductions[grade] = students - adjusted_count

    return adjusted, reductions, True


def project_enrollment(input: ProjectionInput) -> ProjectionResult:
    """Project a target year with capacity constraint and full details."""
    raw_projection = project_single_year(input)
    adjusted, reductions, was_constrained = apply_capacity_constraint(
        raw_projection, input.school_max_capacity
    )

    grades: list[GradeProjection] = []

    for grade in GRADE_SEQUENCE:
        students = adjusted.get(grade, 0)
        class_size = get_effective_class_size(
            grade,
            input.default_class_size,
            input.global_overrides,
            input.level_overrides,
            input.grade_overrides,
        )
        max_div = get_effective_max_divisions(
            grade, input.level_overrides, input.grade_overrides
        )

        divisions = calculate_divisions(students, class_size, max_div)
        avg_size = Decimal(students / divisions) if divisions > 0 else Decimal(0)

        reduction = reductions.get(grade, 0)
        original = raw_projection.get(grade) if was_constrained else None
        reduction_pct = (
            Decimal(reduction / original * 100).quantize(Decimal("0.1"))
            if original and original > 0 and reduction > 0
            else None
        )

        grades.append(
            GradeProjection(
                grade_code=grade,
                cycle_code=GRADE_TO_CYCLE[grade],
                projected_students=students,
                divisions=divisions,
                avg_class_size=avg_size.quantize(Decimal("0.1")),
                original_projection=original,
                reduction_applied=reduction,
                reduction_percentage=reduction_pct,
            )
        )

    total = sum(adjusted.values())
    school_year = f"{input.target_year}/{input.target_year + 1}"
    utilization_rate = (
        Decimal(total / input.school_max_capacity * 100).quantize(Decimal("0.1"))
        if input.school_max_capacity > 0
        else Decimal(0)
    )

    return ProjectionResult(
        school_year=school_year,
        fiscal_year=input.target_year,
        grades=grades,
        total_students=total,
        utilization_rate=utilization_rate,
        was_capacity_constrained=was_constrained,
        total_reduction_applied=sum(reductions.values()) if was_constrained else 0,
    )


def project_multi_year(input: ProjectionInput, years: int = 5) -> list[ProjectionResult]:
    """
    Project enrollment for multiple years.

    Uses iterative cohort progression - each year's output becomes the base
    for the next year.
    """
    results: list[ProjectionResult] = []
    current_enrollment = input.base_year_enrollment.copy()

    for year_offset in range(1, years + 1):
        year_input = input.model_copy()
        year_input.base_year_enrollment = current_enrollment
        year_input.target_year = input.base_year + year_offset
        year_input.base_year = input.base_year + year_offset - 1

        result = project_enrollment(year_input)
        results.append(result)

        current_enrollment = {g.grade_code: g.projected_students for g in result.grades}

    return results

