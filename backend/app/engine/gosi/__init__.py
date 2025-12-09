"""
GOSI (General Organization for Social Insurance) Calculation Engine

KSA GOSI contribution rates:
- Saudi nationals: 21.5% total (11.75% employer + 9.75% employee)
- Expatriates: 2% employer only (hazards insurance)

Usage:
    from app.engine.gosi import calculate_gosi, GOSIInput, GOSIResult

    result = calculate_gosi(GOSIInput(
        gross_salary_sar=Decimal("15000"),
        nationality="saudi"
    ))
"""

from app.engine.gosi.calculator import calculate_gosi, calculate_monthly_gosi
from app.engine.gosi.models import GOSIInput, GOSIResult, Nationality
from app.engine.gosi.validators import validate_gosi_input

__all__ = [
    "GOSIInput",
    "GOSIResult",
    "Nationality",
    "calculate_gosi",
    "calculate_monthly_gosi",
    "validate_gosi_input",
]
