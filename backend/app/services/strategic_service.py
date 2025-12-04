"""
Strategic Planning Service for multi-year financial planning.

Implements business logic for:
- Creating 5-year strategic plans
- Scenario modeling (conservative, base, optimistic)
- Year-over-year projections with growth assumptions
- Strategic initiative tracking
"""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.consolidation import BudgetConsolidation, ConsolidationCategory
from app.models.configuration import BudgetVersion
from app.models.strategic import (
    InitiativeStatus,
    ProjectionCategory,
    ScenarioType,
    StrategicInitiative,
    StrategicPlan,
    StrategicPlanProjection,
    StrategicPlanScenario,
)
from app.services.base import BaseService
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError


class StrategicService:
    """
    Service for 5-year strategic planning and scenario modeling.

    Provides methods for creating multi-year plans, managing scenarios,
    calculating projections, and tracking strategic initiatives.
    """

    # Default scenario assumptions
    DEFAULT_SCENARIOS = {
        ScenarioType.CONSERVATIVE: {
            "enrollment_growth_rate": Decimal("0.01"),  # 1% annual growth
            "fee_increase_rate": Decimal("0.02"),  # 2% annual increase
            "salary_inflation_rate": Decimal("0.025"),  # 2.5% annual inflation
            "operating_inflation_rate": Decimal("0.02"),  # 2% annual inflation
        },
        ScenarioType.BASE_CASE: {
            "enrollment_growth_rate": Decimal("0.04"),  # 4% annual growth
            "fee_increase_rate": Decimal("0.03"),  # 3% annual increase
            "salary_inflation_rate": Decimal("0.035"),  # 3.5% annual inflation
            "operating_inflation_rate": Decimal("0.025"),  # 2.5% annual inflation
        },
        ScenarioType.OPTIMISTIC: {
            "enrollment_growth_rate": Decimal("0.07"),  # 7% annual growth
            "fee_increase_rate": Decimal("0.04"),  # 4% annual increase
            "salary_inflation_rate": Decimal("0.04"),  # 4% annual inflation
            "operating_inflation_rate": Decimal("0.03"),  # 3% annual inflation
        },
    }

    def __init__(self, session: AsyncSession):
        """
        Initialize strategic service.

        Args:
            session: Async database session
        """
        self.session = session
        self.plan_service = BaseService(StrategicPlan, session)
        self.scenario_service = BaseService(StrategicPlanScenario, session)
        self.projection_service = BaseService(StrategicPlanProjection, session)
        self.initiative_service = BaseService(StrategicInitiative, session)

    async def create_strategic_plan(
        self,
        base_version_id: uuid.UUID,
        plan_name: str,
        description: str | None = None,
        years: int = 5,
        create_default_scenarios: bool = True,
    ) -> StrategicPlan:
        """
        Create a new 5-year strategic plan based on a budget version.

        Args:
            base_version_id: Base budget version UUID to use as Year 1
            plan_name: Name for strategic plan
            description: Optional plan description
            years: Number of years to plan (default: 5)
            create_default_scenarios: Whether to create default scenarios

        Returns:
            Created StrategicPlan instance with scenarios

        Raises:
            NotFoundError: If base version not found
            BusinessRuleError: If plan already exists
            ValidationError: If years out of range
        """
        # Validate years
        if years < 1 or years > 5:
            raise ValidationError("Strategic plan must be 1-5 years")

        # Get base budget version
        version_query = select(BudgetVersion).where(BudgetVersion.id == base_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(base_version_id))

        # Check for duplicate plan name
        existing_query = select(StrategicPlan).where(
            and_(
                StrategicPlan.name == plan_name,
                StrategicPlan.deleted_at.is_(None),
            )
        )
        existing_result = await self.session.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise BusinessRuleError(
                "duplicate_plan",
                f"Strategic plan '{plan_name}' already exists",
            )

        # Create plan
        plan = StrategicPlan(
            name=plan_name,
            description=description,
            base_year=version.fiscal_year,
            status="draft",
        )
        self.session.add(plan)
        await self.session.flush()
        await self.session.refresh(plan)

        # Create default scenarios if requested
        if create_default_scenarios:
            await self._create_default_scenarios(plan.id, base_version_id, years)

        # Reload with scenarios
        await self.session.refresh(plan)

        return plan

    async def get_strategic_plan(
        self,
        plan_id: uuid.UUID,
    ) -> StrategicPlan:
        """
        Get strategic plan by ID with all relationships.

        Args:
            plan_id: Strategic plan UUID

        Returns:
            StrategicPlan instance

        Raises:
            NotFoundError: If plan not found
        """
        query = (
            select(StrategicPlan)
            .where(
                and_(
                    StrategicPlan.id == plan_id,
                    StrategicPlan.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(StrategicPlan.scenarios).selectinload(
                    StrategicPlanScenario.projections
                ),
                selectinload(StrategicPlan.initiatives),
            )
        )

        result = await self.session.execute(query)
        plan = result.scalar_one_or_none()

        if not plan:
            raise NotFoundError("StrategicPlan", str(plan_id))

        return plan

    async def get_year_projections(
        self,
        plan_id: uuid.UUID,
        year: int,
        scenario_type: ScenarioType | None = None,
    ) -> dict[str, Any]:
        """
        Get financial projections for a specific year.

        Args:
            plan_id: Strategic plan UUID
            year: Year in plan (1-5)
            scenario_type: Optional filter by scenario type

        Returns:
            Dictionary with year projections:
                - year: Year number
                - fiscal_year: Actual fiscal year
                - scenarios: List of scenario projections

        Raises:
            NotFoundError: If plan not found
            ValidationError: If year out of range
        """
        # Validate year
        if year < 1 or year > 5:
            raise ValidationError("Year must be 1-5")

        # Get plan
        plan = await self.get_strategic_plan(plan_id)

        # Build query for projections
        query = (
            select(StrategicPlanScenario)
            .where(StrategicPlanScenario.strategic_plan_id == plan_id)
            .options(selectinload(StrategicPlanScenario.projections))
        )

        if scenario_type:
            query = query.where(StrategicPlanScenario.scenario_type == scenario_type)

        result = await self.session.execute(query)
        scenarios = result.scalars().all()

        # Extract projections for the specific year
        year_data = {
            "year": year,
            "fiscal_year": plan.base_year + year - 1,
            "scenarios": [],
        }

        for scenario in scenarios:
            scenario_data = {
                "scenario_type": scenario.scenario_type.value,
                "scenario_name": scenario.name,
                "projections": {},
            }

            # Get projections for this year
            year_projections = [
                p for p in scenario.projections if p.year == year
            ]

            for projection in year_projections:
                scenario_data["projections"][projection.category.value] = {
                    "amount_sar": float(projection.amount_sar),
                    "calculation_inputs": projection.calculation_inputs,
                }

            year_data["scenarios"].append(scenario_data)

        return year_data

    async def update_assumptions(
        self,
        scenario_id: uuid.UUID,
        enrollment_growth_rate: Decimal | None = None,
        fee_increase_rate: Decimal | None = None,
        salary_inflation_rate: Decimal | None = None,
        operating_inflation_rate: Decimal | None = None,
        recalculate_projections: bool = True,
    ) -> StrategicPlanScenario:
        """
        Update scenario growth assumptions.

        Args:
            scenario_id: Scenario UUID
            enrollment_growth_rate: Annual enrollment growth rate (optional)
            fee_increase_rate: Annual fee increase rate (optional)
            salary_inflation_rate: Annual salary inflation rate (optional)
            operating_inflation_rate: Annual operating cost inflation rate (optional)
            recalculate_projections: Whether to recalculate projections after update

        Returns:
            Updated StrategicPlanScenario instance

        Raises:
            NotFoundError: If scenario not found
        """
        scenario = await self.scenario_service.get_by_id(scenario_id)

        # Update assumptions
        if enrollment_growth_rate is not None:
            scenario.enrollment_growth_rate = enrollment_growth_rate
        if fee_increase_rate is not None:
            scenario.fee_increase_rate = fee_increase_rate
        if salary_inflation_rate is not None:
            scenario.salary_inflation_rate = salary_inflation_rate
        if operating_inflation_rate is not None:
            scenario.operating_inflation_rate = operating_inflation_rate

        await self.session.flush()
        await self.session.refresh(scenario)

        # Recalculate projections if requested
        if recalculate_projections:
            await self._recalculate_scenario_projections(scenario_id)
            await self.session.refresh(scenario)

        return scenario

    async def compare_scenarios(
        self,
        plan_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Compare all scenarios in a strategic plan.

        Args:
            plan_id: Strategic plan UUID

        Returns:
            Dictionary with scenario comparison data:
                - plan_name: Strategic plan name
                - base_year: Starting fiscal year
                - scenarios: List of scenario summaries
                - comparison_metrics: Side-by-side metrics

        Raises:
            NotFoundError: If plan not found
        """
        plan = await self.get_strategic_plan(plan_id)

        comparison = {
            "plan_id": str(plan.id),
            "plan_name": plan.name,
            "base_year": plan.base_year,
            "scenarios": [],
            "comparison_metrics": {},
        }

        for scenario in plan.scenarios:
            # Calculate scenario totals
            total_revenue = sum(
                p.amount_sar
                for p in scenario.projections
                if p.category == ProjectionCategory.REVENUE
            )
            total_personnel = sum(
                p.amount_sar
                for p in scenario.projections
                if p.category == ProjectionCategory.PERSONNEL_COSTS
            )
            total_operating = sum(
                p.amount_sar
                for p in scenario.projections
                if p.category == ProjectionCategory.OPERATING_COSTS
            )
            total_capex = sum(
                p.amount_sar
                for p in scenario.projections
                if p.category == ProjectionCategory.CAPEX
            )

            total_costs = total_personnel + total_operating
            net_result = total_revenue - total_costs

            scenario_summary = {
                "scenario_type": scenario.scenario_type.value,
                "scenario_name": scenario.name,
                "assumptions": {
                    "enrollment_growth": float(scenario.enrollment_growth_rate),
                    "fee_increase": float(scenario.fee_increase_rate),
                    "salary_inflation": float(scenario.salary_inflation_rate),
                    "operating_inflation": float(scenario.operating_inflation_rate),
                },
                "five_year_totals": {
                    "revenue_sar": float(total_revenue),
                    "personnel_costs_sar": float(total_personnel),
                    "operating_costs_sar": float(total_operating),
                    "total_costs_sar": float(total_costs),
                    "capex_sar": float(total_capex),
                    "net_result_sar": float(net_result),
                },
                "year_by_year": [],
            }

            # Get year-by-year breakdown
            for year in range(1, 6):
                year_projections = [
                    p for p in scenario.projections if p.year == year
                ]
                year_revenue = sum(
                    p.amount_sar
                    for p in year_projections
                    if p.category == ProjectionCategory.REVENUE
                )
                year_costs = sum(
                    p.amount_sar
                    for p in year_projections
                    if p.category in [ProjectionCategory.PERSONNEL_COSTS, ProjectionCategory.OPERATING_COSTS]
                )

                scenario_summary["year_by_year"].append({
                    "year": year,
                    "fiscal_year": plan.base_year + year - 1,
                    "revenue_sar": float(year_revenue),
                    "costs_sar": float(year_costs),
                    "margin_sar": float(year_revenue - year_costs),
                })

            comparison["scenarios"].append(scenario_summary)

        return comparison

    async def add_initiative(
        self,
        plan_id: uuid.UUID,
        name: str,
        description: str | None,
        planned_year: int,
        capex_amount_sar: Decimal,
        operating_impact_sar: Decimal = Decimal("0"),
        status: InitiativeStatus = InitiativeStatus.PLANNED,
    ) -> StrategicInitiative:
        """
        Add strategic initiative to a plan.

        Args:
            plan_id: Strategic plan UUID
            name: Initiative name
            description: Initiative description
            planned_year: Year in plan when initiative occurs (1-5)
            capex_amount_sar: One-time capital expenditure
            operating_impact_sar: Recurring annual operating cost impact
            status: Initiative status

        Returns:
            Created StrategicInitiative instance

        Raises:
            NotFoundError: If plan not found
            ValidationError: If year out of range
        """
        # Validate year
        if planned_year < 1 or planned_year > 5:
            raise ValidationError("Planned year must be 1-5")

        # Verify plan exists
        await self.plan_service.get_by_id(plan_id)

        # Create initiative
        initiative = StrategicInitiative(
            strategic_plan_id=plan_id,
            name=name,
            description=description,
            planned_year=planned_year,
            capex_amount_sar=capex_amount_sar,
            operating_impact_sar=operating_impact_sar,
            status=status,
        )

        self.session.add(initiative)
        await self.session.flush()
        await self.session.refresh(initiative)

        return initiative

    async def _create_default_scenarios(
        self,
        plan_id: uuid.UUID,
        base_version_id: uuid.UUID,
        years: int,
    ) -> None:
        """
        Create default scenarios for a strategic plan.

        Args:
            plan_id: Strategic plan UUID
            base_version_id: Base budget version UUID
            years: Number of years to project
        """
        for scenario_type, assumptions in self.DEFAULT_SCENARIOS.items():
            scenario = StrategicPlanScenario(
                strategic_plan_id=plan_id,
                scenario_type=scenario_type,
                name=f"{scenario_type.value.replace('_', ' ').title()} Scenario",
                description=f"{scenario_type.value.replace('_', ' ').title()} growth scenario",
                enrollment_growth_rate=assumptions["enrollment_growth_rate"],
                fee_increase_rate=assumptions["fee_increase_rate"],
                salary_inflation_rate=assumptions["salary_inflation_rate"],
                operating_inflation_rate=assumptions["operating_inflation_rate"],
                additional_assumptions={
                    "base_version_id": str(base_version_id),
                    "projection_years": years,
                },
            )

            self.session.add(scenario)
            await self.session.flush()
            await self.session.refresh(scenario)

            # Calculate projections for this scenario
            await self._calculate_scenario_projections(
                scenario.id, base_version_id, years
            )

    async def _calculate_scenario_projections(
        self,
        scenario_id: uuid.UUID,
        base_version_id: uuid.UUID,
        years: int,
    ) -> None:
        """
        Calculate financial projections for a scenario.

        Args:
            scenario_id: Scenario UUID
            base_version_id: Base budget version UUID for Year 1 data
            years: Number of years to project
        """
        # Get scenario
        scenario = await self.scenario_service.get_by_id(scenario_id)

        base_data = await self._get_base_projection_inputs(base_version_id)

        # Calculate projections for each year
        for year in range(1, years + 1):
            # Revenue projection
            if year == 1:
                revenue = base_data["revenue"]
            else:
                # Apply enrollment growth and fee increase
                growth_factor = (
                    (1 + scenario.enrollment_growth_rate) *
                    (1 + scenario.fee_increase_rate)
                )
                # Get previous year revenue
                prev_projection = await self._get_projection(
                    scenario_id, year - 1, ProjectionCategory.REVENUE
                )
                revenue = prev_projection.amount_sar * growth_factor if prev_projection else base_data["revenue"]

            revenue_projection = StrategicPlanProjection(
                strategic_plan_scenario_id=scenario_id,
                year=year,
                category=ProjectionCategory.REVENUE,
                amount_sar=revenue,
                calculation_inputs={
                    "base_amount": str(base_data["revenue"]),
                    "enrollment_growth": str(scenario.enrollment_growth_rate),
                    "fee_increase": str(scenario.fee_increase_rate),
                },
            )
            self.session.add(revenue_projection)

            # Personnel costs projection
            if year == 1:
                personnel = base_data["personnel_costs"]
            else:
                prev_projection = await self._get_projection(
                    scenario_id, year - 1, ProjectionCategory.PERSONNEL_COSTS
                )
                personnel = (
                    prev_projection.amount_sar * (1 + scenario.salary_inflation_rate)
                    if prev_projection
                    else base_data["personnel_costs"]
                )

            personnel_projection = StrategicPlanProjection(
                strategic_plan_scenario_id=scenario_id,
                year=year,
                category=ProjectionCategory.PERSONNEL_COSTS,
                amount_sar=personnel,
                calculation_inputs={
                    "base_amount": str(base_data["personnel_costs"]),
                    "salary_inflation": str(scenario.salary_inflation_rate),
                },
            )
            self.session.add(personnel_projection)

            # Operating costs projection
            if year == 1:
                operating = base_data["operating_costs"]
            else:
                prev_projection = await self._get_projection(
                    scenario_id, year - 1, ProjectionCategory.OPERATING_COSTS
                )
                operating = (
                    prev_projection.amount_sar * (1 + scenario.operating_inflation_rate)
                    if prev_projection
                    else base_data["operating_costs"]
                )

            operating_projection = StrategicPlanProjection(
                strategic_plan_scenario_id=scenario_id,
                year=year,
                category=ProjectionCategory.OPERATING_COSTS,
                amount_sar=operating,
                calculation_inputs={
                    "base_amount": str(base_data["operating_costs"]),
                    "operating_inflation": str(scenario.operating_inflation_rate),
                },
            )
            self.session.add(operating_projection)

        await self.session.flush()

    async def _recalculate_scenario_projections(
        self,
        scenario_id: uuid.UUID,
    ) -> None:
        """
        Recalculate projections for a scenario after assumption changes.

        Args:
            scenario_id: Scenario UUID
        """
        # Delete existing projections
        delete_query = select(StrategicPlanProjection).where(
            StrategicPlanProjection.strategic_plan_scenario_id == scenario_id
        )
        result = await self.session.execute(delete_query)
        existing_projections = result.scalars().all()

        for projection in existing_projections:
            await self.session.delete(projection)

        await self.session.flush()

        scenario = await self.scenario_service.get_by_id(scenario_id)
        assumptions = scenario.additional_assumptions or {}
        base_version_id_value = assumptions.get("base_version_id")
        if not base_version_id_value:
            raise BusinessRuleError(
                "missing_base_version",
                "Scenario is missing base budget version for projections",
            )

        try:
            base_version_id = uuid.UUID(str(base_version_id_value))
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid base_version_id in scenario assumptions") from exc

        years = int(assumptions.get("projection_years", 5))
        if years < 1 or years > 5:
            years = 5

        await self._calculate_scenario_projections(scenario_id, base_version_id, years)

    async def _get_projection(
        self,
        scenario_id: uuid.UUID,
        year: int,
        category: ProjectionCategory,
    ) -> StrategicPlanProjection | None:
        """
        Get specific projection for a scenario, year, and category.

        Args:
            scenario_id: Scenario UUID
            year: Year (1-5)
            category: Projection category

        Returns:
            StrategicPlanProjection or None
        """
        query = select(StrategicPlanProjection).where(
            and_(
                StrategicPlanProjection.strategic_plan_scenario_id == scenario_id,
                StrategicPlanProjection.year == year,
                StrategicPlanProjection.category == category,
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_base_projection_inputs(
        self,
        base_version_id: uuid.UUID,
    ) -> dict[str, Decimal]:
        """
        Aggregate Year 1 base amounts from consolidation tables.

        Args:
            base_version_id: Budget version to source Year 1 values

        Returns:
            Dictionary with revenue, personnel_costs, operating_costs, capex, depreciation
        """
        personnel_categories = [
            ConsolidationCategory.PERSONNEL_TEACHING,
            ConsolidationCategory.PERSONNEL_ADMIN,
            ConsolidationCategory.PERSONNEL_SUPPORT,
            ConsolidationCategory.PERSONNEL_SOCIAL,
        ]
        operating_categories = [
            ConsolidationCategory.OPERATING_SUPPLIES,
            ConsolidationCategory.OPERATING_UTILITIES,
            ConsolidationCategory.OPERATING_MAINTENANCE,
            ConsolidationCategory.OPERATING_INSURANCE,
            ConsolidationCategory.OPERATING_OTHER,
        ]
        capex_categories = [
            ConsolidationCategory.CAPEX_EQUIPMENT,
            ConsolidationCategory.CAPEX_IT,
            ConsolidationCategory.CAPEX_FURNITURE,
            ConsolidationCategory.CAPEX_BUILDING,
            ConsolidationCategory.CAPEX_SOFTWARE,
        ]

        def _to_decimal(value: Any) -> Decimal:
            return Decimal("0") if value is None else Decimal(str(value))

        revenue_query = select(func.coalesce(func.sum(BudgetConsolidation.amount_sar), 0)).where(
            and_(
                BudgetConsolidation.budget_version_id == base_version_id,
                BudgetConsolidation.is_revenue.is_(True),
            )
        )
        personnel_query = select(func.coalesce(func.sum(BudgetConsolidation.amount_sar), 0)).where(
            and_(
                BudgetConsolidation.budget_version_id == base_version_id,
                BudgetConsolidation.consolidation_category.in_(personnel_categories),
            )
        )
        operating_query = select(func.coalesce(func.sum(BudgetConsolidation.amount_sar), 0)).where(
            and_(
                BudgetConsolidation.budget_version_id == base_version_id,
                BudgetConsolidation.consolidation_category.in_(operating_categories),
            )
        )
        capex_query = select(func.coalesce(func.sum(BudgetConsolidation.amount_sar), 0)).where(
            and_(
                BudgetConsolidation.budget_version_id == base_version_id,
                BudgetConsolidation.consolidation_category.in_(capex_categories),
            )
        )

        revenue = _to_decimal((await self.session.execute(revenue_query)).scalar())
        personnel_costs = _to_decimal((await self.session.execute(personnel_query)).scalar())
        operating_costs = _to_decimal((await self.session.execute(operating_query)).scalar())
        capex = _to_decimal((await self.session.execute(capex_query)).scalar())

        return {
            "revenue": revenue,
            "personnel_costs": personnel_costs,
            "operating_costs": operating_costs,
            "capex": capex,
            "depreciation": Decimal("0"),
        }
