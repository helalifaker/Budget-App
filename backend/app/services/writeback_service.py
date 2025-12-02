"""
Writeback service for cell-level data operations.

Provides business logic for:
- Single cell updates with optimistic locking
- Batch cell updates for spreadsheet operations
- Change history and audit trail
- Undo/redo operations
- Cell comments and annotations
- Cell locking for approved budgets
- Cache invalidation coordination

This service is the core of real-time collaborative editing,
ensuring data integrity through optimistic locking and
comprehensive change tracking.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheInvalidator
from app.core.logging import logger
from app.schemas.writeback import (
    BatchUpdateRequest,
    BatchUpdateResponse,
    CellChangeResponse,
    CellCreateRequest,
    CellLockResponse,
    CellResponse,
    CellUpdateRequest,
    CellUpdateResponse,
    CommentRequest,
    CommentResponse,
    ConflictDetail,
    LockRequest,
    UndoRequest,
    UndoResponse,
    UnlockRequest,
)
from app.services.exceptions import (
    CellLockedError,
    NotFoundError,
    VersionConflictError,
)

# ==============================================================================
# Module Code to Entity Mapping for Cache Invalidation
# ==============================================================================

MODULE_TO_CACHE_ENTITY: dict[str, str] = {
    "enrollment": "enrollment",
    "class_structure": "class_structure",
    "dhg": "dhg_calculations",
    "revenue": "revenue",
    "personnel_costs": "personnel_costs",
    "operating_costs": "operational_costs",
    "capex": "capex",
    "consolidation": "budget_consolidation",
}


class WritebackService:
    """
    Service for cell-level writeback operations.

    Implements optimistic locking for concurrent editing,
    comprehensive change tracking for undo/redo, and
    coordinates cache invalidation across modules.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize writeback service.

        Args:
            session: Async database session
        """
        self.session = session

    # ==========================================================================
    # Cell CRUD Operations
    # ==========================================================================

    async def get_cell_by_id(
        self,
        cell_id: UUID,
        raise_if_not_found: bool = True,
    ) -> dict[str, Any] | None:
        """
        Get a planning cell by ID.

        Args:
            cell_id: Cell UUID
            raise_if_not_found: Whether to raise NotFoundError if not found

        Returns:
            Cell data dictionary or None

        Raises:
            NotFoundError: If cell not found and raise_if_not_found=True
        """
        query = """
            SELECT
                id, budget_version_id, module_code, entity_id, field_name,
                period_code, value_numeric, value_text, value_type,
                is_locked, lock_reason, locked_by, locked_at,
                version, modified_by, modified_at, created_by_id, created_at,
                (SELECT COUNT(*) FROM efir_budget.cell_comments cc WHERE cc.cell_id = pc.id) as comment_count,
                (SELECT COUNT(*) FROM efir_budget.cell_comments cc WHERE cc.cell_id = pc.id AND NOT cc.is_resolved) as unresolved_comment_count
            FROM efir_budget.planning_cells pc
            WHERE id = :cell_id AND deleted_at IS NULL
        """
        from sqlalchemy import text

        result = await self.session.execute(text(query), {"cell_id": str(cell_id)})
        row = result.fetchone()

        if row is None:
            if raise_if_not_found:
                raise NotFoundError("PlanningCell", str(cell_id))
            return None

        return dict(row._mapping)

    async def create_cell(
        self,
        data: CellCreateRequest,
        user_id: UUID,
    ) -> CellResponse:
        """
        Create a new planning cell.

        Args:
            data: Cell creation data
            user_id: User creating the cell

        Returns:
            Created cell response
        """
        from sqlalchemy import text

        cell_id = uuid4()
        now = datetime.utcnow()

        query = """
            INSERT INTO efir_budget.planning_cells (
                id, budget_version_id, module_code, entity_id, field_name,
                period_code, value_numeric, value_text, value_type,
                version, created_by_id, created_at, modified_by, modified_at
            ) VALUES (
                :id, :budget_version_id, :module_code, :entity_id, :field_name,
                :period_code, :value_numeric, :value_text, :value_type,
                1, :user_id, :now, :user_id, :now
            )
            RETURNING id, budget_version_id, module_code, entity_id, field_name,
                      period_code, value_numeric, value_text, value_type,
                      is_locked, lock_reason, locked_by, locked_at,
                      version, modified_by, modified_at, created_by_id, created_at
        """

        result = await self.session.execute(
            text(query),
            {
                "id": str(cell_id),
                "budget_version_id": str(data.budget_version_id),
                "module_code": data.module_code,
                "entity_id": str(data.entity_id),
                "field_name": data.field_name,
                "period_code": data.period_code,
                "value_numeric": float(data.value_numeric) if data.value_numeric is not None else None,
                "value_text": data.value_text,
                "value_type": data.value_type,
                "user_id": str(user_id),
                "now": now,
            },
        )
        row = result.fetchone()
        await self.session.commit()

        # Invalidate caches
        await self._invalidate_module_cache(data.module_code, str(data.budget_version_id))

        cell_data = dict(row._mapping)
        cell_data["comment_count"] = 0
        cell_data["unresolved_comment_count"] = 0

        return CellResponse(**cell_data)

    async def update_cell(
        self,
        cell_id: UUID,
        update: CellUpdateRequest,
        user_id: UUID,
    ) -> CellUpdateResponse:
        """
        Update a single planning cell with optimistic locking.

        Args:
            cell_id: Cell to update
            update: Update data with version for locking
            user_id: User making the update

        Returns:
            Updated cell response

        Raises:
            NotFoundError: Cell not found
            VersionConflictError: Version mismatch (concurrent modification)
            CellLockedError: Cell is locked
        """
        from sqlalchemy import text

        # Get current cell state
        cell = await self.get_cell_by_id(cell_id)

        # Check if cell is locked
        if cell["is_locked"]:
            raise CellLockedError(
                cell_id=str(cell_id),
                lock_reason=cell.get("lock_reason"),
            )

        # Check version for optimistic locking
        if cell["version"] != update.version:
            raise VersionConflictError(
                resource="PlanningCell",
                current_version=cell["version"],
                provided_version=update.version,
            )

        # Prepare update values
        now = datetime.utcnow()
        new_version = cell["version"] + 1

        # Log change to cell_changes table
        await self._log_cell_change(
            cell_id=cell_id,
            budget_version_id=cell["budget_version_id"],
            module_code=cell["module_code"],
            entity_id=cell["entity_id"],
            field_name=cell["field_name"],
            period_code=cell.get("period_code"),
            old_value_numeric=cell.get("value_numeric"),
            old_value_text=cell.get("value_text"),
            new_value_numeric=update.value_numeric,
            new_value_text=update.value_text,
            change_type="update",
            session_id=uuid4(),
            sequence_number=1,
            user_id=user_id,
        )

        # Perform update
        query = """
            UPDATE efir_budget.planning_cells
            SET
                value_numeric = :value_numeric,
                value_text = :value_text,
                version = :new_version,
                modified_by = :user_id,
                modified_at = :now,
                updated_at = :now
            WHERE id = :cell_id AND version = :expected_version AND deleted_at IS NULL
            RETURNING id, budget_version_id, module_code, entity_id, field_name,
                      period_code, value_numeric, value_text, value_type,
                      version, modified_by, modified_at, is_locked
        """

        result = await self.session.execute(
            text(query),
            {
                "cell_id": str(cell_id),
                "value_numeric": float(update.value_numeric) if update.value_numeric is not None else None,
                "value_text": update.value_text,
                "new_version": new_version,
                "user_id": str(user_id),
                "now": now,
                "expected_version": update.version,
            },
        )
        row = result.fetchone()

        if row is None:
            # Version changed between check and update - race condition
            cell = await self.get_cell_by_id(cell_id)
            raise VersionConflictError(
                resource="PlanningCell",
                current_version=cell["version"],
                provided_version=update.version,
            )

        await self.session.commit()

        # Invalidate caches
        await self._invalidate_module_cache(cell["module_code"], str(cell["budget_version_id"]))

        logger.info(
            "cell_updated",
            cell_id=str(cell_id),
            old_version=update.version,
            new_version=new_version,
            user_id=str(user_id),
        )

        return CellUpdateResponse(**dict(row._mapping))

    async def batch_update_cells(
        self,
        batch: BatchUpdateRequest,
        user_id: UUID,
    ) -> BatchUpdateResponse:
        """
        Update multiple cells in a single transaction.

        Args:
            batch: Batch update request with multiple cell updates
            user_id: User making the updates

        Returns:
            Batch update response with success/failure details
        """
        updated_cells: list[CellUpdateResponse] = []
        conflicts: list[ConflictDetail] = []
        affected_modules: set[tuple[str, str]] = set()  # (module_code, budget_version_id)

        for idx, cell_update in enumerate(batch.updates):
            try:
                # Get current cell state
                cell = await self.get_cell_by_id(cell_update.cell_id, raise_if_not_found=False)

                if cell is None:
                    conflicts.append(
                        ConflictDetail(
                            cell_id=cell_update.cell_id,
                            error_type="not_found",
                            message=f"Cell {cell_update.cell_id} not found",
                            current_version=None,
                            provided_version=cell_update.version,
                        )
                    )
                    if not batch.allow_partial_success:
                        await self.session.rollback()
                        return BatchUpdateResponse(
                            session_id=batch.session_id,
                            updated_count=0,
                            failed_count=len(batch.updates),
                            updated_cells=[],
                            conflicts=conflicts,
                        )
                    continue

                # Check if cell is locked
                if cell["is_locked"]:
                    conflicts.append(
                        ConflictDetail(
                            cell_id=cell_update.cell_id,
                            error_type="cell_locked",
                            message=cell.get("lock_reason") or "Cell is locked",
                            current_version=cell["version"],
                            provided_version=cell_update.version,
                        )
                    )
                    if not batch.allow_partial_success:
                        await self.session.rollback()
                        return BatchUpdateResponse(
                            session_id=batch.session_id,
                            updated_count=0,
                            failed_count=len(batch.updates),
                            updated_cells=[],
                            conflicts=conflicts,
                        )
                    continue

                # Check version
                if cell["version"] != cell_update.version:
                    conflicts.append(
                        ConflictDetail(
                            cell_id=cell_update.cell_id,
                            error_type="version_conflict",
                            message="Cell was modified by another user",
                            current_version=cell["version"],
                            provided_version=cell_update.version,
                        )
                    )
                    if not batch.allow_partial_success:
                        await self.session.rollback()
                        return BatchUpdateResponse(
                            session_id=batch.session_id,
                            updated_count=0,
                            failed_count=len(batch.updates),
                            updated_cells=[],
                            conflicts=conflicts,
                        )
                    continue

                # Log change
                await self._log_cell_change(
                    cell_id=cell_update.cell_id,
                    budget_version_id=cell["budget_version_id"],
                    module_code=cell["module_code"],
                    entity_id=cell["entity_id"],
                    field_name=cell["field_name"],
                    period_code=cell.get("period_code"),
                    old_value_numeric=cell.get("value_numeric"),
                    old_value_text=cell.get("value_text"),
                    new_value_numeric=cell_update.value_numeric,
                    new_value_text=cell_update.value_text,
                    change_type="bulk_update",
                    session_id=batch.session_id,
                    sequence_number=idx + 1,
                    user_id=user_id,
                )

                # Perform update
                from sqlalchemy import text

                now = datetime.utcnow()
                new_version = cell["version"] + 1

                query = """
                    UPDATE efir_budget.planning_cells
                    SET
                        value_numeric = :value_numeric,
                        value_text = :value_text,
                        version = :new_version,
                        modified_by = :user_id,
                        modified_at = :now,
                        updated_at = :now
                    WHERE id = :cell_id AND version = :expected_version AND deleted_at IS NULL
                    RETURNING id, budget_version_id, module_code, entity_id, field_name,
                              period_code, value_numeric, value_text, value_type,
                              version, modified_by, modified_at, is_locked
                """

                result = await self.session.execute(
                    text(query),
                    {
                        "cell_id": str(cell_update.cell_id),
                        "value_numeric": float(cell_update.value_numeric)
                        if cell_update.value_numeric is not None
                        else None,
                        "value_text": cell_update.value_text,
                        "new_version": new_version,
                        "user_id": str(user_id),
                        "now": now,
                        "expected_version": cell_update.version,
                    },
                )
                row = result.fetchone()

                if row is not None:
                    updated_cells.append(CellUpdateResponse(**dict(row._mapping)))
                    affected_modules.add((cell["module_code"], str(cell["budget_version_id"])))

            except Exception as e:
                conflicts.append(
                    ConflictDetail(
                        cell_id=cell_update.cell_id,
                        error_type="validation_error",
                        message=str(e),
                        current_version=None,
                        provided_version=cell_update.version,
                    )
                )
                if not batch.allow_partial_success:
                    await self.session.rollback()
                    return BatchUpdateResponse(
                        session_id=batch.session_id,
                        updated_count=0,
                        failed_count=len(batch.updates),
                        updated_cells=[],
                        conflicts=conflicts,
                    )

        await self.session.commit()

        # Invalidate caches for all affected modules
        for module_code, budget_version_id in affected_modules:
            await self._invalidate_module_cache(module_code, budget_version_id)

        logger.info(
            "batch_update_completed",
            session_id=str(batch.session_id),
            updated_count=len(updated_cells),
            failed_count=len(conflicts),
            user_id=str(user_id),
        )

        return BatchUpdateResponse(
            session_id=batch.session_id,
            updated_count=len(updated_cells),
            failed_count=len(conflicts),
            updated_cells=updated_cells,
            conflicts=conflicts,
        )

    # ==========================================================================
    # Change History Operations
    # ==========================================================================

    async def get_change_history(
        self,
        budget_version_id: UUID,
        module_code: str | None = None,
        entity_id: UUID | None = None,
        field_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CellChangeResponse]:
        """
        Get change history for cells.

        Args:
            budget_version_id: Budget version to query
            module_code: Optional filter by module
            entity_id: Optional filter by entity
            field_name: Optional filter by field
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            List of change history records
        """
        from sqlalchemy import text

        query = """
            SELECT
                id, cell_id, budget_version_id, module_code, entity_id, field_name,
                period_code, old_value_numeric, old_value_text, new_value_numeric, new_value_text,
                change_type, session_id, sequence_number, changed_by, changed_at
            FROM efir_budget.cell_changes
            WHERE budget_version_id = :budget_version_id
        """
        params: dict[str, Any] = {"budget_version_id": str(budget_version_id)}

        if module_code:
            query += " AND module_code = :module_code"
            params["module_code"] = module_code

        if entity_id:
            query += " AND entity_id = :entity_id"
            params["entity_id"] = str(entity_id)

        if field_name:
            query += " AND field_name = :field_name"
            params["field_name"] = field_name

        query += " ORDER BY changed_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = await self.session.execute(text(query), params)
        rows = result.fetchall()

        return [CellChangeResponse(**dict(row._mapping)) for row in rows]

    async def undo_session(
        self,
        request: UndoRequest,
        user_id: UUID,
    ) -> UndoResponse:
        """
        Undo all changes in a session.

        Args:
            request: Undo request with session_id
            user_id: User performing the undo

        Returns:
            Undo response with reverted cells
        """
        from sqlalchemy import text

        # Get all changes in the session (ordered by sequence for proper undo)
        query = """
            SELECT
                id, cell_id, budget_version_id, module_code, entity_id, field_name,
                period_code, old_value_numeric, old_value_text, new_value_numeric, new_value_text,
                change_type, session_id, sequence_number, changed_by, changed_at
            FROM efir_budget.cell_changes
            WHERE session_id = :session_id
            ORDER BY sequence_number DESC
        """
        result = await self.session.execute(text(query), {"session_id": str(request.session_id)})
        changes = result.fetchall()

        if not changes:
            raise NotFoundError("ChangeSession", str(request.session_id))

        new_session_id = uuid4()
        reverted_cells: list[UUID] = []
        failed_cells: list[ConflictDetail] = []
        affected_modules: set[tuple[str, str]] = set()

        for idx, change in enumerate(changes):
            change_dict = dict(change._mapping)
            cell_id = change_dict["cell_id"]

            try:
                # Get current cell state
                cell = await self.get_cell_by_id(UUID(str(cell_id)), raise_if_not_found=False)

                if cell is None:
                    failed_cells.append(
                        ConflictDetail(
                            cell_id=UUID(str(cell_id)),
                            error_type="not_found",
                            message="Cell no longer exists",
                            current_version=None,
                            provided_version=None,
                        )
                    )
                    continue

                if cell["is_locked"]:
                    failed_cells.append(
                        ConflictDetail(
                            cell_id=UUID(str(cell_id)),
                            error_type="cell_locked",
                            message=cell.get("lock_reason") or "Cell is locked",
                            current_version=cell["version"],
                            provided_version=None,
                        )
                    )
                    continue

                # Log the undo change
                await self._log_cell_change(
                    cell_id=UUID(str(cell_id)),
                    budget_version_id=change_dict["budget_version_id"],
                    module_code=change_dict["module_code"],
                    entity_id=change_dict["entity_id"],
                    field_name=change_dict["field_name"],
                    period_code=change_dict.get("period_code"),
                    old_value_numeric=change_dict.get("new_value_numeric"),
                    old_value_text=change_dict.get("new_value_text"),
                    new_value_numeric=change_dict.get("old_value_numeric"),
                    new_value_text=change_dict.get("old_value_text"),
                    change_type="undo",
                    session_id=new_session_id,
                    sequence_number=idx + 1,
                    user_id=user_id,
                )

                # Revert the cell to old values
                now = datetime.utcnow()
                update_query = """
                    UPDATE efir_budget.planning_cells
                    SET
                        value_numeric = :old_value_numeric,
                        value_text = :old_value_text,
                        version = version + 1,
                        modified_by = :user_id,
                        modified_at = :now,
                        updated_at = :now
                    WHERE id = :cell_id AND deleted_at IS NULL
                """

                await self.session.execute(
                    text(update_query),
                    {
                        "cell_id": str(cell_id),
                        "old_value_numeric": change_dict.get("old_value_numeric"),
                        "old_value_text": change_dict.get("old_value_text"),
                        "user_id": str(user_id),
                        "now": now,
                    },
                )

                reverted_cells.append(UUID(str(cell_id)))
                affected_modules.add((change_dict["module_code"], str(change_dict["budget_version_id"])))

            except Exception as e:
                failed_cells.append(
                    ConflictDetail(
                        cell_id=UUID(str(cell_id)),
                        error_type="validation_error",
                        message=str(e),
                        current_version=None,
                        provided_version=None,
                    )
                )

        await self.session.commit()

        # Invalidate caches
        for module_code, budget_version_id in affected_modules:
            await self._invalidate_module_cache(module_code, budget_version_id)

        logger.info(
            "session_undone",
            original_session_id=str(request.session_id),
            new_session_id=str(new_session_id),
            reverted_count=len(reverted_cells),
            failed_count=len(failed_cells),
            user_id=str(user_id),
        )

        return UndoResponse(
            reverted_count=len(reverted_cells),
            new_session_id=new_session_id,
            reverted_cells=reverted_cells,
            failed_cells=failed_cells,
        )

    # ==========================================================================
    # Comment Operations
    # ==========================================================================

    async def add_comment(
        self,
        cell_id: UUID,
        comment: CommentRequest,
        user_id: UUID,
    ) -> CommentResponse:
        """
        Add a comment to a cell.

        Args:
            cell_id: Cell to comment on
            comment: Comment data
            user_id: User adding the comment

        Returns:
            Created comment response
        """
        from sqlalchemy import text

        # Verify cell exists
        await self.get_cell_by_id(cell_id)

        comment_id = uuid4()
        now = datetime.utcnow()

        query = """
            INSERT INTO efir_budget.cell_comments (
                id, cell_id, comment_text, is_resolved, created_by, created_at
            ) VALUES (
                :id, :cell_id, :comment_text, FALSE, :user_id, :now
            )
            RETURNING id, cell_id, comment_text, is_resolved, created_by, created_at,
                      resolved_by, resolved_at
        """

        result = await self.session.execute(
            text(query),
            {
                "id": str(comment_id),
                "cell_id": str(cell_id),
                "comment_text": comment.comment_text,
                "user_id": str(user_id),
                "now": now,
            },
        )
        row = result.fetchone()
        await self.session.commit()

        logger.info(
            "comment_added",
            cell_id=str(cell_id),
            comment_id=str(comment_id),
            user_id=str(user_id),
        )

        return CommentResponse(**dict(row._mapping))

    async def get_cell_comments(
        self,
        cell_id: UUID,
    ) -> list[CommentResponse]:
        """
        Get all comments for a cell.

        Args:
            cell_id: Cell to get comments for

        Returns:
            List of comments
        """
        from sqlalchemy import text

        query = """
            SELECT id, cell_id, comment_text, is_resolved, created_by, created_at,
                   resolved_by, resolved_at
            FROM efir_budget.cell_comments
            WHERE cell_id = :cell_id
            ORDER BY created_at DESC
        """

        result = await self.session.execute(text(query), {"cell_id": str(cell_id)})
        rows = result.fetchall()

        return [CommentResponse(**dict(row._mapping)) for row in rows]

    async def resolve_comment(
        self,
        comment_id: UUID,
        user_id: UUID,
    ) -> CommentResponse:
        """
        Mark a comment as resolved.

        Args:
            comment_id: Comment to resolve
            user_id: User resolving the comment

        Returns:
            Updated comment response
        """
        from sqlalchemy import text

        now = datetime.utcnow()

        query = """
            UPDATE efir_budget.cell_comments
            SET is_resolved = TRUE, resolved_by = :user_id, resolved_at = :now
            WHERE id = :comment_id
            RETURNING id, cell_id, comment_text, is_resolved, created_by, created_at,
                      resolved_by, resolved_at
        """

        result = await self.session.execute(
            text(query),
            {
                "comment_id": str(comment_id),
                "user_id": str(user_id),
                "now": now,
            },
        )
        row = result.fetchone()

        if row is None:
            raise NotFoundError("CellComment", str(comment_id))

        await self.session.commit()

        logger.info(
            "comment_resolved",
            comment_id=str(comment_id),
            user_id=str(user_id),
        )

        return CommentResponse(**dict(row._mapping))

    # ==========================================================================
    # Lock Operations
    # ==========================================================================

    async def lock_cell(
        self,
        cell_id: UUID,
        lock: LockRequest,
        user_id: UUID,
    ) -> CellLockResponse:
        """
        Lock a cell to prevent edits.

        Args:
            cell_id: Cell to lock
            lock: Lock request with reason
            user_id: User locking the cell

        Returns:
            Lock response
        """
        from sqlalchemy import text

        # Verify cell exists
        await self.get_cell_by_id(cell_id)

        now = datetime.utcnow()

        query = """
            UPDATE efir_budget.planning_cells
            SET is_locked = TRUE, lock_reason = :lock_reason, locked_by = :user_id, locked_at = :now
            WHERE id = :cell_id AND deleted_at IS NULL
            RETURNING id, is_locked, lock_reason, locked_by, locked_at
        """

        result = await self.session.execute(
            text(query),
            {
                "cell_id": str(cell_id),
                "lock_reason": lock.lock_reason,
                "user_id": str(user_id),
                "now": now,
            },
        )
        row = result.fetchone()
        await self.session.commit()

        logger.info(
            "cell_locked",
            cell_id=str(cell_id),
            lock_reason=lock.lock_reason,
            user_id=str(user_id),
        )

        return CellLockResponse(**dict(row._mapping))

    async def unlock_cell(
        self,
        cell_id: UUID,
        unlock: UnlockRequest,
        user_id: UUID,
    ) -> CellLockResponse:
        """
        Unlock a cell to allow edits.

        Args:
            cell_id: Cell to unlock
            unlock: Unlock request with optional reason
            user_id: User unlocking the cell

        Returns:
            Lock response
        """
        from sqlalchemy import text

        # Verify cell exists
        await self.get_cell_by_id(cell_id)

        query = """
            UPDATE efir_budget.planning_cells
            SET is_locked = FALSE, lock_reason = NULL, locked_by = NULL, locked_at = NULL
            WHERE id = :cell_id AND deleted_at IS NULL
            RETURNING id, is_locked, lock_reason, locked_by, locked_at
        """

        result = await self.session.execute(
            text(query),
            {"cell_id": str(cell_id)},
        )
        row = result.fetchone()
        await self.session.commit()

        logger.info(
            "cell_unlocked",
            cell_id=str(cell_id),
            unlock_reason=unlock.unlock_reason,
            user_id=str(user_id),
        )

        return CellLockResponse(**dict(row._mapping))

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _log_cell_change(
        self,
        cell_id: UUID,
        budget_version_id: Any,
        module_code: str,
        entity_id: Any,
        field_name: str,
        period_code: str | None,
        old_value_numeric: Decimal | None,
        old_value_text: str | None,
        new_value_numeric: Decimal | None,
        new_value_text: str | None,
        change_type: str,
        session_id: UUID,
        sequence_number: int,
        user_id: UUID,
    ) -> None:
        """Log a cell change to the audit trail."""
        from sqlalchemy import text

        change_id = uuid4()
        now = datetime.utcnow()

        query = """
            INSERT INTO efir_budget.cell_changes (
                id, cell_id, budget_version_id, module_code, entity_id, field_name,
                period_code, old_value_numeric, old_value_text, new_value_numeric, new_value_text,
                change_type, session_id, sequence_number, changed_by, changed_at
            ) VALUES (
                :id, :cell_id, :budget_version_id, :module_code, :entity_id, :field_name,
                :period_code, :old_value_numeric, :old_value_text, :new_value_numeric, :new_value_text,
                :change_type, :session_id, :sequence_number, :user_id, :now
            )
        """

        await self.session.execute(
            text(query),
            {
                "id": str(change_id),
                "cell_id": str(cell_id),
                "budget_version_id": str(budget_version_id),
                "module_code": module_code,
                "entity_id": str(entity_id),
                "field_name": field_name,
                "period_code": period_code,
                "old_value_numeric": float(old_value_numeric) if old_value_numeric is not None else None,
                "old_value_text": old_value_text,
                "new_value_numeric": float(new_value_numeric) if new_value_numeric is not None else None,
                "new_value_text": new_value_text,
                "change_type": change_type,
                "session_id": str(session_id),
                "sequence_number": sequence_number,
                "user_id": str(user_id),
                "now": now,
            },
        )

    async def _invalidate_module_cache(
        self,
        module_code: str,
        budget_version_id: str,
    ) -> None:
        """Invalidate caches for a module and its dependents."""
        cache_entity = MODULE_TO_CACHE_ENTITY.get(module_code)
        if cache_entity:
            try:
                await CacheInvalidator.invalidate(budget_version_id, cache_entity)
                logger.debug(
                    "cache_invalidated",
                    module_code=module_code,
                    cache_entity=cache_entity,
                    budget_version_id=budget_version_id,
                )
            except Exception as e:
                # Log but don't fail the operation if cache invalidation fails
                logger.warning(
                    "cache_invalidation_failed",
                    module_code=module_code,
                    error=str(e),
                )
