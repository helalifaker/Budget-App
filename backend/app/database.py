"""
Database configuration and session management for EFIR Budget Planning Application.

Uses async PostgreSQL with SQLAlchemy 2.0 and asyncpg driver.
Connects to Supabase PostgreSQL with efir_budget schema isolation.
"""

import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.logging import logger

# Load environment variables from .env.local (development) or .env (production)
# Use override=True to ensure backend-specific values take precedence over root .env files
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file, override=False)
else:
    load_dotenv(override=False)  # Load from .env if .env.local doesn't exist

# Prefer lightweight in-memory SQLite during test runs to avoid external DBs
if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("PYTEST_RUNNING"):
    _raw_database_url = "sqlite+aiosqlite:///:memory:"
else:
    # Get database URL from environment
    _raw_database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/postgres",
    )

# Normalize URL scheme for SQLAlchemy 2.x compatibility
# - Convert 'postgres://' to 'postgresql://'
# - Ensure asyncpg driver is used
if _raw_database_url.startswith("postgres://"):
    DATABASE_URL = _raw_database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _raw_database_url.startswith("postgresql://") and "+asyncpg" not in _raw_database_url:
    DATABASE_URL = _raw_database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = _raw_database_url

# For migrations, use DIRECT_URL to bypass connection pooler
DIRECT_URL = os.getenv("DIRECT_URL", DATABASE_URL)


# Custom async connection creator for asyncpg with Supabase pooler compatibility
async def async_creator():
    """
    Custom async connection creator that disables prepared statements BEFORE
    SQLAlchemy uses the connection.

    This ensures that even SQLAlchemy's dialect initialization queries
    (like 'select pg_catalog.version()') don't use prepared statements.

    Required for compatibility with Supabase's pgBouncer/Supavisor poolers.
    """
    from urllib.parse import urlparse

    parsed = urlparse(DATABASE_URL)

    return await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        statement_cache_size=0,  # Disable prepared statement cache (critical for pgBouncer)
        server_settings={"jit": "off"},  # Disable JIT compilation
    )


# Create async engine
# - echo=True for development (logs SQL)
# - NullPool for serverless/connection pooler environments (Supabase)
# - Prepared statement caching disabled via connect_args
#
# IMPORTANT: Supabase uses connection pooling (pgBouncer/Supavisor) which can cause
# "DuplicatePreparedStatementError" when asyncpg reuses prepared statement names.
#
# Solution: Disable prepared statement caching by passing statement_cache_size=0 to asyncpg.
# This parameter MUST be passed as an integer (not string) via connect_args.
#
# References:
# - https://magicstack.github.io/asyncpg/current/faq.html
# - https://github.com/sqlalchemy/sqlalchemy/discussions/10246
# - https://github.com/orgs/supabase/discussions/36618
# - https://www.postgresql.org/docs/current/libpq-connect.html
if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        DATABASE_URL,
        echo=bool(os.getenv("SQL_ECHO", "False") == "True"),
        future=True,
    )
else:
    # For Supabase pgBouncer/Supavisor compatibility:
    # Use prepared_statement_name_func=lambda: "" to force inline queries
    # This completely bypasses prepared statement naming conflicts
    # Reference: https://github.com/MagicStack/asyncpg/issues/839
    import uuid as uuid_module

    def unique_stmt_name() -> str:
        """Generate unique statement name to avoid conflicts with pgBouncer."""
        return f"stmt_{uuid_module.uuid4().hex[:8]}"

    engine = create_async_engine(
        DATABASE_URL,
        echo=bool(os.getenv("SQL_ECHO", "False") == "True"),
        poolclass=NullPool,
        pool_pre_ping=False,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_name_func": unique_stmt_name,
            "server_settings": {"jit": "off"},
        },
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ============================================================================
# Query Performance Monitoring
# ============================================================================


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Event listener to track query start time.

    Stores the start time in the connection info dict for later use
    in the after_cursor_execute event.
    """
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Event listener to log slow queries.

    Logs queries that exceed the SLOW_QUERY_THRESHOLD (default: 100ms).
    Helps identify performance bottlenecks and N+1 query problems.

    Logged fields:
        - duration_seconds: Query execution time
        - statement: SQL query (truncated to 500 chars)
        - query_type: SELECT, INSERT, UPDATE, DELETE, etc.
    """
    # Get slow query threshold from environment (default: 100ms)
    slow_query_threshold = float(os.getenv("SLOW_QUERY_THRESHOLD", "0.1"))

    # Calculate query duration
    total = time.time() - conn.info["query_start_time"].pop(-1)

    if total > slow_query_threshold:
        # Extract query type (SELECT, INSERT, UPDATE, DELETE, etc.)
        query_type = statement.strip().split()[0].upper() if statement else "UNKNOWN"

        # Truncate statement for logging (avoid massive log entries)
        truncated_statement = statement[:500] + "..." if len(statement) > 500 else statement

        logger.warning(
            "slow_query",
            duration_seconds=round(total, 3),
            statement=truncated_statement,
            query_type=query_type,
            threshold_seconds=slow_query_threshold,
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

    Creates efir_budget schema (PostgreSQL only) and all tables.
    Should be run once during application setup or handled by Alembic migrations.

    For SQLite: Only creates tables (schemas not supported).
    For PostgreSQL: Creates efir_budget schema first, then tables.
    """
    # CRITICAL: Import from app.models (not app.models.base) to ensure ALL model
    # classes are imported and registered with Base.metadata before create_all().
    # Without this, tables won't be created because they're not in the metadata.
    from app.models import Base

    async with engine.begin() as conn:
        # Create efir_budget schema if it doesn't exist (PostgreSQL only)
        # SQLite doesn't support schemas, so skip this step
        if not DATABASE_URL.startswith("sqlite"):
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS efir_budget"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.

    Should be called during application shutdown.
    """
    await engine.dispose()
