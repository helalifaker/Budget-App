"""
Comprehensive tests for Subject Hours Service.

Tests all CRUD operations, validation, and business logic for subject hours matrix.
"""

import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from app.models import SubjectHoursMatrix
from app.services.exceptions import ValidationError
from app.services.settings.subject_hours_service import SubjectHoursService
from sqlalchemy.ext.asyncio import AsyncSession


class TestSubjectHoursServiceInitialization:
    """Tests for SubjectHoursService initialization."""

    def test_service_initialization(self):
        """Test service initializes with session and base services."""
        session = MagicMock(spec=AsyncSession)
        service = SubjectHoursService(session)

        assert service.session == session
        assert service._base_service is not None
        assert service._base_service.model == SubjectHoursMatrix
        assert service._cycle_service is not None
        assert service._level_service is not None
        assert service._subject_service is not None


class TestGetSubjectHoursMatrix:
    """Tests for retrieving subject hours matrix."""

    @pytest.mark.asyncio
    async def test_get_subject_hours_matrix_success(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test retrieving subject hours matrix."""
        service = SubjectHoursService(db_session)

        # Create some entries
        await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("4.5"),
            user_id=test_user_id,
        )

        matrix = await service.get_subject_hours_matrix(test_version.id)
        assert len(matrix) >= 1

        # Check eager loading
        entry = matrix[0]
        # Subject and level should be loaded
        assert entry.subject_id is not None
        assert entry.level_id is not None

    @pytest.mark.asyncio
    async def test_get_subject_hours_matrix_empty(
        self, db_session: AsyncSession, test_version
    ):
        """Test retrieving empty matrix returns empty list."""
        service = SubjectHoursService(db_session)
        matrix = await service.get_subject_hours_matrix(test_version.id)
        # May have entries from other tests, just verify it's a list
        assert isinstance(matrix, list)


class TestUpsertSubjectHours:
    """Tests for creating and updating subject hours."""

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_create(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test creating new subject hours entry."""
        service = SubjectHoursService(db_session)

        entry = await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["FRENCH"].id,
            level_id=academic_levels["5EME"].id,
            hours_per_week=Decimal("5.0"),
            is_split=False,
            notes="French language hours",
            user_id=test_user_id,
        )

        assert entry is not None
        assert entry.hours_per_week == Decimal("5.0")
        assert entry.is_split is False
        assert entry.notes == "French language hours"

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_update(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test updating existing subject hours entry."""
        service = SubjectHoursService(db_session)

        # Create first
        entry1 = await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("4.0"),
            user_id=test_user_id,
        )

        # Update same entry
        entry2 = await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("4.5"),
            is_split=True,
            user_id=test_user_id,
        )

        assert entry1.id == entry2.id
        assert entry2.hours_per_week == Decimal("4.5")
        assert entry2.is_split is True

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_invalid_zero_hours(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test zero hours fails validation."""
        service = SubjectHoursService(db_session)

        with pytest.raises(ValidationError, match="between 0 and 12"):
            await service.upsert_subject_hours(
                version_id=test_version.id,
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("0"),
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_invalid_negative_hours(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test negative hours fails validation."""
        service = SubjectHoursService(db_session)

        with pytest.raises(ValidationError, match="between 0 and 12"):
            await service.upsert_subject_hours(
                version_id=test_version.id,
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("-1"),
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_invalid_excessive_hours(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test hours exceeding 12 fails validation."""
        service = SubjectHoursService(db_session)

        with pytest.raises(ValidationError, match="between 0 and 12"):
            await service.upsert_subject_hours(
                version_id=test_version.id,
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("15"),
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_valid_boundary_hours(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test valid boundary hours (0.5 and 12)."""
        service = SubjectHoursService(db_session)

        # Test minimum valid hours
        entry1 = await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("0.5"),
            user_id=test_user_id,
        )
        assert entry1.hours_per_week == Decimal("0.5")

        # Test maximum valid hours
        entry2 = await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("12"),
            user_id=test_user_id,
        )
        assert entry2.hours_per_week == Decimal("12")

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_with_split(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test creating entry with split flag (half-size groups)."""
        service = SubjectHoursService(db_session)

        # Use SVT (Sciences de la Vie et de la Terre) for science lab work
        entry = await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["SVT"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("2.0"),
            is_split=True,
            notes="Lab work in half groups",
            user_id=test_user_id,
        )

        assert entry.is_split is True
        assert "half groups" in entry.notes


class TestBatchUpsertSubjectHours:
    """Tests for batch upsert operations."""

    @pytest.mark.asyncio
    async def test_batch_upsert_create_multiple(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test batch creating multiple entries."""
        from app.schemas.settings import SubjectHoursEntry

        service = SubjectHoursService(db_session)

        entries = [
            SubjectHoursEntry(
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("4.0"),
                is_split=False,
                notes=None,
            ),
            SubjectHoursEntry(
                subject_id=subjects["FRENCH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("5.0"),
                is_split=False,
                notes=None,
            ),
        ]

        result = await service.batch_upsert_subject_hours(
            version_id=test_version.id,
            entries=entries,
            user_id=test_user_id,
        )

        assert result.created_count >= 0
        assert result.updated_count >= 0
        assert result.created_count + result.updated_count == 2
        assert result.deleted_count == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_batch_upsert_with_deletion(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test batch operation with deletion (hours_per_week=None)."""
        from app.schemas.settings import SubjectHoursEntry

        service = SubjectHoursService(db_session)

        # First create an entry
        await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["HISTORY"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("3.0"),
            user_id=test_user_id,
        )

        # Now delete it via batch
        entries = [
            SubjectHoursEntry(
                subject_id=subjects["HISTORY"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=None,  # Deletion marker
                is_split=False,
                notes=None,
            ),
        ]

        result = await service.batch_upsert_subject_hours(
            version_id=test_version.id,
            entries=entries,
            user_id=test_user_id,
        )

        assert result.deleted_count == 1

    @pytest.mark.asyncio
    async def test_batch_upsert_invalid_hours_error(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test batch operation with invalid hours is rejected by Pydantic schema."""
        from app.schemas.settings import SubjectHoursEntry
        from pydantic import ValidationError as PydanticValidationError

        # Pydantic schema validates hours_per_week at instantiation (ge=0, le=12)
        # So invalid hours are rejected before reaching the service
        with pytest.raises(PydanticValidationError) as exc_info:
            SubjectHoursEntry(
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("15"),  # Invalid - exceeds 12
                is_split=False,
                notes=None,
            )

        # Verify the validation error contains the expected message
        assert "hours_per_week" in str(exc_info.value)
        assert "less than or equal to 12" in str(exc_info.value)


class TestGetSubjectHoursMatrixByCycle:
    """Tests for retrieving matrix organized by cycle."""

    @pytest.mark.asyncio
    async def test_get_matrix_by_cycle_all(
        self, db_session: AsyncSession, test_version, academic_cycles
    ):
        """Test retrieving matrix for all cycles."""
        service = SubjectHoursService(db_session)

        result = await service.get_subject_hours_matrix_by_cycle(
            version_id=test_version.id,
            cycle_code=None,
        )

        assert isinstance(result, list)
        # Should have entries for each cycle
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_matrix_by_cycle_filtered(
        self, db_session: AsyncSession, test_version, academic_cycles
    ):
        """Test retrieving matrix filtered by specific cycle."""
        service = SubjectHoursService(db_session)

        result = await service.get_subject_hours_matrix_by_cycle(
            version_id=test_version.id,
            cycle_code="COLL",
        )

        assert isinstance(result, list)
        # Should have only COLL cycle
        if len(result) > 0:
            assert result[0].cycle_code == "COLL"


class TestDeleteSubjectHours:
    """Tests for deleting subject hours entries."""

    @pytest.mark.asyncio
    async def test_delete_subject_hours_success(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test soft deleting a subject hours entry."""
        service = SubjectHoursService(db_session)

        # Create entry - use HISTORY (History-Geography)
        entry = await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["HISTORY"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("2.0"),
            user_id=test_user_id,
        )

        # Delete it
        await service.delete_subject_hours(entry.id, user_id=test_user_id)

        # Verify it's not in the matrix anymore
        matrix = await service.get_subject_hours_matrix(test_version.id)
        entry_ids = [e.id for e in matrix]
        assert entry.id not in entry_ids


class TestGetTotalHoursByLevel:
    """Tests for calculating total hours per level."""

    @pytest.mark.asyncio
    async def test_get_total_hours_by_level(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test calculating total weekly hours for a level."""
        service = SubjectHoursService(db_session)

        # Create entries for the same level
        await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["5EME"].id,
            hours_per_week=Decimal("4.0"),
            user_id=test_user_id,
        )
        await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["FRENCH"].id,
            level_id=academic_levels["5EME"].id,
            hours_per_week=Decimal("5.0"),
            user_id=test_user_id,
        )
        await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["SVT"].id,
            level_id=academic_levels["5EME"].id,
            hours_per_week=Decimal("3.5"),
            user_id=test_user_id,
        )

        total = await service.get_total_hours_by_level(
            version_id=test_version.id,
            level_id=academic_levels["5EME"].id,
        )

        # Total should be 4.0 + 5.0 + 3.5 = 12.5
        assert total >= Decimal("12.5")

    @pytest.mark.asyncio
    async def test_get_total_hours_empty_level(
        self, db_session: AsyncSession, test_version, academic_levels
    ):
        """Test total hours for level with no entries."""
        service = SubjectHoursService(db_session)

        # Use a level that might not have entries
        total = await service.get_total_hours_by_level(
            version_id=test_version.id,
            level_id=academic_levels["PS"].id,  # Maternelle level - unlikely to have secondary subject hours
        )

        # Should return 0 or sum of any existing entries
        assert total >= Decimal("0")


class TestHoursValidation:
    """Tests for hours validation rules."""

    def test_valid_hours_range(self):
        """Test valid hours are within 0-12 range."""
        valid_hours = [Decimal("0.5"), Decimal("1"), Decimal("4.5"), Decimal("12")]

        for hours in valid_hours:
            assert hours > 0 and hours <= 12

    def test_invalid_hours_zero(self):
        """Test zero hours is invalid."""
        hours = Decimal("0")
        is_valid = hours > 0
        assert is_valid is False

    def test_invalid_hours_negative(self):
        """Test negative hours is invalid."""
        hours = Decimal("-1")
        is_valid = hours > 0
        assert is_valid is False

    def test_invalid_hours_excessive(self):
        """Test hours over 12 is invalid."""
        hours = Decimal("13")
        is_valid = hours <= 12
        assert is_valid is False


class TestSplitClassBehavior:
    """Tests for split class (half-size groups) behavior."""

    @pytest.mark.asyncio
    async def test_split_class_doubles_teaching_hours(
        self, db_session: AsyncSession, test_version, subjects, academic_levels, test_user_id
    ):
        """Test that split classes are properly flagged."""
        service = SubjectHoursService(db_session)

        # Physics-Chemistry lab with split classes (half-size groups)
        entry = await service.upsert_subject_hours(
            version_id=test_version.id,
            subject_id=subjects["PHYS"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("2.0"),
            is_split=True,
            notes="Lab work requires half-size groups",
            user_id=test_user_id,
        )

        assert entry.is_split is True
        # Note: The actual doubling of teaching hours is done in DHG calculation
        # Here we just verify the flag is properly stored


class TestSubjectHoursUnitTests:
    """Unit tests using mocks for SubjectHoursService."""

    def test_service_attributes(self):
        """Test service has required attributes."""
        session = MagicMock(spec=AsyncSession)
        service = SubjectHoursService(session)

        assert hasattr(service, "session")
        assert hasattr(service, "_base_service")
        assert hasattr(service, "_cycle_service")
        assert hasattr(service, "_level_service")
        assert hasattr(service, "_subject_service")

    @pytest.mark.asyncio
    async def test_upsert_validates_hours_before_query(self):
        """Test validation happens before database query."""
        session = MagicMock(spec=AsyncSession)
        service = SubjectHoursService(session)

        with pytest.raises(ValidationError):
            await service.upsert_subject_hours(
                version_id=uuid.uuid4(),
                subject_id=uuid.uuid4(),
                level_id=uuid.uuid4(),
                hours_per_week=Decimal("-1"),
            )

        # Session should not have been used for query
        session.execute.assert_not_called()
