"""Add missing audit columns to nationality_distributions.

Revision ID: 012_add_audit_columns
Revises: 011_seed_reference_data
Create Date: 2025-12-06 01:00:00.000000

Adds missing audit columns to nationality_distributions table:
- created_by_id (UUID): User who created the record
- updated_by_id (UUID): User who last updated the record
- deleted_at (TIMESTAMPTZ): Soft delete timestamp

These columns are required because the NationalityDistribution SQLAlchemy model
inherits from BaseModel, which includes AuditMixin and SoftDeleteMixin.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = "012_add_audit_columns"
down_revision: str | None = "011_seed_reference_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add audit columns to nationality_distributions table."""

    # Add created_by_id column
    op.add_column(
        "nationality_distributions",
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who created the record (NULL if system-generated or user deleted)",
        ),
        schema="efir_budget",
    )

    # Add updated_by_id column
    op.add_column(
        "nationality_distributions",
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who last updated the record (NULL if system-updated or user deleted)",
        ),
        schema="efir_budget",
    )

    # Add deleted_at column for soft delete
    op.add_column(
        "nationality_distributions",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        schema="efir_budget",
    )

    # Add foreign key constraints to auth.users
    # Note: These reference Supabase's auth.users table
    op.execute(
        """
        ALTER TABLE efir_budget.nationality_distributions
        ADD CONSTRAINT fk_nationality_distributions_created_by
        FOREIGN KEY (created_by_id) REFERENCES auth.users(id)
        ON DELETE SET NULL;
        """
    )

    op.execute(
        """
        ALTER TABLE efir_budget.nationality_distributions
        ADD CONSTRAINT fk_nationality_distributions_updated_by
        FOREIGN KEY (updated_by_id) REFERENCES auth.users(id)
        ON DELETE SET NULL;
        """
    )


def downgrade() -> None:
    """Remove audit columns from nationality_distributions table."""

    # Drop foreign key constraints first
    op.execute(
        """
        ALTER TABLE efir_budget.nationality_distributions
        DROP CONSTRAINT IF EXISTS fk_nationality_distributions_created_by;
        """
    )

    op.execute(
        """
        ALTER TABLE efir_budget.nationality_distributions
        DROP CONSTRAINT IF EXISTS fk_nationality_distributions_updated_by;
        """
    )

    # Drop columns
    op.drop_column("nationality_distributions", "deleted_at", schema="efir_budget")
    op.drop_column("nationality_distributions", "updated_by_id", schema="efir_budget")
    op.drop_column("nationality_distributions", "created_by_id", schema="efir_budget")
