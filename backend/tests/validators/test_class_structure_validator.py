"""Tests for class structure validators."""

import uuid
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.validators.class_structure import (
    ClassStructureValidationError,
    validate_class_size_params,
    validate_class_structure,
    validate_class_structure_sync,
    validate_enrollment_distribution,
)
from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    BudgetVersion,
    BudgetVersionStatus,
    ClassSizeParam,
)
from app.services.exceptions import ValidationError


class TestClassSizeValidation:
    """Tests for class size parameter validation."""

    def test_validate_class_size_params_valid(self):
        """Test valid class size parameters."""
        # Should not raise
        validate_class_size_params(
            min_size=15,
            target_size=22,
            max_size=28
        )

    def test_validate_class_size_params_min_equals_target(self):
        """Test min cannot equal target."""
        with pytest.raises(ValidationError, match="min < target <= max"):
            validate_class_size_params(
                min_size=22,
                target_size=22,
                max_size=28
            )

    def test_validate_class_size_params_target_exceeds_max(self):
        """Test target cannot exceed max."""
        with pytest.raises(ValidationError, match="min < target <= max"):
            validate_class_size_params(
                min_size=15,
                target_size=30,
                max_size=28
            )

    def test_validate_class_size_params_min_greater_than_target(self):
        """Test min cannot be greater than target."""
        with pytest.raises(ValidationError, match="min < target <= max"):
            validate_class_size_params(
                min_size=25,
                target_size=22,
                max_size=28
            )


class TestEnrollmentDistributionValidation:
    """Tests for enrollment distribution validation."""

    def test_validate_enrollment_distribution_valid(self):
        """Test valid enrollment distribution."""
        # Should not raise
        validate_enrollment_distribution(
            total_students=100,
            distributions={"French": 60, "Saudi": 30, "Other": 10}
        )

    def test_validate_enrollment_distribution_mismatch(self):
        """Test enrollment distribution sum mismatch."""
        with pytest.raises(ValidationError, match="must equal total"):
            validate_enrollment_distribution(
                total_students=100,
                distributions={"French": 60, "Saudi": 30, "Other": 5}  # Sum = 95
            )

    def test_validate_enrollment_distribution_negative(self):
        """Test negative enrollment values."""
        with pytest.raises(ValidationError, match="cannot contain negative values"):
            validate_enrollment_distribution(
                total_students=100,
                distributions={"French": 60, "Saudi": 50, "Other": -10}
            )


class TestClassStructureValidationSync:
    """Tests for synchronous class structure validation."""

    def test_validate_class_structure_sync_valid(self):
        """Test valid class structure passes validation."""
        # Should not raise
        validate_class_structure_sync(
            min_class_size=18,
            max_class_size=30,
            avg_class_size=Decimal("25.0"),
            level_name="6ème",
            number_of_classes=6,
            total_students=150
        )

    def test_validate_class_structure_sync_below_minimum(self):
        """Test class structure below minimum raises error."""
        with pytest.raises(ClassStructureValidationError, match="below minimum"):
            validate_class_structure_sync(
                min_class_size=18,
                max_class_size=30,
                avg_class_size=Decimal("15.0"),
                level_name="6ème",
                number_of_classes=10,
                total_students=150
            )

    def test_validate_class_structure_sync_above_maximum(self):
        """Test class structure above maximum raises error."""
        with pytest.raises(ClassStructureValidationError, match="exceeds maximum"):
            validate_class_structure_sync(
                min_class_size=18,
                max_class_size=30,
                avg_class_size=Decimal("35.0"),
                level_name="6ème",
                number_of_classes=4,
                total_students=140
            )


class TestClassStructureValidationAsync:
    """Tests for async class structure validation with database."""

    @pytest.mark.asyncio
    async def test_validate_class_structure_level_not_found(self, db_session: AsyncSession):
        """Test validation fails when level doesn't exist."""
        fake_level_id = uuid.uuid4()

        with pytest.raises(ClassStructureValidationError, match="not found"):
            await validate_class_structure(
                session=db_session,
                level_id=fake_level_id,
                avg_class_size=Decimal("25.0"),
                number_of_classes=6,
                total_students=150
            )

    @pytest.mark.asyncio
    async def test_validate_class_structure_no_params_allows_any_size(
        self, db_session: AsyncSession, test_user_id
    ):
        """Test validation passes when no class size parameters are configured."""
        # Create cycle and level without class size params
        cycle = AcademicCycle(
            id=uuid.uuid4(),
            code="COLLEGE",
            name_en="Middle School",
            name_fr="Collège",
            sort_order=3,
            requires_atsem=False
        )
        db_session.add(cycle)

        level = AcademicLevel(
            id=uuid.uuid4(),
            cycle_id=cycle.id,
            code="6EME",
            name_en="6th Grade",
            name_fr="6ème",
            sort_order=1,
            is_secondary=True
        )
        db_session.add(level)
        await db_session.flush()

        # Should not raise (no params = no constraints)
        await validate_class_structure(
            session=db_session,
            level_id=level.id,
            avg_class_size=Decimal("50.0"),  # Any size is OK
            number_of_classes=3,
            total_students=150
        )

    @pytest.mark.asyncio
    async def test_validate_class_structure_level_specific_param(
        self, db_session: AsyncSession, test_user_id
    ):
        """Test validation uses level-specific parameters."""
        # Create budget version
        budget_version = BudgetVersion(
            id=uuid.uuid4(),
            name="FY2025 Test v1",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            is_baseline=False,
            notes="Test budget for validator",
            created_by_id=test_user_id
        )
        db_session.add(budget_version)

        # Create cycle, level, and level-specific class size param
        cycle = AcademicCycle(
            id=uuid.uuid4(),
            code="COLLEGE",
            name_en="Middle School",
            name_fr="Collège",
            sort_order=3,
            requires_atsem=False
        )
        db_session.add(cycle)

        level = AcademicLevel(
            id=uuid.uuid4(),
            cycle_id=cycle.id,
            code="6EME",
            name_en="6th Grade",
            name_fr="6ème",
            sort_order=1,
            is_secondary=True
        )
        db_session.add(level)

        # Level-specific parameter
        param = ClassSizeParam(
            id=uuid.uuid4(),
            budget_version_id=budget_version.id,
            level_id=level.id,
            cycle_id=None,
            min_class_size=18,
            target_class_size=25,
            max_class_size=30
        )
        db_session.add(param)
        await db_session.flush()

        # Valid size - should not raise
        await validate_class_structure(
            session=db_session,
            level_id=level.id,
            avg_class_size=Decimal("25.0"),
            number_of_classes=6,
            total_students=150
        )

        # Below minimum - should raise
        with pytest.raises(ClassStructureValidationError, match="below minimum"):
            await validate_class_structure(
                session=db_session,
                level_id=level.id,
                avg_class_size=Decimal("15.0"),
                number_of_classes=10,
                total_students=150
            )

        # Above maximum - should raise
        with pytest.raises(ClassStructureValidationError, match="exceeds maximum"):
            await validate_class_structure(
                session=db_session,
                level_id=level.id,
                avg_class_size=Decimal("35.0"),
                number_of_classes=4,
                total_students=140
            )

    @pytest.mark.asyncio
    async def test_validate_class_structure_cycle_level_param_fallback(
        self, db_session: AsyncSession, test_user_id
    ):
        """Test validation falls back to cycle-level parameters."""
        # Create budget version
        budget_version = BudgetVersion(
            id=uuid.uuid4(),
            name="FY2025 Test v1",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            is_baseline=False,
            notes="Test budget for validator",
            created_by_id=test_user_id
        )
        db_session.add(budget_version)

        # Create cycle with cycle-level class size param
        cycle = AcademicCycle(
            id=uuid.uuid4(),
            code="COLLEGE",
            name_en="Middle School",
            name_fr="Collège",
            sort_order=3,
            requires_atsem=False
        )
        db_session.add(cycle)

        level = AcademicLevel(
            id=uuid.uuid4(),
            cycle_id=cycle.id,
            code="5EME",
            name_en="7th Grade",
            name_fr="5ème",
            sort_order=2,
            is_secondary=True
        )
        db_session.add(level)

        # Cycle-level parameter (no level_id)
        cycle_param = ClassSizeParam(
            id=uuid.uuid4(),
            budget_version_id=budget_version.id,
            cycle_id=cycle.id,
            level_id=None,  # Cycle-level parameter
            min_class_size=20,
            target_class_size=26,
            max_class_size=32
        )
        db_session.add(cycle_param)
        await db_session.flush()

        # Valid size using cycle param - should not raise
        await validate_class_structure(
            session=db_session,
            level_id=level.id,
            avg_class_size=Decimal("28.0"),
            number_of_classes=5,
            total_students=140
        )

        # Below cycle minimum - should raise
        with pytest.raises(ClassStructureValidationError, match="below minimum"):
            await validate_class_structure(
                session=db_session,
                level_id=level.id,
                avg_class_size=Decimal("18.0"),
                number_of_classes=8,
                total_students=144
            )
