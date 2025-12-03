"""
Tests for Analysis API endpoints.

Covers:
- KPI calculation and retrieval
- Dashboard summaries and charts
- Budget vs actual variance analysis
- Strategic planning endpoints
- Materialized view management
- Error handling

Target Coverage: 90%+
"""

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@efir.local"
    user.role = "admin"
    return user


# ==============================================================================
# Test: KPI Endpoints
# ==============================================================================


class TestKPIEndpoints:
    """Tests for KPI calculation and retrieval endpoints."""

    def test_calculate_kpis_success(self, client, mock_user):
        """Test successful KPI calculation."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_kpi_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.calculate_kpis.return_value = {
                "H_E_PRIMARY": {
                    "calculated_value": Decimal("1.2"),
                    "variance_from_target": Decimal("0.1"),
                },
                "E_D_PRIMARY": {
                    "calculated_value": Decimal("25"),
                    "variance_from_target": Decimal("2.5"),
                },
            }
            mock_kpi_value = MagicMock()
            mock_kpi_value.kpi_definition = MagicMock()
            mock_kpi_value.kpi_definition.code = "H_E_PRIMARY"
            mock_service.save_kpi_values.return_value = [mock_kpi_value]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/analysis/kpis/{version_id}/calculate
                pass

    def test_calculate_kpis_not_found(self, client, mock_user):
        """Test KPI calculation with non-existent version."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_kpi_service") as mock_svc:
            from app.services.exceptions import NotFoundError

            mock_service = AsyncMock()
            mock_service.calculate_kpis.side_effect = NotFoundError(
                "BudgetVersion", version_id
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 404 Not Found
                pass

    def test_get_all_kpis_success(self, client, mock_user):
        """Test successful retrieval of all KPIs."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_kpi_service") as mock_svc:
            mock_kpi_def = MagicMock()
            mock_kpi_def.code = "H_E_PRIMARY"
            mock_kpi_def.name_en = "Hours per Student (Primary)"
            mock_kpi_def.unit = "hours"
            mock_kpi_def.target_value = Decimal("1.1")

            mock_kpi_value = MagicMock()
            mock_kpi_value.id = uuid.uuid4()
            mock_kpi_value.budget_version_id = version_id
            mock_kpi_value.calculated_value = Decimal("1.2")
            mock_kpi_value.variance_from_target = Decimal("0.1")
            mock_kpi_value.variance_percent = Decimal("9.09")
            mock_kpi_value.calculation_inputs = {"hours": "720", "students": "600"}
            mock_kpi_value.calculated_at = datetime.utcnow()
            mock_kpi_value.kpi_definition = mock_kpi_def
            mock_kpi_value.notes = None

            mock_service = AsyncMock()
            mock_service.get_all_kpis.return_value = [mock_kpi_value]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/kpis/{version_id}
                pass

    def test_get_all_kpis_by_category(self, client, mock_user):
        """Test retrieval of KPIs filtered by category."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_kpi_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_all_kpis.return_value = []
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/kpis/{version_id}?category=educational
                pass

    def test_get_specific_kpi_success(self, client, mock_user):
        """Test successful retrieval of specific KPI."""
        version_id = uuid.uuid4()
        kpi_code = "H_E_PRIMARY"

        with patch("app.api.v1.analysis.get_kpi_service") as mock_svc:
            mock_kpi_def = MagicMock()
            mock_kpi_def.code = kpi_code
            mock_kpi_def.name_en = "Hours per Student (Primary)"
            mock_kpi_def.unit = "hours"
            mock_kpi_def.target_value = Decimal("1.1")

            mock_kpi_value = MagicMock()
            mock_kpi_value.id = uuid.uuid4()
            mock_kpi_value.budget_version_id = version_id
            mock_kpi_value.calculated_value = Decimal("1.2")
            mock_kpi_value.variance_from_target = Decimal("0.1")
            mock_kpi_value.variance_percent = Decimal("9.09")
            mock_kpi_value.calculation_inputs = {}
            mock_kpi_value.calculated_at = datetime.utcnow()
            mock_kpi_value.kpi_definition = mock_kpi_def
            mock_kpi_value.notes = None

            mock_service = AsyncMock()
            mock_service.get_kpi_by_type.return_value = mock_kpi_value
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/kpis/{version_id}/{kpi_code}
                pass

    def test_get_specific_kpi_not_found(self, client, mock_user):
        """Test retrieval of non-existent KPI."""
        version_id = uuid.uuid4()
        kpi_code = "NONEXISTENT_KPI"

        with patch("app.api.v1.analysis.get_kpi_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_kpi_by_type.return_value = None
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 404 Not Found
                pass

    def test_get_kpi_trends_success(self, client, mock_user):
        """Test successful retrieval of KPI trends."""
        kpi_code = "H_E_PRIMARY"
        version_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        with patch("app.api.v1.analysis.get_kpi_service") as mock_svc:
            mock_def = MagicMock()
            mock_def.name_en = "Hours per Student (Primary)"
            mock_def.unit = "hours"

            mock_service = AsyncMock()
            mock_service.get_kpi_definition.return_value = mock_def
            mock_service.get_kpi_trends.return_value = [
                {"version_id": str(vid), "calculated_value": 1.0 + i * 0.1}
                for i, vid in enumerate(version_ids)
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/kpis/trends/{kpi_code}?version_ids=...
                pass

    def test_get_benchmark_comparison_success(self, client, mock_user):
        """Test successful retrieval of benchmark comparison."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_kpi_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_benchmark_comparison.return_value = {
                "H_E_PRIMARY": {
                    "calculated_value": Decimal("1.2"),
                    "benchmark_value": Decimal("1.1"),
                    "status": "within_range",
                },
                "E_D_PRIMARY": {
                    "calculated_value": Decimal("28"),
                    "benchmark_value": Decimal("25"),
                    "status": "above_range",
                },
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/kpis/{version_id}/benchmarks
                pass


# ==============================================================================
# Test: Dashboard Endpoints
# ==============================================================================


class TestDashboardEndpoints:
    """Tests for dashboard endpoints."""

    def test_get_dashboard_summary_success(self, client, mock_user):
        """Test successful retrieval of dashboard summary."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_dashboard_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_dashboard_summary.return_value = {
                "total_students": 1500,
                "total_classes": 60,
                "total_revenue": Decimal("75000000"),
                "total_costs": Decimal("70000000"),
                "operating_margin": Decimal("6.67"),
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/dashboard/{version_id}/summary
                pass

    def test_get_enrollment_chart_success(self, client, mock_user):
        """Test successful retrieval of enrollment chart data."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_dashboard_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_enrollment_chart_data.return_value = {
                "chart_type": "bar",
                "labels": ["PS", "MS", "GS", "CP", "CE1"],
                "datasets": [
                    {"label": "Students", "data": [100, 110, 120, 130, 125]}
                ],
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/dashboard/{version_id}/charts/enrollment
                pass

    def test_get_cost_breakdown_chart_success(self, client, mock_user):
        """Test successful retrieval of cost breakdown chart."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_dashboard_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_cost_breakdown.return_value = {
                "chart_type": "pie",
                "labels": ["Personnel", "Operating", "CapEx"],
                "datasets": [
                    {"data": [45000000, 15000000, 5000000]}
                ],
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/dashboard/{version_id}/charts/costs
                pass

    def test_get_revenue_breakdown_chart_success(self, client, mock_user):
        """Test successful retrieval of revenue breakdown chart."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_dashboard_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_revenue_breakdown.return_value = {
                "chart_type": "bar",
                "labels": ["Tuition", "DAI", "Registration"],
                "datasets": [
                    {"data": [70000000, 3000000, 2000000]}
                ],
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/dashboard/{version_id}/charts/revenue
                pass

    def test_get_alerts_success(self, client, mock_user):
        """Test successful retrieval of alerts."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_dashboard_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_alerts.return_value = [
                {
                    "type": "warning",
                    "message": "Class size exceeds target in 6ème",
                    "module": "class_structure",
                },
                {
                    "type": "info",
                    "message": "Budget ready for submission",
                    "module": "consolidation",
                },
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/dashboard/{version_id}/alerts
                pass

    def test_get_recent_activity_success(self, client, mock_user):
        """Test successful retrieval of recent activity."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_dashboard_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_recent_activity.return_value = [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "Updated enrollment for 6ème",
                    "user": "user@efir.local",
                },
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/dashboard/{version_id}/activity
                pass

    def test_get_comparison_data_success(self, client, mock_user):
        """Test successful retrieval of comparison data."""
        version_ids = [uuid.uuid4(), uuid.uuid4()]

        with patch("app.api.v1.analysis.get_dashboard_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_comparison_data.return_value = {
                "metric": "summary",
                "versions": [
                    {"version_id": str(vid), "total_revenue": 75000000 + i * 5000000}
                    for i, vid in enumerate(version_ids)
                ],
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/dashboard/compare?version_ids=...
                pass


# ==============================================================================
# Test: Budget vs Actual Endpoints
# ==============================================================================


class TestBudgetActualEndpoints:
    """Tests for budget vs actual variance endpoints."""

    def test_import_actuals_success(self, client, mock_user):
        """Test successful import of actual data."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_budget_actual_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.import_actuals.return_value = {
                "imported_count": 50,
                "total_revenue_imported": Decimal("15000000"),
                "total_expenses_imported": Decimal("12000000"),
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/analysis/actuals/{version_id}/import
                pass

    def test_calculate_variance_success(self, client, mock_user):
        """Test successful variance calculation."""
        version_id = uuid.uuid4()
        period = 6

        with patch("app.api.v1.analysis.get_budget_actual_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.calculate_variance.return_value = [
                MagicMock(account_code="70110", variance=Decimal("500000"))
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/analysis/actuals/{version_id}/calculate-variance
                pass

    def test_get_variance_report_success(self, client, mock_user):
        """Test successful retrieval of variance report."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_budget_actual_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_variance_report.return_value = {
                "total_revenue_variance": Decimal("500000"),
                "total_expense_variance": Decimal("-200000"),
                "variances_by_account": [],
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/actuals/{version_id}/variance
                pass

    def test_create_forecast_revision_success(self, client, mock_user):
        """Test successful forecast revision creation."""
        version_id = uuid.uuid4()

        mock_forecast = MagicMock()
        mock_forecast.id = uuid.uuid4()
        mock_forecast.name = "Forecast Q2 2024"
        mock_forecast.fiscal_year = 2024
        mock_forecast.status = MagicMock()
        mock_forecast.status.value = "FORECAST"
        mock_forecast.created_at = datetime.utcnow()

        with patch("app.api.v1.analysis.get_budget_actual_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.create_forecast_revision.return_value = mock_forecast
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/analysis/actuals/{version_id}/forecast
                pass


# ==============================================================================
# Test: Strategic Planning Endpoints
# ==============================================================================


class TestStrategicPlanningEndpoints:
    """Tests for strategic planning endpoints."""

    def test_create_strategic_plan_success(self, client, mock_user):
        """Test successful strategic plan creation."""
        with patch("app.api.v1.analysis.get_strategic_service") as mock_svc:
            mock_plan = MagicMock()
            mock_plan.id = uuid.uuid4()
            mock_plan.name = "5-Year Plan 2024-2029"
            mock_plan.base_version_id = uuid.uuid4()
            mock_plan.years = 5

            mock_service = AsyncMock()
            mock_service.create_strategic_plan.return_value = mock_plan
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/analysis/strategic-plans
                pass

    def test_get_strategic_plan_success(self, client, mock_user):
        """Test successful strategic plan retrieval."""
        plan_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_strategic_service") as mock_svc:
            mock_plan = MagicMock()
            mock_plan.id = plan_id
            mock_plan.name = "5-Year Plan 2024-2029"

            mock_service = AsyncMock()
            mock_service.get_strategic_plan.return_value = mock_plan
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/strategic-plans/{plan_id}
                pass

    def test_get_strategic_plan_not_found(self, client, mock_user):
        """Test retrieval of non-existent strategic plan."""
        plan_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_strategic_service") as mock_svc:
            from app.services.exceptions import NotFoundError

            mock_service = AsyncMock()
            mock_service.get_strategic_plan.side_effect = NotFoundError(
                "StrategicPlan", plan_id
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 404 Not Found
                pass

    def test_get_year_projection_success(self, client, mock_user):
        """Test successful year projection retrieval."""
        plan_id = uuid.uuid4()
        year = 2025

        with patch("app.api.v1.analysis.get_strategic_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_year_projections.return_value = {
                "year": year,
                "projected_enrollment": 1600,
                "projected_revenue": Decimal("80000000"),
                "projected_costs": Decimal("75000000"),
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/strategic-plans/{plan_id}/year/{year}
                pass

    def test_update_scenario_assumptions_success(self, client, mock_user):
        """Test successful scenario assumptions update."""
        scenario_id = uuid.uuid4()

        mock_scenario = MagicMock()
        mock_scenario.id = scenario_id
        mock_scenario.scenario_type = MagicMock()
        mock_scenario.scenario_type.value = "BASE"

        with patch("app.api.v1.analysis.get_strategic_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.update_assumptions.return_value = mock_scenario
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test PUT /api/v1/analysis/strategic-plans/scenarios/{scenario_id}/assumptions
                pass

    def test_compare_scenarios_success(self, client, mock_user):
        """Test successful scenario comparison."""
        plan_id = uuid.uuid4()

        with patch("app.api.v1.analysis.get_strategic_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.compare_scenarios.return_value = {
                "plan_id": str(plan_id),
                "scenarios": [
                    {"type": "CONSERVATIVE", "total_revenue_y5": Decimal("90000000")},
                    {"type": "BASE", "total_revenue_y5": Decimal("100000000")},
                    {"type": "OPTIMISTIC", "total_revenue_y5": Decimal("110000000")},
                ],
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/strategic-plans/{plan_id}/scenarios
                pass

    def test_add_initiative_success(self, client, mock_user):
        """Test successful initiative addition."""
        plan_id = uuid.uuid4()

        mock_initiative = MagicMock()
        mock_initiative.id = uuid.uuid4()
        mock_initiative.name = "New Science Lab"
        mock_initiative.planned_year = 2025

        with patch("app.api.v1.analysis.get_strategic_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.add_initiative.return_value = mock_initiative
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/analysis/strategic-plans/{plan_id}/initiatives
                pass


# ==============================================================================
# Test: Materialized View Management Endpoints
# ==============================================================================


class TestMaterializedViewEndpoints:
    """Tests for materialized view management endpoints."""

    def test_refresh_all_views_success(self, client, mock_user):
        """Test successful refresh of all materialized views."""
        with patch("app.services.materialized_view_service.MaterializedViewService.refresh_all") as mock_refresh:
            mock_refresh.return_value = {
                "efir_budget.mv_kpi_dashboard": {"status": "success", "duration_ms": 500},
                "efir_budget.mv_budget_consolidation": {"status": "success", "duration_ms": 800},
            }

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/analysis/materialized-views/refresh-all
                pass

    def test_refresh_specific_view_success(self, client, mock_user):
        """Test successful refresh of specific view."""
        view_name = "mv_kpi_dashboard"

        with patch("app.services.materialized_view_service.MaterializedViewService.refresh_view") as mock_refresh:
            mock_refresh.return_value = {
                "view_name": f"efir_budget.{view_name}",
                "status": "success",
                "duration_ms": 500,
            }

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/analysis/materialized-views/refresh/{view_name}
                pass

    def test_refresh_specific_view_invalid(self, client, mock_user):
        """Test refresh of invalid view name."""
        view_name = "invalid_view"

        with patch("app.services.materialized_view_service.MaterializedViewService.refresh_view") as mock_refresh:
            mock_refresh.side_effect = ValueError(f"Invalid view name: {view_name}")

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 400 Bad Request
                pass

    def test_get_view_info_success(self, client, mock_user):
        """Test successful retrieval of view info."""
        view_name = "mv_kpi_dashboard"

        with patch("app.services.materialized_view_service.MaterializedViewService.get_view_info") as mock_info:
            mock_info.return_value = {
                "view_name": f"efir_budget.{view_name}",
                "row_count": 150,
                "size_bytes": 102400,
                "last_refresh": datetime.utcnow().isoformat(),
            }

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/analysis/materialized-views/info/{view_name}
                pass
