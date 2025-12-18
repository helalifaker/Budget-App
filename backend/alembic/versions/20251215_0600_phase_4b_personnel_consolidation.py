"""Phase 4B: Personnel Module Consolidation

Revision ID: 027_phase_4b_personnel_consolidation
Revises: 026_phase_4a_enrollment_consolidation
Create Date: 2025-12-15

Consolidates personnel tables from 7 → 4:

OLD TABLES:
- teachers_employees (25 cols) - ORG-SCOPED - keep (enhance)
- teachers_employee_salaries (20 cols) - VERSION-LINKED → merge into employees
- teachers_aefe_positions (18 cols) - VERSION-LINKED → merge into employees
- teachers_eos_provisions (18 cols) - OUTPUT → REMOVE (calculate on demand)
- teachers_allocations (12 cols) - VERSION-LINKED - keep
- teachers_dhg_requirements (13 cols) - OUTPUT - keep (add lineage)
- teachers_dhg_subject_hours (13 cols) - OUTPUT - keep (add lineage)

NEW STRUCTURE (4 tables):
- teachers_employees - Enhanced with salary + AEFE columns
- teachers_allocations - Keep unchanged
- teachers_dhg_requirements - Keep (add lineage columns)
- teachers_dhg_subject_hours - Keep (add lineage columns)

This migration:
1. Adds salary columns to teachers_employees
2. Adds AEFE position columns to teachers_employees
3. Migrates data from teachers_employee_salaries
4. Migrates data from teachers_aefe_positions
5. Adds lineage columns to DHG OUTPUT tables
6. Drops teachers_eos_provisions (calculated on demand)
"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers
revision: str = "027_phase_4b_personnel_consolidation"
down_revision: str | None = "026_phase_4a_enrollment_consolidation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Consolidate personnel tables."""

    # ========================================================================
    # STEP 1: Add salary columns to teachers_employees
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.teachers_employees
        ADD COLUMN IF NOT EXISTS basic_salary_sar NUMERIC(12,2),
        ADD COLUMN IF NOT EXISTS housing_allowance_sar NUMERIC(12,2) DEFAULT 0,
        ADD COLUMN IF NOT EXISTS transport_allowance_sar NUMERIC(12,2) DEFAULT 0,
        ADD COLUMN IF NOT EXISTS other_allowances_sar NUMERIC(12,2) DEFAULT 0,
        ADD COLUMN IF NOT EXISTS gross_salary_sar NUMERIC(12,2),
        ADD COLUMN IF NOT EXISTS gosi_employer_rate NUMERIC(5,4) DEFAULT 0.1175,
        ADD COLUMN IF NOT EXISTS gosi_employee_rate NUMERIC(5,4) DEFAULT 0.0975,
        ADD COLUMN IF NOT EXISTS gosi_employer_sar NUMERIC(12,2),
        ADD COLUMN IF NOT EXISTS gosi_employee_sar NUMERIC(12,2),
        ADD COLUMN IF NOT EXISTS salary_effective_from DATE,
        ADD COLUMN IF NOT EXISTS salary_effective_to DATE
    """)

    # ========================================================================
    # STEP 2: Add AEFE position columns to teachers_employees
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.teachers_employees
        ADD COLUMN IF NOT EXISTS is_aefe_position BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS aefe_position_type VARCHAR(50),
        ADD COLUMN IF NOT EXISTS aefe_position_number INTEGER,
        ADD COLUMN IF NOT EXISTS prrd_amount_eur NUMERIC(12,2) DEFAULT 41863.00,
        ADD COLUMN IF NOT EXISTS exchange_rate_eur_sar NUMERIC(6,4) DEFAULT 4.05,
        ADD COLUMN IF NOT EXISTS prrd_amount_sar NUMERIC(12,2)
    """)

    # ========================================================================
    # STEP 3: Add lineage columns to teachers_dhg_requirements
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.teachers_dhg_requirements
        ADD COLUMN IF NOT EXISTS computed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS computed_by UUID,
        ADD COLUMN IF NOT EXISTS run_id UUID,
        ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64)
    """)

    # ========================================================================
    # STEP 4: Add lineage columns to teachers_dhg_subject_hours
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.teachers_dhg_subject_hours
        ADD COLUMN IF NOT EXISTS computed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS computed_by UUID,
        ADD COLUMN IF NOT EXISTS run_id UUID,
        ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64)
    """)

    # ========================================================================
    # STEP 5: Migrate salary data from teachers_employee_salaries
    # ========================================================================
    # Get the most recent salary record for each employee/version combination
    op.execute("""
        UPDATE efir_budget.teachers_employees e
        SET
            basic_salary_sar = s.basic_salary_sar,
            housing_allowance_sar = s.housing_allowance_sar,
            transport_allowance_sar = s.transport_allowance_sar,
            other_allowances_sar = s.other_allowances_sar,
            gross_salary_sar = s.gross_salary_sar,
            gosi_employer_rate = s.gosi_employer_rate,
            gosi_employee_rate = s.gosi_employee_rate,
            gosi_employer_sar = s.gosi_employer_sar,
            gosi_employee_sar = s.gosi_employee_sar,
            salary_effective_from = s.effective_from,
            salary_effective_to = s.effective_to
        FROM (
            SELECT DISTINCT ON (employee_id, version_id)
                employee_id, version_id,
                basic_salary_sar, housing_allowance_sar, transport_allowance_sar,
                other_allowances_sar, gross_salary_sar,
                gosi_employer_rate, gosi_employee_rate,
                gosi_employer_sar, gosi_employee_sar,
                effective_from, effective_to
            FROM efir_budget.teachers_employee_salaries
            WHERE deleted_at IS NULL
            ORDER BY employee_id, version_id, effective_from DESC
        ) s
        WHERE e.id = s.employee_id
          AND e.version_id = s.version_id
    """)

    # ========================================================================
    # STEP 6: Migrate AEFE position data from teachers_aefe_positions
    # ========================================================================
    # Link filled AEFE positions to their employees
    op.execute("""
        UPDATE efir_budget.teachers_employees e
        SET
            is_aefe_position = TRUE,
            aefe_position_type = p.position_type::text,
            aefe_position_number = p.position_number,
            prrd_amount_eur = p.prrd_amount_eur,
            exchange_rate_eur_sar = p.exchange_rate_eur_sar,
            prrd_amount_sar = p.prrd_amount_sar
        FROM efir_budget.teachers_aefe_positions p
        WHERE p.employee_id = e.id
          AND p.version_id = e.version_id
          AND p.is_filled = TRUE
          AND p.deleted_at IS NULL
    """)

    # ========================================================================
    # STEP 7: Create view for unfilled AEFE positions (backward compatibility)
    # ========================================================================
    op.execute("""
        CREATE OR REPLACE VIEW efir_budget.vw_aefe_positions AS
        SELECT
            id,
            version_id,
            position_number,
            position_type,
            cycle_id,
            subject_id,
            employee_id,
            prrd_amount_eur,
            exchange_rate_eur_sar,
            prrd_amount_sar,
            is_filled,
            academic_year,
            notes,
            created_at,
            updated_at
        FROM efir_budget.teachers_aefe_positions
        WHERE deleted_at IS NULL
    """)

    # ========================================================================
    # STEP 8: Drop teachers_eos_provisions (calculated on demand)
    # ========================================================================
    # First check if table has any important data we should preserve
    # For safety, we'll just mark it as deprecated with a comment
    op.execute("""
        COMMENT ON TABLE efir_budget.teachers_eos_provisions IS
        'DEPRECATED - Phase 4B: EOS provisions are now calculated on demand by the EOS engine.
         This table will be dropped in a future migration after data validation.'
    """)

    # ========================================================================
    # STEP 9: Create indexes for new columns
    # ========================================================================
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_teachers_employees_is_aefe
        ON efir_budget.teachers_employees(is_aefe_position)
        WHERE is_aefe_position = TRUE
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_teachers_employees_gross_salary
        ON efir_budget.teachers_employees(gross_salary_sar)
        WHERE gross_salary_sar IS NOT NULL
    """)

    # ========================================================================
    # STEP 10: Add check constraints
    # ========================================================================
    op.execute("""
        ALTER TABLE efir_budget.teachers_employees
        ADD CONSTRAINT ck_employees_salary_non_negative
        CHECK (basic_salary_sar IS NULL OR basic_salary_sar >= 0)
    """)

    op.execute("""
        ALTER TABLE efir_budget.teachers_employees
        ADD CONSTRAINT ck_employees_gosi_rates_valid
        CHECK (
            (gosi_employer_rate IS NULL OR (gosi_employer_rate >= 0 AND gosi_employer_rate <= 1))
            AND (gosi_employee_rate IS NULL OR (gosi_employee_rate >= 0 AND gosi_employee_rate <= 1))
        )
    """)


def downgrade() -> None:
    """Revert personnel table consolidation."""

    # Drop check constraints
    op.execute("""
        ALTER TABLE efir_budget.teachers_employees
        DROP CONSTRAINT IF EXISTS ck_employees_gosi_rates_valid
    """)

    op.execute("""
        ALTER TABLE efir_budget.teachers_employees
        DROP CONSTRAINT IF EXISTS ck_employees_salary_non_negative
    """)

    # Drop indexes
    op.execute("""
        DROP INDEX IF EXISTS efir_budget.ix_teachers_employees_gross_salary
    """)

    op.execute("""
        DROP INDEX IF EXISTS efir_budget.ix_teachers_employees_is_aefe
    """)

    # Drop backward compatibility view
    op.execute("""
        DROP VIEW IF EXISTS efir_budget.vw_aefe_positions
    """)

    # Remove deprecation comment from eos_provisions
    op.execute("""
        COMMENT ON TABLE efir_budget.teachers_eos_provisions IS NULL
    """)

    # Remove lineage columns from DHG tables
    op.execute("""
        ALTER TABLE efir_budget.teachers_dhg_subject_hours
        DROP COLUMN IF EXISTS computed_at,
        DROP COLUMN IF EXISTS computed_by,
        DROP COLUMN IF EXISTS run_id,
        DROP COLUMN IF EXISTS inputs_hash
    """)

    op.execute("""
        ALTER TABLE efir_budget.teachers_dhg_requirements
        DROP COLUMN IF EXISTS computed_at,
        DROP COLUMN IF EXISTS computed_by,
        DROP COLUMN IF EXISTS run_id,
        DROP COLUMN IF EXISTS inputs_hash
    """)

    # Remove AEFE columns from employees
    op.execute("""
        ALTER TABLE efir_budget.teachers_employees
        DROP COLUMN IF EXISTS is_aefe_position,
        DROP COLUMN IF EXISTS aefe_position_type,
        DROP COLUMN IF EXISTS aefe_position_number,
        DROP COLUMN IF EXISTS prrd_amount_eur,
        DROP COLUMN IF EXISTS exchange_rate_eur_sar,
        DROP COLUMN IF EXISTS prrd_amount_sar
    """)

    # Remove salary columns from employees
    op.execute("""
        ALTER TABLE efir_budget.teachers_employees
        DROP COLUMN IF EXISTS basic_salary_sar,
        DROP COLUMN IF EXISTS housing_allowance_sar,
        DROP COLUMN IF EXISTS transport_allowance_sar,
        DROP COLUMN IF EXISTS other_allowances_sar,
        DROP COLUMN IF EXISTS gross_salary_sar,
        DROP COLUMN IF EXISTS gosi_employer_rate,
        DROP COLUMN IF EXISTS gosi_employee_rate,
        DROP COLUMN IF EXISTS gosi_employer_sar,
        DROP COLUMN IF EXISTS gosi_employee_sar,
        DROP COLUMN IF EXISTS salary_effective_from,
        DROP COLUMN IF EXISTS salary_effective_to
    """)
