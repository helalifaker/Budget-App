"""
Tests for BudgetActualService.

Tests cover:
- Importing actual data from Odoo
- Variance calculation
- Variance reports
- Forecast revisions based on actuals
"""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from app.models.analysis import (
    ActualData,
    ActualDataSource,
    BudgetVsActual,
    VarianceStatus,
)
from app.models.configuration import BudgetVersion
from app.services.budget_actual_service import BudgetActualService
from app.services.exceptions import NotFoundError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class TestImportActuals:
    """Tests for importing actual financial data."""

    @pytest.mark.asyncio
    async def test_import_actuals_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful import of actual data."""
        service = BudgetActualService(db_session)
        odoo_data = [
            {
                "fiscal_year": 2025,
                "period": 1,
                "account_code": "70110",
                "account_name": "Tuition T1",
                "amount_sar": 1000000.00,
                "currency": "SAR",
            },
            {
                "fiscal_year": 2025,
                "period": 1,
                "account_code": "70120",
                "account_name": "Tuition T2",
                "amount_sar": 500000.00,
            },
        ]

        result = await service.import_actuals(test_budget_version.id, odoo_data)

        assert result["records_imported"] == 2
        assert result["fiscal_year"] == 2025
        assert 1 in result["periods_covered"]
        assert result["total_amount_sar"] == 1500000.00
        assert "import_batch_id" in result

    @pytest.mark.asyncio
    async def test_import_actuals_with_batch_id(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test import with custom batch ID."""
        service = BudgetActualService(db_session)
        custom_batch_id = uuid.uuid4()
        odoo_data = [
            {
                "fiscal_year": 2025,
                "period": 2,
                "account_code": "64110",
                "amount_sar": 200000.00,
            },
        ]

        result = await service.import_actuals(
            test_budget_version.id,
            odoo_data,
            import_batch_id=custom_batch_id,
        )

        assert result["import_batch_id"] == str(custom_batch_id)

    @pytest.mark.asyncio
    async def test_import_actuals_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test import with invalid budget version."""
        service = BudgetActualService(db_session)
        odoo_data = [
            {
                "fiscal_year": 2025,
                "period": 1,
                "account_code": "70110",
                "amount_sar": 100000.00,
            },
        ]

        with pytest.raises(NotFoundError):
            await service.import_actuals(uuid.uuid4(), odoo_data)

    @pytest.mark.asyncio
    async def test_import_actuals_missing_fields(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test import with missing required fields."""
        service = BudgetActualService(db_session)
        odoo_data = [
            {
                "fiscal_year": 2025,
                # Missing: period, account_code, amount_sar
            },
        ]

        with pytest.raises(ValidationError):
            await service.import_actuals(test_budget_version.id, odoo_data)

    @pytest.mark.asyncio
    async def test_import_actuals_multiple_periods(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test import covering multiple periods."""
        service = BudgetActualService(db_session)
        odoo_data = [
            {
                "fiscal_year": 2025,
                "period": 1,
                "account_code": "70110",
                "amount_sar": 100000.00,
            },
            {
                "fiscal_year": 2025,
                "period": 2,
                "account_code": "70110",
                "amount_sar": 100000.00,
            },
            {
                "fiscal_year": 2025,
                "period": 3,
                "account_code": "70110",
                "amount_sar": 100000.00,
            },
        ]

        result = await service.import_actuals(test_budget_version.id, odoo_data)

        assert result["records_imported"] == 3
        assert sorted(result["periods_covered"]) == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_import_actuals_empty_list(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test import with empty data list."""
        service = BudgetActualService(db_session)

        result = await service.import_actuals(test_budget_version.id, [])

        assert result["records_imported"] == 0
        assert result["total_amount_sar"] == 0.0


class TestCalculateVariance:
    """Tests for variance calculation."""

    @pytest.mark.asyncio
    async def test_calculate_variance_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful variance calculation."""
        # Create actual data first
        actual = ActualData(
            fiscal_year=test_budget_version.fiscal_year,
            period=1,
            account_code="70110",
            account_name="Tuition T1",
            amount_sar=Decimal("1000000.00"),
            currency="SAR",
            source=ActualDataSource.ODOO_IMPORT,
            import_batch_id=uuid.uuid4(),
            import_date=datetime.utcnow(),
        )
        db_session.add(actual)
        await db_session.flush()

        service = BudgetActualService(db_session)
        result = await service.calculate_variance(test_budget_version.id, period=1)

        assert len(result) > 0
        assert all(isinstance(v, BudgetVsActual) for v in result)

    @pytest.mark.asyncio
    async def test_calculate_variance_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test variance calculation with invalid version."""
        service = BudgetActualService(db_session)

        with pytest.raises(NotFoundError):
            await service.calculate_variance(uuid.uuid4(), period=1)

    @pytest.mark.asyncio
    async def test_calculate_variance_specific_account(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test variance calculation for specific account."""
        # Create actual data
        actual = ActualData(
            fiscal_year=test_budget_version.fiscal_year,
            period=2,
            account_code="64110",
            account_name="Salaries",
            amount_sar=Decimal("500000.00"),
            currency="SAR",
            source=ActualDataSource.ODOO_IMPORT,
            import_batch_id=uuid.uuid4(),
            import_date=datetime.utcnow(),
        )
        db_session.add(actual)
        await db_session.flush()

        service = BudgetActualService(db_session)
        result = await service.calculate_variance(
            test_budget_version.id,
            period=2,
            account_code="64110",
        )

        assert len(result) > 0
        assert all(v.account_code == "64110" for v in result)

    @pytest.mark.asyncio
    async def test_calculate_variance_updates_existing(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test that variance calculation updates existing records."""
        # Create actual data
        actual = ActualData(
            fiscal_year=test_budget_version.fiscal_year,
            period=3,
            account_code="70110",
            amount_sar=Decimal("100000.00"),
            currency="SAR",
            source=ActualDataSource.ODOO_IMPORT,
            import_batch_id=uuid.uuid4(),
            import_date=datetime.utcnow(),
        )
        db_session.add(actual)
        await db_session.flush()

        service = BudgetActualService(db_session)

        # Calculate first time
        result1 = await service.calculate_variance(test_budget_version.id, period=3)

        # Calculate again - should update
        result2 = await service.calculate_variance(test_budget_version.id, period=3)

        # Should update existing, not create new
        assert len(result1) == len(result2)


class TestGetVarianceReport:
    """Tests for variance report generation."""

    @pytest.mark.asyncio
    async def test_get_variance_report_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test successful variance report generation."""
        # Create variance records
        variance = BudgetVsActual(
            budget_version_id=test_budget_version.id,
            account_code="70110",
            period=1,
            budget_amount_sar=Decimal("1000000.00"),
            actual_amount_sar=Decimal("950000.00"),
            variance_sar=Decimal("-50000.00"),
            variance_percent=Decimal("-5.00"),
            variance_status=VarianceStatus.UNFAVORABLE,
            ytd_budget_sar=Decimal("1000000.00"),
            ytd_actual_sar=Decimal("950000.00"),
            ytd_variance_sar=Decimal("-50000.00"),
            is_material=True,
        )
        db_session.add(variance)
        await db_session.flush()

        service = BudgetActualService(db_session)
        result = await service.get_variance_report(test_budget_version.id)

        assert "summary" in result or "variances" in result

    @pytest.mark.asyncio
    async def test_get_variance_report_invalid_version(
        self,
        db_session: AsyncSession,
    ):
        """Test variance report with invalid version."""
        service = BudgetActualService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_variance_report(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_variance_report_filter_by_period(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test variance report filtered by period."""
        # Create variances for different periods
        variance1 = BudgetVsActual(
            budget_version_id=test_budget_version.id,
            account_code="70110",
            period=1,
            budget_amount_sar=Decimal("100000.00"),
            actual_amount_sar=Decimal("100000.00"),
            variance_sar=Decimal("0.00"),
            variance_percent=Decimal("0.00"),
            variance_status=VarianceStatus.NEUTRAL,
            ytd_budget_sar=Decimal("100000.00"),
            ytd_actual_sar=Decimal("100000.00"),
            ytd_variance_sar=Decimal("0.00"),
            is_material=False,
        )
        variance2 = BudgetVsActual(
            budget_version_id=test_budget_version.id,
            account_code="70110",
            period=2,
            budget_amount_sar=Decimal("200000.00"),
            actual_amount_sar=Decimal("200000.00"),
            variance_sar=Decimal("0.00"),
            variance_percent=Decimal("0.00"),
            variance_status=VarianceStatus.NEUTRAL,
            ytd_budget_sar=Decimal("300000.00"),
            ytd_actual_sar=Decimal("300000.00"),
            ytd_variance_sar=Decimal("0.00"),
            is_material=False,
        )
        db_session.add_all([variance1, variance2])
        await db_session.flush()

        service = BudgetActualService(db_session)
        result = await service.get_variance_report(
            test_budget_version.id,
            period=1,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_variance_report_filter_by_account_pattern(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test variance report filtered by account code pattern."""
        # Create variances for different account types
        revenue = BudgetVsActual(
            budget_version_id=test_budget_version.id,
            account_code="70110",
            period=1,
            budget_amount_sar=Decimal("100000.00"),
            actual_amount_sar=Decimal("100000.00"),
            variance_sar=Decimal("0.00"),
            variance_percent=Decimal("0.00"),
            variance_status=VarianceStatus.NEUTRAL,
            ytd_budget_sar=Decimal("100000.00"),
            ytd_actual_sar=Decimal("100000.00"),
            ytd_variance_sar=Decimal("0.00"),
            is_material=False,
        )
        expense = BudgetVsActual(
            budget_version_id=test_budget_version.id,
            account_code="64110",
            period=1,
            budget_amount_sar=Decimal("50000.00"),
            actual_amount_sar=Decimal("50000.00"),
            variance_sar=Decimal("0.00"),
            variance_percent=Decimal("0.00"),
            variance_status=VarianceStatus.NEUTRAL,
            ytd_budget_sar=Decimal("50000.00"),
            ytd_actual_sar=Decimal("50000.00"),
            ytd_variance_sar=Decimal("0.00"),
            is_material=False,
        )
        db_session.add_all([revenue, expense])
        await db_session.flush()

        service = BudgetActualService(db_session)
        result = await service.get_variance_report(
            test_budget_version.id,
            account_code_pattern="64%",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_variance_report_material_only(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test variance report with material variances only."""
        # Create material and non-material variances
        material = BudgetVsActual(
            budget_version_id=test_budget_version.id,
            account_code="70110",
            period=1,
            budget_amount_sar=Decimal("1000000.00"),
            actual_amount_sar=Decimal("900000.00"),
            variance_sar=Decimal("-100000.00"),
            variance_percent=Decimal("-10.00"),
            variance_status=VarianceStatus.UNFAVORABLE,
            ytd_budget_sar=Decimal("1000000.00"),
            ytd_actual_sar=Decimal("900000.00"),
            ytd_variance_sar=Decimal("-100000.00"),
            is_material=True,
        )
        non_material = BudgetVsActual(
            budget_version_id=test_budget_version.id,
            account_code="70120",
            period=1,
            budget_amount_sar=Decimal("100000.00"),
            actual_amount_sar=Decimal("99000.00"),
            variance_sar=Decimal("-1000.00"),
            variance_percent=Decimal("-1.00"),
            variance_status=VarianceStatus.NEUTRAL,
            ytd_budget_sar=Decimal("100000.00"),
            ytd_actual_sar=Decimal("99000.00"),
            ytd_variance_sar=Decimal("-1000.00"),
            is_material=False,
        )
        db_session.add_all([material, non_material])
        await db_session.flush()

        service = BudgetActualService(db_session)
        result = await service.get_variance_report(
            test_budget_version.id,
            material_only=True,
        )

        assert result is not None


class TestVarianceHelpers:
    """Tests for variance helper methods."""

    @pytest.mark.asyncio
    async def test_materiality_threshold_percentage(
        self,
        db_session: AsyncSession,
    ):
        """Test materiality threshold by percentage."""
        service = BudgetActualService(db_session)

        # Test using internal threshold
        assert service.MATERIALITY_THRESHOLD_PCT == Decimal("5.0")

    @pytest.mark.asyncio
    async def test_materiality_threshold_amount(
        self,
        db_session: AsyncSession,
    ):
        """Test materiality threshold by amount."""
        service = BudgetActualService(db_session)

        # Test using internal threshold
        assert service.MATERIALITY_THRESHOLD_SAR == Decimal("100000.00")
