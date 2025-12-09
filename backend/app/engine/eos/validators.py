"""
Validators for EOS calculation inputs.

Ensures all inputs are valid before calculation.
"""

from datetime import date
from decimal import Decimal

from app.engine.eos.models import EOSInput, EOSProvisionInput


class EOSValidationError(ValueError):
    """Exception raised for EOS validation errors."""

    pass


def validate_eos_input(inputs: EOSInput) -> None:
    """
    Validate EOS calculation inputs.

    Args:
        inputs: EOS calculation inputs

    Raises:
        EOSValidationError: If any validation fails
    """
    # Validate hire_date is not in the future
    if inputs.hire_date > date.today():
        raise EOSValidationError(
            f"Hire date cannot be in the future: {inputs.hire_date}"
        )

    # Validate termination_date is not before hire_date
    if inputs.termination_date < inputs.hire_date:
        raise EOSValidationError(
            f"Termination date ({inputs.termination_date}) cannot be before "
            f"hire date ({inputs.hire_date})"
        )

    # Validate basic_salary is positive
    if inputs.basic_salary_sar <= Decimal("0"):
        raise EOSValidationError(
            f"Basic salary must be positive: {inputs.basic_salary_sar}"
        )

    # Validate reasonable salary range (sanity check)
    if inputs.basic_salary_sar > Decimal("1000000"):
        raise EOSValidationError(
            f"Basic salary seems unreasonably high: {inputs.basic_salary_sar}. "
            "Please verify this is a monthly amount in SAR."
        )


def validate_eos_provision_input(inputs: EOSProvisionInput) -> None:
    """
    Validate EOS provision calculation inputs.

    Args:
        inputs: EOS provision calculation inputs

    Raises:
        EOSValidationError: If any validation fails
    """
    # Validate hire_date is not in the future
    if inputs.hire_date > date.today():
        raise EOSValidationError(
            f"Hire date cannot be in the future: {inputs.hire_date}"
        )

    # Validate as_of_date is not before hire_date
    if inputs.as_of_date < inputs.hire_date:
        raise EOSValidationError(
            f"As-of date ({inputs.as_of_date}) cannot be before "
            f"hire date ({inputs.hire_date})"
        )

    # Validate basic_salary is positive
    if inputs.basic_salary_sar <= Decimal("0"):
        raise EOSValidationError(
            f"Basic salary must be positive: {inputs.basic_salary_sar}"
        )
