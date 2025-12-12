"""
Comprehensive tests for FeeStructureService.

Tests all fee structure operations including:
- Retrieval of fee structures
- Creation and update (upsert) operations
- Filtering by level, nationality type, fee category
- Trimester handling (annual vs trimester fees)
- Soft delete functionality
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import (
    AcademicLevel,
    FeeCategory,
    NationalityType,
)
from app.services.fee_structure_service import FeeStructureService
from sqlalchemy.ext.asyncio import AsyncSession


class TestFeeStructureServiceInitialization:
    """Tests for FeeStructureService initialization."""

    def test_service_initialization(self, db_session: AsyncSession):
        """Test service initializes with session."""
        service = FeeStructureService(db_session)
        assert service.session == db_session
        assert service._base_service is not None


class TestGetFeeStructure:
    """Tests for retrieving fee structure."""

    @pytest.mark.asyncio
    async def test_get_fee_structure_empty(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving fees when none exist."""
        service = FeeStructureService(db_session)
        fees = await service.get_fee_structure(test_budget_version.id)
        assert fees == []

    @pytest.mark.asyncio
    async def test_get_fee_structure_returns_all_for_version(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test retrieving all fees for a budget version."""
        service = FeeStructureService(db_session)

        # Create a fee entry
        ps_level = academic_levels["PS"]
        tuition_cat = fee_categories["TUITION"]
        french_nat = nationality_types["FRENCH"]

        fee = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("50000.00"),
            trimester=None,
        )

        # Retrieve all fees
        fees = await service.get_fee_structure(test_budget_version.id)
        assert len(fees) >= 1
        assert any(f.id == fee.id for f in fees)


class TestGetFeeByCriteria:
    """Tests for retrieving fees by specific criteria."""

    @pytest.mark.asyncio
    async def test_get_fee_by_criteria_not_found(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving fee with non-matching criteria returns None."""
        service = FeeStructureService(db_session)
        fee = await service.get_fee_by_criteria(
            version_id=test_budget_version.id,
            level_id=uuid.uuid4(),
            nationality_type_id=uuid.uuid4(),
            fee_category_id=uuid.uuid4(),
        )
        assert fee is None

    @pytest.mark.asyncio
    async def test_get_fee_by_criteria_annual_fee(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test retrieving annual fee (trimester=None)."""
        service = FeeStructureService(db_session)

        ps_level = academic_levels["PS"]
        registration_cat = fee_categories["REGISTRATION"]
        french_nat = nationality_types["FRENCH"]

        # Create annual registration fee
        created = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=registration_cat.id,
            amount_sar=Decimal("5000.00"),
            trimester=None,
        )

        # Retrieve by criteria
        fee = await service.get_fee_by_criteria(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=registration_cat.id,
            trimester=None,
        )
        assert fee is not None
        assert fee.id == created.id

    @pytest.mark.asyncio
    async def test_get_fee_by_criteria_trimester_fee(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test retrieving trimester-specific fee."""
        service = FeeStructureService(db_session)

        ps_level = academic_levels["PS"]
        tuition_cat = fee_categories["TUITION"]
        french_nat = nationality_types["FRENCH"]

        # Create T1 tuition fee
        created = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("20000.00"),
            trimester=1,
        )

        # Retrieve T1 fee
        fee_t1 = await service.get_fee_by_criteria(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            trimester=1,
        )
        assert fee_t1 is not None
        assert fee_t1.id == created.id

        # T2 should not be found
        fee_t2 = await service.get_fee_by_criteria(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            trimester=2,
        )
        assert fee_t2 is None


class TestGetFeesByLevel:
    """Tests for retrieving fees by level."""

    @pytest.mark.asyncio
    async def test_get_fees_by_level_empty(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving fees for level with no fees."""
        service = FeeStructureService(db_session)
        fees = await service.get_fees_by_level(test_budget_version.id, uuid.uuid4())
        assert fees == []

    @pytest.mark.asyncio
    async def test_get_fees_by_level_returns_all(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test retrieving all fees for a specific level."""
        service = FeeStructureService(db_session)

        ps_level = academic_levels["PS"]
        tuition_cat = fee_categories["TUITION"]
        registration_cat = fee_categories["REGISTRATION"]
        french_nat = nationality_types["FRENCH"]

        # Create multiple fees for PS level
        await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("50000.00"),
        )
        await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=registration_cat.id,
            amount_sar=Decimal("5000.00"),
        )

        # Retrieve fees for PS level
        fees = await service.get_fees_by_level(test_budget_version.id, ps_level.id)
        assert len(fees) >= 2


class TestUpsertFeeStructure:
    """Tests for creating and updating fee structure entries."""

    @pytest.mark.asyncio
    async def test_create_annual_fee(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test creating a new annual fee entry."""
        service = FeeStructureService(db_session)

        ps_level = academic_levels["PS"]
        registration_cat = fee_categories["REGISTRATION"]
        french_nat = nationality_types["FRENCH"]

        fee = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=registration_cat.id,
            amount_sar=Decimal("5500.00"),
            trimester=None,
            notes="Annual registration fee",
        )

        assert fee.id is not None
        assert fee.budget_version_id == test_budget_version.id
        assert fee.level_id == ps_level.id
        assert fee.nationality_type_id == french_nat.id
        assert fee.fee_category_id == registration_cat.id
        assert fee.amount_sar == Decimal("5500.00")
        assert fee.trimester is None
        assert fee.notes == "Annual registration fee"

    @pytest.mark.asyncio
    async def test_create_trimester_fee(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test creating trimester-specific fee entries."""
        service = FeeStructureService(db_session)

        ps_level = academic_levels["PS"]
        tuition_cat = fee_categories["TUITION"]
        french_nat = nationality_types["FRENCH"]

        # Create T1 fee (40%)
        fee_t1 = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("20000.00"),
            trimester=1,
        )

        # Create T2 fee (30%)
        fee_t2 = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("15000.00"),
            trimester=2,
        )

        # Create T3 fee (30%)
        fee_t3 = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("15000.00"),
            trimester=3,
        )

        assert fee_t1.trimester == 1
        assert fee_t2.trimester == 2
        assert fee_t3.trimester == 3
        assert fee_t1.id != fee_t2.id != fee_t3.id

    @pytest.mark.asyncio
    async def test_update_existing_fee(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test updating an existing fee entry."""
        service = FeeStructureService(db_session)

        ps_level = academic_levels["PS"]
        tuition_cat = fee_categories["TUITION"]
        french_nat = nationality_types["FRENCH"]

        # Create initial fee
        fee1 = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("50000.00"),
        )

        # Update the same fee
        fee2 = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("55000.00"),
            notes="Updated fee amount",
        )

        # Should be the same record, not a new one
        assert fee2.id == fee1.id
        assert fee2.amount_sar == Decimal("55000.00")
        assert fee2.notes == "Updated fee amount"


class TestDeleteFeeStructure:
    """Tests for deleting fee structure entries."""

    @pytest.mark.asyncio
    async def test_delete_fee_structure(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test soft deleting a fee structure entry."""
        service = FeeStructureService(db_session)

        ps_level = academic_levels["PS"]
        tuition_cat = fee_categories["TUITION"]
        french_nat = nationality_types["FRENCH"]

        # Create fee
        fee = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("50000.00"),
        )

        # Delete it
        result = await service.delete_fee_structure(fee.id)
        assert result is True

        # Should not be found anymore
        found = await service.get_fee_by_criteria(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
        )
        assert found is None


class TestFeeStructureBusinessRules:
    """Tests for fee structure business rules."""

    @pytest.mark.asyncio
    async def test_different_nationality_different_fees(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
        fee_categories: dict[str, FeeCategory],
        nationality_types: dict[str, NationalityType],
    ):
        """Test that different nationalities can have different fee amounts."""
        service = FeeStructureService(db_session)

        ps_level = academic_levels["PS"]
        tuition_cat = fee_categories["TUITION"]
        french_nat = nationality_types["FRENCH"]
        saudi_nat = nationality_types["SAUDI"]

        # French student fee
        fee_french = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=french_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("50000.00"),
        )

        # Saudi student fee (different rate)
        fee_saudi = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            nationality_type_id=saudi_nat.id,
            fee_category_id=tuition_cat.id,
            amount_sar=Decimal("45000.00"),
        )

        assert fee_french.id != fee_saudi.id
        assert fee_french.amount_sar == Decimal("50000.00")
        assert fee_saudi.amount_sar == Decimal("45000.00")
