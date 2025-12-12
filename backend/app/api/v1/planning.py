"""
Planning API endpoints.

Provides REST API for managing planning operations:
- Enrollment planning and projections
- Class structure calculation
- DHG workforce planning (subject hours, teacher requirements, allocations)
- TRMD gap analysis
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.enrollment_projection import router as enrollment_projection_router
from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.planning import (
    ClassStructureCalculationRequest,
    ClassStructureResponse,
    ClassStructureUpdate,
    DHGHoursCalculationRequest,
    DHGSubjectHoursResponse,
    DHGTeacherRequirementResponse,
    EnrollmentPlanCreate,
    EnrollmentPlanResponse,
    EnrollmentPlanUpdate,
    EnrollmentProjectionRequest,
    EnrollmentSummary,
    EnrollmentTotalsBulkUpdate,
    EnrollmentWithDistributionResponse,
    FTECalculationRequest,
    ImpactCalculationRequest,
    ImpactCalculationResponse,
    NationalityDistributionBulkUpdate,
    NationalityDistributionResponse,
    TeacherAllocationBulkUpdate,
    TeacherAllocationCreate,
    TeacherAllocationResponse,
    TeacherAllocationUpdate,
    TRMDGapAnalysisResponse,
)
from app.schemas.planning_progress import (
    CascadeRequest,
    CascadeResponse,
    PlanningProgressResponse,
)
from app.services.cascade_service import CascadeService
from app.services.class_structure_service import ClassStructureService
from app.services.dhg_service import DHGService
from app.services.enrollment_service import EnrollmentService
from app.services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from app.services.impact_calculator_service import (
    ImpactCalculatorService,
    ProposedChange,
)
from app.services.planning_progress_service import PlanningProgressService

router = APIRouter(prefix="/api/v1/planning", tags=["planning"])
router.include_router(enrollment_projection_router)


def get_enrollment_service(db: AsyncSession = Depends(get_db)) -> EnrollmentService:
    """
    Dependency to get enrollment service instance.

    Args:
        db: Database session

    Returns:
        EnrollmentService instance
    """
    return EnrollmentService(db)


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


def get_dhg_service(db: AsyncSession = Depends(get_db)) -> DHGService:
    """
    Dependency to get DHG service instance.

    Args:
        db: Database session

    Returns:
        DHGService instance
    """
    return DHGService(db)


def get_planning_progress_service(
    db: AsyncSession = Depends(get_db),
) -> PlanningProgressService:
    """
    Dependency to get planning progress service instance.

    Args:
        db: Database session

    Returns:
        PlanningProgressService instance
    """
    return PlanningProgressService(db)


# ==============================================================================
# Enrollment Planning Endpoints
# ==============================================================================


@router.get(
    "/enrollment/{version_id}",
    response_model=list[EnrollmentPlanResponse],
)
async def get_enrollment_plan(
    version_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Get enrollment plan for a budget version.

    Args:
        version_id: Budget version UUID
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        List of enrollment plan entries
    """
    try:
        enrollments = await enrollment_service.get_enrollment_plan(version_id)
        return enrollments
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/enrollment/{version_id}",
    response_model=EnrollmentPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_enrollment(
    version_id: uuid.UUID,
    enrollment_data: EnrollmentPlanCreate,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Create enrollment plan entry.

    Args:
        version_id: Budget version UUID
        enrollment_data: Enrollment data
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        Created enrollment plan entry
    """
    try:
        enrollment = await enrollment_service.create_enrollment(
            version_id=version_id,
            level_id=enrollment_data.level_id,
            nationality_type_id=enrollment_data.nationality_type_id,
            student_count=enrollment_data.student_count,
            notes=enrollment_data.notes,
            user_id=user.user_id,
        )
        return enrollment
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
    "/enrollment/{enrollment_id}",
    response_model=EnrollmentPlanResponse,
)
async def update_enrollment(
    enrollment_id: uuid.UUID,
    enrollment_data: EnrollmentPlanUpdate,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Update enrollment plan entry.

    Args:
        enrollment_id: Enrollment plan UUID
        enrollment_data: Updated enrollment data
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        Updated enrollment plan entry
    """
    try:
        enrollment = await enrollment_service.update_enrollment(
            enrollment_id=enrollment_id,
            student_count=enrollment_data.student_count,
            notes=enrollment_data.notes,
            user_id=user.user_id,
        )
        return enrollment
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
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


@router.delete(
    "/enrollment/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_enrollment(
    enrollment_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Delete enrollment plan entry.

    Args:
        enrollment_id: Enrollment plan UUID
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        No content
    """
    try:
        await enrollment_service.delete_enrollment(enrollment_id, user_id=user.user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/enrollment/{version_id}/summary",
    response_model=EnrollmentSummary,
)
async def get_enrollment_summary(
    version_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Get enrollment summary statistics.

    Args:
        version_id: Budget version UUID
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        Enrollment summary with totals and breakdowns
    """
    try:
        summary = await enrollment_service.get_enrollment_summary(version_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/enrollment/{version_id}/project",
)
async def project_enrollment(
    version_id: uuid.UUID,
    projection_request: EnrollmentProjectionRequest,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Project enrollment growth over multiple years.

    Args:
        version_id: Budget version UUID
        projection_request: Projection parameters
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        List of enrollment projections
    """
    try:
        projections = await enrollment_service.project_enrollment(
            version_id=version_id,
            years_to_project=projection_request.years_to_project,
            growth_scenario=projection_request.growth_scenario,
            custom_growth_rates=projection_request.custom_growth_rates,
        )
        return projections
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


@router.get(
    "/enrollment/{version_id}/with-distribution",
    response_model=EnrollmentWithDistributionResponse,
    summary="Get enrollment with nationality distribution and breakdown",
)
async def get_enrollment_with_distribution(
    version_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Get comprehensive enrollment view with distributions and calculated breakdown.

    Returns enrollment totals by level, nationality distribution percentages,
    and calculated student counts by level × nationality for the enrollment grid UI.

    Args:
        version_id: Budget version UUID
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        EnrollmentWithDistributionResponse with:
        - totals: Enrollment totals by level
        - distributions: Nationality percentages per level
        - breakdown: Calculated student counts by level × nationality
        - summary: Overall statistics
    """
    try:
        data = await enrollment_service.get_enrollment_with_distribution(version_id)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.api_route(
    "/enrollment/{version_id}/bulk",
    methods=["POST", "PUT"],
    response_model=list[EnrollmentPlanResponse],
    summary="Bulk upsert enrollment totals by level",
)
async def bulk_upsert_enrollment_totals(
    version_id: uuid.UUID,
    bulk_data: EnrollmentTotalsBulkUpdate,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Bulk create/update enrollment totals by level.

    Accepts total student counts per level and distributes them according to
    nationality distribution percentages. If no distribution is set for a level,
    students are distributed equally across nationalities.

    Args:
        version_id: Budget version UUID
        bulk_data: Bulk enrollment totals
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        List of enrollment entries after distribution
    """
    try:
        totals_dict = [
            {"level_id": t.level_id, "total_students": t.total_students}
            for t in bulk_data.totals
        ]
        enrollments = await enrollment_service.bulk_upsert_enrollment_totals(
            version_id=version_id,
            totals=totals_dict,
            user_id=user.user_id,
        )
        return enrollments
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


# ==============================================================================
# Nationality Distribution Endpoints
# ==============================================================================


@router.get(
    "/distributions/{version_id}",
    response_model=list[NationalityDistributionResponse],
    summary="Get nationality distributions for a budget version",
)
async def get_distributions(
    version_id: uuid.UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Get nationality distribution percentages for all levels in a budget version.

    Returns the French, Saudi, and Other nationality percentages for each
    academic level, used to calculate student breakdown from total counts.

    Args:
        version_id: Budget version UUID
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        List of NationalityDistributionResponse
    """
    try:
        distributions = await enrollment_service.get_distributions(version_id)
        return distributions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.api_route(
    "/distributions/{version_id}",
    methods=["POST", "PUT"],
    response_model=list[NationalityDistributionResponse],
    summary="Bulk upsert nationality distributions",
)
async def bulk_upsert_distributions(
    version_id: uuid.UUID,
    bulk_data: NationalityDistributionBulkUpdate,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    user: UserDep = ...,
):
    """
    Bulk create/update nationality distributions for a budget version.

    Validates that percentages sum to 100% for each level. Distributions are
    used to calculate student breakdown when entering enrollment totals.

    Args:
        version_id: Budget version UUID
        bulk_data: Distribution percentages
        enrollment_service: Enrollment service
        user: Current authenticated user

    Returns:
        List of upserted NationalityDistributionResponse
    """
    try:
        distributions_dict = [
            {
                "level_id": d.level_id,
                "french_pct": d.french_pct,
                "saudi_pct": d.saudi_pct,
                "other_pct": d.other_pct,
            }
            for d in bulk_data.distributions
        ]
        distributions = await enrollment_service.bulk_upsert_distributions(
            version_id=version_id,
            distributions=distributions_dict,
            user_id=user.user_id,
        )
        return distributions
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# Class Structure Planning Endpoints
# ==============================================================================


@router.get(
    "/class-structure/{version_id}",
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
    "/class-structure/{version_id}/calculate",
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
    "/class-structure/{class_structure_id}",
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


# ==============================================================================
# DHG Subject Hours Endpoints
# ==============================================================================


@router.get(
    "/dhg/subject-hours/{version_id}",
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
        List of DHG subject hours entries
    """
    try:
        subject_hours = await dhg_service.get_dhg_subject_hours(version_id)
        return subject_hours
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/dhg/subject-hours/{version_id}/calculate",
    response_model=list[DHGSubjectHoursResponse],
)
async def calculate_dhg_subject_hours(
    version_id: uuid.UUID,
    calculation_request: DHGHoursCalculationRequest,
    dhg_service: DHGService = Depends(get_dhg_service),
    user: UserDep = ...,
):
    """
    Calculate DHG subject hours from class structure and subject hours matrix.

    Args:
        version_id: Budget version UUID
        calculation_request: Calculation parameters
        dhg_service: DHG service
        user: Current authenticated user

    Returns:
        List of calculated DHG subject hours entries
    """
    try:
        subject_hours = await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=version_id,
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
    "/dhg/teacher-requirements/{version_id}",
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
        List of teacher FTE requirements
    """
    try:
        requirements = await dhg_service.get_teacher_requirements(version_id)
        return requirements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/dhg/teacher-requirements/{version_id}/calculate",
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
    "/dhg/allocations/{version_id}",
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
    "/dhg/allocations/{version_id}",
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
    "/dhg/allocations/{allocation_id}",
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
    "/dhg/allocations/{version_id}/bulk",
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
    "/dhg/allocations/{allocation_id}",
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
# TRMD Gap Analysis Endpoint
# ==============================================================================


@router.get(
    "/dhg/trmd/{version_id}",
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


# ==============================================================================
# Planning Progress & Validation Endpoint
# ==============================================================================


@router.get(
    "/progress/{version_id}",
    response_model=PlanningProgressResponse,
    summary="Get planning progress and validation status",
)
async def get_planning_progress(
    version_id: uuid.UUID,
    progress_service: PlanningProgressService = Depends(get_planning_progress_service),
    user: UserDep = ...,
):
    """
    Get comprehensive planning progress with validation for all 6 planning steps.

    This endpoint analyzes existing planning data to determine completion status,
    identify blockers, and provide validation results for:
    1. Enrollment Planning
    2. Class Structure
    3. DHG Workforce Planning
    4. Revenue Planning
    5. Cost Planning
    6. CapEx Planning

    Args:
        version_id: Budget version UUID
        progress_service: Planning progress service
        user: Current authenticated user

    Returns:
        PlanningProgressResponse with:
        - Overall progress percentage (0-100)
        - Completion status for each of 6 steps
        - Validation checks (passed/failed/warning/info)
        - Blockers with resolution steps
        - Key metrics for each step
    """
    try:
        progress = await progress_service.get_planning_progress(version_id)
        return progress
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# Cascade Recalculation Endpoints
# ==============================================================================


def get_cascade_service(db: AsyncSession = Depends(get_db)) -> CascadeService:
    """
    Dependency to get cascade service instance.

    Args:
        db: Database session

    Returns:
        CascadeService instance
    """
    return CascadeService(db)


@router.post(
    "/{version_id}/cascade",
    response_model=CascadeResponse,
    summary="Cascade recalculation through dependent planning steps",
)
async def cascade_recalculate(
    version_id: uuid.UUID,
    request: CascadeRequest,
    cascade_service: CascadeService = Depends(get_cascade_service),
    user: UserDep = ...,
):
    """
    Trigger cascading recalculation of dependent planning steps.

    When a planning step changes (e.g., enrollment), this endpoint can
    automatically recalculate all dependent downstream steps in the
    correct order:
    - Enrollment → Class Structure → DHG → Costs
    - Enrollment → Revenue
    - DHG → Costs

    Args:
        version_id: Budget version UUID
        request: Cascade request specifying from_step_id or step_ids
        cascade_service: Cascade service
        user: Current authenticated user

    Returns:
        CascadeResponse with recalculated and failed steps

    Example:
        POST /api/v1/planning/{version_id}/cascade
        {"from_step_id": "enrollment"}

        Response:
        {
            "recalculated_steps": ["class_structure", "dhg", "revenue", "costs"],
            "failed_steps": [],
            "message": "Successfully recalculated 4 step(s)"
        }
    """
    try:
        if request.from_step_id:
            result = await cascade_service.recalculate_from_step(
                version_id, request.from_step_id
            )
        elif request.step_ids:
            result = await cascade_service.recalculate_steps(version_id, request.step_ids)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either from_step_id or step_ids must be provided",
            )

        return CascadeResponse(**result.to_dict())
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


# ==============================================================================
# Impact Calculation Endpoint
# ==============================================================================


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
    "/{version_id}/impact",
    response_model=ImpactCalculationResponse,
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
        ImpactCalculationResponse with all calculated metrics

    Example:
        POST /api/v1/planning/{version_id}/impact
        {
            "step_id": "enrollment",
            "dimension_type": "level",
            "dimension_id": "uuid-of-level",
            "field_name": "student_count",
            "new_value": 130
        }

        Response:
        {
            "fte_change": 0.67,
            "fte_current": 95.0,
            "fte_proposed": 95.67,
            "cost_impact_sar": 167500,
            "cost_current_sar": 23750000,
            "cost_proposed_sar": 23917500,
            "revenue_impact_sar": 450000,
            "revenue_current_sar": 56025000,
            "revenue_proposed_sar": 56475000,
            "margin_impact_pct": 0.12,
            "margin_current_pct": 57.6,
            "margin_proposed_pct": 57.72,
            "affected_steps": ["class_structure", "dhg", "costs", "revenue"]
        }
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
