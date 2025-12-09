"""
Tests for Impact Calculator Service

Tests cover:
- Impact metrics calculation for different planning steps
- FTE change calculations
- Cost impact calculations
- Revenue impact calculations
- Margin impact calculations
- Affected steps determination
- Current totals retrieval
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.services.impact_calculator_service import (
    ImpactCalculatorService,
    ImpactMetrics,
    ProposedChange,
    calculate_budget_impact,
)


class TestProposedChange:
    """Tests for ProposedChange model."""

    def test_create_enrollment_change(self):
        """Test creating an enrollment change."""
        change = ProposedChange(
            step_id="enrollment",
            dimension_type="level",
            dimension_id="level-123",
            field_name="student_count",
            new_value=150,
        )
        assert change.step_id == "enrollment"
        assert change.dimension_type == "level"
        assert change.new_value == 150

    def test_create_revenue_change(self):
        """Test creating a revenue change."""
        change = ProposedChange(
            step_id="revenue",
            dimension_type="account_code",
            dimension_code="70100",
            field_name="annual_amount",
            new_value=1000000,
        )
        assert change.step_id == "revenue"
        assert change.dimension_code == "70100"

    def test_create_dhg_change(self):
        """Test creating a DHG change."""
        change = ProposedChange(
            step_id="dhg",
            dimension_type="subject",
            dimension_id="subject-abc",
            field_name="fte_required",
            new_value=2.5,
        )
        assert change.step_id == "dhg"
        assert change.new_value == 2.5


class TestImpactMetrics:
    """Tests for ImpactMetrics model."""

    def test_default_values(self):
        """Test default values are zero."""
        metrics = ImpactMetrics()
        assert metrics.fte_change == 0.0
        assert metrics.fte_current == 0.0
        assert metrics.fte_proposed == 0.0
        assert metrics.cost_impact_sar == Decimal("0")
        assert metrics.revenue_impact_sar == Decimal("0")
        assert metrics.margin_impact_pct == 0.0
        assert metrics.affected_steps == []

    def test_with_values(self):
        """Test creating metrics with values."""
        metrics = ImpactMetrics(
            fte_change=2.5,
            fte_current=50.0,
            fte_proposed=52.5,
            cost_impact_sar=Decimal("500000"),
            cost_current_sar=Decimal("10000000"),
            cost_proposed_sar=Decimal("10500000"),
            revenue_impact_sar=Decimal("600000"),
            revenue_current_sar=Decimal("15000000"),
            revenue_proposed_sar=Decimal("15600000"),
            margin_impact_pct=0.5,
            margin_current_pct=33.3,
            margin_proposed_pct=33.8,
            affected_steps=["dhg", "costs"],
        )
        assert metrics.fte_change == 2.5
        assert metrics.cost_impact_sar == Decimal("500000")
        assert len(metrics.affected_steps) == 2


class TestImpactCalculatorService:
    """Tests for ImpactCalculatorService class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance with mock session."""
        return ImpactCalculatorService(mock_session)

    @pytest.fixture
    def sample_version_id(self):
        """Create a sample version UUID."""
        return uuid4()

    def test_service_initialization(self, mock_session):
        """Test service initialization."""
        service = ImpactCalculatorService(mock_session)
        assert service.session == mock_session

    def test_get_affected_steps_enrollment(self, service):
        """Test affected steps for enrollment changes."""
        affected = service._get_affected_steps("enrollment")
        assert "class_structure" in affected
        assert "dhg" in affected
        assert "costs" in affected
        assert "revenue" in affected

    def test_get_affected_steps_class_structure(self, service):
        """Test affected steps for class structure changes."""
        affected = service._get_affected_steps("class_structure")
        assert "dhg" in affected
        assert "costs" in affected

    def test_get_affected_steps_dhg(self, service):
        """Test affected steps for DHG changes."""
        affected = service._get_affected_steps("dhg")
        assert "costs" in affected

    def test_get_affected_steps_revenue(self, service):
        """Test affected steps for revenue changes (no downstream)."""
        affected = service._get_affected_steps("revenue")
        assert affected == []

    def test_get_affected_steps_costs(self, service):
        """Test affected steps for cost changes (no downstream)."""
        affected = service._get_affected_steps("costs")
        assert affected == []

    def test_get_affected_steps_unknown(self, service):
        """Test affected steps for unknown step type."""
        affected = service._get_affected_steps("unknown_step")
        assert affected == []

    @pytest.mark.asyncio
    async def test_get_current_totals(self, service, mock_session, sample_version_id):
        """Test getting current totals."""
        # Mock FTE query result
        mock_fte_result = MagicMock()
        mock_fte_result.scalar.return_value = 50.0

        # Mock costs query result
        mock_costs_result = MagicMock()
        mock_costs_result.scalar.return_value = Decimal("10000000")

        # Mock revenue query result
        mock_revenue_result = MagicMock()
        mock_revenue_result.scalar.return_value = Decimal("15000000")

        mock_session.execute.side_effect = [
            mock_fte_result,
            mock_costs_result,
            mock_revenue_result,
        ]

        totals = await service._get_current_totals(sample_version_id)

        assert totals["fte"] == 50.0
        assert totals["costs"] == Decimal("10000000")
        assert totals["revenue"] == Decimal("15000000")

    @pytest.mark.asyncio
    async def test_get_current_totals_with_nulls(
        self, service, mock_session, sample_version_id
    ):
        """Test getting current totals when values are null."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        totals = await service._get_current_totals(sample_version_id)

        assert totals["fte"] == 0.0
        assert totals["costs"] == Decimal("0")
        assert totals["revenue"] == Decimal("0")

    @pytest.mark.asyncio
    async def test_calculate_enrollment_impact(
        self, service, mock_session, sample_version_id
    ):
        """Test calculating enrollment change impact."""
        # Mock current enrollment
        mock_enrollment_result = MagicMock()
        mock_enrollment_result.scalar.return_value = 100

        mock_session.execute.return_value = mock_enrollment_result

        current = {
            "fte": 50.0,
            "costs": Decimal("10000000"),
            "revenue": Decimal("15000000"),
        }

        change = ProposedChange(
            step_id="enrollment",
            dimension_type="level",
            dimension_id="level-123",
            field_name="student_count",
            new_value=130,  # 30 more students
        )

        proposed = await service._calculate_enrollment_impact(
            sample_version_id, change, current
        )

        # 30 more students should increase FTE, costs, and revenue
        assert proposed["fte"] > current["fte"]
        assert proposed["costs"] > current["costs"]
        assert proposed["revenue"] > current["revenue"]

    @pytest.mark.asyncio
    async def test_calculate_class_structure_impact(
        self, service, mock_session, sample_version_id
    ):
        """Test calculating class structure change impact."""
        mock_class_result = MagicMock()
        mock_class_result.scalar.return_value = 10

        mock_session.execute.return_value = mock_class_result

        current = {
            "fte": 50.0,
            "costs": Decimal("10000000"),
            "revenue": Decimal("15000000"),
        }

        change = ProposedChange(
            step_id="class_structure",
            dimension_type="level",
            dimension_id="level-123",
            field_name="number_of_classes",
            new_value=12,  # 2 more classes
        )

        proposed = await service._calculate_class_structure_impact(
            sample_version_id, change, current
        )

        # More classes should increase FTE and costs
        assert proposed["fte"] > current["fte"]
        assert proposed["costs"] > current["costs"]
        # Revenue unchanged for class structure changes
        assert proposed["revenue"] == current["revenue"]

    @pytest.mark.asyncio
    async def test_calculate_dhg_impact(
        self, service, mock_session, sample_version_id
    ):
        """Test calculating DHG change impact."""
        mock_dhg_result = MagicMock()
        mock_dhg_result.scalar.return_value = 2.0

        mock_session.execute.return_value = mock_dhg_result

        current = {
            "fte": 50.0,
            "costs": Decimal("10000000"),
            "revenue": Decimal("15000000"),
        }

        change = ProposedChange(
            step_id="dhg",
            dimension_type="subject",
            dimension_id="subject-abc",
            field_name="fte_required",
            new_value=3.0,  # 1 more FTE
        )

        proposed = await service._calculate_dhg_impact(
            sample_version_id, change, current
        )

        assert proposed["fte"] == 51.0  # +1 FTE
        assert proposed["costs"] > current["costs"]
        assert proposed["revenue"] == current["revenue"]

    @pytest.mark.asyncio
    async def test_calculate_revenue_impact(
        self, service, mock_session, sample_version_id
    ):
        """Test calculating revenue change impact."""
        mock_revenue_result = MagicMock()
        mock_revenue_result.scalar.return_value = Decimal("1000000")

        mock_session.execute.return_value = mock_revenue_result

        current = {
            "fte": 50.0,
            "costs": Decimal("10000000"),
            "revenue": Decimal("15000000"),
        }

        change = ProposedChange(
            step_id="revenue",
            dimension_type="account_code",
            dimension_code="70100",
            field_name="annual_amount",
            new_value=1500000,  # +500K
        )

        proposed = await service._calculate_revenue_impact(
            sample_version_id, change, current
        )

        assert proposed["fte"] == current["fte"]
        assert proposed["costs"] == current["costs"]
        assert proposed["revenue"] == Decimal("15500000")

    @pytest.mark.asyncio
    async def test_calculate_costs_impact(
        self, service, mock_session, sample_version_id
    ):
        """Test calculating cost change impact."""
        mock_cost_result = MagicMock()
        mock_cost_result.scalar.return_value = Decimal("500000")

        mock_session.execute.return_value = mock_cost_result

        current = {
            "fte": 50.0,
            "costs": Decimal("10000000"),
            "revenue": Decimal("15000000"),
        }

        change = ProposedChange(
            step_id="costs",
            dimension_type="account_code",
            dimension_code="64100",
            field_name="total_cost_sar",
            new_value=700000,  # +200K
        )

        proposed = await service._calculate_costs_impact(
            sample_version_id, change, current
        )

        assert proposed["fte"] == current["fte"]
        assert proposed["costs"] == Decimal("10200000")
        assert proposed["revenue"] == current["revenue"]

    @pytest.mark.asyncio
    async def test_calculate_impact_full_flow(
        self, service, mock_session, sample_version_id
    ):
        """Test full impact calculation flow."""
        # Mock all database queries
        mock_fte = MagicMock()
        mock_fte.scalar.return_value = 50.0

        mock_costs = MagicMock()
        mock_costs.scalar.return_value = Decimal("10000000")

        mock_revenue = MagicMock()
        mock_revenue.scalar.return_value = Decimal("15000000")

        mock_enrollment = MagicMock()
        mock_enrollment.scalar.return_value = 100

        mock_session.execute.side_effect = [
            mock_fte,      # _get_current_totals - FTE
            mock_costs,    # _get_current_totals - costs
            mock_revenue,  # _get_current_totals - revenue
            mock_enrollment,  # _calculate_enrollment_impact
        ]

        change = ProposedChange(
            step_id="enrollment",
            dimension_type="level",
            dimension_id="level-123",
            field_name="student_count",
            new_value=130,
        )

        metrics = await service.calculate_impact(sample_version_id, change)

        assert isinstance(metrics, ImpactMetrics)
        assert metrics.fte_current == 50.0
        assert metrics.fte_change != 0  # Should have a change
        assert "class_structure" in metrics.affected_steps

    @pytest.mark.asyncio
    async def test_calculate_impact_margin_calculation(
        self, service, mock_session, sample_version_id
    ):
        """Test margin percentage calculation."""
        mock_fte = MagicMock()
        mock_fte.scalar.return_value = 50.0

        mock_costs = MagicMock()
        mock_costs.scalar.return_value = Decimal("10000000")

        mock_revenue = MagicMock()
        mock_revenue.scalar.return_value = Decimal("15000000")

        mock_enrollment = MagicMock()
        mock_enrollment.scalar.return_value = 100

        mock_session.execute.side_effect = [
            mock_fte,
            mock_costs,
            mock_revenue,
            mock_enrollment,
        ]

        change = ProposedChange(
            step_id="enrollment",
            dimension_type="level",
            dimension_id="level-123",
            field_name="student_count",
            new_value=130,
        )

        metrics = await service.calculate_impact(sample_version_id, change)

        # Current margin = (15M - 10M) / 15M * 100 = 33.33%
        assert abs(metrics.margin_current_pct - 33.33) < 0.1

    @pytest.mark.asyncio
    async def test_calculate_impact_unknown_step(
        self, service, mock_session, sample_version_id
    ):
        """Test impact calculation for unknown step type."""
        mock_fte = MagicMock()
        mock_fte.scalar.return_value = 50.0

        mock_costs = MagicMock()
        mock_costs.scalar.return_value = Decimal("10000000")

        mock_revenue = MagicMock()
        mock_revenue.scalar.return_value = Decimal("15000000")

        mock_session.execute.side_effect = [
            mock_fte,
            mock_costs,
            mock_revenue,
        ]

        change = ProposedChange(
            step_id="unknown_step",
            dimension_type="unknown",
            field_name="unknown",
            new_value=0,
        )

        metrics = await service.calculate_impact(sample_version_id, change)

        # Should return zero changes for unknown step
        assert metrics.fte_change == 0
        assert metrics.cost_impact_sar == Decimal("0")
        assert metrics.revenue_impact_sar == Decimal("0")


class TestCalculateBudgetImpactConvenience:
    """Tests for calculate_budget_impact convenience function."""

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test the convenience function creates service and calls calculate."""
        mock_session = AsyncMock()
        version_id = uuid4()

        # Mock the database queries
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        change = ProposedChange(
            step_id="revenue",
            dimension_type="account_code",
            dimension_code="70100",
            field_name="annual_amount",
            new_value=1000000,
        )

        metrics = await calculate_budget_impact(mock_session, version_id, change)

        assert isinstance(metrics, ImpactMetrics)
