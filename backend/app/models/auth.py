"""
Authentication and user models.

This module provides a stub User model for local SQLite development.
In production, Supabase Auth manages the auth.users table in PostgreSQL.
"""

from __future__ import annotations

import uuid

from sqlalchemy import UUID, Column, String

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
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email})>"
