"""
Historical Comparison Service

Provides functionality for fetching and comparing current budget data
against 2 years of historical actuals (N-2, N-1, Current).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BudgetVersion,
    HistoricalActuals,
    HistoricalDimensionType,
    HistoricalModuleCode,
)
from app.schemas.historical import (
    HistoricalComparison,
    HistoricalDataPoint,
)


class HistoricalComparisonService:
    """
    Service for retrieving and comparing historical actuals data.

    Enables comparison of current budget planning against prior year actuals
    with support for:
    - Enrollment by level
    - DHG by subject
    - Revenue by account code
    - Costs by account code
    - CapEx by account code
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session."""
        self.session = session

    async def get_historical_for_module(
        self,
        module_code: HistoricalModuleCode,
        dimension_type: HistoricalDimensionType,
        current_fiscal_year: int,
        history_years: int = 2,
    ) -> dict[str, dict[int, HistoricalDataPoint]]:
        """
        Fetch historical data for a module, organized by dimension code.

        Args:
            module_code: Module to fetch (enrollment, dhg, revenue, etc.)
            dimension_type: Dimension type to group by (level, subject, account_code)
            current_fiscal_year: The current fiscal year being planned
            history_years: Number of historical years to fetch (default 2)

        Returns:
            Dictionary mapping dimension_code -> {fiscal_year -> HistoricalDataPoint}
        """
        # Calculate fiscal years to fetch
        fiscal_years = [current_fiscal_year - i for i in range(1, history_years + 1)]

        # Query historical data
        stmt = (
            select(HistoricalActuals)
            .where(
                HistoricalActuals.module_code == module_code,
                HistoricalActuals.dimension_type == dimension_type,
                HistoricalActuals.fiscal_year.in_(fiscal_years),
                HistoricalActuals.deleted_at.is_(None),
            )
            .order_by(
                HistoricalActuals.dimension_code,
                HistoricalActuals.fiscal_year.desc(),
            )
        )

        result = await self.session.execute(stmt)
        records = result.scalars().all()

        # Organize by dimension code and fiscal year
        historical_data: dict[str, dict[int, HistoricalDataPoint]] = {}

        for record in records:
            dim_code = record.dimension_code
            if dim_code not in historical_data:
                historical_data[dim_code] = {}

            # Determine the value based on module type
            value = self._get_value_for_module(record, module_code)

            historical_data[dim_code][record.fiscal_year] = HistoricalDataPoint(
                fiscal_year=record.fiscal_year,
                value=value,
                is_actual=True,
            )

        return historical_data

    def _get_value_for_module(
        self,
        record: HistoricalActuals,
        module_code: HistoricalModuleCode,
    ) -> Decimal | int | None:
        """Extract the appropriate value from a historical record based on module type."""
        if module_code == HistoricalModuleCode.ENROLLMENT:
            return record.annual_count
        elif module_code == HistoricalModuleCode.CLASS_STRUCTURE:
            return record.annual_classes
        elif module_code == HistoricalModuleCode.DHG:
            # For DHG, prefer FTE, fall back to hours
            return record.annual_fte or record.annual_hours
        elif module_code in (
            HistoricalModuleCode.REVENUE,
            HistoricalModuleCode.COSTS,
            HistoricalModuleCode.CAPEX,
        ):
            return record.annual_amount_sar
        return None

    def build_comparison(
        self,
        current_value: Decimal | int,
        historical_data: dict[int, HistoricalDataPoint] | None,
        current_fiscal_year: int,
    ) -> HistoricalComparison:
        """
        Build a HistoricalComparison object from current value and historical data.

        Args:
            current_value: The current plan value
            historical_data: Dictionary of fiscal_year -> HistoricalDataPoint
            current_fiscal_year: The fiscal year of the current plan

        Returns:
            HistoricalComparison with calculated variances
        """
        n_minus_1_year = current_fiscal_year - 1
        n_minus_2_year = current_fiscal_year - 2

        n_minus_1: HistoricalDataPoint | None = None
        n_minus_2: HistoricalDataPoint | None = None

        if historical_data:
            n_minus_1 = historical_data.get(n_minus_1_year)
            n_minus_2 = historical_data.get(n_minus_2_year)

        # Calculate variances
        vs_n_minus_1_abs: Decimal | int | None = None
        vs_n_minus_1_pct: Decimal | None = None
        vs_n_minus_2_abs: Decimal | int | None = None
        vs_n_minus_2_pct: Decimal | None = None

        if n_minus_1 and n_minus_1.value is not None:
            vs_n_minus_1_abs = current_value - n_minus_1.value
            if n_minus_1.value != 0:
                vs_n_minus_1_pct = Decimal(str(vs_n_minus_1_abs)) / Decimal(
                    str(n_minus_1.value)
                ) * Decimal("100")

        if n_minus_2 and n_minus_2.value is not None:
            vs_n_minus_2_abs = current_value - n_minus_2.value
            if n_minus_2.value != 0:
                vs_n_minus_2_pct = Decimal(str(vs_n_minus_2_abs)) / Decimal(
                    str(n_minus_2.value)
                ) * Decimal("100")

        return HistoricalComparison(
            n_minus_2=n_minus_2,
            n_minus_1=n_minus_1,
            current=current_value,
            vs_n_minus_1_abs=vs_n_minus_1_abs,
            vs_n_minus_1_pct=(
                round(vs_n_minus_1_pct, 2) if vs_n_minus_1_pct is not None else None
            ),
            vs_n_minus_2_abs=vs_n_minus_2_abs,
            vs_n_minus_2_pct=(
                round(vs_n_minus_2_pct, 2) if vs_n_minus_2_pct is not None else None
            ),
        )

    async def get_budget_version_fiscal_year(
        self, budget_version_id: UUID
    ) -> int | None:
        """Get the fiscal year for a budget version."""
        stmt = select(BudgetVersion.fiscal_year).where(
            BudgetVersion.id == budget_version_id,
            BudgetVersion.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_enrollment_with_history(
        self,
        budget_version_id: UUID,
        history_years: int = 2,
    ) -> dict[str, Any]:
        """
        Get enrollment data with historical comparison.

        Returns enrollment by level with N-2 and N-1 actuals.
        """
        from app.models import AcademicLevel, EnrollmentPlan

        # Get fiscal year
        fiscal_year = await self.get_budget_version_fiscal_year(budget_version_id)
        if not fiscal_year:
            raise ValueError(f"Budget version {budget_version_id} not found")

        # Get current enrollment data
        enrollment_stmt = (
            select(EnrollmentPlan, AcademicLevel)
            .join(AcademicLevel, EnrollmentPlan.level_id == AcademicLevel.id)
            .where(
                EnrollmentPlan.budget_version_id == budget_version_id,
                EnrollmentPlan.deleted_at.is_(None),
            )
            .order_by(AcademicLevel.sort_order)
        )
        enrollment_result = await self.session.execute(enrollment_stmt)
        enrollments = enrollment_result.all()

        # Get historical data
        historical = await self.get_historical_for_module(
            module_code=HistoricalModuleCode.ENROLLMENT,
            dimension_type=HistoricalDimensionType.LEVEL,
            current_fiscal_year=fiscal_year,
            history_years=history_years,
        )

        # AGGREGATE enrollment by level (sum across all nationalities)
        # EnrollmentPlan has one row per (level, nationality), so we must aggregate
        level_totals: dict[UUID, tuple[AcademicLevel, int]] = {}
        for enrollment, level in enrollments:
            student_count = enrollment.student_count or 0
            if level.id in level_totals:
                # Add to existing level total
                existing_level, existing_count = level_totals[level.id]
                level_totals[level.id] = (existing_level, existing_count + student_count)
            else:
                # First record for this level
                level_totals[level.id] = (level, student_count)

        # Build response rows from aggregated totals
        rows = []
        total_current = 0

        for _level_id, (level, student_count) in level_totals.items():
            total_current += student_count

            row = {
                "level_id": level.id,
                "level_code": level.code,
                "level_name": level.name_en,
                "student_count": student_count,
                "history": self.build_comparison(
                    current_value=student_count,
                    historical_data=historical.get(level.code),
                    current_fiscal_year=fiscal_year,
                ),
            }
            rows.append(row)

        # Build totals
        total_historical: dict[int, HistoricalDataPoint] = {}
        for _dim_code, year_data in historical.items():
            for year, point in year_data.items():
                if year not in total_historical:
                    total_historical[year] = HistoricalDataPoint(
                        fiscal_year=year, value=0, is_actual=True
                    )
                if point.value:
                    current_total = total_historical[year].value or 0
                    total_historical[year] = HistoricalDataPoint(
                        fiscal_year=year,
                        value=current_total + point.value,
                        is_actual=True,
                    )

        return {
            "budget_version_id": budget_version_id,
            "fiscal_year": fiscal_year,
            "current_fiscal_year": fiscal_year,
            "rows": rows,
            "totals": self.build_comparison(
                current_value=total_current,
                historical_data=total_historical,
                current_fiscal_year=fiscal_year,
            ),
        }

    async def get_dhg_with_history(
        self,
        budget_version_id: UUID,
        history_years: int = 2,
    ) -> dict[str, Any]:
        """
        Get DHG data with historical comparison.

        Returns DHG hours and FTE by subject with N-2 and N-1 actuals.
        """
        from app.models import DHGSubjectHours, Subject

        # Get fiscal year
        fiscal_year = await self.get_budget_version_fiscal_year(budget_version_id)
        if not fiscal_year:
            raise ValueError(f"Budget version {budget_version_id} not found")

        # Get current DHG data
        dhg_stmt = (
            select(DHGSubjectHours, Subject)
            .outerjoin(Subject, DHGSubjectHours.subject_id == Subject.id)
            .where(
                DHGSubjectHours.budget_version_id == budget_version_id,
                DHGSubjectHours.deleted_at.is_(None),
            )
            .order_by(Subject.name_fr)
        )
        dhg_result = await self.session.execute(dhg_stmt)
        dhg_records = dhg_result.all()

        # Get historical data for hours and FTE
        historical_hours = await self.get_historical_for_module(
            module_code=HistoricalModuleCode.DHG,
            dimension_type=HistoricalDimensionType.SUBJECT,
            current_fiscal_year=fiscal_year,
            history_years=history_years,
        )

        # Build response rows
        rows = []
        total_hours = Decimal("0")
        total_fte = Decimal("0")

        for dhg, subject in dhg_records:
            hours = dhg.total_hours or Decimal("0")
            fte = dhg.required_fte or Decimal("0")
            subject_code = subject.code if subject else dhg.subject_code or "UNKNOWN"
            subject_name = subject.name_fr if subject else subject_code

            total_hours += hours
            total_fte += fte

            # For historical FTE, we need to calculate from hours
            # Standard: 18h/week for secondary, 24h/week for primary
            hours_history = historical_hours.get(subject_code, {})

            row = {
                "subject_id": subject.id if subject else None,
                "subject_code": subject_code,
                "subject_name": subject_name,
                "total_hours": hours,
                "fte": fte,
                "hours_history": self.build_comparison(
                    current_value=hours,
                    historical_data=hours_history,
                    current_fiscal_year=fiscal_year,
                ),
                "fte_history": self.build_comparison(
                    current_value=fte,
                    historical_data=None,  # FTE history calculated from hours
                    current_fiscal_year=fiscal_year,
                ),
            }
            rows.append(row)

        # Build totals
        total_hours_historical: dict[int, HistoricalDataPoint] = {}
        for _dim_code, year_data in historical_hours.items():
            for year, point in year_data.items():
                if year not in total_hours_historical:
                    total_hours_historical[year] = HistoricalDataPoint(
                        fiscal_year=year, value=Decimal("0"), is_actual=True
                    )
                if point.value:
                    current_total = total_hours_historical[year].value or Decimal("0")
                    total_hours_historical[year] = HistoricalDataPoint(
                        fiscal_year=year,
                        value=current_total + Decimal(str(point.value)),
                        is_actual=True,
                    )

        return {
            "budget_version_id": budget_version_id,
            "fiscal_year": fiscal_year,
            "current_fiscal_year": fiscal_year,
            "rows": rows,
            "totals_hours": self.build_comparison(
                current_value=total_hours,
                historical_data=total_hours_historical,
                current_fiscal_year=fiscal_year,
            ),
            "totals_fte": self.build_comparison(
                current_value=total_fte,
                historical_data=None,
                current_fiscal_year=fiscal_year,
            ),
        }

    async def get_revenue_with_history(
        self,
        budget_version_id: UUID,
        history_years: int = 2,
    ) -> dict[str, Any]:
        """
        Get revenue data with historical comparison.

        Returns revenue by account code with N-2 and N-1 actuals.
        """
        from app.models import RevenuePlan

        # Get fiscal year
        fiscal_year = await self.get_budget_version_fiscal_year(budget_version_id)
        if not fiscal_year:
            raise ValueError(f"Budget version {budget_version_id} not found")

        # Get current revenue data
        revenue_stmt = (
            select(RevenuePlan)
            .where(
                RevenuePlan.budget_version_id == budget_version_id,
                RevenuePlan.deleted_at.is_(None),
            )
            .order_by(RevenuePlan.account_code)
        )
        revenue_result = await self.session.execute(revenue_stmt)
        revenues = revenue_result.scalars().all()

        # Get historical data
        historical = await self.get_historical_for_module(
            module_code=HistoricalModuleCode.REVENUE,
            dimension_type=HistoricalDimensionType.ACCOUNT_CODE,
            current_fiscal_year=fiscal_year,
            history_years=history_years,
        )

        # Build response rows
        rows = []
        total_current = Decimal("0")

        for revenue in revenues:
            amount = revenue.annual_amount_sar or Decimal("0")
            total_current += amount

            row = {
                "account_code": revenue.account_code,
                "account_name": revenue.description or revenue.account_code,
                "fee_type": getattr(revenue, "fee_type", None),
                "amount_sar": amount,
                "history": self.build_comparison(
                    current_value=amount,
                    historical_data=historical.get(revenue.account_code),
                    current_fiscal_year=fiscal_year,
                ),
            }
            rows.append(row)

        # Build totals
        total_historical: dict[int, HistoricalDataPoint] = {}
        for _dim_code, year_data in historical.items():
            for year, point in year_data.items():
                if year not in total_historical:
                    total_historical[year] = HistoricalDataPoint(
                        fiscal_year=year, value=Decimal("0"), is_actual=True
                    )
                if point.value:
                    current_total = total_historical[year].value or Decimal("0")
                    total_historical[year] = HistoricalDataPoint(
                        fiscal_year=year,
                        value=current_total + Decimal(str(point.value)),
                        is_actual=True,
                    )

        return {
            "budget_version_id": budget_version_id,
            "fiscal_year": fiscal_year,
            "current_fiscal_year": fiscal_year,
            "rows": rows,
            "totals": self.build_comparison(
                current_value=total_current,
                historical_data=total_historical,
                current_fiscal_year=fiscal_year,
            ),
        }

    async def get_costs_with_history(
        self,
        budget_version_id: UUID,
        history_years: int = 2,
    ) -> dict[str, Any]:
        """
        Get costs data with historical comparison.

        Returns costs by account code with N-2 and N-1 actuals,
        split into personnel and operating costs.
        """
        from app.models import OperatingCostPlan, PersonnelCostPlan

        # Get fiscal year
        fiscal_year = await self.get_budget_version_fiscal_year(budget_version_id)
        if not fiscal_year:
            raise ValueError(f"Budget version {budget_version_id} not found")

        # Get current personnel costs
        personnel_stmt = (
            select(PersonnelCostPlan)
            .where(
                PersonnelCostPlan.budget_version_id == budget_version_id,
                PersonnelCostPlan.deleted_at.is_(None),
            )
            .order_by(PersonnelCostPlan.account_code)
        )
        personnel_result = await self.session.execute(personnel_stmt)
        personnel_costs = personnel_result.scalars().all()

        # Get current operating costs
        operating_stmt = (
            select(OperatingCostPlan)
            .where(
                OperatingCostPlan.budget_version_id == budget_version_id,
                OperatingCostPlan.deleted_at.is_(None),
            )
            .order_by(OperatingCostPlan.account_code)
        )
        operating_result = await self.session.execute(operating_stmt)
        operating_costs = operating_result.scalars().all()

        # Get historical data
        historical = await self.get_historical_for_module(
            module_code=HistoricalModuleCode.COSTS,
            dimension_type=HistoricalDimensionType.ACCOUNT_CODE,
            current_fiscal_year=fiscal_year,
            history_years=history_years,
        )

        # Build response rows
        rows = []
        total_current = Decimal("0")
        personnel_total = Decimal("0")
        operating_total = Decimal("0")

        # Personnel costs
        for cost in personnel_costs:
            amount = cost.annual_amount_sar or Decimal("0")
            total_current += amount
            personnel_total += amount

            row = {
                "account_code": cost.account_code,
                "account_name": cost.description or cost.account_code,
                "cost_category": "personnel",
                "amount_sar": amount,
                "history": self.build_comparison(
                    current_value=amount,
                    historical_data=historical.get(cost.account_code),
                    current_fiscal_year=fiscal_year,
                ),
            }
            rows.append(row)

        # Operating costs
        for cost in operating_costs:
            amount = cost.annual_amount_sar or Decimal("0")
            total_current += amount
            operating_total += amount

            row = {
                "account_code": cost.account_code,
                "account_name": cost.description or cost.account_code,
                "cost_category": "operating",
                "amount_sar": amount,
                "history": self.build_comparison(
                    current_value=amount,
                    historical_data=historical.get(cost.account_code),
                    current_fiscal_year=fiscal_year,
                ),
            }
            rows.append(row)

        # Build totals
        total_historical: dict[int, HistoricalDataPoint] = {}
        for _dim_code, year_data in historical.items():
            for year, point in year_data.items():
                if year not in total_historical:
                    total_historical[year] = HistoricalDataPoint(
                        fiscal_year=year, value=Decimal("0"), is_actual=True
                    )
                if point.value:
                    current_total = total_historical[year].value or Decimal("0")
                    total_historical[year] = HistoricalDataPoint(
                        fiscal_year=year,
                        value=current_total + Decimal(str(point.value)),
                        is_actual=True,
                    )

        return {
            "budget_version_id": budget_version_id,
            "fiscal_year": fiscal_year,
            "current_fiscal_year": fiscal_year,
            "rows": rows,
            "totals": self.build_comparison(
                current_value=total_current,
                historical_data=total_historical,
                current_fiscal_year=fiscal_year,
            ),
            "personnel_totals": self.build_comparison(
                current_value=personnel_total,
                historical_data=None,  # Would need to filter historical by category
                current_fiscal_year=fiscal_year,
            ),
            "operating_totals": self.build_comparison(
                current_value=operating_total,
                historical_data=None,
                current_fiscal_year=fiscal_year,
            ),
        }

    async def get_capex_with_history(
        self,
        budget_version_id: UUID,
        history_years: int = 2,
    ) -> dict[str, Any]:
        """
        Get CapEx data with historical comparison.

        Returns CapEx by account code with N-2 and N-1 actuals.
        """
        from app.models import CapExPlan

        # Get fiscal year
        fiscal_year = await self.get_budget_version_fiscal_year(budget_version_id)
        if not fiscal_year:
            raise ValueError(f"Budget version {budget_version_id} not found")

        # Get current CapEx data
        capex_stmt = (
            select(CapExPlan)
            .where(
                CapExPlan.budget_version_id == budget_version_id,
                CapExPlan.deleted_at.is_(None),
            )
            .order_by(CapExPlan.account_code)
        )
        capex_result = await self.session.execute(capex_stmt)
        capex_items = capex_result.scalars().all()

        # Get historical data
        historical = await self.get_historical_for_module(
            module_code=HistoricalModuleCode.CAPEX,
            dimension_type=HistoricalDimensionType.ACCOUNT_CODE,
            current_fiscal_year=fiscal_year,
            history_years=history_years,
        )

        # Build response rows
        rows = []
        total_current = Decimal("0")

        for capex in capex_items:
            amount = capex.annual_amount_sar or Decimal("0")
            total_current += amount

            row = {
                "account_code": capex.account_code,
                "account_name": capex.description or capex.account_code,
                "category": getattr(capex, "category", None),
                "amount_sar": amount,
                "history": self.build_comparison(
                    current_value=amount,
                    historical_data=historical.get(capex.account_code),
                    current_fiscal_year=fiscal_year,
                ),
            }
            rows.append(row)

        # Build totals
        total_historical: dict[int, HistoricalDataPoint] = {}
        for _dim_code, year_data in historical.items():
            for year, point in year_data.items():
                if year not in total_historical:
                    total_historical[year] = HistoricalDataPoint(
                        fiscal_year=year, value=Decimal("0"), is_actual=True
                    )
                if point.value:
                    current_total = total_historical[year].value or Decimal("0")
                    total_historical[year] = HistoricalDataPoint(
                        fiscal_year=year,
                        value=current_total + Decimal(str(point.value)),
                        is_actual=True,
                    )

        return {
            "budget_version_id": budget_version_id,
            "fiscal_year": fiscal_year,
            "current_fiscal_year": fiscal_year,
            "rows": rows,
            "totals": self.build_comparison(
                current_value=total_current,
                historical_data=total_historical,
                current_fiscal_year=fiscal_year,
            ),
        }
