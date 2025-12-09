"""
EOS (End of Service) Calculator

KSA Labor Law Article 84-85 Implementation:
- Years 1-5: 0.5 × monthly basic salary × years
- Years 6+:  1.0 × monthly basic salary × years

Resignation factors (Article 85):
- < 2 years:  0% (no EOS)
- 2-5 years:  33% of calculated EOS
- 5-10 years: 67% of calculated EOS
- > 10 years: 100% of calculated EOS

Note: Prorated calculation for partial years.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.engine.eos.models import (
    EOSInput,
    EOSProvisionInput,
    EOSProvisionResult,
    EOSResult,
    TerminationReason,
)


def _calculate_service_duration(
    hire_date: date,
    end_date: date,
) -> tuple[int, int, Decimal]:
    """
    Calculate years and months of service.

    Args:
        hire_date: Employee start date
        end_date: End date for calculation

    Returns:
        Tuple of (years, months, total_years_decimal)

    Example:
        hire_date=2020-01-15, end_date=2025-12-31
        Returns: (5, 11, 5.917)
    """
    # Calculate total months
    total_months = (end_date.year - hire_date.year) * 12 + (end_date.month - hire_date.month)

    # Adjust for day of month
    if end_date.day < hire_date.day:
        total_months -= 1

    # Handle negative months (end_date before hire_date)
    if total_months < 0:
        total_months = 0

    years = total_months // 12
    months = total_months % 12

    # Calculate decimal years for precise calculation
    total_years = Decimal(str(total_months)) / Decimal("12")
    total_years = total_years.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    return years, months, total_years


def _get_resignation_factor(
    total_service_years: Decimal,
    termination_reason: TerminationReason,
) -> Decimal:
    """
    Get resignation factor based on service duration and reason.

    KSA Labor Law Article 85:
    - < 2 years:  0% (no EOS for resignation)
    - 2-5 years:  33% of calculated EOS
    - 5-10 years: 67% of calculated EOS
    - > 10 years: 100% of calculated EOS

    Args:
        total_service_years: Total years of service as decimal
        termination_reason: Reason for termination

    Returns:
        Resignation factor (0.00, 0.33, 0.67, or 1.00)
    """
    # Full EOS for non-resignation terminations
    if termination_reason != TerminationReason.RESIGNATION:
        return Decimal("1.00")

    # Apply resignation factors
    if total_service_years < Decimal("2"):
        return Decimal("0.00")
    elif total_service_years < Decimal("5"):
        return Decimal("0.33")
    elif total_service_years < Decimal("10"):
        return Decimal("0.67")
    else:
        return Decimal("1.00")


def _calculate_eos_breakdown(
    basic_salary_sar: Decimal,
    total_service_years: Decimal,
) -> tuple[Decimal, Decimal]:
    """
    Calculate EOS breakdown by service period.

    KSA Labor Law:
    - Years 1-5: 0.5 × monthly salary × years (capped at 5 years)
    - Years 6+:  1.0 × monthly salary × years

    Args:
        basic_salary_sar: Monthly basic salary
        total_service_years: Total years of service as decimal

    Returns:
        Tuple of (years_1_to_5_amount, years_6_plus_amount)
    """
    # Calculate years in each bucket
    years_in_first_bucket = min(total_service_years, Decimal("5"))
    years_in_second_bucket = max(total_service_years - Decimal("5"), Decimal("0"))

    # Calculate amounts
    years_1_to_5_amount = (
        Decimal("0.5") * basic_salary_sar * years_in_first_bucket
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    years_6_plus_amount = (
        Decimal("1.0") * basic_salary_sar * years_in_second_bucket
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return years_1_to_5_amount, years_6_plus_amount


def _format_calculation_breakdown(
    years: int,
    months: int,
    total_years: Decimal,
    basic_salary_sar: Decimal,
    years_1_to_5_amount: Decimal,
    years_6_plus_amount: Decimal,
    gross_eos: Decimal,
    resignation_factor: Decimal,
    final_eos: Decimal,
    termination_reason: TerminationReason,
) -> str:
    """Format human-readable calculation breakdown."""
    lines = [
        f"Service: {years}y {months}m = {total_years} years",
    ]

    # Years 1-5 calculation
    years_in_first = min(total_years, Decimal("5"))
    lines.append(
        f"Years 1-5: 0.5 × SAR {basic_salary_sar:,.2f} × {years_in_first:.2f} = SAR {years_1_to_5_amount:,.2f}"
    )

    # Years 6+ calculation (if applicable)
    years_in_second = max(total_years - Decimal("5"), Decimal("0"))
    if years_in_second > 0:
        lines.append(
            f"Years 6+: 1.0 × SAR {basic_salary_sar:,.2f} × {years_in_second:.2f} = SAR {years_6_plus_amount:,.2f}"
        )

    lines.append(f"Gross EOS: SAR {gross_eos:,.2f}")

    # Resignation factor (if applicable)
    if termination_reason == TerminationReason.RESIGNATION:
        factor_percent = int(resignation_factor * 100)
        if total_years < Decimal("2"):
            lines.append(f"Resignation factor (<2yr): {factor_percent}% - No EOS")
        elif total_years < Decimal("5"):
            lines.append(f"Resignation factor (2-5yr): {factor_percent}%")
        elif total_years < Decimal("10"):
            lines.append(f"Resignation factor (5-10yr): {factor_percent}%")
        else:
            lines.append(f"Resignation factor (>10yr): {factor_percent}% - Full EOS")

    lines.append(f"Final EOS: SAR {final_eos:,.2f}")

    return "\n".join(lines)


def calculate_eos(inputs: EOSInput) -> EOSResult:
    """
    Calculate End of Service benefit.

    KSA Labor Law compliant calculation:
    - Years 1-5: 0.5 × monthly basic salary × years
    - Years 6+:  1.0 × monthly basic salary × years
    - Resignation factor applied based on service duration

    Args:
        inputs: EOS calculation inputs

    Returns:
        EOSResult with full breakdown

    Example:
        >>> result = calculate_eos(EOSInput(
        ...     hire_date=date(2020, 1, 1),
        ...     termination_date=date(2025, 12, 31),
        ...     basic_salary_sar=Decimal("10000"),
        ...     termination_reason=TerminationReason.TERMINATION
        ... ))
        >>> result.final_eos_sar
        Decimal('29583.33')
    """
    # Calculate service duration
    years, months, total_years = _calculate_service_duration(
        inputs.hire_date,
        inputs.termination_date,
    )

    # Calculate EOS breakdown
    years_1_to_5_amount, years_6_plus_amount = _calculate_eos_breakdown(
        inputs.basic_salary_sar,
        total_years,
    )

    # Calculate gross EOS
    gross_eos = years_1_to_5_amount + years_6_plus_amount

    # Get resignation factor
    resignation_factor = _get_resignation_factor(
        total_years,
        inputs.termination_reason,
    )

    # Calculate final EOS
    final_eos = (gross_eos * resignation_factor).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Format breakdown
    breakdown = _format_calculation_breakdown(
        years=years,
        months=months,
        total_years=total_years,
        basic_salary_sar=inputs.basic_salary_sar,
        years_1_to_5_amount=years_1_to_5_amount,
        years_6_plus_amount=years_6_plus_amount,
        gross_eos=gross_eos,
        resignation_factor=resignation_factor,
        final_eos=final_eos,
        termination_reason=inputs.termination_reason,
    )

    return EOSResult(
        years_of_service=years,
        months_of_service=months,
        total_service_years=total_years,
        basic_salary_sar=inputs.basic_salary_sar,
        termination_reason=inputs.termination_reason,
        years_1_to_5_amount_sar=years_1_to_5_amount,
        years_6_plus_amount_sar=years_6_plus_amount,
        gross_eos_sar=gross_eos,
        resignation_factor=resignation_factor,
        final_eos_sar=final_eos,
        calculation_breakdown=breakdown,
    )


def calculate_eos_provision(inputs: EOSProvisionInput) -> EOSProvisionResult:
    """
    Calculate EOS provision (accrued liability at a point in time).

    Used for budget planning - calculates what the EOS liability would be
    if the employee were terminated on the as_of_date.
    No resignation factor applied (assumes full termination).

    Args:
        inputs: Provision calculation inputs

    Returns:
        EOSProvisionResult with provision amount
    """
    # Calculate service duration
    years, months, total_years = _calculate_service_duration(
        inputs.hire_date,
        inputs.as_of_date,
    )

    # Calculate EOS breakdown (no resignation factor for provision)
    years_1_to_5_amount, years_6_plus_amount = _calculate_eos_breakdown(
        inputs.basic_salary_sar,
        total_years,
    )

    # Total provision
    provision_amount = years_1_to_5_amount + years_6_plus_amount

    return EOSProvisionResult(
        as_of_date=inputs.as_of_date,
        years_of_service=years,
        months_of_service=months,
        total_service_years=total_years,
        basic_salary_sar=inputs.basic_salary_sar,
        years_1_to_5_amount_sar=years_1_to_5_amount,
        years_6_plus_amount_sar=years_6_plus_amount,
        provision_amount_sar=provision_amount,
    )
