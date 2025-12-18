"""
Enrollment Planning API endpoints.

Handles student count inputs, distributions, and basic projections.
Replaces legacy /planning/enrollment endpoints.
"""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.enrollment.enrollment_plan import (
    EnrollmentPlanBase,
    EnrollmentPlanCreate,
    EnrollmentPlanResponse,
    EnrollmentPlanUpdate,
    EnrollmentSummary,
    EnrollmentTotalsBulkUpdate,
    EnrollmentWithDistributionResponse,
)
from app.schemas.enrollment.enrollment import (
    EnrollmentProjectionRequest,
    EnrollmentProjectionResponse,
)
from app.services.enrollment.enrollment_service import EnrollmentService
from app.services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/enrollment", tags=["Enrollment Planning"])


def get_enrollment_service(db: AsyncSession = Depends(get_db)) -> EnrollmentService:
    """Dependency to get enrollment service instance."""
    return EnrollmentService(db)


@router.get(
    "/{version_id}",
    response_model=list[EnrollmentPlanResponse],
    summary="Get enrollment plan",
)
async def get_enrollment_plan(
    version_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """Get enrollment plan for a budget version."""
    try:
        return await enrollment_service.get_enrollment_plan(version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{version_id}",
    response_model=EnrollmentPlanResponse,
    summary="Create enrollment entry",
    status_code=status.HTTP_201_CREATED,
)
async def create_enrollment(
    version_id: uuid.UUID,
    enrollment_data: EnrollmentPlanCreate,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """Create a single enrollment entry."""
    try:
        return await enrollment_service.create_enrollment(
            version_id=version_id,
            level_id=enrollment_data.level_id,
            nationality_type_id=enrollment_data.nationality_type_id,
            student_count=enrollment_data.student_count,
            notes=enrollment_data.notes,
            user_id=user.user_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put(
    "/{enrollment_id}",
    response_model=EnrollmentPlanResponse,
    summary="Update enrollment entry",
)
async def update_enrollment(
    enrollment_id: uuid.UUID,
    enrollment_data: EnrollmentPlanUpdate,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """Update an enrollment entry."""
    try:
        return await enrollment_service.update_enrollment(
            enrollment_id=enrollment_id,
            student_count=enrollment_data.student_count,
            notes=enrollment_data.notes,
            user_id=user.user_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete enrollment entry",
)
async def delete_enrollment(
    enrollment_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """Delete an enrollment entry."""
    try:
        await enrollment_service.delete_enrollment(enrollment_id, user_id=user.user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{version_id}/summary",
    response_model=EnrollmentSummary,
    summary="Get enrollment summary",
)
async def get_enrollment_summary(
    version_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """Get enrollment summary statistics."""
    try:
        return await enrollment_service.get_enrollment_summary(version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{version_id}/with-distribution",
    response_model=EnrollmentWithDistributionResponse,
    summary="Get enrollment with distribution breakdown",
)
async def get_enrollment_with_distribution(
    version_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """Get enrollment data with calculating nationality breakdowns."""
    try:
        data = await enrollment_service.get_enrollment_with_distribution(version_id)
        return EnrollmentWithDistributionResponse(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{version_id}/project",
    response_model=list[EnrollmentProjectionResponse],
    summary="Project enrollment (Simple)",
)
async def project_enrollment(
    version_id: uuid.UUID,
    request: EnrollmentProjectionRequest,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Generate simple enrollment projection.
    
    NOTE: For advanced Module 7 projection with overrides, use the
    /enrollment-projection API instead.
    """
    try:
        # Check custom growth rates type adaptation if needed
        custom_rates = request.custom_growth_rates
        if custom_rates:
             # Convert float to Decimal if needed, though Pydantic v2 handles this
             custom_rates = {k: Decimal(str(v)) for k, v in custom_rates.items()}

        projections = await enrollment_service.project_enrollment(
            version_id=version_id,
            years_to_project=request.years_to_project,
            growth_scenario=request.growth_scenario,
            custom_growth_rates=custom_rates,
        )
        return projections
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.api_route(
    "/{version_id}/bulk",
    methods=["POST", "PUT"],
    response_model=list[EnrollmentPlanResponse],
    summary="Bulk upsert enrollment totals",
)
async def bulk_upsert_enrollment_totals(
    version_id: uuid.UUID,
    bulk_data: EnrollmentTotalsBulkUpdate,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """Bulk upsert enrollment totals by level (distributes by nationality)."""
    try:
        # Convert Pydantic models to dicts
        totals_dict = [t.model_dump() for t in bulk_data.totals]
        
        return await enrollment_service.bulk_upsert_enrollment_totals(
            version_id=version_id,
            totals=totals_dict,
            user_id=user.user_id,
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
