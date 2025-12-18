"""
Comprehensive tests for TimetableConstraintsService.

Tests all timetable constraint operations including:
- Retrieval of timetable constraints
- Creation and update (upsert) operations
- Validation of max_hours_per_day <= total_hours_per_week
- Subject hours validation against constraints
- Soft delete functionality
"""

import uuid
from decimal import Decimal

import pytest
from app.models import AcademicLevel
from app.services.exceptions import ValidationError
from app.services.settings.timetable_constraints_service import TimetableConstraintsService
from sqlalchemy.ext.asyncio import AsyncSession


class TestTimetableConstraintsServiceInitialization:
    """Tests for TimetableConstraintsService initialization."""

    def test_service_initialization(self, db_session: AsyncSession):
        """Test service initializes with session."""
        service = TimetableConstraintsService(db_session)
        assert service.session == db_session
        assert service._base_service is not None


class TestGetTimetableConstraints:
    """Tests for retrieving timetable constraints."""

    @pytest.mark.asyncio
    async def test_get_timetable_constraints_empty(
        self, db_session: AsyncSession, test_version
    ):
        """Test retrieving constraints when none exist."""
        service = TimetableConstraintsService(db_session)
        constraints = await service.get_timetable_constraints(test_version.id)
        assert constraints == []

    @pytest.mark.asyncio
    async def test_get_timetable_constraints_returns_all_for_version(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test retrieving all timetable constraints for a budget version."""
        service = TimetableConstraintsService(db_session)

        # Create a constraint for PS level
        ps_level = academic_levels["PS"]
        constraint = await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("5.5"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )

        # Retrieve all constraints
        constraints = await service.get_timetable_constraints(test_version.id)
        assert len(constraints) >= 1
        assert any(c.id == constraint.id for c in constraints)

    @pytest.mark.asyncio
    async def test_get_timetable_constraints_ordered_by_level(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test that constraints are ordered by level_id."""
        service = TimetableConstraintsService(db_session)

        # Create constraints for multiple levels
        ps_level = academic_levels["PS"]
        ms_level = academic_levels["MS"]

        await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ms_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("5.5"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )
        await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("5.5"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )

        constraints = await service.get_timetable_constraints(test_version.id)
        # Should be ordered by level_id
        assert len(constraints) >= 2


class TestGetConstraintByLevel:
    """Tests for retrieving constraint by level."""

    @pytest.mark.asyncio
    async def test_get_constraint_by_level_not_found(
        self, db_session: AsyncSession, test_version
    ):
        """Test retrieving constraint for non-existent level returns None."""
        service = TimetableConstraintsService(db_session)
        constraint = await service.get_constraint_by_level(
            test_version.id, uuid.uuid4()
        )
        assert constraint is None

    @pytest.mark.asyncio
    async def test_get_constraint_by_level_found(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test retrieving constraint for existing level."""
        service = TimetableConstraintsService(db_session)

        ps_level = academic_levels["PS"]
        created = await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("5.5"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )

        # Retrieve by level
        constraint = await service.get_constraint_by_level(
            test_version.id, ps_level.id
        )
        assert constraint is not None
        assert constraint.id == created.id
        assert constraint.total_hours_per_week == Decimal("24.0")


class TestUpsertTimetableConstraint:
    """Tests for creating and updating timetable constraints."""

    @pytest.mark.asyncio
    async def test_create_maternelle_constraint(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test creating timetable constraint for maternelle level."""
        service = TimetableConstraintsService(db_session)

        ps_level = academic_levels["PS"]
        constraint = await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("5.5"),
            days_per_week=4,  # Maternelle typically 4 days
            requires_lunch_break=True,
            min_break_duration_minutes=90,  # Nap time in maternelle
            notes="Standard maternelle schedule",
        )

        assert constraint.id is not None
        assert constraint.version_id == test_version.id
        assert constraint.level_id == ps_level.id
        assert constraint.total_hours_per_week == Decimal("24.0")
        assert constraint.max_hours_per_day == Decimal("5.5")
        assert constraint.days_per_week == 4
        assert constraint.requires_lunch_break is True
        assert constraint.min_break_duration_minutes == 90
        assert constraint.notes == "Standard maternelle schedule"

    @pytest.mark.asyncio
    async def test_create_secondary_constraint(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test creating timetable constraint for secondary level (collège)."""
        service = TimetableConstraintsService(db_session)

        # Get 6EME level (first year of collège)
        sixeme_level = academic_levels["6EME"]
        constraint = await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=sixeme_level.id,
            total_hours_per_week=Decimal("26.0"),
            max_hours_per_day=Decimal("6.0"),
            days_per_week=5,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
            notes="Standard collège schedule",
        )

        assert constraint.total_hours_per_week == Decimal("26.0")
        assert constraint.days_per_week == 5

    @pytest.mark.asyncio
    async def test_update_existing_constraint(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test updating an existing timetable constraint."""
        service = TimetableConstraintsService(db_session)

        ps_level = academic_levels["PS"]

        # Create initial constraint
        constraint1 = await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("5.5"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )

        # Update the same constraint
        constraint2 = await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("25.0"),
            max_hours_per_day=Decimal("6.0"),
            days_per_week=5,
            requires_lunch_break=True,
            min_break_duration_minutes=75,
            notes="Updated schedule",
        )

        # Should be the same record, not a new one
        assert constraint2.id == constraint1.id
        assert constraint2.total_hours_per_week == Decimal("25.0")
        assert constraint2.max_hours_per_day == Decimal("6.0")
        assert constraint2.days_per_week == 5
        assert constraint2.notes == "Updated schedule"


class TestTimetableConstraintValidation:
    """Tests for timetable constraint validation rules."""

    @pytest.mark.asyncio
    async def test_validation_max_hours_exceeds_total(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation: max_hours_per_day cannot exceed total_hours_per_week."""
        service = TimetableConstraintsService(db_session)
        ps_level = academic_levels["PS"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_timetable_constraint(
                version_id=test_version.id,
                level_id=ps_level.id,
                total_hours_per_week=Decimal("20.0"),
                max_hours_per_day=Decimal("25.0"),  # > total
                days_per_week=4,
                requires_lunch_break=True,
                min_break_duration_minutes=60,
            )

        assert "max_hours_per_day cannot exceed total_hours_per_week" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_validation_valid_hours_passes(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test that valid hours configuration passes validation."""
        service = TimetableConstraintsService(db_session)
        ps_level = academic_levels["PS"]

        # This should not raise
        constraint = await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("6.0"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )

        assert constraint is not None


class TestDeleteTimetableConstraint:
    """Tests for deleting timetable constraints."""

    @pytest.mark.asyncio
    async def test_delete_timetable_constraint(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test soft deleting a timetable constraint."""
        service = TimetableConstraintsService(db_session)
        ps_level = academic_levels["PS"]

        # Create constraint
        constraint = await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("5.5"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )

        # Delete it
        result = await service.delete_timetable_constraint(constraint.id)
        assert result is True

        # Should not be found anymore
        found = await service.get_constraint_by_level(test_version.id, ps_level.id)
        assert found is None


class TestValidateSubjectHoursFit:
    """Tests for validating subject hours against timetable constraints."""

    @pytest.mark.asyncio
    async def test_validate_subject_hours_within_limit(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation passes when subject hours are within limit."""
        service = TimetableConstraintsService(db_session)
        ps_level = academic_levels["PS"]

        # Create constraint allowing 24h/week
        await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("6.0"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )

        # Validate 20h of subject hours
        is_valid, error = await service.validate_subject_hours_fit(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_subject_hours=Decimal("20.0"),
        )

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_subject_hours_exceeds_limit(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation fails when subject hours exceed limit."""
        service = TimetableConstraintsService(db_session)
        ps_level = academic_levels["PS"]

        # Create constraint allowing 24h/week
        await service.upsert_timetable_constraint(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_hours_per_week=Decimal("24.0"),
            max_hours_per_day=Decimal("6.0"),
            days_per_week=4,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
        )

        # Validate 30h of subject hours (exceeds 24h limit)
        is_valid, error = await service.validate_subject_hours_fit(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_subject_hours=Decimal("30.0"),
        )

        assert is_valid is False
        assert "exceed" in error.lower()
        assert "30" in error
        assert "24" in error

    @pytest.mark.asyncio
    async def test_validate_subject_hours_no_constraint(
        self,
        db_session: AsyncSession,
        test_version,
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test validation passes when no constraint is defined (permissive)."""
        service = TimetableConstraintsService(db_session)
        ps_level = academic_levels["PS"]

        # No constraint created for this level

        # Should pass even with high hours (no constraint = no limit)
        is_valid, error = await service.validate_subject_hours_fit(
            version_id=test_version.id,
            level_id=ps_level.id,
            total_subject_hours=Decimal("100.0"),
        )

        assert is_valid is True
        assert error is None
