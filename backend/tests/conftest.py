"""
Pytest configuration and fixtures for EFIR Budget Planning Application tests.

This file provides common fixtures and configuration for all tests.
"""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

# Import all models to ensure they're registered with SQLAlchemy
from app.models import *  # noqa: F403, F401
from app.models.base import Base


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

    Creates all tables in the test database.
    """
    engine = create_async_engine(
        test_database_url,
        echo=False,  # Set to True for SQL debugging
    )

    async with engine.begin() as conn:
        # SQLite needs an attached schema name to handle "efir_budget.*" table names.
        if test_database_url.startswith("sqlite"):
            await conn.execute(text("ATTACH DATABASE ':memory:' AS efir_budget"))
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
def sample_uuid() -> uuid4:
    """Generate a sample UUID for testing."""
    return uuid4()


# Add more fixtures as needed for specific test scenarios
