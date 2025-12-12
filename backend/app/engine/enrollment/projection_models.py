"""
Enrollment Projection Engine - Pydantic Models

Pure input/output models for the Retention + Lateral Entry projection system
with 4-layer overrides and capacity constraints.

Supports two lateral entry modes:
- Percentage-based: For entry point grades (MS, GS, CP, 6EME, 2NDE)
- Fixed-value: For incidental lateral grades (CE1, CE2, CM1, CM2, etc.)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Entry Point Grade Constants
# =============================================================================

# Entry point grades use percentage-based lateral entry (% of previous grade)
ENTRY_POINT_GRADES: frozenset[str] = frozenset({"MS", "GS", "CP", "6EME", "2NDE"})

# Document defaults for lateral entry (from EFIR_Enrollment_Analysis_v2.md)
DOCUMENT_LATERAL_DEFAULTS: dict[str, dict] = {
    # Entry point grades (percentage-based)
    "MS": {"lateral_rate": Decimal("0.42"), "retention_rate": Decimal("0.96")},
    "GS": {"lateral_rate": Decimal("0.27"), "retention_rate": Decimal("0.96")},
    "CP": {"lateral_rate": Decimal("0.14"), "retention_rate": Decimal("0.96")},
    "6EME": {"lateral_rate": Decimal("0.09"), "retention_rate": Decimal("0.96")},
    "2NDE": {"lateral_rate": Decimal("0.10"), "retention_rate": Decimal("0.96")},
    # Incidental lateral grades (fixed values)
    "CE1": {"fixed_lateral": 7, "retention_rate": Decimal("0.96")},
    "CE2": {"fixed_lateral": 6, "retention_rate": Decimal("0.96")},
    "CM1": {"fixed_lateral": 5, "retention_rate": Decimal("0.96")},
    "CM2": {"fixed_lateral": 7, "retention_rate": Decimal("0.96")},
    "5EME": {"fixed_lateral": 5, "retention_rate": Decimal("0.96")},
    "4EME": {"fixed_lateral": 6, "retention_rate": Decimal("0.96")},
    "3EME": {"fixed_lateral": 6, "retention_rate": Decimal("0.96")},
    "1ERE": {"fixed_lateral": 6, "retention_rate": Decimal("0.96")},
    "TLE": {"fixed_lateral": 1, "retention_rate": Decimal("0.98")},
}


# =============================================================================
# Effective Rates Models (for calibrated projection)
# =============================================================================


class EngineEffectiveRates(BaseModel):
    """
    Resolved effective rates for a single grade.

    This model is used by the projection engine when calibrated rates
    are available from the EnrollmentCalibrationService.

    Entry point grades (MS, GS, CP, 6EME, 2NDE):
        - Use lateral_entry_rate (percentage of previous grade)
        - lateral_entry_fixed is None

    Incidental grades (CE1, CE2, CM1, CM2, 5EME, 4EME, 3EME, 1ERE, TLE):
        - Use lateral_entry_fixed (absolute count)
        - lateral_entry_rate is None
    """

    grade_code: str
    retention_rate: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Retention rate (0.0 to 1.0)",
    )
    lateral_entry_rate: Decimal | None = Field(
        None,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Lateral entry rate as % of previous grade (for entry points)",
    )
    lateral_entry_fixed: int | None = Field(
        None,
        ge=0,
        le=100,
        description="Fixed lateral entry count (for incidental grades)",
    )
    is_percentage_based: bool = Field(
        ...,
        description="True for entry points (% rate), False for incidental (fixed)",
    )

    @property
    def is_entry_point(self) -> bool:
        """Alias for is_percentage_based."""
        return self.is_percentage_based

    model_config = ConfigDict(frozen=True)


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
    """
    Engine input for a target school year.

    Supports two modes for lateral entry calculation:

    1. **Legacy mode** (base_lateral_entry dict):
       - Uses fixed lateral entry counts from base_lateral_entry dict
       - Applies lateral_multiplier from scenario/global overrides
       - All grades treated uniformly with fixed values

    2. **Calibrated mode** (effective_rates dict):
       - Uses EngineEffectiveRates for each grade
       - Entry points (MS, GS, CP, 6EME, 2NDE): percentage of previous grade
       - Incidental grades: fixed values (already multiplied by scenario)
       - Retention and lateral already resolved from Override → Derived → Default

    When effective_rates is provided, it takes precedence over base_lateral_entry.
    """

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
        description="Base lateral entry by grade (legacy mode - fixed values)",
    )

    # Calibrated rates (new mode - takes precedence over base_lateral_entry)
    effective_rates: dict[str, EngineEffectiveRates] | None = Field(
        default=None,
        description="Calibrated effective rates by grade (keyed by grade_code)",
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

