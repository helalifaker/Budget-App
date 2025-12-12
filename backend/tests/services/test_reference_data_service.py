"""
Comprehensive tests for ReferenceDataService.

Tests all read-only reference data access methods including:
- Academic cycles and levels
- Subjects
- Teacher categories
- Fee categories
- Nationality types
- Lookup helpers for bulk operations
"""

import uuid

import pytest
from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    FeeCategory,
    NationalityType,
    Subject,
    TeacherCategory,
)
from app.services.reference_data_service import ReferenceDataService
from sqlalchemy.ext.asyncio import AsyncSession


class TestReferenceDataServiceInitialization:
    """Tests for ReferenceDataService initialization."""

    def test_service_initialization(self, db_session: AsyncSession):
        """Test service initializes with session."""
        service = ReferenceDataService(db_session)
        assert service.session == db_session


class TestAcademicCycleOperations:
    """Tests for academic cycle retrieval."""

    @pytest.mark.asyncio
    async def test_get_academic_cycles_returns_all(
        self, db_session: AsyncSession, academic_cycles: dict[str, AcademicCycle]
    ):
        """Test retrieving all academic cycles."""
        service = ReferenceDataService(db_session)
        cycles = await service.get_academic_cycles()

        assert len(cycles) >= 4  # MAT, ELEM, COLL, LYC
        assert all(isinstance(c, AcademicCycle) for c in cycles)

    @pytest.mark.asyncio
    async def test_get_academic_cycles_ordered_by_sort_order(
        self, db_session: AsyncSession, academic_cycles: dict[str, AcademicCycle]
    ):
        """Test academic cycles are returned in sort_order."""
        service = ReferenceDataService(db_session)
        cycles = await service.get_academic_cycles()

        # Verify sorted by sort_order
        sort_orders = [c.sort_order for c in cycles]
        assert sort_orders == sorted(sort_orders)


class TestAcademicLevelOperations:
    """Tests for academic level retrieval."""

    @pytest.mark.asyncio
    async def test_get_academic_levels_returns_all(
        self, db_session: AsyncSession, academic_levels: dict[str, AcademicLevel]
    ):
        """Test retrieving all academic levels."""
        service = ReferenceDataService(db_session)
        levels = await service.get_academic_levels()

        assert len(levels) >= 3  # At least PS, MS, GS from maternelle
        assert all(isinstance(level, AcademicLevel) for level in levels)

    @pytest.mark.asyncio
    async def test_get_academic_levels_by_cycle(
        self,
        db_session: AsyncSession,
        academic_cycles: dict[str, AcademicCycle],
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test filtering academic levels by cycle ID."""
        service = ReferenceDataService(db_session)
        maternelle_id = academic_cycles["maternelle"].id

        levels = await service.get_academic_levels(cycle_id=maternelle_id)

        assert len(levels) >= 3  # PS, MS, GS
        assert all(level.cycle_id == maternelle_id for level in levels)

    @pytest.mark.asyncio
    async def test_get_academic_levels_loads_cycle_relationship(
        self, db_session: AsyncSession, academic_levels: dict[str, AcademicLevel]
    ):
        """Test that cycle relationship is eagerly loaded."""
        service = ReferenceDataService(db_session)
        levels = await service.get_academic_levels()

        # Should have cycle relationship loaded (no lazy loading exception)
        for level in levels:
            assert level.cycle is not None
            assert isinstance(level.cycle, AcademicCycle)

    @pytest.mark.asyncio
    async def test_get_academic_levels_ordered_by_sort_order(
        self, db_session: AsyncSession, academic_levels: dict[str, AcademicLevel]
    ):
        """Test academic levels are returned in sort_order."""
        service = ReferenceDataService(db_session)
        levels = await service.get_academic_levels()

        # Verify sorted by sort_order
        sort_orders = [level.sort_order for level in levels]
        assert sort_orders == sorted(sort_orders)

    @pytest.mark.asyncio
    async def test_get_levels_by_cycle_code(
        self,
        db_session: AsyncSession,
        academic_cycles: dict[str, AcademicCycle],
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test retrieving levels by cycle code."""
        service = ReferenceDataService(db_session)

        # Get maternelle levels by code (fixture uses MATERNELLE as code)
        levels = await service.get_levels_by_cycle_code("MATERNELLE")

        assert len(levels) >= 3  # PS, MS, GS
        # Verify all belong to maternelle
        for level in levels:
            assert level.cycle_id == academic_cycles["maternelle"].id

    @pytest.mark.asyncio
    async def test_get_levels_by_cycle_code_not_found(
        self, db_session: AsyncSession, academic_cycles: dict[str, AcademicCycle]
    ):
        """Test retrieving levels by non-existent cycle code returns empty."""
        service = ReferenceDataService(db_session)
        levels = await service.get_levels_by_cycle_code("INVALID")

        assert levels == []


class TestSubjectOperations:
    """Tests for subject retrieval."""

    @pytest.mark.asyncio
    async def test_get_subjects_active_only_default(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test get_subjects returns active subjects by default."""
        service = ReferenceDataService(db_session)
        result = await service.get_subjects()

        assert len(result) >= 1
        assert all(isinstance(s, Subject) for s in result)
        assert all(s.is_active for s in result)

    @pytest.mark.asyncio
    async def test_get_subjects_include_inactive(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test get_subjects can include inactive subjects."""
        service = ReferenceDataService(db_session)

        # Get all subjects including inactive
        all_subjects = await service.get_subjects(active_only=False)
        active_subjects = await service.get_subjects(active_only=True)

        # All subjects should be >= active subjects
        assert len(all_subjects) >= len(active_subjects)

    @pytest.mark.asyncio
    async def test_get_subjects_ordered_by_name(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test subjects are ordered by English name."""
        service = ReferenceDataService(db_session)
        result = await service.get_subjects()

        # Verify sorted by name_en
        names = [s.name_en for s in result]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_get_subject_by_code_success(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test retrieving subject by code."""
        service = ReferenceDataService(db_session)

        # Get a known subject (FRENCH is the code in fixture)
        subject = await service.get_subject_by_code("FRENCH")

        assert subject is not None
        assert subject.code == "FRENCH"

    @pytest.mark.asyncio
    async def test_get_subject_by_code_case_insensitive(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test subject code lookup is case insensitive."""
        service = ReferenceDataService(db_session)

        # Test lowercase
        subject = await service.get_subject_by_code("french")

        assert subject is not None
        assert subject.code == "FRENCH"

    @pytest.mark.asyncio
    async def test_get_subject_by_code_not_found(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test retrieving non-existent subject returns None."""
        service = ReferenceDataService(db_session)
        subject = await service.get_subject_by_code("INVALID_CODE")

        assert subject is None

    @pytest.mark.asyncio
    async def test_get_subjects_by_category(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test filtering subjects by category."""
        service = ReferenceDataService(db_session)

        # Get core subjects
        core_subjects = await service.get_subjects_by_category("core")

        assert len(core_subjects) >= 1
        assert all(s.category == "core" for s in core_subjects)
        assert all(s.is_active for s in core_subjects)

    @pytest.mark.asyncio
    async def test_get_subjects_by_category_empty(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test filtering by non-existent category returns empty."""
        service = ReferenceDataService(db_session)
        result = await service.get_subjects_by_category("nonexistent")

        assert result == []


class TestTeacherCategoryOperations:
    """Tests for teacher category retrieval."""

    @pytest.mark.asyncio
    async def test_get_teacher_categories_returns_all(
        self, db_session: AsyncSession, teacher_categories: dict[str, TeacherCategory]
    ):
        """Test retrieving all teacher categories."""
        service = ReferenceDataService(db_session)
        categories = await service.get_teacher_categories()

        assert len(categories) >= 1
        assert all(isinstance(c, TeacherCategory) for c in categories)

    @pytest.mark.asyncio
    async def test_get_teacher_category_by_code_success(
        self, db_session: AsyncSession, teacher_categories: dict[str, TeacherCategory]
    ):
        """Test retrieving teacher category by code."""
        service = ReferenceDataService(db_session)

        # Get AEFE detached category
        category = await service.get_teacher_category_by_code("AEFE_DETACHED")

        assert category is not None
        assert category.code == "AEFE_DETACHED"

    @pytest.mark.asyncio
    async def test_get_teacher_category_by_code_not_found(
        self, db_session: AsyncSession, teacher_categories: dict[str, TeacherCategory]
    ):
        """Test retrieving non-existent category returns None."""
        service = ReferenceDataService(db_session)
        category = await service.get_teacher_category_by_code("INVALID_CODE")

        assert category is None


class TestFeeCategoryOperations:
    """Tests for fee category retrieval."""

    @pytest.mark.asyncio
    async def test_get_fee_categories_returns_all(
        self, db_session: AsyncSession, fee_categories: dict[str, FeeCategory]
    ):
        """Test retrieving all fee categories."""
        service = ReferenceDataService(db_session)
        categories = await service.get_fee_categories()

        assert len(categories) >= 1
        assert all(isinstance(c, FeeCategory) for c in categories)

    @pytest.mark.asyncio
    async def test_get_fee_category_by_code_success(
        self, db_session: AsyncSession, fee_categories: dict[str, FeeCategory]
    ):
        """Test retrieving fee category by code."""
        service = ReferenceDataService(db_session)

        # Get tuition category
        category = await service.get_fee_category_by_code("TUITION")

        assert category is not None
        assert category.code == "TUITION"

    @pytest.mark.asyncio
    async def test_get_fee_category_by_code_not_found(
        self, db_session: AsyncSession, fee_categories: dict[str, FeeCategory]
    ):
        """Test retrieving non-existent fee category returns None."""
        service = ReferenceDataService(db_session)
        category = await service.get_fee_category_by_code("INVALID_CODE")

        assert category is None


class TestNationalityTypeOperations:
    """Tests for nationality type retrieval."""

    @pytest.mark.asyncio
    async def test_get_nationality_types_returns_all(
        self, db_session: AsyncSession, nationality_types: dict[str, NationalityType]
    ):
        """Test retrieving all nationality types."""
        service = ReferenceDataService(db_session)
        types = await service.get_nationality_types()

        assert len(types) >= 1
        assert all(isinstance(t, NationalityType) for t in types)

    @pytest.mark.asyncio
    async def test_get_nationality_types_ordered_by_sort_order(
        self, db_session: AsyncSession, nationality_types: dict[str, NationalityType]
    ):
        """Test nationality types are returned in sort_order."""
        service = ReferenceDataService(db_session)
        types = await service.get_nationality_types()

        # Verify sorted by sort_order
        sort_orders = [t.sort_order for t in types]
        assert sort_orders == sorted(sort_orders)

    @pytest.mark.asyncio
    async def test_get_nationality_type_by_code_success(
        self, db_session: AsyncSession, nationality_types: dict[str, NationalityType]
    ):
        """Test retrieving nationality type by code."""
        service = ReferenceDataService(db_session)

        # Get French nationality
        nat_type = await service.get_nationality_type_by_code("FRENCH")

        assert nat_type is not None
        assert nat_type.code == "FRENCH"

    @pytest.mark.asyncio
    async def test_get_nationality_type_by_code_not_found(
        self, db_session: AsyncSession, nationality_types: dict[str, NationalityType]
    ):
        """Test retrieving non-existent nationality type returns None."""
        service = ReferenceDataService(db_session)
        nat_type = await service.get_nationality_type_by_code("INVALID_CODE")

        assert nat_type is None


class TestLookupHelpers:
    """Tests for bulk lookup helper methods."""

    @pytest.mark.asyncio
    async def test_get_subject_code_to_id_mapping(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test subject code to ID mapping."""
        service = ReferenceDataService(db_session)
        mapping = await service.get_subject_code_to_id_mapping()

        assert isinstance(mapping, dict)
        assert len(mapping) >= 1

        # Verify mapping structure
        for code, subject_id in mapping.items():
            assert isinstance(code, str)
            assert isinstance(subject_id, uuid.UUID)

        # Verify known subject exists in mapping
        assert "FRENCH" in mapping

    @pytest.mark.asyncio
    async def test_get_level_code_to_id_mapping_all_levels(
        self, db_session: AsyncSession, academic_levels: dict[str, AcademicLevel]
    ):
        """Test level code to ID mapping for all levels."""
        service = ReferenceDataService(db_session)
        mapping = await service.get_level_code_to_id_mapping()

        assert isinstance(mapping, dict)
        assert len(mapping) >= 3  # At least PS, MS, GS

        # Verify mapping structure
        for code, level_id in mapping.items():
            assert isinstance(code, str)
            assert isinstance(level_id, uuid.UUID)

        # Verify known level exists in mapping
        assert "PS" in mapping

    @pytest.mark.asyncio
    async def test_get_level_code_to_id_mapping_filtered_by_cycle(
        self,
        db_session: AsyncSession,
        academic_cycles: dict[str, AcademicCycle],
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test level code mapping filtered by cycle codes."""
        service = ReferenceDataService(db_session)

        # Get only maternelle levels (fixture uses MATERNELLE as code)
        mapping = await service.get_level_code_to_id_mapping(cycle_codes=["MATERNELLE"])

        assert isinstance(mapping, dict)
        assert "PS" in mapping  # Maternelle level
        assert "MS" in mapping  # Maternelle level
        assert "GS" in mapping  # Maternelle level

        # College levels should not be present
        assert "6EME" not in mapping

    @pytest.mark.asyncio
    async def test_get_level_code_to_id_mapping_multiple_cycles(
        self,
        db_session: AsyncSession,
        academic_cycles: dict[str, AcademicCycle],
        academic_levels: dict[str, AcademicLevel],
    ):
        """Test level code mapping filtered by multiple cycle codes."""
        service = ReferenceDataService(db_session)

        # Get maternelle and college levels (fixture uses MATERNELLE, COLLEGE as codes)
        mapping = await service.get_level_code_to_id_mapping(
            cycle_codes=["MATERNELLE", "COLLEGE"]
        )

        assert isinstance(mapping, dict)
        # Should include both maternelle and college levels
        assert "PS" in mapping  # Maternelle
        assert "6EME" in mapping  # College


class TestConfigurationServiceDelegation:
    """Tests to verify ConfigurationService properly delegates to ReferenceDataService."""

    @pytest.mark.asyncio
    async def test_configuration_service_uses_reference_data_service(
        self, db_session: AsyncSession, academic_cycles: dict[str, AcademicCycle]
    ):
        """Test that ConfigurationService delegates to ReferenceDataService."""
        from app.services.configuration_service import ConfigurationService

        config_service = ConfigurationService(db_session)

        # Both services should return the same data
        ref_service = ReferenceDataService(db_session)

        config_cycles = await config_service.get_academic_cycles()
        ref_cycles = await ref_service.get_academic_cycles()

        assert len(config_cycles) == len(ref_cycles)
        assert {c.id for c in config_cycles} == {c.id for c in ref_cycles}

    @pytest.mark.asyncio
    async def test_configuration_service_subjects_delegation(
        self, db_session: AsyncSession, subjects: dict[str, Subject]
    ):
        """Test ConfigurationService.get_subjects delegates correctly."""
        from app.services.configuration_service import ConfigurationService

        config_service = ConfigurationService(db_session)
        ref_service = ReferenceDataService(db_session)

        config_subjects = await config_service.get_subjects()
        ref_subjects = await ref_service.get_subjects(active_only=True)

        assert len(config_subjects) == len(ref_subjects)
        assert {s.id for s in config_subjects} == {s.id for s in ref_subjects}
