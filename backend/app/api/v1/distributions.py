"""
Nationality Distributions API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.enrollment.distributions import (
    NationalityDistributionResponse,
    NationalityDistributionBulkUpdate,
)
from app.services.enrollment.enrollment_service import EnrollmentService
from app.services.exceptions import (
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/distributions", tags=["Distributions"])


def get_enrollment_service(db: AsyncSession = Depends(get_db)) -> EnrollmentService:
    """
    Dependency to get enrollment service instance.

    Args:
        db: Database session

    Returns:
        EnrollmentService instance
    """
    return EnrollmentService(db)


@router.get(
    "/{version_id}",
    response_model=list[NationalityDistributionResponse],
    summary="Get nationality distributions for a budget version",
)
async def get_distributions(
    version_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Get nationality distribution percentages for all levels in a budget version.

    Returns the French, Saudi, and Other nationality percentages for each
    academic level, used to calculate student breakdown from total counts.

    Args:
        version_id: Budget version UUID
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        List of NationalityDistributionResponse
    """
    try:
        distributions = await enrollment_service.get_distributions(version_id)
        return distributions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.api_route(
    "/{version_id}",
    methods=["POST", "PUT"],
    response_model=list[NationalityDistributionResponse],
    summary="Bulk upsert nationality distributions",
)
async def bulk_upsert_distributions(
    version_id: uuid.UUID,
    bulk_data: NationalityDistributionBulkUpdate,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Bulk create/update nationality distributions for a budget version.

    Validates that percentages sum to 100% for each level. Distributions are
    used to calculate student breakdown when entering enrollment totals.

    Args:
        version_id: Budget version UUID
        bulk_data: Distribution percentages
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        List of upserted NationalityDistributionResponse
    """
    try:
        distributions_dict = [
            {
                "level_id": d.level_id,
                "french_pct": d.french_pct,
                "saudi_pct": d.saudi_pct,
                "other_pct": d.other_pct,
            }
            for d in bulk_data.distributions
        ]
        distributions = await enrollment_service.bulk_upsert_distributions(
            version_id=version_id,
            distributions=distributions_dict,
            user_id=user.user_id,
        )
        return distributions
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
