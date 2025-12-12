"""Add organization_id to budget_versions table.

This migration adds the organization_id foreign key to budget_versions to enable
proper multi-tenant data isolation for the enrollment calibration feature.

The calibration service requires organization_id to fetch organization-scoped:
- enrollment_derived_parameters
- enrollment_parameter_overrides
- enrollment_scenario_multipliers

Migration Strategy:
1. Add organization_id column as NULLABLE (backward compatible)
2. Backfill existing budget_versions with the default organization ID
3. Make column NOT NULL after backfill
4. Add foreign key constraint
5. Create index for query performance

Revision ID: 020_add_organization_id_to_budget_versions
Revises: 019_audit_columns_enrollment
Create Date: 2025-12-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "020_add_organization_id_to_budget_versions"
down_revision: str | None = "019_audit_columns_enrollment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add organization_id column to budget_versions table."""

    # =========================================================================
    # 1. Add organization_id column as NULLABLE initially
    # =========================================================================
    op.add_column(
        "budget_versions",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,  # Start nullable for safe backfill
            comment="Organization this budget version belongs to",
        ),
        schema="efir_budget",
    )

    # =========================================================================
    # 2. Backfill existing budget_versions with the default organization
    # =========================================================================
    # The organizations table was created in migration 017a and seeded with
    # a default "EFIR French International School" organization.
    op.execute(
        """
        UPDATE efir_budget.budget_versions
        SET organization_id = (
            SELECT id
            FROM efir_budget.organizations
            WHERE is_active = true
            ORDER BY created_at
            LIMIT 1
        )
        WHERE organization_id IS NULL;
        """
    )

    # =========================================================================
    # 3. Make organization_id NOT NULL after backfill
    # =========================================================================
    op.alter_column(
        "budget_versions",
        "organization_id",
        nullable=False,
        schema="efir_budget",
    )

    # =========================================================================
    # 4. Add foreign key constraint
    # =========================================================================
    op.create_foreign_key(
        "fk_budget_versions_organization",
        "budget_versions",
        "organizations",
        ["organization_id"],
        ["id"],
        source_schema="efir_budget",
        referent_schema="efir_budget",
        ondelete="CASCADE",
    )

    # =========================================================================
    # 5. Create index for query performance
    # =========================================================================
    op.create_index(
        "ix_budget_versions_organization_id",
        "budget_versions",
        ["organization_id"],
        schema="efir_budget",
    )

    # =========================================================================
    # 6. Update unique constraint for WORKING versions
    # =========================================================================
    # Business rule: Only one WORKING version per organization per fiscal year
    # Drop the old partial unique index if it exists and create a new one
    # that includes organization_id
    op.execute(
        """
        DROP INDEX IF EXISTS efir_budget.uk_budget_versions_one_working_per_year;
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX uk_budget_versions_one_working_per_org_year
        ON efir_budget.budget_versions (organization_id, fiscal_year)
        WHERE status = 'working' AND deleted_at IS NULL;
        """
    )


def downgrade() -> None:
    """Remove organization_id column from budget_versions table."""

    # Drop the new unique index
    op.execute(
        """
        DROP INDEX IF EXISTS efir_budget.uk_budget_versions_one_working_per_org_year;
        """
    )

    # Recreate the old unique index (without organization_id)
    op.execute(
        """
        CREATE UNIQUE INDEX uk_budget_versions_one_working_per_year
        ON efir_budget.budget_versions (fiscal_year)
        WHERE status = 'working' AND deleted_at IS NULL;
        """
    )

    # Drop the index
    op.drop_index(
        "ix_budget_versions_organization_id",
        table_name="budget_versions",
        schema="efir_budget",
    )

    # Drop the foreign key constraint
    op.drop_constraint(
        "fk_budget_versions_organization",
        "budget_versions",
        schema="efir_budget",
        type_="foreignkey",
    )

    # Drop the column
    op.drop_column(
        "budget_versions",
        "organization_id",
        schema="efir_budget",
    )
