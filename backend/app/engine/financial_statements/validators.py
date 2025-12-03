"""
Financial Statements Engine - Validation Functions

Validation functions for financial statement calculations.
All validators raise specific exceptions on failure.
"""

from decimal import Decimal

from app.engine.financial_statements.models import (
    ConsolidationEntry,
    FinancialPeriod,
    StatementFormat,
    StatementLine,
)


class InvalidFinancialStatementError(Exception):
    """Raised when financial statement validation fails."""

    pass


def validate_statement_format(format_str: str) -> StatementFormat:
    """
    Validate and convert statement format string.

    Args:
        format_str: Format string ("pcg" or "ifrs")

    Returns:
        StatementFormat enum value

    Raises:
        ValueError: If format is invalid

    Example:
        >>> validate_statement_format("pcg")
        StatementFormat.FRENCH_PCG
        >>> validate_statement_format("invalid")
        ValueError: Invalid format 'invalid'. Must be 'pcg' or 'ifrs'.
    """
    format_map = {
        "pcg": StatementFormat.FRENCH_PCG,
        "ifrs": StatementFormat.IFRS,
        "french_pcg": StatementFormat.FRENCH_PCG,
    }

    format_lower = format_str.lower()
    if format_lower not in format_map:
        raise ValueError(
            f"Invalid format '{format_str}'. Must be 'pcg' or 'ifrs'."
        )

    return format_map[format_lower]


def validate_period(period_str: str) -> FinancialPeriod:
    """
    Validate and convert period string.

    Args:
        period_str: Period string

    Returns:
        FinancialPeriod enum value

    Raises:
        ValueError: If period is invalid

    Example:
        >>> validate_period("p1")
        FinancialPeriod.PERIOD_1
        >>> validate_period("invalid")
        ValueError: Invalid period 'invalid'. Must be 'p1', 'summer', 'p2', or 'annual'.
    """
    period_map = {
        "p1": FinancialPeriod.PERIOD_1,
        "summer": FinancialPeriod.SUMMER,
        "p2": FinancialPeriod.PERIOD_2,
        "annual": FinancialPeriod.ANNUAL,
    }

    period_lower = period_str.lower()
    if period_lower not in period_map:
        valid_periods = ", ".join([f"'{p}'" for p in period_map.keys()])
        raise ValueError(
            f"Invalid period '{period_str}'. Must be {valid_periods}."
        )

    return period_map[period_lower]


def validate_consolidation_entry(entry: ConsolidationEntry) -> None:
    """
    Validate consolidation entry data.

    Args:
        entry: Consolidation entry to validate

    Raises:
        InvalidFinancialStatementError: If entry is invalid

    Example:
        >>> entry = ConsolidationEntry(
        ...     account_code="70110",
        ...     account_name="Tuition T1",
        ...     amount_sar=Decimal("1000"),
        ...     is_revenue=True,
        ...     consolidation_category="revenue"
        ... )
        >>> validate_consolidation_entry(entry)  # Should not raise
    """
    # Validate account code format (French PCG: 5-6 digits)
    if not entry.account_code.isdigit():
        raise InvalidFinancialStatementError(
            f"Account code '{entry.account_code}' must contain only digits"
        )

    if len(entry.account_code) < 3 or len(entry.account_code) > 6:
        raise InvalidFinancialStatementError(
            f"Account code '{entry.account_code}' must be 3-6 digits long"
        )

    # Validate revenue account codes (70xxx-77xxx)
    if entry.is_revenue:
        first_digit = entry.account_code[0]
        if first_digit != "7":
            raise InvalidFinancialStatementError(
                f"Revenue account code '{entry.account_code}' must start with 7 (70xxx-77xxx)"
            )

    # Validate expense account codes (60xxx-68xxx)
    if not entry.is_revenue:
        first_digit = entry.account_code[0]
        if first_digit != "6":
            raise InvalidFinancialStatementError(
                f"Expense account code '{entry.account_code}' must start with 6 (60xxx-68xxx)"
            )

    # Validate amount is non-negative
    if entry.amount_sar < 0:
        raise InvalidFinancialStatementError(
            f"Amount for '{entry.account_name}' cannot be negative"
        )


def validate_statement_line(line: StatementLine) -> None:
    """
    Validate statement line data.

    Args:
        line: Statement line to validate

    Raises:
        InvalidFinancialStatementError: If line is invalid

    Example:
        >>> line = StatementLine(
        ...     line_number=1,
        ...     line_type=StatementLineType.ACCOUNT_LINE,
        ...     indent_level=2,
        ...     line_code="70110",
        ...     line_description="Tuition T1",
        ...     amount_sar=Decimal("1000"),
        ...     is_bold=False,
        ...     is_underlined=False
        ... )
        >>> validate_statement_line(line)  # Should not raise
    """
    # Validate line number is positive
    if line.line_number < 1:
        raise InvalidFinancialStatementError(
            f"Line number must be >= 1, got {line.line_number}"
        )

    # Validate indent level
    if line.indent_level < 0 or line.indent_level > 5:
        raise InvalidFinancialStatementError(
            f"Indent level must be 0-5, got {line.indent_level}"
        )

    # Validate description is not empty
    if not line.line_description or not line.line_description.strip():
        raise InvalidFinancialStatementError(
            "Line description cannot be empty"
        )

    # Validate amount if present
    if line.amount_sar is not None:
        # Check for special values (NaN, Infinity)
        if line.amount_sar.is_nan() or line.amount_sar.is_infinite():
            raise InvalidFinancialStatementError(
                f"Amount cannot be NaN or Infinity, got {line.amount_sar}"
            )
        # Check decimal precision
        exponent = line.amount_sar.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -2:
            raise InvalidFinancialStatementError(
                f"Amount must have at most 2 decimal places, got {line.amount_sar}"
            )


def validate_balance_sheet_balance(
    total_assets: Decimal,
    total_liabilities: Decimal,
    total_equity: Decimal,
    tolerance: Decimal = Decimal("0.01"),
) -> bool:
    """
    Validate that balance sheet balances.

    Formula: Assets = Liabilities + Equity

    Args:
        total_assets: Total assets amount
        total_liabilities: Total liabilities amount
        total_equity: Total equity amount
        tolerance: Acceptable difference (default: 0.01 SAR)

    Returns:
        True if balanced within tolerance, False otherwise

    Raises:
        InvalidFinancialStatementError: If difference exceeds tolerance

    Example:
        >>> validate_balance_sheet_balance(
        ...     Decimal("1000"),
        ...     Decimal("600"),
        ...     Decimal("400")
        ... )
        True
        >>> validate_balance_sheet_balance(
        ...     Decimal("1000"),
        ...     Decimal("500"),
        ...     Decimal("400")
        ... )
        InvalidFinancialStatementError: Balance sheet does not balance...
    """
    left_side = total_assets
    right_side = total_liabilities + total_equity

    difference = abs(left_side - right_side)

    if difference > tolerance:
        raise InvalidFinancialStatementError(
            f"Balance sheet does not balance. "
            f"Assets: {total_assets:,.2f} SAR, "
            f"Liabilities + Equity: {right_side:,.2f} SAR, "
            f"Difference: {difference:,.2f} SAR (tolerance: {tolerance:,.2f} SAR)"
        )

    return True


def validate_account_code_range(
    account_code: str,
    min_code: str,
    max_code: str,
) -> bool:
    """
    Validate account code is within a specific range.

    Args:
        account_code: Account code to check
        min_code: Minimum account code (inclusive)
        max_code: Maximum account code (inclusive)

    Returns:
        True if within range

    Raises:
        ValueError: If account code is outside range

    Example:
        >>> validate_account_code_range("70110", "70000", "77999")
        True
        >>> validate_account_code_range("60110", "70000", "77999")
        ValueError: Account code '60110' is outside range 70000-77999
    """
    if not (min_code <= account_code <= max_code):
        raise ValueError(
            f"Account code '{account_code}' is outside range {min_code}-{max_code}"
        )

    return True


def validate_revenue_expense_split(
    revenue_entries: list[ConsolidationEntry],
    expense_entries: list[ConsolidationEntry],
) -> None:
    """
    Validate that revenue and expense entries are properly classified.

    Args:
        revenue_entries: List of revenue entries
        expense_entries: List of expense entries

    Raises:
        InvalidFinancialStatementError: If classification is incorrect

    Example:
        >>> revenue = [ConsolidationEntry(account_code="70110", account_name="Tuition",
        ...     amount_sar=Decimal("1000"), is_revenue=True, consolidation_category="revenue")]
        >>> expense = [ConsolidationEntry(account_code="60110", account_name="Salaries",
        ...     amount_sar=Decimal("500"), is_revenue=False, consolidation_category="personnel")]
        >>> validate_revenue_expense_split(revenue, expense)  # Should not raise
    """
    # Check all revenue entries are marked as revenue
    for entry in revenue_entries:
        if not entry.is_revenue:
            raise InvalidFinancialStatementError(
                f"Entry '{entry.account_name}' ({entry.account_code}) is in revenue list but marked as expense"
            )

    # Check all expense entries are marked as expense
    for entry in expense_entries:
        if entry.is_revenue:
            raise InvalidFinancialStatementError(
                f"Entry '{entry.account_name}' ({entry.account_code}) is in expense list but marked as revenue"
            )


def validate_statement_line_sequence(lines: list[StatementLine]) -> None:
    """
    Validate that statement lines are in correct sequence.

    Args:
        lines: List of statement lines

    Raises:
        InvalidFinancialStatementError: If line numbers are not sequential

    Example:
        >>> lines = [
        ...     StatementLine(line_number=1, line_type=StatementLineType.SECTION_HEADER, ...),
        ...     StatementLine(line_number=2, line_type=StatementLineType.ACCOUNT_LINE, ...),
        ...     StatementLine(line_number=3, line_type=StatementLineType.TOTAL, ...)
        ... ]
        >>> validate_statement_line_sequence(lines)  # Should not raise
    """
    if not lines:
        return

    expected_line_number = 1
    for line in lines:
        if line.line_number != expected_line_number:
            raise InvalidFinancialStatementError(
                f"Line number sequence broken. Expected {expected_line_number}, got {line.line_number}"
            )
        expected_line_number += 1


def validate_pcg_account_code(account_code: str) -> None:
    """
    Validate French PCG account code format.

    PCG codes are 3-6 digits where:
    - First digit indicates class (1-8)
    - Subsequent digits indicate sub-categories

    Args:
        account_code: Account code to validate

    Raises:
        ValueError: If account code format is invalid

    Example:
        >>> validate_pcg_account_code("70110")  # Valid
        >>> validate_pcg_account_code("ABC123")  # Invalid
        ValueError: Account code must contain only digits
    """
    if not account_code.isdigit():
        raise ValueError("Account code must contain only digits")

    if len(account_code) < 3 or len(account_code) > 6:
        raise ValueError("Account code must be 3-6 digits")

    first_digit = int(account_code[0])
    if first_digit < 1 or first_digit > 8:
        raise ValueError(f"Account code class (first digit) must be 1-8, got {first_digit}")
