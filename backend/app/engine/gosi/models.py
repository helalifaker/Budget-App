"""
Pydantic models for GOSI calculation engine.

Defines input and output types for GOSI calculations per KSA labor law.
"""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class Nationality(str, Enum):
    """Employee nationality for GOSI rate determination."""

    SAUDI = "saudi"
    EXPATRIATE = "expatriate"


# GOSI contribution rates (as of 2024)
GOSI_RATES = {
    Nationality.SAUDI: {
        "employer": Decimal("0.1175"),  # 11.75%
        "employee": Decimal("0.0975"),  # 9.75%
        "total": Decimal("0.2150"),  # 21.50%
    },
    Nationality.EXPATRIATE: {
        "employer": Decimal("0.02"),  # 2% (hazards insurance only)
        "employee": Decimal("0.00"),  # 0%
        "total": Decimal("0.02"),  # 2%
    },
}


class GOSIInput(BaseModel):
    """
    Input parameters for GOSI calculation.

    GOSI is calculated on gross salary (not just basic salary).
    """

    gross_salary_sar: Decimal = Field(
        ...,
        gt=Decimal("0"),
        description="Monthly gross salary in SAR",
    )
    nationality: Nationality = Field(
        ...,
        description="Employee nationality (saudi or expatriate)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "gross_salary_sar": 15000.00,
                    "nationality": "saudi",
                }
            ]
        }
    }


class GOSIResult(BaseModel):
    """
    Result of GOSI calculation.

    Contains employer and employee contributions.
    """

    # Input reference
    gross_salary_sar: Decimal = Field(..., description="Gross salary used for calculation")
    nationality: Nationality = Field(..., description="Employee nationality")

    # Rates
    employer_rate: Decimal = Field(..., description="Employer contribution rate")
    employee_rate: Decimal = Field(..., description="Employee contribution rate")
    total_rate: Decimal = Field(..., description="Total contribution rate")

    # Monthly amounts
    employer_contribution_sar: Decimal = Field(
        ...,
        description="Monthly employer contribution (SAR)",
    )
    employee_contribution_sar: Decimal = Field(
        ...,
        description="Monthly employee contribution (SAR)",
    )
    total_contribution_sar: Decimal = Field(
        ...,
        description="Total monthly contribution (SAR)",
    )

    # Net calculations
    net_salary_sar: Decimal = Field(
        ...,
        description="Net salary after employee GOSI deduction",
    )
    total_employer_cost_sar: Decimal = Field(
        ...,
        description="Total employer cost (gross + employer GOSI)",
    )

    # Annual projections
    annual_employer_contribution_sar: Decimal = Field(
        ...,
        description="Annual employer contribution",
    )
    annual_employee_contribution_sar: Decimal = Field(
        ...,
        description="Annual employee contribution",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "gross_salary_sar": 15000.00,
                    "nationality": "saudi",
                    "employer_rate": 0.1175,
                    "employee_rate": 0.0975,
                    "total_rate": 0.2150,
                    "employer_contribution_sar": 1762.50,
                    "employee_contribution_sar": 1462.50,
                    "total_contribution_sar": 3225.00,
                    "net_salary_sar": 13537.50,
                    "total_employer_cost_sar": 16762.50,
                    "annual_employer_contribution_sar": 21150.00,
                    "annual_employee_contribution_sar": 17550.00,
                }
            ]
        }
    }


class GOSISummaryResult(BaseModel):
    """
    Summary of GOSI across multiple employees.

    Used for payroll and budget reporting.
    """

    total_employees: int = Field(..., description="Number of employees")
    saudi_employees: int = Field(..., description="Number of Saudi employees")
    expatriate_employees: int = Field(..., description="Number of expatriate employees")

    # Monthly totals
    total_monthly_employer_sar: Decimal = Field(
        ...,
        description="Total monthly employer GOSI",
    )
    total_monthly_employee_sar: Decimal = Field(
        ...,
        description="Total monthly employee GOSI",
    )

    # Annual totals
    total_annual_employer_sar: Decimal = Field(
        ...,
        description="Total annual employer GOSI",
    )
    total_annual_employee_sar: Decimal = Field(
        ...,
        description="Total annual employee GOSI",
    )
