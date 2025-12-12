"""
Unit tests for the new Enrollment Projection Engine (Retention + Lateral Entry).

These tests validate core formulas, override priority, per-grade clamp,
and school-wide capacity constraint per ENROLLMENT_PROJECTION_IMPLEMENTATION_PLAN.md.
"""

from decimal import Decimal

from app.engine.enrollment import (
    GradeOverride,
    GlobalOverrides,
    LevelOverride,
    ProjectionInput,
    ScenarioParams,
    project_enrollment,
    project_multi_year,
)


def make_base_input(
    *,
    base_year: int = 2025,
    target_year: int = 2026,
    baseline: dict[str, int] | None = None,
    lateral: dict[str, int] | None = None,
    scenario: ScenarioParams | None = None,
    global_overrides: GlobalOverrides | None = None,
    level_overrides: dict[str, LevelOverride] | None = None,
    grade_overrides: dict[str, GradeOverride] | None = None,
    school_max_capacity: int = 1850,
    default_class_size: int = 25,
) -> ProjectionInput:
    if scenario is None:
        scenario = ScenarioParams(
            code="base",
            ps_entry=65,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("0.96"),
            terminal_retention=Decimal("0.98"),
            lateral_multiplier=Decimal("1.0"),
        )
    return ProjectionInput(
        base_year=base_year,
        target_year=target_year,
        projection_years=5,
        school_max_capacity=school_max_capacity,
        default_class_size=default_class_size,
        scenario=scenario,
        base_year_enrollment=baseline or {"PS": 100},
        base_lateral_entry=lateral or {},
        global_overrides=global_overrides,
        level_overrides=level_overrides,
        grade_overrides=grade_overrides,
    )


class TestCoreFormulas:
    def test_ps_entry_growth_with_global_adjustment(self):
        scenario = ScenarioParams(
            code="base",
            ps_entry=65,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("0.96"),
            terminal_retention=Decimal("0.98"),
            lateral_multiplier=Decimal("1.0"),
        )
        overrides = GlobalOverrides(ps_entry_adjustment=10)
        inp = make_base_input(scenario=scenario, global_overrides=overrides)
        res = project_enrollment(inp)
        ps = next(g for g in res.grades if g.grade_code == "PS")
        assert ps.projected_students == 75

    def test_cohort_progression_with_retention_and_lateral(self):
        inp = make_base_input(
            baseline={"PS": 100},
            lateral={"MS": 27},
        )
        res = project_enrollment(inp)
        ms = next(g for g in res.grades if g.grade_code == "MS")
        assert ms.projected_students == 123  # int(100*0.96) + 27

    def test_terminal_retention_applies_to_tle(self):
        inp = make_base_input(
            baseline={"1ERE": 100},
            lateral={"TLE": 1},
        )
        res = project_enrollment(inp)
        tle = next(g for g in res.grades if g.grade_code == "TLE")
        assert tle.projected_students == 99  # int(100*0.98) + 1


class TestOverridesAndClamp:
    def test_grade_override_priority_for_class_size_and_max_divisions(self):
        scenario = ScenarioParams(
            code="base",
            ps_entry=0,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("1.00"),
            terminal_retention=Decimal("1.00"),
            lateral_multiplier=Decimal("1.0"),
        )
        global_overrides = GlobalOverrides(class_size_override=22)
        level_overrides = {
            "ELEM": LevelOverride(cycle_code="ELEM", class_size_ceiling=20, max_divisions=10)
        }
        grade_overrides = {
            "CE1": GradeOverride(
                grade_code="CE1", class_size_ceiling=30, max_divisions=2, retention_rate=None
            )
        }

        inp = make_base_input(
            scenario=scenario,
            baseline={"CP": 200},
            lateral={},
            global_overrides=global_overrides,
            level_overrides=level_overrides,
            grade_overrides=grade_overrides,
        )
        res = project_enrollment(inp)
        ce1 = next(g for g in res.grades if g.grade_code == "CE1")
        assert ce1.projected_students == 60  # clamped to 30*2


class TestSchoolWideCapacityConstraint:
    def test_proportional_reduction_sets_original_and_reductions(self):
        baseline = {g: 50 for g in [
            "PS","MS","GS","CP","CE1","CE2","CM1","CM2","6EME","5EME","4EME","3EME","2NDE","1ERE","TLE"
        ]}
        scenario = ScenarioParams(
            code="base",
            ps_entry=50,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("1.00"),
            terminal_retention=Decimal("1.00"),
            lateral_multiplier=Decimal("0.0"),
        )
        inp = make_base_input(
            scenario=scenario,
            baseline=baseline,
            school_max_capacity=100,
        )
        res = project_enrollment(inp)
        assert res.was_capacity_constrained is True
        assert res.total_reduction_applied > 0
        for g in res.grades:
            assert g.original_projection is not None
            assert g.reduction_applied >= 0


class TestMultiYear:
    def test_project_multi_year_returns_consecutive_years(self):
        inp = make_base_input()
        results = project_multi_year(inp, years=3)
        assert len(results) == 3
        assert [r.fiscal_year for r in results] == [2026, 2027, 2028]

