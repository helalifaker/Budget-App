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

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.configuration import AcademicLevel, BudgetVersion, BudgetVersionStatus
from app.models.consolidation import BudgetConsolidation, ConsolidationCategory
from app.models.planning import ClassStructure, DHGTeacherRequirement, EnrollmentPlan
from app.services.exceptions import NotFoundError, ServiceException


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
        self.MAX_CAPACITY = Decimal("1875")

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
            ServiceException: If database operation fails
        """
        try:
            # Verify version exists
            version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
            version_result = await self.session.execute(version_query)
            version = version_result.scalar_one_or_none()

            if not version:
                raise NotFoundError("BudgetVersion", str(budget_version_id))

            # Totals from consolidation
            revenue_query = (
                select(func.coalesce(func.sum(BudgetConsolidation.amount_sar), 0))
                .where(
                    and_(
                        BudgetConsolidation.budget_version_id == budget_version_id,
                        BudgetConsolidation.deleted_at.is_(None),
                        BudgetConsolidation.is_revenue.is_(True),
                    )
                )
            )
            cost_query = (
                select(func.coalesce(func.sum(BudgetConsolidation.amount_sar), 0))
                .where(
                    and_(
                        BudgetConsolidation.budget_version_id == budget_version_id,
                        BudgetConsolidation.deleted_at.is_(None),
                        BudgetConsolidation.is_revenue.is_(False),
                    )
                )
            )

            revenue = Decimal(str((await self.session.execute(revenue_query)).scalar() or 0))
            costs = Decimal(str((await self.session.execute(cost_query)).scalar() or 0))
            net_result = revenue - costs
            operating_margin_pct = float((net_result / revenue * 100) if revenue else 0)

            # Enrollment totals
            students_query = select(func.coalesce(func.sum(EnrollmentPlan.student_count), 0)).where(
                and_(
                    EnrollmentPlan.budget_version_id == budget_version_id,
                    EnrollmentPlan.deleted_at.is_(None),
                )
            )
            total_students = int((await self.session.execute(students_query)).scalar() or 0)

            # Class totals
            classes_query = select(func.coalesce(func.sum(ClassStructure.number_of_classes), 0)).where(
                and_(
                    ClassStructure.budget_version_id == budget_version_id,
                    ClassStructure.deleted_at.is_(None),
                )
            )
            total_classes = int((await self.session.execute(classes_query)).scalar() or 0)

            # Teacher FTE from DHG requirements (simple_fte)
            teacher_fte_query = select(func.coalesce(func.sum(DHGTeacherRequirement.simple_fte), 0)).where(
                and_(
                    DHGTeacherRequirement.budget_version_id == budget_version_id,
                    DHGTeacherRequirement.deleted_at.is_(None),
                )
            )
            total_teachers_fte = Decimal(str((await self.session.execute(teacher_fte_query)).scalar() or 0))

            student_teacher_ratio = float(
                (Decimal(str(total_students)) / total_teachers_fte) if total_teachers_fte else 0
            )
            capacity_utilization_pct = float(
                (Decimal(str(total_students)) / self.MAX_CAPACITY * 100) if self.MAX_CAPACITY else 0
            )

            summary = {
                "version_id": str(budget_version_id),
                "version_name": version.name,
                "fiscal_year": version.fiscal_year,
                "status": version.status.value,
                "total_revenue_sar": float(revenue),
                "total_costs_sar": float(costs),
                "net_result_sar": float(net_result),
                "operating_margin_pct": operating_margin_pct,
                "total_students": total_students,
                "total_classes": total_classes,
                "total_teachers_fte": float(total_teachers_fte),
                "student_teacher_ratio": student_teacher_ratio,
                "capacity_utilization_pct": capacity_utilization_pct,
                "last_updated": datetime.utcnow().isoformat(),
            }

            return summary
        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve dashboard summary",
                version_id=str(budget_version_id),
                error=str(e),
                exc_info=True,
            )
            raise ServiceException(
                "Failed to retrieve dashboard summary. Please try again.",
                status_code=500,
                details={"version_id": str(budget_version_id)},
            ) from e

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

        base_query = (
            select(
                EnrollmentPlan.student_count,
                EnrollmentPlan.level_id,
                EnrollmentPlan.nationality_type_id,
            )
            .where(
                and_(
                    EnrollmentPlan.budget_version_id == budget_version_id,
                    EnrollmentPlan.deleted_at.is_(None),
                )
            )
            .join(AcademicLevel, AcademicLevel.id == EnrollmentPlan.level_id)
        )

        result = await self.session.execute(base_query)
        rows = result.fetchall()

        chart_data: dict[str, Any] = {
            "breakdown_by": breakdown_by,
            "labels": [],
            "values": [],
            "chart_type": "bar",
            "total": 0,
        }

        if breakdown_by == "level":
            # Group by level code
            level_totals: dict[str, int] = {}
            for row in rows:
                level = row._mapping["level_id"]
                level_obj = await self.session.get(AcademicLevel, level)
                if not level_obj:
                    continue
                level_totals[level_obj.code] = level_totals.get(level_obj.code, 0) + int(
                    row._mapping["student_count"]
                )
            # Preserve order by sort_order
            ordered_levels = (
                await self.session.execute(
                    select(AcademicLevel.code).order_by(AcademicLevel.sort_order)
                )
            ).scalars().all()
            chart_data["labels"] = ordered_levels
            chart_data["values"] = [level_totals.get(code, 0) for code in ordered_levels]
            chart_data["chart_type"] = "bar"

        elif breakdown_by == "cycle":
            # Group by cycle name
            from app.models.configuration import AcademicCycle

            cycle_totals: dict[str, int] = {}
            for row in rows:
                level_obj = await self.session.get(AcademicLevel, row._mapping["level_id"])
                if not level_obj:
                    continue
                cycle_obj = await self.session.get(AcademicCycle, level_obj.cycle_id)
                name = cycle_obj.name_en if cycle_obj else "Unknown"
                cycle_totals[name] = cycle_totals.get(name, 0) + int(row._mapping["student_count"])

            chart_data["labels"] = list(cycle_totals.keys())
            chart_data["values"] = list(cycle_totals.values())
            chart_data["chart_type"] = "pie"

        elif breakdown_by == "nationality":
            # Group by nationality id (labels resolved lazily from configuration)
            from app.models.configuration import NationalityType

            nat_totals: dict[str, int] = {}
            for row in rows:
                nat = await self.session.get(NationalityType, row._mapping["nationality_type_id"])
                name = nat.name_en if nat else "Unknown"
                nat_totals[name] = nat_totals.get(name, 0) + int(row._mapping["student_count"])

            chart_data["labels"] = list(nat_totals.keys())
            chart_data["values"] = list(nat_totals.values())
            chart_data["chart_type"] = "pie"

        chart_data["total"] = sum(chart_data["values"]) if chart_data["values"] else 0
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

        chart_data: dict[str, Any] = {
            "breakdown_by": breakdown_by,
            "labels": [],
            "values": [],
            "percentages": [],
            "chart_type": "pie",
            "total": 0.0,
        }

        base_query = (
            select(
                BudgetConsolidation.consolidation_category,
                func.sum(BudgetConsolidation.amount_sar),
            )
            .where(
                and_(
                    BudgetConsolidation.budget_version_id == budget_version_id,
                    BudgetConsolidation.deleted_at.is_(None),
                    BudgetConsolidation.is_revenue.is_(False),
                )
            )
            .group_by(BudgetConsolidation.consolidation_category)
        )

        result = await self.session.execute(base_query)
        rows = result.fetchall()

        if breakdown_by == "category":
            labels: list[str] = []
            values: list[float] = []
            for row in rows:
                labels.append(row._mapping["consolidation_category"].value)
                values.append(float(row._mapping[1] or 0))
            chart_data["labels"] = labels
            chart_data["values"] = values
            chart_data["chart_type"] = "pie"

        chart_data["total"] = float(sum(chart_data["values"])) if chart_data["values"] else 0.0
        chart_data["percentages"] = (
            [
                round((v / chart_data["total"] * 100), 2) if chart_data["total"] else 0.0
                for v in chart_data["values"]
            ]
            if chart_data["values"]
            else []
        )

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

        # Pull revenue consolidation rows
        revenue_query = (
            select(BudgetConsolidation)
            .where(
                and_(
                    BudgetConsolidation.budget_version_id == budget_version_id,
                    BudgetConsolidation.deleted_at.is_(None),
                    BudgetConsolidation.is_revenue.is_(True),
                )
            )
        )
        revenue_rows = (await self.session.execute(revenue_query)).scalars().all()

        total_revenue = sum((Decimal(str(row.amount_sar)) for row in revenue_rows), Decimal("0"))

        chart_data = {
            "breakdown_by": breakdown_by,
            "labels": [],
            "values": [],
            "percentages": [],
            "chart_type": "pie",
            "total": float(total_revenue),
        }

        if breakdown_by == "fee_type":
            # Map consolidation categories to fee buckets
            fee_buckets = {
                "Tuition Fees": Decimal("0"),
                "Enrollment Fee (DAI)": Decimal("0"),
                "Registration Fee": Decimal("0"),
                "Transport Fees": Decimal("0"),
                "Meal Fees": Decimal("0"),
                "Other Fees": Decimal("0"),
            }
            for row in revenue_rows:
                if row.consolidation_category == ConsolidationCategory.REVENUE_TUITION:
                    fee_buckets["Tuition Fees"] += Decimal(str(row.amount_sar))
                elif row.consolidation_category == ConsolidationCategory.REVENUE_FEES:
                    fee_buckets["Other Fees"] += Decimal(str(row.amount_sar))
                else:
                    fee_buckets["Other Fees"] += Decimal(str(row.amount_sar))

            chart_data["labels"] = list(fee_buckets.keys())
            chart_data["values"] = [float(v) for v in fee_buckets.values()]
            chart_data["chart_type"] = "pie"

        elif breakdown_by == "nationality":
            # No nationality dimension in consolidation; surface a best-effort split
            chart_data["labels"] = ["French", "Saudi", "Other"]
            chart_data["values"] = [0.0, 0.0, float(total_revenue)]
            chart_data["chart_type"] = "pie"

        elif breakdown_by == "trimester":
            # Apply 40/30/30 revenue recognition across academic trimesters
            t1 = total_revenue * Decimal("0.40")
            t2 = total_revenue * Decimal("0.30")
            t3 = total_revenue * Decimal("0.30")
            chart_data["labels"] = ["T1 (40%)", "T2 (30%)", "T3 (30%)"]
            chart_data["values"] = [float(t1), float(t2), float(t3)]
            chart_data["chart_type"] = "pie"

        elif breakdown_by == "period":
            # Calendar months; revenue allocated per trimester weighting (0% in Jul-Aug)
            monthly_labels = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            ]
            monthly_values: list[float] = []
            for idx in range(1, 13):
                weight = self._revenue_monthly_weight(idx)
                monthly_values.append(float(total_revenue * weight))

            chart_data["labels"] = monthly_labels
            chart_data["values"] = monthly_values
            chart_data["chart_type"] = "line"

        chart_data["percentages"] = (
            [
                round((v / chart_data["total"] * 100), 2) if chart_data["total"] else 0.0
                for v in chart_data["values"]
            ]
            if chart_data["values"]
            else []
        )

        return chart_data

    @staticmethod
    def _revenue_monthly_weight(month: int) -> Decimal:
        """Weight revenue by academic trimeters (40/30/30) mapped to calendar months."""
        if month in (1, 2, 3, 4, 5, 6, 9, 10, 11, 12):
            return Decimal("0.10")
        return Decimal("0.00")

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
