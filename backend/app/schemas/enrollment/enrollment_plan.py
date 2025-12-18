"""
Enrollment Plan Schemas.

Request and response models for enrollment planning operations (student count inputs).
Migrated from legacy settings/planning.py.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enrollment.distributions import (
    NationalityDistributionCreate,
    NationalityDistributionResponse,
)


class EnrollmentPlanBase(BaseModel):
    """Base schema for enrollment plan."""

    level_id: uuid.UUID = Field(..., description="Academic level UUID")
    nationality_type_id: uuid.UUID = Field(..., description="Nationality type UUID")
    student_count: int = Field(..., ge=0, description="Projected number of students")
    notes: str | None = Field(None, description="Enrollment notes and assumptions")


class EnrollmentPlanCreate(EnrollmentPlanBase):
    """Schema for creating enrollment plan entry."""

    version_id: uuid.UUID


class EnrollmentPlanUpdate(BaseModel):
    """Schema for updating enrollment plan entry."""

    student_count: int | None = Field(None, ge=0)
    notes: str | None = None


class EnrollmentPlanResponse(EnrollmentPlanBase):
    """Schema for enrollment plan response."""

    id: uuid.UUID
    version_id: uuid.UUID
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


class EnrollmentTotalCreate(BaseModel):
    """Schema for enrollment total by level (without nationality breakdown)."""

    level_id: uuid.UUID = Field(..., description="Academic level UUID")
    total_students: int = Field(..., ge=0, description="Total students at this level")


class EnrollmentTotalsBulkUpdate(BaseModel):
    """Schema for bulk updating enrollment totals."""

    totals: list[EnrollmentTotalCreate] = Field(
        ...,
        description="List of enrollment totals by level",
    )


class EnrollmentBreakdownResponse(BaseModel):
    """Calculated enrollment breakdown by level and nationality."""

    level_id: uuid.UUID
    level_code: str
    level_name: str
    cycle_code: str
    total_students: int
    french_count: int
    saudi_count: int
    other_count: int
    french_pct: Decimal
    saudi_pct: Decimal
    other_pct: Decimal


class EnrollmentWithDistributionResponse(BaseModel):
    """Complete enrollment response with distribution and breakdown."""

    totals: list[EnrollmentTotalCreate]
    distributions: list[NationalityDistributionResponse]
    breakdown: list[EnrollmentBreakdownResponse]
    summary: EnrollmentSummary
