"""Remove school_period column from settings_versions.

Revision ID: 031_remove_school_period
Revises: 030_rls_class_size_params
Create Date: 2025-12-16 02:00:00.000000

The school_period column is no longer needed as the application now
automatically handles both P1 and P2 periods based on fiscal year selection.
Academic years are computed client-side from the fiscal year.

Changes:
- Drops the ck_versions_school_period constraint
- Drops the school_period column from settings_versions
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "031_remove_school_period"
down_revision = "030_rls_class_size_params"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove school_period column and its constraint."""
    # Drop the check constraint first
    op.execute("""
        ALTER TABLE efir_budget.settings_versions
        DROP CONSTRAINT IF EXISTS ck_versions_school_period;
    """)

    # Drop the column
    op.execute("""
        ALTER TABLE efir_budget.settings_versions
        DROP COLUMN IF EXISTS school_period;
    """)


def downgrade() -> None:
    """Re-add school_period column and constraint."""
    # Add column back
    op.execute("""
        ALTER TABLE efir_budget.settings_versions
        ADD COLUMN IF NOT EXISTS school_period SMALLINT;
    """)

    # Add constraint back
    op.execute("""
        ALTER TABLE efir_budget.settings_versions
        ADD CONSTRAINT ck_versions_school_period
        CHECK (school_period IS NULL OR school_period IN (1, 2));
    """)

    # Add column comment
    op.execute("""
        COMMENT ON COLUMN efir_budget.settings_versions.school_period IS
            'School period within fiscal year: 1=Jan-Aug (end of prev AY), 2=Sep-Dec (start of next AY), NULL=Full Year';
    """)
