"""
CapEx Planning API endpoints.

Handles capital expenditure planning and depreciation schedules.
Replaces legacy /planning/capex endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.investments.investments import (
    CapExPlanCreate,
    CapExPlanResponse,
    CapExPlanUpdate,
    DepreciationCalculationResponse,
)
from app.services.exceptions import (
    NotFoundError,
    ValidationError,
)
from app.services.investments.capex_service import CapExService

router = APIRouter(prefix="/capex", tags=["CapEx Planning"])


def get_capex_service(db: AsyncSession = Depends(get_db)) -> CapExService:
    """Dependency to get capex service instance."""
    return CapExService(db)


@router.get(
    "/{version_id}",
    response_model=list[CapExPlanResponse],
    summary="Get CapEx plan",
)
async def get_capex_plan(
    version_id: uuid.UUID,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """Get CapEx plan for a budget version."""
    try:
        return await capex_service.get_capex_plan(version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{version_id}",
    response_model=CapExPlanResponse,
    summary="Create CapEx entry",
    status_code=status.HTTP_201_CREATED,
)
async def create_capex_entry(
    version_id: uuid.UUID,
    data: CapExPlanCreate,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """Create a CapEx plan entry."""
    try:
        return await capex_service.create_capex_entry(
            version_id=version_id,
            account_code=data.account_code,
            description=data.description,
            category=data.category,
            quantity=data.quantity,
            unit_cost_sar=data.unit_cost_sar,
            acquisition_date=data.acquisition_date,
            useful_life_years=data.useful_life_years,
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
    "/{capex_id}",
    response_model=CapExPlanResponse,
    summary="Update CapEx entry",
)
async def update_capex_entry(
    capex_id: uuid.UUID,
    data: CapExPlanUpdate,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """Update a CapEx plan entry."""
    try:
        return await capex_service.update_capex_entry(
            capex_id=capex_id,
            account_code=data.account_code,
            description=data.description,
            category=data.category,
            quantity=data.quantity,
            unit_cost_sar=data.unit_cost_sar,
            acquisition_date=data.acquisition_date,
            useful_life_years=data.useful_life_years,
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
    "/{capex_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete CapEx entry",
)
async def delete_capex_entry(
    capex_id: uuid.UUID,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """Delete a CapEx plan entry."""
    try:
        await capex_service.delete_capex_entry(capex_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{version_id}/summary",
    response_model=dict,
    summary="Get CapEx summary",
)
async def get_capex_summary(
    version_id: uuid.UUID,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """Get summarized CapEx data."""
    try:
        return await capex_service.get_capex_summary(version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{capex_id}/depreciation-schedule",
    response_model=DepreciationCalculationResponse,
    summary="Get depreciation schedule",
)
async def get_depreciation_schedule(
    capex_id: uuid.UUID,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """Get depreciation schedule for an asset."""
    try:
        return await capex_service.get_depreciation_schedule(capex_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
