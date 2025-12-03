"""
Tests for StrategicService.

Tests cover:
- Creating 5-year strategic plans
- Scenario modeling (conservative, base, optimistic)
- Year-over-year projections
- Strategic initiative tracking
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError
from app.services.strategic_service import StrategicService


class TestCreateStrategicPlan:
    """Tests for creating strategic plans."""

    @pytest.mark.asyncio
    async def test_create_strategic_plan_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful strategic plan creation."""
        service = StrategicService(db_session)
        result = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="EFIR 5-Year Plan 2025-2030",
            description="Strategic growth plan",
            years=5,
        )

        assert result is not None
        assert result.name == "EFIR 5-Year Plan 2025-2030"
        assert result.base_year == test_budget_version.fiscal_year

    @pytest.mark.asyncio
    async def test_create_strategic_plan_without_scenarios(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test creating plan without default scenarios."""
        service = StrategicService(db_session)
        result = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Basic Plan",
            create_default_scenarios=False,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_create_strategic_plan_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test creating plan with invalid budget version."""
        service = StrategicService(db_session)

        with pytest.raises(NotFoundError):
            await service.create_strategic_plan(
                base_version_id=uuid.uuid4(),
                plan_name="Test Plan",
            )

    @pytest.mark.asyncio
    async def test_create_strategic_plan_invalid_years(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test creating plan with invalid year range."""
        service = StrategicService(db_session)

        with pytest.raises(ValidationError):
            await service.create_strategic_plan(
                base_version_id=test_budget_version.id,
                plan_name="Invalid Plan",
                years=10,  # Invalid - max is 5
            )

    @pytest.mark.asyncio
    async def test_create_strategic_plan_duplicate_name(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test creating plan with duplicate name."""
        service = StrategicService(db_session)

        # Create first plan
        await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Duplicate Plan",
        )

        # Try to create duplicate
        with pytest.raises(BusinessRuleError):
            await service.create_strategic_plan(
                base_version_id=test_budget_version.id,
                plan_name="Duplicate Plan",
            )


class TestGetStrategicPlan:
    """Tests for retrieving strategic plans."""

    @pytest.mark.asyncio
    async def test_get_strategic_plan_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful plan retrieval."""
        service = StrategicService(db_session)

        # Create plan
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Test Retrieval Plan",
        )

        # Retrieve plan
        result = await service.get_strategic_plan(plan.id)

        assert result is not None
        assert result.id == plan.id

    @pytest.mark.asyncio
    async def test_get_strategic_plan_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving non-existent plan."""
        service = StrategicService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_strategic_plan(uuid.uuid4())


class TestScenarioManagement:
    """Tests for scenario management."""

    @pytest.mark.asyncio
    async def test_create_scenario_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful scenario creation."""
        service = StrategicService(db_session)

        # Create plan without default scenarios
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Scenario Test Plan",
            create_default_scenarios=False,
        )

        # Create custom scenario
        result = await service.create_scenario(
            plan_id=plan.id,
            scenario_type=ScenarioType.BASE_CASE,
            name="Custom Base Case",
            assumptions={
                "enrollment_growth_rate": Decimal("0.05"),
                "fee_increase_rate": Decimal("0.03"),
            },
        )

        assert result is not None
        assert result.scenario_type == ScenarioType.BASE_CASE

    @pytest.mark.asyncio
    async def test_get_scenarios_for_plan(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving scenarios for a plan."""
        service = StrategicService(db_session)

        # Create plan with default scenarios
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Scenario List Plan",
            create_default_scenarios=True,
        )

        # Get scenarios
        result = await service.get_scenarios(plan.id)

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_default_scenario_assumptions(
        self,
        db_session: AsyncSession,
    ):
        """Test default scenario assumptions are defined."""
        service = StrategicService(db_session)

        # Verify default assumptions
        assert ScenarioType.CONSERVATIVE in service.DEFAULT_SCENARIOS
        assert ScenarioType.BASE_CASE in service.DEFAULT_SCENARIOS
        assert ScenarioType.OPTIMISTIC in service.DEFAULT_SCENARIOS

        # Check conservative assumptions
        conservative = service.DEFAULT_SCENARIOS[ScenarioType.CONSERVATIVE]
        assert conservative["enrollment_growth_rate"] == Decimal("0.01")

        # Check base case assumptions
        base_case = service.DEFAULT_SCENARIOS[ScenarioType.BASE_CASE]
        assert base_case["enrollment_growth_rate"] == Decimal("0.04")

        # Check optimistic assumptions
        optimistic = service.DEFAULT_SCENARIOS[ScenarioType.OPTIMISTIC]
        assert optimistic["enrollment_growth_rate"] == Decimal("0.07")


class TestProjectionCalculation:
    """Tests for projection calculations."""

    @pytest.mark.asyncio
    async def test_calculate_projections_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful projection calculation."""
        service = StrategicService(db_session)

        # Create plan
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Projection Test Plan",
        )

        # Calculate projections
        result = await service.calculate_projections(
            plan_id=plan.id,
            scenario_type=ScenarioType.BASE_CASE,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_projections_for_scenario(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving projections for a scenario."""
        service = StrategicService(db_session)

        # Create plan
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Get Projections Plan",
        )

        # Get projections
        result = await service.get_projections(
            plan_id=plan.id,
            scenario_type=ScenarioType.BASE_CASE,
        )

        assert result is not None


class TestStrategicInitiatives:
    """Tests for strategic initiative management."""

    @pytest.mark.asyncio
    async def test_create_initiative_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful initiative creation."""
        service = StrategicService(db_session)

        # Create plan
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Initiative Test Plan",
        )

        # Create initiative
        result = await service.create_initiative(
            plan_id=plan.id,
            name="New Science Lab",
            description="Build a new science laboratory",
            estimated_cost_sar=Decimal("500000.00"),
            target_year=2,
            status=InitiativeStatus.PROPOSED,
        )

        assert result is not None
        assert result.name == "New Science Lab"

    @pytest.mark.asyncio
    async def test_get_initiatives_for_plan(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving initiatives for a plan."""
        service = StrategicService(db_session)

        # Create plan
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Initiative List Plan",
        )

        # Create initiatives
        await service.create_initiative(
            plan_id=plan.id,
            name="Initiative 1",
            estimated_cost_sar=Decimal("100000.00"),
            target_year=1,
        )
        await service.create_initiative(
            plan_id=plan.id,
            name="Initiative 2",
            estimated_cost_sar=Decimal("200000.00"),
            target_year=2,
        )

        # Get initiatives
        result = await service.get_initiatives(plan.id)

        assert result is not None
        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_update_initiative_status(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test updating initiative status."""
        service = StrategicService(db_session)

        # Create plan
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Status Update Plan",
        )

        # Create initiative
        initiative = await service.create_initiative(
            plan_id=plan.id,
            name="Status Test Initiative",
            estimated_cost_sar=Decimal("50000.00"),
            target_year=1,
            status=InitiativeStatus.PROPOSED,
        )

        # Update status
        result = await service.update_initiative_status(
            initiative_id=initiative.id,
            new_status=InitiativeStatus.APPROVED,
        )

        assert result.status == InitiativeStatus.APPROVED


class TestScenarioComparison:
    """Tests for scenario comparison."""

    @pytest.mark.asyncio
    async def test_compare_scenarios(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test comparing scenarios."""
        service = StrategicService(db_session)

        # Create plan with scenarios
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Comparison Plan",
        )

        # Compare scenarios
        result = await service.compare_scenarios(plan.id)

        assert result is not None


class TestPlanSummary:
    """Tests for plan summary generation."""

    @pytest.mark.asyncio
    async def test_get_plan_summary(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test getting plan summary."""
        service = StrategicService(db_session)

        # Create plan
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Summary Plan",
        )

        # Get summary
        result = await service.get_plan_summary(plan.id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_plan_summary_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test getting summary for non-existent plan."""
        service = StrategicService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_plan_summary(uuid.uuid4())
