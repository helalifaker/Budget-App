"""
Pydantic schemas for Class Structure Planning.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


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

    version_id: uuid.UUID


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
    version_id: uuid.UUID
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


class ClassStructureUpdateWithId(ClassStructureUpdate):
    """Schema for updating class structure entry with ID in bulk operations."""

    id: uuid.UUID


class ClassStructureBulkUpdate(BaseModel):
    """Schema for bulk updating class structures."""

    updates: list[ClassStructureUpdateWithId] = Field(
        ...,
        description="List of class structure updates",
    )
