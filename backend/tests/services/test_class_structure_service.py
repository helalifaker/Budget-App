"""
Tests for Class Structure Service.

Covers:
- Class structure calculation from enrollment data
- Class size parameter validation
- ATSEM allocation for Maternelle
- Update and delete operations
- Business rule validation
- Error handling

Target Coverage: 90%+
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    ClassSizeParam,
)
from app.models.planning import ClassStructure, EnrollmentPlan
from app.services.class_structure_service import ClassStructureService
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError


@pytest.fixture
def mock_session():
    """Create mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def class_structure_service(mock_session):
    """Create class structure service instance."""
    return ClassStructureService(mock_session)


@pytest.fixture
def test_user_id():
    """Create test user UUID."""
    return uuid.uuid4()


@pytest.fixture
def mock_budget_version_id():
    """Create test budget version UUID."""
    return uuid.uuid4()


@pytest.fixture
def mock_maternelle_cycle():
    """Create Maternelle cycle."""
    cycle = MagicMock(spec=AcademicCycle)
    cycle.id = uuid.uuid4()
    cycle.code = "MATERNELLE"
    cycle.name_fr = "Maternelle"
    cycle.requires_atsem = True  # ATSEM required for Maternelle
    return cycle


@pytest.fixture
def mock_elementaire_cycle():
    """Create Élémentaire cycle."""
    cycle = MagicMock(spec=AcademicCycle)
    cycle.id = uuid.uuid4()
    cycle.code = "ELEMENTAIRE"
    cycle.name_fr = "Élémentaire"
    cycle.requires_atsem = False
    return cycle


@pytest.fixture
def mock_college_cycle():
    """Create Collège cycle."""
    cycle = MagicMock(spec=AcademicCycle)
    cycle.id = uuid.uuid4()
    cycle.code = "COLLEGE"
    cycle.name_fr = "Collège"
    cycle.requires_atsem = False
    return cycle


@pytest.fixture
def mock_maternelle_levels(mock_maternelle_cycle):
    """Create Maternelle levels (PS, MS, GS)."""
    ps = MagicMock(spec=AcademicLevel)
    ps.id = uuid.uuid4()
    ps.code = "PS"
    ps.name_fr = "Petite Section"
    ps.cycle_id = mock_maternelle_cycle.id
    ps.cycle = mock_maternelle_cycle
    ps.is_secondary = False
    ps.sort_order = 1

    ms = MagicMock(spec=AcademicLevel)
    ms.id = uuid.uuid4()
    ms.code = "MS"
    ms.name_fr = "Moyenne Section"
    ms.cycle_id = mock_maternelle_cycle.id
    ms.cycle = mock_maternelle_cycle
    ms.is_secondary = False
    ms.sort_order = 2

    gs = MagicMock(spec=AcademicLevel)
    gs.id = uuid.uuid4()
    gs.code = "GS"
    gs.name_fr = "Grande Section"
    gs.cycle_id = mock_maternelle_cycle.id
    gs.cycle = mock_maternelle_cycle
    gs.is_secondary = False
    gs.sort_order = 3

    return [ps, ms, gs]


@pytest.fixture
def mock_college_levels(mock_college_cycle):
    """Create Collège levels (6ème, 5ème, 4ème, 3ème)."""
    levels = []
    for i, (code, name) in enumerate([
        ("6EME", "Sixième"),
        ("5EME", "Cinquième"),
        ("4EME", "Quatrième"),
        ("3EME", "Troisième"),
    ]):
        level = MagicMock(spec=AcademicLevel)
        level.id = uuid.uuid4()
        level.code = code
        level.name_fr = name
        level.cycle_id = mock_college_cycle.id
        level.cycle = mock_college_cycle
        level.is_secondary = True
        level.sort_order = i + 1
        levels.append(level)
    return levels


# ==============================================================================
# Test: Get Class Structure
# ==============================================================================


class TestGetClassStructure:
    """Tests for getting class structure."""

    @pytest.mark.asyncio
    async def test_get_class_structure_success(
        self,
        class_structure_service: ClassStructureService,
        mock_session,
        mock_budget_version_id,
    ):
        """Test successful retrieval of class structure."""
        mock_structures = [
            MagicMock(
                id=uuid.uuid4(),
                budget_version_id=mock_budget_version_id,
                level_id=uuid.uuid4(),
                total_students=50,
                number_of_classes=2,
                avg_class_size=Decimal("25.0"),
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_structures
        mock_session.execute.return_value = mock_result

        result = await class_structure_service.get_class_structure(mock_budget_version_id)

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_class_structure_empty(
        self,
        class_structure_service: ClassStructureService,
        mock_session,
        mock_budget_version_id,
    ):
        """Test retrieval when no class structures exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await class_structure_service.get_class_structure(mock_budget_version_id)

        assert result == []


# ==============================================================================
# Test: Calculate Class Structure
# ==============================================================================


class TestCalculateClassStructure:
    """Tests for class structure calculation."""

    @pytest.mark.asyncio
    async def test_calculate_class_structure_target_method(
        self,
        class_structure_service: ClassStructureService,
        mock_session,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """
        Test class structure calculation with target method.

        Formula: classes = CEILING(total_students / target_class_size)
        Example: 75 students / 25 target = 3 classes
        """
        level = mock_college_levels[0]  # 6ème

        # Mock enrollment data
        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (75, level, mock_college_cycle)},
        ):
            # Mock class size params
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                # Mock get_class_structure (no existing structures)
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    # Mock base_service.create
                    created = MagicMock()
                    created.id = uuid.uuid4()
                    created.number_of_classes = 3
                    created.avg_class_size = Decimal("25.0")
                    class_structure_service.base_service = MagicMock()
                    class_structure_service.base_service.create = AsyncMock(
                        return_value=created
                    )

                    result = await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="target",
                        user_id=test_user_id,
                    )

                    assert len(result) == 1
                    # 75 / 25 = 3 classes (exact division)
                    class_structure_service.base_service.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_class_structure_min_method(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """
        Test class structure calculation with min method.

        Formula: classes = CEILING(total_students / min_class_size)
        Example: 75 students / 20 min = 4 classes
        """
        level = mock_college_levels[0]

        # Use 80 students so avg class size (80/4=20) equals min_class_size
        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (80, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    created = MagicMock()
                    created.id = uuid.uuid4()
                    created.number_of_classes = 4  # ceil(80/20) = 4
                    created.avg_class_size = Decimal("20.0")  # 80/4 = 20
                    class_structure_service.base_service = MagicMock()
                    class_structure_service.base_service.create = AsyncMock(
                        return_value=created
                    )

                    result = await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="min",
                        user_id=test_user_id,
                    )

                    assert len(result) == 1

    @pytest.mark.asyncio
    async def test_calculate_class_structure_max_method(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """
        Test class structure calculation with max method.

        Formula: classes = CEILING(total_students / max_class_size)
        Example: 75 students / 30 max = 3 classes
        """
        level = mock_college_levels[0]

        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (75, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    created = MagicMock()
                    created.id = uuid.uuid4()
                    created.number_of_classes = 3  # ceil(75/30) = 3
                    created.avg_class_size = Decimal("25.0")
                    class_structure_service.base_service = MagicMock()
                    class_structure_service.base_service.create = AsyncMock(
                        return_value=created
                    )

                    result = await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="max",
                        user_id=test_user_id,
                    )

                    assert len(result) == 1

    @pytest.mark.asyncio
    async def test_calculate_class_structure_invalid_method(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        test_user_id,
    ):
        """Test calculation with invalid method raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            await class_structure_service.calculate_class_structure(
                version_id=mock_budget_version_id,
                method="invalid_method",
                user_id=test_user_id,
            )

        assert "Invalid calculation method" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_class_structure_no_enrollment_data(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        test_user_id,
    ):
        """Test calculation fails when no enrollment data exists."""
        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={},
        ):
            with pytest.raises(BusinessRuleError) as exc_info:
                await class_structure_service.calculate_class_structure(
                    version_id=mock_budget_version_id,
                    method="target",
                    user_id=test_user_id,
                )

            assert "without enrollment data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_class_structure_no_class_size_params(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """Test calculation fails when no class size params exist."""
        level = mock_college_levels[0]

        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (75, level, mock_college_cycle)},
        ):
            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[],
            ):
                with pytest.raises(BusinessRuleError) as exc_info:
                    await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="target",
                        user_id=test_user_id,
                    )

                assert "without class size parameters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_class_structure_with_override(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """Test calculation with manual override by level."""
        level = mock_college_levels[0]

        # Use 100 students so override to 4 classes gives avg=25, within range [20-30]
        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (100, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    created = MagicMock()
                    created.id = uuid.uuid4()
                    created.number_of_classes = 4  # Override to 4 classes
                    created.avg_class_size = Decimal("25.0")  # 100/4 = 25
                    class_structure_service.base_service = MagicMock()
                    class_structure_service.base_service.create = AsyncMock(
                        return_value=created
                    )

                    result = await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="target",
                        override_by_level={str(level.id): 4},
                        user_id=test_user_id,
                    )

                    assert len(result) == 1


# ==============================================================================
# Test: ATSEM Allocation (Maternelle)
# ==============================================================================


class TestATSEMAllocation:
    """Tests for ATSEM allocation in Maternelle."""

    @pytest.mark.asyncio
    async def test_calculate_atsem_for_maternelle(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_maternelle_levels,
        mock_maternelle_cycle,
        test_user_id,
    ):
        """
        Test ATSEM allocation for Maternelle levels.

        Rule: 1 ATSEM per class in Maternelle
        Example: 3 classes = 3 ATSEMs
        """
        level = mock_maternelle_levels[0]  # PS

        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (60, level, mock_maternelle_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_maternelle_cycle.id
            params.min_class_size = 15
            params.target_class_size = 20
            params.max_class_size = 25

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    created = MagicMock()
                    created.id = uuid.uuid4()
                    created.number_of_classes = 3  # ceil(60/20) = 3
                    created.avg_class_size = Decimal("20.0")
                    created.requires_atsem = True
                    created.atsem_count = 3  # 1 per class
                    class_structure_service.base_service = MagicMock()
                    class_structure_service.base_service.create = AsyncMock(
                        return_value=created
                    )

                    result = await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="target",
                        user_id=test_user_id,
                    )

                    # Verify ATSEM was set in create call
                    call_args = class_structure_service.base_service.create.call_args
                    data = call_args[0][0]
                    assert data["requires_atsem"] is True
                    assert data["atsem_count"] == 3

    @pytest.mark.asyncio
    async def test_no_atsem_for_college(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """Test no ATSEM allocation for Collège levels."""
        level = mock_college_levels[0]  # 6ème

        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (75, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    created = MagicMock()
                    created.id = uuid.uuid4()
                    created.number_of_classes = 3
                    created.avg_class_size = Decimal("25.0")
                    created.requires_atsem = False
                    created.atsem_count = 0
                    class_structure_service.base_service = MagicMock()
                    class_structure_service.base_service.create = AsyncMock(
                        return_value=created
                    )

                    await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="target",
                        user_id=test_user_id,
                    )

                    # Verify no ATSEM
                    call_args = class_structure_service.base_service.create.call_args
                    data = call_args[0][0]
                    assert data["requires_atsem"] is False
                    assert data["atsem_count"] == 0


# ==============================================================================
# Test: Update Class Structure
# ==============================================================================


class TestUpdateClassStructure:
    """Tests for updating class structure."""

    @pytest.mark.asyncio
    async def test_update_number_of_classes(
        self,
        class_structure_service: ClassStructureService,
        test_user_id,
    ):
        """Test updating number of classes."""
        class_structure_id = uuid.uuid4()

        existing = MagicMock(spec=ClassStructure)
        existing.id = class_structure_id
        existing.total_students = 75
        existing.number_of_classes = 3
        existing.avg_class_size = Decimal("25.0")

        with patch.object(
            class_structure_service,
            "get_class_structure_by_id",
            return_value=existing,
        ):
            updated = MagicMock()
            updated.number_of_classes = 4
            updated.avg_class_size = Decimal("18.75")
            class_structure_service.base_service = MagicMock()
            class_structure_service.base_service.update = AsyncMock(return_value=updated)

            result = await class_structure_service.update_class_structure(
                class_structure_id=class_structure_id,
                number_of_classes=4,
                user_id=test_user_id,
            )

            assert result.number_of_classes == 4

    @pytest.mark.asyncio
    async def test_update_invalid_number_of_classes(
        self,
        class_structure_service: ClassStructureService,
        test_user_id,
    ):
        """Test validation error for invalid number of classes."""
        class_structure_id = uuid.uuid4()

        existing = MagicMock(spec=ClassStructure)
        existing.id = class_structure_id

        with patch.object(
            class_structure_service,
            "get_class_structure_by_id",
            return_value=existing,
        ):
            with pytest.raises(ValidationError) as exc_info:
                await class_structure_service.update_class_structure(
                    class_structure_id=class_structure_id,
                    number_of_classes=0,
                    user_id=test_user_id,
                )

            assert "greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_invalid_avg_class_size(
        self,
        class_structure_service: ClassStructureService,
        test_user_id,
    ):
        """Test validation error for invalid average class size."""
        class_structure_id = uuid.uuid4()

        existing = MagicMock(spec=ClassStructure)
        existing.id = class_structure_id

        with patch.object(
            class_structure_service,
            "get_class_structure_by_id",
            return_value=existing,
        ):
            with pytest.raises(ValidationError) as exc_info:
                await class_structure_service.update_class_structure(
                    class_structure_id=class_structure_id,
                    avg_class_size=Decimal("55"),  # > 50
                    user_id=test_user_id,
                )

            assert "between 0 and 50" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_invalid_atsem_count(
        self,
        class_structure_service: ClassStructureService,
        test_user_id,
    ):
        """Test validation error for negative ATSEM count."""
        class_structure_id = uuid.uuid4()

        existing = MagicMock(spec=ClassStructure)
        existing.id = class_structure_id

        with patch.object(
            class_structure_service,
            "get_class_structure_by_id",
            return_value=existing,
        ):
            with pytest.raises(ValidationError) as exc_info:
                await class_structure_service.update_class_structure(
                    class_structure_id=class_structure_id,
                    atsem_count=-1,
                    user_id=test_user_id,
                )

            assert "non-negative" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_recalculates_avg_class_size(
        self,
        class_structure_service: ClassStructureService,
        test_user_id,
    ):
        """Test that updating students/classes recalculates avg_class_size."""
        class_structure_id = uuid.uuid4()

        existing = MagicMock(spec=ClassStructure)
        existing.id = class_structure_id
        existing.total_students = 75
        existing.number_of_classes = 3
        existing.avg_class_size = Decimal("25.0")

        with patch.object(
            class_structure_service,
            "get_class_structure_by_id",
            return_value=existing,
        ):
            updated = MagicMock()
            updated.total_students = 80
            updated.number_of_classes = 3
            updated.avg_class_size = Decimal("26.67")
            class_structure_service.base_service = MagicMock()
            class_structure_service.base_service.update = AsyncMock(return_value=updated)

            await class_structure_service.update_class_structure(
                class_structure_id=class_structure_id,
                total_students=80,
                user_id=test_user_id,
            )

            # Verify avg_class_size was recalculated
            call_args = class_structure_service.base_service.update.call_args
            data = call_args[0][1]
            assert "avg_class_size" in data
            # 80 / 3 = 26.67
            assert data["avg_class_size"] == Decimal("26.67")


# ==============================================================================
# Test: Delete Class Structure
# ==============================================================================


class TestDeleteClassStructure:
    """Tests for deleting class structure."""

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        class_structure_service: ClassStructureService,
    ):
        """Test successful deletion of class structure."""
        class_structure_id = uuid.uuid4()

        class_structure_service.base_service = MagicMock()
        class_structure_service.base_service.delete = AsyncMock(return_value=True)

        result = await class_structure_service.delete_class_structure(
            class_structure_id=class_structure_id,
        )

        assert result is True
        class_structure_service.base_service.delete.assert_called_once_with(
            class_structure_id
        )


# ==============================================================================
# Test: Business Rule Validation
# ==============================================================================


class TestBusinessRuleValidation:
    """Tests for business rule enforcement."""

    @pytest.mark.asyncio
    async def test_avg_class_size_below_minimum(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """
        Test validation when avg class size falls below minimum.

        Rule: min_class_size < target_class_size ≤ max_class_size
        """
        level = mock_college_levels[0]

        # 20 students / 2 classes (via override) = 10 avg (below min of 20)
        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (20, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    with pytest.raises(BusinessRuleError) as exc_info:
                        await class_structure_service.calculate_class_structure(
                            version_id=mock_budget_version_id,
                            method="target",
                            override_by_level={str(level.id): 2},  # Forces avg = 10
                            user_id=test_user_id,
                        )

                    assert "below minimum" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_avg_class_size_exceeds_maximum(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """Test validation when avg class size exceeds maximum."""
        level = mock_college_levels[0]

        # 100 students / 3 classes = 33.33 avg (above max of 30)
        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (100, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    with pytest.raises(BusinessRuleError) as exc_info:
                        await class_structure_service.calculate_class_structure(
                            version_id=mock_budget_version_id,
                            method="target",
                            override_by_level={str(level.id): 3},  # Forces avg = 33.33
                            user_id=test_user_id,
                        )

                    assert "exceeds maximum" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_missing_params_for_level(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """Test validation when no class size params exist for a level."""
        level = mock_college_levels[0]
        another_level = mock_college_levels[1]

        # Enrollment for 6ème, but params only for 5ème
        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (75, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = another_level.id  # Different level
            params.cycle_id = None  # No cycle fallback
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    with pytest.raises(BusinessRuleError) as exc_info:
                        await class_structure_service.calculate_class_structure(
                            version_id=mock_budget_version_id,
                            method="target",
                            user_id=test_user_id,
                        )

                    assert "No class size parameters found for level" in str(exc_info.value)


# ==============================================================================
# Test: Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_single_student_creates_one_class(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """Test that a single student creates exactly one class."""
        level = mock_college_levels[0]

        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (1, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 1  # Allow single student class
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[],
                ):
                    created = MagicMock()
                    created.number_of_classes = 1
                    class_structure_service.base_service = MagicMock()
                    class_structure_service.base_service.create = AsyncMock(
                        return_value=created
                    )

                    result = await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="target",
                        user_id=test_user_id,
                    )

                    call_args = class_structure_service.base_service.create.call_args
                    data = call_args[0][0]
                    assert data["number_of_classes"] == 1

    @pytest.mark.asyncio
    async def test_update_existing_structure(
        self,
        class_structure_service: ClassStructureService,
        mock_budget_version_id,
        mock_college_levels,
        mock_college_cycle,
        test_user_id,
    ):
        """Test that existing structures are updated instead of created."""
        level = mock_college_levels[0]

        with patch.object(
            class_structure_service,
            "_get_enrollment_by_level",
            return_value={level.id: (75, level, mock_college_cycle)},
        ):
            params = MagicMock(spec=ClassSizeParam)
            params.level_id = level.id
            params.cycle_id = mock_college_cycle.id
            params.min_class_size = 20
            params.target_class_size = 25
            params.max_class_size = 30

            with patch.object(
                class_structure_service,
                "_get_class_size_params",
                return_value=[params],
            ):
                # Existing structure
                existing = MagicMock(spec=ClassStructure)
                existing.id = uuid.uuid4()
                existing.level_id = level.id
                existing.number_of_classes = 2

                with patch.object(
                    class_structure_service,
                    "get_class_structure",
                    return_value=[existing],
                ):
                    updated = MagicMock()
                    updated.number_of_classes = 3
                    class_structure_service.base_service = MagicMock()
                    class_structure_service.base_service.update = AsyncMock(
                        return_value=updated
                    )

                    await class_structure_service.calculate_class_structure(
                        version_id=mock_budget_version_id,
                        method="target",
                        user_id=test_user_id,
                    )

                    # Should call update, not create
                    class_structure_service.base_service.update.assert_called_once()
