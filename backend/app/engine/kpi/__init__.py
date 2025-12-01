"""
KPI Engine - Key Performance Indicator calculations (Module 15)

This module provides pure calculation functions for educational and financial KPIs.
All functions follow the pure function pattern with no side effects.
"""

from app.engine.kpi.calculator import (
    calculate_capacity_utilization,
    calculate_cost_per_student,
    calculate_he_ratio_secondary,
    calculate_margin_percentage,
    calculate_revenue_per_student,
    calculate_staff_cost_ratio,
    calculate_student_teacher_ratio,
)
from app.engine.kpi.models import (
    KPICalculationResult,
    KPIInput,
    KPIResult,
    KPIType,
)
from app.engine.kpi.validators import (
    validate_kpi_input,
    validate_ratio_bounds,
)

__all__ = [
    # Models
    "KPIInput",
    "KPIResult",
    "KPICalculationResult",
    "KPIType",
    # Calculator functions
    "calculate_student_teacher_ratio",
    "calculate_he_ratio_secondary",
    "calculate_revenue_per_student",
    "calculate_cost_per_student",
    "calculate_margin_percentage",
    "calculate_staff_cost_ratio",
    "calculate_capacity_utilization",
    # Validators
    "validate_kpi_input",
    "validate_ratio_bounds",
]
