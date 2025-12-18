"""
EFIR Budget Planning Application - Teachers Module Models.

This module contains all teachers_* prefixed tables for the Workforce module.

Table Categories:
-----------------
1. ACTIVE Tables (use these for new development):
   - teachers_employees: Central employee registry (teachers + admin + support)
   - teachers_eos_provisions: End of Service liability tracking
   - teachers_dhg_subject_hours: DHG hours calculation per subject/level (OUTPUT)
   - teachers_dhg_requirements: Teacher FTE requirements per subject (OUTPUT)
   - teachers_allocations: Actual teacher assignments (TRMD gap analysis)

2. DEPRECATED Tables (Phase 4B consolidated - do not use for new code):
   - teachers_employee_salaries: DEPRECATED → Use Employee.basic_salary_sar etc.
   - teachers_aefe_positions: DEPRECATED → Use Employee.is_aefe_position etc.

Module Architecture:
--------------------
This module is part of the 10-module EFIR architecture:
- Module: Workforce
- Route: /workforce/*
- Color: wine
- Primary Role: HR Manager
- Purpose: Employees, DHG, requirements, gap analysis

Data Flow:
----------
Class Structure → DHG Hours → Teacher Requirements → Teacher Allocations
                                                   → Gap Analysis (TRMD)
                                                   → Personnel Costs

DHG Calculation:
----------------
DHG = Dotation Horaire Globale (Total Hours Allocation)
- Sum hours per subject across all levels
- Divide by standard teaching hours (18h secondary, 24h primary)
- Result = FTE (Full-Time Equivalent) teachers needed

TRMD Analysis:
--------------
TRMD = Tableau de Répartition des Moyens par Discipline
- Besoins (Needs) = DHG FTE requirements
- Moyens (Available) = Allocated teachers
- Déficit = Besoins - Moyens (hiring gap)

KSA Labor Law Compliance:
-------------------------
- Basic salary ≥ 50% of gross (for EOS calculation)
- GOSI rates: Saudi (11.75% employer + 9.75% employee), Expat (2% employer)
- EOS: 0.5 month per year (years 1-5), 1.0 month per year (years 6+)

Author: Claude Code
Date: 2025-12-16
Version: 1.0.0
"""

from __future__ import annotations

import os
import uuid
import warnings
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
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

if TYPE_CHECKING:
    from app.models.reference import AcademicCycle, AcademicLevel, Subject, TeacherCategory

# ==============================================================================
# Enums
# ==============================================================================


class EmployeeCategory(str, PyEnum):
    """
    Employee category classification.

    Categories:
    -----------
    AEFE_DETACHED: French ministry teacher on assignment (school pays PRRD ~41,863 EUR/year)
    AEFE_FUNDED: AEFE teacher fully funded (zero cost to school)
    LOCAL_TEACHER: Locally recruited teachers (full salary paid by school)
    ADMINISTRATIVE: Administrative staff (management, secretarial)
    SUPPORT: Support staff (ATSEM, maintenance, cleaning, security)
    """

    AEFE_DETACHED = "aefe_detached"  # School pays PRRD contribution (~41,863 EUR/year)
    AEFE_FUNDED = "aefe_funded"  # Fully funded by AEFE (zero cost to school)
    LOCAL_TEACHER = "local_teacher"  # Locally recruited teachers (full salary)
    ADMINISTRATIVE = "administrative"  # Administrative staff
    SUPPORT = "support"  # Support staff (ATSEM, maintenance, etc.)


class EmployeeNationality(str, PyEnum):
    """
    Employee nationality for GOSI calculation.

    GOSI Rates by Nationality:
    --------------------------
    SAUDI: 21.5% total (11.75% employer + 9.75% employee)
    EXPATRIATE: 2% total (2% employer only, no employee contribution)
    """

    SAUDI = "saudi"  # Saudi national
    EXPATRIATE = "expatriate"  # Expatriate (all non-Saudi)


class ContractType(str, PyEnum):
    """
    Employment contract type.

    Types:
    ------
    PERMANENT: CDI - Contrat à Durée Indéterminée (unlimited)
    FIXED_TERM: CDD - Contrat à Durée Déterminée (fixed-term)
    PART_TIME: Part-time contract
    """

    PERMANENT = "permanent"  # CDI - Permanent contract
    FIXED_TERM = "fixed_term"  # CDD - Fixed-term contract
    PART_TIME = "part_time"  # Part-time contract


class TerminationType(str, PyEnum):
    """
    Termination type affecting EOS calculation.

    EOS Resignation Factors:
    ------------------------
    - < 2 years service: 0% (no EOS)
    - 2-5 years: 33% of calculated EOS
    - 5-10 years: 67% of calculated EOS
    - > 10 years: 100% of calculated EOS

    For TERMINATION, END_OF_CONTRACT, RETIREMENT: Always 100% of EOS
    """

    RESIGNATION = "resignation"  # Employee resignation (factor applies)
    TERMINATION = "termination"  # Employer termination (full EOS)
    END_OF_CONTRACT = "end_of_contract"  # Contract ended (full EOS)
    RETIREMENT = "retirement"  # Retirement (full EOS)


class AEFEPositionType(str, PyEnum):
    """
    AEFE position type.

    Types:
    ------
    DETACHED: School pays PRRD contribution (~41,863 EUR/year)
    FUNDED: Fully funded by AEFE (zero school cost)

    School has 28 AEFE positions total:
    - 24 Detached positions
    - 4 Funded positions
    """

    DETACHED = "detached"  # School pays PRRD contribution
    FUNDED = "funded"  # Fully funded by AEFE (zero school cost)


# ==============================================================================
# ACTIVE Models - Employee Registry
# ==============================================================================


class Employee(BaseModel, VersionedMixin):
    """
    Central employee registry for all staff types.

    This model tracks all employees (teachers, administrative, support) with:
    - Employment details (hire date, contract type, nationality)
    - Teaching assignment (cycle, subject) for teachers
    - Department/role for non-teaching staff
    - Salary components (Phase 4B consolidation from teachers_employee_salaries)
    - AEFE position details (Phase 4B consolidation from teachers_aefe_positions)

    KSA Labor Law Requirements:
    ---------------------------
    - Hire date is required for EOS calculation
    - Nationality determines GOSI rates (Saudi vs Expatriate)
    - Basic salary must be at least 50% of gross salary

    Phase 4B Consolidation:
    -----------------------
    The following columns were consolidated from separate tables:
    - Salary columns (from teachers_employee_salaries)
    - AEFE position columns (from teachers_aefe_positions)

    Example Usage:
    --------------
    # Create a local teacher
    teacher = Employee(
        version_id=version_id,
        employee_code="EMP001",
        full_name="Ahmed Hassan",
        nationality=EmployeeNationality.SAUDI,
        category=EmployeeCategory.LOCAL_TEACHER,
        hire_date=date(2020, 9, 1),
        contract_type=ContractType.PERMANENT,
        cycle_id=secondary_cycle_id,
        subject_id=math_subject_id,
        fte=Decimal("1.00"),
        basic_salary_sar=Decimal("15000.00"),
        housing_allowance_sar=Decimal("3750.00"),
        transport_allowance_sar=Decimal("1500.00"),
    )
    """

    __tablename__ = "teachers_employees"

    # Build table args dynamically - skip explicit indexes during pytest
    _base_table_args = (
        # Unique employee code per version
        UniqueConstraint(
            "version_id",
            "employee_code",
            name="uk_employees_version_code",
        ),
        # Ensure basic_salary_percentage is at least 50% (KSA labor law)
        CheckConstraint(
            "basic_salary_percentage IS NULL OR basic_salary_percentage >= 0.50",
            name="ck_employees_basic_salary_min_50_percent",
        ),
    )

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

    # =========================================================================
    # Identification
    # =========================================================================
    employee_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Auto-generated employee code (EMP001, EMP002, etc.)",
    )

    # =========================================================================
    # Personal Information
    # =========================================================================
    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Employee full name",
    )

    nationality: Mapped[EmployeeNationality] = mapped_column(
        Enum(
            EmployeeNationality,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="Nationality for GOSI calculation (Saudi: 21.5%, Expat: 2%)",
    )

    # =========================================================================
    # Employment Classification
    # =========================================================================
    category: Mapped[EmployeeCategory] = mapped_column(
        Enum(
            EmployeeCategory,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="Employee category (AEFE_DETACHED, AEFE_FUNDED, LOCAL_TEACHER, etc.)",
    )

    # =========================================================================
    # Employment Details
    # =========================================================================
    hire_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Hire date (required for EOS calculation)",
    )

    contract_type: Mapped[ContractType] = mapped_column(
        Enum(
            ContractType,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ContractType.PERMANENT,
        comment="Contract type (permanent, fixed_term, part_time)",
    )

    contract_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Contract end date (for fixed-term contracts)",
    )

    # =========================================================================
    # Teaching Assignment (for teachers only)
    # =========================================================================
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Academic cycle (for teachers)",
    )

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_subjects", "id")),
        nullable=True,
        index=True,
        comment="Primary subject taught (for teachers)",
    )

    # =========================================================================
    # FTE Tracking
    # =========================================================================
    fte: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("1.00"),
        comment="Full-Time Equivalent (1.00 = full-time, 0.50 = half-time)",
    )

    # =========================================================================
    # Non-Teacher Details
    # =========================================================================
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

    # =========================================================================
    # Salary Configuration
    # =========================================================================
    basic_salary_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        default=Decimal("0.50"),
        comment="Basic salary as percentage of gross (min 50% for EOS calculation)",
    )

    # =========================================================================
    # Status Flags
    # =========================================================================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether employee is currently active",
    )

    is_placeholder: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True = Planned position (from DHG gap), False = Base 100 (existing)",
    )

    # =========================================================================
    # Termination Details
    # =========================================================================
    termination_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of termination (if applicable)",
    )

    termination_type: Mapped[TerminationType | None] = mapped_column(
        Enum(
            TerminationType,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="Type of termination (affects EOS calculation)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes",
    )

    # =========================================================================
    # Phase 4B: Consolidated Salary Columns (from teachers_employee_salaries)
    # =========================================================================
    basic_salary_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
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

    gross_salary_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Gross salary (SAR/month) = Basic + Housing + Transport + Other",
    )

    # GOSI Rates
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
    gosi_employer_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="GOSI employer contribution (SAR/month)",
    )

    gosi_employee_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="GOSI employee deduction (SAR/month)",
    )

    # Salary Effective Period
    salary_effective_from: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Salary effective from date",
    )

    salary_effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Salary effective to date (NULL = current)",
    )

    # =========================================================================
    # Phase 4B: Consolidated AEFE Columns (from teachers_aefe_positions)
    # =========================================================================
    is_aefe_position: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this employee holds an AEFE position",
    )

    aefe_position_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="AEFE position type (detached, funded) - NULL if not AEFE",
    )

    aefe_position_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="AEFE position number (1-28) - NULL if not AEFE",
    )

    prrd_amount_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="PRRD contribution (EUR/year) - for detached positions only",
    )

    prrd_exchange_rate_eur_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
        comment="EUR to SAR exchange rate for PRRD conversion",
    )

    prrd_amount_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="PRRD contribution in SAR (= EUR × exchange rate)",
    )

    # =========================================================================
    # Relationships
    # =========================================================================
    cycle: Mapped["AcademicCycle"] = relationship("AcademicCycle", foreign_keys=[cycle_id])
    subject: Mapped["Subject"] = relationship("Subject", foreign_keys=[subject_id])

    # Legacy relationships (maintained for backward compatibility during migration)
    salaries: Mapped[list["EmployeeSalary"]] = relationship(
        "EmployeeSalary",
        back_populates="employee",
        order_by="desc(EmployeeSalary.effective_from)",
    )
    eos_provisions: Mapped[list["EOSProvision"]] = relationship(
        "EOSProvision",
        back_populates="employee",
        order_by="desc(EOSProvision.as_of_date)",
    )
    aefe_position: Mapped["AEFEPosition | None"] = relationship(
        "AEFEPosition",
        back_populates="employee",
        uselist=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Employee(code={self.employee_code}, "
            f"name={self.full_name}, "
            f"category={self.category.value})>"
        )

    @property
    def is_teacher(self) -> bool:
        """Check if employee is a teacher (any type)."""
        return self.category in (
            EmployeeCategory.AEFE_DETACHED,
            EmployeeCategory.AEFE_FUNDED,
            EmployeeCategory.LOCAL_TEACHER,
        )

    @property
    def annual_gross_salary_sar(self) -> Decimal | None:
        """Calculate annual gross salary in SAR."""
        if self.gross_salary_sar:
            return self.gross_salary_sar * 12
        return None


# ==============================================================================
# ACTIVE Models - EOS Provision
# ==============================================================================


class EOSProvision(BaseModel, VersionedMixin):
    """
    End of Service (EOS) provision tracking.

    KSA Labor Law EOS Calculation:
    ------------------------------
    - Years 1-5: 0.5 × monthly basic salary × years
    - Years 6+:  1.0 × monthly basic salary × years

    Resignation Factors (if employee resigns):
    ------------------------------------------
    - < 2 years service: 0% (no EOS)
    - 2-5 years service: 33% of calculated EOS
    - 5-10 years service: 67% of calculated EOS
    - > 10 years service: 100% of calculated EOS

    For termination/contract end/retirement: Always 100%

    The provision represents the accrued liability at a point in time.
    Yearly EOS impact = Current provision - Previous provision.

    Example:
    --------
    Employee with 8 years service, 15,000 SAR basic salary:
    - Years 1-5: 0.5 × 15,000 × 5 = 37,500 SAR
    - Years 6-8: 1.0 × 15,000 × 3 = 45,000 SAR
    - Total provision: 82,500 SAR
    """

    __tablename__ = "teachers_eos_provisions"
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
        ForeignKey(
            get_fk_target("efir_budget", "teachers_employees", "id"),
            ondelete="CASCADE",
        ),
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
        comment="Resignation factor (0.00, 0.33, 0.67, or 1.00) if resigned",
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
    employee: Mapped["Employee"] = relationship("Employee", back_populates="eos_provisions")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<EOSProvision(employee_id={self.employee_id}, "
            f"as_of={self.as_of_date}, "
            f"amount={self.provision_amount_sar:,.2f} SAR)>"
        )


# ==============================================================================
# ACTIVE Models - DHG Planning (OUTPUT tables)
# ==============================================================================


class DHGSubjectHours(BaseModel, VersionedMixin):
    """
    DHG hours calculation per subject and level (OUTPUT table).

    DHG = Dotation Horaire Globale (Total Hours Allocation)

    Formula:
    --------
    total_hours_per_week = number_of_classes × hours_per_class_per_week

    If is_split = true (half-size groups like labs, language practice):
    total_hours_per_week = number_of_classes × hours_per_class_per_week × 2

    Example:
    --------
    Mathématiques in 6ème:
    - 6 classes × 4.5 hours = 27 hours/week

    Sciences Physiques in 3ème (split for labs):
    - 4 classes × 1.5 hours × 2 = 12 hours/week

    Data Flow:
    ----------
    SubjectHoursMatrix → DHGSubjectHours → DHGTeacherRequirement
    (config)            (calculated)      (FTE needs)

    Lineage Columns:
    ----------------
    This is an OUTPUT table with lineage tracking:
    - computed_at: When this output was computed
    - computed_by: User who triggered the computation
    - run_id: Unique ID for the computation run
    - inputs_hash: SHA-256 hash of inputs for cache invalidation
    """

    __tablename__ = "teachers_dhg_subject_hours"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "subject_id",
            "level_id",
            name="uk_dhg_hours_version_subject_level",
        ),
        CheckConstraint(
            "number_of_classes > 0",
            name="ck_dhg_hours_classes_positive",
        ),
        CheckConstraint(
            "hours_per_class_per_week > 0 AND hours_per_class_per_week <= 12",
            name="ck_dhg_hours_realistic_range",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_subjects", "id")),
        nullable=False,
        index=True,
        comment="Subject being taught",
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
        comment="Academic level",
    )

    number_of_classes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of classes at this level (from class_structures)",
    )

    hours_per_class_per_week: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Hours per class per week (from subject_hours_matrix)",
    )

    total_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="Total hours per week (classes × hours, ×2 if split)",
    )

    is_split: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether classes are split (counts as double hours)",
    )

    # =========================================================================
    # Lineage Columns (OUTPUT table tracking)
    # =========================================================================
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this output was computed",
    )

    computed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who triggered the computation",
    )

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Unique ID for the computation run",
    )

    inputs_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of inputs for cache invalidation",
    )

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject")
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DHGSubjectHours(subject_id={self.subject_id}, "
            f"level_id={self.level_id}, "
            f"hours={self.total_hours_per_week})>"
        )


class DHGTeacherRequirement(BaseModel, VersionedMixin):
    """
    Teacher FTE requirements per subject (OUTPUT table).

    This is the aggregation of DHGSubjectHours by subject to determine
    how many teachers are needed.

    Formula (Secondary - 18h standard):
    -----------------------------------
    simple_fte = total_hours_per_week / 18
    rounded_fte = CEILING(simple_fte)  # Round up to whole teachers
    hsa_hours = MAX(0, total_hours_per_week - (rounded_fte × 18))

    Formula (Primary - 24h standard):
    ---------------------------------
    simple_fte = total_hours_per_week / 24
    rounded_fte = CEILING(simple_fte)

    HSA = Heures Supplémentaires Annuelles (Annual Overtime Hours):
    - Overtime hours when total doesn't divide evenly
    - Capped at max_hsa_hours per teacher (typically 2-4 hours)
    - If negative, teachers are underutilized

    Example:
    --------
    Mathématiques across all Collège levels:
    - Total: 96 hours/week
    - Simple FTE: 96 / 18 = 5.33
    - Rounded FTE: 6 teachers
    - HSA: 96 - (6 × 18) = -12 (no overtime, 12 hours slack)

    Lineage Columns:
    ----------------
    This is an OUTPUT table with lineage tracking for audit.
    """

    __tablename__ = "teachers_dhg_requirements"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "subject_id",
            name="uk_dhg_teacher_req_version_subject",
        ),
        CheckConstraint(
            "total_hours_per_week >= 0",
            name="ck_dhg_req_hours_non_negative",
        ),
        CheckConstraint(
            "simple_fte >= 0",
            name="ck_dhg_req_fte_non_negative",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_subjects", "id")),
        nullable=False,
        index=True,
        comment="Subject",
    )

    total_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="Sum of DHG hours for this subject across all levels",
    )

    standard_teaching_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Standard teaching hours (18h secondary, 24h primary)",
    )

    simple_fte: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Exact FTE (total_hours / standard_hours)",
    )

    rounded_fte: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Rounded up FTE (ceiling of simple_fte)",
    )

    hsa_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Overtime hours needed (or negative if underutilized)",
    )

    # =========================================================================
    # Lineage Columns (OUTPUT table tracking)
    # =========================================================================
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this output was computed",
    )

    computed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who triggered the computation",
    )

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Unique ID for the computation run",
    )

    inputs_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of inputs for cache invalidation",
    )

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DHGTeacherRequirement(subject_id={self.subject_id}, "
            f"hours={self.total_hours_per_week}, "
            f"fte={self.rounded_fte})>"
        )


class TeacherAllocation(BaseModel, VersionedMixin):
    """
    Actual teacher assignments for TRMD gap analysis.

    TRMD = Tableau de Répartition des Moyens par Discipline
    (Resource Allocation Table by Subject)

    Gap Analysis Logic:
    -------------------
    Besoins (Need) = DHGTeacherRequirement.rounded_fte
    Moyens (Available) = SUM(TeacherAllocation.fte_count) by subject
    Déficit = Besoins - Moyens

    Interpretation:
    - If Déficit > 0: Need to recruit or assign HSA (overtime)
    - If Déficit < 0: Overallocated (teachers with free hours)
    - If Déficit = 0: Perfectly balanced

    Teacher Categories:
    -------------------
    - AEFE_DETACHED: School pays PRRD (~41,863 EUR/teacher/year)
    - AEFE_FUNDED: Fully funded by AEFE (zero school cost)
    - LOCAL: Locally recruited (full salary paid by school in SAR)

    Example:
    --------
    Mathématiques allocation:
    - DHG Requirement: 6 FTE
    - Allocations:
      - AEFE Detached: 2 FTE (cost = 2 × 41,863 EUR × 4.05 = 339,090 SAR)
      - Local: 3 FTE (cost = 3 × avg_salary)
    - Déficit: 6 - 5 = 1 FTE (need 1 more teacher)
    """

    __tablename__ = "teachers_allocations"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "subject_id",
            "cycle_id",
            "category_id",
            name="uk_allocation_version_subject_cycle_category",
        ),
        CheckConstraint("fte_count > 0", name="ck_allocation_fte_positive"),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_subjects", "id")),
        nullable=False,
        index=True,
        comment="Subject",
    )

    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=False,
        index=True,
        comment="Academic cycle (primary grouping for allocations)",
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_teacher_categories", "id")),
        nullable=False,
        index=True,
        comment="Teacher category (AEFE Detached, AEFE Funded, Local)",
    )

    fte_count: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Number of FTE allocated",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Allocation notes (teacher names, constraints, etc.)",
    )

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject")
    cycle: Mapped["AcademicCycle"] = relationship("AcademicCycle")
    category: Mapped["TeacherCategory"] = relationship("TeacherCategory")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TeacherAllocation(subject_id={self.subject_id}, "
            f"cycle_id={self.cycle_id}, "
            f"fte={self.fte_count})>"
        )


# ==============================================================================
# DEPRECATED Models (Phase 4B - kept for backward compatibility)
# ==============================================================================


class EmployeeSalary(BaseModel, VersionedMixin):
    """
    Employee salary breakdown for local employees.

    .. deprecated:: Phase 4B
        This model is DEPRECATED. Salary data is now consolidated directly
        into the Employee model (basic_salary_sar, housing_allowance_sar, etc.).
        This model is kept for backward compatibility during migration.

        Use Employee.basic_salary_sar and related fields for new code.

        A database view vw_employee_salaries provides backward-compatible queries.

    KSA-compliant salary structure:
    - Basic Salary: ~50% of gross (used for EOS/GOSI calculations)
    - Housing Allowance: ~25% of basic
    - Transport Allowance: ~10% of basic
    - Other Allowances: Variable

    Note: AEFE employees (Detached/Funded) are handled separately through AEFE positions.
    This table only stores salary data for LOCAL employees.
    """

    __tablename__ = "teachers_employee_salaries"
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

    def __init__(self, **kwargs) -> None:
        """Initialize with deprecation warning."""
        warnings.warn(
            "EmployeeSalary is deprecated (Phase 4B). "
            "Use Employee.basic_salary_sar and related fields instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            get_fk_target("efir_budget", "teachers_employees", "id"),
            ondelete="CASCADE",
        ),
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

    # Calculated Gross
    gross_salary_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Gross salary (SAR/month) = Basic + Housing + Transport + Other",
    )

    # GOSI Rates
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
    employee: Mapped["Employee"] = relationship("Employee", back_populates="salaries")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<EmployeeSalary(DEPRECATED, employee_id={self.employee_id}, "
            f"gross={self.gross_salary_sar:,.2f} SAR)>"
        )


class AEFEPosition(BaseModel, VersionedMixin):
    """
    AEFE position management.

    .. deprecated:: Phase 4B
        This model is DEPRECATED. AEFE position data is now consolidated directly
        into the Employee model (is_aefe_position, aefe_position_type, etc.).
        This model is kept for backward compatibility during migration.

        Use Employee.is_aefe_position and related fields for new code.

        A database view vw_aefe_positions provides backward-compatible queries.

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

    __tablename__ = "teachers_aefe_positions"
    __table_args__ = (
        # Unique position number per version
        UniqueConstraint(
            "version_id",
            "position_number",
            name="uk_aefe_positions_version_number",
        ),
        # An employee can only hold one AEFE position per version
        Index(
            "ix_aefe_positions_employee_unique",
            "version_id",
            "employee_id",
            unique=True,
            postgresql_where="employee_id IS NOT NULL",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    def __init__(self, **kwargs) -> None:
        """Initialize with deprecation warning."""
        warnings.warn(
            "AEFEPosition is deprecated (Phase 4B). "
            "Use Employee.is_aefe_position and related fields instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)

    # Position Identification
    position_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Position number (1-28)",
    )

    position_type: Mapped[AEFEPositionType] = mapped_column(
        Enum(
            AEFEPositionType,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="Position type (DETACHED = school pays PRRD, FUNDED = zero cost)",
    )

    # Teaching Assignment
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Academic cycle for this position",
    )

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_subjects", "id")),
        nullable=True,
        index=True,
        comment="Subject for this position",
    )

    # Employee Assignment (NULL if vacant)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            get_fk_target("efir_budget", "teachers_employees", "id"),
            ondelete="SET NULL",
        ),
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
    cycle: Mapped["AcademicCycle"] = relationship("AcademicCycle", foreign_keys=[cycle_id])
    subject: Mapped["Subject"] = relationship("Subject", foreign_keys=[subject_id])
    employee: Mapped["Employee | None"] = relationship(
        "Employee",
        back_populates="aefe_position",
        foreign_keys=[employee_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AEFEPosition(DEPRECATED, number={self.position_number}, "
            f"type={self.position_type.value}, "
            f"filled={self.is_filled})>"
        )


# ==============================================================================
# Backward Compatibility Aliases
# ==============================================================================

# No aliases needed - model names are already canonical
