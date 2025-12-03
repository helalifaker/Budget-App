"""
Enrollment service for managing enrollment planning and projections.

Handles CRUD operations for enrollment plans and integrates with the
enrollment projection engine for growth scenarios and capacity validation.
"""

import uuid
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.engine.enrollment import (
    EnrollmentGrowthScenario,
    EnrollmentInput,
    EnrollmentProjectionResult,
    calculate_enrollment_projection,
)
from app.models.configuration import AcademicLevel, NationalityType
from app.models.planning import EnrollmentPlan
from app.services.base import BaseService
from app.services.exceptions import (
    BusinessRuleError,
    ValidationError,
)


class EnrollmentService:
    """
    Service for enrollment planning operations.

    Provides business logic for enrollment management, projection calculations,
    and capacity validation.
    """

    EFIR_MAX_CAPACITY = 1875

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

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads level, cycle, nationality_type, and audit fields
            - Leverages idx_enrollment_version index
        """
        query = (
            select(EnrollmentPlan)
            .join(EnrollmentPlan.level)
            .join(EnrollmentPlan.nationality_type)
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
                AcademicLevel.sort_order,
                NationalityType.sort_order,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

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

        capacity_utilization = Decimal(
            (total_students / self.EFIR_MAX_CAPACITY) * 100
            if self.EFIR_MAX_CAPACITY > 0
            else 0
        ).quantize(Decimal("0.01"))

        return {
            "total_students": total_students,
            "by_level": by_level,
            "by_cycle": by_cycle,
            "by_nationality": by_nationality,
            "capacity_utilization": capacity_utilization,
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
            if final_year_projection.projected_enrollment > self.EFIR_MAX_CAPACITY / 10:
                projection_result.capacity_exceeded = True

            projections.append(projection_result)

        total_final_year = sum(
            p.projections[-1].projected_enrollment for p in projections
        )
        if total_final_year > self.EFIR_MAX_CAPACITY:
            raise BusinessRuleError(
                "CAPACITY_EXCEEDED",
                f"Projected enrollment ({total_final_year}) exceeds school capacity "
                f"({self.EFIR_MAX_CAPACITY}) in year {years_to_project}",
                details={
                    "projected_total": total_final_year,
                    "max_capacity": self.EFIR_MAX_CAPACITY,
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

        if new_total > self.EFIR_MAX_CAPACITY:
            raise BusinessRuleError(
                "CAPACITY_EXCEEDED",
                f"Total enrollment ({new_total}) would exceed school capacity "
                f"({self.EFIR_MAX_CAPACITY})",
                details={
                    "current_total": current_total,
                    "additional_students": additional_students,
                    "new_total": new_total,
                    "max_capacity": self.EFIR_MAX_CAPACITY,
                },
            )
