"""Fix critical issues: Add soft delete, budget version rules, Planning constraints

Revision ID: 004_fix_critical_issues
Revises: 003_consolidation_layer
Create Date: 2025-12-01 00:45:00

This migration fixes critical issues identified in Phase 0-3 review:

CRITICAL FIXES:
- Audit trail column names already fixed in previous migrations (created_by → created_by_id)
- Audit fields made nullable (nullable=True, ondelete='SET NULL')

HIGH PRIORITY FIXES:
- Add deleted_at columns to ALL tables (soft delete support)
- Add budget version business rules:
  * Unique partial index: only one 'working' per fiscal year
  * Check constraint: forecast versions must have parent
  * Trigger: prevent edits to approved versions
- Add uniqueness constraints to Planning Layer tables
- Add version-lock trigger

This is a non-destructive migration - adds columns and constraints only.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_fix_critical_issues"
down_revision: Union[str, None] = "003_consolidation_layer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply critical fixes."""

    # ========================================================================
    # HIGH-1: Add deleted_at columns to ALL tables
    # ========================================================================

    # Configuration Layer tables (13 tables)
    config_tables = [
        'system_configs',
        'budget_versions',
        'academic_cycles',
        'academic_levels',
        'class_size_params',
        'subjects',
        'subject_hours_matrix',
        'teacher_categories',
        'teacher_cost_params',
        'fee_categories',
        'nationality_types',
        'fee_structure',
        'timetable_constraints',
    ]

    for table in config_tables:
        op.add_column(
            table,
            sa.Column(
                'deleted_at',
                sa.DateTime(timezone=True),
                nullable=True,
                comment='Soft delete timestamp (NULL if active)',
            ),
            schema='efir_budget'
        )

    # Planning Layer tables (9 tables)
    planning_tables = [
        'enrollment_plans',
        'class_structures',
        'dhg_subject_hours',
        'dhg_teacher_requirements',
        'teacher_allocations',
        'revenue_plans',
        'personnel_cost_plans',
        'operating_cost_plans',
        'capex_plans',
    ]

    for table in planning_tables:
        op.add_column(
            table,
            sa.Column(
                'deleted_at',
                sa.DateTime(timezone=True),
                nullable=True,
                comment='Soft delete timestamp (NULL if active)',
            ),
            schema='efir_budget'
        )

    # Consolidation Layer already has deleted_at (no changes needed)

    # ========================================================================
    # HIGH-2: Add Budget Version Business Rules
    # ========================================================================

    # Rule 1: Only one 'working' version per fiscal year
    # Create unique partial index
    op.execute("""
        CREATE UNIQUE INDEX idx_unique_working_per_year
        ON efir_budget.budget_versions (fiscal_year)
        WHERE status = 'working' AND deleted_at IS NULL;
    """)

    # Rule 2: Forecast versions must have parent_version_id
    op.create_check_constraint(
        'ck_forecast_has_parent',
        'budget_versions',
        "(status != 'forecast') OR (parent_version_id IS NOT NULL)",
        schema='efir_budget'
    )

    # Rule 3: Create version-lock trigger to prevent edits to approved versions
    op.execute("""
        CREATE OR REPLACE FUNCTION efir_budget.prevent_approved_version_edit()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Prevent ANY changes to approved versions (except status changes to superseded)
            IF OLD.status = 'approved' THEN
                -- Allow status change from approved to superseded
                IF NEW.status = 'superseded' AND
                   OLD.name = NEW.name AND
                   OLD.fiscal_year = NEW.fiscal_year AND
                   OLD.academic_year = NEW.academic_year THEN
                    RETURN NEW;
                END IF;

                -- Block all other changes
                RAISE EXCEPTION
                    'Cannot modify approved budget version %. To make changes, create a new version or change status to superseded first.',
                    OLD.name;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER budget_version_lock
        BEFORE UPDATE ON efir_budget.budget_versions
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.prevent_approved_version_edit();
    """)

    # ========================================================================
    # HIGH-3: Add Uniqueness Constraints to Planning Layer Tables
    # ========================================================================

    # teacher_allocations: Prevent duplicate allocations
    op.create_unique_constraint(
        'uk_allocation_version_subject_cycle_category',
        'teacher_allocations',
        ['budget_version_id', 'subject_id', 'cycle_id', 'category_id'],
        schema='efir_budget'
    )

    # class_structures: Already has unique constraint (version + level) ✓

    # revenue_plans: Prevent duplicate revenue entries
    op.create_unique_constraint(
        'uk_revenue_version_account',
        'revenue_plans',
        ['budget_version_id', 'account_code'],
        schema='efir_budget'
    )

    # personnel_cost_plans: Prevent duplicate personnel cost entries
    op.create_unique_constraint(
        'uk_personnel_cost_version_account_cycle_category',
        'personnel_cost_plans',
        ['budget_version_id', 'account_code', 'cycle_id', 'category_id'],
        schema='efir_budget'
    )

    # operating_cost_plans: Prevent duplicate operating cost entries
    op.create_unique_constraint(
        'uk_operating_cost_version_account',
        'operating_cost_plans',
        ['budget_version_id', 'account_code'],
        schema='efir_budget'
    )

    # capex_plans: Prevent duplicate CapEx entries
    op.create_unique_constraint(
        'uk_capex_version_account_description',
        'capex_plans',
        ['budget_version_id', 'account_code', 'description'],
        schema='efir_budget'
    )


def downgrade() -> None:
    """Revert critical fixes."""

    # ========================================================================
    # Remove Planning Layer Uniqueness Constraints
    # ========================================================================

    op.drop_constraint('uk_capex_version_account_description', 'capex_plans', schema='efir_budget')
    op.drop_constraint('uk_operating_cost_version_account', 'operating_cost_plans', schema='efir_budget')
    op.drop_constraint('uk_personnel_cost_version_account_cycle_category', 'personnel_cost_plans', schema='efir_budget')
    op.drop_constraint('uk_revenue_version_account', 'revenue_plans', schema='efir_budget')
    op.drop_constraint('uk_allocation_version_subject_cycle_category', 'teacher_allocations', schema='efir_budget')

    # ========================================================================
    # Remove Budget Version Business Rules
    # ========================================================================

    # Drop version-lock trigger
    op.execute("DROP TRIGGER IF EXISTS budget_version_lock ON efir_budget.budget_versions;")
    op.execute("DROP FUNCTION IF EXISTS efir_budget.prevent_approved_version_edit();")

    # Drop check constraint for forecast parent
    op.drop_constraint('ck_forecast_has_parent', 'budget_versions', schema='efir_budget')

    # Drop unique partial index for working versions
    op.execute("DROP INDEX IF EXISTS efir_budget.idx_unique_working_per_year;")

    # ========================================================================
    # Remove deleted_at columns
    # ========================================================================

    # Planning Layer tables
    planning_tables = [
        'enrollment_plans', 'class_structures', 'dhg_subject_hours',
        'dhg_teacher_requirements', 'teacher_allocations', 'revenue_plans',
        'personnel_cost_plans', 'operating_cost_plans', 'capex_plans',
    ]

    for table in planning_tables:
        op.drop_column(table, 'deleted_at', schema='efir_budget')

    # Configuration Layer tables
    config_tables = [
        'system_configs', 'budget_versions', 'academic_cycles',
        'academic_levels', 'class_size_params', 'subjects',
        'subject_hours_matrix', 'teacher_categories', 'teacher_cost_params',
        'fee_categories', 'nationality_types', 'fee_structure',
        'timetable_constraints',
    ]

    for table in config_tables:
        op.drop_column(table, 'deleted_at', schema='efir_budget')
