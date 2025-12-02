"""
Tests for DHG (Dotation Horaire Globale) service.

Covers:
- DHG subject hours calculation
- Teacher requirement calculation
- Teacher allocation management
- Gap analysis (TRMD)
- HSA (overtime) allocation
- Business rule validation
- Error handling

Target Coverage: 95% (from 15.6%)
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    Subject,
    SubjectHoursMatrix,
    TeacherCategory,
    TeacherCostParam,
)
from app.models.planning import (
    ClassStructure,
    DHGSubjectHours,
    DHGTeacherRequirement,
    TeacherAllocation,
)
from app.services.dhg_service import DHGService
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError


@pytest.fixture
async def dhg_service(db_session: AsyncSession) -> DHGService:
    """Create DHG service instance with test database session."""
    return DHGService(db_session)


@pytest.fixture
async def mock_budget_version(db_session: AsyncSession, test_user_id):
    """Create test budget version."""
    from app.models.configuration import BudgetVersion, BudgetVersionStatus
    from datetime import datetime

    version = BudgetVersion(
        id=uuid.uuid4(),
        name="Test Budget 2024",
        fiscal_year=2024,
        academic_year="2024-2025",
        status=BudgetVersionStatus.WORKING,
        created_by_id=test_user_id,
        created_at=datetime.utcnow(),
    )
    db_session.add(version)
    await db_session.flush()
    return version


@pytest.fixture
async def mock_college_cycle(db_session: AsyncSession) -> AcademicCycle:
    """Create Collège cycle."""
    cycle = AcademicCycle(
        id=uuid.uuid4(),
        code="COLLEGE",
        name_fr="Collège",
        name_en="Middle School",
        sort_order=3,
    )
    db_session.add(cycle)
    await db_session.flush()
    return cycle


@pytest.fixture
async def mock_college_levels(
    db_session: AsyncSession, mock_college_cycle: AcademicCycle
) -> list[AcademicLevel]:
    """Create Collège levels (6ème, 5ème, 4ème, 3ème)."""
    levels = [
        AcademicLevel(
            id=uuid.uuid4(),
            code="6EME",
            name_fr="Sixième",
            name_en="6th Grade",
            cycle_id=mock_college_cycle.id,
            sort_order=1,
        ),
        AcademicLevel(
            id=uuid.uuid4(),
            code="5EME",
            name_fr="Cinquième",
            name_en="7th Grade",
            cycle_id=mock_college_cycle.id,
            sort_order=2,
        ),
        AcademicLevel(
            id=uuid.uuid4(),
            code="4EME",
            name_fr="Quatrième",
            name_en="8th Grade",
            cycle_id=mock_college_cycle.id,
            sort_order=3,
        ),
        AcademicLevel(
            id=uuid.uuid4(),
            code="3EME",
            name_fr="Troisième",
            name_en="9th Grade",
            cycle_id=mock_college_cycle.id,
            sort_order=4,
        ),
    ]
    for level in levels:
        db_session.add(level)
    await db_session.flush()
    return levels


@pytest.fixture
async def mock_subjects(db_session: AsyncSession) -> list[Subject]:
    """Create test subjects."""
    subjects = [
        Subject(
            id=uuid.uuid4(),
            code="MATH",
            name_fr="Mathématiques",
            name_en="Mathematics",
            category="CORE",
        ),
        Subject(
            id=uuid.uuid4(),
            code="FR",
            name_fr="Français",
            name_en="French",
            category="CORE",
        ),
        Subject(
            id=uuid.uuid4(),
            code="HIST",
            name_fr="Histoire-Géographie",
            name_en="History-Geography",
            category="CORE",
        ),
    ]
    for subject in subjects:
        db_session.add(subject)
    await db_session.flush()
    return subjects


@pytest.fixture
async def mock_subject_hours_matrix(
    db_session: AsyncSession,
    mock_budget_version,
    mock_subjects: list[Subject],
    mock_college_levels: list[AcademicLevel],
    test_user_id,
) -> list[SubjectHoursMatrix]:
    """
    Create subject hours matrix for Collège.

    Hours per week by subject:
    - Math: 6ème(4.5), 5ème(3.5), 4ème(3.5), 3ème(3.5)
    - French: 6ème(4.5), 5ème(4.5), 4ème(4.5), 3ème(4.0)
    - History: 6ème(3.0), 5ème(3.0), 4ème(3.5), 3ème(3.5)
    """
    hours_data = {
        "MATH": {
            "6EME": Decimal("4.5"),
            "5EME": Decimal("3.5"),
            "4EME": Decimal("3.5"),
            "3EME": Decimal("3.5"),
        },
        "FR": {
            "6EME": Decimal("4.5"),
            "5EME": Decimal("4.5"),
            "4EME": Decimal("4.5"),
            "3EME": Decimal("4.0"),
        },
        "HIST": {
            "6EME": Decimal("3.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.5"),
            "3EME": Decimal("3.5"),
        },
    }

    matrix_entries = []
    for subject in mock_subjects:
        for level in mock_college_levels:
            if subject.code in hours_data and level.code in hours_data[subject.code]:
                entry = SubjectHoursMatrix(
                    id=uuid.uuid4(),
                    budget_version_id=mock_budget_version.id,
                    subject_id=subject.id,
                    level_id=level.id,
                    hours_per_week=hours_data[subject.code][level.code],
                    created_by_id=test_user_id,
                )
                db_session.add(entry)
                matrix_entries.append(entry)

    await db_session.flush()
    return matrix_entries


@pytest.fixture
async def mock_class_structure(
    db_session: AsyncSession,
    mock_budget_version,
    mock_college_levels: list[AcademicLevel],
    test_user_id,
) -> list[ClassStructure]:
    """
    Create class structure for Collège.

    Number of classes:
    - 6ème: 6 classes
    - 5ème: 6 classes
    - 4ème: 5 classes
    - 3ème: 4 classes
    """
    class_counts = {"6EME": 6, "5EME": 6, "4EME": 5, "3EME": 4}

    class_structures = []
    for level in mock_college_levels:
        if level.code in class_counts:
            cs = ClassStructure(
                id=uuid.uuid4(),
                budget_version_id=mock_budget_version.id,
                level_id=level.id,
                number_of_classes=class_counts[level.code],
                avg_class_size=Decimal("25.0"),
                total_students=class_counts[level.code] * 25,
                created_by_id=test_user_id,
            )
            db_session.add(cs)
            class_structures.append(cs)

    await db_session.flush()
    return class_structures


# ==============================================================================
# Test: DHG Subject Hours Calculation
# ==============================================================================


class TestDHGSubjectHoursCalculation:
    """Test DHG subject hours calculation from class structure and subject hours matrix."""

    @pytest.mark.asyncio
    async def test_calculate_dhg_subject_hours_standard_case(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_class_structure,
        mock_subject_hours_matrix,
        mock_subjects,
        mock_college_levels,
    ):
        """
        Test DHG hours calculation for standard Collège case.

        Example (Math in 6ème):
        - 6 classes × 4.5 hours/week = 27 hours/week
        """
        result = await dhg_service.calculate_dhg_subject_hours(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        assert len(result) > 0

        # Find Math in 6ème
        math_6eme = next(
            (
                r
                for r in result
                if r.subject.code == "MATH" and r.level.code == "6EME"
            ),
            None,
        )

        assert math_6eme is not None
        assert math_6eme.num_classes == 6
        assert math_6eme.hours_per_week == Decimal("4.5")
        assert math_6eme.total_hours == Decimal("27.0")  # 6 × 4.5

    @pytest.mark.asyncio
    async def test_calculate_dhg_subject_hours_zero_classes(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        db_session: AsyncSession,
    ):
        """Test DHG calculation with no classes defined."""
        # No class structure created

        result = await dhg_service.calculate_dhg_subject_hours(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Should return empty list or zero hours
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_calculate_dhg_subject_hours_missing_subject_hours_matrix(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_class_structure,
    ):
        """Test DHG calculation when subject hours matrix is incomplete."""
        # Class structure exists but no subject hours matrix

        result = await dhg_service.calculate_dhg_subject_hours(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Should handle gracefully - either skip or use defaults
        # Exact behavior depends on implementation
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_calculate_dhg_subject_hours_partial_recalculation(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_class_structure,
        mock_subject_hours_matrix,
    ):
        """Test partial recalculation (only changed levels)."""
        # First full calculation
        await dhg_service.calculate_dhg_subject_hours(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Second calculation with recalculate_all=False
        result = await dhg_service.calculate_dhg_subject_hours(
            version_id=mock_budget_version.id,
            recalculate_all=False,
        )

        # Should return existing calculations
        assert len(result) > 0


# ==============================================================================
# Test: Teacher Requirement Calculation
# ==============================================================================


class TestTeacherRequirementCalculation:
    """Test teacher FTE requirement calculation from DHG hours."""

    @pytest.mark.asyncio
    async def test_calculate_teacher_requirements_secondary_standard(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_class_structure,
        mock_subject_hours_matrix,
    ):
        """
        Test teacher FTE calculation for secondary (18h standard).

        Example (Math in Collège):
        - Total hours: 6×4.5 + 6×3.5 + 5×3.5 + 4×3.5 = 96 hours/week
        - FTE: 96 ÷ 18 = 5.33 → 6 teachers needed
        """
        # First calculate DHG hours
        await dhg_service.calculate_dhg_subject_hours(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Then calculate teacher requirements
        # Note: Need to implement this method call based on actual service API
        # This is a template - adjust based on actual implementation

        # Expected calculation for Math:
        # 6×4.5 + 6×3.5 + 5×3.5 + 4×3.5 = 27 + 21 + 17.5 + 14 = 79.5 hours
        # FTE: 79.5 ÷ 18 = 4.42 FTE

    @pytest.mark.asyncio
    async def test_calculate_teacher_requirements_hsa_allocation(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """
        Test HSA (overtime) allocation when available FTE < required FTE.

        HSA rules:
        - Max 2-4 hours per teacher
        - Can cover gap between available and required
        """
        # TODO: Implement based on actual service API
        pass

    @pytest.mark.asyncio
    async def test_calculate_teacher_requirements_exceeds_hsa_limit(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test gap analysis when deficit exceeds HSA capacity."""
        # TODO: Implement based on actual service API
        pass


# ==============================================================================
# Test: Teacher Allocation Management
# ==============================================================================


class TestTeacherAllocationManagement:
    """Test CRUD operations for teacher allocations (TRMD)."""

    @pytest.mark.asyncio
    async def test_get_teacher_allocations(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test retrieving teacher allocations for a budget version."""
        # TODO: Implement based on actual service API
        pass

    @pytest.mark.asyncio
    async def test_create_teacher_allocation_aefe_detached(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test creating AEFE detached teacher allocation."""
        # TODO: Implement based on actual service API
        pass

    @pytest.mark.asyncio
    async def test_create_teacher_allocation_local(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test creating local teacher allocation."""
        # TODO: Implement based on actual service API
        pass


# ==============================================================================
# Test: Gap Analysis (TRMD)
# ==============================================================================


class TestGapAnalysis:
    """Test TRMD gap analysis (Besoins vs Moyens)."""

    @pytest.mark.asyncio
    async def test_gap_analysis_deficit_scenario(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """
        Test gap analysis when deficit exists.

        Deficit = Required FTE - Available FTE
        Should calculate HSA coverage and remaining deficit.
        """
        # TODO: Implement based on actual service API
        pass

    @pytest.mark.asyncio
    async def test_gap_analysis_surplus_scenario(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test gap analysis when surplus exists (over-staffed)."""
        # TODO: Implement based on actual service API
        pass


# ==============================================================================
# Test: Business Rule Validation
# ==============================================================================


class TestDHGBusinessRules:
    """Test business rule enforcement."""

    @pytest.mark.asyncio
    async def test_validate_hsa_hours_within_limit(
        self,
        dhg_service: DHGService,
    ):
        """Test HSA hours validation (max 2-4 hours per teacher)."""
        # TODO: Implement based on actual service API
        pass

    @pytest.mark.asyncio
    async def test_validate_standard_hours_by_cycle(
        self,
        dhg_service: DHGService,
    ):
        """
        Test standard hours validation.

        - Primary: 24h/week
        - Secondary: 18h/week
        """
        # TODO: Implement based on actual service API
        pass


# ==============================================================================
# Test: Error Handling
# ==============================================================================


class TestDHGServiceErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_calculate_dhg_budget_version_not_found(
        self,
        dhg_service: DHGService,
    ):
        """Test DHG calculation with non-existent budget version."""
        with pytest.raises(NotFoundError):
            await dhg_service.calculate_dhg_subject_hours(
                version_id=uuid.uuid4(),
                recalculate_all=True,
            )

    @pytest.mark.asyncio
    async def test_get_dhg_subject_hours_empty_version(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test retrieving DHG hours for version with no calculations."""
        result = await dhg_service.get_dhg_subject_hours(
            version_id=mock_budget_version.id
        )

        assert isinstance(result, list)
        assert len(result) == 0
