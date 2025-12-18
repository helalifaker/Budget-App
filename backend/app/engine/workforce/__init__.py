"""
Workforce Module - Personnel Planning Engines

This module contains calculation engines for teacher workforce planning,
including DHG (hours allocation), EOS (end of service), and GOSI (social insurance).

Sub-modules:
- dhg: DHG hours and FTE calculations
- eos: End of service benefit calculations
- gosi: GOSI contribution calculations

Part of the 10-module engine structure matching frontend.
"""

from app.engine.workforce.dhg import (
    DHGHoursResult,
    DHGInput,
    EducationLevel,
    FTECalculationResult,
    HSAAllocation,
    SubjectHours,
    TeacherRequirement,
    TRMDGapResult,
    calculate_dhg_hours,
    calculate_fte_from_hours,
    calculate_hsa_allocation,
    calculate_teacher_requirement,
    calculate_trmd_gap,
    validate_dhg_input,
    validate_hsa_limits,
    validate_standard_hours,
    validate_subject_hours,
)
from app.engine.workforce.eos import (
    EOSInput,
    EOSProvisionInput,
    EOSProvisionResult,
    EOSResult,
    TerminationReason,
    calculate_eos,
    calculate_eos_provision,
    validate_eos_input,
)
from app.engine.workforce.gosi import (
    GOSIInput,
    GOSIResult,
    Nationality,
    calculate_gosi,
    calculate_monthly_gosi,
    validate_gosi_input,
)

__all__ = [
    # DHG Models
    "DHGHoursResult",
    "DHGInput",
    # EOS Models
    "EOSInput",
    "EOSProvisionInput",
    "EOSProvisionResult",
    "EOSResult",
    "EducationLevel",
    "FTECalculationResult",
    # GOSI Models
    "GOSIInput",
    "GOSIResult",
    "HSAAllocation",
    "Nationality",
    "SubjectHours",
    "TRMDGapResult",
    "TeacherRequirement",
    "TerminationReason",
    # DHG Functions
    "calculate_dhg_hours",
    # EOS Functions
    "calculate_eos",
    "calculate_eos_provision",
    "calculate_fte_from_hours",
    # GOSI Functions
    "calculate_gosi",
    "calculate_hsa_allocation",
    "calculate_monthly_gosi",
    "calculate_teacher_requirement",
    "calculate_trmd_gap",
    "validate_dhg_input",
    "validate_eos_input",
    "validate_gosi_input",
    "validate_hsa_limits",
    "validate_standard_hours",
    "validate_subject_hours",
]
