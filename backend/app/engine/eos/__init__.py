"""
End of Service (EOS) Calculation Engine

KSA Labor Law compliant EOS calculation:
- Years 1-5: 0.5 × monthly basic salary × years
- Years 6+:  1.0 × monthly basic salary × years

Resignation Factors:
- < 2 years:  0% (no EOS)
- 2-5 years:  33% of calculated EOS
- 5-10 years: 67% of calculated EOS
- > 10 years: 100% of calculated EOS

Usage:
    from app.engine.eos import calculate_eos, EOSInput, EOSResult

    result = calculate_eos(EOSInput(
        hire_date=date(2020, 1, 1),
        termination_date=date(2025, 12, 31),
        basic_salary_sar=Decimal("10000"),
        is_resignation=True
    ))
"""

from app.engine.eos.calculator import calculate_eos, calculate_eos_provision
from app.engine.eos.models import (
    EOSInput,
    EOSProvisionInput,
    EOSProvisionResult,
    EOSResult,
    TerminationReason,
)
from app.engine.eos.validators import validate_eos_input

__all__ = [
    "EOSInput",
    "EOSProvisionInput",
    "EOSProvisionResult",
    "EOSResult",
    "TerminationReason",
    "calculate_eos",
    "calculate_eos_provision",
    "validate_eos_input",
]
