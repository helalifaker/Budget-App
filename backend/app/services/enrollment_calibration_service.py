"""
Enrollment Calibration Service.

Calculates lateral entry rates and retention rates from a rolling 4-year historical window.
This is the core service for the dynamic lateral entry calculation engine.
"""

from __future__ import annotations

import statistics
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.enrollment.projection_engine import GRADE_SEQUENCE
from app.models import (
    EnrollmentDerivedParameter,
    EnrollmentParameterOverride,
    EnrollmentScenario,
    EnrollmentScenarioMultiplier,
    HistoricalActuals,
    HistoricalDimensionType,
    HistoricalModuleCode,
)
from app.schemas.enrollment_settings import (
    DOCUMENT_DEFAULTS,
    ENTRY_POINT_GRADES,
    MATERNELLE_FUNNEL_GRADES,
    AllEffectiveRates,
    CalibrationResult,
    CalibrationStatus,
    ConfidenceLevel,
    EffectiveRates,
    EnrollmentSettingsResponse,
    EntryPointRateResponse,
    HistoricalDataSummary,
    HistoricalYearSummary,
    IncidentalLateralResponse,
    ScenarioMultiplierResponse,
)

if TYPE_CHECKING:
    pass


def get_previous_grade(grade: str) -> str | None:
    """Get the previous grade in sequence."""
    try:
        idx = GRADE_SEQUENCE.index(grade)
        if idx > 0:
            return GRADE_SEQUENCE[idx - 1]
    except ValueError:
        pass
    return None


def get_historical_window(current_school_year: str, window_size: int = 4) -> list[str]:
    """
    Get the N most recent complete school years.

    Example: Current year 2025/2026, window=4 → ["2021/2022", "2022/2023", "2023/2024", "2024/2025"]
    Example: Current year 2030/2031, window=4 → ["2026/2027", "2027/2028", "2028/2029", "2029/2030"]
    """
    current_start = int(current_school_year.split("/")[0])
    return [f"{y}/{y+1}" for y in range(current_start - window_size, current_start)]


def fiscal_year_to_school_year(fiscal_year: int) -> str:
    """Convert fiscal year integer to school year string.

    Example: 2024 → "2024/2025"
    """
    return f"{fiscal_year}/{fiscal_year + 1}"


def school_year_to_fiscal_year(school_year: str) -> int:
    """Convert school year string to fiscal year integer.

    Example: "2024/2025" → 2024
    """
    return int(school_year.split("/")[0])


def get_historical_fiscal_years(current_school_year: str, window_size: int = 4) -> list[int]:
    """
    Get the N most recent complete fiscal years as integers.

    Example: Current year 2025/2026, window=4 → [2021, 2022, 2023, 2024]
    """
    current_fiscal = school_year_to_fiscal_year(current_school_year)
    return list(range(current_fiscal - window_size, current_fiscal))


def calculate_confidence(std_dev: float, years_used: int) -> ConfidenceLevel:
    """
    Determine confidence level based on standard deviation and data availability.

    High: std_dev < 5%, 3+ years
    Medium: std_dev < 10%, 2+ years
    Low: otherwise
    """
    if years_used >= 3 and std_dev < 0.05:
        return "high"
    elif years_used >= 2 and std_dev < 0.10:
        return "medium"
    return "low"


def calculate_data_quality_score(
    total_years: int,
    avg_confidence: float,
    has_all_grades: bool,
) -> int:
    """Calculate 1-5 star data quality score."""
    score = 1

    # Years available (up to 2 points)
    if total_years >= 4:
        score += 2
    elif total_years >= 2:
        score += 1

    # Average confidence (up to 1 point)
    if avg_confidence >= 0.7:  # Mostly high/medium
        score += 1

    # Grade coverage (up to 1 point)
    if has_all_grades:
        score += 1

    return min(score, 5)


class EnrollmentCalibrationService:
    """
    Service for calibrating enrollment parameters from historical data.

    Uses a rolling 4-year window to calculate:
    - Progression rates (enrollment[G,Y] / enrollment[G-1,Y-1])
    - Retention rates (min(progression_rate, 1.0))
    - Lateral entry rates (max(0, progression_rate - retention_rate))
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # Historical Data Analysis
    # =========================================================================

    async def get_current_school_year(self) -> str:
        """Get the current school year based on system date."""
        now = datetime.now(UTC)
        year = now.year
        # School year starts in September
        if now.month >= 9:
            return f"{year}/{year + 1}"
        return f"{year - 1}/{year}"

    async def get_historical_data_summary(
        self, organization_id: UUID
    ) -> HistoricalDataSummary:
        """Get summary of available historical enrollment data.

        Note: organization_id is accepted for API consistency but HistoricalActuals
        is currently not multi-tenant (RLS policies handle data isolation).
        """
        # Query distinct fiscal years with enrollment data from HistoricalActuals
        # HistoricalActuals stores enrollment by level with:
        # - module_code = 'enrollment'
        # - dimension_type = 'level'
        # - dimension_code = grade code (e.g., '6EME')
        # - annual_count = student count
        stmt = (
            select(
                HistoricalActuals.fiscal_year,
                func.count(HistoricalActuals.id).label("count"),
                func.sum(HistoricalActuals.annual_count).label("total"),
            )
            .where(
                HistoricalActuals.module_code == HistoricalModuleCode.ENROLLMENT,
                HistoricalActuals.dimension_type == HistoricalDimensionType.LEVEL,
            )
            .group_by(HistoricalActuals.fiscal_year)
            .order_by(HistoricalActuals.fiscal_year)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        years_summary = []
        for row in rows:
            school_year = fiscal_year_to_school_year(row.fiscal_year)
            years_summary.append(
                HistoricalYearSummary(
                    school_year=school_year,
                    total_students=int(row.total or 0),
                    grades_with_data=int(row.count or 0),
                    is_complete=int(row.count or 0) >= 14,  # At least 14 grades (excl PS)
                )
            )

        current_year = await self.get_current_school_year()
        recommended = get_historical_window(current_year, window_size=4)

        return HistoricalDataSummary(
            available_years=years_summary,
            recommended_window=recommended,
            total_years=len(years_summary),
            has_sufficient_data=len(years_summary) >= 2,
            earliest_year=years_summary[0].school_year if years_summary else None,
            latest_year=years_summary[-1].school_year if years_summary else None,
        )

    async def _fetch_enrollment_history(
        self,
        organization_id: UUID,
        school_years: list[str],
    ) -> dict[str, dict[str, int]]:
        """
        Fetch historical enrollment data for specified school years.

        Returns: {school_year: {grade_code: total_students}}

        Note: organization_id is accepted for API consistency but HistoricalActuals
        is currently not multi-tenant (RLS policies handle data isolation).
        """
        # Convert school years to fiscal years for query
        fiscal_years = [school_year_to_fiscal_year(y) for y in school_years]

        stmt = (
            select(
                HistoricalActuals.fiscal_year,
                HistoricalActuals.dimension_code.label("grade_code"),
                HistoricalActuals.annual_count.label("total"),
            )
            .where(
                HistoricalActuals.module_code == HistoricalModuleCode.ENROLLMENT,
                HistoricalActuals.dimension_type == HistoricalDimensionType.LEVEL,
                HistoricalActuals.fiscal_year.in_(fiscal_years),
            )
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        # Organize by school year (convert fiscal year back to school year string)
        history: dict[str, dict[str, int]] = {year: {} for year in school_years}
        for row in rows:
            school_year = fiscal_year_to_school_year(row.fiscal_year)
            if school_year in history:
                history[school_year][row.grade_code] = int(row.total or 0)

        return history

    # =========================================================================
    # Calibration Algorithm
    # =========================================================================

    async def calibrate_parameters(
        self,
        organization_id: UUID,
        force: bool = False,
    ) -> CalibrationResult:
        """
        Calculate progression rates and decompose into retention + lateral entry.
        Uses rolling 4-year window of historical data.

        Algorithm:
        1. Fetch historical enrollment for the last 4 complete school years
        2. For each grade (except PS), calculate progression rates year over year
        3. Use median (robust to outliers) if high volatility, else mean
        4. Decompose: retention = min(rate, 1.0), lateral = max(0, rate - retention)
        5. Persist to database
        """
        current_year = await self.get_current_school_year()
        source_years = get_historical_window(current_year, window_size=4)

        # Fetch historical data
        historical_data = await self._fetch_enrollment_history(
            organization_id, source_years
        )

        # Filter to years with actual data
        years_with_data = [y for y in source_years if historical_data.get(y)]

        if len(years_with_data) < 2:
            return CalibrationResult(
                success=False,
                message=f"Insufficient historical data. Need at least 2 years, found {len(years_with_data)}.",
                source_years=years_with_data,
                fallback_used=True,
            )

        # Sort years chronologically
        years_with_data.sort()

        # Calculate progression rates for each grade
        derived_params: dict[str, dict] = {}
        confidence_scores: list[float] = []

        for grade in GRADE_SEQUENCE[1:]:  # Skip PS
            prev_grade = get_previous_grade(grade)
            if not prev_grade:
                continue

            progression_rates: list[float] = []

            for i in range(1, len(years_with_data)):
                prev_year = years_with_data[i - 1]
                curr_year = years_with_data[i]

                prev_enrollment = historical_data[prev_year].get(prev_grade, 0)
                curr_enrollment = historical_data[curr_year].get(grade, 0)

                if prev_enrollment > 0:
                    rate = curr_enrollment / prev_enrollment
                    progression_rates.append(rate)

            if len(progression_rates) >= 2:
                # Calculate statistics
                avg_rate = statistics.mean(progression_rates)
                median_rate = statistics.median(progression_rates)
                std_dev = (
                    statistics.stdev(progression_rates)
                    if len(progression_rates) > 1
                    else 0.0
                )

                # Use median if high volatility (more robust to outliers)
                effective_rate = median_rate if std_dev > 0.10 else avg_rate

                # Decompose into retention + lateral
                # Retention cannot exceed 100%
                retention = min(effective_rate, 1.0)
                lateral = max(0.0, effective_rate - retention)

                confidence = calculate_confidence(std_dev, len(progression_rates))
                confidence_scores.append(
                    1.0 if confidence == "high" else 0.5 if confidence == "medium" else 0.0
                )

                derived_params[grade] = {
                    "progression_rate": Decimal(str(round(effective_rate, 4))),
                    "retention_rate": Decimal(str(round(retention, 4))),
                    "lateral_entry_rate": Decimal(str(round(lateral, 4))),
                    "confidence": confidence,
                    "std_deviation": Decimal(str(round(std_dev, 4))),
                    "years_used": len(progression_rates),
                }

            elif len(progression_rates) == 1:
                # Only one data point - low confidence
                rate = progression_rates[0]
                retention = min(rate, 1.0)
                lateral = max(0.0, rate - retention)

                derived_params[grade] = {
                    "progression_rate": Decimal(str(round(rate, 4))),
                    "retention_rate": Decimal(str(round(retention, 4))),
                    "lateral_entry_rate": Decimal(str(round(lateral, 4))),
                    "confidence": "low",
                    "std_deviation": None,
                    "years_used": 1,
                }
                confidence_scores.append(0.0)

            else:
                # No data - use document defaults
                defaults = DOCUMENT_DEFAULTS.get(grade, {})
                if "lateral_rate" in defaults:
                    derived_params[grade] = {
                        "progression_rate": defaults["retention_rate"] + defaults["lateral_rate"],
                        "retention_rate": defaults["retention_rate"],
                        "lateral_entry_rate": defaults["lateral_rate"],
                        "confidence": "low",
                        "std_deviation": None,
                        "years_used": 0,
                    }
                elif "fixed_lateral" in defaults:
                    # For incidental grades, we still derive retention
                    derived_params[grade] = {
                        "progression_rate": defaults["retention_rate"],
                        "retention_rate": defaults["retention_rate"],
                        "lateral_entry_rate": Decimal("0"),  # Fixed value handled separately
                        "confidence": "low",
                        "std_deviation": None,
                        "years_used": 0,
                    }

        # Persist to database
        now = datetime.now(UTC)
        params_updated = 0

        for grade, params in derived_params.items():
            # Check for existing record
            existing = await self.session.execute(
                select(EnrollmentDerivedParameter).where(
                    EnrollmentDerivedParameter.organization_id == organization_id,
                    EnrollmentDerivedParameter.grade_code == grade,
                )
            )
            existing_param = existing.scalar_one_or_none()

            if existing_param:
                # Update existing
                existing_param.progression_rate = params["progression_rate"]
                existing_param.retention_rate = params["retention_rate"]
                existing_param.lateral_entry_rate = params["lateral_entry_rate"]
                existing_param.confidence = params["confidence"]
                existing_param.std_deviation = params["std_deviation"]
                existing_param.years_used = params["years_used"]
                existing_param.calculated_at = now
                existing_param.source_years = years_with_data
                existing_param.updated_at = now
            else:
                # Create new
                new_param = EnrollmentDerivedParameter(
                    organization_id=organization_id,
                    grade_code=grade,
                    progression_rate=params["progression_rate"],
                    retention_rate=params["retention_rate"],
                    lateral_entry_rate=params["lateral_entry_rate"],
                    confidence=params["confidence"],
                    std_deviation=params["std_deviation"],
                    years_used=params["years_used"],
                    calculated_at=now,
                    source_years=years_with_data,
                )
                self.session.add(new_param)

            params_updated += 1

        await self.session.flush()

        return CalibrationResult(
            success=True,
            message=f"Calibration complete. Updated {params_updated} parameters from {len(years_with_data)} years of data.",
            parameters_updated=params_updated,
            source_years=years_with_data,
            calculated_at=now,
            fallback_used=False,
        )

    # =========================================================================
    # Settings Retrieval
    # =========================================================================

    async def get_calibration_status(
        self, organization_id: UUID
    ) -> CalibrationStatus:
        """Get the current calibration status."""
        # Get latest derived parameters
        stmt = (
            select(EnrollmentDerivedParameter)
            .where(EnrollmentDerivedParameter.organization_id == organization_id)
            .order_by(EnrollmentDerivedParameter.calculated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        latest = result.scalar_one_or_none()

        # Get all derived params for confidence calculation
        all_params_stmt = select(EnrollmentDerivedParameter).where(
            EnrollmentDerivedParameter.organization_id == organization_id
        )
        all_result = await self.session.execute(all_params_stmt)
        all_params = all_result.scalars().all()

        if not latest:
            return CalibrationStatus(
                last_calibrated=None,
                source_years=[],
                overall_confidence="low",
                data_quality_score=1,
                total_years_available=0,
                has_sufficient_data=False,
            )

        # Calculate overall confidence
        confidence_scores = []
        for p in all_params:
            if p.confidence == "high":
                confidence_scores.append(1.0)
            elif p.confidence == "medium":
                confidence_scores.append(0.5)
            else:
                confidence_scores.append(0.0)

        avg_confidence = (
            statistics.mean(confidence_scores) if confidence_scores else 0.0
        )
        overall_confidence: ConfidenceLevel = (
            "high" if avg_confidence >= 0.7
            else "medium" if avg_confidence >= 0.4
            else "low"
        )

        data_quality = calculate_data_quality_score(
            total_years=latest.years_used if latest else 0,
            avg_confidence=avg_confidence,
            has_all_grades=len(all_params) >= 14,
        )

        return CalibrationStatus(
            last_calibrated=latest.calculated_at,
            source_years=latest.source_years if latest else [],
            overall_confidence=overall_confidence,
            data_quality_score=data_quality,
            total_years_available=latest.years_used if latest else 0,
            has_sufficient_data=latest.years_used >= 2 if latest else False,
        )

    async def get_derived_parameters(
        self, organization_id: UUID
    ) -> dict[str, EnrollmentDerivedParameter]:
        """Get all derived parameters for an organization."""
        stmt = select(EnrollmentDerivedParameter).where(
            EnrollmentDerivedParameter.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        params = result.scalars().all()
        return {p.grade_code: p for p in params}

    async def get_parameter_overrides(
        self, organization_id: UUID
    ) -> dict[str, EnrollmentParameterOverride]:
        """Get all parameter overrides for an organization."""
        stmt = select(EnrollmentParameterOverride).where(
            EnrollmentParameterOverride.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        overrides = result.scalars().all()
        return {o.grade_code: o for o in overrides}

    async def get_scenario_multipliers(
        self, organization_id: UUID
    ) -> dict[str, EnrollmentScenarioMultiplier]:
        """Get scenario multipliers for an organization."""
        stmt = select(EnrollmentScenarioMultiplier).where(
            EnrollmentScenarioMultiplier.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        multipliers = result.scalars().all()
        return {m.scenario_code: m for m in multipliers}

    async def get_enrollment_settings(
        self, organization_id: UUID, scenario_code: str = "base"
    ) -> EnrollmentSettingsResponse:
        """Get complete enrollment settings for the Settings tab."""
        # Fetch all data
        calibration_status = await self.get_calibration_status(organization_id)
        derived_params = await self.get_derived_parameters(organization_id)
        overrides = await self.get_parameter_overrides(organization_id)
        multipliers = await self.get_scenario_multipliers(organization_id)

        # Fetch scenarios for names
        scenarios_stmt = select(EnrollmentScenario)
        scenarios_result = await self.session.execute(scenarios_stmt)
        scenarios = {s.code: s for s in scenarios_result.scalars().all()}

        # Build entry point rates
        entry_point_rates: list[EntryPointRateResponse] = []
        for grade in ENTRY_POINT_GRADES:
            derived = derived_params.get(grade)
            override = overrides.get(grade)
            defaults = DOCUMENT_DEFAULTS.get(grade, {})

            # Determine effective values
            effective_rate = Decimal(str(defaults.get("lateral_rate", 0)))
            effective_retention = Decimal(str(defaults.get("retention_rate", "0.96")))

            if derived:
                effective_rate = derived.lateral_entry_rate or effective_rate
                effective_retention = derived.retention_rate or effective_retention

            if override and override.override_lateral_rate and override.manual_lateral_rate:
                effective_rate = override.manual_lateral_rate
            if override and override.override_retention_rate and override.manual_retention_rate:
                effective_retention = override.manual_retention_rate

            category = (
                "maternelle_funnel"
                if grade in MATERNELLE_FUNNEL_GRADES
                else "cycle_transition"
            )

            entry_point_rates.append(
                EntryPointRateResponse(
                    grade_code=grade,
                    is_entry_point=True,
                    derived_rate=derived.lateral_entry_rate if derived else None,
                    derived_retention=derived.retention_rate if derived else None,
                    confidence=derived.confidence if derived else "low",
                    override_enabled=bool(
                        override
                        and (override.override_lateral_rate or override.override_retention_rate)
                    ),
                    manual_rate=override.manual_lateral_rate if override else None,
                    manual_retention=override.manual_retention_rate if override else None,
                    effective_rate=effective_rate,
                    effective_retention=effective_retention,
                    category=category,
                )
            )

        # Build incidental lateral
        incidental_lateral: list[IncidentalLateralResponse] = []
        for grade in GRADE_SEQUENCE[1:]:  # Skip PS
            if grade in ENTRY_POINT_GRADES:
                continue

            derived = derived_params.get(grade)
            override = overrides.get(grade)
            defaults = DOCUMENT_DEFAULTS.get(grade, {})

            effective_value = defaults.get("fixed_lateral", 0)
            effective_retention = Decimal(str(defaults.get("retention_rate", "0.96")))

            if derived:
                effective_retention = derived.retention_rate or effective_retention

            if override and override.override_fixed_lateral and override.manual_fixed_lateral:
                effective_value = override.manual_fixed_lateral
            if override and override.override_retention_rate and override.manual_retention_rate:
                effective_retention = override.manual_retention_rate

            incidental_lateral.append(
                IncidentalLateralResponse(
                    grade_code=grade,
                    is_entry_point=False,
                    derived_value=defaults.get("fixed_lateral"),  # Fixed values from document
                    derived_retention=derived.retention_rate if derived else None,
                    confidence=derived.confidence if derived else "low",
                    override_enabled=bool(
                        override
                        and (override.override_fixed_lateral or override.override_retention_rate)
                    ),
                    manual_value=override.manual_fixed_lateral if override else None,
                    manual_retention=override.manual_retention_rate if override else None,
                    effective_value=effective_value,
                    effective_retention=effective_retention,
                )
            )

        # Build scenario multipliers
        scenario_multipliers: list[ScenarioMultiplierResponse] = []
        default_multipliers = {
            "worst_case": Decimal("0.30"),
            "conservative": Decimal("0.60"),
            "base": Decimal("1.00"),
            "optimistic": Decimal("1.30"),
            "best_case": Decimal("1.50"),
        }

        for code in ["worst_case", "conservative", "base", "optimistic", "best_case"]:
            mult = multipliers.get(code)
            scenario = scenarios.get(code)

            if mult:
                scenario_multipliers.append(
                    ScenarioMultiplierResponse(
                        id=mult.id,
                        organization_id=mult.organization_id,
                        scenario_code=mult.scenario_code,
                        lateral_multiplier=mult.lateral_multiplier,
                        updated_at=mult.updated_at,
                        scenario_name=scenario.name_en if scenario else code,
                        is_default=mult.lateral_multiplier == default_multipliers.get(code),
                    )
                )

        return EnrollmentSettingsResponse(
            calibration_status=calibration_status,
            entry_point_rates=entry_point_rates,
            incidental_lateral=incidental_lateral,
            scenario_multipliers=scenario_multipliers,
        )

    # =========================================================================
    # Effective Rate Resolution
    # =========================================================================

    async def get_effective_rates(
        self,
        organization_id: UUID,
        scenario_code: str = "base",
    ) -> AllEffectiveRates:
        """
        Resolve effective rates for all grades using priority chain:
        Override → Derived → Document Default

        Returns rates ready for the projection engine.
        """
        derived_params = await self.get_derived_parameters(organization_id)
        overrides = await self.get_parameter_overrides(organization_id)
        multipliers = await self.get_scenario_multipliers(organization_id)

        # Get scenario multiplier
        mult = multipliers.get(scenario_code)
        scenario_multiplier = mult.lateral_multiplier if mult else Decimal("1.0")

        rates: dict[str, EffectiveRates] = {}

        for grade in GRADE_SEQUENCE[1:]:  # Skip PS
            derived = derived_params.get(grade)
            override = overrides.get(grade)
            defaults = DOCUMENT_DEFAULTS.get(grade, {})

            is_entry_point = grade in ENTRY_POINT_GRADES

            # Resolve retention rate
            retention = Decimal(str(defaults.get("retention_rate", "0.96")))
            if derived and derived.retention_rate:
                retention = derived.retention_rate
            if override and override.override_retention_rate and override.manual_retention_rate:
                retention = override.manual_retention_rate

            if is_entry_point:
                # Entry point: percentage-based
                lateral_rate = Decimal(str(defaults.get("lateral_rate", 0)))
                if derived and derived.lateral_entry_rate:
                    lateral_rate = derived.lateral_entry_rate
                if override and override.override_lateral_rate and override.manual_lateral_rate:
                    lateral_rate = override.manual_lateral_rate

                # Apply scenario multiplier
                lateral_rate = lateral_rate * scenario_multiplier

                rates[grade] = EffectiveRates(
                    grade_code=grade,
                    retention_rate=retention,
                    lateral_entry_rate=lateral_rate,
                    lateral_entry_fixed=None,
                    is_percentage_based=True,
                )
            else:
                # Incidental: fixed value
                fixed_value = defaults.get("fixed_lateral", 0)
                if override and override.override_fixed_lateral and override.manual_fixed_lateral:
                    fixed_value = override.manual_fixed_lateral

                # Apply scenario multiplier to fixed value
                fixed_value = int(fixed_value * float(scenario_multiplier))

                rates[grade] = EffectiveRates(
                    grade_code=grade,
                    retention_rate=retention,
                    lateral_entry_rate=None,
                    lateral_entry_fixed=fixed_value,
                    is_percentage_based=False,
                )

        # Get calibration timestamp
        calibration_status = await self.get_calibration_status(organization_id)

        return AllEffectiveRates(
            rates=rates,
            scenario_multiplier=scenario_multiplier,
            calibration_timestamp=calibration_status.last_calibrated,
        )

    # =========================================================================
    # Override Management
    # =========================================================================

    async def update_parameter_override(
        self,
        organization_id: UUID,
        override_data: dict,
        updated_by: UUID | None = None,
    ) -> EnrollmentParameterOverride:
        """
        Create or update a parameter override.

        Args:
            organization_id: Organization UUID
            override_data: Dictionary containing:
                - grade_code: Grade to override
                - override_lateral_rate: Whether to override lateral rate
                - manual_lateral_rate: Manual lateral rate value
                - override_retention_rate: Whether to override retention rate
                - manual_retention_rate: Manual retention rate value
                - override_fixed_lateral: Whether to override fixed lateral
                - manual_fixed_lateral: Manual fixed lateral value
                - override_reason: Reason for the override
            updated_by: User UUID making the change
        """
        grade_code = override_data.get("grade_code")
        if not grade_code:
            raise ValueError("grade_code is required")

        stmt = select(EnrollmentParameterOverride).where(
            EnrollmentParameterOverride.organization_id == organization_id,
            EnrollmentParameterOverride.grade_code == grade_code,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if existing:
            existing.override_lateral_rate = override_data.get("override_lateral_rate", False)
            existing.manual_lateral_rate = override_data.get("manual_lateral_rate")
            existing.override_retention_rate = override_data.get("override_retention_rate", False)
            existing.manual_retention_rate = override_data.get("manual_retention_rate")
            existing.override_fixed_lateral = override_data.get("override_fixed_lateral", False)
            existing.manual_fixed_lateral = override_data.get("manual_fixed_lateral")
            existing.override_reason = override_data.get("override_reason")
            existing.updated_by = updated_by
            existing.updated_at = now
            return existing
        else:
            new_override = EnrollmentParameterOverride(
                organization_id=organization_id,
                grade_code=grade_code,
                override_lateral_rate=override_data.get("override_lateral_rate", False),
                manual_lateral_rate=override_data.get("manual_lateral_rate"),
                override_retention_rate=override_data.get("override_retention_rate", False),
                manual_retention_rate=override_data.get("manual_retention_rate"),
                override_fixed_lateral=override_data.get("override_fixed_lateral", False),
                manual_fixed_lateral=override_data.get("manual_fixed_lateral"),
                override_reason=override_data.get("override_reason"),
                updated_by=updated_by,
            )
            self.session.add(new_override)
            await self.session.flush()
            return new_override

    async def update_scenario_multiplier(
        self,
        organization_id: UUID,
        multiplier_data: dict,
    ) -> EnrollmentScenarioMultiplier:
        """
        Update a scenario multiplier.

        Args:
            organization_id: Organization UUID
            multiplier_data: Dictionary containing:
                - scenario_code: Scenario code (e.g., "base", "conservative")
                - lateral_multiplier: Multiplier value (0.1 to 3.0)
        """
        scenario_code = multiplier_data.get("scenario_code")
        lateral_multiplier = multiplier_data.get("lateral_multiplier")

        if not scenario_code:
            raise ValueError("scenario_code is required")
        if lateral_multiplier is None:
            raise ValueError("lateral_multiplier is required")

        stmt = select(EnrollmentScenarioMultiplier).where(
            EnrollmentScenarioMultiplier.organization_id == organization_id,
            EnrollmentScenarioMultiplier.scenario_code == scenario_code,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if existing:
            existing.lateral_multiplier = Decimal(str(lateral_multiplier))
            existing.updated_at = now
            return existing
        else:
            new_mult = EnrollmentScenarioMultiplier(
                organization_id=organization_id,
                scenario_code=scenario_code,
                lateral_multiplier=Decimal(str(lateral_multiplier)),
            )
            self.session.add(new_mult)
            await self.session.flush()
            return new_mult

    # =========================================================================
    # Reset Operations
    # =========================================================================

    async def reset_all_overrides(self, organization_id: UUID) -> None:
        """
        Reset all parameter overrides to use derived/default values.

        This deletes all override records for the organization,
        causing the system to fall back to derived or document default values.
        """
        from sqlalchemy import delete

        stmt = delete(EnrollmentParameterOverride).where(
            EnrollmentParameterOverride.organization_id == organization_id
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def reset_scenario_multipliers(self, organization_id: UUID) -> None:
        """
        Reset scenario multipliers to default values.

        Default values:
        - worst_case: 0.30
        - conservative: 0.60
        - base: 1.00
        - optimistic: 1.30
        - best_case: 1.50
        """
        default_multipliers = {
            "worst_case": Decimal("0.30"),
            "conservative": Decimal("0.60"),
            "base": Decimal("1.00"),
            "optimistic": Decimal("1.30"),
            "best_case": Decimal("1.50"),
        }

        now = datetime.now(UTC)

        for scenario_code, default_value in default_multipliers.items():
            stmt = select(EnrollmentScenarioMultiplier).where(
                EnrollmentScenarioMultiplier.organization_id == organization_id,
                EnrollmentScenarioMultiplier.scenario_code == scenario_code,
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.lateral_multiplier = default_value
                existing.updated_at = now
            else:
                new_mult = EnrollmentScenarioMultiplier(
                    organization_id=organization_id,
                    scenario_code=scenario_code,
                    lateral_multiplier=default_value,
                )
                self.session.add(new_mult)

        await self.session.flush()
