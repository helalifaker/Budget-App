"""
SQLAlchemy Base Models and Mixins for EFIR Budget Planning Application

This module provides common base classes and mixins for all database models.
All models include audit trails and follow consistent patterns.
"""

from __future__ import annotations

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

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created the record (NULL if system-generated or user deleted)",
    )

    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="SET NULL"),
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
    Mixin for tables that belong to a specific budget version.

    Most planning and configuration data is versioned to support
    multiple budget scenarios and historical tracking.
    """

    @declared_attr
    def budget_version_id(cls):
        """Foreign key to budget version."""
        return Column(
            UUID(as_uuid=True),
            ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Budget version this record belongs to",
        )

    @declared_attr
    def budget_version(cls):
        """Relationship to budget version."""
        return relationship(
            "BudgetVersion",
            foreign_keys=[cls.budget_version_id],
            lazy="select",
            # No back_populates - BudgetVersion doesn't have relationships to all versioned tables
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
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key (UUID)",
    )

    @declared_attr.directive
    def __table_args__(cls):
        """Set all tables to efir_budget schema."""
        return {"schema": "efir_budget", "comment": cls.__doc__}

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
        """Set all tables to efir_budget schema."""
        return {"schema": "efir_budget", "comment": cls.__doc__}

    def __repr__(self) -> str:
        """String representation of model."""
        if hasattr(self, "code"):
            return f"<{self.__class__.__name__}(code={self.code})>"
        if hasattr(self, "name"):
            return f"<{self.__class__.__name__}(name={self.name})>"
        return f"<{self.__class__.__name__}(id={self.id})>"
