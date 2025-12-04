"""
Class structure service for managing class formations and ATSEM allocations.

Handles auto-calculation of class structures from enrollment data using
class size parameters, including ATSEM requirements for Maternelle.
"""

import uuid
from decimal import Decimal
from math import ceil

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    ClassSizeParam,
)
from app.models.planning import ClassStructure, EnrollmentPlan
from app.services.base import BaseService
from app.services.exceptions import (
    BusinessRuleError,
    ServiceException,
    ValidationError,
)


class ClassStructureService:
    """
    Service for class structure planning operations.

    Provides business logic for calculating class formations from enrollment
    data, validating class sizes, and managing ATSEM allocations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize class structure service.

        Args:
            session: Async database session
        """
        self.session = session
        self.base_service = BaseService(ClassStructure, session)

    async def get_class_structure(
        self, version_id: uuid.UUID
    ) -> list[ClassStructure]:
        """
        Get class structure for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of ClassStructure instances with relationships loaded

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads level, cycle, budget_version, and audit fields
            - Leverages idx_class_structure_version index

        Raises:
            ServiceException: If database operation fails
        """
        try:
            query = (
                select(ClassStructure)
                .where(
                    and_(
                        ClassStructure.budget_version_id == version_id,
                        ClassStructure.deleted_at.is_(None),
                    )
                )
                .options(
                    selectinload(ClassStructure.level).selectinload(AcademicLevel.cycle),
                    selectinload(ClassStructure.budget_version),
                )
                .order_by(AcademicLevel.sort_order)
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve class structure",
                version_id=str(version_id),
                error=str(e),
                exc_info=True,
            )
            raise ServiceException(
                "Failed to retrieve class structure. Please try again.",
                status_code=500,
                details={"version_id": str(version_id)},
            ) from e

    async def get_class_structure_by_id(
        self, class_structure_id: uuid.UUID
    ) -> ClassStructure:
        """
        Get class structure entry by ID.

        Args:
            class_structure_id: Class structure UUID

        Returns:
            ClassStructure instance

        Raises:
            NotFoundError: If class structure not found
        """
        return await self.base_service.get_by_id(class_structure_id)

    async def calculate_class_structure(
        self,
        version_id: uuid.UUID,
        method: str = "target",
        override_by_level: dict[str, int] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[ClassStructure]:
        """
        Calculate class structures from enrollment data.

        Formula:
            classes = CEILING(total_students / target_class_size)
            avg_class_size = total_students / classes

        Args:
            version_id: Budget version UUID
            method: Calculation method (target, min, max)
            override_by_level: Optional manual overrides by level_id
            user_id: User ID for audit trail

        Returns:
            List of calculated ClassStructure instances

        Raises:
            ValidationError: If invalid parameters
            BusinessRuleError: If validation fails
        """
        if method not in ("target", "min", "max"):
            raise ValidationError(
                f"Invalid calculation method: {method}. Must be: target, min, or max",
                field="method",
            )

        enrollments = await self._get_enrollment_by_level(version_id)

        if not enrollments:
            raise BusinessRuleError(
                "NO_ENROLLMENT_DATA",
                "Cannot calculate class structure without enrollment data",
            )

        class_size_params = await self._get_class_size_params(version_id)

        if not class_size_params:
            raise BusinessRuleError(
                "NO_CLASS_SIZE_PARAMS",
                "Cannot calculate class structure without class size parameters",
            )

        params_by_level = {p.level_id: p for p in class_size_params if p.level_id}
        params_by_cycle = {p.cycle_id: p for p in class_size_params if p.cycle_id}

        existing_structures = await self.get_class_structure(version_id)
        existing_by_level = {cs.level_id: cs for cs in existing_structures}

        results = []

        for level_id, (total_students, level, cycle) in enrollments.items():
            level_id_str = str(level_id)

            if override_by_level and level_id_str in override_by_level:
                number_of_classes = override_by_level[level_id_str]
                calculation_method = "custom"
            else:
                params = params_by_level.get(level_id) or params_by_cycle.get(
                    level.cycle_id
                )

                if not params:
                    raise BusinessRuleError(
                        "MISSING_CLASS_SIZE_PARAMS",
                        f"No class size parameters found for level {level.code}",
                        details={"level_id": str(level_id), "level_code": level.code},
                    )

                if method == "target":
                    divisor = params.target_class_size
                elif method == "min":
                    divisor = params.min_class_size
                else:
                    divisor = params.max_class_size

                number_of_classes = ceil(total_students / divisor)
                calculation_method = method

            if number_of_classes == 0:
                number_of_classes = 1

            avg_class_size = Decimal(total_students / number_of_classes).quantize(
                Decimal("0.01")
            )

            requires_atsem = cycle.requires_atsem
            atsem_count = number_of_classes if requires_atsem else 0

            params = params_by_level.get(level_id) or params_by_cycle.get(
                level.cycle_id
            )
            if params:
                if avg_class_size < params.min_class_size:
                    raise BusinessRuleError(
                        "AVG_BELOW_MIN",
                        f"Average class size ({avg_class_size}) is below minimum "
                        f"({params.min_class_size}) for level {level.code}",
                        details={
                            "level_code": level.code,
                            "avg_class_size": float(avg_class_size),
                            "min_class_size": params.min_class_size,
                        },
                    )
                if avg_class_size > params.max_class_size:
                    raise BusinessRuleError(
                        "AVG_EXCEEDS_MAX",
                        f"Average class size ({avg_class_size}) exceeds maximum "
                        f"({params.max_class_size}) for level {level.code}",
                        details={
                            "level_code": level.code,
                            "avg_class_size": float(avg_class_size),
                            "max_class_size": params.max_class_size,
                        },
                    )

            data = {
                "budget_version_id": version_id,
                "level_id": level_id,
                "total_students": total_students,
                "number_of_classes": number_of_classes,
                "avg_class_size": avg_class_size,
                "requires_atsem": requires_atsem,
                "atsem_count": atsem_count,
                "calculation_method": calculation_method,
            }

            if level_id in existing_by_level:
                existing = existing_by_level[level_id]
                result = await self.base_service.update(
                    existing.id,
                    data,
                    user_id=user_id,
                )
            else:
                result = await self.base_service.create(data, user_id=user_id)

            results.append(result)

        return results

    async def update_class_structure(
        self,
        class_structure_id: uuid.UUID,
        total_students: int | None = None,
        number_of_classes: int | None = None,
        avg_class_size: Decimal | None = None,
        requires_atsem: bool | None = None,
        atsem_count: int | None = None,
        calculation_method: str | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> ClassStructure:
        """
        Update class structure entry.

        Args:
            class_structure_id: Class structure UUID
            total_students: Updated total students
            number_of_classes: Updated number of classes
            avg_class_size: Updated average class size
            requires_atsem: Updated ATSEM requirement
            atsem_count: Updated ATSEM count
            calculation_method: Updated calculation method
            notes: Updated notes
            user_id: User ID for audit trail

        Returns:
            Updated ClassStructure instance

        Raises:
            NotFoundError: If class structure not found
            ValidationError: If validation fails
        """
        class_structure = await self.get_class_structure_by_id(class_structure_id)

        update_data = {}

        if total_students is not None:
            update_data["total_students"] = total_students

        if number_of_classes is not None:
            if number_of_classes <= 0:
                raise ValidationError(
                    "Number of classes must be greater than 0",
                    field="number_of_classes",
                )
            update_data["number_of_classes"] = number_of_classes

        if avg_class_size is not None:
            if avg_class_size <= 0 or avg_class_size > 50:
                raise ValidationError(
                    "Average class size must be between 0 and 50",
                    field="avg_class_size",
                )
            update_data["avg_class_size"] = avg_class_size

        recalc_avg = False
        if (
            total_students is not None and number_of_classes is None
        ) or (
            number_of_classes is not None and total_students is None
        ):
            recalc_avg = True

        if recalc_avg:
            new_students = update_data.get(
                "total_students", class_structure.total_students
            )
            new_classes = update_data.get(
                "number_of_classes", class_structure.number_of_classes
            )
            update_data["avg_class_size"] = Decimal(
                new_students / new_classes
            ).quantize(Decimal("0.01"))

        if requires_atsem is not None:
            update_data["requires_atsem"] = requires_atsem

        if atsem_count is not None:
            if atsem_count < 0:
                raise ValidationError(
                    "ATSEM count must be non-negative", field="atsem_count"
                )
            update_data["atsem_count"] = atsem_count

        if calculation_method is not None:
            update_data["calculation_method"] = calculation_method

        if notes is not None:
            update_data["notes"] = notes

        return await self.base_service.update(
            class_structure_id,
            update_data,
            user_id=user_id,
        )

    async def delete_class_structure(
        self,
        class_structure_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        """
        Delete class structure entry.

        Args:
            class_structure_id: Class structure UUID
            user_id: User ID for audit trail

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If class structure not found
        """
        return await self.base_service.delete(class_structure_id)

    async def _get_enrollment_by_level(
        self, version_id: uuid.UUID
    ) -> dict[uuid.UUID, tuple[int, AcademicLevel, AcademicCycle]]:
        """
        Get total enrollment by level.

        Args:
            version_id: Budget version UUID

        Returns:
            Dictionary mapping level_id to (total_students, level, cycle)

        Performance Notes:
            - Uses aggregation query for enrollment totals (single query)
            - Eager loads levels and cycles in second query
            - Leverages idx_enrollment_version index

        Raises:
            ServiceException: If database operation fails
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
            enrollment_totals = {row.level_id: row.total_students for row in result}

            if not enrollment_totals:
                return {}

            query_levels = (
                select(AcademicLevel)
                .where(AcademicLevel.id.in_(enrollment_totals.keys()))
                .options(selectinload(AcademicLevel.cycle))
            )
            result_levels = await self.session.execute(query_levels)
            levels = {level.id: level for level in result_levels.scalars().all()}

            return {
                level_id: (
                    total_students,
                    levels[level_id],
                    levels[level_id].cycle,
                )
                for level_id, total_students in enrollment_totals.items()
            }
        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve enrollment by level",
                version_id=str(version_id),
                error=str(e),
                exc_info=True,
            )
            raise ServiceException(
                "Failed to retrieve enrollment data. Please try again.",
                status_code=500,
                details={"version_id": str(version_id)},
            ) from e

    async def _get_class_size_params(
        self, version_id: uuid.UUID
    ) -> list[ClassSizeParam]:
        """
        Get class size parameters for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of ClassSizeParam instances

        Raises:
            ServiceException: If database operation fails
        """
        try:
            query = (
                select(ClassSizeParam)
                .where(
                    and_(
                        ClassSizeParam.budget_version_id == version_id,
                        ClassSizeParam.deleted_at.is_(None),
                    )
                )
                .options(
                    selectinload(ClassSizeParam.level),
                    selectinload(ClassSizeParam.cycle),
                )
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve class size parameters",
                version_id=str(version_id),
                error=str(e),
                exc_info=True,
            )
            raise ServiceException(
                "Failed to retrieve class size parameters. Please try again.",
                status_code=500,
                details={"version_id": str(version_id)},
            ) from e
