"""
Enrollment Projection Engine - Pydantic Models

Pure input/output models for the Retention + Lateral Entry projection system
with 4-layer overrides and capacity constraints.

All grades now use percentage-based lateral entry (unified model).
Rates derived from weighted historical analysis: 70% N-1 + 30% N-2 (2024-2025 data).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Grade Classification Constants
# =============================================================================

# Entry point grades - major intake grades (used for UI badges, not calculation)
ENTRY_POINT_GRADES: frozenset[str] = frozenset({"MS", "GS", "CP", "6EME", "2NDE"})

# Cycle-based retention rates (derived from minimum progression analysis)
CYCLE_RETENTION_RATES: dict[str, Decimal] = {
    "MAT": Decimal("0.96"),   # Maternelle: stable families
    "ELEM": Decimal("0.96"),  # Élémentaire: stable families
    "COLL": Decimal("0.97"),  # Collège: high commitment
    "LYC": Decimal("0.93"),   # Lycée: students leave for France/other
}

# =============================================================================
# Unified Lateral Entry Defaults (70/30 Weighted Historical Analysis)
# =============================================================================
# ALL grades now use percentage-based lateral entry (no more fixed values)
# Formula: weighted_progression = 0.70 × (2024→2025) + 0.30 × (2023→2024)
# lateral_rate = weighted_progression - cycle_retention_rate

UNIFIED_LATERAL_DEFAULTS: dict[str, dict[str, Decimal]] = {
    # Maternelle (Entry Points - high lateral)
    "MS": {"lateral_rate": Decimal("0.363"), "retention_rate": Decimal("0.96")},  # 132.3%
    "GS": {"lateral_rate": Decimal("0.265"), "retention_rate": Decimal("0.96")},  # 122.5%

    # Élémentaire
    "CP": {"lateral_rate": Decimal("0.123"), "retention_rate": Decimal("0.96")},  # 108.3% (Entry)
    "CE1": {"lateral_rate": Decimal("0.085"), "retention_rate": Decimal("0.96")},  # 104.5%
    "CE2": {"lateral_rate": Decimal("0.050"), "retention_rate": Decimal("0.96")},  # 101.0%
    "CM1": {"lateral_rate": Decimal("0.017"), "retention_rate": Decimal("0.96")},  # 97.7%
    "CM2": {"lateral_rate": Decimal("0.071"), "retention_rate": Decimal("0.96")},  # 103.1%

    # Collège
    "6EME": {"lateral_rate": Decimal("0.107"), "retention_rate": Decimal("0.97")},  # 107.7% (Entry)
    "5EME": {"lateral_rate": Decimal("0.021"), "retention_rate": Decimal("0.97")},  # 99.1%
    "4EME": {"lateral_rate": Decimal("0.030"), "retention_rate": Decimal("0.97")},  # 100.0%
    "3EME": {"lateral_rate": Decimal("0.028"), "retention_rate": Decimal("0.97")},  # 99.8%

    # Lycée (lower retention - students leave for France)
    "2NDE": {"lateral_rate": Decimal("0.108"), "retention_rate": Decimal("0.93")},  # 103.8% (Entry)
    "1ERE": {"lateral_rate": Decimal("0.045"), "retention_rate": Decimal("0.93")},  # 97.5%
    "TLE": {"lateral_rate": Decimal("0.072"), "retention_rate": Decimal("0.93")},   # 100.2%
}

# Backward compatibility alias
DOCUMENT_LATERAL_DEFAULTS = UNIFIED_LATERAL_DEFAULTS


# =============================================================================
# Effective Rates Models (for calibrated projection)
# =============================================================================


class EngineEffectiveRates(BaseModel):
    """
    Resolved effective rates for a single grade.

    This model is used by the projection engine when calibrated rates
    are available from the EnrollmentCalibrationService.

    All grades now use percentage-based lateral entry (unified model).
    The is_entry_point flag is for UI purposes (badge display) only.
    """

    grade_code: str
    retention_rate: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Retention rate (0.0 to 1.0)",
    )
    lateral_entry_rate: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Lateral entry rate as % of previous grade (all grades)",
    )

    # Deprecated - kept for backward compatibility during migration
    lateral_entry_fixed: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="DEPRECATED: Fixed lateral entry count. Use lateral_entry_rate instead.",
    )
    is_percentage_based: bool = Field(
        default=True,
        description="DEPRECATED: Always True. All grades now use percentage-based lateral.",
    )

    @property
    def is_entry_point(self) -> bool:
        """Check if this grade is a major entry point (for UI badge display)."""
        return self.grade_code in ENTRY_POINT_GRADES

    @property
    def effective_progression(self) -> Decimal:
        """Calculate total progression rate: retention × (1 + lateral)."""
        return self.retention_rate * (Decimal("1") + self.lateral_entry_rate)

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


class GradeProjectionComponents(BaseModel):
    """Intermediate result with retain/lateral breakdown before capacity constraint."""

    grade_code: str
    retained: int = 0  # Students from previous grade × retention_rate
    lateral: int = 0  # Lateral entry (percentage-based or fixed)
    total: int = 0  # retained + lateral

    model_config = ConfigDict(frozen=True)


class GradeProjection(BaseModel):
    """Projection result for a single grade."""

    grade_code: str
    cycle_code: str
    projected_students: int  # Total (T) = retained + lateral (after capacity constraint)
    retained_students: int = 0  # Retain (R): from previous grade
    lateral_students: int = 0  # Lateral (L): new entries
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

    # Auditability: Intermediate calculation steps for debugging and audit trails
    calculation_breakdown: dict[str, Any] | None = Field(
        default=None,
        description="Intermediate calculation steps for audit trail",
    )

    model_config = ConfigDict(frozen=True)


ProjectionStatus = Literal["draft", "validated"]

