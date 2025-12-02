"""
DHG (Dotation Horaire Globale) service for teacher workforce planning.

Handles the complete DHG workflow:
1. Calculate DHG hours from class structure and subject hours matrix
2. Calculate teacher FTE requirements from DHG hours
3. Manage teacher allocations (TRMD)
4. Perform gap analysis (besoins vs moyens)

This is the core calculation engine for secondary teacher workforce planning.
"""

import uuid
from decimal import Decimal
from math import ceil

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import cache_dhg_calculation
from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    Subject,
    SubjectHoursMatrix,
)
from app.models.planning import (
    ClassStructure,
    DHGSubjectHours,
    DHGTeacherRequirement,
    TeacherAllocation,
)
from app.services.base import BaseService
from app.services.exceptions import (
    BusinessRuleError,
    ValidationError,
)


class DHGService:
    """
    Service for DHG workforce planning operations.

    Provides business logic for DHG hours calculation, FTE requirements,
    teacher allocations, and TRMD gap analysis.
    """

    SECONDARY_STANDARD_HOURS = Decimal("18.00")
    PRIMARY_STANDARD_HOURS = Decimal("24.00")

    def __init__(self, session: AsyncSession):
        """
        Initialize DHG service.

        Args:
            session: Async database session
        """
        self.session = session
        self.subject_hours_service = BaseService(DHGSubjectHours, session)
        self.teacher_requirement_service = BaseService(DHGTeacherRequirement, session)
        self.teacher_allocation_service = BaseService(TeacherAllocation, session)

    async def get_dhg_subject_hours(
        self, version_id: uuid.UUID
    ) -> list[DHGSubjectHours]:
        """
        Get DHG subject hours for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of DHGSubjectHours instances with relationships loaded

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads subject, level, cycle, budget_version, and audit fields
            - Leverages idx_dhg_subject_hours_version index
        """
        query = (
            select(DHGSubjectHours)
            .join(DHGSubjectHours.level)
            .join(DHGSubjectHours.subject)
            .where(
                and_(
                    DHGSubjectHours.budget_version_id == version_id,
                    DHGSubjectHours.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(DHGSubjectHours.subject),
                selectinload(DHGSubjectHours.level).selectinload(AcademicLevel.cycle),
                selectinload(DHGSubjectHours.budget_version),
            )
            .order_by(
                AcademicLevel.sort_order,
                Subject.code,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    @cache_dhg_calculation(ttl="1h")
    async def calculate_dhg_subject_hours(
        self,
        budget_version_id: uuid.UUID,
        level_id: uuid.UUID | None = None,
        recalculate_all: bool = True,
        user_id: uuid.UUID | None = None,
    ) -> list[DHGSubjectHours]:
        """
        Calculate DHG subject hours from class structure and subject hours matrix.

        Formula:
            total_hours_per_week = classes × hours_per_class_per_week
            If is_split: total_hours_per_week × 2

        Results are cached for 1 hour per budget version and level.

        Args:
            budget_version_id: Budget version UUID (used as cache key)
            level_id: Optional level ID to filter calculation (used as cache key)
            recalculate_all: Whether to recalculate all or only changed ones
            user_id: User ID for audit trail

        Returns:
            List of calculated DHGSubjectHours instances

        Raises:
            BusinessRuleError: If missing required data
        """
        # Maintain compatibility with existing code
        version_id = budget_version_id
        class_structures = await self._get_class_structures(version_id)
        if not class_structures:
            raise BusinessRuleError(
                "NO_CLASS_STRUCTURE",
                "Cannot calculate DHG hours without class structure data",
            )

        subject_hours_matrix = await self._get_subject_hours_matrix(version_id)
        if not subject_hours_matrix:
            raise BusinessRuleError(
                "NO_SUBJECT_HOURS_MATRIX",
                "Cannot calculate DHG hours without subject hours matrix",
            )

        classes_by_level = {cs.level_id: cs.number_of_classes for cs in class_structures}

        matrix_by_subject_level = {
            (shm.subject_id, shm.level_id): shm for shm in subject_hours_matrix
        }

        existing_dhg_hours = await self.get_dhg_subject_hours(version_id)
        existing_by_subject_level = {
            (dh.subject_id, dh.level_id): dh for dh in existing_dhg_hours
        }

        results = []

        for (subject_id, level_id), matrix_entry in matrix_by_subject_level.items():
            number_of_classes = classes_by_level.get(level_id)
            if not number_of_classes:
                continue

            hours_per_class = matrix_entry.hours_per_week
            is_split = matrix_entry.is_split

            total_hours = Decimal(number_of_classes) * hours_per_class
            if is_split:
                total_hours *= Decimal("2.00")

            total_hours = total_hours.quantize(Decimal("0.01"))

            data = {
                "budget_version_id": version_id,
                "subject_id": subject_id,
                "level_id": level_id,
                "number_of_classes": number_of_classes,
                "hours_per_class_per_week": hours_per_class,
                "total_hours_per_week": total_hours,
                "is_split": is_split,
            }

            key = (subject_id, level_id)
            if key in existing_by_subject_level:
                existing = existing_by_subject_level[key]
                result = await self.subject_hours_service.update(
                    existing.id,
                    data,
                    user_id=user_id,
                )
            else:
                result = await self.subject_hours_service.create(data, user_id=user_id)

            results.append(result)

        return results

    async def get_teacher_requirements(
        self, version_id: uuid.UUID
    ) -> list[DHGTeacherRequirement]:
        """
        Get teacher FTE requirements for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of DHGTeacherRequirement instances with relationships loaded

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads subject, budget_version, and audit fields
            - Leverages idx_dhg_teacher_reqs_version index
        """
        query = (
            select(DHGTeacherRequirement)
            .join(DHGTeacherRequirement.subject)  # Join for ORDER BY
            .where(
                and_(
                    DHGTeacherRequirement.budget_version_id == version_id,
                    DHGTeacherRequirement.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(DHGTeacherRequirement.subject),
                selectinload(DHGTeacherRequirement.budget_version),
            )
            .order_by(Subject.code)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def calculate_teacher_requirements(
        self,
        version_id: uuid.UUID,
        recalculate_all: bool = True,
        user_id: uuid.UUID | None = None,
    ) -> list[DHGTeacherRequirement]:
        """
        Calculate teacher FTE requirements from DHG subject hours.

        Formula (Secondary):
            simple_fte = total_hours_per_week / 18
            rounded_fte = CEILING(simple_fte)
            hsa_hours = MAX(0, total_hours - (rounded_fte × 18))

        Formula (Primary):
            simple_fte = total_hours_per_week / 24
            rounded_fte = CEILING(simple_fte)

        Args:
            version_id: Budget version UUID
            recalculate_all: Whether to recalculate all or only changed ones
            user_id: User ID for audit trail

        Returns:
            List of calculated DHGTeacherRequirement instances

        Raises:
            BusinessRuleError: If missing required data
        """
        dhg_subject_hours = await self.get_dhg_subject_hours(version_id)
        if not dhg_subject_hours:
            raise BusinessRuleError(
                "NO_DHG_HOURS",
                "Cannot calculate teacher requirements without DHG subject hours",
            )

        hours_by_subject: dict[uuid.UUID, list[DHGSubjectHours]] = {}
        for dhg_hour in dhg_subject_hours:
            if dhg_hour.subject_id not in hours_by_subject:
                hours_by_subject[dhg_hour.subject_id] = []
            hours_by_subject[dhg_hour.subject_id].append(dhg_hour)

        existing_requirements = await self.get_teacher_requirements(version_id)
        existing_by_subject = {tr.subject_id: tr for tr in existing_requirements}

        results = []

        for subject_id, subject_hours_list in hours_by_subject.items():
            total_hours_per_week = sum(
                sh.total_hours_per_week for sh in subject_hours_list
            )

            first_entry = subject_hours_list[0]
            is_secondary = first_entry.level.is_secondary

            standard_hours = (
                self.SECONDARY_STANDARD_HOURS
                if is_secondary
                else self.PRIMARY_STANDARD_HOURS
            )

            simple_fte = (total_hours_per_week / standard_hours).quantize(
                Decimal("0.01")
            )
            rounded_fte = ceil(simple_fte)

            hsa_hours = max(
                Decimal("0.00"),
                total_hours_per_week - (Decimal(rounded_fte) * standard_hours),
            ).quantize(Decimal("0.01"))

            data = {
                "budget_version_id": version_id,
                "subject_id": subject_id,
                "total_hours_per_week": total_hours_per_week,
                "standard_teaching_hours": standard_hours,
                "simple_fte": simple_fte,
                "rounded_fte": rounded_fte,
                "hsa_hours": hsa_hours,
            }

            if subject_id in existing_by_subject:
                existing = existing_by_subject[subject_id]
                result = await self.teacher_requirement_service.update(
                    existing.id,
                    data,
                    user_id=user_id,
                )
            else:
                result = await self.teacher_requirement_service.create(
                    data, user_id=user_id
                )

            results.append(result)

        return results

    async def get_teacher_allocations(
        self, version_id: uuid.UUID
    ) -> list[TeacherAllocation]:
        """
        Get teacher allocations for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of TeacherAllocation instances with relationships loaded

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads subject, cycle, category, budget_version, and audit fields
            - Leverages idx_teacher_allocations_version index
        """
        query = (
            select(TeacherAllocation)
            .join(TeacherAllocation.subject)  # Join for ORDER BY
            .join(TeacherAllocation.cycle)  # Join for ORDER BY
            .where(
                and_(
                    TeacherAllocation.budget_version_id == version_id,
                    TeacherAllocation.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(TeacherAllocation.subject),
                selectinload(TeacherAllocation.cycle),
                selectinload(TeacherAllocation.category),
                selectinload(TeacherAllocation.budget_version),
            )
            .order_by(
                Subject.code,
                AcademicCycle.sort_order,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_teacher_allocation(
        self,
        version_id: uuid.UUID,
        subject_id: uuid.UUID,
        cycle_id: uuid.UUID,
        category_id: uuid.UUID,
        fte_count: Decimal,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> TeacherAllocation:
        """
        Create teacher allocation entry.

        Args:
            version_id: Budget version UUID
            subject_id: Subject UUID
            cycle_id: Academic cycle UUID
            category_id: Teacher category UUID
            fte_count: Number of FTE allocated
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            Created TeacherAllocation instance

        Raises:
            ValidationError: If validation fails
        """
        if fte_count <= 0:
            raise ValidationError(
                "FTE count must be greater than 0", field="fte_count"
            )

        query = select(TeacherAllocation).where(
            and_(
                TeacherAllocation.budget_version_id == version_id,
                TeacherAllocation.subject_id == subject_id,
                TeacherAllocation.cycle_id == cycle_id,
                TeacherAllocation.category_id == category_id,
                TeacherAllocation.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValidationError(
                "Teacher allocation already exists for this subject/cycle/category combination",
                details={
                    "subject_id": str(subject_id),
                    "cycle_id": str(cycle_id),
                    "category_id": str(category_id),
                },
            )

        return await self.teacher_allocation_service.create(
            {
                "budget_version_id": version_id,
                "subject_id": subject_id,
                "cycle_id": cycle_id,
                "category_id": category_id,
                "fte_count": fte_count,
                "notes": notes,
            },
            user_id=user_id,
        )

    async def update_teacher_allocation(
        self,
        allocation_id: uuid.UUID,
        fte_count: Decimal | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> TeacherAllocation:
        """
        Update teacher allocation entry.

        Args:
            allocation_id: Teacher allocation UUID
            fte_count: Updated FTE count
            notes: Updated notes
            user_id: User ID for audit trail

        Returns:
            Updated TeacherAllocation instance

        Raises:
            NotFoundError: If allocation not found
            ValidationError: If validation fails
        """
        update_data = {}

        if fte_count is not None:
            if fte_count <= 0:
                raise ValidationError(
                    "FTE count must be greater than 0", field="fte_count"
                )
            update_data["fte_count"] = fte_count

        if notes is not None:
            update_data["notes"] = notes

        return await self.teacher_allocation_service.update(
            allocation_id,
            update_data,
            user_id=user_id,
        )

    async def delete_teacher_allocation(
        self,
        allocation_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        """
        Delete teacher allocation entry.

        Args:
            allocation_id: Teacher allocation UUID
            user_id: User ID for audit trail

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If allocation not found
        """
        return await self.teacher_allocation_service.delete(allocation_id)

    async def bulk_update_allocations(
        self,
        version_id: uuid.UUID,
        allocations: list[dict],
        user_id: uuid.UUID | None = None,
    ) -> list[TeacherAllocation]:
        """
        Bulk create/update teacher allocations.

        Args:
            version_id: Budget version UUID
            allocations: List of allocation dictionaries with keys:
                subject_id, cycle_id, category_id, fte_count, notes (optional)
            user_id: User ID for audit trail

        Returns:
            List of created/updated TeacherAllocation instances

        Raises:
            ValidationError: If validation fails
        """
        existing_allocations = await self.get_teacher_allocations(version_id)
        existing_map = {
            (a.subject_id, a.cycle_id, a.category_id): a
            for a in existing_allocations
        }

        results = []

        for allocation_data in allocations:
            subject_id = allocation_data["subject_id"]
            cycle_id = allocation_data["cycle_id"]
            category_id = allocation_data["category_id"]
            fte_count = allocation_data["fte_count"]
            notes = allocation_data.get("notes")

            if fte_count <= 0:
                raise ValidationError(
                    f"FTE count must be greater than 0 for allocation: {allocation_data}",
                    field="fte_count",
                )

            key = (subject_id, cycle_id, category_id)

            if key in existing_map:
                existing = existing_map[key]
                result = await self.teacher_allocation_service.update(
                    existing.id,
                    {
                        "fte_count": fte_count,
                        "notes": notes,
                    },
                    user_id=user_id,
                )
            else:
                result = await self.teacher_allocation_service.create(
                    {
                        "budget_version_id": version_id,
                        "subject_id": subject_id,
                        "cycle_id": cycle_id,
                        "category_id": category_id,
                        "fte_count": fte_count,
                        "notes": notes,
                    },
                    user_id=user_id,
                )

            results.append(result)

        return results

    async def get_trmd_gap_analysis(self, version_id: uuid.UUID) -> dict:
        """
        Perform TRMD gap analysis (besoins vs moyens).

        TRMD Logic:
            Besoins (Need) = DHGTeacherRequirement.rounded_fte
            Moyens (Available) = SUM(TeacherAllocation.fte_count)
            Déficit = Besoins - Moyens

        Args:
            version_id: Budget version UUID

        Returns:
            Dictionary with gap analysis:
            - budget_version_id
            - total_besoins: Total teacher needs
            - total_moyens: Total available teachers
            - total_deficit: Total gap
            - by_subject: List of gap analyses by subject
            - by_cycle: Deficit breakdown by cycle

        Raises:
            BusinessRuleError: If missing required data
        """
        requirements = await self.get_teacher_requirements(version_id)
        if not requirements:
            raise BusinessRuleError(
                "NO_TEACHER_REQUIREMENTS",
                "Cannot perform TRMD analysis without teacher requirements",
            )

        allocations = await self.get_teacher_allocations(version_id)

        allocations_by_subject: dict[uuid.UUID, Decimal] = {}
        for allocation in allocations:
            subject_id = allocation.subject_id
            if subject_id not in allocations_by_subject:
                allocations_by_subject[subject_id] = Decimal("0.00")
            allocations_by_subject[subject_id] += allocation.fte_count

        by_subject = []
        total_besoins = Decimal("0.00")
        total_moyens = Decimal("0.00")
        total_deficit = Decimal("0.00")

        for requirement in requirements:
            subject_id = requirement.subject_id
            besoins = Decimal(requirement.rounded_fte)
            moyens = allocations_by_subject.get(subject_id, Decimal("0.00"))
            deficit = besoins - moyens

            total_besoins += besoins
            total_moyens += moyens
            total_deficit += deficit

            status = "deficit" if deficit > 0 else ("surplus" if deficit < 0 else "balanced")

            by_subject.append({
                "subject_id": subject_id,
                "subject_code": requirement.subject.code,
                "subject_name": requirement.subject.name_en,
                "cycle_id": None,
                "cycle_code": None,
                "besoins_fte": besoins,
                "moyens_fte": moyens,
                "deficit_fte": deficit,
                "status": status,
            })

        allocations_by_cycle: dict[str, Decimal] = {}
        for allocation in allocations:
            cycle_code = allocation.cycle.code
            if cycle_code not in allocations_by_cycle:
                allocations_by_cycle[cycle_code] = Decimal("0.00")
            allocations_by_cycle[cycle_code] += allocation.fte_count

        by_cycle = {
            cycle_code: float(allocations_by_cycle.get(cycle_code, Decimal("0.00")))
            for cycle_code in allocations_by_cycle.keys()
        }

        return {
            "budget_version_id": version_id,
            "total_besoins": float(total_besoins),
            "total_moyens": float(total_moyens),
            "total_deficit": float(total_deficit),
            "by_subject": by_subject,
            "by_cycle": by_cycle,
        }

    async def _get_class_structures(
        self, version_id: uuid.UUID
    ) -> list[ClassStructure]:
        """
        Get class structures for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of ClassStructure instances

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads level and cycle relationships
            - Leverages idx_class_structure_version index
        """
        query = (
            select(ClassStructure)
            .where(
                and_(
                    ClassStructure.budget_version_id == version_id,
                    ClassStructure.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(ClassStructure.level).selectinload(AcademicLevel.cycle)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_subject_hours_matrix(
        self, version_id: uuid.UUID
    ) -> list[SubjectHoursMatrix]:
        """
        Get subject hours matrix for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of SubjectHoursMatrix instances

        Performance Notes:
            - Uses selectinload for N+1 prevention
            - Eager loads subject and level relationships
            - Leverages idx_subject_hours_version index
        """
        query = (
            select(SubjectHoursMatrix)
            .where(
                and_(
                    SubjectHoursMatrix.budget_version_id == version_id,
                    SubjectHoursMatrix.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(SubjectHoursMatrix.subject),
                selectinload(SubjectHoursMatrix.level),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
