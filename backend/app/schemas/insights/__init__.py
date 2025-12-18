"""Insights module schemas."""

from app.schemas.insights.analysis import (
    # Dashboard
    ActivityLogEntry,
    # Budget vs Actual
    ActualDataImportRequest,
    ActualDataImportResponse,
    AlertResponse,
    # Enums
    AlertSeverityEnum,
    ChartDataResponse,
    ComparisonResponse,
    DashboardSummaryResponse,
    # Common
    ErrorResponse,
    ForecastRevisionRequest,
    ForecastRevisionResponse,
    # KPI
    KPIBenchmarkComparison,
    KPICalculationRequest,
    KPICategoryEnum,
    KPIDefinitionResponse,
    KPITrendPoint,
    KPITrendResponse,
    KPIValueResponse,
    MessageResponse,
    # Strategic
    ScenarioAssumptions,
    ScenarioComparisonResponse,
    ScenarioSummary,
    ScenarioTypeEnum,
    StrategicInitiativeCreate,
    StrategicInitiativeResponse,
    StrategicPlanCreate,
    StrategicPlanResponse,
    StrategicScenarioResponse,
    UpdateAssumptionsRequest,
    VarianceDetailResponse,
    VarianceReportResponse,
    VarianceStatusEnum,
    VarianceSummary,
    VersionComparisonData,
    YearProjectionData,
    YearProjectionResponse,
    YearScenarioProjection,
)
from app.schemas.insights.kpi import (
    KPICalculationRequest as KPIEngineRequest,
)
from app.schemas.insights.kpi import (
    KPICalculationResponse as KPIEngineResponse,
)

__all__ = [
    # Dashboard
    "ActivityLogEntry",
    # Budget vs Actual
    "ActualDataImportRequest",
    "ActualDataImportResponse",
    "AlertResponse",
    # Enums
    "AlertSeverityEnum",
    "ChartDataResponse",
    "ComparisonResponse",
    "DashboardSummaryResponse",
    # Common
    "ErrorResponse",
    "ForecastRevisionRequest",
    "ForecastRevisionResponse",
    # KPI
    "KPIBenchmarkComparison",
    "KPICalculationRequest",
    "KPICategoryEnum",
    "KPIDefinitionResponse",
    # Engine aliases
    "KPIEngineRequest",
    "KPIEngineResponse",
    "KPITrendPoint",
    "KPITrendResponse",
    "KPIValueResponse",
    "MessageResponse",
    # Strategic
    "ScenarioAssumptions",
    "ScenarioComparisonResponse",
    "ScenarioSummary",
    "ScenarioTypeEnum",
    "StrategicInitiativeCreate",
    "StrategicInitiativeResponse",
    "StrategicPlanCreate",
    "StrategicPlanResponse",
    "StrategicScenarioResponse",
    "UpdateAssumptionsRequest",
    "VarianceDetailResponse",
    "VarianceReportResponse",
    "VarianceStatusEnum",
    "VarianceSummary",
    "VersionComparisonData",
    "YearProjectionData",
    "YearProjectionResponse",
    "YearScenarioProjection",
]
