"""
SQLAlchemy Base Models and Mixins for EFIR Budget Planning Application

This module provides common base classes and mixins for all database models.
All models include audit trails and follow consistent patterns.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, UUID, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

# Base class for all models
Base = declarative_base()


# ==============================================================================
# Test Environment Detection and Schema Configuration
# ==============================================================================

def is_test_environment() -> bool:
    """Check if running in test environment (SQLite)."""
    return os.environ.get("PYTEST_RUNNING", "").lower() == "true"


def get_schema(schema_name: str) -> str | None:
    """
    Get schema name based on environment.

    Returns None for SQLite tests (no schema support),
    Returns actual schema name for PostgreSQL production.
    """
    if is_test_environment():
        return None
    return schema_name


def get_fk_target(schema: str, table: str, column: str) -> str:
    """
    Get ForeignKey target string based on environment.

    Returns "table.column" for SQLite tests,
    Returns "schema.table.column" for PostgreSQL production.
    """
    if is_test_environment():
        return f"{table}.{column}"
    return f"{schema}.{table}.{column}"


def get_table_args(*args, schema: str = "efir_budget", comment: str | None = None) -> tuple:
    """
    Get table args tuple with conditional schema based on environment.

    Use this in models that override __table_args__ to ensure SQLite test compatibility.

    Args:
        *args: Any SQLAlchemy constraints (UniqueConstraint, Index, etc.)
        schema: Schema name for PostgreSQL production (default: "efir_budget")
        comment: Table comment/docstring

    Returns:
        Tuple of constraints + dict with schema (or without for tests)

    Example:
        __table_args__ = get_table_args(
            UniqueConstraint("level_id", "fiscal_year", name="uq_enrollment_level_year"),
            comment=__doc__
        )
    """
    table_dict: dict = {}
    if not is_test_environment():
        table_dict["schema"] = schema
    if comment:
        table_dict["comment"] = comment

    if args:
        return (*args, table_dict)
    return (table_dict,)


# ==============================================================================
# Portable JSON Type (JSONB for PostgreSQL, JSON for SQLite)
# ==============================================================================


class PortableJSON(TypeDecorator):
    """
    JSON type that uses JSONB for PostgreSQL and JSON for other databases.

    This allows the same model definitions to work in both production
    (PostgreSQL with JSONB) and tests (SQLite with JSON).
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


# For backward compatibility, export as JSONB-like type
JSONBPortable = PortableJSON


# ==============================================================================
# Portable UUID Type (UUID for PostgreSQL, String for SQLite)
# ==============================================================================


class PortableUUID(TypeDecorator):
    """
    UUID type that works with both PostgreSQL and SQLite.

    PostgreSQL has native UUID support.
    SQLite stores UUIDs as strings (36-character hex format with hyphens).

    This allows the same model definitions to work in both production
    (PostgreSQL with native UUID) and tests/development (SQLite with strings).
    """

    impl = UUID
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            # For SQLite and other databases, store as string
            from sqlalchemy import String
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        """Convert Python UUID to database format."""
        if value is None:
            return None
        if dialect.name == "postgresql":
            # PostgreSQL handles UUID natively
            return value
        else:
            # SQLite: convert UUID to string
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(uuid.UUID(str(value)))  # Ensure proper UUID format

    def process_result_value(self, value, dialect):
        """Convert database value to Python UUID."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        # Convert string or integer to UUID
        try:
            if isinstance(value, int):
                # SQLite sometimes stores as integer
                return uuid.UUID(int=value)
            return uuid.UUID(str(value))
        except (ValueError, TypeError):
            # If conversion fails, return None or raise
            return None


class AuditMixin:
    """
    Audit trail fields for all tables.

    Tracks who created/updated records and when.

    Note: created_by_id and updated_by_id reference auth.users.id (Supabase Auth),
    but no SQLAlchemy User model is defined to avoid complexity. Use direct
    queries to auth.users when user details are needed.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When the record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="When the record was last updated",
    )

    @declared_attr
    def created_by_id(cls) -> Mapped[uuid.UUID | None]:
        """Reference to user who created the record.

        Note: No ForeignKey constraint at ORM level because auth.users is managed
        by Supabase and doesn't have a corresponding SQLAlchemy model.
        The database FK constraint is managed via migrations.
        """
        return mapped_column(
            PortableUUID,
            nullable=True,
            comment="User who created the record (NULL if system-generated or user deleted)",
        )

    @declared_attr
    def updated_by_id(cls) -> Mapped[uuid.UUID | None]:
        """Reference to user who last updated the record.

        Note: No ForeignKey constraint at ORM level because auth.users is managed
        by Supabase and doesn't have a corresponding SQLAlchemy model.
        The database FK constraint is managed via migrations.
        """
        return mapped_column(
            PortableUUID,
            nullable=True,
            comment="User who last updated the record (NULL if system-updated or user deleted)",
        )

    # No relationships to User model - query auth.users directly when needed
    # This avoids circular dependencies and keeps auth separate from business logic


class SoftDeleteMixin:
    """
    Soft delete functionality for tables that need audit history.

    Records are marked as deleted rather than physically removed.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="When the record was soft-deleted (NULL if active)",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.deleted_at = None


class VersionedMixin:
    """
    Mixin for tables that belong to a specific version.

    Most planning and configuration data is versioned to support
    multiple budget scenarios and historical tracking.

    Note: Column renamed from budget_version_id to version_id for consistency.
    """

    @declared_attr
    def version_id(cls):
        """Foreign key to version."""
        return Column(
            PortableUUID,
            ForeignKey(get_fk_target("efir_budget", "settings_versions", "id"), ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Version this record belongs to",
        )

    @declared_attr
    def version(cls):
        """Relationship to version."""
        return relationship(
            "Version",
            foreign_keys=[cls.version_id],
            lazy="select",
            # No back_populates - Version doesn't have relationships to all versioned tables
        )


class BaseModel(Base, AuditMixin, SoftDeleteMixin):
    """
    Base model class for all EFIR budget tables.

    Includes:
    - UUID primary key
    - Audit trail (created_at, updated_at, created_by_id, updated_by_id)
    - Soft delete support (deleted_at)
    - Table args for schema specification

    All tables support soft deletion to maintain audit history and comply
    with AEFE data retention requirements.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key (UUID)",
    )

    @declared_attr.directive
    def __table_args__(cls):
        """Set all tables to efir_budget schema (None for SQLite tests)."""
        schema = get_schema("efir_budget")
        if schema:
            return {"schema": schema, "comment": cls.__doc__}
        return {"comment": cls.__doc__}

    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary.

        Useful for API responses and debugging.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TimestampMixin:
    """
    Simple timestamp mixin without user tracking.

    Use for reference/lookup tables that don't need full audit trails.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When the record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="When the record was last updated",
    )


class ReferenceDataModel(Base, TimestampMixin):
    """
    Base model for reference/lookup tables (cycles, levels, subjects, etc.).

    These tables:
    - Don't need full audit trails (no created_by/updated_by)
    - Are mostly read-only after initial setup
    - Provide dropdown options and lookups
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key (UUID)",
    )

    @declared_attr.directive
    def __table_args__(cls):
        """Set all tables to efir_budget schema (None for SQLite tests)."""
        schema = get_schema("efir_budget")
        if schema:
            return {"schema": schema, "comment": cls.__doc__}
        return {"comment": cls.__doc__}

    def __repr__(self) -> str:
        """String representation of model."""
        if hasattr(self, "code"):
            return f"<{self.__class__.__name__}(code={self.code})>"
        if hasattr(self, "name"):
            return f"<{self.__class__.__name__}(name={self.name})>"
        return f"<{self.__class__.__name__}(id={self.id})>"
