"""
Pydantic schemas for configuration endpoints.

Request and response models for configuration API operations.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.configuration import BudgetVersionStatus

# ==============================================================================
# System Configuration Schemas
# ==============================================================================


class SystemConfigBase(BaseModel):
    """Base schema for system configuration."""

    key: str = Field(..., max_length=100, description="Configuration key")
    value: dict[str, Any] = Field(..., description="Configuration value (JSONB)")
    category: str = Field(..., max_length=50, description="Configuration category")
    description: str = Field(..., description="Configuration description")
    is_active: bool = Field(default=True, description="Whether configuration is active")


class SystemConfigCreate(SystemConfigBase):
    """Schema for creating system configuration."""

    pass


class SystemConfigUpdate(BaseModel):
    """Schema for updating system configuration."""

    value: dict[str, Any] | None = None
    category: str | None = Field(None, max_length=50)
    description: str | None = None
    is_active: bool | None = None


class SystemConfigResponse(SystemConfigBase):
    """Schema for system configuration response."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Budget Version Schemas
# ==============================================================================


class BudgetVersionBase(BaseModel):
    """Base schema for budget version."""

    name: str = Field(..., max_length=100, description="Version name")
    fiscal_year: int = Field(..., ge=2020, le=2100, description="Fiscal year")
    academic_year: str = Field(..., max_length=20, description="Academic year (e.g., '2025-2026')")
    notes: str | None = Field(None, description="Version notes")


class BudgetVersionCreate(BudgetVersionBase):
    """Schema for creating budget version."""

    parent_version_id: uuid.UUID | None = Field(None, description="Parent version for forecast revisions")


class BudgetVersionUpdate(BaseModel):
    """Schema for updating budget version."""

    name: str | None = Field(None, max_length=100)
    notes: str | None = None


class BudgetVersionResponse(BudgetVersionBase):
    """Schema for budget version response."""

    id: uuid.UUID
    status: BudgetVersionStatus
    submitted_at: datetime | None = None
    submitted_by_id: uuid.UUID | None = None
    approved_at: datetime | None = None
    approved_by_id: uuid.UUID | None = None
    is_baseline: bool
    parent_version_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Academic Reference Data Schemas
# ==============================================================================


class AcademicCycleResponse(BaseModel):
    """Schema for academic cycle response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    sort_order: int
    requires_atsem: bool

    model_config = ConfigDict(from_attributes=True)


class AcademicLevelResponse(BaseModel):
    """Schema for academic level response."""

    id: uuid.UUID
    cycle_id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    sort_order: int
    is_secondary: bool

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Class Size Parameters Schemas
# ==============================================================================


class ClassSizeParamBase(BaseModel):
    """Base schema for class size parameters."""

    level_id: uuid.UUID | None = Field(None, description="Academic level (None for cycle default)")
    cycle_id: uuid.UUID | None = Field(None, description="Academic cycle (None for level-specific)")
    min_class_size: int = Field(..., ge=1, le=50, description="Minimum class size")
    target_class_size: int = Field(..., ge=1, le=50, description="Target class size")
    max_class_size: int = Field(..., ge=1, le=50, description="Maximum class size")
    notes: str | None = None

    @field_validator("target_class_size")
    @classmethod
    def validate_target(cls, v: int, info) -> int:
        """Validate target is greater than min."""
        min_size = info.data.get("min_class_size")
        if min_size and v <= min_size:
            raise ValueError("target_class_size must be greater than min_class_size")
        return v

    @field_validator("max_class_size")
    @classmethod
    def validate_max(cls, v: int, info) -> int:
        """Validate max is greater than or equal to target."""
        target_size = info.data.get("target_class_size")
        if target_size and v < target_size:
            raise ValueError("max_class_size must be greater than or equal to target_class_size")
        return v


class ClassSizeParamCreate(ClassSizeParamBase):
    """Schema for creating class size parameter."""

    budget_version_id: uuid.UUID


class ClassSizeParamUpdate(BaseModel):
    """Schema for updating class size parameter."""

    min_class_size: int | None = Field(None, ge=1, le=50)
    target_class_size: int | None = Field(None, ge=1, le=50)
    max_class_size: int | None = Field(None, ge=1, le=50)
    notes: str | None = None


class ClassSizeParamResponse(ClassSizeParamBase):
    """Schema for class size parameter response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Subject Hours Matrix Schemas
# ==============================================================================


class SubjectResponse(BaseModel):
    """Schema for subject response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    category: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SubjectHoursBase(BaseModel):
    """Base schema for subject hours."""

    subject_id: uuid.UUID
    level_id: uuid.UUID
    hours_per_week: Decimal = Field(..., ge=0, le=12, decimal_places=2, description="Hours per week per class")
    is_split: bool = Field(default=False, description="Whether classes are split (half-size groups)")
    notes: str | None = None


class SubjectHoursCreate(SubjectHoursBase):
    """Schema for creating subject hours."""

    budget_version_id: uuid.UUID


class SubjectHoursUpdate(BaseModel):
    """Schema for updating subject hours."""

    hours_per_week: Decimal | None = Field(None, ge=0, le=12, decimal_places=2)
    is_split: bool | None = None
    notes: str | None = None


class SubjectHoursResponse(SubjectHoursBase):
    """Schema for subject hours response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Teacher Cost Parameters Schemas
# ==============================================================================


class TeacherCategoryResponse(BaseModel):
    """Schema for teacher category response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    description: str | None
    is_aefe: bool

    model_config = ConfigDict(from_attributes=True)


class TeacherCostParamBase(BaseModel):
    """Base schema for teacher cost parameters."""

    category_id: uuid.UUID
    cycle_id: uuid.UUID | None = Field(None, description="Academic cycle (None for all cycles)")
    prrd_contribution_eur: Decimal | None = Field(
        None,
        ge=0,
        decimal_places=2,
        description="PRRD contribution per teacher (EUR, for AEFE detached)",
    )
    avg_salary_sar: Decimal | None = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Average salary (SAR/year, for local teachers)",
    )
    social_charges_rate: Decimal = Field(
        default=Decimal("0.21"),
        ge=0,
        le=1,
        decimal_places=4,
        description="Social charges rate (e.g., 0.21 for 21%)",
    )
    benefits_allowance_sar: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
        description="Benefits/allowances per teacher (SAR/year)",
    )
    hsa_hourly_rate_sar: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="HSA (overtime) hourly rate (SAR)",
    )
    max_hsa_hours: Decimal = Field(
        default=Decimal("4.00"),
        ge=0,
        le=10,
        decimal_places=2,
        description="Maximum HSA hours per teacher per week",
    )
    notes: str | None = None


class TeacherCostParamCreate(TeacherCostParamBase):
    """Schema for creating teacher cost parameter."""

    budget_version_id: uuid.UUID


class TeacherCostParamUpdate(BaseModel):
    """Schema for updating teacher cost parameter."""

    prrd_contribution_eur: Decimal | None = Field(None, ge=0, decimal_places=2)
    avg_salary_sar: Decimal | None = Field(None, ge=0, decimal_places=2)
    social_charges_rate: Decimal | None = Field(None, ge=0, le=1, decimal_places=4)
    benefits_allowance_sar: Decimal | None = Field(None, ge=0, decimal_places=2)
    hsa_hourly_rate_sar: Decimal | None = Field(None, ge=0, decimal_places=2)
    max_hsa_hours: Decimal | None = Field(None, ge=0, le=10, decimal_places=2)
    notes: str | None = None


class TeacherCostParamResponse(TeacherCostParamBase):
    """Schema for teacher cost parameter response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Fee Structure Schemas
# ==============================================================================


class FeeCategoryResponse(BaseModel):
    """Schema for fee category response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    account_code: str
    is_recurring: bool
    allows_sibling_discount: bool

    model_config = ConfigDict(from_attributes=True)


class NationalityTypeResponse(BaseModel):
    """Schema for nationality type response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    vat_applicable: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class FeeStructureBase(BaseModel):
    """Base schema for fee structure."""

    level_id: uuid.UUID
    nationality_type_id: uuid.UUID
    fee_category_id: uuid.UUID
    amount_sar: Decimal = Field(..., ge=0, decimal_places=2, description="Fee amount in SAR")
    trimester: int | None = Field(None, ge=1, le=3, description="Trimester (1-3) for tuition, None for annual fees")
    notes: str | None = None


class FeeStructureCreate(FeeStructureBase):
    """Schema for creating fee structure."""

    budget_version_id: uuid.UUID


class FeeStructureUpdate(BaseModel):
    """Schema for updating fee structure."""

    amount_sar: Decimal | None = Field(None, ge=0, decimal_places=2)
    notes: str | None = None


class FeeStructureResponse(FeeStructureBase):
    """Schema for fee structure response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Timetable Constraints Schemas (Module 6)
# ============================================================================


class TimetableConstraintBase(BaseModel):
    """Base schema for timetable constraints."""

    level_id: uuid.UUID = Field(..., description="Academic level")
    total_hours_per_week: Decimal = Field(
        ..., ge=0, le=60, decimal_places=2, description="Total student hours per week"
    )
    max_hours_per_day: Decimal = Field(
        ..., ge=0, le=12, decimal_places=2, description="Maximum hours per day"
    )
    days_per_week: int = Field(..., ge=4, le=6, description="School days per week")
    requires_lunch_break: bool = Field(
        True, description="Whether lunch break is required"
    )
    min_break_duration_minutes: int = Field(
        60, ge=30, le=120, description="Minimum break duration (minutes)"
    )
    notes: str | None = None


class TimetableConstraintCreate(TimetableConstraintBase):
    """Schema for creating timetable constraint."""

    budget_version_id: uuid.UUID = Field(..., description="Budget version")

    @model_validator(mode="after")
    def validate_max_hours(self) -> "TimetableConstraintCreate":
        """Validate max_hours_per_day ≤ total_hours_per_week."""
        if self.max_hours_per_day > self.total_hours_per_week:
            raise ValueError(
                "max_hours_per_day cannot exceed total_hours_per_week"
            )
        return self


class TimetableConstraintUpdate(BaseModel):
    """Schema for updating timetable constraint."""

    budget_version_id: uuid.UUID | None = None
    level_id: uuid.UUID | None = None
    total_hours_per_week: Decimal | None = Field(
        None, ge=0, le=60, decimal_places=2
    )
    max_hours_per_day: Decimal | None = Field(None, ge=0, le=12, decimal_places=2)
    days_per_week: int | None = Field(None, ge=4, le=6)
    requires_lunch_break: bool | None = None
    min_break_duration_minutes: int | None = Field(None, ge=30, le=120)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_max_hours(self) -> "TimetableConstraintUpdate":
        """Validate max_hours_per_day ≤ total_hours_per_week if both provided."""
        if (
            self.max_hours_per_day is not None
            and self.total_hours_per_week is not None
            and self.max_hours_per_day > self.total_hours_per_week
        ):
            raise ValueError(
                "max_hours_per_day cannot exceed total_hours_per_week"
            )
        return self


class TimetableConstraintResponse(TimetableConstraintBase):
    """Schema for timetable constraint response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
