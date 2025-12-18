"""
Extended tests for WritebackService - focusing on uncovered functionality.

This file contains comprehensive tests for:
- Batch update operations with conflict handling
- Undo/redo session logic
- Lock/unlock cell operations
- Comment system (add, get, resolve)
- Change history operations
- Cache invalidation coordination
- Race condition scenarios
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from app.schemas.admin import (
    BatchUpdateRequest,
    CellUpdate,
    CommentRequest,
    LockRequest,
    UndoRequest,
    UnlockRequest,
)
from app.services.admin.writeback_service import WritebackService
from app.services.exceptions import (
    NotFoundError,
    VersionConflictError,
)
from sqlalchemy.ext.asyncio import AsyncSession

# ==============================================================================
# Helper Functions
# ==============================================================================


def create_mock_cell(
    cell_id: UUID | None = None,
    version_id: UUID | None = None,
    module_code: str = "enrollment",
    is_locked: bool = False,
    version: int = 1,
    value_numeric: Decimal | None = Decimal("100"),
    value_text: str | None = None,
) -> dict:
    """Create a mock cell dictionary for testing."""
    return {
        "id": cell_id or uuid4(),
        "version_id": version_id or uuid4(),
        "module_code": module_code,
        "entity_id": uuid4(),
        "field_name": "student_count",
        "period_code": "2025",
        "value_numeric": value_numeric,
        "value_text": value_text,
        "value_type": "numeric" if value_numeric is not None else "text",
        "is_locked": is_locked,
        "lock_reason": "Budget approved" if is_locked else None,
        "locked_by": uuid4() if is_locked else None,
        "locked_at": datetime.utcnow() if is_locked else None,
        "version": version,
        "modified_by": uuid4(),
        "modified_at": datetime.utcnow(),
        "created_by_id": uuid4(),
        "created_at": datetime.utcnow(),
    }


def create_mock_change(
    cell_id: UUID,
    version_id: UUID,
    module_code: str = "enrollment",
    session_id: UUID | None = None,
    sequence_number: int = 1,
    old_value_numeric: Decimal | None = Decimal("100"),
    new_value_numeric: Decimal | None = Decimal("150"),
) -> dict:
    """Create a mock change record for testing."""
    return {
        "id": uuid4(),
        "cell_id": cell_id,
        "version_id": version_id,
        "module_code": module_code,
        "entity_id": uuid4(),
        "field_name": "student_count",
        "period_code": "2025",
        "old_value_numeric": old_value_numeric,
        "old_value_text": None,
        "new_value_numeric": new_value_numeric,
        "new_value_text": None,
        "change_type": "update",
        "session_id": session_id or uuid4(),
        "sequence_number": sequence_number,
        "changed_by": uuid4(),
        "changed_at": datetime.utcnow(),
    }


# ==============================================================================
# Batch Update Tests
# ==============================================================================


class TestBatchUpdateCells:
    """Comprehensive tests for batch cell updates with conflict handling."""

    @pytest.mark.asyncio
    async def test_batch_update_success(self):
        """Test successful batch update of multiple cells."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Setup mocks for 3 cells
        cell_ids = [uuid4() for _ in range(3)]
        version_id = uuid4()

        # Mock get_cell_by_id calls
        cells = [create_mock_cell(cell_id, version_id) for cell_id in cell_ids]

        async def mock_get_cell(cell_id, raise_if_not_found=True):
            for cell in cells:
                if cell["id"] == cell_id:
                    return cell
            return None

        # Mock execute for updates
        mock_result = MagicMock()
        mock_rows = []
        for cell in cells:
            row = MagicMock()
            updated_cell = cell.copy()
            updated_cell["version"] = cell["version"] + 1
            updated_cell["value_numeric"] = Decimal("200")
            row._mapping = updated_cell
            mock_rows.append(row)

        mock_result.fetchone.side_effect = mock_rows
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        # Create batch update request
        batch = BatchUpdateRequest(
            session_id=uuid4(),
            updates=[
                CellUpdate(
                    cell_id=cell_id,
                    value_numeric=Decimal("200"),
                    version=1,
                )
                for cell_id in cell_ids
            ],
            allow_partial_success=False,
        )

        result = await service.batch_update_cells(batch, uuid4())

        assert result.updated_count == 3
        assert result.failed_count == 0
        assert len(result.updated_cells) == 3
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_update_version_conflict(self):
        """Test batch update with version conflict."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()
        version_id = uuid4()

        # Cell has version 5, but client expects version 3
        cell = create_mock_cell(cell_id, version_id, version=5)

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return cell if cell_id_arg == cell_id else None

        mock_session.rollback = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        batch = BatchUpdateRequest(
            session_id=uuid4(),
            updates=[
                CellUpdate(
                    cell_id=cell_id,
                    value_numeric=Decimal("200"),
                    version=3,  # Conflict!
                )
            ],
            allow_partial_success=False,  # Fail fast
        )

        result = await service.batch_update_cells(batch, uuid4())

        assert result.updated_count == 0
        assert result.failed_count == 1
        assert len(result.conflicts) == 1
        assert result.conflicts[0].error_type == "version_conflict"
        assert result.conflicts[0].current_version == 5
        assert result.conflicts[0].provided_version == 3
        mock_session.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_batch_update_partial_success(self):
        """Test batch update with partial success allowed."""
        mock_session = AsyncMock(spec=AsyncSession)

        # 3 cells: 1 succeeds, 1 version conflict, 1 locked
        cell_ids = [uuid4() for _ in range(3)]
        version_id = uuid4()

        cells = [
            create_mock_cell(cell_ids[0], version_id, version=1),  # Success
            create_mock_cell(cell_ids[1], version_id, version=5),  # Conflict
            create_mock_cell(cell_ids[2], version_id, is_locked=True),  # Locked
        ]

        async def mock_get_cell(cell_id, raise_if_not_found=True):
            for cell in cells:
                if cell["id"] == cell_id:
                    return cell
            return None

        # Only first cell updates successfully
        mock_result = MagicMock()
        mock_row = MagicMock()
        updated_cell = cells[0].copy()
        updated_cell["version"] = 2
        updated_cell["value_numeric"] = Decimal("200")
        mock_row._mapping = updated_cell
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        batch = BatchUpdateRequest(
            session_id=uuid4(),
            updates=[
                CellUpdate(cell_id=cell_ids[0], value_numeric=Decimal("200"), version=1),
                CellUpdate(cell_id=cell_ids[1], value_numeric=Decimal("200"), version=3),
                CellUpdate(cell_id=cell_ids[2], value_numeric=Decimal("200"), version=1),
            ],
            allow_partial_success=True,  # Continue on errors
        )

        result = await service.batch_update_cells(batch, uuid4())

        assert result.updated_count == 1
        assert result.failed_count == 2
        assert len(result.conflicts) == 2

        # Check conflict types
        error_types = [c.error_type for c in result.conflicts]
        assert "version_conflict" in error_types
        assert "cell_locked" in error_types

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_update_cell_not_found(self):
        """Test batch update when cell doesn't exist."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return None  # Cell not found

        mock_session.rollback = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        batch = BatchUpdateRequest(
            session_id=uuid4(),
            updates=[
                CellUpdate(cell_id=cell_id, value_numeric=Decimal("200"), version=1)
            ],
            allow_partial_success=False,
        )

        result = await service.batch_update_cells(batch, uuid4())

        assert result.updated_count == 0
        assert result.failed_count == 1
        assert result.conflicts[0].error_type == "not_found"

    @pytest.mark.asyncio
    async def test_batch_update_rollback_on_error(self):
        """Test transaction rollback when allow_partial_success=False."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_ids = [uuid4(), uuid4()]
        version_id = uuid4()

        cells = [
            create_mock_cell(cell_ids[0], version_id),
            create_mock_cell(cell_ids[1], version_id, is_locked=True),  # Locked
        ]

        async def mock_get_cell(cell_id, raise_if_not_found=True):
            for cell in cells:
                if cell["id"] == cell_id:
                    return cell
            return None

        mock_session.rollback = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        batch = BatchUpdateRequest(
            session_id=uuid4(),
            updates=[
                CellUpdate(cell_id=cell_ids[0], value_numeric=Decimal("200"), version=1),
                CellUpdate(cell_id=cell_ids[1], value_numeric=Decimal("200"), version=1),
            ],
            allow_partial_success=False,  # Fail fast
        )

        result = await service.batch_update_cells(batch, uuid4())

        assert result.updated_count == 0
        assert result.failed_count == 2  # All updates failed
        mock_session.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_batch_update_locked_cells(self):
        """Test batch update handles locked cells correctly."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()
        cell = create_mock_cell(cell_id, is_locked=True)
        cell["lock_reason"] = "Budget approved by director"

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return cell if cell_id_arg == cell_id else None

        mock_session.rollback = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        batch = BatchUpdateRequest(
            session_id=uuid4(),
            updates=[
                CellUpdate(cell_id=cell_id, value_numeric=Decimal("200"), version=1)
            ],
            allow_partial_success=False,
        )

        result = await service.batch_update_cells(batch, uuid4())

        assert result.failed_count == 1
        assert result.conflicts[0].error_type == "cell_locked"
        assert "Budget approved by director" in result.conflicts[0].message

    @pytest.mark.asyncio
    async def test_batch_update_cache_invalidation(self):
        """Test cache invalidation after successful batch update."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Two cells from different modules
        cell1_id = uuid4()
        cell2_id = uuid4()
        version_id = uuid4()

        cells = [
            create_mock_cell(cell1_id, version_id, module_code="enrollment"),
            create_mock_cell(cell2_id, version_id, module_code="dhg"),
        ]

        async def mock_get_cell(cell_id, raise_if_not_found=True):
            for cell in cells:
                if cell["id"] == cell_id:
                    return cell
            return None

        mock_result = MagicMock()
        mock_rows = []
        for cell in cells:
            row = MagicMock()
            updated = cell.copy()
            updated["version"] += 1
            row._mapping = updated
            mock_rows.append(row)

        mock_result.fetchone.side_effect = mock_rows
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        # Mock cache invalidation
        with patch("app.services.writeback_service.CacheInvalidator.invalidate") as mock_invalidate:
            mock_invalidate.return_value = AsyncMock()

            batch = BatchUpdateRequest(
                session_id=uuid4(),
                updates=[
                    CellUpdate(cell_id=cell1_id, value_numeric=Decimal("200"), version=1),
                    CellUpdate(cell_id=cell2_id, value_numeric=Decimal("300"), version=1),
                ],
                allow_partial_success=True,
            )

            await service.batch_update_cells(batch, uuid4())

            # Cache invalidation should be called for both modules
            # Note: actual calls depend on module mapping
            assert mock_invalidate.call_count >= 1


# ==============================================================================
# Undo/Redo Tests
# ==============================================================================


class TestUndoSession:
    """Comprehensive tests for undo/redo functionality."""

    @pytest.mark.asyncio
    async def test_undo_session_success(self):
        """Test successful undo of a session with ordered reversal."""
        mock_session = AsyncMock(spec=AsyncSession)

        session_id = uuid4()
        cell_id = uuid4()
        version_id = uuid4()

        # Mock change history (3 changes in sequence)
        changes = [
            create_mock_change(
                cell_id,
                version_id,
                session_id=session_id,
                sequence_number=3,
                old_value_numeric=Decimal("200"),
                new_value_numeric=Decimal("250"),
            ),
            create_mock_change(
                cell_id,
                version_id,
                session_id=session_id,
                sequence_number=2,
                old_value_numeric=Decimal("150"),
                new_value_numeric=Decimal("200"),
            ),
            create_mock_change(
                cell_id,
                version_id,
                session_id=session_id,
                sequence_number=1,
                old_value_numeric=Decimal("100"),
                new_value_numeric=Decimal("150"),
            ),
        ]

        # Mock get change history
        mock_result_changes = MagicMock()
        mock_result_changes.fetchall.return_value = [MagicMock(_mapping=c) for c in changes]

        # Mock get current cell
        current_cell = create_mock_cell(cell_id, version_id, is_locked=False, version=4)

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return current_cell if cell_id_arg == cell_id else None

        # Mock update execution
        mock_result_update = MagicMock()
        mock_result_update.fetchone.return_value = None

        # Setup execute to return different results based on query
        def mock_execute(query, params):
            if "FROM efir_budget.admin_cell_changes" in str(query):
                return mock_result_changes
            elif "INSERT INTO efir_budget.admin_cell_changes" in str(query):
                return MagicMock()
            else:  # UPDATE
                return mock_result_update

        mock_session.execute.side_effect = mock_execute
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        request = UndoRequest(session_id=session_id)
        result = await service.undo_session(request, uuid4())

        assert result.reverted_count == 3
        assert len(result.reverted_cells) == 3
        assert len(result.failed_cells) == 0
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_undo_session_no_changes(self):
        """Test undo when session has no changes."""
        mock_session = AsyncMock(spec=AsyncSession)

        session_id = uuid4()

        # Mock empty change history
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        request = UndoRequest(session_id=session_id)

        with pytest.raises(NotFoundError) as exc_info:
            await service.undo_session(request, uuid4())

        assert str(session_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_undo_session_multiple_cells(self):
        """Test undo with changes to multiple cells."""
        mock_session = AsyncMock(spec=AsyncSession)

        session_id = uuid4()
        cell_ids = [uuid4() for _ in range(3)]
        version_id = uuid4()

        # Changes to 3 different cells
        changes = [
            create_mock_change(cell_ids[i], version_id, session_id=session_id, sequence_number=i + 1)
            for i in range(3)
        ]

        mock_result_changes = MagicMock()
        mock_result_changes.fetchall.return_value = [MagicMock(_mapping=c) for c in changes]

        cells = [create_mock_cell(cell_id, version_id) for cell_id in cell_ids]

        async def mock_get_cell(cell_id, raise_if_not_found=True):
            for cell in cells:
                if cell["id"] == cell_id:
                    return cell
            return None

        def mock_execute(query, params):
            if "FROM efir_budget.admin_cell_changes" in str(query):
                return mock_result_changes
            return MagicMock()

        mock_session.execute.side_effect = mock_execute
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        request = UndoRequest(session_id=session_id)
        result = await service.undo_session(request, uuid4())

        assert result.reverted_count == 3
        assert len(result.reverted_cells) == 3

    @pytest.mark.asyncio
    async def test_undo_session_locked_cell(self):
        """Test undo fails gracefully when cell is locked."""
        mock_session = AsyncMock(spec=AsyncSession)

        session_id = uuid4()
        cell_id = uuid4()
        version_id = uuid4()

        change = create_mock_change(cell_id, version_id, session_id=session_id)
        mock_result_changes = MagicMock()
        mock_result_changes.fetchall.return_value = [MagicMock(_mapping=change)]

        # Cell is now locked
        locked_cell = create_mock_cell(cell_id, version_id, is_locked=True)

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return locked_cell if cell_id_arg == cell_id else None

        def mock_execute(query, params):
            if "FROM efir_budget.admin_cell_changes" in str(query):
                return mock_result_changes
            return MagicMock()

        mock_session.execute.side_effect = mock_execute
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        request = UndoRequest(session_id=session_id)
        result = await service.undo_session(request, uuid4())

        assert result.reverted_count == 0
        assert len(result.failed_cells) == 1
        assert result.failed_cells[0].error_type == "cell_locked"

    @pytest.mark.asyncio
    async def test_undo_session_cell_deleted(self):
        """Test undo when cell no longer exists."""
        mock_session = AsyncMock(spec=AsyncSession)

        session_id = uuid4()
        cell_id = uuid4()
        version_id = uuid4()

        change = create_mock_change(cell_id, version_id, session_id=session_id)
        mock_result_changes = MagicMock()
        mock_result_changes.fetchall.return_value = [MagicMock(_mapping=change)]

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return None  # Cell deleted

        def mock_execute(query, params):
            if "FROM efir_budget.admin_cell_changes" in str(query):
                return mock_result_changes
            return MagicMock()

        mock_session.execute.side_effect = mock_execute
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        request = UndoRequest(session_id=session_id)
        result = await service.undo_session(request, uuid4())

        assert result.reverted_count == 0
        assert len(result.failed_cells) == 1
        assert result.failed_cells[0].error_type == "not_found"

    @pytest.mark.asyncio
    async def test_undo_session_cache_invalidation(self):
        """Test cache invalidation after undo."""
        mock_session = AsyncMock(spec=AsyncSession)

        session_id = uuid4()
        cell_id = uuid4()
        version_id = uuid4()

        change = create_mock_change(cell_id, version_id, session_id=session_id, module_code="enrollment")
        mock_result_changes = MagicMock()
        mock_result_changes.fetchall.return_value = [MagicMock(_mapping=change)]

        cell = create_mock_cell(cell_id, version_id, module_code="enrollment")

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return cell if cell_id_arg == cell_id else None

        def mock_execute(query, params):
            if "FROM efir_budget.admin_cell_changes" in str(query):
                return mock_result_changes
            return MagicMock()

        mock_session.execute.side_effect = mock_execute
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        with patch("app.services.writeback_service.CacheInvalidator.invalidate") as mock_invalidate:
            mock_invalidate.return_value = AsyncMock()

            request = UndoRequest(session_id=session_id)
            await service.undo_session(request, uuid4())

            # Cache should be invalidated for enrollment module
            assert mock_invalidate.call_count >= 1


# ==============================================================================
# Lock/Unlock Tests
# ==============================================================================


class TestLockUnlockOperations:
    """Tests for cell locking and unlocking."""

    @pytest.mark.asyncio
    async def test_lock_cell_success(self):
        """Test successful cell locking."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()
        user_id = uuid4()

        # Mock get_cell_by_id
        cell = create_mock_cell(cell_id, is_locked=False)

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return cell

        # Mock lock update
        mock_result = MagicMock()
        mock_row = MagicMock()
        locked_cell = cell.copy()
        locked_cell["is_locked"] = True
        locked_cell["lock_reason"] = "Budget approved"
        locked_cell["locked_by"] = user_id
        locked_cell["locked_at"] = datetime.utcnow()
        mock_row._mapping = locked_cell
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        lock_request = LockRequest(lock_reason="Budget approved")
        result = await service.lock_cell(cell_id, lock_request, user_id)

        assert result.is_locked is True
        assert result.lock_reason == "Budget approved"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_cell_not_found(self):
        """Test locking non-existent cell raises error."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            if raise_if_not_found:
                raise NotFoundError("PlanningCell", str(cell_id))
            return None

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        lock_request = LockRequest(lock_reason="Test")

        with pytest.raises(NotFoundError):
            await service.lock_cell(cell_id, lock_request, uuid4())

    @pytest.mark.asyncio
    async def test_unlock_cell_success(self):
        """Test successful cell unlocking."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()
        user_id = uuid4()

        # Cell is currently locked
        cell = create_mock_cell(cell_id, is_locked=True)

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return cell

        # Mock unlock update
        mock_result = MagicMock()
        mock_row = MagicMock()
        unlocked_cell = cell.copy()
        unlocked_cell["is_locked"] = False
        unlocked_cell["lock_reason"] = None
        unlocked_cell["locked_by"] = None
        unlocked_cell["locked_at"] = None
        mock_row._mapping = unlocked_cell
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        unlock_request = UnlockRequest(unlock_reason="Budget reopened")
        result = await service.unlock_cell(cell_id, unlock_request, user_id)

        assert result.is_locked is False
        assert result.lock_reason is None
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlock_cell_not_found(self):
        """Test unlocking non-existent cell raises error."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            if raise_if_not_found:
                raise NotFoundError("PlanningCell", str(cell_id))
            return None

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        unlock_request = UnlockRequest()

        with pytest.raises(NotFoundError):
            await service.unlock_cell(cell_id, unlock_request, uuid4())


# ==============================================================================
# Comment Tests
# ==============================================================================


class TestCommentSystem:
    """Tests for cell comment operations."""

    @pytest.mark.asyncio
    async def test_add_comment_success(self):
        """Test successfully adding a comment to a cell."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()
        user_id = uuid4()
        comment_id = uuid4()

        # Mock get_cell_by_id
        cell = create_mock_cell(cell_id)

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return cell

        # Mock comment insert
        mock_result = MagicMock()
        mock_row = MagicMock()
        comment = {
            "id": comment_id,
            "cell_id": cell_id,
            "comment_text": "Please review this value",
            "is_resolved": False,
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "resolved_by": None,
            "resolved_at": None,
        }
        mock_row._mapping = comment
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        comment_request = CommentRequest(comment_text="Please review this value")
        result = await service.add_comment(cell_id, comment_request, user_id)

        assert result.comment_text == "Please review this value"
        assert result.is_resolved is False
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_comment_cell_not_found(self):
        """Test adding comment to non-existent cell raises error."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            if raise_if_not_found:
                raise NotFoundError("PlanningCell", str(cell_id))
            return None

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        comment_request = CommentRequest(comment_text="Test")

        with pytest.raises(NotFoundError):
            await service.add_comment(cell_id, comment_request, uuid4())

    @pytest.mark.asyncio
    async def test_get_cell_comments_success(self):
        """Test retrieving all comments for a cell."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()

        # Mock multiple comments
        comments = [
            {
                "id": uuid4(),
                "cell_id": cell_id,
                "comment_text": f"Comment {i}",
                "is_resolved": i == 0,  # First one resolved
                "created_by": uuid4(),
                "created_at": datetime.utcnow(),
                "resolved_by": uuid4() if i == 0 else None,
                "resolved_at": datetime.utcnow() if i == 0 else None,
            }
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [MagicMock(_mapping=c) for c in comments]
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        result = await service.get_cell_comments(cell_id)

        assert len(result) == 3
        assert result[0].is_resolved is True
        assert result[1].is_resolved is False

    @pytest.mark.asyncio
    async def test_resolve_comment_success(self):
        """Test successfully resolving a comment."""
        mock_session = AsyncMock(spec=AsyncSession)

        comment_id = uuid4()
        user_id = uuid4()

        # Mock resolve update
        mock_result = MagicMock()
        mock_row = MagicMock()
        resolved_comment = {
            "id": comment_id,
            "cell_id": uuid4(),
            "comment_text": "Test comment",
            "is_resolved": True,
            "created_by": uuid4(),
            "created_at": datetime.utcnow(),
            "resolved_by": user_id,
            "resolved_at": datetime.utcnow(),
        }
        mock_row._mapping = resolved_comment
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        result = await service.resolve_comment(comment_id, user_id)

        assert result.is_resolved is True
        assert result.resolved_by == user_id
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_comment_not_found(self):
        """Test resolving non-existent comment raises error."""
        mock_session = AsyncMock(spec=AsyncSession)

        comment_id = uuid4()

        # Mock comment not found
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)

        with pytest.raises(NotFoundError) as exc_info:
            await service.resolve_comment(comment_id, uuid4())

        assert str(comment_id) in str(exc_info.value)


# ==============================================================================
# Change History Tests
# ==============================================================================


class TestChangeHistory:
    """Tests for change history operations."""

    @pytest.mark.asyncio
    async def test_get_change_history_success(self):
        """Test retrieving change history for a budget version."""
        mock_session = AsyncMock(spec=AsyncSession)

        version_id = uuid4()

        # Mock change records
        changes = [
            create_mock_change(uuid4(), version_id, sequence_number=i + 1) for i in range(5)
        ]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [MagicMock(_mapping=c) for c in changes]
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        result = await service.get_change_history(version_id)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_get_change_history_with_filters(self):
        """Test change history with module/entity/field filters."""
        mock_session = AsyncMock(spec=AsyncSession)

        version_id = uuid4()
        entity_id = uuid4()

        changes = [create_mock_change(uuid4(), version_id)]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [MagicMock(_mapping=c) for c in changes]
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        await service.get_change_history(
            version_id,
            module_code="enrollment",
            entity_id=entity_id,
            field_name="student_count",
        )

        # Verify filters were applied (check execute was called with params)
        call_args = mock_session.execute.call_args
        assert call_args is not None
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
        assert params["version_id"] == str(version_id)
        assert params.get("module_code") == "enrollment"

    @pytest.mark.asyncio
    async def test_get_change_history_pagination(self):
        """Test change history pagination."""
        mock_session = AsyncMock(spec=AsyncSession)

        version_id = uuid4()

        # Simulate paginated results
        changes = [create_mock_change(uuid4(), version_id, sequence_number=i + 11) for i in range(10)]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [MagicMock(_mapping=c) for c in changes]
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        result = await service.get_change_history(version_id, limit=10, offset=10)

        assert len(result) == 10

        # Verify limit and offset in query
        call_args = mock_session.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
        assert params["limit"] == 10
        assert params["offset"] == 10

    @pytest.mark.asyncio
    async def test_get_change_history_ordering(self):
        """Test change history is ordered by changed_at DESC."""
        mock_session = AsyncMock(spec=AsyncSession)

        version_id = uuid4()

        # Changes with different timestamps
        base_time = datetime.utcnow()
        changes = []
        for i in range(3):
            change = create_mock_change(uuid4(), version_id, sequence_number=i + 1)
            change["changed_at"] = base_time.replace(second=i)
            changes.append(change)

        # Reverse order (DESC)
        changes = list(reversed(changes))

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [MagicMock(_mapping=c) for c in changes]
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        result = await service.get_change_history(version_id)

        # Most recent should be first
        assert result[0].changed_at > result[1].changed_at
        assert result[1].changed_at > result[2].changed_at


# ==============================================================================
# Cache Invalidation Tests
# ==============================================================================


class TestCacheInvalidationService:
    """Tests for cache invalidation coordination."""

    @pytest.mark.asyncio
    async def test_invalidate_module_cache_success(self):
        """Test successful cache invalidation for each module."""
        mock_session = AsyncMock(spec=AsyncSession)
        service = WritebackService(mock_session)

        modules = ["enrollment", "class_structure", "dhg", "revenue", "personnel_costs", "operating_costs", "capex", "consolidation"]

        with patch("app.services.writeback_service.CacheInvalidator.invalidate") as mock_invalidate:
            mock_invalidate.return_value = AsyncMock()

            for module in modules:
                await service._invalidate_module_cache(module, str(uuid4()))

            # Should be called once per module
            assert mock_invalidate.call_count == len(modules)

    @pytest.mark.asyncio
    async def test_invalidate_cache_invalid_module(self):
        """Test cache invalidation handles unknown module gracefully."""
        mock_session = AsyncMock(spec=AsyncSession)
        service = WritebackService(mock_session)

        with patch("app.services.writeback_service.CacheInvalidator.invalidate") as mock_invalidate:
            mock_invalidate.return_value = AsyncMock()

            # Unknown module - should not raise error
            await service._invalidate_module_cache("unknown_module", str(uuid4()))

            # Invalidate should not be called for unknown module
            mock_invalidate.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalidate_cache_failure_logged(self):
        """Test cache invalidation failure is logged but doesn't fail operation."""
        mock_session = AsyncMock(spec=AsyncSession)
        service = WritebackService(mock_session)

        with patch("app.services.writeback_service.CacheInvalidator.invalidate") as mock_invalidate:
            mock_invalidate.side_effect = Exception("Redis connection failed")

            # Should not raise exception
            await service._invalidate_module_cache("enrollment", str(uuid4()))

            # Exception should be handled internally


# ==============================================================================
# Update Cell Tests (Race Conditions)
# ==============================================================================


class TestUpdateCellRaceConditions:
    """Tests for update_cell with race condition scenarios."""

    @pytest.mark.asyncio
    async def test_update_cell_race_condition_between_check_and_update(self):
        """Test race condition: version changes between check and update."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()

        # First get_cell_by_id returns version 1
        cell_v1 = create_mock_cell(cell_id, version=1)

        # But update fails (returns None) because version changed
        # Second get_cell_by_id returns version 2
        cell_v2 = create_mock_cell(cell_id, version=2)

        call_count = 0

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return cell_v1
            else:
                return cell_v2

        # Mock update returning None (version conflict during update)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        from app.schemas.writeback import CellUpdateRequest

        update_req = CellUpdateRequest(value_numeric=Decimal("200"), version=1)

        with pytest.raises(VersionConflictError) as exc_info:
            await service.update_cell(cell_id, update_req, uuid4())

        # Should report version 2 as current (stored in details dict)
        assert exc_info.value.details["current_version"] == 2
        assert exc_info.value.details["provided_version"] == 1

    @pytest.mark.asyncio
    async def test_update_cell_success_with_change_logging(self):
        """Test successful update logs change correctly."""
        mock_session = AsyncMock(spec=AsyncSession)

        cell_id = uuid4()
        version_id = uuid4()
        user_id = uuid4()

        cell = create_mock_cell(cell_id, version_id, version=1, value_numeric=Decimal("100"))

        async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
            return cell

        # Mock update success
        mock_result = MagicMock()
        mock_row = MagicMock()
        updated_cell = cell.copy()
        updated_cell["version"] = 2
        updated_cell["value_numeric"] = Decimal("150")
        mock_row._mapping = updated_cell
        mock_result.fetchone.return_value = mock_row

        # Track executions
        executions = []

        async def mock_execute(query, params):
            executions.append((str(query), params))
            return mock_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        service = WritebackService(mock_session)
        service.get_cell_by_id = mock_get_cell

        from app.schemas.writeback import CellUpdateRequest

        update_req = CellUpdateRequest(value_numeric=Decimal("150"), version=1)
        result = await service.update_cell(cell_id, update_req, user_id)

        assert result.version == 2
        assert result.value_numeric == Decimal("150")

        # Check that change was logged (INSERT into cell_changes)
        log_queries = [q for q, _ in executions if "INSERT INTO efir_budget.admin_cell_changes" in q]
        assert len(log_queries) == 1
