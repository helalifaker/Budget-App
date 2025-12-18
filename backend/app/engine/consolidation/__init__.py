"""
Consolidation Module - Financial Statements Engine

Provides pure calculation functions for:
- Income Statement generation (French PCG + IFRS formats)
- Balance Sheet generation (Assets + Liabilities)
- Cash Flow Statement generation
- Period-based financial aggregations

All functions are stateless with no side effects.

Part of the 10-module engine structure matching frontend.
"""

from app.engine.consolidation.calculator import (
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
from app.engine.consolidation.models import (
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
from app.engine.consolidation.validators import (
    InvalidFinancialStatementError,
    validate_account_code_range,
    validate_balance_sheet_balance,
    validate_consolidation_entry,
    validate_pcg_account_code,
    validate_period,
    validate_revenue_expense_split,
    validate_statement_format,
    validate_statement_line,
    validate_statement_line_sequence,
)

__all__ = [
    # Models
    "BalanceSheetInput",
    "BalanceSheetResult",
    "CashFlowInput",
    "CashFlowResult",
    "ConsolidationEntry",
    "FinancialPeriod",
    "IncomeStatementInput",
    "IncomeStatementResult",
    # Validators
    "InvalidFinancialStatementError",
    "PeriodTotals",
    "StatementFormat",
    "StatementLine",
    "StatementLineType",
    # Calculator functions
    "calculate_balance_sheet",
    "calculate_cash_flow_statement",
    "calculate_income_statement",
    "calculate_operating_result",
    "calculate_period_totals",
    "format_statement_line",
    "generate_balance_sheet_lines",
    "generate_cash_flow_lines",
    "generate_income_statement_lines",
    "validate_account_code_range",
    "validate_balance_sheet_balance",
    "validate_consolidation_entry",
    "validate_pcg_account_code",
    "validate_period",
    "validate_revenue_expense_split",
    "validate_statement_format",
    "validate_statement_line",
    "validate_statement_line_sequence",
]
