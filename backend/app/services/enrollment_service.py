"""
Enrollment service for managing enrollment planning and projections.

Handles CRUD operations for enrollment plans and integrates with the
enrollment projection engine for growth scenarios and capacity validation.
"""

import uuid
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.logging import logger
from app.engine.enrollment import (
    EnrollmentGrowthScenario,
    EnrollmentInput,
    EnrollmentProjectionResult,
    calculate_enrollment_projection,
)
from app.models.configuration import AcademicLevel, NationalityType
from app.models.planning import EnrollmentPlan, NationalityDistribution
from app.services.base import BaseService
from app.services.enrollment_capacity import get_effective_capacity
from app.services.exceptions import (
    BusinessRuleError,
    ServiceException,
    ValidationError,
)


class EnrollmentService:
    """
    Service for enrollment planning operations.

    Provides business logic for enrollment management, projection calculations,
    and capacity validation.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize enrollment service.

        Args:
            session: Async database session
        """
        self.session = session
        self.base_service = BaseService(EnrollmentPlan, session)

    async def get_enrollment_plan(
        self, version_id: uuid.UUID
    ) -> list[EnrollmentPlan]:
        """
        Get enrollment plan for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of EnrollmentPlan instances with relationships loaded

        Raises:
            ServiceException: If database operation fails

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads level, cycle, nationality_type, and audit fields
            - Leverages idx_enrollment_version index
        """
        try:
            # Create aliases for joined tables to use in order_by
            level_alias = aliased(AcademicLevel)
            nationality_alias = aliased(NationalityType)

            query = (
                select(EnrollmentPlan)
                .join(level_alias, EnrollmentPlan.level_id == level_alias.id)
                .join(nationality_alias, EnrollmentPlan.nationality_type_id == nationality_alias.id)
                .where(
                    and_(
                        EnrollmentPlan.budget_version_id == version_id,
                        EnrollmentPlan.deleted_at.is_(None),
                    )
                )
                .options(
                    selectinload(EnrollmentPlan.level).selectinload(AcademicLevel.cycle),
                    selectinload(EnrollmentPlan.nationality_type),
                    selectinload(EnrollmentPlan.budget_version),
                )
                .order_by(
                    level_alias.sort_order,
                    nationality_alias.sort_order,
                )
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            error_msg = f"SQLAlchemy Error: {type(e).__name__}: {e!s}"
            logger.error(
                "Failed to retrieve enrollment plan",
                version_id=str(version_id),
                error=error_msg,
                exc_info=True,
            )
            raise ServiceException(
                f"Failed to retrieve enrollment plan. {error_msg}",
                status_code=500,
                details={"version_id": str(version_id), "error": error_msg},
            ) from e

    async def get_enrollment_by_id(self, enrollment_id: uuid.UUID) -> EnrollmentPlan:
        """
        Get enrollment plan entry by ID.

        Args:
            enrollment_id: Enrollment plan UUID

        Returns:
            EnrollmentPlan instance

        Raises:
            NotFoundError: If enrollment not found
        """
        return await self.base_service.get_by_id(enrollment_id)

    async def create_enrollment(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
        nationality_type_id: uuid.UUID,
        student_count: int,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> EnrollmentPlan:
        """
        Create enrollment plan entry.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID
            nationality_type_id: Nationality type UUID
            student_count: Number of students
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            Created EnrollmentPlan instance

        Raises:
            ValidationError: If validation fails
            BusinessRuleError: If capacity exceeded
        """
        await self._validate_capacity(version_id, student_count)

        query = select(EnrollmentPlan).where(
            and_(
                EnrollmentPlan.budget_version_id == version_id,
                EnrollmentPlan.level_id == level_id,
                EnrollmentPlan.nationality_type_id == nationality_type_id,
                EnrollmentPlan.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValidationError(
                "Enrollment entry already exists for this level and nationality type",
                details={
                    "level_id": str(level_id),
                    "nationality_type_id": str(nationality_type_id),
                },
            )

        return await self.base_service.create(
            {
                "budget_version_id": version_id,
                "level_id": level_id,
                "nationality_type_id": nationality_type_id,
                "student_count": student_count,
                "notes": notes,
            },
            user_id=user_id,
        )

    async def update_enrollment(
        self,
        enrollment_id: uuid.UUID,
        student_count: int | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> EnrollmentPlan:
        """
        Update enrollment plan entry.

        Args:
            enrollment_id: Enrollment plan UUID
            student_count: Updated student count
            notes: Updated notes
            user_id: User ID for audit trail

        Returns:
            Updated EnrollmentPlan instance

        Raises:
            NotFoundError: If enrollment not found
            BusinessRuleError: If capacity exceeded
        """
        enrollment = await self.get_enrollment_by_id(enrollment_id)

        if student_count is not None:
            delta = student_count - enrollment.student_count
            await self._validate_capacity(
                enrollment.budget_version_id,
                delta,
                exclude_id=enrollment_id,
            )

        update_data = {}
        if student_count is not None:
            update_data["student_count"] = student_count
        if notes is not None:
            update_data["notes"] = notes

        return await self.base_service.update(
            enrollment_id,
            update_data,
            user_id=user_id,
        )

    async def delete_enrollment(
        self,
        enrollment_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        """
        Delete enrollment plan entry.

        Args:
            enrollment_id: Enrollment plan UUID
            user_id: User ID for audit trail

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If enrollment not found
        """
        return await self.base_service.delete(enrollment_id)

    async def get_enrollment_summary(
        self, version_id: uuid.UUID
    ) -> dict[str, any]:
        """
        Get enrollment summary statistics.

        Args:
            version_id: Budget version UUID

        Returns:
            Dictionary with enrollment statistics:
            - total_students: Total enrollment
            - by_level: Breakdown by level code
            - by_cycle: Breakdown by cycle code
            - by_nationality: Breakdown by nationality
            - capacity_utilization: Percentage of max capacity
        """
        enrollments = await self.get_enrollment_plan(version_id)

        total_students = sum(e.student_count for e in enrollments)

        by_level: dict[str, int] = {}
        by_cycle: dict[str, int] = {}
        by_nationality: dict[str, int] = {}

        for enrollment in enrollments:
            level_code = enrollment.level.code
            cycle_code = enrollment.level.cycle.code
            nationality_code = enrollment.nationality_type.code

            by_level[level_code] = by_level.get(level_code, 0) + enrollment.student_count
            by_cycle[cycle_code] = by_cycle.get(cycle_code, 0) + enrollment.student_count
            by_nationality[nationality_code] = (
                by_nationality.get(nationality_code, 0) + enrollment.student_count
            )

        effective_capacity = await get_effective_capacity(self.session, version_id)
        capacity_utilization = Decimal(
            (total_students / effective_capacity) * 100
            if effective_capacity > 0
            else 0
        ).quantize(Decimal("0.01"))

        return {
            "total_students": total_students,
            "by_level": by_level,
            "by_cycle": by_cycle,
            "by_nationality": by_nationality,
            "capacity_utilization": capacity_utilization,
            "max_capacity": effective_capacity,
        }

    async def project_enrollment(
        self,
        version_id: uuid.UUID,
        years_to_project: int = 5,
        growth_scenario: str = "base",
        custom_growth_rates: dict[str, Decimal] | None = None,
    ) -> list[EnrollmentProjectionResult]:
        """
        Calculate enrollment projections for multiple years.

        Args:
            version_id: Budget version UUID
            years_to_project: Number of years to project (1-10)
            growth_scenario: Growth scenario (conservative, base, optimistic)
            custom_growth_rates: Optional custom growth rates by level_id

        Returns:
            List of EnrollmentProjectionResult for each level/nationality combo

        Raises:
            ValidationError: If invalid parameters
            BusinessRuleError: If capacity exceeded in projections
        """
        if not 1 <= years_to_project <= 10:
            raise ValidationError(
                "Years to project must be between 1 and 10",
                field="years_to_project",
            )

        try:
            scenario = EnrollmentGrowthScenario(growth_scenario)
        except ValueError:
            raise ValidationError(
                f"Invalid growth scenario: {growth_scenario}. "
                f"Must be one of: conservative, base, optimistic",
                field="growth_scenario",
            )

        enrollments = await self.get_enrollment_plan(version_id)

        if not enrollments:
            raise BusinessRuleError(
                "NO_ENROLLMENT_DATA",
                "Cannot project enrollment without existing enrollment data",
            )

        effective_capacity = await get_effective_capacity(self.session, version_id)

        projections = []

        for enrollment in enrollments:
            level_id_str = str(enrollment.level_id)
            custom_rate = (
                custom_growth_rates.get(level_id_str)
                if custom_growth_rates
                else None
            )

            enrollment_input = EnrollmentInput(
                level_id=enrollment.level_id,
                level_code=enrollment.level.code,
                nationality=enrollment.nationality_type.code,
                current_enrollment=enrollment.student_count,
                growth_scenario=scenario,
                custom_growth_rate=custom_rate,
                years_to_project=years_to_project,
            )

            projection_result = calculate_enrollment_projection(enrollment_input)

            final_year_projection = projection_result.projections[-1]
            if final_year_projection.projected_enrollment > effective_capacity / 10:
                projection_result.capacity_exceeded = True

            projections.append(projection_result)

        total_final_year = sum(
            p.projections[-1].projected_enrollment for p in projections
        )
        if total_final_year > effective_capacity:
            raise BusinessRuleError(
                "CAPACITY_EXCEEDED",
                f"Projected enrollment ({total_final_year}) exceeds school capacity "
                f"({effective_capacity}) in year {years_to_project}",
                details={
                    "projected_total": total_final_year,
                    "max_capacity": effective_capacity,
                    "year": years_to_project,
                },
            )

        return projections

    async def _validate_capacity(
        self,
        version_id: uuid.UUID,
        additional_students: int,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        """
        Validate that adding students won't exceed capacity.

        Args:
            version_id: Budget version UUID
            additional_students: Number of students to add
            exclude_id: Optional enrollment ID to exclude from current total

        Raises:
            BusinessRuleError: If capacity would be exceeded
        """
        query = select(func.sum(EnrollmentPlan.student_count)).where(
            and_(
                EnrollmentPlan.budget_version_id == version_id,
                EnrollmentPlan.deleted_at.is_(None),
            )
        )

        if exclude_id:
            query = query.where(EnrollmentPlan.id != exclude_id)

        result = await self.session.execute(query)
        current_total = result.scalar_one() or 0

        new_total = current_total + additional_students

        effective_capacity = await get_effective_capacity(self.session, version_id)
        if new_total > effective_capacity:
            raise BusinessRuleError(
                "CAPACITY_EXCEEDED",
                f"Total enrollment ({new_total}) would exceed school capacity "
                f"({effective_capacity})",
                details={
                    "current_total": current_total,
                    "additional_students": additional_students,
                    "new_total": new_total,
                    "max_capacity": effective_capacity,
                },
            )

    # ==========================================================================
    # Nationality Distribution Methods
    # ==========================================================================

    async def get_distributions(
        self, version_id: uuid.UUID
    ) -> list[NationalityDistribution]:
        """
        Get nationality distributions for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of NationalityDistribution instances with level relationships

        Raises:
            ServiceException: If database operation fails
        """
        try:
            query = (
                select(NationalityDistribution)
                .where(NationalityDistribution.budget_version_id == version_id)
                .options(
                    selectinload(NationalityDistribution.level).selectinload(
                        AcademicLevel.cycle
                    ),
                )
                .join(AcademicLevel, NationalityDistribution.level_id == AcademicLevel.id)
                .order_by(AcademicLevel.sort_order)
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve nationality distributions",
                version_id=str(version_id),
                error=str(e),
            )
            raise ServiceException(
                f"Failed to retrieve distributions: {e}",
                status_code=500,
            ) from e

    async def bulk_upsert_distributions(
        self,
        version_id: uuid.UUID,
        distributions: list[dict],
        user_id: uuid.UUID | None = None,
    ) -> list[NationalityDistribution]:
        """
        Bulk upsert nationality distributions for a budget version.

        Validates that percentages sum to 100% for each level before saving.

        Args:
            version_id: Budget version UUID
            distributions: List of distribution dicts with level_id and percentages
            user_id: User ID for audit trail

        Returns:
            List of upserted NationalityDistribution instances

        Raises:
            ValidationError: If percentages don't sum to 100%
            ServiceException: If database operation fails
        """
        # Validate each distribution sums to 100%
        for dist in distributions:
            total = (
                Decimal(str(dist.get("french_pct", 0)))
                + Decimal(str(dist.get("saudi_pct", 0)))
                + Decimal(str(dist.get("other_pct", 0)))
            )
            if total != Decimal("100"):
                raise ValidationError(
                    f"Percentages must sum to 100%, got {total}%",
                    field="distributions",
                    details={"level_id": str(dist.get("level_id")), "total": str(total)},
                )

        try:
            results = []
            for dist_data in distributions:
                level_id = dist_data["level_id"]

                # Check if distribution exists
                query = select(NationalityDistribution).where(
                    and_(
                        NationalityDistribution.budget_version_id == version_id,
                        NationalityDistribution.level_id == level_id,
                    )
                )
                result = await self.session.execute(query)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.french_pct = Decimal(str(dist_data["french_pct"]))
                    existing.saudi_pct = Decimal(str(dist_data["saudi_pct"]))
                    existing.other_pct = Decimal(str(dist_data["other_pct"]))
                    results.append(existing)
                else:
                    # Create new
                    new_dist = NationalityDistribution(
                        id=uuid.uuid4(),
                        budget_version_id=version_id,
                        level_id=level_id,
                        french_pct=Decimal(str(dist_data["french_pct"])),
                        saudi_pct=Decimal(str(dist_data["saudi_pct"])),
                        other_pct=Decimal(str(dist_data["other_pct"])),
                    )
                    self.session.add(new_dist)
                    results.append(new_dist)

            await self.session.commit()

            # Reload with relationships
            return await self.get_distributions(version_id)

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Failed to upsert distributions",
                version_id=str(version_id),
                error=str(e),
            )
            raise ServiceException(
                f"Failed to upsert distributions: {e}",
                status_code=500,
            ) from e

    async def get_enrollment_totals_by_level(
        self, version_id: uuid.UUID
    ) -> list[dict]:
        """
        Get enrollment totals aggregated by level (summing across nationalities).

        Args:
            version_id: Budget version UUID

        Returns:
            List of dicts with level_id and total_students
        """
        try:
            query = (
                select(
                    EnrollmentPlan.level_id,
                    func.sum(EnrollmentPlan.student_count).label("total_students"),
                )
                .where(
                    and_(
                        EnrollmentPlan.budget_version_id == version_id,
                        EnrollmentPlan.deleted_at.is_(None),
                    )
                )
                .group_by(EnrollmentPlan.level_id)
            )
            result = await self.session.execute(query)
            rows = result.all()

            return [
                {"level_id": row.level_id, "total_students": row.total_students or 0}
                for row in rows
            ]
        except SQLAlchemyError as e:
            logger.error(
                "Failed to get enrollment totals",
                version_id=str(version_id),
                error=str(e),
            )
            raise ServiceException(
                f"Failed to get enrollment totals: {e}",
                status_code=500,
            ) from e

    async def bulk_upsert_enrollment_totals(
        self,
        version_id: uuid.UUID,
        totals: list[dict],
        user_id: uuid.UUID | None = None,
    ) -> list[EnrollmentPlan]:
        """
        Bulk upsert enrollment totals by level.

        This replaces the individual level×nationality entries with new totals,
        distributing students according to nationality percentages.

        Args:
            version_id: Budget version UUID
            totals: List of dicts with level_id and total_students
            user_id: User ID for audit trail

        Returns:
            List of enrollment entries

        Raises:
            BusinessRuleError: If capacity exceeded or distributions missing
        """
        # Validate total capacity
        total_students = sum(t.get("total_students", 0) for t in totals)
        effective_capacity = await get_effective_capacity(self.session, version_id)
        if total_students > effective_capacity:
            raise BusinessRuleError(
                "CAPACITY_EXCEEDED",
                f"Total enrollment ({total_students}) exceeds capacity "
                f"({effective_capacity})",
            )

        # Get distributions for calculating breakdown
        distributions = await self.get_distributions(version_id)
        dist_by_level = {d.level_id: d for d in distributions}

        # Get nationality types
        query = select(NationalityType).order_by(NationalityType.sort_order)
        result = await self.session.execute(query)
        nationality_types = {nt.code: nt for nt in result.scalars().all()}

        if not nationality_types:
            raise BusinessRuleError(
                "NO_NATIONALITY_TYPES",
                "Nationality types not configured. Run database migrations.",
            )

        try:
            # Delete existing enrollment for this version
            delete_query = select(EnrollmentPlan).where(
                and_(
                    EnrollmentPlan.budget_version_id == version_id,
                    EnrollmentPlan.deleted_at.is_(None),
                )
            )
            result = await self.session.execute(delete_query)
            existing_enrollments = result.scalars().all()
            for enrollment in existing_enrollments:
                await self.session.delete(enrollment)

            # Create new enrollment entries based on totals and distributions
            new_enrollments = []
            for total_data in totals:
                level_id = total_data["level_id"]
                total = total_data["total_students"]

                if total == 0:
                    continue

                dist = dist_by_level.get(level_id)

                # Calculate breakdown using percentages or default equal split
                if dist:
                    french_count = round(total * dist.french_pct / 100)
                    saudi_count = round(total * dist.saudi_pct / 100)
                    other_count = total - french_count - saudi_count  # Remainder
                else:
                    # Default: equal distribution if no percentages set
                    french_count = total // 3
                    saudi_count = total // 3
                    other_count = total - french_count - saudi_count

                # Create entries for each nationality
                nationality_counts = [
                    ("FRENCH", french_count),
                    ("SAUDI", saudi_count),
                    ("OTHER", other_count),
                ]

                for nat_code, count in nationality_counts:
                    if count <= 0:
                        continue
                    nat_type = nationality_types.get(nat_code)
                    if not nat_type:
                        continue

                    enrollment = EnrollmentPlan(
                        id=uuid.uuid4(),
                        budget_version_id=version_id,
                        level_id=level_id,
                        nationality_type_id=nat_type.id,
                        student_count=count,
                    )
                    self.session.add(enrollment)
                    new_enrollments.append(enrollment)

            await self.session.commit()
            return await self.get_enrollment_plan(version_id)

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Failed to upsert enrollment totals",
                version_id=str(version_id),
                error=str(e),
            )
            raise ServiceException(
                f"Failed to upsert enrollment totals: {e}",
                status_code=500,
            ) from e

    async def get_enrollment_with_distribution(
        self, version_id: uuid.UUID
    ) -> dict:
        """
        Get complete enrollment data with distributions and calculated breakdown.

        Returns a comprehensive view combining:
        - Enrollment totals by level
        - Nationality distribution percentages
        - Calculated breakdown (students by level × nationality)
        - Summary statistics

        Args:
            version_id: Budget version UUID

        Returns:
            Dict with totals, distributions, breakdown, and summary
        """
        # Get all academic levels with cycle info
        query = (
            select(AcademicLevel)
            .options(selectinload(AcademicLevel.cycle))
            .order_by(AcademicLevel.sort_order)
        )
        result = await self.session.execute(query)
        levels = list(result.scalars().all())

        # Get distributions
        distributions = await self.get_distributions(version_id)
        dist_by_level = {d.level_id: d for d in distributions}

        # Get enrollment data
        enrollments = await self.get_enrollment_plan(version_id)

        # Build totals by level
        totals_by_level: dict[uuid.UUID, int] = {}
        enrollment_by_level_nat: dict[tuple, int] = {}

        for enrollment in enrollments:
            level_id = enrollment.level_id
            nat_code = enrollment.nationality_type.code
            totals_by_level[level_id] = (
                totals_by_level.get(level_id, 0) + enrollment.student_count
            )
            enrollment_by_level_nat[(level_id, nat_code)] = enrollment.student_count

        # Build response structures
        totals = []
        breakdown = []

        for level in levels:
            total_students = totals_by_level.get(level.id, 0)
            totals.append({
                "level_id": level.id,
                "total_students": total_students,
            })

            # Get actual counts or calculate from distribution
            french_count = enrollment_by_level_nat.get((level.id, "FRENCH"), 0)
            saudi_count = enrollment_by_level_nat.get((level.id, "SAUDI"), 0)
            other_count = enrollment_by_level_nat.get((level.id, "OTHER"), 0)

            # Get percentages from distribution or calculate from actuals
            dist = dist_by_level.get(level.id)
            if dist:
                french_pct = dist.french_pct
                saudi_pct = dist.saudi_pct
                other_pct = dist.other_pct
            elif total_students > 0:
                french_pct = Decimal(french_count * 100 / total_students).quantize(
                    Decimal("0.01")
                )
                saudi_pct = Decimal(saudi_count * 100 / total_students).quantize(
                    Decimal("0.01")
                )
                other_pct = Decimal("100") - french_pct - saudi_pct
            else:
                french_pct = Decimal("0")
                saudi_pct = Decimal("0")
                other_pct = Decimal("0")

            breakdown.append({
                "level_id": level.id,
                "level_code": level.code,
                "level_name": level.name_fr or level.name_en,
                "cycle_code": level.cycle.code if level.cycle else "",
                "total_students": total_students,
                "french_count": french_count,
                "saudi_count": saudi_count,
                "other_count": other_count,
                "french_pct": french_pct,
                "saudi_pct": saudi_pct,
                "other_pct": other_pct,
            })

        # Build summary
        summary = await self.get_enrollment_summary(version_id)

        return {
            "totals": totals,
            "distributions": [
                {
                    "id": d.id,
                    "budget_version_id": d.budget_version_id,
                    "level_id": d.level_id,
                    "french_pct": d.french_pct,
                    "saudi_pct": d.saudi_pct,
                    "other_pct": d.other_pct,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                }
                for d in distributions
            ],
            "breakdown": breakdown,
            "summary": summary,
        }
