"""
Enrollment Projection Engine - Core Calculations

Pure calculation functions for enrollment projections using retention + lateral entry model.

Key features:
- 3 scenarios with defaults (Conservative, Base, Optimistic)
- 4-layer overrides (Scenario -> Global -> Level -> Grade)
- Per-grade capacity clamp
- School-wide proportional capacity constraint
- Multi-year iterative cohort progression

Part of the Enrollment module.
"""

from app.engine.enrollment.projection.calculator import (
    apply_retention_model,
    calculate_attrition,
    calculate_enrollment_projection,
    calculate_multi_level_total,
)
from app.engine.enrollment.projection.fiscal_year_proration import (
    FiscalYearProration,
    calculate_fiscal_year_weighted_enrollment,
    calculate_proration_by_grade,
)
from app.engine.enrollment.projection.models import (
    EnrollmentGrowthScenario,
    EnrollmentInput,
    EnrollmentProjection,
    EnrollmentProjectionResult,
    RetentionModel,
)
from app.engine.enrollment.projection.projection_engine import (
    GRADE_SEQUENCE,
    GRADE_TO_CYCLE,
    apply_capacity_constraint,
    calculate_divisions,
    calculate_lateral_with_rates,
    get_effective_class_size,
    get_effective_lateral_entry,
    get_effective_lateral_multiplier,
    get_effective_max_divisions,
    get_effective_retention,
    get_effective_retention_with_rates,
    project_enrollment,
    project_multi_year,
    project_single_year,
    validate_projection_input,
)
from app.engine.enrollment.projection.projection_models import (
    CYCLE_RETENTION_RATES,
    DOCUMENT_LATERAL_DEFAULTS,
    ENTRY_POINT_GRADES,
    UNIFIED_LATERAL_DEFAULTS,
    EngineEffectiveRates,
    GlobalOverrides,
    GradeOverride,
    GradeProjection,
    GradeProjectionComponents,
    LevelOverride,
    ProjectionInput,
    ProjectionResult,
    ScenarioParams,
)
from app.engine.enrollment.projection.validators import (
    EFIR_MAX_CAPACITY,
    CapacityExceededError,
    InvalidGrowthRateError,
    validate_attrition_rate,
    validate_capacity,
    validate_growth_rate,
    validate_retention_rate,
    validate_total_capacity,
)

__all__ = [
    # Constants
    "CYCLE_RETENTION_RATES",
    "DOCUMENT_LATERAL_DEFAULTS",
    "EFIR_MAX_CAPACITY",
    "ENTRY_POINT_GRADES",
    "GRADE_SEQUENCE",
    "GRADE_TO_CYCLE",
    "UNIFIED_LATERAL_DEFAULTS",
    # Validators
    "CapacityExceededError",
    # Models - Projection
    "EngineEffectiveRates",
    # Models - Basic
    "EnrollmentGrowthScenario",
    "EnrollmentInput",
    "EnrollmentProjection",
    "EnrollmentProjectionResult",
    # Models - Fiscal Year
    "FiscalYearProration",
    "GlobalOverrides",
    "GradeOverride",
    "GradeProjection",
    "GradeProjectionComponents",
    "InvalidGrowthRateError",
    "LevelOverride",
    "ProjectionInput",
    "ProjectionResult",
    "RetentionModel",
    "ScenarioParams",
    # Calculator functions
    "apply_capacity_constraint",
    "apply_retention_model",
    "calculate_attrition",
    "calculate_divisions",
    "calculate_enrollment_projection",
    "calculate_fiscal_year_weighted_enrollment",
    "calculate_lateral_with_rates",
    "calculate_multi_level_total",
    "calculate_proration_by_grade",
    "get_effective_class_size",
    "get_effective_lateral_entry",
    "get_effective_lateral_multiplier",
    "get_effective_max_divisions",
    "get_effective_retention",
    "get_effective_retention_with_rates",
    "project_enrollment",
    "project_multi_year",
    "project_single_year",
    "validate_attrition_rate",
    "validate_capacity",
    "validate_growth_rate",
    "validate_projection_input",
    "validate_retention_rate",
    "validate_total_capacity",
]
