"""Validate class structure averages against class size parameters.

Revision ID: 005_class_structure_validation
Revises: 004_fix_critical_issues
Create Date: 2025-12-01 01:00:00

Adds a trigger to ensure class_structures.avg_class_size stays within the
configured min/max bounds from class_size_params (level-specific preferred,
else cycle-level).
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_class_structure_validation"
down_revision: str | None = "004_fix_critical_issues"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add validation trigger for class_structures."""
    op.execute(
        """
        CREATE OR REPLACE FUNCTION efir_budget.validate_class_structure_size()
        RETURNS TRIGGER AS $$
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
                    'avg_class_size % outside [% , %] for level % version %',
                    NEW.avg_class_size, v_min, v_max, NEW.level_id, NEW.budget_version_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER validate_class_structure_size
        BEFORE INSERT OR UPDATE ON efir_budget.class_structures
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.validate_class_structure_size();
        """
    )


def downgrade() -> None:
    """Remove validation trigger and function."""
    op.execute(
        "DROP TRIGGER IF EXISTS validate_class_structure_size ON efir_budget.class_structures;"
    )
    op.execute("DROP FUNCTION IF EXISTS efir_budget.validate_class_structure_size();")
