"""
Reference data service for read-only access to lookup tables.

Provides unified access to:
- Academic cycles and levels
- Subjects
- Teacher categories
- Fee categories
- Nationality types

These are static/semi-static reference tables used across all configuration modules.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AcademicCycle,
    AcademicLevel,
    FeeCategory,
    NationalityType,
    Subject,
    TeacherCategory,
)


class ReferenceDataService:
    """
    Service for accessing reference/lookup data.

    All methods are read-only and do not require a budget version context.
    Used by configuration services, planning services, and APIs.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize reference data service.

        Args:
            session: Async database session
        """
        self.session = session

    # ========================================================================
    # Academic Structure (Cycles & Levels)
    # ========================================================================

    async def get_academic_cycles(self) -> list[AcademicCycle]:
        """
        Get all academic cycles.

        Returns:
            List of AcademicCycle instances ordered by sort_order
        """
        query = select(AcademicCycle).order_by(AcademicCycle.sort_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_academic_levels(
        self,
        cycle_id: uuid.UUID | None = None,
    ) -> list[AcademicLevel]:
        """
        Get all academic levels.

        Args:
            cycle_id: Optional cycle filter

        Returns:
            List of AcademicLevel instances with cycle relationship loaded
        """
        query = select(AcademicLevel).options(selectinload(AcademicLevel.cycle))

        if cycle_id:
            query = query.where(AcademicLevel.cycle_id == cycle_id)

        query = query.order_by(AcademicLevel.sort_order)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_levels_by_cycle_code(
        self,
        cycle_code: str,
    ) -> list[AcademicLevel]:
        """
        Get academic levels for a specific cycle by code.

        Args:
            cycle_code: Cycle code (e.g., 'MAT', 'ELEM', 'COLL', 'LYC')

        Returns:
            List of AcademicLevel instances
        """
        query = (
            select(AcademicLevel)
            .join(AcademicCycle)
            .where(AcademicCycle.code == cycle_code)
            .order_by(AcademicLevel.sort_order)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # Subjects
    # ========================================================================

    async def get_subjects(self, active_only: bool = True) -> list[Subject]:
        """
        Get all subjects.

        Args:
            active_only: If True, only return active subjects (default: True)

        Returns:
            List of Subject instances ordered by name
        """
        query = select(Subject).order_by(Subject.name_en)

        if active_only:
            # Use == True for SQLAlchemy comparison (not Python's 'is' operator)
            query = query.where(Subject.is_active == True)  # noqa: E712

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_subject_by_code(self, code: str) -> Subject | None:
        """
        Get a subject by its code.

        Args:
            code: Subject code (case-insensitive)

        Returns:
            Subject instance or None if not found
        """
        query = select(Subject).where(Subject.code == code.upper())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_subjects_by_category(self, category: str) -> list[Subject]:
        """
        Get subjects filtered by category.

        Args:
            category: Subject category ('core', 'elective', 'specialty', 'local')

        Returns:
            List of Subject instances
        """
        query = (
            select(Subject)
            .where(Subject.category == category, Subject.is_active == True)  # noqa: E712
            .order_by(Subject.name_en)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # Teacher Categories
    # ========================================================================

    async def get_teacher_categories(self) -> list[TeacherCategory]:
        """
        Get all teacher categories.

        Returns:
            List of TeacherCategory instances
        """
        query = select(TeacherCategory)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_teacher_category_by_code(self, code: str) -> TeacherCategory | None:
        """
        Get a teacher category by code.

        Args:
            code: Category code (e.g., 'AEFE_DETACHED', 'LOCAL_CDI')

        Returns:
            TeacherCategory instance or None if not found
        """
        query = select(TeacherCategory).where(TeacherCategory.code == code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ========================================================================
    # Fee Categories
    # ========================================================================

    async def get_fee_categories(self) -> list[FeeCategory]:
        """
        Get all fee categories.

        Returns:
            List of FeeCategory instances
        """
        query = select(FeeCategory)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_fee_category_by_code(self, code: str) -> FeeCategory | None:
        """
        Get a fee category by code.

        Args:
            code: Fee category code (e.g., 'TUITION', 'REGISTRATION', 'DAI')

        Returns:
            FeeCategory instance or None if not found
        """
        query = select(FeeCategory).where(FeeCategory.code == code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ========================================================================
    # Nationality Types
    # ========================================================================

    async def get_nationality_types(self) -> list[NationalityType]:
        """
        Get all nationality types.

        Returns:
            List of NationalityType instances ordered by sort_order
        """
        query = select(NationalityType).order_by(NationalityType.sort_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_nationality_type_by_code(self, code: str) -> NationalityType | None:
        """
        Get a nationality type by code.

        Args:
            code: Nationality code (e.g., 'FRENCH', 'SAUDI', 'OTHER')

        Returns:
            NationalityType instance or None if not found
        """
        query = select(NationalityType).where(NationalityType.code == code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ========================================================================
    # Lookup Helpers (for bulk operations)
    # ========================================================================

    async def get_subject_code_to_id_mapping(self) -> dict[str, uuid.UUID]:
        """
        Get a mapping of subject codes to IDs.

        Useful for bulk operations like template application.

        Returns:
            Dict mapping subject code -> UUID
        """
        subjects = await self.get_subjects()
        return {s.code: s.id for s in subjects}

    async def get_level_code_to_id_mapping(
        self,
        cycle_codes: list[str] | None = None,
    ) -> dict[str, uuid.UUID]:
        """
        Get a mapping of level codes to IDs.

        Args:
            cycle_codes: Optional list of cycle codes to filter by

        Returns:
            Dict mapping level code -> UUID
        """
        query = select(AcademicLevel)

        if cycle_codes:
            query = query.join(AcademicCycle).where(AcademicCycle.code.in_(cycle_codes))

        result = await self.session.execute(query)
        levels = result.scalars().all()
        return {level.code: level.id for level in levels}
