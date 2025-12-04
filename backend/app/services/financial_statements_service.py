"""
Financial statements service for generating financial reports.

Handles generation of:
- Income Statement (French PCG + IFRS formats)
- Balance Sheet (if applicable)
- Cash Flow Statement (if applicable)
- Period aggregation and totals
"""

import uuid
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.configuration import BudgetVersion
from app.models.consolidation import (
    BudgetConsolidation,
    ConsolidationCategory,
    FinancialStatement,
    FinancialStatementLine,
    LineType,
    StatementFormat,
    StatementType,
)
from app.services.base import BaseService
from app.services.exceptions import ValidationError


class FinancialStatementsService:
    """
    Service for financial statements generation.

    Provides business logic for:
    - Income statement generation (PCG and IFRS formats)
    - Balance sheet generation
    - Cash flow statement generation
    - Period-specific totals
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize financial statements service.

        Args:
            session: Async database session
        """
        self.session = session
        self.statement_service = BaseService(FinancialStatement, session)
        self.line_service = BaseService(FinancialStatementLine, session)
        self.budget_version_service = BaseService(BudgetVersion, session)

    async def get_income_statement(
        self,
        budget_version_id: uuid.UUID,
        format: str = "pcg",
    ) -> FinancialStatement:
        """
        Get or generate income statement for a budget version.

        Args:
            budget_version_id: Budget version UUID
            format: Statement format ('pcg' or 'ifrs')

        Returns:
            FinancialStatement instance with lines

        Raises:
            NotFoundError: If budget version not found
            ValidationError: If format is invalid
        """
        # Validate format
        if format not in ["pcg", "ifrs"]:
            raise ValidationError(
                f"Invalid format '{format}'. Must be 'pcg' or 'ifrs'.",
                field="format",
            )

        statement_format = (
            StatementFormat.FRENCH_PCG if format == "pcg" else StatementFormat.IFRS
        )

        # Check if statement already exists
        existing = await self._get_existing_statement(
            budget_version_id,
            StatementType.INCOME_STATEMENT,
            statement_format,
        )

        if existing:
            return existing

        # Generate new statement
        return await self._generate_income_statement(
            budget_version_id,
            statement_format,
        )

    async def get_balance_sheet(
        self,
        budget_version_id: uuid.UUID,
    ) -> dict[str, FinancialStatement]:
        """
        Get or generate balance sheet for a budget version.

        Args:
            budget_version_id: Budget version UUID

        Returns:
            Dictionary with 'assets' and 'liabilities' FinancialStatement instances

        Raises:
            NotFoundError: If budget version not found
        """
        # Check if statements already exist
        assets = await self._get_existing_statement(
            budget_version_id,
            StatementType.BALANCE_SHEET_ASSETS,
            StatementFormat.FRENCH_PCG,
        )

        liabilities = await self._get_existing_statement(
            budget_version_id,
            StatementType.BALANCE_SHEET_LIABILITIES,
            StatementFormat.FRENCH_PCG,
        )

        if assets and liabilities:
            return {"assets": assets, "liabilities": liabilities}

        # Generate new statements
        return await self._generate_balance_sheet(budget_version_id)

    async def calculate_statement_lines(
        self,
        budget_version_id: uuid.UUID,
        statement_type: StatementType,
        statement_format: StatementFormat,
    ) -> list[dict]:
        """
        Calculate statement lines by mapping account codes from consolidation.

        Args:
            budget_version_id: Budget version UUID
            statement_type: Type of statement
            statement_format: Format standard

        Returns:
            List of dictionaries with line data ready for creation
        """
        if statement_type == StatementType.INCOME_STATEMENT:
            return await self._calculate_income_statement_lines(
                budget_version_id,
                statement_format,
            )
        elif statement_type == StatementType.BALANCE_SHEET_ASSETS:
            return await self._calculate_balance_sheet_assets_lines(budget_version_id)
        elif statement_type == StatementType.BALANCE_SHEET_LIABILITIES:
            return await self._calculate_balance_sheet_liabilities_lines(budget_version_id)
        elif statement_type == StatementType.CASH_FLOW:
            return await self._calculate_cash_flow_lines(budget_version_id)
        else:
            raise ValidationError(f"Unsupported statement type: {statement_type}")

    async def get_period_totals(
        self,
        budget_version_id: uuid.UUID,
        period: str,
    ) -> dict[str, Decimal]:
        """
        Get period-specific totals from consolidation.

        Periods: 'p1' (Jan-Jun), 'summer' (Jul-Aug), 'p2' (Sep-Dec), 'annual'

        Args:
            budget_version_id: Budget version UUID
            period: Period identifier

        Returns:
            Dictionary with totals:
            {
                "total_revenue": Decimal,
                "total_expenses": Decimal,
                "operating_result": Decimal,
                "net_result": Decimal
            }

        Raises:
            ValidationError: If period is invalid
        """
        valid_periods = ["p1", "summer", "p2", "annual"]
        if period not in valid_periods:
            raise ValidationError(
                f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}",
                field="period",
            )

        # Get all consolidation entries
        query = (
            select(BudgetConsolidation)
            .where(
                and_(
                    BudgetConsolidation.budget_version_id == budget_version_id,
                    BudgetConsolidation.deleted_at.is_(None),
                )
            )
        )
        result = await self.session.execute(query)
        consolidations = result.scalars().all()

        # Calculate totals
        total_revenue = Decimal("0.00")
        total_expenses = Decimal("0.00")

        for item in consolidations:
            if item.is_revenue:
                total_revenue += item.amount_sar
            else:
                total_expenses += item.amount_sar

        operating_result = total_revenue - total_expenses
        net_result = operating_result  # Simplified - no financial income/expenses

        return {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "operating_result": operating_result,
            "net_result": net_result,
        }

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _get_existing_statement(
        self,
        budget_version_id: uuid.UUID,
        statement_type: StatementType,
        statement_format: StatementFormat,
    ) -> FinancialStatement | None:
        """Get existing statement if it exists."""
        query = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.budget_version_id == budget_version_id,
                    FinancialStatement.statement_type == statement_type,
                    FinancialStatement.statement_format == statement_format,
                    FinancialStatement.deleted_at.is_(None),
                )
            )
            .options(selectinload(FinancialStatement.lines))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _generate_income_statement(
        self,
        budget_version_id: uuid.UUID,
        statement_format: StatementFormat,
    ) -> FinancialStatement:
        """Generate income statement."""
        # Get budget version
        budget_version = await self.budget_version_service.get_by_id(budget_version_id)

        # Calculate statement lines
        lines_data = await self._calculate_income_statement_lines(
            budget_version_id,
            statement_format,
        )

        # Calculate total (net result)
        total_amount = Decimal("0.00")
        for line in lines_data:
            if line.get("line_type") == LineType.TOTAL and line.get("line_code") is None:
                total_amount = line.get("amount_sar", Decimal("0.00"))

        # Create statement
        statement_name = (
            f"Compte de résultat {budget_version.academic_year}"
            if statement_format == StatementFormat.FRENCH_PCG
            else f"Income Statement {budget_version.academic_year}"
        )

        statement = await self.statement_service.create({
            "budget_version_id": budget_version_id,
            "statement_type": StatementType.INCOME_STATEMENT,
            "statement_format": statement_format,
            "statement_name": statement_name,
            "fiscal_year": budget_version.fiscal_year,
            "total_amount_sar": total_amount,
            "is_calculated": True,
        })

        # Create lines
        for line_data in lines_data:
            line_data["statement_id"] = statement.id
            await self.line_service.create(line_data)

        # Refresh to get lines
        await self.session.refresh(statement)

        return statement

    async def _generate_balance_sheet(
        self,
        budget_version_id: uuid.UUID,
    ) -> dict[str, FinancialStatement]:
        """Generate balance sheet (assets and liabilities)."""
        # Get budget version
        budget_version = await self.budget_version_service.get_by_id(budget_version_id)

        # Generate assets
        assets_lines = await self._calculate_balance_sheet_assets_lines(budget_version_id)
        assets_total = Decimal("0.00")
        for line in assets_lines:
            if line.get("line_type") == LineType.TOTAL:
                assets_total = line.get("amount_sar", Decimal("0.00"))

        assets_statement = await self.statement_service.create({
            "budget_version_id": budget_version_id,
            "statement_type": StatementType.BALANCE_SHEET_ASSETS,
            "statement_format": StatementFormat.FRENCH_PCG,
            "statement_name": f"Bilan - Actif {budget_version.academic_year}",
            "fiscal_year": budget_version.fiscal_year,
            "total_amount_sar": assets_total,
            "is_calculated": True,
        })

        for line_data in assets_lines:
            line_data["statement_id"] = assets_statement.id
            await self.line_service.create(line_data)

        # Generate liabilities
        liabilities_lines = await self._calculate_balance_sheet_liabilities_lines(
            budget_version_id
        )
        liabilities_total = Decimal("0.00")
        for line in liabilities_lines:
            if line.get("line_type") == LineType.TOTAL:
                liabilities_total = line.get("amount_sar", Decimal("0.00"))

        liabilities_statement = await self.statement_service.create({
            "budget_version_id": budget_version_id,
            "statement_type": StatementType.BALANCE_SHEET_LIABILITIES,
            "statement_format": StatementFormat.FRENCH_PCG,
            "statement_name": f"Bilan - Passif {budget_version.academic_year}",
            "fiscal_year": budget_version.fiscal_year,
            "total_amount_sar": liabilities_total,
            "is_calculated": True,
        })

        for line_data in liabilities_lines:
            line_data["statement_id"] = liabilities_statement.id
            await self.line_service.create(line_data)

        # Refresh to get lines
        await self.session.refresh(assets_statement)
        await self.session.refresh(liabilities_statement)

        return {
            "assets": assets_statement,
            "liabilities": liabilities_statement,
        }

    async def _calculate_income_statement_lines(
        self,
        budget_version_id: uuid.UUID,
        statement_format: StatementFormat,
    ) -> list[dict]:
        """Calculate income statement lines from consolidation."""
        # Get consolidation data
        query = (
            select(BudgetConsolidation)
            .where(
                and_(
                    BudgetConsolidation.budget_version_id == budget_version_id,
                    BudgetConsolidation.deleted_at.is_(None),
                )
            )
            .order_by(
                BudgetConsolidation.is_revenue.desc(),
                BudgetConsolidation.consolidation_category,
            )
        )
        result = await self.session.execute(query)
        consolidations = result.scalars().all()

        lines = []
        line_number = 1

        # REVENUE SECTION
        lines.append({
            "line_number": line_number,
            "line_type": LineType.SECTION_HEADER,
            "indent_level": 0,
            "line_code": None,
            "line_description": "PRODUITS D'EXPLOITATION"
            if statement_format == StatementFormat.FRENCH_PCG
            else "OPERATING REVENUE",
            "amount_sar": None,
            "is_bold": True,
            "is_underlined": False,
        })
        line_number += 1

        # Revenue items
        revenue_total = Decimal("0.00")
        for item in consolidations:
            if item.is_revenue:
                lines.append({
                    "line_number": line_number,
                    "line_type": LineType.ACCOUNT_LINE,
                    "indent_level": 2,
                    "line_code": item.account_code,
                    "line_description": item.account_name,
                    "amount_sar": item.amount_sar,
                    "is_bold": False,
                    "is_underlined": False,
                    "source_consolidation_category": item.consolidation_category.value,
                })
                line_number += 1
                revenue_total += item.amount_sar

        # Revenue subtotal
        lines.append({
            "line_number": line_number,
            "line_type": LineType.SUBTOTAL,
            "indent_level": 1,
            "line_code": None,
            "line_description": "Total Produits d'Exploitation"
            if statement_format == StatementFormat.FRENCH_PCG
            else "Total Operating Revenue",
            "amount_sar": revenue_total,
            "is_bold": True,
            "is_underlined": True,
        })
        line_number += 1

        # EXPENSES SECTION
        lines.append({
            "line_number": line_number,
            "line_type": LineType.SECTION_HEADER,
            "indent_level": 0,
            "line_code": None,
            "line_description": "CHARGES D'EXPLOITATION"
            if statement_format == StatementFormat.FRENCH_PCG
            else "OPERATING EXPENSES",
            "amount_sar": None,
            "is_bold": True,
            "is_underlined": False,
        })
        line_number += 1

        # Expense items
        expense_total = Decimal("0.00")
        for item in consolidations:
            if not item.is_revenue:
                lines.append({
                    "line_number": line_number,
                    "line_type": LineType.ACCOUNT_LINE,
                    "indent_level": 2,
                    "line_code": item.account_code,
                    "line_description": item.account_name,
                    "amount_sar": item.amount_sar,
                    "is_bold": False,
                    "is_underlined": False,
                    "source_consolidation_category": item.consolidation_category.value,
                })
                line_number += 1
                expense_total += item.amount_sar

        # Expense subtotal
        lines.append({
            "line_number": line_number,
            "line_type": LineType.SUBTOTAL,
            "indent_level": 1,
            "line_code": None,
            "line_description": "Total Charges d'Exploitation"
            if statement_format == StatementFormat.FRENCH_PCG
            else "Total Operating Expenses",
            "amount_sar": expense_total,
            "is_bold": True,
            "is_underlined": True,
        })
        line_number += 1

        # OPERATING RESULT
        operating_result = revenue_total - expense_total
        lines.append({
            "line_number": line_number,
            "line_type": LineType.TOTAL,
            "indent_level": 0,
            "line_code": None,
            "line_description": "RÉSULTAT D'EXPLOITATION"
            if statement_format == StatementFormat.FRENCH_PCG
            else "OPERATING RESULT",
            "amount_sar": operating_result,
            "is_bold": True,
            "is_underlined": True,
        })
        line_number += 1

        # NET RESULT (simplified - no financial income/expenses)
        lines.append({
            "line_number": line_number,
            "line_type": LineType.TOTAL,
            "indent_level": 0,
            "line_code": None,
            "line_description": "RÉSULTAT NET"
            if statement_format == StatementFormat.FRENCH_PCG
            else "NET RESULT",
            "amount_sar": operating_result,
            "is_bold": True,
            "is_underlined": True,
        })

        return lines

    async def _calculate_balance_sheet_assets_lines(
        self,
        budget_version_id: uuid.UUID,
    ) -> list[dict]:
        """Calculate balance sheet assets lines (simplified)."""
        lines = []
        line_number = 1

        # Header
        lines.append({
            "line_number": line_number,
            "line_type": LineType.SECTION_HEADER,
            "indent_level": 0,
            "line_code": None,
            "line_description": "ACTIF",
            "amount_sar": None,
            "is_bold": True,
            "is_underlined": False,
        })
        line_number += 1

        # Get CapEx items (fixed assets)
        query = (
            select(BudgetConsolidation)
            .where(
                and_(
                    BudgetConsolidation.budget_version_id == budget_version_id,
                    BudgetConsolidation.source_table == "capex_plans",
                    BudgetConsolidation.deleted_at.is_(None),
                )
            )
        )
        result = await self.session.execute(query)
        capex_items = result.scalars().all()

        total_assets = Decimal("0.00")
        for item in capex_items:
            lines.append({
                "line_number": line_number,
                "line_type": LineType.ACCOUNT_LINE,
                "indent_level": 2,
                "line_code": item.account_code,
                "line_description": item.account_name,
                "amount_sar": item.amount_sar,
                "is_bold": False,
                "is_underlined": False,
            })
            line_number += 1
            total_assets += item.amount_sar

        # Total
        lines.append({
            "line_number": line_number,
            "line_type": LineType.TOTAL,
            "indent_level": 0,
            "line_code": None,
            "line_description": "TOTAL ACTIF",
            "amount_sar": total_assets,
            "is_bold": True,
            "is_underlined": True,
        })

        return lines

    async def _calculate_balance_sheet_liabilities_lines(
        self,
        budget_version_id: uuid.UUID,
    ) -> list[dict]:
        """Calculate balance sheet liabilities lines (simplified)."""
        lines = []
        line_number = 1

        # Compute equity based on total assets (mirrors capex total for now)
        capex_query = (
            select(func.coalesce(func.sum(BudgetConsolidation.amount_sar), 0))
            .where(
                and_(
                    BudgetConsolidation.budget_version_id == budget_version_id,
                    BudgetConsolidation.source_table == "capex_plans",
                    BudgetConsolidation.deleted_at.is_(None),
                )
            )
        )
        total_assets = Decimal(str((await self.session.execute(capex_query)).scalar()))

        # Header
        lines.append({
            "line_number": line_number,
            "line_type": LineType.SECTION_HEADER,
            "indent_level": 0,
            "line_code": None,
            "line_description": "PASSIF",
            "amount_sar": None,
            "is_bold": True,
            "is_underlined": False,
        })
        line_number += 1

        # Simplified: Just show equity as total
        # In reality, this would include detailed equity and liabilities
        total_liabilities = total_assets

        lines.append({
            "line_number": line_number,
            "line_type": LineType.ACCOUNT_LINE,
            "indent_level": 2,
            "line_code": None,
            "line_description": "Capitaux propres",
            "amount_sar": total_liabilities,
            "is_bold": False,
            "is_underlined": False,
        })
        line_number += 1

        # Total
        lines.append({
            "line_number": line_number,
            "line_type": LineType.TOTAL,
            "indent_level": 0,
            "line_code": None,
            "line_description": "TOTAL PASSIF",
            "amount_sar": total_liabilities,
            "is_bold": True,
            "is_underlined": True,
        })

        return lines

    async def _calculate_cash_flow_lines(
        self,
        budget_version_id: uuid.UUID,
    ) -> list[dict]:
        """Calculate cash flow statement lines using consolidation data."""
        capex_categories = {
            ConsolidationCategory.CAPEX_EQUIPMENT,
            ConsolidationCategory.CAPEX_IT,
            ConsolidationCategory.CAPEX_FURNITURE,
            ConsolidationCategory.CAPEX_BUILDING,
            ConsolidationCategory.CAPEX_SOFTWARE,
        }

        query = (
            select(BudgetConsolidation)
            .where(
                and_(
                    BudgetConsolidation.budget_version_id == budget_version_id,
                    BudgetConsolidation.deleted_at.is_(None),
                )
            )
            .order_by(BudgetConsolidation.account_code)
        )
        result = await self.session.execute(query)
        consolidations = result.scalars().all()

        operating_entries: list[BudgetConsolidation] = []
        investing_entries: list[BudgetConsolidation] = []

        for item in consolidations:
            if item.consolidation_category in capex_categories:
                investing_entries.append(item)
            else:
                operating_entries.append(item)

        def _signed_amount(entry: BudgetConsolidation) -> Decimal:
            return entry.amount_sar if entry.is_revenue else -entry.amount_sar

        operating_total = sum((_signed_amount(e) for e in operating_entries), start=Decimal("0.00"))
        investing_total = sum((_signed_amount(e) for e in investing_entries), start=Decimal("0.00"))
        financing_total = Decimal("0.00")  # No financing data yet
        net_change = operating_total + investing_total + financing_total

        lines = []
        line_number = 1

        # Header
        lines.append({
            "line_number": line_number,
            "line_type": LineType.SECTION_HEADER,
            "indent_level": 0,
            "line_code": None,
            "line_description": "TABLEAU DE FLUX DE TRÉSORERIE",
            "amount_sar": None,
            "is_bold": True,
            "is_underlined": False,
        })
        line_number += 1

        # Operating activities
        lines.append({
            "line_number": line_number,
            "line_type": LineType.ACCOUNT_GROUP,
            "indent_level": 1,
            "line_code": None,
            "line_description": "Flux de trésorerie liés aux activités opérationnelles",
            "amount_sar": None,
            "is_bold": True,
            "is_underlined": False,
        })
        line_number += 1

        for entry in operating_entries:
            lines.append({
                "line_number": line_number,
                "line_type": LineType.ACCOUNT_LINE,
                "indent_level": 2,
                "line_code": entry.account_code,
                "line_description": entry.account_name,
                "amount_sar": _signed_amount(entry),
                "is_bold": False,
                "is_underlined": False,
                "source_consolidation_category": entry.consolidation_category.value,
            })
            line_number += 1

        lines.append({
            "line_number": line_number,
            "line_type": LineType.SUBTOTAL,
            "indent_level": 1,
            "line_code": None,
            "line_description": "Total flux opérationnels",
            "amount_sar": operating_total,
            "is_bold": True,
            "is_underlined": True,
        })
        line_number += 1

        # Investing activities
        lines.append({
            "line_number": line_number,
            "line_type": LineType.ACCOUNT_GROUP,
            "indent_level": 1,
            "line_code": None,
            "line_description": "Flux de trésorerie liés aux activités d'investissement",
            "amount_sar": None,
            "is_bold": True,
            "is_underlined": False,
        })
        line_number += 1

        for entry in investing_entries:
            lines.append({
                "line_number": line_number,
                "line_type": LineType.ACCOUNT_LINE,
                "indent_level": 2,
                "line_code": entry.account_code,
                "line_description": entry.account_name,
                "amount_sar": _signed_amount(entry),
                "is_bold": False,
                "is_underlined": False,
                "source_consolidation_category": entry.consolidation_category.value,
            })
            line_number += 1

        lines.append({
            "line_number": line_number,
            "line_type": LineType.SUBTOTAL,
            "indent_level": 1,
            "line_code": None,
            "line_description": "Total flux d'investissement",
            "amount_sar": investing_total,
            "is_bold": True,
            "is_underlined": True,
        })
        line_number += 1

        # Financing placeholder (no data yet, but keep structure for clarity)
        lines.append({
            "line_number": line_number,
            "line_type": LineType.SUBTOTAL,
            "indent_level": 1,
            "line_code": None,
            "line_description": "Total flux de financement",
            "amount_sar": financing_total,
            "is_bold": True,
            "is_underlined": True,
        })
        line_number += 1

        # Net change
        lines.append({
            "line_number": line_number,
            "line_type": LineType.TOTAL,
            "indent_level": 0,
            "line_code": None,
            "line_description": "Variation nette de trésorerie",
            "amount_sar": net_change,
            "is_bold": True,
            "is_underlined": True,
        })

        return lines
