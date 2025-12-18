"""
Tests for Admin API Endpoints

Tests cover:
- Historical data preview endpoint
- Historical data import endpoint
- Import history endpoint
- Template download endpoint
- Historical data deletion endpoint
"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, patch

import pytest
from app.services.admin.historical_import_service import (
    ImportPreviewResult,
    ImportResult,
)


@pytest.fixture
def mock_import_service():
    """Create a mock import service."""
    with patch("app.api.v1.admin.HistoricalImportService") as mock:
        service_instance = AsyncMock()
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_csv_content():
    """Create sample CSV content for testing."""
    return b"fiscal_year,level_code,student_count\n2024,6EME,120\n2024,5EME,115"


@pytest.fixture
def sample_xlsx_content():
    """Create sample XLSX content for testing."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["fiscal_year", "level_code", "student_count"])
    ws.append([2024, "6EME", 120])
    ws.append([2024, "5EME", 115])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.read()


class TestPreviewImportEndpoint:
    """Tests for POST /admin/historical/preview."""

    @pytest.mark.asyncio
    async def test_preview_csv_success(
        self, mock_import_service, sample_csv_content
    ):
        """Test successful CSV preview."""
        mock_import_service.preview_import.return_value = ImportPreviewResult(
            fiscal_year=2024,
            detected_module="enrollment",
            total_rows=2,
            valid_rows=2,
            invalid_rows=0,
            warnings=[],
            errors=[],
            sample_data=[
                {"fiscal_year": 2024, "level_code": "6EME", "student_count": 120},
                {"fiscal_year": 2024, "level_code": "5EME", "student_count": 115},
            ],
            can_import=True,
        )

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/historical/preview",
                files={"file": ("test.csv", sample_csv_content, "text/csv")},
                data={"fiscal_year": "2024"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["fiscal_year"] == 2024
        assert data["detected_module"] == "enrollment"
        assert data["total_rows"] == 2
        assert data["valid_rows"] == 2
        assert data["can_import"] is True

    @pytest.mark.asyncio
    async def test_preview_xlsx_success(
        self, mock_import_service, sample_xlsx_content
    ):
        """Test successful XLSX preview."""
        mock_import_service.preview_import.return_value = ImportPreviewResult(
            fiscal_year=2024,
            detected_module="enrollment",
            total_rows=2,
            valid_rows=2,
            invalid_rows=0,
            warnings=[],
            errors=[],
            sample_data=[],
            can_import=True,
        )

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/historical/preview",
                files={
                    "file": (
                        "test.xlsx",
                        sample_xlsx_content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"fiscal_year": "2024"},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_preview_with_module_override(
        self, mock_import_service, sample_csv_content
    ):
        """Test preview with explicit module specification."""
        mock_import_service.preview_import.return_value = ImportPreviewResult(
            fiscal_year=2024,
            detected_module="enrollment",
            total_rows=2,
            valid_rows=2,
            invalid_rows=0,
            warnings=[],
            errors=[],
            sample_data=[],
            can_import=True,
        )

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/historical/preview",
                files={"file": ("test.csv", sample_csv_content, "text/csv")},
                data={"fiscal_year": "2024", "module": "enrollment"},
            )

        assert response.status_code == 200
        mock_import_service.preview_import.assert_called_once()

    @pytest.mark.asyncio
    async def test_preview_invalid_module(self, sample_csv_content):
        """Test preview with invalid module returns error."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/historical/preview",
                files={"file": ("test.csv", sample_csv_content, "text/csv")},
                data={"fiscal_year": "2024", "module": "invalid_module"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_preview_invalid_file_type(self):
        """Test preview with invalid file type."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/historical/preview",
                files={"file": ("test.txt", b"invalid content", "text/plain")},
                data={"fiscal_year": "2024"},
            )

        assert response.status_code == 400


class TestImportEndpoint:
    """Tests for POST /admin/historical/import."""

    @pytest.mark.asyncio
    async def test_import_success(self, mock_import_service, sample_csv_content):
        """Test successful import."""
        from app.services.admin.historical_import_service import ImportResultStatus

        mock_import_service.import_data.return_value = ImportResult(
            fiscal_year=2024,
            module="enrollment",
            status=ImportResultStatus.SUCCESS,
            imported_count=2,
            updated_count=0,
            skipped_count=0,
            error_count=0,
            message="Import successful",
            errors=[],
        )

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/historical/import",
                files={"file": ("test.csv", sample_csv_content, "text/csv")},
                data={"fiscal_year": "2024"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["fiscal_year"] == 2024
        assert data["module"] == "enrollment"
        assert data["status"] == "success"
        assert data["imported_count"] == 2

    @pytest.mark.asyncio
    async def test_import_with_overwrite(
        self, mock_import_service, sample_csv_content
    ):
        """Test import with overwrite flag."""
        from app.services.admin.historical_import_service import ImportResultStatus

        mock_import_service.import_data.return_value = ImportResult(
            fiscal_year=2024,
            module="enrollment",
            status=ImportResultStatus.SUCCESS,
            imported_count=2,
            updated_count=0,
            skipped_count=0,
            error_count=0,
            message="Import successful",
            errors=[],
        )

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/historical/import",
                files={"file": ("test.csv", sample_csv_content, "text/csv")},
                data={"fiscal_year": "2024", "overwrite": "true"},
            )

        assert response.status_code == 200
        mock_import_service.import_data.assert_called_once()
        call_kwargs = mock_import_service.import_data.call_args.kwargs
        assert call_kwargs.get("overwrite") is True

    @pytest.mark.asyncio
    async def test_import_partial_success(
        self, mock_import_service, sample_csv_content
    ):
        """Test import with partial success."""
        from app.services.admin.historical_import_service import ImportResultStatus

        mock_import_service.import_data.return_value = ImportResult(
            fiscal_year=2024,
            module="enrollment",
            status=ImportResultStatus.PARTIAL,
            imported_count=1,
            updated_count=0,
            skipped_count=1,
            error_count=1,
            message="Import completed with errors",
            errors=["Row 2: Invalid data"],
        )

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/historical/import",
                files={"file": ("test.csv", sample_csv_content, "text/csv")},
                data={"fiscal_year": "2024"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 1
        assert data["skipped_count"] == 1


class TestImportHistoryEndpoint:
    """Tests for GET /admin/historical/history."""

    @pytest.mark.asyncio
    async def test_get_history_success(self, mock_import_service):
        """Test getting import history."""
        mock_import_service.get_import_history.return_value = [
            {
                "fiscal_year": 2024,
                "module": "enrollment",
                "record_count": 15,
                "last_imported": "2024-01-15T10:30:00Z",
            },
            {
                "fiscal_year": 2023,
                "module": "revenue",
                "record_count": 42,
                "last_imported": "2024-01-10T14:20:00Z",
            },
        ]

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/admin/historical/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_history_with_filters(self, mock_import_service):
        """Test getting history with fiscal year filter."""
        mock_import_service.get_import_history.return_value = [
            {
                "fiscal_year": 2024,
                "module": "enrollment",
                "record_count": 15,
                "last_imported": "2024-01-15T10:30:00Z",
            },
        ]

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/admin/historical/history",
                params={"fiscal_year": 2024, "module": "enrollment"},
            )

        assert response.status_code == 200
        mock_import_service.get_import_history.assert_called_once()


class TestTemplateEndpoint:
    """Tests for GET /admin/historical/template/{module}."""

    @pytest.mark.asyncio
    async def test_download_enrollment_template(self):
        """Test downloading enrollment template."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/admin/historical/template/enrollment")

        assert response.status_code == 200
        assert "application/vnd.openxmlformats" in response.headers["content-type"]
        assert "attachment" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_download_dhg_template(self):
        """Test downloading DHG template."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/admin/historical/template/dhg")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_download_revenue_template(self):
        """Test downloading revenue template."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/admin/historical/template/revenue")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_download_costs_template(self):
        """Test downloading costs template."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/admin/historical/template/costs")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_download_capex_template(self):
        """Test downloading CapEx template."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/admin/historical/template/capex")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_download_invalid_template(self):
        """Test downloading template for invalid module."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/admin/historical/template/invalid")

        assert response.status_code == 400


class TestDeleteEndpoint:
    """Tests for DELETE /admin/historical/{fiscal_year}."""

    @pytest.mark.asyncio
    async def test_delete_year_success(self, mock_import_service):
        """Test deleting historical data for a year."""
        mock_import_service._delete_existing.return_value = 15
        mock_import_service.session = AsyncMock()
        mock_import_service.session.commit = AsyncMock()

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete("/api/v1/admin/historical/2024")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_year_with_module(self, mock_import_service):
        """Test deleting historical data for a year and module."""
        mock_import_service._delete_existing.return_value = 15
        mock_import_service.session = AsyncMock()
        mock_import_service.session.commit = AsyncMock()

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(
                "/api/v1/admin/historical/2024",
                params={"module": "enrollment"},
            )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_invalid_module(self):
        """Test deleting with invalid module."""
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(
                "/api/v1/admin/historical/2024",
                params={"module": "invalid"},
            )

        assert response.status_code == 400
