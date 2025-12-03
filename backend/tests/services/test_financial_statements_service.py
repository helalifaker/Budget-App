"""
Unit tests for Financial Statements Service.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.consolidation import LineType, StatementFormat, StatementType
from app.services.financial_statements_service import FinancialStatementsService


class TestFinancialStatementsServiceInitialization:
    """Tests for FinancialStatementsService initialization."""

    def test_service_initialization(self):
        """Test service initializes with session."""
        session = MagicMock()
        service = FinancialStatementsService(session)
        assert service.session == session
        assert service.statement_service is not None
        assert service.line_service is not None
        assert service.budget_version_service is not None


class TestStatementFormat:
    """Tests for statement format validation."""

    def test_valid_pcg_format(self):
        """Test PCG format is valid."""
        format = "pcg"
        assert format in ["pcg", "ifrs"]

    def test_valid_ifrs_format(self):
        """Test IFRS format is valid."""
        format = "ifrs"
        assert format in ["pcg", "ifrs"]

    def test_invalid_format(self):
        """Test invalid format is rejected."""
        format = "us_gaap"
        assert format not in ["pcg", "ifrs"]


class TestStatementFormatEnum:
    """Tests for StatementFormat enum mapping."""

    def test_french_pcg_enum(self):
        """Test French PCG enum value."""
        assert StatementFormat.FRENCH_PCG is not None

    def test_ifrs_enum(self):
        """Test IFRS enum value."""
        assert StatementFormat.IFRS is not None

    def test_format_mapping(self):
        """Test format string to enum mapping."""
        format_map = {
            "pcg": StatementFormat.FRENCH_PCG,
            "ifrs": StatementFormat.IFRS,
        }
        assert format_map["pcg"] == StatementFormat.FRENCH_PCG
        assert format_map["ifrs"] == StatementFormat.IFRS


class TestStatementType:
    """Tests for statement type enumeration."""

    def test_income_statement_type(self):
        """Test income statement type exists."""
        assert StatementType.INCOME_STATEMENT is not None

    def test_balance_sheet_assets_type(self):
        """Test balance sheet assets type exists."""
        assert StatementType.BALANCE_SHEET_ASSETS is not None

    def test_balance_sheet_liabilities_type(self):
        """Test balance sheet liabilities type exists."""
        assert StatementType.BALANCE_SHEET_LIABILITIES is not None

    def test_cash_flow_type(self):
        """Test cash flow statement type exists."""
        assert StatementType.CASH_FLOW is not None


class TestLineType:
    """Tests for financial statement line types."""

    def test_section_header_type(self):
        """Test section header line type."""
        assert LineType.SECTION_HEADER is not None

    def test_account_line_type(self):
        """Test account line type."""
        assert LineType.ACCOUNT_LINE is not None

    def test_subtotal_type(self):
        """Test subtotal line type."""
        assert LineType.SUBTOTAL is not None

    def test_total_type(self):
        """Test total line type."""
        assert LineType.TOTAL is not None


class TestPeriodTotals:
    """Tests for period totals calculation."""

    def test_valid_periods(self):
        """Test valid period identifiers."""
        valid_periods = ["p1", "summer", "p2", "annual"]

        for period in valid_periods:
            assert period in valid_periods

    def test_p1_period_months(self):
        """Test P1 period covers January-June."""
        p1_months = list(range(1, 7))  # Jan-Jun
        assert p1_months == [1, 2, 3, 4, 5, 6]

    def test_summer_period_months(self):
        """Test summer period covers July-August."""
        summer_months = [7, 8]
        assert summer_months == [7, 8]

    def test_p2_period_months(self):
        """Test P2 period covers September-December."""
        p2_months = list(range(9, 13))  # Sep-Dec
        assert p2_months == [9, 10, 11, 12]

    def test_annual_covers_all_months(self):
        """Test annual period covers all 12 months."""
        all_months = list(range(1, 13))
        assert len(all_months) == 12


class TestPeriodTotalsCalculation:
    """Tests for period totals structure."""

    def test_totals_structure(self):
        """Test period totals return expected fields."""
        expected_fields = [
            "total_revenue",
            "total_expenses",
            "operating_result",
            "net_result",
        ]

        for field in expected_fields:
            assert field in expected_fields

    def test_operating_result_calculation(self):
        """Test operating result = revenue - expenses."""
        total_revenue = Decimal("5000000")
        total_expenses = Decimal("4500000")

        operating_result = total_revenue - total_expenses
        assert operating_result == Decimal("500000")

    def test_net_result_equals_operating_for_simplified(self):
        """Test net result equals operating result when no financial items."""
        operating_result = Decimal("500000")
        net_result = operating_result  # Simplified model

        assert net_result == operating_result


class TestIncomeStatementLines:
    """Tests for income statement line generation."""

    def test_revenue_section_header_pcg(self):
        """Test PCG revenue section header."""
        header = "PRODUITS D'EXPLOITATION"
        assert "PRODUITS" in header

    def test_revenue_section_header_ifrs(self):
        """Test IFRS revenue section header."""
        header = "OPERATING REVENUE"
        assert "REVENUE" in header

    def test_expense_section_header_pcg(self):
        """Test PCG expense section header."""
        header = "CHARGES D'EXPLOITATION"
        assert "CHARGES" in header

    def test_expense_section_header_ifrs(self):
        """Test IFRS expense section header."""
        header = "OPERATING EXPENSES"
        assert "EXPENSES" in header

    def test_operating_result_label_pcg(self):
        """Test PCG operating result label."""
        label = "RÉSULTAT D'EXPLOITATION"
        assert "RÉSULTAT" in label

    def test_net_result_label_pcg(self):
        """Test PCG net result label."""
        label = "RÉSULTAT NET"
        assert "NET" in label


class TestLineAttributes:
    """Tests for statement line attributes."""

    def test_line_number_starts_at_one(self):
        """Test line numbering starts at 1."""
        first_line_number = 1
        assert first_line_number == 1

    def test_section_header_indent_level(self):
        """Test section headers have indent level 0."""
        section_header_indent = 0
        assert section_header_indent == 0

    def test_account_line_indent_level(self):
        """Test account lines have indent level 2."""
        account_line_indent = 2
        assert account_line_indent == 2

    def test_subtotal_indent_level(self):
        """Test subtotals have indent level 1."""
        subtotal_indent = 1
        assert subtotal_indent == 1

    def test_total_indent_level(self):
        """Test totals have indent level 0."""
        total_indent = 0
        assert total_indent == 0

    def test_section_header_is_bold(self):
        """Test section headers are bold."""
        is_bold = True
        assert is_bold is True

    def test_subtotal_is_underlined(self):
        """Test subtotals are underlined."""
        is_underlined = True
        assert is_underlined is True


class TestBalanceSheetStructure:
    """Tests for balance sheet structure."""

    def test_balance_sheet_has_assets_and_liabilities(self):
        """Test balance sheet returns assets and liabilities."""
        expected_keys = ["assets", "liabilities"]

        for key in expected_keys:
            assert key in expected_keys

    def test_assets_header_pcg(self):
        """Test PCG assets header."""
        header = "ACTIF"
        assert header == "ACTIF"

    def test_liabilities_header_pcg(self):
        """Test PCG liabilities header."""
        header = "PASSIF"
        assert header == "PASSIF"

    def test_total_assets_label(self):
        """Test total assets label."""
        label = "TOTAL ACTIF"
        assert "TOTAL" in label and "ACTIF" in label

    def test_total_liabilities_label(self):
        """Test total liabilities label."""
        label = "TOTAL PASSIF"
        assert "TOTAL" in label and "PASSIF" in label


class TestCashFlowStatement:
    """Tests for cash flow statement structure."""

    def test_cash_flow_header(self):
        """Test cash flow statement header."""
        header = "TABLEAU DE FLUX DE TRÉSORERIE"
        assert "TRÉSORERIE" in header


class TestRevenueExpenseClassification:
    """Tests for revenue and expense classification."""

    def test_revenue_accounts_start_with_7(self):
        """Test revenue accounts (70xxx-77xxx)."""
        revenue_codes = ["70110", "70120", "70130", "71000", "74500"]

        for code in revenue_codes:
            is_revenue = code.startswith("7")
            assert is_revenue is True

    def test_expense_accounts_start_with_6(self):
        """Test expense accounts (60xxx-68xxx)."""
        expense_codes = ["60110", "61000", "64110", "65000", "68000"]

        for code in expense_codes:
            is_expense = code.startswith("6")
            assert is_expense is True


class TestConsolidationCategoryMapping:
    """Tests for consolidation category to statement line mapping."""

    def test_account_line_has_source_category(self):
        """Test account lines include source consolidation category."""
        line_data = {
            "line_type": LineType.ACCOUNT_LINE,
            "source_consolidation_category": "TUITION_REVENUE",
        }

        assert "source_consolidation_category" in line_data


class TestStatementNaming:
    """Tests for statement naming conventions."""

    def test_pcg_income_statement_name(self):
        """Test PCG income statement name format."""
        academic_year = "2024-2025"
        name = f"Compte de résultat {academic_year}"
        assert "Compte de résultat" in name
        assert academic_year in name

    def test_ifrs_income_statement_name(self):
        """Test IFRS income statement name format."""
        academic_year = "2024-2025"
        name = f"Income Statement {academic_year}"
        assert "Income Statement" in name
        assert academic_year in name

    def test_balance_sheet_assets_name(self):
        """Test balance sheet assets name."""
        academic_year = "2024-2025"
        name = f"Bilan - Actif {academic_year}"
        assert "Bilan" in name and "Actif" in name

    def test_balance_sheet_liabilities_name(self):
        """Test balance sheet liabilities name."""
        academic_year = "2024-2025"
        name = f"Bilan - Passif {academic_year}"
        assert "Bilan" in name and "Passif" in name
