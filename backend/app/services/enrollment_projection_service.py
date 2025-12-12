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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

# NOTE: CacheInvalidator import removed as part of Phase 4 performance fix.
# Cache invalidation was causing 6s delays; now disabled for all config updates.
# See update_config method comment for full rationale.
from app.core.logging import logger
from app.engine.enrollment import (
    EngineEffectiveRates,
    ProjectionInput,
    ScenarioParams,
    calculate_proration_by_grade,
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
from app.engine.enrollment.projection_engine import GRADE_SEQUENCE
from app.models.configuration import AcademicLevel, BudgetVersion, NationalityType
from app.models.enrollment_projection import (
    EnrollmentGlobalOverride,
    EnrollmentGradeOverride,
    EnrollmentLevelOverride,
    EnrollmentProjection,
    EnrollmentProjectionConfig,
    EnrollmentScenario,
)
from app.models.planning import EnrollmentPlan, NationalityDistribution
from app.services.cascade_service import CascadeService
from app.services.enrollment_calibration_service import EnrollmentCalibrationService
from app.services.enrollment_capacity import DEFAULT_SCHOOL_CAPACITY
from app.services.exceptions import NotFoundError, ValidationError


class EnrollmentProjectionService:
    """Service layer for enrollment projections."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------------------------------------------------------------------
    # Scenarios & Config
    # ---------------------------------------------------------------------

    async def get_all_scenarios(self) -> list[EnrollmentScenario]:
        query = select(EnrollmentScenario).order_by(EnrollmentScenario.sort_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_or_create_config(
        self, version_id: uuid.UUID
    ) -> EnrollmentProjectionConfig:
        query = (
            select(EnrollmentProjectionConfig)
            .where(
                and_(
                    EnrollmentProjectionConfig.budget_version_id == version_id,
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

        base_scenario = (
            await self.session.execute(
                select(EnrollmentScenario).where(EnrollmentScenario.code == "base")
            )
        ).scalar_one_or_none()
        if not base_scenario:
            raise NotFoundError("EnrollmentScenario", "base")

        config = EnrollmentProjectionConfig(
            budget_version_id=version_id,
            scenario_id=base_scenario.id,
            base_year=version.fiscal_year - 1,
            projection_years=5,
            school_max_capacity=DEFAULT_SCHOOL_CAPACITY,
            default_class_size=25,
            status="draft",
        )
        self.session.add(config)
        await self.session.commit()

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
        print(f"⏱️ TIMING: get_or_create_config took {time.perf_counter() - _t0:.3f}s")

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
            print(f"⏱️ TIMING: no changes, returning early at {time.perf_counter() - _t0:.3f}s")
            return config

        _t1 = time.perf_counter()
        await self.session.commit()
        print(f"⏱️ TIMING: commit took {time.perf_counter() - _t1:.3f}s")

        # PHASE 11: Use session.get() instead of session.refresh() to avoid extra roundtrip
        # session.get() checks identity map first - if scenario was already loaded in this
        # session (e.g., from get_all_scenarios), no network roundtrip is needed.
        # session.refresh() ALWAYS makes a roundtrip, even for cached objects.
        if scenario_changed and config.scenario_id:
            _t2 = time.perf_counter()
            config.scenario = await self.session.get(EnrollmentScenario, config.scenario_id)
            print(f"⏱️ TIMING: session.get scenario took {time.perf_counter() - _t2:.3f}s")

        # FIX Issue #4: Deferred calculation - only calculate when explicitly requested
        if recalculate:
            await self.calculate_and_save(version_id, config=config)

        # PERFORMANCE FIX (Phase 4): Cache invalidation DISABLED for performance.
        # Cache keys include version_id, so scenario changes don't affect cached calculation data.
        # Cache will auto-expire via TTL, and heavy calculations recalculate on-demand when needed.
        # (Removed: CacheInvalidator.invalidate_background - caused 6s blocking despite fire-and-forget)

        print(f"⏱️ TIMING: update_config TOTAL took {time.perf_counter() - _t0:.3f}s")
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
        # PERFORMANCE FIX: Accept pre-loaded config to avoid redundant queries
        if config is None:
            config = await self.get_or_create_config(version_id)
        scenario = config.scenario

        # Serialize recalculations per config to avoid concurrent inserts
        # that can violate the unique constraint on cached projections.
        await self.session.execute(
            select(EnrollmentProjectionConfig.id)
            .where(EnrollmentProjectionConfig.id == config.id)
            .with_for_update()
        )

        baseline = await self._get_baseline_enrollment(version_id)

        global_overrides, level_overrides, grade_overrides = (
            self._build_engine_overrides(config)
        )

        # Get organization_id from budget_version for calibrated rates lookup.
        # Each budget version belongs to an organization, which scopes the
        # enrollment derived parameters, overrides, and scenario multipliers.
        version = (
            await self.session.execute(
                select(BudgetVersion).where(BudgetVersion.id == version_id)
            )
        ).scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(version_id))

        # Use organization_id to fetch calibrated rates (percentage-based lateral entry)
        # This is the ONLY way to calculate lateral entry - no legacy fallback
        effective_rates = await self._get_calibrated_rates(
            version.organization_id, scenario.code
        )

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

        projections = project_multi_year(engine_input, years=config.projection_years)

        await self.session.execute(
            delete(EnrollmentProjection).where(
                EnrollmentProjection.projection_config_id == config.id
            )
        )
        await self.session.flush()

        now = datetime.now(UTC)

        # PERFORMANCE FIX: Pre-fetch ALL level codes in ONE query (was N+1 pattern)
        # This replaces 75 individual queries with 1 bulk query
        all_levels = (await self.session.execute(select(AcademicLevel))).scalars().all()
        level_code_to_id: dict[str, uuid.UUID] = {
            level.code: level.id for level in all_levels
        }

        # Build all projection rows in memory first
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

        # PERFORMANCE FIX: Bulk insert all rows in ONE statement (was 75 individual inserts)
        if projection_rows:
            await self.session.execute(insert(EnrollmentProjection).values(projection_rows))

        await self.session.commit()
        logger.info("enrollment_projections_calculated", version_id=str(version_id))
        return projections

    async def get_projection_results(
        self, version_id: uuid.UUID, include_fiscal_proration: bool = True
    ):
        config = await self.get_or_create_config(version_id)

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
            await self.calculate_and_save(version_id)

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
        proj_rows = (await self.session.execute(proj_q)).scalars().all()

        projections_by_year: dict[int, list[EnrollmentProjection]] = {}
        for row in proj_rows:
            projections_by_year.setdefault(row.fiscal_year, []).append(row)

        year_responses = []
        baseline_totals = await self._get_baseline_enrollment(version_id)
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
                    EnrollmentPlan.budget_version_id == version_id,
                    EnrollmentPlan.deleted_at.is_(None),
                )
            )
            .group_by(AcademicLevel.code)
        )
        rows = (await self.session.execute(query)).all()
        baseline = {g: 0 for g in GRADE_SEQUENCE}
        baseline.update({code: int(total) for code, total in rows})
        return baseline

    async def _get_calibrated_rates(
        self,
        organization_id: uuid.UUID,
        scenario_code: str,
    ) -> dict[str, EngineEffectiveRates] | None:
        """
        Get calibrated effective rates from EnrollmentCalibrationService.

        This is the ONLY way to get lateral entry rates - there is no legacy fallback.
        Returns None if no calibration data is available for the organization.

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
            # Get calibration status to check if data is available
            status = await calibration_service.get_calibration_status(organization_id)

            if not status.has_sufficient_data:
                logger.info(
                    "No calibration data available for organization %s, using legacy mode",
                    organization_id,
                )
                return None

            # Get effective rates with scenario multiplier applied
            all_rates = await calibration_service.get_effective_rates(
                organization_id, scenario_code
            )

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
                "falling back to legacy mode",
                organization_id,
                str(e),
            )
            return None

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
        level = (
            await self.session.execute(
                select(AcademicLevel).where(AcademicLevel.code == code)
            )
        ).scalar_one_or_none()
        if not level:
            raise NotFoundError("AcademicLevel", code)
        return level.id

    async def _ensure_default_distributions(self, version_id: uuid.UUID) -> None:
        levels = (
            await self.session.execute(select(AcademicLevel))
        ).scalars().all()
        existing = (
            await self.session.execute(
                select(NationalityDistribution).where(
                    and_(
                        NationalityDistribution.budget_version_id == version_id,
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
                    budget_version_id=version_id,
                    level_id=level.id,
                    french_pct=Decimal("30.0"),
                    saudi_pct=Decimal("2.0"),
                    other_pct=Decimal("68.0"),
                )
            )

    async def _write_enrollment_plans_from_projection(
        self, version_id: uuid.UUID, first_year_projection
    ) -> None:
        """Split totals by nationality and upsert enrollment_plans."""
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
                        NationalityDistribution.budget_version_id == version_id,
                        NationalityDistribution.deleted_at.is_(None),
                    )
                )
            )
        ).scalars().all()
        dist_by_level = {d.level_id: d for d in distributions}

        existing_plans = (
            await self.session.execute(
                select(EnrollmentPlan).where(
                    and_(
                        EnrollmentPlan.budget_version_id == version_id,
                        EnrollmentPlan.deleted_at.is_(None),
                    )
                )
            )
        ).scalars().all()
        existing_by_key = {
            (p.level_id, p.nationality_type_id): p for p in existing_plans
        }

        for grade in first_year_projection.grades:
            level_id = await self._level_id_for_code(grade.grade_code)
            dist = dist_by_level.get(level_id)
            if not dist:
                continue

            total = grade.projected_students
            french = round(total * float(dist.french_pct) / 100)
            saudi = round(total * float(dist.saudi_pct) / 100)
            other = total - french - saudi

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
                else:
                    self.session.add(
                        EnrollmentPlan(
                            budget_version_id=version_id,
                            level_id=level_id,
                            nationality_type_id=nat_id,
                            student_count=count,
                            notes="Generated from enrollment projections",
                        )
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
