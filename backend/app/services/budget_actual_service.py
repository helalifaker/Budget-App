"""
Budget vs Actual Service for variance analysis and actuals import.

Implements business logic for:
- Importing actual financial data from Odoo
- Calculating variance between budget and actuals
- Generating variance reports
- Creating forecast revisions based on actuals
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import (
    ActualData,
    ActualDataSource,
    BudgetVsActual,
    VarianceStatus,
)
from app.models.consolidation import BudgetConsolidation
from app.models.configuration import BudgetVersion, BudgetVersionStatus
from app.services.base import BaseService
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError


class BudgetActualService:
    """
    Service for budget vs actual analysis and variance calculation.

    Provides methods for importing actual data from Odoo, calculating
    variances, generating reports, and creating forecast revisions.
    """

    # Variance thresholds
    MATERIALITY_THRESHOLD_PCT = Decimal("5.0")  # 5%
    MATERIALITY_THRESHOLD_SAR = Decimal("100000.00")  # 100K SAR

    def __init__(self, session: AsyncSession):
        """
        Initialize budget vs actual service.

        Args:
            session: Async database session
        """
        self.session = session
        self.actual_data_service = BaseService(ActualData, session)
        self.variance_service = BaseService(BudgetVsActual, session)

    async def import_actuals(
        self,
        budget_version_id: uuid.UUID,
        odoo_data: list[dict[str, Any]],
        import_batch_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Import actual financial data from Odoo.

        Args:
            budget_version_id: Budget version UUID to compare against
            odoo_data: List of Odoo transaction dictionaries with:
                - fiscal_year: Fiscal year (e.g., 2025)
                - period: Month (1-12)
                - account_code: French PCG account code
                - account_name: Account name
                - amount_sar: Amount in SAR
                - currency: Currency code
                - transaction_date: Transaction date (optional)
                - description: Transaction description (optional)
            import_batch_id: Optional batch identifier for grouping

        Returns:
            Dictionary with import summary:
                - records_imported: Number of records imported
                - import_batch_id: Batch identifier
                - fiscal_year: Fiscal year
                - periods_covered: List of periods imported
                - total_amount_sar: Total amount imported

        Raises:
            NotFoundError: If budget version not found
            ValidationError: If import data is invalid
        """
        # Verify budget version exists
        version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        # Generate batch ID if not provided
        if not import_batch_id:
            import_batch_id = uuid.uuid4()

        # Import records
        imported_records = []
        total_amount = Decimal("0")
        periods_covered = set()
        fiscal_year = None

        for record in odoo_data:
            # Validate required fields
            if not all(k in record for k in ["fiscal_year", "period", "account_code", "amount_sar"]):
                raise ValidationError("Missing required fields in Odoo data record")

            # Create ActualData record
            actual_data = ActualData(
                fiscal_year=record["fiscal_year"],
                period=record["period"],
                account_code=record["account_code"],
                account_name=record.get("account_name"),
                amount_sar=Decimal(str(record["amount_sar"])),
                currency=record.get("currency", "SAR"),
                import_batch_id=import_batch_id,
                import_date=datetime.utcnow(),
                source=ActualDataSource.ODOO_IMPORT,
                transaction_date=record.get("transaction_date"),
                description=record.get("description"),
                is_reconciled=False,
            )

            self.session.add(actual_data)
            imported_records.append(actual_data)

            # Track summary data
            total_amount += actual_data.amount_sar
            periods_covered.add(record["period"])
            if not fiscal_year:
                fiscal_year = record["fiscal_year"]

        await self.session.flush()

        return {
            "records_imported": len(imported_records),
            "import_batch_id": str(import_batch_id),
            "fiscal_year": fiscal_year,
            "periods_covered": sorted(list(periods_covered)),
            "total_amount_sar": float(total_amount),
            "import_date": datetime.utcnow().isoformat(),
        }

    async def calculate_variance(
        self,
        budget_version_id: uuid.UUID,
        period: int,
        account_code: str | None = None,
    ) -> list[BudgetVsActual]:
        """
        Calculate budget vs actual variance for a period.

        Args:
            budget_version_id: Budget version UUID
            period: Month (1-12)
            account_code: Optional specific account code to calculate

        Returns:
            List of BudgetVsActual instances with calculated variances

        Raises:
            NotFoundError: If budget version not found
        """
        # Verify budget version exists
        version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        # Get budget amounts from consolidation (annual amounts)
        budget_amounts = await self._get_budget_amounts(budget_version_id, account_code)

        # Get actual amounts for period
        actual_query = select(ActualData).where(
            and_(
                ActualData.fiscal_year == version.fiscal_year,
                ActualData.period == period,
                ActualData.deleted_at.is_(None),
            )
        )

        if account_code:
            actual_query = actual_query.where(ActualData.account_code == account_code)

        actual_result = await self.session.execute(actual_query)
        actuals = actual_result.scalars().all()

        # Calculate variance for each account
        variances = []
        for actual in actuals:
            # Get annual budget amount for this account (default 0 if missing)
            budget_amount = budget_amounts.get(actual.account_code, Decimal("0"))
            # Allocate a simple monthly budget (12-month straight-line) for variance
            monthly_budget = budget_amount / Decimal("12")

            # Calculate variance
            variance_sar = self._calculate_variance_amount(
                account_code=actual.account_code,
                budget_amount=monthly_budget,
                actual_amount=actual.amount_sar,
            )

            variance_percent = Decimal("0")
            if monthly_budget != 0:
                variance_percent = (variance_sar / monthly_budget) * 100

            # Determine variance status
            variance_status = self._determine_variance_status(
                account_code=actual.account_code,
                variance_sar=variance_sar,
                variance_percent=variance_percent,
            )

            # Check materiality
            is_material = self._is_variance_material(
                variance_sar=variance_sar,
                variance_percent=variance_percent,
            )

            # Calculate YTD amounts
            ytd_budget = monthly_budget * Decimal(str(period))
            ytd_actual = await self._get_ytd_actual(
                fiscal_year=version.fiscal_year,
                account_code=actual.account_code,
                through_period=period,
            )
            ytd_variance = self._calculate_variance_amount(
                account_code=actual.account_code,
                budget_amount=ytd_budget,
                actual_amount=ytd_actual,
            )

            # Check if variance already exists
            existing_query = select(BudgetVsActual).where(
                and_(
                    BudgetVsActual.budget_version_id == budget_version_id,
                    BudgetVsActual.account_code == actual.account_code,
                    BudgetVsActual.period == period,
                    BudgetVsActual.deleted_at.is_(None),
                )
            )
            existing_result = await self.session.execute(existing_query)
            existing_variance = existing_result.scalar_one_or_none()

            if existing_variance:
                # Update existing
                existing_variance.budget_amount_sar = budget_amount
                existing_variance.actual_amount_sar = actual.amount_sar
                existing_variance.variance_sar = variance_sar
                existing_variance.variance_percent = variance_percent
                existing_variance.variance_status = variance_status
                existing_variance.ytd_budget_sar = ytd_budget
                existing_variance.ytd_actual_sar = ytd_actual
                existing_variance.ytd_variance_sar = ytd_variance
                existing_variance.is_material = is_material
                variances.append(existing_variance)
            else:
                # Create new
                variance_record = BudgetVsActual(
                    budget_version_id=budget_version_id,
                    account_code=actual.account_code,
                    period=period,
                    budget_amount_sar=budget_amount,
                    actual_amount_sar=actual.amount_sar,
                    variance_sar=variance_sar,
                    variance_percent=variance_percent,
                    variance_status=variance_status,
                    ytd_budget_sar=ytd_budget,
                    ytd_actual_sar=ytd_actual,
                    ytd_variance_sar=ytd_variance,
                    is_material=is_material,
                )
                self.session.add(variance_record)
                variances.append(variance_record)

        await self.session.flush()

        # Refresh to get relationships
        for variance in variances:
            await self.session.refresh(variance)

        return variances

    async def get_variance_report(
        self,
        budget_version_id: uuid.UUID,
        period: int | None = None,
        account_code_pattern: str | None = None,
        material_only: bool = False,
    ) -> dict[str, Any]:
        """
        Get comprehensive variance report.

        Args:
            budget_version_id: Budget version UUID
            period: Optional filter by specific period
            account_code_pattern: Optional filter by account code pattern (e.g., '64%' for personnel)
            material_only: Only include material variances

        Returns:
            Dictionary with variance report data:
                - summary: Overall variance summary
                - variances: List of variance details
                - material_variances: Count of material variances
                - favorable_count: Count of favorable variances
                - unfavorable_count: Count of unfavorable variances

        Raises:
            NotFoundError: If budget version not found
        """
        # Verify budget version exists
        version_query = select(BudgetVersion).where(BudgetVersion.id == budget_version_id)
        version_result = await self.session.execute(version_query)
        version = version_result.scalar_one_or_none()

        if not version:
            raise NotFoundError("BudgetVersion", str(budget_version_id))

        # Build query
        query = select(BudgetVsActual).where(
            and_(
                BudgetVsActual.budget_version_id == budget_version_id,
                BudgetVsActual.deleted_at.is_(None),
            )
        )

        if period:
            query = query.where(BudgetVsActual.period == period)

        if account_code_pattern:
            query = query.where(BudgetVsActual.account_code.like(account_code_pattern))

        if material_only:
            query = query.where(BudgetVsActual.is_material.is_(True))

        query = query.order_by(BudgetVsActual.account_code, BudgetVsActual.period)

        result = await self.session.execute(query)
        variances = result.scalars().all()

        # Calculate summary statistics
        total_budget = sum(v.budget_amount_sar for v in variances)
        total_actual = sum(v.actual_amount_sar for v in variances)
        total_variance = sum(v.variance_sar for v in variances)

        favorable_count = sum(
            1 for v in variances if v.variance_status == VarianceStatus.FAVORABLE
        )
        unfavorable_count = sum(
            1 for v in variances if v.variance_status == VarianceStatus.UNFAVORABLE
        )
        material_count = sum(1 for v in variances if v.is_material)

        return {
            "version_id": str(budget_version_id),
            "version_name": version.name,
            "fiscal_year": version.fiscal_year,
            "period": period,
            "summary": {
                "total_budget_sar": float(total_budget),
                "total_actual_sar": float(total_actual),
                "total_variance_sar": float(total_variance),
                "variance_percent": (
                    float((total_variance / total_budget) * 100) if total_budget else 0
                ),
                "variance_count": len(variances),
                "material_count": material_count,
                "favorable_count": favorable_count,
                "unfavorable_count": unfavorable_count,
            },
            "variances": [
                {
                    "account_code": v.account_code,
                    "period": v.period,
                    "budget_sar": float(v.budget_amount_sar),
                    "actual_sar": float(v.actual_amount_sar),
                    "variance_sar": float(v.variance_sar),
                    "variance_pct": float(v.variance_percent),
                    "status": v.variance_status.value,
                    "is_material": v.is_material,
                    "ytd_budget_sar": float(v.ytd_budget_sar),
                    "ytd_actual_sar": float(v.ytd_actual_sar),
                    "ytd_variance_sar": float(v.ytd_variance_sar),
                }
                for v in variances
            ],
        }

    async def create_forecast_revision(
        self,
        baseline_version_id: uuid.UUID,
        forecast_name: str,
        current_period: int,
    ) -> BudgetVersion:
        """
        Create forecast revision based on actuals to date.

        Creates a new forecast version that:
        - Keeps actuals for periods 1 to current_period
        - Projects remaining periods based on trends

        Args:
            baseline_version_id: Base budget version UUID
            forecast_name: Name for forecast version
            current_period: Current period (actuals available up to this period)

        Returns:
            New BudgetVersion instance with forecast data

        Raises:
            NotFoundError: If baseline version not found
            BusinessRuleError: If forecast cannot be created
        """
        # Get baseline version
        baseline_query = select(BudgetVersion).where(
            BudgetVersion.id == baseline_version_id
        )
        baseline_result = await self.session.execute(baseline_query)
        baseline = baseline_result.scalar_one_or_none()

        if not baseline:
            raise NotFoundError("BudgetVersion", str(baseline_version_id))

        # Check if forecast already exists
        existing_forecast_query = select(BudgetVersion).where(
            and_(
                BudgetVersion.name == forecast_name,
                BudgetVersion.fiscal_year == baseline.fiscal_year,
                BudgetVersion.deleted_at.is_(None),
            )
        )
        existing_result = await self.session.execute(existing_forecast_query)
        if existing_result.scalar_one_or_none():
            raise BusinessRuleError(
                f"Forecast version '{forecast_name}' already exists for fiscal year {baseline.fiscal_year}"
            )

        # Create forecast version
        forecast_version = BudgetVersion(
            name=forecast_name,
            fiscal_year=baseline.fiscal_year,
            academic_year=baseline.academic_year,
            status=BudgetVersionStatus.FORECAST,
        )
        self.session.add(forecast_version)
        await self.session.flush()
        await self.session.refresh(forecast_version)

        # Copy baseline data and adjust with actuals
        # This would involve:
        # 1. Copy all baseline planning data
        # 2. Replace periods 1-current_period with actual results
        # 3. Project remaining periods using trends or baseline
        # Implementation would be added here

        return forecast_version

    async def _get_budget_amounts(
        self,
        budget_version_id: uuid.UUID,
        account_code: str | None = None,
    ) -> dict[str, Decimal]:
        """
        Fetch consolidated budget amounts keyed by account code.

        Args:
            budget_version_id: Budget version to pull consolidation for
            account_code: Optional specific account filter

        Returns:
            Dict of account_code -> annual budget amount
        """
        query = select(BudgetConsolidation).where(
            and_(
                BudgetConsolidation.budget_version_id == budget_version_id,
                BudgetConsolidation.deleted_at.is_(None),
            )
        )

        if account_code:
            query = query.where(BudgetConsolidation.account_code == account_code)

        result = await self.session.execute(query)
        consolidations = result.scalars().all()
        return {c.account_code: Decimal(c.amount_sar) for c in consolidations}

    async def _get_ytd_actual(
        self,
        fiscal_year: int,
        account_code: str,
        through_period: int,
    ) -> Decimal:
        """
        Aggregate actuals from period 1 through the given period.

        Args:
            fiscal_year: Fiscal year to filter
            account_code: Account code to aggregate
            through_period: Inclusive period upper bound (1-12)

        Returns:
            Decimal total of actual amounts
        """
        ytd_query = select(ActualData).where(
            and_(
                ActualData.fiscal_year == fiscal_year,
                ActualData.period <= through_period,
                ActualData.account_code == account_code,
                ActualData.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(ytd_query)
        records = result.scalars().all()
        total = sum((Decimal(str(r.amount_sar)) for r in records), Decimal("0"))
        return total

    def _calculate_variance_amount(
        self,
        account_code: str,
        budget_amount: Decimal,
        actual_amount: Decimal,
    ) -> Decimal:
        """
        Calculate variance amount based on account type.

        For expenses (60xxx-68xxx): Variance = Budget - Actual
        For revenue (70xxx-77xxx): Variance = Actual - Budget

        Args:
            account_code: French PCG account code
            budget_amount: Budgeted amount
            actual_amount: Actual amount

        Returns:
            Variance amount (positive = favorable, negative = unfavorable)
        """
        # Determine if revenue or expense account
        is_revenue = account_code.startswith("7")
        is_expense = account_code.startswith("6")

        if is_revenue:
            # Revenue: Actual - Budget (higher actual is favorable)
            return actual_amount - budget_amount
        elif is_expense:
            # Expense: Budget - Actual (lower actual is favorable)
            return budget_amount - actual_amount
        else:
            # Default to expense logic
            return budget_amount - actual_amount

    def _determine_variance_status(
        self,
        account_code: str,
        variance_sar: Decimal,
        variance_percent: Decimal,
    ) -> VarianceStatus:
        """
        Determine variance favorability status.

        Args:
            account_code: French PCG account code
            variance_sar: Variance amount in SAR
            variance_percent: Variance percentage

        Returns:
            VarianceStatus enum value
        """
        # Check if within tolerance (±5%)
        if abs(variance_percent) <= Decimal("5.0"):
            return VarianceStatus.NEUTRAL

        # Positive variance is favorable, negative is unfavorable
        if variance_sar > 0:
            return VarianceStatus.FAVORABLE
        else:
            return VarianceStatus.UNFAVORABLE

    def _is_variance_material(
        self,
        variance_sar: Decimal,
        variance_percent: Decimal,
    ) -> bool:
        """
        Determine if variance is material.

        Material if: |Variance %| > 5% OR |Variance| > 100,000 SAR

        Args:
            variance_sar: Variance amount in SAR
            variance_percent: Variance percentage

        Returns:
            True if variance is material
        """
        return (
            abs(variance_percent) > self.MATERIALITY_THRESHOLD_PCT
            or abs(variance_sar) > self.MATERIALITY_THRESHOLD_SAR
        )
