"""Strategic Layer: 5-Year Strategic Planning (Module 18)

Revision ID: 007_strategic_layer
Revises: 20251201_0100_class_structure_validation
Create Date: 2025-12-01 01:38:00.000000

Creates Strategic Layer tables:
- Module 18: 5-Year Strategic Planning (strategic_plans, strategic_plan_scenarios,
  strategic_plan_projections, strategic_initiatives)

Business Purpose:
-----------------
1. Enable multi-year strategic planning with 5-year horizon
2. Support scenario modeling (base case, conservative, optimistic, new campus)
3. Project enrollment, revenue, costs, and capital expenditures
4. Track strategic initiatives and major capital investments
5. Facilitate Board-level strategic decision making and long-term planning

Dependencies:
-------------
- Requires: 20251201_0100_class_structure_validation (Phase 4 validation fixes)
- Creates: 4 tables with 3 enum types and comprehensive constraints
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = "007_strategic_layer"
down_revision: str | None = "20251201_0100_class_structure_validation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Strategic Layer tables."""

    # ========================================================================
    # Create Enum Types
    # ========================================================================

    # Module 18: ScenarioType enum
    scenario_type = postgresql.ENUM(
        "base_case",
        "conservative",
        "optimistic",
        "new_campus",
        name="scenariotype",
        schema="efir_budget",
    )
    scenario_type.create(op.get_bind())

    # Module 18: InitiativeStatus enum
    initiative_status = postgresql.ENUM(
        "planned",
        "approved",
        "in_progress",
        "completed",
        "cancelled",
        name="initiativestatus",
        schema="efir_budget",
    )
    initiative_status.create(op.get_bind())

    # Module 18: ProjectionCategory enum
    projection_category = postgresql.ENUM(
        "revenue",
        "personnel_costs",
        "operating_costs",
        "capex",
        "depreciation",
        name="projectioncategory",
        schema="efir_budget",
    )
    projection_category.create(op.get_bind())

    # ========================================================================
    # Module 18: Strategic Planning - strategic_plans (Parent Table)
    # ========================================================================

    op.create_table(
        "strategic_plans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "name",
            sa.String(200),
            nullable=False,
            comment="Unique strategic plan name (e.g., 'EFIR Strategic Plan 2025-2030')",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Plan description and key objectives",
        ),
        sa.Column(
            "base_year",
            sa.Integer(),
            nullable=False,
            comment="Starting year of 5-year plan (e.g., 2025 for 2025-2030 plan)",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
            comment="Plan status: draft, approved, archived",
        ),
        # Audit columns (BaseModel)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Last update timestamp",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who created this record (Supabase Auth UUID)",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who last updated this record (Supabase Auth UUID)",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp",
        ),
        # Constraints
        sa.UniqueConstraint("name", name="uk_strategic_plan_name"),
        sa.CheckConstraint(
            "base_year >= 2000 AND base_year <= 2100",
            name="ck_strategic_plan_year_range",
        ),
        schema="efir_budget",
    )

    # Indexes for strategic_plans
    op.create_index(
        "ix_strategic_plans_name",
        "strategic_plans",
        ["name"],
        unique=True,
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_plans_base_year",
        "strategic_plans",
        ["base_year"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_plans_status",
        "strategic_plans",
        ["status"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 18: Strategic Planning - strategic_plan_scenarios
    # ========================================================================

    op.create_table(
        "strategic_plan_scenarios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "strategic_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "efir_budget.strategic_plans.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            comment="Strategic plan this scenario belongs to",
        ),
        sa.Column(
            "scenario_type",
            postgresql.ENUM(
                "base_case",
                "conservative",
                "optimistic",
                "new_campus",
                name="scenariotype",
                schema="efir_budget",
            ),
            nullable=False,
            comment="Scenario type (base_case, conservative, optimistic, new_campus)",
        ),
        sa.Column(
            "name",
            sa.String(200),
            nullable=False,
            comment="User-friendly scenario name",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Scenario description and key assumptions",
        ),
        sa.Column(
            "enrollment_growth_rate",
            sa.Numeric(5, 4),
            nullable=False,
            comment="Annual enrollment growth rate (e.g., 0.04 = 4% per year)",
        ),
        sa.Column(
            "fee_increase_rate",
            sa.Numeric(5, 4),
            nullable=False,
            comment="Annual fee increase rate (e.g., 0.03 = 3% per year)",
        ),
        sa.Column(
            "salary_inflation_rate",
            sa.Numeric(5, 4),
            nullable=False,
            comment="Annual salary inflation rate (e.g., 0.035 = 3.5% per year)",
        ),
        sa.Column(
            "operating_inflation_rate",
            sa.Numeric(5, 4),
            nullable=False,
            comment="Annual operating cost inflation rate (e.g., 0.025 = 2.5% per year)",
        ),
        sa.Column(
            "additional_assumptions",
            postgresql.JSONB(),
            nullable=True,
            comment="Additional scenario-specific assumptions",
        ),
        # Audit columns (BaseModel)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Last update timestamp",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who created this record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who last updated this record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp",
        ),
        # Constraints
        sa.UniqueConstraint(
            "strategic_plan_id",
            "scenario_type",
            name="uk_strategic_scenario_plan_type",
        ),
        sa.CheckConstraint(
            "enrollment_growth_rate >= -0.50 AND enrollment_growth_rate <= 1.00",
            name="ck_scenario_enrollment_growth_range",
        ),
        sa.CheckConstraint(
            "fee_increase_rate >= -0.20 AND fee_increase_rate <= 0.50",
            name="ck_scenario_fee_increase_range",
        ),
        sa.CheckConstraint(
            "salary_inflation_rate >= -0.20 AND salary_inflation_rate <= 0.50",
            name="ck_scenario_salary_inflation_range",
        ),
        sa.CheckConstraint(
            "operating_inflation_rate >= -0.20 AND operating_inflation_rate <= 0.50",
            name="ck_scenario_operating_inflation_range",
        ),
        schema="efir_budget",
    )

    # Indexes for strategic_plan_scenarios
    op.create_index(
        "ix_strategic_plan_scenarios_strategic_plan_id",
        "strategic_plan_scenarios",
        ["strategic_plan_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_plan_scenarios_scenario_type",
        "strategic_plan_scenarios",
        ["scenario_type"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_scenario_plan_type",
        "strategic_plan_scenarios",
        ["strategic_plan_id", "scenario_type"],
        unique=False,
        schema="efir_budget",
    )

    # ========================================================================
    # Module 18: Strategic Planning - strategic_plan_projections
    # ========================================================================

    op.create_table(
        "strategic_plan_projections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "strategic_plan_scenario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "efir_budget.strategic_plan_scenarios.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            comment="Scenario this projection belongs to",
        ),
        sa.Column(
            "year",
            sa.Integer(),
            nullable=False,
            comment="Year in strategic plan (1-5, where 1 = base_year)",
        ),
        sa.Column(
            "category",
            postgresql.ENUM(
                "revenue",
                "personnel_costs",
                "operating_costs",
                "capex",
                "depreciation",
                name="projectioncategory",
                schema="efir_budget",
            ),
            nullable=False,
            comment="Projection category",
        ),
        sa.Column(
            "amount_sar",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Projected amount in SAR for this year and category",
        ),
        sa.Column(
            "calculation_inputs",
            postgresql.JSONB(),
            nullable=True,
            comment="Inputs used in projection calculation",
        ),
        # Audit columns (BaseModel)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Last update timestamp",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who created this record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who last updated this record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp",
        ),
        # Constraints
        sa.UniqueConstraint(
            "strategic_plan_scenario_id",
            "year",
            "category",
            name="uk_strategic_projection_scenario_year_category",
        ),
        sa.CheckConstraint(
            "year >= 1 AND year <= 5",
            name="ck_projection_year_range",
        ),
        sa.CheckConstraint(
            "amount_sar >= 0",
            name="ck_projection_amount_positive",
        ),
        schema="efir_budget",
    )

    # Indexes for strategic_plan_projections
    op.create_index(
        "ix_strategic_plan_projections_scenario_id",
        "strategic_plan_projections",
        ["strategic_plan_scenario_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_plan_projections_year",
        "strategic_plan_projections",
        ["year"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_plan_projections_category",
        "strategic_plan_projections",
        ["category"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_projection_scenario_year",
        "strategic_plan_projections",
        ["strategic_plan_scenario_id", "year"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 18: Strategic Planning - strategic_initiatives
    # ========================================================================

    op.create_table(
        "strategic_initiatives",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "strategic_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "efir_budget.strategic_plans.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            comment="Strategic plan this initiative belongs to",
        ),
        sa.Column(
            "name",
            sa.String(200),
            nullable=False,
            comment="Initiative name",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Initiative description, objectives, and deliverables",
        ),
        sa.Column(
            "planned_year",
            sa.Integer(),
            nullable=False,
            comment="Year in strategic plan when initiative is planned (1-5)",
        ),
        sa.Column(
            "capex_amount_sar",
            sa.Numeric(15, 2),
            nullable=False,
            server_default="0.00",
            comment="One-time capital expenditure in SAR",
        ),
        sa.Column(
            "operating_impact_sar",
            sa.Numeric(15, 2),
            nullable=False,
            server_default="0.00",
            comment="Annual operating cost impact in SAR",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "planned",
                "approved",
                "in_progress",
                "completed",
                "cancelled",
                name="initiativestatus",
                schema="efir_budget",
            ),
            nullable=False,
            server_default="planned",
            comment="Initiative status",
        ),
        sa.Column(
            "additional_details",
            postgresql.JSONB(),
            nullable=True,
            comment="Additional initiative details",
        ),
        # Audit columns (BaseModel)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Last update timestamp",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who created this record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who last updated this record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp",
        ),
        # Constraints
        sa.CheckConstraint(
            "planned_year >= 1 AND planned_year <= 5",
            name="ck_initiative_year_range",
        ),
        sa.CheckConstraint(
            "capex_amount_sar >= 0",
            name="ck_initiative_capex_positive",
        ),
        schema="efir_budget",
    )

    # Indexes for strategic_initiatives
    op.create_index(
        "ix_strategic_initiatives_strategic_plan_id",
        "strategic_initiatives",
        ["strategic_plan_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_initiatives_name",
        "strategic_initiatives",
        ["name"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_initiatives_planned_year",
        "strategic_initiatives",
        ["planned_year"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_initiatives_status",
        "strategic_initiatives",
        ["status"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_strategic_initiative_plan_year",
        "strategic_initiatives",
        ["strategic_plan_id", "planned_year"],
        schema="efir_budget",
    )

    # ========================================================================
    # Apply updated_at Triggers
    # ========================================================================

    op.execute(
        """
        CREATE TRIGGER set_updated_at_strategic_plans
        BEFORE UPDATE ON efir_budget.strategic_plans
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_strategic_plan_scenarios
        BEFORE UPDATE ON efir_budget.strategic_plan_scenarios
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_strategic_plan_projections
        BEFORE UPDATE ON efir_budget.strategic_plan_projections
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_strategic_initiatives
        BEFORE UPDATE ON efir_budget.strategic_initiatives
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )


def downgrade() -> None:
    """Drop Strategic Layer tables."""

    # Drop triggers (reverse order)
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_strategic_initiatives "
        "ON efir_budget.strategic_initiatives;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_strategic_plan_projections "
        "ON efir_budget.strategic_plan_projections;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_strategic_plan_scenarios "
        "ON efir_budget.strategic_plan_scenarios;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_strategic_plans "
        "ON efir_budget.strategic_plans;"
    )

    # Drop tables (reverse creation order)
    op.drop_table("strategic_initiatives", schema="efir_budget")
    op.drop_table("strategic_plan_projections", schema="efir_budget")
    op.drop_table("strategic_plan_scenarios", schema="efir_budget")
    op.drop_table("strategic_plans", schema="efir_budget")

    # Drop enum types (reverse creation order)
    op.execute("DROP TYPE IF EXISTS efir_budget.projectioncategory;")
    op.execute("DROP TYPE IF EXISTS efir_budget.initiativestatus;")
    op.execute("DROP TYPE IF EXISTS efir_budget.scenariotype;")
