"""
Enrollment Projection Engine - Pydantic Models

Pure input/output models for the Retention + Lateral Entry projection system
with 4-layer overrides and capacity constraints.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ScenarioParams(BaseModel):
    """Scenario default parameters (Layer 1)."""

    code: str
    ps_entry: int = Field(..., ge=0)
    entry_growth_rate: Decimal = Field(..., ge=Decimal("-0.10"), le=Decimal("0.10"))
    default_retention: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("1.0"))
    terminal_retention: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("1.0"))
    lateral_multiplier: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("5.0"))

    model_config = ConfigDict(frozen=True)


class GlobalOverrides(BaseModel):
    """Layer 2 global overrides (applied to all grades unless overridden)."""

    ps_entry_adjustment: int | None = Field(None, ge=-20, le=20)
    retention_adjustment: Decimal | None = Field(None, ge=Decimal("-0.05"), le=Decimal("0.05"))
    lateral_multiplier_override: Decimal | None = Field(None, ge=Decimal("0.5"), le=Decimal("1.5"))
    class_size_override: int | None = Field(None, ge=20, le=30)

    model_config = ConfigDict(frozen=True)


class LevelOverride(BaseModel):
    """Layer 3 overrides per cycle (MAT/ELEM/COLL/LYC)."""

    cycle_code: str
    class_size_ceiling: int | None = Field(None, ge=20, le=30)
    max_divisions: int | None = Field(None, ge=2, le=10)

    model_config = ConfigDict(frozen=True)


class GradeOverride(BaseModel):
    """Layer 4 overrides per grade (highest priority)."""

    grade_code: str
    retention_rate: Decimal | None = Field(None, ge=Decimal("0.85"), le=Decimal("1.00"))
    lateral_entry: int | None = Field(None, ge=0, le=50)
    max_divisions: int | None = Field(None, ge=2, le=8)
    class_size_ceiling: int | None = Field(None, ge=20, le=30)

    model_config = ConfigDict(frozen=True)


class ProjectionInput(BaseModel):
    """Engine input for a target school year."""

    base_year: int = Field(..., description="Base (preceding) school year start")
    target_year: int = Field(..., description="Target school year start")
    projection_years: int = Field(default=5, ge=1, le=10)

    school_max_capacity: int = Field(default=1850, gt=0)
    default_class_size: int = Field(default=25, ge=15, le=40)

    scenario: ScenarioParams
    base_year_enrollment: dict[str, int] = Field(
        ..., description="Enrollment by grade for base_year (preceding year)"
    )
    base_lateral_entry: dict[str, int] = Field(
        default_factory=dict,
        description="Base lateral entry by grade (defaults table)",
    )

    global_overrides: GlobalOverrides | None = None
    level_overrides: dict[str, LevelOverride] | None = None  # keyed by cycle_code
    grade_overrides: dict[str, GradeOverride] | None = None  # keyed by grade_code


class GradeProjection(BaseModel):
    """Projection result for a single grade."""

    grade_code: str
    cycle_code: str
    projected_students: int
    divisions: int
    avg_class_size: Decimal
    original_projection: int | None = None
    reduction_applied: int = 0
    reduction_percentage: Decimal | None = None

    model_config = ConfigDict(frozen=True)


class ProjectionResult(BaseModel):
    """Complete projection result for one target year."""

    school_year: str
    fiscal_year: int
    grades: list[GradeProjection]
    total_students: int
    utilization_rate: Decimal
    was_capacity_constrained: bool
    total_reduction_applied: int = 0

    model_config = ConfigDict(frozen=True)


ProjectionStatus = Literal["draft", "validated"]

