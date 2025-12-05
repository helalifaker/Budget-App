"""
Pydantic schemas for Analysis & Strategic Planning API endpoints.

Provides request/response models for:
- KPI calculations and benchmarks
- Dashboard summaries and charts
- Budget vs actual variance analysis
- Strategic planning and scenario modeling
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Enums
# ============================================================================


class KPICategoryEnum(str, Enum):
    """KPI category for grouping."""

    EDUCATIONAL = "educational"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"


class VarianceStatusEnum(str, Enum):
    """Variance favorability status."""

    FAVORABLE = "favorable"
    UNFAVORABLE = "unfavorable"
    NEUTRAL = "neutral"
    NOT_APPLICABLE = "not_applicable"


class ScenarioTypeEnum(str, Enum):
    """Strategic scenario types."""

    BASE_CASE = "base_case"
    CONSERVATIVE = "conservative"
    OPTIMISTIC = "optimistic"
    NEW_CAMPUS = "new_campus"


class AlertSeverityEnum(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ============================================================================
# KPI Schemas
# ============================================================================


class KPIDefinitionResponse(BaseModel):
    """KPI definition metadata."""

    id: UUID
    code: str
    name_en: str
    name_fr: str
    category: KPICategoryEnum
    formula_text: str
    unit: str
    target_value: Decimal | None
    min_acceptable: Decimal | None
    max_acceptable: Decimal | None
    is_active: bool
    description: str | None

    class Config:
        from_attributes = True


class KPIValueResponse(BaseModel):
    """Calculated KPI value with variance analysis."""

    id: UUID
    budget_version_id: UUID
    kpi_code: str
    kpi_name: str
    calculated_value: Decimal
    variance_from_target: Decimal | None
    variance_percent: Decimal | None
    calculation_inputs: dict[str, Any]
    calculated_at: datetime
    unit: str
    target_value: Decimal | None
    notes: str | None

    class Config:
        from_attributes = True


class KPIBenchmarkComparison(BaseModel):
    """KPI comparison to AEFE benchmark."""

    kpi_code: str
    kpi_name: str
    calculated_value: float
    benchmark_target: float | None
    benchmark_min: float | None
    benchmark_max: float | None
    variance_from_target: float | None
    variance_percent: float | None
    status: str
    unit: str


class KPITrendPoint(BaseModel):
    """Single point in KPI trend analysis."""

    version_id: str
    version_name: str
    fiscal_year: int
    status: str
    calculated_value: float | None
    variance_from_target: float | None
    calculated_at: str | None


class KPITrendResponse(BaseModel):
    """KPI trend across multiple versions."""

    kpi_code: str
    kpi_name: str
    unit: str
    trend_points: list[KPITrendPoint]


class KPICalculationRequest(BaseModel):
    """Request to calculate specific KPIs."""

    kpi_codes: list[str] | None = Field(
        None,
        description="Optional list of specific KPI codes to calculate. If None, calculates all active KPIs.",
    )


# ============================================================================
# Dashboard Schemas
# ============================================================================


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary cards."""

    version_id: str
    version_name: str
    fiscal_year: int
    status: str
    total_revenue_sar: float
    total_costs_sar: float
    net_result_sar: float
    operating_margin_pct: float
    total_students: int
    total_teachers_fte: float
    student_teacher_ratio: float
    capacity_utilization_pct: float
    last_updated: str


class ChartDataResponse(BaseModel):
    """Chart data for visualization."""

    breakdown_by: str
    labels: list[str]
    values: list[float]
    percentages: list[float] | None = None
    chart_type: str
    total: float


class AlertResponse(BaseModel):
    """System alert."""

    id: str
    type: str  # INFO, WARNING, ERROR
    message: str
    timestamp: str


class ActivityLogEntry(BaseModel):
    """Activity log entry."""

    id: str
    action: str
    user: str
    timestamp: str
    details: str | None = None


class VersionComparisonData(BaseModel):
    """Version comparison metric data."""

    id: str
    name: str
    fiscal_year: int


class ComparisonResponse(BaseModel):
    """Multi-version comparison data."""

    versions: list[VersionComparisonData]
    metric_name: str
    values: list[dict[str, Any]]
    labels: list[str] | None


# ============================================================================
# Budget vs Actual Schemas
# ============================================================================


class ActualDataImportRequest(BaseModel):
    """Request to import actual data from Odoo."""

    odoo_data: list[dict[str, Any]] = Field(
        ...,
        description="List of Odoo transaction records with fiscal_year, period, account_code, amount_sar, etc.",
    )
    import_batch_id: UUID | None = Field(
        None,
        description="Optional batch identifier for grouping imports",
    )


class ActualDataImportResponse(BaseModel):
    """Response from actual data import."""

    records_imported: int
    import_batch_id: str
    fiscal_year: int
    periods_covered: list[int]
    total_amount_sar: float
    import_date: str


class VarianceDetailResponse(BaseModel):
    """Single variance detail."""

    account_code: str
    period: int
    budget_sar: float
    actual_sar: float
    variance_sar: float
    variance_pct: float
    status: VarianceStatusEnum
    is_material: bool
    ytd_budget_sar: float
    ytd_actual_sar: float
    ytd_variance_sar: float


class VarianceSummary(BaseModel):
    """Variance report summary statistics."""

    total_budget_sar: float
    total_actual_sar: float
    total_variance_sar: float
    variance_percent: float
    variance_count: int
    material_count: int
    favorable_count: int
    unfavorable_count: int


class VarianceReportResponse(BaseModel):
    """Complete variance report."""

    version_id: str
    version_name: str
    fiscal_year: int
    period: int | None
    summary: VarianceSummary
    variances: list[VarianceDetailResponse]


class ForecastRevisionRequest(BaseModel):
    """Request to create forecast revision."""

    forecast_name: str = Field(..., description="Name for forecast version")
    current_period: int = Field(..., ge=1, le=12, description="Current period with actuals")


class ForecastRevisionResponse(BaseModel):
    """Response from forecast creation."""

    forecast_version_id: str
    forecast_name: str
    fiscal_year: int
    status: str
    created_at: str


# ============================================================================
# Strategic Planning Schemas
# ============================================================================


class ScenarioAssumptions(BaseModel):
    """Scenario growth assumptions."""

    enrollment_growth_rate: Decimal = Field(
        ...,
        ge=Decimal("-0.50"),
        le=Decimal("1.00"),
        description="Annual enrollment growth rate (e.g., 0.04 = 4%)",
    )
    fee_increase_rate: Decimal = Field(
        ...,
        ge=Decimal("-0.20"),
        le=Decimal("0.50"),
        description="Annual fee increase rate (e.g., 0.03 = 3%)",
    )
    salary_inflation_rate: Decimal = Field(
        ...,
        ge=Decimal("-0.20"),
        le=Decimal("0.50"),
        description="Annual salary inflation rate (e.g., 0.035 = 3.5%)",
    )
    operating_inflation_rate: Decimal = Field(
        ...,
        ge=Decimal("-0.20"),
        le=Decimal("0.50"),
        description="Annual operating cost inflation rate (e.g., 0.025 = 2.5%)",
    )


class YearProjectionData(BaseModel):
    """Projection data for a single category and year."""

    amount_sar: float
    calculation_inputs: dict[str, Any] | None


class YearScenarioProjection(BaseModel):
    """All projections for one scenario in one year."""

    scenario_type: ScenarioTypeEnum
    scenario_name: str
    projections: dict[str, YearProjectionData]


class YearProjectionResponse(BaseModel):
    """Year projection response."""

    year: int
    fiscal_year: int
    scenarios: list[YearScenarioProjection]


class StrategicInitiativeCreate(BaseModel):
    """Request to create strategic initiative."""

    name: str = Field(..., max_length=200, description="Initiative name")
    description: str | None = Field(None, description="Initiative description")
    planned_year: int = Field(..., ge=1, le=5, description="Year in plan (1-5)")
    capex_amount_sar: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="One-time capital expenditure",
    )
    operating_impact_sar: Decimal = Field(
        Decimal("0"),
        ge=Decimal("0"),
        description="Recurring annual operating cost impact",
    )


class StrategicInitiativeResponse(BaseModel):
    """Strategic initiative response."""

    id: UUID
    strategic_plan_id: UUID
    name: str
    description: str | None
    planned_year: int
    capex_amount_sar: Decimal
    operating_impact_sar: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioSummary(BaseModel):
    """Summary of one scenario."""

    scenario_type: ScenarioTypeEnum
    scenario_name: str
    assumptions: dict[str, float]
    five_year_totals: dict[str, float]
    year_by_year: list[dict[str, Any]]


class ScenarioComparisonResponse(BaseModel):
    """Comparison of all scenarios in a plan."""

    plan_id: str
    plan_name: str
    base_year: int
    scenarios: list[ScenarioSummary]
    comparison_metrics: dict[str, Any]


class StrategicPlanCreate(BaseModel):
    """Request to create strategic plan."""

    base_version_id: UUID = Field(
        ...,
        description="Base budget version UUID to use as Year 1",
    )
    plan_name: str = Field(..., max_length=200, description="Strategic plan name")
    description: str | None = Field(None, description="Plan description")
    years: int = Field(5, ge=1, le=5, description="Number of years to plan")
    create_default_scenarios: bool = Field(
        True,
        description="Whether to create default scenarios (conservative, base, optimistic)",
    )


class StrategicScenarioResponse(BaseModel):
    """Strategic scenario with projections."""

    id: UUID
    scenario_type: ScenarioTypeEnum
    name: str
    description: str | None
    enrollment_growth_rate: Decimal
    fee_increase_rate: Decimal
    salary_inflation_rate: Decimal
    operating_inflation_rate: Decimal
    additional_assumptions: dict[str, Any] | None

    class Config:
        from_attributes = True


class StrategicPlanResponse(BaseModel):
    """Strategic plan response."""

    id: UUID
    name: str
    description: str | None
    base_year: int
    status: str
    scenarios: list[StrategicScenarioResponse]
    initiatives: list[StrategicInitiativeResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateAssumptionsRequest(BaseModel):
    """Request to update scenario assumptions."""

    enrollment_growth_rate: Decimal | None = Field(
        None,
        ge=Decimal("-0.50"),
        le=Decimal("1.00"),
        description="Annual enrollment growth rate",
    )
    fee_increase_rate: Decimal | None = Field(
        None,
        ge=Decimal("-0.20"),
        le=Decimal("0.50"),
        description="Annual fee increase rate",
    )
    salary_inflation_rate: Decimal | None = Field(
        None,
        ge=Decimal("-0.20"),
        le=Decimal("0.50"),
        description="Annual salary inflation rate",
    )
    operating_inflation_rate: Decimal | None = Field(
        None,
        ge=Decimal("-0.20"),
        le=Decimal("0.50"),
        description="Annual operating inflation rate",
    )
    recalculate_projections: bool = Field(
        True,
        description="Whether to recalculate projections after update",
    )


# ============================================================================
# Common Response Schemas
# ============================================================================


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    details: str | None = None
    status_code: int
