"""
Financial Statements Engine - Data Models

Pydantic models for financial statement calculations.
All models are immutable and validated.
"""

from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class StatementFormat(str, Enum):
    """Financial statement format standard."""

    FRENCH_PCG = "french_pcg"  # French Plan Comptable Général
    IFRS = "ifrs"  # International Financial Reporting Standards


class StatementLineType(str, Enum):
    """Type of line in financial statement."""

    SECTION_HEADER = "section_header"  # Major section (e.g., "REVENUE")
    SUBSECTION_HEADER = "subsection_header"  # Sub-section (e.g., "Tuition Fees")
    ACCOUNT_LINE = "account_line"  # Individual account entry
    SUBTOTAL = "subtotal"  # Subtotal of a section
    TOTAL = "total"  # Grand total
    BLANK_LINE = "blank_line"  # Blank line for spacing


class FinancialPeriod(str, Enum):
    """Financial period for reporting."""

    PERIOD_1 = "p1"  # January - June
    SUMMER = "summer"  # July - August
    PERIOD_2 = "p2"  # September - December
    ANNUAL = "annual"  # Full year


class ConsolidationEntry(BaseModel):
    """
    Consolidation entry for financial statement generation.

    Represents a single line item from budget consolidation.
    """

    account_code: str = Field(..., description="Chart of accounts code (e.g., 70110)")
    account_name: str = Field(..., description="Account name/description")
    amount_sar: Decimal = Field(..., ge=0, description="Amount in SAR")
    is_revenue: bool = Field(..., description="True if revenue, False if expense")
    consolidation_category: str = Field(..., description="Consolidation category")
    period: FinancialPeriod = Field(
        default=FinancialPeriod.ANNUAL, description="Financial period"
    )

    @field_validator("amount_sar")
    @classmethod
    def quantize_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount has exactly 2 decimal places."""
        return v.quantize(Decimal("0.01"))

    class Config:
        frozen = True


class StatementLine(BaseModel):
    """
    Line in a financial statement.

    Represents a single line with formatting and hierarchy.
    """

    line_number: int = Field(..., ge=1, description="Line sequence number")
    line_type: StatementLineType = Field(..., description="Type of line")
    indent_level: int = Field(..., ge=0, le=5, description="Indentation level (0-5)")
    line_code: Optional[str] = Field(None, description="Account code if applicable")
    line_description: str = Field(..., min_length=1, description="Line description")
    amount_sar: Optional[Decimal] = Field(None, description="Amount in SAR")
    is_bold: bool = Field(default=False, description="Display in bold")
    is_underlined: bool = Field(default=False, description="Display underlined")
    source_category: Optional[str] = Field(None, description="Source category")

    @field_validator("amount_sar")
    @classmethod
    def quantize_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure amount has exactly 2 decimal places if present."""
        if v is not None:
            return v.quantize(Decimal("0.01"))
        return v

    class Config:
        frozen = True


class PeriodTotals(BaseModel):
    """
    Period-specific financial totals.

    Aggregates revenue and expenses for a given period.
    """

    period: FinancialPeriod = Field(..., description="Financial period")
    total_revenue: Decimal = Field(..., ge=0, description="Total revenue in SAR")
    total_expenses: Decimal = Field(..., ge=0, description="Total expenses in SAR")
    operating_result: Decimal = Field(..., description="Operating result (profit/loss)")
    net_result: Decimal = Field(..., description="Net result after all items")

    @field_validator("total_revenue", "total_expenses", "operating_result", "net_result")
    @classmethod
    def quantize_amounts(cls, v: Decimal) -> Decimal:
        """Ensure amounts have exactly 2 decimal places."""
        return v.quantize(Decimal("0.01"))

    class Config:
        frozen = True


class IncomeStatementInput(BaseModel):
    """
    Input for income statement calculation.

    Contains all consolidation entries and configuration.
    """

    budget_version_id: UUID = Field(..., description="Budget version UUID")
    fiscal_year: str = Field(..., description="Fiscal year (e.g., '2024-2025')")
    academic_year: str = Field(..., description="Academic year (e.g., '2024/2025')")
    statement_format: StatementFormat = Field(
        default=StatementFormat.FRENCH_PCG, description="Statement format standard"
    )
    consolidation_entries: list[ConsolidationEntry] = Field(
        ..., min_length=0, description="List of consolidation entries"
    )

    class Config:
        frozen = True


class IncomeStatementResult(BaseModel):
    """
    Result of income statement calculation.

    Contains all lines and totals for the statement.
    """

    budget_version_id: UUID = Field(..., description="Budget version UUID")
    fiscal_year: str = Field(..., description="Fiscal year")
    academic_year: str = Field(..., description="Academic year")
    statement_format: StatementFormat = Field(..., description="Statement format")
    statement_name: str = Field(..., description="Statement name/title")
    lines: list[StatementLine] = Field(..., description="Statement lines")
    total_revenue: Decimal = Field(..., ge=0, description="Total revenue")
    total_expenses: Decimal = Field(..., ge=0, description="Total expenses")
    operating_result: Decimal = Field(..., description="Operating result")
    net_result: Decimal = Field(..., description="Net result")

    @field_validator("total_revenue", "total_expenses", "operating_result", "net_result")
    @classmethod
    def quantize_amounts(cls, v: Decimal) -> Decimal:
        """Ensure amounts have exactly 2 decimal places."""
        return v.quantize(Decimal("0.01"))

    class Config:
        frozen = True


class BalanceSheetInput(BaseModel):
    """
    Input for balance sheet calculation.

    Contains assets and liabilities data.
    """

    budget_version_id: UUID = Field(..., description="Budget version UUID")
    fiscal_year: str = Field(..., description="Fiscal year")
    academic_year: str = Field(..., description="Academic year")
    asset_entries: list[ConsolidationEntry] = Field(
        ..., min_length=0, description="Asset entries (CapEx, etc.)"
    )
    liability_entries: list[ConsolidationEntry] = Field(
        default_factory=list, description="Liability entries"
    )
    equity_amount: Decimal = Field(
        default=Decimal("0.00"), ge=0, description="Equity amount in SAR"
    )

    @field_validator("equity_amount")
    @classmethod
    def quantize_equity(cls, v: Decimal) -> Decimal:
        """Ensure equity has exactly 2 decimal places."""
        return v.quantize(Decimal("0.01"))

    class Config:
        frozen = True


class BalanceSheetResult(BaseModel):
    """
    Result of balance sheet calculation.

    Contains assets and liabilities sides with totals.
    """

    budget_version_id: UUID = Field(..., description="Budget version UUID")
    fiscal_year: str = Field(..., description="Fiscal year")
    academic_year: str = Field(..., description="Academic year")
    assets_statement_name: str = Field(..., description="Assets statement name")
    liabilities_statement_name: str = Field(..., description="Liabilities statement name")
    assets_lines: list[StatementLine] = Field(..., description="Assets lines")
    liabilities_lines: list[StatementLine] = Field(..., description="Liabilities lines")
    total_assets: Decimal = Field(..., ge=0, description="Total assets")
    total_liabilities: Decimal = Field(..., ge=0, description="Total liabilities")
    total_equity: Decimal = Field(..., ge=0, description="Total equity")
    is_balanced: bool = Field(..., description="True if Assets = Liabilities + Equity")

    @field_validator("total_assets", "total_liabilities", "total_equity")
    @classmethod
    def quantize_amounts(cls, v: Decimal) -> Decimal:
        """Ensure amounts have exactly 2 decimal places."""
        return v.quantize(Decimal("0.01"))

    class Config:
        frozen = True


class CashFlowInput(BaseModel):
    """
    Input for cash flow statement calculation.

    Contains operating, investing, and financing activities.
    """

    budget_version_id: UUID = Field(..., description="Budget version UUID")
    fiscal_year: str = Field(..., description="Fiscal year")
    academic_year: str = Field(..., description="Academic year")
    operating_entries: list[ConsolidationEntry] = Field(
        ..., description="Operating activities"
    )
    investing_entries: list[ConsolidationEntry] = Field(
        default_factory=list, description="Investing activities (CapEx)"
    )
    financing_entries: list[ConsolidationEntry] = Field(
        default_factory=list, description="Financing activities"
    )

    class Config:
        frozen = True


class CashFlowResult(BaseModel):
    """
    Result of cash flow statement calculation.

    Contains cash flows by category and net change.
    """

    budget_version_id: UUID = Field(..., description="Budget version UUID")
    fiscal_year: str = Field(..., description="Fiscal year")
    academic_year: str = Field(..., description="Academic year")
    statement_name: str = Field(..., description="Statement name")
    lines: list[StatementLine] = Field(..., description="Cash flow lines")
    operating_cash_flow: Decimal = Field(..., description="Operating cash flow")
    investing_cash_flow: Decimal = Field(..., description="Investing cash flow")
    financing_cash_flow: Decimal = Field(..., description="Financing cash flow")
    net_cash_change: Decimal = Field(..., description="Net change in cash")

    @field_validator(
        "operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_change"
    )
    @classmethod
    def quantize_amounts(cls, v: Decimal) -> Decimal:
        """Ensure amounts have exactly 2 decimal places."""
        return v.quantize(Decimal("0.01"))

    class Config:
        frozen = True
