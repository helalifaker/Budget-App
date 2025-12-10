"""Fix function security (search_path) and RLS performance (auth initplan).

Revision ID: 016_fix_security_rls
Revises: 015_workforce_personnel
Create Date: 2025-12-10 12:00:00.000000

Security Fixes:
--------------
- Add SET search_path = '' to all 3 functions in efir_budget schema
- This prevents SQL injection via search_path manipulation

Performance Fixes:
-----------------
- Wrap auth.uid() calls in RLS policies with (SELECT auth.uid())
- This evaluates auth.uid() once per query instead of once per row
- Affects: planning_cells, cell_changes, cell_comments tables

Functions Fixed:
---------------
1. efir_budget.update_updated_at - Trigger for auto-updating timestamps
2. efir_budget.prevent_approved_version_edit - Prevents editing approved budgets
3. efir_budget.validate_class_structure_size - Validates class size constraints

RLS Policies Fixed:
------------------
1. planning_cells_authenticated_access
2. cell_changes_authenticated_access
3. cell_comments_authenticated_access

Note: This migration only affects the efir_budget schema.
      No changes are made to the public schema.
"""

from alembic import op

revision = "016_fix_security_rls"
down_revision = "015_workforce_personnel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # FUNCTION FIXES (Security - search_path)
    # =========================================================================

    # 1. Fix update_updated_at - add SET search_path = ''
    op.execute("""
        CREATE OR REPLACE FUNCTION efir_budget.update_updated_at()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SET search_path = ''
        AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;
    """)

    # 2. Fix prevent_approved_version_edit - add SET search_path = ''
    op.execute("""
        CREATE OR REPLACE FUNCTION efir_budget.prevent_approved_version_edit()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SET search_path = ''
        AS $$
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
        $$;
    """)

    # 3. Fix validate_class_structure_size - add SET search_path = ''
    op.execute("""
        CREATE OR REPLACE FUNCTION efir_budget.validate_class_structure_size()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SET search_path = ''
        AS $$
        DECLARE
            v_min INTEGER;
            v_max INTEGER;
        BEGIN
            -- Find applicable class size params: prefer level-specific, else cycle-level
            SELECT csp.min_class_size, csp.max_class_size
              INTO v_min, v_max
            FROM efir_budget.class_size_params csp
            JOIN efir_budget.academic_levels al ON al.id = NEW.level_id
            WHERE csp.budget_version_id = NEW.budget_version_id
              AND (
                    csp.level_id = NEW.level_id
                 OR (csp.level_id IS NULL AND csp.cycle_id = al.cycle_id)
              )
            ORDER BY CASE WHEN csp.level_id = NEW.level_id THEN 0 ELSE 1 END
            LIMIT 1;

            IF v_min IS NULL OR v_max IS NULL THEN
                RAISE EXCEPTION
                    'No class_size_params defined for level % in version %',
                    NEW.level_id, NEW.budget_version_id;
            END IF;

            IF NEW.avg_class_size < v_min OR NEW.avg_class_size > v_max THEN
                RAISE EXCEPTION
                    'avg_class_size % outside [%, %] for level % version %',
                    NEW.avg_class_size, v_min, v_max, NEW.level_id, NEW.budget_version_id;
            END IF;

            RETURN NEW;
        END;
        $$;
    """)

    # =========================================================================
    # RLS POLICY FIXES (Performance - auth initplan optimization)
    # =========================================================================

    # 4. Fix planning_cells_authenticated_access
    # Use (SELECT auth.uid()) instead of auth.uid() for initplan optimization
    op.execute(
        "DROP POLICY IF EXISTS planning_cells_authenticated_access "
        "ON efir_budget.planning_cells;"
    )
    op.execute("""
        CREATE POLICY planning_cells_authenticated_access
        ON efir_budget.planning_cells
        FOR ALL
        USING (
            (SELECT auth.uid()) IS NOT NULL
            AND budget_version_id IN (
                SELECT id
                FROM efir_budget.budget_versions
                WHERE deleted_at IS NULL
            )
        )
        WITH CHECK (
            (SELECT auth.uid()) IS NOT NULL
            AND budget_version_id IN (
                SELECT id
                FROM efir_budget.budget_versions
                WHERE deleted_at IS NULL
            )
        );
    """)

    # 5. Fix cell_changes_authenticated_access
    op.execute(
        "DROP POLICY IF EXISTS cell_changes_authenticated_access "
        "ON efir_budget.cell_changes;"
    )
    op.execute("""
        CREATE POLICY cell_changes_authenticated_access
        ON efir_budget.cell_changes
        FOR ALL
        USING (
            (SELECT auth.uid()) IS NOT NULL
            AND budget_version_id IN (
                SELECT id
                FROM efir_budget.budget_versions
                WHERE deleted_at IS NULL
            )
        )
        WITH CHECK (
            (SELECT auth.uid()) IS NOT NULL
            AND budget_version_id IN (
                SELECT id
                FROM efir_budget.budget_versions
                WHERE deleted_at IS NULL
            )
        );
    """)

    # 6. Fix cell_comments_authenticated_access
    op.execute(
        "DROP POLICY IF EXISTS cell_comments_authenticated_access "
        "ON efir_budget.cell_comments;"
    )
    op.execute("""
        CREATE POLICY cell_comments_authenticated_access
        ON efir_budget.cell_comments
        FOR ALL
        USING ((SELECT auth.uid()) IS NOT NULL)
        WITH CHECK ((SELECT auth.uid()) IS NOT NULL);
    """)


def downgrade() -> None:
    """Revert to original (insecure/unoptimized) versions.

    Note: Running downgrade will reintroduce:
    - Security: Functions without SET search_path (search_path mutable vulnerability)
    - Performance: RLS policies with direct auth.uid() calls (per-row evaluation)

    Only run this if you need to rollback for compatibility reasons.
    """
    # Revert functions to original (without SET search_path)
    op.execute("""
        CREATE OR REPLACE FUNCTION efir_budget.update_updated_at()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION efir_budget.prevent_approved_version_edit()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF OLD.status = 'approved' THEN
                IF NEW.status = 'superseded' AND
                   OLD.name = NEW.name AND
                   OLD.fiscal_year = NEW.fiscal_year AND
                   OLD.academic_year = NEW.academic_year THEN
                    RETURN NEW;
                END IF;
                RAISE EXCEPTION
                    'Cannot modify approved budget version %. To make changes, create a new version or change status to superseded first.',
                    OLD.name;
            END IF;
            RETURN NEW;
        END;
        $$;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION efir_budget.validate_class_structure_size()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_min INTEGER;
            v_max INTEGER;
        BEGIN
            SELECT csp.min_class_size, csp.max_class_size
              INTO v_min, v_max
            FROM efir_budget.class_size_params csp
            JOIN efir_budget.academic_levels al ON al.id = NEW.level_id
            WHERE csp.budget_version_id = NEW.budget_version_id
              AND (csp.level_id = NEW.level_id
                   OR (csp.level_id IS NULL AND csp.cycle_id = al.cycle_id))
            ORDER BY CASE WHEN csp.level_id = NEW.level_id THEN 0 ELSE 1 END
            LIMIT 1;

            IF v_min IS NULL OR v_max IS NULL THEN
                RAISE EXCEPTION 'No class_size_params defined for level % in version %',
                    NEW.level_id, NEW.budget_version_id;
            END IF;

            IF NEW.avg_class_size < v_min OR NEW.avg_class_size > v_max THEN
                RAISE EXCEPTION 'avg_class_size % outside [%, %] for level % version %',
                    NEW.avg_class_size, v_min, v_max, NEW.level_id, NEW.budget_version_id;
            END IF;

            RETURN NEW;
        END;
        $$;
    """)

    # Revert RLS policies to original (without initplan optimization)
    op.execute(
        "DROP POLICY IF EXISTS planning_cells_authenticated_access "
        "ON efir_budget.planning_cells;"
    )
    op.execute("""
        CREATE POLICY planning_cells_authenticated_access
        ON efir_budget.planning_cells
        FOR ALL
        USING (
            auth.uid() IS NOT NULL
            AND budget_version_id IN (
                SELECT id FROM efir_budget.budget_versions WHERE deleted_at IS NULL
            )
        )
        WITH CHECK (
            auth.uid() IS NOT NULL
            AND budget_version_id IN (
                SELECT id FROM efir_budget.budget_versions WHERE deleted_at IS NULL
            )
        );
    """)

    op.execute(
        "DROP POLICY IF EXISTS cell_changes_authenticated_access "
        "ON efir_budget.cell_changes;"
    )
    op.execute("""
        CREATE POLICY cell_changes_authenticated_access
        ON efir_budget.cell_changes
        FOR ALL
        USING (
            auth.uid() IS NOT NULL
            AND budget_version_id IN (
                SELECT id FROM efir_budget.budget_versions WHERE deleted_at IS NULL
            )
        )
        WITH CHECK (
            auth.uid() IS NOT NULL
            AND budget_version_id IN (
                SELECT id FROM efir_budget.budget_versions WHERE deleted_at IS NULL
            )
        );
    """)

    op.execute(
        "DROP POLICY IF EXISTS cell_comments_authenticated_access "
        "ON efir_budget.cell_comments;"
    )
    op.execute("""
        CREATE POLICY cell_comments_authenticated_access
        ON efir_budget.cell_comments
        FOR ALL
        USING (auth.uid() IS NOT NULL)
        WITH CHECK (auth.uid() IS NOT NULL);
    """)
