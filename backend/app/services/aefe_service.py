"""
AEFE Position Service for managing French Ministry positions.

Handles:
- Position initialization (24 Detached + 4 Funded)
- Position assignment to employees
- PRRD cost calculations (EUR to SAR conversion)
- Vacancy tracking
"""

import uuid
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.personnel import (
    AEFEPosition,
    AEFEPositionType,
    Employee,
    EmployeeCategory,
)
from app.services.base import BaseService
from app.services.exceptions import ValidationError

# AEFE Constants
DEFAULT_PRRD_AMOUNT_EUR = Decimal("41863.00")  # 2024 PRRD rate
DEFAULT_EXCHANGE_RATE_EUR_SAR = Decimal("4.05")  # Approximate EUR/SAR rate

# Standard position counts
DETACHED_POSITIONS_COUNT = 24
FUNDED_POSITIONS_COUNT = 4


class AEFEService(BaseService[AEFEPosition]):
    """
    Service for managing AEFE positions.

    AEFE positions are French Ministry positions with two types:
    - Detached (24 positions): School pays PRRD (~41,863 EUR/year)
    - Funded (4 positions): Fully funded by AEFE (zero cost to school)

    Provides:
    - Position initialization for new budget versions
    - Position-to-employee assignment
    - PRRD cost calculations
    - Vacancy and fill rate tracking
    """

    def __init__(self, session: AsyncSession):
        """Initialize AEFE service."""
        super().__init__(AEFEPosition, session)

    async def initialize_positions(
        self,
        budget_version_id: uuid.UUID,
        academic_year: str,
        prrd_amount_eur: Decimal | None = None,
        exchange_rate_eur_sar: Decimal | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[AEFEPosition]:
        """
        Initialize AEFE positions for a budget version.

        Creates 28 positions: 24 Detached + 4 Funded.
        Should be called once when setting up a new budget version.

        Args:
            budget_version_id: Budget version UUID
            academic_year: Academic year (e.g., "2024-2025")
            prrd_amount_eur: PRRD amount per position (default 41,863 EUR)
            exchange_rate_eur_sar: EUR to SAR exchange rate
            user_id: User ID for audit trail

        Returns:
            List of created positions

        Raises:
            ValidationError: If positions already exist for this version
        """
        # Check if positions already exist
        existing = await self.get_positions_by_version(budget_version_id)
        if existing:
            raise ValidationError(
                f"AEFE positions already exist for budget version {budget_version_id}. "
                "Use update methods to modify existing positions."
            )

        prrd = prrd_amount_eur or DEFAULT_PRRD_AMOUNT_EUR
        rate = exchange_rate_eur_sar or DEFAULT_EXCHANGE_RATE_EUR_SAR
        prrd_sar = (prrd * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        positions = []

        # Create Detached positions (1-24)
        for i in range(1, DETACHED_POSITIONS_COUNT + 1):
            position = AEFEPosition(
                budget_version_id=budget_version_id,
                position_type=AEFEPositionType.DETACHED,
                position_number=i,
                academic_year=academic_year,
                prrd_amount_eur=prrd,
                exchange_rate_eur_sar=rate,
                prrd_amount_sar=prrd_sar,
                is_filled=False,
            )
            if user_id:
                position.created_by_id = user_id
                position.updated_by_id = user_id
            positions.append(position)

        # Create Funded positions (1-4)
        for i in range(1, FUNDED_POSITIONS_COUNT + 1):
            position = AEFEPosition(
                budget_version_id=budget_version_id,
                position_type=AEFEPositionType.FUNDED,
                position_number=i,
                academic_year=academic_year,
                prrd_amount_eur=Decimal("0.00"),  # Funded = zero cost
                exchange_rate_eur_sar=rate,
                prrd_amount_sar=Decimal("0.00"),
                is_filled=False,
            )
            if user_id:
                position.created_by_id = user_id
                position.updated_by_id = user_id
            positions.append(position)

        self.session.add_all(positions)
        await self.session.flush()

        return positions

    async def get_positions_by_version(
        self,
        budget_version_id: uuid.UUID,
        position_type: AEFEPositionType | None = None,
        filled_only: bool | None = None,
    ) -> list[AEFEPosition]:
        """
        Get AEFE positions for a budget version.

        Args:
            budget_version_id: Budget version UUID
            position_type: Filter by position type (DETACHED/FUNDED)
            filled_only: Filter by fill status (True=filled, False=vacant)

        Returns:
            List of positions
        """
        query = (
            select(AEFEPosition)
            .where(AEFEPosition.budget_version_id == budget_version_id)
            .where(AEFEPosition.deleted_at.is_(None))
        )

        if position_type:
            query = query.where(AEFEPosition.position_type == position_type)

        if filled_only is not None:
            query = query.where(AEFEPosition.is_filled == filled_only)

        query = query.order_by(
            AEFEPosition.position_type,
            AEFEPosition.position_number,
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def assign_employee(
        self,
        position_id: uuid.UUID,
        employee_id: uuid.UUID,
        cycle_id: uuid.UUID | None = None,
        subject_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> AEFEPosition:
        """
        Assign an employee to an AEFE position.

        Args:
            position_id: Position UUID
            employee_id: Employee UUID to assign
            cycle_id: Academic cycle (optional)
            subject_id: Teaching subject (optional)
            user_id: User ID for audit trail

        Returns:
            Updated position

        Raises:
            ValidationError: If position is already filled or employee is invalid
        """
        # Get position
        position = await self.get_by_id(position_id)

        if position.is_filled:
            raise ValidationError(
                f"Position {position.position_type.value} #{position.position_number} "
                "is already filled. Unassign current employee first."
            )

        # Verify employee exists and is AEFE category
        employee_query = (
            select(Employee)
            .where(Employee.id == employee_id)
            .where(Employee.deleted_at.is_(None))
        )
        result = await self.session.execute(employee_query)
        employee = result.scalar_one_or_none()

        if not employee:
            raise ValidationError(f"Employee {employee_id} not found")

        expected_category = (
            EmployeeCategory.AEFE_DETACHED
            if position.position_type == AEFEPositionType.DETACHED
            else EmployeeCategory.AEFE_FUNDED
        )

        if employee.category != expected_category:
            raise ValidationError(
                f"Employee category ({employee.category.value}) does not match "
                f"position type ({position.position_type.value}). "
                f"Expected category: {expected_category.value}"
            )

        # Check if employee is already assigned to another position
        existing_query = (
            select(AEFEPosition)
            .where(AEFEPosition.employee_id == employee_id)
            .where(AEFEPosition.budget_version_id == position.budget_version_id)
            .where(AEFEPosition.deleted_at.is_(None))
        )
        existing_result = await self.session.execute(existing_query)
        existing_assignment = existing_result.scalar_one_or_none()

        if existing_assignment:
            raise ValidationError(
                f"Employee is already assigned to position "
                f"{existing_assignment.position_type.value} #{existing_assignment.position_number}"
            )

        # Assign employee
        update_data = {
            "employee_id": employee_id,
            "cycle_id": cycle_id,
            "subject_id": subject_id,
            "is_filled": True,
        }

        return await self.update(position_id, update_data, user_id)

    async def unassign_employee(
        self,
        position_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> AEFEPosition:
        """
        Remove employee assignment from an AEFE position.

        Args:
            position_id: Position UUID
            user_id: User ID for audit trail

        Returns:
            Updated position

        Raises:
            ValidationError: If position is not currently filled
        """
        position = await self.get_by_id(position_id)

        if not position.is_filled:
            raise ValidationError(
                f"Position {position.position_type.value} #{position.position_number} "
                "is not currently assigned."
            )

        update_data = {
            "employee_id": None,
            "cycle_id": None,
            "subject_id": None,
            "is_filled": False,
        }

        return await self.update(position_id, update_data, user_id)

    async def update_prrd_rates(
        self,
        budget_version_id: uuid.UUID,
        prrd_amount_eur: Decimal | None = None,
        exchange_rate_eur_sar: Decimal | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[AEFEPosition]:
        """
        Update PRRD rates for all Detached positions in a budget version.

        Args:
            budget_version_id: Budget version UUID
            prrd_amount_eur: New PRRD amount in EUR
            exchange_rate_eur_sar: New EUR/SAR exchange rate
            user_id: User ID for audit trail

        Returns:
            Updated positions
        """
        positions = await self.get_positions_by_version(
            budget_version_id,
            position_type=AEFEPositionType.DETACHED,
        )

        updated_positions = []

        for position in positions:
            update_data: dict[str, Any] = {}

            if prrd_amount_eur is not None:
                update_data["prrd_amount_eur"] = prrd_amount_eur

            if exchange_rate_eur_sar is not None:
                update_data["exchange_rate_eur_sar"] = exchange_rate_eur_sar

            # Recalculate SAR amount
            eur = prrd_amount_eur or position.prrd_amount_eur
            rate = exchange_rate_eur_sar or position.exchange_rate_eur_sar
            update_data["prrd_amount_sar"] = (eur * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            if update_data:
                updated = await self.update(position.id, update_data, user_id)
                updated_positions.append(updated)

        return updated_positions

    async def get_position_summary(
        self,
        budget_version_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Get summary statistics for AEFE positions.

        Args:
            budget_version_id: Budget version UUID

        Returns:
            Summary dictionary with counts and costs
        """
        positions = await self.get_positions_by_version(budget_version_id)

        detached_filled = 0
        detached_vacant = 0
        funded_filled = 0
        funded_vacant = 0
        total_prrd_sar = Decimal("0.00")

        for pos in positions:
            if pos.position_type == AEFEPositionType.DETACHED:
                if pos.is_filled:
                    detached_filled += 1
                    total_prrd_sar += pos.prrd_amount_sar
                else:
                    detached_vacant += 1
            else:  # FUNDED
                if pos.is_filled:
                    funded_filled += 1
                else:
                    funded_vacant += 1

        total_detached = detached_filled + detached_vacant
        total_funded = funded_filled + funded_vacant
        total_positions = total_detached + total_funded
        total_filled = detached_filled + funded_filled
        total_vacant = detached_vacant + funded_vacant

        # Get PRRD rates from first detached position (if exists)
        prrd_eur = Decimal("0.00")
        exchange_rate = Decimal("0.00")
        detached = [p for p in positions if p.position_type == AEFEPositionType.DETACHED]
        if detached:
            prrd_eur = detached[0].prrd_amount_eur
            exchange_rate = detached[0].exchange_rate_eur_sar

        return {
            "budget_version_id": budget_version_id,
            "total_positions": total_positions,
            "total_filled": total_filled,
            "total_vacant": total_vacant,
            "fill_rate": (
                round(total_filled / total_positions * 100, 1)
                if total_positions > 0
                else 0.0
            ),
            "detached": {
                "total": total_detached,
                "filled": detached_filled,
                "vacant": detached_vacant,
            },
            "funded": {
                "total": total_funded,
                "filled": funded_filled,
                "vacant": funded_vacant,
            },
            "prrd_amount_eur": prrd_eur,
            "exchange_rate_eur_sar": exchange_rate,
            "total_annual_prrd_sar": total_prrd_sar,
            "monthly_prrd_sar": (total_prrd_sar / 12).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
        }

    async def copy_positions_from_version(
        self,
        source_version_id: uuid.UUID,
        target_version_id: uuid.UUID,
        include_assignments: bool = True,
        user_id: uuid.UUID | None = None,
    ) -> list[AEFEPosition]:
        """
        Copy AEFE positions from one budget version to another.

        Useful when creating a new budget version from an existing one.

        Args:
            source_version_id: Source budget version UUID
            target_version_id: Target budget version UUID
            include_assignments: Whether to copy employee assignments
            user_id: User ID for audit trail

        Returns:
            List of created positions in target version

        Raises:
            ValidationError: If target version already has positions
        """
        # Check target doesn't have positions
        existing = await self.get_positions_by_version(target_version_id)
        if existing:
            raise ValidationError(
                f"Target budget version {target_version_id} already has AEFE positions"
            )

        # Get source positions
        source_positions = await self.get_positions_by_version(source_version_id)
        if not source_positions:
            raise ValidationError(
                f"Source budget version {source_version_id} has no AEFE positions to copy"
            )

        new_positions = []

        for source in source_positions:
            position = AEFEPosition(
                budget_version_id=target_version_id,
                position_type=source.position_type,
                position_number=source.position_number,
                academic_year=source.academic_year,
                employee_id=source.employee_id if include_assignments else None,
                cycle_id=source.cycle_id if include_assignments else None,
                subject_id=source.subject_id if include_assignments else None,
                prrd_amount_eur=source.prrd_amount_eur,
                exchange_rate_eur_sar=source.exchange_rate_eur_sar,
                prrd_amount_sar=source.prrd_amount_sar,
                is_filled=source.is_filled if include_assignments else False,
            )
            if user_id:
                position.created_by_id = user_id
                position.updated_by_id = user_id
            new_positions.append(position)

        self.session.add_all(new_positions)
        await self.session.flush()

        return new_positions

    async def get_vacant_positions_by_subject(
        self,
        budget_version_id: uuid.UUID,
    ) -> dict[str, int]:
        """
        Get count of vacant positions grouped by subject.

        Useful for DHG gap analysis to see available AEFE capacity.

        Args:
            budget_version_id: Budget version UUID

        Returns:
            Dict mapping subject_id to vacant position count
        """
        # For vacant positions, subject_id will be None
        # This returns positions that could potentially be filled
        vacant = await self.get_positions_by_version(
            budget_version_id,
            filled_only=False,
        )

        # Count total vacant by type
        detached_vacant = sum(
            1 for p in vacant if p.position_type == AEFEPositionType.DETACHED
        )
        funded_vacant = sum(
            1 for p in vacant if p.position_type == AEFEPositionType.FUNDED
        )

        return {
            "detached_vacant": detached_vacant,
            "funded_vacant": funded_vacant,
            "total_vacant": detached_vacant + funded_vacant,
        }
