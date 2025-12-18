"""
Validators for GOSI calculation inputs.

Ensures all inputs are valid before calculation.
"""

from decimal import Decimal

from .models import GOSIInput


class GOSIValidationError(ValueError):
    """Exception raised for GOSI validation errors."""

    pass


def validate_gosi_input(inputs: GOSIInput) -> None:
    """
    Validate GOSI calculation inputs.

    Args:
        inputs: GOSI calculation inputs

    Raises:
        GOSIValidationError: If any validation fails
    """
    # Validate gross_salary is positive
    if inputs.gross_salary_sar <= Decimal("0"):
        raise GOSIValidationError(
            f"Gross salary must be positive: {inputs.gross_salary_sar}"
        )

    # Validate reasonable salary range (sanity check)
    if inputs.gross_salary_sar > Decimal("1000000"):
        raise GOSIValidationError(
            f"Gross salary seems unreasonably high: {inputs.gross_salary_sar}. "
            "Please verify this is a monthly amount in SAR."
        )

    # Note: Low salaries (< 1,500 SAR) are allowed for part-time employees
    # KSA minimum for full-time Saudis is ~4,000 SAR
