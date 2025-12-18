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
    version_id: uuid.UUID
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
    projected_students: int  # Total (T) = retained + lateral
    retained_students: int = 0  # Retain (R): Students from previous grade
    lateral_students: int = 0  # Lateral (L): New lateral entries
    divisions: int
    avg_class_size: Decimal
    original_projection: int | None = None
    reduction_applied: int = 0
    reduction_percentage: Decimal | None = None
    historical_data: list[int] | None = None  # Deprecated - use historical_years


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


class HistoricalYearData(BaseModel):
    """Historical enrollment data for a single year."""

    fiscal_year: int
    school_year: str  # e.g., "2023/2024"
    grades: dict[str, int]  # grade_code -> student_count
    total_students: int


class ProjectionResultsResponse(BaseModel):
    config: ProjectionConfigResponse
    projections: list[YearProjectionResponse]
    summary: ProjectionSummaryResponse
    historical_years: list[HistoricalYearData] = []  # Last 2 years of actual enrollment
    base_year_data: HistoricalYearData | None = None  # Actual enrollment for base year (e.g., 2025-26 for Budget 2026)


# ==============================================================================
# Validation
# ==============================================================================


class ValidationRequest(BaseModel):
    confirmation: bool = Field(..., description="User confirms downstream cascade")


class ValidationResponse(BaseModel):
    success: bool
    downstream_updated: list[str]


# ==============================================================================
# Calibrated Lateral Rates (Unified Model)
# ==============================================================================


class GradeLateralRateResponse(BaseModel):
    """Lateral entry rate configuration for a single grade (unified model).

    All grades now use percentage-based lateral entry. The distinction between
    entry points and incidental grades is for display/UI purposes only.
    """

    grade_code: str
    cycle_code: str
    is_entry_point: bool = Field(..., description="True for MS, GS, CP, 6EME, 2NDE")

    # Calculated values from historical data
    calculated_retention: Decimal = Field(
        ..., description="Retention rate derived from cycle (MAT/ELEM=96%, COLL=97%, LYC=93%)"
    )
    calculated_lateral: Decimal = Field(
        ..., description="Lateral rate derived from weighted historical progression"
    )
    calculated_progression: Decimal = Field(
        ..., description="Total progression = retention × (1 + lateral)"
    )

    # User-editable overrides
    override_retention: Decimal | None = Field(
        None, ge=Decimal("0.85"), le=Decimal("1.00"), description="User override for retention"
    )
    override_lateral: Decimal | None = Field(
        None, ge=Decimal("0.0"), le=Decimal("1.0"), description="User override for lateral"
    )

    # Effective values (override or calculated)
    effective_retention: Decimal = Field(..., description="Override or calculated")
    effective_lateral: Decimal = Field(..., description="Override or calculated")
    effective_progression: Decimal = Field(..., description="Effective total progression")

    # Source metadata
    progression_n1: Decimal | None = Field(None, description="N-1 year progression rate")
    progression_n2: Decimal | None = Field(None, description="N-2 year progression rate")
    confidence: str = Field(
        default="high", description="Confidence in calculated values (low/medium/high)"
    )


class LateralRatesResponse(BaseModel):
    """Complete lateral rates for all grades (unified table view)."""

    grades: list[GradeLateralRateResponse]
    calibration_years: list[int] = Field(
        default_factory=list, description="Years used for calibration [2025, 2024, 2023]"
    )
    weight_n1: Decimal = Field(default=Decimal("0.70"), description="Weight for N-1 year")
    weight_n2: Decimal = Field(default=Decimal("0.30"), description="Weight for N-2 year")

    # Summary statistics
    total_grades: int = 14
    grades_with_overrides: int = 0
    grades_at_default: int = 14


class GradeLateralRateOverride(BaseModel):
    """Single grade lateral rate override."""

    grade_code: str
    override_retention: Decimal | None = Field(
        None, ge=Decimal("0.85"), le=Decimal("1.00")
    )
    override_lateral: Decimal | None = Field(
        None, ge=Decimal("0.0"), le=Decimal("1.0")
    )


class LateralRateOverrideRequest(BaseModel):
    """Request to override lateral rates for one or more grades."""

    overrides: list[GradeLateralRateOverride]


# ==============================================================================
# Lateral Entry Optimization (Class Structure Aware)
# ==============================================================================


class GradeOptimizationResultResponse(BaseModel):
    """Optimization result for a single grade."""

    grade_code: str
    cycle_code: str
    is_entry_point: bool

    # Input values
    retained_students: int = Field(..., description="Students retained from previous grade")
    historical_demand: int = Field(..., description="Historical lateral demand (from calibration)")

    # Class structure
    base_classes: int = Field(..., description="Number of classes needed for retained students")

    # Capacity calculations
    fill_to_target: int = Field(..., description="Slots to reach target class size")
    fill_to_max: int = Field(..., description="Slots to reach max class size")
    new_class_threshold: int = Field(..., description="Lateral needed to justify new class")

    # Decision and outputs
    decision: str = Field(..., description="Optimization decision (accept_all, accept_fill_max, restrict, new_class, restrict_at_ceiling)")
    accepted: int = Field(..., ge=0, description="Number of new students accepted")
    rejected: int = Field(..., ge=0, description="Number of new students rejected")

    # Final structure
    final_classes: int = Field(..., ge=0, description="Final number of classes")
    final_students: int = Field(..., ge=0, description="Total students (retained + accepted)")

    # Metrics
    avg_class_size: Decimal = Field(..., description="Average class size")
    utilization_pct: Decimal = Field(..., description="Utilization as % of target capacity")
    acceptance_rate: Decimal = Field(..., description="% of demand accepted")


class NewStudentsSummaryRowResponse(BaseModel):
    """Single row in the new students summary table."""

    grade_code: str
    grade_name: str
    cycle_code: str
    is_entry_point: bool

    # Numbers
    historical_demand: int = Field(..., description="What calibration suggests")
    available_slots: int = Field(..., description="Capacity available (fill_to_max)")
    accepted: int = Field(..., description="Actually accepted")
    rejected: int = Field(..., description="Demand - Accepted")

    # Percentages
    acceptance_rate: Decimal = Field(..., description="(accepted / demand) × 100")
    pct_of_total_intake: Decimal = Field(..., description="(accepted / total_new) × 100")

    # Decision
    decision: str = Field(..., description="Optimization decision type")


class NewStudentsSummaryResponse(BaseModel):
    """Complete summary of new student optimization."""

    # Totals
    total_demand: int = Field(..., description="Sum of all historical demand")
    total_available: int = Field(..., description="Sum of all available slots")
    total_accepted: int = Field(..., description="Sum of all accepted students")
    total_rejected: int = Field(..., description="Sum of all rejected students")

    # Overall metrics
    overall_acceptance_rate: Decimal = Field(..., description="(total_accepted / total_demand) × 100")

    # Entry points vs incidental breakdown
    entry_point_demand: int = 0
    entry_point_accepted: int = 0
    incidental_demand: int = 0
    incidental_accepted: int = 0

    # Grades by decision type
    grades_accept_all: list[str] = Field(default_factory=list)
    grades_fill_max: list[str] = Field(default_factory=list)
    grades_restricted: list[str] = Field(default_factory=list)
    grades_new_class: list[str] = Field(default_factory=list)
    grades_at_ceiling: list[str] = Field(default_factory=list)

    # Breakdown by grade
    by_grade: list[NewStudentsSummaryRowResponse] = Field(default_factory=list)


class LateralOptimizationResponse(BaseModel):
    """Complete lateral optimization results."""

    optimization_results: list[GradeOptimizationResultResponse]
    new_students_summary: NewStudentsSummaryResponse

