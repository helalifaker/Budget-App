"""
Writeback API endpoints.

Provides REST API for cell-level data operations supporting real-time
collaborative editing in AG Grid with optimistic locking and undo/redo:

- PUT /cells/{cell_id} - Update single cell with optimistic locking
- POST /cells/batch - Batch update multiple cells
- GET /cells/changes/{version_id} - Get change history
- POST /cells/undo - Undo changes in a session
- POST /cells/{cell_id}/comments - Add comment to cell
- POST /cells/{cell_id}/lock - Lock cell to prevent edits
- DELETE /cells/{cell_id}/lock - Unlock cell

All endpoints support authentication and implement proper HTTP status codes:
- 200: Success
- 201: Created
- 400: Validation error
- 401: Not authenticated
- 403: Forbidden (insufficient permissions)
- 404: Not found
- 409: Version conflict (optimistic locking failure)
- 423: Resource locked
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import PlannerDep, UserDep
from app.schemas.admin.writeback import (
    BatchUpdateRequest,
    BatchUpdateResponse,
    CellChangeResponse,
    CellCreateRequest,
    CellLockResponse,
    CellResponse,
    CellUpdateRequest,
    CellUpdateResponse,
    CommentListResponse,
    CommentRequest,
    CommentResponse,
    LockRequest,
    UndoRequest,
    UndoResponse,
    UnlockRequest,
)
from app.services.admin.writeback_service import WritebackService
from app.services.exceptions import (
    CellLockedError,
    NotFoundError,
    ValidationError,
    VersionConflictError,
)

router = APIRouter(prefix="/writeback", tags=["writeback"])


def get_writeback_service(
    db: AsyncSession = Depends(get_db),
) -> WritebackService:
    """
    Dependency to get writeback service instance.

    Args:
        db: Database session

    Returns:
        WritebackService instance
    """
    return WritebackService(db)


# ==============================================================================
# Cell CRUD Endpoints
# ==============================================================================


@router.get(
    "/cells/{cell_id}",
    response_model=CellResponse,
    summary="Get cell by ID",
    description="Retrieve a single planning cell by its UUID. "
    "Returns full cell details including lock status and comment counts.",
    responses={
        200: {"description": "Cell retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Cell not found"},
    },
)
async def get_cell(
    cell_id: Annotated[UUID, Path(description="Cell UUID")],
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: UserDep = ...,
) -> CellResponse:
    """
    Get a single planning cell by ID.

    Args:
        cell_id: Cell UUID
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        Cell details

    Raises:
        404: Cell not found
    """
    try:
        cell = await writeback_service.get_cell_by_id(cell_id)
        if cell is None:
            raise NotFoundError("PlanningCell", str(cell_id))
        return CellResponse(**cell)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cell: {e!s}",
        )


@router.post(
    "/cells",
    response_model=CellResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cell",
    description="Create a new planning cell. Requires planner or higher permissions.",
    responses={
        201: {"description": "Cell created successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
    },
)
async def create_cell(
    cell_data: CellCreateRequest,
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: PlannerDep = ...,
) -> CellResponse:
    """
    Create a new planning cell.

    Args:
        cell_data: Cell creation data
        writeback_service: Writeback service
        user: Current authenticated user (must be planner or higher)

    Returns:
        Created cell

    Raises:
        400: Validation error
        403: Insufficient permissions
    """
    try:
        cell = await writeback_service.create_cell(cell_data, user.user_id)
        return cell
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cell: {e!s}",
        )


@router.put(
    "/cells/{cell_id}",
    response_model=CellUpdateResponse,
    summary="Update a single cell",
    description="Update a planning cell with optimistic locking. "
    "The version field must match the current version in the database, "
    "or the update will fail with a 409 Conflict error. "
    "Locked cells cannot be updated (returns 423).",
    responses={
        200: {"description": "Cell updated successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Cell not found"},
        409: {
            "description": "Version conflict - cell was modified by another user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": "version_conflict",
                            "message": "Cell was modified by another user",
                            "current_version": 5,
                            "provided_version": 3,
                        }
                    }
                }
            },
        },
        423: {
            "description": "Cell is locked",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": "cell_locked",
                            "message": "Cell is locked: Budget approved",
                            "cell_id": "abc123",
                        }
                    }
                }
            },
        },
    },
)
async def update_cell(
    cell_id: Annotated[UUID, Path(description="Cell UUID")],
    update: CellUpdateRequest,
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: PlannerDep = ...,
) -> CellUpdateResponse:
    """
    Update a single planning cell with optimistic locking.

    The version field implements optimistic locking:
    - Load cell data (includes version number)
    - User makes edits
    - Submit update with same version number
    - If version matches, update succeeds and version increments
    - If version doesn't match (another user edited), returns 409 Conflict

    Args:
        cell_id: Cell UUID
        update: Update data including version for locking
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        Updated cell with new version number

    Raises:
        404: Cell not found
        409: Version conflict (cell was modified by another user)
        423: Cell is locked
    """
    try:
        return await writeback_service.update_cell(cell_id, update, user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except VersionConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "version_conflict",
                "message": e.message,
                "current_version": e.details.get("current_version"),
                "provided_version": e.details.get("provided_version"),
            },
        )
    except CellLockedError as e:
        raise HTTPException(
            status_code=423,  # HTTP 423 Locked
            detail={
                "error": "cell_locked",
                "message": e.message,
                "cell_id": e.details.get("cell_id"),
                "lock_reason": e.details.get("lock_reason"),
            },
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cell: {e!s}",
        )


# ==============================================================================
# Batch Update Endpoint
# ==============================================================================


@router.post(
    "/cells/batch",
    response_model=BatchUpdateResponse,
    summary="Batch update multiple cells",
    description="Update multiple cells in a single transaction. "
    "All updates share the same session_id for grouped undo. "
    "By default, if any update fails, all updates are rolled back. "
    "Set allow_partial_success=true to commit successful updates even if some fail.",
    responses={
        200: {"description": "Batch update completed (check conflicts for failures)"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
    },
)
async def batch_update_cells(
    batch: BatchUpdateRequest,
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: PlannerDep = ...,
) -> BatchUpdateResponse:
    """
    Update multiple cells in a single transaction.

    Use cases:
    - Spreading operations (update 12 period cells at once)
    - Copy/paste in AG Grid (multiple cells)
    - Import operations from Excel

    All updates share the same session_id, which can be used with
    the undo endpoint to revert all changes at once.

    Args:
        batch: Batch update request with list of cell updates
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        Response with updated cells and any conflicts
    """
    try:
        return await writeback_service.batch_update_cells(batch, user.user_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch update cells: {e!s}",
        )


# ==============================================================================
# Change History Endpoint
# ==============================================================================


@router.get(
    "/cells/changes/{version_id}",
    response_model=list[CellChangeResponse],
    summary="Get change history",
    description="Get change history for a budget version. "
    "Can be filtered by module, entity, or field. "
    "Returns changes ordered by changed_at descending (most recent first).",
    responses={
        200: {"description": "Change history retrieved"},
        401: {"description": "Not authenticated"},
    },
)
async def get_change_history(
    version_id: Annotated[UUID, Path(description="Budget version UUID")],
    module_code: Annotated[str | None, Query(description="Filter by module code")] = None,
    entity_id: Annotated[UUID | None, Query(description="Filter by entity ID")] = None,
    field_name: Annotated[str | None, Query(description="Filter by field name")] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Maximum records to return")] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: UserDep = ...,
) -> list[CellChangeResponse]:
    """
    Get change history for cells in a budget version.

    Powers undo/redo functionality and audit trail display.
    Changes are ordered by changed_at descending (most recent first).

    Args:
        version_id: Budget version to query
        module_code: Optional filter by module
        entity_id: Optional filter by entity
        field_name: Optional filter by field
        limit: Maximum records to return (1-1000)
        offset: Number of records to skip
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        List of change history records
    """
    try:
        return await writeback_service.get_change_history(
            version_id=version_id,
            module_code=module_code,
            entity_id=entity_id,
            field_name=field_name,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get change history: {e!s}",
        )


# ==============================================================================
# Undo Endpoint
# ==============================================================================


@router.post(
    "/cells/undo",
    response_model=UndoResponse,
    summary="Undo changes in a session",
    description="Undo all changes in a session by reverting cells to their previous values. "
    "Creates a new session for the undo operation, which can be used to redo. "
    "Locked cells cannot be undone.",
    responses={
        200: {"description": "Undo completed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Session not found"},
    },
)
async def undo_changes(
    request: UndoRequest,
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: PlannerDep = ...,
) -> UndoResponse:
    """
    Undo all changes in a session.

    Reverts all cells in the session to their old_value from the change log.
    Creates a new session for the undo operation, allowing redo if needed.

    Args:
        request: Undo request with session_id
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        Undo response with reverted cells and new session_id for redo
    """
    try:
        return await writeback_service.undo_session(request, user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to undo changes: {e!s}",
        )


# ==============================================================================
# Comment Endpoints
# ==============================================================================


@router.post(
    "/cells/{cell_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to cell",
    description="Add a comment or annotation to a cell. "
    "Comments can be used for notes, questions, or review feedback.",
    responses={
        201: {"description": "Comment added"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        404: {"description": "Cell not found"},
    },
)
async def add_cell_comment(
    cell_id: Annotated[UUID, Path(description="Cell UUID")],
    comment: CommentRequest,
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: UserDep = ...,
) -> CommentResponse:
    """
    Add a comment to a cell.

    Args:
        cell_id: Cell to comment on
        comment: Comment data
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        Created comment
    """
    try:
        return await writeback_service.add_comment(cell_id, comment, user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add comment: {e!s}",
        )


@router.get(
    "/cells/{cell_id}/comments",
    response_model=CommentListResponse,
    summary="Get cell comments",
    description="Get all comments for a cell, ordered by created_at descending.",
    responses={
        200: {"description": "Comments retrieved"},
        401: {"description": "Not authenticated"},
        404: {"description": "Cell not found"},
    },
)
async def get_cell_comments(
    cell_id: Annotated[UUID, Path(description="Cell UUID")],
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: UserDep = ...,
) -> CommentListResponse:
    """
    Get all comments for a cell.

    Args:
        cell_id: Cell to get comments for
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        List of comments with counts
    """
    try:
        # Verify cell exists
        await writeback_service.get_cell_by_id(cell_id)

        comments = await writeback_service.get_cell_comments(cell_id)
        unresolved_count = sum(1 for c in comments if not c.is_resolved)

        return CommentListResponse(
            cell_id=cell_id,
            comments=comments,
            total_count=len(comments),
            unresolved_count=unresolved_count,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comments: {e!s}",
        )


@router.post(
    "/comments/{comment_id}/resolve",
    response_model=CommentResponse,
    summary="Resolve a comment",
    description="Mark a comment as resolved.",
    responses={
        200: {"description": "Comment resolved"},
        401: {"description": "Not authenticated"},
        404: {"description": "Comment not found"},
    },
)
async def resolve_comment(
    comment_id: Annotated[UUID, Path(description="Comment UUID")],
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: UserDep = ...,
) -> CommentResponse:
    """
    Mark a comment as resolved.

    Args:
        comment_id: Comment to resolve
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        Updated comment
    """
    try:
        return await writeback_service.resolve_comment(comment_id, user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve comment: {e!s}",
        )


# ==============================================================================
# Lock/Unlock Endpoints
# ==============================================================================


@router.post(
    "/cells/{cell_id}/lock",
    response_model=CellLockResponse,
    summary="Lock a cell",
    description="Lock a cell to prevent edits. "
    "Typically used after budget approval to freeze values. "
    "Requires planner or higher permissions.",
    responses={
        200: {"description": "Cell locked"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Cell not found"},
    },
)
async def lock_cell(
    cell_id: Annotated[UUID, Path(description="Cell UUID")],
    lock: LockRequest,
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: PlannerDep = ...,
) -> CellLockResponse:
    """
    Lock a cell to prevent edits.

    Args:
        cell_id: Cell to lock
        lock: Lock request with reason
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        Lock response
    """
    try:
        return await writeback_service.lock_cell(cell_id, lock, user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to lock cell: {e!s}",
        )


@router.delete(
    "/cells/{cell_id}/lock",
    response_model=CellLockResponse,
    summary="Unlock a cell",
    description="Unlock a cell to allow edits. "
    "Requires planner or higher permissions.",
    responses={
        200: {"description": "Cell unlocked"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Cell not found"},
    },
)
async def unlock_cell(
    cell_id: Annotated[UUID, Path(description="Cell UUID")],
    unlock: UnlockRequest = UnlockRequest(unlock_reason=None),
    writeback_service: WritebackService = Depends(get_writeback_service),
    user: PlannerDep = ...,
) -> CellLockResponse:
    """
    Unlock a cell to allow edits.

    Args:
        cell_id: Cell to unlock
        unlock: Unlock request with optional reason
        writeback_service: Writeback service
        user: Current authenticated user

    Returns:
        Lock response
    """
    try:
        return await writeback_service.unlock_cell(cell_id, unlock, user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock cell: {e!s}",
        )


# ==============================================================================
# Health Check Endpoint
# ==============================================================================


@router.get(
    "/health",
    summary="Writeback API health check",
    description="Check if the writeback API is operational.",
    responses={
        200: {"description": "API is healthy"},
    },
)
async def health_check() -> dict:
    """
    Health check endpoint for writeback API.

    Returns:
        Status and available endpoints
    """
    return {
        "status": "healthy",
        "service": "writeback",
        "endpoints": {
            "update_cell": "PUT /cells/{cell_id}",
            "batch_update": "POST /cells/batch",
            "change_history": "GET /cells/changes/{version_id}",
            "undo": "POST /cells/undo",
            "add_comment": "POST /cells/{cell_id}/comments",
            "lock_cell": "POST /cells/{cell_id}/lock",
            "unlock_cell": "DELETE /cells/{cell_id}/lock",
        },
    }
