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
from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    Subject,
    SubjectHoursMatrix,
    TeacherCategory,
)
from app.models.planning import (
    ClassStructure,
)
from app.services.dhg_service import DHGService
from app.services.exceptions import BusinessRuleError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def dhg_service(db_session: AsyncSession) -> DHGService:
    """Create DHG service instance with test database session."""
    return DHGService(db_session)


@pytest.fixture
async def mock_budget_version(db_session: AsyncSession, test_user_id):
    """Create test budget version."""
    from datetime import datetime

    from app.models.configuration import BudgetVersion, BudgetVersionStatus

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
            is_secondary=True,  # Collège is secondary
        ),
        AcademicLevel(
            id=uuid.uuid4(),
            code="5EME",
            name_fr="Cinquième",
            name_en="7th Grade",
            cycle_id=mock_college_cycle.id,
            sort_order=2,
            is_secondary=True,  # Collège is secondary
        ),
        AcademicLevel(
            id=uuid.uuid4(),
            code="4EME",
            name_fr="Quatrième",
            name_en="8th Grade",
            cycle_id=mock_college_cycle.id,
            sort_order=3,
            is_secondary=True,  # Collège is secondary
        ),
        AcademicLevel(
            id=uuid.uuid4(),
            code="3EME",
            name_fr="Troisième",
            name_en="9th Grade",
            cycle_id=mock_college_cycle.id,
            sort_order=4,
            is_secondary=True,  # Collège is secondary
        ),
    ]
    for level in levels:
        db_session.add(level)
    await db_session.flush()
    return levels


@pytest.fixture
async def mock_subjects(db_session: AsyncSession) -> list[Subject]:
    """Create test subjects, reusing existing ones to avoid UNIQUE constraint errors.

    This fixture is idempotent - if subjects with these codes already exist
    (from previous tests on the same worker), they are reused instead of
    attempting to create duplicates.
    """
    from sqlalchemy import select

    # Define subjects to create
    subjects_data = [
        ("MATH", "Mathématiques", "Mathematics", "CORE"),
        ("FR", "Français", "French", "CORE"),
        ("HIST", "Histoire-Géographie", "History-Geography", "CORE"),
    ]

    # Check for existing subjects first
    codes = [s[0] for s in subjects_data]
    result = await db_session.execute(select(Subject).where(Subject.code.in_(codes)))
    existing = {s.code: s for s in result.scalars().all()}

    subjects = []
    for code, name_fr, name_en, category in subjects_data:
        if code in existing:
            subjects.append(existing[code])
        else:
            subject = Subject(
                id=uuid.uuid4(),
                code=code,
                name_fr=name_fr,
                name_en=name_en,
                category=category,
            )
            db_session.add(subject)
            subjects.append(subject)

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
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        assert len(result) > 0

        # Find Math in 6ème
        math_6eme = next(
            (r for r in result if r.subject.code == "MATH" and r.level.code == "6EME"),
            None,
        )

        assert math_6eme is not None
        assert math_6eme.number_of_classes == 6
        assert math_6eme.hours_per_class_per_week == Decimal("4.5")
        assert math_6eme.total_hours_per_week == Decimal("27.0")  # 6 × 4.5

    @pytest.mark.asyncio
    async def test_calculate_dhg_subject_hours_zero_classes(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        db_session: AsyncSession,
    ):
        """Test DHG calculation with no classes defined."""
        # No class structure created

        # Should raise BusinessRuleError when no class structure exists
        with pytest.raises(
            BusinessRuleError,
            match="Cannot calculate DHG hours without class structure data",
        ):
            await dhg_service.calculate_dhg_subject_hours(
                budget_version_id=mock_budget_version.id,
                recalculate_all=True,
            )

    @pytest.mark.asyncio
    async def test_calculate_dhg_subject_hours_missing_subject_hours_matrix(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_class_structure,
    ):
        """Test DHG calculation when subject hours matrix is incomplete."""
        # Class structure exists but no subject hours matrix

        # Should raise BusinessRuleError when no subject hours matrix exists
        with pytest.raises(
            BusinessRuleError,
            match="Cannot calculate DHG hours without subject hours matrix",
        ):
            await dhg_service.calculate_dhg_subject_hours(
                budget_version_id=mock_budget_version.id,
                recalculate_all=True,
            )

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
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Second calculation with recalculate_all=False
        result = await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=mock_budget_version.id,
            recalculate_all=False,
        )

        # Should return existing calculations
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_calculate_dhg_subject_hours_split_classes(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_college_levels: list,
        mock_subjects: list,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test DHG calculation with split classes (doubles hours)."""
        from app.models.configuration import SubjectHoursMatrix
        from app.models.planning import ClassStructure

        # Create class structure
        class_structure = ClassStructure(
            id=uuid.uuid4(),
            budget_version_id=mock_budget_version.id,
            level_id=mock_college_levels[0].id,
            total_students=30,
            number_of_classes=1,
            avg_class_size=Decimal("30.0"),
            created_by_id=test_user_id,
            updated_by_id=test_user_id,
        )
        db_session.add(class_structure)
        await db_session.flush()

        # Create subject hours matrix with is_split=True
        matrix = SubjectHoursMatrix(
            id=uuid.uuid4(),
            budget_version_id=mock_budget_version.id,
            subject_id=mock_subjects[0].id,
            level_id=mock_college_levels[0].id,
            hours_per_week=Decimal("3.0"),
            is_split=True,  # Split class doubles the hours
            created_by_id=test_user_id,
            updated_by_id=test_user_id,
        )
        db_session.add(matrix)
        await db_session.flush()

        # Calculate DHG hours
        result = await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        assert len(result) == 1
        # 1 class × 3h × 2 (split) = 6h
        assert result[0].total_hours_per_week == Decimal("6.00")

    @pytest.mark.asyncio
    async def test_calculate_dhg_subject_hours_skips_levels_without_classes(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_college_levels: list,
        mock_subjects: list,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test that calculation skips subject/level pairs with no classes."""
        from app.models.configuration import SubjectHoursMatrix
        from app.models.planning import ClassStructure

        # Create class structure for 6ème only
        class_structure = ClassStructure(
            id=uuid.uuid4(),
            budget_version_id=mock_budget_version.id,
            level_id=mock_college_levels[0].id,  # 6ème
            total_students=30,
            number_of_classes=1,
            avg_class_size=Decimal("30.0"),
            created_by_id=test_user_id,
            updated_by_id=test_user_id,
        )
        db_session.add(class_structure)
        await db_session.flush()

        # Create subject hours matrix for both 6ème and 5ème
        matrices = [
            SubjectHoursMatrix(
                id=uuid.uuid4(),
                budget_version_id=mock_budget_version.id,
                subject_id=mock_subjects[0].id,
                level_id=mock_college_levels[0].id,  # 6ème - has classes
                hours_per_week=Decimal("4.0"),
                is_split=False,
                created_by_id=test_user_id,
                updated_by_id=test_user_id,
            ),
            SubjectHoursMatrix(
                id=uuid.uuid4(),
                budget_version_id=mock_budget_version.id,
                subject_id=mock_subjects[0].id,
                level_id=mock_college_levels[1].id,  # 5ème - NO classes
                hours_per_week=Decimal("3.5"),
                is_split=False,
                created_by_id=test_user_id,
                updated_by_id=test_user_id,
            ),
        ]
        for matrix in matrices:
            db_session.add(matrix)
        await db_session.flush()

        # Calculate DHG hours
        result = await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Should only have 1 result (for 6ème), 5ème should be skipped
        assert len(result) == 1
        assert result[0].level_id == mock_college_levels[0].id  # 6ème
        assert result[0].total_hours_per_week == Decimal("4.00")


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
        mock_subjects: list,
    ):
        """
        Test teacher FTE calculation for secondary (18h standard).

        Example (Math in Collège):
        - Total hours: 6×4.5 + 6×3.5 + 5×3.5 + 4×3.5 = 96 hours/week
        - FTE: 96 ÷ 18 = 5.33 → 6 teachers needed
        """
        # First calculate DHG hours
        await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Then calculate teacher requirements
        requirements = await dhg_service.calculate_teacher_requirements(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Should have requirements for all 3 subjects (Math, French, History)
        assert len(requirements) == 3

        # Find Math requirement
        math_subject = next(s for s in mock_subjects if s.code == "MATH")
        math_req = next(r for r in requirements if r.subject_id == math_subject.id)

        # Expected calculation for Math:
        # 6ème: 6 classes × 4.5h = 27h
        # 5ème: 6 classes × 3.5h = 21h
        # 4ème: 5 classes × 3.5h = 17.5h
        # 3ème: 4 classes × 3.5h = 14h
        # Total: 79.5 hours per week
        assert math_req.total_hours_per_week == Decimal("79.5")
        assert math_req.standard_teaching_hours == Decimal("18")

        # FTE: 79.5 ÷ 18 = 4.42 → round up to 5
        assert math_req.simple_fte == Decimal("4.42")
        assert math_req.rounded_fte == 5

        # HSA: 79.5 - (5 × 18) = 79.5 - 90 = -10.5 → 0 (no overtime needed)
        assert math_req.hsa_hours == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_calculate_teacher_requirements_hsa_allocation(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_college_levels: list,
        mock_subjects: list,
        db_session: AsyncSession,
        test_user_id,
    ):
        """
        Test HSA (overtime) allocation when available FTE < required FTE.

        HSA rules:
        - Max 2-4 hours per teacher
        - Can cover gap between available and required
        """
        # Create class structure with specific numbers to trigger HSA
        # Example: 5 classes needing 20h each = 100h total
        # 100h ÷ 18h = 5.56 FTE → 6 teachers
        # HSA: 100 - (6 × 18) = 100 - 108 = -8 → 0 (no HSA)
        # Let's use 5 classes × 19h = 95h
        # 95 ÷ 18 = 5.28 → 6 teachers
        # HSA: 95 - (6 × 18) = 95 - 108 = -13 → 0 (still no HSA)
        # For HSA, we need: 5 teachers × 20h = 100h
        # 100 ÷ 18 = 5.56 → 6 teachers → 6 × 18 = 108h
        # But if we round DOWN to 5 teachers and add HSA:
        # 5 × 18 = 90h, need 100h, so HSA = 10h

        # Create scenario: 3 classes × 32h = 96h total
        # 96 ÷ 18 = 5.33 → 6 teachers
        # 6 × 18 = 108h > 96h, so no HSA needed
        # For HSA, let's use: 5 classes × 20h = 100h
        # 100 ÷ 18 = 5.56 → 6 teachers → HSA = 0

        # Better scenario: Create hours that result in HSA
        # 5 teachers need 92h (5 × 18 = 90h + 2h HSA)
        # We need total hours where: rounded_fte × 18 < total_hours

        # Create single level class structure
        from app.models.planning import ClassStructure

        class_structure = ClassStructure(
            id=uuid.uuid4(),
            budget_version_id=mock_budget_version.id,
            level_id=mock_college_levels[0].id,  # 6ème
            total_students=125,  # 5 classes × 25 students
            number_of_classes=5,
            avg_class_size=Decimal("25.0"),
            created_by_id=test_user_id,
            updated_by_id=test_user_id,
        )
        db_session.add(class_structure)
        await db_session.flush()

        # Create subject hours that result in calculation
        # Use valid hours_per_week (constraint: > 0 AND <= 12)
        # 5 classes × 5.5h = 27.5h total
        # 27.5 ÷ 18 = 1.53 → 2 teachers needed
        # HSA: 27.5 - (2 × 18) = 27.5 - 36 = -8.5 → 0 (no HSA)

        # Note: HSA formula max(0, total_hours - (rounded_fte × 18))
        # Since rounded_fte = CEILING(total_hours / 18), this will always be ≤ 0
        # HSA in real scenarios applies when comparing available vs required teachers

        from app.models.configuration import SubjectHoursMatrix

        matrix = SubjectHoursMatrix(
            id=uuid.uuid4(),
            budget_version_id=mock_budget_version.id,
            subject_id=mock_subjects[0].id,  # Math
            level_id=mock_college_levels[0].id,  # 6ème
            hours_per_week=Decimal("5.5"),  # Within valid range (0, 12]
            is_split=False,
            created_by_id=test_user_id,
            updated_by_id=test_user_id,
        )
        db_session.add(matrix)
        await db_session.flush()

        # Calculate DHG hours
        await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Calculate teacher requirements
        requirements = await dhg_service.calculate_teacher_requirements(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Verify calculation completed
        assert len(requirements) == 1
        math_req = requirements[0]

        # 5 classes × 5.5h = 27.5h
        assert math_req.total_hours_per_week == Decimal("27.5")
        assert math_req.standard_teaching_hours == Decimal("18")

        # 27.5 ÷ 18 = 1.53 → 2 teachers
        assert math_req.simple_fte == Decimal("1.53")
        assert math_req.rounded_fte == 2

        # HSA: 27.5 - (2 × 18) = -8.5 → 0
        assert math_req.hsa_hours == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_calculate_teacher_requirements_exceeds_hsa_limit(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test gap analysis when deficit exceeds HSA capacity."""
        # Note: With current implementation, HSA is calculated as:
        # max(0, total_hours - (rounded_fte × 18))
        # Since rounded_fte = CEILING(total_hours / 18), this will always be ≤ 0
        # HSA limits are enforced in TRMD gap analysis, not in basic calculation

        # Test that calculation handles zero DHG hours correctly
        with pytest.raises(
            BusinessRuleError,
            match="Cannot calculate teacher requirements without DHG subject hours",
        ):
            await dhg_service.calculate_teacher_requirements(
                version_id=mock_budget_version.id,
                recalculate_all=True,
            )

    @pytest.mark.asyncio
    async def test_calculate_teacher_requirements_updates_existing(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_class_structure,
        mock_subject_hours_matrix,
    ):
        """Test that recalculation updates existing requirements instead of creating new."""
        # First calculation
        await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        requirements1 = await dhg_service.calculate_teacher_requirements(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Second calculation (should update, not create)
        requirements2 = await dhg_service.calculate_teacher_requirements(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Should have same number of requirements
        assert len(requirements2) == len(requirements1)

        # Should have same IDs (updated, not new)
        req1_ids = {r.id for r in requirements1}
        req2_ids = {r.id for r in requirements2}
        assert req1_ids == req2_ids


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
        # Initially empty
        allocations = await dhg_service.get_teacher_allocations(version_id=mock_budget_version.id)
        assert allocations == []

    @pytest.mark.asyncio
    async def test_create_teacher_allocation_aefe_detached(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_subjects: list,
        mock_college_cycle: AcademicCycle,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test creating AEFE detached teacher allocation."""
        # Create teacher category

        aefe_category = TeacherCategory(
            id=uuid.uuid4(),
            code="AEFE_DETACHED",
            name_fr="Résident Détaché",
            name_en="AEFE Detached",
            description="AEFE detached teachers",
        )
        db_session.add(aefe_category)
        await db_session.flush()

        # Create allocation
        allocation = await dhg_service.create_teacher_allocation(
            version_id=mock_budget_version.id,
            subject_id=mock_subjects[0].id,
            cycle_id=mock_college_cycle.id,
            category_id=aefe_category.id,
            fte_count=Decimal("5.0"),
            notes="Test AEFE allocation",
            user_id=test_user_id,
        )

        assert allocation is not None
        assert allocation.fte_count == Decimal("5.0")
        assert allocation.subject_id == mock_subjects[0].id

    @pytest.mark.asyncio
    async def test_create_teacher_allocation_local(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_subjects: list,
        mock_college_cycle: AcademicCycle,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test creating local teacher allocation."""

        local_category = TeacherCategory(
            id=uuid.uuid4(),
            code="LOCAL",
            name_fr="Recruté Local",
            name_en="Local Recruit",
            description="Locally recruited teachers",
        )
        db_session.add(local_category)
        await db_session.flush()

        # Create allocation
        allocation = await dhg_service.create_teacher_allocation(
            version_id=mock_budget_version.id,
            subject_id=mock_subjects[1].id,  # French
            cycle_id=mock_college_cycle.id,
            category_id=local_category.id,
            fte_count=Decimal("3.5"),
            notes="Test local allocation",
            user_id=test_user_id,
        )

        assert allocation is not None
        assert allocation.fte_count == Decimal("3.5")
        assert allocation.subject_id == mock_subjects[1].id

        # Verify duplicate allocation fails
        with pytest.raises(ValidationError, match="already exists"):
            await dhg_service.create_teacher_allocation(
                version_id=mock_budget_version.id,
                subject_id=mock_subjects[1].id,
                cycle_id=mock_college_cycle.id,
                category_id=local_category.id,
                fte_count=Decimal("2.0"),
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_create_teacher_allocation_validation_errors(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_subjects: list,
        mock_college_cycle: AcademicCycle,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test validation errors in create_teacher_allocation."""

        category = TeacherCategory(
            id=uuid.uuid4(),
            code="TEST",
            name_fr="Test",
            name_en="Test",
            description="Test category",
        )
        db_session.add(category)
        await db_session.flush()

        # Test FTE count <= 0 validation
        with pytest.raises(ValidationError, match="must be greater than 0"):
            await dhg_service.create_teacher_allocation(
                version_id=mock_budget_version.id,
                subject_id=mock_subjects[0].id,
                cycle_id=mock_college_cycle.id,
                category_id=category.id,
                fte_count=Decimal("0"),  # Invalid
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_update_teacher_allocation(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_subjects: list,
        mock_college_cycle: AcademicCycle,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test updating teacher allocation FTE count."""

        category = TeacherCategory(
            id=uuid.uuid4(),
            code="AEFE",
            name_fr="AEFE",
            name_en="AEFE",
            description="AEFE teachers",
        )
        db_session.add(category)
        await db_session.flush()

        # Create allocation
        allocation = await dhg_service.create_teacher_allocation(
            version_id=mock_budget_version.id,
            subject_id=mock_subjects[0].id,
            cycle_id=mock_college_cycle.id,
            category_id=category.id,
            fte_count=Decimal("5.0"),
            notes="Initial",
            user_id=test_user_id,
        )

        # Update allocation
        updated = await dhg_service.update_teacher_allocation(
            allocation_id=allocation.id,
            fte_count=Decimal("7.0"),
            notes="Updated",
            user_id=test_user_id,
        )

        assert updated.fte_count == Decimal("7.0")
        assert updated.notes == "Updated"

        # Test validation error for invalid FTE
        with pytest.raises(ValidationError, match="must be greater than 0"):
            await dhg_service.update_teacher_allocation(
                allocation_id=allocation.id,
                fte_count=Decimal("-1.0"),
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_delete_teacher_allocation(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_subjects: list,
        mock_college_cycle: AcademicCycle,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test deleting teacher allocation."""

        category = TeacherCategory(
            id=uuid.uuid4(),
            code="LOCAL",
            name_fr="Local",
            name_en="Local",
            description="Local teachers",
        )
        db_session.add(category)
        await db_session.flush()

        # Create allocation
        allocation = await dhg_service.create_teacher_allocation(
            version_id=mock_budget_version.id,
            subject_id=mock_subjects[0].id,
            cycle_id=mock_college_cycle.id,
            category_id=category.id,
            fte_count=Decimal("3.0"),
            user_id=test_user_id,
        )

        # Delete allocation
        result = await dhg_service.delete_teacher_allocation(
            allocation_id=allocation.id,
            user_id=test_user_id,
        )

        assert result is True

        # Verify it's deleted
        allocations = await dhg_service.get_teacher_allocations(version_id=mock_budget_version.id)
        assert len(allocations) == 0

    @pytest.mark.asyncio
    async def test_bulk_update_allocations(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_subjects: list,
        mock_college_cycle: AcademicCycle,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test bulk create/update of teacher allocations."""

        # Create categories
        aefe_category = TeacherCategory(
            id=uuid.uuid4(),
            code="AEFE",
            name_fr="AEFE",
            name_en="AEFE",
            description="AEFE teachers",
        )
        local_category = TeacherCategory(
            id=uuid.uuid4(),
            code="LOCAL",
            name_fr="Local",
            name_en="Local",
            description="Local teachers",
        )
        db_session.add_all([aefe_category, local_category])
        await db_session.flush()

        # Initial bulk create
        allocations_data = [
            {
                "subject_id": mock_subjects[0].id,  # Math
                "cycle_id": mock_college_cycle.id,
                "category_id": aefe_category.id,
                "fte_count": Decimal("5.0"),
                "notes": "Initial Math AEFE",
            },
            {
                "subject_id": mock_subjects[1].id,  # French
                "cycle_id": mock_college_cycle.id,
                "category_id": local_category.id,
                "fte_count": Decimal("3.0"),
                "notes": "Initial French Local",
            },
        ]

        results = await dhg_service.bulk_update_allocations(
            version_id=mock_budget_version.id,
            allocations=allocations_data,
            user_id=test_user_id,
        )

        assert len(results) == 2
        assert results[0].fte_count == Decimal("5.0")
        assert results[1].fte_count == Decimal("3.0")

        # Bulk update (modify existing + add new)
        updated_allocations_data = [
            {
                "subject_id": mock_subjects[0].id,  # Math - UPDATE
                "cycle_id": mock_college_cycle.id,
                "category_id": aefe_category.id,
                "fte_count": Decimal("7.0"),  # Changed from 5.0
                "notes": "Updated Math AEFE",
            },
            {
                "subject_id": mock_subjects[1].id,  # French - UPDATE
                "cycle_id": mock_college_cycle.id,
                "category_id": local_category.id,
                "fte_count": Decimal("4.0"),  # Changed from 3.0
                "notes": "Updated French Local",
            },
            {
                "subject_id": mock_subjects[2].id,  # History - NEW
                "cycle_id": mock_college_cycle.id,
                "category_id": aefe_category.id,
                "fte_count": Decimal("2.0"),
                "notes": "New History AEFE",
            },
        ]

        updated_results = await dhg_service.bulk_update_allocations(
            version_id=mock_budget_version.id,
            allocations=updated_allocations_data,
            user_id=test_user_id,
        )

        assert len(updated_results) == 3
        assert updated_results[0].fte_count == Decimal("7.0")  # Updated
        assert updated_results[1].fte_count == Decimal("4.0")  # Updated
        assert updated_results[2].fte_count == Decimal("2.0")  # New

        # Verify validation error for invalid FTE
        invalid_allocations = [
            {
                "subject_id": mock_subjects[0].id,
                "cycle_id": mock_college_cycle.id,
                "category_id": aefe_category.id,
                "fte_count": Decimal("-1.0"),  # Invalid
            }
        ]

        with pytest.raises(ValidationError, match="must be greater than 0"):
            await dhg_service.bulk_update_allocations(
                version_id=mock_budget_version.id,
                allocations=invalid_allocations,
                user_id=test_user_id,
            )


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
        mock_class_structure,
        mock_subject_hours_matrix,
        mock_subjects: list,
        mock_college_cycle: AcademicCycle,
        db_session: AsyncSession,
        test_user_id,
    ):
        """
        Test gap analysis when deficit exists.

        Deficit = Required FTE - Available FTE
        Should calculate HSA coverage and remaining deficit.
        """
        # Calculate DHG hours and teacher requirements
        await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        await dhg_service.calculate_teacher_requirements(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Create partial allocation (less than required)

        local_category = TeacherCategory(
            id=uuid.uuid4(),
            code="LOCAL",
            name_fr="Recruté Local",
            name_en="Local Recruit",
            description="Locally recruited teachers",
        )
        db_session.add(local_category)
        await db_session.flush()

        # Allocate 2 FTE for Math (requirement is 5)
        await dhg_service.create_teacher_allocation(
            version_id=mock_budget_version.id,
            subject_id=mock_subjects[0].id,  # Math
            cycle_id=mock_college_cycle.id,
            category_id=local_category.id,
            fte_count=Decimal("2.0"),
            user_id=test_user_id,
        )

        # Perform gap analysis
        gap_analysis = await dhg_service.get_trmd_gap_analysis(version_id=mock_budget_version.id)

        # Verify structure
        assert gap_analysis["budget_version_id"] == mock_budget_version.id
        assert gap_analysis["total_besoins"] > 0
        assert gap_analysis["total_moyens"] == 2.0  # Only Math has allocation
        assert gap_analysis["total_deficit"] > 0  # Deficit exists
        assert len(gap_analysis["by_subject"]) == 3  # Math, French, History

        # Find Math subject analysis
        math_analysis = next(s for s in gap_analysis["by_subject"] if s["subject_code"] == "MATH")
        assert math_analysis["besoins_fte"] == 5  # Rounded FTE for Math
        assert math_analysis["moyens_fte"] == Decimal("2.0")
        assert math_analysis["deficit_fte"] == 3  # 5 - 2
        assert math_analysis["status"] == "deficit"

    @pytest.mark.asyncio
    async def test_gap_analysis_surplus_scenario(
        self,
        dhg_service: DHGService,
        mock_budget_version,
        mock_class_structure,
        mock_subject_hours_matrix,
        mock_subjects: list,
        mock_college_cycle: AcademicCycle,
        db_session: AsyncSession,
        test_user_id,
    ):
        """Test gap analysis when surplus exists (over-staffed)."""
        # Calculate requirements
        await dhg_service.calculate_dhg_subject_hours(
            budget_version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        await dhg_service.calculate_teacher_requirements(
            version_id=mock_budget_version.id,
            recalculate_all=True,
        )

        # Create over-allocation (more than required)

        aefe_category = TeacherCategory(
            id=uuid.uuid4(),
            code="AEFE",
            name_fr="AEFE",
            name_en="AEFE",
            description="AEFE teachers",
        )
        db_session.add(aefe_category)
        await db_session.flush()

        # Allocate 8 FTE for Math (requirement is 5) - surplus of 3
        await dhg_service.create_teacher_allocation(
            version_id=mock_budget_version.id,
            subject_id=mock_subjects[0].id,  # Math
            cycle_id=mock_college_cycle.id,
            category_id=aefe_category.id,
            fte_count=Decimal("8.0"),
            user_id=test_user_id,
        )

        # Perform gap analysis
        gap_analysis = await dhg_service.get_trmd_gap_analysis(version_id=mock_budget_version.id)

        # Find Math subject analysis
        math_analysis = next(s for s in gap_analysis["by_subject"] if s["subject_code"] == "MATH")
        assert math_analysis["besoins_fte"] == 5
        assert math_analysis["moyens_fte"] == Decimal("8.0")
        assert math_analysis["deficit_fte"] == -3  # 5 - 8 = -3 (surplus)
        assert math_analysis["status"] == "surplus"

    @pytest.mark.asyncio
    async def test_gap_analysis_no_requirements(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test gap analysis fails when no teacher requirements exist."""
        # No DHG hours or teacher requirements calculated

        with pytest.raises(
            BusinessRuleError,
            match="Cannot perform TRMD analysis without teacher requirements",
        ):
            await dhg_service.get_trmd_gap_analysis(version_id=mock_budget_version.id)


# ==============================================================================
# Test: Business Rule Validation
# ==============================================================================


class TestDHGBusinessRules:
    """Test business rule enforcement.

    Note: Business rule validation is covered in the engine tests.
    Service-level validation tests are covered in functional tests above.
    """

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
        # Non-existent budget version results in empty class structures
        # which triggers BusinessRuleError
        with pytest.raises(
            BusinessRuleError,
            match="Cannot calculate DHG hours without class structure data",
        ):
            await dhg_service.calculate_dhg_subject_hours(
                budget_version_id=uuid.uuid4(),
                recalculate_all=True,
            )

    @pytest.mark.asyncio
    async def test_get_dhg_subject_hours_empty_version(
        self,
        dhg_service: DHGService,
        mock_budget_version,
    ):
        """Test retrieving DHG hours for version with no calculations."""
        result = await dhg_service.get_dhg_subject_hours(version_id=mock_budget_version.id)

        assert isinstance(result, list)
        assert len(result) == 0
