"""
Pytest configuration and fixtures for EFIR Budget Planning Application tests.

This file provides common fixtures and configuration for all tests, including:
- Database setup
- Sample data fixtures
- Budget version fixtures
- Configuration fixtures
- Authentication mocks
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

# Import all models to ensure they're registered with SQLAlchemy
from app.models import *  # noqa: F403
from app.models.base import Base
from app.models.configuration import (
    AcademicCycle,
    AcademicLevel,
    BudgetVersion,
    BudgetVersionStatus,
    ClassSizeParam,
    FeeCategory,
    FeeStructure,
    NationalityType,
    Subject,
    SubjectHoursMatrix,
    SystemConfig,
    TeacherCategory,
    TeacherCostParam,
)
from app.models.planning import (
    ClassStructure,
    DHGSubjectHours,
    DHGTeacherRequirement,
    EnrollmentPlan,
)
from sqlalchemy import UUID as SQLUUID
from sqlalchemy import String, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

# ==============================================================================
# Test-only User Model for auth.users
# ==============================================================================
# Production code intentionally avoids defining a User model to keep auth
# separate from business logic. For tests, we need a minimal model so
# SQLAlchemy can resolve foreign keys to auth.users.id


class User(Base):
    """
    Minimal User model for test database only.

    Simulates Supabase auth.users table structure for testing.
    Production code uses direct queries to auth.users when needed.
    """

    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.

    This fixture ensures that all async tests use the same event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Get test database URL.

    Uses in-memory SQLite for fast tests.
    For integration tests with PostgreSQL, override this fixture.
    """
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def engine(test_database_url: str):
    """
    Create async database engine for tests.

    Creates all tables in the test database including auth schema.
    """
    engine = create_async_engine(
        test_database_url,
        echo=False,  # Set to True for SQL debugging
    )

    async with engine.begin() as conn:
        # SQLite needs attached schemas to handle multi-schema table names
        if test_database_url.startswith("sqlite"):
            # Attach schemas for efir_budget.* and auth.* tables
            await conn.execute(text("ATTACH DATABASE ':memory:' AS efir_budget"))
            await conn.execute(text("ATTACH DATABASE ':memory:' AS auth"))

        # Create all tables (including auth.users from User model)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for each test.

    Each test gets a fresh session that's rolled back after the test.
    """
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_uuid() -> UUID:
    """Generate a sample UUID for testing."""
    return uuid4()


@pytest.fixture
async def test_user_id(db_session: AsyncSession) -> UUID:
    """
    Create a test user in auth.users and return the ID.

    This ensures foreign key constraints to auth.users.id are satisfied.
    """
    user_id = uuid4()
    user = User(id=user_id, email="test@efir.local")
    db_session.add(user)
    await db_session.flush()
    return user_id


# ==============================================================================
# Academic Structure Fixtures
# ==============================================================================


@pytest.fixture
async def academic_cycles(db_session: AsyncSession) -> dict[str, AcademicCycle]:
    """Create academic cycles for testing."""
    maternelle = AcademicCycle(
        id=uuid4(),
        code="MATERNELLE",
        name_en="Preschool",
        name_fr="Maternelle",
        sort_order=1,
        requires_atsem=True,
        is_secondary=False,
    )
    elementaire = AcademicCycle(
        id=uuid4(),
        code="ELEMENTAIRE",
        name_en="Elementary",
        name_fr="Élémentaire",
        sort_order=2,
        requires_atsem=False,
        is_secondary=False,
    )
    college = AcademicCycle(
        id=uuid4(),
        code="COLLEGE",
        name_en="Middle School",
        name_fr="Collège",
        sort_order=3,
        requires_atsem=False,
        is_secondary=True,
    )
    lycee = AcademicCycle(
        id=uuid4(),
        code="LYCEE",
        name_en="High School",
        name_fr="Lycée",
        sort_order=4,
        requires_atsem=False,
        is_secondary=True,
    )

    db_session.add_all([maternelle, elementaire, college, lycee])
    await db_session.flush()

    return {
        "maternelle": maternelle,
        "elementaire": elementaire,
        "college": college,
        "lycee": lycee,
    }


@pytest.fixture
async def academic_levels(
    db_session: AsyncSession, academic_cycles: dict
) -> dict[str, AcademicLevel]:
    """Create academic levels for testing."""
    levels = {
        "PS": AcademicLevel(
            id=uuid4(),
            code="PS",
            name_en="Petite Section",
            name_fr="Petite Section",
            cycle_id=academic_cycles["maternelle"].id,
            sort_order=1,
            is_secondary=False,
        ),
        "MS": AcademicLevel(
            id=uuid4(),
            code="MS",
            name_en="Moyenne Section",
            name_fr="Moyenne Section",
            cycle_id=academic_cycles["maternelle"].id,
            sort_order=2,
            is_secondary=False,
        ),
        "GS": AcademicLevel(
            id=uuid4(),
            code="GS",
            name_en="Grande Section",
            name_fr="Grande Section",
            cycle_id=academic_cycles["maternelle"].id,
            sort_order=3,
            is_secondary=False,
        ),
        "CP": AcademicLevel(
            id=uuid4(),
            code="CP",
            name_en="CP",
            name_fr="CP",
            cycle_id=academic_cycles["elementaire"].id,
            sort_order=4,
            is_secondary=False,
        ),
        "6EME": AcademicLevel(
            id=uuid4(),
            code="6EME",
            name_en="6ème",
            name_fr="6ème",
            cycle_id=academic_cycles["college"].id,
            sort_order=11,
            is_secondary=True,
        ),
        "5EME": AcademicLevel(
            id=uuid4(),
            code="5EME",
            name_en="5ème",
            name_fr="5ème",
            cycle_id=academic_cycles["college"].id,
            sort_order=12,
            is_secondary=True,
        ),
    }

    db_session.add_all(levels.values())
    await db_session.flush()

    return levels


@pytest.fixture
async def nationality_types(db_session: AsyncSession) -> dict[str, NationalityType]:
    """Create nationality types for testing."""
    types = {
        "FRENCH": NationalityType(
            id=uuid4(),
            code="FRENCH",
            name_en="French",
            name_fr="Français",
            sort_order=1,
        ),
        "SAUDI": NationalityType(
            id=uuid4(),
            code="SAUDI",
            name_en="Saudi",
            name_fr="Saoudien",
            sort_order=2,
        ),
        "OTHER": NationalityType(
            id=uuid4(),
            code="OTHER",
            name_en="Other",
            name_fr="Autre",
            sort_order=3,
        ),
    }

    db_session.add_all(types.values())
    await db_session.flush()

    return types


@pytest.fixture
async def subjects(db_session: AsyncSession) -> dict[str, Subject]:
    """Create subjects for testing."""
    subjects_data = {
        "FRENCH": Subject(
            id=uuid4(),
            code="FRENCH",
            name_en="French Language",
            name_fr="Français",
            is_active=True,
        ),
        "MATH": Subject(
            id=uuid4(),
            code="MATH",
            name_en="Mathematics",
            name_fr="Mathématiques",
            is_active=True,
        ),
        "HISTORY": Subject(
            id=uuid4(),
            code="HISTORY",
            name_en="History-Geography",
            name_fr="Histoire-Géographie",
            is_active=True,
        ),
        "ENGLISH": Subject(
            id=uuid4(),
            code="ENGLISH",
            name_en="English",
            name_fr="Anglais",
            is_active=True,
        ),
    }

    db_session.add_all(subjects_data.values())
    await db_session.flush()

    return subjects_data


@pytest.fixture
async def teacher_categories(db_session: AsyncSession) -> dict[str, TeacherCategory]:
    """Create teacher categories for testing."""
    categories = {
        "AEFE_DETACHED": TeacherCategory(
            id=uuid4(),
            code="AEFE_DETACHED",
            name_en="AEFE Detached Teacher",
            name_fr="Enseignant AEFE Détaché",
        ),
        "AEFE_FUNDED": TeacherCategory(
            id=uuid4(),
            code="AEFE_FUNDED",
            name_en="AEFE Funded Teacher",
            name_fr="Enseignant AEFE Financé",
        ),
        "LOCAL": TeacherCategory(
            id=uuid4(),
            code="LOCAL",
            name_en="Local Teacher",
            name_fr="Enseignant Local",
        ),
    }

    db_session.add_all(categories.values())
    await db_session.flush()

    return categories


@pytest.fixture
async def fee_categories(db_session: AsyncSession) -> dict[str, FeeCategory]:
    """Create fee categories for testing."""
    categories = {
        "TUITION": FeeCategory(
            id=uuid4(),
            code="TUITION",
            name_en="Tuition",
            name_fr="Scolarité",
            nationality_type_id=None,
        ),
        "DAI": FeeCategory(
            id=uuid4(),
            code="DAI",
            name_en="Annual Enrollment Fee",
            name_fr="Droit Annuel d'Inscription",
            nationality_type_id=None,
        ),
        "REGISTRATION": FeeCategory(
            id=uuid4(),
            code="REGISTRATION",
            name_en="Registration Fee",
            name_fr="Frais d'Inscription",
            nationality_type_id=None,
        ),
    }

    db_session.add_all(categories.values())
    await db_session.flush()

    return categories


# ==============================================================================
# Budget Version Fixtures
# ==============================================================================


@pytest.fixture
async def test_budget_version(
    db_session: AsyncSession, test_user_id: UUID
) -> BudgetVersion:
    """Create a test budget version."""
    version = BudgetVersion(
        id=uuid4(),
        name="FY2025 Budget v1",
        fiscal_year=2025,
        academic_year="2024-2025",
        status=BudgetVersionStatus.WORKING,
        is_baseline=False,
        notes="Test budget version",
        created_by_id=test_user_id,
        created_at=datetime.utcnow(),
    )

    db_session.add(version)
    await db_session.flush()

    return version


@pytest.fixture
async def test_class_size_params(
    db_session: AsyncSession,
    test_budget_version: BudgetVersion,
    academic_levels: dict,
    test_user_id: UUID,
) -> list[ClassSizeParam]:
    """Create test class size parameters."""
    params = [
        ClassSizeParam(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["PS"].id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=20,
            max_class_size=24,
            notes="Maternelle PS",
            created_by_id=test_user_id,
        ),
        ClassSizeParam(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            cycle_id=None,
            min_class_size=20,
            target_class_size=28,
            max_class_size=32,
            notes="Collège 6ème",
            created_by_id=test_user_id,
        ),
    ]

    db_session.add_all(params)
    await db_session.flush()

    return params


@pytest.fixture
async def test_enrollment_data(
    db_session: AsyncSession,
    test_budget_version: BudgetVersion,
    academic_levels: dict,
    nationality_types: dict,
    test_user_id: UUID,
) -> list[EnrollmentPlan]:
    """Create test enrollment data."""
    enrollments = [
        EnrollmentPlan(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["PS"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            student_count=35,
            notes="PS French students",
            created_by_id=test_user_id,
        ),
        EnrollmentPlan(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["PS"].id,
            nationality_type_id=nationality_types["SAUDI"].id,
            student_count=15,
            notes="PS Saudi students",
            created_by_id=test_user_id,
        ),
        EnrollmentPlan(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            student_count=80,
            notes="6ème French students",
            created_by_id=test_user_id,
        ),
    ]

    db_session.add_all(enrollments)
    await db_session.flush()

    return enrollments


@pytest.fixture
async def test_class_structure(
    db_session: AsyncSession,
    test_budget_version: BudgetVersion,
    academic_levels: dict,
    test_user_id: UUID,
) -> list[ClassStructure]:
    """Create test class structure data."""
    structures = [
        ClassStructure(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["PS"].id,
            total_students=50,
            number_of_classes=3,
            avg_class_size=Decimal("16.67"),
            requires_atsem=True,
            atsem_count=3,
            calculation_method="target",
            created_by_id=test_user_id,
        ),
        ClassStructure(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            total_students=80,
            number_of_classes=3,
            avg_class_size=Decimal("26.67"),
            requires_atsem=False,
            atsem_count=0,
            calculation_method="target",
            created_by_id=test_user_id,
        ),
    ]

    db_session.add_all(structures)
    await db_session.flush()

    return structures


@pytest.fixture
async def test_subject_hours_matrix(
    db_session: AsyncSession,
    test_budget_version: BudgetVersion,
    subjects: dict,
    academic_levels: dict,
    test_user_id: UUID,
) -> list[SubjectHoursMatrix]:
    """Create test subject hours matrix."""
    matrix = [
        SubjectHoursMatrix(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("4.5"),
            is_split=False,
            notes="Mathématiques 6ème",
            created_by_id=test_user_id,
        ),
        SubjectHoursMatrix(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            subject_id=subjects["FRENCH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("5.0"),
            is_split=False,
            notes="Français 6ème",
            created_by_id=test_user_id,
        ),
        SubjectHoursMatrix(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            subject_id=subjects["ENGLISH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("3.0"),
            is_split=True,
            notes="Anglais 6ème (split groups)",
            created_by_id=test_user_id,
        ),
    ]

    db_session.add_all(matrix)
    await db_session.flush()

    return matrix


@pytest.fixture
async def test_teacher_cost_params(
    db_session: AsyncSession,
    test_budget_version: BudgetVersion,
    teacher_categories: dict,
    academic_cycles: dict,
    test_user_id: UUID,
) -> list[TeacherCostParam]:
    """Create test teacher cost parameters."""
    params = [
        TeacherCostParam(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41863.00"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("0.00"),
            hsa_hourly_rate_sar=Decimal("200.00"),
            max_hsa_hours=Decimal("4.0"),
            notes="AEFE Detached Teacher",
            created_by_id=test_user_id,
        ),
        TeacherCostParam(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000.00"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("24000.00"),
            hsa_hourly_rate_sar=Decimal("150.00"),
            max_hsa_hours=Decimal("2.0"),
            notes="Local Secondary Teacher",
            created_by_id=test_user_id,
        ),
    ]

    db_session.add_all(params)
    await db_session.flush()

    return params


@pytest.fixture
async def test_fee_structure(
    db_session: AsyncSession,
    test_budget_version: BudgetVersion,
    academic_levels: dict,
    nationality_types: dict,
    fee_categories: dict,
    test_user_id: UUID,
) -> list[FeeStructure]:
    """Create test fee structure."""
    fees = [
        # Tuition for PS - French
        FeeStructure(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["PS"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            fee_category_id=fee_categories["TUITION"].id,
            amount_sar=Decimal("25000.00"),
            trimester=None,
            notes="PS Tuition - French",
            created_by_id=test_user_id,
        ),
        # DAI for PS - French
        FeeStructure(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["PS"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            fee_category_id=fee_categories["DAI"].id,
            amount_sar=Decimal("3000.00"),
            trimester=None,
            notes="PS DAI - French",
            created_by_id=test_user_id,
        ),
        # Tuition for 6EME - French
        FeeStructure(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            fee_category_id=fee_categories["TUITION"].id,
            amount_sar=Decimal("32000.00"),
            trimester=None,
            notes="6ème Tuition - French",
            created_by_id=test_user_id,
        ),
    ]

    db_session.add_all(fees)
    await db_session.flush()

    return fees


@pytest.fixture
async def test_dhg_data(
    db_session: AsyncSession,
    test_budget_version: BudgetVersion,
    subjects: dict,
    academic_levels: dict,
    test_class_structure: list[ClassStructure],
    test_subject_hours_matrix: list[SubjectHoursMatrix],
    test_user_id: UUID,
) -> dict:
    """Create test DHG hours and teacher requirements."""
    # DHG Subject Hours
    dhg_hours = [
        DHGSubjectHours(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            number_of_classes=3,
            hours_per_class_per_week=Decimal("4.5"),
            total_hours_per_week=Decimal("13.5"),  # 3 × 4.5
            is_split=False,
            created_by_id=test_user_id,
        ),
        DHGSubjectHours(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            subject_id=subjects["FRENCH"].id,
            level_id=academic_levels["6EME"].id,
            number_of_classes=3,
            hours_per_class_per_week=Decimal("5.0"),
            total_hours_per_week=Decimal("15.0"),  # 3 × 5.0
            is_split=False,
            created_by_id=test_user_id,
        ),
    ]

    # DHG Teacher Requirements
    teacher_requirements = [
        DHGTeacherRequirement(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            subject_id=subjects["MATH"].id,
            total_hours_per_week=Decimal("13.5"),
            standard_teaching_hours=Decimal("18.00"),
            simple_fte=Decimal("0.75"),  # 13.5 / 18
            rounded_fte=1,
            hsa_hours=Decimal("4.5"),  # 18 - 13.5
            created_by_id=test_user_id,
        ),
        DHGTeacherRequirement(
            id=uuid4(),
            budget_version_id=test_budget_version.id,
            subject_id=subjects["FRENCH"].id,
            total_hours_per_week=Decimal("15.0"),
            standard_teaching_hours=Decimal("18.00"),
            simple_fte=Decimal("0.83"),  # 15.0 / 18
            rounded_fte=1,
            hsa_hours=Decimal("3.0"),  # 18 - 15
            created_by_id=test_user_id,
        ),
    ]

    db_session.add_all(dhg_hours + teacher_requirements)
    await db_session.flush()

    return {
        "dhg_hours": dhg_hours,
        "teacher_requirements": teacher_requirements,
    }


# ==============================================================================
# System Configuration Fixtures
# ==============================================================================


@pytest.fixture
async def test_system_config(
    db_session: AsyncSession, test_user_id: UUID
) -> SystemConfig:
    """Create a test system configuration."""
    config = SystemConfig(
        id=uuid4(),
        key="eur_to_sar_rate",
        value={"rate": 4.05, "effective_date": "2025-01-01"},
        category="exchange_rates",
        description="EUR to SAR exchange rate",
        is_active=True,
        created_by_id=test_user_id,
    )

    db_session.add(config)
    await db_session.flush()

    return config
