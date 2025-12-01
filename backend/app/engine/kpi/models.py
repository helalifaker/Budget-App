"""
KPI Engine - Pydantic Models

Input/output models for key performance indicator calculations.
All models use Pydantic for validation and type safety.
"""

from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class KPIType(str, Enum):
    """KPI calculation types for educational and financial metrics."""

    STUDENT_TEACHER_RATIO = "student_teacher_ratio"  # Students ÷ Teachers
    HE_RATIO_SECONDARY = "he_ratio_secondary"  # DHG Hours ÷ Secondary Students
    REVENUE_PER_STUDENT = "revenue_per_student"  # Total Revenue ÷ Students
    COST_PER_STUDENT = "cost_per_student"  # Total Costs ÷ Students
    MARGIN_PERCENTAGE = "margin_percentage"  # (Revenue - Costs) ÷ Revenue × 100
    STAFF_COST_RATIO = "staff_cost_ratio"  # Personnel Costs ÷ Total Costs × 100
    CAPACITY_UTILIZATION = "capacity_utilization"  # Current Students ÷ Max Capacity × 100


class KPIInput(BaseModel):
    """
    Input data for KPI calculations.

    Contains all necessary data points for calculating educational
    and financial performance indicators.
    """

    budget_id: UUID | None = Field(None, description="Budget UUID (optional)")

    # Student metrics
    total_students: int = Field(..., ge=0, description="Total enrolled students")
    secondary_students: int = Field(
        ..., ge=0, description="Secondary students (Collège + Lycée)"
    )
    max_capacity: int = Field(..., ge=1, description="School maximum capacity")

    # Teacher metrics
    total_teacher_fte: Decimal = Field(
        ..., ge=Decimal("0"), description="Total teacher FTE (full-time equivalent)"
    )
    dhg_hours_total: Decimal | None = Field(
        None,
        ge=Decimal("0"),
        description="Total DHG hours for secondary (for H/E ratio)",
    )

    # Financial metrics (in SAR)
    total_revenue: Decimal = Field(..., ge=Decimal("0"), description="Total revenue (SAR)")
    total_costs: Decimal = Field(..., ge=Decimal("0"), description="Total costs (SAR)")
    personnel_costs: Decimal = Field(
        ..., ge=Decimal("0"), description="Total personnel costs (SAR)"
    )

    @field_validator("secondary_students")
    @classmethod
    def validate_secondary_students_subset(cls, v: int, info) -> int:
        """Ensure secondary students <= total students."""
        if "total_students" in info.data:
            total = info.data["total_students"]
            if v > total:
                raise ValueError(
                    f"Secondary students ({v}) cannot exceed total students ({total})"
                )
        return v

    @field_validator("personnel_costs")
    @classmethod
    def validate_personnel_within_total_costs(cls, v: Decimal, info) -> Decimal:
        """Ensure personnel costs <= total costs."""
        if "total_costs" in info.data:
            total = info.data["total_costs"]
            if v > total:
                raise ValueError(
                    f"Personnel costs ({v}) cannot exceed total costs ({total})"
                )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "budget_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_students": 1850,
                "secondary_students": 650,
                "max_capacity": 1875,
                "total_teacher_fte": 154.2,
                "dhg_hours_total": 877.5,
                "total_revenue": 83272500,
                "total_costs": 74945250,
                "personnel_costs": 52461675,
            }
        }


class KPIResult(BaseModel):
    """
    Single KPI calculation result.

    Represents one calculated performance indicator with its value
    and comparison to target/benchmark.
    """

    kpi_type: KPIType = Field(..., description="Type of KPI calculated")
    value: Decimal = Field(..., description="Calculated KPI value")
    target_value: Decimal | None = Field(
        None, description="Target/benchmark value for comparison"
    )
    unit: str = Field(..., description="Unit of measurement (ratio, SAR, %, etc.)")
    variance_from_target: Decimal | None = Field(
        None,
        description="Difference from target (positive = above target, negative = below)",
    )
    performance_status: str | None = Field(
        None, description="Performance assessment (on_target, above_target, below_target)"
    )

    @field_validator("performance_status")
    @classmethod
    def validate_performance_status_values(cls, v: str | None) -> str | None:
        """Ensure performance status is a valid value."""
        if v is not None and v not in {"on_target", "above_target", "below_target"}:
            raise ValueError(
                f"Performance status must be on_target, above_target, or below_target, got {v}"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "kpi_type": "student_teacher_ratio",
                "value": 12.0,
                "target_value": 12.0,
                "unit": "ratio",
                "variance_from_target": 0.0,
                "performance_status": "on_target",
            }
        }


class KPICalculationResult(BaseModel):
    """
    Complete set of KPI calculation results.

    Contains all calculated KPIs for a budget or planning scenario.
    """

    budget_id: UUID | None = Field(None, description="Budget UUID (if applicable)")
    calculation_date: str | None = Field(
        None, description="ISO 8601 date when calculations were performed"
    )

    # Educational KPIs
    student_teacher_ratio: KPIResult | None = Field(
        None, description="Students per teacher (target: ~12.0)"
    )
    he_ratio_secondary: KPIResult | None = Field(
        None, description="Hours per student in secondary (target: ~1.35)"
    )
    capacity_utilization: KPIResult | None = Field(
        None, description="% of maximum capacity used (target: 90-95%)"
    )

    # Financial KPIs
    revenue_per_student: KPIResult | None = Field(
        None, description="Revenue per student in SAR (target: ~45,000)"
    )
    cost_per_student: KPIResult | None = Field(
        None, description="Cost per student in SAR"
    )
    margin_percentage: KPIResult | None = Field(
        None, description="Profit margin % (target: ~10%)"
    )
    staff_cost_ratio: KPIResult | None = Field(
        None, description="Personnel as % of total costs (target: ~70%)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "budget_id": "123e4567-e89b-12d3-a456-426614174000",
                "calculation_date": "2025-12-01",
                "student_teacher_ratio": {
                    "kpi_type": "student_teacher_ratio",
                    "value": 12.0,
                    "target_value": 12.0,
                    "unit": "ratio",
                    "variance_from_target": 0.0,
                    "performance_status": "on_target",
                },
                "he_ratio_secondary": {
                    "kpi_type": "he_ratio_secondary",
                    "value": 1.35,
                    "target_value": 1.35,
                    "unit": "ratio",
                    "variance_from_target": 0.0,
                    "performance_status": "on_target",
                },
                "margin_percentage": {
                    "kpi_type": "margin_percentage",
                    "value": 10.0,
                    "target_value": 10.0,
                    "unit": "%",
                    "variance_from_target": 0.0,
                    "performance_status": "on_target",
                },
            }
        }
