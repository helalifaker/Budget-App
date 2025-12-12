"""
Unit tests for the new Enrollment Projection Engine (Retention + Lateral Entry).

These tests validate core formulas, override priority, per-grade clamp,
and school-wide capacity constraint per ENROLLMENT_PROJECTION_IMPLEMENTATION_PLAN.md.

Also tests calibrated mode with percentage-based lateral entry for entry point grades.
"""

from decimal import Decimal

from app.engine.enrollment import (
    DOCUMENT_LATERAL_DEFAULTS,
    ENTRY_POINT_GRADES,
    EngineEffectiveRates,
    GlobalOverrides,
    GradeOverride,
    LevelOverride,
    ProjectionInput,
    ScenarioParams,
    calculate_lateral_with_rates,
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


# =============================================================================
# Helper functions for calibrated mode tests
# =============================================================================


def make_effective_rates_for_grade(
    grade: str,
    retention_rate: Decimal = Decimal("0.96"),
    lateral_entry_rate: Decimal | None = None,
    lateral_entry_fixed: int | None = None,
) -> EngineEffectiveRates:
    """Create EngineEffectiveRates for a single grade."""
    is_entry_point = grade in ENTRY_POINT_GRADES

    if is_entry_point and lateral_entry_rate is None:
        # Use document default for entry points
        defaults = DOCUMENT_LATERAL_DEFAULTS.get(grade, {})
        lateral_entry_rate = defaults.get("lateral_rate", Decimal("0.10"))

    if not is_entry_point and lateral_entry_fixed is None:
        # Use document default for incidental
        defaults = DOCUMENT_LATERAL_DEFAULTS.get(grade, {})
        lateral_entry_fixed = defaults.get("fixed_lateral", 5)

    return EngineEffectiveRates(
        grade_code=grade,
        retention_rate=retention_rate,
        lateral_entry_rate=lateral_entry_rate if is_entry_point else None,
        lateral_entry_fixed=lateral_entry_fixed if not is_entry_point else None,
        is_percentage_based=is_entry_point,
    )


def make_all_effective_rates(
    retention: Decimal = Decimal("0.96"),
    scenario_multiplier: Decimal = Decimal("1.0"),
) -> dict[str, EngineEffectiveRates]:
    """Create effective rates for all grades (except PS)."""
    rates = {}
    for grade in [
        "MS", "GS", "CP", "CE1", "CE2", "CM1", "CM2",
        "6EME", "5EME", "4EME", "3EME", "2NDE", "1ERE", "TLE"
    ]:
        defaults = DOCUMENT_LATERAL_DEFAULTS.get(grade, {})
        is_entry_point = grade in ENTRY_POINT_GRADES

        if is_entry_point:
            base_rate = defaults.get("lateral_rate", Decimal("0.10"))
            # Apply scenario multiplier to entry point rates
            effective_rate = base_rate * scenario_multiplier
            rates[grade] = EngineEffectiveRates(
                grade_code=grade,
                retention_rate=defaults.get("retention_rate", retention),
                lateral_entry_rate=effective_rate,
                lateral_entry_fixed=None,
                is_percentage_based=True,
            )
        else:
            base_fixed = defaults.get("fixed_lateral", 5)
            # Apply scenario multiplier to fixed values
            effective_fixed = int(base_fixed * float(scenario_multiplier))
            rates[grade] = EngineEffectiveRates(
                grade_code=grade,
                retention_rate=defaults.get("retention_rate", retention),
                lateral_entry_rate=None,
                lateral_entry_fixed=effective_fixed,
                is_percentage_based=False,
            )

    return rates


def make_calibrated_input(
    *,
    base_year: int = 2025,
    target_year: int = 2026,
    baseline: dict[str, int] | None = None,
    effective_rates: dict[str, EngineEffectiveRates] | None = None,
    scenario: ScenarioParams | None = None,
    global_overrides: GlobalOverrides | None = None,
    level_overrides: dict[str, LevelOverride] | None = None,
    grade_overrides: dict[str, GradeOverride] | None = None,
    school_max_capacity: int = 1850,
    default_class_size: int = 25,
) -> ProjectionInput:
    """Create ProjectionInput for calibrated mode."""
    if scenario is None:
        scenario = ScenarioParams(
            code="base",
            ps_entry=65,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("0.96"),
            terminal_retention=Decimal("0.98"),
            lateral_multiplier=Decimal("1.0"),
        )
    if effective_rates is None:
        effective_rates = make_all_effective_rates()

    return ProjectionInput(
        base_year=base_year,
        target_year=target_year,
        projection_years=5,
        school_max_capacity=school_max_capacity,
        default_class_size=default_class_size,
        scenario=scenario,
        base_year_enrollment=baseline or {"PS": 100},
        base_lateral_entry={},  # Empty in calibrated mode
        effective_rates=effective_rates,
        global_overrides=global_overrides,
        level_overrides=level_overrides,
        grade_overrides=grade_overrides,
    )


# =============================================================================
# Test Classes for Calibrated Mode
# =============================================================================


class TestCalculateLateralWithRates:
    """Tests for the calculate_lateral_with_rates function."""

    def test_entry_point_uses_percentage_rate(self):
        """Entry point grades should use percentage of previous grade."""
        rates = {
            "CP": EngineEffectiveRates(
                grade_code="CP",
                retention_rate=Decimal("0.96"),
                lateral_entry_rate=Decimal("0.14"),  # 14%
                lateral_entry_fixed=None,
                is_percentage_based=True,
            )
        }
        prev_enrollment = 100
        lateral, retention = calculate_lateral_with_rates("CP", prev_enrollment, rates)

        # 14% of 100 = 14
        assert lateral == 14
        assert retention == Decimal("0.96")

    def test_incidental_uses_fixed_value(self):
        """Incidental grades should use fixed lateral value."""
        rates = {
            "CE1": EngineEffectiveRates(
                grade_code="CE1",
                retention_rate=Decimal("0.96"),
                lateral_entry_rate=None,
                lateral_entry_fixed=7,
                is_percentage_based=False,
            )
        }
        prev_enrollment = 100  # Should not affect result for incidental
        lateral, retention = calculate_lateral_with_rates("CE1", prev_enrollment, rates)

        # Fixed value of 7
        assert lateral == 7
        assert retention == Decimal("0.96")

    def test_missing_grade_uses_document_defaults(self):
        """Missing grade should fall back to document defaults."""
        rates = {}  # Empty rates
        prev_enrollment = 100
        lateral, retention = calculate_lateral_with_rates("MS", prev_enrollment, rates)

        # MS is entry point, default rate is 42%
        # 42% of 100 = 42
        assert lateral == 42
        assert retention == Decimal("0.96")

    def test_entry_point_scales_with_enrollment(self):
        """Entry point lateral should scale with previous enrollment."""
        rates = {
            "6EME": EngineEffectiveRates(
                grade_code="6EME",
                retention_rate=Decimal("0.96"),
                lateral_entry_rate=Decimal("0.09"),  # 9%
                lateral_entry_fixed=None,
                is_percentage_based=True,
            )
        }

        # With 100 students: 9
        lateral_100, _ = calculate_lateral_with_rates("6EME", 100, rates)
        assert lateral_100 == 9

        # With 200 students: 18
        lateral_200, _ = calculate_lateral_with_rates("6EME", 200, rates)
        assert lateral_200 == 18

    def test_zero_rate_gives_zero_lateral(self):
        """Zero lateral rate should give zero lateral entry."""
        rates = {
            "2NDE": EngineEffectiveRates(
                grade_code="2NDE",
                retention_rate=Decimal("0.96"),
                lateral_entry_rate=Decimal("0"),
                lateral_entry_fixed=None,
                is_percentage_based=True,
            )
        }
        lateral, _ = calculate_lateral_with_rates("2NDE", 100, rates)
        assert lateral == 0


class TestCalibratedProjection:
    """Tests for projection engine in calibrated mode."""

    def test_calibrated_mode_activated_when_effective_rates_provided(self):
        """When effective_rates is provided, calibrated mode is used."""
        effective_rates = make_all_effective_rates()
        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=effective_rates,
        )
        assert inp.effective_rates is not None

    def test_entry_point_uses_percentage_in_projection(self):
        """CP should use percentage-based lateral entry from calibrated rates."""
        # Create rates with 20% lateral rate for CP
        rates = make_all_effective_rates()
        rates["CP"] = EngineEffectiveRates(
            grade_code="CP",
            retention_rate=Decimal("0.96"),
            lateral_entry_rate=Decimal("0.20"),  # 20%
            lateral_entry_fixed=None,
            is_percentage_based=True,
        )

        inp = make_calibrated_input(
            baseline={"GS": 100},  # 100 students in GS
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        cp = next(g for g in res.grades if g.grade_code == "CP")
        # Expected: 100 * 0.96 (retention) + 100 * 0.20 (lateral) = 96 + 20 = 116
        assert cp.projected_students == 116

    def test_incidental_uses_fixed_value_in_projection(self):
        """CE1 should use fixed lateral entry value."""
        rates = make_all_effective_rates()
        rates["CE1"] = EngineEffectiveRates(
            grade_code="CE1",
            retention_rate=Decimal("0.96"),
            lateral_entry_rate=None,
            lateral_entry_fixed=10,  # Fixed 10 students
            is_percentage_based=False,
        )

        inp = make_calibrated_input(
            baseline={"CP": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        ce1 = next(g for g in res.grades if g.grade_code == "CE1")
        # Expected: 100 * 0.96 + 10 = 106
        assert ce1.projected_students == 106

    def test_grade_override_takes_priority_over_effective_rates(self):
        """Grade overrides should override effective rates."""
        rates = make_all_effective_rates()
        rates["MS"] = EngineEffectiveRates(
            grade_code="MS",
            retention_rate=Decimal("0.96"),
            lateral_entry_rate=Decimal("0.40"),  # 40%
            lateral_entry_fixed=None,
            is_percentage_based=True,
        )

        # Override lateral to fixed 5
        grade_overrides = {
            "MS": GradeOverride(
                grade_code="MS",
                lateral_entry=5,  # Override lateral entry
            )
        }

        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
            grade_overrides=grade_overrides,
        )
        res = project_enrollment(inp)

        ms = next(g for g in res.grades if g.grade_code == "MS")
        # Expected: 100 * 0.96 + 5 (overridden) = 101
        assert ms.projected_students == 101

    def test_maternelle_funnel_entry_points(self):
        """MS and GS should both use percentage-based lateral entry."""
        rates = make_all_effective_rates()
        # MS: 42% lateral, GS: 27% lateral (document defaults)

        inp = make_calibrated_input(
            baseline={"PS": 100, "MS": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        ms = next(g for g in res.grades if g.grade_code == "MS")
        gs = next(g for g in res.grades if g.grade_code == "GS")

        # MS: 100 * 0.96 + 100 * 0.42 = 96 + 42 = 138
        assert ms.projected_students == 138
        # GS: 100 * 0.96 + 100 * 0.27 = 96 + 27 = 123
        assert gs.projected_students == 123

    def test_cycle_transition_entry_points(self):
        """CP, 6EME, 2NDE should use percentage-based lateral entry."""
        rates = make_all_effective_rates()

        inp = make_calibrated_input(
            baseline={
                "GS": 100,  # For CP
                "CM2": 100,  # For 6EME
                "3EME": 100,  # For 2NDE
            },
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        cp = next(g for g in res.grades if g.grade_code == "CP")
        sixeme = next(g for g in res.grades if g.grade_code == "6EME")
        seconde = next(g for g in res.grades if g.grade_code == "2NDE")

        # CP: 100 * 0.96 + 100 * 0.14 = 96 + 14 = 110
        assert cp.projected_students == 110
        # 6EME: 100 * 0.96 + 100 * 0.09 = 96 + 9 = 105
        assert sixeme.projected_students == 105
        # 2NDE: 100 * 0.96 + 100 * 0.10 = 96 + 10 = 106
        assert seconde.projected_students == 106


class TestScenarioMultiplierEffect:
    """Tests for scenario multiplier applied to effective rates."""

    def test_conservative_scenario_reduces_lateral(self):
        """Conservative scenario (0.6x) should reduce lateral entry."""
        # Create rates with 0.6x multiplier applied
        rates = make_all_effective_rates(scenario_multiplier=Decimal("0.60"))

        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        ms = next(g for g in res.grades if g.grade_code == "MS")
        # MS default rate: 42%, with 0.6x multiplier: 25.2%
        # 100 * 0.96 + 100 * 0.252 = 96 + 25 = 121
        assert ms.projected_students == 121

    def test_optimistic_scenario_increases_lateral(self):
        """Optimistic scenario (1.3x) should increase lateral entry."""
        rates = make_all_effective_rates(scenario_multiplier=Decimal("1.30"))

        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        ms = next(g for g in res.grades if g.grade_code == "MS")
        # MS default rate: 42%, with 1.3x multiplier: 54.6%
        # 100 * 0.96 + 100 * 0.546 = 96 + 54 = 150
        assert ms.projected_students == 150

    def test_worst_case_scenario_minimizes_lateral(self):
        """Worst case scenario (0.3x) should minimize lateral entry."""
        rates = make_all_effective_rates(scenario_multiplier=Decimal("0.30"))

        inp = make_calibrated_input(
            baseline={"CP": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        ce1 = next(g for g in res.grades if g.grade_code == "CE1")
        # CE1 default fixed: 7, with 0.3x multiplier: 2
        # 100 * 0.96 + 2 = 98
        assert ce1.projected_students == 98


class TestCalibratedMultiYear:
    """Tests for multi-year projection in calibrated mode."""

    def test_multi_year_with_calibrated_rates(self):
        """Multi-year projection should use calibrated rates consistently."""
        rates = make_all_effective_rates()

        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
        )
        results = project_multi_year(inp, years=3)

        assert len(results) == 3
        # Each year should have consistent application of calibrated rates
        for result in results:
            # All grades should be projected
            assert len(result.grades) == 15

    def test_multi_year_entry_point_scaling(self):
        """Entry point lateral should scale as enrollment changes over years.

        Note: In multi-year projection, years_diff is always 1 for each iteration
        because base_year is updated each year. PS entry is calculated as:
        ps_entry * (1 + growth_rate)^1 for each year.
        """
        rates = make_all_effective_rates()

        # Start with high PS entry to see cascade effect
        scenario = ScenarioParams(
            code="optimistic",
            ps_entry=100,  # High PS entry
            entry_growth_rate=Decimal("0.05"),  # 5% growth
            default_retention=Decimal("0.96"),
            terminal_retention=Decimal("0.98"),
            lateral_multiplier=Decimal("1.0"),
        )

        inp = make_calibrated_input(
            baseline={"PS": 80},
            effective_rates=rates,
            scenario=scenario,
        )
        results = project_multi_year(inp, years=3)

        # In multi-year mode, PS is 100 * 1.05^1 = 105 for each year
        # because years_diff is always 1 (target_year - base_year = 1)
        ps_values = [
            next(g for g in r.grades if g.grade_code == "PS").projected_students
            for r in results
        ]
        assert ps_values[0] == 105  # 100 * 1.05^1
        assert ps_values[1] == 105  # 100 * 1.05^1 (same each year)
        assert ps_values[2] == 105  # 100 * 1.05^1

        # Verify lateral entry scales with previous grade enrollment
        # MS receives students from PS, so MS lateral should reflect PS size
        ms_values = [
            next(g for g in r.grades if g.grade_code == "MS").projected_students
            for r in results
        ]
        # Calculation uses int() truncation:
        # Year 1: PS base=80 → MS = int(80*0.96) + int(80*0.42) = 76 + 33 = 109
        # Year 2: PS=105 → MS = int(105*0.96) + int(105*0.42) = 100 + 44 = 144
        # Year 3: PS=105 → MS = int(105*0.96) + int(105*0.42) = 100 + 44 = 144
        assert ms_values[0] == 109  # From base {"PS": 80}
        assert ms_values[1] == 144  # From year 1 {"PS": 105}
        assert ms_values[2] == 144  # From year 2 {"PS": 105}


class TestBackwardCompatibility:
    """Tests to ensure legacy mode still works."""

    def test_legacy_mode_when_no_effective_rates(self):
        """Legacy mode should work when effective_rates is None."""
        inp = make_base_input(
            baseline={"PS": 100},
            lateral={"MS": 27},  # Legacy fixed lateral
        )
        assert inp.effective_rates is None

        res = project_enrollment(inp)
        ms = next(g for g in res.grades if g.grade_code == "MS")
        # Legacy: 100 * 0.96 + 27 = 123
        assert ms.projected_students == 123

    def test_legacy_mode_with_lateral_multiplier(self):
        """Legacy mode should apply lateral multiplier to fixed values."""
        scenario = ScenarioParams(
            code="conservative",
            ps_entry=65,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("0.96"),
            terminal_retention=Decimal("0.98"),
            lateral_multiplier=Decimal("0.5"),  # 50% multiplier
        )

        inp = make_base_input(
            baseline={"PS": 100},
            lateral={"MS": 20},  # Will be multiplied by 0.5
            scenario=scenario,
        )

        res = project_enrollment(inp)
        ms = next(g for g in res.grades if g.grade_code == "MS")
        # 100 * 0.96 + 20 * 0.5 = 96 + 10 = 106
        assert ms.projected_students == 106

