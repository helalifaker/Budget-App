"""
Cost Planning API endpoints.

Handles personnel and operating cost planning.
Refactored to exclude Revenue and CapEx (now in dedicated modules).
Replaces legacy /planning/costs endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.costs import (
    OperatingCostCalculationRequest,
    OperatingCostPlanCreate,
    OperatingCostPlanResponse,
    PersonnelCostCalculationRequest,
    PersonnelCostPlanCreate,
    PersonnelCostPlanResponse,
)
from app.services.costs.cost_service import CostService
from app.services.exceptions import (
    ValidationError,
)

router = APIRouter(prefix="/costs", tags=["Cost Planning"])


def get_cost_service(db: AsyncSession = Depends(get_db)) -> CostService:
    """Dependency to get cost service instance."""
    return CostService(db)


# ==============================================================================
# Personnel Cost Planning Endpoints
# ==============================================================================


@router.get("/personnel/{version_id}", response_model=list[PersonnelCostPlanResponse])
async def get_personnel_costs(
    version_id: uuid.UUID,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """Get personnel cost plan for a budget version."""
    try:
        return await cost_service.get_personnel_costs(version_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/personnel/{version_id}/calculate")
async def calculate_personnel_costs(
    version_id: uuid.UUID,
    calculation_request: PersonnelCostCalculationRequest,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """Calculate personnel costs from DHG teacher allocations."""
    try:
        return await cost_service.calculate_personnel_costs_from_dhg(
            version_id=version_id,
            eur_to_sar_rate=calculation_request.eur_to_sar_rate,
            user_id=user.user_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/personnel/{version_id}", response_model=PersonnelCostPlanResponse)
async def create_personnel_cost_entry(
    version_id: uuid.UUID,
    cost_data: PersonnelCostPlanCreate,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """Create or update personnel cost plan entry."""
    try:
        return await cost_service.create_personnel_cost_entry(
            version_id=version_id,
            account_code=cost_data.account_code,
            description=cost_data.description,
            fte_count=cost_data.fte_count,
            unit_cost_sar=cost_data.unit_cost_sar,
            category_id=cost_data.category_id,
            cycle_id=cost_data.cycle_id,
            is_calculated=cost_data.is_calculated,
            calculation_driver=cost_data.calculation_driver,
            notes=cost_data.notes,
            user_id=user.user_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==============================================================================
# Operating Cost Planning Endpoints
# ==============================================================================


@router.get("/operating/{version_id}", response_model=list[OperatingCostPlanResponse])
async def get_operating_costs(
    version_id: uuid.UUID,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """Get operating cost plan for a budget version."""
    try:
        return await cost_service.get_operating_costs(version_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/operating/{version_id}/calculate")
async def calculate_operating_costs(
    version_id: uuid.UUID,
    calculation_request: OperatingCostCalculationRequest,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """Calculate operating costs using driver-based models."""
    try:
        return await cost_service.calculate_operating_costs(
            version_id=version_id,
            cost_drivers=calculation_request.driver_rates,
            user_id=user.user_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/operating/{version_id}", response_model=OperatingCostPlanResponse)
async def create_operating_cost_entry(
    version_id: uuid.UUID,
    cost_data: OperatingCostPlanCreate,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """Create or update operating cost plan entry."""
    try:
        return await cost_service.create_operating_cost_entry(
            version_id=version_id,
            account_code=cost_data.account_code,
            description=cost_data.description,
            category=cost_data.category,
            amount_sar=cost_data.amount_sar,
            is_calculated=cost_data.is_calculated,
            calculation_driver=cost_data.calculation_driver,
            notes=cost_data.notes,
            user_id=user.user_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{version_id}/summary")
async def get_cost_summary(
    version_id: uuid.UUID,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """Get cost summary for a budget version."""
    try:
        return await cost_service.get_cost_summary(version_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
