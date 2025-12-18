"""
Pydantic schemas for cost planning endpoints.

Request and response models for:
- Personnel cost planning (64xxx accounts)
- Operating cost planning (60xxx-68xxx accounts)
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ==============================================================================
# Personnel Cost Planning Schemas
# ==============================================================================


class PersonnelCostPlanBase(BaseModel):
    """Base schema for personnel cost plan."""

    account_code: str = Field(..., max_length=20, description="PCG expense account (64xxx)")
    description: str = Field(..., description="Cost description")
    category_id: uuid.UUID | None = Field(
        None, description="Teacher category (NULL for non-teaching staff)"
    )
    cycle_id: uuid.UUID | None = Field(None, description="Academic cycle (NULL for admin/support)")
    fte_count: Decimal = Field(..., ge=Decimal("0"), description="Number of FTE")
    unit_cost_sar: Decimal = Field(..., ge=Decimal("0"), description="Cost per FTE (SAR/year)")
    total_cost_sar: Decimal = Field(..., ge=Decimal("0"), description="Total cost (FTE × unit_cost)")
    is_calculated: bool = Field(default=False, description="Whether auto-calculated from drivers")
    calculation_driver: str | None = Field(
        None, max_length=100, description="Driver (e.g., 'dhg_allocation', 'class_structure')"
    )
    notes: str | None = Field(None, description="Cost notes")

    @field_validator("account_code")
    @classmethod
    def validate_account_code(cls, v: str) -> str:
        """Validate account code is personnel expense account (64xxx)."""
        if not v.startswith("64"):
            raise ValueError(f"Personnel cost account code must start with 64, got {v}")
        return v


class PersonnelCostPlanCreate(PersonnelCostPlanBase):
    """Schema for creating personnel cost plan entry."""

    pass


class PersonnelCostPlanUpdate(BaseModel):
    """Schema for updating personnel cost plan entry."""

    account_code: str | None = Field(None, max_length=20)
    description: str | None = None
    category_id: uuid.UUID | None = None
    cycle_id: uuid.UUID | None = None
    fte_count: Decimal | None = Field(None, ge=Decimal("0"))
    unit_cost_sar: Decimal | None = Field(None, ge=Decimal("0"))
    total_cost_sar: Decimal | None = Field(None, ge=Decimal("0"))
    is_calculated: bool | None = None
    calculation_driver: str | None = Field(None, max_length=100)
    notes: str | None = None


class PersonnelCostPlanResponse(PersonnelCostPlanBase):
    """Schema for personnel cost plan response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonnelCostCalculationRequest(BaseModel):
    """Schema for personnel cost calculation request from DHG."""

    teacher_allocations: list[dict] = Field(..., description="Teacher allocation data from DHG")
    include_hsa: bool = Field(default=True, description="Include HSA (overtime) costs")
    eur_to_sar_rate: Decimal = Field(default=Decimal("4.05"), description="EUR to SAR exchange rate")


class PersonnelCostCalculationResponse(BaseModel):
    """Schema for personnel cost calculation response."""

    total_cost: Decimal = Field(..., description="Total personnel cost")
    cost_by_category: dict[str, Decimal] = Field(..., description="Cost by teacher category")
    cost_by_cycle: dict[str, Decimal] = Field(..., description="Cost by academic cycle")
    cost_by_account: dict[str, Decimal] = Field(..., description="Cost by account code")
    total_fte: Decimal = Field(..., description="Total FTE count")
    hsa_costs: Decimal | None = Field(None, description="Total HSA costs")
    calculation_details: dict = Field(..., description="Detailed calculation breakdown")


# ==============================================================================
# Operating Cost Planning Schemas
# ==============================================================================


class OperatingCostPlanBase(BaseModel):
    """Base schema for operating cost plan."""

    account_code: str = Field(..., max_length=20, description="PCG expense account (60xxx-68xxx)")
    description: str = Field(..., description="Expense description")
    category: str = Field(
        ..., max_length=50, description="Category (supplies, utilities, maintenance, insurance, etc.)"
    )
    amount_sar: Decimal = Field(..., ge=Decimal("0"), description="Expense amount in SAR")
    is_calculated: bool = Field(default=False, description="Whether auto-calculated from driver")
    calculation_driver: str | None = Field(
        None, max_length=100, description="Driver (e.g., 'enrollment', 'square_meters', 'fixed')"
    )
    notes: str | None = Field(None, description="Expense notes")

    @field_validator("account_code")
    @classmethod
    def validate_account_code(cls, v: str) -> str:
        """Validate account code is operating expense account (60xxx-68xxx)."""
        if not v.startswith(("60", "61", "62", "63", "65", "66", "68")):
            raise ValueError(f"Operating cost account code must start with 60-63, 65-66, or 68, got {v}")
        return v


class OperatingCostPlanCreate(OperatingCostPlanBase):
    """Schema for creating operating cost plan entry."""

    pass


class OperatingCostPlanUpdate(BaseModel):
    """Schema for updating operating cost plan entry."""

    account_code: str | None = Field(None, max_length=20)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    amount_sar: Decimal | None = Field(None, ge=Decimal("0"))
    is_calculated: bool | None = None
    calculation_driver: str | None = Field(None, max_length=100)
    notes: str | None = None


class OperatingCostPlanResponse(OperatingCostPlanBase):
    """Schema for operating cost plan response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OperatingCostCalculationRequest(BaseModel):
    """Schema for operating cost calculation request."""

    enrollment_count: int = Field(..., description="Total enrollment for enrollment-driven costs")
    square_meters: Decimal | None = Field(None, description="Total square meters for facility-driven costs")
    driver_rates: dict[str, Decimal] = Field(
        ..., description="Cost per driver unit (e.g., cost per student, cost per sqm)"
    )


class OperatingCostCalculationResponse(BaseModel):
    """Schema for operating cost calculation response."""

    total_cost: Decimal = Field(..., description="Total operating cost")
    cost_by_category: dict[str, Decimal] = Field(..., description="Cost by category")
    cost_by_account: dict[str, Decimal] = Field(..., description="Cost by account code")
    enrollment_driven_costs: Decimal = Field(..., description="Costs driven by enrollment")
    facility_driven_costs: Decimal = Field(..., description="Costs driven by facility size")
    fixed_costs: Decimal = Field(..., description="Fixed costs")
    calculation_details: dict = Field(..., description="Detailed calculation breakdown")
