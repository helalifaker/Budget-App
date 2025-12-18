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

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse
from app.database import get_db
from app.dependencies.auth import ManagerDep, UserDep
from app.models import Organization, ScenarioType, VersionStatus
from app.schemas.settings import (
    AcademicCycleResponse,
    AcademicLevelResponse,
    ApplyTemplateRequest,
    ApplyTemplateResponse,
    BudgetVersionClone,
    BudgetVersionCreate,
    BudgetVersionResponse,
    BudgetVersionUpdate,
    ClassSizeParamBatchRequest,
    ClassSizeParamBatchResponse,
    ClassSizeParamCreate,
    ClassSizeParamResponse,
    FeeCategoryResponse,
    FeeStructureCreate,
    FeeStructureResponse,
    NationalityTypeResponse,
    SubjectCreateRequest,
    SubjectHoursBatchRequest,
    SubjectHoursBatchResponse,
    SubjectHoursCreate,
    SubjectHoursMatrixResponse,
    SubjectHoursResponse,
    SubjectResponse,
    SystemConfigCreate,
    SystemConfigResponse,
    TeacherCategoryResponse,
    TeacherCostParamCreate,
    TeacherCostParamResponse,
    TemplateInfo,
    TimetableConstraintCreate,
    TimetableConstraintResponse,
)
from app.services.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.services.settings.configuration_service import ConfigurationService

# Backward compatibility alias
BudgetVersionStatus = VersionStatus

router = APIRouter(prefix="", tags=["configuration"])


@router.get("/debug-token")
async def debug_token(user: UserDep = ...):
    """
    Debug endpoint to test JWT token verification.
    
    Returns the decoded token claims to confirm authentication is working.
    """
    return {
        "sub": user.user_id,
        "email": user.user_email,
        "role": user.user_role,
        "status": "authenticated",
        "message": "JWT token verified successfully",
    }


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
# Version Endpoints
# ==============================================================================


@router.get("/budget-versions", response_model=PaginatedResponse[BudgetVersionResponse])
async def get_versions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    fiscal_year: int | None = Query(None, description="Filter by fiscal year"),
    status: BudgetVersionStatus | None = Query(None, description="Filter by status"),
    scenario_type: ScenarioType | None = Query(None, description="Filter by scenario type"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get paginated versions.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        fiscal_year: Optional fiscal year filter
        status: Optional status filter
        scenario_type: Optional scenario type filter
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Paginated response with versions
    """
    result = await config_service.get_versions_paginated(
        page=page,
        page_size=page_size,
        fiscal_year=fiscal_year,
        status=status,
        scenario_type=scenario_type,
    )
    return result


@router.get("/budget-versions/{version_id}", response_model=BudgetVersionResponse)
async def get_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get version by ID.

    Args:
        version_id: Version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Version

    Raises:
        HTTPException: 404 if version not found
    """
    try:
        version = await config_service.get_version(version_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/budget-versions", response_model=BudgetVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    version_data: BudgetVersionCreate,
    request: Request,  # Get request to access state
    db: AsyncSession = Depends(get_db),
    config_service: ConfigurationService = Depends(get_config_service),
):
    """
    Create a new version.

    Args:
        version_data: Version data
        db: Database session for organization lookup
        config_service: Configuration service

    Returns:
        Created version

    Raises:
        HTTPException: 409 if a working version already exists for the fiscal year
        HTTPException: 400 if no organization is available
    """
    try:
        # Get user_id from request state if available (set by AuthenticationMiddleware)
        user_id_str = getattr(request.state, "user_id", None)
        try:
            user_id = uuid.UUID(str(user_id_str)) if user_id_str else None
        except (ValueError, AttributeError):
            user_id = None

        # Resolve organization_id if not provided
        organization_id = version_data.organization_id
        if organization_id is None:
            # For single-tenant deployment: get the default (first active) organization
            result = await db.execute(
                select(Organization)
                .where(Organization.is_active == True)  # noqa: E712
                .limit(1)
            )
            org = result.scalar_one_or_none()
            if org is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active organization found. Please create an organization first.",
                )
            organization_id = org.id

        version = await config_service.create_version(
            name=version_data.name,
            fiscal_year=version_data.fiscal_year,
            academic_year=version_data.academic_year,
            organization_id=organization_id,
            scenario_type=version_data.scenario_type,
            notes=version_data.notes,
            parent_version_id=version_data.parent_version_id,
            user_id=user_id,
        )
        return version
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create version: {e!s}")


@router.put("/budget-versions/{version_id}", response_model=BudgetVersionResponse)
async def update_version(
    version_id: uuid.UUID,
    version_data: BudgetVersionUpdate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Update version metadata.

    Args:
        version_id: Version UUID
        version_data: Updated version data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Updated version

    Raises:
        HTTPException: 404 if version not found
    """
    try:
        version = await config_service.version_service.update(
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
async def submit_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Submit version for approval.

    Args:
        version_id: Version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Submitted version

    Raises:
        HTTPException: 422 if version cannot be submitted
    """
    try:
        version = await config_service.submit_version(version_id, user.user_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/budget-versions/{version_id}/approve", response_model=BudgetVersionResponse)
async def approve_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: ManagerDep = ...,
):
    """
    Approve version (manager/admin only).

    Args:
        version_id: Version UUID
        config_service: Configuration service
        user: Current authenticated user (must be manager or admin)

    Returns:
        Approved version

    Raises:
        HTTPException: 422 if version cannot be approved
    """
    try:
        version = await config_service.approve_version(version_id, user.user_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/budget-versions/{version_id}/reject", response_model=BudgetVersionResponse)
async def reject_version(
    version_id: uuid.UUID,
    reason: str | None = Query(None, description="Reason for rejecting the version"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: ManagerDep = ...,
):
    """
    Reject a submitted version (manager/admin only).

    This returns the version to WORKING status, allowing the submitter
    to make corrections. The rejection reason is stored in the notes field
    for audit trail purposes.

    Args:
        version_id: Version UUID
        reason: Optional reason for rejection (stored in notes)
        config_service: Configuration service
        user: Current authenticated user (must be manager or admin)

    Returns:
        Rejected version (now in WORKING status)

    Raises:
        HTTPException: 404 if version not found
        HTTPException: 422 if version cannot be rejected (wrong status)
    """
    try:
        version = await config_service.reject_version(
            version_id, user.user_id, reason=reason
        )
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/budget-versions/{version_id}/supersede", response_model=BudgetVersionResponse)
async def supersede_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Mark version as superseded.

    Args:
        version_id: Version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Superseded version

    Raises:
        HTTPException: 404 if version not found
    """
    try:
        version = await config_service.supersede_version(version_id, user.user_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/budget-versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Delete (soft delete) a version.

    Business Rule: Cannot delete approved versions. Approved versions must be
    superseded instead to maintain audit trail.

    Args:
        version_id: Version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if version not found
        HTTPException: 422 if version is approved (cannot delete approved budgets)
    """
    try:
        await config_service.delete_version(version_id, user.user_id)
        return None  # 204 No Content
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/budget-versions/{version_id}/clone",
    response_model=BudgetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_version(
    version_id: uuid.UUID,
    clone_data: BudgetVersionClone,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Clone a version to create a new baseline for the next fiscal year.

    This is the recommended approach for creating next year's budget based on current
    year's configuration. Optionally clones all configuration data (class sizes, subject
    hours, teacher costs, fees).

    The cloned version:
    - Has status WORKING (not approved)
    - Has parent_version_id pointing to source (establishes lineage)
    - Optionally includes all configuration data from source
    - Does NOT include planning data (enrollment, classes, DHG, etc.) - recalculated

    Args:
        version_id: Source version UUID to clone
        clone_data: Clone parameters (name, fiscal_year, academic_year, clone_configuration)
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Newly created version

    Raises:
        HTTPException: 404 if source version not found
        HTTPException: 409 if working version exists for target fiscal year
    """
    try:
        new_version = await config_service.clone_version(
            source_version_id=version_id,
            name=clone_data.name,
            fiscal_year=clone_data.fiscal_year,
            academic_year=clone_data.academic_year,
            scenario_type=clone_data.scenario_type,
            clone_configuration=clone_data.clone_configuration,
            user_id=user.user_id,
        )
        return new_version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


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
            version_id=param_data.version_id,
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


@router.delete("/class-size-params/{param_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_size_param(
    param_id: uuid.UUID,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Delete a class size parameter (soft delete).

    Args:
        param_id: Class size parameter UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if parameter not found
    """
    try:
        await config_service.class_size_param_service.soft_delete(param_id, user.user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/class-size-params/batch", response_model=ClassSizeParamBatchResponse)
async def batch_upsert_class_size_params(
    batch_data: ClassSizeParamBatchRequest,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Batch create/update class size parameters with optimistic locking.

    Efficiently saves multiple class size params in a single transaction.
    Uses updated_at for optimistic locking to prevent lost updates from
    concurrent modifications.

    Args:
        batch_data: Batch request with version_id and entries list
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        ClassSizeParamBatchResponse with per-entry results:
        - created_count: Number of new records created
        - updated_count: Number of existing records updated
        - conflict_count: Number of records with optimistic locking conflicts
        - entries: Per-entry status (created/updated/conflict)

    Notes:
        - Max 50 entries per request
        - Each entry can include updated_at for optimistic locking
        - Conflicts return the current updated_at for client refresh
    """
    try:
        result = await config_service.batch_upsert_class_size_params(
            version_id=batch_data.version_id,
            entries=batch_data.entries,
            user_id=user.user_id,
        )
        return result
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
            version_id=hours_data.version_id,
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


@router.get("/subject-hours/matrix", response_model=SubjectHoursMatrixResponse)
async def get_subject_hours_matrix_by_cycle(
    version_id: uuid.UUID = Query(..., description="Budget version ID"),
    cycle_code: str = Query(..., description="Cycle code (e.g., 'COLL', 'LYC')"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get subject hours matrix organized by cycle.

    Returns a matrix view with all subjects as rows and levels as columns,
    including hours per week and split class settings. Non-applicable subjects
    for the cycle are marked with is_applicable=False.

    Args:
        version_id: Budget version UUID
        cycle_code: Cycle code to filter (e.g., 'COLL' for Collège, 'LYC' for Lycée)
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        SubjectHoursMatrixResponse with levels and subjects organized for display

    Raises:
        HTTPException: 404 if budget version or cycle not found
    """
    try:
        matrix_list = await config_service.get_subject_hours_matrix_by_cycle(
            version_id=version_id,
            cycle_code=cycle_code,
        )
        # Service returns a list, but with cycle_code filter it should have exactly one item
        if not matrix_list:
            raise NotFoundError(f"Cycle with code '{cycle_code}' not found")
        return matrix_list[0]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/subject-hours/batch", response_model=SubjectHoursBatchResponse)
async def batch_save_subject_hours(
    batch_data: SubjectHoursBatchRequest,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Batch create/update/delete subject hours entries.

    Efficiently saves multiple subject hours in a single transaction.
    - Entries with hours_per_week=None will be deleted
    - Existing entries will be updated
    - New entries will be created

    Max 200 entries per request to prevent timeout.

    Args:
        batch_data: Batch request with version_id and entries list
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        SubjectHoursBatchResponse with created/updated/deleted counts and any errors

    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 404 if budget version not found
    """
    try:
        result = await config_service.batch_upsert_subject_hours(
            version_id=batch_data.version_id,
            entries=batch_data.entries,
            user_id=user.user_id,
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/subject-hours/templates", response_model=list[TemplateInfo])
async def get_curriculum_templates(
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get list of available curriculum templates.

    Returns pre-built AEFE standard curriculum templates that can be applied
    to quickly populate subject hours configuration.

    Args:
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of TemplateInfo with code, name, description, and applicable cycles
    """
    templates = config_service.get_available_templates()
    return templates


@router.post("/subject-hours/apply-template", response_model=ApplyTemplateResponse)
async def apply_curriculum_template(
    request: ApplyTemplateRequest,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Apply a predefined curriculum template to populate subject hours.

    Templates contain standard AEFE weekly hours for each subject-level combination.
    Use this to quickly set up subject hours based on French national curriculum.

    Args:
        request: ApplyTemplateRequest with template_code and overwrite_existing flag
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        ApplyTemplateResponse with created/updated counts

    Raises:
        HTTPException: 400 if template not found or validation fails
        HTTPException: 404 if budget version not found
    """
    try:
        result = await config_service.apply_curriculum_template(
            version_id=request.version_id,
            template_code=request.template_code,
            cycle_codes=request.cycle_codes,
            overwrite_existing=request.overwrite_existing,
            user_id=user.user_id,
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreateRequest,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Create a new custom subject.

    Allows adding subjects not in the standard AEFE curriculum (e.g., local
    language courses, electives specific to the school).

    Args:
        subject_data: Subject data with code, names, category, and applicable cycles
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Created Subject

    Raises:
        HTTPException: 400 if validation fails (e.g., duplicate code)
        HTTPException: 409 if subject code already exists
    """
    try:
        # Note: applicable_cycles from schema is for frontend validation only
        # The Subject model doesn't store this field (can be added in future migration)
        subject = await config_service.create_subject(
            code=subject_data.code,
            name_fr=subject_data.name_fr,
            name_en=subject_data.name_en,
            category=subject_data.category,
            user_id=user.user_id,
        )
        return subject
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
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
            version_id=param_data.version_id,
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
            version_id=fee_data.version_id,
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


# ============================================================================
# Timetable Constraints (Module 6)
# ============================================================================


@router.get("/timetable-constraints", response_model=list[TimetableConstraintResponse])
async def get_timetable_constraints(
    version_id: uuid.UUID = Query(..., description="Budget version ID"),
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Get timetable constraints for a budget version.

    Args:
        version_id: Budget version UUID
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        List of timetable constraints

    Raises:
        HTTPException: 404 if budget version not found
    """
    try:
        constraints = await config_service.get_timetable_constraints(version_id)
        return constraints
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/timetable-constraints", response_model=TimetableConstraintResponse)
async def upsert_timetable_constraint(
    constraint_data: TimetableConstraintCreate,
    config_service: ConfigurationService = Depends(get_config_service),
    user: UserDep = ...,
):
    """
    Create or update timetable constraint.

    Args:
        constraint_data: Timetable constraint data
        config_service: Configuration service
        user: Current authenticated user

    Returns:
        Created or updated timetable constraint

    Raises:
        HTTPException: 400 if validation fails (e.g., max_hours_per_day > total_hours_per_week)
        HTTPException: 404 if budget version or level not found
    """
    try:
        constraint = await config_service.upsert_timetable_constraint(
            version_id=constraint_data.version_id,
            level_id=constraint_data.level_id,
            total_hours_per_week=constraint_data.total_hours_per_week,
            max_hours_per_day=constraint_data.max_hours_per_day,
            days_per_week=constraint_data.days_per_week,
            requires_lunch_break=constraint_data.requires_lunch_break,
            min_break_duration_minutes=constraint_data.min_break_duration_minutes,
            notes=constraint_data.notes,
            user_id=user.user_id,
        )
        return constraint
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
