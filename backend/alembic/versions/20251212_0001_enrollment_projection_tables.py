"""Enrollment projection tables and seed data (Module 7 upgrade).

Revision ID: 017_enrollment_projection_tables
Revises: 016_fix_security_rls
Create Date: 2025-12-12 00:01:00.000000

Creates the enrollment projection subsystem tables:
1. enrollment_scenarios (reference, 3 scenarios)
2. enrollment_lateral_entry_defaults (reference, per grade)
3. enrollment_projection_configs (per budget version)
4. enrollment_global_overrides (layer 2)
5. enrollment_level_overrides (layer 3)
6. enrollment_grade_overrides (layer 4)
7. enrollment_projections (cached results)

Seeds:
- Worst/Base/Best scenarios per ENROLLMENT_PROJECTION_IMPLEMENTATION_PLAN.md
- Base lateral entry defaults by grade code
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "017_enrollment_projection_tables"
down_revision = "016_fix_security_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create projection tables and seed reference data."""

    # =========================================================================
    # 1. enrollment_scenarios (reference)
    # =========================================================================
    op.create_table(
        "enrollment_scenarios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=False),
        sa.Column("name_fr", sa.String(100), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("description_fr", sa.Text(), nullable=True),
        sa.Column("ps_entry", sa.Integer(), nullable=False),
        sa.Column("entry_growth_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("default_retention", sa.Numeric(5, 4), nullable=False),
        sa.Column("terminal_retention", sa.Numeric(5, 4), nullable=False),
        sa.Column("lateral_multiplier", sa.Numeric(4, 2), nullable=False),
        sa.Column("color_code", sa.String(10), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("code", name="uk_enrollment_scenarios_code"),
        schema="efir_budget",
        comment="Enrollment scenario defaults (Worst/Base/Best)",
    )

    # =========================================================================
    # 2. enrollment_lateral_entry_defaults (reference)
    # =========================================================================
    op.create_table(
        "enrollment_lateral_entry_defaults",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.academic_levels.id"),
            nullable=False,
        ),
        sa.Column("base_lateral_entry", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint("base_lateral_entry >= 0", name="ck_lateral_defaults_non_negative"),
        sa.UniqueConstraint("level_id", name="uk_lateral_defaults_level"),
        schema="efir_budget",
        comment="Historical base lateral entry per academic level",
    )

    # =========================================================================
    # 3. enrollment_projection_configs (versioned)
    # =========================================================================
    op.create_table(
        "enrollment_projection_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scenario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.enrollment_scenarios.id"),
            nullable=False,
        ),
        sa.Column("base_year", sa.Integer(), nullable=False),
        sa.Column(
            "projection_years",
            sa.Integer(),
            nullable=False,
            server_default="5",
        ),
        sa.Column(
            "school_max_capacity",
            sa.Integer(),
            nullable=False,
            server_default="1850",
        ),
        sa.Column(
            "default_class_size",
            sa.Integer(),
            nullable=False,
            server_default="25",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "validated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.users.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "projection_years BETWEEN 1 AND 10",
            name="ck_projection_configs_years_range",
        ),
        sa.CheckConstraint(
            "school_max_capacity > 0",
            name="ck_projection_configs_capacity_positive",
        ),
        sa.CheckConstraint(
            "default_class_size BETWEEN 15 AND 40",
            name="ck_projection_configs_default_class_size_range",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'validated')",
            name="ck_projection_configs_status_valid",
        ),
        sa.UniqueConstraint("budget_version_id", name="uk_projection_configs_version"),
        schema="efir_budget",
        comment="Per-version projection configuration",
    )
    op.create_index(
        "idx_projection_configs_version",
        "enrollment_projection_configs",
        ["budget_version_id"],
        schema="efir_budget",
    )
    op.create_index(
        "idx_projection_configs_status",
        "enrollment_projection_configs",
        ["status"],
        schema="efir_budget",
    )

    # =========================================================================
    # 4. enrollment_global_overrides (layer 2)
    # =========================================================================
    op.create_table(
        "enrollment_global_overrides",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "projection_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "efir_budget.enrollment_projection_configs.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("ps_entry_adjustment", sa.Integer(), nullable=True),
        sa.Column("retention_adjustment", sa.Numeric(5, 4), nullable=True),
        sa.Column("lateral_multiplier_override", sa.Numeric(4, 2), nullable=True),
        sa.Column("class_size_override", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "ps_entry_adjustment BETWEEN -20 AND 20",
            name="ck_global_overrides_ps_entry_adjustment_range",
        ),
        sa.CheckConstraint(
            "retention_adjustment BETWEEN -0.05 AND 0.05",
            name="ck_global_overrides_retention_adjustment_range",
        ),
        sa.CheckConstraint(
            "lateral_multiplier_override BETWEEN 0.5 AND 1.5",
            name="ck_global_overrides_lateral_multiplier_range",
        ),
        sa.CheckConstraint(
            "class_size_override BETWEEN 20 AND 30",
            name="ck_global_overrides_class_size_range",
        ),
        sa.UniqueConstraint(
            "projection_config_id", name="uk_global_overrides_config"
        ),
        schema="efir_budget",
        comment="Global overrides for a projection config",
    )

    # =========================================================================
    # 5. enrollment_level_overrides (layer 3)
    # =========================================================================
    op.create_table(
        "enrollment_level_overrides",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "projection_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "efir_budget.enrollment_projection_configs.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.academic_cycles.id"),
            nullable=False,
        ),
        sa.Column("class_size_ceiling", sa.Integer(), nullable=True),
        sa.Column("max_divisions", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "class_size_ceiling BETWEEN 20 AND 30",
            name="ck_level_overrides_class_size_ceiling_range",
        ),
        sa.CheckConstraint(
            "max_divisions BETWEEN 2 AND 10",
            name="ck_level_overrides_max_divisions_range",
        ),
        sa.UniqueConstraint(
            "projection_config_id",
            "cycle_id",
            name="uk_level_overrides_config_cycle",
        ),
        schema="efir_budget",
        comment="Level (cycle) overrides for a projection config",
    )
    op.create_index(
        "idx_level_overrides_config",
        "enrollment_level_overrides",
        ["projection_config_id"],
        schema="efir_budget",
    )

    # =========================================================================
    # 6. enrollment_grade_overrides (layer 4)
    # =========================================================================
    op.create_table(
        "enrollment_grade_overrides",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "projection_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "efir_budget.enrollment_projection_configs.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.academic_levels.id"),
            nullable=False,
        ),
        sa.Column("retention_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("lateral_entry", sa.Integer(), nullable=True),
        sa.Column("max_divisions", sa.Integer(), nullable=True),
        sa.Column("class_size_ceiling", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "retention_rate BETWEEN 0.85 AND 1.00",
            name="ck_grade_overrides_retention_range",
        ),
        sa.CheckConstraint(
            "lateral_entry BETWEEN 0 AND 50",
            name="ck_grade_overrides_lateral_entry_range",
        ),
        sa.CheckConstraint(
            "max_divisions BETWEEN 2 AND 8",
            name="ck_grade_overrides_max_divisions_range",
        ),
        sa.CheckConstraint(
            "class_size_ceiling BETWEEN 20 AND 30",
            name="ck_grade_overrides_class_size_ceiling_range",
        ),
        sa.UniqueConstraint(
            "projection_config_id",
            "level_id",
            name="uk_grade_overrides_config_level",
        ),
        schema="efir_budget",
        comment="Grade overrides for a projection config",
    )
    op.create_index(
        "idx_grade_overrides_config",
        "enrollment_grade_overrides",
        ["projection_config_id"],
        schema="efir_budget",
    )

    # =========================================================================
    # 7. enrollment_projections (cached results)
    # =========================================================================
    op.create_table(
        "enrollment_projections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "projection_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "efir_budget.enrollment_projection_configs.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("school_year", sa.String(9), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column(
            "level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.academic_levels.id"),
            nullable=False,
        ),
        sa.Column("projected_students", sa.Integer(), nullable=False),
        sa.Column("divisions", sa.Integer(), nullable=False),
        sa.Column("avg_class_size", sa.Numeric(4, 1), nullable=True),
        sa.Column(
            "fiscal_year_weighted_students", sa.Numeric(6, 1), nullable=True
        ),
        sa.Column(
            "was_capacity_constrained",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("original_projection", sa.Integer(), nullable=True),
        sa.Column(
            "reduction_applied",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("reduction_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "calculation_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "projected_students >= 0",
            name="ck_projections_projected_students_non_negative",
        ),
        sa.CheckConstraint(
            "divisions >= 0",
            name="ck_projections_divisions_non_negative",
        ),
        sa.UniqueConstraint(
            "projection_config_id",
            "school_year",
            "level_id",
            name="uk_projections_config_year_level",
        ),
        schema="efir_budget",
        comment="Cached enrollment projections per year and level",
    )
    op.create_index(
        "idx_projections_config",
        "enrollment_projections",
        ["projection_config_id"],
        schema="efir_budget",
    )
    op.create_index(
        "idx_projections_fiscal_year",
        "enrollment_projections",
        ["fiscal_year"],
        schema="efir_budget",
    )

    # =========================================================================
    # Apply updated_at triggers
    # =========================================================================
    new_tables = [
        "enrollment_scenarios",
        "enrollment_lateral_entry_defaults",
        "enrollment_projection_configs",
        "enrollment_global_overrides",
        "enrollment_level_overrides",
        "enrollment_grade_overrides",
        "enrollment_projections",
    ]
    for table in new_tables:
        op.execute(f"""
            CREATE TRIGGER set_updated_at
            BEFORE UPDATE ON efir_budget.{table}
            FOR EACH ROW
            EXECUTE FUNCTION efir_budget.update_updated_at();
        """)

    # =========================================================================
    # Seed scenarios (3 rows)
    # =========================================================================
    op.execute(
        """
        INSERT INTO efir_budget.enrollment_scenarios
            (code, name_en, name_fr, description_en, description_fr,
             ps_entry, entry_growth_rate, default_retention, terminal_retention,
             lateral_multiplier, color_code, sort_order)
        VALUES
            ('worst_case', 'Worst Case', 'Pire Cas',
             'Economic downturn, expat departures, competitive pressure',
             'Ralentissement économique, départs d''expatriés, pression concurrentielle',
             45, -0.02, 0.90, 0.92, 0.3, '#EF4444', 1),
            ('base', 'Base', 'Base',
             'Historical average continuation, no significant changes',
             'Continuation de la moyenne historique, pas de changements significatifs',
             65, 0.00, 0.96, 0.98, 1.0, '#3B82F6', 2),
            ('best_case', 'Best Case', 'Meilleur Cas',
             'Maximum growth, strong demand, near-capacity utilization',
             'Croissance maximale, forte demande, utilisation proche de la capacité',
             85, 0.03, 0.99, 1.00, 1.5, '#22C55E', 3)
        ON CONFLICT (code) DO NOTHING;
        """
    )

    # =========================================================================
    # Seed base lateral entry defaults (14 rows)
    # =========================================================================
    op.execute(
        """
        INSERT INTO efir_budget.enrollment_lateral_entry_defaults (level_id, base_lateral_entry, notes)
        SELECT id,
          CASE code
            WHEN 'MS' THEN 27
            WHEN 'GS' THEN 20
            WHEN 'CP' THEN 12
            WHEN 'CE1' THEN 7
            WHEN 'CE2' THEN 6
            WHEN 'CM1' THEN 5
            WHEN 'CM2' THEN 7
            WHEN '6EME' THEN 8
            WHEN '5EME' THEN 5
            WHEN '4EME' THEN 6
            WHEN '3EME' THEN 6
            WHEN '2NDE' THEN 8
            WHEN '1ERE' THEN 6
            WHEN 'TLE' THEN 1
          END,
          'Historical average lateral entry'
        FROM efir_budget.academic_levels
        WHERE code IN (
          'MS','GS','CP','CE1','CE2','CM1','CM2',
          '6EME','5EME','4EME','3EME','2NDE','1ERE','TLE'
        )
        ON CONFLICT (level_id) DO NOTHING;
        """
    )


def downgrade() -> None:
    """Drop projection tables."""

    op.drop_table("enrollment_projections", schema="efir_budget")
    op.drop_table("enrollment_grade_overrides", schema="efir_budget")
    op.drop_table("enrollment_level_overrides", schema="efir_budget")
    op.drop_table("enrollment_global_overrides", schema="efir_budget")
    op.drop_table("enrollment_projection_configs", schema="efir_budget")
    op.drop_table("enrollment_lateral_entry_defaults", schema="efir_budget")
    op.drop_table("enrollment_scenarios", schema="efir_budget")

