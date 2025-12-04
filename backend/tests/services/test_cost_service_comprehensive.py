"""
Comprehensive tests for CostService to achieve 95% coverage.

Tests cover:
- Personnel cost calculations from DHG allocations (AEFE + Local)
- Operating cost calculations (enrollment-driven, facility-driven, fixed)
- Account code validation (64xxx for personnel, 60-68xxx for operating)
- Cost summary and aggregation
- CRUD operations for personnel and operating costs
- Edge cases and error handling
- Real EFIR data scenarios
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import (
    AcademicCycle,
    BudgetVersion,
    TeacherCategory,
    TeacherCostParam,
)
from app.models.planning import (
    EnrollmentPlan,
    TeacherAllocation,
)
from app.services.cost_service import CostService
from app.services.exceptions import ServiceException, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


# ==============================================================================
# Personnel Cost CRUD Tests
# ==============================================================================


class TestPersonnelCostCRUD:
    """Comprehensive tests for personnel cost CRUD operations."""

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
    async def test_create_personnel_cost_entry_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        test_user_id: uuid.UUID,
    ):
        """Test creating a personnel cost entry successfully."""
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
        assert result.is_calculated is False

    @pytest.mark.asyncio
    async def test_create_personnel_cost_invalid_account_code(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating personnel cost with invalid account code fails."""
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
        assert exc_info.value.details.get("field") == "account_code"

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
        assert result.description == "Admin Staff"

    @pytest.mark.asyncio
    async def test_get_personnel_cost_by_account_with_category(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        test_user_id: uuid.UUID,
    ):
        """Test retrieving personnel cost filtered by category."""
        service = CostService(db_session)

        # Create entry with category
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="AEFE Teachers",
            fte_count=Decimal("8"),
            unit_cost_sar=Decimal("169547.15"),
            category_id=teacher_categories["AEFE_DETACHED"].id,
            user_id=test_user_id,
        )

        result = await service.get_personnel_cost_by_account(
            version_id=test_budget_version.id,
            account_code="64110",
            category_id=teacher_categories["AEFE_DETACHED"].id,
        )

        assert result is not None
        assert result.category_id == teacher_categories["AEFE_DETACHED"].id

    @pytest.mark.asyncio
    async def test_update_personnel_cost_entry(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating an existing personnel cost entry."""
        service = CostService(db_session)

        # Create entry
        entry1 = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64130",
            description="Support Staff",
            fte_count=Decimal("3"),
            unit_cost_sar=Decimal("80000.00"),
            user_id=test_user_id,
        )

        # Update (upsert with same account)
        entry2 = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64130",
            description="Support Staff - Updated",
            fte_count=Decimal("4"),
            unit_cost_sar=Decimal("85000.00"),
            user_id=test_user_id,
        )

        assert entry1.id == entry2.id
        assert entry2.fte_count == Decimal("4")
        assert entry2.total_cost_sar == Decimal("340000.00")

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
            account_code="64140",
            description="Temporary Staff",
            fte_count=Decimal("2"),
            unit_cost_sar=Decimal("60000.00"),
            user_id=test_user_id,
        )

        # Delete
        result = await service.delete_personnel_cost_entry(entry.id)
        assert result is True

        # Verify it's deleted (soft delete)
        costs = await service.get_personnel_costs(test_budget_version.id)
        assert len([c for c in costs if c.id == entry.id]) == 0

    @pytest.mark.asyncio
    async def test_personnel_cost_with_calculation_driver(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating personnel cost with calculation driver."""
        service = CostService(db_session)

        result = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="DHG Teachers",
            fte_count=Decimal("15"),
            unit_cost_sar=Decimal("180000.00"),
            is_calculated=True,
            calculation_driver="dhg_allocation",
            notes="Calculated from DHG",
            user_id=test_user_id,
        )

        assert result.is_calculated is True
        assert result.calculation_driver == "dhg_allocation"

    @pytest.mark.asyncio
    async def test_personnel_cost_zero_fte(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating personnel cost with zero FTE."""
        service = CostService(db_session)

        result = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="Vacant Position",
            fte_count=Decimal("0"),
            unit_cost_sar=Decimal("180000.00"),
            user_id=test_user_id,
        )

        assert result.fte_count == Decimal("0")
        assert result.total_cost_sar == Decimal("0")


# ==============================================================================
# Operating Cost CRUD Tests
# ==============================================================================


class TestOperatingCostCRUD:
    """Comprehensive tests for operating cost CRUD operations."""

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
    async def test_create_operating_cost_entry_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating an operating cost entry successfully."""
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
        assert result.category == "supplies"

    @pytest.mark.asyncio
    async def test_create_operating_cost_invalid_account_code(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating operating cost with invalid account code fails."""
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
        """Test that all valid operating account code prefixes are accepted."""
        service = CostService(db_session)

        valid_codes = [
            ("60610", "Supplies"),  # 60xxx - Purchases
            ("61520", "Maintenance"),  # 61xxx - External services
            ("62600", "Insurance"),  # 62xxx - Other external services
            ("63100", "Professional Fees"),  # 63xxx - Taxes and fees
            ("65100", "Other Operating"),  # 65xxx - Other management costs
            ("66100", "Financial Charges"),  # 66xxx - Financial costs
            ("68100", "Depreciation"),  # 68xxx - Provisions
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
    async def test_get_operating_cost_by_account(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test retrieving operating cost by account code."""
        service = CostService(db_session)

        # Create entry
        await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="61600",
            description="Cleaning Services",
            category="services",
            amount_sar=Decimal("250000.00"),
            user_id=test_user_id,
        )

        result = await service.get_operating_cost_by_account(
            test_budget_version.id,
            "61600",
        )

        assert result is not None
        assert result.account_code == "61600"
        assert result.description == "Cleaning Services"

    @pytest.mark.asyncio
    async def test_update_operating_cost_entry(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating an existing operating cost entry."""
        service = CostService(db_session)

        # Create entry
        entry1 = await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="60700",
            description="Office Supplies",
            category="supplies",
            amount_sar=Decimal("50000.00"),
            user_id=test_user_id,
        )

        # Update (upsert with same account)
        entry2 = await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="60700",
            description="Office Supplies - Updated",
            category="supplies",
            amount_sar=Decimal("55000.00"),
            user_id=test_user_id,
        )

        assert entry1.id == entry2.id
        assert entry2.amount_sar == Decimal("55000.00")

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
            account_code="60800",
            description="Test Cost",
            category="other",
            amount_sar=Decimal("5000.00"),
            user_id=test_user_id,
        )

        # Delete
        result = await service.delete_operating_cost_entry(entry.id)
        assert result is True

        # Verify deleted
        costs = await service.get_operating_costs(test_budget_version.id)
        assert len([c for c in costs if c.id == entry.id]) == 0

    @pytest.mark.asyncio
    async def test_operating_cost_with_calculation_driver(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating operating cost with calculation driver."""
        service = CostService(db_session)

        result = await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="60610",
            description="Calculated Supplies",
            category="supplies",
            amount_sar=Decimal("300000.00"),
            is_calculated=True,
            calculation_driver="enrollment",
            notes="600 students × 500 SAR/student",
            user_id=test_user_id,
        )

        assert result.is_calculated is True
        assert result.calculation_driver == "enrollment"


# ==============================================================================
# DHG-Based Personnel Cost Calculation Tests
# ==============================================================================


class TestDHGPersonnelCostCalculation:
    """Tests for calculating personnel costs from DHG allocations."""

    @pytest.mark.asyncio
    async def test_calculate_personnel_costs_from_dhg_no_allocations(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test DHG calculation fails when no allocations exist."""
        service = CostService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.calculate_personnel_costs_from_dhg(
                version_id=test_budget_version.id,
                user_id=test_user_id,
            )

        assert "No teacher allocations found" in str(exc_info.value)
        assert exc_info.value.details.get("field") == "allocations"

    @pytest.mark.asyncio
    async def test_calculate_personnel_costs_from_dhg_no_cost_params(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        subjects: dict,
        test_user_id: uuid.UUID,
    ):
        """Test DHG calculation fails when no cost parameters exist."""
        service = CostService(db_session)

        # Create allocation without cost parameters
        allocation = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            subject_id=subjects["MATH"].id,
            fte_count=Decimal("5.0"),
            created_by_id=test_user_id,
        )
        db_session.add(allocation)
        await db_session.flush()

        with pytest.raises(ValidationError) as exc_info:
            await service.calculate_personnel_costs_from_dhg(
                version_id=test_budget_version.id,
                user_id=test_user_id,
            )

        assert "No teacher cost parameters found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_personnel_costs_from_dhg_success_aefe(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        subjects: dict,
        test_user_id: uuid.UUID,
    ):
        """Test successful DHG cost calculation for AEFE teachers."""
        service = CostService(db_session)

        # Create cost parameters for AEFE
        cost_param = TeacherCostParam(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=None,  # Default for all cycles
            prrd_contribution_eur=Decimal("41863"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("0"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            created_by_id=test_user_id,
        )
        db_session.add(cost_param)

        # Create allocation for AEFE teacher
        allocation = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=academic_cycles["college"].id,
            subject_id=subjects["MATH"].id,
            fte_count=Decimal("5.0"),
            created_by_id=test_user_id,
        )
        db_session.add(allocation)
        await db_session.flush()

        # Calculate costs with default EUR to SAR rate (4.05)
        result = await service.calculate_personnel_costs_from_dhg(
            version_id=test_budget_version.id,
            eur_to_sar_rate=Decimal("4.05"),
            user_id=test_user_id,
        )

        # Expected: 5 FTE × (41863 EUR × 4.05 SAR/EUR) = 5 × 169,545.15 = 847,725.75
        expected_cost = Decimal("5.0") * (Decimal("41863") * Decimal("4.05"))

        assert result["total_fte"] == Decimal("5.0")
        assert result["total_cost"] == expected_cost
        assert len(result["created_entries"]) == 1
        # Check if any AEFE-related category exists
        category_names = list(result["cost_by_category"].keys())
        assert any("AEFE" in cat for cat in category_names)

    @pytest.mark.asyncio
    async def test_calculate_personnel_costs_from_dhg_success_local(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        subjects: dict,
        test_user_id: uuid.UUID,
    ):
        """Test successful DHG cost calculation for local teachers."""
        service = CostService(db_session)

        # Create cost parameters for local teachers
        cost_param = TeacherCostParam(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("20000"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            created_by_id=test_user_id,
        )
        db_session.add(cost_param)

        # Create allocation for local teacher
        allocation = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            subject_id=subjects["FRENCH"].id,
            fte_count=Decimal("8.0"),
            created_by_id=test_user_id,
        )
        db_session.add(allocation)
        await db_session.flush()

        # Calculate costs
        result = await service.calculate_personnel_costs_from_dhg(
            version_id=test_budget_version.id,
            user_id=test_user_id,
        )

        # Expected: salary + (salary × 0.21) + benefits
        # = 180000 + 37800 + 20000 = 237,800 per teacher
        # × 8 FTE = 1,902,400
        base = Decimal("180000")
        social_charges = base * Decimal("0.21")
        benefits = Decimal("20000")
        unit_cost = base + social_charges + benefits
        expected_cost = Decimal("8.0") * unit_cost

        assert result["total_fte"] == Decimal("8.0")
        assert result["total_cost"] == expected_cost
        assert len(result["created_entries"]) == 1
        # Check if any Local-related category exists
        category_names = list(result["cost_by_category"].keys())
        assert any("Local" in cat for cat in category_names)

    @pytest.mark.asyncio
    async def test_calculate_personnel_costs_from_dhg_combined_categories(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        subjects: dict,
        test_user_id: uuid.UUID,
    ):
        """Test DHG calculation with multiple categories and cycles."""
        service = CostService(db_session)

        # Cost params for AEFE
        cost_param_aefe = TeacherCostParam(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41863"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("0"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            created_by_id=test_user_id,
        )
        db_session.add(cost_param_aefe)

        # Cost params for Local (Collège)
        cost_param_local_college = TeacherCostParam(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("20000"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            created_by_id=test_user_id,
        )
        db_session.add(cost_param_local_college)

        # Cost params for Local (Élémentaire)
        cost_param_local_elementaire = TeacherCostParam(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["elementaire"].id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("160000"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("15000"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            created_by_id=test_user_id,
        )
        db_session.add(cost_param_local_elementaire)

        # Allocations
        alloc_aefe = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=academic_cycles["college"].id,
            subject_id=subjects["MATH"].id,
            fte_count=Decimal("3.0"),
            created_by_id=test_user_id,
        )
        db_session.add(alloc_aefe)

        alloc_local_college = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            subject_id=subjects["FRENCH"].id,
            fte_count=Decimal("5.0"),
            created_by_id=test_user_id,
        )
        db_session.add(alloc_local_college)

        alloc_local_elementaire = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["elementaire"].id,
            subject_id=subjects["MATH"].id,
            fte_count=Decimal("7.0"),
            created_by_id=test_user_id,
        )
        db_session.add(alloc_local_elementaire)

        await db_session.flush()

        # Calculate costs
        result = await service.calculate_personnel_costs_from_dhg(
            version_id=test_budget_version.id,
            eur_to_sar_rate=Decimal("4.05"),
            user_id=test_user_id,
        )

        # Verify total FTE
        assert result["total_fte"] == Decimal("15.0")  # 3 + 5 + 7

        # Should have 3 cost entries (one per category+cycle combination)
        assert len(result["created_entries"]) == 3

        # Verify breakdown by category
        assert len(result["cost_by_category"]) >= 2

        # Verify breakdown by cycle
        assert len(result["cost_by_cycle"]) >= 2

    @pytest.mark.asyncio
    async def test_calculate_personnel_costs_from_dhg_fallback_to_default(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        subjects: dict,
        test_user_id: uuid.UUID,
    ):
        """Test DHG calculation falls back to default cost params when cycle-specific not found."""
        service = CostService(db_session)

        # Create cost parameters with cycle_id=None (default)
        cost_param = TeacherCostParam(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=None,  # Default for all cycles
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("170000"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("18000"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            created_by_id=test_user_id,
        )
        db_session.add(cost_param)

        # Create allocation for a specific cycle (Lycée)
        allocation = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["lycee"].id,  # No specific param for lycee
            subject_id=subjects["MATH"].id,
            fte_count=Decimal("4.0"),
            created_by_id=test_user_id,
        )
        db_session.add(allocation)
        await db_session.flush()

        # Should use default cost params
        result = await service.calculate_personnel_costs_from_dhg(
            version_id=test_budget_version.id,
            user_id=test_user_id,
        )

        assert result["total_fte"] == Decimal("4.0")
        assert len(result["created_entries"]) == 1

    @pytest.mark.asyncio
    async def test_calculate_personnel_costs_from_dhg_skip_missing_param(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        subjects: dict,
        test_user_id: uuid.UUID,
    ):
        """Test DHG calculation skips allocations with no matching cost params."""
        service = CostService(db_session)

        # Create cost parameters for LOCAL only
        cost_param = TeacherCostParam(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=None,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("20000"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            created_by_id=test_user_id,
        )
        db_session.add(cost_param)

        # Create allocations for both LOCAL and AEFE
        alloc_local = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            subject_id=subjects["MATH"].id,
            fte_count=Decimal("5.0"),
            created_by_id=test_user_id,
        )
        db_session.add(alloc_local)

        alloc_aefe = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=academic_cycles["college"].id,
            subject_id=subjects["FRENCH"].id,
            fte_count=Decimal("3.0"),  # This will be skipped
            created_by_id=test_user_id,
        )
        db_session.add(alloc_aefe)

        await db_session.flush()

        # Calculate - should only process LOCAL
        result = await service.calculate_personnel_costs_from_dhg(
            version_id=test_budget_version.id,
            user_id=test_user_id,
        )

        # Only LOCAL allocation should be processed
        assert result["total_fte"] == Decimal("5.0")
        assert len(result["created_entries"]) == 1

    @pytest.mark.asyncio
    async def test_calculate_personnel_costs_from_dhg_zero_prrd(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        subjects: dict,
        test_user_id: uuid.UUID,
    ):
        """Test DHG calculation with null PRRD contribution."""
        service = CostService(db_session)

        # AEFE_FUNDED has no PRRD cost
        cost_param = TeacherCostParam(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_FUNDED"].id,
            cycle_id=None,
            prrd_contribution_eur=None,  # Fully funded by AEFE
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("0"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            created_by_id=test_user_id,
        )
        db_session.add(cost_param)

        allocation = TeacherAllocation(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_FUNDED"].id,
            cycle_id=academic_cycles["college"].id,
            subject_id=subjects["MATH"].id,
            fte_count=Decimal("2.0"),
            created_by_id=test_user_id,
        )
        db_session.add(allocation)
        await db_session.flush()

        result = await service.calculate_personnel_costs_from_dhg(
            version_id=test_budget_version.id,
            user_id=test_user_id,
        )

        # Zero cost for AEFE_FUNDED
        assert result["total_cost"] == Decimal("0")
        assert result["total_fte"] == Decimal("2.0")


# ==============================================================================
# Driver-Based Operating Cost Calculation Tests
# ==============================================================================


class TestDriverBasedOperatingCostCalculation:
    """Tests for driver-based operating cost calculations."""

    @pytest.mark.asyncio
    async def test_calculate_operating_costs_no_enrollment(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test operating cost calculation fails without enrollment data."""
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

        assert "No enrollment data found" in str(exc_info.value)
        assert exc_info.value.details.get("field") == "enrollment"

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
        expected_supplies_cost = 130 * Decimal("500.00")  # 65,000

        assert result["enrollment_count"] == 130
        assert result["enrollment_driven_costs"] == expected_supplies_cost
        assert len(result["created_entries"]) >= 1
        assert result["created_entries"][0].account_code == "60610"

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

        expected_maintenance = Decimal("5000") * Decimal("50.00")  # 250,000

        assert result["facility_driven_costs"] == expected_maintenance
        assert any(
            e.account_code == "61520" for e in result["created_entries"]
        )

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
        assert any(
            e.account_code == "62600" for e in result["created_entries"]
        )

    @pytest.mark.asyncio
    async def test_calculate_operating_costs_combined_drivers(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test operating cost calculation with multiple drivers combined."""
        service = CostService(db_session)

        cost_drivers = {
            "cost_per_student_supplies": Decimal("500.00"),
            "square_meters": Decimal("5000"),
            "cost_per_sqm_maintenance": Decimal("50.00"),
            "insurance_annual": Decimal("500000.00"),
        }

        result = await service.calculate_operating_costs(
            version_id=test_budget_version.id,
            cost_drivers=cost_drivers,
            user_id=test_user_id,
        )

        # 130 students × 500 = 65,000
        # 5000 sqm × 50 = 250,000
        # Insurance = 500,000
        # Total = 815,000
        expected_total = Decimal("815000.00")

        assert result["total_cost"] == expected_total
        assert len(result["created_entries"]) == 3


# ==============================================================================
# Cost Summary Tests
# ==============================================================================


class TestCostSummary:
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
    async def test_get_cost_summary_with_personnel_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test summary with personnel costs only."""
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

        summary = await service.get_cost_summary(test_budget_version.id)

        expected_personnel = Decimal("4000000.00")  # 20 × 200,000

        assert summary["total_personnel_cost"] == expected_personnel
        assert summary["total_operating_cost"] == Decimal("0")
        assert summary["total_cost"] == expected_personnel
        assert summary["personnel_entry_count"] == 1

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_operating_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test summary with operating costs only."""
        service = CostService(db_session)

        # Create operating costs
        await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="60610",
            description="Supplies",
            category="supplies",
            amount_sar=Decimal("300000.00"),
            user_id=test_user_id,
        )

        summary = await service.get_cost_summary(test_budget_version.id)

        assert summary["total_operating_cost"] == Decimal("300000.00")
        assert summary["total_personnel_cost"] == Decimal("0")
        assert summary["total_cost"] == Decimal("300000.00")
        assert summary["operating_entry_count"] == 1

    @pytest.mark.asyncio
    async def test_get_cost_summary_combined(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test summary with both personnel and operating costs."""
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

    @pytest.mark.asyncio
    async def test_get_cost_summary_by_category(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        test_user_id: uuid.UUID,
    ):
        """Test summary aggregates costs by category."""
        service = CostService(db_session)

        # Create costs for different categories
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="AEFE Teachers",
            fte_count=Decimal("10"),
            unit_cost_sar=Decimal("169547.15"),
            category_id=teacher_categories["AEFE_DETACHED"].id,
            user_id=test_user_id,
        )
        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64111",
            description="Local Teachers",
            fte_count=Decimal("15"),
            unit_cost_sar=Decimal("180000.00"),
            category_id=teacher_categories["LOCAL"].id,
            user_id=test_user_id,
        )

        # Create operating costs for different categories
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

        assert len(summary["personnel_by_category"]) == 2
        assert len(summary["operating_by_category"]) == 2
        assert "supplies" in summary["operating_by_category"]
        assert summary["operating_by_category"]["supplies"] == Decimal("300000.00")


# ==============================================================================
# Real EFIR Data Tests
# ==============================================================================


class TestRealEFIRData:
    """Tests using realistic EFIR school cost data."""

    @pytest.mark.asyncio
    async def test_realistic_aefe_personnel_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        test_user_id: uuid.UUID,
    ):
        """Test AEFE teacher costs with real PRRD data."""
        service = CostService(db_session)

        # AEFE Detached Teachers (PRRD in EUR)
        # PRRD = 41,863 EUR/teacher
        # Exchange rate = 4.05 SAR/EUR (default parameter)
        # Cost per teacher = 41,863 × 4.05 = 169,545.15 SAR
        # For 10 teachers = 1,695,451.50 SAR

        result = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="AEFE Detached Teachers (PRRD Contribution)",
            fte_count=Decimal("10"),
            unit_cost_sar=Decimal("169545.15"),  # 41863 × 4.05
            category_id=teacher_categories["AEFE_DETACHED"].id,
            is_calculated=True,
            calculation_driver="dhg_allocation",
            notes="AEFE PRRD: 41,863 EUR × 4.05 SAR/EUR = 169,545.15 SAR/teacher",
            user_id=test_user_id,
        )

        assert result.total_cost_sar == Decimal("1695451.50")

    @pytest.mark.asyncio
    async def test_realistic_local_personnel_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
        test_user_id: uuid.UUID,
    ):
        """Test local teacher costs with real salary data."""
        service = CostService(db_session)

        # Local Secondary Teachers
        # Base salary = 180,000 SAR/year
        # Social charges (21%) = 37,800 SAR
        # Benefits = 20,000 SAR
        # Total = 237,800 SAR/teacher
        # For 15 teachers = 3,567,000 SAR

        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64111",
            description="Local Teachers - Secondary (Collège)",
            fte_count=Decimal("15"),
            unit_cost_sar=Decimal("237800.00"),
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            is_calculated=True,
            calculation_driver="dhg_allocation",
            notes="Base: 180K + Social charges (21%): 37.8K + Benefits: 20K = 237.8K SAR",
            user_id=test_user_id,
        )

        # Local Primary Teachers
        # Base salary = 160,000 SAR/year
        # Social charges (21%) = 33,600 SAR
        # Benefits = 15,000 SAR
        # Total = 208,600 SAR/teacher
        # For 20 teachers = 4,172,000 SAR

        await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64112",
            description="Local Teachers - Primary (Élémentaire)",
            fte_count=Decimal("20"),
            unit_cost_sar=Decimal("208600.00"),
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["elementaire"].id,
            is_calculated=True,
            calculation_driver="dhg_allocation",
            notes="Base: 160K + Social charges (21%): 33.6K + Benefits: 15K = 208.6K SAR",
            user_id=test_user_id,
        )

        summary = await service.get_cost_summary(test_budget_version.id)

        # Total: 3,567,000 + 4,172,000 = 7,739,000 SAR
        assert summary["total_personnel_cost"] == Decimal("7739000.00")
        assert summary["personnel_entry_count"] == 2

    @pytest.mark.asyncio
    async def test_realistic_atsem_costs(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_cycles: dict[str, AcademicCycle],
        test_user_id: uuid.UUID,
    ):
        """Test ATSEM costs for Maternelle."""
        service = CostService(db_session)

        # ATSEM (Classroom assistants for Maternelle)
        # 1 per class
        # Average salary: 60,000 SAR/year
        # 6 classes in Maternelle = 6 ATSEM

        result = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64150",
            description="ATSEM - Maternelle Classroom Assistants",
            fte_count=Decimal("6"),
            unit_cost_sar=Decimal("60000.00"),
            cycle_id=academic_cycles["maternelle"].id,
            is_calculated=True,
            calculation_driver="class_count",
            notes="1 ATSEM per Maternelle class × 6 classes = 6 FTE",
            user_id=test_user_id,
        )

        assert result.total_cost_sar == Decimal("360000.00")

    @pytest.mark.asyncio
    async def test_realistic_operating_costs_comprehensive(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test comprehensive realistic operating cost structure."""
        service = CostService(db_session)

        operating_costs = [
            ("60610", "Student Supplies and Educational Materials", "supplies", Decimal("500000")),
            ("60620", "Textbooks and Library Resources", "supplies", Decimal("300000")),
            ("60810", "Utilities - Electricity", "utilities", Decimal("400000")),
            ("60820", "Utilities - Water", "utilities", Decimal("200000")),
            ("61520", "Building Maintenance and Repairs", "maintenance", Decimal("400000")),
            ("61600", "Cleaning and Janitorial Services", "services", Decimal("250000")),
            ("61800", "Security Services", "services", Decimal("180000")),
            ("62100", "Transportation - School Buses", "transportation", Decimal("350000")),
            ("62600", "Insurance Premiums", "insurance", Decimal("300000")),
            ("63100", "Professional Services and Consulting", "services", Decimal("200000")),
            ("65100", "IT and Software Licenses", "technology", Decimal("150000")),
            ("66100", "Bank Charges and Financial Fees", "financial", Decimal("50000")),
        ]

        for account, desc, category, amount in operating_costs:
            await service.create_operating_cost_entry(
                version_id=test_budget_version.id,
                account_code=account,
                description=desc,
                category=category,
                amount_sar=amount,
                is_calculated=False,
                user_id=test_user_id,
            )

        summary = await service.get_cost_summary(test_budget_version.id)

        # Total: 3,280,000 SAR
        assert summary["total_operating_cost"] == Decimal("3280000")
        assert summary["operating_entry_count"] == 12


# ==============================================================================
# Edge Cases and Error Handling Tests
# ==============================================================================


class TestEdgeCasesAndErrors:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_personnel_cost_decimal_precision(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test personnel cost calculation maintains decimal precision."""
        service = CostService(db_session)

        result = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64110",
            description="Fractional FTE",
            fte_count=Decimal("5.333"),  # Fractional FTE
            unit_cost_sar=Decimal("169545.15"),
            user_id=test_user_id,
        )

        # 5.333 × 169545.15 = 904,173.05 (rounded to 2 decimals)
        expected = Decimal("5.333") * Decimal("169545.15")
        assert result.total_cost_sar == expected.quantize(Decimal("0.01"))

    @pytest.mark.asyncio
    async def test_operating_cost_zero_amount(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating operating cost with zero amount."""
        service = CostService(db_session)

        result = await service.create_operating_cost_entry(
            version_id=test_budget_version.id,
            account_code="60610",
            description="Waived Cost",
            category="supplies",
            amount_sar=Decimal("0"),
            user_id=test_user_id,
        )

        assert result.amount_sar == Decimal("0")

    @pytest.mark.asyncio
    async def test_personnel_cost_with_cycle_no_category(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        academic_cycles: dict[str, AcademicCycle],
        test_user_id: uuid.UUID,
    ):
        """Test creating personnel cost with cycle but no category."""
        service = CostService(db_session)

        result = await service.create_personnel_cost_entry(
            version_id=test_budget_version.id,
            account_code="64200",
            description="General Staff",
            fte_count=Decimal("3"),
            unit_cost_sar=Decimal("100000.00"),
            category_id=None,
            cycle_id=academic_cycles["college"].id,
            user_id=test_user_id,
        )

        assert result.cycle_id == academic_cycles["college"].id
        assert result.category_id is None

    @pytest.mark.asyncio
    async def test_get_personnel_cost_by_account_not_found(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving non-existent personnel cost returns None."""
        service = CostService(db_session)

        result = await service.get_personnel_cost_by_account(
            version_id=test_budget_version.id,
            account_code="64999",  # Non-existent
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_operating_cost_by_account_not_found(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving non-existent operating cost returns None."""
        service = CostService(db_session)

        result = await service.get_operating_cost_by_account(
            version_id=test_budget_version.id,
            account_code="60999",  # Non-existent
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_calculate_operating_costs_empty_drivers(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_enrollment_data: list[EnrollmentPlan],
        test_user_id: uuid.UUID,
    ):
        """Test operating cost calculation with empty drivers dict."""
        service = CostService(db_session)

        cost_drivers = {}  # Empty drivers

        result = await service.calculate_operating_costs(
            version_id=test_budget_version.id,
            cost_drivers=cost_drivers,
            user_id=test_user_id,
        )

        # Should succeed but create no entries
        assert result["total_cost"] == Decimal("0")
        assert len(result["created_entries"]) == 0
