"""Historical Comparison: Add historical actuals for planning comparison.

Revision ID: 014_historical_comparison
Revises: 013_seed_subjects
Create Date: 2025-12-06 18:00:00.000000

Creates tables for historical comparison feature:
- historical_actuals: Annual historical data by module and dimension
- mv_annual_actuals: Materialized view for fast annual aggregations

Business Purpose:
-----------------
Enable comparison of current budget planning against 2 years of historical
actuals (N-2, N-1) in all 6 planning grids. Supports:
- Enrollment: Historical student counts by level
- DHG: Historical teacher FTE by subject
- Revenue: Historical revenue by account code
- Costs: Historical costs by account code and category
- CapEx: Historical capital expenditures by category

Data Source:
------------
Historical data is initially loaded via manual Excel import, with annual
refresh mechanism. Financial actuals can also be aggregated from actual_data.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = "014_historical_comparison"
down_revision: str | None = "013_seed_subjects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create historical comparison tables and materialized view."""

    # =========================================================================
    # Create HistoricalModuleCode enum for type safety
    # =========================================================================

    historical_module_code = postgresql.ENUM(
        "enrollment",
        "class_structure",
        "dhg",
        "revenue",
        "costs",
        "capex",
        name="historicalmodulecode",
        schema="efir_budget",
        create_type=False,
    )
    historical_module_code.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create HistoricalDimensionType enum
    # =========================================================================

    historical_dimension_type = postgresql.ENUM(
        "level",  # For enrollment (level_id)
        "subject",  # For DHG (subject_code)
        "account_code",  # For revenue/costs/capex
        "cost_category",  # For costs breakdown
        "teacher_category",  # For DHG (AEFE, local, etc.)
        "nationality",  # For enrollment nationality distribution
        "fee_type",  # For revenue by fee type
        name="historicaldimensiontype",
        schema="efir_budget",
        create_type=False,
    )
    historical_dimension_type.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create HistoricalDataSource enum
    # =========================================================================

    historical_data_source = postgresql.ENUM(
        "odoo_import",
        "manual_upload",
        "skolengo_import",
        "system_aggregation",
        name="historicaldatasource",
        schema="efir_budget",
        create_type=False,
    )
    historical_data_source.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create historical_actuals table
    # =========================================================================

    op.create_table(
        "historical_actuals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="Primary key (UUID)",
        ),
        sa.Column(
            "fiscal_year",
            sa.Integer(),
            nullable=False,
            comment="Fiscal year of historical data (e.g., 2024 for FY 2024-2025)",
        ),
        sa.Column(
            "module_code",
            historical_module_code,
            nullable=False,
            comment="Module identifier: enrollment, dhg, revenue, costs, capex",
        ),
        sa.Column(
            "dimension_type",
            historical_dimension_type,
            nullable=False,
            comment="Type of dimension: level, subject, account_code, etc.",
        ),
        sa.Column(
            "dimension_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Reference UUID (level_id, subject_id, etc.) if applicable",
        ),
        sa.Column(
            "dimension_code",
            sa.String(50),
            nullable=False,
            comment="Human-readable code (level_code, account_code, subject_code)",
        ),
        sa.Column(
            "dimension_name",
            sa.String(200),
            nullable=True,
            comment="Human-readable name for display purposes",
        ),
        # Numeric value columns (use appropriate one based on module)
        sa.Column(
            "annual_amount_sar",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Annual monetary amount in SAR (for revenue, costs, capex)",
        ),
        sa.Column(
            "annual_count",
            sa.Integer(),
            nullable=True,
            comment="Annual count value (for enrollment student counts)",
        ),
        sa.Column(
            "annual_fte",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Annual FTE value (for DHG teacher allocations)",
        ),
        sa.Column(
            "annual_hours",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Annual hours value (for DHG subject hours)",
        ),
        sa.Column(
            "annual_classes",
            sa.Integer(),
            nullable=True,
            comment="Annual class count (for class_structure)",
        ),
        # Metadata columns
        sa.Column(
            "data_source",
            historical_data_source,
            nullable=False,
            server_default=sa.text("'manual_upload'"),
            comment="Source of historical data (odoo_import, manual_upload, etc.)",
        ),
        sa.Column(
            "import_batch_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Batch identifier for grouped imports",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Optional notes about this historical data point",
        ),
        # Audit columns
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
        # Constraints
        sa.UniqueConstraint(
            "fiscal_year",
            "module_code",
            "dimension_type",
            "dimension_code",
            name="uk_historical_year_module_dim",
        ),
        sa.CheckConstraint(
            "fiscal_year >= 2020 AND fiscal_year <= 2099",
            name="ck_historical_fiscal_year_range",
        ),
        sa.CheckConstraint(
            "(annual_amount_sar IS NOT NULL) OR (annual_count IS NOT NULL) OR "
            "(annual_fte IS NOT NULL) OR (annual_hours IS NOT NULL) OR (annual_classes IS NOT NULL)",
            name="ck_historical_has_value",
        ),
        schema="efir_budget",
        comment="Historical actuals for planning comparison (N-2, N-1 data)",
    )

    # =========================================================================
    # Create Indexes for historical_actuals
    # =========================================================================

    # Primary lookup index (most common query pattern)
    op.create_index(
        "ix_historical_lookup",
        "historical_actuals",
        ["fiscal_year", "module_code", "dimension_type"],
        schema="efir_budget",
    )

    # Index for fetching by module across years
    op.create_index(
        "ix_historical_module_year",
        "historical_actuals",
        ["module_code", "fiscal_year"],
        schema="efir_budget",
    )

    # Index for dimension code lookup
    op.create_index(
        "ix_historical_dimension_code",
        "historical_actuals",
        ["dimension_code"],
        schema="efir_budget",
    )

    # Index for import batch tracking
    op.create_index(
        "ix_historical_import_batch",
        "historical_actuals",
        ["import_batch_id"],
        schema="efir_budget",
    )

    # Soft delete filter index
    op.create_index(
        "ix_historical_deleted_at",
        "historical_actuals",
        ["deleted_at"],
        schema="efir_budget",
    )

    # =========================================================================
    # Create Materialized View for Annual Actuals from actual_data
    # =========================================================================

    # This view aggregates financial actuals by fiscal year and account code
    # for quick comparison with historical_actuals
    op.execute(
        """
        CREATE MATERIALIZED VIEW efir_budget.mv_annual_actuals AS
        SELECT
            fiscal_year,
            account_code,
            account_name,
            SUM(amount_sar) AS annual_amount_sar,
            COUNT(*) AS transaction_count,
            MIN(import_date) AS first_import_date,
            MAX(import_date) AS last_import_date
        FROM efir_budget.actual_data
        WHERE deleted_at IS NULL
          AND period = 0  -- Annual totals only (0 represents full year)
        GROUP BY fiscal_year, account_code, account_name

        UNION ALL

        -- Also aggregate from monthly data if annual not available
        SELECT
            fiscal_year,
            account_code,
            MAX(account_name) AS account_name,
            SUM(amount_sar) AS annual_amount_sar,
            COUNT(*) AS transaction_count,
            MIN(import_date) AS first_import_date,
            MAX(import_date) AS last_import_date
        FROM efir_budget.actual_data
        WHERE deleted_at IS NULL
          AND period > 0  -- Monthly data
          AND fiscal_year NOT IN (
              SELECT DISTINCT fiscal_year
              FROM efir_budget.actual_data
              WHERE deleted_at IS NULL AND period = 0
          )
        GROUP BY fiscal_year, account_code
        WITH DATA;
        """
    )

    # Create unique index on materialized view for REFRESH CONCURRENTLY
    op.execute(
        """
        CREATE UNIQUE INDEX ix_mv_annual_actuals_pk
        ON efir_budget.mv_annual_actuals (fiscal_year, account_code);
        """
    )

    # Create additional index for faster lookups
    op.execute(
        """
        CREATE INDEX ix_mv_annual_actuals_year
        ON efir_budget.mv_annual_actuals (fiscal_year);
        """
    )

    # =========================================================================
    # Create updated_at Trigger for historical_actuals
    # =========================================================================

    op.execute(
        """
        CREATE TRIGGER set_updated_at_historical_actuals
        BEFORE UPDATE ON efir_budget.historical_actuals
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    # =========================================================================
    # Create Function to Refresh Materialized View
    # =========================================================================

    op.execute(
        """
        CREATE OR REPLACE FUNCTION efir_budget.refresh_mv_annual_actuals()
        RETURNS void
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY efir_budget.mv_annual_actuals;
        END;
        $$;
        """
    )

    # Grant execute permission to authenticated users
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION efir_budget.refresh_mv_annual_actuals()
        TO authenticated;
        """
    )

    # =========================================================================
    # Enable RLS on historical_actuals
    # =========================================================================

    op.execute("ALTER TABLE efir_budget.historical_actuals ENABLE ROW LEVEL SECURITY;")

    # Policy: Allow all authenticated users to read historical data
    op.execute(
        """
        CREATE POLICY "historical_actuals_select_policy"
        ON efir_budget.historical_actuals
        FOR SELECT
        TO authenticated
        USING (deleted_at IS NULL);
        """
    )

    # Policy: Only admins can insert/update/delete historical data
    op.execute(
        """
        CREATE POLICY "historical_actuals_admin_all_policy"
        ON efir_budget.historical_actuals
        FOR ALL
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM auth.users
                WHERE id = auth.uid()
                AND raw_user_meta_data->>'role' IN ('admin', 'finance_director')
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM auth.users
                WHERE id = auth.uid()
                AND raw_user_meta_data->>'role' IN ('admin', 'finance_director')
            )
        );
        """
    )


def downgrade() -> None:
    """Drop historical comparison tables and materialized view."""

    # Drop RLS policies
    op.execute(
        "DROP POLICY IF EXISTS historical_actuals_admin_all_policy "
        "ON efir_budget.historical_actuals;"
    )
    op.execute(
        "DROP POLICY IF EXISTS historical_actuals_select_policy "
        "ON efir_budget.historical_actuals;"
    )

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS efir_budget.refresh_mv_annual_actuals();")

    # Drop trigger
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_historical_actuals "
        "ON efir_budget.historical_actuals;"
    )

    # Drop materialized view and its indexes
    op.execute("DROP MATERIALIZED VIEW IF EXISTS efir_budget.mv_annual_actuals CASCADE;")

    # Drop indexes
    op.drop_index("ix_historical_deleted_at", table_name="historical_actuals", schema="efir_budget")
    op.drop_index("ix_historical_import_batch", table_name="historical_actuals", schema="efir_budget")
    op.drop_index("ix_historical_dimension_code", table_name="historical_actuals", schema="efir_budget")
    op.drop_index("ix_historical_module_year", table_name="historical_actuals", schema="efir_budget")
    op.drop_index("ix_historical_lookup", table_name="historical_actuals", schema="efir_budget")

    # Drop table
    op.drop_table("historical_actuals", schema="efir_budget")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS efir_budget.historicaldatasource;")
    op.execute("DROP TYPE IF EXISTS efir_budget.historicaldimensiontype;")
    op.execute("DROP TYPE IF EXISTS efir_budget.historicalmodulecode;")
