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

    @pytest.mark.skip(reason="Requires enrollment test data in fixtures")
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
        assert result["chart_type"] == "pie"

    @pytest.mark.skip(reason="Period breakdown not yet implemented in get_cost_breakdown service")
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

    @pytest.mark.asyncio
    async def test_get_alerts_capacity_warning_90_percent(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test capacity warning alert at exactly 90%."""
        service = DashboardService(db_session)

        # Mock get_dashboard_summary to return 90% capacity
        async def mock_summary(version_id):
            return {
                "capacity_utilization_pct": 90.0,
                "operating_margin_pct": 10.0,
            }

        service.get_dashboard_summary = mock_summary

        alerts = await service.get_alerts(test_budget_version.id)

        # Should have capacity warning alert
        capacity_alerts = [a for a in alerts if a["alert_type"] == "capacity_warning"]
        assert len(capacity_alerts) == 1
        assert capacity_alerts[0]["severity"] == "warning"
        assert capacity_alerts[0]["metric_value"] == 90.0
        assert capacity_alerts[0]["threshold_value"] == 90.0
        assert "High Capacity Utilization" in capacity_alerts[0]["title"]

    @pytest.mark.asyncio
    async def test_get_alerts_capacity_critical_95_percent(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test capacity critical alert at exactly 95%."""
        service = DashboardService(db_session)

        # Mock get_dashboard_summary to return 95% capacity
        async def mock_summary(version_id):
            return {
                "capacity_utilization_pct": 95.0,
                "operating_margin_pct": 10.0,
            }

        service.get_dashboard_summary = mock_summary

        alerts = await service.get_alerts(test_budget_version.id)

        # Should have capacity critical alert (not warning)
        capacity_alerts = [a for a in alerts if a["alert_type"] == "capacity_critical"]
        assert len(capacity_alerts) == 1
        assert capacity_alerts[0]["severity"] == "critical"
        assert capacity_alerts[0]["metric_value"] == 95.0
        assert capacity_alerts[0]["threshold_value"] == 95.0
        assert "Critical: Near Maximum Capacity" in capacity_alerts[0]["title"]

    @pytest.mark.asyncio
    async def test_get_alerts_capacity_critical_above_95_percent(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test capacity critical alert above 95%."""
        service = DashboardService(db_session)

        # Mock get_dashboard_summary to return 98% capacity
        async def mock_summary(version_id):
            return {
                "capacity_utilization_pct": 98.0,
                "operating_margin_pct": 10.0,
            }

        service.get_dashboard_summary = mock_summary

        alerts = await service.get_alerts(test_budget_version.id)

        # Should have capacity critical alert
        capacity_alerts = [a for a in alerts if a["alert_type"] == "capacity_critical"]
        assert len(capacity_alerts) == 1
        assert capacity_alerts[0]["severity"] == "critical"
        assert capacity_alerts[0]["metric_value"] == 98.0

    @pytest.mark.asyncio
    async def test_get_alerts_operating_margin_below_5_percent(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test low operating margin alert below 5%."""
        service = DashboardService(db_session)

        # Mock get_dashboard_summary to return 4% margin
        async def mock_summary(version_id):
            return {
                "capacity_utilization_pct": 80.0,
                "operating_margin_pct": 4.0,
            }

        service.get_dashboard_summary = mock_summary

        alerts = await service.get_alerts(test_budget_version.id)

        # Should have margin alert
        margin_alerts = [a for a in alerts if a["alert_type"] == "margin_low"]
        assert len(margin_alerts) == 1
        assert margin_alerts[0]["severity"] == "warning"
        assert margin_alerts[0]["metric_value"] == 4.0
        assert margin_alerts[0]["threshold_value"] == 5.0
        assert "Low Operating Margin" in margin_alerts[0]["title"]

    @pytest.mark.asyncio
    async def test_get_alerts_multiple_severity_levels(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test multiple alerts with different severity levels."""
        service = DashboardService(db_session)

        # Mock get_dashboard_summary to trigger multiple alerts
        async def mock_summary(version_id):
            return {
                "capacity_utilization_pct": 96.0,  # Critical
                "operating_margin_pct": 3.5,  # Warning
            }

        service.get_dashboard_summary = mock_summary

        alerts = await service.get_alerts(test_budget_version.id)

        # Should have critical, warning, and info alerts
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        warning_alerts = [a for a in alerts if a["severity"] == "warning"]
        info_alerts = [a for a in alerts if a["severity"] == "info"]

        assert len(critical_alerts) >= 1  # Capacity critical
        assert len(warning_alerts) >= 1  # Margin low
        assert len(info_alerts) >= 1  # Version draft status

    @pytest.mark.asyncio
    async def test_get_alerts_no_alerts_all_ok(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test no alerts when all metrics are healthy."""
        service = DashboardService(db_session)

        # Mock get_dashboard_summary with healthy metrics
        async def mock_summary(version_id):
            return {
                "capacity_utilization_pct": 75.0,  # Below warning threshold
                "operating_margin_pct": 12.0,  # Above 5%
            }

        service.get_dashboard_summary = mock_summary

        alerts = await service.get_alerts(test_budget_version.id)

        # Should only have info alert for version status
        capacity_alerts = [a for a in alerts if "capacity" in a["alert_type"]]
        margin_alerts = [a for a in alerts if a["alert_type"] == "margin_low"]

        assert len(capacity_alerts) == 0
        assert len(margin_alerts) == 0

    @pytest.mark.asyncio
    async def test_get_alerts_version_working_status(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test version status alert for WORKING budget."""
        service = DashboardService(db_session)

        alerts = await service.get_alerts(test_budget_version.id)

        # Should have version draft alert
        version_alerts = [a for a in alerts if a["alert_type"] == "version_draft"]
        assert len(version_alerts) == 1
        assert version_alerts[0]["severity"] == "info"
        assert "Draft" in version_alerts[0]["title"]

    @pytest.mark.asyncio
    async def test_get_alerts_capacity_exactly_at_warning(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test capacity alert at exact warning threshold."""
        service = DashboardService(db_session)

        # Mock get_dashboard_summary to return exactly 90%
        async def mock_summary(version_id):
            return {
                "capacity_utilization_pct": 90.0,
                "operating_margin_pct": 10.0,
            }

        service.get_dashboard_summary = mock_summary

        alerts = await service.get_alerts(test_budget_version.id)

        # Should trigger warning (>=)
        capacity_alerts = [a for a in alerts if "capacity" in a["alert_type"]]
        assert len(capacity_alerts) == 1
        assert capacity_alerts[0]["alert_type"] == "capacity_warning"


# =============================================================================
# Tests for Recent Activity
# =============================================================================


class TestGetRecentActivity:
    """Tests for recent activity tracking."""

    @pytest.mark.asyncio
    async def test_get_recent_activity_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful recent activity retrieval."""
        service = DashboardService(db_session)
        result = await service.get_recent_activity(
            budget_version_id=test_budget_version.id
        )

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_recent_activity_ordering(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test recent activity is ordered by timestamp descending."""
        # Create multiple budget versions with different timestamps
        from datetime import datetime, timedelta
        from app.models.configuration import BudgetVersionStatus

        version1 = BudgetVersion(
            id=uuid.uuid4(),
            name="Version 1",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            created_by_id=test_user_id,
            created_at=datetime.utcnow() - timedelta(hours=3),
            updated_at=datetime.utcnow() - timedelta(hours=3),
        )
        version2 = BudgetVersion(
            id=uuid.uuid4(),
            name="Version 2",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            created_by_id=test_user_id,
            created_at=datetime.utcnow() - timedelta(hours=1),
            updated_at=datetime.utcnow() - timedelta(hours=1),
        )

        db_session.add_all([version1, version2])
        await db_session.flush()

        service = DashboardService(db_session)
        activities = await service.get_recent_activity(limit=10)

        # Should be ordered by timestamp descending (newest first)
        assert len(activities) >= 2
        # Verify ordering by checking timestamps
        for i in range(len(activities) - 1):
            current_ts = activities[i]["timestamp"]
            next_ts = activities[i + 1]["timestamp"]
            assert current_ts >= next_ts

    @pytest.mark.asyncio
    async def test_get_recent_activity_limit(
        self,
        db_session: AsyncSession,
        test_user_id: uuid.UUID,
    ):
        """Test recent activity pagination limit."""
        # Create 5 budget versions
        versions = []
        from datetime import datetime, timedelta
        from app.models.configuration import BudgetVersionStatus

        for i in range(5):
            version = BudgetVersion(
                id=uuid.uuid4(),
                name=f"Version {i}",
                fiscal_year=2025,
                academic_year="2024-2025",
                status=BudgetVersionStatus.WORKING,
                created_by_id=test_user_id,
                created_at=datetime.utcnow() - timedelta(hours=i),
                updated_at=datetime.utcnow() - timedelta(hours=i),
            )
            versions.append(version)

        db_session.add_all(versions)
        await db_session.flush()

        service = DashboardService(db_session)
        activities = await service.get_recent_activity(limit=3)

        # Should respect limit
        assert len(activities) <= 3

    @pytest.mark.asyncio
    async def test_get_recent_activity_empty(
        self,
        db_session: AsyncSession,
    ):
        """Test recent activity with no activity."""
        service = DashboardService(db_session)
        activities = await service.get_recent_activity()

        # Should return empty list or minimal activities
        assert isinstance(activities, list)

    @pytest.mark.asyncio
    async def test_get_recent_activity_filter_by_version(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test recent activity filtered by specific version."""
        from app.models.configuration import BudgetVersionStatus

        # Create another version
        other_version = BudgetVersion(
            id=uuid.uuid4(),
            name="Other Version",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            created_by_id=test_user_id,
        )
        db_session.add(other_version)
        await db_session.flush()

        service = DashboardService(db_session)
        activities = await service.get_recent_activity(
            budget_version_id=test_budget_version.id
        )

        # All activities should be for the specified version
        for activity in activities:
            assert activity["version_id"] == str(test_budget_version.id)

    @pytest.mark.asyncio
    async def test_get_recent_activity_submitted_version(
        self,
        db_session: AsyncSession,
        test_user_id: uuid.UUID,
    ):
        """Test recent activity includes submission activity."""
        from datetime import datetime
        from app.models.configuration import BudgetVersionStatus

        version = BudgetVersion(
            id=uuid.uuid4(),
            name="Submitted Version",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.SUBMITTED,
            created_by_id=test_user_id,
            submitted_at=datetime.utcnow(),
            submitted_by_id=test_user_id,
        )
        db_session.add(version)
        await db_session.flush()

        service = DashboardService(db_session)
        activities = await service.get_recent_activity(budget_version_id=version.id)

        # Should have submission activity
        submission_activities = [
            a for a in activities if a["activity_type"] == "version_submitted"
        ]
        assert len(submission_activities) >= 1

    @pytest.mark.asyncio
    async def test_get_recent_activity_approved_version(
        self,
        db_session: AsyncSession,
        test_user_id: uuid.UUID,
    ):
        """Test recent activity includes approval activity."""
        from datetime import datetime
        from app.models.configuration import BudgetVersionStatus

        version = BudgetVersion(
            id=uuid.uuid4(),
            name="Approved Version",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.APPROVED,
            created_by_id=test_user_id,
            submitted_at=datetime.utcnow(),
            submitted_by_id=test_user_id,
            approved_at=datetime.utcnow(),
            approved_by_id=test_user_id,
        )
        db_session.add(version)
        await db_session.flush()

        service = DashboardService(db_session)
        activities = await service.get_recent_activity(budget_version_id=version.id)

        # Should have approval activity
        approval_activities = [
            a for a in activities if a["activity_type"] == "version_approved"
        ]
        assert len(approval_activities) >= 1


# =============================================================================
# Tests for Version Comparison
# =============================================================================


class TestGetComparisonData:
    """Tests for version comparison."""

    @pytest.mark.asyncio
    async def test_get_comparison_data_two_versions(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test comparison data for two versions."""
        from app.models.configuration import BudgetVersionStatus

        # Create second version
        version2 = BudgetVersion(
            id=uuid.uuid4(),
            name="Version 2",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            created_by_id=test_user_id,
        )
        db_session.add(version2)
        await db_session.flush()

        service = DashboardService(db_session)
        result = await service.get_comparison_data(
            version_ids=[test_budget_version.id, version2.id],
            metric="summary",
        )

        assert result is not None
        assert "versions" in result
        assert len(result["versions"]) == 2
        assert "values" in result
        assert len(result["values"]) == 2

    @pytest.mark.asyncio
    async def test_get_comparison_data_multiple_versions(
        self,
        db_session: AsyncSession,
        test_user_id: uuid.UUID,
    ):
        """Test comparison data for 3+ versions."""
        from app.models.configuration import BudgetVersionStatus

        # Create 4 versions
        versions = []
        for i in range(4):
            version = BudgetVersion(
                id=uuid.uuid4(),
                name=f"Version {i+1}",
                fiscal_year=2025,
                academic_year="2024-2025",
                status=BudgetVersionStatus.WORKING,
                created_by_id=test_user_id,
            )
            versions.append(version)
            db_session.add(version)

        await db_session.flush()

        service = DashboardService(db_session)
        version_ids = [v.id for v in versions]
        result = await service.get_comparison_data(
            version_ids=version_ids,
            metric="summary",
        )

        assert len(result["versions"]) == 4
        assert len(result["values"]) == 4

    @pytest.mark.asyncio
    async def test_get_comparison_data_metrics_accuracy(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test comparison data metrics accuracy."""
        service = DashboardService(db_session)
        result = await service.get_comparison_data(
            version_ids=[test_budget_version.id],
            metric="summary",
        )

        # Verify structure
        assert result["metric_name"] == "summary"
        assert "versions" in result
        assert "values" in result

        # Verify each value has expected keys
        for value in result["values"]:
            assert "total_revenue" in value
            assert "total_costs" in value
            assert "net_result" in value
            assert "students" in value

    @pytest.mark.asyncio
    async def test_get_comparison_data_invalid_version_skipped(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test comparison data skips invalid version IDs."""
        service = DashboardService(db_session)

        # Include valid and invalid version IDs
        result = await service.get_comparison_data(
            version_ids=[test_budget_version.id, uuid.uuid4()],
            metric="summary",
        )

        # Should only include valid version
        assert len(result["versions"]) == 1
        assert result["versions"][0]["id"] == str(test_budget_version.id)


class TestKPISummary:
    """Tests for KPI summary generation."""

    @pytest.mark.asyncio
    async def test_get_kpi_summary_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful KPI summary retrieval."""
        service = DashboardService(db_session)

        result = await service.get_kpi_summary(test_budget_version.id)

        assert result is not None
        assert result["version_id"] == str(test_budget_version.id)
        assert "financial_kpis" in result
        assert "operational_kpis" in result
        assert "staffing_kpis" in result

        # Check financial KPIs structure
        financial = result["financial_kpis"]
        assert "total_revenue_sar" in financial
        assert "total_costs_sar" in financial
        assert "net_result_sar" in financial
        assert "operating_margin_pct" in financial
        assert "revenue_per_student_sar" in financial
        assert "cost_per_student_sar" in financial

        # Check operational KPIs structure
        operational = result["operational_kpis"]
        assert "total_students" in operational
        assert "total_classes" in operational
        assert "capacity_utilization_pct" in operational
        assert "student_teacher_ratio" in operational

        # Check staffing KPIs structure
        staffing = result["staffing_kpis"]
        assert "total_teachers_fte" in staffing

    @pytest.mark.asyncio
    async def test_get_kpi_summary_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test KPI summary for non-existent version."""
        from app.services.exceptions import NotFoundError

        service = DashboardService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_kpi_summary(uuid.uuid4())


class TestDashboardWidgets:
    """Tests for dashboard widget data generation."""

    @pytest.mark.asyncio
    async def test_get_budget_status_widget(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test budget status widget data."""
        service = DashboardService(db_session)

        result = await service.get_budget_status_widget(test_budget_version.id)

        assert result is not None
        assert "version_info" in result
        assert "status_badge" in result
        assert "metrics" in result
        assert "alerts" in result

        # Check version info
        version_info = result["version_info"]
        assert version_info["id"] == str(test_budget_version.id)
        assert "name" in version_info
        assert "fiscal_year" in version_info
        assert "status" in version_info

        # Check status badge
        status_badge = result["status_badge"]
        assert "color" in status_badge
        assert "label" in status_badge

        # Check metrics
        metrics = result["metrics"]
        assert "total_revenue_sar" in metrics
        assert "total_costs_sar" in metrics
        assert "net_result_sar" in metrics
        assert "operating_margin_pct" in metrics
        assert "total_students" in metrics
        assert "capacity_utilization_pct" in metrics

        # Check alerts
        alerts = result["alerts"]
        assert "total" in alerts
        assert "critical" in alerts
        assert "warning" in alerts

    @pytest.mark.asyncio
    async def test_get_budget_status_widget_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test budget status widget for non-existent version."""
        from app.services.exceptions import NotFoundError

        service = DashboardService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_budget_status_widget(uuid.uuid4())
