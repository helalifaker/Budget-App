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
from app.engine.enrollment.models import (
    EnrollmentGrowthScenario,
    EnrollmentInput,
    EnrollmentProjection,
    EnrollmentProjectionResult,
    RetentionModel,
)
from app.engine.enrollment.validators import (
    validate_capacity,
    validate_growth_rate,
)

__all__ = [
    "EnrollmentGrowthScenario",
    # Models
    "EnrollmentInput",
    "EnrollmentProjection",
    "EnrollmentProjectionResult",
    "RetentionModel",
    "apply_retention_model",
    "calculate_attrition",
    # Calculator functions
    "calculate_enrollment_projection",
    # Validators
    "validate_capacity",
    "validate_growth_rate",
]
