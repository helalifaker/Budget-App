"""
Enrollment Calibration Service.

Calculates lateral entry rates and retention rates using weighted historical analysis.
Uses 70% N-1 + 30% N-2 weighting as specified in the enrollment projection model.

This is the core service for the dynamic lateral entry calculation engine.
"""

from __future__ import annotations

import statistics
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import (
    get_cached_calibration_data,
    invalidate_calibration_cache,
    set_cached_calibration_data,
)
from app.core.logging import logger
from app.engine.enrollment.calibration.calibration_engine import (
    HistoricalEnrollmentYear,
    calibrate_from_historical,
)
from app.engine.enrollment.projection.projection_engine import GRADE_SEQUENCE
from app.models import (
    EnrollmentScenario,
    HistoricalActuals,
    HistoricalDimensionType,
    HistoricalModuleCode,
    StudentsCalibration,
    StudentsConfig,
    Version,
    VersionStatus,
)
from app.schemas.enrollment.enrollment_settings import (
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
from app.services.exceptions import NotFoundError

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
    # Version Helpers
    # =========================================================================

    async def _get_version(self, version_id: UUID) -> Version:
        """
        Fetch a version by ID.

        Args:
            version_id: The UUID of the version

        Returns:
            Version model instance

        Raises:
            NotFoundError: If version doesn't exist
        """
        stmt = select(Version).where(Version.id == version_id)
        result = await self.session.execute(stmt)
        version = result.scalar_one_or_none()

        if not version:
            raise NotFoundError(
                message=f"Version {version_id} not found",
                entity_type="Version",
                entity_id=str(version_id),
            )
        return version

    def _get_target_school_year(self, version: Version) -> str:
        """
        Get the target school year from a version.

        The fiscal_year is the STARTING year of the academic year.
        Example: fiscal_year=2026 → target school year "2026/2027"

        Args:
            version: The BudgetVersion model

        Returns:
            School year string (e.g., "2026/2027")
        """
        return f"{version.fiscal_year}/{version.fiscal_year + 1}"

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

        OPTIMIZED: Results are cached for 24 hours since historical data is immutable.
        """
        import hashlib
        import json

        org_id_str = str(organization_id)

        # Create deterministic cache key from sorted school years
        years_sorted = sorted(school_years)
        years_hash = hashlib.md5("".join(years_sorted).encode()).hexdigest()[:8]
        cache_key_suffix = f"{org_id_str}:{years_hash}"

        # LAYER 2: Check Redis cache first
        cached_json = await get_cached_calibration_data(
            organization_id=cache_key_suffix,
            data_type="history",
        )
        if cached_json:
            logger.debug(
                "enrollment_history_cache_hit",
                organization_id=org_id_str,
                school_years=school_years,
            )
            return json.loads(cached_json)

        logger.debug(
            "enrollment_history_cache_miss",
            organization_id=org_id_str,
            school_years=school_years,
        )

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

        # LAYER 2: Cache result for 24 hours (86400 seconds)
        # Historical data is immutable, so long TTL is safe
        await set_cached_calibration_data(
            organization_id=cache_key_suffix,
            data_type="history",
            data=json.dumps(history),
            ttl_seconds=86400,  # 24 hours
        )
        logger.debug(
            "enrollment_history_cached",
            organization_id=org_id_str,
            school_years=school_years,
        )

        return history

    # =========================================================================
    # Calibration Algorithm
    # =========================================================================

    def _convert_to_engine_format(
        self,
        historical_data: dict[str, dict[str, int]],
    ) -> list[HistoricalEnrollmentYear]:
        """
        Convert database historical data to the format expected by calibration engine.

        Args:
            historical_data: {school_year: {grade_code: count}} from database

        Returns:
            List of HistoricalEnrollmentYear for the pure engine
        """
        engine_data: list[HistoricalEnrollmentYear] = []

        for school_year, grades in historical_data.items():
            if grades:  # Only include years with data
                fiscal_year = school_year_to_fiscal_year(school_year)
                engine_data.append(
                    HistoricalEnrollmentYear(
                        fiscal_year=fiscal_year,
                        grades=grades,
                    )
                )

        return engine_data

    def _calculate_confidence_from_engine_result(
        self,
        progression_n1: Decimal | None,
        progression_n2: Decimal | None,
    ) -> tuple[ConfidenceLevel, Decimal | None, int]:
        """
        Calculate confidence level and stats from engine calibration result.

        Returns:
            Tuple of (confidence_level, std_deviation, years_used)
        """
        if progression_n1 is not None and progression_n2 is not None:
            # Both N-1 and N-2 available - calculate std dev
            rates = [float(progression_n1), float(progression_n2)]
            std_dev = statistics.stdev(rates) if len(rates) > 1 else 0.0
            years_used = 2
            confidence = calculate_confidence(std_dev, years_used)
            return confidence, Decimal(str(round(std_dev, 4))), years_used
        elif progression_n1 is not None:
            # Only N-1 available
            return "medium", None, 1
        elif progression_n2 is not None:
            # Only N-2 available (unusual but possible)
            return "low", None, 1
        else:
            # No data
            return "low", None, 0

    async def calibrate_parameters(
        self,
        organization_id: UUID,
        version_id: UUID,
        force: bool = False,
    ) -> CalibrationResult:
        """
        Calculate progression rates using 70% N-1 + 30% N-2 weighted average.

        This uses the pure calibration engine which implements the correct
        weighted algorithm as specified in the enrollment projection model.

        IMPORTANT: The target year is derived from the budget version, NOT the system date.
        For Budget 2026 (fiscal_year=2026), the target is 2026-2027 academic year.
        Calibration uses N-1 (2025-2026) and N-2 (2024-2025) historical data.

        Args:
            organization_id: Organization UUID
            version_id: Budget version UUID - determines target academic year
            force: Force recalculation even if cached data exists

        Algorithm:
        1. Get target school year from budget version (fiscal_year → "YYYY/YYYY+1")
        2. Fetch historical enrollment for the 4 years BEFORE the target
        3. Convert to engine format (HistoricalEnrollmentYear)
        4. Call pure calibration engine with 70/30 weighting
        5. Persist results to database

        The weighted formula:
        - N-1 transition (most recent) gets 70% weight
        - N-2 transition (previous) gets 30% weight
        - If only N-1 available, uses N-1 alone (100%)
        - If no data, falls back to document defaults
        """
        # Get target year from budget version (NOT system date!)
        version = await self._get_version(version_id)
        target_school_year = self._get_target_school_year(version)

        # Get historical window: 4 years BEFORE the target year
        # For target 2026/2027, window is: 2022/2023, 2023/2024, 2024/2025, 2025/2026
        source_years = get_historical_window(target_school_year, window_size=4)

        # Fetch historical data from database
        historical_data = await self._fetch_enrollment_history(
            organization_id, source_years
        )

        # Filter to years with actual data
        years_with_data = [y for y in source_years if historical_data.get(y)]

        if len(years_with_data) < 2:
            return CalibrationResult(
                success=False,
                message=f"Insufficient historical data for {target_school_year}. Need at least 2 years, found {len(years_with_data)}.",
                source_years=years_with_data,
                target_school_year=target_school_year,
                fallback_used=True,
            )

        # Sort years chronologically (most recent last for engine)
        years_with_data.sort()

        # Convert to engine format
        engine_data = self._convert_to_engine_format(
            {y: historical_data[y] for y in years_with_data}
        )

        # Call pure calibration engine with 70/30 weighting
        calibration_result = calibrate_from_historical(
            historical_data=engine_data,
            weight_n1=Decimal("0.70"),
            weight_n2=Decimal("0.30"),
        )

        # Persist results to database
        now = datetime.now(UTC)
        params_updated = 0

        # OPTIMIZED: Fetch all existing records in one query to avoid N+1
        existing_records_stmt = select(StudentsCalibration).where(
            StudentsCalibration.organization_id == organization_id
        )
        existing_records_result = await self.session.execute(existing_records_stmt)
        existing_records_map = {
            r.grade_code: r for r in existing_records_result.scalars().all()
        }

        for grade, engine_grade_result in calibration_result.grades.items():
            # Calculate confidence from engine result
            confidence, std_dev, years_used = self._calculate_confidence_from_engine_result(
                engine_grade_result.progression_n1,
                engine_grade_result.progression_n2,
            )

            existing_param = existing_records_map.get(grade)

            if existing_param:
                # Update existing calibration record
                existing_param.progression_rate = engine_grade_result.weighted_progression
                existing_param.retention_rate = engine_grade_result.base_retention
                existing_param.lateral_entry_rate = engine_grade_result.derived_lateral_rate
                existing_param.confidence = confidence
                existing_param.std_deviation = std_dev
                existing_param.years_used = years_used
                existing_param.calculated_at = now
                existing_param.source_years = years_with_data
                existing_param.updated_at = now
            else:
                # Create new calibration record (unified model)
                new_param = StudentsCalibration(
                    organization_id=organization_id,
                    grade_code=grade,
                    progression_rate=engine_grade_result.weighted_progression,
                    retention_rate=engine_grade_result.base_retention,
                    lateral_entry_rate=engine_grade_result.derived_lateral_rate,
                    confidence=confidence,
                    std_deviation=std_dev,
                    years_used=years_used,
                    calculated_at=now,
                    source_years=years_with_data,
                )
                self.session.add(new_param)

            params_updated += 1

        await self.session.flush()

        # LAYER 2: Invalidate effective rates cache (O(1) direct deletion)
        # After calibration, derived parameters have changed → effective rates are stale
        await invalidate_calibration_cache(str(organization_id))
        logger.info(
            "calibration_cache_invalidated",
            organization_id=str(organization_id),
            params_updated=params_updated,
        )

        return CalibrationResult(
            success=True,
            message=f"Calibration complete for {target_school_year} using 70% N-1 + 30% N-2 weighting. Updated {params_updated} parameters from {len(years_with_data)} years of data.",
            parameters_updated=params_updated,
            source_years=years_with_data,
            target_school_year=target_school_year,
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
        # Get latest calibration record (uses unified StudentsCalibration model)
        stmt = (
            select(StudentsCalibration)
            .where(StudentsCalibration.organization_id == organization_id)
            .order_by(StudentsCalibration.calculated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        latest = result.scalar_one_or_none()

        # Get all calibration records for confidence calculation
        all_params_stmt = select(StudentsCalibration).where(
            StudentsCalibration.organization_id == organization_id
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
    ) -> dict[str, StudentsCalibration]:
        """Get all calibration data (derived parameters + overrides) for an organization.

        Uses the unified StudentsCalibration model which replaces:
        - students_derived_parameters
        - students_parameter_overrides
        """
        stmt = select(StudentsCalibration).where(
            StudentsCalibration.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        params = result.scalars().all()
        return {p.grade_code: p for p in params}

    async def get_parameter_overrides(
        self, organization_id: UUID
    ) -> dict[str, StudentsCalibration]:
        """Get parameter overrides for an organization.

        NOTE: Now returns the same data as get_derived_parameters() since
        the StudentsCalibration model unifies both derived and override data.
        The override columns are: override_lateral_rate, manual_lateral_rate,
        override_retention_rate, manual_retention_rate, override_fixed_lateral,
        manual_fixed_lateral.
        """
        # Same query as get_derived_parameters - unified model has all columns
        return await self.get_derived_parameters(organization_id)

    async def get_scenario_multipliers(
        self, organization_id: UUID
    ) -> dict[str, tuple[StudentsConfig, UUID]]:
        """Get scenario multipliers for an organization.

        Uses the unified StudentsConfig model which replaces:
        - students_scenario_multipliers (now part of students_configs)

        Returns dict mapping scenario_code to (config, organization_id) tuples
        since StudentsConfig links to organization via Version.
        """
        # Join through Version to filter by organization_id
        stmt = (
            select(StudentsConfig, Version.organization_id)
            .join(Version, StudentsConfig.version_id == Version.id)
            .where(Version.organization_id == organization_id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        # Return dict of scenario_code -> (config, organization_id)
        return {row[0].scenario_code: (row[0], row[1]) for row in rows}

    async def get_enrollment_settings(
        self, organization_id: UUID, scenario_code: str = "base"
    ) -> EnrollmentSettingsResponse:
        """
        Get complete enrollment settings for the Settings tab.

        OPTIMIZED: Uses Redis cache + parallel DB queries + reference cache.
        Performance layers:
        1. Check Redis cache first (instant if hit)
        2. If miss, execute 4 queries in parallel (saves ~1.5s)
        3. Use reference cache for scenarios (zero latency)
        4. Cache result for 4 hours
        """
        import asyncio

        from app.core.reference_cache import reference_cache

        org_id_str = str(organization_id)

        # LAYER 2: Check Redis cache first
        cached_json = await get_cached_calibration_data(
            organization_id=org_id_str,
            data_type="settings",
            scenario_code=scenario_code,
        )
        if cached_json:
            logger.debug(
                "enrollment_settings_cache_hit",
                organization_id=org_id_str,
                scenario_code=scenario_code,
            )
            return EnrollmentSettingsResponse.model_validate_json(cached_json)

        logger.debug(
            "enrollment_settings_cache_miss",
            organization_id=org_id_str,
            scenario_code=scenario_code,
        )

        # PERFORMANCE: Execute queries sequentially to avoid IllegalStateChangeError
        # (AsyncSession cannot be used concurrently)
        calibration_status = await self.get_calibration_status(organization_id)
        derived_params = await self.get_derived_parameters(organization_id)
        overrides = derived_params  # Reuse same data, methods are identical
        multipliers = await self.get_scenario_multipliers(organization_id)

        # LAYER 1: Use reference cache for scenarios (zero latency)
        scenarios: dict[str, Any] = {}
        if reference_cache.is_loaded:
            for s in reference_cache.get_scenarios():
                scenarios[s.code] = s
        else:
            # Fallback to DB query if cache not loaded
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
            mult_data = multipliers.get(code)
            scenario = scenarios.get(code)

            if mult_data:
                # Unpack tuple: (StudentsConfig, organization_id)
                config, org_id = mult_data
                scenario_multipliers.append(
                    ScenarioMultiplierResponse(
                        id=config.id,
                        organization_id=org_id,
                        scenario_code=config.scenario_code,
                        lateral_multiplier=config.lateral_multiplier,
                        updated_at=config.updated_at,
                        scenario_name=scenario.name_en if scenario else code,
                        is_default=config.lateral_multiplier == default_multipliers.get(code),
                    )
                )

        result = EnrollmentSettingsResponse(
            calibration_status=calibration_status,
            entry_point_rates=entry_point_rates,
            incidental_lateral=incidental_lateral,
            scenario_multipliers=scenario_multipliers,
        )

        # LAYER 2: Cache result for 4 hours
        await set_cached_calibration_data(
            organization_id=org_id_str,
            data_type="settings",
            data=result.model_dump_json(),
            ttl_seconds=14400,  # 4 hours
            scenario_code=scenario_code,
        )
        logger.debug(
            "enrollment_settings_cached",
            organization_id=org_id_str,
            scenario_code=scenario_code,
        )

        return result

    # =========================================================================
    # Effective Rate Resolution
    # =========================================================================

    async def get_effective_rates_fast(
        self,
        organization_id: UUID,
        scenario_code: str = "base",
    ) -> AllEffectiveRates:
        """
        OPTIMIZED: Resolve effective rates using Redis cache + parallel DB queries.

        Performance layers:
        1. Check Redis cache first (instant if hit)
        2. If miss, execute 3 queries in parallel (saves ~600-900ms)
        3. Cache result for 4 hours

        This method reduces 6+ sequential queries to 1 query by fetching
        all calibration data in parallel. Each query to Supabase has ~150-300ms
        latency, so batching saves 1-2 seconds.

        Priority chain: Override → Derived → Document Default
        """
        import asyncio

        org_id_str = str(organization_id)

        # LAYER 2: Check Redis cache first (O(1) lookup)
        cached_json = await get_cached_calibration_data(
            organization_id=org_id_str,
            data_type="effective",
            scenario_code=scenario_code,
        )
        if cached_json:
            logger.debug(
                "effective_rates_cache_hit",
                organization_id=org_id_str,
                scenario_code=scenario_code,
            )
            return AllEffectiveRates.model_validate_json(cached_json)

        logger.debug(
            "effective_rates_cache_miss",
            organization_id=org_id_str,
            scenario_code=scenario_code,
        )

        # PERFORMANCE: Execute queries in ONE round-trip using asyncio.gather
        # Each individual query takes ~150-300ms due to Supabase latency
        # Note: Using unified models (StudentsCalibration combines derived + overrides)

        # StudentsCalibration now holds both derived parameters and overrides
        calibration_task = self.session.execute(
            select(StudentsCalibration).where(
                StudentsCalibration.organization_id == organization_id
            )
        )
        # StudentsConfig joined with Version for organization filtering
        multipliers_task = self.session.execute(
            select(StudentsConfig, Version.organization_id)
            .join(Version, StudentsConfig.version_id == Version.id)
            .where(Version.organization_id == organization_id)
        )

        # Execute queries concurrently (saves ~300-600ms)
        calibration_result, multipliers_result = await asyncio.gather(
            calibration_task, multipliers_task
        )

        # Calibration data serves as both derived params and overrides
        calibration_data = {p.grade_code: p for p in calibration_result.scalars().all()}
        derived_params = calibration_data
        overrides = calibration_data  # Same data, override columns are in unified model
        multipliers = {row[0].scenario_code: row[0] for row in multipliers_result.all()}

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

        # Get last calibration timestamp from derived params (if any)
        calibration_timestamp = None
        if derived_params:
            latest = max(
                (p.calculated_at for p in derived_params.values() if p.calculated_at),
                default=None,
            )
            calibration_timestamp = latest

        result = AllEffectiveRates(
            rates=rates,
            scenario_multiplier=scenario_multiplier,
            calibration_timestamp=calibration_timestamp,
        )

        # LAYER 2: Cache result for 4 hours (14400 seconds)
        await set_cached_calibration_data(
            organization_id=org_id_str,
            data_type="effective",
            data=result.model_dump_json(),
            ttl_seconds=14400,  # 4 hours
            scenario_code=scenario_code,
        )
        logger.debug(
            "effective_rates_cached",
            organization_id=org_id_str,
            scenario_code=scenario_code,
        )

        return result

    async def get_effective_rates(
        self,
        organization_id: UUID,
        scenario_code: str = "base",
    ) -> AllEffectiveRates:
        """
        Resolve effective rates for all grades using priority chain:
        Override → Derived → Document Default

        Returns rates ready for the projection engine.

        NOTE: This is the legacy sequential version. Use get_effective_rates_fast()
        for better performance (saves ~1-2 seconds on Supabase).
        """
        derived_params = await self.get_derived_parameters(organization_id)
        overrides = await self.get_parameter_overrides(organization_id)
        multipliers_data = await self.get_scenario_multipliers(organization_id)

        # Get scenario multiplier (multipliers_data returns tuples: (config, org_id))
        mult_data = multipliers_data.get(scenario_code)
        scenario_multiplier = mult_data[0].lateral_multiplier if mult_data else Decimal("1.0")

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
    ) -> StudentsCalibration:
        """
        Create or update a parameter override.

        Uses the unified StudentsCalibration model where override columns are
        part of the same record as derived parameters.

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

        # Query unified StudentsCalibration model
        stmt = select(StudentsCalibration).where(
            StudentsCalibration.organization_id == organization_id,
            StudentsCalibration.grade_code == grade_code,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if existing:
            # Update override columns on existing calibration record
            existing.override_lateral_rate = override_data.get("override_lateral_rate", False)
            existing.manual_lateral_rate = override_data.get("manual_lateral_rate")
            existing.override_retention_rate = override_data.get("override_retention_rate", False)
            existing.manual_retention_rate = override_data.get("manual_retention_rate")
            existing.override_fixed_lateral = override_data.get("override_fixed_lateral", False)
            existing.manual_fixed_lateral = override_data.get("manual_fixed_lateral")
            existing.override_reason = override_data.get("override_reason")
            existing.updated_by_id = updated_by
            existing.updated_at = now
            calibration_result = existing
        else:
            # Create new calibration record with override data
            # Note: Derived values will be null until calibration runs
            new_calibration = StudentsCalibration(
                organization_id=organization_id,
                grade_code=grade_code,
                override_lateral_rate=override_data.get("override_lateral_rate", False),
                manual_lateral_rate=override_data.get("manual_lateral_rate"),
                override_retention_rate=override_data.get("override_retention_rate", False),
                manual_retention_rate=override_data.get("manual_retention_rate"),
                override_fixed_lateral=override_data.get("override_fixed_lateral", False),
                manual_fixed_lateral=override_data.get("manual_fixed_lateral"),
                override_reason=override_data.get("override_reason"),
                updated_by_id=updated_by,
            )
            self.session.add(new_calibration)
            await self.session.flush()
            calibration_result = new_calibration

        # LAYER 2: Invalidate effective rates cache (O(1) direct deletion)
        await invalidate_calibration_cache(str(organization_id))
        logger.info(
            "parameter_override_cache_invalidated",
            organization_id=str(organization_id),
            grade_code=grade_code,
        )

        return calibration_result

    async def update_scenario_multiplier(
        self,
        organization_id: UUID,
        multiplier_data: dict,
    ) -> StudentsConfig:
        """
        Update a scenario multiplier.

        Uses the unified StudentsConfig model linked via version_id.

        Args:
            organization_id: Organization UUID
            multiplier_data: Dictionary containing:
                - scenario_code: Scenario code (e.g., "base", "conservative")
                - lateral_multiplier: Multiplier value (0.1 to 3.0)
        """
        from datetime import datetime

        scenario_code = multiplier_data.get("scenario_code")
        lateral_multiplier = multiplier_data.get("lateral_multiplier")

        if not scenario_code:
            raise ValueError("scenario_code is required")
        if lateral_multiplier is None:
            raise ValueError("lateral_multiplier is required")

        # Find working version for organization
        version_stmt = (
            select(Version)
            .where(
                Version.organization_id == organization_id,
                Version.status == VersionStatus.WORKING,
                Version.deleted_at.is_(None),
            )
            .order_by(Version.fiscal_year.desc())
            .limit(1)
        )
        version_result = await self.session.execute(version_stmt)
        working_version = version_result.scalar_one_or_none()

        if not working_version:
            raise NotFoundError(f"No working version found for organization {organization_id}")

        # Query existing config for this version and scenario
        stmt = (
            select(StudentsConfig)
            .where(
                StudentsConfig.version_id == working_version.id,
                StudentsConfig.scenario_code == scenario_code,
            )
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if existing:
            existing.lateral_multiplier = Decimal(str(lateral_multiplier))
            existing.updated_at = now
            config_result = existing
        else:
            # Create new config with default values
            new_config = StudentsConfig(
                version_id=working_version.id,
                scenario_code=scenario_code,
                lateral_multiplier=Decimal(str(lateral_multiplier)),
                base_year=working_version.fiscal_year,
                projection_years=5,  # Default
                school_max_capacity=1850,  # Default
                default_class_size=25,  # Default
            )
            self.session.add(new_config)
            await self.session.flush()
            config_result = new_config

        # LAYER 2: Invalidate effective rates cache (O(1) direct deletion)
        await invalidate_calibration_cache(str(organization_id))
        logger.info(
            "scenario_multiplier_cache_invalidated",
            organization_id=str(organization_id),
            scenario_code=scenario_code,
        )

        return config_result

    # =========================================================================
    # Reset Operations
    # =========================================================================

    async def reset_all_overrides(self, organization_id: UUID) -> None:
        """
        Reset all parameter overrides to use derived/default values.

        Using the unified StudentsCalibration model, this resets override columns
        to their default values (False/None) while preserving derived data.
        """
        from sqlalchemy import update

        # Reset override columns to defaults in StudentsCalibration
        stmt = (
            update(StudentsCalibration)
            .where(StudentsCalibration.organization_id == organization_id)
            .values(
                override_lateral_rate=False,
                manual_lateral_rate=None,
                override_retention_rate=False,
                manual_retention_rate=None,
                override_fixed_lateral=False,
                manual_fixed_lateral=None,
                override_reason=None,
                updated_at=datetime.now(UTC),
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

        # LAYER 2: Invalidate effective rates cache (O(1) direct deletion)
        await invalidate_calibration_cache(str(organization_id))
        logger.info(
            "reset_overrides_cache_invalidated",
            organization_id=str(organization_id),
        )

    async def reset_scenario_multipliers(self, organization_id: UUID) -> None:
        """
        Reset scenario multipliers to default values.

        Uses the unified StudentsConfig model linked via version_id.

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

        # Find working version for organization
        version_stmt = (
            select(Version)
            .where(
                Version.organization_id == organization_id,
                Version.status == VersionStatus.WORKING,
                Version.deleted_at.is_(None),
            )
            .order_by(Version.fiscal_year.desc())
            .limit(1)
        )
        version_result = await self.session.execute(version_stmt)
        working_version = version_result.scalar_one_or_none()

        if not working_version:
            raise NotFoundError(f"No working version found for organization {organization_id}")

        now = datetime.now(UTC)

        for scenario_code, default_value in default_multipliers.items():
            stmt = select(StudentsConfig).where(
                StudentsConfig.version_id == working_version.id,
                StudentsConfig.scenario_code == scenario_code,
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.lateral_multiplier = default_value
                existing.updated_at = now
            else:
                new_config = StudentsConfig(
                    version_id=working_version.id,
                    scenario_code=scenario_code,
                    lateral_multiplier=default_value,
                    base_year=working_version.fiscal_year,
                    projection_years=5,  # Default
                    school_max_capacity=1850,  # Default
                    default_class_size=25,  # Default
                )
                self.session.add(new_config)

        await self.session.flush()

        # LAYER 2: Invalidate effective rates cache (O(1) direct deletion)
        await invalidate_calibration_cache(str(organization_id))
        logger.info(
            "reset_multipliers_cache_invalidated",
            organization_id=str(organization_id),
        )
