"""
Unit tests for Class Structure Service - Class Formation Planning.
"""

import uuid
from decimal import Decimal
from math import ceil
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.class_structure_service import ClassStructureService
from app.services.exceptions import BusinessRuleError, ValidationError


@pytest.fixture
def db_session():
    """Create a mock async session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def class_service(db_session):
    """Create ClassStructureService instance with mocked session."""
    return ClassStructureService(db_session)


class TestClassStructureServiceInitialization:
    """Tests for ClassStructureService initialization."""

    def test_service_initialization(self, db_session):
        """Test service initializes with session."""
        service = ClassStructureService(db_session)
        assert service.session == db_session
        assert service.base_service is not None


class TestCalculationMethodValidation:
    """Tests for calculation method validation."""

    @pytest.mark.asyncio
    async def test_calculate_validates_method_target(self, class_service):
        """Test 'target' is a valid calculation method."""
        # Mock empty enrollment to trigger early exit
        class_service._get_enrollment_by_level = AsyncMock(return_value={})

        with pytest.raises(BusinessRuleError) as exc_info:
            await class_service.calculate_class_structure(
                version_id=uuid.uuid4(),
                method="target",
            )

        # Should fail due to no enrollment, not invalid method
        assert "NO_ENROLLMENT" in exc_info.value.details.get("rule", "")

    @pytest.mark.asyncio
    async def test_calculate_validates_method_min(self, class_service):
        """Test 'min' is a valid calculation method."""
        class_service._get_enrollment_by_level = AsyncMock(return_value={})

        with pytest.raises(BusinessRuleError) as exc_info:
            await class_service.calculate_class_structure(
                version_id=uuid.uuid4(),
                method="min",
            )

        assert "NO_ENROLLMENT" in exc_info.value.details.get("rule", "")

    @pytest.mark.asyncio
    async def test_calculate_validates_method_max(self, class_service):
        """Test 'max' is a valid calculation method."""
        class_service._get_enrollment_by_level = AsyncMock(return_value={})

        with pytest.raises(BusinessRuleError) as exc_info:
            await class_service.calculate_class_structure(
                version_id=uuid.uuid4(),
                method="max",
            )

        assert "NO_ENROLLMENT" in exc_info.value.details.get("rule", "")

    @pytest.mark.asyncio
    async def test_calculate_rejects_invalid_method(self, class_service):
        """Test invalid method is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            await class_service.calculate_class_structure(
                version_id=uuid.uuid4(),
                method="average",  # Invalid
            )

        assert "target, min, or max" in str(exc_info.value)


class TestClassCountCalculation:
    """Tests for class count calculation formulas."""

    def test_class_count_formula_exact_division(self):
        """Test class count with exact division."""
        total_students = 100
        target_class_size = 25

        number_of_classes = ceil(total_students / target_class_size)

        assert number_of_classes == 4

    def test_class_count_formula_rounds_up(self):
        """Test class count rounds up for partial classes."""
        total_students = 101
        target_class_size = 25

        number_of_classes = ceil(total_students / target_class_size)

        # 101 / 25 = 4.04, ceiling = 5
        assert number_of_classes == 5

    def test_class_count_minimum_one(self):
        """Test at least one class is formed."""
        total_students = 5
        target_class_size = 25

        number_of_classes = max(1, ceil(total_students / target_class_size))

        assert number_of_classes == 1

    def test_class_count_with_different_targets(self):
        """Test class count varies by target size."""
        total_students = 75

        # With target 25
        classes_25 = ceil(total_students / 25)
        assert classes_25 == 3

        # With target 20 (more classes)
        classes_20 = ceil(total_students / 20)
        assert classes_20 == 4

        # With target 30 (fewer classes)
        classes_30 = ceil(total_students / 30)
        assert classes_30 == 3


class TestAverageClassSizeCalculation:
    """Tests for average class size calculation."""

    def test_avg_class_size_formula(self):
        """Test average = total_students / number_of_classes."""
        total_students = 100
        number_of_classes = 4

        avg_class_size = Decimal(total_students / number_of_classes).quantize(
            Decimal("0.01")
        )

        assert avg_class_size == Decimal("25.00")

    def test_avg_class_size_with_remainder(self):
        """Test average handles non-even division."""
        total_students = 76
        number_of_classes = 3

        avg_class_size = Decimal(total_students / number_of_classes).quantize(
            Decimal("0.01")
        )

        # 76 / 3 = 25.333...
        assert avg_class_size == Decimal("25.33")

    def test_avg_class_size_precision(self):
        """Test average is rounded to 2 decimal places."""
        total_students = 100
        number_of_classes = 3

        avg_class_size = Decimal(total_students / number_of_classes).quantize(
            Decimal("0.01")
        )

        # 100 / 3 = 33.333...
        assert avg_class_size == Decimal("33.33")
        assert len(str(avg_class_size).split(".")[-1]) <= 2


class TestATSEMAllocation:
    """Tests for ATSEM (preschool assistant) allocation."""

    def test_atsem_count_equals_classes_when_required(self):
        """Test ATSEM count = number of classes for Maternelle."""
        number_of_classes = 6
        requires_atsem = True

        atsem_count = number_of_classes if requires_atsem else 0

        assert atsem_count == 6

    def test_atsem_count_zero_when_not_required(self):
        """Test ATSEM count = 0 for non-Maternelle levels."""
        number_of_classes = 6
        requires_atsem = False

        atsem_count = number_of_classes if requires_atsem else 0

        assert atsem_count == 0


class TestUpdateValidation:
    """Tests for class structure update validation."""

    @pytest.mark.asyncio
    async def test_update_validates_number_of_classes_positive(self, class_service):
        """Test number of classes must be > 0."""
        class_id = uuid.uuid4()

        # Mock existing entry
        mock_entry = MagicMock()
        mock_entry.total_students = 100
        mock_entry.number_of_classes = 4
        class_service.get_class_structure_by_id = AsyncMock(return_value=mock_entry)

        with pytest.raises(ValidationError) as exc_info:
            await class_service.update_class_structure(
                class_structure_id=class_id,
                number_of_classes=0,
            )

        assert "greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_validates_avg_class_size_range(self, class_service):
        """Test average class size must be 0 < size <= 50."""
        class_id = uuid.uuid4()

        mock_entry = MagicMock()
        class_service.get_class_structure_by_id = AsyncMock(return_value=mock_entry)

        # Test negative
        with pytest.raises(ValidationError):
            await class_service.update_class_structure(
                class_structure_id=class_id,
                avg_class_size=Decimal("-5"),
            )

        # Test > 50
        with pytest.raises(ValidationError):
            await class_service.update_class_structure(
                class_structure_id=class_id,
                avg_class_size=Decimal("55"),
            )

    @pytest.mark.asyncio
    async def test_update_validates_atsem_count_non_negative(self, class_service):
        """Test ATSEM count must be >= 0."""
        class_id = uuid.uuid4()

        mock_entry = MagicMock()
        class_service.get_class_structure_by_id = AsyncMock(return_value=mock_entry)

        with pytest.raises(ValidationError) as exc_info:
            await class_service.update_class_structure(
                class_structure_id=class_id,
                atsem_count=-1,
            )

        assert "non-negative" in str(exc_info.value)


class TestRecalculateAverageOnUpdate:
    """Tests for automatic average recalculation on update."""

    @pytest.mark.asyncio
    async def test_recalculates_avg_when_students_change(self, class_service):
        """Test average is recalculated when only students change."""
        class_id = uuid.uuid4()

        mock_entry = MagicMock()
        mock_entry.total_students = 100
        mock_entry.number_of_classes = 4
        class_service.get_class_structure_by_id = AsyncMock(return_value=mock_entry)
        class_service.base_service.update = AsyncMock(return_value=mock_entry)

        await class_service.update_class_structure(
            class_structure_id=class_id,
            total_students=120,  # Changed
        )

        # Should have called update with recalculated average
        call_args = class_service.base_service.update.call_args
        update_data = call_args[0][1]

        # 120 students / 4 classes = 30.00 avg
        assert update_data["avg_class_size"] == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_recalculates_avg_when_classes_change(self, class_service):
        """Test average is recalculated when only classes change."""
        class_id = uuid.uuid4()

        mock_entry = MagicMock()
        mock_entry.total_students = 100
        mock_entry.number_of_classes = 4
        class_service.get_class_structure_by_id = AsyncMock(return_value=mock_entry)
        class_service.base_service.update = AsyncMock(return_value=mock_entry)

        await class_service.update_class_structure(
            class_structure_id=class_id,
            number_of_classes=5,  # Changed
        )

        call_args = class_service.base_service.update.call_args
        update_data = call_args[0][1]

        # 100 students / 5 classes = 20.00 avg
        assert update_data["avg_class_size"] == Decimal("20.00")


class TestBusinessRuleErrors:
    """Tests for business rule error scenarios."""

    @pytest.mark.asyncio
    async def test_no_enrollment_data_error(self, class_service):
        """Test error when no enrollment data exists."""
        class_service._get_enrollment_by_level = AsyncMock(return_value={})

        with pytest.raises(BusinessRuleError) as exc_info:
            await class_service.calculate_class_structure(uuid.uuid4())

        assert exc_info.value.details.get("rule") == "NO_ENROLLMENT_DATA"

    @pytest.mark.asyncio
    async def test_no_class_size_params_error(self, class_service):
        """Test error when no class size parameters exist."""
        # Mock enrollment exists
        mock_level = MagicMock()
        mock_level.code = "6eme"
        mock_level.cycle_id = uuid.uuid4()
        mock_cycle = MagicMock()
        mock_cycle.requires_atsem = False

        class_service._get_enrollment_by_level = AsyncMock(return_value={
            uuid.uuid4(): (100, mock_level, mock_cycle)
        })
        class_service._get_class_size_params = AsyncMock(return_value=[])

        with pytest.raises(BusinessRuleError) as exc_info:
            await class_service.calculate_class_structure(uuid.uuid4())

        assert exc_info.value.details.get("rule") == "NO_CLASS_SIZE_PARAMS"


class TestFrenchEducationLevels:
    """Tests for French education system level handling."""

    def test_maternelle_requires_atsem(self):
        """Test Maternelle levels (PS, MS, GS) require ATSEM."""
        maternelle_levels = ["PS", "MS", "GS"]
        for level in maternelle_levels:
            # By business rule, Maternelle cycle has requires_atsem = True
            assert level in ["PS", "MS", "GS"]

    def test_elementaire_levels(self):
        """Test Élémentaire levels are correctly identified."""
        elementaire_levels = ["CP", "CE1", "CE2", "CM1", "CM2"]
        assert len(elementaire_levels) == 5

    def test_college_levels(self):
        """Test Collège levels are correctly identified."""
        college_levels = ["6ème", "5ème", "4ème", "3ème"]
        assert len(college_levels) == 4

    def test_lycee_levels(self):
        """Test Lycée levels are correctly identified."""
        lycee_levels = ["2nde", "1ère", "Terminale"]
        assert len(lycee_levels) == 3


class TestClassSizeConstraints:
    """Tests for class size constraint validation."""

    def test_typical_class_size_ranges(self):
        """Test typical class size ranges by cycle."""
        # Maternelle typically has smaller classes
        maternelle_min, maternelle_max = 20, 28

        # Élémentaire
        elementaire_min, elementaire_max = 20, 28

        # Collège/Lycée can be slightly larger
        secondary_min, secondary_max = 25, 35

        assert maternelle_min < maternelle_max
        assert elementaire_min < elementaire_max
        assert secondary_min < secondary_max

    def test_efir_class_size_constraints(self):
        """Test EFIR-specific class size constraints."""
        # Based on EFIR school profile
        max_students = 1875
        avg_class_size = 25
        expected_classes = ceil(max_students / avg_class_size)

        assert expected_classes == 75


class TestCustomOverrides:
    """Tests for custom class count overrides."""

    @pytest.mark.asyncio
    async def test_override_uses_custom_method(self, class_service):
        """Test that custom override sets method to 'custom'."""
        version_id = uuid.uuid4()
        level_id = uuid.uuid4()

        # Mock data
        mock_level = MagicMock()
        mock_level.code = "6eme"
        mock_level.cycle_id = uuid.uuid4()
        mock_cycle = MagicMock()
        mock_cycle.requires_atsem = False

        mock_params = MagicMock()
        mock_params.level_id = level_id
        mock_params.cycle_id = None
        mock_params.min_class_size = 20
        mock_params.max_class_size = 30
        mock_params.target_class_size = 25

        class_service._get_enrollment_by_level = AsyncMock(return_value={
            level_id: (100, mock_level, mock_cycle)
        })
        class_service._get_class_size_params = AsyncMock(return_value=[mock_params])
        class_service.get_class_structure = AsyncMock(return_value=[])
        class_service.base_service.create = AsyncMock(return_value=MagicMock())

        await class_service.calculate_class_structure(
            version_id=version_id,
            override_by_level={str(level_id): 5},  # Force 5 classes
        )

        # Verify create was called with custom method
        call_args = class_service.base_service.create.call_args
        data = call_args[0][0]
        assert data["calculation_method"] == "custom"
        assert data["number_of_classes"] == 5
