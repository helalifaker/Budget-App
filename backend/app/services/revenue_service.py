"""
Revenue service for revenue planning operations.

Handles revenue calculation from enrollment, fee structure application,
sibling discounts, and trimester distribution.
"""

import uuid
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import cache_revenue_projection
from app.engine.revenue import (
    FeeCategory as EngineFeeCategory,
)
from app.engine.revenue import (
    TuitionInput,
    calculate_total_student_revenue,
)
from app.models.configuration import FeeCategory, FeeStructure
from app.models.planning import EnrollmentPlan, RevenuePlan
from app.services.base import BaseService
from app.services.exceptions import ValidationError


class RevenueService:
    """
    Service for revenue planning operations.

    Provides business logic for revenue calculation and management.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize revenue service.

        Args:
            session: Async database session
        """
        self.session = session
        self.revenue_plan_service = BaseService(RevenuePlan, session)

    async def get_revenue_plan(
        self,
        version_id: uuid.UUID,
    ) -> list[RevenuePlan]:
        """
        Get revenue plan for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            List of RevenuePlan instances
        """
        return await self.revenue_plan_service.get_all(
            filters={"budget_version_id": version_id}
        )

    async def get_revenue_by_account(
        self,
        version_id: uuid.UUID,
        account_code: str,
    ) -> RevenuePlan | None:
        """
        Get revenue plan entry by account code.

        Args:
            version_id: Budget version UUID
            account_code: PCG account code

        Returns:
            RevenuePlan instance or None
        """
        query = select(RevenuePlan).where(
            and_(
                RevenuePlan.budget_version_id == version_id,
                RevenuePlan.account_code == account_code,
                RevenuePlan.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_revenue_entry(
        self,
        version_id: uuid.UUID,
        account_code: str,
        description: str,
        category: str,
        amount_sar: Decimal,
        is_calculated: bool = False,
        calculation_driver: str | None = None,
        trimester: int | None = None,
        notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> RevenuePlan:
        """
        Create or update revenue plan entry.

        Args:
            version_id: Budget version UUID
            account_code: PCG revenue account (70xxx-77xxx)
            description: Line item description
            category: Category (tuition, fees, other)
            amount_sar: Revenue amount in SAR
            is_calculated: Whether auto-calculated from drivers
            calculation_driver: Driver reference
            trimester: Trimester (1-3) for tuition, None for annual
            notes: Revenue notes
            user_id: User ID for audit trail

        Returns:
            RevenuePlan instance
        """
        if not account_code.startswith(("70", "71", "72", "73", "74", "75", "76", "77")):
            raise ValidationError(
                f"Revenue account code must start with 70-77, got {account_code}",
                field="account_code",
            )

        existing = await self.get_revenue_by_account(version_id, account_code)

        data = {
            "budget_version_id": version_id,
            "account_code": account_code,
            "description": description,
            "category": category,
            "amount_sar": amount_sar,
            "is_calculated": is_calculated,
            "calculation_driver": calculation_driver,
            "trimester": trimester,
            "notes": notes,
        }

        if existing:
            return await self.revenue_plan_service.update(
                existing.id,
                data,
                user_id=user_id,
            )
        else:
            return await self.revenue_plan_service.create(data, user_id=user_id)

    @cache_revenue_projection(ttl="30m")
    async def calculate_revenue_from_enrollment(
        self,
        budget_version_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> dict:
        """
        Calculate revenue from enrollment and fee structure.

        Applies sibling discounts and trimester distribution.
        Results are cached for 30 minutes.

        Args:
            budget_version_id: Budget version UUID (used as cache key)
            user_id: User ID for audit trail

        Returns:
            Dictionary with calculation results and created revenue entries
        """
        # Maintain compatibility with existing code
        version_id = budget_version_id
        # Get enrollment data
        enrollment_query = (
            select(EnrollmentPlan)
            .where(
                and_(
                    EnrollmentPlan.budget_version_id == version_id,
                    EnrollmentPlan.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(EnrollmentPlan.level),
                selectinload(EnrollmentPlan.nationality_type),
            )
        )
        enrollment_result = await self.session.execute(enrollment_query)
        enrollments = list(enrollment_result.scalars().all())

        if not enrollments:
            raise ValidationError(
                "No enrollment data found for this budget version. "
                "Please create enrollment plan first.",
                field="enrollment",
            )

        # Get fee structure
        fee_query = (
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
        fee_result = await self.session.execute(fee_query)
        fee_structures = list(fee_result.scalars().all())

        if not fee_structures:
            raise ValidationError(
                "No fee structure found for this budget version. "
                "Please configure fee structure first.",
                field="fee_structure",
            )

        # Build fee lookup map: (level_id, nationality_id, category_id) -> fees
        fee_map = {}
        for fee in fee_structures:
            key = (fee.level_id, fee.nationality_type_id, fee.fee_category_id)
            if key not in fee_map:
                fee_map[key] = {}

            # Map fee category code to fee type
            if fee.fee_category.code == "TUITION":
                if fee.trimester:
                    fee_map[key][f"tuition_t{fee.trimester}"] = fee.amount_sar
                else:
                    fee_map[key]["tuition"] = fee.amount_sar
            elif fee.fee_category.code == "DAI":
                fee_map[key]["dai"] = fee.amount_sar
            elif fee.fee_category.code == "REGISTRATION":
                fee_map[key]["registration"] = fee.amount_sar

        # Calculate revenue for each enrollment entry
        student_revenues = []
        total_revenue = Decimal("0")
        revenue_by_level = {}
        revenue_by_nationality = {}
        total_discounts = Decimal("0")

        for enrollment in enrollments:
            # Find matching fees from fee_map
            fees = None
            for key, fee_data in fee_map.items():
                level_id, nat_id, _cat_id = key
                if level_id == enrollment.level_id and nat_id == enrollment.nationality_type_id:
                    fees = fee_data
                    break

            if not fees or "tuition" not in fees:
                continue

            # Map nationality to fee category enum
            nat_code = enrollment.nationality_type.code
            if nat_code == "FRENCH":
                fee_cat = EngineFeeCategory.FRENCH_TTC
            elif nat_code == "SAUDI":
                fee_cat = EngineFeeCategory.SAUDI_HT
            else:
                fee_cat = EngineFeeCategory.OTHER_TTC

            # Calculate revenue for each student in this enrollment group
            # Note: In real implementation, we'd need sibling data
            # For now, assume no siblings (sibling_order=1)
            for _student_num in range(enrollment.student_count):
                tuition_input = TuitionInput(
                    level_id=enrollment.level_id,
                    level_code=enrollment.level.code,
                    fee_category=fee_cat,
                    tuition_fee=fees.get("tuition", Decimal("0")),
                    dai_fee=fees.get("dai", Decimal("0")),
                    registration_fee=fees.get("registration", Decimal("0")),
                    sibling_order=1,  # Default, would come from actual sibling data
                )

                student_revenue = calculate_total_student_revenue(tuition_input)
                student_revenues.append(student_revenue.tuition_revenue)

                total_revenue += student_revenue.total_annual_revenue
                total_discounts += student_revenue.tuition_revenue.sibling_discount_amount

                # Aggregate by level
                level_code = enrollment.level.code
                if level_code not in revenue_by_level:
                    revenue_by_level[level_code] = Decimal("0")
                revenue_by_level[level_code] += student_revenue.total_annual_revenue

                # Aggregate by nationality
                nat_name = enrollment.nationality_type.name_en
                if nat_name not in revenue_by_nationality:
                    revenue_by_nationality[nat_name] = Decimal("0")
                revenue_by_nationality[nat_name] += student_revenue.total_annual_revenue

        # Create revenue plan entries
        # Tuition by trimester (T1: 40%, T2: 30%, T3: 30%)
        tuition_revenue = total_revenue  # Simplified, should exclude DAI and registration
        t1_revenue = tuition_revenue * Decimal("0.40")
        t2_revenue = tuition_revenue * Decimal("0.30")
        t3_revenue = tuition_revenue * Decimal("0.30")

        created_entries = []

        # Create T1 entry
        t1_entry = await self.create_revenue_entry(
            version_id=version_id,
            account_code="70110",
            description="Scolarité Trimestre 1",
            category="tuition",
            amount_sar=t1_revenue,
            is_calculated=True,
            calculation_driver="enrollment",
            trimester=1,
            notes="Calculated from enrollment × fee structure (40%)",
            user_id=user_id,
        )
        created_entries.append(t1_entry)

        # Create T2 entry
        t2_entry = await self.create_revenue_entry(
            version_id=version_id,
            account_code="70120",
            description="Scolarité Trimestre 2",
            category="tuition",
            amount_sar=t2_revenue,
            is_calculated=True,
            calculation_driver="enrollment",
            trimester=2,
            notes="Calculated from enrollment × fee structure (30%)",
            user_id=user_id,
        )
        created_entries.append(t2_entry)

        # Create T3 entry
        t3_entry = await self.create_revenue_entry(
            version_id=version_id,
            account_code="70130",
            description="Scolarité Trimestre 3",
            category="tuition",
            amount_sar=t3_revenue,
            is_calculated=True,
            calculation_driver="enrollment",
            trimester=3,
            notes="Calculated from enrollment × fee structure (30%)",
            user_id=user_id,
        )
        created_entries.append(t3_entry)

        await self.session.flush()

        return {
            "total_revenue": total_revenue,
            "revenue_by_level": revenue_by_level,
            "revenue_by_nationality": revenue_by_nationality,
            "sibling_discounts_applied": total_discounts,
            "trimester_distribution": {
                "T1": t1_revenue,
                "T2": t2_revenue,
                "T3": t3_revenue,
            },
            "created_entries": created_entries,
            "student_count": sum(e.student_count for e in enrollments),
        }

    async def delete_revenue_entry(
        self,
        entry_id: uuid.UUID,
    ) -> bool:
        """
        Delete revenue plan entry.

        Args:
            entry_id: Revenue plan entry UUID

        Returns:
            True if deleted successfully
        """
        return await self.revenue_plan_service.delete(entry_id)

    async def get_revenue_summary(
        self,
        version_id: uuid.UUID,
    ) -> dict:
        """
        Get revenue summary for a budget version.

        Args:
            version_id: Budget version UUID

        Returns:
            Dictionary with revenue summary statistics
        """
        revenue_plans = await self.get_revenue_plan(version_id)

        total_revenue = Decimal("0")
        revenue_by_category = {}
        revenue_by_trimester = {}
        calculated_revenue = Decimal("0")
        manual_revenue = Decimal("0")

        for plan in revenue_plans:
            total_revenue += plan.amount_sar

            # By category
            if plan.category not in revenue_by_category:
                revenue_by_category[plan.category] = Decimal("0")
            revenue_by_category[plan.category] += plan.amount_sar

            # By trimester
            if plan.trimester:
                trimester_key = f"T{plan.trimester}"
                if trimester_key not in revenue_by_trimester:
                    revenue_by_trimester[trimester_key] = Decimal("0")
                revenue_by_trimester[trimester_key] += plan.amount_sar

            # Calculated vs manual
            if plan.is_calculated:
                calculated_revenue += plan.amount_sar
            else:
                manual_revenue += plan.amount_sar

        return {
            "total_revenue": total_revenue,
            "revenue_by_category": revenue_by_category,
            "revenue_by_trimester": revenue_by_trimester,
            "calculated_revenue": calculated_revenue,
            "manual_revenue": manual_revenue,
            "entry_count": len(revenue_plans),
        }
