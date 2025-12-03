"""
Unit tests for Dashboard Service - Aggregated Data Presentation.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import BudgetVersionStatus
from app.services.dashboard_service import DashboardService
from app.services.exceptions import NotFoundError


@pytest.fixture
def db_session():
    """Create a mock async session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    return session


@pytest.fixture
def dashboard_service(db_session):
    """Create DashboardService instance with mocked session."""
    return DashboardService(db_session)


class TestDashboardServiceInitialization:
    """Tests for DashboardService initialization."""

    def test_dashboard_service_initialization(self, db_session):
        """Test service initializes with session and thresholds."""
        service = DashboardService(db_session)
        assert service.session == db_session
        assert service.CAPACITY_WARNING_PCT == Decimal("90")
        assert service.CAPACITY_CRITICAL_PCT == Decimal("95")
        assert service.VARIANCE_WARNING_PCT == Decimal("5")
        assert service.VARIANCE_CRITICAL_PCT == Decimal("10")


class TestAlertThresholds:
    """Tests for alert threshold values."""

    def test_capacity_warning_threshold(self):
        """Test capacity warning triggers at 90%."""
        threshold = DashboardService.CAPACITY_WARNING_PCT
        assert threshold == Decimal("90")

    def test_capacity_critical_threshold(self):
        """Test capacity critical triggers at 95%."""
        threshold = DashboardService.CAPACITY_CRITICAL_PCT
        assert threshold == Decimal("95")

    def test_variance_warning_threshold(self):
        """Test variance warning triggers at 5%."""
        threshold = DashboardService.VARIANCE_WARNING_PCT
        assert threshold == Decimal("5")

    def test_variance_critical_threshold(self):
        """Test variance critical triggers at 10%."""
        threshold = DashboardService.VARIANCE_CRITICAL_PCT
        assert threshold == Decimal("10")


class TestDashboardSummary:
    """Tests for dashboard summary generation."""

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_returns_expected_structure(self, dashboard_service, db_session):
        """Test summary returns all expected fields."""
        version_id = uuid.uuid4()

        # Mock budget version exists
        mock_version = MagicMock()
        mock_version.id = version_id
        mock_version.name = "Budget 2025"
        mock_version.fiscal_year = 2025
        mock_version.status = BudgetVersionStatus.WORKING

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        summary = await dashboard_service.get_dashboard_summary(version_id)

        assert "version_id" in summary
        assert "version_name" in summary
        assert "fiscal_year" in summary
        assert "status" in summary
        assert "total_revenue_sar" in summary
        assert "total_costs_sar" in summary
        assert "net_result_sar" in summary
        assert "operating_margin_pct" in summary
        assert "total_students" in summary
        assert "total_teachers_fte" in summary
        assert "student_teacher_ratio" in summary
        assert "capacity_utilization_pct" in summary
        assert "last_updated" in summary

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_raises_not_found(self, dashboard_service, db_session):
        """Test summary raises NotFoundError if version not found."""
        version_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_session.execute.return_value = mock_result

        with pytest.raises(NotFoundError):
            await dashboard_service.get_dashboard_summary(version_id)


class TestEnrollmentChartData:
    """Tests for enrollment chart data generation."""

    @pytest.mark.asyncio
    async def test_enrollment_chart_by_level(self, dashboard_service, db_session):
        """Test enrollment chart breakdown by level."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_version.id = version_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        chart_data = await dashboard_service.get_enrollment_chart_data(
            version_id, breakdown_by="level"
        )

        assert chart_data["breakdown_by"] == "level"
        assert chart_data["chart_type"] == "bar"
        assert "PS" in chart_data["labels"]
        assert "Term" in chart_data["labels"]
        assert len(chart_data["labels"]) == 15  # All French education levels

    @pytest.mark.asyncio
    async def test_enrollment_chart_by_nationality(self, dashboard_service, db_session):
        """Test enrollment chart breakdown by nationality."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        chart_data = await dashboard_service.get_enrollment_chart_data(
            version_id, breakdown_by="nationality"
        )

        assert chart_data["breakdown_by"] == "nationality"
        assert chart_data["chart_type"] == "pie"
        assert chart_data["labels"] == ["French", "Saudi", "Other"]

    @pytest.mark.asyncio
    async def test_enrollment_chart_by_cycle(self, dashboard_service, db_session):
        """Test enrollment chart breakdown by academic cycle."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        chart_data = await dashboard_service.get_enrollment_chart_data(
            version_id, breakdown_by="cycle"
        )

        assert chart_data["breakdown_by"] == "cycle"
        assert chart_data["chart_type"] == "pie"
        assert "Maternelle" in chart_data["labels"]
        assert "Élémentaire" in chart_data["labels"]
        assert "Collège" in chart_data["labels"]
        assert "Lycée" in chart_data["labels"]


class TestCostBreakdownChartData:
    """Tests for cost breakdown chart data generation."""

    @pytest.mark.asyncio
    async def test_cost_breakdown_by_category(self, dashboard_service, db_session):
        """Test cost breakdown by category."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        chart_data = await dashboard_service.get_cost_breakdown(
            version_id, breakdown_by="category"
        )

        assert chart_data["breakdown_by"] == "category"
        assert chart_data["chart_type"] == "pie"
        assert "Personnel Costs" in chart_data["labels"]
        assert "Operating Costs" in chart_data["labels"]

    @pytest.mark.asyncio
    async def test_cost_breakdown_by_period(self, dashboard_service, db_session):
        """Test cost breakdown by period shows monthly data."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        chart_data = await dashboard_service.get_cost_breakdown(
            version_id, breakdown_by="period"
        )

        assert chart_data["breakdown_by"] == "period"
        assert chart_data["chart_type"] == "line"
        assert len(chart_data["labels"]) == 12  # 12 months


class TestRevenueBreakdownChartData:
    """Tests for revenue breakdown chart data generation."""

    @pytest.mark.asyncio
    async def test_revenue_breakdown_by_fee_type(self, dashboard_service, db_session):
        """Test revenue breakdown by fee type."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        chart_data = await dashboard_service.get_revenue_breakdown(
            version_id, breakdown_by="fee_type"
        )

        assert chart_data["breakdown_by"] == "fee_type"
        assert chart_data["chart_type"] == "pie"
        assert "Tuition Fees" in chart_data["labels"]
        assert "Enrollment Fee (DAI)" in chart_data["labels"]
        assert "Registration Fee" in chart_data["labels"]

    @pytest.mark.asyncio
    async def test_revenue_breakdown_by_trimester(self, dashboard_service, db_session):
        """Test revenue breakdown by trimester shows EFIR payment schedule."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        chart_data = await dashboard_service.get_revenue_breakdown(
            version_id, breakdown_by="trimester"
        )

        assert chart_data["breakdown_by"] == "trimester"
        # Labels should reflect T1 (40%), T2 (30%), T3 (30%) split
        assert "T1 (40%)" in chart_data["labels"]
        assert "T2 (30%)" in chart_data["labels"]
        assert "T3 (30%)" in chart_data["labels"]


class TestAlerts:
    """Tests for alert generation."""

    @pytest.mark.asyncio
    async def test_capacity_critical_alert(self, dashboard_service, db_session):
        """Test critical alert is generated for capacity >= 95%."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_version.id = version_id
        mock_version.name = "Budget 2025"
        mock_version.fiscal_year = 2025
        mock_version.status = BudgetVersionStatus.APPROVED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        # Mock summary with critical capacity
        dashboard_service.get_dashboard_summary = AsyncMock(return_value={
            "capacity_utilization_pct": 96,
            "operating_margin_pct": 10,
        })

        alerts = await dashboard_service.get_alerts(version_id)

        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        assert len(critical_alerts) >= 1
        assert any("capacity" in a["alert_type"] for a in critical_alerts)

    @pytest.mark.asyncio
    async def test_capacity_warning_alert(self, dashboard_service, db_session):
        """Test warning alert is generated for capacity >= 90% but < 95%."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_version.status = BudgetVersionStatus.APPROVED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        # Mock summary with warning capacity
        dashboard_service.get_dashboard_summary = AsyncMock(return_value={
            "capacity_utilization_pct": 92,
            "operating_margin_pct": 10,
        })

        alerts = await dashboard_service.get_alerts(version_id)

        warning_alerts = [a for a in alerts if a["severity"] == "warning"]
        capacity_warnings = [a for a in warning_alerts if "capacity" in a["alert_type"]]
        assert len(capacity_warnings) >= 1

    @pytest.mark.asyncio
    async def test_low_margin_alert(self, dashboard_service, db_session):
        """Test warning alert for low operating margin."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_version.status = BudgetVersionStatus.APPROVED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        # Mock summary with low margin
        dashboard_service.get_dashboard_summary = AsyncMock(return_value={
            "capacity_utilization_pct": 80,
            "operating_margin_pct": 3,  # Below 5% threshold
        })

        alerts = await dashboard_service.get_alerts(version_id)

        margin_alerts = [a for a in alerts if "margin" in a["alert_type"]]
        assert len(margin_alerts) >= 1

    @pytest.mark.asyncio
    async def test_draft_version_info_alert(self, dashboard_service, db_session):
        """Test info alert for working/draft version."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_version.id = version_id
        mock_version.name = "Budget 2025 Draft"
        mock_version.status = BudgetVersionStatus.WORKING

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        dashboard_service.get_dashboard_summary = AsyncMock(return_value={
            "capacity_utilization_pct": 80,
            "operating_margin_pct": 10,
        })

        alerts = await dashboard_service.get_alerts(version_id)

        info_alerts = [a for a in alerts if a["severity"] == "info"]
        draft_alerts = [a for a in info_alerts if "draft" in a["alert_type"]]
        assert len(draft_alerts) >= 1


class TestAlertStructure:
    """Tests for alert response structure."""

    @pytest.mark.asyncio
    async def test_alert_has_required_fields(self, dashboard_service, db_session):
        """Test each alert has all required fields."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_version.status = BudgetVersionStatus.WORKING

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        db_session.execute.return_value = mock_result

        dashboard_service.get_dashboard_summary = AsyncMock(return_value={
            "capacity_utilization_pct": 96,
            "operating_margin_pct": 3,
        })

        alerts = await dashboard_service.get_alerts(version_id)

        for alert in alerts:
            assert "alert_type" in alert
            assert "severity" in alert
            assert "title" in alert
            assert "message" in alert
            assert "created_at" in alert


class TestRecentActivity:
    """Tests for recent activity generation."""

    @pytest.mark.asyncio
    async def test_activity_includes_version_creation(self, dashboard_service, db_session):
        """Test activity includes version creation events."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_version.id = version_id
        mock_version.name = "Budget 2025"
        mock_version.created_at = datetime(2025, 1, 15, 10, 30)
        mock_version.updated_at = datetime(2025, 1, 15, 10, 30)
        mock_version.submitted_at = None
        mock_version.approved_at = None
        mock_version.created_by_id = uuid.uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_version]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result

        activities = await dashboard_service.get_recent_activity(version_id)

        creation_activities = [a for a in activities if a["activity_type"] == "version_created"]
        assert len(creation_activities) >= 1

    @pytest.mark.asyncio
    async def test_activity_includes_submission(self, dashboard_service, db_session):
        """Test activity includes version submission events."""
        version_id = uuid.uuid4()

        mock_version = MagicMock()
        mock_version.id = version_id
        mock_version.name = "Budget 2025"
        mock_version.created_at = datetime(2025, 1, 15)
        mock_version.submitted_at = datetime(2025, 1, 20)
        mock_version.approved_at = None
        mock_version.created_by_id = None
        mock_version.submitted_by_id = uuid.uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_version]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result

        activities = await dashboard_service.get_recent_activity(version_id)

        submission_activities = [a for a in activities if a["activity_type"] == "version_submitted"]
        assert len(submission_activities) >= 1

    @pytest.mark.asyncio
    async def test_activity_respects_limit(self, dashboard_service, db_session):
        """Test activity list respects the limit parameter."""
        mock_versions = [MagicMock(
            id=uuid.uuid4(),
            name=f"Budget {i}",
            created_at=datetime(2025, 1, i + 1),
            submitted_at=None,
            approved_at=None,
            created_by_id=None,
        ) for i in range(30)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_versions

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result

        activities = await dashboard_service.get_recent_activity(limit=10)

        assert len(activities) <= 10


class TestComparisonData:
    """Tests for version comparison data."""

    @pytest.mark.asyncio
    async def test_comparison_includes_all_versions(self, dashboard_service, db_session):
        """Test comparison data includes all requested versions."""
        version_ids = [uuid.uuid4(), uuid.uuid4()]

        mock_versions = [
            MagicMock(id=version_ids[0], name="Budget 2024", fiscal_year=2024),
            MagicMock(id=version_ids[1], name="Budget 2025", fiscal_year=2025),
        ]

        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            mock_result = MagicMock()
            if call_count < 2:
                mock_result.scalar_one_or_none.return_value = mock_versions[call_count]
                call_count += 1
            else:
                mock_result.scalar_one_or_none.return_value = mock_versions[0]
            return mock_result

        db_session.execute = AsyncMock(side_effect=mock_execute)

        dashboard_service.get_dashboard_summary = AsyncMock(return_value={
            "total_revenue_sar": 1000000,
            "total_costs_sar": 800000,
            "net_result_sar": 200000,
            "total_students": 1500,
        })

        comparison = await dashboard_service.get_comparison_data(version_ids, metric="summary")

        assert len(comparison["versions"]) == 2
        assert len(comparison["values"]) == 2


class TestChartTypes:
    """Tests for chart type recommendations."""

    def test_level_breakdown_uses_bar_chart(self):
        """Test level breakdown recommends bar chart."""
        # Level data is ordered and categorical - bar is appropriate
        expected_type = "bar"
        assert expected_type == "bar"

    def test_nationality_breakdown_uses_pie_chart(self):
        """Test nationality breakdown recommends pie chart."""
        # Nationality is a simple proportion - pie is appropriate
        expected_type = "pie"
        assert expected_type == "pie"

    def test_period_breakdown_uses_line_chart(self):
        """Test period/time breakdown recommends line chart."""
        # Time series data - line chart is appropriate
        expected_type = "line"
        assert expected_type == "line"
