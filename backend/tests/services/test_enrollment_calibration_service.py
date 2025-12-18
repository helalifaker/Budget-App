"""
Tests for Enrollment Calibration Service.

Tests cover:
- Rolling 4-year window calculation
- Historical data fetching and summarization
- Calibration algorithm (progression rate decomposition)
- Confidence level calculation
- Parameter override management
- Scenario multiplier management
- Effective rate resolution (override → derived → default)
- Reset operations

NOTE: Uses both unit tests (mocked) and integration tests (with DB fixtures).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models import (
    AcademicLevel,
    EnrollmentScenario,
    HistoricalActuals,
    HistoricalDimensionType,
    HistoricalModuleCode,
    StudentsCalibration,
    Version,
    VersionStatus,
)

# Backward compatibility aliases
BudgetVersion = Version
BudgetVersionStatus = VersionStatus
from app.schemas.enrollment.enrollment_settings import (
    DOCUMENT_DEFAULTS,
    ENTRY_POINT_GRADES,
)
from app.services.enrollment.enrollment_calibration_service import (
    EnrollmentCalibrationService,
    calculate_confidence,
    calculate_data_quality_score,
    fiscal_year_to_school_year,
    get_historical_fiscal_years,
    get_historical_window,
    get_previous_grade,
    school_year_to_fiscal_year,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ==============================================================================
# Unit Tests - Pure Functions (No DB Required)
# ==============================================================================


class TestGetPreviousGrade:
    """Tests for get_previous_grade helper function."""

    def test_ms_has_no_previous(self):
        """MS is first grade in sequence after PS."""
        # MS's previous is PS, but we're looking for grade-1
        prev = get_previous_grade("PS")
        assert prev is None

    def test_gs_previous_is_ms(self):
        """GS previous grade is MS."""
        prev = get_previous_grade("GS")
        assert prev == "MS"

    def test_cp_previous_is_gs(self):
        """CP previous grade is GS."""
        prev = get_previous_grade("CP")
        assert prev == "GS"

    def test_6eme_previous_is_cm2(self):
        """6EME previous grade is CM2."""
        prev = get_previous_grade("6EME")
        assert prev == "CM2"

    def test_2nde_previous_is_3eme(self):
        """2NDE previous grade is 3EME."""
        prev = get_previous_grade("2NDE")
        assert prev == "3EME"

    def test_tle_previous_is_1ere(self):
        """TLE previous grade is 1ERE."""
        prev = get_previous_grade("TLE")
        assert prev == "1ERE"

    def test_invalid_grade_returns_none(self):
        """Invalid grade returns None."""
        prev = get_previous_grade("INVALID")
        assert prev is None


class TestGetHistoricalWindow:
    """Tests for get_historical_window helper function."""

    def test_window_for_2025_2026(self):
        """Test window calculation for 2025/2026."""
        window = get_historical_window("2025/2026", window_size=4)
        assert window == ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]

    def test_window_for_2030_2031(self):
        """Test window calculation for 2030/2031 (future-proofing)."""
        window = get_historical_window("2030/2031", window_size=4)
        assert window == ["2026/2027", "2027/2028", "2028/2029", "2029/2030"]

    def test_window_size_2(self):
        """Test with custom window size of 2."""
        window = get_historical_window("2025/2026", window_size=2)
        assert window == ["2023/2024", "2024/2025"]

    def test_window_size_5(self):
        """Test with custom window size of 5."""
        window = get_historical_window("2025/2026", window_size=5)
        assert len(window) == 5
        assert window[0] == "2020/2021"

    def test_window_is_chronologically_sorted(self):
        """Window years should be chronologically sorted."""
        window = get_historical_window("2025/2026")
        years = [int(y.split("/")[0]) for y in window]
        assert years == sorted(years)


class TestFiscalYearConversion:
    """Tests for fiscal year ↔ school year conversion functions."""

    def test_fiscal_to_school_year_2024(self):
        """Test 2024 → '2024/2025'."""
        assert fiscal_year_to_school_year(2024) == "2024/2025"

    def test_fiscal_to_school_year_2021(self):
        """Test 2021 → '2021/2022'."""
        assert fiscal_year_to_school_year(2021) == "2021/2022"

    def test_school_to_fiscal_year_2024(self):
        """Test '2024/2025' → 2024."""
        assert school_year_to_fiscal_year("2024/2025") == 2024

    def test_school_to_fiscal_year_2021(self):
        """Test '2021/2022' → 2021."""
        assert school_year_to_fiscal_year("2021/2022") == 2021

    def test_roundtrip_conversion(self):
        """Test that conversions are inverses of each other."""
        for year in [2020, 2024, 2030]:
            school_year = fiscal_year_to_school_year(year)
            assert school_year_to_fiscal_year(school_year) == year


class TestGetHistoricalFiscalYears:
    """Tests for get_historical_fiscal_years helper function."""

    def test_fiscal_years_for_2025_2026(self):
        """Test fiscal year window calculation for 2025/2026."""
        fiscal_years = get_historical_fiscal_years("2025/2026", window_size=4)
        assert fiscal_years == [2021, 2022, 2023, 2024]

    def test_fiscal_years_for_2030_2031(self):
        """Test fiscal year window calculation for 2030/2031."""
        fiscal_years = get_historical_fiscal_years("2030/2031", window_size=4)
        assert fiscal_years == [2026, 2027, 2028, 2029]

    def test_fiscal_years_window_size_2(self):
        """Test with window size 2."""
        fiscal_years = get_historical_fiscal_years("2025/2026", window_size=2)
        assert fiscal_years == [2023, 2024]


class TestCalculateConfidence:
    """Tests for calculate_confidence helper function."""

    def test_high_confidence_low_std_3_years(self):
        """High confidence: std < 5%, 3+ years."""
        confidence = calculate_confidence(std_dev=0.03, years_used=3)
        assert confidence == "high"

    def test_high_confidence_low_std_4_years(self):
        """High confidence: std < 5%, 4 years."""
        confidence = calculate_confidence(std_dev=0.04, years_used=4)
        assert confidence == "high"

    def test_medium_confidence_medium_std_2_years(self):
        """Medium confidence: std < 10%, 2+ years."""
        confidence = calculate_confidence(std_dev=0.08, years_used=2)
        assert confidence == "medium"

    def test_medium_confidence_low_std_2_years(self):
        """Medium confidence: std < 5%, but only 2 years."""
        confidence = calculate_confidence(std_dev=0.04, years_used=2)
        assert confidence == "medium"

    def test_low_confidence_high_std(self):
        """Low confidence: std >= 10%."""
        confidence = calculate_confidence(std_dev=0.15, years_used=4)
        assert confidence == "low"

    def test_low_confidence_insufficient_years(self):
        """Low confidence: insufficient years."""
        confidence = calculate_confidence(std_dev=0.02, years_used=1)
        assert confidence == "low"

    def test_boundary_at_5_percent(self):
        """Boundary test at 5% std threshold."""
        # Exactly 5% should be medium (not <5%)
        confidence = calculate_confidence(std_dev=0.05, years_used=3)
        assert confidence == "medium"

    def test_boundary_at_10_percent(self):
        """Boundary test at 10% std threshold."""
        # Exactly 10% should be low (not <10%)
        confidence = calculate_confidence(std_dev=0.10, years_used=3)
        assert confidence == "low"


class TestCalculateDataQualityScore:
    """Tests for calculate_data_quality_score helper function."""

    def test_minimum_score_no_data(self):
        """Minimum score with no data."""
        score = calculate_data_quality_score(
            total_years=0, avg_confidence=0.0, has_all_grades=False
        )
        assert score == 1

    def test_maximum_score_full_data(self):
        """Maximum score with full data."""
        score = calculate_data_quality_score(
            total_years=4, avg_confidence=0.8, has_all_grades=True
        )
        assert score == 5

    def test_partial_years_bonus(self):
        """Test 2-3 years gives 1 point bonus."""
        score = calculate_data_quality_score(
            total_years=3, avg_confidence=0.0, has_all_grades=False
        )
        assert score == 2  # 1 base + 1 for years

    def test_full_years_bonus(self):
        """Test 4+ years gives 2 points bonus."""
        score = calculate_data_quality_score(
            total_years=5, avg_confidence=0.0, has_all_grades=False
        )
        assert score == 3  # 1 base + 2 for years

    def test_confidence_bonus(self):
        """Test high confidence gives 1 point bonus."""
        score = calculate_data_quality_score(
            total_years=0, avg_confidence=0.75, has_all_grades=False
        )
        assert score == 2  # 1 base + 1 for confidence

    def test_grade_coverage_bonus(self):
        """Test all grades gives 1 point bonus."""
        score = calculate_data_quality_score(
            total_years=0, avg_confidence=0.0, has_all_grades=True
        )
        assert score == 2  # 1 base + 1 for grades


class TestDocumentDefaults:
    """Tests for document defaults constants."""

    def test_entry_point_grades_have_lateral_rate(self):
        """Entry point grades should have lateral_rate in defaults."""
        for grade in ENTRY_POINT_GRADES:
            assert grade in DOCUMENT_DEFAULTS
            assert "lateral_rate" in DOCUMENT_DEFAULTS[grade]
            assert "retention_rate" in DOCUMENT_DEFAULTS[grade]

    def test_incidental_grades_have_fixed_lateral(self):
        """Incidental grades should have fixed_lateral in defaults."""
        incidental_grades = {"CE1", "CE2", "CM1", "CM2", "5EME", "4EME", "3EME", "1ERE", "TLE"}
        for grade in incidental_grades:
            assert grade in DOCUMENT_DEFAULTS
            assert "fixed_lateral" in DOCUMENT_DEFAULTS[grade]
            assert "retention_rate" in DOCUMENT_DEFAULTS[grade]

    def test_ms_lateral_rate(self):
        """MS should have 42% lateral rate."""
        assert DOCUMENT_DEFAULTS["MS"]["lateral_rate"] == Decimal("0.42")

    def test_cp_lateral_rate(self):
        """CP should have 14% lateral rate."""
        assert DOCUMENT_DEFAULTS["CP"]["lateral_rate"] == Decimal("0.14")

    def test_tle_higher_retention(self):
        """TLE should have 98% retention rate."""
        assert DOCUMENT_DEFAULTS["TLE"]["retention_rate"] == Decimal("0.98")

    def test_tle_low_lateral(self):
        """TLE should have fixed lateral of 1."""
        assert DOCUMENT_DEFAULTS["TLE"]["fixed_lateral"] == 1


# ==============================================================================
# Unit Tests - Service Methods (Mocked DB)
# ==============================================================================


class TestCalibrationServiceUnit:
    """Unit tests for CalibrationService with mocked database."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> EnrollmentCalibrationService:
        """Create service with mock session."""
        return EnrollmentCalibrationService(mock_session)

    @pytest.mark.asyncio
    async def test_get_current_school_year_september(self, service):
        """Test school year detection in September (new year)."""
        with patch("app.services.enrollment.enrollment_calibration_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 9, 15, tzinfo=UTC)
            year = await service.get_current_school_year()
            assert year == "2025/2026"

    @pytest.mark.asyncio
    async def test_get_current_school_year_june(self, service):
        """Test school year detection in June (same year)."""
        with patch("app.services.enrollment.enrollment_calibration_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, tzinfo=UTC)
            year = await service.get_current_school_year()
            assert year == "2024/2025"

    @pytest.mark.asyncio
    async def test_calibration_insufficient_data(self, service, mock_session):
        """Test calibration fails gracefully with insufficient data."""
        org_id = uuid.uuid4()
        version_id = uuid.uuid4()

        # Create mock budget version for the lookup
        mock_budget_version = MagicMock(spec=BudgetVersion)
        mock_budget_version.fiscal_year = 2025  # Targets 2025/2026
        mock_budget_version.id = version_id

        # Configure mock session to return budget version first, then empty historical data
        def mock_execute_side_effect(stmt):
            mock_result = MagicMock()
            # First call is for budget version lookup
            if "budget_versions" in str(stmt).lower() or hasattr(stmt, "_raw_columns"):
                mock_result.scalar_one_or_none.return_value = mock_budget_version
            else:
                # Historical data query returns empty
                mock_result.all.return_value = []
            return mock_result

        mock_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        result = await service.calibrate_parameters(org_id, version_id)

        assert result.success is False
        assert "Insufficient" in result.message
        assert result.fallback_used is True


# ==============================================================================
# Integration Tests - With DB Fixtures
# ==============================================================================


# NOTE: organization_id fixture is provided by conftest.py and creates an actual
# Organization record in the database to satisfy FK constraints.


@pytest.fixture
async def academic_levels_list(
    db_session: AsyncSession, academic_cycles: dict
) -> list[AcademicLevel]:
    """Create academic levels for all grades, linked to academic cycles.

    Uses the academic_cycles fixture from conftest.py to satisfy FK constraints.
    """
    from app.engine.enrollment.projection.projection_engine import GRADE_SEQUENCE

    # Map grades to cycles
    grade_to_cycle = {
        "PS": "maternelle",
        "MS": "maternelle",
        "GS": "maternelle",
        "CP": "elementaire",
        "CE1": "elementaire",
        "CE2": "elementaire",
        "CM1": "elementaire",
        "CM2": "elementaire",
        "6EME": "college",
        "5EME": "college",
        "4EME": "college",
        "3EME": "college",
        "2NDE": "lycee",
        "1ERE": "lycee",
        "TLE": "lycee",
    }

    # Grades that are secondary level

    levels = []
    for idx, grade in enumerate(GRADE_SEQUENCE):
        cycle_key = grade_to_cycle.get(grade, "elementaire")
        cycle = academic_cycles[cycle_key]

        level = AcademicLevel(
            id=uuid.uuid4(),
            code=grade,
            name_en=f"Grade {grade}",
            name_fr=f"Niveau {grade}",
            cycle_id=cycle.id,
            sort_order=idx,
        )
        db_session.add(level)
        levels.append(level)

    await db_session.flush()
    return levels


@pytest.fixture
async def enrollment_scenarios(db_session: AsyncSession) -> list[EnrollmentScenario]:
    """Create enrollment scenarios with all required fields."""
    scenarios = [
        EnrollmentScenario(
            id=uuid.uuid4(),
            code="worst_case",
            name_en="Worst Case",
            name_fr="Pire Cas",
            ps_entry=60,
            entry_growth_rate=Decimal("-0.05"),
            default_retention=Decimal("0.92"),
            terminal_retention=Decimal("0.94"),
            lateral_multiplier=Decimal("0.30"),
            sort_order=1,
        ),
        EnrollmentScenario(
            id=uuid.uuid4(),
            code="conservative",
            name_en="Conservative",
            name_fr="Conservateur",
            ps_entry=70,
            entry_growth_rate=Decimal("0.00"),
            default_retention=Decimal("0.95"),
            terminal_retention=Decimal("0.96"),
            lateral_multiplier=Decimal("0.60"),
            sort_order=2,
        ),
        EnrollmentScenario(
            id=uuid.uuid4(),
            code="base",
            name_en="Base Case",
            name_fr="Cas de Base",
            ps_entry=80,
            entry_growth_rate=Decimal("0.02"),
            default_retention=Decimal("0.96"),
            terminal_retention=Decimal("0.97"),
            lateral_multiplier=Decimal("1.00"),
            sort_order=3,
        ),
        EnrollmentScenario(
            id=uuid.uuid4(),
            code="optimistic",
            name_en="Optimistic",
            name_fr="Optimiste",
            ps_entry=90,
            entry_growth_rate=Decimal("0.05"),
            default_retention=Decimal("0.97"),
            terminal_retention=Decimal("0.98"),
            lateral_multiplier=Decimal("1.30"),
            sort_order=4,
        ),
        EnrollmentScenario(
            id=uuid.uuid4(),
            code="best_case",
            name_en="Best Case",
            name_fr="Meilleur Cas",
            ps_entry=100,
            entry_growth_rate=Decimal("0.08"),
            default_retention=Decimal("0.98"),
            terminal_retention=Decimal("0.99"),
            lateral_multiplier=Decimal("1.50"),
            sort_order=5,
        ),
    ]

    for scenario in scenarios:
        db_session.add(scenario)

    await db_session.flush()
    return scenarios


@pytest.fixture
async def calibration_budget_version(
    db_session: AsyncSession,
    organization_id: uuid.UUID,
) -> BudgetVersion:
    """Create a budget version for calibration tests.

    Uses fiscal_year=2025, which means:
    - target_school_year = "2025/2026"
    - Historical window uses 2021-2024 data (N-4 to N-1)

    Note: This fixture does NOT depend on test_user_id to avoid
    creating unnecessary user records for calibration tests.
    """
    version = BudgetVersion(
        id=uuid.uuid4(),
        name="Budget 2025 Test",
        fiscal_year=2025,
        academic_year="2025-2026",  # STARTING year convention
        status=BudgetVersionStatus.WORKING,
        is_baseline=False,
        notes="Test budget for calibration",
        organization_id=organization_id,
        created_by_id=None,  # No user required for this test
        created_at=datetime.now(UTC),
    )
    db_session.add(version)
    await db_session.flush()
    return version


@pytest.fixture
async def historical_enrollment_data(
    db_session: AsyncSession,
    organization_id: uuid.UUID,
    academic_levels_list: list[AcademicLevel],
) -> dict[str, dict[str, int]]:
    """Create 4 years of historical enrollment data using HistoricalActuals.

    Note: HistoricalActuals stores data by fiscal_year (int), module_code, dimension_type,
    and dimension_code. For enrollment data:
    - module_code = ENROLLMENT
    - dimension_type = LEVEL
    - dimension_code = grade code (e.g., '6EME')
    - annual_count = student count
    """
    # Simulated enrollment data with realistic progression
    historical_data = {
        "2021/2022": {
            "PS": 75, "MS": 80, "GS": 85, "CP": 90,
            "CE1": 88, "CE2": 87, "CM1": 85, "CM2": 83,
            "6EME": 95, "5EME": 92, "4EME": 90, "3EME": 88,
            "2NDE": 75, "1ERE": 72, "TLE": 70,
        },
        "2022/2023": {
            "PS": 78, "MS": 82, "GS": 88, "CP": 94,
            "CE1": 93, "CE2": 91, "CM1": 90, "CM2": 88,
            "6EME": 100, "5EME": 97, "4EME": 94, "3EME": 92,
            "2NDE": 80, "1ERE": 76, "TLE": 73,
        },
        "2023/2024": {
            "PS": 80, "MS": 85, "GS": 90, "CP": 97,
            "CE1": 97, "CE2": 96, "CM1": 94, "CM2": 93,
            "6EME": 105, "5EME": 102, "4EME": 99, "3EME": 96,
            "2NDE": 85, "1ERE": 81, "TLE": 77,
        },
        "2024/2025": {
            "PS": 82, "MS": 88, "GS": 93, "CP": 100,
            "CE1": 100, "CE2": 100, "CM1": 99, "CM2": 97,
            "6EME": 110, "5EME": 107, "4EME": 104, "3EME": 101,
            "2NDE": 90, "1ERE": 86, "TLE": 82,
        },
    }

    for school_year, grades in historical_data.items():
        fiscal_year = school_year_to_fiscal_year(school_year)
        for grade_code, total in grades.items():
            historical_actual = HistoricalActuals(
                id=uuid.uuid4(),
                fiscal_year=fiscal_year,
                module_code=HistoricalModuleCode.ENROLLMENT,
                dimension_type=HistoricalDimensionType.LEVEL,
                dimension_code=grade_code,
                annual_count=total,
            )
            db_session.add(historical_actual)

    await db_session.flush()
    return historical_data


class TestCalibrationServiceIntegration:
    """Integration tests for CalibrationService with real database."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> EnrollmentCalibrationService:
        """Create service with real session."""
        return EnrollmentCalibrationService(db_session)

    @pytest.mark.asyncio
    async def test_historical_data_summary_no_data(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        academic_levels_list: list[AcademicLevel],
    ):
        """Test summary with no historical data."""
        summary = await service.get_historical_data_summary(organization_id)

        assert summary.total_years == 0
        assert summary.has_sufficient_data is False
        assert summary.available_years == []

    @pytest.mark.asyncio
    async def test_historical_data_summary_with_data(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        historical_enrollment_data: dict,
    ):
        """Test summary with historical data."""
        summary = await service.get_historical_data_summary(organization_id)

        assert summary.total_years == 4
        assert summary.has_sufficient_data is True
        assert len(summary.available_years) == 4
        assert summary.earliest_year == "2021/2022"
        assert summary.latest_year == "2024/2025"

    @pytest.mark.asyncio
    async def test_calibration_with_sufficient_data(
        self,
        service: EnrollmentCalibrationService,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,
        historical_enrollment_data: dict,
    ):
        """Test calibration successfully calculates rates.

        Uses budget version with fiscal_year=2025 targeting 2025/2026.
        Historical window: 2021-2024 data.
        """
        result = await service.calibrate_parameters(
            organization_id, calibration_budget_version.id
        )

        assert result.success is True
        assert result.parameters_updated > 0
        assert len(result.source_years) > 0
        assert result.fallback_used is False
        assert result.target_school_year == "2025/2026"

        # Verify calibration data was saved (uses unified StudentsCalibration model)
        stmt = select(StudentsCalibration).where(
            StudentsCalibration.organization_id == organization_id
        )
        db_result = await db_session.execute(stmt)
        params = db_result.scalars().all()

        assert len(params) > 0

    @pytest.mark.asyncio
    async def test_calibration_status_after_calibration(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,
        historical_enrollment_data: dict,
    ):
        """Test calibration status reflects successful calibration."""
        await service.calibrate_parameters(
            organization_id, calibration_budget_version.id
        )
        status = await service.get_calibration_status(organization_id)

        assert status.last_calibrated is not None
        assert len(status.source_years) > 0
        assert status.total_years_available > 0
        assert status.has_sufficient_data is True

    @pytest.mark.asyncio
    async def test_update_parameter_override(
        self,
        service: EnrollmentCalibrationService,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
    ):
        """Test creating and updating parameter override."""
        user_id = uuid.uuid4()

        # Create override
        override_data = {
            "grade_code": "CP",
            "override_lateral_rate": True,
            "manual_lateral_rate": Decimal("0.20"),
            "override_reason": "Crisis adjustment",
        }

        await service.update_parameter_override(organization_id, override_data, user_id)

        # Verify override was saved
        overrides = await service.get_parameter_overrides(organization_id)
        assert "CP" in overrides
        assert overrides["CP"].manual_lateral_rate == Decimal("0.20")

        # Update override
        override_data["manual_lateral_rate"] = Decimal("0.25")
        await service.update_parameter_override(organization_id, override_data, user_id)

        # Verify update
        overrides = await service.get_parameter_overrides(organization_id)
        assert overrides["CP"].manual_lateral_rate == Decimal("0.25")

    @pytest.mark.asyncio
    async def test_update_scenario_multiplier(
        self,
        service: EnrollmentCalibrationService,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,  # Need working version
    ):
        """Test creating and updating scenario multiplier."""
        multiplier_data = {
            "scenario_code": "conservative",
            "lateral_multiplier": Decimal("0.70"),
        }

        await service.update_scenario_multiplier(organization_id, multiplier_data)

        # Verify multiplier was saved (returns tuple: (config, org_id))
        multipliers = await service.get_scenario_multipliers(organization_id)
        assert "conservative" in multipliers
        config, _ = multipliers["conservative"]
        assert config.lateral_multiplier == Decimal("0.70")

    @pytest.mark.asyncio
    async def test_effective_rates_with_override(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,
        historical_enrollment_data: dict,
    ):
        """Test effective rates use override when set."""
        # First calibrate
        await service.calibrate_parameters(
            organization_id, calibration_budget_version.id
        )

        # Set override for CP
        override_data = {
            "grade_code": "CP",
            "override_lateral_rate": True,
            "manual_lateral_rate": Decimal("0.25"),
        }
        await service.update_parameter_override(organization_id, override_data)

        # Get effective rates
        effective = await service.get_effective_rates(organization_id, "base")

        # CP should use override value
        assert effective.rates["CP"].lateral_entry_rate == Decimal("0.25")
        assert effective.rates["CP"].is_percentage_based is True

    @pytest.mark.asyncio
    async def test_effective_rates_without_override(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,
        historical_enrollment_data: dict,
    ):
        """Test effective rates use derived when no override."""
        # Calibrate
        await service.calibrate_parameters(
            organization_id, calibration_budget_version.id
        )

        # Get effective rates (no override set)
        effective = await service.get_effective_rates(organization_id, "base")

        # All entry points should have rates
        for grade in ENTRY_POINT_GRADES:
            if grade != "PS":  # PS is handled differently
                assert effective.rates[grade].is_percentage_based is True
                assert effective.rates[grade].lateral_entry_rate is not None

    @pytest.mark.asyncio
    async def test_scenario_multiplier_applied_to_rates(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,  # Need working version
    ):
        """Test scenario multiplier affects lateral entry rates."""
        # Set multiplier for conservative scenario
        multiplier_data = {
            "scenario_code": "conservative",
            "lateral_multiplier": Decimal("0.50"),
        }
        await service.update_scenario_multiplier(organization_id, multiplier_data)

        # Get effective rates for conservative
        effective = await service.get_effective_rates(organization_id, "conservative")

        # Multiplier should be applied
        assert effective.scenario_multiplier == Decimal("0.50")

    @pytest.mark.asyncio
    async def test_reset_all_overrides(
        self,
        service: EnrollmentCalibrationService,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
    ):
        """Test resetting all overrides.

        The unified StudentsCalibration model resets override flags but
        preserves records (with derived data).
        """
        # Create multiple overrides
        for grade in ["CP", "6EME", "2NDE"]:
            await service.update_parameter_override(
                organization_id,
                {"grade_code": grade, "override_lateral_rate": True, "manual_lateral_rate": Decimal("0.20")},
            )

        # Verify overrides exist with flags enabled
        overrides = await service.get_parameter_overrides(organization_id)
        assert len(overrides) == 3
        for _grade_code, calibration in overrides.items():
            assert calibration.override_lateral_rate is True

        # Reset all
        await service.reset_all_overrides(organization_id)

        # Verify override flags are reset (records still exist but flags are False)
        overrides = await service.get_parameter_overrides(organization_id)
        assert len(overrides) == 3  # Records preserved
        for _grade_code, calibration in overrides.items():
            assert calibration.override_lateral_rate is False
            assert calibration.manual_lateral_rate is None

    @pytest.mark.asyncio
    async def test_reset_scenario_multipliers(
        self,
        service: EnrollmentCalibrationService,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,  # Need working version
    ):
        """Test resetting scenario multipliers to defaults."""
        # Set non-default multiplier
        await service.update_scenario_multiplier(
            organization_id,
            {"scenario_code": "conservative", "lateral_multiplier": Decimal("0.90")},
        )

        # Reset
        await service.reset_scenario_multipliers(organization_id)

        # Verify defaults restored (returns tuple: (config, org_id))
        multipliers = await service.get_scenario_multipliers(organization_id)
        conservative_config, _ = multipliers["conservative"]
        base_config, _ = multipliers["base"]
        assert conservative_config.lateral_multiplier == Decimal("0.60")
        assert base_config.lateral_multiplier == Decimal("1.00")


class TestWeightedCalibrationAlgorithm:
    """Tests specifically for the 70% N-1 + 30% N-2 weighted calibration algorithm.

    These tests verify that the service correctly uses the weighted average
    formula as documented in the enrollment projection specification.
    """

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> EnrollmentCalibrationService:
        """Create service with real session."""
        return EnrollmentCalibrationService(db_session)

    @pytest.fixture
    async def three_year_historical_data(
        self,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
        academic_levels_list: list[AcademicLevel],
    ) -> dict[str, dict[str, int]]:
        """Create 3 years of historical data with predictable progression.

        This data is designed to verify the 70/30 weighted formula:
        - N-1 transition (2024→2025): MS gets 120 students from 100 PS = 120% progression
        - N-2 transition (2023→2024): MS gets 110 students from 100 PS = 110% progression
        - Expected weighted: 0.70 * 1.20 + 0.30 * 1.10 = 0.84 + 0.33 = 1.17 (117%)
        """
        historical_data = {
            "2022/2023": {
                "PS": 100, "MS": 95, "GS": 90, "CP": 85,
                "CE1": 80, "CE2": 75, "CM1": 70, "CM2": 65,
                "6EME": 60, "5EME": 58, "4EME": 56, "3EME": 54,
                "2NDE": 50, "1ERE": 48, "TLE": 46,
            },
            "2023/2024": {
                "PS": 100, "MS": 110, "GS": 100, "CP": 95,  # MS: 110/100 = 110%
                "CE1": 90, "CE2": 85, "CM1": 80, "CM2": 75,
                "6EME": 70, "5EME": 65, "4EME": 63, "3EME": 60,
                "2NDE": 58, "1ERE": 55, "TLE": 52,
            },
            "2024/2025": {
                "PS": 100, "MS": 120, "GS": 115, "CP": 105,  # MS: 120/100 = 120%
                "CE1": 100, "CE2": 95, "CM1": 90, "CM2": 85,
                "6EME": 80, "5EME": 75, "4EME": 70, "3EME": 68,
                "2NDE": 65, "1ERE": 62, "TLE": 58,
            },
        }

        for school_year, grades in historical_data.items():
            fiscal_year = school_year_to_fiscal_year(school_year)
            for grade_code, total in grades.items():
                historical_actual = HistoricalActuals(
                    id=uuid.uuid4(),
                    fiscal_year=fiscal_year,
                    module_code=HistoricalModuleCode.ENROLLMENT,
                    dimension_type=HistoricalDimensionType.LEVEL,
                    dimension_code=grade_code,
                    annual_count=total,
                )
                db_session.add(historical_actual)

        await db_session.flush()
        return historical_data

    @pytest.mark.asyncio
    async def test_calibration_uses_70_30_weighting(
        self,
        service: EnrollmentCalibrationService,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,
        three_year_historical_data: dict,
    ):
        """Test that calibration uses 70% N-1 + 30% N-2 weighted formula.

        For MS grade (with budget targeting 2025/2026):
        - N-1 progression (2024→2025): 120/100 = 1.20
        - N-2 progression (2023→2024): 110/100 = 1.10
        - Weighted: 0.70 * 1.20 + 0.30 * 1.10 = 0.84 + 0.33 = 1.17

        Lateral rate = weighted_progression - retention
                     = 1.17 - 0.96 (MAT cycle)
                     = 0.21 (21%)
        """
        result = await service.calibrate_parameters(
            organization_id, calibration_budget_version.id
        )

        assert result.success is True
        assert "70% N-1 + 30% N-2" in result.message
        assert result.target_school_year == "2025/2026"

        # Verify MS grade calculation (uses unified StudentsCalibration model)
        stmt = select(StudentsCalibration).where(
            StudentsCalibration.organization_id == organization_id,
            StudentsCalibration.grade_code == "MS",
        )
        db_result = await db_session.execute(stmt)
        ms_param = db_result.scalar_one()

        # Expected: 0.70 * 1.20 + 0.30 * 1.10 = 1.17
        expected_progression = Decimal("1.1700")
        assert ms_param.progression_rate == expected_progression

        # Retention for MAT cycle is 0.96
        assert ms_param.retention_rate == Decimal("0.96")

        # Lateral = progression - retention = 1.17 - 0.96 = 0.21
        expected_lateral = Decimal("0.210")
        assert ms_param.lateral_entry_rate == expected_lateral

    @pytest.mark.asyncio
    async def test_calibration_with_only_n1_data(
        self,
        service: EnrollmentCalibrationService,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,
        academic_levels_list: list[AcademicLevel],
    ):
        """Test calibration falls back to N-1 only when N-2 is unavailable.

        With only 2 years of data, we can only calculate N-1 transition.
        The weighted function should return N-1 alone (100% weight).
        """
        # Create only 2 years of data
        historical_data = {
            "2023/2024": {
                "PS": 100, "MS": 90, "GS": 85, "CP": 80,
                "CE1": 75, "CE2": 70, "CM1": 65, "CM2": 60,
                "6EME": 55, "5EME": 50, "4EME": 48, "3EME": 45,
                "2NDE": 42, "1ERE": 40, "TLE": 38,
            },
            "2024/2025": {
                "PS": 100, "MS": 130, "GS": 95, "CP": 90,  # MS: 130/100 = 130%
                "CE1": 85, "CE2": 80, "CM1": 75, "CM2": 70,
                "6EME": 65, "5EME": 60, "4EME": 55, "3EME": 52,
                "2NDE": 48, "1ERE": 45, "TLE": 42,
            },
        }

        for school_year, grades in historical_data.items():
            fiscal_year = school_year_to_fiscal_year(school_year)
            for grade_code, total in grades.items():
                historical_actual = HistoricalActuals(
                    id=uuid.uuid4(),
                    fiscal_year=fiscal_year,
                    module_code=HistoricalModuleCode.ENROLLMENT,
                    dimension_type=HistoricalDimensionType.LEVEL,
                    dimension_code=grade_code,
                    annual_count=total,
                )
                db_session.add(historical_actual)

        await db_session.flush()

        result = await service.calibrate_parameters(
            organization_id, calibration_budget_version.id
        )

        assert result.success is True
        assert result.target_school_year == "2025/2026"

        # Verify MS grade - should use N-1 alone (130%) (uses unified StudentsCalibration)
        stmt = select(StudentsCalibration).where(
            StudentsCalibration.organization_id == organization_id,
            StudentsCalibration.grade_code == "MS",
        )
        db_result = await db_session.execute(stmt)
        ms_param = db_result.scalar_one()

        # With only N-1, progression should be 1.30
        assert ms_param.progression_rate == Decimal("1.3000")

        # Lateral = 1.30 - 0.96 = 0.34
        assert ms_param.lateral_entry_rate == Decimal("0.340")

    @pytest.mark.asyncio
    async def test_calibration_message_confirms_algorithm(
        self,
        service: EnrollmentCalibrationService,
        db_session: AsyncSession,
        organization_id: uuid.UUID,
        calibration_budget_version: BudgetVersion,
        three_year_historical_data: dict,
    ):
        """Test that calibration success message confirms 70/30 algorithm."""
        result = await service.calibrate_parameters(
            organization_id, calibration_budget_version.id
        )

        assert result.success is True
        assert "70% N-1 + 30% N-2" in result.message
        assert result.target_school_year == "2025/2026"


class TestEnrollmentSettingsResponse:
    """Tests for get_enrollment_settings endpoint response."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> EnrollmentCalibrationService:
        """Create service with real session."""
        return EnrollmentCalibrationService(db_session)

    @pytest.mark.asyncio
    async def test_settings_structure(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        enrollment_scenarios: list[EnrollmentScenario],
    ):
        """Test settings response has correct structure."""
        settings = await service.get_enrollment_settings(organization_id)

        assert hasattr(settings, "calibration_status")
        assert hasattr(settings, "entry_point_rates")
        assert hasattr(settings, "incidental_lateral")
        assert hasattr(settings, "scenario_multipliers")

    @pytest.mark.asyncio
    async def test_entry_point_rates_count(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        enrollment_scenarios: list[EnrollmentScenario],
    ):
        """Test correct number of entry point rates."""
        settings = await service.get_enrollment_settings(organization_id)

        # Should have 5 entry points: MS, GS, CP, 6EME, 2NDE
        assert len(settings.entry_point_rates) == 5

        grade_codes = {r.grade_code for r in settings.entry_point_rates}
        assert grade_codes == ENTRY_POINT_GRADES

    @pytest.mark.asyncio
    async def test_incidental_lateral_count(
        self,
        service: EnrollmentCalibrationService,
        organization_id: uuid.UUID,
        enrollment_scenarios: list[EnrollmentScenario],
    ):
        """Test correct number of incidental lateral grades."""
        settings = await service.get_enrollment_settings(organization_id)

        # Should have 9 incidental grades: CE1-CM2 (4) + 5EME-3EME (3) + 1ERE + TLE
        assert len(settings.incidental_lateral) == 9

        grade_codes = {r.grade_code for r in settings.incidental_lateral}
        expected = {"CE1", "CE2", "CM1", "CM2", "5EME", "4EME", "3EME", "1ERE", "TLE"}
        assert grade_codes == expected
