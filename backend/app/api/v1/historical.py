"""
Historical Comparison API Router

Provides endpoints for fetching planning data with historical actuals
for comparison (N-2, N-1, Current).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.historical import (
    CapExWithHistoryResponse,
    ClassStructureWithHistoryResponse,
    CostsWithHistoryResponse,
    DHGWithHistoryResponse,
    EnrollmentWithHistoryResponse,
    RevenueWithHistoryResponse,
)
from app.services.historical_comparison_service import HistoricalComparisonService

router = APIRouter(prefix="/api/v1/historical", tags=["Historical Comparison"])


# =============================================================================
# Enrollment with History
# =============================================================================


@router.get(
    "/enrollment/{budget_version_id}",
    response_model=EnrollmentWithHistoryResponse,
    summary="Get enrollment with historical comparison",
    description=(
        "Retrieve enrollment data by level with 2 years of historical actuals. "
        "Shows N-2, N-1 actual values alongside current plan with variance calculations."
    ),
)
async def get_enrollment_with_history(
    budget_version_id: UUID,
    history_years: int = Query(2, ge=1, le=5, description="Number of historical years"),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentWithHistoryResponse:
    """Get enrollment data with historical comparison."""
    service = HistoricalComparisonService(db)

    try:
        data = await service.get_enrollment_with_history(
            budget_version_id=budget_version_id,
            history_years=history_years,
        )
        return EnrollmentWithHistoryResponse(**data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# Class Structure with History
# =============================================================================


@router.get(
    "/classes/{budget_version_id}",
    response_model=ClassStructureWithHistoryResponse,
    summary="Get class structure with historical comparison",
    description=(
        "Retrieve class structure data by level with historical actuals. "
        "Shows class counts from N-2 and N-1 alongside current plan."
    ),
)
async def get_classes_with_history(
    budget_version_id: UUID,
    history_years: int = Query(2, ge=1, le=5, description="Number of historical years"),
    db: AsyncSession = Depends(get_db),
) -> ClassStructureWithHistoryResponse:
    """Get class structure data with historical comparison."""
    service = HistoricalComparisonService(db)

    # Note: Class structure historical comparison uses the same enrollment service
    # but returns class counts instead of student counts
    try:
        # For now, return a stub response
        # In full implementation, would query ClassStructure model
        fiscal_year = await service.get_budget_version_fiscal_year(budget_version_id)
        if not fiscal_year:
            raise ValueError(f"Budget version {budget_version_id} not found")

        return ClassStructureWithHistoryResponse(
            budget_version_id=budget_version_id,
            fiscal_year=fiscal_year,
            current_fiscal_year=fiscal_year,
            rows=[],
            totals=service.build_comparison(0, None, fiscal_year),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# DHG with History
# =============================================================================


@router.get(
    "/dhg/{budget_version_id}",
    response_model=DHGWithHistoryResponse,
    summary="Get DHG with historical comparison",
    description=(
        "Retrieve DHG workforce data by subject with historical actuals. "
        "Shows teacher hours and FTE from N-2 and N-1 alongside current plan."
    ),
)
async def get_dhg_with_history(
    budget_version_id: UUID,
    history_years: int = Query(2, ge=1, le=5, description="Number of historical years"),
    db: AsyncSession = Depends(get_db),
) -> DHGWithHistoryResponse:
    """Get DHG data with historical comparison."""
    service = HistoricalComparisonService(db)

    try:
        data = await service.get_dhg_with_history(
            budget_version_id=budget_version_id,
            history_years=history_years,
        )
        return DHGWithHistoryResponse(**data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# Revenue with History
# =============================================================================


@router.get(
    "/revenue/{budget_version_id}",
    response_model=RevenueWithHistoryResponse,
    summary="Get revenue with historical comparison",
    description=(
        "Retrieve revenue data by account code with historical actuals. "
        "Shows revenue amounts from N-2 and N-1 alongside current plan."
    ),
)
async def get_revenue_with_history(
    budget_version_id: UUID,
    history_years: int = Query(2, ge=1, le=5, description="Number of historical years"),
    db: AsyncSession = Depends(get_db),
) -> RevenueWithHistoryResponse:
    """Get revenue data with historical comparison."""
    service = HistoricalComparisonService(db)

    try:
        data = await service.get_revenue_with_history(
            budget_version_id=budget_version_id,
            history_years=history_years,
        )
        return RevenueWithHistoryResponse(**data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# Costs with History
# =============================================================================


@router.get(
    "/costs/{budget_version_id}",
    response_model=CostsWithHistoryResponse,
    summary="Get costs with historical comparison",
    description=(
        "Retrieve cost data by account code with historical actuals. "
        "Shows personnel and operating costs from N-2 and N-1 alongside current plan."
    ),
)
async def get_costs_with_history(
    budget_version_id: UUID,
    history_years: int = Query(2, ge=1, le=5, description="Number of historical years"),
    db: AsyncSession = Depends(get_db),
) -> CostsWithHistoryResponse:
    """Get costs data with historical comparison."""
    service = HistoricalComparisonService(db)

    try:
        data = await service.get_costs_with_history(
            budget_version_id=budget_version_id,
            history_years=history_years,
        )
        return CostsWithHistoryResponse(**data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# CapEx with History
# =============================================================================


@router.get(
    "/capex/{budget_version_id}",
    response_model=CapExWithHistoryResponse,
    summary="Get CapEx with historical comparison",
    description=(
        "Retrieve CapEx data by account code with historical actuals. "
        "Shows capital expenditure amounts from N-2 and N-1 alongside current plan."
    ),
)
async def get_capex_with_history(
    budget_version_id: UUID,
    history_years: int = Query(2, ge=1, le=5, description="Number of historical years"),
    db: AsyncSession = Depends(get_db),
) -> CapExWithHistoryResponse:
    """Get CapEx data with historical comparison."""
    service = HistoricalComparisonService(db)

    try:
        data = await service.get_capex_with_history(
            budget_version_id=budget_version_id,
            history_years=history_years,
        )
        return CapExWithHistoryResponse(**data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
