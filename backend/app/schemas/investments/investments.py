"""
Pydantic schemas for investments (CapEx) planning endpoints.

Request and response models for:
- Capital expenditure planning
- Asset depreciation calculations
- Project budgets
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ==============================================================================
# CapEx Planning Schemas
# ==============================================================================


class CapExPlanBase(BaseModel):
    """Base schema for CapEx plan."""

    account_code: str = Field(..., max_length=20, description="PCG account code (20xxx-21xxx assets)")
    description: str = Field(..., description="Asset description")
    category: str = Field(
        ..., max_length=50, description="Category (equipment, IT, furniture, building, software)"
    )
    quantity: int = Field(..., ge=1, description="Number of units")
    unit_cost_sar: Decimal = Field(..., ge=Decimal("0"), description="Cost per unit (SAR)")
    total_cost_sar: Decimal = Field(..., ge=Decimal("0"), description="Total cost (quantity × unit_cost)")
    acquisition_date: date = Field(..., description="Expected acquisition date")
    useful_life_years: int = Field(..., ge=1, le=50, description="Depreciation life (years)")
    notes: str | None = Field(None, description="CapEx notes and justification")

    @field_validator("account_code")
    @classmethod
    def validate_account_code(cls, v: str) -> str:
        """Validate account code is asset account (20xxx-21xxx)."""
        if not v.startswith(("20", "21")):
            raise ValueError(f"CapEx account code must start with 20 or 21, got {v}")
        return v

    @field_validator("total_cost_sar")
    @classmethod
    def validate_total_cost(cls, v: Decimal, info) -> Decimal:
        """Validate total cost matches quantity × unit_cost."""
        data = info.data
        if "quantity" in data and "unit_cost_sar" in data:
            expected_total = Decimal(data["quantity"]) * data["unit_cost_sar"]
            if abs(v - expected_total) > Decimal("0.01"):
                raise ValueError(
                    f"Total cost ({v}) does not match quantity × unit_cost ({expected_total})"
                )
        return v


class CapExPlanCreate(CapExPlanBase):
    """Schema for creating CapEx plan entry."""

    pass


class CapExPlanUpdate(BaseModel):
    """Schema for updating CapEx plan entry."""

    account_code: str | None = Field(None, max_length=20)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    quantity: int | None = Field(None, ge=1)
    unit_cost_sar: Decimal | None = Field(None, ge=Decimal("0"))
    total_cost_sar: Decimal | None = Field(None, ge=Decimal("0"))
    acquisition_date: date | None = None
    useful_life_years: int | None = Field(None, ge=1, le=50)
    notes: str | None = None


class CapExPlanResponse(CapExPlanBase):
    """Schema for CapEx plan response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepreciationCalculationRequest(BaseModel):
    """Schema for depreciation calculation request."""

    asset_id: uuid.UUID = Field(..., description="CapEx asset ID")
    calculation_year: int = Field(..., ge=2020, le=2100, description="Year to calculate depreciation for")


class DepreciationCalculationResponse(BaseModel):
    """Schema for depreciation calculation response."""

    asset_id: uuid.UUID
    acquisition_cost: Decimal
    useful_life_years: int
    annual_depreciation: Decimal
    accumulated_depreciation: Decimal
    book_value: Decimal
    calculation_year: int
    is_fully_depreciated: bool
