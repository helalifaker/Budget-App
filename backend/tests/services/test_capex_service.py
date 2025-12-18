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
from app.models import CapExPlan, Version
from app.services.exceptions import NotFoundError, ValidationError
from app.services.investments.capex_service import CapExService
from sqlalchemy.ext.asyncio import AsyncSession

# Backward compatibility alias
BudgetVersion = Version


class TestGetCapExPlan:
    """Tests for retrieving CapEx plans."""

    @pytest.mark.asyncio
    async def test_get_capex_plan_empty(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
    ):
        """Test retrieving empty CapEx plan."""
        service = CapExService(db_session)
        result = await service.get_capex_plan(test_version.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_capex_plan_with_entries(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test retrieving CapEx plan with entries."""
        # Create CapEx entries
        entry1 = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
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
            version_id=test_version.id,
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
        result = await service.get_capex_plan(test_version.id)

        assert len(result) == 2


class TestGetCapExById:
    """Tests for retrieving CapEx by ID."""

    @pytest.mark.asyncio
    async def test_get_capex_by_id_success(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test retrieving CapEx entry by ID."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test successful CapEx entry creation."""
        service = CapExService(db_session)
        result = await service.create_capex_entry(
            version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx creation with invalid account code."""
        service = CapExService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_capex_entry(
                version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx creation with invalid quantity."""
        service = CapExService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_capex_entry(
                version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx creation with invalid useful life."""
        service = CapExService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_capex_entry(
                version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx creation with zero useful life."""
        service = CapExService(db_session)

        with pytest.raises(ValidationError):
            await service.create_capex_entry(
                version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that total cost is calculated correctly."""
        service = CapExService(db_session)
        result = await service.create_capex_entry(
            version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test creating CapEx entries with different categories."""
        service = CapExService(db_session)

        categories = ["equipment", "IT", "furniture", "building", "software"]

        for i, category in enumerate(categories):
            result = await service.create_capex_entry(
                version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx entry description."""
        # Create entry
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that updating quantity recalculates total cost."""
        # Create entry
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
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
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test successful CapEx entry deletion."""
        # Create entry
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
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
        result = await service.get_capex_plan(test_version.id)
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


class TestUpdateCapExValidation:
    """Tests for update validation edge cases."""

    @pytest.mark.asyncio
    async def test_update_capex_invalid_account_code(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx with invalid account code."""
        # Create entry
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
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

        with pytest.raises(ValidationError) as exc_info:
            await service.update_capex_entry(
                capex_id=entry.id,
                account_code="64110",  # Invalid - not 20xxx or 21xxx
            )

        assert "20 or 21" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_capex_invalid_quantity(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx with invalid quantity."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
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

        with pytest.raises(ValidationError) as exc_info:
            await service.update_capex_entry(
                capex_id=entry.id,
                quantity=0,  # Invalid
            )

        assert "at least 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_capex_invalid_useful_life(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx with invalid useful life."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
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

        with pytest.raises(ValidationError) as exc_info:
            await service.update_capex_entry(
                capex_id=entry.id,
                useful_life_years=100,  # Invalid - max 50
            )

        assert "between 1 and 50" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_capex_change_category(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx category."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
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
        result = await service.update_capex_entry(
            capex_id=entry.id,
            category="equipment",
        )

        assert result.category == "equipment"

    @pytest.mark.asyncio
    async def test_update_capex_change_acquisition_date(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx acquisition date."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
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
        new_date = date(2025, 6, 1)
        result = await service.update_capex_entry(
            capex_id=entry.id,
            acquisition_date=new_date,
        )

        assert result.acquisition_date == new_date

    @pytest.mark.asyncio
    async def test_update_capex_change_unit_cost(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx unit cost recalculates total."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
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
            unit_cost_sar=Decimal("1500.00"),
        )

        assert result.unit_cost_sar == Decimal("1500.00")
        assert result.total_cost_sar == Decimal("15000.00")  # 10 * 1500

    @pytest.mark.asyncio
    async def test_update_capex_change_notes(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx notes."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("1000.00"),
            total_cost_sar=Decimal("1000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            notes="Old notes",
            created_by_id=test_user_id,
        )
        db_session.add(entry)
        await db_session.flush()

        service = CapExService(db_session)
        result = await service.update_capex_entry(
            capex_id=entry.id,
            notes="New notes",
        )

        assert result.notes == "New notes"

    @pytest.mark.asyncio
    async def test_update_capex_valid_account_code(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx with valid account code (line 185 coverage)."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
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
        result = await service.update_capex_entry(
            capex_id=entry.id,
            account_code="20100",  # Valid - starts with 20
        )

        assert result.account_code == "20100"

    @pytest.mark.asyncio
    async def test_update_capex_valid_useful_life(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test updating CapEx with valid useful life (line 213 coverage)."""
        entry = CapExPlan(
            id=uuid.uuid4(),
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
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
        result = await service.update_capex_entry(
            capex_id=entry.id,
            useful_life_years=10,  # Valid - within 1-50 range
        )

        assert result.useful_life_years == 10


class TestDepreciationCalculation:
    """Tests for depreciation calculations."""

    @pytest.mark.asyncio
    async def test_calculate_depreciation_normal_case(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation calculation for year 2 of 5-year life."""
        # EFIR Scenario: IT Equipment SAR 50,000, 5-year life
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Classroom Computers",
            category="IT",
            quantity=10,
            unit_cost_sar=Decimal("5000.00"),
            acquisition_date=date(2023, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )

        # Calculate depreciation for year 2025 (2 years after acquisition)
        result = await service.calculate_depreciation(capex.id, 2025)

        # Annual depreciation = 50,000 / 5 = 10,000
        assert result["annual_depreciation"] == Decimal("10000.00")
        # Years elapsed = 2
        assert result["years_elapsed"] == 2
        # Accumulated = 10,000 * 2 = 20,000
        assert result["accumulated_depreciation"] == Decimal("20000.00")
        # Book value = 50,000 - 20,000 = 30,000
        assert result["book_value"] == Decimal("30000.00")
        assert result["is_fully_depreciated"] is False

    @pytest.mark.asyncio
    async def test_calculate_depreciation_acquisition_year(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation in acquisition year (year 0)."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21800",
            description="Science Lab Equipment",
            category="equipment",
            quantity=1,
            unit_cost_sar=Decimal("200000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        # Calculate depreciation for acquisition year
        result = await service.calculate_depreciation(capex.id, 2025)

        # Annual depreciation = 200,000 / 10 = 20,000
        assert result["annual_depreciation"] == Decimal("20000.00")
        # Years elapsed = 0
        assert result["years_elapsed"] == 0
        # Accumulated = 20,000 * 0 = 0
        assert result["accumulated_depreciation"] == Decimal("0.00")
        # Book value = 200,000 - 0 = 200,000
        assert result["book_value"] == Decimal("200000.00")
        assert result["is_fully_depreciated"] is False

    @pytest.mark.asyncio
    async def test_calculate_depreciation_fully_depreciated(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation when asset is fully depreciated."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Old IT Equipment",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("50000.00"),
            acquisition_date=date(2020, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )

        # Calculate depreciation after useful life (2020 + 5 = 2025, so 2026 is fully depreciated)
        result = await service.calculate_depreciation(capex.id, 2026)

        # Annual depreciation = 50,000 / 5 = 10,000
        assert result["annual_depreciation"] == Decimal("10000.00")
        # Years elapsed = 6 (beyond useful life)
        assert result["years_elapsed"] == 6
        # Accumulated capped at acquisition cost
        assert result["accumulated_depreciation"] == Decimal("50000.00")
        # Book value = 0
        assert result["book_value"] == Decimal("0.00")
        assert result["is_fully_depreciated"] is True

    @pytest.mark.asyncio
    async def test_calculate_depreciation_single_year_life(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation with 1-year useful life (edge case)."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21900",
            description="Short-lived Software License",
            category="software",
            quantity=1,
            unit_cost_sar=Decimal("10000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=1,
            user_id=test_user_id,
        )

        # Calculate for acquisition year
        result = await service.calculate_depreciation(capex.id, 2025)
        assert result["annual_depreciation"] == Decimal("10000.00")
        assert result["accumulated_depreciation"] == Decimal("0.00")
        assert result["is_fully_depreciated"] is False

        # Calculate for year 1 (fully depreciated)
        result_year1 = await service.calculate_depreciation(capex.id, 2026)
        assert result_year1["accumulated_depreciation"] == Decimal("10000.00")
        assert result_year1["book_value"] == Decimal("0.00")
        assert result_year1["is_fully_depreciated"] is True

    @pytest.mark.asyncio
    async def test_calculate_depreciation_decimal_precision(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation with decimal precision (0.01 SAR)."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset with Odd Numbers",
            category="IT",
            quantity=3,
            unit_cost_sar=Decimal("3333.33"),
            acquisition_date=date(2023, 1, 1),
            useful_life_years=7,
            user_id=test_user_id,
        )

        # Total cost = 3 * 3333.33 = 9999.99
        result = await service.calculate_depreciation(capex.id, 2025)

        # Annual depreciation = 9999.99 / 7 = 1428.57
        assert result["annual_depreciation"] == Decimal("1428.57")
        # Years elapsed = 2
        assert result["years_elapsed"] == 2
        # Accumulated = 1428.57 * 2 = 2857.14
        assert result["accumulated_depreciation"] == Decimal("2857.14")
        # Book value = 9999.99 - 2857.14 = 7142.85
        assert result["book_value"] == Decimal("7142.85")

    @pytest.mark.asyncio
    async def test_calculate_depreciation_large_amounts(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation with large amounts (EFIR building improvements)."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="20100",
            description="Building Improvements",
            category="building",
            quantity=1,
            unit_cost_sar=Decimal("5000000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=20,
            user_id=test_user_id,
        )

        result = await service.calculate_depreciation(capex.id, 2026)

        # Annual depreciation = 5,000,000 / 20 = 250,000
        assert result["annual_depreciation"] == Decimal("250000.00")
        assert result["years_elapsed"] == 1
        assert result["accumulated_depreciation"] == Decimal("250000.00")
        assert result["book_value"] == Decimal("4750000.00")

    @pytest.mark.asyncio
    async def test_calculate_depreciation_before_acquisition(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation calculation fails before acquisition year."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Future Asset",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("10000.00"),
            acquisition_date=date(2026, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )

        with pytest.raises(ValidationError) as exc_info:
            await service.calculate_depreciation(capex.id, 2025)

        assert "before acquisition year" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_depreciation_metadata(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation result includes all metadata."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Test Asset",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("10000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )

        result = await service.calculate_depreciation(capex.id, 2026)

        # Verify all metadata is present
        assert "asset_id" in result
        assert result["asset_description"] == "Test Asset"
        assert result["account_code"] == "21500"
        assert result["category"] == "IT"
        assert result["acquisition_cost"] == Decimal("10000.00")
        assert result["acquisition_date"] == date(2025, 1, 1)
        assert result["useful_life_years"] == 5
        assert result["calculation_year"] == 2026


class TestDepreciationSchedule:
    """Tests for multi-year depreciation schedules."""

    @pytest.mark.asyncio
    async def test_get_depreciation_schedule_full_life(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation schedule for entire useful life."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="IT Equipment",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("50000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )

        schedule = await service.get_depreciation_schedule(capex.id, years_ahead=10)

        # Should have 6 entries (year 0 through year 5)
        assert len(schedule) == 6

        # Verify progression
        for i, entry in enumerate(schedule):
            assert entry["years_elapsed"] == i
            assert entry["calculation_year"] == 2025 + i

        # Last entry should be fully depreciated
        assert schedule[-1]["is_fully_depreciated"] is True
        assert schedule[-1]["book_value"] == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_get_depreciation_schedule_partial_years(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation schedule stops at useful life."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="IT Equipment",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("100000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        # Request 3 years ahead
        schedule = await service.get_depreciation_schedule(capex.id, years_ahead=3)

        # Should have 4 entries (years 0, 1, 2, 3)
        assert len(schedule) == 4

    @pytest.mark.asyncio
    async def test_get_depreciation_schedule_single_year(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation schedule for 1-year asset."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21900",
            description="Short-lived Asset",
            category="software",
            quantity=1,
            unit_cost_sar=Decimal("10000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=1,
            user_id=test_user_id,
        )

        schedule = await service.get_depreciation_schedule(capex.id, years_ahead=5)

        # Should have 2 entries (year 0 and year 1)
        assert len(schedule) == 2

    @pytest.mark.asyncio
    async def test_get_depreciation_schedule_precision(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test depreciation schedule maintains decimal precision."""
        service = CapExService(db_session)
        capex = await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Furniture",
            category="furniture",
            quantity=20,
            unit_cost_sar=Decimal("10000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        # Total cost = 200,000
        schedule = await service.get_depreciation_schedule(capex.id, years_ahead=10)

        # Verify each entry has proper decimal precision
        for entry in schedule:
            assert entry["annual_depreciation"] == Decimal("20000.00")
            # Check decimal places
            assert entry["accumulated_depreciation"].as_tuple().exponent == -2
            assert entry["book_value"].as_tuple().exponent == -2


class TestCapExSummary:
    """Tests for CapEx summary statistics."""

    @pytest.mark.asyncio
    async def test_get_capex_summary_by_category(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx summary grouped by category."""
        service = CapExService(db_session)

        # Create entries in different categories
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Computers",
            category="IT",
            quantity=10,
            unit_cost_sar=Decimal("5000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21510",
            description="Servers",
            category="IT",
            quantity=2,
            unit_cost_sar=Decimal("25000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=7,
            user_id=test_user_id,
        )
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21700",
            description="Desks",
            category="furniture",
            quantity=50,
            unit_cost_sar=Decimal("2000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        summary = await service.get_capex_summary(test_version.id)

        # Total = 50,000 + 50,000 + 100,000 = 200,000
        assert summary["total_capex"] == Decimal("200000.00")
        assert summary["item_count"] == 3

        # Check category breakdown
        assert "IT" in summary["capex_by_category"]
        assert summary["capex_by_category"]["IT"]["total_cost"] == Decimal("100000.00")
        assert summary["capex_by_category"]["IT"]["item_count"] == 2

        assert "furniture" in summary["capex_by_category"]
        assert summary["capex_by_category"]["furniture"]["total_cost"] == Decimal("100000.00")
        assert summary["capex_by_category"]["furniture"]["item_count"] == 1

    @pytest.mark.asyncio
    async def test_get_capex_summary_by_account(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx summary grouped by account code."""
        service = CapExService(db_session)

        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Item 1",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("10000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Item 2",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("15000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21600",
            description="Item 3",
            category="equipment",
            quantity=1,
            unit_cost_sar=Decimal("20000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        summary = await service.get_capex_summary(test_version.id)

        # Check account breakdown
        assert "21500" in summary["capex_by_account"]
        assert summary["capex_by_account"]["21500"] == Decimal("25000.00")

        assert "21600" in summary["capex_by_account"]
        assert summary["capex_by_account"]["21600"] == Decimal("20000.00")

    @pytest.mark.asyncio
    async def test_get_capex_summary_empty(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
    ):
        """Test CapEx summary with no entries."""
        service = CapExService(db_session)
        summary = await service.get_capex_summary(test_version.id)

        assert summary["total_capex"] == Decimal("0")
        assert summary["item_count"] == 0
        assert summary["capex_by_category"] == {}
        assert summary["capex_by_account"] == {}

    @pytest.mark.asyncio
    async def test_get_capex_summary_totals(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test CapEx summary total calculations."""
        service = CapExService(db_session)

        # EFIR realistic scenario
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Classroom Computers",
            category="IT",
            quantity=50,
            unit_cost_sar=Decimal("5000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21800",
            description="Science Lab Equipment",
            category="equipment",
            quantity=1,
            unit_cost_sar=Decimal("200000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="20100",
            description="Building Improvements",
            category="building",
            quantity=1,
            unit_cost_sar=Decimal("5000000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=20,
            user_id=test_user_id,
        )

        summary = await service.get_capex_summary(test_version.id)

        # Total = 250,000 + 200,000 + 5,000,000 = 5,450,000
        assert summary["total_capex"] == Decimal("5450000.00")
        assert summary["item_count"] == 3


class TestAnnualDepreciation:
    """Tests for annual depreciation totals."""

    @pytest.mark.asyncio
    async def test_get_annual_depreciation_single_asset(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test annual depreciation for single asset."""
        service = CapExService(db_session)
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="IT Equipment",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("100000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        result = await service.get_annual_depreciation(test_version.id, 2026)

        # Annual depreciation = 100,000 / 10 = 10,000
        assert result["calculation_year"] == 2026
        assert result["total_annual_depreciation"] == Decimal("10000.00")
        assert "IT" in result["depreciation_by_category"]
        assert result["depreciation_by_category"]["IT"] == Decimal("10000.00")

    @pytest.mark.asyncio
    async def test_get_annual_depreciation_multiple_assets(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test annual depreciation aggregation across assets."""
        service = CapExService(db_session)

        # Asset 1: 50,000 SAR, 5-year life = 10,000/year
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="Computers",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("50000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )

        # Asset 2: 200,000 SAR, 10-year life = 20,000/year
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21700",
            description="Furniture",
            category="furniture",
            quantity=1,
            unit_cost_sar=Decimal("200000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        result = await service.get_annual_depreciation(test_version.id, 2026)

        # Total = 10,000 + 20,000 = 30,000
        assert result["total_annual_depreciation"] == Decimal("30000.00")

    @pytest.mark.asyncio
    async def test_get_annual_depreciation_by_category(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test annual depreciation grouped by category."""
        service = CapExService(db_session)

        # IT: 50,000 / 5 = 10,000
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="IT Asset 1",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("50000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )

        # IT: 30,000 / 3 = 10,000
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21510",
            description="IT Asset 2",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("30000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=3,
            user_id=test_user_id,
        )

        # Furniture: 100,000 / 10 = 10,000
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21700",
            description="Furniture",
            category="furniture",
            quantity=1,
            unit_cost_sar=Decimal("100000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        result = await service.get_annual_depreciation(test_version.id, 2026)

        # IT category: 10,000 + 10,000 = 20,000
        assert result["depreciation_by_category"]["IT"] == Decimal("20000.00")
        # Furniture category: 10,000
        assert result["depreciation_by_category"]["furniture"] == Decimal("10000.00")
        # Total: 30,000
        assert result["total_annual_depreciation"] == Decimal("30000.00")

    @pytest.mark.asyncio
    async def test_get_annual_depreciation_empty_plan(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
    ):
        """Test annual depreciation with no assets."""
        service = CapExService(db_session)
        result = await service.get_annual_depreciation(test_version.id, 2025)

        assert result["total_annual_depreciation"] == Decimal("0")
        assert result["depreciation_by_category"] == {}

    @pytest.mark.asyncio
    async def test_get_annual_depreciation_future_assets_excluded(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test that future assets are excluded from current year depreciation."""
        service = CapExService(db_session)

        # Asset acquired in 2025
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21500",
            description="2025 Asset",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("50000.00"),
            acquisition_date=date(2025, 1, 1),
            useful_life_years=5,
            user_id=test_user_id,
        )

        # Asset acquired in 2027 (future)
        await service.create_capex_entry(
            version_id=test_version.id,
            account_code="21510",
            description="2027 Asset",
            category="IT",
            quantity=1,
            unit_cost_sar=Decimal("30000.00"),
            acquisition_date=date(2027, 1, 1),
            useful_life_years=3,
            user_id=test_user_id,
        )

        # Calculate for 2026 (before second asset is acquired)
        result = await service.get_annual_depreciation(test_version.id, 2026)

        # Should only include first asset: 50,000 / 5 = 10,000
        assert result["total_annual_depreciation"] == Decimal("10000.00")


class TestCapExCalculations:
    """Tests for CapEx calculations."""

    @pytest.mark.asyncio
    async def test_total_cost_calculation(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test total cost calculation for multiple entries."""
        service = CapExService(db_session)

        # Create multiple entries
        await service.create_capex_entry(
            version_id=test_version.id,
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
            version_id=test_version.id,
            account_code="21600",
            description="Item 2",
            category="equipment",
            quantity=5,
            unit_cost_sar=Decimal("2000.00"),
            acquisition_date=date(2025, 2, 1),
            useful_life_years=10,
            user_id=test_user_id,
        )

        result = await service.get_capex_plan(test_version.id)

        total = sum(item.total_cost_sar for item in result)
        assert total == Decimal("20000.00")  # (10*1000) + (5*2000)

    @pytest.mark.asyncio
    async def test_depreciation_eligible_entries(
        self,
        db_session: AsyncSession,
        test_version: BudgetVersion,
        test_user_id: uuid.UUID,
    ):
        """Test entries are eligible for depreciation."""
        service = CapExService(db_session)

        result = await service.create_capex_entry(
            version_id=test_version.id,
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
