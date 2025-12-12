"""
Enrollment Engine - Enrollment projection calculations (Module 7)

This module provides pure calculation functions for enrollment planning,
including growth projections, capacity validation, and retention modeling.
"""

from app.engine.enrollment.calculator import (
    apply_retention_model,
    calculate_attrition,
    calculate_enrollment_projection,
)
from app.engine.enrollment.fiscal_year_proration import (
    calculate_fiscal_year_weighted_enrollment,
    calculate_proration_by_grade,
    get_school_years_for_fiscal_year,
)
from app.engine.enrollment.models import (
    EnrollmentGrowthScenario,
    EnrollmentInput,
    EnrollmentProjection,
    EnrollmentProjectionResult,
    RetentionModel,
)
from app.engine.enrollment.projection_engine import (
    project_enrollment,
    project_multi_year,
    validate_projection_input,
)
from app.engine.enrollment.projection_models import (
    GlobalOverrides,
    GradeOverride,
    GradeProjection,
    LevelOverride,
    ProjectionInput,
    ProjectionResult,
    ScenarioParams,
)
from app.engine.enrollment.validators import (
    validate_capacity,
    validate_growth_rate,
)

__all__ = [
    "EnrollmentGrowthScenario",
    "EnrollmentInput",
    "EnrollmentProjection",
    "EnrollmentProjectionResult",
    "GlobalOverrides",
    "GradeOverride",
    "GradeProjection",
    "LevelOverride",
    "ProjectionInput",
    "ProjectionResult",
    "RetentionModel",
    "ScenarioParams",
    "apply_retention_model",
    "calculate_attrition",
    "calculate_enrollment_projection",
    "calculate_fiscal_year_weighted_enrollment",
    "calculate_proration_by_grade",
    "get_school_years_for_fiscal_year",
    "project_enrollment",
    "project_multi_year",
    "validate_capacity",
    "validate_growth_rate",
    "validate_projection_input",
]
