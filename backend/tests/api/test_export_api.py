"""
Tests for Export API endpoints.

Covers:
- Excel export (budget consolidation, KPI dashboard)
- PDF export (budget summary)
- CSV export (budget line items)
- Error handling (missing dependencies, invalid version IDs)
- File generation and streaming

Target Coverage: 90%+
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.main import app
from app.models.configuration import BudgetVersion, BudgetVersionStatus
from app.models.consolidation import BudgetConsolidation
from app.models.analysis import KPICalculation
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_budget_version():
    """Create mock budget version."""
    version = MagicMock(spec=BudgetVersion)
    version.id = uuid.uuid4()
    version.name = "Budget 2024-2025"
    version.fiscal_year = 2024
    version.status = BudgetVersionStatus.WORKING
    return version


@pytest.fixture
def mock_consolidation(mock_budget_version):
    """Create mock consolidation data."""
    consolidation = MagicMock(spec=BudgetConsolidation)
    consolidation.budget_version = mock_budget_version
    consolidation.total_revenue = Decimal("63000000.00")
    consolidation.total_personnel_costs = Decimal("45000000.00")
    consolidation.total_operating_costs = Decimal("12000000.00")
    consolidation.total_capex = Decimal("5000000.00")
    consolidation.net_result = Decimal("1000000.00")
    return consolidation


@pytest.fixture
def mock_kpis():
    """Create mock KPI data."""
    kpis = []
    for i in range(3):
        kpi = MagicMock(spec=KPICalculation)
        kpi.kpi_definition = MagicMock()
        kpi.kpi_definition.code = f"KPI_{i+1}"
        kpi.kpi_definition.name_en = f"KPI {i+1} Name"
        kpi.kpi_definition.target_value = Decimal("100.00")
        kpi.calculated_value = Decimal("95.00") if i == 0 else Decimal("105.00")
        kpi.variance_from_target = Decimal("-5.00") if i == 0 else Decimal("5.00")
        kpis.append(kpi)
    return kpis


class TestExcelExport:
    """Test Excel export endpoints."""

    @pytest.mark.asyncio
    async def test_export_budget_excel_success(
        self, client, mock_consolidation
    ):
        """Test successful budget Excel export."""
        import openpyxl
        from io import BytesIO
        
        with patch("app.api.v1.export.ConsolidationService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_consolidation = AsyncMock(return_value=mock_consolidation)
            mock_service_class.return_value = mock_service

            version_id = mock_consolidation.budget_version.id
            response = client.get(f"/api/v1/export/budget/{version_id}/excel")

            # Assertions
            assert response.status_code == 200
            assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]
            assert ".xlsx" in response.headers["content-disposition"]
            
            # Verify file can be opened
            wb = openpyxl.load_workbook(BytesIO(response.content))
            assert "Summary" in wb.sheetnames

    @patch("app.api.v1.export.openpyxl")
    @patch("app.api.v1.export.ConsolidationService")
    def test_export_budget_excel_without_details(
        self, mock_service_class, mock_openpyxl, client, mock_consolidation
    ):
        """Test budget Excel export with include_details=False."""
        mock_service = AsyncMock()
        mock_service.get_consolidation = AsyncMock(return_value=mock_consolidation)
        mock_service_class.return_value = mock_service

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_openpyxl.Workbook.return_value = mock_wb

        version_id = mock_consolidation.budget_version.id
        response = client.get(
            f"/api/v1/export/budget/{version_id}/excel?include_details=false"
        )

        assert response.status_code == 200
        assert "attachment" in response.headers["content-disposition"]

    @patch("app.api.v1.export.ConsolidationService")
    def test_export_budget_excel_version_not_found(
        self, mock_service_class, client
    ):
        """Test Excel export with invalid version ID."""
        mock_service = AsyncMock()
        mock_service.get_consolidation = AsyncMock(side_effect=Exception("Not found"))
        mock_service_class.return_value = mock_service

        version_id = uuid.uuid4()
        response = client.get(f"/api/v1/export/budget/{version_id}/excel")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_budget_excel_missing_openpyxl(self, client):
        """Test Excel export when openpyxl is not installed."""
        with patch("app.api.v1.export.openpyxl", side_effect=ImportError()):
            version_id = uuid.uuid4()
            response = client.get(f"/api/v1/export/budget/{version_id}/excel")

            assert response.status_code == 501
            assert "openpyxl" in response.json()["detail"].lower()

    @patch("app.api.v1.export.openpyxl")
    @patch("app.api.v1.export.KPIService")
    def test_export_kpi_excel_success(
        self, mock_service_class, mock_openpyxl, client, mock_kpis
    ):
        """Test successful KPI Excel export."""
        mock_service = AsyncMock()
        mock_service.get_all_kpis = AsyncMock(return_value=mock_kpis)
        mock_service_class.return_value = mock_service

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_openpyxl.Workbook.return_value = mock_wb

        version_id = uuid.uuid4()
        response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "kpi_dashboard" in response.headers["content-disposition"]
        mock_service.get_all_kpis.assert_called_once_with(version_id)

    def test_export_kpi_excel_missing_openpyxl(self, client):
        """Test KPI Excel export when openpyxl is not installed."""
        with patch("app.api.v1.export.openpyxl", side_effect=ImportError()):
            version_id = uuid.uuid4()
            response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

            assert response.status_code == 501
            assert "openpyxl" in response.json()["detail"].lower()


class TestPDFExport:
    """Test PDF export endpoints."""

    @patch("app.api.v1.export.reportlab")
    @patch("app.api.v1.export.ConsolidationService")
    def test_export_budget_pdf_success(
        self, mock_service_class, mock_reportlab, client, mock_consolidation
    ):
        """Test successful budget PDF export."""
        mock_service = AsyncMock()
        mock_service.get_consolidation = AsyncMock(return_value=mock_consolidation)
        mock_service_class.return_value = mock_service

        mock_doc = MagicMock()
        mock_reportlab.platypus.SimpleDocTemplate.return_value = mock_doc

        version_id = mock_consolidation.budget_version.id
        response = client.get(f"/api/v1/export/budget/{version_id}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert ".pdf" in response.headers["content-disposition"]
        mock_doc.build.assert_called_once()

    @patch("app.api.v1.export.reportlab")
    @patch("app.api.v1.export.ConsolidationService")
    def test_export_budget_pdf_version_not_found(
        self, mock_service_class, mock_reportlab, client
    ):
        """Test PDF export with invalid version ID."""
        mock_service = AsyncMock()
        mock_service.get_consolidation = AsyncMock(side_effect=Exception("Not found"))
        mock_service_class.return_value = mock_service

        version_id = uuid.uuid4()
        response = client.get(f"/api/v1/export/budget/{version_id}/pdf")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_budget_pdf_missing_reportlab(self, client):
        """Test PDF export when reportlab is not installed."""
        with patch("app.api.v1.export.reportlab", side_effect=ImportError()):
            version_id = uuid.uuid4()
            response = client.get(f"/api/v1/export/budget/{version_id}/pdf")

            assert response.status_code == 501
            assert "reportlab" in response.json()["detail"].lower()


class TestCSVExport:
    """Test CSV export endpoints."""

    @patch("app.api.v1.export.ConsolidationService")
    def test_export_budget_csv_success(
        self, mock_service_class, client
    ):
        """Test successful budget CSV export."""
        mock_service = AsyncMock()
        mock_line_items = [
            {
                "account_code": "70110",
                "account_name": "Tuition T1",
                "consolidation_category": "Revenue",
                "is_revenue": True,
                "amount_sar": Decimal("25000000.00"),
                "source_table": "revenue",
            },
            {
                "account_code": "64110",
                "account_name": "Teaching Salaries",
                "consolidation_category": "Personnel",
                "is_revenue": False,
                "amount_sar": Decimal("30000000.00"),
                "source_table": "costs",
            },
        ]
        mock_service.calculate_line_items = AsyncMock(return_value=mock_line_items)
        mock_service_class.return_value = mock_service

        version_id = uuid.uuid4()
        response = client.get(f"/api/v1/export/budget/{version_id}/csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "attachment" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]
        
        # Verify CSV content
        content = response.text
        assert "account_code" in content
        assert "70110" in content
        assert "64110" in content
        mock_service.calculate_line_items.assert_called_once_with(version_id)

    @patch("app.api.v1.export.ConsolidationService")
    def test_export_budget_csv_empty_data(
        self, mock_service_class, client
    ):
        """Test CSV export with empty line items."""
        mock_service = AsyncMock()
        mock_service.calculate_line_items = AsyncMock(return_value=[])
        mock_service_class.return_value = mock_service

        version_id = uuid.uuid4()
        response = client.get(f"/api/v1/export/budget/{version_id}/csv")

        assert response.status_code == 200
        assert "account_code" in response.text  # Header should still be present

    @patch("app.api.v1.export.ConsolidationService")
    def test_export_budget_csv_service_error(
        self, mock_service_class, client
    ):
        """Test CSV export when service raises an error."""
        mock_service = AsyncMock()
        mock_service.calculate_line_items = AsyncMock(side_effect=Exception("Database error"))
        mock_service_class.return_value = mock_service

        version_id = uuid.uuid4()
        # The endpoint doesn't catch service errors, so this will raise
        # In a real scenario, we'd want to handle this gracefully
        with pytest.raises(Exception):
            client.get(f"/api/v1/export/budget/{version_id}/csv")


class TestExportEdgeCases:
    """Test edge cases and error scenarios."""

    @patch("app.api.v1.export.openpyxl")
    @patch("app.api.v1.export.ConsolidationService")
    def test_export_excel_with_none_values(
        self, mock_service_class, mock_openpyxl, client, mock_consolidation
    ):
        """Test Excel export when consolidation has None values."""
        # Set some values to None
        mock_consolidation.total_revenue = None
        mock_consolidation.total_personnel_costs = None
        mock_consolidation.net_result = None

        mock_service = AsyncMock()
        mock_service.get_consolidation = AsyncMock(return_value=mock_consolidation)
        mock_service_class.return_value = mock_service

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_openpyxl.Workbook.return_value = mock_wb

        version_id = mock_consolidation.budget_version.id
        response = client.get(f"/api/v1/export/budget/{version_id}/excel")

        # Should still succeed, using Decimal("0") for None values
        assert response.status_code == 200

    @patch("app.api.v1.export.openpyxl")
    @patch("app.api.v1.export.KPIService")
    def test_export_kpi_excel_with_none_values(
        self, mock_service_class, mock_openpyxl, client
    ):
        """Test KPI Excel export when KPIs have None values."""
        kpi = MagicMock()
        kpi.kpi_definition = None
        kpi.calculated_value = None
        kpi.variance_from_target = None

        mock_service = AsyncMock()
        mock_service.get_all_kpis = AsyncMock(return_value=[kpi])
        mock_service_class.return_value = mock_service

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_openpyxl.Workbook.return_value = mock_wb

        version_id = uuid.uuid4()
        response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

        # Should handle None values gracefully
        assert response.status_code == 200

    def test_export_invalid_uuid_format(self, client):
        """Test export with invalid UUID format."""
        response = client.get("/api/v1/export/budget/invalid-uuid/excel")
        assert response.status_code == 422  # Validation error

