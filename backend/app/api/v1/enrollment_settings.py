"""
Enrollment Settings API Routes.

Endpoints for managing enrollment calibration settings - the first step in enrollment planning.
This includes auto-derived lateral entry rates, retention rates, and scenario multipliers.

Mounted under /api/v1/enrollment/settings.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.schemas.enrollment import (
    CalibrationRequest,
    CalibrationResult,
    CalibrationStatus,
    EnrollmentSettingsResponse,
    HistoricalDataSummary,
    ParameterOverridesBulkUpdate,
    ParameterOverrideUpdate,
    ScenarioMultipliersBulkUpdate,
    ScenarioMultiplierUpdate,
)
from app.services.enrollment.enrollment_calibration_service import EnrollmentCalibrationService
from app.services.exceptions import ServiceException

router = APIRouter(prefix="/enrollment/settings", tags=["Enrollment Settings"])


def get_service(db: AsyncSession = Depends(get_db)) -> EnrollmentCalibrationService:
    """Dependency to get calibration service instance."""
    return EnrollmentCalibrationService(db)


# =============================================================================
# Organization ID Resolution
# =============================================================================
# For now, organization_id is passed as a query parameter.
# In production, this would typically be resolved from the user's session
# or the currently selected organization in the frontend.
# RLS policies ensure users can only access data for their own organizations.
# =============================================================================


@router.get("", response_model=EnrollmentSettingsResponse)
async def get_enrollment_settings(
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    scenario_code: str = Query("base", description="Scenario code for effective rates"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> EnrollmentSettingsResponse:
    """
    Get complete enrollment settings for the Settings tab.

    Returns:
    - Calibration status (last calibrated, data quality, confidence)
    - Entry point rates (MS, GS, CP, 6EME, 2NDE) with derived, override, and effective values
    - Incidental lateral values (CE1-CM2, 5EME-3EME, 1ERE, TLE)
    - Scenario multipliers for all scenarios

    This is the main endpoint for populating the Settings tab UI.
    """
    try:
        return await service.get_enrollment_settings(organization_id, scenario_code)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/status", response_model=CalibrationStatus)
async def get_calibration_status(
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> CalibrationStatus:
    """
    Get the current calibration status.

    Returns information about:
    - When parameters were last calibrated
    - Which historical years were used
    - Overall confidence level
    - Data quality score (1-5 stars)
    """
    try:
        return await service.get_calibration_status(organization_id)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/calibrate", response_model=CalibrationResult)
async def calibrate_parameters(
    request: CalibrationRequest,
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> CalibrationResult:
    """
    Trigger recalibration of derived parameters.

    IMPORTANT: The target academic year is determined by the version_id.
    For Budget 2026 (fiscal_year=2026), the target is 2026-2027 academic year.
    Calibration uses N-1 (2025-2026) and N-2 (2024-2025) historical data.

    This calculates:
    - Progression rates for each grade from historical enrollment data
    - Decomposes into retention rate + lateral entry rate
    - Uses a rolling 4-year historical window (years BEFORE the target)
    - Determines confidence levels based on data quality

    The calibration runs automatically when historical data changes,
    but can be manually triggered using this endpoint.

    Use `force=true` to recalculate even if cached data is fresh.

    Request body:
    - version_id: Required - determines target academic year for calibration
    - force: Optional - force recalculation even if cached data is fresh
    """
    try:
        return await service.calibrate_parameters(
            organization_id,
            version_id=request.version_id,
            force=request.force,
        )
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/history", response_model=HistoricalDataSummary)
async def get_historical_data_summary(
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> HistoricalDataSummary:
    """
    Get summary of available historical data for calibration.

    Returns:
    - List of available school years with enrollment data
    - Whether each year has complete data for all grades
    - Recommended window of years to use for calibration
    - Whether sufficient data is available for reliable calibration
    """
    try:
        return await service.get_historical_data_summary(organization_id)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/overrides/{grade_code}", response_model=EnrollmentSettingsResponse)
async def update_parameter_override(
    grade_code: str,
    override: ParameterOverrideUpdate,
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    scenario_code: str = Query("base", description="Scenario code for effective rates"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> EnrollmentSettingsResponse:
    """
    Update parameter override for a specific grade.

    Allows overriding:
    - Lateral entry rate (for entry point grades)
    - Fixed lateral value (for incidental grades)
    - Retention rate (for any grade)

    When override is enabled, the manual value takes precedence over the derived value.
    When override is disabled, the derived value (or document default if unavailable) is used.

    Returns updated settings so the UI can refresh.
    """
    try:
        # Ensure grade_code matches the path parameter
        override_data = override.model_dump()
        override_data["grade_code"] = grade_code

        await service.update_parameter_override(
            organization_id, override_data, user.user_id
        )

        # Return updated settings
        return await service.get_enrollment_settings(organization_id, scenario_code)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/overrides", response_model=EnrollmentSettingsResponse)
async def update_parameter_overrides_bulk(
    overrides: ParameterOverridesBulkUpdate,
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    scenario_code: str = Query("base", description="Scenario code for effective rates"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> EnrollmentSettingsResponse:
    """
    Bulk update parameter overrides for multiple grades.

    Useful when the user modifies several grades and clicks "Save All".
    """
    try:
        for override in overrides.overrides:
            await service.update_parameter_override(
                organization_id, override.model_dump(), user.user_id
            )

        return await service.get_enrollment_settings(organization_id, scenario_code)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/multipliers/{scenario_code}", response_model=EnrollmentSettingsResponse)
async def update_scenario_multiplier(
    scenario_code: str,
    multiplier: ScenarioMultiplierUpdate,
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> EnrollmentSettingsResponse:
    """
    Update the lateral entry multiplier for a specific scenario.

    Scenario multipliers affect how lateral entry is calculated:
    - Base (1.0x): Uses derived/override rates as-is
    - Conservative (0.6x): Reduces lateral entry by 40%
    - Optimistic (1.3x): Increases lateral entry by 30%
    - Worst Case (0.3x): Reduces lateral entry by 70%
    - Best Case (1.5x): Increases lateral entry by 50%

    Returns updated settings so the UI can refresh.
    """
    try:
        # Ensure scenario_code matches the path parameter
        multiplier_data = multiplier.model_dump()
        multiplier_data["scenario_code"] = scenario_code

        await service.update_scenario_multiplier(organization_id, multiplier_data)

        return await service.get_enrollment_settings(organization_id, scenario_code)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/multipliers", response_model=EnrollmentSettingsResponse)
async def update_scenario_multipliers_bulk(
    multipliers: ScenarioMultipliersBulkUpdate,
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    scenario_code: str = Query("base", description="Scenario code for effective rates"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> EnrollmentSettingsResponse:
    """
    Bulk update scenario multipliers.

    Useful when the user modifies multiple scenarios and clicks "Save All".
    """
    try:
        for multiplier in multipliers.multipliers:
            await service.update_scenario_multiplier(
                organization_id, multiplier.model_dump()
            )

        return await service.get_enrollment_settings(organization_id, scenario_code)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/reset-overrides", response_model=EnrollmentSettingsResponse)
async def reset_all_overrides(
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    scenario_code: str = Query("base", description="Scenario code for effective rates"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> EnrollmentSettingsResponse:
    """
    Reset all parameter overrides to use derived/default values.

    This disables all manual overrides, reverting to:
    1. Derived values (from historical calibration) if available
    2. Document defaults if no historical data

    Scenario multipliers are reset to their default values.
    """
    try:
        await service.reset_all_overrides(organization_id)
        return await service.get_enrollment_settings(organization_id, scenario_code)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/reset-multipliers", response_model=EnrollmentSettingsResponse)
async def reset_scenario_multipliers(
    organization_id: uuid.UUID = Query(..., description="Organization ID"),
    scenario_code: str = Query("base", description="Scenario code for effective rates"),
    service: EnrollmentCalibrationService = Depends(get_service),
    user: UserDep = ...,
) -> EnrollmentSettingsResponse:
    """
    Reset scenario multipliers to default values.

    Default values:
    - Worst Case: 0.30
    - Conservative: 0.60
    - Base: 1.00
    - Optimistic: 1.30
    - Best Case: 1.50
    """
    try:
        await service.reset_scenario_multipliers(organization_id)
        return await service.get_enrollment_settings(organization_id, scenario_code)
    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
