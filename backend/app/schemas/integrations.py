"""
Pydantic Schemas for Integration API

This module defines request and response schemas for integration endpoints.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# ODOO INTEGRATION SCHEMAS
# ============================================================================


class OdooConnectionRequest(BaseModel):
    """Request schema for testing Odoo connection."""

    url: str = Field(..., description="Odoo server URL")
    database: str = Field(..., description="Odoo database name")
    username: str = Field(..., description="Odoo username")
    password: str = Field(..., description="Odoo password")


class OdooConnectionResponse(BaseModel):
    """Response schema for Odoo connection test."""

    success: bool = Field(..., description="Whether connection was successful")
    message: str = Field(..., description="Status message")
    user_id: int | None = Field(None, description="Odoo user ID if connected")


class OdooImportActualsRequest(BaseModel):
    """Request schema for importing actuals from Odoo."""

    budget_version_id: UUID = Field(..., description="Budget version to import into")
    period: Literal["T1", "T2", "T3"] = Field(..., description="Period to import (T1, T2, or T3)")
    fiscal_year: int = Field(..., description="Fiscal year (e.g., 2025)")


class OdooActualRecord(BaseModel):
    """Schema for a single actual record."""

    account_code: str = Field(..., description="EFIR account code")
    amount: float = Field(..., description="Amount in SAR")
    description: str | None = Field(None, description="Transaction description")


class OdooImportActualsResponse(BaseModel):
    """Response schema for Odoo actuals import."""

    success: bool = Field(..., description="Whether import was successful")
    message: str = Field(..., description="Status message")
    records_imported: int = Field(..., description="Number of records imported")
    batch_id: UUID = Field(..., description="Batch ID for tracking")
    log_id: UUID = Field(..., description="Integration log ID")


class OdooSyncRequest(BaseModel):
    """Request schema for auto-syncing all periods from Odoo."""

    budget_version_id: UUID = Field(..., description="Budget version to sync")
    fiscal_year: int = Field(..., description="Fiscal year (e.g., 2025)")


class OdooActualsListResponse(BaseModel):
    """Response schema for listing imported actuals."""

    actuals: list[OdooActualRecord] = Field(..., description="List of actual records")
    total_count: int = Field(..., description="Total number of records")
    period: str = Field(..., description="Period")


# ============================================================================
# SKOLENGO INTEGRATION SCHEMAS
# ============================================================================


class SkolengoExportRequest(BaseModel):
    """Request schema for exporting enrollment to Skolengo."""

    budget_version_id: UUID = Field(..., description="Budget version to export from")


class SkolengoEnrollmentRecord(BaseModel):
    """Schema for enrollment record in Skolengo format."""

    level: str = Field(..., description="Academic level (PS, MS, GS, CP, etc.)")
    nationality: Literal["French", "Saudi", "Other"] = Field(
        ..., description="Student nationality category"
    )
    count: int = Field(..., description="Number of students", ge=0)


class SkolengoImportRequest(BaseModel):
    """Request schema for importing enrollment from Skolengo file."""

    budget_version_id: UUID = Field(..., description="Budget version to import into")


class SkolengoImportResponse(BaseModel):
    """Response schema for Skolengo enrollment import."""

    success: bool = Field(..., description="Whether import was successful")
    message: str = Field(..., description="Status message")
    records_imported: int = Field(..., description="Number of records imported")
    log_id: UUID = Field(..., description="Integration log ID")


class SkolengoSyncRequest(BaseModel):
    """Request schema for syncing enrollment via Skolengo API."""

    budget_version_id: UUID = Field(..., description="Budget version to sync")


class EnrollmentVariance(BaseModel):
    """Schema for enrollment variance between budget and actual."""

    level: str = Field(..., description="Academic level")
    nationality: str = Field(..., description="Nationality category")
    budget: int = Field(..., description="Budgeted enrollment")
    actual: int = Field(..., description="Actual enrollment")
    variance: int = Field(..., description="Variance (actual - budget)")
    variance_percent: float = Field(..., description="Variance percentage")


class SkolengoComparisonResponse(BaseModel):
    """Response schema for enrollment comparison."""

    variances: list[EnrollmentVariance] = Field(..., description="List of variances")
    total_budget: int = Field(..., description="Total budgeted enrollment")
    total_actual: int = Field(..., description="Total actual enrollment")
    total_variance: int = Field(..., description="Total variance")


# ============================================================================
# AEFE INTEGRATION SCHEMAS
# ============================================================================


class AEFEPositionRecord(BaseModel):
    """Schema for AEFE position record."""

    teacher_name: str | None = Field(None, description="Teacher name (optional)")
    category: str = Field(..., description="Position category (Detached, Funded, etc.)")
    cycle: str = Field(..., description="Cycle (Maternelle, Elementaire, Secondary)")
    prrd_rate: float = Field(..., description="PRRD contribution rate in EUR", ge=0)
    is_aefe_funded: bool = Field(
        False, description="Whether position is fully AEFE-funded (no school cost)"
    )


class AEFEImportRequest(BaseModel):
    """Request schema for importing AEFE positions."""

    # File will be uploaded via multipart/form-data, not in JSON body
    pass


class AEFEImportResponse(BaseModel):
    """Response schema for AEFE position import."""

    success: bool = Field(..., description="Whether import was successful")
    message: str = Field(..., description="Status message")
    records_imported: int = Field(..., description="Number of positions imported")
    log_id: UUID = Field(..., description="Integration log ID")


class AEFEPositionSummary(BaseModel):
    """Schema for AEFE position summary by category."""

    category: str = Field(..., description="Position category")
    cycle: str = Field(..., description="Cycle")
    count: int = Field(..., description="Number of positions")
    total_prrd: float = Field(..., description="Total PRRD contribution in EUR")


class AEFEPositionListResponse(BaseModel):
    """Response schema for listing AEFE positions."""

    positions: list[AEFEPositionSummary] = Field(..., description="Position summaries")
    total_positions: int = Field(..., description="Total number of positions")
    total_aefe_funded: int = Field(..., description="Number of AEFE-funded positions")
    total_prrd_contribution: float = Field(..., description="Total PRRD contribution in EUR")


# ============================================================================
# INTEGRATION SETTINGS SCHEMAS
# ============================================================================


class IntegrationSettingsCreate(BaseModel):
    """Request schema for creating integration settings."""

    integration_type: Literal["odoo", "skolengo", "aefe"] = Field(
        ..., description="Integration type"
    )
    config: dict[str, Any] = Field(..., description="Configuration data (will be encrypted)")
    auto_sync_enabled: bool = Field(False, description="Enable automatic syncing")
    auto_sync_interval_minutes: int | None = Field(
        None, description="Sync interval in minutes", ge=5
    )


class IntegrationSettingsUpdate(BaseModel):
    """Request schema for updating integration settings."""

    config: dict[str, Any] | None = Field(None, description="Updated configuration")
    is_active: bool | None = Field(None, description="Whether integration is active")
    auto_sync_enabled: bool | None = Field(None, description="Enable automatic syncing")
    auto_sync_interval_minutes: int | None = Field(
        None, description="Sync interval in minutes", ge=5
    )


class IntegrationSettingsResponse(BaseModel):
    """Response schema for integration settings."""

    id: UUID = Field(..., description="Settings ID")
    integration_type: str = Field(..., description="Integration type")
    config: dict[str, Any] = Field(
        ..., description="Configuration (sensitive data masked)"
    )
    is_active: bool = Field(..., description="Whether integration is active")
    last_sync_at: datetime | None = Field(None, description="Last sync timestamp")
    auto_sync_enabled: bool = Field(..., description="Whether auto-sync is enabled")
    auto_sync_interval_minutes: int | None = Field(None, description="Auto-sync interval")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


# ============================================================================
# INTEGRATION LOG SCHEMAS
# ============================================================================


class IntegrationLogResponse(BaseModel):
    """Response schema for integration log entry."""

    id: UUID = Field(..., description="Log ID")
    integration_type: str = Field(..., description="Integration type")
    action: str = Field(..., description="Action performed")
    status: str = Field(..., description="Operation status")
    records_processed: int = Field(..., description="Records processed")
    records_failed: int = Field(..., description="Records failed")
    error_message: str | None = Field(None, description="Error message if failed")
    metadata_json: dict[str, Any] | None = Field(None, description="Additional metadata")
    batch_id: UUID | None = Field(None, description="Batch ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by_id: UUID | None = Field(None, description="User who initiated the operation")

    class Config:
        """Pydantic config."""

        from_attributes = True


class IntegrationLogListResponse(BaseModel):
    """Response schema for listing integration logs."""

    logs: list[IntegrationLogResponse] = Field(..., description="List of log entries")
    total_count: int = Field(..., description="Total number of logs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")


# ============================================================================
# ACCOUNT MAPPING SCHEMAS
# ============================================================================


class AccountMappingConfig(BaseModel):
    """Configuration for Odoo to EFIR account mapping."""

    odoo_account: str = Field(..., description="Odoo account code")
    efir_account: str = Field(..., description="EFIR account code")
    description: str | None = Field(None, description="Mapping description")


class LevelMappingConfig(BaseModel):
    """Configuration for Skolengo to EFIR level mapping."""

    skolengo_level: str = Field(..., description="Skolengo level name")
    efir_level: str = Field(..., description="EFIR level code")
    cycle: str = Field(..., description="Educational cycle")
