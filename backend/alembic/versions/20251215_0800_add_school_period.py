"""Add school_period column to settings_versions

Revision ID: 029_add_school_period
Revises: 028_phase_4c_financial_consolidation
Create Date: 2025-12-15 08:00:00.000000

Adds school_period column to settings_versions table for linking budget versions
to specific academic periods within a fiscal year:
- Period 1 (P1): Jan-Aug → End of previous academic year (e.g., Jan-Aug 2026 → AY 2025-2026)
- Period 2 (P2): Sep-Dec → Start of next academic year (e.g., Sep-Dec 2026 → AY 2026-2027)
- NULL: Full Year (both periods combined)

This is critical for:
- Linking GL actuals (monthly from Odoo) to correct version
- Mid-year forecasts that update P2 while keeping P1 actuals
- Revenue/cost recognition timing
"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers
revision: str = "029_add_school_period"
down_revision: str | None = "028_phase_4c_financial_consolidation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add school_period column to settings_versions."""

    # Add school_period column with NULL default (backward compatible)
    op.execute("""
        ALTER TABLE efir_budget.settings_versions
        ADD COLUMN IF NOT EXISTS school_period SMALLINT;
    """)

    # Add constraint: must be 1, 2, or NULL
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_versions_school_period'
            ) THEN
                ALTER TABLE efir_budget.settings_versions
                ADD CONSTRAINT ck_versions_school_period
                CHECK (school_period IS NULL OR school_period IN (1, 2));
            END IF;
        END $$;
    """)

    # Add column comment
    op.execute("""
        COMMENT ON COLUMN efir_budget.settings_versions.school_period IS
            'School period within fiscal year: 1=Jan-Aug (end of prev AY), 2=Sep-Dec (start of next AY), NULL=Full Year';
    """)


def downgrade() -> None:
    """Remove school_period column from settings_versions."""

    # Drop constraint first
    op.execute("""
        ALTER TABLE efir_budget.settings_versions
        DROP CONSTRAINT IF EXISTS ck_versions_school_period;
    """)

    # Drop column
    op.execute("""
        ALTER TABLE efir_budget.settings_versions
        DROP COLUMN IF EXISTS school_period;
    """)
