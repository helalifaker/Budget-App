"""
DHG Engine - Teacher Workforce Planning (Module 9)

This module implements the DHG (Dotation Horaire Globale) methodology
for calculating teacher workforce requirements in the French education system.

DHG Formula:
    Total Hours = Σ(Classes × Hours per Subject per Level)
    Teacher FTE = Total Hours ÷ Standard Hours (18h/week for secondary)

Key Concepts:
- DHG Hours: Total teaching hours required based on curriculum
- Standard Hours: 18h/week for secondary, 24h/week for primary
- HSA: Overtime hours (max 2-4h per teacher)
- TRMD: Gap analysis (Besoins vs Available positions)
- AEFE Costs: School contribution for detached teachers
"""

from app.engine.dhg.calculator import (
    calculate_dhg_hours,
    calculate_fte_from_hours,
    calculate_teacher_requirement,
    calculate_hsa_allocation,
)
from app.engine.dhg.models import (
    EducationLevel,
    DHGInput,
    SubjectHours,
    DHGHoursResult,
    FTECalculationResult,
    TeacherRequirement,
    HSAAllocation,
)
from app.engine.dhg.validators import (
    validate_dhg_input,
    validate_subject_hours,
    validate_hsa_limits,
)

__all__ = [
    # Models
    "EducationLevel",
    "DHGInput",
    "SubjectHours",
    "DHGHoursResult",
    "FTECalculationResult",
    "TeacherRequirement",
    "HSAAllocation",
    # Calculator functions
    "calculate_dhg_hours",
    "calculate_fte_from_hours",
    "calculate_teacher_requirement",
    "calculate_hsa_allocation",
    # Validators
    "validate_dhg_input",
    "validate_subject_hours",
    "validate_hsa_limits",
]
