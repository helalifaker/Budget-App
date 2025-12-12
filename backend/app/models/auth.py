"""
Authentication and user models.

This module provides stub User and Organization models for local SQLite development.
In production, Supabase Auth manages the auth.users table, and the organizations
table is managed via Supabase migrations.
"""

from __future__ import annotations

import uuid as uuid_module

from sqlalchemy import UUID, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import DATABASE_URL
from app.models.base import Base


class User(Base):
    """
    Stub user model for local SQLite development.

    In production, this table is managed by Supabase Auth (auth.users schema).
    This stub model allows foreign key relationships to work during local development.

    Attributes:
        id: Unique user identifier (UUID)
        email: User's email address (unique)
    """

    __tablename__ = "users"

    # Conditional schema assignment: PostgreSQL uses efir_budget, SQLite uses default
    if not DATABASE_URL.startswith("sqlite"):
        __table_args__ = {"schema": "efir_budget"}

    # Primary fields - UUID type to match foreign key references
    id: Mapped[uuid_module.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email})>"


class Organization(Base):
    """
    Stub organization model for local SQLite development.

    In production, this table is managed via Supabase migrations.
    This stub model allows foreign key relationships to work during local development
    and testing with SQLite.

    Attributes:
        id: Unique organization identifier (UUID)
        name: Organization name
        is_active: Whether the organization is active
    """

    __tablename__ = "organizations"

    # Conditional schema assignment: PostgreSQL uses efir_budget, SQLite uses default
    if not DATABASE_URL.startswith("sqlite"):
        __table_args__ = {"schema": "efir_budget"}

    # Primary fields - UUID type to match foreign key references
    id: Mapped[uuid_module.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        """String representation of Organization."""
        return f"<Organization(id={self.id}, name={self.name})>"
