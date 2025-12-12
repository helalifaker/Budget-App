"""
Subject Hours service.

Manages subject hours matrix configuration including hours per week
for each subject/level combination in a budget version.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    Subject,
    SubjectHoursMatrix,
)
from app.services.base import BaseService
from app.services.exceptions import ValidationError

if TYPE_CHECKING:
    from app.schemas.configuration import (
        SubjectHoursBatchResponse,
        SubjectHoursEntry,
        SubjectHoursMatrixResponse,
    )


class SubjectHoursService:
    """
    Service for managing subject hours matrix.

    The subject hours matrix defines how many hours per week each subject
    is taught at each academic level. This is fundamental to DHG calculation
    and teacher FTE planning.

    Key Features:
        - Hours per week configuration (0-12 hours)
        - Support for split classes (half-size groups)
        - Batch upsert for efficient updates
        - Matrix view by academic cycle

    Business Rules:
        - Hours must be between 0 and 12 per week
        - Each (subject, level) combination is unique per budget version
        - Split classes multiply teaching hours but not student hours
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize subject hours service.

        Args:
            session: Async database session
        """
        self.session = session
        self._base_service = BaseService(SubjectHoursMatrix, session)
        self._cycle_service = BaseService(AcademicCycle, session)
        self._level_service = BaseService(AcademicLevel, session)
        self._subject_service = BaseService(Subject, session)

    async def get_subject_hours_matrix(
        self,
        version_id: uuid.UUID,
    ) -> list[SubjectHoursMatrix]:
        """
        Get subject hours matrix for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of SubjectHoursMatrix instances with eager-loaded
            subject and level relationships
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

    async def upsert_subject_hours(
        self,
        version_id: uuid.UUID,
        subject_id: uuid.UUID,
        level_id: uuid.UUID,
        hours_per_week: Decimal,
        is_split: bool = False,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> SubjectHoursMatrix:
        """
        Create or update subject hours configuration.

        Args:
            version_id: Budget version UUID
            subject_id: Subject UUID
            level_id: Academic level UUID
            hours_per_week: Hours per week per class
            is_split: Whether classes are split (half-size groups)
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            SubjectHoursMatrix instance

        Raises:
            ValidationError: If hours are invalid (not between 0 and 12)
        """
        if hours_per_week <= 0 or hours_per_week > 12:
            raise ValidationError(
                "Hours per week must be between 0 and 12",
                field="hours_per_week",
            )

        # Find existing entry
        query = select(SubjectHoursMatrix).where(
            and_(
                SubjectHoursMatrix.budget_version_id == version_id,
                SubjectHoursMatrix.subject_id == subject_id,
                SubjectHoursMatrix.level_id == level_id,
                SubjectHoursMatrix.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "budget_version_id": version_id,
            "subject_id": subject_id,
            "level_id": level_id,
            "hours_per_week": hours_per_week,
            "is_split": is_split,
            "notes": notes,
        }

        if existing:
            return await self._base_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self._base_service.create(data, user_id=user_id)

    async def batch_upsert_subject_hours(
        self,
        version_id: uuid.UUID,
        entries: list[SubjectHoursEntry],
        user_id: uuid.UUID | None = None,
    ) -> SubjectHoursBatchResponse:
        """
        Batch create, update, or delete subject hours entries.

        Entries with hours_per_week=None will be deleted (soft delete).

        Args:
            version_id: Budget version UUID
            entries: List of subject hours entries
            user_id: User ID for audit trail

        Returns:
            SubjectHoursBatchResponse with counts and errors
        """
        from app.schemas.configuration import SubjectHoursBatchResponse

        created_count = 0
        updated_count = 0
        deleted_count = 0
        errors: list[str] = []

        for entry in entries:
            try:
                # Find existing entry
                query = select(SubjectHoursMatrix).where(
                    and_(
                        SubjectHoursMatrix.budget_version_id == version_id,
                        SubjectHoursMatrix.subject_id == entry.subject_id,
                        SubjectHoursMatrix.level_id == entry.level_id,
                        SubjectHoursMatrix.deleted_at.is_(None),
                    )
                )
                result = await self.session.execute(query)
                existing = result.scalar_one_or_none()

                # Handle deletion
                if entry.hours_per_week is None:
                    if existing:
                        await self._base_service.soft_delete(existing.id, user_id)
                        deleted_count += 1
                    continue

                # Validate hours range
                if entry.hours_per_week < 0 or entry.hours_per_week > 12:
                    errors.append(
                        f"Invalid hours for subject {entry.subject_id}, level {entry.level_id}: "
                        f"must be 0-12, got {entry.hours_per_week}"
                    )
                    continue

                data = {
                    "budget_version_id": version_id,
                    "subject_id": entry.subject_id,
                    "level_id": entry.level_id,
                    "hours_per_week": entry.hours_per_week,
                    "is_split": entry.is_split,
                    "notes": entry.notes,
                }

                if existing:
                    await self._base_service.update(existing.id, data, user_id=user_id)
                    updated_count += 1
                else:
                    await self._base_service.create(data, user_id=user_id)
                    created_count += 1

            except Exception as e:
                errors.append(
                    f"Error processing subject {entry.subject_id}, level {entry.level_id}: {e!s}"
                )

        return SubjectHoursBatchResponse(
            created_count=created_count,
            updated_count=updated_count,
            deleted_count=deleted_count,
            errors=errors,
        )

    async def get_subject_hours_matrix_by_cycle(
        self,
        version_id: uuid.UUID,
        cycle_code: str | None = None,
    ) -> list[SubjectHoursMatrixResponse]:
        """
        Get subject hours organized as a matrix by cycle.

        Returns all subjects with their hours for each level in the cycle,
        including subjects with no hours configured (empty cells).

        Args:
            version_id: Budget version UUID
            cycle_code: Optional cycle code filter (e.g., 'COLL', 'LYC')

        Returns:
            List of SubjectHoursMatrixResponse (one per cycle)
        """
        from app.schemas.configuration import (
            LevelInfo,
            SubjectHoursMatrixResponse,
            SubjectLevelHours,
            SubjectWithHours,
        )

        # Get cycles
        cycles_query = select(AcademicCycle).order_by(AcademicCycle.sort_order)
        if cycle_code:
            cycles_query = cycles_query.where(AcademicCycle.code == cycle_code)
        cycles_result = await self.session.execute(cycles_query)
        cycles = list(cycles_result.scalars().all())

        # Get all subjects (active only)
        # Note: Subject model doesn't have sort_order, order by category then code
        subjects_query = (
            select(Subject)
            .where(Subject.is_active == True)  # noqa: E712
            .order_by(Subject.category, Subject.code)
        )
        subjects_result = await self.session.execute(subjects_query)
        subjects = list(subjects_result.scalars().all())

        # Get all subject hours for this version
        hours_query = select(SubjectHoursMatrix).where(
            and_(
                SubjectHoursMatrix.budget_version_id == version_id,
                SubjectHoursMatrix.deleted_at.is_(None),
            )
        )
        hours_result = await self.session.execute(hours_query)
        all_hours = list(hours_result.scalars().all())

        # Create hours lookup: (subject_id, level_id) -> SubjectHoursMatrix
        hours_lookup: dict[tuple[uuid.UUID, uuid.UUID], SubjectHoursMatrix] = {
            (h.subject_id, h.level_id): h for h in all_hours
        }

        result: list[SubjectHoursMatrixResponse] = []

        for cycle in cycles:
            # Get levels for this cycle
            levels_query = (
                select(AcademicLevel)
                .where(AcademicLevel.cycle_id == cycle.id)
                .order_by(AcademicLevel.sort_order)
            )
            levels_result = await self.session.execute(levels_query)
            levels = list(levels_result.scalars().all())

            level_infos = [
                LevelInfo(
                    id=level.id,
                    code=level.code,
                    name_en=level.name_en,
                    name_fr=level.name_fr,
                    sort_order=level.sort_order,
                )
                for level in levels
            ]

            # Build subject data with hours
            subjects_with_hours: list[SubjectWithHours] = []
            for subject in subjects:
                # Determine if subject is applicable to this cycle
                # For now, all subjects are applicable to COLL and LYC
                is_applicable = cycle.code in ("COLL", "LYC")

                hours_dict: dict[str, SubjectLevelHours] = {}
                for level in levels:
                    key = (subject.id, level.id)
                    if key in hours_lookup:
                        h = hours_lookup[key]
                        hours_dict[str(level.id)] = SubjectLevelHours(
                            hours_per_week=h.hours_per_week,
                            is_split=h.is_split,
                            notes=h.notes,
                        )
                    else:
                        hours_dict[str(level.id)] = SubjectLevelHours(
                            hours_per_week=None,
                            is_split=False,
                            notes=None,
                        )

                subjects_with_hours.append(
                    SubjectWithHours(
                        id=subject.id,
                        code=subject.code,
                        name_en=subject.name_en,
                        name_fr=subject.name_fr,
                        category=subject.category,
                        is_applicable=is_applicable,
                        hours=hours_dict,
                    )
                )

            result.append(
                SubjectHoursMatrixResponse(
                    cycle_id=cycle.id,
                    cycle_code=cycle.code,
                    cycle_name=cycle.name_en,
                    levels=level_infos,
                    subjects=subjects_with_hours,
                )
            )

        return result

    async def delete_subject_hours(
        self,
        entry_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> None:
        """
        Soft delete a subject hours entry.

        Args:
            entry_id: SubjectHoursMatrix entry UUID
            user_id: User ID for audit trail
        """
        await self._base_service.soft_delete(entry_id, user_id)

    async def get_total_hours_by_level(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
    ) -> Decimal:
        """
        Get total weekly hours for a specific level.

        Useful for validating against timetable constraints.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID

        Returns:
            Total hours per week for the level
        """
        query = select(SubjectHoursMatrix).where(
            and_(
                SubjectHoursMatrix.budget_version_id == version_id,
                SubjectHoursMatrix.level_id == level_id,
                SubjectHoursMatrix.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        entries = result.scalars().all()

        return sum((e.hours_per_week for e in entries), Decimal("0"))
