"""
Pydantic schemas for Enrollment Projection endpoints.

These mirror the projection config/override/result structures used by the
Retention + Lateral Entry enrollment projection system.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# Scenarios
# ==============================================================================


class EnrollmentScenarioResponse(BaseModel):
    id: uuid.UUID
    code: str
    name_en: str
    name_fr: str
    description_en: str | None = None
    description_fr: str | None = None
    ps_entry: int
    entry_growth_rate: Decimal
    default_retention: Decimal
    terminal_retention: Decimal
    lateral_multiplier: Decimal
    color_code: str | None = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ScenarioListResponse(BaseModel):
    scenarios: list[EnrollmentScenarioResponse]


# ==============================================================================
# Config and Overrides
# ==============================================================================


class GlobalOverridesUpdate(BaseModel):
    ps_entry_adjustment: int | None = Field(None, ge=-20, le=20)
    retention_adjustment: Decimal | None = Field(None, ge=Decimal("-0.05"), le=Decimal("0.05"))
    lateral_multiplier_override: Decimal | None = Field(None, ge=Decimal("0.5"), le=Decimal("1.5"))
    class_size_override: int | None = Field(None, ge=20, le=30)

    model_config = ConfigDict(from_attributes=True)


class LevelOverrideItem(BaseModel):
    cycle_id: uuid.UUID
    class_size_ceiling: int | None = Field(None, ge=20, le=30)
    max_divisions: int | None = Field(None, ge=2, le=10)


class LevelOverridesUpdate(BaseModel):
    overrides: list[LevelOverrideItem]


class GradeOverrideItem(BaseModel):
    level_id: uuid.UUID
    retention_rate: Decimal | None = Field(None, ge=Decimal("0.85"), le=Decimal("1.00"))
    lateral_entry: int | None = Field(None, ge=0, le=50)
    max_divisions: int | None = Field(None, ge=2, le=8)
    class_size_ceiling: int | None = Field(None, ge=20, le=30)


class GradeOverridesUpdate(BaseModel):
    overrides: list[GradeOverrideItem]


class LevelOverrideResponse(LevelOverrideItem):
    cycle_code: str
    cycle_name: str

    model_config = ConfigDict(from_attributes=True)


class GradeOverrideResponse(GradeOverrideItem):
    level_code: str
    level_name: str

    model_config = ConfigDict(from_attributes=True)


class ProjectionConfigUpdate(BaseModel):
    scenario_id: uuid.UUID | None = None
    base_year: int | None = None
    projection_years: int | None = Field(None, ge=1, le=10)
    school_max_capacity: int | None = Field(None, gt=0)
    default_class_size: int | None = Field(None, ge=15, le=40)


class ProjectionConfigResponse(BaseModel):
    id: uuid.UUID
    budget_version_id: uuid.UUID
    scenario_id: uuid.UUID
    scenario: EnrollmentScenarioResponse
    base_year: int
    projection_years: int
    school_max_capacity: int
    default_class_size: int
    status: str
    validated_at: datetime | None = None
    validated_by: uuid.UUID | None = None
    global_overrides: GlobalOverridesUpdate | None = None
    level_overrides: list[LevelOverrideResponse] = []
    grade_overrides: list[GradeOverrideResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Results
# ==============================================================================


class GradeProjectionResponse(BaseModel):
    grade_code: str
    cycle_code: str
    projected_students: int
    divisions: int
    avg_class_size: Decimal
    original_projection: int | None = None
    reduction_applied: int = 0
    reduction_percentage: Decimal | None = None
    historical_data: list[int] | None = None


class YearProjectionResponse(BaseModel):
    school_year: str
    fiscal_year: int
    grades: list[GradeProjectionResponse]
    total_students: int
    utilization_rate: Decimal
    was_capacity_constrained: bool
    total_reduction_applied: int
    fiscal_weighted_enrollment: dict[str, Decimal] | None = None


class ProjectionSummaryResponse(BaseModel):
    base_year_total: int
    final_year_total: int
    cagr: Decimal
    years_at_capacity: int


class ProjectionResultsResponse(BaseModel):
    config: ProjectionConfigResponse
    projections: list[YearProjectionResponse]
    summary: ProjectionSummaryResponse


# ==============================================================================
# Validation
# ==============================================================================


class ValidationRequest(BaseModel):
    confirmation: bool = Field(..., description="User confirms downstream cascade")


class ValidationResponse(BaseModel):
    success: bool
    downstream_updated: list[str]

