"""
Pydantic schemas for historical comparison feature.

These schemas define request/response models for the historical comparison API,
enabling comparison of current budget planning against 2 years of prior actuals.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Historical Data Point Schemas
# =============================================================================


class HistoricalDataPoint(BaseModel):
    """Single historical data point for a specific fiscal year."""

    fiscal_year: int = Field(..., description="Fiscal year of the data")
    value: Decimal | int | None = Field(None, description="The actual value")
    is_actual: bool = Field(True, description="Whether this is actual data (vs projected)")

    model_config = ConfigDict(from_attributes=True)


class HistoricalComparison(BaseModel):
    """
    Historical comparison data showing N-2, N-1, and current values
    with absolute and percentage changes.
    """

    n_minus_2: HistoricalDataPoint | None = Field(
        None, description="Data from 2 fiscal years ago"
    )
    n_minus_1: HistoricalDataPoint | None = Field(
        None, description="Data from 1 fiscal year ago"
    )
    current: Decimal | int = Field(..., description="Current plan value")

    # Variance vs N-1
    vs_n_minus_1_abs: Decimal | int | None = Field(
        None, description="Absolute change vs prior year"
    )
    vs_n_minus_1_pct: Decimal | None = Field(
        None, description="Percentage change vs prior year"
    )

    # Variance vs N-2
    vs_n_minus_2_abs: Decimal | int | None = Field(
        None, description="Absolute change vs 2 years ago"
    )
    vs_n_minus_2_pct: Decimal | None = Field(
        None, description="Percentage change vs 2 years ago"
    )

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Enrollment with History
# =============================================================================


class EnrollmentWithHistoryRow(BaseModel):
    """Enrollment data row with historical comparison."""

    level_id: UUID = Field(..., description="Level UUID")
    level_code: str = Field(..., description="Level code (e.g., '6EME', 'CP')")
    level_name: str = Field(..., description="Level display name")
    student_count: int = Field(..., description="Current plan student count")
    history: HistoricalComparison = Field(..., description="Historical comparison data")

    model_config = ConfigDict(from_attributes=True)


class EnrollmentWithHistoryResponse(BaseModel):
    """Response containing enrollment data with historical columns."""

    version_id: UUID
    fiscal_year: int
    current_fiscal_year: int
    rows: list[EnrollmentWithHistoryRow]
    totals: HistoricalComparison = Field(..., description="Total student count comparison")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Class Structure with History
# =============================================================================


class ClassStructureWithHistoryRow(BaseModel):
    """Class structure data row with historical comparison."""

    level_id: UUID = Field(..., description="Level UUID")
    level_code: str = Field(..., description="Level code")
    level_name: str = Field(..., description="Level display name")
    class_count: int = Field(..., description="Current plan class count")
    average_class_size: Decimal = Field(..., description="Average students per class")
    history: HistoricalComparison = Field(..., description="Historical class count comparison")

    model_config = ConfigDict(from_attributes=True)


class ClassStructureWithHistoryResponse(BaseModel):
    """Response containing class structure with historical columns."""

    version_id: UUID
    fiscal_year: int
    current_fiscal_year: int
    rows: list[ClassStructureWithHistoryRow]
    totals: HistoricalComparison

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# DHG with History
# =============================================================================


class DHGWithHistoryRow(BaseModel):
    """DHG data row with historical comparison."""

    subject_id: UUID | None = Field(None, description="Subject UUID (if applicable)")
    subject_code: str = Field(..., description="Subject code (e.g., 'MATH', 'FRAN')")
    subject_name: str = Field(..., description="Subject display name")
    total_hours: Decimal = Field(..., description="Current plan total hours")
    fte: Decimal = Field(..., description="Current plan FTE")
    hours_history: HistoricalComparison = Field(..., description="Historical hours comparison")
    fte_history: HistoricalComparison = Field(..., description="Historical FTE comparison")

    model_config = ConfigDict(from_attributes=True)


class DHGWithHistoryResponse(BaseModel):
    """Response containing DHG data with historical columns."""

    version_id: UUID
    fiscal_year: int
    current_fiscal_year: int
    rows: list[DHGWithHistoryRow]
    totals_hours: HistoricalComparison
    totals_fte: HistoricalComparison

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Revenue with History
# =============================================================================


class RevenueWithHistoryRow(BaseModel):
    """Revenue data row with historical comparison."""

    account_code: str = Field(..., description="PCG account code")
    account_name: str = Field(..., description="Account display name")
    fee_type: str | None = Field(None, description="Fee type category")
    amount_sar: Decimal = Field(..., description="Current plan revenue amount")
    history: HistoricalComparison = Field(..., description="Historical revenue comparison")

    model_config = ConfigDict(from_attributes=True)


class RevenueWithHistoryResponse(BaseModel):
    """Response containing revenue data with historical columns."""

    version_id: UUID
    fiscal_year: int
    current_fiscal_year: int
    rows: list[RevenueWithHistoryRow]
    totals: HistoricalComparison

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Costs with History
# =============================================================================


class CostsWithHistoryRow(BaseModel):
    """Costs data row with historical comparison."""

    account_code: str = Field(..., description="PCG account code")
    account_name: str = Field(..., description="Account display name")
    cost_category: str | None = Field(None, description="Cost category")
    amount_sar: Decimal = Field(..., description="Current plan cost amount")
    history: HistoricalComparison = Field(..., description="Historical cost comparison")

    model_config = ConfigDict(from_attributes=True)


class CostsWithHistoryResponse(BaseModel):
    """Response containing costs data with historical columns."""

    version_id: UUID
    fiscal_year: int
    current_fiscal_year: int
    rows: list[CostsWithHistoryRow]
    totals: HistoricalComparison
    personnel_totals: HistoricalComparison | None = None
    operating_totals: HistoricalComparison | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# CapEx with History
# =============================================================================


class CapExWithHistoryRow(BaseModel):
    """CapEx data row with historical comparison."""

    account_code: str = Field(..., description="PCG account code")
    account_name: str = Field(..., description="Account display name")
    category: str | None = Field(None, description="CapEx category")
    amount_sar: Decimal = Field(..., description="Current plan CapEx amount")
    history: HistoricalComparison = Field(..., description="Historical CapEx comparison")

    model_config = ConfigDict(from_attributes=True)


class CapExWithHistoryResponse(BaseModel):
    """Response containing CapEx data with historical columns."""

    version_id: UUID
    fiscal_year: int
    current_fiscal_year: int
    rows: list[CapExWithHistoryRow]
    totals: HistoricalComparison

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Impact Calculation
# =============================================================================


class ImpactCalculationRequest(BaseModel):
    """Request for real-time impact calculation."""

    version_id: UUID = Field(..., description="Budget version to calculate impact for")
    changes: list[dict] = Field(
        ..., description="List of proposed changes with dimension_code and new_value"
    )
    module: str = Field(
        ..., description="Module code: enrollment, dhg, revenue, costs, capex"
    )


class ImpactCalculationResponse(BaseModel):
    """Response with calculated impact metrics."""

    version_id: UUID
    module: str

    # Impact metrics
    fte_change: Decimal | None = Field(None, description="Change in FTE (for enrollment/DHG)")
    cost_impact_sar: Decimal | None = Field(None, description="Impact on costs")
    revenue_impact_sar: Decimal | None = Field(None, description="Impact on revenue")
    margin_impact_pct: Decimal | None = Field(None, description="Impact on operating margin")

    # Comparison details
    current_value: Decimal | int
    proposed_value: Decimal | int
    vs_n_minus_1_pct: Decimal | None = Field(
        None, description="Proposed value vs prior year %"
    )

    calculation_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When calculation was performed"
    )

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Historical Import Schemas
# =============================================================================


class HistoricalImportRecord(BaseModel):
    """Single record for historical data import."""

    fiscal_year: int = Field(..., ge=2020, le=2099)
    dimension_code: str = Field(..., max_length=50)
    dimension_name: str | None = Field(None, max_length=200)
    value: Decimal | int = Field(..., description="The value to import")


class HistoricalImportRequest(BaseModel):
    """Request for importing historical data."""

    module: str = Field(
        ..., description="Module code: enrollment, dhg, revenue, costs, capex"
    )
    dimension_type: str = Field(
        ..., description="Dimension type: level, subject, account_code, etc."
    )
    records: list[HistoricalImportRecord] = Field(..., min_length=1)
    overwrite: bool = Field(
        False, description="Whether to overwrite existing data for the same period"
    )


class HistoricalImportResult(BaseModel):
    """Result of historical data import."""

    success: bool
    records_imported: int
    records_skipped: int
    records_updated: int
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    import_batch_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Query Parameters
# =============================================================================


class HistoricalQueryParams(BaseModel):
    """Query parameters for historical data endpoints."""

    include_history: bool = Field(True, description="Include historical comparison columns")
    history_years: int = Field(2, ge=1, le=5, description="Number of historical years")

    model_config = ConfigDict(from_attributes=True)
