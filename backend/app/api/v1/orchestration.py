"""
Planning Orchestration API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.settings.planning_progress import (
    CascadeRequest,
    CascadeResponse,
    PlanningProgressResponse,
)
from app.services.admin.cascade_service import CascadeService
from app.services.enrollment.planning_progress_service import PlanningProgressService
from app.services.exceptions import (
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/orchestration", tags=["Planning Orchestration"])


def get_planning_progress_service(
    db: AsyncSession = Depends(get_db),
) -> PlanningProgressService:
    """Dependency to get planning progress service instance."""
    return PlanningProgressService(db)


def get_cascade_service(db: AsyncSession = Depends(get_db)) -> CascadeService:
    """Dependency to get cascade service instance."""
    return CascadeService(db)


# ==============================================================================
# Planning Progress & Validation Endpoint
# ==============================================================================


@router.get(
    "/progress/{version_id}",
    response_model=PlanningProgressResponse,
    summary="Get planning progress and validation status",
)
async def get_planning_progress(
    version_id: uuid.UUID,
    progress_service: PlanningProgressService = Depends(get_planning_progress_service),
    user: UserDep = ...,
):
    """
    Get comprehensive planning progress with validation for all 6 planning steps.

    Args:
        version_id: Budget version UUID
        progress_service: Planning progress service
        user: Current authenticated user

    Returns:
        PlanningProgressResponse with status, validation, and blockers
    """
    try:
        progress = await progress_service.get_planning_progress(version_id)
        return progress
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# Cascade Recalculation Endpoints
# ==============================================================================


@router.post(
    "/cascade/{version_id}",
    response_model=CascadeResponse,
    summary="Cascade recalculation through dependent planning steps",
)
async def cascade_recalculate(
    version_id: uuid.UUID,
    request: CascadeRequest,
    cascade_service: CascadeService = Depends(get_cascade_service),
    user: UserDep = ...,
):
    """
    Trigger cascading recalculation of dependent planning steps.

    When a planning step changes (e.g., enrollment), this endpoint can
    automatically recalculate all dependent downstream steps in the
    correct order.

    Args:
        version_id: Budget version UUID
        request: Cascade request specifying from_step_id or step_ids
        cascade_service: Cascade service
        user: Current authenticated user

    Returns:
        CascadeResponse with recalculated and failed steps
    """
    try:
        if request.from_step_id:
            result = await cascade_service.recalculate_from_step(
                version_id, request.from_step_id
            )
        elif request.step_ids:
            result = await cascade_service.recalculate_steps(version_id, request.step_ids)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either from_step_id or step_ids must be provided",
            )

        return CascadeResponse(**result.to_dict())
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
