"""
Tests for Cascade Service

Tests cover:
- Dependency graph traversal
- Downstream step identification
- Cascade recalculation execution
- Error handling during cascade
- Topological ordering
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.services.admin.cascade_service import (
    CALCULATION_ORDER,
    CASCADE_DEPENDENCIES,
    CascadeResult,
    CascadeService,
    get_downstream_steps,
)


class TestCascadeDependencies:
    """Tests for dependency constants."""

    def test_enrollment_dependencies(self):
        """Test enrollment has correct dependencies."""
        deps = CASCADE_DEPENDENCIES["enrollment"]
        assert "class_structure" in deps
        assert "revenue" in deps

    def test_class_structure_dependencies(self):
        """Test class_structure has correct dependencies."""
        deps = CASCADE_DEPENDENCIES["class_structure"]
        assert "dhg" in deps

    def test_dhg_dependencies(self):
        """Test dhg has correct dependencies."""
        deps = CASCADE_DEPENDENCIES["dhg"]
        assert "costs" in deps

    def test_revenue_no_dependencies(self):
        """Test revenue has no downstream dependencies."""
        deps = CASCADE_DEPENDENCIES["revenue"]
        assert deps == []

    def test_costs_no_dependencies(self):
        """Test costs has no downstream dependencies."""
        deps = CASCADE_DEPENDENCIES["costs"]
        assert deps == []

    def test_capex_no_dependencies(self):
        """Test capex has no downstream dependencies."""
        deps = CASCADE_DEPENDENCIES["capex"]
        assert deps == []


class TestCalculationOrder:
    """Tests for calculation order constant."""

    def test_order_starts_with_enrollment(self):
        """Test calculation order starts with enrollment."""
        assert CALCULATION_ORDER[0] == "enrollment"

    def test_order_ends_with_capex(self):
        """Test calculation order ends with capex."""
        assert CALCULATION_ORDER[-1] == "capex"

    def test_dhg_after_class_structure(self):
        """Test DHG comes after class_structure."""
        class_idx = CALCULATION_ORDER.index("class_structure")
        dhg_idx = CALCULATION_ORDER.index("dhg")
        assert dhg_idx > class_idx

    def test_costs_after_dhg(self):
        """Test costs comes after DHG."""
        dhg_idx = CALCULATION_ORDER.index("dhg")
        costs_idx = CALCULATION_ORDER.index("costs")
        assert costs_idx > dhg_idx


class TestGetDownstreamSteps:
    """Tests for get_downstream_steps function."""

    def test_enrollment_downstream(self):
        """Test getting downstream steps from enrollment."""
        downstream = get_downstream_steps("enrollment")
        # Enrollment affects: class_structure, revenue, dhg (via class_structure), costs (via dhg)
        assert "class_structure" in downstream
        assert "revenue" in downstream
        # DHG should be included as it depends on class_structure
        assert "dhg" in downstream
        # Costs should be included as it depends on dhg
        assert "costs" in downstream

    def test_class_structure_downstream(self):
        """Test getting downstream steps from class_structure."""
        downstream = get_downstream_steps("class_structure")
        assert "dhg" in downstream
        assert "costs" in downstream
        # Revenue should not be included
        assert "revenue" not in downstream

    def test_dhg_downstream(self):
        """Test getting downstream steps from dhg."""
        downstream = get_downstream_steps("dhg")
        assert "costs" in downstream
        assert len(downstream) == 1

    def test_revenue_no_downstream(self):
        """Test revenue has no downstream steps."""
        downstream = get_downstream_steps("revenue")
        assert downstream == []

    def test_costs_no_downstream(self):
        """Test costs has no downstream steps."""
        downstream = get_downstream_steps("costs")
        assert downstream == []

    def test_capex_no_downstream(self):
        """Test capex has no downstream steps."""
        downstream = get_downstream_steps("capex")
        assert downstream == []

    def test_unknown_step_no_downstream(self):
        """Test unknown step has no downstream."""
        downstream = get_downstream_steps("unknown_step")
        assert downstream == []

    def test_downstream_is_topologically_sorted(self):
        """Test downstream steps are in correct order."""
        downstream = get_downstream_steps("enrollment")
        # class_structure should come before dhg
        if "class_structure" in downstream and "dhg" in downstream:
            assert downstream.index("class_structure") < downstream.index("dhg")
        # dhg should come before costs
        if "dhg" in downstream and "costs" in downstream:
            assert downstream.index("dhg") < downstream.index("costs")

    def test_no_cycles(self):
        """Test no cycles in dependency resolution."""
        # Should not raise RecursionError
        for step in CALCULATION_ORDER:
            downstream = get_downstream_steps(step)
            # Step should not be in its own downstream
            assert step not in downstream


class TestCascadeResult:
    """Tests for CascadeResult class."""

    def test_empty_result(self):
        """Test empty cascade result."""
        result = CascadeResult()
        assert result.recalculated_steps == []
        assert result.failed_steps == []
        assert result.errors == {}

    def test_message_success(self):
        """Test message for successful cascade."""
        result = CascadeResult()
        result.recalculated_steps = ["class_structure", "dhg", "costs"]
        assert "3 step(s)" in result.message
        assert "Successfully" in result.message

    def test_message_with_failures(self):
        """Test message when some steps failed."""
        result = CascadeResult()
        result.recalculated_steps = ["class_structure"]
        result.failed_steps = ["dhg"]
        result.errors = {"dhg": "Calculation error"}
        assert "1" in result.message and "failed" in result.message

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = CascadeResult()
        result.recalculated_steps = ["class_structure"]
        result.failed_steps = ["dhg"]
        result.errors = {"dhg": "Error message"}

        data = result.to_dict()
        assert data["recalculated_steps"] == ["class_structure"]
        assert data["failed_steps"] == ["dhg"]
        assert "message" in data


class TestCascadeService:
    """Tests for CascadeService class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance with mock session."""
        return CascadeService(mock_session)

    @pytest.fixture
    def sample_version_id(self):
        """Create a sample version UUID."""
        return uuid4()

    def test_service_initialization(self, mock_session):
        """Test service initialization."""
        service = CascadeService(mock_session)
        assert service.session == mock_session

    @pytest.mark.asyncio
    async def test_recalculate_from_revenue_no_downstream(
        self, service, sample_version_id
    ):
        """Test recalculation from revenue (no downstream steps)."""
        result = await service.recalculate_from_step(sample_version_id, "revenue")

        assert isinstance(result, CascadeResult)
        assert result.recalculated_steps == []
        assert result.failed_steps == []

    @pytest.mark.asyncio
    async def test_recalculate_from_dhg(self, service, sample_version_id):
        """Test recalculation from dhg."""
        with patch("app.services.costs.cost_service.CostService") as MockCostsService:
            mock_costs_service = AsyncMock()
            MockCostsService.return_value = mock_costs_service
            mock_costs_service.calculate = AsyncMock()

            result = await service.recalculate_from_step(sample_version_id, "dhg")

            assert "costs" in result.recalculated_steps
            mock_costs_service.calculate.assert_called_once_with(sample_version_id)

    @pytest.mark.asyncio
    async def test_recalculate_from_class_structure(self, service, sample_version_id):
        """Test recalculation from class_structure."""
        with patch("app.services.workforce.dhg_service.DHGService") as MockDHGService, \
             patch("app.services.costs.cost_service.CostService") as MockCostsService:

            mock_dhg_service = AsyncMock()
            MockDHGService.return_value = mock_dhg_service
            mock_dhg_service.calculate = AsyncMock()

            mock_costs_service = AsyncMock()
            MockCostsService.return_value = mock_costs_service
            mock_costs_service.calculate = AsyncMock()

            result = await service.recalculate_from_step(
                sample_version_id, "class_structure"
            )

            assert "dhg" in result.recalculated_steps
            assert "costs" in result.recalculated_steps
            # DHG should be calculated before costs
            dhg_idx = result.recalculated_steps.index("dhg")
            costs_idx = result.recalculated_steps.index("costs")
            assert dhg_idx < costs_idx

    @pytest.mark.asyncio
    async def test_recalculate_from_enrollment(self, service, sample_version_id):
        """Test recalculation from enrollment (full cascade)."""
        with patch("app.services.enrollment.class_structure_service.ClassStructureService") as MockClassService, \
             patch("app.services.workforce.dhg_service.DHGService") as MockDHGService, \
             patch("app.services.revenue.revenue_service.RevenueService") as MockRevenueService, \
             patch("app.services.costs.cost_service.CostService") as MockCostsService:

            for MockService in [MockClassService, MockDHGService, MockRevenueService, MockCostsService]:
                mock_instance = AsyncMock()
                MockService.return_value = mock_instance
                mock_instance.calculate = AsyncMock()

            result = await service.recalculate_from_step(sample_version_id, "enrollment")

            # All downstream should be recalculated
            assert "class_structure" in result.recalculated_steps
            assert "revenue" in result.recalculated_steps
            assert "dhg" in result.recalculated_steps
            assert "costs" in result.recalculated_steps

    @pytest.mark.asyncio
    async def test_recalculate_handles_service_error(self, service, sample_version_id):
        """Test recalculation handles service errors gracefully."""
        with patch("app.services.costs.cost_service.CostService") as MockCostsService:
            mock_costs_service = AsyncMock()
            MockCostsService.return_value = mock_costs_service
            mock_costs_service.calculate = AsyncMock(
                side_effect=Exception("Calculation failed")
            )

            result = await service.recalculate_from_step(sample_version_id, "dhg")

            assert "costs" in result.failed_steps
            assert "costs" in result.errors
            assert "Calculation failed" in result.errors["costs"]

    @pytest.mark.asyncio
    async def test_recalculate_steps_specific_list(self, service, sample_version_id):
        """Test recalculating specific steps."""
        with patch("app.services.workforce.dhg_service.DHGService") as MockDHGService, \
             patch("app.services.revenue.revenue_service.RevenueService") as MockRevenueService:

            mock_dhg_service = AsyncMock()
            MockDHGService.return_value = mock_dhg_service
            mock_dhg_service.calculate = AsyncMock()

            mock_revenue_service = AsyncMock()
            MockRevenueService.return_value = mock_revenue_service
            mock_revenue_service.calculate = AsyncMock()

            result = await service.recalculate_steps(
                sample_version_id, ["revenue", "dhg"]
            )

            assert "dhg" in result.recalculated_steps
            assert "revenue" in result.recalculated_steps
            # Should be sorted by calculation order
            dhg_idx = result.recalculated_steps.index("dhg")
            revenue_idx = result.recalculated_steps.index("revenue")
            assert dhg_idx < revenue_idx  # DHG comes before revenue in order

    @pytest.mark.asyncio
    async def test_recalculate_steps_empty_list(self, service, sample_version_id):
        """Test recalculating with empty step list."""
        result = await service.recalculate_steps(sample_version_id, [])
        assert result.recalculated_steps == []
        assert result.failed_steps == []

    @pytest.mark.asyncio
    async def test_recalculate_steps_partial_failure(self, service, sample_version_id):
        """Test recalculating when some steps fail."""
        with patch("app.services.workforce.dhg_service.DHGService") as MockDHGService, \
             patch("app.services.costs.cost_service.CostService") as MockCostsService:

            mock_dhg_service = AsyncMock()
            MockDHGService.return_value = mock_dhg_service
            mock_dhg_service.calculate = AsyncMock()  # Success

            mock_costs_service = AsyncMock()
            MockCostsService.return_value = mock_costs_service
            mock_costs_service.calculate = AsyncMock(
                side_effect=Exception("Costs error")
            )

            result = await service.recalculate_steps(
                sample_version_id, ["dhg", "costs"]
            )

            assert "dhg" in result.recalculated_steps
            assert "costs" in result.failed_steps
            assert "Costs error" in result.errors["costs"]
