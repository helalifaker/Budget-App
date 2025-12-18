"""API schemas for DHG endpoints."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.engine.workforce.dhg.models import (
    DHGHoursResult,
    DHGInput,
)

# Reuse engine models for API layer
DHGCalculationRequest = DHGInput
DHGCalculationResponse = DHGHoursResult


# ==============================================================================
# DHG Subject Hours Schemas
# ==============================================================================


class DHGSubjectHoursBase(BaseModel):
    """Base schema for DHG subject hours."""

    subject_id: uuid.UUID = Field(..., description="Subject UUID")
    level_id: uuid.UUID = Field(..., description="Academic level UUID")
    number_of_classes: int = Field(..., gt=0, description="Number of classes")
    hours_per_class_per_week: Decimal = Field(
        ..., gt=0, le=12, description="Hours per class per week", decimal_places=2
    )
    total_hours_per_week: Decimal = Field(
        ..., ge=0, description="Total hours per week", decimal_places=2
    )
    is_split: bool = Field(default=False, description="Whether classes are split")


class DHGSubjectHoursCreate(DHGSubjectHoursBase):
    """Schema for creating DHG subject hours entry."""

    version_id: uuid.UUID


class DHGSubjectHoursUpdate(BaseModel):
    """Schema for updating DHG subject hours entry."""

    number_of_classes: int | None = Field(None, gt=0)
    hours_per_class_per_week: Decimal | None = Field(None, gt=0, le=12, decimal_places=2)
    total_hours_per_week: Decimal | None = Field(None, ge=0, decimal_places=2)
    is_split: bool | None = None


class DHGSubjectHoursResponse(DHGSubjectHoursBase):
    """Schema for DHG subject hours response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DHGHoursCalculationRequest(BaseModel):
    """Request for DHG hours calculation."""

    recalculate_all: bool = Field(
        default=True,
        description="Whether to recalculate all levels or only changed ones",
    )


# ==============================================================================
# DHG Teacher Requirements Schemas
# ==============================================================================


class DHGTeacherRequirementBase(BaseModel):
    """Base schema for DHG teacher requirements."""

    subject_id: uuid.UUID = Field(..., description="Subject UUID")
    total_hours_per_week: Decimal = Field(
        ..., ge=0, description="Total hours per week", decimal_places=2
    )
    standard_teaching_hours: Decimal = Field(
        ..., gt=0, description="Standard teaching hours", decimal_places=2
    )
    simple_fte: Decimal = Field(..., ge=0, description="Simple FTE", decimal_places=2)
    rounded_fte: int = Field(..., ge=0, description="Rounded FTE")
    hsa_hours: Decimal = Field(
        default=Decimal("0.00"), description="HSA overtime hours", decimal_places=2
    )


class DHGTeacherRequirementCreate(DHGTeacherRequirementBase):
    """Schema for creating DHG teacher requirement entry."""

    version_id: uuid.UUID


class DHGTeacherRequirementUpdate(BaseModel):
    """Schema for updating DHG teacher requirement entry."""

    total_hours_per_week: Decimal | None = Field(None, ge=0, decimal_places=2)
    standard_teaching_hours: Decimal | None = Field(None, gt=0, decimal_places=2)
    simple_fte: Decimal | None = Field(None, ge=0, decimal_places=2)
    rounded_fte: int | None = Field(None, ge=0)
    hsa_hours: Decimal | None = Field(None, decimal_places=2)


class DHGTeacherRequirementResponse(DHGTeacherRequirementBase):
    """Schema for DHG teacher requirement response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FTECalculationRequest(BaseModel):
    """Request for FTE calculation."""

    recalculate_all: bool = Field(
        default=True,
        description="Whether to recalculate all subjects or only changed ones",
    )


# ==============================================================================
# Teacher Allocation Schemas
# ==============================================================================


class TeacherAllocationBase(BaseModel):
    """Base schema for teacher allocation."""

    subject_id: uuid.UUID = Field(..., description="Subject UUID")
    cycle_id: uuid.UUID = Field(..., description="Academic cycle UUID")
    category_id: uuid.UUID = Field(..., description="Teacher category UUID")
    fte_count: Decimal = Field(..., gt=0, description="FTE count", decimal_places=2)
    notes: str | None = None


class TeacherAllocationCreate(TeacherAllocationBase):
    """Schema for creating teacher allocation entry."""

    version_id: uuid.UUID


class TeacherAllocationUpdate(BaseModel):
    """Schema for updating teacher allocation entry."""

    fte_count: Decimal | None = Field(None, gt=0, decimal_places=2)
    notes: str | None = None


class TeacherAllocationResponse(TeacherAllocationBase):
    """Schema for teacher allocation response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeacherAllocationBulkUpdate(BaseModel):
    """Request for bulk updating teacher allocations."""

    allocations: list[TeacherAllocationCreate] = Field(
        ..., description="List of allocations to create/update"
    )


# ==============================================================================
# TRMD (Gap Analysis) Schemas
# ==============================================================================


class TRMDGapAnalysis(BaseModel):
    """TRMD gap analysis result."""

    subject_id: uuid.UUID
    subject_code: str
    subject_name: str
    cycle_id: uuid.UUID | None
    cycle_code: str | None
    besoins_fte: Decimal = Field(..., description="Teacher needs (DHG requirements)")
    moyens_fte: Decimal = Field(..., description="Available teachers (allocations)")
    deficit_fte: Decimal = Field(..., description="Gap (besoins - moyens)")
    status: str = Field(..., description="Status: deficit, balanced, surplus")


class TRMDGapAnalysisResponse(BaseModel):
    """Response containing all TRMD gap analyses."""

    version_id: uuid.UUID
    total_besoins: Decimal
    total_moyens: Decimal
    total_deficit: Decimal
    by_subject: list[TRMDGapAnalysis]
    by_cycle: dict[str, Decimal] = Field(..., description="Deficit by cycle")
