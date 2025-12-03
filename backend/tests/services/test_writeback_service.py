"""
Tests for WritebackService.

Tests cover:
- Module cache mapping
- Service initialization
- Cell CRUD operations (with mocking)
- Optimistic locking logic
- Schema validations

Note: Full integration tests require PostgreSQL with efir_budget schema.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.schemas.writeback import (
    BatchUpdateRequest,
    CellCreateRequest,
    CellUpdate,
    CellUpdateRequest,
    CommentRequest,
    LockRequest,
    UndoRequest,
    UnlockRequest,
)
from app.services.exceptions import (
    CellLockedError,
    NotFoundError,
    VersionConflictError,
)
from app.services.writeback_service import (
    MODULE_TO_CACHE_ENTITY,
    WritebackService,
)
from sqlalchemy.ext.asyncio import AsyncSession


class TestModuleCacheMapping:
    """Tests for module to cache entity mapping."""

    def test_module_mapping_defined(self):
        """Test that module to cache entity mapping is defined."""
        assert "enrollment" in MODULE_TO_CACHE_ENTITY
        assert "class_structure" in MODULE_TO_CACHE_ENTITY
        assert "dhg" in MODULE_TO_CACHE_ENTITY
        assert "revenue" in MODULE_TO_CACHE_ENTITY
        assert "personnel_costs" in MODULE_TO_CACHE_ENTITY
        assert "operating_costs" in MODULE_TO_CACHE_ENTITY
        assert "capex" in MODULE_TO_CACHE_ENTITY
        assert "consolidation" in MODULE_TO_CACHE_ENTITY

    def test_module_mapping_values(self):
        """Test that module mapping has expected cache entity values."""
        assert MODULE_TO_CACHE_ENTITY["enrollment"] == "enrollment"
        assert MODULE_TO_CACHE_ENTITY["dhg"] == "dhg_calculations"
        assert MODULE_TO_CACHE_ENTITY["consolidation"] == "budget_consolidation"

    def test_all_modules_mapped(self):
        """Test that all expected modules are mapped."""
        expected_modules = [
            "enrollment",
            "class_structure",
            "dhg",
            "revenue",
            "personnel_costs",
            "operating_costs",
            "capex",
            "consolidation",
        ]
        for module in expected_modules:
            assert module in MODULE_TO_CACHE_ENTITY


class TestWritebackServiceInit:
    """Tests for WritebackService initialization."""

    @pytest.mark.asyncio
    async def test_service_init(
        self,
        db_session: AsyncSession,
    ):
        """Test service initialization."""
        service = WritebackService(db_session)
        assert service.session == db_session


class TestGetCellById:
    """Tests for cell retrieval by ID."""

    @pytest.mark.asyncio
    async def test_get_cell_success(self):
        """Test successful cell retrieval."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": uuid4(),
            "budget_version_id": uuid4(),
            "module_code": "enrollment",
            "entity_id": uuid4(),
            "field_name": "student_count",
            "period_code": "2025",
            "value_numeric": Decimal("100"),
            "value_text": None,
            "value_type": "numeric",
            "is_locked": False,
            "lock_reason": None,
            "locked_by": None,
            "locked_at": None,
            "version": 1,
            "modified_by": uuid4(),
            "modified_at": datetime.utcnow(),
            "created_by_id": uuid4(),
            "created_at": datetime.utcnow(),
            "comment_count": 0,
            "unresolved_comment_count": 0,
        }
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        cell_id = uuid4()
        result = await service.get_cell_by_id(cell_id)

        assert result is not None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cell_not_found_raises(self):
        """Test cell retrieval raises NotFoundError when not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        cell_id = uuid4()

        with pytest.raises(NotFoundError):
            await service.get_cell_by_id(cell_id, raise_if_not_found=True)

    @pytest.mark.asyncio
    async def test_get_cell_not_found_returns_none(self):
        """Test cell retrieval returns None when not found and flag is False."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        cell_id = uuid4()
        result = await service.get_cell_by_id(cell_id, raise_if_not_found=False)

        assert result is None


class TestCellUpdateValidation:
    """Tests for cell update validation logic."""

    @pytest.mark.asyncio
    async def test_update_cell_locked_raises(self):
        """Test that updating locked cell raises error."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()
        locked_cell = {
            "id": cell_id,
            "budget_version_id": uuid4(),
            "module_code": "enrollment",
            "entity_id": uuid4(),
            "field_name": "student_count",
            "period_code": "2025",
            "value_numeric": Decimal("100"),
            "value_text": None,
            "value_type": "numeric",
            "is_locked": True,
            "lock_reason": "Budget approved",
            "version": 1,
        }

        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping=locked_cell)
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        user_id = uuid4()
        data = CellUpdateRequest(
            value_numeric=Decimal("150"),
            version=1,
        )

        with pytest.raises(CellLockedError):
            await service.update_cell(cell_id, data, user_id)

    @pytest.mark.asyncio
    async def test_update_cell_version_conflict(self):
        """Test that version mismatch raises conflict error."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()
        cell_data = {
            "id": cell_id,
            "budget_version_id": uuid4(),
            "module_code": "enrollment",
            "entity_id": uuid4(),
            "field_name": "student_count",
            "period_code": "2025",
            "value_numeric": Decimal("100"),
            "value_text": None,
            "value_type": "numeric",
            "is_locked": False,
            "version": 5,  # Server has version 5
        }

        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping=cell_data)
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        user_id = uuid4()
        data = CellUpdateRequest(
            value_numeric=Decimal("150"),
            version=3,  # Client expects version 3
        )

        with pytest.raises(VersionConflictError):
            await service.update_cell(cell_id, data, user_id)


class TestSchemaValidation:
    """Tests for request/response schema validation."""

    def test_cell_create_request(self):
        """Test CellCreateRequest schema validation."""
        data = CellCreateRequest(
            budget_version_id=uuid4(),
            module_code="enrollment",
            entity_id=uuid4(),
            field_name="student_count",
            period_code="2025",
            value_numeric=Decimal("100"),
            value_type="numeric",
        )

        assert data.module_code == "enrollment"
        assert data.field_name == "student_count"
        assert data.value_numeric == Decimal("100")

    def test_cell_update_request(self):
        """Test CellUpdateRequest schema validation."""
        data = CellUpdateRequest(
            value_numeric=Decimal("150"),
            version=1,
        )

        assert data.value_numeric == Decimal("150")
        assert data.version == 1

    def test_cell_update_request_with_text(self):
        """Test CellUpdateRequest with text value."""
        data = CellUpdateRequest(
            value_text="Test note",
            version=2,
        )

        assert data.value_text == "Test note"
        assert data.version == 2

    def test_batch_update_request(self):
        """Test BatchUpdateRequest schema validation."""
        request = BatchUpdateRequest(
            updates=[
                CellUpdate(
                    cell_id=uuid4(),
                    value_numeric=Decimal("100"),
                    version=1,
                ),
                CellUpdate(
                    cell_id=uuid4(),
                    value_text="Test",
                    version=1,
                ),
            ]
        )

        assert len(request.updates) == 2

    def test_lock_request(self):
        """Test LockRequest schema validation."""
        data = LockRequest(lock_reason="Budget approved")
        assert data.lock_reason == "Budget approved"

    def test_unlock_request(self):
        """Test UnlockRequest schema validation."""
        data = UnlockRequest(unlock_reason="Budget reopened")
        assert data.unlock_reason == "Budget reopened"

    def test_unlock_request_optional_reason(self):
        """Test UnlockRequest with no reason."""
        data = UnlockRequest()
        assert data.unlock_reason is None

    def test_comment_request(self):
        """Test CommentRequest schema validation."""
        data = CommentRequest(comment_text="Review this value")
        assert data.comment_text == "Review this value"

    def test_undo_request(self):
        """Test UndoRequest schema validation."""
        session_id = uuid4()
        request = UndoRequest(session_id=session_id)
        assert request.session_id == session_id


class TestCacheInvalidation:
    """Tests for cache invalidation logic."""

    def test_module_to_cache_entity_mapping_coverage(self):
        """Test all modules have cache entity mappings."""
        efir_modules = [
            "enrollment",
            "class_structure",
            "dhg",
            "revenue",
            "personnel_costs",
            "operating_costs",
            "capex",
            "consolidation",
        ]

        for module in efir_modules:
            assert module in MODULE_TO_CACHE_ENTITY, f"Module {module} not mapped"
            assert MODULE_TO_CACHE_ENTITY[module], f"Module {module} has empty mapping"

    def test_cache_entity_values_not_empty(self):
        """Test cache entity values are meaningful strings."""
        for module, entity in MODULE_TO_CACHE_ENTITY.items():
            assert isinstance(entity, str)
            assert len(entity) > 0
            assert entity.islower() or "_" in entity


class TestOptimisticLocking:
    """Tests for optimistic locking behavior."""

    def test_version_field_required(self):
        """Test that version field is required in CellUpdateRequest."""
        with pytest.raises(Exception):
            CellUpdateRequest(value_numeric=Decimal("100"))

    def test_version_must_be_positive(self):
        """Test version must be a positive integer >= 1."""
        # Version 1 is the minimum
        data = CellUpdateRequest(value_numeric=Decimal("100"), version=1)
        assert data.version == 1

        # Higher versions work
        data = CellUpdateRequest(value_numeric=Decimal("100"), version=5)
        assert data.version == 5

    def test_version_zero_rejected(self):
        """Test version 0 is rejected."""
        with pytest.raises(Exception):
            CellUpdateRequest(value_numeric=Decimal("100"), version=0)
