"""
SQLAlchemy Models for Personnel/Workforce Management Module.

This module provides employee-based personnel management with:
- Full employee registry (teachers, administrative, support staff)
- KSA labor law compliant salary and EOS calculations
- AEFE position management (Detached + Funded)
- Budget version support for planning scenarios

Key Tables:
- employees: Central employee registry with Base 100 vs Planned distinction
- employee_salaries: KSA-compliant salary breakdown (Basic + Housing + Transport + Other)
- eos_provisions: End of Service liability tracking
- aefe_positions: AEFE position allocation (24 Detached + 4 Funded)
"""

from __future__ import annotations

import os
import uuid
from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    BaseModel,
    VersionedMixin,
    get_fk_target,
    get_schema,
)

# ==============================================================================
# Enums
# ==============================================================================


class EmployeeCategory(str, PyEnum):
    """Employee category classification."""

    AEFE_DETACHED = "aefe_detached"  # AEFE detached (school pays PRRD ~41,863 EUR)
    AEFE_FUNDED = "aefe_funded"  # AEFE fully funded (zero cost to school)
    LOCAL_TEACHER = "local_teacher"  # Locally recruited teachers
    ADMINISTRATIVE = "administrative"  # Administrative staff
    SUPPORT = "support"  # Support staff (ATSEM, maintenance, etc.)


class EmployeeNationality(str, PyEnum):
    """Employee nationality for GOSI calculation."""

    SAUDI = "saudi"  # Saudi national (GOSI: 21.5% - 11.75% employer + 9.75% employee)
    EXPATRIATE = "expatriate"  # Expatriate (GOSI: 2% employer only)


class ContractType(str, PyEnum):
    """Employment contract type."""

    PERMANENT = "permanent"  # CDI - Permanent contract
    FIXED_TERM = "fixed_term"  # CDD - Fixed-term contract
    PART_TIME = "part_time"  # Part-time contract


class TerminationType(str, PyEnum):
    """Termination type (affects EOS calculation)."""

    RESIGNATION = "resignation"  # Employee resignation (EOS factor applies)
    TERMINATION = "termination"  # Employer termination (full EOS)
    END_OF_CONTRACT = "end_of_contract"  # Contract ended (full EOS)
    RETIREMENT = "retirement"  # Retirement (full EOS)


class AEFEPositionType(str, PyEnum):
    """AEFE position type."""

    DETACHED = "detached"  # School pays PRRD contribution
    FUNDED = "funded"  # Fully funded by AEFE (zero school cost)


# ==============================================================================
# Employee Model
# ==============================================================================


class Employee(BaseModel, VersionedMixin):
    """
    Central employee registry.

    Tracks all staff (teachers + administrative + support) with:
    - Employment details (hire date, contract type, nationality)
    - Teaching assignment (cycle, subject) for teachers
    - Department/role for non-teachers
    - Base 100 vs Planned (placeholder) distinction

    KSA labor law requirements:
    - Hire date is required for EOS calculation
    - Nationality determines GOSI rates (Saudi vs Expatriate)
    - Basic salary percentage must be at least 50% of gross
    """

    __tablename__ = "employees"
    # Build table args dynamically - skip explicit indexes during pytest to avoid SQLite collision
    _base_table_args = (
        # Unique employee code per budget version
        UniqueConstraint(
            "budget_version_id",
            "employee_code",
            name="uk_employees_version_code",
        ),
        # Ensure basic_salary_percentage is at least 50%
        CheckConstraint(
            "basic_salary_percentage IS NULL OR basic_salary_percentage >= 0.50",
            name="ck_employees_basic_salary_min_50_percent",
        ),
    )
    # Only add explicit indexes in production (PostgreSQL) - SQLite handles indexes via column attrs
    if not os.environ.get("PYTEST_RUNNING"):
        __table_args__ = (
            *_base_table_args,
            Index("ix_employees_category", "category"),
            Index("ix_employees_is_active", "is_active"),
            Index("ix_employees_is_placeholder", "is_placeholder"),
            {"schema": "efir_budget"},
        )
    else:
        __table_args__ = (*_base_table_args, {})  # type: ignore[assignment]

    # Auto-generated employee code (EMP001, EMP002, etc.)
    employee_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Auto-generated employee code (EMP001, EMP002, etc.)",
    )

    # Personal Information
    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Employee full name",
    )

    nationality: Mapped[EmployeeNationality] = mapped_column(
        Enum(EmployeeNationality, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="Nationality for GOSI calculation (Saudi: 21.5%, Expat: 2%)",
    )

    # Employment Classification
    category: Mapped[EmployeeCategory] = mapped_column(
        Enum(EmployeeCategory, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        # Note: index defined explicitly in __table_args__ as ix_employees_category
        comment="Employee category (AEFE_DETACHED, AEFE_FUNDED, LOCAL_TEACHER, ADMINISTRATIVE, SUPPORT)",
    )

    # Employment Details
    hire_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Hire date (required for EOS calculation)",
    )

    contract_type: Mapped[ContractType] = mapped_column(
        Enum(ContractType, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ContractType.PERMANENT,
        comment="Contract type (permanent, fixed_term, part_time)",
    )

    contract_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Contract end date (for fixed-term contracts)",
    )

    # Teaching Assignment (for teachers only)
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Academic cycle (for teachers)",
    )

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "subjects", "id")),
        nullable=True,
        index=True,
        comment="Primary subject taught (for teachers)",
    )

    # FTE tracking
    fte: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("1.00"),
        comment="Full-Time Equivalent (1.00 = full-time, 0.50 = half-time)",
    )

    # Non-Teacher Details
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Department (for administrative/support staff)",
    )

    job_title: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Job title/position",
    )

    # Salary Configuration (for local employees)
    basic_salary_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        default=Decimal("0.50"),
        comment="Basic salary as percentage of gross (min 50% for EOS calculation)",
    )

    # Status Flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        # Note: index defined explicitly in __table_args__ as ix_employees_is_active
        comment="Whether employee is currently active",
    )

    is_placeholder: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        # Note: index defined explicitly in __table_args__ as ix_employees_is_placeholder
        comment="True = Planned position (from DHG gap), False = Base 100 (existing employee)",
    )

    # Termination Details
    termination_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of termination (if applicable)",
    )

    termination_type: Mapped[TerminationType | None] = mapped_column(
        Enum(TerminationType, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="Type of termination (affects EOS calculation)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes",
    )

    # Relationships
    cycle = relationship("AcademicCycle", foreign_keys=[cycle_id])
    subject = relationship("Subject", foreign_keys=[subject_id])
    salaries = relationship("EmployeeSalary", back_populates="employee", order_by="desc(EmployeeSalary.effective_from)")
    eos_provisions = relationship("EOSProvision", back_populates="employee", order_by="desc(EOSProvision.as_of_date)")
    aefe_position = relationship("AEFEPosition", back_populates="employee", uselist=False)


# ==============================================================================
# Employee Salary Model
# ==============================================================================


class EmployeeSalary(BaseModel, VersionedMixin):
    """
    Employee salary breakdown for local employees.

    KSA-compliant salary structure:
    - Basic Salary: ~50% of gross (used for EOS/GOSI calculations)
    - Housing Allowance: ~25% of basic
    - Transport Allowance: ~10% of basic
    - Other Allowances: Variable

    Note: AEFE employees (Detached/Funded) are handled separately through AEFE positions.
    This table only stores salary data for LOCAL employees.
    """

    __tablename__ = "employee_salaries"
    __table_args__ = (
        # Ensure no overlapping salary periods for same employee
        UniqueConstraint(
            "employee_id",
            "effective_from",
            name="uk_employee_salaries_employee_effective_from",
        ),
        # GOSI rates must be realistic
        CheckConstraint(
            "gosi_employer_rate >= 0 AND gosi_employer_rate <= 0.20",
            name="ck_employee_salaries_valid_gosi_employer_rate",
        ),
        CheckConstraint(
            "gosi_employee_rate >= 0 AND gosi_employee_rate <= 0.15",
            name="ck_employee_salaries_valid_gosi_employee_rate",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "employees", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Employee this salary belongs to",
    )

    # Effective Period
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Salary effective from date",
    )

    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Salary effective to date (NULL = current)",
    )

    # Salary Components (all in SAR)
    basic_salary_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Basic salary (SAR/month) - used for EOS/GOSI calculations",
    )

    housing_allowance_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Housing allowance (SAR/month)",
    )

    transport_allowance_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Transport allowance (SAR/month)",
    )

    other_allowances_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Other allowances (SAR/month)",
    )

    # Calculated Gross (can be computed or stored for performance)
    gross_salary_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Gross salary (SAR/month) = Basic + Housing + Transport + Other",
    )

    # GOSI Rates (stored to allow future rate changes)
    gosi_employer_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.1175"),
        comment="GOSI employer rate (Saudi: 11.75%, Expat: 2%)",
    )

    gosi_employee_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0975"),
        comment="GOSI employee rate (Saudi: 9.75%, Expat: 0%)",
    )

    # Calculated GOSI amounts
    gosi_employer_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="GOSI employer contribution (SAR/month)",
    )

    gosi_employee_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="GOSI employee deduction (SAR/month)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Salary notes",
    )

    # Relationships
    employee = relationship("Employee", back_populates="salaries")


# ==============================================================================
# EOS Provision Model
# ==============================================================================


class EOSProvision(BaseModel, VersionedMixin):
    """
    End of Service (EOS) provision tracking.

    KSA Labor Law EOS Calculation:
    - Years 1-5: 0.5 × monthly basic salary × years
    - Years 6+:  1.0 × monthly basic salary × years

    Resignation Factors (if employee resigns):
    - < 2 years:  0% (no EOS)
    - 2-5 years:  33% of calculated EOS
    - 5-10 years: 67% of calculated EOS
    - > 10 years: 100% of calculated EOS

    The provision represents the accrued liability at a point in time.
    Yearly EOS impact = Current provision - Previous provision.
    """

    __tablename__ = "eos_provisions"
    __table_args__ = (
        # One provision per employee per date
        UniqueConstraint(
            "employee_id",
            "as_of_date",
            name="uk_eos_provisions_employee_date",
        ),
        # Provision amounts must be non-negative
        CheckConstraint(
            "provision_amount_sar >= 0",
            name="ck_eos_provisions_non_negative_amount",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "employees", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Employee this provision belongs to",
    )

    # Point in time for provision calculation
    as_of_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of provision calculation",
    )

    # Service Duration
    years_of_service: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Complete years of service",
    )

    months_of_service: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Additional months of service (0-11)",
    )

    # Base Salary at calculation time
    base_salary_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Basic salary used for calculation (SAR/month)",
    )

    # Provision Components
    years_1_to_5_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="EOS for years 1-5 (0.5 × salary × years)",
    )

    years_6_plus_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="EOS for years 6+ (1.0 × salary × years)",
    )

    # Total Provision
    provision_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Total EOS provision (SAR) = Years 1-5 + Years 6+",
    )

    # Resignation Factor (if applicable)
    resignation_factor: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="Resignation factor (0.00, 0.33, 0.67, or 1.00) if employee resigned",
    )

    adjusted_provision_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Adjusted provision after resignation factor (if applicable)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Calculation notes",
    )

    # Relationships
    employee = relationship("Employee", back_populates="eos_provisions")


# ==============================================================================
# AEFE Position Model
# ==============================================================================


class AEFEPosition(BaseModel, VersionedMixin):
    """
    AEFE position management.

    The school has 28 AEFE positions:
    - 24 Detached positions: School pays PRRD contribution (~41,863 EUR/year)
    - 4 Funded positions: Fully funded by AEFE (zero cost to school)

    Each position can be:
    - Filled: Assigned to an employee
    - Vacant: Available for assignment

    PRRD (Participation à la Rémunération des Résidents Détachés):
    - Annual contribution paid to AEFE for detached teachers
    - Amount in EUR, converted to SAR for budget calculations
    """

    __tablename__ = "aefe_positions"
    __table_args__ = (
        # Unique position number per budget version
        UniqueConstraint(
            "budget_version_id",
            "position_number",
            name="uk_aefe_positions_version_number",
        ),
        # An employee can only hold one AEFE position per budget version
        Index(
            "ix_aefe_positions_employee_unique",
            "budget_version_id",
            "employee_id",
            unique=True,
            postgresql_where="employee_id IS NOT NULL",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    # Position Identification
    position_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Position number (1-28)",
    )

    position_type: Mapped[AEFEPositionType] = mapped_column(
        Enum(AEFEPositionType, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="Position type (DETACHED = school pays PRRD, FUNDED = zero cost)",
    )

    # Teaching Assignment
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Academic cycle for this position",
    )

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "subjects", "id")),
        nullable=True,
        index=True,
        comment="Subject for this position",
    )

    # Employee Assignment (NULL if vacant)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "employees", "id"), ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Employee assigned to this position (NULL if vacant)",
    )

    # PRRD Cost (for Detached positions)
    prrd_amount_eur: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("41863.00"),
        comment="PRRD contribution (EUR/year)",
    )

    exchange_rate_eur_sar: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        nullable=False,
        default=Decimal("4.05"),
        comment="EUR to SAR exchange rate",
    )

    prrd_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="PRRD contribution in SAR (= EUR × exchange rate)",
    )

    # Status
    is_filled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether position is filled (has assigned employee)",
    )

    # Academic Year (for tracking)
    academic_year: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Academic year (e.g., '2025-2026')",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Position notes",
    )

    # Relationships
    cycle = relationship("AcademicCycle", foreign_keys=[cycle_id])
    subject = relationship("Subject", foreign_keys=[subject_id])
    employee = relationship("Employee", back_populates="aefe_position", foreign_keys=[employee_id])
