"""
EFIR Budget Planning Application - Finance Module Models.

This module contains all finance_* prefixed tables for financial planning
and reporting.

Table Categories:
-----------------
1. ACTIVE Tables (use these for new development):
   - finance_data: Unified financial planning data (Phase 4C - replaces 4 legacy tables)
   - finance_consolidations: Budget consolidation by account code (OUTPUT)
   - finance_statements: Financial statement headers (OUTPUT)
   - finance_statement_lines: Financial statement line items (OUTPUT)

2. DEPRECATED Tables (Phase 4C consolidated - do not use for new code):
   - finance_revenue_plans: DEPRECATED → Use FinanceData(data_type=REVENUE)
   - finance_personnel_cost_plans: DEPRECATED → Use FinanceData(data_type=PERSONNEL_COST)
   - finance_operating_cost_plans: DEPRECATED → Use FinanceData(data_type=OPERATING_COST)
   - finance_capex_plans: DEPRECATED → Use FinanceData(data_type=CAPEX)

Module Architecture:
--------------------
This module supports multiple EFIR modules:
- Revenue: /revenue/* (gold color, Finance Director)
- Costs: /costs/* (orange color, Finance Director)
- Investments: /investments/* (teal color, CFO)
- Consolidation: /consolidation/* (blue color, Finance Director)

Data Flow:
----------
Planning Inputs → FinanceData → BudgetConsolidation → FinancialStatement

French PCG Account Structure:
-----------------------------
Revenue (Class 7):
- 701xx: Tuition fees (by trimester: T1=40%, T2=30%, T3=30%)
- 702xx-709xx: Registration, DAI, transport, canteen fees
- 75xxx-77xxx: Other revenue

Expenses (Class 6):
- 60xxx: Purchases (supplies, books, equipment)
- 61xxx: External services (maintenance, cleaning, security)
- 62xxx: Other external expenses (insurance, legal)
- 63xxx: Taxes and duties
- 64xxx: Personnel costs (salaries, social charges)
- 65xxx: Other operating expenses
- 66xxx: Financial expenses
- 68xxx: Depreciation and provisions

Assets (Class 2):
- 20xxx: Intangible assets (software, licenses)
- 21xxx: Tangible assets (buildings, equipment, furniture, IT)

Author: Claude Code
Date: 2025-12-16
Version: 1.0.0
"""

from __future__ import annotations

import os
import uuid
import warnings
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    BaseModel,
    VersionedMixin,
    get_fk_target,
    get_schema,
)

if TYPE_CHECKING:
    from app.models.reference import AcademicCycle, TeacherCategory

# ==============================================================================
# Enums - Finance Data
# ==============================================================================


class FinanceDataType(str, PyEnum):
    """
    Type discriminator for unified finance_data table.

    Phase 4C Consolidation:
    -----------------------
    This enum enables the unified finance_data table to replace 4 separate tables:
    - finance_revenue_plans → data_type='revenue'
    - finance_operating_cost_plans → data_type='operating_cost'
    - finance_personnel_cost_plans → data_type='personnel_cost'
    - finance_capex_plans → data_type='capex'

    Query Examples:
    ---------------
    # All revenue for a version:
    SELECT * FROM finance_data WHERE version_id = ? AND data_type = 'revenue'

    # Sum by data_type:
    SELECT data_type, SUM(amount_sar) as total
    FROM finance_data WHERE version_id = ?
    GROUP BY data_type
    """

    REVENUE = "revenue"  # Tuition, fees, other revenue (70xxx-77xxx)
    OPERATING_COST = "operating_cost"  # Supplies, utilities, maintenance (60xxx-68xxx)
    PERSONNEL_COST = "personnel_cost"  # Salaries, benefits, GOSI (64xxx)
    CAPEX = "capex"  # Capital expenditure - equipment, IT, furniture (20xxx-21xxx)


# ==============================================================================
# Enums - Consolidation & Statements
# ==============================================================================


class ConsolidationCategory(str, PyEnum):
    """
    Budget consolidation category for grouping and reporting.

    Revenue Categories:
    -------------------
    REVENUE_TUITION: 701xx - Tuition fees by trimester
    REVENUE_FEES: 702xx-709xx - DAI, registration, transport, canteen
    REVENUE_OTHER: 75xxx-77xxx - Other revenue

    Personnel Categories:
    ---------------------
    PERSONNEL_TEACHING: 64110-64119 - Teaching staff salaries
    PERSONNEL_ADMIN: 64120-64129 - Administrative staff salaries
    PERSONNEL_SUPPORT: 64130-64139 - Support staff salaries
    PERSONNEL_SOCIAL: 645xx - Social charges (GOSI, EOS)

    Operating Categories:
    ---------------------
    OPERATING_SUPPLIES: 606xx - Educational supplies
    OPERATING_UTILITIES: 6061x - Electricity, water, gas
    OPERATING_MAINTENANCE: 615xx - Building and equipment maintenance
    OPERATING_INSURANCE: 616xx - Insurance premiums
    OPERATING_OTHER: 60xxx-68xxx - Other operating expenses

    CapEx Categories:
    -----------------
    CAPEX_EQUIPMENT: 2154x - Educational equipment
    CAPEX_IT: 2183x - Computers, servers, network
    CAPEX_FURNITURE: 2184x - Desks, chairs, storage
    CAPEX_BUILDING: 213xx - Building improvements
    CAPEX_SOFTWARE: 205xx - Software licenses
    """

    REVENUE_TUITION = "revenue_tuition"
    REVENUE_FEES = "revenue_fees"
    REVENUE_OTHER = "revenue_other"
    PERSONNEL_TEACHING = "personnel_teaching"
    PERSONNEL_ADMIN = "personnel_admin"
    PERSONNEL_SUPPORT = "personnel_support"
    PERSONNEL_SOCIAL = "personnel_social"
    OPERATING_SUPPLIES = "operating_supplies"
    OPERATING_UTILITIES = "operating_utilities"
    OPERATING_MAINTENANCE = "operating_maintenance"
    OPERATING_INSURANCE = "operating_insurance"
    OPERATING_OTHER = "operating_other"
    CAPEX_EQUIPMENT = "capex_equipment"
    CAPEX_IT = "capex_it"
    CAPEX_FURNITURE = "capex_furniture"
    CAPEX_BUILDING = "capex_building"
    CAPEX_SOFTWARE = "capex_software"


class StatementType(str, PyEnum):
    """
    Financial statement type.

    Types:
    ------
    INCOME_STATEMENT: Compte de résultat (P&L)
        - Shows revenues vs expenses for the period
        - Calculates operating result and net result

    BALANCE_SHEET_ASSETS: Bilan - Actif
        - Fixed assets (immobilisations)
        - Current assets (actif circulant)

    BALANCE_SHEET_LIABILITIES: Bilan - Passif
        - Equity (capitaux propres)
        - Provisions
        - Debt (dettes)

    CASH_FLOW: Tableau de flux de trésorerie
        - Operating cash flow
        - Investing cash flow (CapEx)
        - Financing cash flow
    """

    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET_ASSETS = "balance_sheet_assets"
    BALANCE_SHEET_LIABILITIES = "balance_sheet_liabilities"
    CASH_FLOW = "cash_flow"


class StatementFormat(str, PyEnum):
    """
    Financial statement format standard.

    Formats:
    --------
    FRENCH_PCG: French Plan Comptable Général
        - Standard format for French accounting
        - Used by AEFE schools worldwide

    IFRS: International Financial Reporting Standards
        - International format
        - May be required for certain reporting
    """

    FRENCH_PCG = "french_pcg"
    IFRS = "ifrs"


class LineType(str, PyEnum):
    """
    Financial statement line type for display formatting.

    Types:
    ------
    SECTION_HEADER: Section title (e.g., "PRODUITS D'EXPLOITATION")
        - Bold, no amount, indent_level=0

    ACCOUNT_GROUP: Account group (e.g., "70 - Ventes")
        - May have subtotal amount, indent_level=1

    ACCOUNT_LINE: Individual account (e.g., "701 - Scolarité")
        - Always has amount, indent_level=2

    SUBTOTAL: Subtotal line (e.g., "Total Produits d'Exploitation")
        - Sum of section, indent_level=1, underlined

    TOTAL: Total line (e.g., "Résultat net")
        - Final calculation, indent_level=0, bold + double underline
    """

    SECTION_HEADER = "section_header"
    ACCOUNT_GROUP = "account_group"
    ACCOUNT_LINE = "account_line"
    SUBTOTAL = "subtotal"
    TOTAL = "total"


# ==============================================================================
# ACTIVE Models - Unified Finance Data (Phase 4C)
# ==============================================================================


class FinanceData(BaseModel, VersionedMixin):
    """
    Unified financial planning data (Phase 4C consolidation).

    This model replaces 4 separate tables:
    - finance_revenue_plans → data_type='revenue'
    - finance_operating_cost_plans → data_type='operating_cost'
    - finance_personnel_cost_plans → data_type='personnel_cost'
    - finance_capex_plans → data_type='capex'

    Benefits:
    ---------
    - Single table for all financial planning data
    - Simpler queries across all financial categories
    - Consistent structure with type-specific nullable columns
    - Lineage tracking for OUTPUT data audit

    Query Examples:
    ---------------
    # All revenue for a version:
    SELECT * FROM finance_data WHERE version_id = ? AND data_type = 'revenue'

    # Or use the backward-compatible view:
    SELECT * FROM vw_finance_revenue WHERE version_id = ?

    # Sum by data_type:
    SELECT data_type, SUM(amount_sar) as total
    FROM finance_data WHERE version_id = ?
    GROUP BY data_type

    Example Usage:
    --------------
    # Create tuition revenue entry
    revenue = FinanceData(
        version_id=version_id,
        data_type=FinanceDataType.REVENUE,
        account_code="70110",
        description="Tuition T1 - French Students",
        category="tuition",
        amount_sar=Decimal("15500000.00"),
        trimester=1,
        is_calculated=True,
        calculation_driver="enrollment",
    )

    # Create personnel cost entry
    cost = FinanceData(
        version_id=version_id,
        data_type=FinanceDataType.PERSONNEL_COST,
        account_code="64110",
        description="Teaching Salaries - Secondary",
        category="salary",
        amount_sar=Decimal("8500000.00"),
        cycle_id=secondary_cycle_id,
        fte_count=Decimal("25.00"),
        unit_cost_sar=Decimal("340000.00"),
        is_calculated=True,
        calculation_driver="dhg_allocation",
    )
    """

    __tablename__ = "finance_data"

    _base_table_args = (
        # Trimester constraint (revenue only: 1, 2, or 3)
        CheckConstraint(
            "trimester IS NULL OR trimester BETWEEN 1 AND 3",
            name="ck_finance_data_trimester_range",
        ),
    )

    if not os.environ.get("PYTEST_RUNNING"):
        __table_args__ = (
            *_base_table_args,
            Index("ix_finance_data_version_id", "version_id"),
            Index("ix_finance_data_data_type", "data_type"),
            Index("ix_finance_data_account_code", "account_code"),
            Index("ix_finance_data_category", "category"),
            Index("ix_finance_data_version_type", "version_id", "data_type"),
            {"schema": "efir_budget"},
        )
    else:
        __table_args__ = (*_base_table_args, {})  # type: ignore[assignment]

    # =========================================================================
    # Discriminator Column
    # =========================================================================
    data_type: Mapped[FinanceDataType] = mapped_column(
        Enum(
            FinanceDataType,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
        comment="Data type: revenue, operating_cost, personnel_cost, capex",
    )

    # =========================================================================
    # Common Columns (all data types)
    # =========================================================================
    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="French PCG account code (e.g., 70110, 64110)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Description of the line item",
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Category for grouping (e.g., tuition, salary, supplies)",
    )

    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Amount in SAR (total_cost_sar for costs)",
    )

    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if auto-calculated from inputs",
    )

    calculation_driver: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="What drives the calculation (e.g., 'enrollment', 'fte_count')",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes",
    )

    # =========================================================================
    # Revenue-specific Columns (only for data_type='revenue')
    # =========================================================================
    trimester: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Revenue only: Trimester (1, 2, or 3) for timing",
    )

    # =========================================================================
    # Personnel-specific Columns (only for data_type='personnel_cost')
    # =========================================================================
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_teacher_categories", "id")),
        nullable=True,
        index=True,
        comment="Personnel only: Teacher category FK",
    )

    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Personnel only: Academic cycle FK",
    )

    fte_count: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Personnel only: FTE count",
    )

    unit_cost_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Personnel/CapEx: Unit cost in SAR",
    )

    # =========================================================================
    # CapEx-specific Columns (only for data_type='capex')
    # =========================================================================
    quantity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="CapEx only: Quantity of items",
    )

    acquisition_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="CapEx only: When acquired/planned",
    )

    useful_life_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="CapEx only: Depreciation period in years",
    )

    # =========================================================================
    # Lineage Columns (OUTPUT table tracking)
    # =========================================================================
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this output was computed",
    )

    computed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who triggered the computation",
    )

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Unique ID for the computation run",
    )

    inputs_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of inputs for cache invalidation",
    )

    # =========================================================================
    # Relationships
    # =========================================================================
    teacher_category: Mapped["TeacherCategory | None"] = relationship(
        "TeacherCategory",
        foreign_keys=[category_id],
        lazy="selectin",
    )

    academic_cycle: Mapped["AcademicCycle | None"] = relationship(
        "AcademicCycle",
        foreign_keys=[cycle_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<FinanceData(type={self.data_type.value}, "
            f"account={self.account_code}, "
            f"amount={self.amount_sar:,.2f} SAR)>"
        )

    @property
    def is_revenue(self) -> bool:
        """Check if this is a revenue entry."""
        return self.data_type == FinanceDataType.REVENUE

    @property
    def is_cost(self) -> bool:
        """Check if this is a cost entry (not revenue)."""
        return self.data_type != FinanceDataType.REVENUE

    @property
    def total_cost_sar(self) -> Decimal:
        """Alias for amount_sar (backward compatibility)."""
        return self.amount_sar


# ==============================================================================
# ACTIVE Models - Budget Consolidation (OUTPUT)
# ==============================================================================


class BudgetConsolidation(BaseModel, VersionedMixin):
    """
    Budget consolidation - aggregates all revenues and costs by account code (OUTPUT).

    This is the core consolidation table that rolls up all Planning Layer data
    into a single view per budget version, providing the foundation for
    financial statements and management reporting.

    Business Logic:
    ---------------
    1. Aggregates FinanceData by account_code and data_type
    2. Calculates subtotals by consolidation_category
    3. Calculates net result (revenue - expenses)

    Formulas:
    ---------
    Total Revenue = Σ(finance_data.amount_sar) WHERE data_type = 'revenue'
    Total Personnel = Σ(finance_data.amount_sar) WHERE data_type = 'personnel_cost'
    Total Operating = Σ(finance_data.amount_sar) WHERE data_type = 'operating_cost'
    Total CapEx = Σ(finance_data.amount_sar) WHERE data_type = 'capex'

    Operating Result = Total Revenue - Total Personnel - Total Operating
    Net Result = Operating Result - Financial Expenses + Financial Income

    Version Comparison:
    -------------------
    Compare approved vs working:
        SELECT
            a.account_code,
            a.amount_sar AS approved_amount,
            w.amount_sar AS working_amount,
            (w.amount_sar - a.amount_sar) AS variance,
            ((w.amount_sar - a.amount_sar) / NULLIF(a.amount_sar, 0) * 100) AS variance_pct
        FROM finance_consolidations a
        JOIN finance_consolidations w ON a.account_code = w.account_code
        WHERE a.version_id = 'approved_version_id'
          AND w.version_id = 'working_version_id'

    Lineage Columns:
    ----------------
    This is an OUTPUT table with lineage tracking for audit.
    """

    __tablename__ = "finance_consolidations"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "account_code",
            name="uk_consolidation_version_account",
        ),
        CheckConstraint(
            "amount_sar >= 0 OR is_revenue = false",
            name="ck_consolidation_revenue_positive",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

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
        Enum(
            ConsolidationCategory,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
        comment="Grouping category for reporting",
    )

    is_revenue: Mapped[bool] = mapped_column(
        Boolean,
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
        comment="Source table name (finance_data)",
    )

    source_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of source records aggregated",
    )

    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="True if auto-calculated, False if manual override",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes or explanations for this consolidation line",
    )

    # =========================================================================
    # Lineage Columns (OUTPUT table tracking)
    # =========================================================================
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this output was computed",
    )

    computed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who triggered the computation",
    )

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Unique ID for the computation run",
    )

    inputs_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of inputs for cache invalidation",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<BudgetConsolidation(account={self.account_code}, "
            f"amount={self.amount_sar:,.2f} SAR, "
            f"category={self.consolidation_category.value})>"
        )


# ==============================================================================
# ACTIVE Models - Financial Statements (OUTPUT)
# ==============================================================================


class FinancialStatement(BaseModel, VersionedMixin):
    """
    Financial statement header (OUTPUT table).

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

    Lineage Columns:
    ----------------
    This is an OUTPUT table with lineage tracking for audit.
    """

    __tablename__ = "finance_statements"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "statement_type",
            "statement_format",
            name="uk_statement_version_type_format",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    # Statement Configuration
    statement_type: Mapped[StatementType] = mapped_column(
        Enum(
            StatementType,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
        comment="Type of financial statement",
    )

    statement_format: Mapped[StatementFormat] = mapped_column(
        Enum(
            StatementFormat,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
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

    # Summary Totals
    total_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total statement amount (net result or total assets/liabilities)",
    )

    # Metadata
    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="True if auto-calculated, False if manual",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes for this statement",
    )

    # =========================================================================
    # Lineage Columns (OUTPUT table tracking)
    # =========================================================================
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this output was computed",
    )

    computed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who triggered the computation",
    )

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Unique ID for the computation run",
    )

    inputs_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of inputs for cache invalidation",
    )

    # Relationships
    lines: Mapped[list["FinancialStatementLine"]] = relationship(
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


class FinancialStatementLine(BaseModel):
    """
    Individual line item in a financial statement (OUTPUT table).

    Represents a single row in the formatted financial statement, which can be:
    - Section headers (bold titles)
    - Account groups (category summaries)
    - Account lines (individual accounts with amounts)
    - Subtotals and totals

    Display Structure:
    ------------------
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

    Hierarchy:
    ----------
    indent_level = 0: Section headers, grand totals
    indent_level = 1: Account groups, subtotals
    indent_level = 2: Account lines

    Lineage Columns:
    ----------------
    This is an OUTPUT table with lineage tracking for audit.
    """

    __tablename__ = "finance_statement_lines"
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
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    # Foreign Keys
    statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            get_fk_target("efir_budget", "finance_statements", "id"),
            ondelete="CASCADE",
        ),
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
        Enum(
            LineType,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
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
        Boolean,
        nullable=False,
        default=False,
        comment="True if line should be displayed in bold",
    )

    is_underlined: Mapped[bool] = mapped_column(
        Boolean,
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

    # =========================================================================
    # Lineage Columns (OUTPUT table tracking)
    # =========================================================================
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this output was computed",
    )

    computed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who triggered the computation",
    )

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Unique ID for the computation run",
    )

    inputs_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of inputs for cache invalidation",
    )

    # Relationships
    statement: Mapped["FinancialStatement"] = relationship(
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


# ==============================================================================
# DEPRECATED Models (Phase 4C - kept for backward compatibility)
# ==============================================================================


class RevenuePlan(BaseModel, VersionedMixin):
    """
    Revenue projections by account code.

    .. deprecated:: Phase 4C
        This model is DEPRECATED. Revenue data is now stored in the unified
        FinanceData table with data_type='revenue'.
        This model is kept for backward compatibility during migration.

        Use FinanceData(data_type=FinanceDataType.REVENUE) for new code.

    Revenue Categories (70xxx-77xxx):
    - 70110-70130: Tuition fees by trimester (T1=40%, T2=30%, T3=30%)
    - 70140: DAI (Droit Annuel d'Inscription)
    - 70150: Registration fees
    - 70200: Transportation fees
    - 70300: Canteen fees
    - 77xxx: Other revenue
    """

    __tablename__ = "finance_revenue_plans"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "account_code",
            name="uk_revenue_version_account",
        ),
        CheckConstraint(
            "amount_sar >= 0",
            name="ck_revenue_non_negative",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    def __init__(self, **kwargs) -> None:
        """Initialize with deprecation warning."""
        warnings.warn(
            "RevenuePlan is deprecated (Phase 4C). "
            "Use FinanceData(data_type=FinanceDataType.REVENUE) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PCG revenue account (70xxx-77xxx)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Line item description",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category (tuition, fees, other)",
    )

    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Revenue amount in SAR",
    )

    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether auto-calculated from drivers",
    )

    calculation_driver: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Driver reference (e.g., 'enrollment', 'fee_structure')",
    )

    trimester: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Trimester (1-3) for tuition, NULL for annual",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Revenue notes and assumptions",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<RevenuePlan(DEPRECATED, account={self.account_code}, "
            f"amount={self.amount_sar:,.2f} SAR)>"
        )


class PersonnelCostPlan(BaseModel, VersionedMixin):
    """
    Personnel cost projections (salaries, benefits, social charges).

    .. deprecated:: Phase 4C
        This model is DEPRECATED. Personnel cost data is now stored in the unified
        FinanceData table with data_type='personnel_cost'.
        This model is kept for backward compatibility during migration.

        Use FinanceData(data_type=FinanceDataType.PERSONNEL_COST) for new code.

    Cost Categories (64xxx):
    - 64110: Teaching salaries
    - 64120: Administrative salaries
    - 64130: Support staff salaries
    - 64500: Social charges (21% of gross salary)
    - 64600: Benefits and allowances
    """

    __tablename__ = "finance_personnel_cost_plans"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "account_code",
            "cycle_id",
            "category_id",
            name="uk_personnel_cost_version_account_cycle_category",
        ),
        CheckConstraint(
            "fte_count >= 0",
            name="ck_personnel_fte_non_negative",
        ),
        CheckConstraint(
            "unit_cost_sar >= 0 AND total_cost_sar >= 0",
            name="ck_personnel_costs_non_negative",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    def __init__(self, **kwargs) -> None:
        """Initialize with deprecation warning."""
        warnings.warn(
            "PersonnelCostPlan is deprecated (Phase 4C). "
            "Use FinanceData(data_type=FinanceDataType.PERSONNEL_COST) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PCG expense account (64xxx)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Cost description",
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_teacher_categories", "id")),
        nullable=True,
        index=True,
        comment="Teacher category (NULL for non-teaching staff)",
    )

    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Academic cycle (NULL for admin/support)",
    )

    fte_count: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Number of FTE",
    )

    unit_cost_sar: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Cost per FTE (SAR/year)",
    )

    total_cost_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Total cost (FTE × unit_cost)",
    )

    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether auto-calculated from drivers",
    )

    calculation_driver: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Driver (e.g., 'dhg_allocation', 'class_structure')",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Cost notes",
    )

    # Relationships
    category: Mapped["TeacherCategory | None"] = relationship(
        "TeacherCategory",
        foreign_keys=[category_id],
    )
    cycle: Mapped["AcademicCycle | None"] = relationship(
        "AcademicCycle",
        foreign_keys=[cycle_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<PersonnelCostPlan(DEPRECATED, account={self.account_code}, "
            f"fte={self.fte_count}, total={self.total_cost_sar:,.2f} SAR)>"
        )


class OperatingCostPlan(BaseModel, VersionedMixin):
    """
    Operating expense projections (non-personnel).

    .. deprecated:: Phase 4C
        This model is DEPRECATED. Operating cost data is now stored in the unified
        FinanceData table with data_type='operating_cost'.
        This model is kept for backward compatibility during migration.

        Use FinanceData(data_type=FinanceDataType.OPERATING_COST) for new code.

    Cost Categories (60xxx-68xxx):
    - 60xxx: Purchases (supplies, books, equipment)
    - 61xxx: External services (maintenance, cleaning, security)
    - 62xxx: Other external expenses (insurance, legal)
    - 63xxx: Taxes and duties
    - 65xxx: Other operating expenses
    - 66xxx: Financial expenses
    - 68xxx: Depreciation and provisions
    """

    __tablename__ = "finance_operating_cost_plans"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "account_code",
            name="uk_operating_cost_version_account",
        ),
        CheckConstraint(
            "amount_sar >= 0",
            name="ck_operating_cost_non_negative",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    def __init__(self, **kwargs) -> None:
        """Initialize with deprecation warning."""
        warnings.warn(
            "OperatingCostPlan is deprecated (Phase 4C). "
            "Use FinanceData(data_type=FinanceDataType.OPERATING_COST) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PCG expense account (60xxx-68xxx)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Expense description",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category (supplies, utilities, maintenance, insurance, etc.)",
    )

    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Expense amount in SAR",
    )

    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether auto-calculated from driver",
    )

    calculation_driver: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Driver (e.g., 'enrollment', 'square_meters', 'fixed')",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Expense notes",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<OperatingCostPlan(DEPRECATED, account={self.account_code}, "
            f"amount={self.amount_sar:,.2f} SAR)>"
        )


class CapExPlan(BaseModel, VersionedMixin):
    """
    Capital expenditure projections (asset purchases).

    .. deprecated:: Phase 4C
        This model is DEPRECATED. CapEx data is now stored in the unified
        FinanceData table with data_type='capex'.
        This model is kept for backward compatibility during migration.

        Use FinanceData(data_type=FinanceDataType.CAPEX) for new code.

    Asset Categories (PCG 20xxx-21xxx):
    - 20xxx: Intangible assets (software, licenses)
    - 21xxx: Tangible assets
        - 2131: Buildings
        - 2135: Installations (HVAC, electrical)
        - 2154: Equipment and furniture
        - 2155: IT equipment
        - 2158: Other tangible assets

    Depreciation Periods:
    - Buildings: 20-40 years
    - Installations: 10-20 years
    - Equipment: 5-10 years
    - IT equipment: 3-5 years
    - Software: 3-5 years
    """

    __tablename__ = "finance_capex_plans"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "account_code",
            "description",
            name="uk_capex_version_account_description",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_capex_quantity_positive",
        ),
        CheckConstraint(
            "unit_cost_sar >= 0 AND total_cost_sar >= 0",
            name="ck_capex_costs_non_negative",
        ),
        CheckConstraint(
            "useful_life_years > 0 AND useful_life_years <= 50",
            name="ck_capex_life_realistic",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    def __init__(self, **kwargs) -> None:
        """Initialize with deprecation warning."""
        warnings.warn(
            "CapExPlan is deprecated (Phase 4C). "
            "Use FinanceData(data_type=FinanceDataType.CAPEX) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PCG account code (20xxx-21xxx assets)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Asset description",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category (equipment, IT, furniture, building, software)",
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of units",
    )

    unit_cost_sar: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Cost per unit (SAR)",
    )

    total_cost_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Total cost (quantity × unit_cost)",
    )

    acquisition_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Expected acquisition date",
    )

    useful_life_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Depreciation life (years)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="CapEx notes and justification",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<CapExPlan(DEPRECATED, account={self.account_code}, "
            f"qty={self.quantity}, total={self.total_cost_sar:,.2f} SAR)>"
        )


# ==============================================================================
# Backward Compatibility Aliases
# ==============================================================================

# No aliases needed - model names are already canonical
