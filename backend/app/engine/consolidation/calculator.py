"""
Financial Statements Engine - Calculator Functions

Pure calculation functions for financial statement generation.
All functions are stateless with no side effects.

Formulas:
---------
Operating Result:
    operating_result = total_revenue - total_expenses

Net Result (Simplified):
    net_result = operating_result
    (In full implementation: + financial_income - financial_expenses)

Balance Sheet Balance:
    total_assets = total_liabilities + total_equity

Cash Flow:
    net_cash_change = operating_cash_flow + investing_cash_flow + financing_cash_flow
"""

from decimal import Decimal

from .models import (
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


def calculate_operating_result(
    total_revenue: Decimal,
    total_expenses: Decimal,
) -> Decimal:
    """
    Calculate operating result (profit/loss).

    Formula:
        operating_result = total_revenue - total_expenses

    Args:
        total_revenue: Total revenue amount in SAR
        total_expenses: Total expenses amount in SAR

    Returns:
        Operating result (positive = profit, negative = loss)

    Example:
        >>> calculate_operating_result(Decimal("100000"), Decimal("90000"))
        Decimal('10000.00')
        >>> calculate_operating_result(Decimal("100000"), Decimal("110000"))
        Decimal('-10000.00')
    """
    result = total_revenue - total_expenses
    return result.quantize(Decimal("0.01"))


def calculate_period_totals(
    consolidation_entries: list[ConsolidationEntry],
    period: FinancialPeriod,
) -> PeriodTotals:
    """
    Calculate financial totals for a specific period.

    Args:
        consolidation_entries: List of consolidation entries
        period: Financial period to calculate

    Returns:
        PeriodTotals with revenue, expenses, and results

    Example:
        >>> entries = [
        ...     ConsolidationEntry(
        ...         account_code="70110", account_name="Tuition",
        ...         amount_sar=Decimal("100000"), is_revenue=True,
        ...         consolidation_category="revenue", period=FinancialPeriod.ANNUAL
        ...     ),
        ...     ConsolidationEntry(
        ...         account_code="64110", account_name="Salaries",
        ...         amount_sar=Decimal("60000"), is_revenue=False,
        ...         consolidation_category="personnel", period=FinancialPeriod.ANNUAL
        ...     )
        ... ]
        >>> totals = calculate_period_totals(entries, FinancialPeriod.ANNUAL)
        >>> totals.total_revenue
        Decimal('100000.00')
        >>> totals.operating_result
        Decimal('40000.00')
    """
    # Filter entries by period
    period_entries = [e for e in consolidation_entries if e.period == period]

    # Calculate totals
    total_revenue = Decimal("0.00")
    total_expenses = Decimal("0.00")

    for entry in period_entries:
        if entry.is_revenue:
            total_revenue += entry.amount_sar
        else:
            total_expenses += entry.amount_sar

    # Calculate results
    operating_result = calculate_operating_result(total_revenue, total_expenses)
    net_result = operating_result  # Simplified - no financial items

    return PeriodTotals(
        period=period,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        operating_result=operating_result,
        net_result=net_result,
    )


def format_statement_line(
    line_number: int,
    line_type: StatementLineType,
    description: str,
    amount: Decimal | None = None,
    indent_level: int = 0,
    line_code: str | None = None,
    is_bold: bool = False,
    is_underlined: bool = False,
    source_category: str | None = None,
) -> StatementLine:
    """
    Create a formatted statement line.

    Args:
        line_number: Sequential line number
        line_type: Type of line
        description: Line description text
        amount: Amount in SAR (None for headers)
        indent_level: Indentation level (0-5)
        line_code: Account code if applicable
        is_bold: Display in bold
        is_underlined: Display underlined
        source_category: Source consolidation category

    Returns:
        StatementLine instance

    Example:
        >>> line = format_statement_line(
        ...     1, StatementLineType.SECTION_HEADER, "REVENUE",
        ...     indent_level=0, is_bold=True
        ... )
        >>> line.line_description
        'REVENUE'
    """
    return StatementLine(
        line_number=line_number,
        line_type=line_type,
        indent_level=indent_level,
        line_code=line_code,
        line_description=description,
        amount_sar=amount,
        is_bold=is_bold,
        is_underlined=is_underlined,
        source_category=source_category,
    )


def generate_income_statement_lines(
    consolidation_entries: list[ConsolidationEntry],
    statement_format: StatementFormat,
) -> list[StatementLine]:
    """
    Generate income statement lines from consolidation entries.

    Creates formatted lines with:
    - Revenue section
    - Expense section
    - Operating result
    - Net result

    Args:
        consolidation_entries: List of consolidation entries
        statement_format: Statement format (PCG or IFRS)

    Returns:
        List of formatted statement lines

    Example:
        >>> entries = [...]  # Consolidation entries
        >>> lines = generate_income_statement_lines(entries, StatementFormat.FRENCH_PCG)
        >>> len(lines) > 0
        True
    """
    lines: list[StatementLine] = []
    line_number = 1

    # Separate revenue and expenses
    revenue_entries = [e for e in consolidation_entries if e.is_revenue]
    expense_entries = [e for e in consolidation_entries if not e.is_revenue]

    # Calculate totals
    total_revenue = sum((e.amount_sar for e in revenue_entries), start=Decimal("0.00"))
    total_expenses = sum((e.amount_sar for e in expense_entries), start=Decimal("0.00"))

    # REVENUE SECTION
    revenue_header = (
        "PRODUITS D'EXPLOITATION"
        if statement_format == StatementFormat.FRENCH_PCG
        else "OPERATING REVENUE"
    )
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SECTION_HEADER,
            revenue_header,
            indent_level=0,
            is_bold=True,
        )
    )
    line_number += 1

    # Revenue line items
    for entry in sorted(revenue_entries, key=lambda x: x.account_code):
        lines.append(
            format_statement_line(
                line_number,
                StatementLineType.ACCOUNT_LINE,
                entry.account_name,
                amount=entry.amount_sar,
                indent_level=2,
                line_code=entry.account_code,
                source_category=entry.consolidation_category,
            )
        )
        line_number += 1

    # Revenue subtotal
    revenue_subtotal_desc = (
        "Total Produits d'Exploitation"
        if statement_format == StatementFormat.FRENCH_PCG
        else "Total Operating Revenue"
    )
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SUBTOTAL,
            revenue_subtotal_desc,
            amount=total_revenue,
            indent_level=1,
            is_bold=True,
            is_underlined=True,
        )
    )
    line_number += 1

    # Blank line
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.BLANK_LINE,
            " ",
            indent_level=0,
        )
    )
    line_number += 1

    # EXPENSES SECTION
    expense_header = (
        "CHARGES D'EXPLOITATION"
        if statement_format == StatementFormat.FRENCH_PCG
        else "OPERATING EXPENSES"
    )
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SECTION_HEADER,
            expense_header,
            indent_level=0,
            is_bold=True,
        )
    )
    line_number += 1

    # Expense line items
    for entry in sorted(expense_entries, key=lambda x: x.account_code):
        lines.append(
            format_statement_line(
                line_number,
                StatementLineType.ACCOUNT_LINE,
                entry.account_name,
                amount=entry.amount_sar,
                indent_level=2,
                line_code=entry.account_code,
                source_category=entry.consolidation_category,
            )
        )
        line_number += 1

    # Expense subtotal
    expense_subtotal_desc = (
        "Total Charges d'Exploitation"
        if statement_format == StatementFormat.FRENCH_PCG
        else "Total Operating Expenses"
    )
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SUBTOTAL,
            expense_subtotal_desc,
            amount=total_expenses,
            indent_level=1,
            is_bold=True,
            is_underlined=True,
        )
    )
    line_number += 1

    # Blank line
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.BLANK_LINE,
            " ",
            indent_level=0,
        )
    )
    line_number += 1

    # OPERATING RESULT
    operating_result = calculate_operating_result(total_revenue, total_expenses)
    operating_result_desc = (
        "RÉSULTAT D'EXPLOITATION"
        if statement_format == StatementFormat.FRENCH_PCG
        else "OPERATING RESULT"
    )
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.TOTAL,
            operating_result_desc,
            amount=operating_result,
            indent_level=0,
            is_bold=True,
            is_underlined=True,
        )
    )
    line_number += 1

    # NET RESULT (simplified - same as operating result)
    net_result_desc = (
        "RÉSULTAT NET"
        if statement_format == StatementFormat.FRENCH_PCG
        else "NET RESULT"
    )
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.TOTAL,
            net_result_desc,
            amount=operating_result,
            indent_level=0,
            is_bold=True,
            is_underlined=True,
        )
    )

    return lines


def calculate_income_statement(
    income_input: IncomeStatementInput,
) -> IncomeStatementResult:
    """
    Calculate complete income statement.

    Args:
        income_input: Income statement input data

    Returns:
        IncomeStatementResult with all lines and totals

    Example:
        >>> from uuid import uuid4
        >>> input_data = IncomeStatementInput(
        ...     version_id=uuid4(),
        ...     fiscal_year="2024-2025",
        ...     academic_year="2024/2025",
        ...     statement_format=StatementFormat.FRENCH_PCG,
        ...     consolidation_entries=[...]
        ... )
        >>> result = calculate_income_statement(input_data)
        >>> result.net_result == result.operating_result
        True
    """
    # Generate lines
    lines = generate_income_statement_lines(
        income_input.consolidation_entries,
        income_input.statement_format,
    )

    # Calculate totals
    revenue_entries = [e for e in income_input.consolidation_entries if e.is_revenue]
    expense_entries = [e for e in income_input.consolidation_entries if not e.is_revenue]

    total_revenue = sum((e.amount_sar for e in revenue_entries), start=Decimal("0.00"))
    total_expenses = sum((e.amount_sar for e in expense_entries), start=Decimal("0.00"))
    operating_result = calculate_operating_result(total_revenue, total_expenses)

    # Statement name
    statement_name = (
        f"Compte de résultat {income_input.academic_year}"
        if income_input.statement_format == StatementFormat.FRENCH_PCG
        else f"Income Statement {income_input.academic_year}"
    )

    return IncomeStatementResult(
        version_id=income_input.version_id,
        fiscal_year=income_input.fiscal_year,
        academic_year=income_input.academic_year,
        statement_format=income_input.statement_format,
        statement_name=statement_name,
        lines=lines,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        operating_result=operating_result,
        net_result=operating_result,  # Simplified
    )


def generate_balance_sheet_lines(
    asset_entries: list[ConsolidationEntry],
    liability_entries: list[ConsolidationEntry],
    equity_amount: Decimal,
) -> tuple[list[StatementLine], list[StatementLine]]:
    """
    Generate balance sheet lines for assets and liabilities.

    Args:
        asset_entries: Asset consolidation entries
        liability_entries: Liability consolidation entries
        equity_amount: Total equity amount

    Returns:
        Tuple of (assets_lines, liabilities_lines)

    Example:
        >>> assets, liabilities = generate_balance_sheet_lines([], [], Decimal("1000"))
        >>> len(assets) > 0
        True
        >>> len(liabilities) > 0
        True
    """
    # ASSETS LINES
    assets_lines: list[StatementLine] = []
    line_number = 1

    # Assets header
    assets_lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SECTION_HEADER,
            "ACTIF",
            indent_level=0,
            is_bold=True,
        )
    )
    line_number += 1

    # Asset items
    total_assets = Decimal("0.00")
    for entry in sorted(asset_entries, key=lambda x: x.account_code):
        assets_lines.append(
            format_statement_line(
                line_number,
                StatementLineType.ACCOUNT_LINE,
                entry.account_name,
                amount=entry.amount_sar,
                indent_level=2,
                line_code=entry.account_code,
            )
        )
        line_number += 1
        total_assets += entry.amount_sar

    # Total assets
    assets_lines.append(
        format_statement_line(
            line_number,
            StatementLineType.TOTAL,
            "TOTAL ACTIF",
            amount=total_assets,
            indent_level=0,
            is_bold=True,
            is_underlined=True,
        )
    )

    # LIABILITIES LINES
    liabilities_lines: list[StatementLine] = []
    line_number = 1

    # Liabilities header
    liabilities_lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SECTION_HEADER,
            "PASSIF",
            indent_level=0,
            is_bold=True,
        )
    )
    line_number += 1

    # Equity
    liabilities_lines.append(
        format_statement_line(
            line_number,
            StatementLineType.ACCOUNT_LINE,
            "Capitaux propres",
            amount=equity_amount,
            indent_level=2,
        )
    )
    line_number += 1

    # Liability items
    total_liabilities = Decimal("0.00")
    for entry in sorted(liability_entries, key=lambda x: x.account_code):
        liabilities_lines.append(
            format_statement_line(
                line_number,
                StatementLineType.ACCOUNT_LINE,
                entry.account_name,
                amount=entry.amount_sar,
                indent_level=2,
                line_code=entry.account_code,
            )
        )
        line_number += 1
        total_liabilities += entry.amount_sar

    # Total liabilities + equity
    total_passif = equity_amount + total_liabilities
    liabilities_lines.append(
        format_statement_line(
            line_number,
            StatementLineType.TOTAL,
            "TOTAL PASSIF",
            amount=total_passif,
            indent_level=0,
            is_bold=True,
            is_underlined=True,
        )
    )

    return assets_lines, liabilities_lines


def calculate_balance_sheet(
    balance_input: BalanceSheetInput,
) -> BalanceSheetResult:
    """
    Calculate complete balance sheet.

    Args:
        balance_input: Balance sheet input data

    Returns:
        BalanceSheetResult with assets and liabilities sides

    Example:
        >>> from uuid import uuid4
        >>> input_data = BalanceSheetInput(
        ...     version_id=uuid4(),
        ...     fiscal_year="2024-2025",
        ...     academic_year="2024/2025",
        ...     asset_entries=[...],
        ...     equity_amount=Decimal("1000")
        ... )
        >>> result = calculate_balance_sheet(input_data)
        >>> result.is_balanced
        True
    """
    # Generate lines
    assets_lines, liabilities_lines = generate_balance_sheet_lines(
        balance_input.asset_entries,
        balance_input.liability_entries,
        balance_input.equity_amount,
    )

    # Calculate totals
    total_assets = sum((e.amount_sar for e in balance_input.asset_entries), start=Decimal("0.00"))
    total_liabilities = sum((e.amount_sar for e in balance_input.liability_entries), start=Decimal("0.00"))
    total_equity = balance_input.equity_amount

    # Check balance
    is_balanced = abs(total_assets - (total_liabilities + total_equity)) <= Decimal("0.01")

    return BalanceSheetResult(
        version_id=balance_input.version_id,
        fiscal_year=balance_input.fiscal_year,
        academic_year=balance_input.academic_year,
        assets_statement_name=f"Bilan - Actif {balance_input.academic_year}",
        liabilities_statement_name=f"Bilan - Passif {balance_input.academic_year}",
        assets_lines=assets_lines,
        liabilities_lines=liabilities_lines,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        total_equity=total_equity,
        is_balanced=is_balanced,
    )


def generate_cash_flow_lines(
    operating_entries: list[ConsolidationEntry],
    investing_entries: list[ConsolidationEntry],
    financing_entries: list[ConsolidationEntry],
) -> list[StatementLine]:
    """
    Generate cash flow statement lines.

    Args:
        operating_entries: Operating activity entries
        investing_entries: Investing activity entries
        financing_entries: Financing activity entries

    Returns:
        List of formatted statement lines

    Example:
        >>> lines = generate_cash_flow_lines([], [], [])
        >>> len(lines) > 0
        True
    """
    lines: list[StatementLine] = []
    line_number = 1

    # Header
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SECTION_HEADER,
            "TABLEAU DE FLUX DE TRÉSORERIE",
            indent_level=0,
            is_bold=True,
        )
    )
    line_number += 1

    # Operating activities
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SUBSECTION_HEADER,
            "Flux de trésorerie liés aux activités opérationnelles",
            indent_level=1,
            is_bold=True,
        )
    )
    line_number += 1

    operating_total = sum(
        (e.amount_sar if e.is_revenue else -e.amount_sar for e in operating_entries),
        start=Decimal("0.00")
    )

    for entry in operating_entries:
        amount = entry.amount_sar if entry.is_revenue else -entry.amount_sar
        lines.append(
            format_statement_line(
                line_number,
                StatementLineType.ACCOUNT_LINE,
                entry.account_name,
                amount=amount,
                indent_level=2,
                line_code=entry.account_code,
            )
        )
        line_number += 1

    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.SUBTOTAL,
            "Total flux opérationnels",
            amount=operating_total,
            indent_level=1,
            is_bold=True,
        )
    )
    line_number += 1

    # Investing activities
    investing_total = sum((-e.amount_sar for e in investing_entries), start=Decimal("0.00"))

    # Financing activities (if any)
    financing_total = sum(
        (e.amount_sar if e.is_revenue else -e.amount_sar for e in financing_entries),
        start=Decimal("0.00")
    )

    # Net cash change
    net_change = operating_total + investing_total + financing_total
    lines.append(
        format_statement_line(
            line_number,
            StatementLineType.TOTAL,
            "Variation nette de trésorerie",
            amount=net_change,
            indent_level=0,
            is_bold=True,
            is_underlined=True,
        )
    )

    return lines


def calculate_cash_flow_statement(
    cash_flow_input: CashFlowInput,
) -> CashFlowResult:
    """
    Calculate complete cash flow statement.

    Args:
        cash_flow_input: Cash flow input data

    Returns:
        CashFlowResult with all cash flow categories

    Example:
        >>> from uuid import uuid4
        >>> input_data = CashFlowInput(
        ...     version_id=uuid4(),
        ...     fiscal_year="2024-2025",
        ...     academic_year="2024/2025",
        ...     operating_entries=[...]
        ... )
        >>> result = calculate_cash_flow_statement(input_data)
        >>> result.net_cash_change
        Decimal('...')
    """
    # Generate lines
    lines = generate_cash_flow_lines(
        cash_flow_input.operating_entries,
        cash_flow_input.investing_entries,
        cash_flow_input.financing_entries,
    )

    # Calculate totals
    operating_cash_flow = sum(
        (e.amount_sar if e.is_revenue else -e.amount_sar
        for e in cash_flow_input.operating_entries),
        start=Decimal("0.00")
    )

    investing_cash_flow = sum(
        (-e.amount_sar for e in cash_flow_input.investing_entries),
        start=Decimal("0.00")
    )

    financing_cash_flow = sum(
        (e.amount_sar if e.is_revenue else -e.amount_sar
        for e in cash_flow_input.financing_entries),
        start=Decimal("0.00")
    )

    net_cash_change = operating_cash_flow + investing_cash_flow + financing_cash_flow

    return CashFlowResult(
        version_id=cash_flow_input.version_id,
        fiscal_year=cash_flow_input.fiscal_year,
        academic_year=cash_flow_input.academic_year,
        statement_name=f"Tableau de Flux de Trésorerie {cash_flow_input.academic_year}",
        lines=lines,
        operating_cash_flow=operating_cash_flow.quantize(Decimal("0.01")),
        investing_cash_flow=investing_cash_flow.quantize(Decimal("0.01")),
        financing_cash_flow=financing_cash_flow.quantize(Decimal("0.01")),
        net_cash_change=net_cash_change.quantize(Decimal("0.01")),
    )
