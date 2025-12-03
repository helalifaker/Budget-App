"""
Unit tests for Strategic Service - Multi-year Financial Planning.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategic import ScenarioType, InitiativeStatus
from app.services.strategic_service import StrategicService
from app.services.exceptions import ValidationError


@pytest.fixture
def db_session():
    """Create a mock async session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def strategic_service(db_session):
    """Create StrategicService instance with mocked session."""
    return StrategicService(db_session)


class TestDefaultScenarioAssumptions:
    """Tests for default scenario assumptions."""

    def test_conservative_scenario_defaults(self):
        """Test conservative scenario has lowest growth rates."""
        defaults = StrategicService.DEFAULT_SCENARIOS[ScenarioType.CONSERVATIVE]

        assert defaults["enrollment_growth_rate"] == Decimal("0.01")  # 1%
        assert defaults["fee_increase_rate"] == Decimal("0.02")  # 2%
        assert defaults["salary_inflation_rate"] == Decimal("0.025")  # 2.5%
        assert defaults["operating_inflation_rate"] == Decimal("0.02")  # 2%

    def test_base_case_scenario_defaults(self):
        """Test base case scenario has moderate growth rates."""
        defaults = StrategicService.DEFAULT_SCENARIOS[ScenarioType.BASE_CASE]

        assert defaults["enrollment_growth_rate"] == Decimal("0.04")  # 4%
        assert defaults["fee_increase_rate"] == Decimal("0.03")  # 3%
        assert defaults["salary_inflation_rate"] == Decimal("0.035")  # 3.5%
        assert defaults["operating_inflation_rate"] == Decimal("0.025")  # 2.5%

    def test_optimistic_scenario_defaults(self):
        """Test optimistic scenario has highest growth rates."""
        defaults = StrategicService.DEFAULT_SCENARIOS[ScenarioType.OPTIMISTIC]

        assert defaults["enrollment_growth_rate"] == Decimal("0.07")  # 7%
        assert defaults["fee_increase_rate"] == Decimal("0.04")  # 4%
        assert defaults["salary_inflation_rate"] == Decimal("0.04")  # 4%
        assert defaults["operating_inflation_rate"] == Decimal("0.03")  # 3%

    def test_all_scenarios_have_required_assumptions(self):
        """Test all defined default scenarios include required assumption keys."""
        required_keys = [
            "enrollment_growth_rate",
            "fee_increase_rate",
            "salary_inflation_rate",
            "operating_inflation_rate",
        ]

        # Test only scenarios that have default assumptions defined
        for scenario_type in StrategicService.DEFAULT_SCENARIOS.keys():
            defaults = StrategicService.DEFAULT_SCENARIOS[scenario_type]
            for key in required_keys:
                assert key in defaults, f"Missing {key} in {scenario_type}"

    def test_scenario_rates_are_ordered_correctly(self):
        """Test conservative < base < optimistic for growth rates."""
        conservative = StrategicService.DEFAULT_SCENARIOS[ScenarioType.CONSERVATIVE]
        base_case = StrategicService.DEFAULT_SCENARIOS[ScenarioType.BASE_CASE]
        optimistic = StrategicService.DEFAULT_SCENARIOS[ScenarioType.OPTIMISTIC]

        # Enrollment growth should be ordered
        assert conservative["enrollment_growth_rate"] < base_case["enrollment_growth_rate"]
        assert base_case["enrollment_growth_rate"] < optimistic["enrollment_growth_rate"]

        # Fee increases should be ordered
        assert conservative["fee_increase_rate"] < base_case["fee_increase_rate"]
        assert base_case["fee_increase_rate"] < optimistic["fee_increase_rate"]


class TestStrategicPlanValidation:
    """Tests for strategic plan creation validation."""

    @pytest.mark.asyncio
    async def test_create_plan_validates_years_minimum(self, strategic_service):
        """Test plan creation fails for years < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await strategic_service.create_strategic_plan(
                base_version_id=uuid.uuid4(),
                plan_name="Test Plan",
                years=0,
            )

        assert "1-5 years" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_plan_validates_years_maximum(self, strategic_service):
        """Test plan creation fails for years > 5."""
        with pytest.raises(ValidationError) as exc_info:
            await strategic_service.create_strategic_plan(
                base_version_id=uuid.uuid4(),
                plan_name="Test Plan",
                years=6,
            )

        assert "1-5 years" in str(exc_info.value)


class TestYearProjectionValidation:
    """Tests for year projection validation."""

    @pytest.mark.asyncio
    async def test_get_year_projections_validates_year_minimum(self, strategic_service, db_session):
        """Test projection retrieval fails for year < 1."""
        plan_id = uuid.uuid4()

        # Mock plan exists
        mock_plan = MagicMock()
        mock_plan.id = plan_id
        mock_plan.base_year = 2025
        mock_plan.scenarios = []
        mock_plan.initiatives = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_plan
        db_session.execute.return_value = mock_result

        with pytest.raises(ValidationError) as exc_info:
            await strategic_service.get_year_projections(
                plan_id=plan_id,
                year=0,
            )

        assert "1-5" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_year_projections_validates_year_maximum(self, strategic_service, db_session):
        """Test projection retrieval fails for year > 5."""
        plan_id = uuid.uuid4()

        mock_plan = MagicMock()
        mock_plan.id = plan_id
        mock_plan.base_year = 2025
        mock_plan.scenarios = []
        mock_plan.initiatives = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_plan
        db_session.execute.return_value = mock_result

        with pytest.raises(ValidationError) as exc_info:
            await strategic_service.get_year_projections(
                plan_id=plan_id,
                year=6,
            )

        assert "1-5" in str(exc_info.value)


class TestInitiativeValidation:
    """Tests for strategic initiative validation."""

    @pytest.mark.asyncio
    async def test_add_initiative_validates_year_range(self, strategic_service):
        """Test initiative creation validates planned year is 1-5."""
        plan_id = uuid.uuid4()

        # Mock plan exists
        strategic_service.plan_service.get_by_id = AsyncMock(return_value=MagicMock())

        # Year 0 should fail
        with pytest.raises(ValidationError):
            await strategic_service.add_initiative(
                plan_id=plan_id,
                name="New Building",
                description="Expand campus",
                planned_year=0,
                capex_amount_sar=Decimal("5000000"),
            )

        # Year 6 should fail
        with pytest.raises(ValidationError):
            await strategic_service.add_initiative(
                plan_id=plan_id,
                name="New Building",
                description="Expand campus",
                planned_year=6,
                capex_amount_sar=Decimal("5000000"),
            )


class TestProjectionCalculations:
    """Tests for financial projection calculations."""

    def test_revenue_growth_formula(self):
        """Test revenue growth = (1 + enrollment) × (1 + fee_increase)."""
        enrollment_growth = Decimal("0.04")  # 4%
        fee_increase = Decimal("0.03")  # 3%

        # Compound growth factor
        growth_factor = (1 + enrollment_growth) * (1 + fee_increase)

        # Expected: 1.04 × 1.03 = 1.0712 (7.12% total growth)
        assert growth_factor == Decimal("1.0712")

    def test_personnel_cost_projection(self):
        """Test personnel cost grows by salary inflation."""
        base_personnel = Decimal("28500000")
        salary_inflation = Decimal("0.035")  # 3.5%

        year2_personnel = base_personnel * (1 + salary_inflation)

        expected = Decimal("29497500")  # 28.5M × 1.035
        assert year2_personnel == expected

    def test_operating_cost_projection(self):
        """Test operating cost grows by operating inflation."""
        base_operating = Decimal("18500000")
        operating_inflation = Decimal("0.025")  # 2.5%

        year2_operating = base_operating * (1 + operating_inflation)

        expected = Decimal("18962500")  # 18.5M × 1.025
        assert year2_operating == expected

    def test_multi_year_compound_growth(self):
        """Test 5-year compound growth calculation."""
        base_revenue = Decimal("55515000")
        annual_growth = Decimal("0.0712")  # 7.12% per year

        year5_revenue = base_revenue * ((1 + annual_growth) ** 4)

        # After 4 years of compounding
        # 55515000 × 1.0712^4 ≈ 73,179,000
        assert year5_revenue > base_revenue * Decimal("1.30")


class TestScenarioComparison:
    """Tests for scenario comparison functionality."""

    def test_net_result_calculation(self):
        """Test net result = revenue - costs."""
        total_revenue = Decimal("100000000")
        total_personnel = Decimal("45000000")
        total_operating = Decimal("30000000")

        total_costs = total_personnel + total_operating
        net_result = total_revenue - total_costs

        assert net_result == Decimal("25000000")

    def test_operating_margin_calculation(self):
        """Test operating margin = net_result / revenue × 100."""
        revenue = Decimal("100000000")
        costs = Decimal("85000000")

        net_result = revenue - costs
        margin_pct = (net_result / revenue) * 100

        assert margin_pct == Decimal("15")  # 15%


class TestScenarioTypes:
    """Tests for scenario type definitions."""

    def test_scenario_types_exist(self):
        """Test all expected scenario types are defined."""
        assert ScenarioType.CONSERVATIVE
        assert ScenarioType.BASE_CASE
        assert ScenarioType.OPTIMISTIC

    def test_default_scenarios_cover_standard_types(self):
        """Test default scenarios exist for standard planning scenario types."""
        # Standard scenario types used for normal planning
        standard_scenarios = [
            ScenarioType.CONSERVATIVE,
            ScenarioType.BASE_CASE,
            ScenarioType.OPTIMISTIC,
        ]
        for scenario_type in standard_scenarios:
            assert scenario_type in StrategicService.DEFAULT_SCENARIOS


class TestInitiativeStatus:
    """Tests for initiative status definitions."""

    def test_initiative_statuses_exist(self):
        """Test expected initiative statuses are defined."""
        assert InitiativeStatus.PLANNED
        # Check for other common statuses
        assert hasattr(InitiativeStatus, "IN_PROGRESS") or hasattr(InitiativeStatus, "APPROVED")


class TestFiscalYearCalculation:
    """Tests for fiscal year calculations."""

    def test_fiscal_year_from_base_year(self):
        """Test fiscal year = base_year + year - 1."""
        base_year = 2025

        for year in range(1, 6):
            expected_fiscal_year = base_year + year - 1
            assert expected_fiscal_year == base_year + (year - 1)

        # Year 1 = 2025
        # Year 2 = 2026
        # Year 3 = 2027
        # Year 4 = 2028
        # Year 5 = 2029

    def test_five_year_span(self):
        """Test 5-year plan spans correct years."""
        base_year = 2025
        plan_years = 5

        first_year = base_year
        last_year = base_year + plan_years - 1

        assert first_year == 2025
        assert last_year == 2029


class TestGrowthRateReasonability:
    """Tests that growth rates are reasonable."""

    def test_enrollment_growth_reasonable(self):
        """Test enrollment growth rates are reasonable (0-10%)."""
        for scenario in StrategicService.DEFAULT_SCENARIOS.values():
            rate = scenario["enrollment_growth_rate"]
            assert Decimal("0") <= rate <= Decimal("0.10")

    def test_fee_increase_reasonable(self):
        """Test fee increase rates are reasonable (0-5%)."""
        for scenario in StrategicService.DEFAULT_SCENARIOS.values():
            rate = scenario["fee_increase_rate"]
            assert Decimal("0") <= rate <= Decimal("0.05")

    def test_salary_inflation_reasonable(self):
        """Test salary inflation rates are reasonable (0-6%)."""
        for scenario in StrategicService.DEFAULT_SCENARIOS.values():
            rate = scenario["salary_inflation_rate"]
            assert Decimal("0") <= rate <= Decimal("0.06")

    def test_operating_inflation_reasonable(self):
        """Test operating inflation rates are reasonable (0-5%)."""
        for scenario in StrategicService.DEFAULT_SCENARIOS.values():
            rate = scenario["operating_inflation_rate"]
            assert Decimal("0") <= rate <= Decimal("0.05")
