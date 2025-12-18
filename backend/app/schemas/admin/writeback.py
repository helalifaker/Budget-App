"""
Pydantic schemas for writeback API endpoints.

Request and response models for cell-level data operations:
- Single cell updates with optimistic locking
- Batch cell updates for spreadsheet operations
- Change history and audit trail
- Undo/redo operations
- Cell comments and annotations
- Cell locking for approved budgets

These schemas support real-time collaborative editing in AG Grid with
conflict detection and resolution.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ==============================================================================
# Value Type Enumeration
# ==============================================================================

ValueType = Literal["numeric", "text", "boolean", "date", "percentage", "currency"]
ChangeType = Literal["create", "update", "delete", "undo", "redo", "bulk_update"]


# ==============================================================================
# Cell Update Schemas
# ==============================================================================


class CellUpdateRequest(BaseModel):
    """
    Request to update a single planning cell with optimistic locking.

    The version field is used for optimistic locking - the update will fail
    if the cell has been modified by another user since it was loaded.
    """

    value_numeric: Decimal | None = Field(
        None,
        description="Numeric value for the cell (for numeric, currency, percentage types)",
        examples=[Decimal("1234.56")],
    )
    value_text: str | None = Field(
        None,
        max_length=500,
        description="Text value for the cell (for text, date types)",
        examples=["Budget note"],
    )
    version: int = Field(
        ...,
        ge=1,
        description="Current version of the cell for optimistic locking. "
        "Must match the version in the database or update will fail with 409 Conflict.",
        examples=[1],
    )

    @model_validator(mode="after")
    def validate_at_least_one_value(self) -> "CellUpdateRequest":
        """Ensure at least one value field is provided."""
        if self.value_numeric is None and self.value_text is None:
            raise ValueError("At least one of value_numeric or value_text must be provided")
        return self


class CellUpdateResponse(BaseModel):
    """
    Response after successful cell update.

    Returns the updated cell with the new version number for subsequent updates.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Cell unique identifier")
    version_id: UUID = Field(..., description="Budget version this cell belongs to")
    module_code: str = Field(..., description="Module code (e.g., 'enrollment', 'dhg', 'revenue')")
    entity_id: UUID = Field(..., description="Entity ID within the module (e.g., enrollment_plan_id)")
    field_name: str = Field(..., description="Field name being edited (e.g., 'student_count')")
    period_code: str | None = Field(None, description="Period code if applicable (e.g., 'P1', 'P2')")
    value_numeric: Decimal | None = Field(None, description="Updated numeric value")
    value_text: str | None = Field(None, description="Updated text value")
    value_type: ValueType = Field(..., description="Type of value stored")
    version: int = Field(..., description="New version number (incremented after update)")
    modified_by: UUID = Field(..., description="User who made the update")
    modified_at: datetime = Field(..., description="Timestamp of the update")
    is_locked: bool = Field(default=False, description="Whether the cell is locked")


# ==============================================================================
# Batch Update Schemas
# ==============================================================================


class CellUpdate(BaseModel):
    """
    Individual cell update within a batch operation.

    Used for spreadsheet operations like copy/paste, fill-down, or import.
    """

    cell_id: UUID = Field(..., description="Cell identifier to update")
    value_numeric: Decimal | None = Field(None, description="Numeric value")
    value_text: str | None = Field(None, description="Text value")
    version: int = Field(
        ...,
        ge=1,
        description="Current version for optimistic locking",
    )

    @model_validator(mode="after")
    def validate_at_least_one_value(self) -> "CellUpdate":
        """Ensure at least one value field is provided."""
        if self.value_numeric is None and self.value_text is None:
            raise ValueError("At least one of value_numeric or value_text must be provided")
        return self


class BatchUpdateRequest(BaseModel):
    """
    Batch update multiple cells in a single transaction.

    Use cases:
    - Spreading operations (update 12 period cells at once)
    - Copy/paste in AG Grid (multiple cells)
    - Import operations from Excel

    All updates share the same session_id for grouped undo capability.
    """

    session_id: UUID = Field(
        default_factory=uuid4,
        description="Unique session identifier for grouping changes. "
        "All updates in this batch can be undone together.",
    )
    updates: list[CellUpdate] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of cell updates (1-1000 cells per batch)",
    )
    allow_partial_success: bool = Field(
        default=False,
        description="If True, successful updates will be committed even if some fail. "
        "If False (default), all updates fail if any single update fails.",
    )


class ConflictDetail(BaseModel):
    """Details about a cell update conflict during batch operation."""

    cell_id: UUID = Field(..., description="Cell that had a conflict")
    error_type: Literal["version_conflict", "cell_locked", "validation_error", "not_found"] = Field(
        ..., description="Type of conflict"
    )
    message: str = Field(..., description="Human-readable error message")
    current_version: int | None = Field(None, description="Current version in database (for conflicts)")
    provided_version: int | None = Field(None, description="Version provided in request")


class BatchUpdateResponse(BaseModel):
    """Response for batch update operation."""

    session_id: UUID = Field(..., description="Session identifier for undo operation")
    updated_count: int = Field(..., ge=0, description="Number of cells successfully updated")
    failed_count: int = Field(..., ge=0, description="Number of cells that failed to update")
    updated_cells: list[CellUpdateResponse] = Field(
        default_factory=list,
        description="List of successfully updated cells",
    )
    conflicts: list[ConflictDetail] = Field(
        default_factory=list,
        description="List of cells that failed to update",
    )


# ==============================================================================
# Change History Schemas
# ==============================================================================


class CellChangeResponse(BaseModel):
    """
    Change history record for audit trail.

    Tracks who changed what, when, and provides old/new values for undo.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Change record identifier")
    cell_id: UUID = Field(..., description="Cell that was changed")
    version_id: UUID = Field(..., description="Budget version")
    module_code: str = Field(..., description="Module code")
    entity_id: UUID = Field(..., description="Entity ID within module")
    field_name: str = Field(..., description="Field that was changed")
    period_code: str | None = Field(None, description="Period code if applicable")
    old_value_numeric: Decimal | None = Field(None, description="Previous numeric value")
    old_value_text: str | None = Field(None, description="Previous text value")
    new_value_numeric: Decimal | None = Field(None, description="New numeric value")
    new_value_text: str | None = Field(None, description="New text value")
    change_type: ChangeType = Field(..., description="Type of change")
    session_id: UUID = Field(..., description="Session ID for grouped undo")
    sequence_number: int = Field(..., description="Sequence within session for ordering")
    changed_by: UUID = Field(..., description="User who made the change")
    changed_at: datetime = Field(..., description="When the change was made")


class ChangeHistoryFilters(BaseModel):
    """Filters for querying change history."""

    module_code: str | None = Field(None, description="Filter by module code")
    entity_id: UUID | None = Field(None, description="Filter by entity ID")
    field_name: str | None = Field(None, description="Filter by field name")
    changed_by: UUID | None = Field(None, description="Filter by user who made changes")
    change_type: ChangeType | None = Field(None, description="Filter by change type")
    from_date: datetime | None = Field(None, description="Filter changes after this date")
    to_date: datetime | None = Field(None, description="Filter changes before this date")


# ==============================================================================
# Undo/Redo Schemas
# ==============================================================================


class UndoRequest(BaseModel):
    """
    Request to undo all changes in a session.

    Reverts all cells in the session to their previous values.
    """

    session_id: UUID = Field(
        ...,
        description="Session identifier of changes to undo. "
        "All changes made in this session will be reverted.",
    )


class UndoResponse(BaseModel):
    """Response after undo operation."""

    reverted_count: int = Field(..., ge=0, description="Number of cells reverted")
    new_session_id: UUID = Field(
        ...,
        description="New session ID for the undo operation. "
        "Use this session_id to redo the changes if needed.",
    )
    reverted_cells: list[UUID] = Field(
        default_factory=list,
        description="List of cell IDs that were reverted",
    )
    failed_cells: list[ConflictDetail] = Field(
        default_factory=list,
        description="Cells that could not be reverted (e.g., if locked)",
    )


class RedoRequest(BaseModel):
    """Request to redo an undone session."""

    session_id: UUID = Field(
        ...,
        description="Session ID of the undo operation to redo. "
        "This is the new_session_id returned from the undo response.",
    )


class RedoResponse(BaseModel):
    """Response after redo operation."""

    reapplied_count: int = Field(..., ge=0, description="Number of cells re-applied")
    new_session_id: UUID = Field(..., description="New session ID for subsequent undo")
    reapplied_cells: list[UUID] = Field(
        default_factory=list,
        description="List of cell IDs that were re-applied",
    )
    failed_cells: list[ConflictDetail] = Field(
        default_factory=list,
        description="Cells that could not be re-applied",
    )


# ==============================================================================
# Cell Comment Schemas
# ==============================================================================


class CommentRequest(BaseModel):
    """Request to add a comment to a cell."""

    comment_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Comment text (1-2000 characters)",
        examples=["Verify this enrollment projection with HR department"],
    )


class CommentResponse(BaseModel):
    """Cell comment details."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Comment identifier")
    cell_id: UUID = Field(..., description="Cell this comment belongs to")
    comment_text: str = Field(..., description="Comment content")
    is_resolved: bool = Field(default=False, description="Whether the comment has been resolved")
    created_by: UUID = Field(..., description="User who created the comment")
    created_at: datetime = Field(..., description="When the comment was created")
    resolved_by: UUID | None = Field(None, description="User who resolved the comment")
    resolved_at: datetime | None = Field(None, description="When the comment was resolved")


class CommentListResponse(BaseModel):
    """List of comments for a cell."""

    cell_id: UUID = Field(..., description="Cell identifier")
    comments: list[CommentResponse] = Field(default_factory=list, description="List of comments")
    total_count: int = Field(..., ge=0, description="Total number of comments")
    unresolved_count: int = Field(..., ge=0, description="Number of unresolved comments")


class ResolveCommentRequest(BaseModel):
    """Request to resolve a comment."""

    resolution_note: str | None = Field(
        None,
        max_length=500,
        description="Optional note about how the comment was resolved",
    )


# ==============================================================================
# Cell Lock Schemas
# ==============================================================================


class LockRequest(BaseModel):
    """Request to lock a cell to prevent edits."""

    lock_reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Reason for locking the cell",
        examples=["Budget approved - no further edits allowed"],
    )


class UnlockRequest(BaseModel):
    """Request to unlock a cell."""

    unlock_reason: str | None = Field(
        None,
        max_length=500,
        description="Reason for unlocking the cell",
        examples=["Budget reopened for revision"],
    )


class CellLockResponse(BaseModel):
    """Response after lock/unlock operation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Cell identifier")
    is_locked: bool = Field(..., description="Current lock status")
    lock_reason: str | None = Field(None, description="Reason for locking")
    locked_by: UUID | None = Field(None, description="User who locked the cell")
    locked_at: datetime | None = Field(None, description="When the cell was locked")


# ==============================================================================
# Bulk Lock Schemas
# ==============================================================================


class BulkLockRequest(BaseModel):
    """Request to lock multiple cells at once."""

    cell_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of cell IDs to lock",
    )
    lock_reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Reason for locking all cells",
    )


class BulkLockResponse(BaseModel):
    """Response after bulk lock operation."""

    locked_count: int = Field(..., ge=0, description="Number of cells locked")
    already_locked_count: int = Field(..., ge=0, description="Number of cells already locked")
    failed_count: int = Field(..., ge=0, description="Number of cells that failed to lock")
    locked_cells: list[UUID] = Field(default_factory=list, description="Successfully locked cells")
    failed_cells: list[ConflictDetail] = Field(
        default_factory=list,
        description="Cells that could not be locked",
    )


# ==============================================================================
# Cell Create Schema (for new cells)
# ==============================================================================


class CellCreateRequest(BaseModel):
    """Request to create a new planning cell."""

    version_id: UUID = Field(..., description="Budget version for this cell")
    module_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Module code (e.g., 'enrollment', 'dhg', 'revenue')",
    )
    entity_id: UUID = Field(..., description="Entity ID within the module")
    field_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Field name being stored",
    )
    period_code: str | None = Field(
        None,
        max_length=20,
        description="Period code if applicable (e.g., 'P1', 'P2', 'ANNUAL')",
    )
    value_numeric: Decimal | None = Field(None, description="Numeric value")
    value_text: str | None = Field(None, max_length=500, description="Text value")
    value_type: ValueType = Field(default="numeric", description="Type of value")

    @model_validator(mode="after")
    def validate_at_least_one_value(self) -> "CellCreateRequest":
        """Ensure at least one value field is provided."""
        if self.value_numeric is None and self.value_text is None:
            raise ValueError("At least one of value_numeric or value_text must be provided")
        return self


# ==============================================================================
# Get Cell Schema
# ==============================================================================


class CellResponse(BaseModel):
    """Full cell response with all details."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Cell unique identifier")
    version_id: UUID = Field(..., description="Budget version")
    module_code: str = Field(..., description="Module code")
    entity_id: UUID = Field(..., description="Entity ID")
    field_name: str = Field(..., description="Field name")
    period_code: str | None = Field(None, description="Period code")
    value_numeric: Decimal | None = Field(None, description="Numeric value")
    value_text: str | None = Field(None, description="Text value")
    value_type: ValueType = Field(..., description="Value type")
    is_locked: bool = Field(default=False, description="Lock status")
    lock_reason: str | None = Field(None, description="Lock reason")
    locked_by: UUID | None = Field(None, description="User who locked")
    locked_at: datetime | None = Field(None, description="Lock timestamp")
    version: int = Field(..., description="Version for optimistic locking")
    modified_by: UUID | None = Field(None, description="Last modifier")
    modified_at: datetime | None = Field(None, description="Last modification time")
    created_by: UUID = Field(..., description="Creator")
    created_at: datetime = Field(..., description="Creation time")
    comment_count: int = Field(default=0, description="Number of comments")
    unresolved_comment_count: int = Field(default=0, description="Unresolved comments")


class CellListResponse(BaseModel):
    """List of cells with pagination."""

    cells: list[CellResponse] = Field(default_factory=list, description="List of cells")
    total_count: int = Field(..., ge=0, description="Total number of cells")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of cells per page")
    has_next: bool = Field(..., description="Whether there are more pages")
