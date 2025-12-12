"""Add enrollment derived parameters and settings tables.

This migration adds tables for:
1. enrollment_derived_parameters - Auto-calculated rates from rolling 4-year history
2. enrollment_parameter_overrides - User overrides for lateral/retention rates
3. enrollment_scenario_multipliers - Single multiplier per scenario

These tables support the dynamic lateral entry calculation engine.

Revision ID: 018_enrollment_derived_parameters
Revises: 017_enrollment_projection_tables
Create Date: 2025-12-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "018_enrollment_derived_parameters"
down_revision = "017a_organizations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create enrollment derived parameters and settings tables."""

    # =========================================================================
    # 1. enrollment_derived_parameters - Auto-calculated from history
    # =========================================================================
    op.create_table(
        "enrollment_derived_parameters",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grade_code", sa.String(10), nullable=False),

        # Derived values
        sa.Column("progression_rate", sa.Numeric(6, 4), nullable=True),  # e.g., 1.1410 = 114.10%
        sa.Column("lateral_entry_rate", sa.Numeric(6, 4), nullable=True),  # e.g., 0.1410 = 14.10%
        sa.Column("retention_rate", sa.Numeric(6, 4), nullable=True),  # e.g., 0.9600 = 96.00%

        # Quality indicators
        sa.Column("confidence", sa.String(10), nullable=False, server_default="low"),
        sa.Column("std_deviation", sa.Numeric(6, 4), nullable=True),
        sa.Column("years_used", sa.Integer(), nullable=False, server_default="0"),

        # Metadata
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("source_years", postgresql.JSONB(), nullable=False, server_default="[]"),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["efir_budget.organizations.id"],
            name="fk_derived_params_organization",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("organization_id", "grade_code", name="uk_derived_params_org_grade"),
        sa.CheckConstraint("confidence IN ('high', 'medium', 'low')", name="ck_derived_params_confidence"),
        sa.CheckConstraint("progression_rate >= 0 AND progression_rate <= 3", name="ck_derived_params_progression_range"),
        sa.CheckConstraint("lateral_entry_rate >= 0 AND lateral_entry_rate <= 1", name="ck_derived_params_lateral_range"),
        sa.CheckConstraint("retention_rate >= 0 AND retention_rate <= 1", name="ck_derived_params_retention_range"),
        sa.CheckConstraint("years_used >= 0", name="ck_derived_params_years_non_negative"),
        schema="efir_budget",
        comment="Auto-calculated enrollment parameters from rolling 4-year historical window",
    )

    # Indexes for enrollment_derived_parameters
    op.create_index(
        "ix_derived_params_org_id",
        "enrollment_derived_parameters",
        ["organization_id"],
        schema="efir_budget",
    )

    # =========================================================================
    # 2. enrollment_parameter_overrides - User overrides per grade
    # =========================================================================
    op.create_table(
        "enrollment_parameter_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grade_code", sa.String(10), nullable=False),

        # Override flags and values
        sa.Column("override_lateral_rate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manual_lateral_rate", sa.Numeric(6, 4), nullable=True),  # 0.0000 to 1.0000

        sa.Column("override_retention_rate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manual_retention_rate", sa.Numeric(6, 4), nullable=True),  # 0.5000 to 1.0000

        sa.Column("override_fixed_lateral", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manual_fixed_lateral", sa.Integer(), nullable=True),  # 0 to 100

        # Metadata
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["efir_budget.organizations.id"],
            name="fk_param_overrides_organization",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["auth.users.id"],
            name="fk_param_overrides_updated_by",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("organization_id", "grade_code", name="uk_param_overrides_org_grade"),
        sa.CheckConstraint(
            "manual_lateral_rate IS NULL OR (manual_lateral_rate >= 0 AND manual_lateral_rate <= 1)",
            name="ck_param_overrides_lateral_range"
        ),
        sa.CheckConstraint(
            "manual_retention_rate IS NULL OR (manual_retention_rate >= 0.5 AND manual_retention_rate <= 1)",
            name="ck_param_overrides_retention_range"
        ),
        sa.CheckConstraint(
            "manual_fixed_lateral IS NULL OR (manual_fixed_lateral >= 0 AND manual_fixed_lateral <= 100)",
            name="ck_param_overrides_fixed_lateral_range"
        ),
        schema="efir_budget",
        comment="User overrides for enrollment parameters (lateral entry and retention rates)",
    )

    # Indexes for enrollment_parameter_overrides
    op.create_index(
        "ix_param_overrides_org_id",
        "enrollment_parameter_overrides",
        ["organization_id"],
        schema="efir_budget",
    )

    # =========================================================================
    # 3. enrollment_scenario_multipliers - Single multiplier per scenario
    # =========================================================================
    op.create_table(
        "enrollment_scenario_multipliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_code", sa.String(20), nullable=False),

        # Single multiplier per scenario
        sa.Column("lateral_multiplier", sa.Numeric(4, 2), nullable=False, server_default="1.00"),

        # Metadata
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["efir_budget.organizations.id"],
            name="fk_scenario_mult_organization",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("organization_id", "scenario_code", name="uk_scenario_mult_org_scenario"),
        sa.CheckConstraint(
            "lateral_multiplier >= 0.1 AND lateral_multiplier <= 3.0",
            name="ck_scenario_mult_range"
        ),
        schema="efir_budget",
        comment="Scenario-specific lateral entry multipliers",
    )

    # Indexes for enrollment_scenario_multipliers
    op.create_index(
        "ix_scenario_mult_org_id",
        "enrollment_scenario_multipliers",
        ["organization_id"],
        schema="efir_budget",
    )

    # =========================================================================
    # 4. Seed default scenario multipliers for existing organizations
    # =========================================================================
    op.execute(
        """
        INSERT INTO efir_budget.enrollment_scenario_multipliers (organization_id, scenario_code, lateral_multiplier)
        SELECT o.id, s.code,
            CASE s.code
                WHEN 'worst_case' THEN 0.30
                WHEN 'conservative' THEN 0.60
                WHEN 'base' THEN 1.00
                WHEN 'optimistic' THEN 1.30
                WHEN 'best_case' THEN 1.50
            END
        FROM efir_budget.organizations o
        CROSS JOIN efir_budget.enrollment_scenarios s
        ON CONFLICT (organization_id, scenario_code) DO NOTHING;
        """
    )

    # =========================================================================
    # 5. RLS Policies
    # =========================================================================

    # Enable RLS on new tables
    op.execute("ALTER TABLE efir_budget.enrollment_derived_parameters ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE efir_budget.enrollment_parameter_overrides ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE efir_budget.enrollment_scenario_multipliers ENABLE ROW LEVEL SECURITY;")

    # RLS for enrollment_derived_parameters
    op.execute(
        """
        CREATE POLICY "derived_params_select_own_org"
        ON efir_budget.enrollment_derived_parameters
        FOR SELECT
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "derived_params_insert_own_org"
        ON efir_budget.enrollment_derived_parameters
        FOR INSERT
        TO authenticated
        WITH CHECK (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "derived_params_update_own_org"
        ON efir_budget.enrollment_derived_parameters
        FOR UPDATE
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        )
        WITH CHECK (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "derived_params_delete_own_org"
        ON efir_budget.enrollment_derived_parameters
        FOR DELETE
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    # RLS for enrollment_parameter_overrides
    op.execute(
        """
        CREATE POLICY "param_overrides_select_own_org"
        ON efir_budget.enrollment_parameter_overrides
        FOR SELECT
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "param_overrides_insert_own_org"
        ON efir_budget.enrollment_parameter_overrides
        FOR INSERT
        TO authenticated
        WITH CHECK (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "param_overrides_update_own_org"
        ON efir_budget.enrollment_parameter_overrides
        FOR UPDATE
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        )
        WITH CHECK (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "param_overrides_delete_own_org"
        ON efir_budget.enrollment_parameter_overrides
        FOR DELETE
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    # RLS for enrollment_scenario_multipliers
    op.execute(
        """
        CREATE POLICY "scenario_mult_select_own_org"
        ON efir_budget.enrollment_scenario_multipliers
        FOR SELECT
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "scenario_mult_insert_own_org"
        ON efir_budget.enrollment_scenario_multipliers
        FOR INSERT
        TO authenticated
        WITH CHECK (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "scenario_mult_update_own_org"
        ON efir_budget.enrollment_scenario_multipliers
        FOR UPDATE
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        )
        WITH CHECK (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    op.execute(
        """
        CREATE POLICY "scenario_mult_delete_own_org"
        ON efir_budget.enrollment_scenario_multipliers
        FOR DELETE
        TO authenticated
        USING (
            organization_id IN (
                SELECT organization_id FROM efir_budget.user_organizations
                WHERE user_id = auth.uid()
            )
        );
        """
    )

    # =========================================================================
    # 6. Service role bypass policies (for backend service operations)
    # =========================================================================
    op.execute(
        """
        CREATE POLICY "derived_params_service_role_all"
        ON efir_budget.enrollment_derived_parameters
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
        """
    )

    op.execute(
        """
        CREATE POLICY "param_overrides_service_role_all"
        ON efir_budget.enrollment_parameter_overrides
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
        """
    )

    op.execute(
        """
        CREATE POLICY "scenario_mult_service_role_all"
        ON efir_budget.enrollment_scenario_multipliers
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
        """
    )


def downgrade() -> None:
    """Drop enrollment derived parameters and settings tables."""

    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS derived_params_service_role_all ON efir_budget.enrollment_derived_parameters;")
    op.execute("DROP POLICY IF EXISTS derived_params_delete_own_org ON efir_budget.enrollment_derived_parameters;")
    op.execute("DROP POLICY IF EXISTS derived_params_update_own_org ON efir_budget.enrollment_derived_parameters;")
    op.execute("DROP POLICY IF EXISTS derived_params_insert_own_org ON efir_budget.enrollment_derived_parameters;")
    op.execute("DROP POLICY IF EXISTS derived_params_select_own_org ON efir_budget.enrollment_derived_parameters;")

    op.execute("DROP POLICY IF EXISTS param_overrides_service_role_all ON efir_budget.enrollment_parameter_overrides;")
    op.execute("DROP POLICY IF EXISTS param_overrides_delete_own_org ON efir_budget.enrollment_parameter_overrides;")
    op.execute("DROP POLICY IF EXISTS param_overrides_update_own_org ON efir_budget.enrollment_parameter_overrides;")
    op.execute("DROP POLICY IF EXISTS param_overrides_insert_own_org ON efir_budget.enrollment_parameter_overrides;")
    op.execute("DROP POLICY IF EXISTS param_overrides_select_own_org ON efir_budget.enrollment_parameter_overrides;")

    op.execute("DROP POLICY IF EXISTS scenario_mult_service_role_all ON efir_budget.enrollment_scenario_multipliers;")
    op.execute("DROP POLICY IF EXISTS scenario_mult_delete_own_org ON efir_budget.enrollment_scenario_multipliers;")
    op.execute("DROP POLICY IF EXISTS scenario_mult_update_own_org ON efir_budget.enrollment_scenario_multipliers;")
    op.execute("DROP POLICY IF EXISTS scenario_mult_insert_own_org ON efir_budget.enrollment_scenario_multipliers;")
    op.execute("DROP POLICY IF EXISTS scenario_mult_select_own_org ON efir_budget.enrollment_scenario_multipliers;")

    # Drop tables
    op.drop_table("enrollment_scenario_multipliers", schema="efir_budget")
    op.drop_table("enrollment_parameter_overrides", schema="efir_budget")
    op.drop_table("enrollment_derived_parameters", schema="efir_budget")
