"""
Revenue and Cost API endpoints.

Provides REST API for managing revenue and cost planning:
- Revenue planning (tuition, fees)
- Personnel cost planning (salaries, benefits)
- Operating cost planning (supplies, utilities, etc.)
- CapEx planning (assets, depreciation)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.costs import (
    CapExPlanCreate,
    CapExPlanResponse,
    CapExPlanUpdate,
    DepreciationCalculationRequest,
    DepreciationCalculationResponse,
    OperatingCostCalculationRequest,
    OperatingCostPlanCreate,
    OperatingCostPlanResponse,
    PersonnelCostCalculationRequest,
    PersonnelCostPlanCreate,
    PersonnelCostPlanResponse,
    RevenuePlanCreate,
    RevenuePlanResponse,
)
from app.services.capex_service import CapExService
from app.services.cost_service import CostService
from app.services.exceptions import (
    NotFoundError,
    ValidationError,
)
from app.services.revenue_service import RevenueService

router = APIRouter(prefix="/api/v1/planning", tags=["revenue-costs"])


def get_revenue_service(db: AsyncSession = Depends(get_db)) -> RevenueService:
    """
    Dependency to get revenue service instance.

    Args:
        db: Database session

    Returns:
        RevenueService instance
    """
    return RevenueService(db)


def get_cost_service(db: AsyncSession = Depends(get_db)) -> CostService:
    """
    Dependency to get cost service instance.

    Args:
        db: Database session

    Returns:
        CostService instance
    """
    return CostService(db)


def get_capex_service(db: AsyncSession = Depends(get_db)) -> CapExService:
    """
    Dependency to get CapEx service instance.

    Args:
        db: Database session

    Returns:
        CapExService instance
    """
    return CapExService(db)


# ==============================================================================
# Revenue Planning Endpoints
# ==============================================================================


@router.get("/revenue/{version_id}", response_model=list[RevenuePlanResponse])
async def get_revenue_plan(
    version_id: uuid.UUID,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """
    Get revenue plan for a budget version.

    Args:
        version_id: Budget version UUID
        revenue_service: Revenue service
        user: Current authenticated user

    Returns:
        List of revenue plan entries
    """
    try:
        revenue_plan = await revenue_service.get_revenue_plan(version_id)
        return revenue_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revenue/{version_id}/calculate")
async def calculate_revenue(
    version_id: uuid.UUID,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """
    Calculate revenue from enrollment and fee structure.

    Applies sibling discounts and trimester distribution.

    Args:
        version_id: Budget version UUID
        revenue_service: Revenue service
        user: Current authenticated user

    Returns:
        Revenue calculation results
    """
    try:
        result = await revenue_service.calculate_revenue_from_enrollment(
            version_id=version_id,
            user_id=user.id,
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revenue/{version_id}", response_model=RevenuePlanResponse)
async def create_revenue_entry(
    version_id: uuid.UUID,
    revenue_data: RevenuePlanCreate,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """
    Create or update revenue plan entry.

    Args:
        version_id: Budget version UUID
        revenue_data: Revenue plan data
        revenue_service: Revenue service
        user: Current authenticated user

    Returns:
        Created/updated revenue plan entry
    """
    try:
        entry = await revenue_service.create_revenue_entry(
            version_id=version_id,
            account_code=revenue_data.account_code,
            description=revenue_data.description,
            category=revenue_data.category,
            amount_sar=revenue_data.amount_sar,
            is_calculated=revenue_data.is_calculated,
            calculation_driver=revenue_data.calculation_driver,
            trimester=revenue_data.trimester,
            notes=revenue_data.notes,
            user_id=user.id,
        )
        return entry
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue/{version_id}/summary")
async def get_revenue_summary(
    version_id: uuid.UUID,
    revenue_service: RevenueService = Depends(get_revenue_service),
    user: UserDep = ...,
):
    """
    Get revenue summary for a budget version.

    Args:
        version_id: Budget version UUID
        revenue_service: Revenue service
        user: Current authenticated user

    Returns:
        Revenue summary statistics
    """
    try:
        summary = await revenue_service.get_revenue_summary(version_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Personnel Cost Planning Endpoints
# ==============================================================================


@router.get("/costs/personnel/{version_id}", response_model=list[PersonnelCostPlanResponse])
async def get_personnel_costs(
    version_id: uuid.UUID,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """
    Get personnel cost plan for a budget version.

    Args:
        version_id: Budget version UUID
        cost_service: Cost service
        user: Current authenticated user

    Returns:
        List of personnel cost plan entries
    """
    try:
        personnel_costs = await cost_service.get_personnel_costs(version_id)
        return personnel_costs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/costs/personnel/{version_id}/calculate")
async def calculate_personnel_costs(
    version_id: uuid.UUID,
    calculation_request: PersonnelCostCalculationRequest,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """
    Calculate personnel costs from DHG teacher allocations.

    Args:
        version_id: Budget version UUID
        calculation_request: Calculation parameters
        cost_service: Cost service
        user: Current authenticated user

    Returns:
        Personnel cost calculation results
    """
    try:
        result = await cost_service.calculate_personnel_costs_from_dhg(
            version_id=version_id,
            eur_to_sar_rate=calculation_request.eur_to_sar_rate,
            user_id=user.id,
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/costs/personnel/{version_id}", response_model=PersonnelCostPlanResponse)
async def create_personnel_cost_entry(
    version_id: uuid.UUID,
    cost_data: PersonnelCostPlanCreate,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """
    Create or update personnel cost plan entry.

    Args:
        version_id: Budget version UUID
        cost_data: Personnel cost plan data
        cost_service: Cost service
        user: Current authenticated user

    Returns:
        Created/updated personnel cost plan entry
    """
    try:
        entry = await cost_service.create_personnel_cost_entry(
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
            user_id=user.id,
        )
        return entry
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Operating Cost Planning Endpoints
# ==============================================================================


@router.get("/costs/operating/{version_id}", response_model=list[OperatingCostPlanResponse])
async def get_operating_costs(
    version_id: uuid.UUID,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """
    Get operating cost plan for a budget version.

    Args:
        version_id: Budget version UUID
        cost_service: Cost service
        user: Current authenticated user

    Returns:
        List of operating cost plan entries
    """
    try:
        operating_costs = await cost_service.get_operating_costs(version_id)
        return operating_costs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/costs/operating/{version_id}/calculate")
async def calculate_operating_costs(
    version_id: uuid.UUID,
    calculation_request: OperatingCostCalculationRequest,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """
    Calculate operating costs using driver-based models.

    Args:
        version_id: Budget version UUID
        calculation_request: Calculation parameters with driver rates
        cost_service: Cost service
        user: Current authenticated user

    Returns:
        Operating cost calculation results
    """
    try:
        result = await cost_service.calculate_operating_costs(
            version_id=version_id,
            cost_drivers=calculation_request.driver_rates,
            user_id=user.id,
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/costs/operating/{version_id}", response_model=OperatingCostPlanResponse)
async def create_operating_cost_entry(
    version_id: uuid.UUID,
    cost_data: OperatingCostPlanCreate,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """
    Create or update operating cost plan entry.

    Args:
        version_id: Budget version UUID
        cost_data: Operating cost plan data
        cost_service: Cost service
        user: Current authenticated user

    Returns:
        Created/updated operating cost plan entry
    """
    try:
        entry = await cost_service.create_operating_cost_entry(
            version_id=version_id,
            account_code=cost_data.account_code,
            description=cost_data.description,
            category=cost_data.category,
            amount_sar=cost_data.amount_sar,
            is_calculated=cost_data.is_calculated,
            calculation_driver=cost_data.calculation_driver,
            notes=cost_data.notes,
            user_id=user.id,
        )
        return entry
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/{version_id}/summary")
async def get_cost_summary(
    version_id: uuid.UUID,
    cost_service: CostService = Depends(get_cost_service),
    user: UserDep = ...,
):
    """
    Get cost summary for a budget version.

    Args:
        version_id: Budget version UUID
        cost_service: Cost service
        user: Current authenticated user

    Returns:
        Cost summary statistics (personnel + operating)
    """
    try:
        summary = await cost_service.get_cost_summary(version_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# CapEx Planning Endpoints
# ==============================================================================


@router.get("/capex/{version_id}", response_model=list[CapExPlanResponse])
async def get_capex_plan(
    version_id: uuid.UUID,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """
    Get CapEx plan for a budget version.

    Args:
        version_id: Budget version UUID
        capex_service: CapEx service
        user: Current authenticated user

    Returns:
        List of CapEx plan entries
    """
    try:
        capex_plan = await capex_service.get_capex_plan(version_id)
        return capex_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capex/{version_id}", response_model=CapExPlanResponse)
async def create_capex_entry(
    version_id: uuid.UUID,
    capex_data: CapExPlanCreate,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """
    Create CapEx plan entry.

    Args:
        version_id: Budget version UUID
        capex_data: CapEx plan data
        capex_service: CapEx service
        user: Current authenticated user

    Returns:
        Created CapEx plan entry
    """
    try:
        entry = await capex_service.create_capex_entry(
            version_id=version_id,
            account_code=capex_data.account_code,
            description=capex_data.description,
            category=capex_data.category,
            quantity=capex_data.quantity,
            unit_cost_sar=capex_data.unit_cost_sar,
            acquisition_date=capex_data.acquisition_date,
            useful_life_years=capex_data.useful_life_years,
            notes=capex_data.notes,
            user_id=user.id,
        )
        return entry
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/capex/{version_id}/{capex_id}", response_model=CapExPlanResponse)
async def update_capex_entry(
    version_id: uuid.UUID,
    capex_id: uuid.UUID,
    capex_data: CapExPlanUpdate,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """
    Update CapEx plan entry.

    Args:
        version_id: Budget version UUID
        capex_id: CapEx entry UUID
        capex_data: Updated CapEx plan data
        capex_service: CapEx service
        user: Current authenticated user

    Returns:
        Updated CapEx plan entry
    """
    try:
        entry = await capex_service.update_capex_entry(
            capex_id=capex_id,
            account_code=capex_data.account_code,
            description=capex_data.description,
            category=capex_data.category,
            quantity=capex_data.quantity,
            unit_cost_sar=capex_data.unit_cost_sar,
            acquisition_date=capex_data.acquisition_date,
            useful_life_years=capex_data.useful_life_years,
            notes=capex_data.notes,
            user_id=user.id,
        )
        return entry
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/capex/{version_id}/{capex_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_capex_entry(
    version_id: uuid.UUID,
    capex_id: uuid.UUID,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """
    Delete CapEx plan entry.

    Args:
        version_id: Budget version UUID
        capex_id: CapEx entry UUID
        capex_service: CapEx service
        user: Current authenticated user

    Returns:
        No content (204)
    """
    try:
        await capex_service.delete_capex_entry(capex_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capex/{capex_id}/depreciation", response_model=DepreciationCalculationResponse)
async def calculate_depreciation(
    capex_id: uuid.UUID,
    depreciation_request: DepreciationCalculationRequest,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """
    Calculate depreciation for a CapEx asset.

    Args:
        capex_id: CapEx entry UUID
        depreciation_request: Depreciation calculation parameters
        capex_service: CapEx service
        user: Current authenticated user

    Returns:
        Depreciation calculation results
    """
    try:
        result = await capex_service.calculate_depreciation(
            capex_id=capex_id,
            calculation_year=depreciation_request.calculation_year,
        )
        return DepreciationCalculationResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capex/{capex_id}/depreciation-schedule")
async def get_depreciation_schedule(
    capex_id: uuid.UUID,
    years_ahead: int = Query(10, ge=1, le=50, description="Number of years to project"),
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """
    Get multi-year depreciation schedule for an asset.

    Args:
        capex_id: CapEx entry UUID
        years_ahead: Number of years to project
        capex_service: CapEx service
        user: Current authenticated user

    Returns:
        Depreciation schedule (list of yearly calculations)
    """
    try:
        schedule = await capex_service.get_depreciation_schedule(
            capex_id=capex_id,
            years_ahead=years_ahead,
        )
        return schedule
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capex/{version_id}/summary")
async def get_capex_summary(
    version_id: uuid.UUID,
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """
    Get CapEx summary for a budget version.

    Args:
        version_id: Budget version UUID
        capex_service: CapEx service
        user: Current authenticated user

    Returns:
        CapEx summary statistics
    """
    try:
        summary = await capex_service.get_capex_summary(version_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capex/{version_id}/depreciation/{year}")
async def get_annual_depreciation(
    version_id: uuid.UUID,
    year: int = Path(..., ge=2020, le=2100, description="Calculation year"),
    capex_service: CapExService = Depends(get_capex_service),
    user: UserDep = ...,
):
    """
    Get total annual depreciation for all assets in a version.

    Args:
        version_id: Budget version UUID
        year: Calculation year
        capex_service: CapEx service
        user: Current authenticated user

    Returns:
        Annual depreciation totals
    """
    try:
        result = await capex_service.get_annual_depreciation(
            version_id=version_id,
            calculation_year=year,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
