"""
Configuration API endpoints.

Provides REST API for managing system configuration and budget parameters:
- System configuration
- Budget versions
- Class size parameters
- Subject hours matrix
- Teacher cost parameters
- Fee structure
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import ManagerDep, UserDep
from app.models.configuration import BudgetVersionStatus
from app.schemas.configuration import (
    AcademicCycleResponse,
    AcademicLevelResponse,
    BudgetVersionCreate,
    BudgetVersionResponse,
    BudgetVersionUpdate,
    ClassSizeParamCreate,
    ClassSizeParamResponse,
    FeeCategoryResponse,
    FeeStructureCreate,
    FeeStructureResponse,
    NationalityTypeResponse,
    SubjectHoursCreate,
    SubjectHoursResponse,
    SubjectResponse,
    SystemConfigCreate,
    SystemConfigResponse,
    TeacherCategoryResponse,
    TeacherCostParamCreate,
    TeacherCostParamResponse,
)
from app.services.configuration_service import ConfigurationService
from app.services.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/api/v1", tags=["configuration"])


def get_config_service(db: AsyncSession = Depends(get_db)) -> ConfigurationService:
    """
    Dependency to get configuration service instance.

    Args:
        db: Database session

    Returns:
        ConfigurationService instance
    """
    return ConfigurationService(db)


# ==============================================================================
# System Configuration Endpoints
# ==============================================================================


@router.get("/config/system", response_model=list[SystemConfigResponse])
async def get_system_configs(
    category: str | None = Query(None, description="Filter by category"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get all system configurations.

    Args:
        category: Optional category filter
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of system configurations
    """
    configs = await config_service.get_all_system_configs(category=category)
    return configs


@router.get("/config/system/{key}", response_model=SystemConfigResponse)
async def get_system_config(
    key: str,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get system configuration by key.

    Args:
        key: Configuration key
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        System configuration

    Raises:
        HTTPException: 404 if configuration not found
    """
    try:
        config = await config_service.get_system_config(key)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration with key '{key}' not found",
            )
        return config
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/config/system/{key}", response_model=SystemConfigResponse)
async def upsert_system_config(
    key: str,
    config_data: SystemConfigCreate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Create or update system configuration.

    Args:
        key: Configuration key
        config_data: Configuration data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Created or updated system configuration

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        config = await config_service.upsert_system_config(
            key=key,
            value=config_data.value,
            category=config_data.category,
            description=config_data.description,
            user_id=user.user_id,
        )
        return config
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# Budget Version Endpoints
# ==============================================================================


@router.get("/budget-versions", response_model=list[BudgetVersionResponse])
async def get_budget_versions(
    fiscal_year: int | None = Query(None, description="Filter by fiscal year"),
    status: BudgetVersionStatus | None = Query(None, description="Filter by status"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get all budget versions.

    Args:
        fiscal_year: Optional fiscal year filter
        status: Optional status filter
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of budget versions
    """
    versions = await config_service.get_all_budget_versions(
        fiscal_year=fiscal_year,
        status=status,
    )
    return versions


@router.get("/budget-versions/{version_id}", response_model=BudgetVersionResponse)
async def get_budget_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get budget version by ID.

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Budget version

    Raises:
        HTTPException: 404 if version not found
    """
    try:
        version = await config_service.get_budget_version(version_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/budget-versions", response_model=BudgetVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_version(
    version_data: BudgetVersionCreate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Create a new budget version.

    Args:
        version_data: Budget version data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Created budget version

    Raises:
        HTTPException: 409 if a working version already exists for the fiscal year
    """
    try:
        version = await config_service.create_budget_version(
            name=version_data.name,
            fiscal_year=version_data.fiscal_year,
            academic_year=version_data.academic_year,
            notes=version_data.notes,
            parent_version_id=version_data.parent_version_id,
            user_id=user.user_id,
        )
        return version
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/budget-versions/{version_id}", response_model=BudgetVersionResponse)
async def update_budget_version(
    version_id: uuid.UUID,
    version_data: BudgetVersionUpdate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Update budget version metadata.

    Args:
        version_id: Budget version UUID
        version_data: Updated version data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Updated budget version

    Raises:
        HTTPException: 404 if version not found
    """
    try:
        version = await config_service.budget_version_service.update(
            version_id,
            version_data.model_dump(exclude_unset=True),
            user_id=user.user_id,
        )
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/budget-versions/{version_id}/submit", response_model=BudgetVersionResponse)
async def submit_budget_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Submit budget version for approval.

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Submitted budget version

    Raises:
        HTTPException: 422 if version cannot be submitted
    """
    try:
        version = await config_service.submit_budget_version(version_id, user.user_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/budget-versions/{version_id}/approve", response_model=BudgetVersionResponse)
async def approve_budget_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: ManagerDep = ...,
):
    """
    Approve budget version (manager/admin only).

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user (must be manager or admin)

    Returns:
        Approved budget version

    Raises:
        HTTPException: 422 if version cannot be approved
    """
    try:
        version = await config_service.approve_budget_version(version_id, user.user_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/budget-versions/{version_id}/supersede", response_model=BudgetVersionResponse)
async def supersede_budget_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Mark budget version as superseded.

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Superseded budget version

    Raises:
        HTTPException: 404 if version not found
    """
    try:
        version = await config_service.supersede_budget_version(version_id, user.user_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==============================================================================
# Academic Reference Data Endpoints
# ==============================================================================


@router.get("/academic-cycles", response_model=list[AcademicCycleResponse])
async def get_academic_cycles(
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get all academic cycles.

    Args:
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of academic cycles
    """
    cycles = await config_service.get_academic_cycles()
    return cycles


@router.get("/academic-levels", response_model=list[AcademicLevelResponse])
async def get_academic_levels(
    cycle_id: uuid.UUID | None = Query(None, description="Filter by cycle"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get all academic levels.

    Args:
        cycle_id: Optional cycle filter
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of academic levels
    """
    levels = await config_service.get_academic_levels(cycle_id=cycle_id)
    return levels


# ==============================================================================
# Class Size Parameters Endpoints
# ==============================================================================


@router.get("/class-size-params", response_model=list[ClassSizeParamResponse])
async def get_class_size_params(
    version_id: uuid.UUID = Query(..., description="Budget version ID"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get class size parameters for a budget version.

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of class size parameters
    """
    params = await config_service.get_class_size_params(version_id)
    return params


@router.put("/class-size-params", response_model=ClassSizeParamResponse)
async def upsert_class_size_param(
    param_data: ClassSizeParamCreate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Create or update class size parameter.

    Args:
        param_data: Class size parameter data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Created or updated class size parameter

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        param = await config_service.upsert_class_size_param(
            version_id=param_data.budget_version_id,
            level_id=param_data.level_id,
            cycle_id=param_data.cycle_id,
            min_class_size=param_data.min_class_size,
            target_class_size=param_data.target_class_size,
            max_class_size=param_data.max_class_size,
            notes=param_data.notes,
            user_id=user.user_id,
        )
        return param
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# Subject Hours Matrix Endpoints
# ==============================================================================


@router.get("/subjects", response_model=list[SubjectResponse])
async def get_subjects(
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get all active subjects.

    Args:
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of subjects
    """
    subjects = await config_service.get_subjects()
    return subjects


@router.get("/subject-hours", response_model=list[SubjectHoursResponse])
async def get_subject_hours_matrix(
    version_id: uuid.UUID = Query(..., description="Budget version ID"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get subject hours matrix for a budget version.

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of subject hours configurations
    """
    matrix = await config_service.get_subject_hours_matrix(version_id)
    return matrix


@router.put("/subject-hours", response_model=SubjectHoursResponse)
async def upsert_subject_hours(
    hours_data: SubjectHoursCreate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Create or update subject hours configuration.

    Args:
        hours_data: Subject hours data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Created or updated subject hours

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        hours = await config_service.upsert_subject_hours(
            version_id=hours_data.budget_version_id,
            subject_id=hours_data.subject_id,
            level_id=hours_data.level_id,
            hours_per_week=hours_data.hours_per_week,
            is_split=hours_data.is_split,
            notes=hours_data.notes,
            user_id=user.user_id,
        )
        return hours
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# Teacher Cost Parameters Endpoints
# ==============================================================================


@router.get("/teacher-categories", response_model=list[TeacherCategoryResponse])
async def get_teacher_categories(
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get all teacher categories.

    Args:
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of teacher categories
    """
    categories = await config_service.get_teacher_categories()
    return categories


@router.get("/teacher-costs", response_model=list[TeacherCostParamResponse])
async def get_teacher_cost_params(
    version_id: uuid.UUID = Query(..., description="Budget version ID"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get teacher cost parameters for a budget version.

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of teacher cost parameters
    """
    params = await config_service.get_teacher_cost_params(version_id)
    return params


@router.put("/teacher-costs", response_model=TeacherCostParamResponse)
async def upsert_teacher_cost_param(
    param_data: TeacherCostParamCreate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Create or update teacher cost parameter.

    Args:
        param_data: Teacher cost parameter data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Created or updated teacher cost parameter

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        param = await config_service.upsert_teacher_cost_param(
            version_id=param_data.budget_version_id,
            category_id=param_data.category_id,
            cycle_id=param_data.cycle_id,
            prrd_contribution_eur=param_data.prrd_contribution_eur,
            avg_salary_sar=param_data.avg_salary_sar,
            social_charges_rate=param_data.social_charges_rate,
            benefits_allowance_sar=param_data.benefits_allowance_sar,
            hsa_hourly_rate_sar=param_data.hsa_hourly_rate_sar,
            max_hsa_hours=param_data.max_hsa_hours,
            notes=param_data.notes,
            user_id=user.user_id,
        )
        return param
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# Fee Structure Endpoints
# ==============================================================================


@router.get("/fee-categories", response_model=list[FeeCategoryResponse])
async def get_fee_categories(
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get all fee categories.

    Args:
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of fee categories
    """
    categories = await config_service.get_fee_categories()
    return categories


@router.get("/nationality-types", response_model=list[NationalityTypeResponse])
async def get_nationality_types(
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get all nationality types.

    Args:
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of nationality types
    """
    types = await config_service.get_nationality_types()
    return types


@router.get("/fee-structure", response_model=list[FeeStructureResponse])
async def get_fee_structure(
    version_id: uuid.UUID = Query(..., description="Budget version ID"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get fee structure for a budget version.

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of fee structure entries
    """
    structure = await config_service.get_fee_structure(version_id)
    return structure


@router.put("/fee-structure", response_model=FeeStructureResponse)
async def upsert_fee_structure(
    fee_data: FeeStructureCreate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Create or update fee structure entry.

    Args:
        fee_data: Fee structure data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Created or updated fee structure entry

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        fee = await config_service.upsert_fee_structure(
            version_id=fee_data.budget_version_id,
            level_id=fee_data.level_id,
            nationality_type_id=fee_data.nationality_type_id,
            fee_category_id=fee_data.fee_category_id,
            amount_sar=fee_data.amount_sar,
            trimester=fee_data.trimester,
            notes=fee_data.notes,
            user_id=user.user_id,
        )
        return fee
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
