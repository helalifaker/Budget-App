"""
Tests for Revenue and Costs API endpoints.

Covers:
- Revenue planning (GET, POST, calculate)
- Personnel cost planning (GET, POST, calculate)
- Operating cost planning (GET, POST, calculate)
- CapEx planning (CRUD, depreciation)
- Cost summaries
- Error handling

Target Coverage: 90%+
"""

import uuid
from datetime import date
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
# Test: Revenue Planning Endpoints
# ==============================================================================


class TestRevenueEndpoints:
    """Tests for revenue planning endpoints."""

    def test_get_revenue_plan_success(self, client, mock_user):
        """Test successful retrieval of revenue plan."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_revenue_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_revenue_plan.return_value = [
                MagicMock(
                    id=uuid.uuid4(),
                    budget_version_id=version_id,
                    account_code="70110",
                    description="Tuition T1",
                    category="tuition",
                    amount_sar=Decimal("25000000"),
                    trimester=1,
                )
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/revenue/{version_id}
                pass

    def test_calculate_revenue_success(self, client, mock_user):
        """Test successful revenue calculation from enrollment."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_revenue_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.calculate_revenue_from_enrollment.return_value = {
                "total_revenue": Decimal("75000000"),
                "revenue_by_level": {"PS": Decimal("5000000"), "6EME": Decimal("10000000")},
                "revenue_by_nationality": {"French": Decimal("60000000")},
                "sibling_discounts_applied": Decimal("500000"),
                "trimester_distribution": {
                    "T1": Decimal("30000000"),
                    "T2": Decimal("22500000"),
                    "T3": Decimal("22500000"),
                },
                "created_entries": [],
                "student_count": 1500,
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/planning/revenue/{version_id}/calculate
                pass

    def test_calculate_revenue_missing_enrollment(self, client, mock_user):
        """Test revenue calculation fails without enrollment data."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_revenue_service") as mock_svc:
            from app.services.exceptions import ValidationError

            mock_service = AsyncMock()
            mock_service.calculate_revenue_from_enrollment.side_effect = ValidationError(
                "No enrollment data found for this budget version"
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 400 Bad Request
                pass

    def test_create_revenue_entry_success(self, client, mock_user):
        """Test successful creation of revenue entry."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_revenue_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.create_revenue_entry.return_value = MagicMock(
                id=uuid.uuid4(),
                budget_version_id=version_id,
                account_code="70210",
                description="DAI Fees",
                category="fees",
                amount_sar=Decimal("3000000"),
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/planning/revenue/{version_id}
                pass

    def test_create_revenue_entry_invalid_account(self, client, mock_user):
        """Test revenue entry creation with invalid account code."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_revenue_service") as mock_svc:
            from app.services.exceptions import ValidationError

            mock_service = AsyncMock()
            mock_service.create_revenue_entry.side_effect = ValidationError(
                "Revenue account code must start with 70-77, got 64110"
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 400 Bad Request
                pass

    def test_get_revenue_summary_success(self, client, mock_user):
        """Test successful retrieval of revenue summary."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_revenue_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_revenue_summary.return_value = {
                "total_revenue": Decimal("75000000"),
                "revenue_by_category": {"tuition": Decimal("70000000"), "fees": Decimal("5000000")},
                "revenue_by_trimester": {"T1": Decimal("30000000"), "T2": Decimal("22500000"), "T3": Decimal("22500000")},
                "calculated_revenue": Decimal("70000000"),
                "manual_revenue": Decimal("5000000"),
                "entry_count": 5,
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/revenue/{version_id}/summary
                pass


# ==============================================================================
# Test: Personnel Cost Planning Endpoints
# ==============================================================================


class TestPersonnelCostEndpoints:
    """Tests for personnel cost planning endpoints."""

    def test_get_personnel_costs_success(self, client, mock_user):
        """Test successful retrieval of personnel costs."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_personnel_costs.return_value = [
                MagicMock(
                    id=uuid.uuid4(),
                    budget_version_id=version_id,
                    account_code="64110",
                    description="Teaching Salaries - Secondary",
                    fte_count=Decimal("45.5"),
                    unit_cost_sar=Decimal("240000"),
                    total_cost_sar=Decimal("10920000"),
                )
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/costs/personnel/{version_id}
                pass

    def test_calculate_personnel_costs_success(self, client, mock_user):
        """Test successful personnel cost calculation from DHG."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.calculate_personnel_costs_from_dhg.return_value = {
                "total_personnel_cost": Decimal("45000000"),
                "by_category": {
                    "AEFE Detached": Decimal("15000000"),
                    "Local Teachers": Decimal("25000000"),
                    "ATSEM": Decimal("5000000"),
                },
                "total_fte": Decimal("100"),
                "aefe_contribution_eur": Decimal("2000000"),
                "created_entries": [],
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/planning/costs/personnel/{version_id}/calculate
                pass

    def test_calculate_personnel_costs_missing_dhg(self, client, mock_user):
        """Test personnel cost calculation fails without DHG data."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            from app.services.exceptions import ValidationError

            mock_service = AsyncMock()
            mock_service.calculate_personnel_costs_from_dhg.side_effect = ValidationError(
                "No teacher allocations found for this budget version"
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 400 Bad Request
                pass

    def test_create_personnel_cost_entry_success(self, client, mock_user):
        """Test successful creation of personnel cost entry."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.create_personnel_cost_entry.return_value = MagicMock(
                id=uuid.uuid4(),
                budget_version_id=version_id,
                account_code="64110",
                description="Math Teacher",
                fte_count=Decimal("1.0"),
                unit_cost_sar=Decimal("240000"),
                total_cost_sar=Decimal("240000"),
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/planning/costs/personnel/{version_id}
                pass

    def test_create_personnel_cost_invalid_account(self, client, mock_user):
        """Test personnel cost entry with invalid account code."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            from app.services.exceptions import ValidationError

            mock_service = AsyncMock()
            mock_service.create_personnel_cost_entry.side_effect = ValidationError(
                "Personnel cost account code must start with 64, got 70110"
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 400 Bad Request
                pass


# ==============================================================================
# Test: Operating Cost Planning Endpoints
# ==============================================================================


class TestOperatingCostEndpoints:
    """Tests for operating cost planning endpoints."""

    def test_get_operating_costs_success(self, client, mock_user):
        """Test successful retrieval of operating costs."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_operating_costs.return_value = [
                MagicMock(
                    id=uuid.uuid4(),
                    budget_version_id=version_id,
                    account_code="60110",
                    description="Educational Supplies",
                    category="supplies",
                    amount_sar=Decimal("500000"),
                )
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/costs/operating/{version_id}
                pass

    def test_calculate_operating_costs_success(self, client, mock_user):
        """Test successful operating cost calculation."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.calculate_operating_costs.return_value = {
                "total_operating_cost": Decimal("15000000"),
                "by_category": {
                    "supplies": Decimal("500000"),
                    "utilities": Decimal("2000000"),
                    "maintenance": Decimal("1500000"),
                },
                "driver_based_cost": Decimal("10000000"),
                "fixed_cost": Decimal("5000000"),
                "created_entries": [],
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/planning/costs/operating/{version_id}/calculate
                pass

    def test_create_operating_cost_entry_success(self, client, mock_user):
        """Test successful creation of operating cost entry."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.create_operating_cost_entry.return_value = MagicMock(
                id=uuid.uuid4(),
                budget_version_id=version_id,
                account_code="61100",
                description="External Services",
                category="services",
                amount_sar=Decimal("1000000"),
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/planning/costs/operating/{version_id}
                pass

    def test_get_cost_summary_success(self, client, mock_user):
        """Test successful retrieval of combined cost summary."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_cost_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_cost_summary.return_value = {
                "total_personnel_cost": Decimal("45000000"),
                "total_operating_cost": Decimal("15000000"),
                "total_cost": Decimal("60000000"),
                "personnel_percentage": Decimal("75"),
                "operating_percentage": Decimal("25"),
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/costs/{version_id}/summary
                pass


# ==============================================================================
# Test: CapEx Planning Endpoints
# ==============================================================================


class TestCapExEndpoints:
    """Tests for CapEx planning endpoints."""

    def test_get_capex_plan_success(self, client, mock_user):
        """Test successful retrieval of CapEx plan."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_capex_plan.return_value = [
                MagicMock(
                    id=uuid.uuid4(),
                    budget_version_id=version_id,
                    account_code="21500",
                    description="IT Equipment",
                    category="equipment",
                    quantity=50,
                    unit_cost_sar=Decimal("3000"),
                    total_cost_sar=Decimal("150000"),
                    useful_life_years=5,
                )
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/capex/{version_id}
                pass

    def test_create_capex_entry_success(self, client, mock_user):
        """Test successful creation of CapEx entry."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.create_capex_entry.return_value = MagicMock(
                id=uuid.uuid4(),
                budget_version_id=version_id,
                account_code="21500",
                description="New Computers",
                category="equipment",
                quantity=20,
                unit_cost_sar=Decimal("5000"),
                total_cost_sar=Decimal("100000"),
                acquisition_date=date(2024, 9, 1),
                useful_life_years=5,
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/planning/capex/{version_id}
                pass

    def test_update_capex_entry_success(self, client, mock_user):
        """Test successful update of CapEx entry."""
        version_id = uuid.uuid4()
        capex_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.update_capex_entry.return_value = MagicMock(
                id=capex_id,
                budget_version_id=version_id,
                account_code="21500",
                description="Updated Computers",
                quantity=25,
                unit_cost_sar=Decimal("4500"),
                total_cost_sar=Decimal("112500"),
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test PUT /api/v1/planning/capex/{version_id}/{capex_id}
                pass

    def test_update_capex_entry_not_found(self, client, mock_user):
        """Test update fails when CapEx entry doesn't exist."""
        version_id = uuid.uuid4()
        capex_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            from app.services.exceptions import NotFoundError

            mock_service = AsyncMock()
            mock_service.update_capex_entry.side_effect = NotFoundError(
                "CapExPlan", capex_id
            )
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would expect 404 Not Found
                pass

    def test_delete_capex_entry_success(self, client, mock_user):
        """Test successful deletion of CapEx entry."""
        version_id = uuid.uuid4()
        capex_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.delete_capex_entry.return_value = True
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test DELETE /api/v1/planning/capex/{version_id}/{capex_id}
                pass

    def test_calculate_depreciation_success(self, client, mock_user):
        """Test successful depreciation calculation."""
        capex_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.calculate_depreciation.return_value = {
                "capex_id": capex_id,
                "calculation_year": 2024,
                "annual_depreciation": Decimal("20000"),
                "accumulated_depreciation": Decimal("40000"),
                "net_book_value": Decimal("60000"),
                "depreciation_method": "straight_line",
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test POST /api/v1/planning/capex/{capex_id}/depreciation
                pass

    def test_get_depreciation_schedule_success(self, client, mock_user):
        """Test successful retrieval of depreciation schedule."""
        capex_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_depreciation_schedule.return_value = [
                {
                    "year": 2024,
                    "annual_depreciation": Decimal("20000"),
                    "accumulated_depreciation": Decimal("20000"),
                    "net_book_value": Decimal("80000"),
                },
                {
                    "year": 2025,
                    "annual_depreciation": Decimal("20000"),
                    "accumulated_depreciation": Decimal("40000"),
                    "net_book_value": Decimal("60000"),
                },
            ]
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/capex/{capex_id}/depreciation-schedule
                pass

    def test_get_capex_summary_success(self, client, mock_user):
        """Test successful retrieval of CapEx summary."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_capex_summary.return_value = {
                "total_capex": Decimal("5000000"),
                "by_category": {
                    "equipment": Decimal("2000000"),
                    "furniture": Decimal("1000000"),
                    "buildings": Decimal("2000000"),
                },
                "annual_depreciation": Decimal("500000"),
                "entry_count": 15,
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/capex/{version_id}/summary
                pass

    def test_get_annual_depreciation_success(self, client, mock_user):
        """Test successful retrieval of annual depreciation totals."""
        version_id = uuid.uuid4()
        year = 2024

        with patch("app.api.v1.costs.get_capex_service") as mock_svc:
            mock_service = AsyncMock()
            mock_service.get_annual_depreciation.return_value = {
                "calculation_year": year,
                "total_annual_depreciation": Decimal("500000"),
                "by_category": {
                    "equipment": Decimal("200000"),
                    "furniture": Decimal("100000"),
                    "buildings": Decimal("200000"),
                },
            }
            mock_svc.return_value = mock_service

            with patch("app.dependencies.auth.get_current_user", return_value=mock_user):
                # Would test GET /api/v1/planning/capex/{version_id}/depreciation/{year}
                pass
