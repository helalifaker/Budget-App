"""
Unit tests for the Enrollment Calibration Engine.

Tests the weighted historical analysis for deriving enrollment rates.
"""

from decimal import Decimal

from app.engine.enrollment.calibration.calibration_engine import (
    CalibrationResult,
    GradeCalibrationResult,
    HistoricalEnrollmentYear,
    calculate_grade_progression,
    calculate_weighted_progression,
    calibrate_from_historical,
    calibrate_grade,
    compare_with_defaults,
    derive_lateral_rate,
    get_default_effective_rates,
)
from app.engine.enrollment.projection.projection_models import (
    CYCLE_RETENTION_RATES,
    UNIFIED_LATERAL_DEFAULTS,
)


class TestCalculateGradeProgression:
    """Tests for calculate_grade_progression function."""

    def test_basic_progression_calculation(self):
        """Test basic progression rate calculation."""
        from_year: HistoricalEnrollmentYear = {
            "fiscal_year": 2024,
            "grades": {"PS": 100, "MS": 110},
        }
        to_year: HistoricalEnrollmentYear = {
            "fiscal_year": 2025,
            "grades": {"PS": 105, "MS": 120},
        }

        result = calculate_grade_progression("MS", "PS", from_year, to_year)

        assert result is not None
        assert result.grade_code == "MS"
        assert result.from_year == 2024
        assert result.to_year == 2025
        assert result.prev_grade_students == 100
        assert result.current_grade_students == 120
        # 120/100 = 1.2
        assert result.progression_rate == Decimal("1.2000")

    def test_progression_below_100_percent(self):
        """Test progression rate below 100% (attrition)."""
        from_year: HistoricalEnrollmentYear = {
            "fiscal_year": 2024,
            "grades": {"CM2": 100},
        }
        to_year: HistoricalEnrollmentYear = {
            "fiscal_year": 2025,
            "grades": {"6EME": 95},
        }

        result = calculate_grade_progression("6EME", "CM2", from_year, to_year)

        assert result is not None
        assert result.progression_rate == Decimal("0.9500")

    def test_zero_previous_enrollment_returns_none(self):
        """Test that zero previous enrollment returns None."""
        from_year: HistoricalEnrollmentYear = {
            "fiscal_year": 2024,
            "grades": {"PS": 0},
        }
        to_year: HistoricalEnrollmentYear = {
            "fiscal_year": 2025,
            "grades": {"MS": 50},
        }

        result = calculate_grade_progression("MS", "PS", from_year, to_year)

        assert result is None

    def test_missing_grade_uses_zero(self):
        """Test that missing grade in to_year uses zero students."""
        from_year: HistoricalEnrollmentYear = {
            "fiscal_year": 2024,
            "grades": {"PS": 100},
        }
        to_year: HistoricalEnrollmentYear = {
            "fiscal_year": 2025,
            "grades": {},  # MS not present
        }

        result = calculate_grade_progression("MS", "PS", from_year, to_year)

        assert result is not None
        assert result.current_grade_students == 0
        assert result.progression_rate == Decimal("0.0000")


class TestCalculateWeightedProgression:
    """Tests for calculate_weighted_progression function."""

    def test_70_30_weighted_average(self):
        """Test default 70/30 weighted average."""
        progression_n1 = Decimal("1.10")  # 110%
        progression_n2 = Decimal("1.30")  # 130%

        result = calculate_weighted_progression(progression_n1, progression_n2)

        # 1.10 * 0.70 + 1.30 * 0.30 = 0.77 + 0.39 = 1.16
        assert result == Decimal("1.1600")

    def test_only_n1_available(self):
        """Test when only N-1 data is available."""
        result = calculate_weighted_progression(
            Decimal("1.20"), None
        )

        assert result == Decimal("1.20")

    def test_only_n2_available(self):
        """Test when only N-2 data is available."""
        result = calculate_weighted_progression(
            None, Decimal("1.15")
        )

        assert result == Decimal("1.15")

    def test_no_data_returns_none(self):
        """Test when no data is available."""
        result = calculate_weighted_progression(None, None)

        assert result is None

    def test_custom_weights(self):
        """Test with custom weights."""
        progression_n1 = Decimal("1.00")
        progression_n2 = Decimal("2.00")

        # 50/50 split
        result = calculate_weighted_progression(
            progression_n1, progression_n2,
            weight_n1=Decimal("0.50"),
            weight_n2=Decimal("0.50"),
        )

        # 1.00 * 0.50 + 2.00 * 0.50 = 0.50 + 1.00 = 1.50
        assert result == Decimal("1.5000")


class TestDeriveLateralRate:
    """Tests for derive_lateral_rate function."""

    def test_positive_lateral_rate(self):
        """Test deriving positive lateral rate from progression above retention."""
        weighted_progression = Decimal("1.323")  # 132.3%
        retention = Decimal("0.96")

        result = derive_lateral_rate(weighted_progression, retention)

        # 1.323 - 0.96 = 0.363
        assert result == Decimal("0.363")

    def test_zero_lateral_when_progression_equals_retention(self):
        """Test lateral is zero when progression equals retention."""
        result = derive_lateral_rate(Decimal("0.96"), Decimal("0.96"))

        assert result == Decimal("0.000")

    def test_lateral_capped_at_zero_for_attrition(self):
        """Test lateral is capped at zero for attrition cases."""
        # Progression below retention (attrition)
        result = derive_lateral_rate(Decimal("0.90"), Decimal("0.96"))

        # Should be capped at 0, not -0.06
        assert result == Decimal("0.000")


class TestCalibrateGrade:
    """Tests for calibrate_grade function."""

    def test_calibrate_with_three_years_data(self):
        """Test calibration with 3 years of data (N-1 + N-2)."""
        historical_data: list[HistoricalEnrollmentYear] = [
            {"fiscal_year": 2025, "grades": {"PS": 105, "MS": 135}},  # Most recent
            {"fiscal_year": 2024, "grades": {"PS": 100, "MS": 120}},  # N-1 base
            {"fiscal_year": 2023, "grades": {"PS": 90, "MS": 100}},   # N-2 base
        ]

        result = calibrate_grade("MS", historical_data)

        assert result is not None
        assert result.grade_code == "MS"
        assert result.cycle_code == "MAT"
        assert result.is_entry_point is True
        assert result.base_retention == Decimal("0.96")

        # N-1 progression: 135/100 = 1.35
        # N-2 progression: 120/90 = 1.333...
        # Weighted: 1.35 * 0.70 + 1.333 * 0.30 ≈ 0.945 + 0.4 = 1.345
        assert result.progression_n1 == Decimal("1.3500")
        assert result.progression_n2 is not None

    def test_calibrate_with_two_years_data(self):
        """Test calibration with only 2 years of data (N-1 only)."""
        historical_data: list[HistoricalEnrollmentYear] = [
            {"fiscal_year": 2025, "grades": {"PS": 105, "MS": 120}},
            {"fiscal_year": 2024, "grades": {"PS": 100, "MS": 110}},
        ]

        result = calibrate_grade("MS", historical_data)

        assert result is not None
        # N-1 progression: 120/100 = 1.20
        assert result.progression_n1 == Decimal("1.2000")
        assert result.progression_n2 is None

    def test_calibrate_returns_none_for_insufficient_data(self):
        """Test calibration returns None with insufficient data."""
        historical_data: list[HistoricalEnrollmentYear] = [
            {"fiscal_year": 2025, "grades": {"PS": 105, "MS": 120}},
        ]

        result = calibrate_grade("MS", historical_data)

        assert result is None

    def test_calibrate_returns_none_for_ps_grade(self):
        """Test calibration returns None for PS (entry grade with no previous)."""
        historical_data: list[HistoricalEnrollmentYear] = [
            {"fiscal_year": 2025, "grades": {"PS": 105}},
            {"fiscal_year": 2024, "grades": {"PS": 100}},
        ]

        result = calibrate_grade("PS", historical_data)

        assert result is None


class TestCalibrateFromHistorical:
    """Tests for calibrate_from_historical function."""

    def test_calibrate_all_grades(self):
        """Test calibrating all grades from historical data."""
        # Create realistic historical data
        historical_data: list[HistoricalEnrollmentYear] = [
            {
                "fiscal_year": 2025,
                "grades": {
                    "PS": 65, "MS": 85, "GS": 100,
                    "CP": 108, "CE1": 105, "CE2": 100,
                    "CM1": 98, "CM2": 103,
                    "6EME": 107, "5EME": 99, "4EME": 100, "3EME": 100,
                    "2NDE": 103, "1ERE": 97, "TLE": 100,
                },
            },
            {
                "fiscal_year": 2024,
                "grades": {
                    "PS": 65, "MS": 80, "GS": 95,
                    "CP": 100, "CE1": 100, "CE2": 100,
                    "CM1": 100, "CM2": 100,
                    "6EME": 100, "5EME": 100, "4EME": 100, "3EME": 100,
                    "2NDE": 100, "1ERE": 100, "TLE": 100,
                },
            },
        ]

        result = calibrate_from_historical(historical_data)

        assert isinstance(result, CalibrationResult)
        # Should have 14 grades (all except PS)
        assert len(result.grades) == 14
        assert "PS" not in result.grades
        assert "MS" in result.grades
        assert "TLE" in result.grades

    def test_calibration_result_to_effective_rates(self):
        """Test converting calibration result to effective rates."""
        historical_data: list[HistoricalEnrollmentYear] = [
            {"fiscal_year": 2025, "grades": {"PS": 100, "MS": 130}},
            {"fiscal_year": 2024, "grades": {"PS": 100, "MS": 120}},
        ]

        calibration = calibrate_from_historical(historical_data)
        rates = calibration.to_effective_rates()

        assert "MS" in rates
        assert rates["MS"].grade_code == "MS"
        assert rates["MS"].retention_rate == Decimal("0.96")

    def test_grades_without_data_use_defaults(self):
        """Test that grades without historical data use defaults."""
        # Only provide data for MS, other grades will use defaults
        historical_data: list[HistoricalEnrollmentYear] = [
            {"fiscal_year": 2025, "grades": {"PS": 100, "MS": 130}},
            {"fiscal_year": 2024, "grades": {"PS": 100, "MS": 120}},
        ]

        result = calibrate_from_historical(historical_data)

        # CP should have default values since no CP data provided
        cp_result = result.grades.get("CP")
        assert cp_result is not None
        # Should use defaults from UNIFIED_LATERAL_DEFAULTS
        assert cp_result.base_retention == Decimal("0.96")


class TestGetDefaultEffectiveRates:
    """Tests for get_default_effective_rates function."""

    def test_returns_rates_for_all_grades_except_ps(self):
        """Test that default rates are returned for all grades except PS."""
        rates = get_default_effective_rates()

        assert "PS" not in rates
        assert len(rates) == 14

    def test_rates_match_unified_defaults(self):
        """Test that rates match UNIFIED_LATERAL_DEFAULTS."""
        rates = get_default_effective_rates()

        for grade, rate in rates.items():
            defaults = UNIFIED_LATERAL_DEFAULTS.get(grade, {})
            expected_retention = defaults.get("retention_rate", Decimal("0.96"))
            expected_lateral = defaults.get("lateral_rate", Decimal("0"))

            assert rate.retention_rate == expected_retention
            assert rate.lateral_entry_rate == expected_lateral

    def test_entry_point_detection(self):
        """Test that entry point grades are correctly identified."""
        rates = get_default_effective_rates()

        # Entry points
        assert rates["MS"].is_entry_point is True
        assert rates["GS"].is_entry_point is True
        assert rates["CP"].is_entry_point is True
        assert rates["6EME"].is_entry_point is True
        assert rates["2NDE"].is_entry_point is True

        # Non-entry points
        assert rates["CE1"].is_entry_point is False
        assert rates["5EME"].is_entry_point is False
        assert rates["TLE"].is_entry_point is False


class TestCompareWithDefaults:
    """Tests for compare_with_defaults function."""

    def test_comparison_shows_differences(self):
        """Test that comparison shows differences from defaults."""
        historical_data: list[HistoricalEnrollmentYear] = [
            {"fiscal_year": 2025, "grades": {"PS": 100, "MS": 150}},  # High lateral
            {"fiscal_year": 2024, "grades": {"PS": 100, "MS": 120}},
        ]

        calibration = calibrate_from_historical(historical_data)
        comparison = compare_with_defaults(calibration)

        assert "MS" in comparison
        ms_compare = comparison["MS"]

        # Check comparison fields exist
        assert "calibrated_lateral" in ms_compare
        assert "default_lateral" in ms_compare
        assert "lateral_diff" in ms_compare
        assert "calibrated_retention" in ms_compare
        assert "default_retention" in ms_compare


class TestGradeCalibrationResultProperties:
    """Tests for GradeCalibrationResult properties."""

    def test_effective_progression_calculation(self):
        """Test effective_progression property calculation."""
        result = GradeCalibrationResult(
            grade_code="MS",
            cycle_code="MAT",
            is_entry_point=True,
            weighted_progression=Decimal("1.32"),
            base_retention=Decimal("0.96"),
            derived_lateral_rate=Decimal("0.36"),
            progression_n1=Decimal("1.30"),
            progression_n2=Decimal("1.35"),
            weight_n1=Decimal("0.70"),
            weight_n2=Decimal("0.30"),
        )

        # effective_progression = retention × (1 + lateral)
        # = 0.96 × (1 + 0.36) = 0.96 × 1.36 = 1.3056
        expected = Decimal("0.96") * Decimal("1.36")
        assert result.effective_progression == expected


class TestCycleRetentionRates:
    """Tests for cycle-specific retention rates."""

    def test_maternelle_retention(self):
        """Test MAT cycle retention rate."""
        assert CYCLE_RETENTION_RATES["MAT"] == Decimal("0.96")

    def test_elementaire_retention(self):
        """Test ELEM cycle retention rate."""
        assert CYCLE_RETENTION_RATES["ELEM"] == Decimal("0.96")

    def test_college_retention(self):
        """Test COLL cycle retention rate (higher commitment)."""
        assert CYCLE_RETENTION_RATES["COLL"] == Decimal("0.97")

    def test_lycee_retention(self):
        """Test LYC cycle retention rate (students leave for France)."""
        assert CYCLE_RETENTION_RATES["LYC"] == Decimal("0.93")
