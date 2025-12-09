"""Consolidation Layer: Budget Consolidation and Financial Statements (Modules 13-14)

Revision ID: 003_consolidation_layer
Revises: 002_planning_layer
Create Date: 2025-12-01 00:30:00

Creates tables for Consolidation Layer:
- Module 13: Budget Consolidation
  - budget_consolidations: Aggregated revenues and costs by account code

- Module 14: Financial Statements
  - financial_statements: Statement headers (Income Statement, Balance Sheet)
  - financial_statement_lines: Statement line items with hierarchy

Business Purpose:
-----------------
1. Consolidate all Planning Layer data into unified budget view
2. Generate formal financial statements in French PCG or IFRS format
3. Support version comparison (approved vs working, budget vs actual)
4. Provide foundation for management reporting and analysis

Dependencies:
-------------
- Requires: 002_planning_layer (Planning Layer must exist)
- Creates: 3 tables with enums and constraints
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_consolidation_layer"
down_revision: str | None = "002_planning_layer"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Consolidation Layer tables."""

    # ========================================================================
    # Create Enum Types
    # ========================================================================

    # ConsolidationCategory enum
    consolidation_category = postgresql.ENUM(
        "revenue_tuition",
        "revenue_fees",
        "revenue_other",
        "personnel_teaching",
        "personnel_admin",
        "personnel_support",
        "personnel_social",
        "operating_supplies",
        "operating_utilities",
        "operating_maintenance",
        "operating_insurance",
        "operating_other",
        "capex_equipment",
        "capex_it",
        "capex_furniture",
        "capex_building",
        "capex_software",
        name="consolidationcategory",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    consolidation_category.create(op.get_bind(), checkfirst=True)

    # StatementType enum
    statement_type = postgresql.ENUM(
        "income_statement",
        "balance_sheet_assets",
        "balance_sheet_liabilities",
        "cash_flow",
        name="statementtype",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    statement_type.create(op.get_bind(), checkfirst=True)

    # StatementFormat enum
    statement_format = postgresql.ENUM(
        "french_pcg",
        "ifrs",
        name="statementformat",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    statement_format.create(op.get_bind(), checkfirst=True)

    # LineType enum
    line_type = postgresql.ENUM(
        "section_header",
        "account_group",
        "account_line",
        "subtotal",
        "total",
        name="linetype",
        schema="efir_budget",
        create_type=False,  # Prevent auto-creation when used in Column
    )
    line_type.create(op.get_bind(), checkfirst=True)

    # ========================================================================
    # Module 13: Budget Consolidation
    # ========================================================================

    op.create_table(
        "budget_consolidations",
        # Primary Key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        # Foreign Keys
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            comment="Budget version this consolidation belongs to",
        ),
        # Account Information
        sa.Column(
            "account_code",
            sa.String(10),
            nullable=False,
            comment="French PCG account code (e.g., 70110, 64110)",
        ),
        sa.Column(
            "account_name",
            sa.String(200),
            nullable=False,
            comment="Account name (e.g., 'Scolarité T1', 'Salaires enseignants')",
        ),
        sa.Column(
            "consolidation_category",
            consolidation_category,  # Use already-created enum variable
            nullable=False,
            comment="Grouping category for reporting",
        ),
        sa.Column(
            "is_revenue",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="True if revenue (70xxx-77xxx), False if expense (60xxx-68xxx)",
        ),
        # Amounts
        sa.Column(
            "amount_sar",
            sa.Numeric(15, 2),
            nullable=False,
            server_default="0.00",
            comment="Total amount in SAR (aggregated from source tables)",
        ),
        # Calculation Metadata
        sa.Column(
            "source_table",
            sa.String(50),
            nullable=False,
            comment="Source table name (revenue_plans, personnel_cost_plans, etc.)",
        ),
        sa.Column(
            "source_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Number of source records aggregated",
        ),
        sa.Column(
            "is_calculated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="True if auto-calculated, False if manual override",
        ),
        # Optional Notes
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Optional notes or explanations for this consolidation line",
        ),
        # Audit Fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Record creation timestamp",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created this record",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Last update timestamp",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
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
            "budget_version_id",
            "account_code",
            name="uk_consolidation_version_account",
        ),
        sa.CheckConstraint(
            "amount_sar >= 0 OR is_revenue = false",
            name="ck_consolidation_revenue_positive",
        ),
        schema="efir_budget",
        comment="Budget consolidation - aggregates all revenues and costs by account code",
    )

    # Create indexes
    op.create_index(
        "ix_efir_budget_budget_consolidations_budget_version_id",
        "budget_consolidations",
        ["budget_version_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_budget_consolidations_account_code",
        "budget_consolidations",
        ["account_code"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_budget_consolidations_consolidation_category",
        "budget_consolidations",
        ["consolidation_category"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_budget_consolidations_is_revenue",
        "budget_consolidations",
        ["is_revenue"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 14: Financial Statements (Header)
    # ========================================================================

    op.create_table(
        "financial_statements",
        # Primary Key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        # Foreign Keys
        sa.Column(
            "budget_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            comment="Budget version this statement belongs to",
        ),
        # Statement Configuration
        sa.Column(
            "statement_type",
            statement_type,  # Use already-created enum variable
            nullable=False,
            comment="Type of financial statement",
        ),
        sa.Column(
            "statement_format",
            statement_format,  # Use already-created enum variable
            nullable=False,
            comment="Accounting standard format",
        ),
        sa.Column(
            "statement_name",
            sa.String(200),
            nullable=False,
            comment="Statement name (e.g., 'Compte de résultat 2025-2026')",
        ),
        # Period Information
        sa.Column(
            "fiscal_year",
            sa.Integer(),
            nullable=False,
            comment="Fiscal year (e.g., 2025 for 2025-2026)",
        ),
        # Summary Totals
        sa.Column(
            "total_amount_sar",
            sa.Numeric(15, 2),
            nullable=False,
            server_default="0.00",
            comment="Total statement amount (net result or total assets/liabilities)",
        ),
        # Metadata
        sa.Column(
            "is_calculated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="True if auto-calculated, False if manual",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Optional notes for this statement",
        ),
        # Audit Fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Record creation timestamp",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created this record",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Last update timestamp",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
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
            "budget_version_id",
            "statement_type",
            "statement_format",
            name="uk_statement_version_type_format",
        ),
        schema="efir_budget",
        comment="Financial statement header (Income Statement, Balance Sheet, Cash Flow)",
    )

    # Create indexes
    op.create_index(
        "ix_efir_budget_financial_statements_budget_version_id",
        "financial_statements",
        ["budget_version_id"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_financial_statements_statement_type",
        "financial_statements",
        ["statement_type"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_financial_statements_statement_format",
        "financial_statements",
        ["statement_format"],
        schema="efir_budget",
    )
    op.create_index(
        "ix_efir_budget_financial_statements_fiscal_year",
        "financial_statements",
        ["fiscal_year"],
        schema="efir_budget",
    )

    # ========================================================================
    # Module 14: Financial Statement Lines
    # ========================================================================

    op.create_table(
        "financial_statement_lines",
        # Primary Key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            comment="Primary key (UUID)",
        ),
        # Foreign Keys
        sa.Column(
            "statement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("efir_budget.financial_statements.id", ondelete="CASCADE"),
            nullable=False,
            comment="Financial statement this line belongs to",
        ),
        # Line Structure
        sa.Column(
            "line_number",
            sa.Integer(),
            nullable=False,
            comment="Sequential line number for ordering (1, 2, 3, ...)",
        ),
        sa.Column(
            "line_type",
            line_type,  # Use already-created enum variable
            nullable=False,
            comment="Type of line (header, account, subtotal, total)",
        ),
        sa.Column(
            "indent_level",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Indentation level (0-3) for hierarchy display",
        ),
        # Line Content
        sa.Column(
            "line_code",
            sa.String(10),
            nullable=True,
            comment="Account code or section code (e.g., '70', '701', '64110')",
        ),
        sa.Column(
            "line_description",
            sa.String(200),
            nullable=False,
            comment="Line description (e.g., 'Scolarité', 'Total Produits')",
        ),
        sa.Column(
            "amount_sar",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Amount in SAR (null for headers without amounts)",
        ),
        # Display Formatting
        sa.Column(
            "is_bold",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="True if line should be displayed in bold",
        ),
        sa.Column(
            "is_underlined",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="True if line should be underlined (for totals)",
        ),
        # Source Traceability
        sa.Column(
            "source_consolidation_category",
            sa.String(50),
            nullable=True,
            comment="Source consolidation category (if applicable)",
        ),
        # Audit Fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Record creation timestamp",
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who created this record",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Last update timestamp",
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
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
            "statement_id",
            "line_number",
            name="uk_statement_line_number",
        ),
        sa.CheckConstraint(
            "indent_level >= 0 AND indent_level <= 3",
            name="ck_statement_line_indent",
        ),
        sa.CheckConstraint(
            "line_number > 0",
            name="ck_statement_line_number_positive",
        ),
        schema="efir_budget",
        comment="Individual line item in a financial statement",
    )

    # Create indexes
    op.create_index(
        "ix_efir_budget_financial_statement_lines_statement_id",
        "financial_statement_lines",
        ["statement_id"],
        schema="efir_budget",
    )

    # ========================================================================
    # Apply updated_at Trigger to All Tables
    # ========================================================================

    # Trigger for budget_consolidations
    op.execute(
        """
        CREATE TRIGGER set_updated_at_budget_consolidations
        BEFORE UPDATE ON efir_budget.budget_consolidations
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    # Trigger for financial_statements
    op.execute(
        """
        CREATE TRIGGER set_updated_at_financial_statements
        BEFORE UPDATE ON efir_budget.financial_statements
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )

    # Trigger for financial_statement_lines
    op.execute(
        """
        CREATE TRIGGER set_updated_at_financial_statement_lines
        BEFORE UPDATE ON efir_budget.financial_statement_lines
        FOR EACH ROW
        EXECUTE FUNCTION efir_budget.update_updated_at();
        """
    )


def downgrade() -> None:
    """Drop Consolidation Layer tables."""

    # Drop triggers
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_financial_statement_lines "
        "ON efir_budget.financial_statement_lines;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_financial_statements "
        "ON efir_budget.financial_statements;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_updated_at_budget_consolidations "
        "ON efir_budget.budget_consolidations;"
    )

    # Drop tables (in reverse dependency order)
    op.drop_table("financial_statement_lines", schema="efir_budget")
    op.drop_table("financial_statements", schema="efir_budget")
    op.drop_table("budget_consolidations", schema="efir_budget")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS efir_budget.linetype;")
    op.execute("DROP TYPE IF EXISTS efir_budget.statementformat;")
    op.execute("DROP TYPE IF EXISTS efir_budget.statementtype;")
    op.execute("DROP TYPE IF EXISTS efir_budget.consolidationcategory;")
