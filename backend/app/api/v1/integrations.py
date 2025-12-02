"""
API Endpoints for Integration Management

This module provides REST API endpoints for:
- Odoo integration (financial actuals import)
- Skolengo integration (enrollment import/export)
- AEFE integration (position import)
- Integration settings management
- Integration logs viewing
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.integrations import IntegrationLog, IntegrationSettings
from app.schemas.integrations import (
    AEFEImportResponse,
    AEFEPositionListResponse,
    IntegrationLogListResponse,
    IntegrationLogResponse,
    IntegrationSettingsCreate,
    IntegrationSettingsResponse,
    IntegrationSettingsUpdate,
    OdooActualsListResponse,
    OdooConnectionRequest,
    OdooConnectionResponse,
    OdooImportActualsRequest,
    OdooImportActualsResponse,
    OdooSyncRequest,
    SkolengoComparisonResponse,
    SkolengoImportResponse,
)
from app.services.aefe_integration import AEFEIntegrationService, InvalidFileFormatError
from app.services.exceptions import IntegrationError
from app.services.odoo_integration import (
    OdooAuthenticationError,
    OdooConnectionError,
    OdooDataError,
    OdooIntegrationService,
)
from app.services.skolengo_integration import (
    SkolengoConnectionError,
    SkolengoDataError,
    SkolengoIntegrationService,
)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ============================================================================
# ODOO ENDPOINTS
# ============================================================================


@router.post("/odoo/connect", response_model=OdooConnectionResponse)
async def test_odoo_connection(
    request: OdooConnectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Test Odoo connection without saving credentials.

    Returns connection status and user ID if successful.
    """
    service = OdooIntegrationService(db)

    try:
        success, message, user_id = await service.test_connection(
            url=request.url,
            database=request.database,
            username=request.username,
            password=request.password,
        )

        return OdooConnectionResponse(
            success=success,
            message=message,
            user_id=user_id,
        )

    except (OdooConnectionError, OdooAuthenticationError) as e:
        return OdooConnectionResponse(
            success=False,
            message=str(e),
            user_id=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.post("/odoo/import-actuals", response_model=OdooImportActualsResponse)
async def import_odoo_actuals(
    request: OdooImportActualsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Import actual financial data from Odoo for specified period.

    Requires Odoo connection settings to be configured.
    """
    service = OdooIntegrationService(db)

    try:
        # Get settings
        stmt = select(IntegrationSettings).where(
            IntegrationSettings.integration_type == "odoo",
            IntegrationSettings.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Odoo integration is not configured. Please configure connection settings first.",
            )

        # Extract connection details
        config = settings.config
        url = config.get("url")
        database = config.get("database")
        username = config.get("username")
        encrypted_password = config.get("password")

        if not all([url, database, username, encrypted_password]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Odoo connection details are incomplete",
            )

        # Type narrowing - mypy now knows these are str, not Any | None
        assert isinstance(url, str)
        assert isinstance(database, str)
        assert isinstance(username, str)
        assert isinstance(encrypted_password, str)

        password = service._decrypt_password(encrypted_password)

        # Fetch actuals from Odoo
        actuals = await service.fetch_actuals(
            url=url,
            database=database,
            username=username,
            password=password,
            period=request.period,
            fiscal_year=request.fiscal_year,
        )

        # Import actuals into database
        batch_id, log_id, records_imported = await service.import_actuals(
            budget_version_id=request.budget_version_id,
            period=request.period,
            fiscal_year=request.fiscal_year,
            actuals=actuals,
        )

        return OdooImportActualsResponse(
            success=True,
            message=f"Successfully imported {records_imported} actual records for period {request.period}",
            records_imported=records_imported,
            batch_id=batch_id,
            log_id=log_id,
        )

    except (OdooConnectionError, OdooDataError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.post("/odoo/sync", response_model=dict[str, Any])
async def sync_odoo_actuals(
    request: OdooSyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Auto-sync actual financial data from Odoo for all periods (T1, T2, T3).

    Requires Odoo connection settings to be configured.
    """
    service = OdooIntegrationService(db)

    try:
        results = await service.sync_actuals(
            budget_version_id=request.budget_version_id,
            fiscal_year=request.fiscal_year,
        )

        return {
            "success": True,
            "message": "Sync completed",
            "results": results,
        }

    except (OdooConnectionError, OdooDataError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.get("/odoo/actuals/{version_id}", response_model=OdooActualsListResponse)
async def get_odoo_actuals(
    version_id: UUID,
    period: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get imported actual financial data for a budget version and period.
    """
    # TODO: Query budget_actuals table
    # For now, return mock data
    return OdooActualsListResponse(
        actuals=[],
        total_count=0,
        period=period,
    )


# ============================================================================
# SKOLENGO ENDPOINTS
# ============================================================================


@router.get("/skolengo/export/{version_id}")
async def export_skolengo_enrollment(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Export enrollment data to CSV format for Skolengo.

    Returns CSV file download.
    """
    service = SkolengoIntegrationService(db)

    try:
        csv_bytes, filename = await service.export_enrollment(version_id)

        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except SkolengoDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.post("/skolengo/import", response_model=SkolengoImportResponse)
async def import_skolengo_enrollment(
    budget_version_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Import enrollment data from uploaded CSV or Excel file.

    File must contain columns: Level, Nationality, Count
    """
    service = SkolengoIntegrationService(db)

    try:
        log_id, records_imported = await service.import_enrollment(
            budget_version_id=budget_version_id,
            file=file,
        )

        return SkolengoImportResponse(
            success=True,
            message=f"Successfully imported {records_imported} enrollment records",
            records_imported=records_imported,
            log_id=log_id,
        )

    except InvalidFileFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SkolengoDataError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.post("/skolengo/sync/{version_id}", response_model=SkolengoImportResponse)
async def sync_skolengo_enrollment(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync enrollment data via Skolengo API.

    Requires Skolengo API credentials to be configured.
    """
    service = SkolengoIntegrationService(db)

    try:
        log_id, records_synced = await service.sync_enrollment(
            budget_version_id=version_id
        )

        return SkolengoImportResponse(
            success=True,
            message=f"Successfully synced {records_synced} enrollment records",
            records_imported=records_synced,
            log_id=log_id,
        )

    except SkolengoConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.get("/skolengo/compare/{version_id}", response_model=SkolengoComparisonResponse)
async def compare_skolengo_enrollments(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Compare budget vs actual enrollment and calculate variances.

    Returns variance report by level and nationality.
    """
    service = SkolengoIntegrationService(db)

    try:
        comparison = await service.compare_enrollments(version_id)

        return SkolengoComparisonResponse(**comparison)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


# ============================================================================
# AEFE ENDPOINTS
# ============================================================================


@router.post("/aefe/import", response_model=AEFEImportResponse)
async def import_aefe_positions(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Import AEFE position data from uploaded Excel file.

    File must contain columns: Teacher Name, Category, Cycle, PRRD Rate
    """
    service = AEFEIntegrationService(db)

    try:
        log_id, records_imported = await service.import_positions(file=file)

        return AEFEImportResponse(
            success=True,
            message=f"Successfully imported {records_imported} AEFE positions",
            records_imported=records_imported,
            log_id=log_id,
        )

    except InvalidFileFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.get("/aefe/positions", response_model=list[dict[str, Any]])
async def get_aefe_positions(
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed list of all AEFE positions.
    """
    service = AEFEIntegrationService(db)

    try:
        positions = await service.get_positions_list()
        return positions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.get("/aefe/summary", response_model=AEFEPositionListResponse)
async def get_aefe_position_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary of AEFE positions by category and cycle.

    Includes total positions, AEFE-funded positions, and PRRD contribution.
    """
    service = AEFEIntegrationService(db)

    try:
        summary = await service.get_position_summary()
        return AEFEPositionListResponse(**summary)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


@router.get("/aefe/template")
async def download_aefe_template(
    db: AsyncSession = Depends(get_db),
):
    """
    Download Excel template for AEFE position import.
    """
    service = AEFEIntegrationService(db)

    try:
        excel_bytes, filename = await service.export_positions_template()

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e!s}",
        )


# ============================================================================
# INTEGRATION SETTINGS ENDPOINTS
# ============================================================================


@router.post("/settings", response_model=IntegrationSettingsResponse)
async def create_integration_settings(
    request: IntegrationSettingsCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create or update integration settings.

    Stores connection details and configuration for external integrations.
    Sensitive data (passwords, API keys) is encrypted before storage.
    """
    try:
        # Check if settings already exist
        stmt = select(IntegrationSettings).where(
            IntegrationSettings.integration_type == request.integration_type
        )
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings:
            # Update existing
            settings.config = request.config
            settings.auto_sync_enabled = request.auto_sync_enabled
            settings.auto_sync_interval_minutes = request.auto_sync_interval_minutes
        else:
            # Create new
            settings = IntegrationSettings(
                integration_type=request.integration_type,
                config=request.config,
                is_active=True,
                auto_sync_enabled=request.auto_sync_enabled,
                auto_sync_interval_minutes=request.auto_sync_interval_minutes,
            )
            db.add(settings)

        await db.commit()
        await db.refresh(settings)

        # Mask sensitive data in response
        safe_config = {k: "***MASKED***" if k in ["password", "api_key"] else v for k, v in settings.config.items()}
        settings.config = safe_config

        return settings

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {e!s}",
        )


@router.get("/settings/{integration_type}", response_model=IntegrationSettingsResponse)
async def get_integration_settings(
    integration_type: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get integration settings for specified integration type.

    Sensitive data is masked in the response.
    """
    stmt = select(IntegrationSettings).where(
        IntegrationSettings.integration_type == integration_type
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings for {integration_type} not found",
        )

    # Mask sensitive data
    safe_config = {k: "***MASKED***" if k in ["password", "api_key"] else v for k, v in settings.config.items()}
    settings.config = safe_config

    return settings


@router.patch("/settings/{integration_type}", response_model=IntegrationSettingsResponse)
async def update_integration_settings(
    integration_type: str,
    request: IntegrationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update integration settings.

    Only provided fields are updated.
    """
    stmt = select(IntegrationSettings).where(
        IntegrationSettings.integration_type == integration_type
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings for {integration_type} not found",
        )

    try:
        if request.config is not None:
            settings.config = request.config
        if request.is_active is not None:
            settings.is_active = request.is_active
        if request.auto_sync_enabled is not None:
            settings.auto_sync_enabled = request.auto_sync_enabled
        if request.auto_sync_interval_minutes is not None:
            settings.auto_sync_interval_minutes = request.auto_sync_interval_minutes

        await db.commit()
        await db.refresh(settings)

        # Mask sensitive data
        safe_config = {k: "***MASKED***" if k in ["password", "api_key"] else v for k, v in settings.config.items()}
        settings.config = safe_config

        return settings

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {e!s}",
        )


# ============================================================================
# INTEGRATION LOGS ENDPOINTS
# ============================================================================


@router.get("/logs", response_model=IntegrationLogListResponse)
async def get_integration_logs(
    integration_type: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    Get integration logs with optional filtering.

    Supports filtering by integration type and status.
    """
    try:
        query = select(IntegrationLog)

        if integration_type:
            query = query.where(IntegrationLog.integration_type == integration_type)
        if status_filter:
            query = query.where(IntegrationLog.status == status_filter)

        query = query.order_by(IntegrationLog.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        logs = result.scalars().all()

        # Get total count
        count_query = select(IntegrationLog)
        if integration_type:
            count_query = count_query.where(IntegrationLog.integration_type == integration_type)
        if status_filter:
            count_query = count_query.where(IntegrationLog.status == status_filter)

        count_result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())

        return IntegrationLogListResponse(
            logs=[IntegrationLogResponse.model_validate(log) for log in logs],
            total_count=total_count,
            page=offset // limit + 1,
            page_size=limit,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch logs: {e!s}",
        )


@router.get("/logs/{log_id}", response_model=IntegrationLogResponse)
async def get_integration_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed integration log by ID.
    """
    stmt = select(IntegrationLog).where(IntegrationLog.id == log_id)
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log with ID {log_id} not found",
        )

    return IntegrationLogResponse.model_validate(log)
