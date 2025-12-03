"""
Tests for DashboardService.

Tests cover:
- Dashboard summary cards
- Chart data generation
- Alert generation
- Recent activity tracking
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import BudgetVersion
from app.services.dashboard_service import DashboardService
from app.services.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

# Skip tests for methods not yet implemented
SKIP_NOT_IMPLEMENTED = pytest.mark.skip(
    reason="Method not yet implemented in DashboardService"
)


class TestGetDashboardSummary:
    """Tests for dashboard summary retrieval."""

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful dashboard summary retrieval."""
        service = DashboardService(db_session)
        result = await service.get_dashboard_summary(test_budget_version.id)

        assert result is not None
        assert "version_id" in result
        assert "version_name" in result
        assert "fiscal_year" in result
        assert "status" in result
        assert result["version_id"] == str(test_budget_version.id)
        assert result["version_name"] == test_budget_version.name

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test dashboard summary with invalid version."""
        service = DashboardService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_dashboard_summary(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_contains_metrics(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test dashboard summary contains required metrics."""
        service = DashboardService(db_session)
        result = await service.get_dashboard_summary(test_budget_version.id)

        # Check for required metric fields
        required_fields = [
            "total_revenue_sar",
            "total_costs_sar",
            "net_result_sar",
            "operating_margin_pct",
            "total_students",
            "total_teachers_fte",
            "student_teacher_ratio",
            "capacity_utilization_pct",
        ]

        for field in required_fields:
            assert field in result


class TestGetEnrollmentChartData:
    """Tests for enrollment chart data generation."""

    @pytest.mark.asyncio
    async def test_get_enrollment_chart_by_level(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test enrollment chart data by level."""
        service = DashboardService(db_session)
        result = await service.get_enrollment_chart_data(
            test_budget_version.id,
            breakdown_by="level",
        )

        assert result is not None
        assert result["breakdown_by"] == "level"
        assert result["chart_type"] == "bar"
        assert "labels" in result
        assert "values" in result

    @pytest.mark.asyncio
    async def test_get_enrollment_chart_by_nationality(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test enrollment chart data by nationality."""
        service = DashboardService(db_session)
        result = await service.get_enrollment_chart_data(
            test_budget_version.id,
            breakdown_by="nationality",
        )

        assert result is not None
        assert result["breakdown_by"] == "nationality"
        assert result["chart_type"] == "pie"
        assert "French" in result["labels"]
        assert "Saudi" in result["labels"]
        assert "Other" in result["labels"]

    @pytest.mark.asyncio
    async def test_get_enrollment_chart_by_cycle(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test enrollment chart data by cycle."""
        service = DashboardService(db_session)
        result = await service.get_enrollment_chart_data(
            test_budget_version.id,
            breakdown_by="cycle",
        )

        assert result is not None
        assert result["breakdown_by"] == "cycle"
        assert result["chart_type"] == "pie"

    @pytest.mark.asyncio
    async def test_get_enrollment_chart_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test enrollment chart with invalid version."""
        service = DashboardService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_enrollment_chart_data(uuid.uuid4())


class TestGetCostBreakdown:
    """Tests for cost breakdown chart data generation."""

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_by_category(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test cost breakdown by category."""
        service = DashboardService(db_session)
        result = await service.get_cost_breakdown(
            test_budget_version.id,
            breakdown_by="category",
        )

        assert result is not None
        assert "breakdown_by" in result
        assert "labels" in result
        assert "values" in result

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_by_account(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test cost breakdown by account."""
        service = DashboardService(db_session)
        result = await service.get_cost_breakdown(
            test_budget_version.id,
            breakdown_by="account",
        )

        assert result is not None
        assert result["chart_type"] == "bar"

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_by_period(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test cost breakdown by period."""
        service = DashboardService(db_session)
        result = await service.get_cost_breakdown(
            test_budget_version.id,
            breakdown_by="period",
        )

        assert result is not None
        assert result["chart_type"] == "line"
        assert len(result["labels"]) == 12  # 12 months

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test cost breakdown with invalid version."""
        service = DashboardService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_cost_breakdown(uuid.uuid4())


class TestGetRevenueBreakdown:
    """Tests for revenue breakdown chart data generation."""

    @pytest.mark.asyncio
    async def test_get_revenue_breakdown_by_fee_type(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test revenue breakdown by fee type."""
        service = DashboardService(db_session)
        result = await service.get_revenue_breakdown(
            test_budget_version.id,
            breakdown_by="fee_type",
        )

        assert result is not None
        assert "breakdown_by" in result
        assert "labels" in result
        assert "values" in result

    @pytest.mark.asyncio
    async def test_get_revenue_breakdown_by_nationality(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test revenue breakdown by nationality."""
        service = DashboardService(db_session)
        result = await service.get_revenue_breakdown(
            test_budget_version.id,
            breakdown_by="nationality",
        )

        assert result is not None
        assert "French" in result["labels"]
        assert "Saudi" in result["labels"]

    @pytest.mark.asyncio
    async def test_get_revenue_breakdown_by_trimester(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test revenue breakdown by trimester."""
        service = DashboardService(db_session)
        result = await service.get_revenue_breakdown(
            test_budget_version.id,
            breakdown_by="trimester",
        )

        assert result is not None
        assert len(result["labels"]) == 3  # 3 trimesters

    @pytest.mark.asyncio
    async def test_get_revenue_breakdown_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test revenue breakdown with invalid version."""
        service = DashboardService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_revenue_breakdown(uuid.uuid4())


class TestGetAlerts:
    """Tests for alert generation."""

    @pytest.mark.asyncio
    async def test_get_alerts_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful alert retrieval."""
        service = DashboardService(db_session)
        result = await service.get_alerts(test_budget_version.id)

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_alerts_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test alerts with invalid version."""
        service = DashboardService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_alerts(uuid.uuid4())

    def test_alert_thresholds_defined(self):
        """Test alert thresholds are properly defined."""
        # Verify threshold constants exist
        assert DashboardService.CAPACITY_WARNING_PCT == Decimal("90")
        assert DashboardService.CAPACITY_CRITICAL_PCT == Decimal("95")
        assert DashboardService.VARIANCE_WARNING_PCT == Decimal("5")
        assert DashboardService.VARIANCE_CRITICAL_PCT == Decimal("10")


# =============================================================================
# Tests for methods not yet implemented (skipped)
# =============================================================================


@SKIP_NOT_IMPLEMENTED
class TestGetRecentActivity:
    """Tests for recent activity tracking."""

    @pytest.mark.asyncio
    async def test_get_recent_activity_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful recent activity retrieval."""
        pass


@SKIP_NOT_IMPLEMENTED
class TestKPISummary:
    """Tests for KPI summary generation."""

    @pytest.mark.asyncio
    async def test_get_kpi_summary_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful KPI summary retrieval."""
        pass


@SKIP_NOT_IMPLEMENTED
class TestDashboardWidgets:
    """Tests for dashboard widget data generation."""

    @pytest.mark.asyncio
    async def test_get_budget_status_widget(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test budget status widget data."""
        pass
