"""
Revenue Planning API endpoints.

Handles revenue planning, tuition fees, and discounts.
Replaces legacy /planning/revenue endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.revenue.revenue import (
    RevenueBulkUpdateRequest,
    RevenueBulkUpdateResponse,
    RevenueCalculationRequest,
    RevenueCalculationResponse,
    RevenuePlanCreate,
    RevenuePlanResponse,
    RevenuePlanUpdate,
)
from app.services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from app.services.revenue.revenue_service import RevenueService

router = APIRouter(prefix="/revenue", tags=["Revenue Planning"])


def get_revenue_service(db: AsyncSession = Depends(get_db)) -> RevenueService:
    """Dependency to get revenue service instance."""
    return RevenueService(db)


@router.get(
    "/{version_id}",
    response_model=list[RevenuePlanResponse],
    summary="Get revenue plan",
)
async def get_revenue_plan(
    version_id: uuid.UUID,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """Get revenue plan for a budget version."""
    try:
        return await revenue_service.get_revenue_plan(version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{version_id}",
    response_model=RevenuePlanResponse,
    summary="Create revenue entry",
    status_code=status.HTTP_201_CREATED,
)
async def create_revenue_entry(
    version_id: uuid.UUID,
    data: RevenuePlanCreate,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """Create a revenue plan entry."""
    try:
        return await revenue_service.create_revenue_entry(
            version_id=version_id,
            account_code=data.account_code,
            description=data.description,
            category=data.category,
            amount_sar=data.amount_sar,
            is_calculated=data.is_calculated,
            calculation_driver=data.calculation_driver,
            trimester=data.trimester,
            notes=data.notes,
            user_id=user.user_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put(
    "/{revenue_id}",
    response_model=RevenuePlanResponse,
    summary="Update revenue entry",
)
async def update_revenue_entry(
    revenue_id: uuid.UUID,
    data: RevenuePlanUpdate,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """Update a revenue plan entry."""
    try:
        return await revenue_service.update_revenue_entry(
            revenue_id=revenue_id,
            account_code=data.account_code,
            description=data.description,
            category=data.category,
            amount_sar=data.amount_sar,
            is_calculated=data.is_calculated,
            calculation_driver=data.calculation_driver,
            trimester=data.trimester,
            notes=data.notes,
            user_id=user.user_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/{revenue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete revenue entry",
)
async def delete_revenue_entry(
    revenue_id: uuid.UUID,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """Delete a revenue plan entry."""
    try:
        await revenue_service.delete_revenue_entry(revenue_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{version_id}/calculate",
    response_model=RevenueCalculationResponse,
    summary="Calculate revenue",
)
async def calculate_revenue(
    version_id: uuid.UUID,
    request: RevenueCalculationRequest,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """Calculate revenue based on enrollment and assumptions."""
    try:
        return await revenue_service.calculate_revenue_from_enrollment(
            version_id=version_id,
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


@router.get(
    "/{version_id}/summary",
    response_model=dict,
    summary="Get revenue summary",
)
async def get_revenue_summary(
    version_id: uuid.UUID,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """Get summarized revenue data."""
    try:
        return await revenue_service.get_revenue_summary(version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{version_id}/bulk-update",
    response_model=RevenueBulkUpdateResponse,
    summary="Bulk update revenue",
)
async def bulk_update_revenue(
    version_id: uuid.UUID,
    bulk_data: RevenueBulkUpdateRequest,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """Bulk update revenue entries."""
    try:
        return await revenue_service.bulk_update_revenue(
            version_id=version_id,
            updates=bulk_data.updates,
            user_id=user.user_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
