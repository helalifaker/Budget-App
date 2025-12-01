"""
Alembic environment configuration for EFIR Budget Planning Application
Configured for async PostgreSQL with asyncpg driver targeting efir_budget schema
"""
import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment variable
# Falls back to .env.local for development
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Ensure we're using asyncpg driver for async support
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
    config.set_main_option("sqlalchemy.url", database_url)

# Import models for autogenerate support
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Base

target_metadata = Base.metadata

# Schema targeting - all migrations will be in efir_budget schema
SCHEMA_NAME = "efir_budget"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=SCHEMA_NAME,  # Store alembic_version in efir_budget schema
        include_schemas=True,
    )

    with context.begin_transaction():
        # Create schema if it doesn't exist
        context.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}")
        # Set search path to efir_budget schema
        context.execute(f"SET search_path TO {SCHEMA_NAME}, public")
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations with schema targeting."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=SCHEMA_NAME,  # Store alembic_version in efir_budget schema
        include_schemas=True,
    )

    with context.begin_transaction():
        # Create schema if it doesn't exist
        context.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}")
        # Set search path to efir_budget schema for all migrations
        context.execute(f"SET search_path TO {SCHEMA_NAME}, public")
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async support."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
