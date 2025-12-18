"""
Unit Tests for Financial Statements Engine

Tests for financial statement calculations using the pure function pattern.
Target Coverage: 100%

Test Categories:
1. Income statement calculations (PCG and IFRS formats)
2. Balance sheet calculations (Assets and Liabilities)
3. Cash flow statement calculations
4. Operating result calculations
5. Period totals calculations
6. Statement line formatting
7. Validation (account codes, formats, periods)
8. Balance sheet balancing
9. Edge cases and error handling
10. Statement line sequencing
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.engine.consolidation import (
    BalanceSheetInput,
    BalanceSheetResult,
    CashFlowInput,
    CashFlowResult,
    ConsolidationEntry,
    FinancialPeriod,
    IncomeStatementInput,
    IncomeStatementResult,
    InvalidFinancialStatementError,
    PeriodTotals,
    StatementFormat,
    StatementLine,
    StatementLineType,
    calculate_balance_sheet,
    calculate_cash_flow_statement,
    calculate_income_statement,
    calculate_operating_result,
    calculate_period_totals,
    format_statement_line,
    generate_balance_sheet_lines,
    generate_cash_flow_lines,
    generate_income_statement_lines,
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
from pydantic import ValidationError


class TestOperatingResultCalculations:
    """Test operating result calculations."""

    def test_calculate_operating_result_profit(self):
        """Test operating result with profit."""
        # Revenue: 100,000 SAR, Expenses: 90,000 SAR → Profit: 10,000 SAR
        result = calculate_operating_result(Decimal("100000"), Decimal("90000"))

        assert result == Decimal("10000.00")
        assert result > 0  # Profit

    def test_calculate_operating_result_loss(self):
        """Test operating result with loss."""
        # Revenue: 90,000 SAR, Expenses: 100,000 SAR → Loss: -10,000 SAR
        result = calculate_operating_result(Decimal("90000"), Decimal("100000"))

        assert result == Decimal("-10000.00")
        assert result < 0  # Loss

    def test_calculate_operating_result_breakeven(self):
        """Test operating result at breakeven."""
        # Revenue: 100,000 SAR, Expenses: 100,000 SAR → Breakeven: 0 SAR
        result = calculate_operating_result(Decimal("100000"), Decimal("100000"))

        assert result == Decimal("0.00")

    def test_calculate_operating_result_zero_revenue(self):
        """Test operating result with zero revenue."""
        result = calculate_operating_result(Decimal("0"), Decimal("50000"))

        assert result == Decimal("-50000.00")

    def test_calculate_operating_result_zero_expenses(self):
        """Test operating result with zero expenses."""
        result = calculate_operating_result(Decimal("100000"), Decimal("0"))

        assert result == Decimal("100000.00")

    def test_calculate_operating_result_precision(self):
        """Test operating result maintains 2 decimal precision."""
        result = calculate_operating_result(
            Decimal("83272500.00"), Decimal("74945250.00")
        )

        assert result == Decimal("8327250.00")
        # Check precision
        assert result.as_tuple().exponent == -2


class TestPeriodTotalsCalculations:
    """Test period-specific totals calculations."""

    def test_calculate_period_totals_annual(self):
        """Test annual period totals calculation."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Tuition T1",
                amount_sar=Decimal("30000"),
                is_revenue=True,
                consolidation_category="revenue",
                period=FinancialPeriod.ANNUAL,
            ),
            ConsolidationEntry(
                account_code="64110",
                account_name="Teacher Salaries",
                amount_sar=Decimal("20000"),
                is_revenue=False,
                consolidation_category="personnel",
                period=FinancialPeriod.ANNUAL,
            ),
        ]

        totals = calculate_period_totals(entries, FinancialPeriod.ANNUAL)

        assert totals.period == FinancialPeriod.ANNUAL
        assert totals.total_revenue == Decimal("30000.00")
        assert totals.total_expenses == Decimal("20000.00")
        assert totals.operating_result == Decimal("10000.00")
        assert totals.net_result == Decimal("10000.00")

    def test_calculate_period_totals_period_1(self):
        """Test Period 1 (Jan-Jun) totals."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Tuition T1",
                amount_sar=Decimal("18000"),
                is_revenue=True,
                consolidation_category="revenue",
                period=FinancialPeriod.PERIOD_1,
            ),
            ConsolidationEntry(
                account_code="64110",
                account_name="Salaries P1",
                amount_sar=Decimal("12000"),
                is_revenue=False,
                consolidation_category="personnel",
                period=FinancialPeriod.PERIOD_1,
            ),
        ]

        totals = calculate_period_totals(entries, FinancialPeriod.PERIOD_1)

        assert totals.period == FinancialPeriod.PERIOD_1
        assert totals.total_revenue == Decimal("18000.00")
        assert totals.total_expenses == Decimal("12000.00")
        assert totals.operating_result == Decimal("6000.00")

    def test_calculate_period_totals_summer(self):
        """Test Summer (Jul-Aug) period totals."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Summer Camp Revenue",
                amount_sar=Decimal("5000"),
                is_revenue=True,
                consolidation_category="revenue",
                period=FinancialPeriod.SUMMER,
            ),
            ConsolidationEntry(
                account_code="61100",
                account_name="Summer Expenses",
                amount_sar=Decimal("3000"),
                is_revenue=False,
                consolidation_category="operational",
                period=FinancialPeriod.SUMMER,
            ),
        ]

        totals = calculate_period_totals(entries, FinancialPeriod.SUMMER)

        assert totals.period == FinancialPeriod.SUMMER
        assert totals.total_revenue == Decimal("5000.00")
        assert totals.total_expenses == Decimal("3000.00")

    def test_calculate_period_totals_period_2(self):
        """Test Period 2 (Sep-Dec) totals."""
        entries = [
            ConsolidationEntry(
                account_code="70120",
                account_name="Tuition T2",
                amount_sar=Decimal("13500"),
                is_revenue=True,
                consolidation_category="revenue",
                period=FinancialPeriod.PERIOD_2,
            ),
        ]

        totals = calculate_period_totals(entries, FinancialPeriod.PERIOD_2)

        assert totals.period == FinancialPeriod.PERIOD_2
        assert totals.total_revenue == Decimal("13500.00")

    def test_calculate_period_totals_no_entries(self):
        """Test period totals with no entries."""
        totals = calculate_period_totals([], FinancialPeriod.ANNUAL)

        assert totals.total_revenue == Decimal("0.00")
        assert totals.total_expenses == Decimal("0.00")
        assert totals.operating_result == Decimal("0.00")
        assert totals.net_result == Decimal("0.00")

    def test_calculate_period_totals_filters_by_period(self):
        """Test that period totals filter correctly by period."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="P1 Revenue",
                amount_sar=Decimal("10000"),
                is_revenue=True,
                consolidation_category="revenue",
                period=FinancialPeriod.PERIOD_1,
            ),
            ConsolidationEntry(
                account_code="70120",
                account_name="P2 Revenue",
                amount_sar=Decimal("20000"),
                is_revenue=True,
                consolidation_category="revenue",
                period=FinancialPeriod.PERIOD_2,
            ),
        ]

        # Calculate for P1 only
        totals_p1 = calculate_period_totals(entries, FinancialPeriod.PERIOD_1)
        assert totals_p1.total_revenue == Decimal("10000.00")

        # Calculate for P2 only
        totals_p2 = calculate_period_totals(entries, FinancialPeriod.PERIOD_2)
        assert totals_p2.total_revenue == Decimal("20000.00")


class TestStatementLineFormatting:
    """Test statement line formatting."""

    def test_format_statement_line_section_header(self):
        """Test formatting section header line."""
        line = format_statement_line(
            line_number=1,
            line_type=StatementLineType.SECTION_HEADER,
            description="REVENUE",
            indent_level=0,
            is_bold=True,
        )

        assert line.line_number == 1
        assert line.line_type == StatementLineType.SECTION_HEADER
        assert line.line_description == "REVENUE"
        assert line.indent_level == 0
        assert line.is_bold is True
        assert line.amount_sar is None

    def test_format_statement_line_account_line(self):
        """Test formatting account line with amount."""
        line = format_statement_line(
            line_number=5,
            line_type=StatementLineType.ACCOUNT_LINE,
            description="Tuition Fees T1",
            amount=Decimal("45000"),
            indent_level=2,
            line_code="70110",
        )

        assert line.line_number == 5
        assert line.line_type == StatementLineType.ACCOUNT_LINE
        assert line.line_description == "Tuition Fees T1"
        assert line.amount_sar == Decimal("45000")
        assert line.line_code == "70110"
        assert line.indent_level == 2

    def test_format_statement_line_subtotal(self):
        """Test formatting subtotal line."""
        line = format_statement_line(
            line_number=10,
            line_type=StatementLineType.SUBTOTAL,
            description="Total Revenue",
            amount=Decimal("100000"),
            indent_level=1,
            is_bold=True,
            is_underlined=True,
        )

        assert line.line_type == StatementLineType.SUBTOTAL
        assert line.is_bold is True
        assert line.is_underlined is True

    def test_format_statement_line_total(self):
        """Test formatting total line."""
        line = format_statement_line(
            line_number=20,
            line_type=StatementLineType.TOTAL,
            description="NET RESULT",
            amount=Decimal("10000"),
            indent_level=0,
            is_bold=True,
            is_underlined=True,
        )

        assert line.line_type == StatementLineType.TOTAL
        assert line.indent_level == 0

    def test_format_statement_line_blank_line(self):
        """Test formatting blank line for spacing."""
        line = format_statement_line(
            line_number=15,
            line_type=StatementLineType.BLANK_LINE,
            description=" ",  # Use space instead of empty string for Pydantic validation
            indent_level=0,
        )

        assert line.line_type == StatementLineType.BLANK_LINE
        assert line.line_description == " "  # Updated expectation
        assert line.amount_sar is None

    def test_format_statement_line_with_source_category(self):
        """Test formatting line with source category."""
        line = format_statement_line(
            line_number=3,
            line_type=StatementLineType.ACCOUNT_LINE,
            description="Personnel Costs",
            amount=Decimal("50000"),
            indent_level=2,
            source_category="personnel",
        )

        assert line.source_category == "personnel"


class TestIncomeStatementLineGeneration:
    """Test income statement line generation."""

    def test_generate_income_statement_lines_pcg_format(self):
        """Test generating income statement lines in French PCG format."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Frais de scolarité T1",
                amount_sar=Decimal("45000"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
            ConsolidationEntry(
                account_code="64110",
                account_name="Salaires enseignants",
                amount_sar=Decimal("30000"),
                is_revenue=False,
                consolidation_category="personnel",
            ),
        ]

        lines = generate_income_statement_lines(entries, StatementFormat.FRENCH_PCG)

        assert len(lines) > 0

        # Check revenue header
        revenue_header = lines[0]
        assert revenue_header.line_type == StatementLineType.SECTION_HEADER
        assert "PRODUITS" in revenue_header.line_description

        # Check expense header exists
        expense_headers = [
            l for l in lines if "CHARGES" in l.line_description
        ]
        assert len(expense_headers) > 0

        # Check operating result exists
        operating_result_lines = [
            l for l in lines if "RÉSULTAT D'EXPLOITATION" in l.line_description
        ]
        assert len(operating_result_lines) > 0

        # Check net result exists
        net_result_lines = [
            l for l in lines if "RÉSULTAT NET" in l.line_description
        ]
        assert len(net_result_lines) > 0

    def test_generate_income_statement_lines_ifrs_format(self):
        """Test generating income statement lines in IFRS format."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Tuition Fees",
                amount_sar=Decimal("45000"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
        ]

        lines = generate_income_statement_lines(entries, StatementFormat.IFRS)

        # Check IFRS English labels
        revenue_header = lines[0]
        assert "OPERATING REVENUE" in revenue_header.line_description

    def test_generate_income_statement_lines_no_entries(self):
        """Test generating income statement with no entries."""
        lines = generate_income_statement_lines([], StatementFormat.FRENCH_PCG)

        # Should still have headers and totals
        assert len(lines) > 0

        # Find totals
        total_lines = [l for l in lines if l.line_type == StatementLineType.SUBTOTAL]
        assert len(total_lines) == 2  # Revenue total + Expense total

        # Revenue and expense totals should be 0
        revenue_total = next(
            l for l in total_lines if "Produits" in l.line_description
        )
        assert revenue_total.amount_sar == Decimal("0.00")

    def test_generate_income_statement_lines_sorts_by_account_code(self):
        """Test that entries are sorted by account code."""
        entries = [
            ConsolidationEntry(
                account_code="70120",
                account_name="Tuition T2",
                amount_sar=Decimal("13500"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
            ConsolidationEntry(
                account_code="70110",
                account_name="Tuition T1",
                amount_sar=Decimal("18000"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
        ]

        lines = generate_income_statement_lines(entries, StatementFormat.FRENCH_PCG)

        # Get account lines
        account_lines = [l for l in lines if l.line_type == StatementLineType.ACCOUNT_LINE]

        # First account line should be 70110 (comes before 70120)
        assert account_lines[0].line_code == "70110"
        assert account_lines[1].line_code == "70120"

    def test_generate_income_statement_lines_includes_blank_lines(self):
        """Test that blank lines are included for spacing."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Revenue",
                amount_sar=Decimal("1000"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
            ConsolidationEntry(
                account_code="64110",
                account_name="Expense",
                amount_sar=Decimal("500"),
                is_revenue=False,
                consolidation_category="personnel",
            ),
        ]

        lines = generate_income_statement_lines(entries, StatementFormat.FRENCH_PCG)

        # Should have blank lines for spacing
        blank_lines = [l for l in lines if l.line_type == StatementLineType.BLANK_LINE]
        assert len(blank_lines) >= 2  # After revenue section and expense section


class TestIncomeStatementCalculation:
    """Test complete income statement calculation."""

    def test_calculate_income_statement_pcg_format(self):
        """Test complete income statement calculation in PCG format."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Frais de scolarité T1",
                amount_sar=Decimal("45000"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
            ConsolidationEntry(
                account_code="64110",
                account_name="Salaires",
                amount_sar=Decimal("30000"),
                is_revenue=False,
                consolidation_category="personnel",
            ),
        ]

        input_data = IncomeStatementInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            statement_format=StatementFormat.FRENCH_PCG,
            consolidation_entries=entries,
        )

        result = calculate_income_statement(input_data)

        assert isinstance(result, IncomeStatementResult)
        assert result.version_id == input_data.version_id
        assert result.fiscal_year == "2024-2025"
        assert result.academic_year == "2024/2025"
        assert result.statement_format == StatementFormat.FRENCH_PCG
        assert "Compte de résultat" in result.statement_name
        assert result.total_revenue == Decimal("45000.00")
        assert result.total_expenses == Decimal("30000.00")
        assert result.operating_result == Decimal("15000.00")
        assert result.net_result == Decimal("15000.00")
        assert len(result.lines) > 0

    def test_calculate_income_statement_ifrs_format(self):
        """Test complete income statement calculation in IFRS format."""
        input_data = IncomeStatementInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            statement_format=StatementFormat.IFRS,
            consolidation_entries=[],
        )

        result = calculate_income_statement(input_data)

        assert result.statement_format == StatementFormat.IFRS
        assert "Income Statement" in result.statement_name

    def test_calculate_income_statement_with_loss(self):
        """Test income statement calculation showing loss."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Revenue",
                amount_sar=Decimal("50000"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
            ConsolidationEntry(
                account_code="64110",
                account_name="Expenses",
                amount_sar=Decimal("70000"),
                is_revenue=False,
                consolidation_category="personnel",
            ),
        ]

        input_data = IncomeStatementInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            statement_format=StatementFormat.FRENCH_PCG,
            consolidation_entries=entries,
        )

        result = calculate_income_statement(input_data)

        assert result.operating_result == Decimal("-20000.00")
        assert result.net_result == Decimal("-20000.00")
        assert result.operating_result < 0  # Loss

    def test_calculate_income_statement_no_entries(self):
        """Test income statement with no consolidation entries."""
        input_data = IncomeStatementInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            statement_format=StatementFormat.FRENCH_PCG,
            consolidation_entries=[],
        )

        result = calculate_income_statement(input_data)

        assert result.total_revenue == Decimal("0.00")
        assert result.total_expenses == Decimal("0.00")
        assert result.operating_result == Decimal("0.00")


class TestBalanceSheetLineGeneration:
    """Test balance sheet line generation."""

    def test_generate_balance_sheet_lines_with_assets(self):
        """Test generating balance sheet lines with assets."""
        asset_entries = [
            ConsolidationEntry(
                account_code="21300",
                account_name="Equipment",
                amount_sar=Decimal("50000"),
                is_revenue=False,
                consolidation_category="capex",
            ),
            ConsolidationEntry(
                account_code="21500",
                account_name="Furniture",
                amount_sar=Decimal("20000"),
                is_revenue=False,
                consolidation_category="capex",
            ),
        ]

        equity_amount = Decimal("70000")

        assets_lines, liabilities_lines = generate_balance_sheet_lines(
            asset_entries, [], equity_amount
        )

        # Check assets
        assert len(assets_lines) > 0
        assets_header = assets_lines[0]
        assert assets_header.line_type == StatementLineType.SECTION_HEADER
        assert "ACTIF" in assets_header.line_description

        # Check total assets line
        total_assets_line = assets_lines[-1]
        assert total_assets_line.line_type == StatementLineType.TOTAL
        assert total_assets_line.amount_sar == Decimal("70000.00")

        # Check liabilities
        assert len(liabilities_lines) > 0
        liabilities_header = liabilities_lines[0]
        assert "PASSIF" in liabilities_header.line_description

        # Check equity line
        equity_lines = [
            l for l in liabilities_lines if "Capitaux propres" in l.line_description
        ]
        assert len(equity_lines) == 1
        assert equity_lines[0].amount_sar == Decimal("70000.00")

    def test_generate_balance_sheet_lines_sorted_by_account(self):
        """Test that balance sheet lines are sorted by account code."""
        asset_entries = [
            ConsolidationEntry(
                account_code="21500",
                account_name="Furniture",
                amount_sar=Decimal("20000"),
                is_revenue=False,
                consolidation_category="capex",
            ),
            ConsolidationEntry(
                account_code="21300",
                account_name="Equipment",
                amount_sar=Decimal("50000"),
                is_revenue=False,
                consolidation_category="capex",
            ),
        ]

        assets_lines, _ = generate_balance_sheet_lines(asset_entries, [], Decimal("0"))

        # Get account lines
        account_lines = [
            l for l in assets_lines if l.line_type == StatementLineType.ACCOUNT_LINE
        ]

        # Should be sorted: 21300 before 21500
        assert account_lines[0].line_code == "21300"
        assert account_lines[1].line_code == "21500"

    def test_generate_balance_sheet_lines_no_assets(self):
        """Test balance sheet with no assets."""
        assets_lines, liabilities_lines = generate_balance_sheet_lines(
            [], [], Decimal("0")
        )

        # Should still have headers and totals
        assert len(assets_lines) > 0
        assert len(liabilities_lines) > 0

        # Total should be 0
        total_assets_line = assets_lines[-1]
        assert total_assets_line.amount_sar == Decimal("0.00")


class TestBalanceSheetCalculation:
    """Test complete balance sheet calculation."""

    def test_calculate_balance_sheet_balanced(self):
        """Test balanced balance sheet calculation."""
        asset_entries = [
            ConsolidationEntry(
                account_code="21300",
                account_name="Equipment",
                amount_sar=Decimal("100000"),
                is_revenue=False,
                consolidation_category="capex",
            ),
        ]

        input_data = BalanceSheetInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            asset_entries=asset_entries,
            liability_entries=[],
            equity_amount=Decimal("100000"),
        )

        result = calculate_balance_sheet(input_data)

        assert isinstance(result, BalanceSheetResult)
        assert result.total_assets == Decimal("100000.00")
        assert result.total_equity == Decimal("100000.00")
        assert result.total_liabilities == Decimal("0.00")
        assert result.is_balanced is True  # Assets = Equity + Liabilities

    def test_calculate_balance_sheet_with_liabilities(self):
        """Test balance sheet with liabilities."""
        asset_entries = [
            ConsolidationEntry(
                account_code="21300",
                account_name="Equipment",
                amount_sar=Decimal("150000"),
                is_revenue=False,
                consolidation_category="capex",
            ),
        ]

        liability_entries = [
            ConsolidationEntry(
                account_code="40000",
                account_name="Accounts Payable",
                amount_sar=Decimal("30000"),
                is_revenue=False,
                consolidation_category="liabilities",
            ),
        ]

        input_data = BalanceSheetInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            asset_entries=asset_entries,
            liability_entries=liability_entries,
            equity_amount=Decimal("120000"),
        )

        result = calculate_balance_sheet(input_data)

        assert result.total_assets == Decimal("150000.00")
        assert result.total_liabilities == Decimal("30000.00")
        assert result.total_equity == Decimal("120000.00")
        # 150000 = 120000 + 30000
        assert result.is_balanced is True

    def test_calculate_balance_sheet_unbalanced(self):
        """Test unbalanced balance sheet (within tolerance)."""
        # Intentionally unbalanced by small amount (within 0.01 tolerance)
        asset_entries = [
            ConsolidationEntry(
                account_code="21300",
                account_name="Equipment",
                amount_sar=Decimal("100000.00"),
                is_revenue=False,
                consolidation_category="capex",
            ),
        ]

        input_data = BalanceSheetInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            asset_entries=asset_entries,
            equity_amount=Decimal("100000.01"),  # Off by 0.01
        )

        result = calculate_balance_sheet(input_data)

        # Should still be considered balanced (within tolerance)
        assert result.is_balanced is True

    def test_calculate_balance_sheet_statement_names(self):
        """Test balance sheet statement names."""
        input_data = BalanceSheetInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            asset_entries=[],
            equity_amount=Decimal("0"),
        )

        result = calculate_balance_sheet(input_data)

        assert "Bilan - Actif" in result.assets_statement_name
        assert "Bilan - Passif" in result.liabilities_statement_name
        assert "2024/2025" in result.assets_statement_name


class TestCashFlowLineGeneration:
    """Test cash flow statement line generation."""

    def test_generate_cash_flow_lines_operating_activities(self):
        """Test cash flow lines for operating activities."""
        operating_entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Cash from tuition",
                amount_sar=Decimal("45000"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
            ConsolidationEntry(
                account_code="64110",
                account_name="Cash for salaries",
                amount_sar=Decimal("30000"),
                is_revenue=False,
                consolidation_category="personnel",
            ),
        ]

        lines = generate_cash_flow_lines(operating_entries, [], [])

        assert len(lines) > 0

        # Check header
        header = lines[0]
        assert header.line_type == StatementLineType.SECTION_HEADER
        assert "TRÉSORERIE" in header.line_description

        # Check operating activities section
        operating_section = [
            l for l in lines if "opérationnelles" in l.line_description.lower()
        ]
        assert len(operating_section) > 0

    def test_generate_cash_flow_lines_investing_activities(self):
        """Test cash flow lines for investing activities."""
        investing_entries = [
            ConsolidationEntry(
                account_code="21300",
                account_name="Equipment purchase",
                amount_sar=Decimal("50000"),
                is_revenue=False,
                consolidation_category="capex",
            ),
        ]

        lines = generate_cash_flow_lines([], investing_entries, [])

        # Investing activities should appear as negative (cash outflow)
        # Total should show net cash change
        net_change_line = lines[-1]
        assert net_change_line.line_type == StatementLineType.TOTAL


class TestCashFlowCalculation:
    """Test complete cash flow statement calculation."""

    def test_calculate_cash_flow_statement(self):
        """Test complete cash flow statement calculation."""
        operating_entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Operating revenue",
                amount_sar=Decimal("100000"),
                is_revenue=True,
                consolidation_category="revenue",
            ),
            ConsolidationEntry(
                account_code="64110",
                account_name="Operating expenses",
                amount_sar=Decimal("60000"),
                is_revenue=False,
                consolidation_category="personnel",
            ),
        ]

        investing_entries = [
            ConsolidationEntry(
                account_code="21300",
                account_name="CapEx",
                amount_sar=Decimal("20000"),
                is_revenue=False,
                consolidation_category="capex",
            ),
        ]

        input_data = CashFlowInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            operating_entries=operating_entries,
            investing_entries=investing_entries,
        )

        result = calculate_cash_flow_statement(input_data)

        assert isinstance(result, CashFlowResult)
        assert result.operating_cash_flow == Decimal("40000.00")  # 100k - 60k
        assert result.investing_cash_flow == Decimal("-20000.00")  # -20k (outflow)
        assert result.financing_cash_flow == Decimal("0.00")
        assert result.net_cash_change == Decimal("20000.00")  # 40k - 20k


class TestValidationFunctions:
    """Test validation functions."""

    def test_validate_statement_format_pcg(self):
        """Test validating PCG format."""
        fmt = validate_statement_format("pcg")
        assert fmt == StatementFormat.FRENCH_PCG

        fmt = validate_statement_format("french_pcg")
        assert fmt == StatementFormat.FRENCH_PCG

    def test_validate_statement_format_ifrs(self):
        """Test validating IFRS format."""
        fmt = validate_statement_format("ifrs")
        assert fmt == StatementFormat.IFRS

    def test_validate_statement_format_invalid(self):
        """Test validating invalid format."""
        with pytest.raises(ValueError, match="Invalid format"):
            validate_statement_format("invalid")

    def test_validate_period_all_periods(self):
        """Test validating all period types."""
        assert validate_period("p1") == FinancialPeriod.PERIOD_1
        assert validate_period("summer") == FinancialPeriod.SUMMER
        assert validate_period("p2") == FinancialPeriod.PERIOD_2
        assert validate_period("annual") == FinancialPeriod.ANNUAL

    def test_validate_period_case_insensitive(self):
        """Test period validation is case insensitive."""
        assert validate_period("P1") == FinancialPeriod.PERIOD_1
        assert validate_period("SUMMER") == FinancialPeriod.SUMMER

    def test_validate_period_invalid(self):
        """Test validating invalid period."""
        with pytest.raises(ValueError, match="Invalid period"):
            validate_period("invalid")

    def test_validate_consolidation_entry_revenue_account(self):
        """Test validating revenue entry with correct account code."""
        entry = ConsolidationEntry(
            account_code="70110",
            account_name="Tuition",
            amount_sar=Decimal("1000"),
            is_revenue=True,
            consolidation_category="revenue",
        )

        validate_consolidation_entry(entry)  # Should not raise

    def test_validate_consolidation_entry_expense_account(self):
        """Test validating expense entry with correct account code."""
        entry = ConsolidationEntry(
            account_code="64110",
            account_name="Salaries",
            amount_sar=Decimal("500"),
            is_revenue=False,
            consolidation_category="personnel",
        )

        validate_consolidation_entry(entry)  # Should not raise

    def test_validate_consolidation_entry_invalid_revenue_code(self):
        """Test validation fails for revenue with wrong account code."""
        entry = ConsolidationEntry(
            account_code="64110",  # Expense code (6xxxx)
            account_name="Invalid",
            amount_sar=Decimal("1000"),
            is_revenue=True,  # But marked as revenue!
            consolidation_category="revenue",
        )

        with pytest.raises(InvalidFinancialStatementError, match="must start with 7"):
            validate_consolidation_entry(entry)

    def test_validate_consolidation_entry_invalid_expense_code(self):
        """Test validation fails for expense with wrong account code."""
        entry = ConsolidationEntry(
            account_code="70110",  # Revenue code (7xxxx)
            account_name="Invalid",
            amount_sar=Decimal("500"),
            is_revenue=False,  # But marked as expense!
            consolidation_category="personnel",
        )

        with pytest.raises(InvalidFinancialStatementError, match="must start with 6"):
            validate_consolidation_entry(entry)

    def test_validate_consolidation_entry_non_digit_code(self):
        """Test validation fails for non-digit account code."""
        entry = ConsolidationEntry(
            account_code="ABC123",
            account_name="Invalid",
            amount_sar=Decimal("1000"),
            is_revenue=True,
            consolidation_category="revenue",
        )

        with pytest.raises(InvalidFinancialStatementError, match="must contain only digits"):
            validate_consolidation_entry(entry)

    def test_validate_consolidation_entry_invalid_length(self):
        """Test validation fails for invalid account code length."""
        # Too short
        entry = ConsolidationEntry(
            account_code="70",
            account_name="Invalid",
            amount_sar=Decimal("1000"),
            is_revenue=True,
            consolidation_category="revenue",
        )

        with pytest.raises(InvalidFinancialStatementError, match="must be 3-6 digits"):
            validate_consolidation_entry(entry)

    def test_validate_consolidation_entry_negative_amount(self):
        """Test validation fails for negative amount."""
        # Pydantic validation catches this first
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            ConsolidationEntry(
                account_code="70110",
                account_name="Invalid",
                amount_sar=Decimal("-1000"),  # Negative!
                is_revenue=True,
                consolidation_category="revenue",
            )

    def test_validate_statement_line_valid(self):
        """Test validating valid statement line."""
        line = StatementLine(
            line_number=1,
            line_type=StatementLineType.ACCOUNT_LINE,
            indent_level=2,
            line_code="70110",
            line_description="Tuition",
            amount_sar=Decimal("1000"),
            is_bold=False,
            is_underlined=False,
        )

        validate_statement_line(line)  # Should not raise

    def test_validate_statement_line_invalid_line_number(self):
        """Test validation fails for invalid line number."""
        # Pydantic now validates at model creation time
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            StatementLine(
                line_number=0,  # Invalid - must be >= 1
                line_type=StatementLineType.ACCOUNT_LINE,
                indent_level=0,
                line_description="Test",
            )

    def test_validate_statement_line_invalid_indent(self):
        """Test validation fails for invalid indent level."""
        # Pydantic now validates at model creation time
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="less than or equal to 5"):
            StatementLine(
                line_number=1,
                line_type=StatementLineType.ACCOUNT_LINE,
                indent_level=10,  # Invalid - must be 0-5
                line_description="Test",
            )

    def test_validate_statement_line_empty_description(self):
        """Test validation fails for empty description."""
        line = StatementLine(
            line_number=1,
            line_type=StatementLineType.ACCOUNT_LINE,
            indent_level=0,
            line_description="   ",  # Empty/whitespace only
        )

        with pytest.raises(InvalidFinancialStatementError, match="cannot be empty"):
            validate_statement_line(line)

    def test_validate_balance_sheet_balance_balanced(self):
        """Test balance sheet balance validation when balanced."""
        result = validate_balance_sheet_balance(
            Decimal("100000"),  # Assets
            Decimal("60000"),   # Liabilities
            Decimal("40000"),   # Equity
        )

        assert result is True

    def test_validate_balance_sheet_balance_unbalanced(self):
        """Test balance sheet balance validation when unbalanced."""
        with pytest.raises(InvalidFinancialStatementError, match="does not balance"):
            validate_balance_sheet_balance(
                Decimal("100000"),  # Assets
                Decimal("50000"),   # Liabilities
                Decimal("40000"),   # Equity (should be 50k to balance)
            )

    def test_validate_balance_sheet_balance_within_tolerance(self):
        """Test balance sheet accepts small differences within tolerance."""
        result = validate_balance_sheet_balance(
            Decimal("100000.00"),
            Decimal("60000.00"),
            Decimal("39999.99"),  # Off by 0.01
            tolerance=Decimal("0.01"),
        )

        assert result is True

    def test_validate_account_code_range_valid(self):
        """Test account code range validation for valid code."""
        result = validate_account_code_range("70110", "70000", "77999")
        assert result is True

    def test_validate_account_code_range_invalid(self):
        """Test account code range validation for invalid code."""
        with pytest.raises(ValueError, match="outside range"):
            validate_account_code_range("60110", "70000", "77999")

    def test_validate_revenue_expense_split_valid(self):
        """Test revenue/expense split validation when correct."""
        revenue = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Revenue",
                amount_sar=Decimal("1000"),
                is_revenue=True,
                consolidation_category="revenue",
            )
        ]

        expense = [
            ConsolidationEntry(
                account_code="64110",
                account_name="Expense",
                amount_sar=Decimal("500"),
                is_revenue=False,
                consolidation_category="personnel",
            )
        ]

        validate_revenue_expense_split(revenue, expense)  # Should not raise

    def test_validate_revenue_expense_split_invalid(self):
        """Test revenue/expense split validation fails when incorrect."""
        revenue = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Revenue",
                amount_sar=Decimal("1000"),
                is_revenue=False,  # Wrong! Should be True
                consolidation_category="revenue",
            )
        ]

        with pytest.raises(InvalidFinancialStatementError, match="marked as expense"):
            validate_revenue_expense_split(revenue, [])

    def test_validate_statement_line_sequence_valid(self):
        """Test statement line sequence validation when correct."""
        lines = [
            StatementLine(
                line_number=1,
                line_type=StatementLineType.SECTION_HEADER,
                indent_level=0,
                line_description="Header",
            ),
            StatementLine(
                line_number=2,
                line_type=StatementLineType.ACCOUNT_LINE,
                indent_level=2,
                line_description="Line 1",
                amount_sar=Decimal("100"),
            ),
            StatementLine(
                line_number=3,
                line_type=StatementLineType.TOTAL,
                indent_level=0,
                line_description="Total",
                amount_sar=Decimal("100"),
            ),
        ]

        validate_statement_line_sequence(lines)  # Should not raise

    def test_validate_statement_line_sequence_broken(self):
        """Test statement line sequence validation fails when broken."""
        lines = [
            StatementLine(
                line_number=1,
                line_type=StatementLineType.SECTION_HEADER,
                indent_level=0,
                line_description="Header",
            ),
            StatementLine(
                line_number=5,  # Broken! Should be 2
                line_type=StatementLineType.ACCOUNT_LINE,
                indent_level=2,
                line_description="Line 1",
            ),
        ]

        with pytest.raises(InvalidFinancialStatementError, match="sequence broken"):
            validate_statement_line_sequence(lines)

    def test_validate_statement_line_sequence_empty(self):
        """Test statement line sequence validation with empty list."""
        validate_statement_line_sequence([])  # Should not raise

    def test_validate_pcg_account_code_valid(self):
        """Test PCG account code validation for valid codes."""
        validate_pcg_account_code("70110")  # Valid
        validate_pcg_account_code("641")    # Valid (3 digits)
        validate_pcg_account_code("701105") # Valid (6 digits)

    def test_validate_pcg_account_code_non_digits(self):
        """Test PCG validation fails for non-digit codes."""
        with pytest.raises(ValueError, match="must contain only digits"):
            validate_pcg_account_code("ABC123")

    def test_validate_pcg_account_code_invalid_length(self):
        """Test PCG validation fails for invalid length."""
        with pytest.raises(ValueError, match="must be 3-6 digits"):
            validate_pcg_account_code("70")  # Too short

        with pytest.raises(ValueError, match="must be 3-6 digits"):
            validate_pcg_account_code("7011051")  # Too long

    def test_validate_pcg_account_code_invalid_class(self):
        """Test PCG validation fails for invalid first digit."""
        with pytest.raises(ValueError, match="must be 1-8"):
            validate_pcg_account_code("90110")  # Class 9 invalid


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""

    def test_income_statement_very_large_amounts(self):
        """Test income statement with very large amounts."""
        entries = [
            ConsolidationEntry(
                account_code="70110",
                account_name="Revenue",
                amount_sar=Decimal("9999999999.99"),  # ~10 billion
                is_revenue=True,
                consolidation_category="revenue",
            ),
        ]

        input_data = IncomeStatementInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            statement_format=StatementFormat.FRENCH_PCG,
            consolidation_entries=entries,
        )

        result = calculate_income_statement(input_data)

        assert result.total_revenue == Decimal("9999999999.99")

    def test_balance_sheet_zero_equity(self):
        """Test balance sheet with zero equity."""
        input_data = BalanceSheetInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            asset_entries=[],
            equity_amount=Decimal("0"),
        )

        result = calculate_balance_sheet(input_data)

        assert result.total_equity == Decimal("0.00")
        assert result.is_balanced is True

    def test_cash_flow_all_categories_empty(self):
        """Test cash flow with all categories empty."""
        input_data = CashFlowInput(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            operating_entries=[],
        )

        result = calculate_cash_flow_statement(input_data)

        assert result.operating_cash_flow == Decimal("0.00")
        assert result.investing_cash_flow == Decimal("0.00")
        assert result.financing_cash_flow == Decimal("0.00")
        assert result.net_cash_change == Decimal("0.00")

    def test_statement_line_maximum_indent(self):
        """Test statement line with maximum indent level."""
        line = format_statement_line(
            1,
            StatementLineType.ACCOUNT_LINE,
            "Deeply nested",
            indent_level=5,  # Maximum
        )

        assert line.indent_level == 5

    def test_consolidation_entry_decimal_precision(self):
        """Test consolidation entry quantizes to 2 decimals."""
        entry = ConsolidationEntry(
            account_code="70110",
            account_name="Test",
            amount_sar=Decimal("1000.12345"),  # More than 2 decimals
            is_revenue=True,
            consolidation_category="revenue",
        )

        # Should be quantized to 2 decimals
        assert entry.amount_sar == Decimal("1000.12")

    def test_period_totals_immutability(self):
        """Test that PeriodTotals is immutable."""
        totals = PeriodTotals(
            period=FinancialPeriod.ANNUAL,
            total_revenue=Decimal("100"),
            total_expenses=Decimal("50"),
            operating_result=Decimal("50"),
            net_result=Decimal("50"),
        )

        with pytest.raises(ValidationError):
            totals.total_revenue = Decimal("200")  # Should fail - frozen

    def test_income_statement_result_immutability(self):
        """Test that IncomeStatementResult is immutable."""
        result = IncomeStatementResult(
            version_id=uuid4(),
            fiscal_year="2024-2025",
            academic_year="2024/2025",
            statement_format=StatementFormat.FRENCH_PCG,
            statement_name="Test",
            lines=[],
            total_revenue=Decimal("100"),
            total_expenses=Decimal("50"),
            operating_result=Decimal("50"),
            net_result=Decimal("50"),
        )

        with pytest.raises(ValidationError):
            result.total_revenue = Decimal("200")  # Should fail - frozen
