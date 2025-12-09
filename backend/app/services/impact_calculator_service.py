"""
Impact Calculator Service - Real-time impact preview calculations

Calculates the cascading impact of proposed budget changes before they are saved.
This allows users to see the downstream effects of their edits in real-time.

Key Metrics Calculated:
- FTE Change: Impact on teacher Full-Time Equivalents
- Cost Impact: Total change in personnel + operating costs
- Revenue Impact: Change in expected revenue
- Margin Impact: Net impact on operating margin percentage
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import (
    ClassStructure,
    DHGTeacherRequirement,
    EnrollmentPlan,
    PersonnelCostPlan,
    RevenuePlan,
)


class ImpactMetrics(BaseModel):
    """Metrics showing the impact of a proposed change."""

    fte_change: float = 0.0
    fte_current: float = 0.0
    fte_proposed: float = 0.0

    cost_impact_sar: Decimal = Decimal("0")
    cost_current_sar: Decimal = Decimal("0")
    cost_proposed_sar: Decimal = Decimal("0")

    revenue_impact_sar: Decimal = Decimal("0")
    revenue_current_sar: Decimal = Decimal("0")
    revenue_proposed_sar: Decimal = Decimal("0")

    margin_impact_pct: float = 0.0
    margin_current_pct: float = 0.0
    margin_proposed_pct: float = 0.0

    affected_steps: list[str] = []

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProposedChange(BaseModel):
    """Represents a proposed change to a planning value."""

    step_id: str  # 'enrollment', 'class_structure', 'dhg', 'revenue', 'costs', 'capex'
    dimension_type: str  # 'level', 'subject', 'account_code'
    dimension_id: str | None = None
    dimension_code: str | None = None
    field_name: str  # The field being changed
    new_value: Any  # The proposed new value


class ImpactCalculatorService:
    """Service for calculating real-time impact of proposed budget changes."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def calculate_impact(
        self,
        version_id: UUID,
        proposed_change: ProposedChange,
    ) -> ImpactMetrics:
        """
        Calculate the cascading impact of a proposed change.

        This is a preview-only calculation - no database changes are made.

        Args:
            version_id: Budget version UUID
            proposed_change: The proposed change to evaluate

        Returns:
            ImpactMetrics showing FTE, cost, revenue, and margin impacts
        """
        metrics = ImpactMetrics()

        # Get current totals
        current = await self._get_current_totals(version_id)

        # Calculate proposed totals based on the change type
        if proposed_change.step_id == "enrollment":
            proposed = await self._calculate_enrollment_impact(
                version_id, proposed_change, current
            )
        elif proposed_change.step_id == "class_structure":
            proposed = await self._calculate_class_structure_impact(
                version_id, proposed_change, current
            )
        elif proposed_change.step_id == "dhg":
            proposed = await self._calculate_dhg_impact(
                version_id, proposed_change, current
            )
        elif proposed_change.step_id == "revenue":
            proposed = await self._calculate_revenue_impact(
                version_id, proposed_change, current
            )
        elif proposed_change.step_id == "costs":
            proposed = await self._calculate_costs_impact(
                version_id, proposed_change, current
            )
        else:
            # Unknown step type - return zero impact
            proposed = current

        # Calculate deltas
        metrics.fte_current = current["fte"]
        metrics.fte_proposed = proposed["fte"]
        metrics.fte_change = proposed["fte"] - current["fte"]

        metrics.cost_current_sar = current["costs"]
        metrics.cost_proposed_sar = proposed["costs"]
        metrics.cost_impact_sar = proposed["costs"] - current["costs"]

        metrics.revenue_current_sar = current["revenue"]
        metrics.revenue_proposed_sar = proposed["revenue"]
        metrics.revenue_impact_sar = proposed["revenue"] - current["revenue"]

        # Calculate margin impact
        if current["revenue"] > 0:
            metrics.margin_current_pct = float(
                (current["revenue"] - current["costs"]) / current["revenue"] * 100
            )
        if proposed["revenue"] > 0:
            metrics.margin_proposed_pct = float(
                (proposed["revenue"] - proposed["costs"]) / proposed["revenue"] * 100
            )
        metrics.margin_impact_pct = metrics.margin_proposed_pct - metrics.margin_current_pct

        # Determine affected steps
        metrics.affected_steps = self._get_affected_steps(proposed_change.step_id)

        return metrics

    async def _get_current_totals(self, version_id: UUID) -> dict[str, Any]:
        """Get current FTE, costs, and revenue totals for a budget version."""
        # Get total FTE from DHG
        fte_result = await self.session.execute(
            select(func.sum(DHGTeacherRequirement.simple_fte)).where(
                DHGTeacherRequirement.budget_version_id == version_id,
                DHGTeacherRequirement.deleted_at.is_(None),
            )
        )
        total_fte = fte_result.scalar() or 0.0

        # Get total costs from personnel cost plans
        costs_result = await self.session.execute(
            select(func.sum(PersonnelCostPlan.total_cost_sar)).where(
                PersonnelCostPlan.budget_version_id == version_id,
                PersonnelCostPlan.deleted_at.is_(None),
            )
        )
        total_costs = costs_result.scalar() or Decimal("0")

        # Get total revenue
        revenue_result = await self.session.execute(
            select(func.sum(RevenuePlan.amount_sar)).where(
                RevenuePlan.budget_version_id == version_id,
                RevenuePlan.deleted_at.is_(None),
            )
        )
        total_revenue = revenue_result.scalar() or Decimal("0")

        return {
            "fte": float(total_fte),
            "costs": Decimal(str(total_costs)),
            "revenue": Decimal(str(total_revenue)),
        }

    async def _calculate_enrollment_impact(
        self,
        version_id: UUID,
        change: ProposedChange,
        current: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate impact of enrollment change.

        Enrollment changes cascade to:
        - Class structure (more students = more classes)
        - DHG hours (more classes = more teaching hours)
        - Personnel costs (more FTE = more salary costs)
        - Revenue (more students = more tuition)
        """
        # Get current enrollment for the level
        level_id = change.dimension_id

        # Get current student count for this level
        enrollment_result = await self.session.execute(
            select(EnrollmentPlan.student_count).where(
                EnrollmentPlan.budget_version_id == version_id,
                EnrollmentPlan.level_id == level_id,
                EnrollmentPlan.deleted_at.is_(None),
            )
        )
        current_students = enrollment_result.scalar() or 0

        # Calculate change
        try:
            new_students = int(change.new_value)
        except (ValueError, TypeError):
            new_students = current_students

        student_delta = new_students - current_students

        # Simple estimation rules (can be refined based on actual business logic):
        # - Average tuition per student: ~45,000 SAR/year
        # - Students per FTE: ~15 students
        # - Cost per FTE: ~250,000 SAR/year

        avg_tuition = Decimal("45000")
        students_per_fte = 15
        cost_per_fte = Decimal("250000")

        # Calculate impacts
        fte_delta = student_delta / students_per_fte
        revenue_delta = Decimal(str(student_delta)) * avg_tuition
        cost_delta = Decimal(str(fte_delta)) * cost_per_fte

        return {
            "fte": current["fte"] + fte_delta,
            "costs": current["costs"] + cost_delta,
            "revenue": current["revenue"] + revenue_delta,
        }

    async def _calculate_class_structure_impact(
        self,
        version_id: UUID,
        change: ProposedChange,
        current: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate impact of class structure change.

        Class structure changes cascade to:
        - DHG hours (more classes = more teaching hours)
        - Personnel costs (more hours = more FTE)
        """
        # Get current class count for this level
        level_id = change.dimension_id

        class_result = await self.session.execute(
            select(ClassStructure.number_of_classes).where(
                ClassStructure.budget_version_id == version_id,
                ClassStructure.level_id == level_id,
                ClassStructure.deleted_at.is_(None),
            )
        )
        current_classes = class_result.scalar() or 0

        try:
            new_classes = int(change.new_value)
        except (ValueError, TypeError):
            new_classes = current_classes

        class_delta = new_classes - current_classes

        # Estimation: ~1.5 FTE per class, ~250,000 SAR per FTE
        fte_per_class = 1.5
        cost_per_fte = Decimal("250000")

        fte_delta = class_delta * fte_per_class
        cost_delta = Decimal(str(fte_delta)) * cost_per_fte

        return {
            "fte": current["fte"] + fte_delta,
            "costs": current["costs"] + cost_delta,
            "revenue": current["revenue"],  # Class changes don't directly affect revenue
        }

    async def _calculate_dhg_impact(
        self,
        version_id: UUID,
        change: ProposedChange,
        current: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate impact of DHG (workforce) change.

        DHG changes cascade to:
        - Personnel costs
        """
        # For DHG changes, we're typically changing FTE directly
        try:
            new_fte = float(change.new_value)
        except (ValueError, TypeError):
            return current

        # Get current FTE for this subject/level
        subject_id = change.dimension_id

        dhg_result = await self.session.execute(
            select(DHGTeacherRequirement.simple_fte).where(
                DHGTeacherRequirement.budget_version_id == version_id,
                DHGTeacherRequirement.subject_id == subject_id,
                DHGTeacherRequirement.deleted_at.is_(None),
            )
        )
        current_fte = dhg_result.scalar() or 0.0

        fte_delta = new_fte - current_fte

        # Cost per FTE
        cost_per_fte = Decimal("250000")
        cost_delta = Decimal(str(fte_delta)) * cost_per_fte

        return {
            "fte": current["fte"] + fte_delta,
            "costs": current["costs"] + cost_delta,
            "revenue": current["revenue"],  # DHG changes don't affect revenue
        }

    async def _calculate_revenue_impact(
        self,
        version_id: UUID,
        change: ProposedChange,
        current: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate impact of direct revenue change."""
        try:
            new_amount = Decimal(str(change.new_value))
        except (ValueError, TypeError):
            return current

        # Get current amount for this revenue line
        account_code = change.dimension_code

        revenue_result = await self.session.execute(
            select(RevenuePlan.amount_sar).where(
                RevenuePlan.budget_version_id == version_id,
                RevenuePlan.account_code == account_code,
                RevenuePlan.deleted_at.is_(None),
            )
        )
        current_amount = revenue_result.scalar() or Decimal("0")

        revenue_delta = new_amount - current_amount

        return {
            "fte": current["fte"],  # Revenue changes don't affect FTE
            "costs": current["costs"],  # Revenue changes don't affect costs
            "revenue": current["revenue"] + revenue_delta,
        }

    async def _calculate_costs_impact(
        self,
        version_id: UUID,
        change: ProposedChange,
        current: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate impact of direct cost change."""
        try:
            new_amount = Decimal(str(change.new_value))
        except (ValueError, TypeError):
            return current

        # Get current amount for this cost line
        account_code = change.dimension_code

        cost_result = await self.session.execute(
            select(PersonnelCostPlan.total_cost_sar).where(
                PersonnelCostPlan.budget_version_id == version_id,
                PersonnelCostPlan.account_code == account_code,
                PersonnelCostPlan.deleted_at.is_(None),
            )
        )
        current_amount = cost_result.scalar() or Decimal("0")

        cost_delta = new_amount - current_amount

        return {
            "fte": current["fte"],  # Direct cost changes don't affect FTE
            "costs": current["costs"] + cost_delta,
            "revenue": current["revenue"],  # Cost changes don't affect revenue
        }

    def _get_affected_steps(self, step_id: str) -> list[str]:
        """Get the list of steps affected by a change to the given step."""
        cascade_map = {
            "enrollment": ["class_structure", "dhg", "costs", "revenue"],
            "class_structure": ["dhg", "costs"],
            "dhg": ["costs"],
            "revenue": [],
            "costs": [],
            "capex": [],
        }
        return cascade_map.get(step_id, [])


async def calculate_budget_impact(
    session: AsyncSession,
    version_id: UUID,
    proposed_change: ProposedChange,
) -> ImpactMetrics:
    """
    Convenience function to calculate budget impact.

    Args:
        session: Database session
        version_id: Budget version UUID
        proposed_change: The proposed change

    Returns:
        ImpactMetrics with all calculated impacts
    """
    service = ImpactCalculatorService(session)
    return await service.calculate_impact(version_id, proposed_change)
