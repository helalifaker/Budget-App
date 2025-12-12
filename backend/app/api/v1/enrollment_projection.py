"""
Enrollment Projection API Routes (Module 7 upgrade).

Endpoints for managing enrollment projections with 4-layer override architecture.
Mounted under /api/v1/planning/enrollment-projection.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.enrollment_projection import (
    GlobalOverridesUpdate,
    GradeOverridesUpdate,
    LevelOverridesUpdate,
    ProjectionConfigResponse,
    ProjectionConfigUpdate,
    ProjectionResultsResponse,
    ScenarioListResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.enrollment_projection_service import EnrollmentProjectionService
from app.services.exceptions import ServiceException

router = APIRouter(prefix="/enrollment-projection", tags=["Enrollment Projection"])


def get_service(db: AsyncSession = Depends(get_db)) -> EnrollmentProjectionService:
    return EnrollmentProjectionService(db)


@router.get("/scenarios", response_model=ScenarioListResponse)
async def get_scenarios(service: EnrollmentProjectionService = Depends(get_service)):
    scenarios = await service.get_all_scenarios()
    return {"scenarios": scenarios}


@router.get("/{version_id}/config", response_model=ProjectionConfigResponse)
async def get_projection_config(
    version_id: uuid.UUID,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        return await service.get_or_create_config(version_id)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{version_id}/config", response_model=ProjectionConfigResponse)
async def update_projection_config(
    version_id: uuid.UUID,
    updates: ProjectionConfigUpdate,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        return await service.update_config(version_id, updates.model_dump(exclude_unset=True))
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{version_id}/global-overrides", response_model=ProjectionConfigResponse)
async def update_global_overrides(
    version_id: uuid.UUID,
    overrides: GlobalOverridesUpdate,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        return await service.update_global_overrides(
            version_id, overrides.model_dump(exclude_unset=True)
        )
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{version_id}/level-overrides", response_model=ProjectionConfigResponse)
async def update_level_overrides(
    version_id: uuid.UUID,
    overrides: LevelOverridesUpdate,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        items = [o.model_dump() for o in overrides.overrides]
        return await service.update_level_overrides(version_id, items)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{version_id}/grade-overrides", response_model=ProjectionConfigResponse)
async def update_grade_overrides(
    version_id: uuid.UUID,
    overrides: GradeOverridesUpdate,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        items = [o.model_dump() for o in overrides.overrides]
        return await service.update_grade_overrides(version_id, items)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{version_id}/results", response_model=ProjectionResultsResponse)
async def get_projection_results(
    version_id: uuid.UUID,
    include_fiscal_proration: bool = True,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        payload = await service.get_projection_results(version_id, include_fiscal_proration)
        return ProjectionResultsResponse(**payload)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{version_id}/calculate", response_model=ProjectionResultsResponse)
async def calculate_projection(
    version_id: uuid.UUID,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        await service.calculate_and_save(version_id)
        payload = await service.get_projection_results(version_id, include_fiscal_proration=True)
        return ProjectionResultsResponse(**payload)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{version_id}/validate", response_model=ValidationResponse)
async def validate_projection(
    version_id: uuid.UUID,
    request: ValidationRequest,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        result = await service.validate_and_cascade(
            version_id, user.user_id, request.confirmation
        )
        return ValidationResponse(**result)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{version_id}/unvalidate", response_model=ProjectionConfigResponse)
async def unvalidate_projection(
    version_id: uuid.UUID,
    service: EnrollmentProjectionService = Depends(get_service),
    user: UserDep = ...,
):
    try:
        return await service.unvalidate(version_id, user.user_id)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
