"""
Fee Structure service.

Manages fee amounts per level, nationality type, and fee category.
Fees can be annual (like registration) or trimester-based (like tuition).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.configuration import FeeStructure
from app.services.base import BaseService


class FeeStructureService:
    """
    Service for managing fee structure.

    Fee structure defines the amount charged for each combination of:
    - Academic level (e.g., PS, CP, 6EME)
    - Nationality type (French, Saudi, Other)
    - Fee category (Tuition, Registration, DAI)
    - Trimester (for recurring fees) or None (for annual fees)
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize fee structure service.

        Args:
            session: Async database session
        """
        self.session = session
        self._base_service = BaseService(FeeStructure, session)

    async def get_fee_structure(
        self,
        version_id: uuid.UUID,
    ) -> list[FeeStructure]:
        """
        Get fee structure for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of FeeStructure instances with relationships loaded
        """
        query = (
            select(FeeStructure)
            .where(
                and_(
                    FeeStructure.budget_version_id == version_id,
                    FeeStructure.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(FeeStructure.level),
                selectinload(FeeStructure.nationality_type),
                selectinload(FeeStructure.fee_category),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_fee_by_criteria(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
        nationality_type_id: uuid.UUID,
        fee_category_id: uuid.UUID,
        trimester: int | None = None,
    ) -> FeeStructure | None:
        """
        Get specific fee entry by all criteria.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID
            nationality_type_id: Nationality type UUID
            fee_category_id: Fee category UUID
            trimester: Trimester (1-3) or None for annual fees

        Returns:
            FeeStructure instance or None if not found
        """
        if trimester:
            trimester_condition = FeeStructure.trimester == trimester
        else:
            trimester_condition = FeeStructure.trimester.is_(None)

        query = select(FeeStructure).where(
            and_(
                FeeStructure.budget_version_id == version_id,
                FeeStructure.level_id == level_id,
                FeeStructure.nationality_type_id == nationality_type_id,
                FeeStructure.fee_category_id == fee_category_id,
                trimester_condition,
                FeeStructure.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_fees_by_level(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
    ) -> list[FeeStructure]:
        """
        Get all fees for a specific academic level.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID

        Returns:
            List of FeeStructure instances for the level
        """
        query = (
            select(FeeStructure)
            .where(
                and_(
                    FeeStructure.budget_version_id == version_id,
                    FeeStructure.level_id == level_id,
                    FeeStructure.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(FeeStructure.nationality_type),
                selectinload(FeeStructure.fee_category),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_fee_structure(
        self,
        version_id: uuid.UUID,
        level_id: uuid.UUID,
        nationality_type_id: uuid.UUID,
        fee_category_id: uuid.UUID,
        amount_sar: Decimal,
        trimester: int | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> FeeStructure:
        """
        Create or update fee structure entry.

        Args:
            version_id: Budget version UUID
            level_id: Academic level UUID
            nationality_type_id: Nationality type UUID
            fee_category_id: Fee category UUID
            amount_sar: Fee amount in SAR
            trimester: Trimester (1-3) for tuition, None for annual fees
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            FeeStructure instance

        Business Rules:
            - Tuition fees are typically charged per trimester (T1: 40%, T2: 30%, T3: 30%)
            - Registration and DAI are typically annual (trimester=None)
            - Sibling discounts apply to tuition but not to DAI/registration
        """
        # Find existing entry
        if trimester:
            trimester_condition = FeeStructure.trimester == trimester
        else:
            trimester_condition = FeeStructure.trimester.is_(None)

        query = select(FeeStructure).where(
            and_(
                FeeStructure.budget_version_id == version_id,
                FeeStructure.level_id == level_id,
                FeeStructure.nationality_type_id == nationality_type_id,
                FeeStructure.fee_category_id == fee_category_id,
                trimester_condition,
                FeeStructure.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "budget_version_id": version_id,
            "level_id": level_id,
            "nationality_type_id": nationality_type_id,
            "fee_category_id": fee_category_id,
            "amount_sar": amount_sar,
            "trimester": trimester,
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

    async def delete_fee_structure(
        self,
        fee_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        """
        Soft delete a fee structure entry.

        Args:
            fee_id: Fee structure UUID to delete
            user_id: User ID for audit trail

        Returns:
            True if deleted successfully
        """
        await self._base_service.soft_delete(fee_id, user_id=user_id)
        return True
