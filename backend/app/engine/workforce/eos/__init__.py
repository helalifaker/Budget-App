"""
End of Service (EOS) Calculation Engine

KSA Labor Law compliant EOS calculation:
- Years 1-5: 0.5 x monthly basic salary x years
- Years 6+:  1.0 x monthly basic salary x years

Resignation Factors:
- < 2 years:  0% (no EOS)
- 2-5 years:  33% of calculated EOS
- 5-10 years: 67% of calculated EOS
- > 10 years: 100% of calculated EOS

Part of the Workforce module.

Usage:
    from app.engine.workforce.eos import calculate_eos, EOSInput, EOSResult

    result = calculate_eos(EOSInput(
        hire_date=date(2020, 1, 1),
        termination_date=date(2025, 12, 31),
        basic_salary_sar=Decimal("10000"),
        is_resignation=True
    ))
"""

from app.engine.workforce.eos.calculator import calculate_eos, calculate_eos_provision
from app.engine.workforce.eos.models import (
    EOSInput,
    EOSProvisionInput,
    EOSProvisionResult,
    EOSResult,
    TerminationReason,
)
from app.engine.workforce.eos.validators import validate_eos_input

__all__ = [
    # Models
    "EOSInput",
    "EOSProvisionInput",
    "EOSProvisionResult",
    "EOSResult",
    "TerminationReason",
    # Calculator functions
    "calculate_eos",
    "calculate_eos_provision",
    # Validators
    "validate_eos_input",
]
