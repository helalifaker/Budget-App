"""
GOSI (General Organization for Social Insurance) Calculator

KSA GOSI contribution rates:
- Saudi nationals: 21.5% total
  - Employer: 11.75% (retirement 9%, hazards 2%, SANED 0.75%)
  - Employee: 9.75% (retirement)
- Expatriates: 2% total
  - Employer: 2% (hazards insurance only)
  - Employee: 0%

GOSI is calculated on gross salary.
"""

from decimal import ROUND_HALF_UP, Decimal

from .models import GOSI_RATES, GOSIInput, GOSIResult, Nationality


def calculate_gosi(inputs: GOSIInput) -> GOSIResult:
    """
    Calculate GOSI contributions.

    Args:
        inputs: GOSI calculation inputs

    Returns:
        GOSIResult with full breakdown

    Example:
        >>> result = calculate_gosi(GOSIInput(
        ...     gross_salary_sar=Decimal("15000"),
        ...     nationality=Nationality.SAUDI
        ... ))
        >>> result.employer_contribution_sar
        Decimal('1762.50')
    """
    # Get rates for nationality
    rates = GOSI_RATES[inputs.nationality]

    # Calculate contributions
    employer_contribution = (inputs.gross_salary_sar * rates["employer"]).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    employee_contribution = (inputs.gross_salary_sar * rates["employee"]).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total_contribution = employer_contribution + employee_contribution

    # Calculate net salary and total employer cost
    net_salary = inputs.gross_salary_sar - employee_contribution
    total_employer_cost = inputs.gross_salary_sar + employer_contribution

    # Calculate annual amounts
    annual_employer = employer_contribution * 12
    annual_employee = employee_contribution * 12

    return GOSIResult(
        gross_salary_sar=inputs.gross_salary_sar,
        nationality=inputs.nationality,
        employer_rate=rates["employer"],
        employee_rate=rates["employee"],
        total_rate=rates["total"],
        employer_contribution_sar=employer_contribution,
        employee_contribution_sar=employee_contribution,
        total_contribution_sar=total_contribution,
        net_salary_sar=net_salary,
        total_employer_cost_sar=total_employer_cost,
        annual_employer_contribution_sar=annual_employer,
        annual_employee_contribution_sar=annual_employee,
    )


def calculate_monthly_gosi(
    gross_salary_sar: Decimal,
    nationality: Nationality,
) -> tuple[Decimal, Decimal]:
    """
    Quick calculation of monthly GOSI contributions.

    Simplified version for use in bulk calculations.

    Args:
        gross_salary_sar: Monthly gross salary
        nationality: Employee nationality

    Returns:
        Tuple of (employer_contribution, employee_contribution)
    """
    rates = GOSI_RATES[nationality]

    employer = (gross_salary_sar * rates["employer"]).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    employee = (gross_salary_sar * rates["employee"]).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return employer, employee


def get_gosi_rates(nationality: Nationality) -> dict[str, Decimal]:
    """
    Get GOSI rates for a nationality.

    Args:
        nationality: Employee nationality

    Returns:
        Dict with employer, employee, and total rates
    """
    return GOSI_RATES[nationality]
