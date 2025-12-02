"""
Dashboard Service for aggregating and presenting summary data.

Implements business logic for:
- Dashboard summary cards (revenue, costs, students, teachers)
- Chart data generation (enrollment, costs, revenue breakdowns)
- Alert generation (capacity, variance, staffing)
- Recent activity tracking
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import BudgetVersion, BudgetVersionStatus
from app.services.exceptions import NotFoundError


class DashboardService:
    """
    Service for dashboard data aggregation and presentation.

    Provides methods for generating dashboard summaries, charts,
    alerts, and activity feeds for different user roles.
    """

    # Alert thresholds
    CAPACITY_WARNING_PCT = Decimal("90")
    CAPACITY_CRITICAL_PCT = Decimal("95")
    VARIANCE_WARNING_PCT = Decimal("5")
    VARIANCE_CRITICAL_PCT = Decimal("10")

    def __init__(self, session: AsyncSession):
        """
        Initialize dashboard service.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_dashboard_summary(
        self,
        budget_version_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Get dashboard summary cards for a budget version.

        Args:
            budget_version_id: Budget version UUID

        Returns:
            Dictionary with summary metrics:
                - total_revenue: Total revenue in SAR
                - total_costs: Total costs in SAR
                - net_result: Revenue - Costs
                - operating_margin: Net result as % of revenue
                - total_students: Total enrolled students
                - total_teachers: Total teacher FTE
                - student_teacher_ratio: Students per teacher
                - capacity_utilization: % of max capacity used

        Raises:
            NotFoundError: If budget version not found
        """
        # Verify version exists
        version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        # Get aggregated data
        # This would query from consolidated tables
        # For now, return placeholder structure
        summary = {
            "version_id": str(budget_version_id),
            "version_name": version.name,
            "fiscal_year": version.fiscal_year,
            "status": version.status.value,
            "total_revenue_sar": 0.0,
            "total_costs_sar": 0.0,
            "net_result_sar": 0.0,
            "operating_margin_pct": 0.0,
            "total_students": 0,
            "total_teachers_fte": 0.0,
            "student_teacher_ratio": 0.0,
            "capacity_utilization_pct": 0.0,
            "last_updated": datetime.utcnow().isoformat(),
        }

        return summary

    async def get_enrollment_chart_data(
        self,
        budget_version_id: uuid.UUID,
        breakdown_by: str = "level",
    ) -> dict[str, Any]:
        """
        Get enrollment chart data for visualization.

        Args:
            budget_version_id: Budget version UUID
            breakdown_by: Breakdown dimension ('level', 'nationality', 'cycle')

        Returns:
            Dictionary with chart data:
                - labels: List of category names
                - values: List of student counts
                - chart_type: Suggested chart type
                - total: Total students

        Raises:
            NotFoundError: If budget version not found
        """
        # Verify version exists
        version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        # Query enrollment data
        # This would aggregate from EnrollmentPlan table
        chart_data = {
            "breakdown_by": breakdown_by,
            "labels": [],
            "values": [],
            "chart_type": "bar",
            "total": 0,
        }

        if breakdown_by == "level":
            chart_data["chart_type"] = "bar"
            chart_data["labels"] = ["PS", "MS", "GS", "CP", "CE1", "CE2", "CM1", "CM2", "6ème", "5ème", "4ème", "3ème", "2nde", "1ère", "Term"]
            chart_data["values"] = [0] * 15

        elif breakdown_by == "nationality":
            chart_data["chart_type"] = "pie"
            chart_data["labels"] = ["French", "Saudi", "Other"]
            chart_data["values"] = [0, 0, 0]

        elif breakdown_by == "cycle":
            chart_data["chart_type"] = "pie"
            chart_data["labels"] = ["Maternelle", "Élémentaire", "Collège", "Lycée"]
            chart_data["values"] = [0, 0, 0, 0]

        return chart_data

    async def get_cost_breakdown(
        self,
        budget_version_id: uuid.UUID,
        breakdown_by: str = "category",
    ) -> dict[str, Any]:
        """
        Get cost breakdown chart data.

        Args:
            budget_version_id: Budget version UUID
            breakdown_by: Breakdown dimension ('category', 'account', 'period')

        Returns:
            Dictionary with chart data:
                - labels: List of category names
                - values: List of cost amounts (SAR)
                - percentages: List of percentages of total
                - chart_type: Suggested chart type
                - total: Total costs

        Raises:
            NotFoundError: If budget version not found
        """
        # Verify version exists
        version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        # Query cost data from CostConsolidation
        chart_data = {
            "breakdown_by": breakdown_by,
            "labels": [],
            "values": [],
            "percentages": [],
            "chart_type": "pie",
            "total": 0.0,
        }

        if breakdown_by == "category":
            chart_data["labels"] = [
                "Personnel Costs",
                "Operating Costs",
                "Facility Costs",
                "Administrative Costs",
                "Other Costs",
            ]
            chart_data["values"] = [0.0] * 5
            chart_data["chart_type"] = "pie"

        elif breakdown_by == "account":
            chart_data["chart_type"] = "bar"
            # Would populate from PCG account structure

        elif breakdown_by == "period":
            chart_data["chart_type"] = "line"
            chart_data["labels"] = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
            chart_data["values"] = [0.0] * 12

        return chart_data

    async def get_revenue_breakdown(
        self,
        budget_version_id: uuid.UUID,
        breakdown_by: str = "fee_type",
    ) -> dict[str, Any]:
        """
        Get revenue breakdown chart data.

        Args:
            budget_version_id: Budget version UUID
            breakdown_by: Breakdown dimension ('fee_type', 'nationality', 'period', 'trimester')

        Returns:
            Dictionary with chart data:
                - labels: List of category names
                - values: List of revenue amounts (SAR)
                - percentages: List of percentages of total
                - chart_type: Suggested chart type
                - total: Total revenue

        Raises:
            NotFoundError: If budget version not found
        """
        # Verify version exists
        version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        # Query revenue data from RevenueConsolidation
        chart_data = {
            "breakdown_by": breakdown_by,
            "labels": [],
            "values": [],
            "percentages": [],
            "chart_type": "pie",
            "total": 0.0,
        }

        if breakdown_by == "fee_type":
            chart_data["labels"] = [
                "Tuition Fees",
                "Enrollment Fee (DAI)",
                "Registration Fee",
                "Transport Fees",
                "Meal Fees",
                "Other Fees",
            ]
            chart_data["values"] = [0.0] * 6
            chart_data["chart_type"] = "pie"

        elif breakdown_by == "nationality":
            chart_data["labels"] = ["French", "Saudi", "Other"]
            chart_data["values"] = [0.0, 0.0, 0.0]
            chart_data["chart_type"] = "pie"

        elif breakdown_by == "trimester":
            chart_data["labels"] = ["T1 (40%)", "T2 (30%)", "T3 (30%)"]
            chart_data["values"] = [0.0, 0.0, 0.0]
            chart_data["chart_type"] = "pie"

        elif breakdown_by == "period":
            chart_data["chart_type"] = "line"
            chart_data["labels"] = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
            chart_data["values"] = [0.0] * 12

        return chart_data

    async def get_alerts(
        self,
        budget_version_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """
        Get system alerts for a budget version.

        Alerts include:
        - Capacity warnings (> 90% utilization)
        - Budget variance warnings (> 5% from target)
        - Staffing gaps (insufficient teachers)
        - KPI threshold violations

        Args:
            budget_version_id: Budget version UUID

        Returns:
            List of alert dictionaries with:
                - alert_type: Type of alert
                - severity: 'info', 'warning', 'critical'
                - title: Alert title
                - message: Detailed message
                - metric_value: Current value
                - threshold_value: Threshold that triggered alert
                - created_at: Alert timestamp

        Raises:
            NotFoundError: If budget version not found
        """
        # Verify version exists
        version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        alerts = []

        # Get summary data for alert evaluation
        summary = await self.get_dashboard_summary(budget_version_id)

        # Capacity utilization alerts
        capacity_pct = Decimal(str(summary.get("capacity_utilization_pct", 0)))
        if capacity_pct >= self.CAPACITY_CRITICAL_PCT:
            alerts.append({
                "alert_type": "capacity_critical",
                "severity": "critical",
                "title": "Critical: Near Maximum Capacity",
                "message": f"School capacity at {capacity_pct}%. Immediate action required.",
                "metric_value": float(capacity_pct),
                "threshold_value": float(self.CAPACITY_CRITICAL_PCT),
                "created_at": datetime.utcnow().isoformat(),
            })
        elif capacity_pct >= self.CAPACITY_WARNING_PCT:
            alerts.append({
                "alert_type": "capacity_warning",
                "severity": "warning",
                "title": "Warning: High Capacity Utilization",
                "message": f"School capacity at {capacity_pct}%. Consider expansion planning.",
                "metric_value": float(capacity_pct),
                "threshold_value": float(self.CAPACITY_WARNING_PCT),
                "created_at": datetime.utcnow().isoformat(),
            })

        # Operating margin alerts
        margin_pct = Decimal(str(summary.get("operating_margin_pct", 0)))
        if margin_pct < Decimal("5"):
            alerts.append({
                "alert_type": "margin_low",
                "severity": "warning",
                "title": "Low Operating Margin",
                "message": f"Operating margin at {margin_pct}%, below 5% target.",
                "metric_value": float(margin_pct),
                "threshold_value": 5.0,
                "created_at": datetime.utcnow().isoformat(),
            })

        # Version status alerts
        if version.status == BudgetVersionStatus.WORKING:
            alerts.append({
                "alert_type": "version_draft",
                "severity": "info",
                "title": "Budget Version in Draft",
                "message": f"Budget version '{version.name}' is still in working status.",
                "metric_value": None,
                "threshold_value": None,
                "created_at": datetime.utcnow().isoformat(),
            })

        return alerts

    async def get_recent_activity(
        self,
        budget_version_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get recent activity log for budget versions.

        Args:
            budget_version_id: Optional filter by specific version
            limit: Maximum number of activities to return

        Returns:
            List of activity dictionaries with:
                - activity_type: Type of activity
                - description: Activity description
                - version_id: Related budget version
                - version_name: Budget version name
                - user_id: User who performed action
                - timestamp: When activity occurred
        """
        activities = []

        # Query budget version changes
        query = select(BudgetVersion).where(BudgetVersion.deleted_at.is_(None))

        if budget_version_id:
            query = query.where(BudgetVersion.id == budget_version_id)

        query = query.order_by(BudgetVersion.updated_at.desc()).limit(limit)

        result = await self.session.execute(query)
        versions = result.scalars().all()

        for version in versions:
            # Version creation activity
            if version.created_at:
                activities.append({
                    "activity_type": "version_created",
                    "description": f"Budget version '{version.name}' created",
                    "version_id": str(version.id),
                    "version_name": version.name,
                    "user_id": str(version.created_by_id) if hasattr(version, "created_by_id") and version.created_by_id else None,
                    "timestamp": version.created_at.isoformat(),
                })

            # Version submission activity
            if version.submitted_at:
                activities.append({
                    "activity_type": "version_submitted",
                    "description": f"Budget version '{version.name}' submitted for approval",
                    "version_id": str(version.id),
                    "version_name": version.name,
                    "user_id": str(version.submitted_by_id) if version.submitted_by_id else None,
                    "timestamp": version.submitted_at.isoformat(),
                })

            # Version approval activity
            if version.approved_at:
                activities.append({
                    "activity_type": "version_approved",
                    "description": f"Budget version '{version.name}' approved",
                    "version_id": str(version.id),
                    "version_name": version.name,
                    "user_id": str(version.approved_by_id) if version.approved_by_id else None,
                    "timestamp": version.approved_at.isoformat(),
                })

        # Sort by timestamp descending
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return activities[:limit]

    async def get_comparison_data(
        self,
        version_ids: list[uuid.UUID],
        metric: str = "summary",
    ) -> dict[str, Any]:
        """
        Get comparison data across multiple budget versions.

        Args:
            version_ids: List of budget version UUIDs to compare
            metric: Metric to compare ('summary', 'enrollment', 'revenue', 'costs', 'kpis')

        Returns:
            Dictionary with comparison data:
                - versions: List of version names
                - metric_name: Name of metric being compared
                - values: List of values for each version
                - labels: Optional category labels for complex metrics
        """
        comparison = {
            "versions": [],
            "metric_name": metric,
            "values": [],
            "labels": None,
        }

        for version_id in version_ids:
            # Get version
            version_query = select(BudgetVersion).where(BudgetVersion.id == version_id)
            version_result = await self.session.execute(version_query)
            version = version_result.scalar_one_or_none()

            if not version:
                continue

            comparison["versions"].append({
                "id": str(version.id),
                "name": version.name,
                "fiscal_year": version.fiscal_year,
            })

            # Get metric data based on type
            if metric == "summary":
                summary = await self.get_dashboard_summary(version_id)
                comparison["values"].append({
                    "total_revenue": summary.get("total_revenue_sar", 0),
                    "total_costs": summary.get("total_costs_sar", 0),
                    "net_result": summary.get("net_result_sar", 0),
                    "students": summary.get("total_students", 0),
                })

        return comparison
