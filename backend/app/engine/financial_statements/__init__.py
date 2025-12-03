"""
Financial Statements Engine - Pure Calculation Functions

Provides pure calculation functions for:
- Income Statement generation (French PCG + IFRS formats)
- Balance Sheet generation (Assets + Liabilities)
- Cash Flow Statement generation
- Period-based financial aggregations

All functions are stateless with no side effects.
"""

from app.engine.financial_statements.calculator import (
    calculate_balance_sheet,
    calculate_cash_flow_statement,
    calculate_income_statement,
    calculate_operating_result,
    calculate_period_totals,
    format_statement_line,
    generate_balance_sheet_lines,
    generate_cash_flow_lines,
    generate_income_statement_lines,
)
from app.engine.financial_statements.models import (
    BalanceSheetInput,
    BalanceSheetResult,
    CashFlowInput,
    CashFlowResult,
    ConsolidationEntry,
    FinancialPeriod,
    IncomeStatementInput,
    IncomeStatementResult,
    PeriodTotals,
    StatementFormat,
    StatementLine,
    StatementLineType,
)
from app.engine.financial_statements.validators import (
    InvalidFinancialStatementError,
    validate_balance_sheet_balance,
    validate_consolidation_entry,
    validate_period,
    validate_statement_format,
    validate_statement_line,
)

__all__ = [
    # Calculator functions
    "calculate_income_statement",
    "calculate_balance_sheet",
    "calculate_cash_flow_statement",
    "calculate_operating_result",
    "calculate_period_totals",
    "generate_income_statement_lines",
    "generate_balance_sheet_lines",
    "generate_cash_flow_lines",
    "format_statement_line",
    # Models
    "IncomeStatementInput",
    "IncomeStatementResult",
    "BalanceSheetInput",
    "BalanceSheetResult",
    "CashFlowInput",
    "CashFlowResult",
    "StatementLine",
    "StatementLineType",
    "StatementFormat",
    "ConsolidationEntry",
    "PeriodTotals",
    "FinancialPeriod",
    # Validators
    "validate_statement_format",
    "validate_period",
    "validate_consolidation_entry",
    "validate_statement_line",
    "validate_balance_sheet_balance",
    "InvalidFinancialStatementError",
]
