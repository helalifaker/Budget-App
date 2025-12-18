"""
Class Size Parameters service.

Manages minimum, target, and maximum class sizes per academic level/cycle.
These parameters are used by the Class Structure module to determine
how many classes to form based on enrollment numbers.
"""

from __future__ import annotations

import uuid
from datetime import UTC

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClassSizeParam
from app.services.base import BaseService
from app.services.exceptions import ValidationError


class ClassSizeService:
    """
    Service for managing class size parameters.

    Class size parameters define:
    - Minimum class size (below which a class won't form)
    - Target class size (ideal number of students)
    - Maximum class size (capacity limit)

    Parameters can be set at the cycle level (default) or overridden per level.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize class size service.

        Args:
            session: Async database session
        """
        self.session = session
        self._base_service = BaseService(ClassSizeParam, session)

    async def get_class_size_params(
        self,
        version_id: uuid.UUID,
    ) -> list[ClassSizeParam]:
        """
        Get class size parameters for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of ClassSizeParam instances
        """
        return await self._base_service.get_all(
            filters={"version_id": version_id}
        )

    async def get_class_size_param_by_level(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
    ) -> ClassSizeParam | None:
        """
        Get class size parameter for a specific level.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID

        Returns:
            ClassSizeParam instance or None if not found
        """
        query = select(ClassSizeParam).where(
            and_(
                ClassSizeParam.version_id == version_id,
                ClassSizeParam.level_id == level_id,
                ClassSizeParam.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_class_size_param_by_cycle(
        self,
        version_id: uuid.UUID,
        cycle_id: uuid.UUID,
    ) -> ClassSizeParam | None:
        """
        Get cycle-level default class size parameter.

        Args:
            version_id: Budget version UUID
            cycle_id: Academic cycle UUID

        Returns:
            ClassSizeParam instance or None if not found
        """
        query = select(ClassSizeParam).where(
            and_(
                ClassSizeParam.version_id == version_id,
                ClassSizeParam.cycle_id == cycle_id,
                ClassSizeParam.level_id.is_(None),
                ClassSizeParam.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert_class_size_param(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID | None,
        cycle_id: uuid.UUID | None,
        min_class_size: int,
        target_class_size: int,
        max_class_size: int,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> ClassSizeParam:
        """
        Create or update class size parameter.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID (None for cycle default)
            cycle_id: Academic cycle UUID (None for level-specific)
            min_class_size: Minimum class size
            target_class_size: Target class size
            max_class_size: Maximum class size
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            ClassSizeParam instance

        Raises:
            ValidationError: If parameters are invalid

        Business Rules:
            - min < target <= max must hold
            - Either level_id OR cycle_id must be provided (not both)
            - Cycle-level parameters act as defaults
            - Level-level parameters override cycle defaults
        """
        # Validate class size constraints
        if min_class_size >= target_class_size or target_class_size > max_class_size:
            raise ValidationError(
                "Invalid class size parameters. Must satisfy: min < target <= max"
            )

        # Validate exactly one of level_id/cycle_id is provided
        if not level_id and not cycle_id:
            raise ValidationError("Either level_id or cycle_id must be provided")

        if level_id and cycle_id:
            raise ValidationError("Cannot specify both level_id and cycle_id")

        # Find existing parameter
        if level_id:
            query = select(ClassSizeParam).where(
                and_(
                    ClassSizeParam.version_id == version_id,
                    ClassSizeParam.level_id == level_id,
                    ClassSizeParam.deleted_at.is_(None),
                )
            )
        else:
            query = select(ClassSizeParam).where(
                and_(
                    ClassSizeParam.version_id == version_id,
                    ClassSizeParam.cycle_id == cycle_id,
                    ClassSizeParam.level_id.is_(None),
                    ClassSizeParam.deleted_at.is_(None),
                )
            )

        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "version_id": version_id,
            "level_id": level_id,
            "cycle_id": cycle_id,
            "min_class_size": min_class_size,
            "target_class_size": target_class_size,
            "max_class_size": max_class_size,
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

    async def delete_class_size_param(
        self,
        param_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        """
        Soft delete a class size parameter.

        Args:
            param_id: Parameter UUID to delete
            user_id: User ID for audit trail

        Returns:
            True if deleted successfully
        """
        await self._base_service.soft_delete(param_id, user_id=user_id)
        return True

    async def batch_upsert_class_size_params(
        self,
        version_id: uuid.UUID,
        entries: list,
        user_id: uuid.UUID | None = None,
    ):
        """
        Batch create or update class size parameters with optimistic locking.

        Args:
            version_id: Budget version UUID
            entries: List of ClassSizeParamBatchEntry objects
            user_id: User ID for audit trail

        Returns:
            ClassSizeParamBatchResponse with per-entry status

        Optimistic Locking:
            - If entry has updated_at, verify it matches DB before update
            - If mismatch (>1s difference), return conflict status for that entry
            - New entries (no updated_at) are always created
        """

        from app.schemas.configuration import (
            ClassSizeParamBatchResponse,
            ClassSizeParamBatchResponseEntry,
        )

        results: list[ClassSizeParamBatchResponseEntry] = []
        created_count = 0
        updated_count = 0
        conflict_count = 0

        for entry in entries:
            # Validate class size constraints
            if (
                entry.min_class_size >= entry.target_class_size
                or entry.target_class_size > entry.max_class_size
            ):
                conflict_count += 1
                results.append(
                    ClassSizeParamBatchResponseEntry(
                        level_id=entry.level_id,
                        id=None,
                        status="conflict",
                        error="Invalid class size: min < target <= max required",
                        updated_at=None,
                    )
                )
                continue

            # Find existing parameter for this level
            query = select(ClassSizeParam).where(
                and_(
                    ClassSizeParam.version_id == version_id,
                    ClassSizeParam.level_id == entry.level_id,
                    ClassSizeParam.deleted_at.is_(None),
                )
            )
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()

            data = {
                "version_id": version_id,
                "level_id": entry.level_id,
                "cycle_id": None,
                "min_class_size": entry.min_class_size,
                "target_class_size": entry.target_class_size,
                "max_class_size": entry.max_class_size,
                "notes": entry.notes,
            }

            if existing:
                # Optimistic locking check
                if entry.updated_at is not None:
                    # Compare timestamps (allow 1 second tolerance for precision)
                    db_updated_at = existing.updated_at
                    expected_updated_at = entry.updated_at

                    # Ensure both are timezone-aware for comparison
                    if db_updated_at.tzinfo is None:
                        db_updated_at = db_updated_at.replace(tzinfo=UTC)
                    if expected_updated_at.tzinfo is None:
                        expected_updated_at = expected_updated_at.replace(
                            tzinfo=UTC
                        )

                    time_diff = abs(
                        (db_updated_at - expected_updated_at).total_seconds()
                    )
                    if time_diff > 1:
                        # Conflict detected
                        conflict_count += 1
                        results.append(
                            ClassSizeParamBatchResponseEntry(
                                level_id=entry.level_id,
                                id=existing.id,
                                status="conflict",
                                error=f"Record modified since fetch. Expected: {expected_updated_at.isoformat()}, Current: {db_updated_at.isoformat()}",
                                updated_at=db_updated_at,
                            )
                        )
                        continue

                # Update existing
                updated = await self._base_service.update(
                    existing.id,
                    data,
                    user_id=user_id,
                )
                updated_count += 1
                results.append(
                    ClassSizeParamBatchResponseEntry(
                        level_id=entry.level_id,
                        id=updated.id,
                        status="updated",
                        updated_at=updated.updated_at,
                    )
                )
            else:
                # Create new
                created = await self._base_service.create(data, user_id=user_id)
                created_count += 1
                results.append(
                    ClassSizeParamBatchResponseEntry(
                        level_id=entry.level_id,
                        id=created.id,
                        status="created",
                        updated_at=created.updated_at,
                    )
                )

        # Commit all changes in single transaction
        await self.session.commit()

        return ClassSizeParamBatchResponse(
            created_count=created_count,
            updated_count=updated_count,
            conflict_count=conflict_count,
            entries=results,
        )
