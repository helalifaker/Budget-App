"""
Centralized test fixtures and mock data for EFIR Budget Planning tests.

Organized by domain:
- Configuration fixtures (academic levels, subjects, fees, costs)
- Planning fixtures (enrollment, classes, DHG, allocations)
- Consolidation fixtures (revenue, costs, CapEx)
- Analysis fixtures (KPIs, dashboards)
- Budget version fixtures

Usage:
    from tests.fixtures import (
        mock_budget_version,
        mock_enrollment_plan,
        mock_dhg_subject_hours,
    )

All fixtures use realistic EFIR data based on:
- EFIR_Data_Summary_v2.md
- EFIR_Module_Technical_Specification.md
- EFIR_Workforce_Planning_Logic.md
"""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    BudgetVersion,
    BudgetVersionStatus,
    FeeCategory,
    FeeStructure,
    Subject,
    SubjectHoursMatrix,
    TeacherCategory,
    TeacherCostParam,
)
from app.models.planning import (
    CapExPlan,
    ClassStructure,
    DHGSubjectHours,
    DHGTeacherRequirement,
    EnrollmentPlan,
    OperatingCostPlan,
    PersonnelCostPlan,
    RevenuePlan,
    TeacherAllocation,
)


# ==============================================================================
# Test User ID (matches auth.users created in conftest.py)
# ==============================================================================

TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ==============================================================================
# Configuration Fixtures
# ==============================================================================


@pytest.fixture
async def mock_academic_cycles(db_session: AsyncSession) -> list[AcademicCycle]:
    """Create all academic cycles."""
    cycles = [
        AcademicCycle(
            id=uuid.uuid4(),
            code="MATERNELLE",
            name="Maternelle",
            description="Preschool (PS, MS, GS)",
            sort_order=1,
            created_by_id=TEST_USER_ID,
        ),
        AcademicCycle(
            id=uuid.uuid4(),
            code="ELEMENTAIRE",
            name="Élémentaire",
            description="Elementary (CP, CE1, CE2, CM1, CM2)",
            sort_order=2,
            created_by_id=TEST_USER_ID,
        ),
        AcademicCycle(
            id=uuid.uuid4(),
            code="COLLEGE",
            name="Collège",
            description="Middle school (6ème-3ème)",
            sort_order=3,
            created_by_id=TEST_USER_ID,
        ),
        AcademicCycle(
            id=uuid.uuid4(),
            code="LYCEE",
            name="Lycée",
            description="High school (2nde-Terminale)",
            sort_order=4,
            created_by_id=TEST_USER_ID,
        ),
    ]

    for cycle in cycles:
        db_session.add(cycle)
    await db_session.commit()

    for cycle in cycles:
        await db_session.refresh(cycle)

    return cycles


@pytest.fixture
async def mock_academic_levels(
    db_session: AsyncSession, mock_academic_cycles: list[AcademicCycle]
) -> list[AcademicLevel]:
    """
    Create all academic levels (PS → Terminale).

    Total: 15 levels
    - Maternelle: PS, MS, GS (3)
    - Élémentaire: CP, CE1, CE2, CM1, CM2 (5)
    - Collège: 6ème, 5ème, 4ème, 3ème (4)
    - Lycée: 2nde, 1ère, Terminale (3)
    """
    cycle_map = {c.code: c for c in mock_academic_cycles}

    levels_data = [
        # Maternelle
        ("PS", "Petite Section", "MATERNELLE", 1),
        ("MS", "Moyenne Section", "MATERNELLE", 2),
        ("GS", "Grande Section", "MATERNELLE", 3),
        # Élémentaire
        ("CP", "Cours Préparatoire", "ELEMENTAIRE", 4),
        ("CE1", "Cours Élémentaire 1", "ELEMENTAIRE", 5),
        ("CE2", "Cours Élémentaire 2", "ELEMENTAIRE", 6),
        ("CM1", "Cours Moyen 1", "ELEMENTAIRE", 7),
        ("CM2", "Cours Moyen 2", "ELEMENTAIRE", 8),
        # Collège
        ("6EME", "6ème", "COLLEGE", 9),
        ("5EME", "5ème", "COLLEGE", 10),
        ("4EME", "4ème", "COLLEGE", 11),
        ("3EME", "3ème", "COLLEGE", 12),
        # Lycée
        ("2NDE", "2nde", "LYCEE", 13),
        ("1ERE", "1ère", "LYCEE", 14),
        ("TERM", "Terminale", "LYCEE", 15),
    ]

    levels = []
    for code, name, cycle_code, sort_order in levels_data:
        level = AcademicLevel(
            id=uuid.uuid4(),
            code=code,
            name=name,
            cycle_id=cycle_map[cycle_code].id,
            sort_order=sort_order,
            created_by_id=TEST_USER_ID,
        )
        db_session.add(level)
        levels.append(level)

    await db_session.commit()

    for level in levels:
        await db_session.refresh(level)

    return levels


@pytest.fixture
async def mock_subjects(db_session: AsyncSession) -> list[Subject]:
    """
    Create core subjects for French education system.

    Categories:
    - CORE: Math, French, History, Sciences, Languages
    - SPECIALTY: Philosophy, Economics, Arts
    - ACTIVITY: PE, Music, Arts
    """
    subjects_data = [
        # Core subjects
        ("MATH", "Mathématiques", "Mathematics", "CORE"),
        ("FR", "Français", "French language and literature", "CORE"),
        ("HIST", "Histoire-Géographie", "History and Geography", "CORE"),
        ("SVT", "Sciences de la Vie et de la Terre", "Life and Earth Sciences", "CORE"),
        ("PHYS", "Physique-Chimie", "Physics and Chemistry", "CORE"),
        ("LV1", "Langue Vivante 1 (Anglais)", "First Foreign Language (English)", "CORE"),
        ("LV2", "Langue Vivante 2", "Second Foreign Language", "CORE"),
        # Specialty subjects
        ("PHILO", "Philosophie", "Philosophy", "SPECIALTY"),
        ("ECO", "Sciences Économiques et Sociales", "Economics and Social Sciences", "SPECIALTY"),
        ("ART", "Arts Plastiques", "Visual Arts", "SPECIALTY"),
        # Activity subjects
        ("EPS", "Éducation Physique et Sportive", "Physical Education", "ACTIVITY"),
        ("MUS", "Éducation Musicale", "Music Education", "ACTIVITY"),
    ]

    subjects = []
    for code, name, description, category in subjects_data:
        subject = Subject(
            id=uuid.uuid4(),
            code=code,
            name=name,
            description=description,
            category=category,
            created_by_id=TEST_USER_ID,
        )
        db_session.add(subject)
        subjects.append(subject)

    await db_session.commit()

    for subject in subjects:
        await db_session.refresh(subject)

    return subjects


@pytest.fixture
async def mock_subject_hours_matrix_college(
    db_session: AsyncSession,
    mock_subjects: list[Subject],
    mock_academic_levels: list[AcademicLevel],
) -> list[SubjectHoursMatrix]:
    """
    Create subject hours matrix for Collège (6ème-3ème).

    Based on French national curriculum:
    https://www.education.gouv.fr/

    Hours per week by level:
    - 6ème: Math(4.5), FR(4.5), HIST(3), SVT(1.5), PHYS(0), LV1(4), EPS(4)
    - 5ème: Math(3.5), FR(4.5), HIST(3), SVT(1.5), PHYS(1.5), LV1(3), LV2(2.5), EPS(3)
    - 4ème: Math(3.5), FR(4.5), HIST(3.5), SVT(1.5), PHYS(1.5), LV1(3), LV2(2.5), EPS(3)
    - 3ème: Math(3.5), FR(4), HIST(3.5), SVT(1.5), PHYS(1.5), LV1(3), LV2(2.5), EPS(3)
    """
    subject_map = {s.code: s for s in mock_subjects}
    level_map = {l.code: l for l in mock_academic_levels}

    # Hours matrix: {subject_code: {level_code: hours}}
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
        "SVT": {
            "6EME": Decimal("1.5"),
            "5EME": Decimal("1.5"),
            "4EME": Decimal("1.5"),
            "3EME": Decimal("1.5"),
        },
        "PHYS": {
            "5EME": Decimal("1.5"),
            "4EME": Decimal("1.5"),
            "3EME": Decimal("1.5"),
        },
        "LV1": {
            "6EME": Decimal("4.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.0"),
        },
        "LV2": {
            "5EME": Decimal("2.5"),
            "4EME": Decimal("2.5"),
            "3EME": Decimal("2.5"),
        },
        "EPS": {
            "6EME": Decimal("4.0"),
            "5EME": Decimal("3.0"),
            "4EME": Decimal("3.0"),
            "3EME": Decimal("3.0"),
        },
    }

    matrix_entries = []
    for subject_code, level_hours in hours_data.items():
        for level_code, hours in level_hours.items():
            if subject_code in subject_map and level_code in level_map:
                entry = SubjectHoursMatrix(
                    id=uuid.uuid4(),
                    subject_id=subject_map[subject_code].id,
                    level_id=level_map[level_code].id,
                    hours_per_week=hours,
                    fiscal_year=2024,
                    created_by_id=TEST_USER_ID,
                )
                db_session.add(entry)
                matrix_entries.append(entry)

    await db_session.commit()

    for entry in matrix_entries:
        await db_session.refresh(entry)

    return matrix_entries


@pytest.fixture
async def mock_fee_structure(
    db_session: AsyncSession, mock_academic_levels: list[AcademicLevel]
) -> list[FeeStructure]:
    """
    Create fee structure for FY2024.

    Based on EFIR_Data_Summary_v2.md:
    - Maternelle: 19,500 SAR (French TTC), 20,475 SAR (Saudi HT), 22,500 SAR (Other TTC)
    - Élémentaire: 24,000 SAR
    - Collège: 28,500 SAR
    - Lycée: 31,500 SAR

    Fee categories:
    - TUITION: Annual tuition
    - DAI: Droit Annuel d'Inscription (Annual enrollment fee)
    - REGISTRATION: One-time registration fee
    """
    level_map = {l.code: l for l in mock_academic_levels}

    # Fee amounts by cycle and nationality
    fee_data = {
        # Maternelle (PS, MS, GS)
        "PS": {
            FeeCategory.TUITION: {
                "FRENCH": Decimal("19500.00"),
                "SAUDI": Decimal("20475.00"),
                "OTHER": Decimal("22500.00"),
            },
            FeeCategory.DAI: {
                "FRENCH": Decimal("1500.00"),
                "SAUDI": Decimal("1575.00"),
                "OTHER": Decimal("1500.00"),
            },
        },
        # Élémentaire (CP-CM2)
        "CP": {
            FeeCategory.TUITION: {
                "FRENCH": Decimal("24000.00"),
                "SAUDI": Decimal("25200.00"),
                "OTHER": Decimal("27000.00"),
            },
            FeeCategory.DAI: {
                "FRENCH": Decimal("1500.00"),
                "SAUDI": Decimal("1575.00"),
                "OTHER": Decimal("1500.00"),
            },
        },
        # Collège (6ème-3ème)
        "6EME": {
            FeeCategory.TUITION: {
                "FRENCH": Decimal("28500.00"),
                "SAUDI": Decimal("29925.00"),
                "OTHER": Decimal("31500.00"),
            },
            FeeCategory.DAI: {
                "FRENCH": Decimal("2000.00"),
                "SAUDI": Decimal("2100.00"),
                "OTHER": Decimal("2000.00"),
            },
        },
        # Lycée (2nde-Term)
        "2NDE": {
            FeeCategory.TUITION: {
                "FRENCH": Decimal("31500.00"),
                "SAUDI": Decimal("33075.00"),
                "OTHER": Decimal("34500.00"),
            },
            FeeCategory.DAI: {
                "FRENCH": Decimal("2500.00"),
                "SAUDI": Decimal("2625.00"),
                "OTHER": Decimal("2500.00"),
            },
        },
    }

    fee_structures = []
    for level_code, categories in fee_data.items():
        if level_code in level_map:
            for category, nationalities in categories.items():
                for nationality, amount in nationalities.items():
                    fee = FeeStructure(
                        id=uuid.uuid4(),
                        level_id=level_map[level_code].id,
                        fee_category=category,
                        nationality=nationality,
                        amount_sar=amount,
                        fiscal_year=2024,
                        created_by_id=TEST_USER_ID,
                    )
                    db_session.add(fee)
                    fee_structures.append(fee)

    await db_session.commit()

    for fee in fee_structures:
        await db_session.refresh(fee)

    return fee_structures


@pytest.fixture
async def mock_teacher_cost_params(
    db_session: AsyncSession,
) -> dict[TeacherCategory, TeacherCostParam]:
    """
    Create teacher cost parameters for FY2024.

    Based on EFIR_Workforce_Planning_Logic.md:

    AEFE Detached:
    - PRRD: 41,863 EUR/teacher
    - Social charges: 42%
    - EUR to SAR: 4.25

    AEFE Funded:
    - Zero cost to school

    Local Teachers:
    - Monthly salary: 12,500 SAR
    - Months: 12
    - Social charges: 11%
    """
    params_data = {
        TeacherCategory.AEFE_DETACHED: {
            "prrd_eur": Decimal("41863.00"),
            "social_charges_pct": Decimal("0.42"),
            "eur_to_sar_rate": Decimal("4.25"),
            "monthly_salary_sar": None,
            "months_per_year": None,
        },
        TeacherCategory.AEFE_FUNDED: {
            "prrd_eur": Decimal("0.00"),
            "social_charges_pct": Decimal("0.00"),
            "eur_to_sar_rate": Decimal("4.25"),
            "monthly_salary_sar": None,
            "months_per_year": None,
        },
        TeacherCategory.LOCAL: {
            "prrd_eur": None,
            "social_charges_pct": Decimal("0.11"),
            "eur_to_sar_rate": None,
            "monthly_salary_sar": Decimal("12500.00"),
            "months_per_year": 12,
        },
    }

    params = {}
    for category, data in params_data.items():
        param = TeacherCostParam(
            id=uuid.uuid4(),
            category=category,
            fiscal_year=2024,
            **data,
            created_by_id=TEST_USER_ID,
        )
        db_session.add(param)
        params[category] = param

    await db_session.commit()

    for param in params.values():
        await db_session.refresh(param)

    return params


# ==============================================================================
# Budget Version Fixtures
# ==============================================================================


@pytest.fixture
async def mock_budget_version(db_session: AsyncSession) -> BudgetVersion:
    """Create test budget version in WORKING status."""
    version = BudgetVersion(
        id=uuid.uuid4(),
        name="Test Budget 2024",
        fiscal_year=2024,
        status=BudgetVersionStatus.WORKING,
        notes="Test budget for unit testing",
        created_by_id=TEST_USER_ID,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)
    return version


@pytest.fixture
async def mock_budget_version_submitted(db_session: AsyncSession) -> BudgetVersion:
    """Create test budget version in SUBMITTED status."""
    version = BudgetVersion(
        id=uuid.uuid4(),
        name="Test Budget 2024 Submitted",
        fiscal_year=2024,
        status=BudgetVersionStatus.SUBMITTED,
        submitted_at=datetime.utcnow(),
        submitted_by_id=TEST_USER_ID,
        created_by_id=TEST_USER_ID,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)
    return version


# ==============================================================================
# Planning Fixtures
# ==============================================================================


@pytest.fixture
async def mock_enrollment_plan(
    db_session: AsyncSession,
    mock_budget_version: BudgetVersion,
    mock_academic_levels: list[AcademicLevel],
) -> list[EnrollmentPlan]:
    """
    Create enrollment plan for 880 total students.

    Distribution based on EFIR_Data_Summary_v2.md:
    - Maternelle: 120 (PS:40, MS:40, GS:40)
    - Élémentaire: 320 (CP:68, CE1:64, CE2:64, CM1:62, CM2:62)
    - Collège: 260 (6ème:70, 5ème:68, 4ème:62, 3ème:60)
    - Lycée: 180 (2nde:65, 1ère:60, Term:55)
    """
    level_map = {l.code: l for l in mock_academic_levels}

    # Student counts by level and nationality
    enrollment_data = {
        # Maternelle
        "PS": {"FRENCH": 24, "SAUDI": 10, "OTHER": 6},
        "MS": {"FRENCH": 24, "SAUDI": 10, "OTHER": 6},
        "GS": {"FRENCH": 24, "SAUDI": 10, "OTHER": 6},
        # Élémentaire
        "CP": {"FRENCH": 40, "SAUDI": 18, "OTHER": 10},
        "CE1": {"FRENCH": 38, "SAUDI": 16, "OTHER": 10},
        "CE2": {"FRENCH": 38, "SAUDI": 16, "OTHER": 10},
        "CM1": {"FRENCH": 37, "SAUDI": 15, "OTHER": 10},
        "CM2": {"FRENCH": 37, "SAUDI": 15, "OTHER": 10},
        # Collège
        "6EME": {"FRENCH": 42, "SAUDI": 18, "OTHER": 10},
        "5EME": {"FRENCH": 40, "SAUDI": 18, "OTHER": 10},
        "4EME": {"FRENCH": 37, "SAUDI": 15, "OTHER": 10},
        "3EME": {"FRENCH": 36, "SAUDI": 14, "OTHER": 10},
        # Lycée
        "2NDE": {"FRENCH": 39, "SAUDI": 16, "OTHER": 10},
        "1ERE": {"FRENCH": 36, "SAUDI": 14, "OTHER": 10},
        "TERM": {"FRENCH": 33, "SAUDI": 12, "OTHER": 10},
    }

    enrollments = []
    for level_code, nationalities in enrollment_data.items():
        if level_code in level_map:
            for nationality, count in nationalities.items():
                enrollment = EnrollmentPlan(
                    id=uuid.uuid4(),
                    budget_version_id=mock_budget_version.id,
                    level_id=level_map[level_code].id,
                    nationality=nationality,
                    student_count=count,
                    created_by_id=TEST_USER_ID,
                )
                db_session.add(enrollment)
                enrollments.append(enrollment)

    await db_session.commit()

    for enrollment in enrollments:
        await db_session.refresh(enrollment)

    return enrollments


@pytest.fixture
async def mock_class_structure(
    db_session: AsyncSession,
    mock_budget_version: BudgetVersion,
    mock_academic_levels: list[AcademicLevel],
) -> list[ClassStructure]:
    """
    Create class structure based on enrollment.

    Class counts (target class size: 25):
    - Maternelle: PS(2), MS(2), GS(2) = 6 classes
    - Élémentaire: CP(3), CE1(3), CE2(3), CM1(2), CM2(2) = 13 classes
    - Collège: 6ème(3), 5ème(3), 4ème(2), 3ème(2) = 10 classes
    - Lycée: 2nde(3), 1ère(2), Term(2) = 7 classes
    Total: 36 classes
    """
    level_map = {l.code: l for l in mock_academic_levels}

    class_data = {
        # Maternelle (40 students each → 2 classes of 20)
        "PS": {"num_classes": 2, "total_students": 40, "avg_size": Decimal("20.0")},
        "MS": {"num_classes": 2, "total_students": 40, "avg_size": Decimal("20.0")},
        "GS": {"num_classes": 2, "total_students": 40, "avg_size": Decimal("20.0")},
        # Élémentaire
        "CP": {"num_classes": 3, "total_students": 68, "avg_size": Decimal("22.7")},
        "CE1": {"num_classes": 3, "total_students": 64, "avg_size": Decimal("21.3")},
        "CE2": {"num_classes": 3, "total_students": 64, "avg_size": Decimal("21.3")},
        "CM1": {"num_classes": 2, "total_students": 62, "avg_size": Decimal("31.0")},
        "CM2": {"num_classes": 2, "total_students": 62, "avg_size": Decimal("31.0")},
        # Collège
        "6EME": {"num_classes": 3, "total_students": 70, "avg_size": Decimal("23.3")},
        "5EME": {"num_classes": 3, "total_students": 68, "avg_size": Decimal("22.7")},
        "4EME": {"num_classes": 2, "total_students": 62, "avg_size": Decimal("31.0")},
        "3EME": {"num_classes": 2, "total_students": 60, "avg_size": Decimal("30.0")},
        # Lycée
        "2NDE": {"num_classes": 3, "total_students": 65, "avg_size": Decimal("21.7")},
        "1ERE": {"num_classes": 2, "total_students": 60, "avg_size": Decimal("30.0")},
        "TERM": {"num_classes": 2, "total_students": 55, "avg_size": Decimal("27.5")},
    }

    class_structures = []
    for level_code, data in class_data.items():
        if level_code in level_map:
            cs = ClassStructure(
                id=uuid.uuid4(),
                budget_version_id=mock_budget_version.id,
                level_id=level_map[level_code].id,
                num_classes=data["num_classes"],
                total_students=data["total_students"],
                avg_class_size=data["avg_size"],
                created_by_id=TEST_USER_ID,
            )
            db_session.add(cs)
            class_structures.append(cs)

    await db_session.commit()

    for cs in class_structures:
        await db_session.refresh(cs)

    return class_structures


# ==============================================================================
# Helper Functions
# ==============================================================================


def get_fixture_by_code(fixtures: list, code: str):
    """Helper to get fixture by code."""
    return next((f for f in fixtures if f.code == code), None)


def get_fixture_by_id(fixtures: list, fixture_id: uuid.UUID):
    """Helper to get fixture by ID."""
    return next((f for f in fixtures if f.id == fixture_id), None)
