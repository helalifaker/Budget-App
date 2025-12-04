"""
Tests for FinancialStatementsService.

Tests cover:
- Income statement generation (PCG and IFRS formats)
- Balance sheet generation
- Period totals calculation
- Statement line calculation
- Validation errors
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import BudgetVersion
from app.models.consolidation import (
    BudgetConsolidation,
    ConsolidationCategory,
    FinancialStatement,
    LineType,
    StatementFormat,
    StatementType,
)
from app.services.exceptions import ValidationError
from app.services.financial_statements_service import FinancialStatementsService
from sqlalchemy.ext.asyncio import AsyncSession


class TestGetIncomeStatement:
    """Tests for income statement retrieval and generation."""

    @pytest.mark.asyncio
    async def test_get_income_statement_pcg_format(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test generating income statement in PCG format."""
        # Create consolidation data
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Scolarité T1",
            amount_sar=Decimal("2000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        expense = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="personnel_cost_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.PERSONNEL_TEACHING,
            account_code="64110",
            account_name="Salaires enseignants",
            amount_sar=Decimal("1500000.00"),
            is_revenue=False,
            created_by_id=test_user_id,
        )
        db_session.add_all([revenue, expense])
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        result = await service.get_income_statement(test_budget_version.id, format="pcg")

        assert result is not None
        assert result.statement_type == StatementType.INCOME_STATEMENT
        assert result.statement_format == StatementFormat.FRENCH_PCG
        assert result.budget_version_id == test_budget_version.id

    @pytest.mark.asyncio
    async def test_get_income_statement_ifrs_format(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test generating income statement in IFRS format."""
        # Create consolidation data
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Tuition T1",
            amount_sar=Decimal("1000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        db_session.add(revenue)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        result = await service.get_income_statement(test_budget_version.id, format="ifrs")

        assert result is not None
        assert result.statement_type == StatementType.INCOME_STATEMENT
        assert result.statement_format == StatementFormat.IFRS

    @pytest.mark.asyncio
    async def test_get_income_statement_invalid_format(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test invalid format raises ValidationError."""
        service = FinancialStatementsService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.get_income_statement(test_budget_version.id, format="invalid")

        assert "Invalid format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_income_statement_existing(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test retrieval of existing income statement."""
        # Create existing statement
        existing_statement = FinancialStatement(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            statement_type=StatementType.INCOME_STATEMENT,
            statement_format=StatementFormat.FRENCH_PCG,
            statement_name="Compte de résultat 2024-2025",
            fiscal_year=2025,
            total_amount_sar=Decimal("500000.00"),
            is_calculated=True,
        )
        db_session.add(existing_statement)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        result = await service.get_income_statement(test_budget_version.id, format="pcg")

        assert result.id == existing_statement.id

    @pytest.mark.asyncio
    async def test_get_income_statement_empty_consolidation(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test income statement generation with no consolidation data."""
        service = FinancialStatementsService(db_session)
        result = await service.get_income_statement(test_budget_version.id, format="pcg")

        assert result is not None
        assert result.total_amount_sar == Decimal("0.00")


class TestGetBalanceSheet:
    """Tests for balance sheet generation."""

    @pytest.mark.asyncio
    async def test_get_balance_sheet_generates_both_parts(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test balance sheet generates assets and liabilities."""
        # Create CapEx consolidation for assets
        capex = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="capex_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.CAPEX_EQUIPMENT,
            account_code="21500",
            account_name="Equipment",
            amount_sar=Decimal("500000.00"),
            is_revenue=False,
            created_by_id=test_user_id,
        )
        db_session.add(capex)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        result = await service.get_balance_sheet(test_budget_version.id)

        assert "assets" in result
        assert "liabilities" in result
        assert result["assets"].statement_type == StatementType.BALANCE_SHEET_ASSETS
        assert result["liabilities"].statement_type == StatementType.BALANCE_SHEET_LIABILITIES

    @pytest.mark.asyncio
    async def test_get_balance_sheet_existing(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieval of existing balance sheet."""
        # Create existing statements
        assets = FinancialStatement(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            statement_type=StatementType.BALANCE_SHEET_ASSETS,
            statement_format=StatementFormat.FRENCH_PCG,
            statement_name="Bilan - Actif 2024-2025",
            fiscal_year=2025,
            total_amount_sar=Decimal("500000.00"),
            is_calculated=True,
        )
        liabilities = FinancialStatement(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            statement_type=StatementType.BALANCE_SHEET_LIABILITIES,
            statement_format=StatementFormat.FRENCH_PCG,
            statement_name="Bilan - Passif 2024-2025",
            fiscal_year=2025,
            total_amount_sar=Decimal("500000.00"),
            is_calculated=True,
        )
        db_session.add_all([assets, liabilities])
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        result = await service.get_balance_sheet(test_budget_version.id)

        assert result["assets"].id == assets.id
        assert result["liabilities"].id == liabilities.id


class TestCalculateStatementLines:
    """Tests for statement line calculation."""

    @pytest.mark.asyncio
    async def test_calculate_income_statement_lines(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test income statement line calculation."""
        # Create consolidation data
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Tuition",
            amount_sar=Decimal("2000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        db_session.add(revenue)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.INCOME_STATEMENT,
            StatementFormat.FRENCH_PCG,
        )

        assert len(lines) > 0
        # Should have section headers, account lines, subtotals, and totals
        line_types = [line.get("line_type") for line in lines]
        assert LineType.SECTION_HEADER in line_types
        assert LineType.ACCOUNT_LINE in line_types

    @pytest.mark.asyncio
    async def test_calculate_balance_sheet_assets_lines(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test balance sheet assets line calculation."""
        capex = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="capex_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.CAPEX_EQUIPMENT,
            account_code="21500",
            account_name="Fixed Assets",
            amount_sar=Decimal("300000.00"),
            is_revenue=False,
            created_by_id=test_user_id,
        )
        db_session.add(capex)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.BALANCE_SHEET_ASSETS,
            StatementFormat.FRENCH_PCG,
        )

        assert len(lines) > 0
        # Should have header and total at minimum
        line_types = [line.get("line_type") for line in lines]
        assert LineType.SECTION_HEADER in line_types
        assert LineType.TOTAL in line_types

    @pytest.mark.asyncio
    async def test_calculate_balance_sheet_liabilities_lines(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test balance sheet liabilities line calculation."""
        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.BALANCE_SHEET_LIABILITIES,
            StatementFormat.FRENCH_PCG,
        )

        assert len(lines) > 0
        # Should have header, equity line, and total
        line_descriptions = [line.get("line_description") for line in lines]
        assert "PASSIF" in line_descriptions

    @pytest.mark.asyncio
    async def test_calculate_cash_flow_lines(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test cash flow statement line calculation."""
        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.CASH_FLOW,
            StatementFormat.FRENCH_PCG,
        )

        assert len(lines) > 0
        # Should have at least a header
        line_descriptions = [line.get("line_description") for line in lines]
        assert "TABLEAU DE FLUX DE TRÉSORERIE" in line_descriptions

    @pytest.mark.asyncio
    async def test_cash_flow_totals_and_signs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Cash flow subtotals should reflect operating and investing cash movements."""
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Tuition",
            amount_sar=Decimal("1000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        expense = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="operating_costs",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.OPERATING_SUPPLIES,
            account_code="60610",
            account_name="Supplies",
            amount_sar=Decimal("400000.00"),
            is_revenue=False,
            created_by_id=test_user_id,
        )
        capex = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="capex_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.CAPEX_EQUIPMENT,
            account_code="21540",
            account_name="Equipment",
            amount_sar=Decimal("200000.00"),
            is_revenue=False,
            created_by_id=test_user_id,
        )
        db_session.add_all([revenue, expense, capex])
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.CASH_FLOW,
            StatementFormat.FRENCH_PCG,
        )

        def _find(description: str) -> dict:
            return next(line for line in lines if line["line_description"] == description)

        operating_subtotal = _find("Total flux opérationnels")
        investing_subtotal = _find("Total flux d'investissement")
        net_change = _find("Variation nette de trésorerie")

        assert operating_subtotal["amount_sar"] == Decimal("600000.00")
        assert investing_subtotal["amount_sar"] == Decimal("-200000.00")
        assert net_change["amount_sar"] == Decimal("400000.00")


class TestGetPeriodTotals:
    """Tests for period totals calculation."""

    @pytest.mark.asyncio
    async def test_get_period_totals_p1(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test P1 (Jan-Jun) period totals."""
        # Create consolidation data
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Tuition",
            amount_sar=Decimal("2000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        expense = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="personnel_cost_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.PERSONNEL_TEACHING,
            account_code="64110",
            account_name="Salaries",
            amount_sar=Decimal("1500000.00"),
            is_revenue=False,
            created_by_id=test_user_id,
        )
        db_session.add_all([revenue, expense])
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        result = await service.get_period_totals(test_budget_version.id, "p1")

        assert "total_revenue" in result
        assert "total_expenses" in result
        assert "operating_result" in result
        assert "net_result" in result
        assert result["total_revenue"] == Decimal("2000000.00")
        assert result["total_expenses"] == Decimal("1500000.00")
        assert result["operating_result"] == Decimal("500000.00")

    @pytest.mark.asyncio
    async def test_get_period_totals_summer(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test summer period totals."""
        service = FinancialStatementsService(db_session)
        result = await service.get_period_totals(test_budget_version.id, "summer")

        assert result["total_revenue"] == Decimal("0.00")
        assert result["total_expenses"] == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_get_period_totals_p2(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test P2 (Sep-Dec) period totals."""
        service = FinancialStatementsService(db_session)
        result = await service.get_period_totals(test_budget_version.id, "p2")

        assert "total_revenue" in result
        assert "operating_result" in result

    @pytest.mark.asyncio
    async def test_get_period_totals_annual(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test annual period totals."""
        # Create revenue
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_OTHER,
            account_code="70800",
            account_name="Other Revenue",
            amount_sar=Decimal("100000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        db_session.add(revenue)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        result = await service.get_period_totals(test_budget_version.id, "annual")

        assert result["total_revenue"] == Decimal("100000.00")

    @pytest.mark.asyncio
    async def test_get_period_totals_invalid_period(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test invalid period raises ValidationError."""
        service = FinancialStatementsService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.get_period_totals(test_budget_version.id, "invalid")

        assert "Invalid period" in str(exc_info.value)


class TestIncomeStatementCalculation:
    """Tests for detailed income statement calculation."""

    @pytest.mark.asyncio
    async def test_income_statement_revenue_total(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test revenue total calculation in income statement."""
        # Create multiple revenue items
        revenues = [
            BudgetConsolidation(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                source_table="revenue_plans",
                source_count=1,
            is_calculated=True,
                consolidation_category=ConsolidationCategory.REVENUE_TUITION,
                account_code="70110",
                account_name="Tuition T1",
                amount_sar=Decimal("1000000.00"),
                is_revenue=True,
                created_by_id=test_user_id,
            ),
            BudgetConsolidation(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                source_table="revenue_plans",
                source_count=1,
            is_calculated=True,
                consolidation_category=ConsolidationCategory.REVENUE_FEES,
                account_code="70140",
                account_name="DAI",
                amount_sar=Decimal("500000.00"),
                is_revenue=True,
                created_by_id=test_user_id,
            ),
        ]
        db_session.add_all(revenues)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.INCOME_STATEMENT,
            StatementFormat.FRENCH_PCG,
        )

        # Find revenue subtotal
        revenue_subtotal = next(
            (line for line in lines if line.get("line_type") == LineType.SUBTOTAL
             and "Produits" in str(line.get("line_description", ""))),
            None
        )
        assert revenue_subtotal is not None
        assert revenue_subtotal["amount_sar"] == Decimal("1500000.00")

    @pytest.mark.asyncio
    async def test_income_statement_expense_total(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test expense total calculation in income statement."""
        # Create expense items
        expenses = [
            BudgetConsolidation(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                source_table="personnel_cost_plans",
                source_count=1,
            is_calculated=True,
                consolidation_category=ConsolidationCategory.PERSONNEL_TEACHING,
                account_code="64110",
                account_name="Teaching Salaries",
                amount_sar=Decimal("800000.00"),
                is_revenue=False,
                created_by_id=test_user_id,
            ),
            BudgetConsolidation(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                source_table="operating_cost_plans",
                source_count=1,
            is_calculated=True,
                consolidation_category=ConsolidationCategory.OPERATING_OTHER,
                account_code="61100",
                account_name="Rent",
                amount_sar=Decimal("200000.00"),
                is_revenue=False,
                created_by_id=test_user_id,
            ),
        ]
        db_session.add_all(expenses)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.INCOME_STATEMENT,
            StatementFormat.FRENCH_PCG,
        )

        # Find expense subtotal
        expense_subtotal = next(
            (line for line in lines if line.get("line_type") == LineType.SUBTOTAL
             and "Charges" in str(line.get("line_description", ""))),
            None
        )
        assert expense_subtotal is not None
        assert expense_subtotal["amount_sar"] == Decimal("1000000.00")

    @pytest.mark.asyncio
    async def test_income_statement_operating_result(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test operating result calculation."""
        # Create revenue and expense
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Tuition",
            amount_sar=Decimal("3000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        expense = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="personnel_cost_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.PERSONNEL_TEACHING,
            account_code="64110",
            account_name="Salaries",
            amount_sar=Decimal("2000000.00"),
            is_revenue=False,
            created_by_id=test_user_id,
        )
        db_session.add_all([revenue, expense])
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.INCOME_STATEMENT,
            StatementFormat.FRENCH_PCG,
        )

        # Find operating result
        operating_result = next(
            (line for line in lines if line.get("line_type") == LineType.TOTAL
             and "EXPLOITATION" in str(line.get("line_description", ""))),
            None
        )
        assert operating_result is not None
        assert operating_result["amount_sar"] == Decimal("1000000.00")


class TestStatementLineFormatting:
    """Tests for statement line formatting."""

    @pytest.mark.asyncio
    async def test_line_numbers_sequential(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test line numbers are sequential."""
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Tuition",
            amount_sar=Decimal("1000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        db_session.add(revenue)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.INCOME_STATEMENT,
            StatementFormat.FRENCH_PCG,
        )

        line_numbers = [line.get("line_number") for line in lines]
        expected_numbers = list(range(1, len(lines) + 1))
        assert line_numbers == expected_numbers

    @pytest.mark.asyncio
    async def test_indent_levels_correct(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test indent levels are correct."""
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Tuition",
            amount_sar=Decimal("1000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        db_session.add(revenue)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.INCOME_STATEMENT,
            StatementFormat.FRENCH_PCG,
        )

        for line in lines:
            line_type = line.get("line_type")
            indent = line.get("indent_level")

            if line_type == LineType.SECTION_HEADER:
                assert indent == 0
            elif line_type == LineType.ACCOUNT_LINE:
                assert indent == 2
            elif line_type == LineType.SUBTOTAL:
                assert indent == 1
            elif line_type == LineType.TOTAL:
                assert indent == 0

    @pytest.mark.asyncio
    async def test_bold_formatting(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test bold formatting on headers and totals."""
        revenue = BudgetConsolidation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            source_table="revenue_plans",
            source_count=1,
            is_calculated=True,
            consolidation_category=ConsolidationCategory.REVENUE_TUITION,
            account_code="70110",
            account_name="Tuition",
            amount_sar=Decimal("1000000.00"),
            is_revenue=True,
            created_by_id=test_user_id,
        )
        db_session.add(revenue)
        await db_session.flush()

        service = FinancialStatementsService(db_session)
        lines = await service.calculate_statement_lines(
            test_budget_version.id,
            StatementType.INCOME_STATEMENT,
            StatementFormat.FRENCH_PCG,
        )

        for line in lines:
            line_type = line.get("line_type")
            is_bold = line.get("is_bold")

            if line_type in [LineType.SECTION_HEADER, LineType.SUBTOTAL, LineType.TOTAL]:
                assert is_bold is True
            elif line_type == LineType.ACCOUNT_LINE:
                assert is_bold is False
