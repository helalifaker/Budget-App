"""Shared helpers for resolving school capacity per budget version."""

from __future__ import annotations

import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EnrollmentProjectionConfig

DEFAULT_SCHOOL_CAPACITY = 1850


async def get_effective_capacity(session: AsyncSession, version_id: uuid.UUID) -> int:
    """
    Return per-version capacity if a projection config exists, else default.

    Source of truth: enrollment_projection_configs.school_max_capacity.
    """
    query = select(EnrollmentProjectionConfig.school_max_capacity).where(
        and_(
            EnrollmentProjectionConfig.version_id == version_id,
            EnrollmentProjectionConfig.deleted_at.is_(None),
        )
    )
    capacity = (await session.execute(query)).scalar_one_or_none()
    return int(capacity) if capacity else DEFAULT_SCHOOL_CAPACITY

