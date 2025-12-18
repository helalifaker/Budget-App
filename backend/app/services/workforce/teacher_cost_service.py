"""
Teacher Cost Parameters service.

Manages teacher salary, benefits, and contribution costs per category.
Supports both AEFE teachers (PRRD contribution) and local teachers (direct salary).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TeacherCostParam
from app.services.base import BaseService
from app.services.exceptions import ValidationError


class TeacherCostParametersService:
    """
    Service for managing teacher cost parameters.

    Teacher cost parameters define salary and benefit costs for each teacher category:
    - AEFE Detached: PRRD contribution in EUR (converted to SAR at budget rate)
    - AEFE Funded: No cost to school (fully funded by AEFE)
    - Local Teachers: Direct salary in SAR + social charges + benefits

    HSA (Heures Supplémentaires Annuelles) defines overtime rates and limits.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize teacher cost parameters service.

        Args:
            session: Async database session
        """
        self.session = session
        self._base_service = BaseService(TeacherCostParam, session)

    async def get_teacher_cost_params(
        self,
        version_id: uuid.UUID,
    ) -> list[TeacherCostParam]:
        """
        Get teacher cost parameters for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of TeacherCostParam instances with relationships loaded
        """
        query = (
            select(TeacherCostParam)
            .where(
                and_(
                    TeacherCostParam.version_id == version_id,
                    TeacherCostParam.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(TeacherCostParam.category),
                selectinload(TeacherCostParam.cycle),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_teacher_cost_param_by_criteria(
        self,
        version_id: uuid.UUID,
        category_id: uuid.UUID,
        cycle_id: uuid.UUID | None = None,
    ) -> TeacherCostParam | None:
        """
        Get specific teacher cost parameter by category and cycle.

        Args:
            version_id: Budget version UUID
            category_id: Teacher category UUID
            cycle_id: Academic cycle UUID (None for all-cycles default)

        Returns:
            TeacherCostParam instance or None if not found
        """
        if cycle_id:
            cycle_condition = TeacherCostParam.cycle_id == cycle_id
        else:
            cycle_condition = TeacherCostParam.cycle_id.is_(None)

        query = (
            select(TeacherCostParam)
            .where(
                and_(
                    TeacherCostParam.version_id == version_id,
                    TeacherCostParam.category_id == category_id,
                    cycle_condition,
                    TeacherCostParam.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(TeacherCostParam.category),
                selectinload(TeacherCostParam.cycle),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_params_by_category(
        self,
        version_id: uuid.UUID,
        category_id: uuid.UUID,
    ) -> list[TeacherCostParam]:
        """
        Get all teacher cost parameters for a specific category.

        Args:
            version_id: Budget version UUID
            category_id: Teacher category UUID

        Returns:
            List of TeacherCostParam instances (may include cycle-specific params)
        """
        query = (
            select(TeacherCostParam)
            .where(
                and_(
                    TeacherCostParam.version_id == version_id,
                    TeacherCostParam.category_id == category_id,
                    TeacherCostParam.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(TeacherCostParam.cycle),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_teacher_cost_param(
        self,
        version_id: uuid.UUID,
        category_id: uuid.UUID,
        cycle_id: uuid.UUID | None,
        prrd_contribution_eur: Decimal | None,
        avg_salary_sar: Decimal | None,
        social_charges_rate: Decimal,
        benefits_allowance_sar: Decimal,
        hsa_hourly_rate_sar: Decimal,
        max_hsa_hours: Decimal,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> TeacherCostParam:
        """
        Create or update teacher cost parameter.

        Args:
            version_id: Budget version UUID
            category_id: Teacher category UUID (AEFE_DETACHED, AEFE_FUNDED, LOCAL, etc.)
            cycle_id: Academic cycle UUID (None for all cycles)
            prrd_contribution_eur: PRRD contribution (EUR, for AEFE detached teachers)
            avg_salary_sar: Average salary (SAR/year, for local teachers)
            social_charges_rate: Social charges rate (e.g., 0.12 for GOSI 12%)
            benefits_allowance_sar: Benefits/allowances (SAR/year)
            hsa_hourly_rate_sar: HSA hourly rate (SAR)
            max_hsa_hours: Maximum HSA hours per week (typically 2-4)
            notes: Optional notes
            user_id: User ID for audit trail

        Returns:
            TeacherCostParam instance

        Raises:
            ValidationError: If parameters are invalid

        Business Rules:
            - social_charges_rate must be between 0 and 1 (0% to 100%)
            - hsa_hourly_rate_sar must be positive
            - max_hsa_hours must be between 0 and 10
            - At least one of prrd_contribution_eur or avg_salary_sar should be set
              (unless category is AEFE_FUNDED which has no cost)
        """
        # Validate parameters
        self._validate_params(
            social_charges_rate=social_charges_rate,
            hsa_hourly_rate_sar=hsa_hourly_rate_sar,
            max_hsa_hours=max_hsa_hours,
        )

        # Find existing entry
        if cycle_id:
            cycle_condition = TeacherCostParam.cycle_id == cycle_id
        else:
            cycle_condition = TeacherCostParam.cycle_id.is_(None)

        query = select(TeacherCostParam).where(
            and_(
                TeacherCostParam.version_id == version_id,
                TeacherCostParam.category_id == category_id,
                cycle_condition,
                TeacherCostParam.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        data = {
            "version_id": version_id,
            "category_id": category_id,
            "cycle_id": cycle_id,
            "prrd_contribution_eur": prrd_contribution_eur,
            "avg_salary_sar": avg_salary_sar,
            "social_charges_rate": social_charges_rate,
            "benefits_allowance_sar": benefits_allowance_sar,
            "hsa_hourly_rate_sar": hsa_hourly_rate_sar,
            "max_hsa_hours": max_hsa_hours,
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

    async def delete_teacher_cost_param(
        self,
        param_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        """
        Soft delete a teacher cost parameter.

        Args:
            param_id: Parameter UUID to delete
            user_id: User ID for audit trail

        Returns:
            True if deleted successfully
        """
        await self._base_service.soft_delete(param_id, user_id=user_id)
        return True

    def _validate_params(
        self,
        social_charges_rate: Decimal,
        hsa_hourly_rate_sar: Decimal,
        max_hsa_hours: Decimal,
    ) -> None:
        """
        Validate teacher cost parameters.

        Args:
            social_charges_rate: Social charges rate
            hsa_hourly_rate_sar: HSA hourly rate
            max_hsa_hours: Max HSA hours

        Raises:
            ValidationError: If validation fails
        """
        if social_charges_rate < Decimal("0") or social_charges_rate > Decimal("1"):
            raise ValidationError(
                "social_charges_rate must be between 0 and 1 (0% to 100%)"
            )

        if hsa_hourly_rate_sar < Decimal("0"):
            raise ValidationError("hsa_hourly_rate_sar must be non-negative")

        if max_hsa_hours < Decimal("0") or max_hsa_hours > Decimal("10"):
            raise ValidationError("max_hsa_hours must be between 0 and 10")
