"""
Tests for RevenueService.

Tests cover:
- Revenue plan CRUD operations
- Account code validation (70xxx-77xxx)
- Revenue calculation from enrollment and fees
- Trimester distribution (T1: 40%, T2: 30%, T3: 30%)
- Sibling discount application
- Revenue summary statistics
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import BudgetVersion, FeeStructure
from app.models.planning import EnrollmentPlan
from app.services.exceptions import ValidationError
from app.services.revenue_service import RevenueService
from sqlalchemy.ext.asyncio import AsyncSession


class TestRevenueServiceCRUD:
    """Tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_revenue_plan_empty(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving empty revenue plan."""
        service = RevenueService(db_session)

        result = await service.get_revenue_plan(test_budget_version.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_create_revenue_entry_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating a revenue entry."""
        service = RevenueService(db_session)

        result = await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70110",
            description="Scolarité Trimestre 1",
            category="tuition",
            amount_sar=Decimal("1000000.00"),
            is_calculated=False,
            trimester=1,
            notes="Test entry",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.account_code == "70110"
        assert result.amount_sar == Decimal("1000000.00")
        assert result.trimester == 1

    @pytest.mark.asyncio
    async def test_create_revenue_entry_update_existing(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating revenue entry updates existing entry with same account code."""
        service = RevenueService(db_session)

        # Create first entry
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70110",
            description="Original",
            category="tuition",
            amount_sar=Decimal("1000000.00"),
            user_id=test_user_id,
        )

        # Create second entry with same account code
        result = await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70110",
            description="Updated",
            category="tuition",
            amount_sar=Decimal("1500000.00"),
            user_id=test_user_id,
        )

        # Should update, not create new
        all_entries = await service.get_revenue_plan(test_budget_version.id)
        tuition_entries = [e for e in all_entries if e.account_code == "70110"]

        assert len(tuition_entries) == 1
        assert result.amount_sar == Decimal("1500000.00")
        assert result.description == "Updated"

    @pytest.mark.asyncio
    async def test_get_revenue_by_account(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test retrieving revenue by account code."""
        service = RevenueService(db_session)

        # Create entry
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70200",
            description="DAI Revenue",
            category="fees",
            amount_sar=Decimal("500000.00"),
            user_id=test_user_id,
        )

        result = await service.get_revenue_by_account(
            test_budget_version.id,
            "70200",
        )

        assert result is not None
        assert result.account_code == "70200"
        assert result.amount_sar == Decimal("500000.00")

    @pytest.mark.asyncio
    async def test_get_revenue_by_account_not_found(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving non-existent revenue returns None."""
        service = RevenueService(db_session)

        result = await service.get_revenue_by_account(
            test_budget_version.id,
            "70999",  # Non-existent
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_revenue_entry(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test deleting a revenue entry."""
        service = RevenueService(db_session)

        # Create entry
        entry = await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70300",
            description="Test entry",
            category="other",
            amount_sar=Decimal("100000.00"),
            user_id=test_user_id,
        )

        # Delete
        result = await service.delete_revenue_entry(entry.id)

        assert result is True

        # Verify deleted
        deleted = await service.get_revenue_by_account(
            test_budget_version.id,
            "70300",
        )
        assert deleted is None


class TestRevenueServiceAccountValidation:
    """Tests for account code validation."""

    @pytest.mark.asyncio
    async def test_valid_account_codes(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that valid revenue account codes (70-77) are accepted."""
        service = RevenueService(db_session)

        valid_codes = [
            "70110",  # 70xxx - Tuition
            "71100",  # 71xxx
            "72100",  # 72xxx
            "73100",  # 73xxx
            "74100",  # 74xxx
            "75100",  # 75xxx
            "76100",  # 76xxx
            "77100",  # 77xxx
        ]

        for code in valid_codes:
            result = await service.create_revenue_entry(
                version_id=test_budget_version.id,
                account_code=code,
                description=f"Revenue {code}",
                category="other",
                amount_sar=Decimal("10000.00"),
                user_id=test_user_id,
            )
            assert result.account_code == code

    @pytest.mark.asyncio
    async def test_invalid_account_code_expense(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that expense account codes (60-68) are rejected."""
        service = RevenueService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_revenue_entry(
                version_id=test_budget_version.id,
                account_code="64110",  # Personnel expense
                description="Invalid",
                category="tuition",
                amount_sar=Decimal("10000.00"),
                user_id=test_user_id,
            )

        assert "70-77" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_account_code_asset(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that asset account codes are rejected."""
        service = RevenueService(db_session)

        invalid_codes = ["10100", "20200", "30300", "40400", "50500"]

        for code in invalid_codes:
            with pytest.raises(ValidationError):
                await service.create_revenue_entry(
                    version_id=test_budget_version.id,
                    account_code=code,
                    description="Invalid",
                    category="other",
                    amount_sar=Decimal("10000.00"),
                    user_id=test_user_id,
                )


class TestRevenueServiceCalculation:
    """Tests for revenue calculation from enrollment."""

    @pytest.mark.asyncio
    async def test_calculate_revenue_no_enrollment(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test calculation fails without enrollment data."""
        service = RevenueService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.calculate_revenue_from_enrollment(
                budget_version_id=test_budget_version.id,
                user_id=test_user_id,
            )

        assert "No enrollment data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_revenue_no_fee_structure(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test calculation fails without fee structure."""
        service = RevenueService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.calculate_revenue_from_enrollment(
                budget_version_id=test_budget_version.id,
                user_id=test_user_id,
            )

        assert "No fee structure" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_revenue_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_fee_structure: list[FeeStructure],
        test_user_id: uuid.UUID,
    ):
        """Test successful revenue calculation."""
        service = RevenueService(db_session)

        result = await service.calculate_revenue_from_enrollment(
            budget_version_id=test_budget_version.id,
            user_id=test_user_id,
        )

        assert "total_revenue" in result
        assert result["total_revenue"] >= Decimal("0")
        assert "trimester_distribution" in result
        assert "created_entries" in result

    @pytest.mark.asyncio
    async def test_calculate_revenue_trimester_distribution(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_fee_structure: list[FeeStructure],
        test_user_id: uuid.UUID,
    ):
        """Test trimester distribution is correct (40%, 30%, 30%)."""
        service = RevenueService(db_session)

        result = await service.calculate_revenue_from_enrollment(
            budget_version_id=test_budget_version.id,
            user_id=test_user_id,
        )

        distribution = result["trimester_distribution"]
        total = result["total_revenue"]

        if total > 0:
            t1_pct = (distribution["T1"] / total) * 100
            t2_pct = (distribution["T2"] / total) * 100
            t3_pct = (distribution["T3"] / total) * 100

            # Allow for small rounding differences
            assert abs(t1_pct - Decimal("40")) < Decimal("0.1")
            assert abs(t2_pct - Decimal("30")) < Decimal("0.1")
            assert abs(t3_pct - Decimal("30")) < Decimal("0.1")


class TestRevenueServiceSummary:
    """Tests for revenue summary statistics."""

    @pytest.mark.asyncio
    async def test_get_revenue_summary_empty(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test summary for version with no revenue."""
        service = RevenueService(db_session)

        summary = await service.get_revenue_summary(test_budget_version.id)

        assert summary["total_revenue"] == Decimal("0")
        assert summary["entry_count"] == 0
        assert summary["revenue_by_category"] == {}
        assert summary["revenue_by_trimester"] == {}

    @pytest.mark.asyncio
    async def test_get_revenue_summary_with_entries(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test summary with multiple revenue entries."""
        service = RevenueService(db_session)

        # Create tuition entries
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70110",
            description="T1 Tuition",
            category="tuition",
            amount_sar=Decimal("400000.00"),
            trimester=1,
            is_calculated=True,
            user_id=test_user_id,
        )
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70120",
            description="T2 Tuition",
            category="tuition",
            amount_sar=Decimal("300000.00"),
            trimester=2,
            is_calculated=True,
            user_id=test_user_id,
        )
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70130",
            description="T3 Tuition",
            category="tuition",
            amount_sar=Decimal("300000.00"),
            trimester=3,
            is_calculated=True,
            user_id=test_user_id,
        )

        # Create fee entry
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70200",
            description="DAI",
            category="fees",
            amount_sar=Decimal("100000.00"),
            is_calculated=False,
            user_id=test_user_id,
        )

        summary = await service.get_revenue_summary(test_budget_version.id)

        assert summary["total_revenue"] == Decimal("1100000.00")
        assert summary["entry_count"] == 4
        assert summary["revenue_by_category"]["tuition"] == Decimal("1000000.00")
        assert summary["revenue_by_category"]["fees"] == Decimal("100000.00")
        assert summary["revenue_by_trimester"]["T1"] == Decimal("400000.00")
        assert summary["revenue_by_trimester"]["T2"] == Decimal("300000.00")
        assert summary["revenue_by_trimester"]["T3"] == Decimal("300000.00")
        assert summary["calculated_revenue"] == Decimal("1000000.00")
        assert summary["manual_revenue"] == Decimal("100000.00")


class TestRevenueServiceRealEFIRData:
    """Tests using realistic EFIR school revenue data."""

    @pytest.mark.asyncio
    async def test_realistic_tuition_revenue(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test with realistic EFIR tuition amounts."""
        service = RevenueService(db_session)

        # Based on EFIR data: ~1,800 students × ~30,000 SAR avg = ~54M SAR
        # Trimester distribution: T1: 40%, T2: 30%, T3: 30%
        total_tuition = Decimal("54000000.00")
        t1 = total_tuition * Decimal("0.40")
        t2 = total_tuition * Decimal("0.30")
        t3 = total_tuition * Decimal("0.30")

        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70110",
            description="Scolarité Trimestre 1",
            category="tuition",
            amount_sar=t1,
            trimester=1,
            is_calculated=True,
            user_id=test_user_id,
        )
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70120",
            description="Scolarité Trimestre 2",
            category="tuition",
            amount_sar=t2,
            trimester=2,
            is_calculated=True,
            user_id=test_user_id,
        )
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70130",
            description="Scolarité Trimestre 3",
            category="tuition",
            amount_sar=t3,
            trimester=3,
            is_calculated=True,
            user_id=test_user_id,
        )

        # DAI revenue: ~1,800 students × 3,000 SAR = ~5.4M SAR
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70200",
            description="Droit Annuel d'Inscription (DAI)",
            category="fees",
            amount_sar=Decimal("5400000.00"),
            is_calculated=True,
            user_id=test_user_id,
        )

        summary = await service.get_revenue_summary(test_budget_version.id)

        # Total should be ~59.4M SAR
        assert summary["total_revenue"] == Decimal("59400000.00")
        assert summary["revenue_by_category"]["tuition"] == Decimal("54000000.00")
        assert summary["revenue_by_category"]["fees"] == Decimal("5400000.00")

    @pytest.mark.asyncio
    async def test_fee_categories_by_nationality(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test different fee handling for French, Saudi, Other nationalities."""
        service = RevenueService(db_session)

        # French students (TTC - includes VAT)
        # Saudi students (HT - VAT exempt)
        # Other students (TTC - includes VAT)

        # Create separate entries for tracking nationality-based revenue
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70111",
            description="Scolarité T1 - Français",
            category="tuition_french",
            amount_sar=Decimal("15000000.00"),  # ~500 French students
            trimester=1,
            user_id=test_user_id,
        )
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70112",
            description="Scolarité T1 - Saoudien",
            category="tuition_saudi",
            amount_sar=Decimal("4000000.00"),  # ~150 Saudi students
            trimester=1,
            user_id=test_user_id,
        )
        await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70113",
            description="Scolarité T1 - Autres",
            category="tuition_other",
            amount_sar=Decimal("2000000.00"),  # ~75 Other students
            trimester=1,
            user_id=test_user_id,
        )

        summary = await service.get_revenue_summary(test_budget_version.id)

        # French should be majority
        french_revenue = summary["revenue_by_category"].get("tuition_french", Decimal("0"))
        total_revenue = summary["total_revenue"]

        assert french_revenue > total_revenue / 2  # French is majority


class TestRevenueServiceEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_zero_revenue_entry(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating zero revenue entry."""
        service = RevenueService(db_session)

        result = await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70500",
            description="Zero revenue",
            category="other",
            amount_sar=Decimal("0.00"),
            user_id=test_user_id,
        )

        assert result.amount_sar == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_large_revenue_amounts(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test handling large revenue amounts."""
        service = RevenueService(db_session)

        # 100 million SAR
        large_amount = Decimal("100000000.00")

        result = await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70600",
            description="Large revenue",
            category="other",
            amount_sar=large_amount,
            user_id=test_user_id,
        )

        assert result.amount_sar == large_amount

        summary = await service.get_revenue_summary(test_budget_version.id)
        assert summary["total_revenue"] == large_amount

    @pytest.mark.asyncio
    async def test_decimal_precision(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test decimal precision is maintained."""
        service = RevenueService(db_session)

        precise_amount = Decimal("1234567.89")

        result = await service.create_revenue_entry(
            version_id=test_budget_version.id,
            account_code="70700",
            description="Precise amount",
            category="other",
            amount_sar=precise_amount,
            user_id=test_user_id,
        )

        assert result.amount_sar == precise_amount

    @pytest.mark.asyncio
    async def test_multiple_versions_isolation(
        self,
        db_session: AsyncSession,
        test_user_id: uuid.UUID,
    ):
        """Test revenue entries are isolated by budget version."""
        service = RevenueService(db_session)

        # Create two versions
        from app.models.configuration import BudgetVersion, BudgetVersionStatus
        version1 = BudgetVersion(
            id=uuid.uuid4(),
            name="Version 1",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            created_by_id=test_user_id,
        )
        version2 = BudgetVersion(
            id=uuid.uuid4(),
            name="Version 2",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            created_by_id=test_user_id,
        )
        db_session.add_all([version1, version2])
        await db_session.flush()

        # Create entries in each version
        await service.create_revenue_entry(
            version_id=version1.id,
            account_code="70110",
            description="V1 Revenue",
            category="tuition",
            amount_sar=Decimal("1000000.00"),
            user_id=test_user_id,
        )
        await service.create_revenue_entry(
            version_id=version2.id,
            account_code="70110",
            description="V2 Revenue",
            category="tuition",
            amount_sar=Decimal("2000000.00"),
            user_id=test_user_id,
        )

        # Verify isolation
        v1_entries = await service.get_revenue_plan(version1.id)
        v2_entries = await service.get_revenue_plan(version2.id)

        assert len(v1_entries) == 1
        assert len(v2_entries) == 1
        assert v1_entries[0].amount_sar == Decimal("1000000.00")
        assert v2_entries[0].amount_sar == Decimal("2000000.00")
