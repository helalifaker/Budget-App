"""
Tests for CapExService.

Tests cover:
- CapEx plan retrieval
- Creating CapEx entries
- Updating CapEx entries
- Deleting CapEx entries
- Depreciation calculations
- Validation rules
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from app.models.configuration import BudgetVersion
from app.models.planning import CapExPlan
from app.services.capex_service import CapExService
from app.services.exceptions import NotFoundError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class TestGetCapExPlan:
    """Tests for retrieving CapEx plans."""

    @pytest.mark.asyncio
    async def test_get_capex_plan_empty(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
    ):
        """Test retrieving empty CapEx plan."""
        service = CapExService(db_session)
        result = await service.get_capex_plan(test_budget_version.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_capex_plan_with_entries(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test retrieving CapEx plan with entries."""
        # Create CapEx entries
        entry1 = CapExPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="21500",
            description="Classroom Computers",
            category="IT",
            quantity=50,
            unit_cost_sar=Decimal("5000.00"),
            total_cost_sar=Decimal("250000.00"),
            acquisition_date=date(2025, 3, 1),
            useful_life_years=5,
            created_by_id=test_user_id,
        )
        entry2 = CapExPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="21800",
            description="Science Lab Equipment",
            category="equipment",
            quantity=10,
            unit_cost_sar=Decimal("20000.00"),
            total_cost_sar=Decimal("200000.00"),
            acquisition_date=date(2025, 6, 1),
            useful_life_years=10,
            created_by_id=test_user_id,
        )
        db_session.add_all([entry1, entry2])
        await db_session.flush()

        service = CapExService(db_session)
        result = await service.get_capex_plan(test_budget_version.id)

        assert len(result) == 2


class TestGetCapExById:
    """Tests for retrieving CapEx by ID."""

    @pytest.mark.asyncio
    async def test_get_capex_by_id_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test retrieving CapEx entry by ID."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="21500",
            description="Projectors",
            category="IT",
            quantity=20,
            unit_cost_sar=Decimal("3000.00"),
            total_cost_sar=Decimal("60000.00"),
            acquisition_date=date(2025, 4, 1),
            useful_life_years=7,
            created_by_id=test_user_id,
        )
        db_session.add(entry)
        await db_session.flush()

        service = CapExService(db_session)
        result = await service.get_capex_by_id(entry.id)

        assert result.id == entry.id
        assert result.description == "Projectors"

    @pytest.mark.asyncio
    async def test_get_capex_by_id_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving non-existent CapEx entry."""
        service = CapExService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_capex_by_id(uuid.uuid4())


class TestCreateCapExEntry:
    """Tests for creating CapEx entries."""

    @pytest.mark.asyncio
    async def test_create_capex_entry_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test successful CapEx entry creation."""
        service = CapExService(db_session)
        result = await service.create_capex_entry(
            version_id=test_budget_version.id,
            account_code="21500",
            description="Interactive Whiteboards",
            category="IT",
            quantity=15,
            unit_cost_sar=Decimal("8000.00"),
            acquisition_date=date(2025, 5, 1),
            useful_life_years=8,
            notes="For new classrooms",
            user_id=test_user_id,
        )

        assert result is not None
        assert result.description == "Interactive Whiteboards"
        assert result.total_cost_sar == Decimal("120000.00")  # 15 * 8000

    @pytest.mark.asyncio
    async def test_create_capex_entry_invalid_account_code(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx creation with invalid account code."""
        service = CapExService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_capex_entry(
                version_id=test_budget_version.id,
                account_code="64110",  # Invalid - not 20xxx or 21xxx
                description="Test",
                category="IT",
                quantity=1,
                unit_cost_sar=Decimal("1000.00"),
                acquisition_date=date(2025, 1, 1),
                useful_life_years=5,
                user_id=test_user_id,
            )

        assert "20 or 21" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_capex_entry_invalid_quantity(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx creation with invalid quantity."""
        service = CapExService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_capex_entry(
                version_id=test_budget_version.id,
                account_code="21500",
                description="Test",
                category="IT",
                quantity=0,  # Invalid - must be at least 1
                unit_cost_sar=Decimal("1000.00"),
                acquisition_date=date(2025, 1, 1),
                useful_life_years=5,
                user_id=test_user_id,
            )

        assert "at least 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_capex_entry_invalid_useful_life(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx creation with invalid useful life."""
        service = CapExService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_capex_entry(
                version_id=test_budget_version.id,
                account_code="21500",
                description="Test",
                category="IT",
                quantity=1,
                unit_cost_sar=Decimal("1000.00"),
                acquisition_date=date(2025, 1, 1),
                useful_life_years=100,  # Invalid - max is 50
                user_id=test_user_id,
            )

        assert "between 1 and 50" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_capex_entry_zero_useful_life(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx creation with zero useful life."""
        service = CapExService(db_session)

        with pytest.raises(ValidationError):
            await service.create_capex_entry(
                version_id=test_budget_version.id,
                account_code="21500",
                description="Test",
                category="IT",
                quantity=1,
                unit_cost_sar=Decimal("1000.00"),
                acquisition_date=date(2025, 1, 1),
                useful_life_years=0,
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_create_capex_entry_calculates_total(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that total cost is calculated correctly."""
        service = CapExService(db_session)
        result = await service.create_capex_entry(
            version_id=test_budget_version.id,
            account_code="20100",
            description="Building Renovation",
            category="building",
            quantity=1,
            unit_cost_sar=Decimal("500000.00"),
            acquisition_date=date(2025, 7, 1),
            useful_life_years=20,
            user_id=test_user_id,
        )

        assert result.total_cost_sar == Decimal("500000.00")

    @pytest.mark.asyncio
    async def test_create_capex_different_categories(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating CapEx entries with different categories."""
        service = CapExService(db_session)

        categories = ["equipment", "IT", "furniture", "building", "software"]

        for i, category in enumerate(categories):
            result = await service.create_capex_entry(
                version_id=test_budget_version.id,
                account_code=f"215{i:02d}",
                description=f"Test {category}",
                category=category,
                quantity=1,
                unit_cost_sar=Decimal("10000.00"),
                acquisition_date=date(2025, 1, 1),
                useful_life_years=5,
                user_id=test_user_id,
            )

            assert result.category == category


class TestUpdateCapExEntry:
    """Tests for updating CapEx entries."""

    @pytest.mark.asyncio
    async def test_update_capex_entry_description(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx entry description."""
        # Create entry
        entry = CapExPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="21500",
            description="Old Description",
            category="IT",
            quantity=10,
            unit_cost_sar=Decimal("1000.00"),
            total_cost_sar=Decimal("10000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            created_by_id=test_user_id,
        )
        db_session.add(entry)
        await db_session.flush()

        service = CapExService(db_session)
        result = await service.update_capex_entry(
            capex_id=entry.id,
            description="New Description",
        )

        assert result.description == "New Description"

    @pytest.mark.asyncio
    async def test_update_capex_entry_quantity_recalculates_total(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that updating quantity recalculates total cost."""
        # Create entry
        entry = CapExPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="21500",
            description="Laptops",
            category="IT",
            quantity=10,
            unit_cost_sar=Decimal("5000.00"),
            total_cost_sar=Decimal("50000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            created_by_id=test_user_id,
        )
        db_session.add(entry)
        await db_session.flush()

        service = CapExService(db_session)
        result = await service.update_capex_entry(
            capex_id=entry.id,
            quantity=20,
        )

        assert result.quantity == 20
        assert result.total_cost_sar == Decimal("100000.00")


class TestDeleteCapExEntry:
    """Tests for deleting CapEx entries."""

    @pytest.mark.asyncio
    async def test_delete_capex_entry_success(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test successful CapEx entry deletion."""
        # Create entry
        entry = CapExPlan(
            id=uuid.uuid4(),
            budget_version_id=test_budget_version.id,
            account_code="21500",
            description="To Delete",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("1000.00"),
            total_cost_sar=Decimal("1000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            created_by_id=test_user_id,
        )
        db_session.add(entry)
        await db_session.flush()

        service = CapExService(db_session)
        await service.delete_capex_entry(entry.id)

        # Verify deleted (soft delete)
        result = await service.get_capex_plan(test_budget_version.id)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_delete_capex_entry_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test deleting non-existent CapEx entry."""
        service = CapExService(db_session)

        with pytest.raises(NotFoundError):
            await service.delete_capex_entry(uuid.uuid4())


class TestCapExCalculations:
    """Tests for CapEx calculations."""

    @pytest.mark.asyncio
    async def test_total_cost_calculation(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test total cost calculation for multiple entries."""
        service = CapExService(db_session)

        # Create multiple entries
        await service.create_capex_entry(
            version_id=test_budget_version.id,
            account_code="21500",
            description="Item 1",
            category="IT",
            quantity=10,
            unit_cost_sar=Decimal("1000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )
        await service.create_capex_entry(
            version_id=test_budget_version.id,
            account_code="21600",
            description="Item 2",
            category="equipment",
            quantity=5,
            unit_cost_sar=Decimal("2000.00"),
            acquisition_date=date(2025, 2, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        result = await service.get_capex_plan(test_budget_version.id)

        total = sum(item.total_cost_sar for item in result)
        assert total == Decimal("20000.00")  # (10*1000) + (5*2000)

    @pytest.mark.asyncio
    async def test_depreciation_eligible_entries(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test entries are eligible for depreciation."""
        service = CapExService(db_session)

        result = await service.create_capex_entry(
            version_id=test_budget_version.id,
            account_code="21500",
            description="Depreciable Asset",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("100000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        # Asset should have useful life for depreciation
        assert result.useful_life_years == 10
        # Annual depreciation would be 100000/10 = 10000
        expected_annual_depreciation = result.total_cost_sar / result.useful_life_years
        assert expected_annual_depreciation == Decimal("10000.00")
