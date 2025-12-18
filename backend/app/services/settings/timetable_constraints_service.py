"""
Timetable Constraints service.

Manages school day structure including:
- Total teaching hours per week
- Maximum hours per day
- Days per week (4-6)
- Break requirements
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TimetableConstraint
from app.services.base import BaseService
from app.services.exceptions import ValidationError


class TimetableConstraintsService:
    """
    Service for managing timetable constraints.

    Timetable constraints define the structure of the school day/week for each level:
    - How many hours of instruction per week
    - Maximum hours per day (for student well-being)
    - Number of school days per week
    - Break requirements

    These constraints are used to validate subject hours don't exceed capacity.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize timetable constraints service.

        Args:
            session: Async database session
        """
        self.session = session
        self._base_service = BaseService(TimetableConstraint, session)

    async def get_timetable_constraints(
        self,
        version_id: uuid.UUID,
    ) -> list[TimetableConstraint]:
        """
        Get timetable constraints for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of TimetableConstraint instances ordered by level
        """
        query = (
            select(TimetableConstraint)
            .where(
                and_(
                    TimetableConstraint.version_id == version_id,
                    TimetableConstraint.deleted_at.is_(None),
                )
            )
            .options(selectinload(TimetableConstraint.level))
            .order_by(TimetableConstraint.level_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_constraint_by_level(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
    ) -> TimetableConstraint | None:
        """
        Get timetable constraint for a specific level.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID

        Returns:
            TimetableConstraint instance or None if not found
        """
        query = select(TimetableConstraint).where(
            and_(
                TimetableConstraint.version_id == version_id,
                TimetableConstraint.level_id == level_id,
                TimetableConstraint.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert_timetable_constraint(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
        total_hours_per_week: Decimal,
        max_hours_per_day: Decimal,
        days_per_week: int,
        requires_lunch_break: bool,
        min_break_duration_minutes: int,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> TimetableConstraint:
        """
        Create or update timetable constraint.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID
            total_hours_per_week: Total student hours per week
            max_hours_per_day: Maximum hours per day
            days_per_week: School days per week (4-6)
            requires_lunch_break: Whether lunch break is required
            min_break_duration_minutes: Minimum break duration (minutes)
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            TimetableConstraint instance

        Raises:
            ValidationError: If max_hours_per_day > total_hours_per_week

        Business Rules:
            - French system: typically 24h/week primary, 26-30h/week secondary
            - max_hours_per_day should not exceed total_hours_per_week
            - days_per_week is typically 4 (maternelle) or 5 (other cycles)
            - Saudi adaptation: Saturday may be a school day
        """
        # Validate cross-field constraint
        if max_hours_per_day > total_hours_per_week:
            raise ValidationError(
                "max_hours_per_day cannot exceed total_hours_per_week"
            )

        # Find existing constraint
        query = select(TimetableConstraint).where(
            and_(
                TimetableConstraint.version_id == version_id,
                TimetableConstraint.level_id == level_id,
                TimetableConstraint.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "version_id": version_id,
            "level_id": level_id,
            "total_hours_per_week": total_hours_per_week,
            "max_hours_per_day": max_hours_per_day,
            "days_per_week": days_per_week,
            "requires_lunch_break": requires_lunch_break,
            "min_break_duration_minutes": min_break_duration_minutes,
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

    async def delete_timetable_constraint(
        self,
        constraint_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        """
        Soft delete a timetable constraint.

        Args:
            constraint_id: Constraint UUID to delete
            user_id: User ID for audit trail

        Returns:
            True if deleted successfully
        """
        await self._base_service.soft_delete(constraint_id, user_id=user_id)
        return True

    async def validate_subject_hours_fit(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
        total_subject_hours: Decimal,
    ) -> tuple[bool, str | None]:
        """
        Validate that total subject hours fit within timetable constraints.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID
            total_subject_hours: Sum of all subject hours for the level

        Returns:
            Tuple of (is_valid, error_message)
        """
        constraint = await self.get_constraint_by_level(version_id, level_id)

        if not constraint:
            return True, None  # No constraint defined, assume valid

        if total_subject_hours > constraint.total_hours_per_week:
            return (
                False,
                f"Total subject hours ({total_subject_hours}h) exceed "
                f"timetable capacity ({constraint.total_hours_per_week}h/week)",
            )

        return True, None
