"""Add organizations and user_organizations tables.

Revision ID: 017a_organizations
Revises: 017_enrollment_projection_tables
Create Date: 2025-12-12 15:00:00.000000

This migration must run BEFORE 018_enrollment_derived_parameters because
that migration has FKs and RLS policies referencing these tables.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "017a_organizations"
down_revision: str | None = "017_enrollment_projection_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create organizations and user_organizations tables in efir_budget schema."""

    # =========================================================================
    # 1. Create the organizations table
    # =========================================================================
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="efir_budget",
        comment="Organizations (schools) in the system",
    )

    # Create index on is_active for faster lookups
    op.create_index(
        "ix_organizations_is_active",
        "organizations",
        ["is_active"],
        schema="efir_budget",
    )

    # Insert a default organization for EFIR (single-tenant deployment)
    op.execute(
        """
        INSERT INTO efir_budget.organizations (name, is_active)
        VALUES ('EFIR French International School', true)
        ON CONFLICT DO NOTHING;
        """
    )

    # Enable RLS on organizations table
    op.execute("ALTER TABLE efir_budget.organizations ENABLE ROW LEVEL SECURITY;")

    # Create RLS policy for authenticated users to read active organizations
    op.execute(
        """
        CREATE POLICY organizations_select_policy ON efir_budget.organizations
        FOR SELECT TO authenticated
        USING (is_active = true);
        """
    )

    # Create service_role bypass policy (for backend operations)
    op.execute(
        """
        CREATE POLICY organizations_service_role_all ON efir_budget.organizations
        FOR ALL TO service_role
        USING (true)
        WITH CHECK (true);
        """
    )

    # =========================================================================
    # 2. Create the user_organizations table (for multi-tenant access control)
    # =========================================================================
    op.create_table(
        "user_organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(50),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth.users.id"],
            name="fk_user_organizations_user",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["efir_budget.organizations.id"],
            name="fk_user_organizations_org",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "organization_id", name="uk_user_org"),
        schema="efir_budget",
        comment="Maps users to their organizations with roles",
    )

    # Create indexes for user_organizations lookups
    op.create_index(
        "ix_user_organizations_user_id",
        "user_organizations",
        ["user_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_user_organizations_organization_id",
        "user_organizations",
        ["organization_id"],
        schema="efir_budget",
    )

    # Enable RLS on user_organizations
    op.execute(
        "ALTER TABLE efir_budget.user_organizations ENABLE ROW LEVEL SECURITY;"
    )

    # RLS policy: Users can see their own organization memberships
    op.execute(
        """
        CREATE POLICY user_organizations_select_own ON efir_budget.user_organizations
        FOR SELECT TO authenticated
        USING (user_id = auth.uid());
        """
    )

    # Service role bypass for user_organizations
    op.execute(
        """
        CREATE POLICY user_organizations_service_role_all ON efir_budget.user_organizations
        FOR ALL TO service_role
        USING (true)
        WITH CHECK (true);
        """
    )

    # =========================================================================
    # 3. Link existing users to the default organization
    # =========================================================================
    op.execute(
        """
        INSERT INTO efir_budget.user_organizations (user_id, organization_id, role)
        SELECT u.id, o.id, 'admin'
        FROM auth.users u
        CROSS JOIN efir_budget.organizations o
        WHERE o.is_active = true
        ON CONFLICT (user_id, organization_id) DO NOTHING;
        """
    )


def downgrade() -> None:
    """Drop organizations and user_organizations tables."""

    # Drop user_organizations RLS policies
    op.execute(
        "DROP POLICY IF EXISTS user_organizations_service_role_all "
        "ON efir_budget.user_organizations;"
    )
    op.execute(
        "DROP POLICY IF EXISTS user_organizations_select_own "
        "ON efir_budget.user_organizations;"
    )

    # Drop user_organizations indexes and table
    op.drop_index(
        "ix_user_organizations_organization_id",
        table_name="user_organizations",
        schema="efir_budget",
    )
    op.drop_index(
        "ix_user_organizations_user_id",
        table_name="user_organizations",
        schema="efir_budget",
    )
    op.drop_table("user_organizations", schema="efir_budget")

    # Drop organizations RLS policies
    op.execute(
        "DROP POLICY IF EXISTS organizations_service_role_all "
        "ON efir_budget.organizations;"
    )
    op.execute(
        "DROP POLICY IF EXISTS organizations_select_policy "
        "ON efir_budget.organizations;"
    )

    # Drop organizations index and table
    op.drop_index(
        "ix_organizations_is_active",
        table_name="organizations",
        schema="efir_budget",
    )
    op.drop_table("organizations", schema="efir_budget")
