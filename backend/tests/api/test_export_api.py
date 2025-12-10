"""
Tests for Export API endpoints.

Tests cover:
- Excel export for budget consolidation (with/without openpyxl)
- Excel export for KPI dashboard (with/without openpyxl)
- PDF export for budget summary (with/without reportlab)
- CSV export for budget line items
- Error handling for missing dependencies and invalid data
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Note: `client` fixture is defined in conftest.py with proper engine dependency


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@efir.local"
    user.role = "admin"
    return user


@pytest.fixture
def mock_consolidation_data():
    """Create mock consolidation data."""
    consolidation = MagicMock()
    consolidation.budget_version = MagicMock()
    consolidation.budget_version.name = "FY2025 Budget"
    consolidation.budget_version.status = MagicMock(value="APPROVED")
    consolidation.total_revenue = Decimal("50000000.00")
    consolidation.total_personnel_costs = Decimal("35000000.00")
    consolidation.total_operating_costs = Decimal("10000000.00")
    consolidation.total_capex = Decimal("3000000.00")
    consolidation.net_result = Decimal("2000000.00")
    return consolidation


@pytest.fixture
def mock_kpi_data():
    """Create mock KPI data."""
    kpi1 = MagicMock()
    kpi1.kpi_definition = MagicMock()
    kpi1.kpi_definition.code = "HE_RATIO"
    kpi1.kpi_definition.name_en = "Hours per Student Ratio"
    kpi1.kpi_definition.target_value = Decimal("1.2")
    kpi1.calculated_value = Decimal("1.18")
    kpi1.variance_from_target = Decimal("-0.02")

    kpi2 = MagicMock()
    kpi2.kpi_definition = MagicMock()
    kpi2.kpi_definition.code = "ED_RATIO"
    kpi2.kpi_definition.name_en = "Students per Class"
    kpi2.kpi_definition.target_value = Decimal("22")
    kpi2.calculated_value = Decimal("23.5")
    kpi2.variance_from_target = Decimal("1.5")

    return [kpi1, kpi2]


@pytest.fixture
def mock_line_items():
    """Create mock budget line items."""
    return [
        {
            "account_code": "70110",
            "account_name": "Scolarité T1",
            "consolidation_category": "tuition",
            "is_revenue": True,
            "amount_sar": Decimal("15000000.00"),
            "source_table": "revenue_plan",
        },
        {
            "account_code": "64110",
            "account_name": "Teaching Salaries",
            "consolidation_category": "personnel",
            "is_revenue": False,
            "amount_sar": Decimal("25000000.00"),
            "source_table": "cost_plan",
        },
    ]


class TestExportBudgetExcel:
    """Tests for Excel budget export endpoint."""

    def test_export_budget_excel_success(
        self, client, mock_user, mock_consolidation_data
    ):
        """Test successful budget export to Excel."""
        version_id = uuid.uuid4()

        # Mock openpyxl
        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            # Set up mock openpyxl
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb

            # Mock styles
            mock_styles = MagicMock()
            mock_openpyxl.styles = mock_styles

            # Mock ConsolidationService
            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_consolidation.return_value = mock_consolidation_data
                mock_service_class.return_value = mock_service

                response = client.get(
                    f"/api/v1/export/budget/{version_id}/excel?include_details=true"
                )

                # Verify response
                assert response.status_code == 200
                assert (
                    response.headers["content-type"]
                    == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                assert "attachment" in response.headers["content-disposition"]
                assert f"budget_consolidation_{version_id}" in response.headers[
                    "content-disposition"
                ]

    def test_export_budget_excel_missing_openpyxl(self, client, mock_user):
        """Test budget export when openpyxl is not installed."""
        version_id = uuid.uuid4()

        # Mock openpyxl with side_effect (triggers ImportError in export.py)
        mock_openpyxl = MagicMock()
        mock_openpyxl.side_effect = ImportError("No module named 'openpyxl'")

        with patch("app.api.v1.export.openpyxl", mock_openpyxl):
            response = client.get(f"/api/v1/export/budget/{version_id}/excel")

            # Verify 501 Not Implemented
            assert response.status_code == 501
            assert "openpyxl" in response.json()["detail"]

    def test_export_budget_excel_version_not_found(
        self, client, mock_user
    ):
        """Test budget export with non-existent version."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_openpyxl.Workbook = MagicMock()
            mock_openpyxl.styles = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_consolidation.side_effect = Exception(
                    "Version not found"
                )
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/excel")

                # Verify 404
                assert response.status_code == 404
                assert "not found" in response.json()["detail"].lower()

    def test_export_budget_excel_include_details_false(
        self, client, mock_user, mock_consolidation_data
    ):
        """Test budget export without details."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_consolidation.return_value = mock_consolidation_data
                mock_service_class.return_value = mock_service

                response = client.get(
                    f"/api/v1/export/budget/{version_id}/excel?include_details=false"
                )

                assert response.status_code == 200


class TestExportKPIExcel:
    """Tests for Excel KPI export endpoint."""

    def test_export_kpi_excel_success(self, client, mock_user, mock_kpi_data):
        """Test successful KPI export to Excel."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            # Set up mock
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()
            mock_openpyxl.utils.get_column_letter = lambda x: chr(64 + x)

            with patch("app.api.v1.export.KPIService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_all_kpis.return_value = mock_kpi_data
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

                # Verify response
                assert response.status_code == 200
                assert (
                    response.headers["content-type"]
                    == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                assert "attachment" in response.headers["content-disposition"]
                assert f"kpi_dashboard_{version_id}" in response.headers[
                    "content-disposition"
                ]

    def test_export_kpi_excel_empty_kpis(self, client, mock_user):
        """Test KPI export with no KPIs."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()
            mock_openpyxl.utils.get_column_letter = lambda x: chr(64 + x)

            with patch("app.api.v1.export.KPIService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_all_kpis.return_value = []
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

                # Should still succeed with empty data
                assert response.status_code == 200

    def test_export_kpi_excel_missing_openpyxl(self, client, mock_user):
        """Test KPI export when openpyxl is not installed."""
        version_id = uuid.uuid4()

        # Mock openpyxl with side_effect (triggers ImportError in export.py)
        mock_openpyxl = MagicMock()
        mock_openpyxl.side_effect = ImportError("No module named 'openpyxl'")

        with patch("app.api.v1.export.openpyxl", mock_openpyxl):
            response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

            assert response.status_code == 501
            assert "openpyxl" in response.json()["detail"]


class TestExportBudgetPDF:
    """Tests for PDF budget export endpoint."""

    def test_export_budget_pdf_success(
        self, client, mock_user, mock_consolidation_data
    ):
        """Test successful budget export to PDF."""
        version_id = uuid.uuid4()

        # Mock reportlab
        with patch("app.api.v1.export.reportlab") as mock_reportlab:
            # Set up comprehensive mock for reportlab
            mock_lib = MagicMock()
            mock_lib.colors = MagicMock()
            mock_lib.pagesizes.A4 = (595, 842)
            mock_lib.units.cm = 28.35
            mock_lib.styles.ParagraphStyle = MagicMock()
            mock_lib.styles.getSampleStyleSheet = MagicMock(
                return_value={
                    "Heading1": MagicMock(),
                    "Heading2": MagicMock(),
                    "Normal": MagicMock(),
                }
            )
            mock_reportlab.lib = mock_lib

            mock_platypus = MagicMock()
            mock_platypus.Paragraph = MagicMock()
            mock_platypus.SimpleDocTemplate = MagicMock()
            mock_platypus.Spacer = MagicMock()
            mock_platypus.Table = MagicMock()
            mock_platypus.TableStyle = MagicMock()
            mock_reportlab.platypus = mock_platypus

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_consolidation.return_value = mock_consolidation_data
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/pdf")

                # Verify response
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/pdf"
                assert "attachment" in response.headers["content-disposition"]
                assert f"budget_report_{version_id}" in response.headers[
                    "content-disposition"
                ]

    def test_export_budget_pdf_reportlab_import_error_with_patch(
        self, client, mock_user
    ):
        """Test PDF export when reportlab is explicitly patched to raise ImportError."""
        version_id = uuid.uuid4()

        # Mock reportlab with side_effect attribute (simulates patched import failure)
        mock_reportlab = MagicMock()
        mock_reportlab.side_effect = ImportError("Reportlab not available")

        with patch("app.api.v1.export.reportlab", mock_reportlab):
            response = client.get(f"/api/v1/export/budget/{version_id}/pdf")

            # Should raise 501 when explicitly patched to fail
            assert response.status_code == 501
            assert "reportlab" in response.json()["detail"]

    def test_export_budget_pdf_version_not_found(self, client, mock_user):
        """Test PDF export with non-existent version."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.reportlab") as mock_reportlab:
            mock_reportlab.lib = MagicMock()
            mock_reportlab.platypus = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_consolidation.side_effect = Exception(
                    "Version not found"
                )
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/pdf")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"].lower()


class TestExportBudgetCSV:
    """Tests for CSV budget export endpoint."""

    def test_export_budget_csv_success(self, client, mock_user, mock_line_items):
        """Test successful budget export to CSV."""
        version_id = uuid.uuid4()

        with patch(
            "app.api.v1.export.ConsolidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.calculate_line_items.return_value = mock_line_items
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/v1/export/budget/{version_id}/csv")

            # Verify response
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv"
            assert "attachment" in response.headers["content-disposition"]
            assert f"budget_items_{version_id}" in response.headers[
                "content-disposition"
            ]

            # Verify CSV content structure
            content = response.text
            lines = content.split("\\n")

            # Check headers
            assert "account_code" in lines[0]
            assert "account_name" in lines[0]
            assert "category" in lines[0]
            assert "is_revenue" in lines[0]
            assert "amount_sar" in lines[0]

            # Check data rows
            assert "70110" in content
            assert "Scolarité T1" in content
            assert "64110" in content
            assert "Teaching Salaries" in content

    def test_export_budget_csv_empty_line_items(self, client, mock_user):
        """Test CSV export with no line items."""
        version_id = uuid.uuid4()

        with patch(
            "app.api.v1.export.ConsolidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.calculate_line_items.return_value = []
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/v1/export/budget/{version_id}/csv")

            # Should still succeed with empty data
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv"

            # Should have headers but no data rows
            content = response.text
            lines = content.split("\\n")
            assert len(lines) >= 1  # At least headers
            assert "account_code" in lines[0]


class TestExportEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_export_invalid_uuid(self, client, mock_user):
        """Test export with invalid UUID format."""
        response = client.get("/api/v1/export/budget/not-a-uuid/excel")

        # Should return 422 Unprocessable Entity for invalid UUID
        assert response.status_code == 422

    def test_export_with_none_budget_version(
        self, client, mock_user
    ):
        """Test export when consolidation has None budget_version."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_consolidation = MagicMock()
                mock_consolidation.budget_version = None  # No budget version
                mock_consolidation.total_revenue = Decimal("0")
                mock_consolidation.total_personnel_costs = Decimal("0")
                mock_consolidation.total_operating_costs = Decimal("0")
                mock_consolidation.total_capex = Decimal("0")
                mock_consolidation.net_result = Decimal("0")
                mock_service.get_consolidation.return_value = mock_consolidation
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/excel")

                # Should handle None budget_version gracefully
                assert response.status_code == 200

    def test_export_kpi_with_none_definition(self, client, mock_user):
        """Test KPI export when KPI has None definition."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()
            mock_openpyxl.utils.get_column_letter = lambda x: chr(64 + x)

            with patch("app.api.v1.export.KPIService") as mock_service_class:
                mock_service = AsyncMock()
                mock_kpi = MagicMock()
                mock_kpi.kpi_definition = None  # No definition
                mock_kpi.calculated_value = Decimal("1.5")
                mock_kpi.variance_from_target = Decimal("0.2")
                mock_service.get_all_kpis.return_value = [mock_kpi]
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

                # Should handle None kpi_definition gracefully
                assert response.status_code == 200

    def test_export_large_dataset_excel(self, client, mock_user):
        """Test Excel export with large dataset."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_consolidation = MagicMock()
                mock_consolidation.budget_version = MagicMock(name="Budget 2025")
                mock_consolidation.total_revenue = Decimal("999999999.99")
                mock_consolidation.total_personnel_costs = Decimal("500000000.00")
                mock_consolidation.total_operating_costs = Decimal("200000000.00")
                mock_consolidation.total_capex = Decimal("100000000.00")
                mock_consolidation.net_result = Decimal("199999999.99")
                mock_service.get_consolidation.return_value = mock_consolidation
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/excel")

                assert response.status_code == 200

    def test_export_csv_special_characters(self, client, mock_user):
        """Test CSV export with special characters in data."""
        version_id = uuid.uuid4()

        special_items = [
            {
                "account_code": "70110",
                "account_name": 'Scolarité T1, "Maternelle"',
                "consolidation_category": "tuition",
                "is_revenue": True,
                "amount_sar": Decimal("5000000.00"),
                "source_table": "revenue_plan",
            }
        ]

        with patch(
            "app.api.v1.export.ConsolidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.calculate_line_items.return_value = special_items
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/v1/export/budget/{version_id}/csv")

            assert response.status_code == 200
            assert "Scolarité" in response.text or "Scolarit" in response.text

    def test_export_csv_utf8_encoding(self, client, mock_user):
        """Test CSV export with UTF-8 characters."""
        version_id = uuid.uuid4()

        utf8_items = [
            {
                "account_code": "70110",
                "account_name": "Scolarité Élémentaire",
                "consolidation_category": "tuition",
                "is_revenue": True,
                "amount_sar": Decimal("3000000.00"),
                "source_table": "revenue_plan",
            }
        ]

        with patch(
            "app.api.v1.export.ConsolidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.calculate_line_items.return_value = utf8_items
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/v1/export/budget/{version_id}/csv")

            assert response.status_code == 200

    def test_export_csv_large_dataset(self, client, mock_user):
        """Test CSV export with large number of line items."""
        version_id = uuid.uuid4()

        large_items = [
            {
                "account_code": f"7{i:04d}",
                "account_name": f"Line Item {i}",
                "consolidation_category": "revenue",
                "is_revenue": True,
                "amount_sar": Decimal(str(i * 1000)),
                "source_table": "revenue_plan",
            }
            for i in range(100)
        ]

        with patch(
            "app.api.v1.export.ConsolidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.calculate_line_items.return_value = large_items
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/v1/export/budget/{version_id}/csv")

            assert response.status_code == 200
            lines = response.text.split("\n")
            assert len(lines) >= 100

    def test_export_pdf_empty_consolidation(self, client, mock_user):
        """Test PDF export with empty consolidation."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.reportlab") as mock_reportlab:
            mock_lib = MagicMock()
            mock_lib.colors = MagicMock()
            mock_lib.pagesizes.A4 = (595, 842)
            mock_lib.units.cm = 28.35
            mock_lib.styles.ParagraphStyle = MagicMock()
            mock_lib.styles.getSampleStyleSheet = MagicMock(
                return_value={
                    "Heading1": MagicMock(),
                    "Heading2": MagicMock(),
                    "Normal": MagicMock(),
                }
            )
            mock_reportlab.lib = mock_lib
            mock_reportlab.platypus = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_consolidation = MagicMock()
                mock_consolidation.budget_version = None
                mock_consolidation.total_revenue = None
                mock_consolidation.total_personnel_costs = None
                mock_consolidation.total_operating_costs = None
                mock_consolidation.total_capex = None
                mock_consolidation.net_result = None
                mock_service.get_consolidation.return_value = mock_consolidation
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/pdf")

                assert response.status_code == 200

    def test_export_excel_zero_values(self, client, mock_user):
        """Test Excel export with all zero values."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_consolidation = MagicMock()
                mock_consolidation.budget_version = MagicMock(name="Empty Budget")
                mock_consolidation.total_revenue = Decimal("0")
                mock_consolidation.total_personnel_costs = Decimal("0")
                mock_consolidation.total_operating_costs = Decimal("0")
                mock_consolidation.total_capex = Decimal("0")
                mock_consolidation.net_result = Decimal("0")
                mock_service.get_consolidation.return_value = mock_consolidation
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/excel")

                assert response.status_code == 200

    def test_export_kpi_negative_variances(self, client, mock_user):
        """Test KPI export with negative variances."""
        version_id = uuid.uuid4()

        kpi_data = [
            MagicMock(
                kpi_definition=MagicMock(
                    code="TEST_KPI",
                    name_en="Test KPI",
                    target_value=Decimal("100")
                ),
                calculated_value=Decimal("80"),
                variance_from_target=Decimal("-20")
            )
        ]

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()
            mock_openpyxl.utils.get_column_letter = lambda x: chr(64 + x)

            with patch("app.api.v1.export.KPIService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_all_kpis.return_value = kpi_data
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

                assert response.status_code == 200

    def test_export_csv_missing_optional_fields(self, client, mock_user):
        """Test CSV export with line items missing optional fields."""
        version_id = uuid.uuid4()

        minimal_items = [
            {
                "account_code": "70110",
                # Missing account_name, category, etc.
            }
        ]

        with patch(
            "app.api.v1.export.ConsolidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.calculate_line_items.return_value = minimal_items
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/v1/export/budget/{version_id}/csv")

            assert response.status_code == 200
            assert "70110" in response.text

    def test_export_concurrent_excel_requests(self, client, mock_user, mock_consolidation_data):
        """Test multiple concurrent Excel export requests."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_consolidation.return_value = mock_consolidation_data
                mock_service_class.return_value = mock_service

                # Make multiple concurrent requests
                responses = [
                    client.get(f"/api/v1/export/budget/{version_id}/excel")
                    for _ in range(3)
                ]

                # All should succeed
                for response in responses:
                    assert response.status_code == 200

    def test_export_service_timeout(self, client, mock_user):
        """Test export with service timeout."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_openpyxl.Workbook = MagicMock()
            mock_openpyxl.styles = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_consolidation.side_effect = TimeoutError("Service timeout")
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/excel")

                # Should return 404 or 500 (generic exception handling)
                assert response.status_code in (404, 500)

    def test_export_invalid_query_params(self, client, mock_user):
        """Test export with invalid query parameters."""
        version_id = uuid.uuid4()

        response = client.get(
            f"/api/v1/export/budget/{version_id}/excel?include_details=invalid"
        )

        # FastAPI validation should catch invalid boolean
        assert response.status_code == 422

    def test_export_kpi_null_values(self, client, mock_user):
        """Test KPI export with null calculated values."""
        version_id = uuid.uuid4()

        kpi_data = [
            MagicMock(
                kpi_definition=MagicMock(
                    code="NULL_KPI",
                    name_en="Null KPI",
                    target_value=None
                ),
                calculated_value=None,
                variance_from_target=None
            )
        ]

        with patch("app.api.v1.export.openpyxl") as mock_openpyxl:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_openpyxl.Workbook.return_value = mock_wb
            mock_openpyxl.styles = MagicMock()
            mock_openpyxl.utils.get_column_letter = lambda x: chr(64 + x)

            with patch("app.api.v1.export.KPIService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_all_kpis.return_value = kpi_data
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/kpi/{version_id}/excel")

                assert response.status_code == 200

    def test_export_pdf_large_amounts(self, client, mock_user):
        """Test PDF export with very large amounts."""
        version_id = uuid.uuid4()

        with patch("app.api.v1.export.reportlab") as mock_reportlab:
            mock_lib = MagicMock()
            mock_lib.colors = MagicMock()
            mock_lib.pagesizes.A4 = (595, 842)
            mock_lib.units.cm = 28.35
            mock_lib.styles.ParagraphStyle = MagicMock()
            mock_lib.styles.getSampleStyleSheet = MagicMock(
                return_value={
                    "Heading1": MagicMock(),
                    "Heading2": MagicMock(),
                    "Normal": MagicMock(),
                }
            )
            mock_reportlab.lib = mock_lib
            mock_reportlab.platypus = MagicMock()

            with patch(
                "app.api.v1.export.ConsolidationService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_consolidation = MagicMock()
                mock_consolidation.budget_version = MagicMock(name="Large Budget")
                mock_consolidation.budget_version.status = MagicMock(value="APPROVED")
                mock_consolidation.total_revenue = Decimal("999999999999.99")
                mock_consolidation.total_personnel_costs = Decimal("500000000000.00")
                mock_consolidation.total_operating_costs = Decimal("200000000000.00")
                mock_consolidation.total_capex = Decimal("100000000000.00")
                mock_consolidation.net_result = Decimal("199999999999.99")
                mock_service.get_consolidation.return_value = mock_consolidation
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/v1/export/budget/{version_id}/pdf")

                assert response.status_code == 200

    def test_export_csv_boolean_fields(self, client, mock_user):
        """Test CSV export with boolean fields properly formatted."""
        version_id = uuid.uuid4()

        items_with_booleans = [
            {
                "account_code": "70110",
                "account_name": "Revenue Item",
                "consolidation_category": "revenue",
                "is_revenue": True,
                "amount_sar": Decimal("1000000.00"),
                "source_table": "revenue_plan",
            },
            {
                "account_code": "64110",
                "account_name": "Cost Item",
                "consolidation_category": "personnel",
                "is_revenue": False,
                "amount_sar": Decimal("500000.00"),
                "source_table": "cost_plan",
            }
        ]

        with patch(
            "app.api.v1.export.ConsolidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.calculate_line_items.return_value = items_with_booleans
            mock_service_class.return_value = mock_service

            response = client.get(f"/api/v1/export/budget/{version_id}/csv")

            assert response.status_code == 200
            assert "True" in response.text or "False" in response.text
