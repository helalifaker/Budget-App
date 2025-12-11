"""
Pytest configuration and fixtures for EFIR Budget Planning Application tests.

This file provides common fixtures and configuration for all tests, including:
- Database setup (worker-isolated SQLite for parallel testing)
- Sample data fixtures
- Budget version fixtures
- Configuration fixtures
- Authentication mocks

NOTE: This configuration supports pytest-xdist parallel execution by using
unique IN-MEMORY SQLite databases per worker with distinct connection URIs.
"""

import itertools
import os
import tempfile
from pathlib import Path

# ==============================================================================
# CRITICAL: Set test environment variables BEFORE importing app modules
# ==============================================================================
# This must happen before any app imports because app/database.py reads
# environment variables at import time to configure the database engine.

# Force lightweight SQLite database for tests to avoid external dependencies
os.environ["USE_SQLITE_FOR_TESTS"] = "true"
os.environ["PYTEST_RUNNING"] = "true"
os.environ["REDIS_ENABLED"] = "false"

# Create worker-specific database URL for pytest-xdist parallel execution
# Each worker gets its own SQLite file to prevent "index already exists" errors
_worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")

# Use PID-based unique temp directory for additional isolation
# This ensures each pytest run (even concurrent ones) gets unique databases
_pid = os.getpid()
_temp_dir = Path(tempfile.gettempdir()) / f"efir_test_dbs_{_pid}"
_temp_dir.mkdir(exist_ok=True)
_WORKER_DB_PATH: Path = _temp_dir / f"test_efir_{_worker_id}.db"

# Clean up any existing database file from previous runs
if _WORKER_DB_PATH.exists():
    try:
        _WORKER_DB_PATH.unlink()
    except OSError:
        pass  # File might be locked, will be overwritten

# Set TEST_DATABASE_URL so app/database.py uses the worker-specific file
_worker_db_url = f"sqlite+aiosqlite:///{_WORKER_DB_PATH}"
os.environ["TEST_DATABASE_URL"] = _worker_db_url
print(f"\n🔧 Worker {_worker_id} (PID {_pid}): Using database at {_WORKER_DB_PATH}")

# ==============================================================================
# Now safe to import app modules
# ==============================================================================

import asyncio
from collections.abc import AsyncGenerator, Generator, Callable
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

# Import all models to ensure they're registered with SQLAlchemy
from app.models import *  # noqa: F403

# Import User from app.models.auth (already imported via `from app.models import *`)
# The User model in auth.py properly handles both SQLite and PostgreSQL schemas
from app.models.auth import User  # Re-import explicitly for clarity
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
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ==============================================================================
# Pytest Hooks for Database Setup and Cleanup
# ==============================================================================


def pytest_configure(config):
    """
    Pytest hook called early during pytest startup.

    Ensures test environment is properly configured before any tests run.
    This hook runs BEFORE test collection, making it ideal for environment setup.
    """
    # Ensure test flags are set (belt and suspenders approach)
    os.environ["PYTEST_RUNNING"] = "true"
    os.environ["USE_SQLITE_FOR_TESTS"] = "true"
    os.environ["REDIS_ENABLED"] = "false"


def pytest_unconfigure(config):
    """
    Pytest hook called before test process exits.

    Cleans up the worker-specific SQLite database file and temp directory.
    """
    if _WORKER_DB_PATH and _WORKER_DB_PATH.exists():
        try:
            _WORKER_DB_PATH.unlink()
            print(f"\n🧹 Cleaned up test database: {_WORKER_DB_PATH}")
        except OSError:
            pass  # Best effort cleanup

    # Clean up the temp directory if empty
    if _temp_dir and _temp_dir.exists():
        try:
            # Only remove if empty (other workers might still be using it)
            if not list(_temp_dir.iterdir()):
                _temp_dir.rmdir()
        except OSError:
            pass


def get_worker_database_url() -> str:
    """
    Get the worker-specific SQLite database URL.

    Returns a file-based SQLite URL unique to the current pytest-xdist worker,
    preventing parallel test execution conflicts.
    """
    return _worker_db_url

# ==============================================================================
# CRITICAL: Strip schemas IMMEDIATELY after models are imported
# ==============================================================================
# This must run at module import time, BEFORE any ORM mappers are configured.
# If we wait until a fixture, the mappers will already have cached the schema refs.

def _strip_all_schemas_from_metadata():
    """
    Strip PostgreSQL schemas from all tables and ForeignKeys at import time.

    This is necessary because SQLite doesn't support PostgreSQL-style schemas,
    and SQLAlchemy ORM mappers cache FK references during import.
    """
    # Step 1: Strip schema from all tables
    for table in Base.metadata.tables.values():
        table.schema = None

    # Step 2: Strip schema from all ForeignKey constraints
    for table in Base.metadata.tables.values():
        for constraint in table.constraints:
            if hasattr(constraint, 'elements'):
                for fk_element in constraint.elements:
                    if hasattr(fk_element, '_colspec'):
                        original_colspec = fk_element._colspec
                        if '.' in original_colspec:
                            parts = original_colspec.split('.')
                            if len(parts) == 3:  # schema.table.column
                                fk_element._colspec = f"{parts[1]}.{parts[2]}"

    # Step 3: Strip schema from columns that have ForeignKey references
    for table in Base.metadata.tables.values():
        for column in table.columns:
            for fk in column.foreign_keys:
                if hasattr(fk, '_colspec'):
                    original_colspec = fk._colspec
                    if '.' in original_colspec:
                        parts = original_colspec.split('.')
                        if len(parts) == 3:  # schema.table.column
                            fk._colspec = f"{parts[1]}.{parts[2]}"

# Run immediately at import time for SQLite tests
if os.environ.get("USE_SQLITE_FOR_TESTS", "").lower() == "true":
    _strip_all_schemas_from_metadata()
    print(f"✅ Stripped schemas from {len(Base.metadata.tables)} tables at import time")


# ==============================================================================
# SQLite Schema Stripping for Cross-Database Compatibility
# ==============================================================================


def strip_schema_from_sql(sql_str: str) -> str:
    """
    Strip PostgreSQL schema prefixes from SQL for SQLite compatibility.

    Converts:
        efir_budget.table_name -> table_name
        auth.users -> users

    This is necessary because SQLite doesn't support PostgreSQL-style schemas.
    """
    import re

    # Replace schema.table patterns with just table
    # Match efir_budget.table_name or auth.table_name
    sql_str = re.sub(r'\befir_budget\.', '', sql_str)
    sql_str = re.sub(r'\bauth\.', '', sql_str)

    return sql_str


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

    Uses file-based SQLite with worker-specific paths for pytest-xdist isolation.
    Each parallel worker gets its own database file to prevent conflicts.

    For integration tests with PostgreSQL, override this fixture.
    """
    return get_worker_database_url()


@pytest.fixture(scope="session")
async def engine(test_database_url: str):
    """
    Create async database engine for tests.

    Creates all tables in the test database including auth schema.
    Uses file-based SQLite with worker isolation for pytest-xdist parallel execution.

    IMPORTANT: For pytest-xdist, each worker gets its own database file,
    which is cleaned up after the test session ends.
    """
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")

    # For SQLite, use schema translation to strip PostgreSQL schemas
    # This is the recommended SQLAlchemy 2.0 approach for cross-database compatibility
    if test_database_url.startswith("sqlite"):
        test_engine = create_async_engine(
            test_database_url,
            echo=False,  # Set to True for SQL debugging
            execution_options={
                "schema_translate_map": {
                    "efir_budget": None,  # Translate efir_budget schema to no schema
                    "auth": None,  # Translate auth schema to no schema
                }
            },
        )
    else:
        test_engine = create_async_engine(
            test_database_url,
            echo=False,
        )

    async with test_engine.begin() as conn:
        if test_database_url.startswith("sqlite"):
            # Step 1: Ensure schemas are stripped from Base.metadata
            # SQLite doesn't support PostgreSQL-style schemas
            for table in Base.metadata.tables.values():
                table.schema = None

            # Step 2: FORCE drop all objects using raw SQL
            # This is more reliable than SQLAlchemy's drop_all for SQLite
            # because it ensures indexes are dropped before tables
            print(f"\n🗑️ Worker {worker_id}: Force-dropping all SQLite objects...")

            # Get all indexes and drop them first
            index_result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
            )
            indexes = [row[0] for row in index_result.fetchall()]
            for idx_name in indexes:
                try:
                    await conn.execute(text(f'DROP INDEX IF EXISTS "{idx_name}"'))
                except Exception:
                    pass  # Index might be auto-dropped with table

            # Get all tables and drop them
            table_result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            )
            tables = [row[0] for row in table_result.fetchall()]
            for table_name in tables:
                try:
                    await conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
                except Exception:
                    pass  # Table might have dependencies

            # Also call SQLAlchemy's drop_all for completeness
            await conn.run_sync(Base.metadata.drop_all)

            # Verify database is now empty
            verify_result = await conn.execute(
                text("SELECT type, name FROM sqlite_master WHERE type IN ('table', 'index') AND name NOT LIKE 'sqlite_%'")
            )
            remaining = [(row[0], row[1]) for row in verify_result.fetchall()]
            if remaining:
                print(f"⚠️ Worker {worker_id}: Still have {len(remaining)} objects after cleanup: {remaining[:5]}...")
            else:
                print(f"✅ Worker {worker_id}: Database is clean")

            print(f"\n🔍 Worker {worker_id}: Creating {len(Base.metadata.tables)} tables...")

            # Step 3: Create all tables fresh
            await conn.run_sync(Base.metadata.create_all)

            # Verify tables were created
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Worker {worker_id}: Created {len(tables)} tables in SQLite")
        else:
            # PostgreSQL: Create all tables with original metadata
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    yield test_engine

    await test_engine.dispose()


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
    )
    elementaire = AcademicCycle(
        id=uuid4(),
        code="ELEMENTAIRE",
        name_en="Elementary",
        name_fr="Élémentaire",
        sort_order=2,
        requires_atsem=False,
    )
    college = AcademicCycle(
        id=uuid4(),
        code="COLLEGE",
        name_en="Middle School",
        name_fr="Collège",
        sort_order=3,
        requires_atsem=False,
    )
    lycee = AcademicCycle(
        id=uuid4(),
        code="LYCEE",
        name_en="High School",
        name_fr="Lycée",
        sort_order=4,
        requires_atsem=False,
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
        # Elementary levels (Élémentaire) - CE1 through CM2
        "CE1": AcademicLevel(
            id=uuid4(),
            code="CE1",
            name_en="CE1",
            name_fr="CE1",
            cycle_id=academic_cycles["elementaire"].id,
            sort_order=5,
            is_secondary=False,
        ),
        "CE2": AcademicLevel(
            id=uuid4(),
            code="CE2",
            name_en="CE2",
            name_fr="CE2",
            cycle_id=academic_cycles["elementaire"].id,
            sort_order=6,
            is_secondary=False,
        ),
        "CM1": AcademicLevel(
            id=uuid4(),
            code="CM1",
            name_en="CM1",
            name_fr="CM1",
            cycle_id=academic_cycles["elementaire"].id,
            sort_order=7,
            is_secondary=False,
        ),
        "CM2": AcademicLevel(
            id=uuid4(),
            code="CM2",
            name_en="CM2",
            name_fr="CM2",
            cycle_id=academic_cycles["elementaire"].id,
            sort_order=8,
            is_secondary=False,
        ),
        # Middle school levels (Collège) - 4ème and 3ème
        "4EME": AcademicLevel(
            id=uuid4(),
            code="4EME",
            name_en="4ème",
            name_fr="4ème",
            cycle_id=academic_cycles["college"].id,
            sort_order=13,
            is_secondary=True,
        ),
        "3EME": AcademicLevel(
            id=uuid4(),
            code="3EME",
            name_en="3ème",
            name_fr="3ème",
            cycle_id=academic_cycles["college"].id,
            sort_order=14,
            is_secondary=True,
        ),
        # High school levels (Lycée) - 2nde, 1ère, Terminale
        "2NDE": AcademicLevel(
            id=uuid4(),
            code="2NDE",
            name_en="2nde",
            name_fr="2nde",
            cycle_id=academic_cycles["lycee"].id,
            sort_order=15,
            is_secondary=True,
        ),
        "1ERE": AcademicLevel(
            id=uuid4(),
            code="1ERE",
            name_en="1ère",
            name_fr="1ère",
            cycle_id=academic_cycles["lycee"].id,
            sort_order=16,
            is_secondary=True,
        ),
        "TERM": AcademicLevel(
            id=uuid4(),
            code="TERM",
            name_en="Terminale",
            name_fr="Terminale",
            cycle_id=academic_cycles["lycee"].id,
            sort_order=17,
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
    """Create subjects for testing, using existing subjects if they already exist."""
    from sqlalchemy import select

    # Define subject data to create
    subjects_to_create = [
        ("FRENCH", "French Language", "Français", "core"),
        ("MATH", "Mathematics", "Mathématiques", "core"),
        ("HISTORY", "History-Geography", "Histoire-Géographie", "core"),
        ("ENGLISH", "English", "Anglais", "core"),
        ("SVT", "Life and Earth Sciences", "Sciences de la Vie et de la Terre", "specialty"),
        ("PHYS", "Physics-Chemistry", "Physique-Chimie", "core"),
        ("LV2", "Second Foreign Language", "Langue Vivante 2", "core"),
        ("PHILO", "Philosophy", "Philosophie", "core"),
        ("ECO", "Economics", "Sciences Économiques", "specialty"),
        ("ART", "Visual Arts", "Arts Plastiques", "elective"),
        ("EPS", "Physical Education", "Éducation Physique et Sportive", "core"),
        ("MUS", "Music Education", "Éducation Musicale", "elective"),
    ]

    # Get existing subjects first
    codes = [s[0] for s in subjects_to_create]
    result = await db_session.execute(
        select(Subject).where(Subject.code.in_(codes))
    )
    existing_subjects = {s.code: s for s in result.scalars().all()}

    # Create missing subjects
    subjects_data = {}
    for code, name_en, name_fr, category in subjects_to_create:
        if code in existing_subjects:
            subjects_data[code] = existing_subjects[code]
        else:
            subject = Subject(
                id=uuid4(),
                code=code,
                name_en=name_en,
                name_fr=name_fr,
                category=category,
                is_active=True,
            )
            db_session.add(subject)
            subjects_data[code] = subject

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
            account_code="70110",
            is_recurring=True,
            allows_sibling_discount=True,
        ),
        "DAI": FeeCategory(
            id=uuid4(),
            code="DAI",
            name_en="Annual Enrollment Fee",
            name_fr="Droit Annuel d'Inscription",
            account_code="70140",
            is_recurring=True,
            allows_sibling_discount=False,
        ),
        "REGISTRATION": FeeCategory(
            id=uuid4(),
            code="REGISTRATION",
            name_en="Registration Fee",
            name_fr="Frais d'Inscription",
            account_code="70150",
            is_recurring=False,
            allows_sibling_discount=False,
        ),
    }

    db_session.add_all(categories.values())
    await db_session.flush()

    return categories


# ==============================================================================
# Budget Version Fixtures
# ==============================================================================

# Worker-aware fiscal year counter to prevent collisions in parallel test execution
# Each pytest-xdist worker gets a unique 10-year range within valid bounds (2000-2100):
#   master (single-process): 2025, 2026, ...
#   gw0: 2030, 2031, ...
#   gw1: 2040, 2041, ...
#   gw2: 2050, 2051, ...
# This ensures fiscal years stay within StrategicPlan's CHECK constraint (2000-2100)
def _get_worker_fiscal_year_base() -> int:
    """Calculate base fiscal year based on pytest-xdist worker ID."""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    if worker_id == "master":
        return 2025
    try:
        worker_num = int(worker_id.replace("gw", ""))
        # Use 10-year gaps: gw0=2030, gw1=2040, gw2=2050, etc.
        return 2030 + (worker_num * 10)
    except ValueError:
        return 2025


_fiscal_year_counter = itertools.count(_get_worker_fiscal_year_base())


@pytest.fixture
def fiscal_year_factory() -> Callable[[], int]:
    """Return a callable that generates unique fiscal years per worker."""
    return lambda: next(_fiscal_year_counter)


@pytest.fixture
async def test_budget_version(
    db_session: AsyncSession, test_user_id: UUID, fiscal_year_factory
) -> BudgetVersion:
    """Create a test budget version."""
    fiscal_year = fiscal_year_factory()
    version = BudgetVersion(
        id=uuid4(),
        name=f"FY{fiscal_year} Budget v1",
        fiscal_year=fiscal_year,
        academic_year=f"{fiscal_year-1}-{fiscal_year}",
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


@pytest.fixture
async def system_configs(
    db_session: AsyncSession, test_user_id: UUID
) -> dict[str, SystemConfig]:
    """Create comprehensive system configurations for integration tests."""
    configs = {
        "EUR_TO_SAR_RATE": SystemConfig(
            id=uuid4(),
            key="eur_to_sar_rate",
            value={"rate": 3.75, "effective_date": "2025-01-01"},
            category="exchange_rates",
            description="EUR to SAR exchange rate for AEFE cost calculations",
            is_active=True,
            created_by_id=test_user_id,
        ),
        "SCHOOL_CAPACITY": SystemConfig(
            id=uuid4(),
            key="school_capacity",
            value={"max_students": 1875, "warning_threshold": 1800},
            category="general",
            description="Maximum student enrollment capacity",
            is_active=True,
            created_by_id=test_user_id,
        ),
        "FISCAL_YEAR_START": SystemConfig(
            id=uuid4(),
            key="fiscal_year_start",
            value={"month": 1, "day": 1, "format": "MM-DD"},
            category="general",
            description="Fiscal year start date (January 1st)",
            is_active=True,
            created_by_id=test_user_id,
        ),
    }

    db_session.add_all(configs.values())
    await db_session.flush()

    return configs


# ==============================================================================
# API Test Client Fixture
# ==============================================================================


@pytest.fixture(scope="module")
def client(engine):
    """
    Create test client for API tests.

    IMPORTANT: This fixture depends on 'engine' to ensure the session-scoped
    database setup completes BEFORE TestClient is created. This prevents
    "index already exists" errors from competing create_all() calls.

    The engine fixture handles all table creation; startup_event's init_db()
    is skipped when PYTEST_RUNNING is set.

    This fixture is module-scoped for efficiency - one client per test module.

    Usage in API tests:
        def test_my_endpoint(client):
            response = client.get("/api/v1/some-endpoint")
    """
    from app.main import app
    from starlette.testclient import TestClient

    # Use context manager to trigger startup/shutdown events
    # Note: init_db() in startup_event is skipped due to PYTEST_RUNNING env var
    with TestClient(app) as test_client:
        yield test_client
