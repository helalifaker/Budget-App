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
from app.models import AcademicCycle, AcademicLevel
from app.services.exceptions import ValidationError
from app.services.settings.class_size_service import ClassSizeService
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
        self, db_session: AsyncSession, test_version
    ):
        """Test retrieving class sizes when none exist."""
        service = ClassSizeService(db_session)
        params = await service.get_class_size_params(test_version.id)
        assert params == []

    @pytest.mark.asyncio
    async def test_get_class_size_params_returns_all_for_version(
        self,
        db_session: AsyncSession,
        test_version,
        academic_cycles: dict[str, AcademicCycle],
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test retrieving all class size params for a budget version."""
        service = ClassSizeService(db_session)

        # Create a class size param for a level
        ps_level = academic_levels["PS"]
        param = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Retrieve all params
        params = await service.get_class_size_params(test_version.id)
        assert len(params) >= 1
        assert any(p.id == param.id for p in params)


class TestGetClassSizeParamByLevel:
    """Tests for retrieving class size by level."""

    @pytest.mark.asyncio
    async def test_get_param_by_level_not_found(
        self, db_session: AsyncSession, test_version
    ):
        """Test retrieving param for non-existent level returns None."""
        service = ClassSizeService(db_session)
        param = await service.get_class_size_param_by_level(
            test_version.id, uuid.uuid4()
        )
        assert param is None

    @pytest.mark.asyncio
    async def test_get_param_by_level_found(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test retrieving param for existing level."""
        service = ClassSizeService(db_session)

        # Create param for PS level
        ps_level = academic_levels["PS"]
        created = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Retrieve by level
        param = await service.get_class_size_param_by_level(
            test_version.id, ps_level.id
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
        self, db_session: AsyncSession, test_version
    ):
        """Test retrieving param for non-existent cycle returns None."""
        service = ClassSizeService(db_session)
        param = await service.get_class_size_param_by_cycle(
            test_version.id, uuid.uuid4()
        )
        assert param is None

    @pytest.mark.asyncio
    async def test_get_param_by_cycle_found(
        self,
        db_session: AsyncSession,
        test_version,
        academic_cycles: dict[str, AcademicCycle],
    ):
        """Test retrieving cycle-level default param."""
        service = ClassSizeService(db_session)

        # Create cycle-level default for maternelle
        maternelle = academic_cycles["maternelle"]
        created = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=None,
            cycle_id=maternelle.id,
            min_class_size=18,
            target_class_size=22,
            max_class_size=28,
        )

        # Retrieve by cycle
        param = await service.get_class_size_param_by_cycle(
            test_version.id, maternelle.id
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
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test creating a new level-specific class size param."""
        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]
        param = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=12,
            target_class_size=18,
            max_class_size=24,
            notes="Test notes",
        )

        assert param.id is not None
        assert param.version_id == test_version.id
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
        test_version,
        academic_cycles: dict[str, AcademicCycle],
    ):
        """Test creating a cycle-level default class size param."""
        service = ClassSizeService(db_session)

        college = academic_cycles["college"]
        param = await service.upsert_class_size_param(
            version_id=test_version.id,
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
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test updating an existing class size param."""
        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]

        # Create initial param
        param1 = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Update the same param
        param2 = await service.upsert_class_size_param(
            version_id=test_version.id,
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
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation: min must be < target."""
        service = ClassSizeService(db_session)
        ps_level = academic_levels["PS"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_version.id,
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
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation: target must be <= max."""
        service = ClassSizeService(db_session)
        ps_level = academic_levels["PS"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_version.id,
                level_id=ps_level.id,
                cycle_id=None,
                min_class_size=15,
                target_class_size=30,  # target > max
                max_class_size=25,
            )

        assert "min < target <= max" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_neither_level_nor_cycle(
        self, db_session: AsyncSession, test_version
    ):
        """Test validation: either level_id or cycle_id must be provided."""
        service = ClassSizeService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_version.id,
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
        test_version,
        academic_cycles: dict[str, AcademicCycle],
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation: cannot specify both level_id and cycle_id."""
        service = ClassSizeService(db_session)
        ps_level = academic_levels["PS"]
        maternelle = academic_cycles["maternelle"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_version.id,
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
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test soft deleting a class size param."""
        service = ClassSizeService(db_session)
        ps_level = academic_levels["PS"]

        # Create param
        param = await service.upsert_class_size_param(
            version_id=test_version.id,
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
            test_version.id, ps_level.id
        )
        assert found is None


class TestBatchUpsertClassSizeParams:
    """Tests for batch upsert operations with optimistic locking."""

    @pytest.mark.asyncio
    async def test_batch_upsert_create_multiple(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test batch creating multiple new class size params."""
        from app.schemas.settings import ClassSizeParamBatchEntry

        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]
        ms_level = academic_levels["MS"]
        gs_level = academic_levels["GS"]

        entries = [
            ClassSizeParamBatchEntry(
                level_id=ps_level.id,
                min_class_size=12,
                target_class_size=18,
                max_class_size=24,
                notes="PS config",
            ),
            ClassSizeParamBatchEntry(
                level_id=ms_level.id,
                min_class_size=14,
                target_class_size=20,
                max_class_size=26,
            ),
            ClassSizeParamBatchEntry(
                level_id=gs_level.id,
                min_class_size=16,
                target_class_size=22,
                max_class_size=28,
            ),
        ]

        result = await service.batch_upsert_class_size_params(
            version_id=test_version.id,
            entries=entries,
        )

        assert result.created_count == 3
        assert result.updated_count == 0
        assert result.conflict_count == 0
        assert len(result.entries) == 3
        assert all(e.status == "created" for e in result.entries)
        assert all(e.id is not None for e in result.entries)

    @pytest.mark.asyncio
    async def test_batch_upsert_update_existing(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test batch updating existing class size params."""
        from app.schemas.settings import ClassSizeParamBatchEntry

        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]

        # Create an existing param first
        existing = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Now batch update it (without updated_at for non-locking update)
        entries = [
            ClassSizeParamBatchEntry(
                level_id=ps_level.id,
                min_class_size=16,
                target_class_size=22,
                max_class_size=28,
                notes="Updated in batch",
            ),
        ]

        result = await service.batch_upsert_class_size_params(
            version_id=test_version.id,
            entries=entries,
        )

        assert result.created_count == 0
        assert result.updated_count == 1
        assert result.conflict_count == 0
        assert result.entries[0].id == existing.id
        assert result.entries[0].status == "updated"

        # Verify the update persisted
        updated = await service.get_class_size_param_by_level(
            test_version.id, ps_level.id
        )
        assert updated is not None
        assert updated.min_class_size == 16
        assert updated.target_class_size == 22
        assert updated.max_class_size == 28
        assert updated.notes == "Updated in batch"

    @pytest.mark.asyncio
    async def test_batch_upsert_optimistic_lock_conflict(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test optimistic locking detects conflicts when updated_at doesn't match."""
        from datetime import UTC, datetime, timedelta

        from app.schemas.settings import ClassSizeParamBatchEntry

        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]

        # Create an existing param
        existing = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Try to update with an OLD updated_at (simulating stale data)
        stale_updated_at = datetime.now(UTC) - timedelta(hours=1)

        entries = [
            ClassSizeParamBatchEntry(
                level_id=ps_level.id,
                min_class_size=16,
                target_class_size=22,
                max_class_size=28,
                updated_at=stale_updated_at,  # Stale timestamp
            ),
        ]

        result = await service.batch_upsert_class_size_params(
            version_id=test_version.id,
            entries=entries,
        )

        assert result.created_count == 0
        assert result.updated_count == 0
        assert result.conflict_count == 1
        assert result.entries[0].status == "conflict"
        assert result.entries[0].id == existing.id
        assert "modified since fetch" in (result.entries[0].error or "").lower()

    @pytest.mark.asyncio
    async def test_batch_upsert_optimistic_lock_success(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test optimistic locking allows update when updated_at matches."""
        from app.schemas.settings import ClassSizeParamBatchEntry

        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]

        # Create an existing param
        existing = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        # Update with the CORRECT updated_at
        entries = [
            ClassSizeParamBatchEntry(
                level_id=ps_level.id,
                min_class_size=16,
                target_class_size=22,
                max_class_size=28,
                updated_at=existing.updated_at,  # Matching timestamp
            ),
        ]

        result = await service.batch_upsert_class_size_params(
            version_id=test_version.id,
            entries=entries,
        )

        assert result.created_count == 0
        assert result.updated_count == 1
        assert result.conflict_count == 0
        assert result.entries[0].status == "updated"

    @pytest.mark.asyncio
    async def test_batch_upsert_partial_conflicts(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test batch upsert with mix of successes and conflicts."""
        from datetime import UTC, datetime, timedelta

        from app.schemas.settings import ClassSizeParamBatchEntry

        service = ClassSizeService(db_session)

        ps_level = academic_levels["PS"]
        ms_level = academic_levels["MS"]

        # Create existing params
        await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ps_level.id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=25,
        )

        ms_existing = await service.upsert_class_size_param(
            version_id=test_version.id,
            level_id=ms_level.id,
            cycle_id=None,
            min_class_size=16,
            target_class_size=21,
            max_class_size=26,
        )

        stale_updated_at = datetime.now(UTC) - timedelta(hours=1)

        # PS with stale timestamp (conflict), MS with correct timestamp (success)
        entries = [
            ClassSizeParamBatchEntry(
                level_id=ps_level.id,
                min_class_size=17,
                target_class_size=23,
                max_class_size=29,
                updated_at=stale_updated_at,  # Stale - will conflict
            ),
            ClassSizeParamBatchEntry(
                level_id=ms_level.id,
                min_class_size=18,
                target_class_size=24,
                max_class_size=30,
                updated_at=ms_existing.updated_at,  # Correct - will succeed
            ),
        ]

        result = await service.batch_upsert_class_size_params(
            version_id=test_version.id,
            entries=entries,
        )

        assert result.created_count == 0
        assert result.updated_count == 1
        assert result.conflict_count == 1

        # Check individual entry statuses
        ps_result = next(e for e in result.entries if e.level_id == ps_level.id)
        ms_result = next(e for e in result.entries if e.level_id == ms_level.id)

        assert ps_result.status == "conflict"
        assert ms_result.status == "updated"

    @pytest.mark.asyncio
    async def test_batch_upsert_validation_error_at_schema(
        self,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test Pydantic schema validates min < target <= max.

        Note: Validation happens at schema level via Pydantic field_validators,
        so invalid data never reaches the service. This test verifies
        the Pydantic validation works correctly.
        """
        from app.schemas.settings import ClassSizeParamBatchEntry
        from pydantic import ValidationError as PydanticValidationError

        ps_level = academic_levels["PS"]

        # Pydantic should raise validation error for min >= target
        with pytest.raises(PydanticValidationError) as exc_info:
            ClassSizeParamBatchEntry(
                level_id=ps_level.id,
                min_class_size=25,  # Invalid: min >= target
                target_class_size=20,
                max_class_size=30,
            )

        # Verify error message
        error_str = str(exc_info.value)
        assert "target_class_size" in error_str
        assert "greater than min_class_size" in error_str

    @pytest.mark.asyncio
    async def test_batch_upsert_target_greater_than_max_validation(
        self,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test Pydantic schema validates target <= max."""
        from app.schemas.settings import ClassSizeParamBatchEntry
        from pydantic import ValidationError as PydanticValidationError

        ps_level = academic_levels["PS"]

        # Pydantic should raise validation error for target > max
        with pytest.raises(PydanticValidationError) as exc_info:
            ClassSizeParamBatchEntry(
                level_id=ps_level.id,
                min_class_size=15,
                target_class_size=35,  # Invalid: target > max
                max_class_size=30,
            )

        # Verify error message
        error_str = str(exc_info.value)
        assert "max_class_size" in error_str

    @pytest.mark.asyncio
    async def test_batch_upsert_empty_entries(
        self,
        db_session: AsyncSession,
        test_version,
    ):
        """Test batch upsert with empty entries list."""
        service = ClassSizeService(db_session)

        result = await service.batch_upsert_class_size_params(
            version_id=test_version.id,
            entries=[],
        )

        assert result.created_count == 0
        assert result.updated_count == 0
        assert result.conflict_count == 0
        assert len(result.entries) == 0
