"""
Pydantic models for EOS calculation engine.

Defines input and output types for EOS calculations per KSA labor law.
"""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class TerminationReason(str, Enum):
    """Termination reason enum for EOS calculation."""

    TERMINATION = "termination"  # Employer termination (full EOS)
    RESIGNATION = "resignation"  # Employee resignation (factor applies)
    END_OF_CONTRACT = "end_of_contract"  # Contract ended (full EOS)
    RETIREMENT = "retirement"  # Retirement (full EOS)


class EOSInput(BaseModel):
    """
    Input parameters for EOS calculation.

    All required fields for calculating End of Service benefits.
    """

    hire_date: date = Field(..., description="Employee hire date")
    termination_date: date = Field(
        default_factory=date.today,
        description="Termination date (defaults to today for provision calculation)",
    )
    basic_salary_sar: Decimal = Field(
        ...,
        gt=Decimal("0"),
        description="Monthly basic salary in SAR (not gross)",
    )
    termination_reason: TerminationReason = Field(
        default=TerminationReason.TERMINATION,
        description="Reason for termination (affects resignation factor)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "hire_date": "2020-01-01",
                    "termination_date": "2025-12-31",
                    "basic_salary_sar": 10000.00,
                    "termination_reason": "resignation",
                }
            ]
        }
    }


class EOSResult(BaseModel):
    """
    Result of EOS calculation.

    Contains full breakdown of EOS components and final amounts.
    """

    # Service duration
    years_of_service: int = Field(..., description="Complete years of service")
    months_of_service: int = Field(..., description="Additional months (0-11)")
    total_service_years: Decimal = Field(..., description="Total years including months as decimal")

    # Base inputs
    basic_salary_sar: Decimal = Field(..., description="Monthly basic salary used for calculation")
    termination_reason: TerminationReason = Field(..., description="Termination reason")

    # Calculation breakdown
    years_1_to_5_amount_sar: Decimal = Field(
        ...,
        description="EOS for years 1-5: 0.5 × salary × years (max 5)",
    )
    years_6_plus_amount_sar: Decimal = Field(
        ...,
        description="EOS for years 6+: 1.0 × salary × years",
    )
    gross_eos_sar: Decimal = Field(
        ...,
        description="Total EOS before resignation factor",
    )

    # Resignation factor
    resignation_factor: Decimal = Field(
        ...,
        description="Factor applied for resignation (0.00, 0.33, 0.67, or 1.00)",
    )
    final_eos_sar: Decimal = Field(
        ...,
        description="Final EOS amount after applying resignation factor",
    )

    # Human-readable breakdown
    calculation_breakdown: str = Field(
        ...,
        description="Human-readable calculation explanation",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "years_of_service": 5,
                    "months_of_service": 11,
                    "total_service_years": 5.92,
                    "basic_salary_sar": 10000.00,
                    "termination_reason": "resignation",
                    "years_1_to_5_amount_sar": 25000.00,
                    "years_6_plus_amount_sar": 0.00,
                    "gross_eos_sar": 29583.33,
                    "resignation_factor": 0.67,
                    "final_eos_sar": 19820.83,
                    "calculation_breakdown": "Service: 5y 11m = 5.92 years\nYears 1-5: 0.5 × SAR 10,000 × 5.00 = SAR 25,000.00\nYears 6+: 1.0 × SAR 10,000 × 0.92 = SAR 9,166.67 (prorated)\nGross EOS: SAR 29,583.33\nResignation factor (5-10yr): 67%\nFinal EOS: SAR 19,820.83",
                }
            ]
        }
    }


class EOSProvisionInput(BaseModel):
    """
    Input for calculating EOS provision (point-in-time liability).

    Used for calculating the accrued EOS liability at a specific date
    without actual termination.
    """

    hire_date: date = Field(..., description="Employee hire date")
    as_of_date: date = Field(
        default_factory=date.today,
        description="Date for provision calculation",
    )
    basic_salary_sar: Decimal = Field(
        ...,
        gt=Decimal("0"),
        description="Current monthly basic salary in SAR",
    )


class EOSProvisionResult(BaseModel):
    """
    Result of EOS provision calculation.

    Represents the accrued liability at a point in time.
    """

    as_of_date: date = Field(..., description="Date of provision calculation")
    years_of_service: int = Field(..., description="Complete years of service")
    months_of_service: int = Field(..., description="Additional months (0-11)")
    total_service_years: Decimal = Field(..., description="Total years as decimal")
    basic_salary_sar: Decimal = Field(..., description="Basic salary used")
    years_1_to_5_amount_sar: Decimal = Field(..., description="EOS for years 1-5")
    years_6_plus_amount_sar: Decimal = Field(..., description="EOS for years 6+")
    provision_amount_sar: Decimal = Field(..., description="Total provision amount")
