"""Analysis Layer: KPIs, Dashboards, and Budget vs Actual (Modules 15-17)

Revision ID: 005_analysis_layer
Revises: 004_fix_critical_issues
Create Date: 2025-12-01 00:57:00.000000

Creates Analysis Layer tables:
- Module 15: Statistical Analysis (kpi_definitions, kpi_values)
- Module 16: Dashboard Configuration (dashboard_configs, dashboard_widgets, user_preferences)
- Module 17: Budget vs Actual Analysis (actual_data, budget_vs_actual, variance_explanations)

Business Purpose:
-----------------
1. Calculate and track Key Performance Indicators (KPIs) for budget analysis
2. Provide customizable dashboards for different user roles
3. Enable variance analysis comparing budgeted vs actual amounts from Odoo
4. Support data-driven decision making and performance monitoring

Dependencies:
-------------
- Requires: 20251201_0045_fix_critical_issues (Phase 3 fixes)
- Creates: 8 tables with 5 enum types and comprehensive constraints
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = "005_analysis_layer"
down_revision: str | None = "004_fix_critical_issues"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Analysis Layer tables."""

    # ========================================================================
    # Create Enum Types
    # ========================================================================

    # Module 15: KPICategory enum
    kpi_category = postgresql.ENUM(
        "educational",
        "financial",
        "operational",
        "strategic",
        name="kpicategory",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    kpi_category.create(op.get_bind(), checkfirst=True)

    # Module 16: WidgetType enum
    widget_type = postgresql.ENUM(
        "kpi_card",
        "chart",
        "table",
        "variance_table",
        "waterfall",
        "gauge",
        "timeline",
        "heatmap",
        name="widgettype",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    widget_type.create(op.get_bind(), checkfirst=True)

    # Module 16: DashboardRole enum
    dashboard_role = postgresql.ENUM(
        "executive",
        "finance_manager",
        "department",
        "operations",
        name="dashboardrole",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    dashboard_role.create(op.get_bind(), checkfirst=True)

    # Module 17: VarianceStatus enum
    variance_status = postgresql.ENUM(
        "favorable",
        "unfavorable",
        "neutral",
        "not_applicable",
        name="variancestatus",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    variance_status.create(op.get_bind(), checkfirst=True)

    # Module 17: ActualDataSource enum
    actual_data_source = postgresql.ENUM(
        "odoo_import",
        "manual_entry",
        "system_calc",
        name="actualdatasource",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    actual_data_source.create(op.get_bind(), checkfirst=True)

    # ========================================================================
    # Module 15: Statistical Analysis - kpi_definitions (Reference Data)
    # ========================================================================

    op.create_table(
        "kpi_definitions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "code",
            sa.String(50),
            nullable=False,
            comment="Unique KPI code (e.g., 'H_E_RATIO', 'STAFF_COST_PCT')",
        ),
        sa.Column(
            "name_en",
            sa.String(200),
            nullable=False,
            comment="KPI name in English",
        ),
        sa.Column(
            "name_fr",
            sa.String(200),
            nullable=False,
            comment="KPI name in French",
        ),
        sa.Column(
            "category",
            kpi_category,  # Use already-created enum variable
            nullable=False,
            comment="KPI category for grouping",
        ),
        sa.Column(
            "formula_text",
            sa.Text(),
            nullable=False,
            comment="Human-readable formula",
        ),
        sa.Column(
            "unit",
            sa.String(20),
            nullable=False,
            comment="Unit of measure (ratio, percentage, currency, count, hours)",
        ),
        sa.Column(
            "target_value",
            sa.Numeric(15, 4),
            nullable=True,
            comment="Target benchmark value",
        ),
        sa.Column(
            "min_acceptable",
            sa.Numeric(15, 4),
            nullable=True,
            comment="Minimum acceptable value (lower bound)",
        ),
        sa.Column(
            "max_acceptable",
            sa.Numeric(15, 4),
            nullable=True,
            comment="Maximum acceptable value (upper bound)",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether this KPI is actively calculated",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Detailed description and interpretation guide",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created the record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who last updated the record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        sa.UniqueConstraint("code", name="uk_kpi_definition_code"),
        sa.CheckConstraint("target_value >= 0", name="ck_kpi_target_positive"),
        schema="efir_budget",
        comment="KPI metadata catalog with formulas and targets",
    )

    # Create indexes for kpi_definitions
    op.create_index(
        "ix_efir_budget_kpi_definitions_code",
        "kpi_definitions",
        ["code"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_kpi_definitions_category",
        "kpi_definitions",
        ["category"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 15: Statistical Analysis - kpi_values (Versioned)
    # ========================================================================

    op.create_table(
        "kpi_values",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            comment="Budget version this record belongs to",
        ),
        sa.Column(
            "kpi_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.kpi_definitions.id"),
            nullable=False,
            comment="KPI being calculated",
        ),
        sa.Column(
            "calculated_value",
            sa.Numeric(15, 4),
            nullable=False,
            comment="Calculated KPI value",
        ),
        sa.Column(
            "variance_from_target",
            sa.Numeric(15, 4),
            nullable=True,
            comment="Variance from target (calculated - target)",
        ),
        sa.Column(
            "variance_percent",
            sa.Numeric(8, 2),
            nullable=True,
            comment="Variance as percentage",
        ),
        sa.Column(
            "calculation_inputs",
            postgresql.JSONB(),
            nullable=False,
            comment="Inputs used for calculation (audit trail)",
        ),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When KPI was calculated",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Optional notes or interpretation",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created the record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who last updated the record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        sa.UniqueConstraint(
            "budget_version_id",
            "kpi_definition_id",
            name="uk_kpi_value_version_definition",
        ),
        sa.CheckConstraint(
            "calculated_value IS NOT NULL",
            name="ck_kpi_value_calculated_not_null",
        ),
        schema="efir_budget",
        comment="KPI calculated values per budget version",
    )

    # Create indexes for kpi_values
    op.create_index(
        "ix_efir_budget_kpi_values_budget_version_id",
        "kpi_values",
        ["budget_version_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_kpi_values_kpi_definition_id",
        "kpi_values",
        ["kpi_definition_id"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 16: Dashboard Configuration - dashboard_configs
    # ========================================================================

    op.create_table(
        "dashboard_configs",
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
            comment="Dashboard name",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Dashboard purpose and contents",
        ),
        sa.Column(
            "dashboard_role",
            dashboard_role,  # Use already-created enum variable
            nullable=True,
            comment="Role for system templates (NULL for user custom)",
        ),
        sa.Column(
            "is_system_template",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="True for pre-defined templates, False for user custom",
        ),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=True,
            comment="Owner user (NULL for system templates)",
        ),
        sa.Column(
            "is_public",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Whether dashboard is visible to other users",
        ),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Default dashboard for role or user",
        ),
        sa.Column(
            "layout_config",
            postgresql.JSONB(),
            nullable=False,
            comment="Grid layout configuration (12×12 grid, gap size, etc.)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created the record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who last updated the record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        sa.UniqueConstraint(
            "owner_user_id",
            "name",
            name="uk_dashboard_owner_name",
        ),
        sa.UniqueConstraint(
            "dashboard_role",
            name="uk_dashboard_role_template",
        ),
        sa.CheckConstraint(
            "((is_system_template = true) AND dashboard_role IS NOT NULL AND owner_user_id IS NULL) "
            "OR ((is_system_template = false) AND dashboard_role IS NULL AND owner_user_id IS NOT NULL)",
            name="ck_dashboard_system_or_user",
        ),
        schema="efir_budget",
        comment="Dashboard definitions (system templates + user custom dashboards)",
    )

    # Create indexes for dashboard_configs
    op.create_index(
        "ix_efir_budget_dashboard_configs_dashboard_role",
        "dashboard_configs",
        ["dashboard_role"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_dashboard_configs_is_system_template",
        "dashboard_configs",
        ["is_system_template"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_dashboard_configs_owner_user_id",
        "dashboard_configs",
        ["owner_user_id"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 16: Dashboard Configuration - dashboard_widgets
    # ========================================================================

    op.create_table(
        "dashboard_widgets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "dashboard_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.dashboard_configs.id", ondelete="CASCADE"),
            nullable=False,
            comment="Parent dashboard",
        ),
        sa.Column(
            "widget_type",
            widget_type,  # Use already-created enum variable
            nullable=False,
            comment="Type of widget",
        ),
        sa.Column(
            "title",
            sa.String(200),
            nullable=False,
            comment="Widget title displayed to user",
        ),
        sa.Column(
            "data_source_query",
            sa.Text(),
            nullable=False,
            comment="Query identifier or API endpoint for data",
        ),
        sa.Column(
            "widget_config",
            postgresql.JSONB(),
            nullable=False,
            comment="Widget-specific configuration (type-dependent)",
        ),
        sa.Column(
            "position_x",
            sa.Integer(),
            nullable=False,
            comment="Grid position X (0-11, left to right)",
        ),
        sa.Column(
            "position_y",
            sa.Integer(),
            nullable=False,
            comment="Grid position Y (0+, top to bottom)",
        ),
        sa.Column(
            "width",
            sa.Integer(),
            nullable=False,
            comment="Widget width in grid columns (1-12)",
        ),
        sa.Column(
            "height",
            sa.Integer(),
            nullable=False,
            comment="Widget height in grid rows (1-10)",
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="Display order within dashboard",
        ),
        sa.Column(
            "refresh_interval_seconds",
            sa.Integer(),
            nullable=True,
            comment="Auto-refresh interval in seconds (NULL = no auto-refresh)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created the record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who last updated the record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        sa.CheckConstraint(
            "position_x >= 0 AND position_x < 12",
            name="ck_widget_position_x",
        ),
        sa.CheckConstraint(
            "position_y >= 0",
            name="ck_widget_position_y",
        ),
        sa.CheckConstraint(
            "width > 0 AND width <= 12",
            name="ck_widget_width",
        ),
        sa.CheckConstraint(
            "height > 0 AND height <= 10",
            name="ck_widget_height",
        ),
        sa.CheckConstraint(
            "position_x + width <= 12",
            name="ck_widget_position_within_grid",
        ),
        sa.CheckConstraint(
            "refresh_interval_seconds >= 0",
            name="ck_widget_refresh_positive",
        ),
        schema="efir_budget",
        comment="Widget definitions within dashboards",
    )

    # Create indexes for dashboard_widgets
    op.create_index(
        "ix_efir_budget_dashboard_widgets_dashboard_config_id",
        "dashboard_widgets",
        ["dashboard_config_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_dashboard_widgets_widget_type",
        "dashboard_widgets",
        ["widget_type"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 16: Dashboard Configuration - user_preferences
    # ========================================================================

    op.create_table(
        "user_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=False,
            comment="User these preferences belong to",
        ),
        sa.Column(
            "default_dashboard_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.dashboard_configs.id", ondelete="SET NULL"),
            nullable=True,
            comment="User's default dashboard (overrides role default)",
        ),
        sa.Column(
            "theme",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'light'"),
            comment="UI theme (light, dark, auto)",
        ),
        sa.Column(
            "default_fiscal_year",
            sa.Integer(),
            nullable=True,
            comment="User's default fiscal year filter",
        ),
        sa.Column(
            "display_preferences",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Number format, language, timezone, date format",
        ),
        sa.Column(
            "notification_settings",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Email alerts, dashboard notifications, weekly summary",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created the record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who last updated the record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        sa.UniqueConstraint("user_id", name="uk_user_preferences_user_id"),
        schema="efir_budget",
        comment="User-specific preferences and settings",
    )

    # Create indexes for user_preferences
    op.create_index(
        "ix_efir_budget_user_preferences_user_id",
        "user_preferences",
        ["user_id"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 17: Budget vs Actual Analysis - actual_data
    # ========================================================================

    op.create_table(
        "actual_data",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "fiscal_year",
            sa.Integer(),
            nullable=False,
            comment="Fiscal year (e.g., 2025 for FY 2025-2026)",
        ),
        sa.Column(
            "period",
            sa.Integer(),
            nullable=False,
            comment="Month (0-12, 0 = annual total)",
        ),
        sa.Column(
            "account_code",
            sa.String(20),
            nullable=False,
            comment="French PCG account code",
        ),
        sa.Column(
            "account_name",
            sa.String(200),
            nullable=True,
            comment="Account name from Odoo",
        ),
        sa.Column(
            "amount_sar",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Actual amount in SAR",
        ),
        sa.Column(
            "currency",
            sa.String(3),
            nullable=False,
            server_default=sa.text("'SAR'"),
            comment="Original currency code (SAR, EUR, etc.)",
        ),
        sa.Column(
            "import_batch_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Batch import identifier for traceability",
        ),
        sa.Column(
            "import_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When data was imported from Odoo",
        ),
        sa.Column(
            "source",
            actual_data_source,  # Use already-created enum variable
            nullable=False,
            server_default=sa.text("'odoo_import'"),
            comment="Source of actual data",
        ),
        sa.Column(
            "transaction_date",
            sa.Date(),
            nullable=True,
            comment="Original transaction date (if single transaction)",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Transaction description from Odoo",
        ),
        sa.Column(
            "is_reconciled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Whether actual data has been validated/reconciled",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created the record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who last updated the record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        sa.CheckConstraint(
            "period >= 0 AND period <= 12",
            name="ck_actual_period_range",
        ),
        sa.CheckConstraint(
            "fiscal_year >= 2020 AND fiscal_year <= 2099",
            name="ck_actual_fiscal_year_range",
        ),
        sa.CheckConstraint(
            "amount_sar IS NOT NULL",
            name="ck_actual_amount_not_null",
        ),
        schema="efir_budget",
        comment="Actual financial data imported from Odoo GL",
    )

    # Create indexes for actual_data
    op.create_index(
        "ix_efir_budget_actual_data_fiscal_year",
        "actual_data",
        ["fiscal_year"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_actual_data_period",
        "actual_data",
        ["period"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_actual_data_account_code",
        "actual_data",
        ["account_code"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_actual_data_import_batch_id",
        "actual_data",
        ["import_batch_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_actual_data_source",
        "actual_data",
        ["source"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_actual_data_is_reconciled",
        "actual_data",
        ["is_reconciled"],
        schema="efir_budget",
    )
    # Composite index for common query pattern
    op.create_index(
        "ix_actual_data_fy_period_account",
        "actual_data",
        ["fiscal_year", "period", "account_code"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 17: Budget vs Actual Analysis - budget_vs_actual (Versioned)
    # ========================================================================

    op.create_table(
        "budget_vs_actual",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            comment="Budget version this record belongs to",
        ),
        sa.Column(
            "account_code",
            sa.String(20),
            nullable=False,
            comment="French PCG account code",
        ),
        sa.Column(
            "period",
            sa.Integer(),
            nullable=False,
            comment="Month (1-12)",
        ),
        sa.Column(
            "budget_amount_sar",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Budgeted amount from budget_consolidations",
        ),
        sa.Column(
            "actual_amount_sar",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Actual amount from actual_data (Odoo)",
        ),
        sa.Column(
            "variance_sar",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Variance (budget - actual for expenses; actual - budget for revenue)",
        ),
        sa.Column(
            "variance_percent",
            sa.Numeric(8, 2),
            nullable=False,
            comment="Variance as percentage",
        ),
        sa.Column(
            "variance_status",
            variance_status,  # Use already-created enum variable
            nullable=False,
            comment="Favorability status",
        ),
        sa.Column(
            "ytd_budget_sar",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Year-to-date budget (cumulative from period 1)",
        ),
        sa.Column(
            "ytd_actual_sar",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Year-to-date actual (cumulative from period 1)",
        ),
        sa.Column(
            "ytd_variance_sar",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Year-to-date variance",
        ),
        sa.Column(
            "is_material",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Variance exceeds materiality threshold (5% or 100K SAR)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created the record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who last updated the record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        sa.UniqueConstraint(
            "budget_version_id",
            "account_code",
            "period",
            name="uk_variance_version_account_period",
        ),
        sa.CheckConstraint(
            "period >= 1 AND period <= 12",
            name="ck_variance_period_range",
        ),
        sa.CheckConstraint(
            "budget_amount_sar IS NOT NULL AND actual_amount_sar IS NOT NULL",
            name="ck_variance_amounts_not_null",
        ),
        schema="efir_budget",
        comment="Variance analysis comparing budget to actual",
    )

    # Create indexes for budget_vs_actual
    op.create_index(
        "ix_efir_budget_budget_vs_actual_budget_version_id",
        "budget_vs_actual",
        ["budget_version_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_budget_vs_actual_account_code",
        "budget_vs_actual",
        ["account_code"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_budget_vs_actual_period",
        "budget_vs_actual",
        ["period"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_budget_vs_actual_variance_status",
        "budget_vs_actual",
        ["variance_status"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_budget_vs_actual_is_material",
        "budget_vs_actual",
        ["is_material"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 17: Budget vs Actual Analysis - variance_explanations
    # ========================================================================

    op.create_table(
        "variance_explanations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "budget_vs_actual_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_vs_actual.id", ondelete="CASCADE"),
            nullable=False,
            comment="Variance being explained",
        ),
        sa.Column(
            "explanation_text",
            sa.Text(),
            nullable=False,
            comment="Detailed explanation of variance (minimum 10 characters)",
        ),
        sa.Column(
            "root_cause",
            sa.String(100),
            nullable=False,
            comment="Root cause category (enrollment_variance, price_variance, etc.)",
        ),
        sa.Column(
            "corrective_action",
            sa.Text(),
            nullable=True,
            comment="Planned corrective action to address variance",
        ),
        sa.Column(
            "action_deadline",
            sa.Date(),
            nullable=True,
            comment="Deadline for completing corrective action",
        ),
        sa.Column(
            "is_resolved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Whether variance issue has been resolved",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="When the record was last updated",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created the record",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who last updated the record",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the record was soft-deleted (NULL if active)",
        ),
        sa.CheckConstraint(
            "explanation_text IS NOT NULL AND length(explanation_text) > 10",
            name="ck_explanation_text_required",
        ),
        schema="efir_budget",
        comment="User-provided explanations for variances",
    )

    # Create indexes for variance_explanations
    op.create_index(
        "ix_efir_budget_variance_explanations_budget_vs_actual_id",
        "variance_explanations",
        ["budget_vs_actual_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_variance_explanations_is_resolved",
        "variance_explanations",
        ["is_resolved"],
        schema="efir_budget",
    )

    # ========================================================================
    # Apply updated_at Triggers to All Tables
    # ========================================================================

    op.execute(
        """
        CREATE TRIGGER set_updated_at_kpi_definitions
        BEFORE UPDATE ON efir_budget.kpi_definitions
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_kpi_values
        BEFORE UPDATE ON efir_budget.kpi_values
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_dashboard_configs
        BEFORE UPDATE ON efir_budget.dashboard_configs
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_dashboard_widgets
        BEFORE UPDATE ON efir_budget.dashboard_widgets
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_user_preferences
        BEFORE UPDATE ON efir_budget.user_preferences
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_actual_data
        BEFORE UPDATE ON efir_budget.actual_data
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_budget_vs_actual
        BEFORE UPDATE ON efir_budget.budget_vs_actual
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at_variance_explanations
        BEFORE UPDATE ON efir_budget.variance_explanations
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )


def downgrade() -> None:
    """Drop Analysis Layer tables."""

    # Drop triggers (reverse order)
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_variance_explanations "
        "ON efir_budget.variance_explanations;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_budget_vs_actual "
        "ON efir_budget.budget_vs_actual;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_actual_data "
        "ON efir_budget.actual_data;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_user_preferences "
        "ON efir_budget.user_preferences;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_dashboard_widgets "
        "ON efir_budget.dashboard_widgets;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_dashboard_configs "
        "ON efir_budget.dashboard_configs;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_kpi_values " "ON efir_budget.kpi_values;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_kpi_definitions "
        "ON efir_budget.kpi_definitions;"
    )

    # Drop tables (reverse creation order)
    op.drop_table("variance_explanations", schema="efir_budget")
    op.drop_table("budget_vs_actual", schema="efir_budget")
    op.drop_table("actual_data", schema="efir_budget")
    op.drop_table("user_preferences", schema="efir_budget")
    op.drop_table("dashboard_widgets", schema="efir_budget")
    op.drop_table("dashboard_configs", schema="efir_budget")
    op.drop_table("kpi_values", schema="efir_budget")
    op.drop_table("kpi_definitions", schema="efir_budget")

    # Drop enum types (reverse creation order)
    op.execute("DROP TYPE IF EXISTS efir_budget.actualdatasource;")
    op.execute("DROP TYPE IF EXISTS efir_budget.variancestatus;")
    op.execute("DROP TYPE IF EXISTS efir_budget.dashboardrole;")
    op.execute("DROP TYPE IF EXISTS efir_budget.widgettype;")
    op.execute("DROP TYPE IF EXISTS efir_budget.kpicategory;")
