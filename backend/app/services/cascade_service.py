"""
Cascade Service - Auto-recalculation of dependent planning steps

When a planning step is saved, this service can trigger recalculation
of all downstream dependent steps in the correct order.

Cascade dependencies:
- Enrollment → Class Structure → DHG → Costs
- Enrollment → Revenue
- DHG → Costs
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

# Cascade dependency map: which steps need recalculation when a step changes
# Key: step_id, Value: list of steps that depend on this step
CASCADE_DEPENDENCIES: dict[str, list[str]] = {
    "enrollment": ["class_structure", "revenue"],
    "class_structure": ["dhg"],
    "dhg": ["costs"],
    "revenue": [],
    "costs": [],
    "capex": [],
}

# Calculation order for each step (topologically sorted)
CALCULATION_ORDER = [
    "enrollment",
    "class_structure",
    "dhg",
    "revenue",
    "costs",
    "capex",
]


def get_downstream_steps(step_id: str, visited: set[str] | None = None) -> list[str]:
    """
    Get all downstream steps that need recalculation (recursively).
    Returns steps in topological order for correct execution sequence.
    """
    if visited is None:
        visited = set()

    if step_id in visited:
        return []
    visited.add(step_id)

    direct_deps = CASCADE_DEPENDENCIES.get(step_id, [])
    all_deps: list[str] = []

    for dep in direct_deps:
        all_deps.append(dep)
        all_deps.extend(get_downstream_steps(dep, visited))

    # Remove duplicates while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for dep in all_deps:
        if dep not in seen:
            seen.add(dep)
            result.append(dep)

    # Sort by calculation order to ensure correct sequence
    return sorted(result, key=lambda x: CALCULATION_ORDER.index(x) if x in CALCULATION_ORDER else 999)


class CascadeResult:
    """Result of a cascade recalculation operation."""

    def __init__(self) -> None:
        self.recalculated_steps: list[str] = []
        self.failed_steps: list[str] = []
        self.errors: dict[str, str] = {}

    @property
    def message(self) -> str:
        """Generate a summary message."""
        if not self.failed_steps:
            return f"Successfully recalculated {len(self.recalculated_steps)} step(s)"
        return f"Recalculated {len(self.recalculated_steps)} step(s), {len(self.failed_steps)} failed"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "recalculated_steps": self.recalculated_steps,
            "failed_steps": self.failed_steps,
            "message": self.message,
        }


class CascadeService:
    """Service for cascading recalculations through planning steps."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def recalculate_from_step(
        self,
        version_id: UUID,
        from_step_id: str,
    ) -> CascadeResult:
        """
        Recalculate all steps downstream from a given step.

        Args:
            version_id: Budget version UUID
            from_step_id: The step that changed (will recalculate all downstream)

        Returns:
            CascadeResult with recalculated and failed steps
        """
        result = CascadeResult()

        # Get downstream steps in correct order
        downstream_steps = get_downstream_steps(from_step_id)

        if not downstream_steps:
            return result

        # Import calculation services here to avoid circular imports
        from app.services.class_structure_service import ClassStructureService
        from app.services.cost_service import CostService
        from app.services.dhg_service import DHGService
        from app.services.revenue_service import RevenueService

        # Service mapping
        step_services = {
            "class_structure": ClassStructureService,
            "dhg": DHGService,
            "revenue": RevenueService,
            "costs": CostService,
        }

        # Recalculate each downstream step in order
        for step_id in downstream_steps:
            try:
                service_class = step_services.get(step_id)
                if service_class:
                    service = service_class(self.session)
                    await service.calculate(version_id)
                    result.recalculated_steps.append(step_id)
                else:
                    # No service for this step (e.g., capex is manual)
                    result.recalculated_steps.append(step_id)
            except Exception as e:
                result.failed_steps.append(step_id)
                result.errors[step_id] = str(e)

        return result

    async def recalculate_steps(
        self,
        version_id: UUID,
        step_ids: list[str],
    ) -> CascadeResult:
        """
        Recalculate specific steps in the correct order.

        Args:
            version_id: Budget version UUID
            step_ids: List of step IDs to recalculate

        Returns:
            CascadeResult with recalculated and failed steps
        """
        result = CascadeResult()

        # Sort steps by calculation order
        sorted_steps = sorted(
            step_ids,
            key=lambda x: CALCULATION_ORDER.index(x) if x in CALCULATION_ORDER else 999
        )

        # Import calculation services here to avoid circular imports
        from app.services.class_structure_service import ClassStructureService
        from app.services.cost_service import CostService
        from app.services.dhg_service import DHGService
        from app.services.revenue_service import RevenueService

        # Service mapping
        step_services = {
            "class_structure": ClassStructureService,
            "dhg": DHGService,
            "revenue": RevenueService,
            "costs": CostService,
        }

        # Recalculate each step in order
        for step_id in sorted_steps:
            try:
                service_class = step_services.get(step_id)
                if service_class:
                    service = service_class(self.session)
                    await service.calculate(version_id)
                    result.recalculated_steps.append(step_id)
            except Exception as e:
                result.failed_steps.append(step_id)
                result.errors[step_id] = str(e)

        return result
