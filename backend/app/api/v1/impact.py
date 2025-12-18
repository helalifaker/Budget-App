"""
Impact Calculation API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.insights.impact import (
    ImpactCalculationRequest,
    ImpactCalculationResponse,
)
from app.services.exceptions import (
    NotFoundError,
    ValidationError,
)
from app.services.insights.impact_calculator_service import (
    ImpactCalculatorService,
    ProposedChange,
)

router = APIRouter(prefix="/impact", tags=["Impact Analysis"])


def get_impact_calculator_service(
    db: AsyncSession = Depends(get_db),
) -> ImpactCalculatorService:
    """
    Dependency to get impact calculator service instance.

    Args:
        db: Database session

    Returns:
        ImpactCalculatorService instance
    """
    return ImpactCalculatorService(db)


@router.post(
    "/{version_id}",
    response_model=ImpactCalculationResponse,
    summary="Calculate impact of proposed change",
)
async def calculate_impact(
    version_id: uuid.UUID,
    request: ImpactCalculationRequest,
    impact_service: ImpactCalculatorService = Depends(get_impact_calculator_service),
    user: UserDep = ...,
):
    """
    Calculate the real-time impact of a proposed budget change.

    This endpoint allows users to preview the cascading effects of a change
    before actually saving it. It calculates:
    - FTE impact (change in teacher Full-Time Equivalents)
    - Cost impact (change in total costs)
    - Revenue impact (change in total revenue)
    - Margin impact (change in operating margin %)

    The calculation is a preview only - no database changes are made.

    Args:
        version_id: Budget version UUID
        request: Proposed change details
        impact_service: Impact calculator service
        user: Current authenticated user

    Returns:
        PlanningImpactResponse with all calculated metrics
    """
    try:
        # Convert request to service model
        proposed_change = ProposedChange(
            step_id=request.step_id,
            dimension_type=request.dimension_type,
            dimension_id=request.dimension_id,
            dimension_code=request.dimension_code,
            field_name=request.field_name,
            new_value=request.new_value,
        )

        # Calculate impact
        impact_metrics = await impact_service.calculate_impact(
            version_id=version_id,
            proposed_change=proposed_change,
        )

        # Return response
        return ImpactCalculationResponse(
            fte_change=impact_metrics.fte_change,
            fte_current=impact_metrics.fte_current,
            fte_proposed=impact_metrics.fte_proposed,
            cost_impact_sar=impact_metrics.cost_impact_sar,
            cost_current_sar=impact_metrics.cost_current_sar,
            cost_proposed_sar=impact_metrics.cost_proposed_sar,
            revenue_impact_sar=impact_metrics.revenue_impact_sar,
            revenue_current_sar=impact_metrics.revenue_current_sar,
            revenue_proposed_sar=impact_metrics.revenue_proposed_sar,
            margin_impact_pct=impact_metrics.margin_impact_pct,
            margin_current_pct=impact_metrics.margin_current_pct,
            margin_proposed_pct=impact_metrics.margin_proposed_pct,
            affected_steps=impact_metrics.affected_steps,
        )
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
