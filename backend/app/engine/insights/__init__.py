"""
Insights Module - Analytics and KPI Engines

This module contains calculation engines for key performance indicators
and analytics dashboards.

Sub-modules:
- kpi: Key performance indicator calculations
"""

# Re-export from kpi sub-module
from app.engine.insights.kpi import (
    KPICalculationResult,
    KPIInput,
    KPIResult,
    KPIType,
    calculate_all_kpis,
    calculate_capacity_utilization,
    calculate_cost_per_student,
    calculate_he_ratio_secondary,
    calculate_margin_percentage,
    calculate_revenue_per_student,
    calculate_staff_cost_ratio,
    calculate_student_teacher_ratio,
    validate_kpi_input,
    validate_ratio_bounds,
)

__all__ = [
    "KPICalculationResult",
    "KPIInput",
    "KPIResult",
    "KPIType",
    "calculate_all_kpis",
    "calculate_capacity_utilization",
    "calculate_cost_per_student",
    "calculate_he_ratio_secondary",
    "calculate_margin_percentage",
    "calculate_revenue_per_student",
    "calculate_staff_cost_ratio",
    "calculate_student_teacher_ratio",
    "validate_kpi_input",
    "validate_ratio_bounds",
]
