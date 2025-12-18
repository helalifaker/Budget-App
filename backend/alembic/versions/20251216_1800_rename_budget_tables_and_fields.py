"""Rename budget tables and fields to version terminology

Revision ID: 032_rename_budget_terminology
Revises: 031_remove_school_period
Create Date: 2025-12-16 18:00:00.000000

This migration renames all "budget" references to "version" terminology:
- Tables: insights_budget_vs_actual → insights_version_vs_actual
- Columns: budget_amount_sar → version_amount_sar (in insights_version_vs_actual)
- Indexes: All budget-related indexes renamed
- RLS Policies: Recreated with new names
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "032_rename_budget_terminology"
down_revision = "031_remove_school_period"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Rename all budget-related database objects to use version terminology.

    Note: finance_consolidations is already correct (no 'budget' in name from Phase 3B).
    Only insights_budget_vs_actual needs renaming.
    """

    # ========================================
    # STEP 1: Rename Tables
    # ========================================

    # Rename insights_budget_vs_actual → insights_version_vs_actual
    op.execute("""
        ALTER TABLE efir_budget.insights_budget_vs_actual
        RENAME TO insights_version_vs_actual;
    """)

    # ========================================
    # STEP 2: Rename Columns
    # ========================================

    # Rename budget_amount_sar → version_amount_sar in insights_version_vs_actual
    op.execute("""
        ALTER TABLE efir_budget.insights_version_vs_actual
        RENAME COLUMN budget_amount_sar TO version_amount_sar;
    """)

    # Note: insights_actual_data doesn't have budget_amount_sar column (it has amount_sar)
    # No column rename needed for that table

    # ========================================
    # STEP 3: Rename Indexes
    # ========================================

    # insights_version_vs_actual indexes
    op.execute("""
        ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_budget_vs_actual_budget_version_id
        RENAME TO ix_efir_budget_version_vs_actual_version_id;
    """)

    op.execute("""
        ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_budget_vs_actual_account_code
        RENAME TO ix_efir_budget_version_vs_actual_account_code;
    """)

    op.execute("""
        ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_budget_vs_actual_period
        RENAME TO ix_efir_budget_version_vs_actual_period;
    """)

    op.execute("""
        ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_budget_vs_actual_variance_status
        RENAME TO ix_efir_budget_version_vs_actual_variance_status;
    """)

    op.execute("""
        ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_budget_vs_actual_is_material
        RENAME TO ix_efir_budget_version_vs_actual_is_material;
    """)

    # ========================================
    # STEP 4: Update RLS Policies (if they exist)
    # ========================================

    # Drop old RLS policies for insights_budget_vs_actual (now insights_version_vs_actual)
    op.execute("""
        DROP POLICY IF EXISTS "insights_budget_vs_actual_viewer_select"
        ON efir_budget.insights_version_vs_actual;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "insights_budget_vs_actual_editor_insert"
        ON efir_budget.insights_version_vs_actual;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "insights_budget_vs_actual_editor_update"
        ON efir_budget.insights_version_vs_actual;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "insights_budget_vs_actual_editor_delete"
        ON efir_budget.insights_version_vs_actual;
    """)

    # Create new RLS policies for insights_version_vs_actual
    # Note: Using user_organizations table (not admin_user_organizations)
    op.execute("""
        CREATE POLICY "insights_version_vs_actual_viewer_select"
        ON efir_budget.insights_version_vs_actual
        FOR SELECT
        USING (
            (SELECT auth.uid()) IN (
                SELECT user_id
                FROM efir_budget.user_organizations uo
                JOIN efir_budget.settings_versions sv ON sv.organization_id = uo.organization_id
                WHERE sv.id = insights_version_vs_actual.version_id
            )
        );
    """)

    op.execute("""
        CREATE POLICY "insights_version_vs_actual_editor_insert"
        ON efir_budget.insights_version_vs_actual
        FOR INSERT
        WITH CHECK (
            (SELECT auth.uid()) IN (
                SELECT user_id
                FROM efir_budget.user_organizations uo
                JOIN efir_budget.settings_versions sv ON sv.organization_id = uo.organization_id
                WHERE sv.id = insights_version_vs_actual.version_id
                AND uo.role IN ('Admin', 'Finance Director', 'Editor')
            )
        );
    """)

    op.execute("""
        CREATE POLICY "insights_version_vs_actual_editor_update"
        ON efir_budget.insights_version_vs_actual
        FOR UPDATE
        USING (
            (SELECT auth.uid()) IN (
                SELECT user_id
                FROM efir_budget.user_organizations uo
                JOIN efir_budget.settings_versions sv ON sv.organization_id = uo.organization_id
                WHERE sv.id = insights_version_vs_actual.version_id
                AND uo.role IN ('Admin', 'Finance Director', 'Editor')
            )
        );
    """)

    op.execute("""
        CREATE POLICY "insights_version_vs_actual_editor_delete"
        ON efir_budget.insights_version_vs_actual
        FOR DELETE
        USING (
            (SELECT auth.uid()) IN (
                SELECT user_id
                FROM efir_budget.user_organizations uo
                JOIN efir_budget.settings_versions sv ON sv.organization_id = uo.organization_id
                WHERE sv.id = insights_version_vs_actual.version_id
                AND uo.role IN ('Admin', 'Finance Director')
            )
        );
    """)

    # ========================================
    # Validation (logging only - not blocking)
    # ========================================
    print("Migration 032_rename_budget_terminology completed successfully:")
    print("  ✓ Renamed insights_budget_vs_actual → insights_version_vs_actual")
    print("  ✓ Renamed budget_amount_sar → version_amount_sar")
    print("  ✓ Renamed 5 indexes")
    print("  ✓ Recreated 4 RLS policies")


def downgrade() -> None:
    """
    Rollback: Revert all naming back to budget terminology.
    """

    # ========================================
    # STEP 1: Revert RLS Policies
    # ========================================

    # Drop new policies
    op.execute("DROP POLICY IF EXISTS insights_version_vs_actual_viewer_select ON efir_budget.insights_version_vs_actual;")
    op.execute("DROP POLICY IF EXISTS insights_version_vs_actual_editor_insert ON efir_budget.insights_version_vs_actual;")
    op.execute("DROP POLICY IF EXISTS insights_version_vs_actual_editor_update ON efir_budget.insights_version_vs_actual;")
    op.execute("DROP POLICY IF EXISTS insights_version_vs_actual_editor_delete ON efir_budget.insights_version_vs_actual;")

    # Recreate old policies
    op.execute("""
        CREATE POLICY "insights_budget_vs_actual_viewer_select"
        ON efir_budget.insights_version_vs_actual
        FOR SELECT
        USING (
            (SELECT auth.uid()) IN (
                SELECT user_id
                FROM efir_budget.user_organizations uo
                JOIN efir_budget.settings_versions sv ON sv.organization_id = uo.organization_id
                WHERE sv.id = insights_version_vs_actual.version_id
            )
        );
    """)

    op.execute("""
        CREATE POLICY "insights_budget_vs_actual_editor_insert"
        ON efir_budget.insights_version_vs_actual
        FOR INSERT
        WITH CHECK (
            (SELECT auth.uid()) IN (
                SELECT user_id
                FROM efir_budget.user_organizations uo
                JOIN efir_budget.settings_versions sv ON sv.organization_id = uo.organization_id
                WHERE sv.id = insights_version_vs_actual.version_id
                AND uo.role IN ('Admin', 'Finance Director', 'Editor')
            )
        );
    """)

    op.execute("""
        CREATE POLICY "insights_budget_vs_actual_editor_update"
        ON efir_budget.insights_version_vs_actual
        FOR UPDATE
        USING (
            (SELECT auth.uid()) IN (
                SELECT user_id
                FROM efir_budget.user_organizations uo
                JOIN efir_budget.settings_versions sv ON sv.organization_id = uo.organization_id
                WHERE sv.id = insights_version_vs_actual.version_id
                AND uo.role IN ('Admin', 'Finance Director', 'Editor')
            )
        );
    """)

    op.execute("""
        CREATE POLICY "insights_budget_vs_actual_editor_delete"
        ON efir_budget.insights_version_vs_actual
        FOR DELETE
        USING (
            (SELECT auth.uid()) IN (
                SELECT user_id
                FROM efir_budget.user_organizations uo
                JOIN efir_budget.settings_versions sv ON sv.organization_id = uo.organization_id
                WHERE sv.id = insights_version_vs_actual.version_id
                AND uo.role IN ('Admin', 'Finance Director')
            )
        );
    """)

    # ========================================
    # STEP 2: Revert Index Renames
    # ========================================

    op.execute("ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_version_vs_actual_version_id RENAME TO ix_efir_budget_budget_vs_actual_budget_version_id;")
    op.execute("ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_version_vs_actual_account_code RENAME TO ix_efir_budget_budget_vs_actual_account_code;")
    op.execute("ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_version_vs_actual_period RENAME TO ix_efir_budget_budget_vs_actual_period;")
    op.execute("ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_version_vs_actual_variance_status RENAME TO ix_efir_budget_budget_vs_actual_variance_status;")
    op.execute("ALTER INDEX IF EXISTS efir_budget.ix_efir_budget_version_vs_actual_is_material RENAME TO ix_efir_budget_budget_vs_actual_is_material;")

    # ========================================
    # STEP 3: Revert Column Renames
    # ========================================

    op.execute("ALTER TABLE efir_budget.insights_version_vs_actual RENAME COLUMN version_amount_sar TO budget_amount_sar;")

    # ========================================
    # STEP 4: Revert Table Renames
    # ========================================

    op.execute("ALTER TABLE efir_budget.insights_version_vs_actual RENAME TO insights_budget_vs_actual;")

    print("Rollback 032_rename_budget_terminology completed successfully - reverted to budget terminology")
