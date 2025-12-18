"""
Class Structure API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.enrollment.class_structure import (
    ClassStructureCalculationRequest,
    ClassStructureResponse,
    ClassStructureUpdate,
    ClassStructureBulkUpdate,
)
from app.services.enrollment.class_structure_service import ClassStructureService
from app.services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/class-structure", tags=["Class Structure"])


def get_class_structure_service(
    db: AsyncSession = Depends(get_db),
) -> ClassStructureService:
    """
    Dependency to get class structure service instance.

    Args:
        db: Database session

    Returns:
        ClassStructureService instance
    """
    return ClassStructureService(db)


@router.get(
    "/{version_id}",
    response_model=list[ClassStructureResponse],
)
async def get_class_structure(
    version_id: uuid.UUID,
    class_structure_service: ClassStructureService = Depends(
        get_class_structure_service
    ),
    user: UserDep = ...,
):
    """
    Get class structure for a budget version.

    Args:
        version_id: Budget version UUID
        class_structure_service: Class structure service
        user: Current authenticated user

    Returns:
        List of class structure entries
    """
    try:
        class_structures = await class_structure_service.get_class_structure(
            version_id
        )
        return class_structures
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{version_id}/calculate",
    response_model=list[ClassStructureResponse],
)
async def calculate_class_structure(
    version_id: uuid.UUID,
    calculation_request: ClassStructureCalculationRequest,
    class_structure_service: ClassStructureService = Depends(
        get_class_structure_service
    ),
    user: UserDep = ...,
):
    """
    Calculate class structures from enrollment data.

    Args:
        version_id: Budget version UUID
        calculation_request: Calculation parameters
        class_structure_service: Class structure service
        user: Current authenticated user

    Returns:
        List of calculated class structure entries
    """
    try:
        class_structures = await class_structure_service.calculate_class_structure(
            version_id=version_id,
            method=calculation_request.method,
            override_by_level=calculation_request.override_by_level,
            user_id=user.user_id,
        )
        return class_structures
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put(
    "/{class_structure_id}",
    response_model=ClassStructureResponse,
)
async def update_class_structure(
    class_structure_id: uuid.UUID,
    class_structure_data: ClassStructureUpdate,
    class_structure_service: ClassStructureService = Depends(
        get_class_structure_service
    ),
    user: UserDep = ...,
):
    """
    Update class structure entry.

    Args:
        class_structure_id: Class structure UUID
        class_structure_data: Updated class structure data
        class_structure_service: Class structure service
        user: Current authenticated user

    Returns:
        Updated class structure entry
    """
    try:
        class_structure = await class_structure_service.update_class_structure(
            class_structure_id=class_structure_id,
            total_students=class_structure_data.total_students,
            number_of_classes=class_structure_data.number_of_classes,
            avg_class_size=class_structure_data.avg_class_size,
            requires_atsem=class_structure_data.requires_atsem,
            atsem_count=class_structure_data.atsem_count,
            calculation_method=class_structure_data.calculation_method,
            notes=class_structure_data.notes,
            user_id=user.user_id,
        )
        return class_structure
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.api_route(
    "/{version_id}/bulk",
    methods=["POST", "PUT"],
    response_model=list[ClassStructureResponse],
    summary="Bulk update class structures",
)
async def bulk_update_class_structure(
    version_id: uuid.UUID,
    bulk_data: ClassStructureBulkUpdate,
    class_structure_service: ClassStructureService = Depends(
        get_class_structure_service
    ),
    user: UserDep = ...,
):
    """
    Bulk update class structure entries.
    """
    try:
        # Convert schema list to dict list for service
        updates_dict = [u.model_dump() for u in bulk_data.updates]
        
        class_structures = await class_structure_service.bulk_update_class_structure(
            updates=updates_dict,
            user_id=user.user_id,
        )
        return class_structures
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
