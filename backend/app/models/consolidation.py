"""
EFIR Budget Planning Application - Consolidation Layer Models

This module contains SQLAlchemy models for Modules 13-14:
- Module 13: Budget Consolidation (budget_consolidations)
- Module 14: Financial Statements (financial_statements, financial_statement_lines)

Author: Claude Code
Date: 2025-12-01
Version: 3.0.0
"""

from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, VersionedMixin

if TYPE_CHECKING:
    from app.models.configuration import BudgetVersion


# ============================================================================
# Module 13: Budget Consolidation
# ============================================================================


class ConsolidationCategory(str, enum.Enum):
    """Budget consolidation category for grouping."""

    REVENUE_TUITION = "revenue_tuition"  # 701xx - Tuition by trimester
    REVENUE_FEES = "revenue_fees"  # 702xx-709xx - DAI, registration, etc.
    REVENUE_OTHER = "revenue_other"  # 75xxx-77xxx - Other revenue
    PERSONNEL_TEACHING = "personnel_teaching"  # 64110-64119 - Teaching staff
    PERSONNEL_ADMIN = "personnel_admin"  # 64120-64129 - Admin staff
    PERSONNEL_SUPPORT = "personnel_support"  # 64130-64139 - Support staff
    PERSONNEL_SOCIAL = "personnel_social"  # 645xx - Social charges
    OPERATING_SUPPLIES = "operating_supplies"  # 606xx - Supplies
    OPERATING_UTILITIES = "operating_utilities"  # 6061x - Utilities
    OPERATING_MAINTENANCE = "operating_maintenance"  # 615xx - Maintenance
    OPERATING_INSURANCE = "operating_insurance"  # 616xx - Insurance
    OPERATING_OTHER = "operating_other"  # 60xxx-68xxx - Other operating
    CAPEX_EQUIPMENT = "capex_equipment"  # 2154x - Equipment
    CAPEX_IT = "capex_it"  # 2183x - IT
    CAPEX_FURNITURE = "capex_furniture"  # 2184x - Furniture
    CAPEX_BUILDING = "capex_building"  # 213xx - Building improvements
    CAPEX_SOFTWARE = "capex_software"  # 205xx - Software


class BudgetConsolidation(BaseModel, VersionedMixin):
    """
    Budget consolidation - aggregates all revenues and costs by account code.

    This is the core consolidation table that rolls up all Planning Layer data
    into a single view per budget version, providing the foundation for
    financial statements and management reporting.

    Business Logic:
    ---------------
    1. Aggregates revenue_plans by account_code
    2. Aggregates personnel_cost_plans by account_code
    3. Aggregates operating_cost_plans by account_code
    4. Aggregates capex_plans by account_code (investment, not expense)
    5. Calculates subtotals by consolidation_category
    6. Calculates net result (revenue - expenses)

    Formulas:
    ---------
    Total Revenue = Σ(revenue_plans.total_amount_sar) by account_code
    Total Personnel Costs = Σ(personnel_cost_plans.total_cost_sar) by account_code
    Total Operating Costs = Σ(operating_cost_plans.total_cost_sar) by account_code
    Total CapEx = Σ(capex_plans.total_cost_sar) by account_code

    Operating Result = Total Revenue - Total Personnel - Total Operating
    Net Result = Operating Result - Financial Expenses + Financial Income

    Example (2025-2026 Approved Budget):
    -------------------------------------
    Account 70110 (Tuition T1):
        amount_sar = 45,678,000 (from revenue_plans aggregation)
        category = revenue_tuition
        is_revenue = True

    Account 64110 (Teaching Salaries):
        amount_sar = 28,500,000 (from personnel_cost_plans aggregation)
        category = personnel_teaching
        is_revenue = False

    Operating Result = 45,678,000 - 28,500,000 - ... = X SAR
    Net Result = Operating Result - 0 + 0 = X SAR (simplified)

    Version Comparison:
    -------------------
    Compare approved vs working:
        SELECT
            a.account_code,
            a.amount_sar AS approved_amount,
            w.amount_sar AS working_amount,
            (w.amount_sar - a.amount_sar) AS variance,
            ((w.amount_sar - a.amount_sar) / a.amount_sar * 100) AS variance_pct
        FROM budget_consolidations a
        JOIN budget_consolidations w ON a.account_code = w.account_code
        WHERE a.budget_version_id = 'approved_version_id'
          AND w.budget_version_id = 'working_version_id'
    """

    __tablename__ = "budget_consolidations"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "account_code",
            name="uk_consolidation_version_account",
        ),
        CheckConstraint(
            "amount_sar >= 0 OR is_revenue = false",
            name="ck_consolidation_revenue_positive",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Note: budget_version_id is inherited from VersionedMixin

    # Account Information
    account_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="French PCG account code (e.g., 70110, 64110)",
    )
    account_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Account name (e.g., 'Scolarité T1', 'Salaires enseignants')",
    )
    consolidation_category: Mapped[ConsolidationCategory] = mapped_column(
        Enum(ConsolidationCategory, schema="efir_budget"),
        nullable=False,
        index=True,
        comment="Grouping category for reporting",
    )
    is_revenue: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True,
        comment="True if revenue (70xxx-77xxx), False if expense (60xxx-68xxx)",
    )

    # Amounts
    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total amount in SAR (aggregated from source tables)",
    )

    # Calculation Metadata
    source_table: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Source table name (revenue_plans, personnel_cost_plans, etc.)",
    )
    source_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of source records aggregated",
    )
    is_calculated: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="True if auto-calculated, False if manual override",
    )

    # Optional Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes or explanations for this consolidation line",
    )

    # Relationships
    budget_version: Mapped[BudgetVersion] = relationship(
        "BudgetVersion",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<BudgetConsolidation(account={self.account_code}, "
            f"amount={self.amount_sar:,.2f} SAR, "
            f"category={self.consolidation_category.value})>"
        )


# ============================================================================
# Module 14: Financial Statements
# ============================================================================


class StatementType(str, enum.Enum):
    """Financial statement type."""

    INCOME_STATEMENT = "income_statement"  # Compte de résultat (P&L)
    BALANCE_SHEET_ASSETS = "balance_sheet_assets"  # Bilan - Actif
    BALANCE_SHEET_LIABILITIES = "balance_sheet_liabilities"  # Bilan - Passif
    CASH_FLOW = "cash_flow"  # Tableau de flux de trésorerie


class StatementFormat(str, enum.Enum):
    """Financial statement format standard."""

    FRENCH_PCG = "french_pcg"  # French Plan Comptable Général
    IFRS = "ifrs"  # International Financial Reporting Standards


class FinancialStatement(BaseModel, VersionedMixin):
    """
    Financial statement header (Income Statement, Balance Sheet, Cash Flow).

    Generates formal financial statements in French PCG or IFRS format
    from consolidated budget data.

    Statement Types:
    ----------------
    1. Income Statement (Compte de résultat):
       - Revenues (Produits): 70xxx-77xxx
       - Expenses (Charges): 60xxx-68xxx
       - Operating Result (Résultat d'exploitation)
       - Financial Result (Résultat financier)
       - Net Result (Résultat net)

    2. Balance Sheet (Bilan):
       - Assets (Actif): Fixed assets, current assets
       - Liabilities (Passif): Equity, debt, provisions

    3. Cash Flow Statement:
       - Operating activities
       - Investing activities (CapEx)
       - Financing activities

    Example (Income Statement - French PCG Format):
    ------------------------------------------------
    PRODUITS D'EXPLOITATION:
    70 - Ventes de produits fabriqués, prestations
        701 - Scolarité                           45,678,000
        702 - Droits d'inscription                 3,200,000
        Total Produits d'Exploitation             48,878,000

    CHARGES D'EXPLOITATION:
    60 - Achats
        606 - Fournitures scolaires                  850,000
    61 - Services extérieurs
        615 - Entretien et réparations               450,000
    64 - Charges de personnel
        641 - Rémunérations du personnel          28,500,000
        645 - Charges sociales                     5,985,000
        Total Charges d'Exploitation              35,785,000

    RÉSULTAT D'EXPLOITATION                       13,093,000
    """

    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "statement_type",
            "statement_format",
            name="uk_statement_version_type_format",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Note: budget_version_id is inherited from VersionedMixin

    # Statement Configuration
    statement_type: Mapped[StatementType] = mapped_column(
        Enum(StatementType, schema="efir_budget"),
        nullable=False,
        index=True,
        comment="Type of financial statement",
    )
    statement_format: Mapped[StatementFormat] = mapped_column(
        Enum(StatementFormat, schema="efir_budget"),
        nullable=False,
        index=True,
        comment="Accounting standard format",
    )
    statement_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Statement name (e.g., 'Compte de résultat 2025-2026')",
    )

    # Period Information
    fiscal_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Fiscal year (e.g., 2025 for 2025-2026)",
    )

    # Summary Totals (calculated from lines)
    total_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total statement amount (net result or total assets/liabilities)",
    )

    # Metadata
    is_calculated: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="True if auto-calculated, False if manual",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes for this statement",
    )

    # Relationships
    budget_version: Mapped[BudgetVersion] = relationship(
        "BudgetVersion",
        lazy="selectin",
    )
    lines: Mapped[list[FinancialStatementLine]] = relationship(
        "FinancialStatementLine",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<FinancialStatement(type={self.statement_type.value}, "
            f"format={self.statement_format.value}, "
            f"FY{self.fiscal_year})>"
        )


class LineType(str, enum.Enum):
    """Financial statement line type."""

    SECTION_HEADER = "section_header"  # Section title (e.g., "PRODUITS D'EXPLOITATION")
    ACCOUNT_GROUP = "account_group"  # Account group (e.g., "70 - Ventes")
    ACCOUNT_LINE = "account_line"  # Individual account (e.g., "701 - Scolarité")
    SUBTOTAL = "subtotal"  # Subtotal line
    TOTAL = "total"  # Total line (e.g., "Total Produits", "Résultat net")


class FinancialStatementLine(BaseModel):
    """
    Individual line item in a financial statement.

    Represents a single row in the formatted financial statement, which can be:
    - Section headers (bold titles)
    - Account groups (category summaries)
    - Account lines (individual accounts with amounts)
    - Subtotals and totals

    Display Structure:
    ------------------
    Line Format (Income Statement Example):
    ```
    [indent_level] [line_code] - [line_description]    [amount_sar]

    PRODUITS D'EXPLOITATION                              (header)
      70 - Ventes de produits fabriqués                  (group)
        701 - Scolarité                    45,678,000    (account)
        702 - Droits d'inscription          3,200,000    (account)
      Total Produits d'Exploitation        48,878,000    (subtotal)

    CHARGES D'EXPLOITATION                               (header)
      64 - Charges de personnel                          (group)
        641 - Rémunérations               28,500,000    (account)
        645 - Charges sociales             5,985,000    (account)
      Total Charges d'Exploitation         35,785,000    (subtotal)

    RÉSULTAT D'EXPLOITATION                13,093,000    (total)
    ```

    Hierarchy:
    ----------
    indent_level = 0: Section headers
    indent_level = 1: Account groups
    indent_level = 2: Account lines
    indent_level = 1: Subtotals
    indent_level = 0: Grand totals
    """

    __tablename__ = "financial_statement_lines"
    __table_args__ = (
        UniqueConstraint(
            "statement_id",
            "line_number",
            name="uk_statement_line_number",
        ),
        CheckConstraint(
            "indent_level >= 0 AND indent_level <= 3",
            name="ck_statement_line_indent",
        ),
        CheckConstraint(
            "line_number > 0",
            name="ck_statement_line_number_positive",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Foreign Keys
    statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.financial_statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Financial statement this line belongs to",
    )

    # Line Structure
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential line number for ordering (1, 2, 3, ...)",
    )
    line_type: Mapped[LineType] = mapped_column(
        Enum(LineType, schema="efir_budget"),
        nullable=False,
        comment="Type of line (header, account, subtotal, total)",
    )
    indent_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Indentation level (0-3) for hierarchy display",
    )

    # Line Content
    line_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Account code or section code (e.g., '70', '701', '64110')",
    )
    line_description: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Line description (e.g., 'Scolarité', 'Total Produits')",
    )
    amount_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Amount in SAR (null for headers without amounts)",
    )

    # Display Formatting
    is_bold: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="True if line should be displayed in bold",
    )
    is_underlined: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="True if line should be underlined (for totals)",
    )

    # Source Traceability
    source_consolidation_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Source consolidation category (if applicable)",
    )

    # Relationships
    statement: Mapped[FinancialStatement] = relationship(
        "FinancialStatement",
        lazy="selectin",
        overlaps="lines",
    )

    def __repr__(self) -> str:
        """String representation."""
        amount_str = f"{self.amount_sar:,.2f}" if self.amount_sar else "N/A"
        return (
            f"<FinancialStatementLine(#{self.line_number}, "
            f"type={self.line_type.value}, "
            f"desc='{self.line_description}', "
            f"amount={amount_str} SAR)>"
        )


# ============================================================================
# End of Consolidation Layer Models
# ============================================================================
