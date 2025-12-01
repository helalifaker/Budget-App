"""
Pydantic schemas for planning endpoints.

Request and response models for planning API operations:
- Enrollment planning
- Class structure planning
- DHG workforce planning (subject hours, teacher requirements, allocations)
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# Enrollment Planning Schemas
# ==============================================================================


class EnrollmentPlanBase(BaseModel):
    """Base schema for enrollment plan."""

    level_id: uuid.UUID = Field(..., description="Academic level UUID")
    nationality_type_id: uuid.UUID = Field(..., description="Nationality type UUID")
    student_count: int = Field(..., ge=0, description="Projected number of students")
    notes: str | None = Field(None, description="Enrollment notes and assumptions")


class EnrollmentPlanCreate(EnrollmentPlanBase):
    """Schema for creating enrollment plan entry."""

    budget_version_id: uuid.UUID


class EnrollmentPlanUpdate(BaseModel):
    """Schema for updating enrollment plan entry."""

    student_count: int | None = Field(None, ge=0)
    notes: str | None = None


class EnrollmentPlanResponse(EnrollmentPlanBase):
    """Schema for enrollment plan response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnrollmentSummary(BaseModel):
    """Summary statistics for enrollment."""

    total_students: int = Field(..., description="Total student count")
    by_level: dict[str, int] = Field(..., description="Student count by level code")
    by_cycle: dict[str, int] = Field(..., description="Student count by cycle code")
    by_nationality: dict[str, int] = Field(..., description="Student count by nationality")
    capacity_utilization: Decimal = Field(..., description="Capacity utilization percentage")


class EnrollmentProjectionRequest(BaseModel):
    """Request for enrollment projection calculation."""

    years_to_project: int = Field(..., ge=1, le=10, description="Number of years to project")
    growth_scenario: str = Field(
        default="base",
        description="Growth scenario: conservative, base, optimistic",
    )
    custom_growth_rates: dict[str, Decimal] | None = Field(
        None,
        description="Optional custom growth rates by level_id",
    )


# ==============================================================================
# Class Structure Planning Schemas
# ==============================================================================


class ClassStructureBase(BaseModel):
    """Base schema for class structure."""

    level_id: uuid.UUID = Field(..., description="Academic level UUID")
    total_students: int = Field(..., ge=0, description="Total students at this level")
    number_of_classes: int = Field(..., gt=0, description="Number of classes formed")
    avg_class_size: Decimal = Field(
        ..., gt=0, le=50, description="Average class size", decimal_places=2
    )
    requires_atsem: bool = Field(default=False, description="Whether ATSEM is required")
    atsem_count: int = Field(..., ge=0, description="Number of ATSEM needed")
    calculation_method: str = Field(
        default="target", description="Method used (target, min, max, custom)"
    )
    notes: str | None = None


class ClassStructureCreate(ClassStructureBase):
    """Schema for creating class structure entry."""

    budget_version_id: uuid.UUID


class ClassStructureUpdate(BaseModel):
    """Schema for updating class structure entry."""

    total_students: int | None = Field(None, ge=0)
    number_of_classes: int | None = Field(None, gt=0)
    avg_class_size: Decimal | None = Field(None, gt=0, le=50, decimal_places=2)
    requires_atsem: bool | None = None
    atsem_count: int | None = Field(None, ge=0)
    calculation_method: str | None = None
    notes: str | None = None


class ClassStructureResponse(ClassStructureBase):
    """Schema for class structure response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassStructureCalculationRequest(BaseModel):
    """Request for class structure calculation."""

    method: str = Field(
        default="target",
        description="Calculation method: target, min, max",
    )
    override_by_level: dict[str, int] | None = Field(
        None,
        description="Optional manual override for specific level_ids",
    )


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

    budget_version_id: uuid.UUID


class DHGSubjectHoursUpdate(BaseModel):
    """Schema for updating DHG subject hours entry."""

    number_of_classes: int | None = Field(None, gt=0)
    hours_per_class_per_week: Decimal | None = Field(None, gt=0, le=12, decimal_places=2)
    total_hours_per_week: Decimal | None = Field(None, ge=0, decimal_places=2)
    is_split: bool | None = None


class DHGSubjectHoursResponse(DHGSubjectHoursBase):
    """Schema for DHG subject hours response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
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

    budget_version_id: uuid.UUID


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
    budget_version_id: uuid.UUID
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

    budget_version_id: uuid.UUID


class TeacherAllocationUpdate(BaseModel):
    """Schema for updating teacher allocation entry."""

    fte_count: Decimal | None = Field(None, gt=0, decimal_places=2)
    notes: str | None = None


class TeacherAllocationResponse(TeacherAllocationBase):
    """Schema for teacher allocation response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
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

    budget_version_id: uuid.UUID
    total_besoins: Decimal
    total_moyens: Decimal
    total_deficit: Decimal
    by_subject: list[TRMDGapAnalysis]
    by_cycle: dict[str, Decimal] = Field(..., description="Deficit by cycle")
