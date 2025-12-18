"""
GOSI (General Organization for Social Insurance) Calculation Engine

KSA GOSI contribution rates:
- Saudi nationals: 21.5% total (11.75% employer + 9.75% employee)
- Expatriates: 2% employer only (hazards insurance)

Part of the Workforce module.

Usage:
    from app.engine.workforce.gosi import calculate_gosi, GOSIInput, GOSIResult

    result = calculate_gosi(GOSIInput(
        gross_salary_sar=Decimal("15000"),
        nationality="saudi"
    ))
"""

from app.engine.workforce.gosi.calculator import calculate_gosi, calculate_monthly_gosi
from app.engine.workforce.gosi.models import GOSIInput, GOSIResult, Nationality
from app.engine.workforce.gosi.validators import validate_gosi_input

__all__ = [
    # Models
    "GOSIInput",
    "GOSIResult",
    "Nationality",
    # Calculator functions
    "calculate_gosi",
    "calculate_monthly_gosi",
    # Validators
    "validate_gosi_input",
]
