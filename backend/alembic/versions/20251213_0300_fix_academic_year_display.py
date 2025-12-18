"""Fix academic_year display strings to match STARTING year convention.

Revision ID: 023_fix_academic_year_display
Revises: 022_add_retain_lateral_columns
Create Date: 2025-12-13

The fiscal_year field uses the STARTING year convention:
- fiscal_year=2026 means academic year 2026-2027

This migration fixes any academic_year values that don't match this convention.
For example, if fiscal_year=2026 has academic_year="2025-2026", it will be
corrected to "2026-2027".

This ensures consistency across the system where:
- fiscal_year=2026 → academic_year="2026-2027" → target school year "2026/2027"
"""

from alembic import op

# revision identifiers, used by Alembic
revision = "023_fix_academic_year_display"
down_revision = "022_add_retain_lateral_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix academic_year to match the STARTING year convention.

    fiscal_year is the STARTING year, so:
    - fiscal_year=2026 should have academic_year="2026-2027"
    - NOT academic_year="2025-2026"
    """
    # Fix any mismatched academic_year values in budget_versions
    # The correct format is: fiscal_year || '-' || (fiscal_year + 1)
    op.execute("""
        UPDATE efir_budget.budget_versions
        SET academic_year = fiscal_year || '-' || (fiscal_year + 1)
        WHERE academic_year != (fiscal_year || '-' || (fiscal_year + 1))
    """)

    # NOTE: historical_actuals table does NOT have academic_year column
    # It only has fiscal_year, so no fix needed there


def downgrade() -> None:
    """No downgrade - this is a data fix, not a schema change.

    The previous values were incorrect, so there's nothing to restore.
    If needed, you can manually set academic_year values, but the
    STARTING year convention is the correct one.
    """
    pass
