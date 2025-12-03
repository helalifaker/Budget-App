"""
Tests for CostService.

Tests cover:
- Personnel cost CRUD operations
- Operating cost CRUD operations
- Account code validation (64xxx for personnel, 60-68xxx for operating)
- Cost calculation from DHG allocations
- Driver-based operating cost calculation
- Cost summary statistics
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import (
    AcademicCycle,
    BudgetVersion,
    TeacherCategory,
    TeacherCostParam,
)
from app.models.planning import EnrollmentPlan, OperatingCostPlan, PersonnelCostPlan
from app.services.cost_service import CostService
from app.services.exceptions import ValidationError


class TestCostServicePersonnelCRUD:
    """Tests for personnel cost CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_personnel_costs_empty(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving empty personnel costs."""
        service = CostService(db_session)

        result = await service.get_personnel_costs(test_budget_version.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_create_personnel_cost_entry(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        test_user_id: uuid.UUID,
    ):
        """Test creating a personnel cost entry."""
        service = CostService(db_session)

        result = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="Teaching Staff - Secondary",
            fte_count=Decimal("10.5"),
            unit_cost_sar=Decimal("180000.00"),
            category_id=teacher_categories["LOCAL"].id,
            is_calculated=False,
            notes="Test entry",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.account_code == "64110"
        assert result.fte_count == Decimal("10.5")
        assert result.unit_cost_sar == Decimal("180000.00")
        assert result.total_cost_sar == Decimal("1890000.00")  # 10.5 × 180000

    @pytest.mark.asyncio
    async def test_create_personnel_cost_invalid_account(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating personnel cost with invalid account code."""
        service = CostService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_personnel_cost_entry(
                version_id=test_budget_version.id,
                account_code="70110",  # Revenue account, not personnel
                description="Invalid",
                fte_count=Decimal("1"),
                unit_cost_sar=Decimal("100000.00"),
                user_id=test_user_id,
            )

        assert "64" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_personnel_cost_by_account(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test retrieving personnel cost by account code."""
        service = CostService(db_session)

        # Create entry
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64120",
            description="Admin Staff",
            fte_count=Decimal("5"),
            unit_cost_sar=Decimal("150000.00"),
            user_id=test_user_id,
        )

        result = await service.get_personnel_cost_by_account(
            test_budget_version.id,
            "64120",
        )

        assert result is not None
        assert result.account_code == "64120"

    @pytest.mark.asyncio
    async def test_delete_personnel_cost_entry(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test deleting a personnel cost entry."""
        service = CostService(db_session)

        # Create entry
        entry = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64130",
            description="Support Staff",
            fte_count=Decimal("3"),
            unit_cost_sar=Decimal("80000.00"),
            user_id=test_user_id,
        )

        # Delete
        result = await service.delete_personnel_cost_entry(entry.id)

        assert result is True


class TestCostServiceOperatingCRUD:
    """Tests for operating cost CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_operating_costs_empty(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving empty operating costs."""
        service = CostService(db_session)

        result = await service.get_operating_costs(test_budget_version.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_create_operating_cost_entry(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating an operating cost entry."""
        service = CostService(db_session)

        result = await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="60610",
            description="Student Supplies",
            category="supplies",
            amount_sar=Decimal("500000.00"),
            is_calculated=False,
            notes="Test entry",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.account_code == "60610"
        assert result.amount_sar == Decimal("500000.00")

    @pytest.mark.asyncio
    async def test_create_operating_cost_invalid_account(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating operating cost with invalid account code."""
        service = CostService(db_session)

        # 64xxx is personnel, not operating
        with pytest.raises(ValidationError) as exc_info:
            await service.create_operating_cost_entry(
                version_id=test_budget_version.id,
                account_code="64110",
                description="Invalid",
                category="supplies",
                amount_sar=Decimal("10000.00"),
                user_id=test_user_id,
            )

        assert "60-63, 65-66, or 68" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_valid_operating_account_codes(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that valid operating account codes are accepted."""
        service = CostService(db_session)

        valid_codes = [
            ("60610", "Supplies"),
            ("61520", "Maintenance"),
            ("62600", "Insurance"),
            ("63100", "Professional Fees"),
            ("65100", "Other Operating"),
            ("66100", "Financial Charges"),
            ("68100", "Depreciation"),
        ]

        for code, description in valid_codes:
            result = await service.create_operating_cost_entry(
                version_id=test_budget_version.id,
                account_code=code,
                description=description,
                category="other",
                amount_sar=Decimal("10000.00"),
                user_id=test_user_id,
            )
            assert result.account_code == code

    @pytest.mark.asyncio
    async def test_delete_operating_cost_entry(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test deleting an operating cost entry."""
        service = CostService(db_session)

        # Create entry
        entry = await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="60700",
            description="Test",
            category="other",
            amount_sar=Decimal("5000.00"),
            user_id=test_user_id,
        )

        # Delete
        result = await service.delete_operating_cost_entry(entry.id)

        assert result is True


class TestCostServiceCalculation:
    """Tests for cost calculation methods."""

    @pytest.mark.asyncio
    async def test_calculate_operating_costs_no_enrollment(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test operating cost calculation fails without enrollment."""
        service = CostService(db_session)

        cost_drivers = {
            "cost_per_student_supplies": Decimal("500.00"),
        }

        with pytest.raises(ValidationError) as exc_info:
            await service.calculate_operating_costs(
                version_id=test_budget_version.id,
                cost_drivers=cost_drivers,
                user_id=test_user_id,
            )

        assert "No enrollment data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_operating_costs_enrollment_driven(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test operating cost calculation with enrollment driver."""
        service = CostService(db_session)

        cost_drivers = {
            "cost_per_student_supplies": Decimal("500.00"),
        }

        result = await service.calculate_operating_costs(
            version_id=test_budget_version.id,
            cost_drivers=cost_drivers,
            user_id=test_user_id,
        )

        # Enrollment from fixtures: 35 + 15 + 80 = 130 students
        expected_supplies_cost = 130 * Decimal("500.00")

        assert result["enrollment_count"] == 130
        assert result["enrollment_driven_costs"] == expected_supplies_cost
        assert len(result["created_entries"]) >= 1

    @pytest.mark.asyncio
    async def test_calculate_operating_costs_facility_driven(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test operating cost calculation with facility drivers."""
        service = CostService(db_session)

        cost_drivers = {
            "square_meters": Decimal("5000"),  # 5000 sqm facility
            "cost_per_sqm_maintenance": Decimal("50.00"),  # 50 SAR/sqm
        }

        result = await service.calculate_operating_costs(
            version_id=test_budget_version.id,
            cost_drivers=cost_drivers,
            user_id=test_user_id,
        )

        expected_maintenance = Decimal("5000") * Decimal("50.00")

        assert result["facility_driven_costs"] == expected_maintenance

    @pytest.mark.asyncio
    async def test_calculate_operating_costs_fixed(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test operating cost calculation with fixed costs."""
        service = CostService(db_session)

        cost_drivers = {
            "insurance_annual": Decimal("500000.00"),
        }

        result = await service.calculate_operating_costs(
            version_id=test_budget_version.id,
            cost_drivers=cost_drivers,
            user_id=test_user_id,
        )

        assert result["fixed_costs"] == Decimal("500000.00")


class TestCostServiceSummary:
    """Tests for cost summary statistics."""

    @pytest.mark.asyncio
    async def test_get_cost_summary_empty(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test summary for version with no costs."""
        service = CostService(db_session)

        summary = await service.get_cost_summary(test_budget_version.id)

        assert summary["total_cost"] == Decimal("0")
        assert summary["total_personnel_cost"] == Decimal("0")
        assert summary["total_operating_cost"] == Decimal("0")
        assert summary["personnel_entry_count"] == 0
        assert summary["operating_entry_count"] == 0

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_entries(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test summary with multiple cost entries."""
        service = CostService(db_session)

        # Create personnel costs
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="Teaching Staff",
            fte_count=Decimal("20"),
            unit_cost_sar=Decimal("200000.00"),
            user_id=test_user_id,
        )
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64120",
            description="Admin Staff",
            fte_count=Decimal("5"),
            unit_cost_sar=Decimal("150000.00"),
            user_id=test_user_id,
        )

        # Create operating costs
        await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="60610",
            description="Supplies",
            category="supplies",
            amount_sar=Decimal("300000.00"),
            user_id=test_user_id,
        )
        await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="61520",
            description="Maintenance",
            category="maintenance",
            amount_sar=Decimal("200000.00"),
            user_id=test_user_id,
        )

        summary = await service.get_cost_summary(test_budget_version.id)

        # Personnel: (20 × 200000) + (5 × 150000) = 4,750,000
        expected_personnel = Decimal("4750000.00")
        # Operating: 300000 + 200000 = 500,000
        expected_operating = Decimal("500000.00")

        assert summary["total_personnel_cost"] == expected_personnel
        assert summary["total_operating_cost"] == expected_operating
        assert summary["total_cost"] == expected_personnel + expected_operating
        assert summary["personnel_entry_count"] == 2
        assert summary["operating_entry_count"] == 2


class TestCostServiceRealEFIRData:
    """Tests using realistic EFIR school cost data."""

    @pytest.mark.asyncio
    async def test_realistic_personnel_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        test_user_id: uuid.UUID,
    ):
        """Test with realistic EFIR personnel cost structure."""
        service = CostService(db_session)

        # AEFE Detached Teachers (PRRD in EUR)
        # ~10 teachers × 41,863 EUR × 4.05 SAR/EUR = ~1,695,000 SAR
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="AEFE Detached Teachers (PRRD)",
            fte_count=Decimal("10"),
            unit_cost_sar=Decimal("169547.15"),  # 41863 × 4.05
            category_id=teacher_categories["AEFE_DETACHED"].id,
            is_calculated=True,
            calculation_driver="dhg_allocation",
            user_id=test_user_id,
        )

        # Local Secondary Teachers
        # ~15 teachers × 180,000 SAR = 2,700,000 SAR
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64111",
            description="Local Teachers - Secondary",
            fte_count=Decimal("15"),
            unit_cost_sar=Decimal("180000.00"),
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            is_calculated=True,
            calculation_driver="dhg_allocation",
            user_id=test_user_id,
        )

        # Local Primary Teachers
        # ~20 teachers × 160,000 SAR = 3,200,000 SAR
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64112",
            description="Local Teachers - Primary",
            fte_count=Decimal("20"),
            unit_cost_sar=Decimal("160000.00"),
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["elementaire"].id,
            is_calculated=True,
            calculation_driver="dhg_allocation",
            user_id=test_user_id,
        )

        summary = await service.get_cost_summary(test_budget_version.id)

        # Total: ~7.6M SAR
        assert summary["total_personnel_cost"] > Decimal("7000000")
        assert summary["personnel_entry_count"] == 3

    @pytest.mark.asyncio
    async def test_realistic_operating_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test with realistic EFIR operating cost structure."""
        service = CostService(db_session)

        operating_costs = [
            ("60610", "Student Supplies and Materials", "supplies", Decimal("500000")),
            ("61520", "Building Maintenance", "maintenance", Decimal("400000")),
            ("60620", "Utilities (Electricity, Water)", "utilities", Decimal("600000")),
            ("62600", "Insurance Premiums", "insurance", Decimal("300000")),
            ("61600", "Cleaning Services", "services", Decimal("250000")),
            ("63100", "Professional Services", "services", Decimal("200000")),
            ("66100", "Bank Charges and Fees", "financial", Decimal("50000")),
        ]

        for account, desc, category, amount in operating_costs:
            await service.create_operating_cost_entry(
                version_id=test_budget_version.id,
                account_code=account,
                description=desc,
                category=category,
                amount_sar=amount,
                user_id=test_user_id,
            )

        summary = await service.get_cost_summary(test_budget_version.id)

        # Total: 2.3M SAR
        assert summary["total_operating_cost"] == Decimal("2300000")
        assert summary["operating_entry_count"] == 7
