"""
Strategic Planning API endpoints.

Provides REST API for Module 18: 5-Year Strategic Planning.
- Strategic plans CRUD
- Scenario management
- Year-over-year projections
- Strategic initiative tracking

Path prefix: /api/v1/strategic
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies.auth import UserDep
from app.models.strategic import (
    ProjectionCategory,
    StrategicPlan,
    StrategicPlanScenario,
)
from app.services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from app.services.strategic_service import StrategicService

router = APIRouter(prefix="/api/v1/strategic", tags=["strategic"])


# ============================================================================
# Request/Response Schemas (matching frontend expectations)
# ============================================================================


class StrategicScenarioDTO(BaseModel):
    """Strategic scenario DTO matching frontend schema."""

    id: str
    name: str
    description: str
    enrollment_growth_rate: float
    fee_increase_rate: float
    salary_inflation_rate: float
    operating_growth_rate: float  # Maps from operating_inflation_rate


class StrategicPlanDTO(BaseModel):
    """Strategic plan DTO matching frontend schema."""

    id: str
    name: str
    base_version_id: str
    base_year: int
    years_count: int
    scenarios: list[StrategicScenarioDTO]
    created_at: str
    updated_at: str


class StrategicProjectionDTO(BaseModel):
    """Strategic projection DTO matching frontend schema."""

    year: int
    students: int
    classes: int
    teachers: float
    revenue: float
    personnel_costs: float
    operating_costs: float
    net_income: float
    operating_margin: float


class CreatePlanRequest(BaseModel):
    """Request to create a strategic plan."""

    name: str = Field(..., max_length=200, description="Plan name")
    base_version_id: str = Field(..., description="Base budget version UUID")
    years_count: int = Field(5, ge=1, le=5, description="Number of years")


class UpdateAssumptionsRequest(BaseModel):
    """Request to update scenario assumptions."""

    scenario_id: str = Field(..., description="Scenario UUID")
    enrollment_growth_rate: float = Field(..., ge=-0.50, le=1.00)
    fee_increase_rate: float = Field(..., ge=-0.20, le=0.50)
    salary_inflation_rate: float = Field(..., ge=-0.20, le=0.50)
    operating_growth_rate: float = Field(..., ge=-0.20, le=0.50)


class DeleteResponse(BaseModel):
    """Response for delete operations."""

    success: bool


# ============================================================================
# Service Dependency
# ============================================================================


def get_strategic_service(db: AsyncSession = Depends(get_db)) -> StrategicService:
    """Get strategic service instance."""
    return StrategicService(db)


# ============================================================================
# Helper Functions
# ============================================================================


def _scenario_to_dto(scenario: StrategicPlanScenario) -> StrategicScenarioDTO:
    """Convert SQLAlchemy scenario to DTO."""
    return StrategicScenarioDTO(
        id=str(scenario.id),
        name=scenario.name,
        description=scenario.description or "",
        enrollment_growth_rate=float(scenario.enrollment_growth_rate),
        fee_increase_rate=float(scenario.fee_increase_rate),
        salary_inflation_rate=float(scenario.salary_inflation_rate),
        operating_growth_rate=float(scenario.operating_inflation_rate),  # Note: mapped name
    )


def _plan_to_dto(plan: StrategicPlan) -> StrategicPlanDTO:
    """Convert SQLAlchemy plan to DTO."""
    # Extract base_version_id from first scenario's additional_assumptions
    base_version_id = ""
    years_count = 5
    if plan.scenarios:
        assumptions = plan.scenarios[0].additional_assumptions or {}
        base_version_id = str(assumptions.get("base_version_id", ""))
        years_count = int(assumptions.get("projection_years", 5))

    return StrategicPlanDTO(
        id=str(plan.id),
        name=plan.name,
        base_version_id=base_version_id,
        base_year=plan.base_year,
        years_count=years_count,
        scenarios=[_scenario_to_dto(s) for s in plan.scenarios],
        created_at=plan.created_at.isoformat() if plan.created_at else datetime.utcnow().isoformat(),
        updated_at=plan.updated_at.isoformat() if plan.updated_at else datetime.utcnow().isoformat(),
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/plans",
    response_model=list[StrategicPlanDTO],
)
async def get_plans(
    current_user: UserDep = None,
    db: AsyncSession = Depends(get_db),
) -> list[StrategicPlanDTO]:
    """
    Get all strategic plans.

    Returns a list of all active strategic plans with their scenarios.
    """
    query = (
        select(StrategicPlan)
        .where(StrategicPlan.deleted_at.is_(None))
        .options(
            selectinload(StrategicPlan.scenarios),
            selectinload(StrategicPlan.initiatives),
        )
        .order_by(StrategicPlan.created_at.desc())
    )

    result = await db.execute(query)
    plans = result.scalars().all()

    return [_plan_to_dto(plan) for plan in plans]


@router.get(
    "/plans/{plan_id}",
    response_model=StrategicPlanDTO,
)
async def get_plan(
    plan_id: str,
    current_user: UserDep = None,
    strategic_service: StrategicService = Depends(get_strategic_service),
) -> StrategicPlanDTO:
    """
    Get a specific strategic plan by ID.

    Returns the plan with all scenarios and their projections.
    """
    try:
        plan_uuid = uuid.UUID(plan_id)
        plan = await strategic_service.get_strategic_plan(plan_uuid)
        return _plan_to_dto(plan)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan ID format: {plan_id}",
        ) from e
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/plans",
    response_model=StrategicPlanDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    request: CreatePlanRequest,
    current_user: UserDep = None,
    strategic_service: StrategicService = Depends(get_strategic_service),
    db: AsyncSession = Depends(get_db),
) -> StrategicPlanDTO:
    """
    Create a new strategic plan.

    Creates a 5-year strategic plan based on a budget version,
    automatically generating default scenarios (conservative, base case, optimistic).
    """
    try:
        base_version_uuid = uuid.UUID(request.base_version_id)
        plan = await strategic_service.create_strategic_plan(
            base_version_id=base_version_uuid,
            plan_name=request.name,
            description=None,
            years=request.years_count,
            create_default_scenarios=True,
        )
        await db.commit()
        await db.refresh(plan)

        # Reload with relationships
        refreshed_plan = await strategic_service.get_strategic_plan(plan.id)
        return _plan_to_dto(refreshed_plan)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid base version ID format: {request.base_version_id}",
        ) from e
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put(
    "/plans/{plan_id}/scenarios/{scenario_id}",
    response_model=StrategicScenarioDTO,
)
async def update_scenario_assumptions(
    plan_id: str,
    scenario_id: str,
    request: UpdateAssumptionsRequest,
    current_user: UserDep = None,
    strategic_service: StrategicService = Depends(get_strategic_service),
    db: AsyncSession = Depends(get_db),
) -> StrategicScenarioDTO:
    """
    Update scenario growth assumptions.

    Updates the growth rates for a scenario and recalculates projections.
    """
    try:
        scenario_uuid = uuid.UUID(scenario_id)
        scenario = await strategic_service.update_assumptions(
            scenario_id=scenario_uuid,
            enrollment_growth_rate=Decimal(str(request.enrollment_growth_rate)),
            fee_increase_rate=Decimal(str(request.fee_increase_rate)),
            salary_inflation_rate=Decimal(str(request.salary_inflation_rate)),
            operating_inflation_rate=Decimal(str(request.operating_growth_rate)),
            recalculate_projections=True,
        )
        await db.commit()
        await db.refresh(scenario)

        return _scenario_to_dto(scenario)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario ID format: {scenario_id}",
        ) from e
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "/plans/{plan_id}/scenarios/{scenario_id}/projections",
    response_model=list[StrategicProjectionDTO],
)
async def get_projections(
    plan_id: str,
    scenario_id: str,
    current_user: UserDep = None,
    db: AsyncSession = Depends(get_db),
) -> list[StrategicProjectionDTO]:
    """
    Get projections for a scenario.

    Returns year-by-year financial projections for a specific scenario.
    """
    try:
        scenario_uuid = uuid.UUID(scenario_id)

        # Get scenario with projections
        query = (
            select(StrategicPlanScenario)
            .where(
                and_(
                    StrategicPlanScenario.id == scenario_uuid,
                    StrategicPlanScenario.deleted_at.is_(None),
                )
            )
            .options(selectinload(StrategicPlanScenario.projections))
        )

        result = await db.execute(query)
        scenario = result.scalar_one_or_none()

        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        # Build projection DTOs by year
        projections_by_year: dict[int, dict[str, Any]] = {}
        for projection in scenario.projections:
            year = projection.year
            if year not in projections_by_year:
                projections_by_year[year] = {
                    "year": year,
                    "students": 0,
                    "classes": 0,
                    "teachers": 0.0,
                    "revenue": 0.0,
                    "personnel_costs": 0.0,
                    "operating_costs": 0.0,
                    "net_income": 0.0,
                    "operating_margin": 0.0,
                }

            # Map category to field
            if projection.category == ProjectionCategory.REVENUE:
                projections_by_year[year]["revenue"] = float(projection.amount_sar)
            elif projection.category == ProjectionCategory.PERSONNEL_COSTS:
                projections_by_year[year]["personnel_costs"] = float(projection.amount_sar)
            elif projection.category == ProjectionCategory.OPERATING_COSTS:
                projections_by_year[year]["operating_costs"] = float(projection.amount_sar)

        # Calculate derived fields (net_income, operating_margin)
        projection_list: list[StrategicProjectionDTO] = []
        for year in sorted(projections_by_year.keys()):
            data = projections_by_year[year]
            total_costs = data["personnel_costs"] + data["operating_costs"]
            data["net_income"] = data["revenue"] - total_costs
            data["operating_margin"] = (
                (data["net_income"] / data["revenue"] * 100) if data["revenue"] > 0 else 0.0
            )
            projection_list.append(StrategicProjectionDTO(**data))

        return projection_list
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario ID format: {scenario_id}",
        ) from e


@router.delete(
    "/plans/{plan_id}",
    response_model=DeleteResponse,
)
async def delete_plan(
    plan_id: str,
    current_user: UserDep = None,
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """
    Delete a strategic plan.

    Soft-deletes the plan (sets deleted_at timestamp).
    """
    try:
        plan_uuid = uuid.UUID(plan_id)

        # Get the plan
        query = select(StrategicPlan).where(
            and_(
                StrategicPlan.id == plan_uuid,
                StrategicPlan.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategic plan {plan_id} not found",
            )

        # Soft delete
        plan.deleted_at = datetime.utcnow()
        await db.commit()

        return DeleteResponse(success=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan ID format: {plan_id}",
        ) from e
