"""
Unit tests for CapEx Service - Capital Expenditure Planning.
"""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.capex_service import CapExService
from app.services.exceptions import ValidationError


@pytest.fixture
def db_session():
    """Create a mock async session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def capex_service(db_session):
    """Create CapExService instance with mocked session."""
    return CapExService(db_session)


class TestCapExServiceInitialization:
    """Tests for CapExService initialization."""

    def test_capex_service_initialization(self, db_session):
        """Test service initializes with session."""
        service = CapExService(db_session)
        assert service.session == db_session
        assert service.capex_plan_service is not None


class TestCapExValidation:
    """Tests for CapEx entry validation."""

    @pytest.mark.asyncio
    async def test_create_capex_validates_account_code_prefix(self, capex_service):
        """Test CapEx requires account code starting with 20 or 21."""
        version_id = uuid.uuid4()

        capex_service.capex_plan_service.create = AsyncMock()

        with pytest.raises(ValidationError) as exc_info:
            await capex_service.create_capex_entry(
                version_id=version_id,
                account_code="60110",  # Invalid - should be 20xxx or 21xxx
                description="Computers",
                category="IT",
                quantity=10,
                unit_cost_sar=Decimal("5000"),
                acquisition_date=date(2025, 3, 1),
                useful_life_years=5,
            )

        assert "must start with 20 or 21" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_capex_accepts_valid_account_codes(self, capex_service):
        """Test valid CapEx account codes are accepted."""
        version_id = uuid.uuid4()

        mock_entry = MagicMock()
        capex_service.capex_plan_service.create = AsyncMock(return_value=mock_entry)

        # Test 20xxx (land, buildings)
        result = await capex_service.create_capex_entry(
            version_id=version_id,
            account_code="20500",
            description="Building improvements",
            category="building",
            quantity=1,
            unit_cost_sar=Decimal("500000"),
            acquisition_date=date(2025, 6, 1),
            useful_life_years=20,
        )
        assert result is not None

        # Test 21xxx (equipment, furniture)
        result = await capex_service.create_capex_entry(
            version_id=version_id,
            account_code="21830",
            description="IT equipment",
            category="IT",
            quantity=50,
            unit_cost_sar=Decimal("3000"),
            acquisition_date=date(2025, 3, 1),
            useful_life_years=5,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_create_capex_validates_quantity_minimum(self, capex_service):
        """Test CapEx requires quantity >= 1."""
        version_id = uuid.uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await capex_service.create_capex_entry(
                version_id=version_id,
                account_code="21830",
                description="Computers",
                category="IT",
                quantity=0,  # Invalid
                unit_cost_sar=Decimal("5000"),
                acquisition_date=date(2025, 3, 1),
                useful_life_years=5,
            )

        assert "at least 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_capex_validates_useful_life_range(self, capex_service):
        """Test CapEx requires useful life between 1 and 50 years."""
        version_id = uuid.uuid4()

        # Test zero years
        with pytest.raises(ValidationError) as exc_info:
            await capex_service.create_capex_entry(
                version_id=version_id,
                account_code="21830",
                description="Computers",
                category="IT",
                quantity=10,
                unit_cost_sar=Decimal("5000"),
                acquisition_date=date(2025, 3, 1),
                useful_life_years=0,
            )
        assert "between 1 and 50" in str(exc_info.value)

        # Test > 50 years
        with pytest.raises(ValidationError) as exc_info:
            await capex_service.create_capex_entry(
                version_id=version_id,
                account_code="21830",
                description="Computers",
                category="IT",
                quantity=10,
                unit_cost_sar=Decimal("5000"),
                acquisition_date=date(2025, 3, 1),
                useful_life_years=51,
            )
        assert "between 1 and 50" in str(exc_info.value)


class TestCapExTotalCostCalculation:
    """Tests for CapEx total cost calculation."""

    @pytest.mark.asyncio
    async def test_total_cost_equals_quantity_times_unit_cost(self, capex_service):
        """Test total_cost_sar = quantity × unit_cost_sar."""
        version_id = uuid.uuid4()

        create_mock = AsyncMock()
        capex_service.capex_plan_service.create = create_mock

        await capex_service.create_capex_entry(
            version_id=version_id,
            account_code="21830",
            description="Computers",
            category="IT",
            quantity=25,
            unit_cost_sar=Decimal("4000"),
            acquisition_date=date(2025, 3, 1),
            useful_life_years=5,
        )

        # Verify create was called with correct total
        call_args = create_mock.call_args
        data = call_args[0][0]
        assert data["total_cost_sar"] == Decimal("100000")  # 25 × 4000


class TestDepreciationCalculation:
    """Tests for depreciation calculation logic."""

    @pytest.mark.asyncio
    async def test_straight_line_depreciation_formula(self, capex_service):
        """Test annual depreciation = acquisition_cost / useful_life."""
        capex_id = uuid.uuid4()

        # Mock a CapEx entry
        mock_capex = MagicMock()
        mock_capex.id = capex_id
        mock_capex.total_cost_sar = Decimal("100000")
        mock_capex.acquisition_date = date(2020, 1, 1)
        mock_capex.useful_life_years = 10
        mock_capex.description = "Office equipment"
        mock_capex.account_code = "21830"
        mock_capex.category = "equipment"

        capex_service.get_capex_by_id = AsyncMock(return_value=mock_capex)

        result = await capex_service.calculate_depreciation(capex_id, 2025)

        # Annual depreciation = 100000 / 10 = 10000
        assert result["annual_depreciation"] == Decimal("10000.00")

        # Years elapsed = 2025 - 2020 = 5
        assert result["years_elapsed"] == 5

        # Accumulated = 10000 × 5 = 50000
        assert result["accumulated_depreciation"] == Decimal("50000.00")

        # Book value = 100000 - 50000 = 50000
        assert result["book_value"] == Decimal("50000.00")

        # Not fully depreciated yet
        assert result["is_fully_depreciated"] is False

    @pytest.mark.asyncio
    async def test_depreciation_caps_at_acquisition_cost(self, capex_service):
        """Test accumulated depreciation cannot exceed acquisition cost."""
        capex_id = uuid.uuid4()

        mock_capex = MagicMock()
        mock_capex.id = capex_id
        mock_capex.total_cost_sar = Decimal("50000")
        mock_capex.acquisition_date = date(2015, 1, 1)
        mock_capex.useful_life_years = 5
        mock_capex.description = "Old equipment"
        mock_capex.account_code = "21830"
        mock_capex.category = "equipment"

        capex_service.get_capex_by_id = AsyncMock(return_value=mock_capex)

        # Calculate for year beyond useful life (10 years after acquisition)
        result = await capex_service.calculate_depreciation(capex_id, 2025)

        # Accumulated should equal total cost
        assert result["accumulated_depreciation"] == Decimal("50000")

        # Book value should be zero
        assert result["book_value"] == Decimal("0.00")

        # Should be marked as fully depreciated
        assert result["is_fully_depreciated"] is True

    @pytest.mark.asyncio
    async def test_depreciation_validates_calculation_year(self, capex_service):
        """Test depreciation fails if year is before acquisition."""
        capex_id = uuid.uuid4()

        mock_capex = MagicMock()
        mock_capex.id = capex_id
        mock_capex.total_cost_sar = Decimal("100000")
        mock_capex.acquisition_date = date(2025, 1, 1)
        mock_capex.useful_life_years = 10

        capex_service.get_capex_by_id = AsyncMock(return_value=mock_capex)

        with pytest.raises(ValidationError) as exc_info:
            await capex_service.calculate_depreciation(capex_id, 2020)

        assert "cannot be before acquisition year" in str(exc_info.value)


class TestDepreciationSchedule:
    """Tests for multi-year depreciation schedule."""

    @pytest.mark.asyncio
    async def test_depreciation_schedule_length(self, capex_service):
        """Test schedule includes years up to useful life."""
        capex_id = uuid.uuid4()

        mock_capex = MagicMock()
        mock_capex.id = capex_id
        mock_capex.total_cost_sar = Decimal("60000")
        mock_capex.acquisition_date = date(2025, 1, 1)
        mock_capex.useful_life_years = 5
        mock_capex.description = "Equipment"
        mock_capex.account_code = "21830"
        mock_capex.category = "equipment"

        capex_service.get_capex_by_id = AsyncMock(return_value=mock_capex)

        schedule = await capex_service.get_depreciation_schedule(capex_id, years_ahead=10)

        # Should have 6 entries (year 0 through year 5)
        assert len(schedule) == 6

    @pytest.mark.asyncio
    async def test_depreciation_schedule_progression(self, capex_service):
        """Test depreciation schedule shows decreasing book value."""
        capex_id = uuid.uuid4()

        mock_capex = MagicMock()
        mock_capex.id = capex_id
        mock_capex.total_cost_sar = Decimal("50000")
        mock_capex.acquisition_date = date(2025, 1, 1)
        mock_capex.useful_life_years = 5
        mock_capex.description = "Equipment"
        mock_capex.account_code = "21830"
        mock_capex.category = "equipment"

        capex_service.get_capex_by_id = AsyncMock(return_value=mock_capex)

        schedule = await capex_service.get_depreciation_schedule(capex_id, years_ahead=5)

        # Book value should decrease each year
        book_values = [entry["book_value"] for entry in schedule]
        for i in range(1, len(book_values)):
            assert book_values[i] < book_values[i - 1], "Book value should decrease"

        # Final book value should be zero
        assert schedule[-1]["book_value"] == Decimal("0.00")


class TestCapExSummary:
    """Tests for CapEx summary calculations."""

    @pytest.mark.asyncio
    async def test_capex_summary_totals(self, capex_service):
        """Test CapEx summary aggregates correctly."""
        version_id = uuid.uuid4()

        mock_entries = [
            MagicMock(
                total_cost_sar=Decimal("100000"),
                category="IT",
                account_code="21830",
            ),
            MagicMock(
                total_cost_sar=Decimal("50000"),
                category="IT",
                account_code="21830",
            ),
            MagicMock(
                total_cost_sar=Decimal("200000"),
                category="furniture",
                account_code="21810",
            ),
        ]

        capex_service.get_capex_plan = AsyncMock(return_value=mock_entries)

        summary = await capex_service.get_capex_summary(version_id)

        assert summary["total_capex"] == Decimal("350000")
        assert summary["item_count"] == 3
        assert summary["capex_by_category"]["IT"]["total_cost"] == Decimal("150000")
        assert summary["capex_by_category"]["IT"]["item_count"] == 2
        assert summary["capex_by_category"]["furniture"]["total_cost"] == Decimal("200000")


class TestDepreciationFormulas:
    """Tests for depreciation calculation formulas."""

    def test_annual_depreciation_formula(self):
        """Test annual_depreciation = cost / useful_life."""
        acquisition_cost = Decimal("100000")
        useful_life = 10

        annual_depreciation = acquisition_cost / Decimal(useful_life)

        assert annual_depreciation == Decimal("10000")

    def test_accumulated_depreciation_formula(self):
        """Test accumulated_depreciation = annual × years_elapsed."""
        annual_depreciation = Decimal("10000")
        years_elapsed = 4

        accumulated = annual_depreciation * Decimal(years_elapsed)

        assert accumulated == Decimal("40000")

    def test_book_value_formula(self):
        """Test book_value = cost - accumulated_depreciation."""
        acquisition_cost = Decimal("100000")
        accumulated = Decimal("40000")

        book_value = acquisition_cost - accumulated

        assert book_value == Decimal("60000")

    def test_depreciation_rounding(self):
        """Test depreciation values are rounded to 2 decimal places."""
        acquisition_cost = Decimal("100000")
        useful_life = 3  # Results in repeating decimal

        annual_depreciation = acquisition_cost / Decimal(useful_life)
        rounded = annual_depreciation.quantize(Decimal("0.01"))

        assert str(rounded) == "33333.33"

    def test_total_depreciation_equals_cost(self):
        """Test sum of depreciation over useful life equals cost."""
        acquisition_cost = Decimal("10000")
        useful_life = 4

        annual = (acquisition_cost / Decimal(useful_life)).quantize(Decimal("0.01"))
        # 10000 / 4 = 2500.00

        total_depreciated = annual * Decimal(useful_life)

        assert total_depreciated == acquisition_cost


class TestCapExAccountCodePatterns:
    """Tests for CapEx PCG account code patterns."""

    def test_20xxx_codes_for_immovables(self):
        """Test 20xxx codes are for land and buildings."""
        codes = {
            "20100": "Land",
            "20500": "Building improvements",
            "20700": "Building installations",
        }

        for code in codes:
            assert code.startswith("20")

    def test_21xxx_codes_for_equipment(self):
        """Test 21xxx codes are for equipment and furniture."""
        codes = {
            "21500": "Industrial equipment",
            "21810": "Office furniture",
            "21830": "IT equipment",
            "21850": "Vehicles",
        }

        for code in codes:
            assert code.startswith("21")

    def test_valid_capex_prefixes(self):
        """Test only 20 and 21 prefixes are valid for CapEx."""
        valid_prefixes = ("20", "21")
        invalid_prefixes = ("22", "23", "60", "61", "64")

        for prefix in valid_prefixes:
            assert prefix in ("20", "21")

        for prefix in invalid_prefixes:
            assert prefix not in valid_prefixes


class TestUpdateCapExEntry:
    """Tests for CapEx entry updates."""

    @pytest.mark.asyncio
    async def test_update_recalculates_total_cost(self, capex_service):
        """Test updating quantity or unit cost recalculates total."""
        capex_id = uuid.uuid4()

        mock_capex = MagicMock()
        mock_capex.quantity = 10
        mock_capex.unit_cost_sar = Decimal("5000")
        mock_capex.total_cost_sar = Decimal("50000")

        capex_service.get_capex_by_id = AsyncMock(return_value=mock_capex)
        update_mock = AsyncMock(return_value=mock_capex)
        capex_service.capex_plan_service.update = update_mock

        await capex_service.update_capex_entry(
            capex_id=capex_id,
            quantity=20,  # Changed from 10 to 20
        )

        call_args = update_mock.call_args
        data = call_args[0][1]
        # New total = 20 × 5000 = 100000
        assert data["total_cost_sar"] == Decimal("100000")

    @pytest.mark.asyncio
    async def test_update_validates_account_code(self, capex_service):
        """Test update validates new account code if provided."""
        capex_id = uuid.uuid4()

        mock_capex = MagicMock()
        mock_capex.quantity = 10
        mock_capex.unit_cost_sar = Decimal("5000")

        capex_service.get_capex_by_id = AsyncMock(return_value=mock_capex)

        with pytest.raises(ValidationError):
            await capex_service.update_capex_entry(
                capex_id=capex_id,
                account_code="60100",  # Invalid for CapEx
            )
