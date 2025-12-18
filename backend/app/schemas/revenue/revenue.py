"""
Pydantic schemas for revenue planning endpoints.

Request and response models for:
- Revenue planning (tuition, fees, other revenue)
- Revenue calculations from enrollment drivers
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Import engine models for calculation schemas
from app.engine.revenue.models import (
    StudentRevenueResult,
    TuitionInput,
)

# ==============================================================================
# Revenue Planning Schemas
# ==============================================================================


class RevenuePlanBase(BaseModel):
    """Base schema for revenue plan."""

    account_code: str = Field(..., max_length=20, description="PCG revenue account (70xxx-77xxx)")
    description: str = Field(..., description="Line item description")
    category: str = Field(..., max_length=50, description="Category (tuition, fees, other)")
    amount_sar: Decimal = Field(..., ge=Decimal("0"), description="Revenue amount in SAR")
    is_calculated: bool = Field(default=False, description="Whether auto-calculated from drivers")
    calculation_driver: str | None = Field(
        None, max_length=100, description="Driver reference (e.g., 'enrollment', 'fee_structure')"
    )
    trimester: int | None = Field(None, ge=1, le=3, description="Trimester (1-3) for tuition, NULL for annual")
    notes: str | None = Field(None, description="Revenue notes and assumptions")

    @field_validator("account_code")
    @classmethod
    def validate_account_code(cls, v: str) -> str:
        """Validate account code is revenue account (70xxx-77xxx)."""
        if not v.startswith(("70", "71", "72", "73", "74", "75", "76", "77")):
            raise ValueError(f"Revenue account code must start with 70-77, got {v}")
        return v


class RevenuePlanCreate(RevenuePlanBase):
    """Schema for creating revenue plan entry."""

    pass


class RevenuePlanUpdate(BaseModel):
    """Schema for updating revenue plan entry."""

    account_code: str | None = Field(None, max_length=20)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    amount_sar: Decimal | None = Field(None, ge=Decimal("0"))
    is_calculated: bool | None = None
    calculation_driver: str | None = Field(None, max_length=100)
    trimester: int | None = Field(None, ge=1, le=3)
    notes: str | None = None


class RevenuePlanResponse(RevenuePlanBase):
    """Schema for revenue plan response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RevenueBulkUpdateItem(BaseModel):
    """Schema for a single item in bulk update."""

    id: uuid.UUID
    amount_sar: Decimal | None = Field(None, ge=Decimal("0"))
    notes: str | None = None


class RevenueBulkUpdateRequest(BaseModel):
    """Schema for bulk update request."""

    updates: list[RevenueBulkUpdateItem]


class RevenueBulkUpdateResponse(BaseModel):
    """Schema for bulk update response."""

    success: bool
    count: int


class RevenueCalculationRequest(BaseModel):
    """Schema for revenue calculation request from enrollment."""

    enrollment_data: list[dict] = Field(..., description="Enrollment data for calculation")
    sibling_data: list[dict] | None = Field(None, description="Sibling discount data")
    include_trimester_split: bool = Field(default=True, description="Split revenue by trimester")


class RevenueCalculationResponse(BaseModel):
    """Schema for revenue calculation response."""

    total_revenue: Decimal = Field(..., description="Total calculated revenue")
    revenue_by_level: dict[str, Decimal] = Field(..., description="Revenue by academic level")
    revenue_by_category: dict[str, Decimal] = Field(..., description="Revenue by fee category")
    revenue_by_account: dict[str, Decimal] = Field(..., description="Revenue by account code")
    trimester_distribution: dict[str, Decimal] | None = Field(None, description="Trimester split")
    sibling_discounts_applied: Decimal = Field(..., description="Total sibling discounts")
    calculation_details: dict = Field(..., description="Detailed calculation breakdown")


# ==============================================================================
# Engine Model Aliases (for API compatibility)
# ==============================================================================

# Reuse engine models for calculation layer
EngineRevenueInput = TuitionInput
EngineRevenueResult = StudentRevenueResult
