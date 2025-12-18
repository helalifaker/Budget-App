"""
Pydantic schemas for Impact Calculation.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ImpactCalculationRequest(BaseModel):
    """Request for calculating impact of a proposed change."""

    step_id: str = Field(
        ...,
        description="Planning step: enrollment, class_structure, dhg, revenue, costs, capex",
    )
    dimension_type: str = Field(
        ...,
        description="Dimension type: level, subject, account_code",
    )
    dimension_id: str | None = Field(None, description="UUID of the dimension (level, subject)")
    dimension_code: str | None = Field(None, description="Code for the dimension (e.g., account code)")
    field_name: str = Field(..., description="The field being changed")
    new_value: str | float | int | None = Field(..., description="The proposed new value")


class ImpactCalculationResponse(BaseModel):
    """Response containing calculated impact metrics."""

    model_config = ConfigDict(from_attributes=True)

    fte_change: float = Field(description="Change in FTE")
    fte_current: float = Field(description="Current total FTE")
    fte_proposed: float = Field(description="Proposed total FTE")

    cost_impact_sar: Decimal = Field(description="Impact on total costs in SAR")
    cost_current_sar: Decimal = Field(description="Current total costs in SAR")
    cost_proposed_sar: Decimal = Field(description="Proposed total costs in SAR")

    revenue_impact_sar: Decimal = Field(description="Impact on revenue in SAR")
    revenue_current_sar: Decimal = Field(description="Current revenue in SAR")
    revenue_proposed_sar: Decimal = Field(description="Proposed revenue in SAR")

    margin_impact_pct: float = Field(description="Impact on operating margin percentage")
    margin_current_pct: float = Field(description="Current operating margin percentage")
    margin_proposed_pct: float = Field(description="Proposed operating margin percentage")

    affected_steps: list[str] = Field(description="List of steps affected by this change")
