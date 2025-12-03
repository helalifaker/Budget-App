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
from app.models.configuration import BudgetVersion
from app.models.strategic import (
    ScenarioType,
)
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError
from app.services.strategic_service import StrategicService
from sqlalchemy.ext.asyncio import AsyncSession

# Skip tests for methods not yet implemented
SKIP_NOT_IMPLEMENTED = pytest.mark.skip(
    reason="Method not yet implemented in StrategicService"
)


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


# =============================================================================
# Tests for methods not yet implemented (skipped)
# =============================================================================


@SKIP_NOT_IMPLEMENTED
class TestCreateScenario:
    """Tests for scenario creation."""

    @pytest.mark.asyncio
    async def test_create_scenario_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful scenario creation."""
        pass


@SKIP_NOT_IMPLEMENTED
class TestGetScenarios:
    """Tests for retrieving scenarios."""

    @pytest.mark.asyncio
    async def test_get_scenarios_for_plan(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving scenarios for a plan."""
        pass


class TestProjectionCalculation:
    """Tests for projection calculations."""

    @pytest.mark.asyncio
    async def test_get_year_projections_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving year projections."""
        service = StrategicService(db_session)

        # Create plan with default scenarios
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Projection Test Plan",
        )

        # Get year projections
        result = await service.get_year_projections(
            plan_id=plan.id,
            scenario_type=ScenarioType.BASE_CASE,
            year=1,
        )

        assert result is not None


class TestStrategicInitiatives:
    """Tests for strategic initiative management."""

    @pytest.mark.asyncio
    async def test_add_initiative_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful initiative creation using add_initiative."""
        service = StrategicService(db_session)

        # Create plan
        plan = await service.create_strategic_plan(
            base_version_id=test_budget_version.id,
            plan_name="Initiative Test Plan",
        )

        # Add initiative
        result = await service.add_initiative(
            plan_id=plan.id,
            name="New Science Lab",
            description="Build a new science laboratory",
            capex_amount_sar=Decimal("500000.00"),
            planned_year=2,
        )

        assert result is not None
        assert result.name == "New Science Lab"


@SKIP_NOT_IMPLEMENTED
class TestGetInitiatives:
    """Tests for retrieving initiatives."""

    @pytest.mark.asyncio
    async def test_get_initiatives_for_plan(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving initiatives for a plan."""
        pass


@SKIP_NOT_IMPLEMENTED
class TestUpdateInitiativeStatus:
    """Tests for updating initiative status."""

    @pytest.mark.asyncio
    async def test_update_initiative_status(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test updating initiative status."""
        pass


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


@SKIP_NOT_IMPLEMENTED
class TestPlanSummary:
    """Tests for plan summary generation."""

    @pytest.mark.asyncio
    async def test_get_plan_summary(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test getting plan summary."""
        pass

    @pytest.mark.asyncio
    async def test_get_plan_summary_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test getting summary for non-existent plan."""
        pass
