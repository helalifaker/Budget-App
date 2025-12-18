"""
Unit tests for the new Enrollment Projection Engine (Retention + Lateral Entry).

These tests validate core formulas, override priority, per-grade clamp,
and school-wide capacity constraint per ENROLLMENT_PROJECTION_IMPLEMENTATION_PLAN.md.

Also tests calibrated mode with percentage-based lateral entry for entry point grades.
"""

from decimal import Decimal

from app.engine.enrollment import (
    CYCLE_RETENTION_RATES,
    DOCUMENT_LATERAL_DEFAULTS,
    GRADE_TO_CYCLE,
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
    retention_rate: Decimal | None = None,
    lateral_entry_rate: Decimal | None = None,
) -> EngineEffectiveRates:
    """Create EngineEffectiveRates for a single grade (unified percentage model)."""
    defaults = DOCUMENT_LATERAL_DEFAULTS.get(grade, {})

    if retention_rate is None:
        retention_rate = defaults.get("retention_rate", Decimal("0.96"))

    if lateral_entry_rate is None:
        lateral_entry_rate = defaults.get("lateral_rate", Decimal("0.0"))

    return EngineEffectiveRates(
        grade_code=grade,
        retention_rate=retention_rate,
        lateral_entry_rate=lateral_entry_rate,
        lateral_entry_fixed=None,  # Deprecated
        is_percentage_based=True,  # Always true (unified model)
    )


def make_all_effective_rates(
    retention: Decimal | None = None,  # None = use cycle-based defaults
    scenario_multiplier: Decimal = Decimal("1.0"),
) -> dict[str, EngineEffectiveRates]:
    """Create effective rates for all grades (except PS) using unified percentage model.

    Now uses cycle-based retention rates from CYCLE_RETENTION_RATES:
    - MAT (PS, MS, GS): 96%
    - ELEM (CP-CM2): 96%
    - COLL (6EME-3EME): 97%
    - LYC (2NDE-TLE): 93%
    """
    rates = {}
    for grade in [
        "MS", "GS", "CP", "CE1", "CE2", "CM1", "CM2",
        "6EME", "5EME", "4EME", "3EME", "2NDE", "1ERE", "TLE"
    ]:
        defaults = DOCUMENT_LATERAL_DEFAULTS.get(grade, {})
        base_rate = defaults.get("lateral_rate", Decimal("0.0"))
        # Apply scenario multiplier to all grades (unified percentage model)
        effective_rate = base_rate * scenario_multiplier

        # Use cycle-based retention if not overridden
        if retention is not None:
            grade_retention = retention
        else:
            cycle = GRADE_TO_CYCLE.get(grade, "ELEM")
            grade_retention = defaults.get(
                "retention_rate", CYCLE_RETENTION_RATES.get(cycle, Decimal("0.96"))
            )

        rates[grade] = EngineEffectiveRates(
            grade_code=grade,
            retention_rate=grade_retention,
            lateral_entry_rate=effective_rate,
            lateral_entry_fixed=None,  # Deprecated
            is_percentage_based=True,  # Always true (unified model)
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

    def test_incidental_uses_percentage_rate(self):
        """All grades now use percentage-based lateral (unified model)."""
        rates = {
            "CE1": EngineEffectiveRates(
                grade_code="CE1",
                retention_rate=Decimal("0.96"),
                lateral_entry_rate=Decimal("0.085"),  # 8.5% per unified defaults
                lateral_entry_fixed=None,  # Deprecated - not used
                is_percentage_based=True,  # Always true now
            )
        }
        prev_enrollment = 100
        lateral, retention = calculate_lateral_with_rates("CE1", prev_enrollment, rates)

        # 8.5% of 100 = 8 (int)
        assert lateral == 8
        assert retention == Decimal("0.96")

    def test_missing_grade_uses_document_defaults(self):
        """Missing grade should fall back to UNIFIED_LATERAL_DEFAULTS."""
        rates = {}  # Empty rates
        prev_enrollment = 100
        lateral, retention = calculate_lateral_with_rates("MS", prev_enrollment, rates)

        # MS default rate from UNIFIED_LATERAL_DEFAULTS is 36.3%
        # int(100 * 0.363) = 36
        assert lateral == 36
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

    def test_incidental_uses_percentage_in_projection(self):
        """CE1 should use percentage-based lateral entry (unified model)."""
        rates = make_all_effective_rates()
        rates["CE1"] = EngineEffectiveRates(
            grade_code="CE1",
            retention_rate=Decimal("0.96"),
            lateral_entry_rate=Decimal("0.10"),  # 10% lateral rate
            lateral_entry_fixed=None,  # Deprecated
            is_percentage_based=True,  # Always true
        )

        inp = make_calibrated_input(
            baseline={"CP": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        ce1 = next(g for g in res.grades if g.grade_code == "CE1")
        # Expected: 100 * 0.96 (retention) + 100 * 0.10 (lateral) = 96 + 10 = 106
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
        # Using DOCUMENT_LATERAL_DEFAULTS: MS=36.3%, GS=26.5%

        inp = make_calibrated_input(
            baseline={"PS": 100, "MS": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        ms = next(g for g in res.grades if g.grade_code == "MS")
        gs = next(g for g in res.grades if g.grade_code == "GS")

        # MS: int(100 * 0.96) + int(100 * 0.363) = 96 + 36 = 132
        assert ms.projected_students == 132
        # GS: int(100 * 0.96) + int(100 * 0.265) = 96 + 26 = 122
        assert gs.projected_students == 122

    def test_cycle_transition_entry_points(self):
        """CP, 6EME, 2NDE should use percentage-based lateral entry."""
        rates = make_all_effective_rates()
        # Using DOCUMENT_LATERAL_DEFAULTS: CP=12.3%, 6EME=10.7%, 2NDE=10.8%
        # Note: retention varies by cycle (ELEM=0.96, COLL=0.97, LYC=0.93)

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

        # CP (ELEM): int(100 * 0.96) + int(100 * 0.123) = 96 + 12 = 108
        assert cp.projected_students == 108
        # 6EME (COLL): int(100 * 0.97) + int(100 * 0.107) = 97 + 10 = 107
        assert sixeme.projected_students == 107
        # 2NDE (LYC): int(100 * 0.93) + int(100 * 0.108) = 93 + 10 = 103
        assert seconde.projected_students == 103

    def test_global_retention_adjustment_applies_in_calibrated_mode(self):
        """Global retention_adjustment should be applied on top of calibrated rates.

        This test verifies the fix for Issue 1: retention slider not affecting projections
        when using calibrated mode. The global_overrides.retention_adjustment should now
        be applied on top of the calibrated retention rates.
        """
        # Create rates with 96% retention
        rates = make_all_effective_rates()
        rates["MS"] = EngineEffectiveRates(
            grade_code="MS",
            retention_rate=Decimal("0.96"),  # Base retention from calibration
            lateral_entry_rate=Decimal("0.40"),
            lateral_entry_fixed=None,
            is_percentage_based=True,
        )

        # Increase retention by 1% via global override
        global_overrides = GlobalOverrides(
            retention_adjustment=Decimal("0.01"),  # +1% retention adjustment
        )

        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
            global_overrides=global_overrides,
        )
        res = project_enrollment(inp)

        ms = next(g for g in res.grades if g.grade_code == "MS")
        # Without fix: int(100 * 0.96) + int(100 * 0.40) = 96 + 40 = 136
        # With fix (0.96 + 0.01 = 0.97 retention):
        # int(100 * 0.97) + int(100 * 0.40) = 97 + 40 = 137
        assert ms.retained_students == 97  # 100 * 0.97 = 97 (with adjustment)
        assert ms.lateral_students == 40  # 100 * 0.40 = 40
        assert ms.projected_students == 137  # 97 + 40 = 137

    def test_global_retention_adjustment_at_max_boundary(self):
        """Global retention adjustment at max (+5%) should apply correctly."""
        # Create rates with 96% retention
        rates = make_all_effective_rates()
        rates["MS"] = EngineEffectiveRates(
            grade_code="MS",
            retention_rate=Decimal("0.96"),  # 96% retention
            lateral_entry_rate=Decimal("0.10"),  # 10% lateral
            lateral_entry_fixed=None,
            is_percentage_based=True,
        )

        # Apply max adjustment of +5%
        global_overrides = GlobalOverrides(
            retention_adjustment=Decimal("0.05"),  # +5% (max allowed by schema)
        )

        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
            global_overrides=global_overrides,
        )
        res = project_enrollment(inp)

        ms = next(g for g in res.grades if g.grade_code == "MS")
        # 0.96 + 0.05 = 1.01 -> clamped to 1.0 (100%)
        # int(100 * 1.0) + int(100 * 0.10) = 100 + 10 = 110
        assert ms.retained_students == 100  # Clamped to 100%
        assert ms.lateral_students == 10
        assert ms.projected_students == 110


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
        # MS default rate: 36.3%, with 0.6x multiplier: 21.78%
        # int(100 * 0.96) + int(100 * 0.2178) = 96 + 21 = 117
        assert ms.projected_students == 117

    def test_optimistic_scenario_increases_lateral(self):
        """Optimistic scenario (1.3x) should increase lateral entry."""
        rates = make_all_effective_rates(scenario_multiplier=Decimal("1.30"))

        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)

        ms = next(g for g in res.grades if g.grade_code == "MS")
        # MS default rate: 36.3%, with 1.3x multiplier: 47.19%
        # int(100 * 0.96) + int(100 * 0.4719) = 96 + 47 = 143
        assert ms.projected_students == 143

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
        # Using DOCUMENT_LATERAL_DEFAULTS: MS lateral_rate=36.3%
        ms_values = [
            next(g for g in r.grades if g.grade_code == "MS").projected_students
            for r in results
        ]
        # Calculation uses int() truncation:
        # Year 1: PS base=80 → MS = int(80*0.96) + int(80*0.363) = 76 + 29 = 105
        # Year 2: PS=105 → MS = int(105*0.96) + int(105*0.363) = 100 + 38 = 138
        # Year 3: PS=105 → MS = int(105*0.96) + int(105*0.363) = 100 + 38 = 138
        assert ms_values[0] == 105  # From base {"PS": 80}
        assert ms_values[1] == 138  # From year 1 {"PS": 105}
        assert ms_values[2] == 138  # From year 2 {"PS": 105}


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


# =============================================================================
# Tests for Retain/Lateral Breakdown (R|L|T sub-columns)
# =============================================================================


class TestRetainLateralBreakdown:
    """Tests for retained_students and lateral_students breakdown in GradeProjection."""

    def test_grade_projection_has_retain_lateral_breakdown(self):
        """GradeProjection should include retained_students and lateral_students."""
        rates = make_all_effective_rates()
        rates["MS"] = EngineEffectiveRates(
            grade_code="MS",
            retention_rate=Decimal("0.96"),
            lateral_entry_rate=Decimal("0.40"),  # 40%
            lateral_entry_fixed=None,
            is_percentage_based=True,
        )

        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)
        ms = next(g for g in res.grades if g.grade_code == "MS")

        # Verify breakdown:
        # Retained = int(100 * 0.96) = 96
        # Lateral = int(100 * 0.40) = 40
        # Total = 96 + 40 = 136
        assert ms.retained_students == 96
        assert ms.lateral_students == 40
        assert ms.projected_students == 136
        assert ms.projected_students == ms.retained_students + ms.lateral_students

    def test_ps_grade_has_zero_retain(self):
        """PS grade should have retained_students=0 (entry grade has no retention)."""
        scenario = ScenarioParams(
            code="base",
            ps_entry=65,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("0.96"),
            terminal_retention=Decimal("0.98"),
            lateral_multiplier=Decimal("1.0"),
        )
        inp = make_base_input(scenario=scenario, baseline={})

        res = project_enrollment(inp)
        ps = next(g for g in res.grades if g.grade_code == "PS")

        # PS has no retention (entry grade), all students are "new" (lateral)
        assert ps.retained_students == 0
        assert ps.lateral_students == 65  # All PS students are lateral entries
        assert ps.projected_students == 65

    def test_incidental_grade_uses_percentage_lateral(self):
        """Incidental grade (CE1) should use percentage-based lateral (unified model)."""
        rates = make_all_effective_rates()
        rates["CE1"] = EngineEffectiveRates(
            grade_code="CE1",
            retention_rate=Decimal("0.96"),
            lateral_entry_rate=Decimal("0.10"),  # 10% lateral rate
            lateral_entry_fixed=None,  # Deprecated
            is_percentage_based=True,  # Always true
        )

        inp = make_calibrated_input(
            baseline={"CP": 100},
            effective_rates=rates,
        )
        res = project_enrollment(inp)
        ce1 = next(g for g in res.grades if g.grade_code == "CE1")

        # Retained = int(100 * 0.96) = 96
        # Lateral = int(100 * 0.10) = 10
        # Total = 96 + 10 = 106
        assert ce1.retained_students == 96
        assert ce1.lateral_students == 10
        assert ce1.projected_students == 106

    def test_capacity_constraint_preserves_retain_lateral_ratio(self):
        """When capacity constraint is applied, R and L should be reduced proportionally."""
        # Create scenario where total exceeds capacity
        baseline = {g: 50 for g in [
            "PS", "MS", "GS", "CP", "CE1", "CE2", "CM1", "CM2",
            "6EME", "5EME", "4EME", "3EME", "2NDE", "1ERE", "TLE"
        ]}
        scenario = ScenarioParams(
            code="base",
            ps_entry=50,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("1.00"),  # 100% retention for simplicity
            terminal_retention=Decimal("1.00"),
            lateral_multiplier=Decimal("0.0"),  # No lateral in legacy mode
        )
        inp = make_base_input(
            scenario=scenario,
            baseline=baseline,
            school_max_capacity=100,  # Very low capacity to trigger constraint
        )

        res = project_enrollment(inp)
        assert res.was_capacity_constrained is True

        # Check that total still equals retained + lateral for all grades
        for g in res.grades:
            assert g.projected_students == g.retained_students + g.lateral_students

    def test_multi_year_retain_lateral_consistency(self):
        """Multi-year projection should maintain R|L|T breakdown for each year."""
        rates = make_all_effective_rates()
        inp = make_calibrated_input(
            baseline={"PS": 100},
            effective_rates=rates,
        )
        results = project_multi_year(inp, years=3)

        for year_result in results:
            for grade in year_result.grades:
                # Total should always equal retained + lateral
                assert grade.projected_students == grade.retained_students + grade.lateral_students

    def test_entry_point_lateral_scales_with_previous_enrollment(self):
        """Entry point lateral entry should scale with previous grade enrollment."""
        rates = make_all_effective_rates()
        rates["MS"] = EngineEffectiveRates(
            grade_code="MS",
            retention_rate=Decimal("0.96"),
            lateral_entry_rate=Decimal("0.42"),  # 42%
            lateral_entry_fixed=None,
            is_percentage_based=True,
        )

        # Test with 50 PS students (small enough to avoid grade capacity constraint)
        inp_50 = make_calibrated_input(baseline={"PS": 50}, effective_rates=rates)
        res_50 = project_enrollment(inp_50)
        ms_50 = next(g for g in res_50.grades if g.grade_code == "MS")

        # Test with 100 PS students (still within capacity)
        inp_100 = make_calibrated_input(baseline={"PS": 100}, effective_rates=rates)
        res_100 = project_enrollment(inp_100)
        ms_100 = next(g for g in res_100.grades if g.grade_code == "MS")

        # Lateral should scale proportionally with previous enrollment
        assert ms_50.lateral_students == 21  # int(50 * 0.42)
        assert ms_100.lateral_students == 42  # int(100 * 0.42)

        # Retained should also scale proportionally
        assert ms_50.retained_students == 48  # int(50 * 0.96)
        assert ms_100.retained_students == 96  # int(100 * 0.96)

        # Verify scaling factor (2x enrollment → ~2x students)
        assert ms_100.lateral_students == ms_50.lateral_students * 2
        assert ms_100.retained_students == ms_50.retained_students * 2

