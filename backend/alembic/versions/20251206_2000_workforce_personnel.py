"""Workforce Module: Employee-based personnel management.

Revision ID: 015_workforce_personnel
Revises: 014_historical_comparison
Create Date: 2025-12-06 20:00:00.000000

Creates tables for employee-based personnel management:
- employees: Central employee registry (Base 100 + Planned positions)
- employee_salaries: KSA-compliant salary breakdown
- eos_provisions: End of Service liability tracking
- aefe_positions: AEFE position allocation (24 Detached + 4 Funded)

Business Purpose:
-----------------
Transform from category-based teacher costs to employee-level tracking with:
- Full KSA labor law compliance (EOS, GOSI calculations)
- AEFE employee handling (Detached with PRRD, Funded at zero cost)
- DHG integration for placeholder position creation
- Clear Base 100 vs Planned employee distinction

KSA Labor Law Requirements:
--------------------------
- EOS: 0.5 months/year (years 1-5), 1.0 month/year (years 6+)
- GOSI: Saudi 21.5% (11.75% employer + 9.75% employee), Expat 2% employer only
- Resignation factors: <2yr=0%, 2-5yr=33%, 5-10yr=67%, >10yr=100%

AEFE Structure:
--------------
- 24 Detached positions: School pays PRRD (~41,863 EUR/year)
- 4 Funded positions: Fully funded by AEFE (zero school cost)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = "015_workforce_personnel"
down_revision: str | None = "014_historical_comparison"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create workforce/personnel management tables."""

    # =========================================================================
    # Create EmployeeCategory enum
    # =========================================================================
    employee_category = postgresql.ENUM(
        "aefe_detached",  # AEFE detached (school pays PRRD ~41,863 EUR)
        "aefe_funded",  # AEFE fully funded (zero cost to school)
        "local_teacher",  # Locally recruited teachers
        "administrative",  # Administrative staff
        "support",  # Support staff (ATSEM, maintenance, etc.)
        name="employeecategory",
        schema="efir_budget",
        create_type=False,
    )
    employee_category.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create EmployeeNationality enum (for GOSI calculation)
    # =========================================================================
    employee_nationality = postgresql.ENUM(
        "saudi",  # Saudi national (GOSI: 21.5%)
        "expatriate",  # Expatriate (GOSI: 2%)
        name="employeenationality",
        schema="efir_budget",
        create_type=False,
    )
    employee_nationality.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create ContractType enum
    # =========================================================================
    contract_type = postgresql.ENUM(
        "permanent",  # CDI - Permanent contract
        "fixed_term",  # CDD - Fixed-term contract
        "part_time",  # Part-time contract
        name="contracttype",
        schema="efir_budget",
        create_type=False,
    )
    contract_type.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create TerminationType enum
    # =========================================================================
    termination_type = postgresql.ENUM(
        "resignation",  # Employee resignation (EOS factor applies)
        "termination",  # Employer termination (full EOS)
        "end_of_contract",  # Contract ended (full EOS)
        "retirement",  # Retirement (full EOS)
        name="terminationtype",
        schema="efir_budget",
        create_type=False,
    )
    termination_type.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create AEFEPositionType enum
    # =========================================================================
    aefe_position_type = postgresql.ENUM(
        "detached",  # School pays PRRD contribution
        "funded",  # Fully funded by AEFE (zero school cost)
        name="aefepositiontype",
        schema="efir_budget",
        create_type=False,
    )
    aefe_position_type.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create employees table - Central Employee Registry
    # =========================================================================
    op.create_table(
        "employees",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        # Budget version (for versioned data)
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Employee identification
        sa.Column(
            "employee_code",
            sa.String(20),
            nullable=False,
            index=True,
            comment="Auto-generated employee code (EMP001, EMP002, etc.)",
        ),
        # Personal information
        sa.Column(
            "full_name",
            sa.String(200),
            nullable=False,
            comment="Employee full name",
        ),
        sa.Column(
            "nationality",
            employee_nationality,
            nullable=False,
            comment="Nationality for GOSI calculation (Saudi: 21.5%, Expat: 2%)",
        ),
        # Employment classification
        sa.Column(
            "category",
            employee_category,
            nullable=False,
            index=True,
            comment="Employee category",
        ),
        # Employment details
        sa.Column(
            "hire_date",
            sa.Date,
            nullable=False,
            comment="Hire date (required for EOS calculation)",
        ),
        sa.Column(
            "contract_type",
            contract_type,
            nullable=False,
            server_default="permanent",
            comment="Contract type (permanent, fixed_term, part_time)",
        ),
        sa.Column(
            "contract_end_date",
            sa.Date,
            nullable=True,
            comment="Contract end date (for fixed-term contracts)",
        ),
        # Teaching assignment (for teachers)
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.academic_cycles.id"),
            nullable=True,
            index=True,
            comment="Academic cycle (for teachers)",
        ),
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.subjects.id"),
            nullable=True,
            index=True,
            comment="Primary subject taught (for teachers)",
        ),
        # FTE tracking
        sa.Column(
            "fte",
            sa.Numeric(4, 2),
            nullable=False,
            server_default="1.00",
            comment="Full-Time Equivalent (1.00 = full-time)",
        ),
        # Non-teacher details
        sa.Column(
            "department",
            sa.String(100),
            nullable=True,
            comment="Department (for administrative/support staff)",
        ),
        sa.Column(
            "job_title",
            sa.String(100),
            nullable=True,
            comment="Job title/position",
        ),
        # Salary configuration
        sa.Column(
            "basic_salary_percentage",
            sa.Numeric(4, 2),
            nullable=True,
            server_default="0.50",
            comment="Basic salary as percentage of gross (min 50%)",
        ),
        # Status flags
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="true",
            index=True,
            comment="Whether employee is currently active",
        ),
        sa.Column(
            "is_placeholder",
            sa.Boolean,
            nullable=False,
            server_default="false",
            index=True,
            comment="True = Planned position (from DHG gap), False = Base 100",
        ),
        # Termination details
        sa.Column(
            "termination_date",
            sa.Date,
            nullable=True,
            comment="Date of termination (if applicable)",
        ),
        sa.Column(
            "termination_type",
            termination_type,
            nullable=True,
            comment="Type of termination (affects EOS calculation)",
        ),
        sa.Column("notes", sa.Text, nullable=True, comment="Additional notes"),
        # Audit columns
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.UniqueConstraint(
            "budget_version_id",
            "employee_code",
            name="uk_employees_version_code",
        ),
        sa.CheckConstraint(
            "basic_salary_percentage IS NULL OR basic_salary_percentage >= 0.50",
            name="ck_employees_basic_salary_min_50_percent",
        ),
        sa.Index("ix_employees_category", "category"),
        sa.Index("ix_employees_is_active", "is_active"),
        sa.Index("ix_employees_is_placeholder", "is_placeholder"),
        schema="efir_budget",
        comment="Central employee registry with Base 100 vs Planned distinction",
    )

    # =========================================================================
    # Create employee_salaries table - KSA-compliant salary breakdown
    # =========================================================================
    op.create_table(
        "employee_salaries",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        # Budget version (for versioned data)
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Employee reference
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.employees.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Employee this salary belongs to",
        ),
        # Effective period
        sa.Column(
            "effective_from",
            sa.Date,
            nullable=False,
            comment="Salary effective from date",
        ),
        sa.Column(
            "effective_to",
            sa.Date,
            nullable=True,
            comment="Salary effective to date (NULL = current)",
        ),
        # Salary components (all in SAR)
        sa.Column(
            "basic_salary_sar",
            sa.Numeric(12, 2),
            nullable=False,
            comment="Basic salary (SAR/month) - used for EOS/GOSI",
        ),
        sa.Column(
            "housing_allowance_sar",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="Housing allowance (SAR/month)",
        ),
        sa.Column(
            "transport_allowance_sar",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="Transport allowance (SAR/month)",
        ),
        sa.Column(
            "other_allowances_sar",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="Other allowances (SAR/month)",
        ),
        sa.Column(
            "gross_salary_sar",
            sa.Numeric(12, 2),
            nullable=False,
            comment="Gross salary (SAR/month) = Basic + Housing + Transport + Other",
        ),
        # GOSI rates
        sa.Column(
            "gosi_employer_rate",
            sa.Numeric(5, 4),
            nullable=False,
            server_default="0.1175",
            comment="GOSI employer rate (Saudi: 11.75%, Expat: 2%)",
        ),
        sa.Column(
            "gosi_employee_rate",
            sa.Numeric(5, 4),
            nullable=False,
            server_default="0.0975",
            comment="GOSI employee rate (Saudi: 9.75%, Expat: 0%)",
        ),
        # Calculated GOSI amounts
        sa.Column(
            "gosi_employer_sar",
            sa.Numeric(12, 2),
            nullable=False,
            comment="GOSI employer contribution (SAR/month)",
        ),
        sa.Column(
            "gosi_employee_sar",
            sa.Numeric(12, 2),
            nullable=False,
            comment="GOSI employee deduction (SAR/month)",
        ),
        sa.Column("notes", sa.Text, nullable=True, comment="Salary notes"),
        # Audit columns
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.UniqueConstraint(
            "employee_id",
            "effective_from",
            name="uk_employee_salaries_employee_effective_from",
        ),
        sa.CheckConstraint(
            "gosi_employer_rate >= 0 AND gosi_employer_rate <= 0.20",
            name="ck_employee_salaries_valid_gosi_employer_rate",
        ),
        sa.CheckConstraint(
            "gosi_employee_rate >= 0 AND gosi_employee_rate <= 0.15",
            name="ck_employee_salaries_valid_gosi_employee_rate",
        ),
        schema="efir_budget",
        comment="KSA-compliant salary breakdown (Basic + Housing + Transport + Other)",
    )

    # =========================================================================
    # Create eos_provisions table - End of Service liability tracking
    # =========================================================================
    op.create_table(
        "eos_provisions",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        # Budget version (for versioned data)
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Employee reference
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.employees.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Employee this provision belongs to",
        ),
        # Point in time for calculation
        sa.Column(
            "as_of_date",
            sa.Date,
            nullable=False,
            comment="Date of provision calculation",
        ),
        # Service duration
        sa.Column(
            "years_of_service",
            sa.Integer,
            nullable=False,
            comment="Complete years of service",
        ),
        sa.Column(
            "months_of_service",
            sa.Integer,
            nullable=False,
            comment="Additional months of service (0-11)",
        ),
        # Base salary at calculation time
        sa.Column(
            "base_salary_sar",
            sa.Numeric(12, 2),
            nullable=False,
            comment="Basic salary used for calculation (SAR/month)",
        ),
        # Provision components
        sa.Column(
            "years_1_to_5_amount_sar",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="EOS for years 1-5 (0.5 × salary × years)",
        ),
        sa.Column(
            "years_6_plus_amount_sar",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="EOS for years 6+ (1.0 × salary × years)",
        ),
        # Total provision
        sa.Column(
            "provision_amount_sar",
            sa.Numeric(12, 2),
            nullable=False,
            comment="Total EOS provision (SAR) = Years 1-5 + Years 6+",
        ),
        # Resignation factor (if applicable)
        sa.Column(
            "resignation_factor",
            sa.Numeric(4, 2),
            nullable=True,
            comment="Resignation factor (0.00, 0.33, 0.67, or 1.00)",
        ),
        sa.Column(
            "adjusted_provision_sar",
            sa.Numeric(12, 2),
            nullable=True,
            comment="Adjusted provision after resignation factor",
        ),
        sa.Column("notes", sa.Text, nullable=True, comment="Calculation notes"),
        # Audit columns
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.UniqueConstraint(
            "employee_id",
            "as_of_date",
            name="uk_eos_provisions_employee_date",
        ),
        sa.CheckConstraint(
            "provision_amount_sar >= 0",
            name="ck_eos_provisions_non_negative_amount",
        ),
        schema="efir_budget",
        comment="End of Service (EOS) provision tracking per KSA labor law",
    )

    # =========================================================================
    # Create aefe_positions table - AEFE position allocation
    # =========================================================================
    op.create_table(
        "aefe_positions",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        # Budget version (for versioned data)
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Position identification
        sa.Column(
            "position_number",
            sa.Integer,
            nullable=False,
            comment="Position number (1-28)",
        ),
        sa.Column(
            "position_type",
            aefe_position_type,
            nullable=False,
            comment="Position type (DETACHED = PRRD, FUNDED = zero cost)",
        ),
        # Teaching assignment
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.academic_cycles.id"),
            nullable=True,
            index=True,
            comment="Academic cycle for this position",
        ),
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.subjects.id"),
            nullable=True,
            index=True,
            comment="Subject for this position",
        ),
        # Employee assignment (NULL if vacant)
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.employees.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
            comment="Employee assigned (NULL if vacant)",
        ),
        # PRRD cost (for Detached positions)
        sa.Column(
            "prrd_amount_eur",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="41863.00",
            comment="PRRD contribution (EUR/year)",
        ),
        sa.Column(
            "exchange_rate_eur_sar",
            sa.Numeric(8, 4),
            nullable=False,
            server_default="4.05",
            comment="EUR to SAR exchange rate",
        ),
        sa.Column(
            "prrd_amount_sar",
            sa.Numeric(12, 2),
            nullable=False,
            comment="PRRD contribution in SAR",
        ),
        # Status
        sa.Column(
            "is_filled",
            sa.Boolean,
            nullable=False,
            server_default="false",
            index=True,
            comment="Whether position is filled",
        ),
        sa.Column(
            "academic_year",
            sa.String(20),
            nullable=True,
            comment="Academic year (e.g., '2025-2026')",
        ),
        sa.Column("notes", sa.Text, nullable=True, comment="Position notes"),
        # Audit columns
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.UniqueConstraint(
            "budget_version_id",
            "position_number",
            name="uk_aefe_positions_version_number",
        ),
        schema="efir_budget",
        comment="AEFE position allocation (24 Detached + 4 Funded)",
    )

    # Create unique partial index for employee assignment
    # An employee can only hold one AEFE position per budget version
    op.execute("""
        CREATE UNIQUE INDEX ix_aefe_positions_employee_unique
        ON efir_budget.aefe_positions (budget_version_id, employee_id)
        WHERE employee_id IS NOT NULL;
    """)

    # =========================================================================
    # Create RLS policies for multi-tenant access
    # =========================================================================

    # Enable RLS on all new tables
    op.execute("ALTER TABLE efir_budget.employees ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE efir_budget.employee_salaries ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE efir_budget.eos_provisions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE efir_budget.aefe_positions ENABLE ROW LEVEL SECURITY;")

    # Policy for employees - authenticated users can access all employees in their org's budget versions
    op.execute("""
        CREATE POLICY employees_select_policy ON efir_budget.employees
        FOR SELECT
        USING (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY employees_insert_policy ON efir_budget.employees
        FOR INSERT
        WITH CHECK (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY employees_update_policy ON efir_budget.employees
        FOR UPDATE
        USING (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY employees_delete_policy ON efir_budget.employees
        FOR DELETE
        USING (auth.uid() IS NOT NULL);
    """)

    # Similar policies for employee_salaries
    op.execute("""
        CREATE POLICY employee_salaries_select_policy ON efir_budget.employee_salaries
        FOR SELECT
        USING (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY employee_salaries_insert_policy ON efir_budget.employee_salaries
        FOR INSERT
        WITH CHECK (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY employee_salaries_update_policy ON efir_budget.employee_salaries
        FOR UPDATE
        USING (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY employee_salaries_delete_policy ON efir_budget.employee_salaries
        FOR DELETE
        USING (auth.uid() IS NOT NULL);
    """)

    # Similar policies for eos_provisions
    op.execute("""
        CREATE POLICY eos_provisions_select_policy ON efir_budget.eos_provisions
        FOR SELECT
        USING (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY eos_provisions_insert_policy ON efir_budget.eos_provisions
        FOR INSERT
        WITH CHECK (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY eos_provisions_update_policy ON efir_budget.eos_provisions
        FOR UPDATE
        USING (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY eos_provisions_delete_policy ON efir_budget.eos_provisions
        FOR DELETE
        USING (auth.uid() IS NOT NULL);
    """)

    # Similar policies for aefe_positions
    op.execute("""
        CREATE POLICY aefe_positions_select_policy ON efir_budget.aefe_positions
        FOR SELECT
        USING (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY aefe_positions_insert_policy ON efir_budget.aefe_positions
        FOR INSERT
        WITH CHECK (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY aefe_positions_update_policy ON efir_budget.aefe_positions
        FOR UPDATE
        USING (auth.uid() IS NOT NULL);
    """)

    op.execute("""
        CREATE POLICY aefe_positions_delete_policy ON efir_budget.aefe_positions
        FOR DELETE
        USING (auth.uid() IS NOT NULL);
    """)


def downgrade() -> None:
    """Drop workforce/personnel management tables and enums."""

    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS employees_select_policy ON efir_budget.employees;")
    op.execute("DROP POLICY IF EXISTS employees_insert_policy ON efir_budget.employees;")
    op.execute("DROP POLICY IF EXISTS employees_update_policy ON efir_budget.employees;")
    op.execute("DROP POLICY IF EXISTS employees_delete_policy ON efir_budget.employees;")

    op.execute("DROP POLICY IF EXISTS employee_salaries_select_policy ON efir_budget.employee_salaries;")
    op.execute("DROP POLICY IF EXISTS employee_salaries_insert_policy ON efir_budget.employee_salaries;")
    op.execute("DROP POLICY IF EXISTS employee_salaries_update_policy ON efir_budget.employee_salaries;")
    op.execute("DROP POLICY IF EXISTS employee_salaries_delete_policy ON efir_budget.employee_salaries;")

    op.execute("DROP POLICY IF EXISTS eos_provisions_select_policy ON efir_budget.eos_provisions;")
    op.execute("DROP POLICY IF EXISTS eos_provisions_insert_policy ON efir_budget.eos_provisions;")
    op.execute("DROP POLICY IF EXISTS eos_provisions_update_policy ON efir_budget.eos_provisions;")
    op.execute("DROP POLICY IF EXISTS eos_provisions_delete_policy ON efir_budget.eos_provisions;")

    op.execute("DROP POLICY IF EXISTS aefe_positions_select_policy ON efir_budget.aefe_positions;")
    op.execute("DROP POLICY IF EXISTS aefe_positions_insert_policy ON efir_budget.aefe_positions;")
    op.execute("DROP POLICY IF EXISTS aefe_positions_update_policy ON efir_budget.aefe_positions;")
    op.execute("DROP POLICY IF EXISTS aefe_positions_delete_policy ON efir_budget.aefe_positions;")

    # Drop partial index
    op.execute("DROP INDEX IF EXISTS efir_budget.ix_aefe_positions_employee_unique;")

    # Drop tables in reverse dependency order
    op.drop_table("aefe_positions", schema="efir_budget")
    op.drop_table("eos_provisions", schema="efir_budget")
    op.drop_table("employee_salaries", schema="efir_budget")
    op.drop_table("employees", schema="efir_budget")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS efir_budget.aefepositiontype;")
    op.execute("DROP TYPE IF EXISTS efir_budget.terminationtype;")
    op.execute("DROP TYPE IF EXISTS efir_budget.contracttype;")
    op.execute("DROP TYPE IF EXISTS efir_budget.employeenationality;")
    op.execute("DROP TYPE IF EXISTS efir_budget.employeecategory;")
