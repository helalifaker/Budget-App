"""Add RLS policies to settings_class_size_params table.

Revision ID: 030_rls_class_size_params
Revises: 029_add_school_period
Create Date: 2025-12-16 01:00:00.000000

Adds Row Level Security (RLS) policies to the settings_class_size_params table.

Organization access is determined via the version_id FK -> settings_versions.organization_id.

Policies:
- SELECT: All authenticated users in the organization
- INSERT/UPDATE: Editors and admins only
- DELETE: Admins only
- Service role bypass for backend operations

Performance Notes:
- Uses (SELECT auth.uid()) instead of auth.uid() for initplan optimization
- Subqueries are evaluated once per query instead of once per row
"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers
revision: str = "030_rls_class_size_params"
down_revision: str | None = "029_add_school_period"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add RLS policies to settings_class_size_params."""

    # =========================================================================
    # STEP 1: Enable RLS on the table
    # =========================================================================
    op.execute("""
        ALTER TABLE efir_budget.settings_class_size_params
        ENABLE ROW LEVEL SECURITY;
    """)

    # Force RLS for table owner too (important for security)
    op.execute("""
        ALTER TABLE efir_budget.settings_class_size_params
        FORCE ROW LEVEL SECURITY;
    """)

    # =========================================================================
    # STEP 2: SELECT policy - All authenticated users in the organization
    # =========================================================================
    op.execute("""
        CREATE POLICY "class_size_params_select_own_org"
        ON efir_budget.settings_class_size_params
        FOR SELECT
        TO authenticated
        USING (
            version_id IN (
                SELECT sv.id
                FROM efir_budget.settings_versions sv
                WHERE sv.organization_id IN (
                    SELECT uo.organization_id
                    FROM efir_budget.user_organizations uo
                    WHERE uo.user_id = (SELECT auth.uid())
                )
            )
        );
    """)

    # =========================================================================
    # STEP 3: INSERT policy - Editors and admins only
    # =========================================================================
    op.execute("""
        CREATE POLICY "class_size_params_insert_editors"
        ON efir_budget.settings_class_size_params
        FOR INSERT
        TO authenticated
        WITH CHECK (
            version_id IN (
                SELECT sv.id
                FROM efir_budget.settings_versions sv
                WHERE sv.organization_id IN (
                    SELECT uo.organization_id
                    FROM efir_budget.user_organizations uo
                    WHERE uo.user_id = (SELECT auth.uid())
                    AND uo.role IN ('admin', 'editor')
                )
            )
        );
    """)

    # =========================================================================
    # STEP 4: UPDATE policy - Editors and admins only
    # =========================================================================
    op.execute("""
        CREATE POLICY "class_size_params_update_editors"
        ON efir_budget.settings_class_size_params
        FOR UPDATE
        TO authenticated
        USING (
            version_id IN (
                SELECT sv.id
                FROM efir_budget.settings_versions sv
                WHERE sv.organization_id IN (
                    SELECT uo.organization_id
                    FROM efir_budget.user_organizations uo
                    WHERE uo.user_id = (SELECT auth.uid())
                    AND uo.role IN ('admin', 'editor')
                )
            )
        )
        WITH CHECK (
            version_id IN (
                SELECT sv.id
                FROM efir_budget.settings_versions sv
                WHERE sv.organization_id IN (
                    SELECT uo.organization_id
                    FROM efir_budget.user_organizations uo
                    WHERE uo.user_id = (SELECT auth.uid())
                    AND uo.role IN ('admin', 'editor')
                )
            )
        );
    """)

    # =========================================================================
    # STEP 5: DELETE policy - Admins only
    # =========================================================================
    op.execute("""
        CREATE POLICY "class_size_params_delete_admins"
        ON efir_budget.settings_class_size_params
        FOR DELETE
        TO authenticated
        USING (
            version_id IN (
                SELECT sv.id
                FROM efir_budget.settings_versions sv
                WHERE sv.organization_id IN (
                    SELECT uo.organization_id
                    FROM efir_budget.user_organizations uo
                    WHERE uo.user_id = (SELECT auth.uid())
                    AND uo.role = 'admin'
                )
            )
        );
    """)

    # =========================================================================
    # STEP 6: Service role bypass for backend operations
    # =========================================================================
    op.execute("""
        CREATE POLICY "class_size_params_service_role_all"
        ON efir_budget.settings_class_size_params
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
    """)


def downgrade() -> None:
    """Remove RLS policies from settings_class_size_params."""

    # Drop policies in reverse order
    op.execute("""
        DROP POLICY IF EXISTS "class_size_params_service_role_all"
        ON efir_budget.settings_class_size_params;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "class_size_params_delete_admins"
        ON efir_budget.settings_class_size_params;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "class_size_params_update_editors"
        ON efir_budget.settings_class_size_params;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "class_size_params_insert_editors"
        ON efir_budget.settings_class_size_params;
    """)

    op.execute("""
        DROP POLICY IF EXISTS "class_size_params_select_own_org"
        ON efir_budget.settings_class_size_params;
    """)

    # Disable RLS
    op.execute("""
        ALTER TABLE efir_budget.settings_class_size_params
        DISABLE ROW LEVEL SECURITY;
    """)
