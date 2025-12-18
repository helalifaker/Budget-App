"""
Lateral Entry Optimizer - Pydantic Models

Models for the capacity-aware lateral entry optimization system.

Instead of projecting demand (unreliable due to hyper-growth), this system
optimizes class structure by asking: "How many students can we efficiently
accommodate while minimizing rejections?"

Decision Logic:
    1. ACCEPT_ALL: demand ≤ fill_to_target (comfortable buffer)
    2. ACCEPT_FILL_MAX: fill_to_target < demand ≤ fill_to_max (fills classes)
    3. RESTRICT: fill_to_max < demand < new_class_threshold (awkward middle)
    4. NEW_CLASS: demand ≥ new_class_threshold (justifies opening new class)
    5. RESTRICT_AT_CEILING: At max_divisions limit (cannot expand further)
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Enums
# =============================================================================


class OptimizationDecision(str, Enum):
    """
    Decision type for lateral entry optimization.

    These decisions determine how many new students to accept based on
    class structure optimization rather than raw demand projection.
    """

    ACCEPT_ALL = "accept_all"
    """Demand ≤ fill_to_target. Accept all, leaves comfortable buffer."""

    ACCEPT_FILL_MAX = "accept_fill_max"
    """fill_to_target < demand ≤ fill_to_max. Accept all, fills to max class size."""

    RESTRICT = "restrict"
    """fill_to_max < demand < new_class_threshold. Cap at fill_to_max (awkward middle)."""

    NEW_CLASS = "new_class"
    """demand ≥ new_class_threshold. Accept enough to justify opening new class."""

    RESTRICT_AT_CEILING = "restrict_at_ceiling"
    """At max_divisions limit. Cannot expand further, cap at current capacity."""

    INSUFFICIENT_DEMAND = "insufficient_demand"
    """Demand is below minimum viable class size. Special handling needed."""


# =============================================================================
# Input Models
# =============================================================================


class ClassSizeConfig(BaseModel):
    """
    Class size parameters for a single grade.

    These values come from the class_size_params table and define
    the constraints for class formation.
    """

    min_class_size: int = Field(
        ...,
        ge=10,
        le=35,
        description="Minimum students per class (below which class won't form)",
    )
    target_class_size: int = Field(
        ...,
        ge=15,
        le=35,
        description="Target students per class (ideal operational size)",
    )
    max_class_size: int = Field(
        ...,
        ge=15,
        le=40,
        description="Maximum students per class (hard capacity limit)",
    )
    max_divisions: int = Field(
        default=6,
        ge=1,
        le=10,
        description="Maximum number of classes (divisions) for this grade",
    )

    model_config = ConfigDict(frozen=True)


class GradeOptimizationInput(BaseModel):
    """
    Input for optimizing lateral entry for a single grade.

    Contains all information needed to make an optimization decision.
    """

    grade_code: str = Field(..., description="Grade code (e.g., 'MS', '6EME')")
    cycle_code: str = Field(..., description="Cycle code (MAT, ELEM, COLL, LYC)")

    retained_students: int = Field(
        ...,
        ge=0,
        description="Students retained from previous grade (prev × retention_rate)",
    )
    historical_demand: int = Field(
        ...,
        ge=0,
        description="Historical lateral entry demand (from calibration)",
    )
    class_size_config: ClassSizeConfig = Field(
        ...,
        description="Class size parameters for this grade",
    )

    is_entry_point: bool = Field(
        default=False,
        description="True if this is a major entry point grade (MS, GS, CP, 6EME, 2NDE)",
    )

    model_config = ConfigDict(frozen=True)


# =============================================================================
# Output Models
# =============================================================================


class GradeOptimizationResult(BaseModel):
    """
    Result of optimization for a single grade.

    Contains the decision, capacities, and final student counts.
    """

    grade_code: str
    cycle_code: str
    is_entry_point: bool

    # Input values (echoed back for reference)
    retained_students: int
    historical_demand: int

    # Class structure from retention
    base_classes: int = Field(
        ...,
        description="Number of classes needed just for retained students",
    )

    # Capacity calculations
    fill_to_target: int = Field(
        ...,
        description="Slots available to reach target class size",
    )
    fill_to_max: int = Field(
        ...,
        description="Slots available to reach max class size",
    )
    new_class_threshold: int = Field(
        ...,
        description="Minimum lateral needed to justify opening new class",
    )

    # Decision
    decision: OptimizationDecision = Field(
        ...,
        description="Optimization decision made",
    )

    # Outputs
    accepted: int = Field(
        ...,
        ge=0,
        description="Number of new students accepted",
    )
    rejected: int = Field(
        ...,
        ge=0,
        description="Number of new students rejected (demand - accepted)",
    )

    # Final structure
    final_classes: int = Field(
        ...,
        ge=0,
        description="Final number of classes after optimization",
    )
    final_students: int = Field(
        ...,
        ge=0,
        description="Total students (retained + accepted)",
    )

    # Metrics
    avg_class_size: Decimal = Field(
        ...,
        description="Average class size after optimization",
    )
    utilization_pct: Decimal = Field(
        default=Decimal("0.0"),
        description="Utilization as percentage of target capacity",
    )
    acceptance_rate: Decimal = Field(
        default=Decimal("100.0"),
        description="Percentage of demand that was accepted",
    )

    model_config = ConfigDict(frozen=True)


class NewStudentsSummaryRow(BaseModel):
    """
    Single row in the new students summary table.

    Provides a clear view of intake optimization by grade.
    """

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
    pct_of_total_intake: Decimal = Field(
        ...,
        description="(accepted / total_new_students) × 100",
    )

    # Decision indicator
    decision: OptimizationDecision

    model_config = ConfigDict(frozen=True)


class NewStudentsSummary(BaseModel):
    """
    Complete summary of new student optimization across all grades.

    This is the model for the summary table at the bottom of the planning page.
    """

    # Totals
    total_demand: int = Field(..., description="Sum of all historical demand")
    total_available: int = Field(..., description="Sum of all available slots")
    total_accepted: int = Field(..., description="Sum of all accepted students")
    total_rejected: int = Field(..., description="Sum of all rejected students")

    # Overall metrics
    overall_acceptance_rate: Decimal = Field(
        ...,
        description="(total_accepted / total_demand) × 100",
    )

    # Breakdown by grade
    by_grade: list[NewStudentsSummaryRow] = Field(
        ...,
        description="Summary for each grade",
    )

    # Entry points vs incidental breakdown
    entry_point_demand: int = 0
    entry_point_accepted: int = 0
    incidental_demand: int = 0
    incidental_accepted: int = 0

    # Grades by decision type (for quick analysis)
    grades_accept_all: list[str] = Field(default_factory=list)
    grades_fill_max: list[str] = Field(default_factory=list)
    grades_restricted: list[str] = Field(default_factory=list)
    grades_new_class: list[str] = Field(default_factory=list)
    grades_at_ceiling: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


# =============================================================================
# Type Aliases
# =============================================================================

GradeDecisionMap = dict[str, GradeOptimizationResult]
"""Mapping from grade_code to optimization result."""

ClassSizeConfigMap = dict[str, ClassSizeConfig]
"""Mapping from grade_code to class size configuration."""
