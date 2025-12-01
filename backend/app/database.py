"""
Database configuration and session management for EFIR Budget Planning Application.

Uses async PostgreSQL with SQLAlchemy 2.0 and asyncpg driver.
Connects to Supabase PostgreSQL with efir_budget schema isolation.
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/postgres",
)

# For migrations, use DIRECT_URL to bypass connection pooler
DIRECT_URL = os.getenv("DIRECT_URL", DATABASE_URL)

# Create async engine
# - echo=True for development (logs SQL)
# - pool_pre_ping=True to handle stale connections
# - NullPool for serverless/connection pooler environments (Supabase)
engine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.getenv("SQL_ECHO", "False") == "True"),
    pool_pre_ping=True,
    poolclass=NullPool,  # Recommended for Supabase connection pooler
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.

    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session

    Ensures session is closed after use, even if exception occurs.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database schema.

    Creates efir_budget schema and all tables.
    Should be run once during application setup or handled by Alembic migrations.
    """
    from app.models.base import Base

    async with engine.begin() as conn:
        # Create efir_budget schema if it doesn't exist
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS efir_budget"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.

    Should be called during application shutdown.
    """
    await engine.dispose()
