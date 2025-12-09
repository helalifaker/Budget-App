"""
Planning Progress Schemas.

Pydantic models for the planning progress tracking and validation API.
These schemas define the contract for progress checking across all 6 planning steps.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# ==============================================================================
# Validation Schemas
# ==============================================================================


class StepValidation(BaseModel):
    """
    Validation check result for a planning step.

    Represents a single validation check (e.g., "enrollment_exists",
    "capacity_check") with its status and message.
    """

    check_id: str = Field(..., description="Unique identifier for this validation check")
    status: Literal["passed", "failed", "warning", "info"] = Field(
        ..., description="Validation check result status"
    )
    message: str = Field(..., description="Human-readable validation message")
    details: dict[str, Any] | None = Field(
        None, description="Additional details about the validation check"
    )


class StepBlocker(BaseModel):
    """
    Blocker preventing progress on a planning step.

    Blockers are critical issues that prevent the user from completing
    this step or moving to dependent steps.
    """

    message: str = Field(..., description="Description of the blocking issue")
    resolution: str = Field(
        ..., description="Suggested action to resolve the blocker"
    )


class StepProgress(BaseModel):
    """
    Progress and validation status for a single planning step.

    Represents the current state of one of the 6 planning steps
    (enrollment, class_structure, dhg, revenue, costs, capex).
    """

    step_id: str = Field(
        ...,
        description="Step identifier: enrollment, class_structure, dhg, revenue, costs, capex",
    )
    step_number: int = Field(..., ge=1, le=6, description="Step sequence number (1-6)")
    status: Literal["not_started", "in_progress", "completed", "blocked", "error"] = (
        Field(..., description="Current status of this planning step")
    )
    progress_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Completion percentage (0-100)"
    )
    validation: list[StepValidation] = Field(
        default_factory=list, description="List of validation check results"
    )
    blockers: list[StepBlocker] = Field(
        default_factory=list,
        description="List of blockers preventing progress on this step",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Key metrics for this step (e.g., total_students, total_fte)",
    )


# ==============================================================================
# Response Schemas
# ==============================================================================


class PlanningProgressResponse(BaseModel):
    """
    Overall planning progress for a budget version.

    Aggregates progress across all 6 planning steps with overall metrics,
    validation results, and blockers.
    """

    budget_version_id: UUID = Field(..., description="Budget version UUID")
    overall_progress: float = Field(
        ..., ge=0.0, le=100.0, description="Overall completion percentage (0-100)"
    )
    completed_steps: int = Field(
        ..., ge=0, le=6, description="Number of completed steps (0-6)"
    )
    total_steps: int = Field(
        default=6, description="Total number of planning steps (always 6)"
    )
    steps: list[StepProgress] = Field(
        ..., description="Progress details for each of the 6 planning steps"
    )


# ==============================================================================
# Step-Specific Metadata
# ==============================================================================


class StepMetadata(BaseModel):
    """
    Static metadata for a planning step.

    Defines display information, routing, and help content structure
    for each of the 6 planning steps.
    """

    step_id: str
    step_number: int
    title: str
    description: str
    route: str  # Frontend route path (e.g., "/planning/enrollment")
    icon: str  # Icon name (e.g., "Users", "Calculator", "DollarSign")
    prerequisite_steps: list[str] = Field(
        default_factory=list, description="Step IDs that must be completed first"
    )


# ==============================================================================
# Cascade Schemas
# ==============================================================================


class CascadeRequest(BaseModel):
    """
    Request to cascade recalculations through dependent planning steps.

    Either from_step_id OR step_ids should be provided:
    - from_step_id: Recalculate all steps downstream from this step
    - step_ids: Recalculate only these specific steps
    """

    from_step_id: str | None = Field(
        None,
        description="Step ID to cascade from (will recalculate all downstream steps)",
    )
    step_ids: list[str] | None = Field(
        None,
        description="Specific step IDs to recalculate (alternative to from_step_id)",
    )


class CascadeResponse(BaseModel):
    """Response from cascade recalculation operation."""

    recalculated_steps: list[str] = Field(
        default_factory=list, description="Steps that were successfully recalculated"
    )
    failed_steps: list[str] = Field(
        default_factory=list, description="Steps that failed recalculation"
    )
    message: str = Field(..., description="Summary message of the operation")


# Static step metadata
STEP_METADATA: dict[str, StepMetadata] = {
    "enrollment": StepMetadata(
        step_id="enrollment",
        step_number=1,
        title="Enrollment Planning",
        description="Project student enrollment by level and nationality",
        route="/planning/enrollment",
        icon="Users",
        prerequisite_steps=[],
    ),
    "class_structure": StepMetadata(
        step_id="class_structure",
        step_number=2,
        title="Class Structure",
        description="Calculate number of classes from enrollment",
        route="/planning/classes",
        icon="Grid3x3",
        prerequisite_steps=["enrollment"],
    ),
    "dhg": StepMetadata(
        step_id="dhg",
        step_number=3,
        title="DHG Workforce Planning",
        description="Calculate teacher FTE requirements and allocations",
        route="/planning/dhg",
        icon="Calculator",
        prerequisite_steps=["class_structure"],
    ),
    "revenue": StepMetadata(
        step_id="revenue",
        step_number=4,
        title="Revenue Planning",
        description="Project tuition, fees, and other revenue streams",
        route="/planning/revenue",
        icon="DollarSign",
        prerequisite_steps=["enrollment"],
    ),
    "costs": StepMetadata(
        step_id="costs",
        step_number=5,
        title="Cost Planning",
        description="Plan personnel and operating costs",
        route="/planning/costs",
        icon="TrendingDown",
        prerequisite_steps=["dhg", "enrollment"],
    ),
    "capex": StepMetadata(
        step_id="capex",
        step_number=6,
        title="CapEx Planning",
        description="Plan capital expenditures and depreciation (optional)",
        route="/planning/capex",
        icon="Building2",
        prerequisite_steps=[],
    ),
}
