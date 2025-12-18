"""Add retained_students and lateral_students columns to enrollment_projections.

Revision ID: 022_add_retain_lateral_columns
Revises: 021_add_organization_id_to_budget_versions
Create Date: 2025-12-13

These columns store the breakdown of projected students into:
- retained_students: Students retained from previous grade (R)
- lateral_students: New lateral entries (L)
- projected_students: Total (T) = R + L

This enables the enhanced projection results table to show R|L|T sub-columns.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "022_add_retain_lateral_columns"
down_revision = "021_add_organization_id_to_budget_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add retained_students and lateral_students columns."""

    # Add retained_students column with default 0
    op.add_column(
        "enrollment_projections",
        sa.Column("retained_students", sa.Integer(), nullable=False, server_default="0"),
        schema="efir_budget",
    )

    # Add lateral_students column with default 0
    op.add_column(
        "enrollment_projections",
        sa.Column("lateral_students", sa.Integer(), nullable=False, server_default="0"),
        schema="efir_budget",
    )

    # Remove server defaults after column creation (optional, for cleaner schema)
    # The SQLAlchemy model uses default=0 which works at app level
    op.alter_column(
        "enrollment_projections",
        "retained_students",
        server_default=None,
        schema="efir_budget",
    )
    op.alter_column(
        "enrollment_projections",
        "lateral_students",
        server_default=None,
        schema="efir_budget",
    )


def downgrade() -> None:
    """Remove retained_students and lateral_students columns."""

    op.drop_column("enrollment_projections", "lateral_students", schema="efir_budget")
    op.drop_column("enrollment_projections", "retained_students", schema="efir_budget")
