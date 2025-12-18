"""
Pydantic schemas for Nationality Distributions.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class NationalityDistributionBase(BaseModel):
    """Base schema for nationality distribution."""

    level_id: uuid.UUID = Field(..., description="Academic level UUID")
    french_pct: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="French nationality percentage (0-100)",
    )
    saudi_pct: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="Saudi nationality percentage (0-100)",
    )
    other_pct: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="Other nationalities percentage (0-100)",
    )


class NationalityDistributionCreate(NationalityDistributionBase):
    """Schema for creating nationality distribution entry."""

    pass


class NationalityDistributionUpdate(BaseModel):
    """Schema for updating nationality distribution entry."""

    french_pct: Decimal | None = Field(None, ge=0, le=100)
    saudi_pct: Decimal | None = Field(None, ge=0, le=100)
    other_pct: Decimal | None = Field(None, ge=0, le=100)


class NationalityDistributionResponse(NationalityDistributionBase):
    """Schema for nationality distribution response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NationalityDistributionBulkUpdate(BaseModel):
    """Schema for bulk updating nationality distributions."""

    distributions: list[NationalityDistributionCreate] = Field(
        ...,
        description="List of distributions to upsert",
    )
