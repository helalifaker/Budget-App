"""
Comprehensive tests for ClassSizeService.

Tests all class size parameter operations including:
- Retrieval of class size parameters
- Creation and update (upsert) operations
- Validation of min < target <= max constraint
- Level-specific vs cycle-level defaults
- Soft delete functionality
"""

import uuid

import pytest
from app.models.configuration import AcademicCycle, AcademicLevel
from app.services.class_size_service import ClassSizeService
from app.services.exceptions import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class TestClassSizeServiceInitialization:
    """Tests for ClassSizeService initialization."""

    def test_service_initialization(self, db_session: AsyncSession):
        """Test service initializes with session."""
        service = ClassSizeService(db_session)
        assert service.session == db_session
        assert service._base_service is not None


class TestGetClassSizeParams:
    """Tests for retrieving class size parameters."""

    @pytest.mark.asyncio
    async def test_get_class_size_params_empty(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving class sizes when none exist."""
        service = ClassSizeService(db_session)
        params = await service.get_class_size_params(test_budget_version.id)
        assert params == []

    @pytest.mark.asyncio
    async def test_get_class_size_params_returns_all_for_version(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_cycles: dict[str, AcademicCycle],
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test retrieving all class size params for a budget version."""
        service = ClassSizeService(db_session)

        # Create a class size param for a level
        ps_level = academic_levels["PS"]
        param = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Retrieve all params
        params = await service.get_class_size_params(test_budget_version.id)
        assert len(params) >= 1
        assert any(p.id == param.id for p in params)


class TestGetClassSizeParamByLevel:
    """Tests for retrieving class size by level."""

    @pytest.mark.asyncio
    async def test_get_param_by_level_not_found(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving param for non-existent level returns None."""
        service = ClassSizeService(db_session)
        param = await service.get_class_size_param_by_level(
            test_budget_version.id, uuid.uuid4()
        )
        assert param is None

    @pytest.mark.asyncio
    async def test_get_param_by_level_found(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test retrieving param for existing level."""
        service = ClassSizeService(db_session)

        # Create param for PS level
        ps_level = academic_levels["PS"]
        created = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Retrieve by level
        param = await service.get_class_size_param_by_level(
            test_budget_version.id, ps_level.id
        )
        assert param is not None
        assert param.id == created.id
        assert param.min_class_size == 15
        assert param.target_class_size == 20
        assert param.max_class_size == 25


class TestGetClassSizeParamByCycle:
    """Tests for retrieving cycle-level defaults."""

    @pytest.mark.asyncio
    async def test_get_param_by_cycle_not_found(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving param for non-existent cycle returns None."""
        service = ClassSizeService(db_session)
        param = await service.get_class_size_param_by_cycle(
            test_budget_version.id, uuid.uuid4()
        )
        assert param is None

    @pytest.mark.asyncio
    async def test_get_param_by_cycle_found(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_cycles: dict[str, AcademicCycle],
    ):
        """Test retrieving cycle-level default param."""
        service = ClassSizeService(db_session)

        # Create cycle-level default for maternelle
        maternelle = academic_cycles["maternelle"]
        created = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=None,
            cycle_id=maternelle.id,
            min_class_size=18,
            target_class_size=22,
            max_class_size=28,
        )

        # Retrieve by cycle
        param = await service.get_class_size_param_by_cycle(
            test_budget_version.id, maternelle.id
        )
        assert param is not None
        assert param.id == created.id
        assert param.level_id is None
        assert param.cycle_id == maternelle.id


class TestUpsertClassSizeParam:
    """Tests for creating and updating class size parameters."""

    @pytest.mark.asyncio
    async def test_create_level_specific_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test creating a new level-specific class size param."""
        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]
        param = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=12,
            target_class_size=18,
            max_class_size=24,
            notes="Test notes",
        )

        assert param.id is not None
        assert param.budget_version_id == test_budget_version.id
        assert param.level_id == ps_level.id
        assert param.cycle_id is None
        assert param.min_class_size == 12
        assert param.target_class_size == 18
        assert param.max_class_size == 24
        assert param.notes == "Test notes"

    @pytest.mark.asyncio
    async def test_create_cycle_default_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_cycles: dict[str, AcademicCycle],
    ):
        """Test creating a cycle-level default class size param."""
        service = ClassSizeService(db_session)

        college = academic_cycles["college"]
        param = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=None,
            cycle_id=college.id,
            min_class_size=20,
            target_class_size=25,
            max_class_size=30,
        )

        assert param.id is not None
        assert param.level_id is None
        assert param.cycle_id == college.id
        assert param.min_class_size == 20

    @pytest.mark.asyncio
    async def test_update_existing_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test updating an existing class size param."""
        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]

        # Create initial param
        param1 = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Update the same param
        param2 = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=16,
            target_class_size=22,
            max_class_size=28,
            notes="Updated",
        )

        # Should be the same record, not a new one
        assert param2.id == param1.id
        assert param2.min_class_size == 16
        assert param2.target_class_size == 22
        assert param2.max_class_size == 28
        assert param2.notes == "Updated"


class TestClassSizeValidation:
    """Tests for class size validation rules."""

    @pytest.mark.asyncio
    async def test_validation_min_not_less_than_target(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation: min must be < target."""
        service = ClassSizeService(db_session)
        ps_level = academic_levels["PS"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=ps_level.id,
                cycle_id=None,
                min_class_size=20,  # min >= target
                target_class_size=20,
                max_class_size=25,
            )

        assert "min < target <= max" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_target_not_greater_than_max(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation: target must be <= max."""
        service = ClassSizeService(db_session)
        ps_level = academic_levels["PS"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=ps_level.id,
                cycle_id=None,
                min_class_size=15,
                target_class_size=30,  # target > max
                max_class_size=25,
            )

        assert "min < target <= max" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_neither_level_nor_cycle(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test validation: either level_id or cycle_id must be provided."""
        service = ClassSizeService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=None,
                cycle_id=None,
                min_class_size=15,
                target_class_size=20,
                max_class_size=25,
            )

        assert "level_id or cycle_id must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_both_level_and_cycle(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_cycles: dict[str, AcademicCycle],
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation: cannot specify both level_id and cycle_id."""
        service = ClassSizeService(db_session)
        ps_level = academic_levels["PS"]
        maternelle = academic_cycles["maternelle"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=ps_level.id,
                cycle_id=maternelle.id,
                min_class_size=15,
                target_class_size=20,
                max_class_size=25,
            )

        assert "Cannot specify both" in str(exc_info.value)


class TestDeleteClassSizeParam:
    """Tests for deleting class size parameters."""

    @pytest.mark.asyncio
    async def test_delete_class_size_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test soft deleting a class size param."""
        service = ClassSizeService(db_session)
        ps_level = academic_levels["PS"]

        # Create param
        param = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Delete it
        result = await service.delete_class_size_param(param.id)
        assert result is True

        # Should not be found anymore
        found = await service.get_class_size_param_by_level(
            test_budget_version.id, ps_level.id
        )
        assert found is None
