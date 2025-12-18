"""
Pydantic schemas for strategic planning endpoints.

This module will contain schemas for:
- Long-term planning (multi-year projections)
- Scenario management (what-if analysis)
- Strategic targets and KPI goals
- Board reporting and executive summaries

Currently a placeholder - schemas will be added as features are implemented.
"""

from pydantic import BaseModel, Field

# ==============================================================================
# Strategic Planning Schemas (Placeholder)
# ==============================================================================


class StrategicScenarioBase(BaseModel):
    """Base schema for strategic scenario - placeholder."""

    name: str = Field(..., max_length=100, description="Scenario name")
    description: str | None = Field(None, description="Scenario description")


class StrategicTargetBase(BaseModel):
    """Base schema for strategic target - placeholder."""

    metric_name: str = Field(..., max_length=100, description="Target metric name")
    target_value: float = Field(..., description="Target value")
    target_year: int = Field(..., ge=2020, le=2100, description="Target year")


# Additional schemas to be added:
# - StrategicScenarioCreate, StrategicScenarioUpdate, StrategicScenarioResponse
# - StrategicTargetCreate, StrategicTargetUpdate, StrategicTargetResponse
# - MultiYearProjectionRequest, MultiYearProjectionResponse
# - BoardReportRequest, BoardReportResponse
# - ScenarioComparisonRequest, ScenarioComparisonResponse
