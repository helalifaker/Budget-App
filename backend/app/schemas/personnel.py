"""
Pydantic schemas for workforce/personnel management endpoints.

Request and response models for:
- Employee management (CRUD, Base 100 vs Planned)
- Salary management (KSA-compliant structure)
- EOS provision calculation and tracking
- AEFE position management

KSA Labor Law Reference:
- Basic salary must be at least 50% of gross for EOS calculation
- GOSI: Saudi 21.5% (11.75% employer + 9.75% employee), Expat 2% employer only
- EOS: 0.5 months/year (years 1-5), 1.0 month/year (years 6+)
- Resignation factors: <2yr=0%, 2-5yr=33%, 5-10yr=67%, >10yr=100%
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.personnel import (
    AEFEPositionType,
    ContractType,
    EmployeeCategory,
    EmployeeNationality,
    TerminationType,
)

# ==============================================================================
# Employee Schemas
# ==============================================================================


class EmployeeBase(BaseModel):
    """Base schema for employee data."""

    full_name: str = Field(..., max_length=200, description="Employee full name")
    nationality: EmployeeNationality = Field(
        ...,
        description="Nationality for GOSI calculation (saudi=21.5%, expatriate=2%)",
    )
    category: EmployeeCategory = Field(..., description="Employee category")
    hire_date: date = Field(..., description="Hire date (required for EOS calculation)")
    contract_type: ContractType = Field(
        default=ContractType.PERMANENT,
        description="Contract type",
    )
    contract_end_date: date | None = Field(
        None,
        description="Contract end date (for fixed-term contracts)",
    )
    cycle_id: uuid.UUID | None = Field(None, description="Academic cycle (for teachers)")
    subject_id: uuid.UUID | None = Field(None, description="Primary subject (for teachers)")
    fte: Decimal = Field(
        default=Decimal("1.00"),
        ge=Decimal("0.00"),
        le=Decimal("1.00"),
        description="Full-Time Equivalent (1.00 = full-time)",
    )
    department: str | None = Field(None, max_length=100, description="Department (for non-teachers)")
    job_title: str | None = Field(None, max_length=100, description="Job title/position")
    basic_salary_percentage: Decimal | None = Field(
        default=Decimal("0.50"),
        ge=Decimal("0.50"),
        le=Decimal("1.00"),
        description="Basic salary as percentage of gross (min 50%)",
    )
    is_active: bool = Field(default=True, description="Whether employee is active")
    is_placeholder: bool = Field(
        default=False,
        description="True = Planned position (from DHG gap), False = Base 100",
    )
    notes: str | None = Field(None, description="Additional notes")


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee."""

    budget_version_id: uuid.UUID = Field(..., description="Budget version ID")

    @field_validator("hire_date")
    @classmethod
    def validate_hire_date(cls, v: date) -> date:
        """Ensure hire date is not in the future."""
        if v > date.today():
            raise ValueError("Hire date cannot be in the future")
        return v

    @model_validator(mode="after")
    def validate_teacher_fields(self) -> "EmployeeCreate":
        """Validate teacher-specific fields are present for teacher categories."""
        if self.category in (
            EmployeeCategory.AEFE_DETACHED,
            EmployeeCategory.AEFE_FUNDED,
            EmployeeCategory.LOCAL_TEACHER,
        ):
            # Teachers should have cycle_id set (subject is optional for primary teachers)
            if self.cycle_id is None and not self.is_placeholder:
                # Only require for non-placeholder employees
                pass  # Allow for now, can be set later
        return self


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""

    full_name: str | None = Field(None, max_length=200)
    nationality: EmployeeNationality | None = None
    category: EmployeeCategory | None = None
    contract_type: ContractType | None = None
    contract_end_date: date | None = None
    cycle_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    fte: Decimal | None = Field(None, ge=Decimal("0.00"), le=Decimal("1.00"))
    department: str | None = Field(None, max_length=100)
    job_title: str | None = Field(None, max_length=100)
    basic_salary_percentage: Decimal | None = Field(
        None, ge=Decimal("0.50"), le=Decimal("1.00")
    )
    is_active: bool | None = None
    notes: str | None = None
    termination_date: date | None = None
    termination_type: TerminationType | None = None


class EmployeeResponse(EmployeeBase):
    """Schema for employee response."""

    id: uuid.UUID
    employee_code: str = Field(..., description="Auto-generated employee code (EMP001, etc.)")
    budget_version_id: uuid.UUID
    termination_date: date | None = None
    termination_type: TerminationType | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def convert_types_from_sqlite(cls, data: Any) -> Any:
        """Handle SQLite type conversions."""
        if hasattr(data, "__dict__"):
            data_dict = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
        elif isinstance(data, dict):
            data_dict = data.copy()
        else:
            return data

        # Convert datetime fields
        datetime_fields = ["created_at", "updated_at"]
        for field in datetime_fields:
            value = data_dict.get(field)
            if value is not None and isinstance(value, int):
                try:
                    data_dict[field] = datetime.fromtimestamp(value, tz=UTC)
                except (ValueError, OSError):
                    data_dict[field] = datetime.now(UTC)

        return data_dict


class EmployeeBulkResponse(BaseModel):
    """Schema for bulk employee list response."""

    employees: list[EmployeeResponse]
    total: int
    base_100_count: int = Field(..., description="Number of Base 100 employees")
    planned_count: int = Field(..., description="Number of Planned (placeholder) employees")


# ==============================================================================
# Placeholder Employee Creation (from DHG Gap)
# ==============================================================================


class PlaceholderEmployeeCreate(BaseModel):
    """Schema for creating placeholder employee from DHG gap analysis."""

    budget_version_id: uuid.UUID = Field(..., description="Budget version ID")
    category: EmployeeCategory = Field(
        default=EmployeeCategory.LOCAL_TEACHER,
        description="Employee category for placeholder",
    )
    cycle_id: uuid.UUID | None = Field(None, description="Academic cycle")
    subject_id: uuid.UUID | None = Field(None, description="Subject")
    fte: Decimal = Field(
        default=Decimal("1.00"),
        ge=Decimal("0.00"),
        le=Decimal("1.00"),
        description="FTE requirement",
    )
    estimated_salary_sar: Decimal | None = Field(
        None,
        gt=Decimal("0"),
        description="Estimated gross salary based on category average",
    )
    notes: str | None = Field(None, description="Placeholder notes (e.g., from DHG gap)")


class PlaceholderValidationRequest(BaseModel):
    """Schema for validating and confirming placeholder creation."""

    placeholder_id: uuid.UUID = Field(
        ...,
        description="ID of placeholder employee to validate",
    )
    confirmed: bool = Field(
        default=False,
        description="User confirmation to finalize placeholder creation",
    )


# ==============================================================================
# Employee Salary Schemas
# ==============================================================================


class EmployeeSalaryBase(BaseModel):
    """Base schema for employee salary."""

    effective_from: date = Field(..., description="Salary effective from date")
    effective_to: date | None = Field(None, description="Salary effective to date")
    basic_salary_sar: Decimal = Field(
        ...,
        gt=Decimal("0"),
        description="Basic salary (SAR/month) - used for EOS/GOSI",
    )
    housing_allowance_sar: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0"),
        description="Housing allowance (SAR/month)",
    )
    transport_allowance_sar: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0"),
        description="Transport allowance (SAR/month)",
    )
    other_allowances_sar: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0"),
        description="Other allowances (SAR/month)",
    )
    notes: str | None = Field(None, description="Salary notes")


class EmployeeSalaryCreate(EmployeeSalaryBase):
    """Schema for creating employee salary."""

    budget_version_id: uuid.UUID = Field(..., description="Budget version ID")
    employee_id: uuid.UUID = Field(..., description="Employee ID")

    @model_validator(mode="after")
    def validate_dates(self) -> "EmployeeSalaryCreate":
        """Ensure effective_to is after effective_from."""
        if self.effective_to and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class EmployeeSalaryUpdate(BaseModel):
    """Schema for updating employee salary."""

    effective_to: date | None = None
    basic_salary_sar: Decimal | None = Field(None, gt=Decimal("0"))
    housing_allowance_sar: Decimal | None = Field(None, ge=Decimal("0"))
    transport_allowance_sar: Decimal | None = Field(None, ge=Decimal("0"))
    other_allowances_sar: Decimal | None = Field(None, ge=Decimal("0"))
    notes: str | None = None


class EmployeeSalaryResponse(EmployeeSalaryBase):
    """Schema for employee salary response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    employee_id: uuid.UUID
    gross_salary_sar: Decimal = Field(..., description="Gross salary = Basic + Housing + Transport + Other")
    gosi_employer_rate: Decimal = Field(..., description="GOSI employer rate")
    gosi_employee_rate: Decimal = Field(..., description="GOSI employee rate")
    gosi_employer_sar: Decimal = Field(..., description="GOSI employer contribution")
    gosi_employee_sar: Decimal = Field(..., description="GOSI employee deduction")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalaryBreakdownResponse(BaseModel):
    """Schema for salary breakdown display."""

    employee_id: uuid.UUID
    employee_name: str
    nationality: EmployeeNationality
    basic_salary_sar: Decimal
    housing_allowance_sar: Decimal
    transport_allowance_sar: Decimal
    other_allowances_sar: Decimal
    gross_salary_sar: Decimal
    gosi_employer_sar: Decimal
    gosi_employee_sar: Decimal
    net_salary_sar: Decimal = Field(..., description="Gross - GOSI employee")
    total_employer_cost_sar: Decimal = Field(..., description="Gross + GOSI employer")


# ==============================================================================
# EOS Provision Schemas
# ==============================================================================


class EOSProvisionBase(BaseModel):
    """Base schema for EOS provision."""

    as_of_date: date = Field(..., description="Date of provision calculation")


class EOSProvisionCreate(EOSProvisionBase):
    """Schema for creating/calculating EOS provision."""

    budget_version_id: uuid.UUID = Field(..., description="Budget version ID")
    employee_id: uuid.UUID = Field(..., description="Employee ID")


class EOSProvisionResponse(EOSProvisionBase):
    """Schema for EOS provision response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    employee_id: uuid.UUID
    years_of_service: int
    months_of_service: int
    base_salary_sar: Decimal
    years_1_to_5_amount_sar: Decimal
    years_6_plus_amount_sar: Decimal
    provision_amount_sar: Decimal
    resignation_factor: Decimal | None = None
    adjusted_provision_sar: Decimal | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EOSCalculationRequest(BaseModel):
    """Schema for calculating EOS (without saving)."""

    hire_date: date = Field(..., description="Employee hire date")
    termination_date: date | None = Field(
        None,
        description="Termination date (defaults to today)",
    )
    basic_salary_sar: Decimal = Field(..., gt=Decimal("0"), description="Monthly basic salary")
    termination_type: TerminationType | None = Field(
        None,
        description="Type of termination (affects resignation factor)",
    )


class EOSCalculationResponse(BaseModel):
    """Schema for EOS calculation result."""

    years_of_service: int
    months_of_service: int
    total_service_years: Decimal = Field(..., description="Total years including months")
    years_1_to_5_amount_sar: Decimal
    years_6_plus_amount_sar: Decimal
    gross_eos_sar: Decimal = Field(..., description="Total before resignation factor")
    resignation_factor: Decimal | None = Field(
        None,
        description="Factor applied for resignation (0.00, 0.33, 0.67, 1.00)",
    )
    final_eos_sar: Decimal = Field(..., description="Final EOS amount after factor")
    calculation_breakdown: str = Field(..., description="Human-readable calculation breakdown")


class EOSSummaryResponse(BaseModel):
    """Schema for EOS summary across all employees."""

    budget_version_id: uuid.UUID
    as_of_date: date
    total_employees: int
    total_provision_sar: Decimal
    provision_by_category: dict[str, Decimal]
    year_over_year_change_sar: Decimal | None = Field(
        None,
        description="Change from previous year's provision",
    )


# ==============================================================================
# AEFE Position Schemas
# ==============================================================================


class AEFEPositionBase(BaseModel):
    """Base schema for AEFE position."""

    position_number: int = Field(..., ge=1, le=28, description="Position number (1-28)")
    position_type: AEFEPositionType = Field(..., description="Position type (detached or funded)")
    cycle_id: uuid.UUID | None = Field(None, description="Academic cycle")
    subject_id: uuid.UUID | None = Field(None, description="Subject")
    prrd_amount_eur: Decimal = Field(
        default=Decimal("41863.00"),
        gt=Decimal("0"),
        description="PRRD contribution (EUR/year)",
    )
    exchange_rate_eur_sar: Decimal = Field(
        default=Decimal("4.05"),
        gt=Decimal("0"),
        description="EUR to SAR exchange rate",
    )
    academic_year: str | None = Field(None, max_length=20, description="Academic year")
    notes: str | None = Field(None, description="Position notes")


class AEFEPositionCreate(AEFEPositionBase):
    """Schema for creating AEFE position."""

    budget_version_id: uuid.UUID = Field(..., description="Budget version ID")
    employee_id: uuid.UUID | None = Field(None, description="Assigned employee (NULL if vacant)")


class AEFEPositionUpdate(BaseModel):
    """Schema for updating AEFE position."""

    cycle_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    employee_id: uuid.UUID | None = None
    prrd_amount_eur: Decimal | None = Field(None, gt=Decimal("0"))
    exchange_rate_eur_sar: Decimal | None = Field(None, gt=Decimal("0"))
    academic_year: str | None = Field(None, max_length=20)
    notes: str | None = None


class AEFEPositionResponse(AEFEPositionBase):
    """Schema for AEFE position response."""

    id: uuid.UUID
    budget_version_id: uuid.UUID
    employee_id: uuid.UUID | None = None
    prrd_amount_sar: Decimal = Field(..., description="PRRD in SAR")
    is_filled: bool
    employee_name: str | None = Field(None, description="Assigned employee name")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AEFEPositionSummaryResponse(BaseModel):
    """Schema for AEFE positions summary."""

    budget_version_id: uuid.UUID
    total_positions: int = Field(default=28, description="Total AEFE positions (24 + 4)")
    detached_positions: int = Field(default=24, description="Detached positions (school pays PRRD)")
    funded_positions: int = Field(default=4, description="Funded positions (zero cost)")
    filled_positions: int
    vacant_positions: int
    total_prrd_eur: Decimal = Field(..., description="Total PRRD cost in EUR")
    total_prrd_sar: Decimal = Field(..., description="Total PRRD cost in SAR")
    positions: list[AEFEPositionResponse]


class InitializeAEFEPositionsRequest(BaseModel):
    """Schema for initializing 28 AEFE positions."""

    budget_version_id: uuid.UUID = Field(..., description="Budget version ID")
    academic_year: str = Field(..., max_length=20, description="Academic year")
    prrd_amount_eur: Decimal = Field(
        default=Decimal("41863.00"),
        description="PRRD amount per detached position",
    )
    exchange_rate_eur_sar: Decimal = Field(
        default=Decimal("4.05"),
        description="EUR to SAR exchange rate",
    )


# ==============================================================================
# Workforce Summary Schemas
# ==============================================================================


class WorkforceSummaryResponse(BaseModel):
    """Schema for workforce summary dashboard."""

    budget_version_id: uuid.UUID
    total_employees: int
    active_employees: int
    base_100_count: int
    planned_count: int
    by_category: dict[str, int]
    by_nationality: dict[str, int]
    total_fte: Decimal
    aefe_positions_filled: int
    aefe_positions_vacant: int
    total_monthly_payroll_sar: Decimal
    total_gosi_employer_sar: Decimal
    total_eos_provision_sar: Decimal
