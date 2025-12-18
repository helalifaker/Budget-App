"""
Enrollment Engine - Pydantic Models

Input/output models for enrollment projection calculations.
All models use Pydantic for validation and type safety.
"""

from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EnrollmentGrowthScenario(str, Enum):
    """Enrollment growth scenario types aligned with strategic planning."""

    CONSERVATIVE = "conservative"  # 0-2% growth per year
    BASE = "base"  # 3-5% growth per year
    OPTIMISTIC = "optimistic"  # 6-8% growth per year


class EnrollmentInput(BaseModel):
    """
    Input data for enrollment projection calculations.

    Used to calculate projected enrollment for a future year based on
    current enrollment and growth assumptions.
    """

    level_id: UUID = Field(..., description="Academic level UUID")
    level_code: str = Field(..., description="Level code (e.g., 'CP', '6EME', 'TERMINALE')")
    nationality: str = Field(..., description="Nationality category (French, Saudi, Other)")
    current_enrollment: int = Field(..., ge=0, description="Current student count")
    growth_scenario: EnrollmentGrowthScenario | None = Field(
        default=EnrollmentGrowthScenario.BASE,
        description="Growth scenario (conservative, base, optimistic)",
    )
    custom_growth_rate: Decimal | None = Field(
        default=None,
        ge=Decimal("-0.50"),
        le=Decimal("1.00"),
        description="Optional custom growth rate (-50% to +100%, overrides scenario)",
    )
    years_to_project: int = Field(
        default=1, ge=1, le=10, description="Number of years to project forward"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "level_id": "123e4567-e89b-12d3-a456-426614174000",
                "level_code": "6EME",
                "nationality": "French",
                "current_enrollment": 120,
                "growth_scenario": "base",
                "custom_growth_rate": None,
                "years_to_project": 5,
            }
        }
    )

    @field_validator("current_enrollment")
    @classmethod
    def validate_enrollment_nonnegative(cls, v: int) -> int:
        """Ensure enrollment is non-negative."""
        if v < 0:
            raise ValueError("Enrollment must be non-negative")
        return v


class EnrollmentProjection(BaseModel):
    """
    Single year enrollment projection result.

    Represents projected enrollment for one academic level, nationality,
    and future year.
    """

    year: int = Field(..., ge=1, description="Projection year (1-10)")
    projected_enrollment: int = Field(..., ge=0, description="Projected student count")
    growth_rate_applied: Decimal = Field(
        ..., description="Actual growth rate applied for this year"
    )
    cumulative_growth: Decimal = Field(
        ..., description="Cumulative growth from year 1 to this year"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "year": 3,
                "projected_enrollment": 135,
                "growth_rate_applied": 0.04,
                "cumulative_growth": 0.1249,
            }
        }
    )


class EnrollmentProjectionResult(BaseModel):
    """
    Complete multi-year enrollment projection result.

    Contains projections for all requested years plus metadata about
    the calculation.
    """

    level_id: UUID = Field(..., description="Academic level UUID")
    level_code: str = Field(..., description="Level code")
    nationality: str = Field(..., description="Nationality category")
    base_enrollment: int = Field(..., ge=0, description="Starting enrollment")
    scenario: EnrollmentGrowthScenario = Field(..., description="Growth scenario used")
    projections: list[EnrollmentProjection] = Field(
        ..., description="Year-by-year projections"
    )
    total_growth_students: int = Field(
        ..., description="Total student growth from year 1 to final year"
    )
    total_growth_percent: Decimal = Field(
        ..., description="Total percentage growth from year 1 to final year"
    )
    capacity_exceeded: bool = Field(
        default=False, description="Whether projections exceed school capacity"
    )

    model_config = ConfigDict(
        frozen=True,  # Make model immutable after creation
        json_schema_extra={
            "example": {
                "level_id": "123e4567-e89b-12d3-a456-426614174000",
                "level_code": "6EME",
                "nationality": "French",
                "base_enrollment": 120,
                "scenario": "base",
                "projections": [
                    {
                        "year": 1,
                        "projected_enrollment": 120,
                        "growth_rate_applied": 0.00,
                        "cumulative_growth": 0.00,
                    },
                    {
                        "year": 2,
                        "projected_enrollment": 125,
                        "growth_rate_applied": 0.04,
                        "cumulative_growth": 0.04,
                    },
                    {
                        "year": 3,
                        "projected_enrollment": 130,
                        "growth_rate_applied": 0.04,
                        "cumulative_growth": 0.0816,
                    },
                ],
                "total_growth_students": 10,
                "total_growth_percent": 0.0816,
                "capacity_exceeded": False,
            }
        },
    )


class RetentionModel(BaseModel):
    """
    Retention and attrition modeling parameters.

    Models student retention rates by level to refine enrollment projections
    beyond simple growth rates.
    """

    level_id: UUID = Field(..., description="Academic level UUID")
    retention_rate: Decimal = Field(
        ..., ge=Decimal("0.50"), le=Decimal("1.00"), description="Student retention rate (50-100%)"
    )
    attrition_rate: Decimal = Field(
        ..., ge=Decimal("0.00"), le=Decimal("0.50"), description="Student attrition rate (0-50%)"
    )
    new_student_intake: int = Field(
        ..., ge=0, description="Expected new student enrollment for this level"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "level_id": "123e4567-e89b-12d3-a456-426614174000",
                "retention_rate": 0.95,  # 95% stay
                "attrition_rate": 0.05,  # 5% leave
                "new_student_intake": 25,
            }
        }
    )

    @field_validator("attrition_rate")
    @classmethod
    def validate_attrition_retention_sum(cls, v: Decimal, info) -> Decimal:
        """Ensure retention + attrition = 100%."""
        if "retention_rate" in info.data:
            retention = info.data["retention_rate"]
            if abs((retention + v) - Decimal("1.00")) > Decimal("0.01"):
                raise ValueError(
                    f"Retention ({retention}) + Attrition ({v}) must equal 1.00"
                )
        return v
