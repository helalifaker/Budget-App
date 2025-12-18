"""
DHG Workforce Planning API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.workforce.dhg import (
    DHGSubjectHoursResponse,
    DHGSubjectHoursUpdate,
    DHGHoursCalculationRequest,
    DHGTeacherRequirementResponse,
    FTECalculationRequest,
    TeacherAllocationResponse,
    TeacherAllocationCreate,
    TeacherAllocationUpdate,
    TeacherAllocationBulkUpdate,
    TRMDGapAnalysisResponse,
)
from app.services.workforce.dhg_service import DHGService
from app.services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/dhg", tags=["DHG Workforce"])


def get_dhg_service(db: AsyncSession = Depends(get_db)) -> DHGService:
    """
    Dependency to get DHG service instance.

    Args:
        db: Database session

    Returns:
        DHGService instance
    """
    return DHGService(db)


# ==============================================================================
# DHG Subject Hours Endpoints
# ==============================================================================


@router.get(
    "/subject-hours/{version_id}",
    response_model=list[DHGSubjectHoursResponse],
)
async def get_dhg_subject_hours(
    version_id: uuid.UUID,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Get DHG subject hours for a budget version.

    Args:
        version_id: Budget version UUID
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        List of DHG subject hours
    """
    try:
        subject_hours = await dhg_service.get_dhg_subject_hours(version_id)
        return subject_hours
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/subject-hours/{version_id}/calculate",
    response_model=list[DHGSubjectHoursResponse],
)
async def calculate_dhg_hours(
    version_id: uuid.UUID,
    calculation_request: DHGHoursCalculationRequest,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Calculate and initialize DHG subject hours from class structure.

    Args:
        version_id: Budget version UUID
        calculation_request: Calculation parameters
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        List of calculated subject hours
    """
    try:
        subject_hours = await dhg_service.calculate_dhg_hours(
            version_id=version_id,
            recalculate_all=calculation_request.recalculate_all,
            user_id=user.user_id,
        )
        return subject_hours
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# DHG Teacher Requirements Endpoints
# ==============================================================================


@router.get(
    "/teacher-requirements/{version_id}",
    response_model=list[DHGTeacherRequirementResponse],
)
async def get_teacher_requirements(
    version_id: uuid.UUID,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Get teacher FTE requirements for a budget version.

    Args:
        version_id: Budget version UUID
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        List of teacher requirements
    """
    try:
        requirements = await dhg_service.get_teacher_requirements(version_id)
        return requirements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/teacher-requirements/{version_id}/calculate",
    response_model=list[DHGTeacherRequirementResponse],
)
async def calculate_teacher_requirements(
    version_id: uuid.UUID,
    calculation_request: FTECalculationRequest,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Calculate teacher FTE requirements from DHG subject hours.

    Args:
        version_id: Budget version UUID
        calculation_request: Calculation parameters
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        List of calculated teacher FTE requirements
    """
    try:
        requirements = await dhg_service.calculate_teacher_requirements(
            version_id=version_id,
            recalculate_all=calculation_request.recalculate_all,
            user_id=user.user_id,
        )
        return requirements
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# Teacher Allocations Endpoints
# ==============================================================================


@router.get(
    "/allocations/{version_id}",
    response_model=list[TeacherAllocationResponse],
)
async def get_teacher_allocations(
    version_id: uuid.UUID,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Get teacher allocations for a budget version.

    Args:
        version_id: Budget version UUID
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        List of teacher allocations
    """
    try:
        allocations = await dhg_service.get_teacher_allocations(version_id)
        return allocations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/allocations/{version_id}",
    response_model=TeacherAllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_teacher_allocation(
    version_id: uuid.UUID,
    allocation_data: TeacherAllocationCreate,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Create teacher allocation entry.

    Args:
        version_id: Budget version UUID
        allocation_data: Allocation data
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        Created teacher allocation entry
    """
    try:
        allocation = await dhg_service.create_teacher_allocation(
            version_id=version_id,
            subject_id=allocation_data.subject_id,
            cycle_id=allocation_data.cycle_id,
            category_id=allocation_data.category_id,
            fte_count=allocation_data.fte_count,
            notes=allocation_data.notes,
            user_id=user.user_id,
        )
        return allocation
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put(
    "/allocations/{allocation_id}",
    response_model=TeacherAllocationResponse,
)
async def update_teacher_allocation(
    allocation_id: uuid.UUID,
    allocation_data: TeacherAllocationUpdate,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Update teacher allocation entry.

    Args:
        allocation_id: Teacher allocation UUID
        allocation_data: Updated allocation data
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        Updated teacher allocation entry
    """
    try:
        allocation = await dhg_service.update_teacher_allocation(
            allocation_id=allocation_id,
            fte_count=allocation_data.fte_count,
            notes=allocation_data.notes,
            user_id=user.user_id,
        )
        return allocation
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.api_route(
    "/allocations/{version_id}/bulk",
    methods=["POST", "PUT"],
    response_model=list[TeacherAllocationResponse],
)
async def bulk_update_teacher_allocations(
    version_id: uuid.UUID,
    bulk_data: TeacherAllocationBulkUpdate,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Bulk create/update teacher allocations.

    Args:
        version_id: Budget version UUID
        bulk_data: Bulk allocation data
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        List of created/updated teacher allocations
    """
    try:
        allocations_dict = [
            {
                "subject_id": a.subject_id,
                "cycle_id": a.cycle_id,
                "category_id": a.category_id,
                "fte_count": a.fte_count,
                "notes": a.notes,
            }
            for a in bulk_data.allocations
        ]
        allocations = await dhg_service.bulk_update_allocations(
            version_id=version_id,
            allocations=allocations_dict,
            user_id=user.user_id,
        )
        return allocations
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/allocations/{allocation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_teacher_allocation(
    allocation_id: uuid.UUID,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Delete teacher allocation entry.

    Args:
        allocation_id: Teacher allocation UUID
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        No content
    """
    try:
        await dhg_service.delete_teacher_allocation(allocation_id, user_id=user.user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# DHG Draft/Apply BFF Endpoints (Performance Pattern)
# ==============================================================================


@router.post(
    "/{version_id}/draft",
    response_model=list[TeacherAllocationResponse],
)
async def save_dhg_draft(
    version_id: uuid.UUID,
    bulk_data: TeacherAllocationBulkUpdate,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Save DHG allocation changes as a draft without recalculating FTE.

    This endpoint saves allocation changes quickly for auto-save functionality.
    Use /apply to commit changes and recalculate teacher requirements.

    Args:
        version_id: Budget version UUID
        bulk_data: Allocation changes to save
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        List of saved teacher allocations
    """
    try:
        allocations_dict = [
            {
                "subject_id": a.subject_id,
                "cycle_id": a.cycle_id,
                "category_id": a.category_id,
                "fte_count": a.fte_count,
                "notes": a.notes,
            }
            for a in bulk_data.allocations
        ]
        allocations = await dhg_service.bulk_update_allocations(
            version_id=version_id,
            allocations=allocations_dict,
            user_id=user.user_id,
        )
        return allocations
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{version_id}/apply",
    response_model=TRMDGapAnalysisResponse,
)
async def apply_dhg_and_calculate(
    version_id: uuid.UUID,
    bulk_data: TeacherAllocationBulkUpdate | None = None,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Apply DHG allocation changes and run full FTE calculation (BFF endpoint).

    This combines:
    1. Save any pending allocation changes
    2. Recalculate teacher requirements (FTE)
    3. Update TRMD gap analysis
    4. Return updated gap analysis

    Args:
        version_id: Budget version UUID
        bulk_data: Optional final allocation changes
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        Updated TRMD gap analysis with recalculated data
    """
    try:
        # Step 1: Save any pending allocation changes
        if bulk_data and bulk_data.allocations:
            allocations_dict = [
                {
                    "subject_id": a.subject_id,
                    "cycle_id": a.cycle_id,
                    "category_id": a.category_id,
                    "fte_count": a.fte_count,
                    "notes": a.notes,
                }
                for a in bulk_data.allocations
            ]
            await dhg_service.bulk_update_allocations(
                version_id=version_id,
                allocations=allocations_dict,
                user_id=user.user_id,
            )

        # Step 2: Recalculate teacher requirements
        await dhg_service.calculate_teacher_requirements(
            version_id=version_id,
            recalculate_all=True,
            user_id=user.user_id,
        )

        # Step 3: Return updated TRMD gap analysis
        analysis = await dhg_service.get_trmd_gap_analysis(version_id)
        return analysis
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# TRMD Gap Analysis Endpoint
# ==============================================================================


@router.get(
    "/trmd/{version_id}",
    response_model=TRMDGapAnalysisResponse,
)
async def get_trmd_gap_analysis(
    version_id: uuid.UUID,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Get TRMD gap analysis (besoins vs moyens).

    Args:
        version_id: Budget version UUID
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        TRMD gap analysis with deficit breakdown
    """
    try:
        analysis = await dhg_service.get_trmd_gap_analysis(version_id)
        return analysis
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
