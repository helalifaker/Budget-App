"""
Cost service for personnel and operating cost planning operations.

Handles cost calculation from DHG allocations, enrollment data,
and driver-based cost models.
"""

import uuid
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models import (
    AcademicCycle,
    EnrollmentPlan,
    OperatingCostPlan,
    PersonnelCostPlan,
    TeacherAllocation,
    TeacherCategory,
    TeacherCostParam,
)
from app.services.base import BaseService
from app.services.exceptions import ServiceException, ValidationError


class CostService:
    """
    Service for personnel and operating cost planning operations.

    Provides business logic for cost calculation and management.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize cost service.

        Args:
            session: Async database session
        """
        self.session = session
        self.personnel_cost_service = BaseService(PersonnelCostPlan, session)
        self.operating_cost_service = BaseService(OperatingCostPlan, session)

    # ==============================================================================
    # Personnel Cost Operations
    # ==============================================================================

    async def get_personnel_costs(
        self,
        version_id: uuid.UUID,
    ) -> list[PersonnelCostPlan]:
        """
        Get personnel cost plan for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of PersonnelCostPlan instances
        """
        return await self.personnel_cost_service.get_all(
            filters={"version_id": version_id}
        )

    async def get_personnel_cost_by_account(
        self,
        version_id: uuid.UUID,
        account_code: str,
        category_id: uuid.UUID | None = None,
        cycle_id: uuid.UUID | None = None,
    ) -> PersonnelCostPlan | None:
        """
        Get personnel cost entry by account code and filters.

        Args:
            version_id: Budget version UUID
            account_code: PCG account code
            category_id: Teacher category ID (optional)
            cycle_id: Academic cycle ID (optional)

        Returns:
            PersonnelCostPlan instance or None
        """
        conditions = [
            PersonnelCostPlan.version_id == version_id,
            PersonnelCostPlan.account_code == account_code,
            PersonnelCostPlan.deleted_at.is_(None),
        ]

        if category_id:
            conditions.append(PersonnelCostPlan.category_id == category_id)
        else:
            conditions.append(PersonnelCostPlan.category_id.is_(None))

        if cycle_id:
            conditions.append(PersonnelCostPlan.cycle_id == cycle_id)
        else:
            conditions.append(PersonnelCostPlan.cycle_id.is_(None))

        query = select(PersonnelCostPlan).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_personnel_cost_entry(
        self,
        version_id: uuid.UUID,
        account_code: str,
        description: str,
        fte_count: Decimal,
        unit_cost_sar: Decimal,
        category_id: uuid.UUID | None = None,
        cycle_id: uuid.UUID | None = None,
        is_calculated: bool = False,
        calculation_driver: str | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> PersonnelCostPlan:
        """
        Create or update personnel cost entry.

        Args:
            version_id: Budget version UUID
            account_code: PCG expense account (64xxx)
            description: Cost description
            fte_count: Number of FTE
            unit_cost_sar: Cost per FTE (SAR/year)
            category_id: Teacher category ID
            cycle_id: Academic cycle ID
            is_calculated: Whether auto-calculated
            calculation_driver: Driver reference
            notes: Cost notes
            user_id: User ID for audit trail

        Returns:
            PersonnelCostPlan instance
        """
        if not account_code.startswith("64"):
            raise ValidationError(
                f"Personnel cost account code must start with 64, got {account_code}",
                field="account_code",
            )

        total_cost_sar = fte_count * unit_cost_sar

        existing = await self.get_personnel_cost_by_account(
            version_id, account_code, category_id, cycle_id
        )

        data = {
            "version_id": version_id,
            "account_code": account_code,
            "description": description,
            "category_id": category_id,
            "cycle_id": cycle_id,
            "fte_count": fte_count,
            "unit_cost_sar": unit_cost_sar,
            "total_cost_sar": total_cost_sar,
            "is_calculated": is_calculated,
            "calculation_driver": calculation_driver,
            "notes": notes,
        }

        if existing:
            return await self.personnel_cost_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self.personnel_cost_service.create(data, user_id=user_id)

    async def calculate_personnel_costs_from_dhg(
        self,
        version_id: uuid.UUID,
        eur_to_sar_rate: Decimal = Decimal("4.05"),
        user_id: uuid.UUID | None = None,
    ) -> dict:
        """
        Calculate personnel costs from DHG teacher allocations.

        AEFE Cost Formula:
            cost = fte × prrd_eur × eur_to_sar_rate

        Local Cost Formula:
            cost = fte × (salary + social_charges_21% + benefits + hsa)

        Args:
            version_id: Budget version UUID
            eur_to_sar_rate: EUR to SAR exchange rate
            user_id: User ID for audit trail

        Returns:
            Dictionary with calculation results and created cost entries

        Raises:
            ValidationError: If teacher allocations or cost parameters are missing
            ServiceException: If database operations fail
        """
        try:
            # Get teacher allocations
            allocation_query = (
                select(TeacherAllocation)
                .where(
                    and_(
                        TeacherAllocation.version_id == version_id,
                        TeacherAllocation.deleted_at.is_(None),
                    )
                )
                .options(
                    selectinload(TeacherAllocation.category),
                    selectinload(TeacherAllocation.cycle),
                    selectinload(TeacherAllocation.subject),
                )
            )
            allocation_result = await self.session.execute(allocation_query)
            allocations = list(allocation_result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve teacher allocations for cost calculation",
                version_id=str(version_id),
                error=str(e),
                exc_info=True,
            )
            raise ServiceException(
                "Failed to retrieve teacher allocation data. Please try again.",
                status_code=500,
                details={"version_id": str(version_id)},
            ) from e

        if not allocations:
            raise ValidationError(
                "No teacher allocations found for this budget version. "
                "Please complete DHG planning first.",
                field="allocations",
            )

        # Get teacher cost parameters
        cost_param_query = (
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
        cost_param_result = await self.session.execute(cost_param_query)
        cost_params = list(cost_param_result.scalars().all())

        if not cost_params:
            raise ValidationError(
                "No teacher cost parameters found for this budget version. "
                "Please configure teacher cost parameters first.",
                field="cost_params",
            )

        # Build cost parameter lookup map
        cost_param_map = {}
        for param in cost_params:
            key = (param.category_id, param.cycle_id)
            cost_param_map[key] = param

        # Calculate costs by category and cycle
        total_cost = Decimal("0")
        cost_by_category = {}
        cost_by_cycle = {}
        total_fte = Decimal("0")
        created_entries = []

        # Group allocations by category and cycle
        allocation_groups = {}
        for allocation in allocations:
            key = (allocation.category_id, allocation.cycle_id)
            if key not in allocation_groups:
                allocation_groups[key] = []
            allocation_groups[key].append(allocation)

        # Calculate cost for each group
        for (category_id, cycle_id), group_allocations in allocation_groups.items():
            # Find matching cost parameters
            cost_param = cost_param_map.get((category_id, cycle_id))
            if not cost_param:
                # Try to find default (cycle=None)
                cost_param = cost_param_map.get((category_id, None))

            if not cost_param:
                continue

            # Sum FTE for this group
            group_fte = sum(alloc.fte_count for alloc in group_allocations)
            total_fte += group_fte

            # Get category to determine cost calculation method
            category_query = select(TeacherCategory).where(
                TeacherCategory.id == category_id
            )
            category_result = await self.session.execute(category_query)
            category = category_result.scalar_one_or_none()

            if not category:
                continue

            # Calculate unit cost based on category
            if category.code in ("AEFE_DETACHED", "AEFE_FUNDED"):
                # AEFE: cost = prrd_eur × eur_to_sar_rate
                if cost_param.prrd_contribution_eur:
                    unit_cost_sar = cost_param.prrd_contribution_eur * eur_to_sar_rate
                else:
                    unit_cost_sar = Decimal("0")
            else:
                # Local: cost = salary + social_charges + benefits
                base_salary = cost_param.avg_salary_sar or Decimal("0")
                social_charges = base_salary * cost_param.social_charges_rate
                benefits = cost_param.benefits_allowance_sar or Decimal("0")
                unit_cost_sar = base_salary + social_charges + benefits

            # Calculate total cost for this group
            group_cost = group_fte * unit_cost_sar
            total_cost += group_cost

            # Track by category
            cat_name = category.name_en
            if cat_name not in cost_by_category:
                cost_by_category[cat_name] = Decimal("0")
            cost_by_category[cat_name] += group_cost

            # Track by cycle
            if cycle_id:
                cycle_query = select(AcademicCycle).where(AcademicCycle.id == cycle_id)
                cycle_result = await self.session.execute(cycle_query)
                cycle = cycle_result.scalar_one_or_none()
                if cycle:
                    cycle_name = cycle.name_en
                    if cycle_name not in cost_by_cycle:
                        cost_by_cycle[cycle_name] = Decimal("0")
                    cost_by_cycle[cycle_name] += group_cost

            # Create personnel cost entry
            account_code = "64110"  # Teaching salaries
            description = f"Teaching Staff - {category.name_en}"
            if cycle_id:
                cycle_query = select(AcademicCycle).where(AcademicCycle.id == cycle_id)
                cycle_result = await self.session.execute(cycle_query)
                cycle = cycle_result.scalar_one_or_none()
                if cycle:
                    description += f" - {cycle.name_en}"

            entry = await self.create_personnel_cost_entry(
                version_id=version_id,
                account_code=account_code,
                description=description,
                fte_count=group_fte,
                unit_cost_sar=unit_cost_sar,
                category_id=category_id,
                cycle_id=cycle_id,
                is_calculated=True,
                calculation_driver="dhg_allocation",
                notes="Calculated from DHG teacher allocations",
                user_id=user_id,
            )
            created_entries.append(entry)

        await self.session.flush()

        return {
            "total_cost": total_cost,
            "cost_by_category": cost_by_category,
            "cost_by_cycle": cost_by_cycle,
            "total_fte": total_fte,
            "created_entries": created_entries,
        }

    async def delete_personnel_cost_entry(
        self,
        entry_id: uuid.UUID,
    ) -> bool:
        """
        Delete personnel cost entry.

        Args:
            entry_id: Personnel cost entry UUID

        Returns:
            True if deleted successfully
        """
        return await self.personnel_cost_service.delete(entry_id)

    # ==============================================================================
    # Operating Cost Operations
    # ==============================================================================

    async def get_operating_costs(
        self,
        version_id: uuid.UUID,
    ) -> list[OperatingCostPlan]:
        """
        Get operating cost plan for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of OperatingCostPlan instances
        """
        return await self.operating_cost_service.get_all(
            filters={"version_id": version_id}
        )

    async def get_operating_cost_by_account(
        self,
        version_id: uuid.UUID,
        account_code: str,
    ) -> OperatingCostPlan | None:
        """
        Get operating cost entry by account code.

        Args:
            version_id: Budget version UUID
            account_code: PCG account code

        Returns:
            OperatingCostPlan instance or None
        """
        query = select(OperatingCostPlan).where(
            and_(
                OperatingCostPlan.version_id == version_id,
                OperatingCostPlan.account_code == account_code,
                OperatingCostPlan.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_operating_cost_entry(
        self,
        version_id: uuid.UUID,
        account_code: str,
        description: str,
        category: str,
        amount_sar: Decimal,
        is_calculated: bool = False,
        calculation_driver: str | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> OperatingCostPlan:
        """
        Create or update operating cost entry.

        Args:
            version_id: Budget version UUID
            account_code: PCG expense account (60xxx-68xxx)
            description: Expense description
            category: Category (supplies, utilities, maintenance, etc.)
            amount_sar: Expense amount in SAR
            is_calculated: Whether auto-calculated from driver
            calculation_driver: Driver reference
            notes: Expense notes
            user_id: User ID for audit trail

        Returns:
            OperatingCostPlan instance
        """
        if not account_code.startswith(("60", "61", "62", "63", "65", "66", "68")):
            raise ValidationError(
                f"Operating cost account code must start with 60-63, 65-66, or 68, got {account_code}",
                field="account_code",
            )

        existing = await self.get_operating_cost_by_account(version_id, account_code)

        data = {
            "version_id": version_id,
            "account_code": account_code,
            "description": description,
            "category": category,
            "amount_sar": amount_sar,
            "is_calculated": is_calculated,
            "calculation_driver": calculation_driver,
            "notes": notes,
        }

        if existing:
            return await self.operating_cost_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self.operating_cost_service.create(data, user_id=user_id)

    async def calculate_operating_costs(
        self,
        version_id: uuid.UUID,
        cost_drivers: dict[str, Decimal],
        user_id: uuid.UUID | None = None,
    ) -> dict:
        """
        Calculate operating costs using driver-based models.

        Drivers:
            - enrollment: Cost per student (supplies, books, etc.)
            - square_meters: Cost per sqm (utilities, maintenance, cleaning)
            - fixed: Fixed annual costs (insurance, rent, etc.)

        Args:
            version_id: Budget version UUID
            cost_drivers: Dictionary of driver rates
            user_id: User ID for audit trail

        Returns:
            Dictionary with calculation results and created cost entries
        """
        # Get enrollment count
        enrollment_query = select(func.sum(EnrollmentPlan.student_count)).where(
            and_(
                EnrollmentPlan.version_id == version_id,
                EnrollmentPlan.deleted_at.is_(None),
            )
        )
        enrollment_result = await self.session.execute(enrollment_query)
        total_enrollment = enrollment_result.scalar() or 0

        if total_enrollment == 0:
            raise ValidationError(
                "No enrollment data found. Please create enrollment plan first.",
                field="enrollment",
            )

        # Calculate costs by driver
        enrollment_driven_costs = Decimal("0")
        facility_driven_costs = Decimal("0")
        fixed_costs = Decimal("0")
        created_entries = []

        # Enrollment-driven costs (per student)
        if "cost_per_student_supplies" in cost_drivers:
            supplies_cost = Decimal(total_enrollment) * cost_drivers["cost_per_student_supplies"]
            enrollment_driven_costs += supplies_cost

            entry = await self.create_operating_cost_entry(
                version_id=version_id,
                account_code="60610",
                description="Student Supplies and Materials",
                category="supplies",
                amount_sar=supplies_cost,
                is_calculated=True,
                calculation_driver="enrollment",
                notes=f"Calculated: {total_enrollment} students × {cost_drivers['cost_per_student_supplies']} SAR/student",
                user_id=user_id,
            )
            created_entries.append(entry)

        # Facility-driven costs (per square meter)
        if "square_meters" in cost_drivers and "cost_per_sqm_maintenance" in cost_drivers:
            maintenance_cost = cost_drivers["square_meters"] * cost_drivers["cost_per_sqm_maintenance"]
            facility_driven_costs += maintenance_cost

            entry = await self.create_operating_cost_entry(
                version_id=version_id,
                account_code="61520",
                description="Facility Maintenance",
                category="maintenance",
                amount_sar=maintenance_cost,
                is_calculated=True,
                calculation_driver="square_meters",
                notes=f"Calculated: {cost_drivers['square_meters']} sqm × {cost_drivers['cost_per_sqm_maintenance']} SAR/sqm",
                user_id=user_id,
            )
            created_entries.append(entry)

        # Fixed costs
        if "insurance_annual" in cost_drivers:
            insurance_cost = cost_drivers["insurance_annual"]
            fixed_costs += insurance_cost

            entry = await self.create_operating_cost_entry(
                version_id=version_id,
                account_code="62600",
                description="Insurance Premiums",
                category="insurance",
                amount_sar=insurance_cost,
                is_calculated=False,
                calculation_driver="fixed",
                notes="Annual insurance premium",
                user_id=user_id,
            )
            created_entries.append(entry)

        await self.session.flush()

        total_cost = enrollment_driven_costs + facility_driven_costs + fixed_costs

        return {
            "total_cost": total_cost,
            "enrollment_driven_costs": enrollment_driven_costs,
            "facility_driven_costs": facility_driven_costs,
            "fixed_costs": fixed_costs,
            "created_entries": created_entries,
            "enrollment_count": total_enrollment,
        }

    async def delete_operating_cost_entry(
        self,
        entry_id: uuid.UUID,
    ) -> bool:
        """
        Delete operating cost entry.

        Args:
            entry_id: Operating cost entry UUID

        Returns:
            True if deleted successfully
        """
        return await self.operating_cost_service.delete(entry_id)

    async def get_cost_summary(
        self,
        version_id: uuid.UUID,
    ) -> dict:
        """
        Get cost summary for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            Dictionary with cost summary statistics
        """
        personnel_costs = await self.get_personnel_costs(version_id)
        operating_costs = await self.get_operating_costs(version_id)

        total_personnel_cost = sum(p.total_cost_sar for p in personnel_costs)
        total_operating_cost = sum(o.amount_sar for o in operating_costs)
        total_cost = total_personnel_cost + total_operating_cost

        personnel_by_category = {}
        for cost in personnel_costs:
            if cost.category:
                cat_key = str(cost.category_id)
                if cat_key not in personnel_by_category:
                    personnel_by_category[cat_key] = Decimal("0")
                personnel_by_category[cat_key] += cost.total_cost_sar

        operating_by_category = {}
        for cost in operating_costs:
            if cost.category not in operating_by_category:
                operating_by_category[cost.category] = Decimal("0")
            operating_by_category[cost.category] += cost.amount_sar

        return {
            "total_cost": total_cost,
            "total_personnel_cost": total_personnel_cost,
            "total_operating_cost": total_operating_cost,
            "personnel_by_category": personnel_by_category,
            "operating_by_category": operating_by_category,
            "personnel_entry_count": len(personnel_costs),
            "operating_entry_count": len(operating_costs),
        }
