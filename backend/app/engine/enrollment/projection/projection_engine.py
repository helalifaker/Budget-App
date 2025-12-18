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

from app.engine.enrollment.projection.projection_models import (
    DOCUMENT_LATERAL_DEFAULTS,
    EngineEffectiveRates,
    GlobalOverrides,
    GradeOverride,
    GradeProjection,
    GradeProjectionComponents,
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
    """
    Calculate effective lateral entry count (legacy mode).

    This is the legacy mode that uses fixed lateral entry values.
    For calibrated mode with percentage-based entry points, use
    calculate_lateral_with_rates() instead.
    """
    if grade_overrides and grade in grade_overrides:
        v = grade_overrides[grade].lateral_entry
        if v is not None:
            return v

    base = base_lateral_entry.get(grade, 0)
    # Performance: Single Decimal multiplication, then truncate to int
    return int(Decimal(base) * lateral_multiplier)


def calculate_lateral_with_rates(
    grade: str,
    prev_enrollment: int,
    effective_rates: dict[str, EngineEffectiveRates],
) -> tuple[int, Decimal]:
    """
    Calculate lateral entry using calibrated effective rates.

    All grades now use percentage-based lateral entry (unified model):
        lateral = prev_enrollment × lateral_entry_rate

    Returns:
        tuple[int, Decimal]: (lateral_count, effective_retention_rate)
    """
    rates = effective_rates.get(grade)
    if not rates:
        # Fallback to unified defaults (all percentage-based)
        defaults = DOCUMENT_LATERAL_DEFAULTS.get(grade, {})
        retention = defaults.get("retention_rate", Decimal("0.96"))
        lateral_rate = defaults.get("lateral_rate", Decimal("0"))
        # Performance: Decimal multiplication preserves precision
        lateral = int(Decimal(prev_enrollment) * lateral_rate)
        return lateral, retention

    # Use calibrated rates (all grades use percentage-based lateral)
    retention = rates.retention_rate
    lateral_rate = rates.lateral_entry_rate
    # Performance: Decimal multiplication preserves precision
    lateral = int(Decimal(prev_enrollment) * lateral_rate)

    return lateral, retention


def get_effective_retention_with_rates(
    grade: str,
    effective_rates: dict[str, EngineEffectiveRates] | None,
    scenario: ScenarioParams,
    global_overrides: GlobalOverrides | None,
    grade_overrides: dict[str, GradeOverride] | None,
) -> Decimal:
    """
    Get effective retention rate with support for calibrated rates.

    Priority:
    1. Grade override (if set)
    2. Effective rates (if provided)
    3. Legacy mode (global adjustment + scenario default)
    """
    # Check grade override first (highest priority)
    if grade_overrides and grade in grade_overrides:
        override_val = grade_overrides[grade].retention_rate
        if override_val is not None:
            return override_val

    # Check effective_rates (calibrated mode)
    if effective_rates and grade in effective_rates:
        return effective_rates[grade].retention_rate

    # Fall back to legacy mode
    base_retention = (
        scenario.terminal_retention if grade == "TLE" else scenario.default_retention
    )
    if global_overrides and global_overrides.retention_adjustment is not None:
        adjusted = base_retention + global_overrides.retention_adjustment
        return min(max(adjusted, Decimal("0.0")), Decimal("1.0"))

    return base_retention


def calculate_divisions(students: int, class_size: int, max_divisions: int) -> int:
    """Calculate number of divisions (classes) needed."""
    if students == 0:
        return 0
    divisions = -(-students // class_size)
    return min(divisions, max_divisions)


def project_single_year(input: ProjectionInput) -> dict[str, GradeProjectionComponents]:
    """
    Project enrollment for a single target year with retain/lateral breakdown.

    Returns:
        dict[str, GradeProjectionComponents]: grade_code -> components (retained, lateral, total)

    Supports two modes:

    1. **Calibrated mode** (when input.effective_rates is provided):
       - Uses percentage-based lateral entry for entry points (MS, GS, CP, 6EME, 2NDE)
       - Uses fixed lateral values for incidental grades
       - Retention and lateral rates from EngineEffectiveRates

    2. **Legacy mode** (when input.effective_rates is None):
       - Uses fixed lateral values from base_lateral_entry for all grades
       - Applies lateral_multiplier from scenario
       - Retention from scenario defaults + adjustments

    Assumes input.base_year_enrollment represents the immediately
    preceding school year. For multi-year projections, call via
    project_multi_year(), which iteratively updates the base.
    """
    result: dict[str, GradeProjectionComponents] = {}
    years_diff = input.target_year - input.base_year

    # PS entry calculation (same for both modes)
    # PS has no "retain" - all students are new entries (lateral)
    ps_entry = input.scenario.ps_entry
    if input.global_overrides and input.global_overrides.ps_entry_adjustment:
        ps_entry += input.global_overrides.ps_entry_adjustment

    # Performance: Keep as Decimal throughout for precision, avoid float conversion
    growth_rate = input.scenario.entry_growth_rate
    # Compound growth: ps_entry * (1 + rate)^years using Decimal arithmetic
    growth_factor = (Decimal("1") + growth_rate) ** years_diff
    ps_total = round(ps_entry * growth_factor)
    result["PS"] = GradeProjectionComponents(
        grade_code="PS",
        retained=0,  # PS has no retention - it's the entry grade
        lateral=ps_total,  # All PS students are "new entries"
        total=ps_total,
    )

    # Check which mode to use
    use_calibrated_mode = input.effective_rates is not None

    for i in range(1, len(GRADE_SEQUENCE)):
        grade = GRADE_SEQUENCE[i]
        prev_grade = GRADE_SEQUENCE[i - 1]
        prev_enrollment = input.base_year_enrollment.get(prev_grade, 0)

        if use_calibrated_mode:
            # Calibrated mode: use effective_rates for retention and lateral
            lateral, retention = calculate_lateral_with_rates(
                grade, prev_enrollment, input.effective_rates  # type: ignore
            )

            # Apply global retention adjustment if set (on top of calibrated rate)
            # This allows users to fine-tune retention via the slider control
            if (
                input.global_overrides
                and input.global_overrides.retention_adjustment is not None
            ):
                retention = retention + input.global_overrides.retention_adjustment
                # Clamp to valid range [0.0, 1.0]
                retention = min(max(retention, Decimal("0.0")), Decimal("1.0"))

            # Grade overrides still have highest priority for retention
            if input.grade_overrides and grade in input.grade_overrides:
                override_retention = input.grade_overrides[grade].retention_rate
                if override_retention is not None:
                    retention = override_retention

            # Grade overrides for lateral entry (fixed value override)
            if input.grade_overrides and grade in input.grade_overrides:
                override_lateral = input.grade_overrides[grade].lateral_entry
                if override_lateral is not None:
                    lateral = override_lateral
        else:
            # Legacy mode: use base_lateral_entry with multiplier
            retention = get_effective_retention(
                grade, input.scenario, input.global_overrides, input.grade_overrides
            )
            lateral_mult = get_effective_lateral_multiplier(
                input.scenario, input.global_overrides
            )
            lateral = get_effective_lateral_entry(
                grade, input.base_lateral_entry, lateral_mult, input.grade_overrides
            )

        # Performance: Decimal multiplication preserves precision
        retained = int(Decimal(prev_enrollment) * retention)
        projected = retained + lateral

        # Apply grade capacity constraint
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

        # If capacity constrains, reduce both retained and lateral proportionally
        if projected > grade_capacity:
            # Performance: Use Decimal for precise proportional reduction
            reduction_factor = Decimal(grade_capacity) / Decimal(projected) if projected > 0 else Decimal("1")
            retained = round(Decimal(retained) * reduction_factor)
            lateral = round(Decimal(lateral) * reduction_factor)
            projected = grade_capacity

        result[grade] = GradeProjectionComponents(
            grade_code=grade,
            retained=retained,
            lateral=lateral,
            total=projected,
        )

    return result


def apply_capacity_constraint(
    components_by_grade: dict[str, GradeProjectionComponents],
    max_capacity: int,
) -> tuple[dict[str, GradeProjectionComponents], dict[str, int], bool]:
    """
    Apply school-wide capacity constraint with proportional reduction.

    Preserves the retain/lateral breakdown by reducing both proportionally.

    Returns:
        tuple[dict[str, GradeProjectionComponents], dict[str, int], bool]:
            (adjusted_components, reductions_by_grade, was_constrained)
    """
    total = sum(comp.total for comp in components_by_grade.values())

    if total <= max_capacity:
        return components_by_grade, {g: 0 for g in components_by_grade}, False

    reduction_factor = max_capacity / total
    adjusted: dict[str, GradeProjectionComponents] = {}
    reductions: dict[str, int] = {}

    for grade, comp in components_by_grade.items():
        adjusted_retained = round(comp.retained * reduction_factor)
        adjusted_lateral = round(comp.lateral * reduction_factor)
        adjusted_total = adjusted_retained + adjusted_lateral

        adjusted[grade] = GradeProjectionComponents(
            grade_code=grade,
            retained=adjusted_retained,
            lateral=adjusted_lateral,
            total=adjusted_total,
        )
        reductions[grade] = comp.total - adjusted_total

    return adjusted, reductions, True


def project_enrollment(input: ProjectionInput) -> ProjectionResult:
    """Project a target year with capacity constraint and full details."""
    raw_components = project_single_year(input)
    adjusted_components, reductions, was_constrained = apply_capacity_constraint(
        raw_components, input.school_max_capacity
    )

    grades: list[GradeProjection] = []

    for grade in GRADE_SEQUENCE:
        comp = adjusted_components.get(grade)
        if not comp:
            continue

        students = comp.total
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
        # Performance: Decimal division BEFORE conversion (avoid integer division loss)
        avg_size = Decimal(students) / Decimal(divisions) if divisions > 0 else Decimal(0)

        reduction = reductions.get(grade, 0)
        raw_comp = raw_components.get(grade)
        original = raw_comp.total if was_constrained and raw_comp else None
        # Performance: Decimal division BEFORE multiplication (precision)
        reduction_pct = (
            (Decimal(reduction) / Decimal(original) * 100).quantize(Decimal("0.1"))
            if original and original > 0 and reduction > 0
            else None
        )

        grades.append(
            GradeProjection(
                grade_code=grade,
                cycle_code=GRADE_TO_CYCLE[grade],
                projected_students=students,
                retained_students=comp.retained,
                lateral_students=comp.lateral,
                divisions=divisions,
                avg_class_size=avg_size.quantize(Decimal("0.1")),
                original_projection=original,
                reduction_applied=reduction,
                reduction_percentage=reduction_pct,
            )
        )

    total = sum(comp.total for comp in adjusted_components.values())
    school_year = f"{input.target_year}/{input.target_year + 1}"
    # Performance: Decimal division BEFORE multiplication (precision)
    utilization_rate = (
        (Decimal(total) / Decimal(input.school_max_capacity) * 100).quantize(Decimal("0.1"))
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

