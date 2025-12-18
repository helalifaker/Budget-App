"""
Enrollment Projection Service (Module 7 upgrade).

Orchestrates config/override persistence, calls the pure projection engine,
caches results, and handles validation cascade to downstream planning steps.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import and_, delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

# NOTE: CacheInvalidator import removed as part of Phase 4 performance fix.
# Cache invalidation was causing 6s delays; now disabled for all config updates.
# See update_config method comment for full rationale.
from app.core.cache import get_cached_calibration_data, set_cached_calibration_data
from app.core.logging import logger
from app.core.reference_cache import CachedScenario, reference_cache
from app.engine.enrollment import (
    ClassSizeConfig,
    EngineEffectiveRates,
    GradeOptimizationInput,
    GradeOptimizationResult,
    NewStudentsSummary,
    ProjectionInput,
    ScenarioParams,
    build_new_students_summary,
    calculate_proration_by_grade,
    is_entry_point_grade,
    optimize_grade_lateral_entry,
    optimize_ps_entry,
    project_multi_year,
    validate_projection_input,
)
from app.engine.enrollment import (
    GlobalOverrides as EngineGlobalOverrides,
)
from app.engine.enrollment import (
    GradeOverride as EngineGradeOverride,
)
from app.engine.enrollment import (
    LevelOverride as EngineLevelOverride,
)
from app.engine.enrollment.projection.projection_engine import GRADE_SEQUENCE, GRADE_TO_CYCLE
from app.engine.enrollment.projection.projection_models import UNIFIED_LATERAL_DEFAULTS
from app.models import (
    AcademicLevel,
    ClassSizeParam,
    EnrollmentGlobalOverride,
    EnrollmentGradeOverride,
    EnrollmentLevelOverride,
    EnrollmentPlan,
    EnrollmentProjection,
    EnrollmentProjectionConfig,
    EnrollmentScenario,
    HistoricalActuals,
    HistoricalDimensionType,
    HistoricalModuleCode,
    NationalityDistribution,
    NationalityType,
    Version,
)
from app.services.admin.cascade_service import CascadeService
from app.services.enrollment.enrollment_calibration_service import EnrollmentCalibrationService
from app.services.enrollment.enrollment_capacity import DEFAULT_SCHOOL_CAPACITY
from app.services.exceptions import NotFoundError, ValidationError

# Backward compatibility alias
BudgetVersion = Version


class EnrollmentProjectionService:
    """Service layer for enrollment projections."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------------------------------------------------------------------
    # Scenarios & Config
    # ---------------------------------------------------------------------

    async def get_all_scenarios(self) -> list[CachedScenario]:
        """Get all enrollment scenarios from in-memory cache (zero latency)."""
        if reference_cache.is_loaded:
            return reference_cache.get_scenarios()
        # Fallback to DB query if cache not loaded
        query = select(EnrollmentScenario).order_by(EnrollmentScenario.sort_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())  # type: ignore[return-value]

    async def get_or_create_config(
        self, version_id: uuid.UUID
    ) -> EnrollmentProjectionConfig:
        query = (
            select(EnrollmentProjectionConfig)
            .where(
                and_(
                    EnrollmentProjectionConfig.version_id == version_id,
                    EnrollmentProjectionConfig.deleted_at.is_(None),
                )
            )
            # PERFORMANCE FIX (Phase 11): Aggressive joinedload for ALL relations
            # to reduce database roundtrips from 5 to 1 query.
            # - joinedload for collections is safe here because:
            #   1. Data volume is tiny (4 level_overrides, 0 grade_overrides)
            #   2. Cartesian product risk is negligible
            #   3. Network latency (~400ms/roundtrip) dominates query execution (~0.1ms)
            # This reduces Supabase cloud latency from ~2s (5 roundtrips) to ~400ms (1 roundtrip).
            # NOTE: .unique() REQUIRED after execute() when using joinedload with collections!
            .options(
                joinedload(EnrollmentProjectionConfig.scenario),  # FK → 1 row
                joinedload(EnrollmentProjectionConfig.global_overrides),  # uselist=False → 1 row
                joinedload(EnrollmentProjectionConfig.level_overrides).joinedload(
                    EnrollmentLevelOverride.cycle  # FK → 1 row per override
                ),
                joinedload(EnrollmentProjectionConfig.grade_overrides).joinedload(
                    EnrollmentGradeOverride.level  # FK → 1 row per override
                ),
            )
        )
        # PHASE 11: .unique() is REQUIRED when using joinedload with One-to-Many collections
        # Without it, SQLAlchemy 2.0 may return duplicate parent rows due to LEFT JOINs
        existing = (await self.session.execute(query)).unique().scalar_one_or_none()
        if existing:
            return existing

        version = (
            await self.session.execute(
                select(BudgetVersion).where(BudgetVersion.id == version_id)
            )
        ).scalar_one_or_none()
        if not version:
            raise NotFoundError("BudgetVersion", str(version_id))

        # PERFORMANCE: Use in-memory cache for base scenario lookup (saves ~200ms)
        if reference_cache.is_loaded:
            cached_base = reference_cache.get_base_scenario()
            if not cached_base:
                raise NotFoundError("EnrollmentScenario", "base")
            base_scenario_id = cached_base.id
        else:
            # Fallback to DB query if cache not loaded
            base_scenario = (
                await self.session.execute(
                    select(EnrollmentScenario).where(EnrollmentScenario.code == "base")
                )
            ).scalar_one_or_none()
            if not base_scenario:
                raise NotFoundError("EnrollmentScenario", "base")
            base_scenario_id = base_scenario.id

        config = EnrollmentProjectionConfig(
            version_id=version_id,
            scenario_id=base_scenario_id,
            base_year=version.fiscal_year - 1,
            projection_years=5,
            school_max_capacity=DEFAULT_SCHOOL_CAPACITY,
            default_class_size=25,
            status="draft",
        )
        self.session.add(config)

        try:
            await self.session.commit()
            # SUCCESS: Re-fetch with eager-loaded relationships for consistent return type
            await self.session.refresh(config)
            refetch_query = (
                select(EnrollmentProjectionConfig)
                .where(EnrollmentProjectionConfig.id == config.id)
                .options(
                    joinedload(EnrollmentProjectionConfig.scenario),
                    joinedload(EnrollmentProjectionConfig.global_overrides),
                    joinedload(EnrollmentProjectionConfig.level_overrides).joinedload(
                        EnrollmentLevelOverride.cycle
                    ),
                    joinedload(EnrollmentProjectionConfig.grade_overrides).joinedload(
                        EnrollmentGradeOverride.level
                    ),
                )
            )
            return (await self.session.execute(refetch_query)).unique().scalar_one()
        except IntegrityError:
            # Race condition: another request created the config between our SELECT and INSERT
            # Rollback and retry the SELECT - the config now exists
            await self.session.rollback()
            logger.info(
                "get_or_create_config_race_condition",
                version_id=str(version_id),
                message="Concurrent insert detected, retrying SELECT",
            )
            # Only recurse after IntegrityError to fetch the existing config
            return await self.get_or_create_config(version_id)

    async def update_config(
        self,
        version_id: uuid.UUID,
        updates: dict,
        recalculate: bool = False,
    ) -> EnrollmentProjectionConfig:
        import time
        _t0 = time.perf_counter()

        # PERFORMANCE FIX: Single query at start - avoid double get_or_create_config
        # The first call already loads all relationships with selectinload
        config = await self.get_or_create_config(version_id)
        logger.debug("timing_get_or_create_config", duration_s=round(time.perf_counter() - _t0, 3))

        # Track if anything actually changed
        changed = False
        scenario_changed = False

        for key in [
            "scenario_id",
            "base_year",
            "projection_years",
            "school_max_capacity",
            "default_class_size",
        ]:
            if key in updates and updates[key] is not None:
                old_value = getattr(config, key)
                new_value = updates[key]
                if old_value != new_value:
                    setattr(config, key, new_value)
                    changed = True
                    if key == "scenario_id":
                        scenario_changed = True

        # Early return if nothing changed - saves commit + cache invalidation
        if not changed:
            logger.debug("timing_no_changes_early_return", duration_s=round(time.perf_counter() - _t0, 3))
            return config

        _t1 = time.perf_counter()
        await self.session.commit()
        logger.debug("timing_commit", duration_s=round(time.perf_counter() - _t1, 3))

        # PHASE 11: Use session.get() instead of session.refresh() to avoid extra roundtrip
        # session.get() checks identity map first - if scenario was already loaded in this
        # session (e.g., from get_all_scenarios), no network roundtrip is needed.
        # session.refresh() ALWAYS makes a roundtrip, even for cached objects.
        if scenario_changed and config.scenario_id:
            _t2 = time.perf_counter()
            config.scenario = await self.session.get(EnrollmentScenario, config.scenario_id)
            logger.debug("timing_session_get_scenario", duration_s=round(time.perf_counter() - _t2, 3))

        # FIX Issue #4: Deferred calculation - only calculate when explicitly requested
        if recalculate:
            await self.calculate_and_save(version_id, config=config)

        # PERFORMANCE FIX (Phase 4): Cache invalidation DISABLED for performance.
        # Cache keys include version_id, so scenario changes don't affect cached calculation data.
        # Cache will auto-expire via TTL, and heavy calculations recalculate on-demand when needed.
        # (Removed: CacheInvalidator.invalidate_background - caused 6s blocking despite fire-and-forget)

        logger.debug("timing_update_config_total", duration_s=round(time.perf_counter() - _t0, 3))
        # PERFORMANCE FIX: Return the already-loaded config directly
        # No need for second get_or_create_config - nested relationships haven't changed
        # (level_overrides.cycle and grade_overrides.level are reference data)
        return config

    # ---------------------------------------------------------------------
    # Overrides
    # ---------------------------------------------------------------------

    async def update_global_overrides(
        self,
        version_id: uuid.UUID,
        overrides: dict,
        recalculate: bool = False,
    ) -> EnrollmentProjectionConfig:
        # PERFORMANCE FIX: Single query - avoid double get_or_create_config
        config = await self.get_or_create_config(version_id)

        existing = config.global_overrides
        if existing:
            for k, v in overrides.items():
                setattr(existing, k, v)
        else:
            new_override = EnrollmentGlobalOverride(
                projection_config_id=config.id,
                **overrides,
            )
            self.session.add(new_override)
            # Attach to config so it's available in response
            config.global_overrides = new_override

        await self.session.commit()

        # FIX Issue #4: Deferred calculation - only calculate when explicitly requested
        if recalculate:
            await self.calculate_and_save(version_id, config=config)

        # PERFORMANCE FIX (Phase 4): Cache invalidation DISABLED (see update_config comment)

        # PERFORMANCE FIX: Return already-loaded config - no second query needed
        # global_overrides is already updated in memory
        return config

    async def update_level_overrides(
        self,
        version_id: uuid.UUID,
        override_items: list[dict],
        recalculate: bool = False,
    ) -> EnrollmentProjectionConfig:
        # PERFORMANCE FIX: Single query - avoid double get_or_create_config
        config = await self.get_or_create_config(version_id)

        existing_q = select(EnrollmentLevelOverride).where(
            and_(
                EnrollmentLevelOverride.projection_config_id == config.id,
                EnrollmentLevelOverride.deleted_at.is_(None),
            )
        )
        existing_rows = (await self.session.execute(existing_q)).scalars().all()
        existing_by_cycle = {row.cycle_id: row for row in existing_rows}

        for item in override_items:
            cycle_id = item["cycle_id"]
            row = existing_by_cycle.get(cycle_id)
            if row:
                row.class_size_ceiling = item.get("class_size_ceiling")
                row.max_divisions = item.get("max_divisions")
            else:
                self.session.add(
                    EnrollmentLevelOverride(
                        projection_config_id=config.id,
                        cycle_id=cycle_id,
                        class_size_ceiling=item.get("class_size_ceiling"),
                        max_divisions=item.get("max_divisions"),
                    )
                )

        await self.session.commit()

        # FIX Issue #4: Deferred calculation - only calculate when explicitly requested
        if recalculate:
            await self.calculate_and_save(version_id, config=config)

        # PERFORMANCE FIX (Phase 4): Cache invalidation DISABLED (see update_config comment)

        # PERFORMANCE FIX: Refresh level_overrides relationship to include new items
        # This is a single query instead of full get_or_create_config (7 queries)
        await self.session.refresh(config, ["level_overrides"])
        return config

    async def update_grade_overrides(
        self,
        version_id: uuid.UUID,
        override_items: list[dict],
        recalculate: bool = False,
    ) -> EnrollmentProjectionConfig:
        # PERFORMANCE FIX: Single query - avoid double get_or_create_config
        config = await self.get_or_create_config(version_id)

        existing_q = select(EnrollmentGradeOverride).where(
            and_(
                EnrollmentGradeOverride.projection_config_id == config.id,
                EnrollmentGradeOverride.deleted_at.is_(None),
            )
        )
        existing_rows = (await self.session.execute(existing_q)).scalars().all()
        existing_by_level = {row.level_id: row for row in existing_rows}

        for item in override_items:
            level_id = item["level_id"]
            row = existing_by_level.get(level_id)
            if row:
                row.retention_rate = item.get("retention_rate")
                row.lateral_entry = item.get("lateral_entry")
                row.max_divisions = item.get("max_divisions")
                row.class_size_ceiling = item.get("class_size_ceiling")
            else:
                self.session.add(
                    EnrollmentGradeOverride(
                        projection_config_id=config.id,
                        level_id=level_id,
                        retention_rate=item.get("retention_rate"),
                        lateral_entry=item.get("lateral_entry"),
                        max_divisions=item.get("max_divisions"),
                        class_size_ceiling=item.get("class_size_ceiling"),
                    )
                )

        await self.session.commit()

        # FIX Issue #4: Deferred calculation - only calculate when explicitly requested
        if recalculate:
            await self.calculate_and_save(version_id, config=config)

        # PERFORMANCE FIX (Phase 4): Cache invalidation DISABLED (see update_config comment)

        # PERFORMANCE FIX: Refresh grade_overrides relationship to include new items
        # This is a single query instead of full get_or_create_config (7 queries)
        await self.session.refresh(config, ["grade_overrides"])
        return config

    # ---------------------------------------------------------------------
    # Calculation & Cache
    # ---------------------------------------------------------------------

    async def calculate_and_save(
        self,
        version_id: uuid.UUID,
        config: EnrollmentProjectionConfig | None = None,
    ) -> list:
        """
        Calculate enrollment projections and save to database.

        Args:
            version_id: Budget version ID
            config: Pre-loaded config (optional, avoids redundant queries)

        Uses calibrated rates from the EnrollmentCalibrationService with percentage-based
        lateral entry for entry point grades (MS, GS, CP, 6EME, 2NDE) derived from the
        rolling 4-year historical window.

        The calibration service resolves rates using priority chain:
        Override → Derived (from history) → Document Default
        """
        import time

        timings: dict[str, float] = {}
        t_start = time.perf_counter()

        # PERFORMANCE FIX: Accept pre-loaded config to avoid redundant queries
        t0 = time.perf_counter()
        if config is None:
            config = await self.get_or_create_config(version_id)
        scenario = config.scenario
        timings["get_config"] = round(time.perf_counter() - t0, 3)

        # Serialize recalculations per config to avoid concurrent inserts
        # that can violate the unique constraint on cached projections.
        t0 = time.perf_counter()
        await self.session.execute(
            select(EnrollmentProjectionConfig.id)
            .where(EnrollmentProjectionConfig.id == config.id)
            .with_for_update()
        )
        timings["for_update_lock"] = round(time.perf_counter() - t0, 3)

        # NOTE: SQLAlchemy async sessions do NOT support concurrent operations on the
        # same session. Using asyncio.gather() here causes IllegalStateChangeError.
        # Run queries sequentially for correctness.
        t0 = time.perf_counter()
        baseline = await self._get_baseline_from_historical(config.base_year)
        timings["get_baseline"] = round(time.perf_counter() - t0, 3)

        t0 = time.perf_counter()
        result = await self.session.execute(
            select(BudgetVersion).where(BudgetVersion.id == version_id)
        )
        version = result.scalar_one_or_none()
        timings["get_version"] = round(time.perf_counter() - t0, 3)

        if not version:
            raise NotFoundError("BudgetVersion", str(version_id))

        t0 = time.perf_counter()
        global_overrides, level_overrides, grade_overrides = (
            self._build_engine_overrides(config)
        )
        timings["build_overrides"] = round(time.perf_counter() - t0, 3)

        # Use organization_id to fetch calibrated rates (percentage-based lateral entry)
        # This is the ONLY way to calculate lateral entry - no legacy fallback
        # PERFORMANCE: Uses get_effective_rates_fast() which runs queries in parallel
        t0 = time.perf_counter()
        effective_rates = await self._get_calibrated_rates(
            version.organization_id, scenario.code
        )
        timings["get_calibrated_rates"] = round(time.perf_counter() - t0, 3)

        engine_input = ProjectionInput(
            base_year=config.base_year,
            target_year=config.base_year + 1,
            projection_years=config.projection_years,
            school_max_capacity=config.school_max_capacity or DEFAULT_SCHOOL_CAPACITY,
            default_class_size=config.default_class_size,
            scenario=ScenarioParams(
                code=scenario.code,
                ps_entry=scenario.ps_entry,
                entry_growth_rate=scenario.entry_growth_rate,
                default_retention=scenario.default_retention,
                terminal_retention=scenario.terminal_retention,
                lateral_multiplier=scenario.lateral_multiplier,
            ),
            base_year_enrollment=baseline,
            base_lateral_entry={},  # Not used - calibration provides effective_rates
            effective_rates=effective_rates,  # From calibration service
            global_overrides=global_overrides,
            level_overrides=level_overrides,
            grade_overrides=grade_overrides,
        )

        errors = validate_projection_input(engine_input)
        if errors:
            raise ValidationError("Invalid projection input", details={"errors": errors})

        t0 = time.perf_counter()
        projections = project_multi_year(engine_input, years=config.projection_years)
        timings["projection_calculation"] = round(time.perf_counter() - t0, 3)

        t0 = time.perf_counter()
        await self.session.execute(
            delete(EnrollmentProjection).where(
                EnrollmentProjection.projection_config_id == config.id
            )
        )
        await self.session.flush()
        timings["delete_old_projections"] = round(time.perf_counter() - t0, 3)

        now = datetime.now(UTC)

        # PERFORMANCE FIX: Use in-memory cache for level lookups (zero latency)
        t0 = time.perf_counter()
        if reference_cache.is_loaded:
            all_levels = reference_cache.get_levels()
            level_code_to_id: dict[str, uuid.UUID] = {lv.code: lv.id for lv in all_levels}
        else:
            # Fallback to DB query if cache not loaded
            all_levels_db = (await self.session.execute(select(AcademicLevel))).scalars().all()
            level_code_to_id = {level.code: level.id for level in all_levels_db}
        timings["fetch_academic_levels"] = round(time.perf_counter() - t0, 3)

        # Build all projection rows in memory first
        t0 = time.perf_counter()
        projection_rows: list[dict] = []
        prev_enrollment = baseline

        for year_result in projections:
            curr_enrollment = {g.grade_code: g.projected_students for g in year_result.grades}
            proration = calculate_proration_by_grade(
                prev_enrollment, curr_enrollment, year_result.fiscal_year
            )

            for g in year_result.grades:
                level_id = level_code_to_id.get(g.grade_code)
                if not level_id:
                    raise NotFoundError("AcademicLevel", g.grade_code)

                projection_rows.append({
                    "projection_config_id": config.id,
                    "school_year": year_result.school_year,
                    "fiscal_year": year_result.fiscal_year,
                    "level_id": level_id,
                    "projected_students": g.projected_students,
                    "retained_students": g.retained_students,
                    "lateral_students": g.lateral_students,
                    "divisions": g.divisions,
                    "avg_class_size": g.avg_class_size,
                    "fiscal_year_weighted_students": proration.get(g.grade_code, {}).get(
                        "weighted_enrollment"
                    ),
                    "was_capacity_constrained": year_result.was_capacity_constrained,
                    "original_projection": g.original_projection,
                    "reduction_applied": g.reduction_applied,
                    "reduction_percentage": g.reduction_percentage,
                    "calculation_timestamp": now,
                })

            prev_enrollment = curr_enrollment
        timings["build_projection_rows"] = round(time.perf_counter() - t0, 3)

        # PERFORMANCE FIX: Bulk insert all rows in ONE statement (was 75 individual inserts)
        t0 = time.perf_counter()
        if projection_rows:
            await self.session.execute(insert(EnrollmentProjection).values(projection_rows))
        timings["bulk_insert"] = round(time.perf_counter() - t0, 3)

        t0 = time.perf_counter()
        await self.session.commit()
        timings["commit"] = round(time.perf_counter() - t0, 3)

        timings["total"] = round(time.perf_counter() - t_start, 3)

        # Log all timings for performance analysis
        logger.info(
            "enrollment_projections_calculated",
            version_id=str(version_id),
            **timings,
        )
        return projections

    async def get_projection_results(
        self,
        version_id: uuid.UUID,
        include_fiscal_proration: bool = True,
        config: EnrollmentProjectionConfig | None = None,
        skip_existence_check: bool = False,
    ):
        """
        Get projection results with sequential queries.

        NOTE: SQLAlchemy async sessions do NOT support concurrent operations on the
        same session. The original asyncio.gather() implementation caused
        IllegalStateChangeError. Queries now run sequentially for correctness.

        Args:
            version_id: Budget version UUID
            include_fiscal_proration: Whether to include fiscal year weighting
            config: Pre-loaded config (optional, saves ~500ms if provided)
            skip_existence_check: Skip existence check when we KNOW projections exist
                                  (e.g., after calculate_and_save). Saves ~300ms.
        """
        # PERFORMANCE FIX: Use pre-loaded config if provided (saves ~500ms)
        if config is None:
            config = await self.get_or_create_config(version_id)

        # PERFORMANCE FIX: Skip existence check when caller knows projections exist
        # (e.g., immediately after calculate_and_save)
        if not skip_existence_check:
            existing = (
                await self.session.execute(
                    select(func.count(EnrollmentProjection.id)).where(
                        and_(
                            EnrollmentProjection.projection_config_id == config.id,
                            EnrollmentProjection.deleted_at.is_(None),
                        )
                    )
                )
            ).scalar_one()
            if existing == 0:
                await self.calculate_and_save(version_id, config=config)

        # NOTE: SQLAlchemy async sessions do NOT support concurrent operations on the
        # same session. Using asyncio.gather() here causes IllegalStateChangeError.
        # Run queries sequentially for correctness.

        # Query 1: Get projections
        proj_q = (
            select(EnrollmentProjection)
            .join(AcademicLevel, EnrollmentProjection.level_id == AcademicLevel.id)
            .where(
                and_(
                    EnrollmentProjection.projection_config_id == config.id,
                    EnrollmentProjection.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(EnrollmentProjection.level).selectinload(
                    AcademicLevel.cycle
                )
            )
            .order_by(EnrollmentProjection.fiscal_year, AcademicLevel.sort_order)
        )
        proj_result = await self.session.execute(proj_q)
        proj_rows = proj_result.scalars().all()

        # Query 2: Get baseline
        baseline_totals = await self._get_baseline_from_historical(config.base_year)

        # Query 3: Get historical
        historical_years = await self._get_historical_enrollment_data(config.base_year, num_years=2)

        # Query 4: Get base year data
        base_year_data = await self._get_base_year_enrollment_data(config.base_year)

        projections_by_year: dict[int, list[EnrollmentProjection]] = {}
        for row in proj_rows:
            projections_by_year.setdefault(row.fiscal_year, []).append(row)

        year_responses = []
        base_total = sum(baseline_totals.values())
        prev_year_grades = baseline_totals.copy()
        for fiscal_year, rows in sorted(projections_by_year.items()):
            curr_year_grades = {r.level.code: r.projected_students for r in rows}
            fiscal_map = None
            if include_fiscal_proration:
                fiscal_map = {
                    g: p["weighted_enrollment"]
                    for g, p in calculate_proration_by_grade(
                        prev_year_grades, curr_year_grades, fiscal_year
                    ).items()
                }
            year_responses.append(
                {
                    "school_year": rows[0].school_year,
                    "fiscal_year": fiscal_year,
                    "grades": [
                        {
                            "grade_code": r.level.code,
                            "cycle_code": r.level.cycle.code,
                            "projected_students": r.projected_students,
                            "retained_students": r.retained_students,
                            "lateral_students": r.lateral_students,
                            "divisions": r.divisions,
                            "avg_class_size": r.avg_class_size or Decimal("0.0"),
                            "original_projection": r.original_projection,
                            "reduction_applied": r.reduction_applied,
                            "reduction_percentage": r.reduction_percentage,
                        }
                        for r in rows
                    ],
                    "total_students": sum(r.projected_students for r in rows),
                    "utilization_rate": Decimal(
                        sum(r.projected_students for r in rows)
                        / (config.school_max_capacity or DEFAULT_SCHOOL_CAPACITY)
                        * 100
                    ).quantize(Decimal("0.1")),
                    "was_capacity_constrained": any(r.was_capacity_constrained for r in rows),
                    "total_reduction_applied": sum(r.reduction_applied for r in rows),
                    "fiscal_weighted_enrollment": fiscal_map,
                }
            )
            prev_year_grades = curr_year_grades

        summary = self._build_summary(
            base_total=base_total if year_responses else 0,
            final_total=year_responses[-1]["total_students"] if year_responses else 0,
            years=config.projection_years,
            years_at_capacity=sum(1 for y in year_responses if y["was_capacity_constrained"]),
        )

        return {
            "config": config,
            "projections": year_responses,
            "summary": summary,
            "historical_years": historical_years,
            "base_year_data": base_year_data,
        }

    # ---------------------------------------------------------------------
    # Validation cascade
    # ---------------------------------------------------------------------

    async def validate_and_cascade(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
        confirmation: bool,
    ):
        if not confirmation:
            raise ValidationError("Validation requires confirmation")

        config = await self.get_or_create_config(version_id)
        projections = await self.calculate_and_save(version_id)
        if not projections:
            raise ValidationError("No projections available to validate")

        config.status = "validated"
        config.validated_at = datetime.now(UTC)
        config.validated_by = user_id

        await self._ensure_default_distributions(version_id)
        # CRITICAL: Flush to ensure distributions are visible to subsequent query
        await self.session.flush()
        await self._write_enrollment_plans_from_projection(version_id, projections[0])

        await self.session.commit()

        cascade_service = CascadeService(self.session)
        cascade_result = await cascade_service.recalculate_from_step(version_id, "enrollment")

        # PERFORMANCE FIX (Phase 4): Cache invalidation DISABLED (see update_config comment)

        return {
            "success": True,
            "downstream_updated": cascade_result.recalculated_steps,
        }

    async def unvalidate(self, version_id: uuid.UUID, user_id: uuid.UUID):
        # PERFORMANCE FIX: Single query - avoid double get_or_create_config
        config = await self.get_or_create_config(version_id)
        if config.status != "validated":
            return config

        config.status = "draft"
        config.validated_at = None
        config.validated_by = None
        await self.session.commit()

        # PERFORMANCE FIX (Phase 4): Cache invalidation DISABLED (see update_config comment)

        # PERFORMANCE FIX: Return already-loaded config - no second query needed
        # Only scalar fields changed, relationships are unchanged
        return config

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    async def _get_baseline_enrollment(self, version_id: uuid.UUID) -> dict[str, int]:
        """
        Aggregate existing enrollment_plans (sum across nationalities) to grade totals.
        Missing grades default to 0.
        """
        query = (
            select(AcademicLevel.code, func.coalesce(func.sum(EnrollmentPlan.student_count), 0))
            .join(EnrollmentPlan, EnrollmentPlan.level_id == AcademicLevel.id)
            .where(
                and_(
                    EnrollmentPlan.version_id == version_id,
                    EnrollmentPlan.deleted_at.is_(None),
                )
            )
            .group_by(AcademicLevel.code)
        )
        rows = (await self.session.execute(query)).all()
        baseline = {g: 0 for g in GRADE_SEQUENCE}
        baseline.update({code: int(total) for code, total in rows})
        return baseline

    async def _get_baseline_from_historical(self, base_year: int) -> dict[str, int]:
        """
        Get baseline enrollment from historical_actuals (previous year's actual data).

        This method fetches actual enrollment data from the historical_actuals table
        for the specified base year. This is the correct source for base year data
        in projections, as it represents real enrollment numbers from the previous
        academic year.

        PERFORMANCE OPTIMIZED: Results are cached in Redis for 24 hours since
        historical data is immutable. Saves ~300ms per call.

        Args:
            base_year: The fiscal year to fetch actuals for (e.g., 2025 for Budget 2026)

        Returns:
            Dictionary mapping grade_code to student count (e.g., {"PS": 65, "MS": 71, ...})
        """
        import json

        # Deterministic cache key - base_year is immutable
        cache_key_suffix = f"baseline:{base_year}"

        # LAYER 2: Check Redis cache first
        cached = await get_cached_calibration_data(
            organization_id=cache_key_suffix,
            data_type="projection",
        )
        if cached:
            logger.debug("baseline_from_historical_cache_hit", base_year=base_year)
            return json.loads(cached)

        logger.debug("baseline_from_historical_cache_miss", base_year=base_year)

        # DB query (cache miss)
        query = (
            select(
                HistoricalActuals.dimension_code,
                HistoricalActuals.annual_count,
            )
            .where(
                and_(
                    HistoricalActuals.module_code == HistoricalModuleCode.ENROLLMENT,
                    HistoricalActuals.dimension_type == HistoricalDimensionType.LEVEL,
                    HistoricalActuals.fiscal_year == base_year,
                    HistoricalActuals.deleted_at.is_(None),
                )
            )
        )
        rows = (await self.session.execute(query)).all()
        baseline = {g: 0 for g in GRADE_SEQUENCE}
        baseline.update(
            {code: int(count) for code, count in rows if code and count is not None}
        )

        # LAYER 2: Cache for 24 hours (immutable historical data)
        await set_cached_calibration_data(
            organization_id=cache_key_suffix,
            data_type="projection",
            data=json.dumps(baseline),
            ttl_seconds=86400,  # 24 hours
        )
        logger.debug("baseline_from_historical_cached", base_year=base_year)

        return baseline

    async def _get_calibrated_rates(
        self,
        organization_id: uuid.UUID,
        scenario_code: str,
    ) -> dict[str, EngineEffectiveRates]:
        """
        Get calibrated effective rates from EnrollmentCalibrationService.

        PERFORMANCE OPTIMIZED: Uses get_effective_rates_fast() which executes
        3 queries in parallel instead of 6+ sequential queries, saving ~1-2 seconds
        on remote databases like Supabase.

        Returns calibrated rates if available, otherwise returns an empty dict.
        When returning an empty dict, the engine will use DOCUMENT_LATERAL_DEFAULTS
        which provides sensible percentage-based defaults for all grades.

        The calibration service resolves rates using priority chain:
        Override → Derived (from history) → Document Default

        For entry point grades (MS, GS, CP, 6EME, 2NDE):
        - Returns percentage-based lateral_entry_rate

        For incidental grades (CE1, CE2, CM1, CM2, etc.):
        - Returns fixed lateral_entry_fixed

        The scenario multiplier is already applied to the rates.
        """
        calibration_service = EnrollmentCalibrationService(self.session)

        try:
            # PERFORMANCE: Use get_effective_rates_fast() which executes queries in parallel
            # This saves ~1-2 seconds compared to sequential queries
            # The fast method also returns calibration_timestamp, so we skip the
            # separate get_calibration_status() call which added 2 more queries
            all_rates = await calibration_service.get_effective_rates_fast(
                organization_id, scenario_code
            )

            # If no rates returned, the engine will use document defaults
            if not all_rates.rates:
                logger.info(
                    "No calibration data for organization %s, using document defaults",
                    organization_id,
                )
                return {}

            # Convert API schema rates to engine rates
            engine_rates: dict[str, EngineEffectiveRates] = {}
            for grade_code, rate in all_rates.rates.items():
                engine_rates[grade_code] = EngineEffectiveRates(
                    grade_code=rate.grade_code,
                    retention_rate=rate.retention_rate,
                    lateral_entry_rate=rate.lateral_entry_rate,
                    lateral_entry_fixed=rate.lateral_entry_fixed,
                    is_percentage_based=rate.is_percentage_based,
                )

            logger.info(
                "Using calibrated rates for organization %s with scenario %s",
                organization_id,
                scenario_code,
            )
            return engine_rates

        except Exception as e:
            logger.warning(
                "Failed to get calibrated rates for organization %s: %s, "
                "using document defaults",
                organization_id,
                str(e),
            )
            # Return empty dict - engine will use DOCUMENT_LATERAL_DEFAULTS
            return {}

    def _build_engine_overrides(
        self, config: EnrollmentProjectionConfig
    ) -> tuple[
        EngineGlobalOverrides | None,
        dict[str, EngineLevelOverride],
        dict[str, EngineGradeOverride],
    ]:
        global_overrides = None
        if config.global_overrides:
            global_overrides = EngineGlobalOverrides(
                ps_entry_adjustment=config.global_overrides.ps_entry_adjustment,
                retention_adjustment=config.global_overrides.retention_adjustment,
                lateral_multiplier_override=config.global_overrides.lateral_multiplier_override,
                class_size_override=config.global_overrides.class_size_override,
            )

        level_overrides: dict[str, EngineLevelOverride] = {}
        for lo in config.level_overrides:
            level_overrides[lo.cycle.code] = EngineLevelOverride(
                cycle_code=lo.cycle.code,
                class_size_ceiling=lo.class_size_ceiling,
                max_divisions=lo.max_divisions,
            )

        grade_overrides: dict[str, EngineGradeOverride] = {}
        for go in config.grade_overrides:
            grade_overrides[go.level.code] = EngineGradeOverride(
                grade_code=go.level.code,
                retention_rate=go.retention_rate,
                lateral_entry=go.lateral_entry,
                max_divisions=go.max_divisions,
                class_size_ceiling=go.class_size_ceiling,
            )

        return global_overrides, level_overrides, grade_overrides

    async def _level_id_for_code(self, code: str) -> uuid.UUID:
        """Get level ID by code using in-memory cache (zero latency)."""
        if reference_cache.is_loaded:
            cached_level = reference_cache.get_level_by_code(code)
            if not cached_level:
                raise NotFoundError("AcademicLevel", code)
            return cached_level.id
        # Fallback to DB query if cache not loaded
        level = (
            await self.session.execute(
                select(AcademicLevel).where(AcademicLevel.code == code)
            )
        ).scalar_one_or_none()
        if not level:
            raise NotFoundError("AcademicLevel", code)
        return level.id

    async def _ensure_default_distributions(self, version_id: uuid.UUID) -> None:
        # PERFORMANCE: Use in-memory cache for levels (zero latency)
        if reference_cache.is_loaded:
            levels = reference_cache.get_levels()
        else:
            levels = (  # type: ignore[assignment]
                await self.session.execute(select(AcademicLevel))
            ).scalars().all()
        existing = (
            await self.session.execute(
                select(NationalityDistribution).where(
                    and_(
                        NationalityDistribution.version_id == version_id,
                        NationalityDistribution.deleted_at.is_(None),
                    )
                )
            )
        ).scalars().all()
        existing_by_level = {d.level_id: d for d in existing}

        for level in levels:
            if level.id in existing_by_level:
                continue
            self.session.add(
                NationalityDistribution(
                    version_id=version_id,
                    level_id=level.id,
                    french_pct=Decimal("30.0"),
                    saudi_pct=Decimal("2.0"),
                    other_pct=Decimal("68.0"),
                )
            )

    async def _write_enrollment_plans_from_projection(
        self, version_id: uuid.UUID, first_year_projection
    ) -> None:
        """Split totals by nationality and upsert enrollment_plans.

        This method creates EnrollmentPlan records that downstream modules
        (Class Structure, DHG, etc.) depend on.
        """
        logger.info(
            "Starting _write_enrollment_plans_from_projection",
            version_id=str(version_id),
            num_grades=len(first_year_projection.grades) if first_year_projection else 0,
        )

        nationality_types = (
            await self.session.execute(select(NationalityType))
        ).scalars().all()
        nat_by_code = {n.code: n for n in nationality_types}
        french_id = nat_by_code["FRENCH"].id
        saudi_id = nat_by_code["SAUDI"].id
        other_id = nat_by_code["OTHER"].id

        distributions = (
            await self.session.execute(
                select(NationalityDistribution).where(
                    and_(
                        NationalityDistribution.version_id == version_id,
                        NationalityDistribution.deleted_at.is_(None),
                    )
                )
            )
        ).scalars().all()
        dist_by_level = {d.level_id: d for d in distributions}

        logger.debug(
            "Fetched nationality distributions",
            version_id=str(version_id),
            distribution_count=len(distributions),
        )

        existing_plans = (
            await self.session.execute(
                select(EnrollmentPlan).where(
                    and_(
                        EnrollmentPlan.version_id == version_id,
                        EnrollmentPlan.deleted_at.is_(None),
                    )
                )
            )
        ).scalars().all()
        existing_by_key = {
            (p.level_id, p.nationality_type_id): p for p in existing_plans
        }

        logger.debug(
            "Fetched existing enrollment plans",
            version_id=str(version_id),
            existing_count=len(existing_plans),
        )

        created_count = 0
        updated_count = 0
        skipped_grades = []
        total_students = 0

        for grade in first_year_projection.grades:
            level_id = await self._level_id_for_code(grade.grade_code)
            dist = dist_by_level.get(level_id)
            if not dist:
                skipped_grades.append(grade.grade_code)
                logger.warning(
                    "Skipping grade - no nationality distribution found",
                    grade_code=grade.grade_code,
                    level_id=str(level_id) if level_id else None,
                )
                continue

            total = grade.projected_students
            french = round(total * float(dist.french_pct) / 100)
            saudi = round(total * float(dist.saudi_pct) / 100)
            other = total - french - saudi
            total_students += total

            for nat_id, count in [
                (french_id, french),
                (saudi_id, saudi),
                (other_id, other),
            ]:
                key = (level_id, nat_id)
                existing = existing_by_key.get(key)
                if existing:
                    existing.student_count = count
                    existing.notes = "Generated from enrollment projections"
                    updated_count += 1
                else:
                    self.session.add(
                        EnrollmentPlan(
                            version_id=version_id,
                            level_id=level_id,
                            nationality_type_id=nat_id,
                            student_count=count,
                            notes="Generated from enrollment projections",
                        )
                    )
                    created_count += 1

        logger.info(
            "Completed _write_enrollment_plans_from_projection",
            version_id=str(version_id),
            created_count=created_count,
            updated_count=updated_count,
            total_students=total_students,
            skipped_grades=skipped_grades if skipped_grades else None,
        )

    def _build_summary(
        self, base_total: int, final_total: int, years: int, years_at_capacity: int
    ) -> dict:
        if base_total <= 0 or years <= 0:
            cagr = Decimal("0.0")
        else:
            cagr = (Decimal(final_total) / Decimal(base_total)) ** (
                Decimal("1") / Decimal(str(years))
            ) - Decimal("1")
        return {
            "base_year_total": base_total,
            "final_year_total": final_total,
            "cagr": cagr.quantize(Decimal("0.0001")),
            "years_at_capacity": years_at_capacity,
        }

    async def _get_historical_enrollment_data(
        self, base_year: int, num_years: int = 2
    ) -> list[dict]:
        """
        Fetch historical enrollment data from HistoricalActuals.

        Note: HistoricalActuals is currently not organization-scoped.
        If multi-tenant support is needed, add organization_id column via migration.

        PERFORMANCE OPTIMIZED: Results are cached in Redis for 24 hours since
        historical data is immutable. Saves ~800ms per call.

        Args:
            base_year: The base year for projections (we fetch years before this)
            num_years: Number of historical years to fetch (default: 2)

        Returns:
            List of dicts with fiscal_year, school_year, grades, total_students
        """
        import hashlib
        import json

        # Deterministic cache key based on years requested
        target_years = [base_year - i for i in range(1, num_years + 1)]
        years_hash = hashlib.md5(str(sorted(target_years)).encode()).hexdigest()[:8]
        cache_key_suffix = f"historical:{years_hash}"

        # LAYER 2: Check Redis cache first
        cached = await get_cached_calibration_data(
            organization_id=cache_key_suffix,
            data_type="projection",
        )
        if cached:
            logger.debug(
                "historical_enrollment_cache_hit",
                base_year=base_year,
                num_years=num_years,
            )
            return json.loads(cached)

        logger.debug(
            "historical_enrollment_cache_miss",
            base_year=base_year,
            num_years=num_years,
        )

        # DB query (cache miss)
        query = (
            select(
                HistoricalActuals.fiscal_year,
                HistoricalActuals.dimension_code,  # grade_code
                HistoricalActuals.annual_count,
            )
            .where(
                and_(
                    HistoricalActuals.module_code == HistoricalModuleCode.ENROLLMENT,
                    HistoricalActuals.dimension_type == HistoricalDimensionType.LEVEL,
                    HistoricalActuals.fiscal_year.in_(target_years),
                    HistoricalActuals.deleted_at.is_(None),
                )
            )
            .order_by(HistoricalActuals.fiscal_year.asc())
        )

        rows = (await self.session.execute(query)).all()

        # Group by fiscal year
        years_data: dict[int, dict[str, int]] = {}
        for fiscal_year, grade_code, count in rows:
            if fiscal_year not in years_data:
                years_data[fiscal_year] = {}
            if grade_code and count is not None:
                years_data[fiscal_year][grade_code] = count

        # Build response list
        result = []
        for fiscal_year in sorted(years_data.keys()):
            grades = years_data[fiscal_year]
            result.append({
                "fiscal_year": fiscal_year,
                "school_year": f"{fiscal_year}/{fiscal_year + 1}",
                "grades": grades,
                "total_students": sum(grades.values()),
            })

        # LAYER 2: Cache for 24 hours (immutable historical data)
        await set_cached_calibration_data(
            organization_id=cache_key_suffix,
            data_type="projection",
            data=json.dumps(result),
            ttl_seconds=86400,  # 24 hours
        )
        logger.debug(
            "historical_enrollment_cached",
            base_year=base_year,
            num_years=num_years,
        )

        return result

    async def _get_base_year_enrollment_data(self, base_year: int) -> dict | None:
        """
        Fetch actual enrollment data for the base year.

        This is used to display the "BASE" column in the projection grid,
        showing the actual enrollment that projections are calculated from.

        PERFORMANCE OPTIMIZED: Results are cached in Redis for 24 hours since
        historical data is immutable. Saves ~300ms per call.

        Args:
            base_year: The fiscal year to fetch actuals for (e.g., 2025 for Budget 2026)

        Returns:
            Dict with fiscal_year, school_year, grades, total_students or None if no data
        """
        import json

        # Deterministic cache key - base_year is immutable
        cache_key_suffix = f"base_year_data:{base_year}"

        # LAYER 2: Check Redis cache first
        cached = await get_cached_calibration_data(
            organization_id=cache_key_suffix,
            data_type="projection",
        )
        if cached:
            logger.debug("base_year_enrollment_cache_hit", base_year=base_year)
            # Handle "null" string from json.dumps(None)
            data = json.loads(cached)
            return data if data else None

        logger.debug("base_year_enrollment_cache_miss", base_year=base_year)

        # DB query (cache miss)
        query = (
            select(
                HistoricalActuals.dimension_code,  # grade_code
                HistoricalActuals.annual_count,
            )
            .where(
                and_(
                    HistoricalActuals.module_code == HistoricalModuleCode.ENROLLMENT,
                    HistoricalActuals.dimension_type == HistoricalDimensionType.LEVEL,
                    HistoricalActuals.fiscal_year == base_year,
                    HistoricalActuals.deleted_at.is_(None),
                )
            )
        )

        rows = (await self.session.execute(query)).all()

        if not rows:
            # Cache the "no data" result too to avoid repeated DB queries
            await set_cached_calibration_data(
                organization_id=cache_key_suffix,
                data_type="projection",
                data=json.dumps(None),
                ttl_seconds=86400,  # 24 hours
            )
            return None  # No historical data for base year

        grades = {
            grade_code: count
            for grade_code, count in rows
            if grade_code and count is not None
        }

        result = {
            "fiscal_year": base_year,
            "school_year": f"{base_year}/{base_year + 1}",
            "grades": grades,
            "total_students": sum(grades.values()),
        }

        # LAYER 2: Cache for 24 hours (immutable historical data)
        await set_cached_calibration_data(
            organization_id=cache_key_suffix,
            data_type="projection",
            data=json.dumps(result),
            ttl_seconds=86400,  # 24 hours
        )
        logger.debug("base_year_enrollment_cached", base_year=base_year)

        return result

    # ---------------------------------------------------------------------
    # Lateral Entry Optimization (Class Structure Aware)
    # ---------------------------------------------------------------------

    async def _get_class_size_configs(
        self, version_id: uuid.UUID
    ) -> dict[str, ClassSizeConfig]:
        """
        Get effective class size configurations for all grades.

        Resolves level-specific → cycle-level → default hierarchy.

        Args:
            version_id: Budget version UUID

        Returns:
            Dict mapping grade_code to ClassSizeConfig
        """
        # Get all class size params for this version
        params_query = select(ClassSizeParam).where(
            and_(
                ClassSizeParam.version_id == version_id,
                ClassSizeParam.deleted_at.is_(None),
            )
        )
        params = (await self.session.execute(params_query)).scalars().all()

        # PERFORMANCE: Use in-memory cache for levels (zero latency)
        if reference_cache.is_loaded:
            levels = reference_cache.get_levels()
        else:
            levels = (  # type: ignore[assignment]
                await self.session.execute(select(AcademicLevel))
            ).scalars().all()

        # Build params lookup: level_id → param, cycle_id → param
        level_params: dict[uuid.UUID, ClassSizeParam] = {}
        cycle_params: dict[uuid.UUID, ClassSizeParam] = {}

        for param in params:
            if param.level_id:
                level_params[param.level_id] = param
            elif param.cycle_id:
                cycle_params[param.cycle_id] = param

        # Default configs by cycle (fallback values)
        default_configs = {
            "MAT": ClassSizeConfig(
                min_class_size=21, target_class_size=25, max_class_size=28, max_divisions=6
            ),
            "ELEM": ClassSizeConfig(
                min_class_size=21, target_class_size=25, max_class_size=28, max_divisions=6
            ),
            "COLL": ClassSizeConfig(
                min_class_size=15, target_class_size=25, max_class_size=30, max_divisions=6
            ),
            "LYC": ClassSizeConfig(
                min_class_size=15, target_class_size=25, max_class_size=30, max_divisions=6
            ),
        }

        # Build effective config for each grade
        configs: dict[str, ClassSizeConfig] = {}

        for grade in GRADE_SEQUENCE:
            cycle_code = GRADE_TO_CYCLE.get(grade, "ELEM")

            # Find level ID for this grade
            level_id = None
            cycle_id = None
            for level in levels:
                if level.code == grade:
                    level_id = level.id
                    cycle_id = level.cycle_id
                    break

            # Resolution priority: level-specific → cycle-level → default
            param = None
            if level_id and level_id in level_params:
                param = level_params[level_id]
            elif cycle_id and cycle_id in cycle_params:
                param = cycle_params[cycle_id]

            if param:
                configs[grade] = ClassSizeConfig(
                    min_class_size=param.min_class_size,
                    target_class_size=param.target_class_size,
                    max_class_size=param.max_class_size,
                    max_divisions=6,  # Default, could be overridden from level_overrides
                )
            else:
                configs[grade] = default_configs.get(
                    cycle_code,
                    ClassSizeConfig(
                        min_class_size=21,
                        target_class_size=25,
                        max_class_size=28,
                        max_divisions=6,
                    ),
                )

        return configs

    async def calculate_lateral_optimization(
        self,
        version_id: uuid.UUID,
        base_year_enrollment: dict[str, int],
        effective_rates: dict[str, EngineEffectiveRates] | None = None,
        ps_entry: int = 55,
        entry_growth_rate: Decimal = Decimal("0.0"),
    ) -> tuple[list[GradeOptimizationResult], NewStudentsSummary]:
        """
        Calculate optimal lateral entry for all grades using class structure optimization.

        This implements the capacity-aware lateral entry model that minimizes
        rejections while maintaining efficient class structures.

        Args:
            version_id: Budget version UUID (for class size config lookup)
            base_year_enrollment: Current enrollment by grade
            effective_rates: Calibrated rates from EnrollmentCalibrationService
            ps_entry: Base PS entry count from scenario
            entry_growth_rate: Growth rate to apply to PS entry

        Returns:
            Tuple of (list of grade optimization results, summary)
        """
        # Get class size configs from database
        class_configs = await self._get_class_size_configs(version_id)

        results: list[GradeOptimizationResult] = []

        # PS is special - pure entry point with no retention
        ps_demand = int(ps_entry * (1 + float(entry_growth_rate)))
        ps_result = optimize_ps_entry(ps_demand, class_configs.get("PS", class_configs["MS"]))
        results.append(ps_result)

        # Process other grades in sequence
        for i in range(1, len(GRADE_SEQUENCE)):
            grade = GRADE_SEQUENCE[i]
            prev_grade = GRADE_SEQUENCE[i - 1]

            # Calculate retained students from previous grade
            prev_enrollment = base_year_enrollment.get(prev_grade, 0)

            # Get retention rate (from calibration or document defaults)
            if effective_rates and grade in effective_rates:
                retention_rate = float(effective_rates[grade].retention_rate)
            else:
                # Use document defaults when no calibration data available
                defaults = UNIFIED_LATERAL_DEFAULTS.get(grade, {})
                retention_rate = float(defaults.get("retention_rate", Decimal("0.96")))

            retained = int(prev_enrollment * retention_rate)

            # Get historical demand (from calibration or document defaults)
            historical_demand = 0
            if effective_rates and grade in effective_rates:
                rate = effective_rates[grade]
                if rate.is_percentage_based and rate.lateral_entry_rate:
                    # Entry point: percentage of previous grade
                    historical_demand = int(
                        prev_enrollment * float(rate.lateral_entry_rate)
                    )
                elif rate.lateral_entry_fixed is not None:
                    # Incidental: fixed count
                    historical_demand = rate.lateral_entry_fixed
            else:
                # Use document defaults when no calibration data available
                defaults = UNIFIED_LATERAL_DEFAULTS.get(grade)
                if defaults:
                    lateral_rate = float(defaults.get("lateral_rate", 0))
                    historical_demand = int(prev_enrollment * lateral_rate)

            # Get class size config for this grade
            config = class_configs.get(grade)
            if not config:
                cycle_code = GRADE_TO_CYCLE.get(grade, "ELEM")
                config = class_configs.get(
                    grade,
                    ClassSizeConfig(
                        min_class_size=21 if cycle_code in ("MAT", "ELEM") else 15,
                        target_class_size=25,
                        max_class_size=28 if cycle_code in ("MAT", "ELEM") else 30,
                        max_divisions=6,
                    ),
                )

            # Build optimization input
            grade_input = GradeOptimizationInput(
                grade_code=grade,
                cycle_code=GRADE_TO_CYCLE.get(grade, "ELEM"),
                retained_students=retained,
                historical_demand=historical_demand,
                class_size_config=config,
                is_entry_point=is_entry_point_grade(grade),
            )

            # Run optimization
            result = optimize_grade_lateral_entry(grade_input)
            results.append(result)

        # Build summary
        summary = build_new_students_summary(results)

        logger.info(
            "lateral_optimization_calculated",
            version_id=str(version_id),
            total_demand=summary.total_demand,
            total_accepted=summary.total_accepted,
            acceptance_rate=str(summary.overall_acceptance_rate),
        )

        return results, summary

    async def get_lateral_optimization(
        self,
        version_id: uuid.UUID,
    ) -> dict:
        """
        Get lateral entry optimization results for a budget version.

        Calculates optimization based on current projection config and baseline.

        Args:
            version_id: Budget version UUID

        Returns:
            Dict with optimization_results and new_students_summary
        """
        config = await self.get_or_create_config(version_id)
        scenario = config.scenario
        # Use historical_actuals for base year (actual enrollment from previous year)
        baseline = await self._get_baseline_from_historical(config.base_year)

        # Get organization_id for calibrated rates
        version = (
            await self.session.execute(
                select(BudgetVersion).where(BudgetVersion.id == version_id)
            )
        ).scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(version_id))

        effective_rates = await self._get_calibrated_rates(
            version.organization_id, scenario.code
        )

        results, summary = await self.calculate_lateral_optimization(
            version_id=version_id,
            base_year_enrollment=baseline,
            effective_rates=effective_rates,
            ps_entry=scenario.ps_entry,
            entry_growth_rate=scenario.entry_growth_rate,
        )

        return {
            "optimization_results": [
                {
                    "grade_code": r.grade_code,
                    "cycle_code": r.cycle_code,
                    "is_entry_point": r.is_entry_point,
                    "retained_students": r.retained_students,
                    "historical_demand": r.historical_demand,
                    "base_classes": r.base_classes,
                    "fill_to_target": r.fill_to_target,
                    "fill_to_max": r.fill_to_max,
                    "new_class_threshold": r.new_class_threshold,
                    "decision": r.decision.value,
                    "accepted": r.accepted,
                    "rejected": r.rejected,
                    "final_classes": r.final_classes,
                    "final_students": r.final_students,
                    "avg_class_size": r.avg_class_size,
                    "utilization_pct": r.utilization_pct,
                    "acceptance_rate": r.acceptance_rate,
                }
                for r in results
            ],
            "new_students_summary": {
                "total_demand": summary.total_demand,
                "total_available": summary.total_available,
                "total_accepted": summary.total_accepted,
                "total_rejected": summary.total_rejected,
                "overall_acceptance_rate": summary.overall_acceptance_rate,
                "entry_point_demand": summary.entry_point_demand,
                "entry_point_accepted": summary.entry_point_accepted,
                "incidental_demand": summary.incidental_demand,
                "incidental_accepted": summary.incidental_accepted,
                "grades_accept_all": summary.grades_accept_all,
                "grades_fill_max": summary.grades_fill_max,
                "grades_restricted": summary.grades_restricted,
                "grades_new_class": summary.grades_new_class,
                "grades_at_ceiling": summary.grades_at_ceiling,
                "by_grade": [
                    {
                        "grade_code": row.grade_code,
                        "grade_name": row.grade_name,
                        "cycle_code": row.cycle_code,
                        "is_entry_point": row.is_entry_point,
                        "historical_demand": row.historical_demand,
                        "available_slots": row.available_slots,
                        "accepted": row.accepted,
                        "rejected": row.rejected,
                        "acceptance_rate": row.acceptance_rate,
                        "pct_of_total_intake": row.pct_of_total_intake,
                        "decision": row.decision.value,
                    }
                    for row in summary.by_grade
                ],
            },
        }
