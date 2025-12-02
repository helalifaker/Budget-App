"""
SQLAlchemy Models for Integration Management

This module defines models for tracking external system integrations:
- IntegrationLog: Audit log for all integration operations
- IntegrationSettings: Configuration storage for integration connections
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, PortableJSON


class IntegrationLog(BaseModel):
    """
    Audit log for integration operations.

    Tracks all import/export operations with external systems (Odoo, Skolengo, AEFE).
    Provides audit trail for troubleshooting and compliance.
    """

    __tablename__ = "integration_logs"

    integration_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of integration: 'odoo', 'skolengo', or 'aefe'",
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Action performed: 'import_actuals', 'export_enrollment', 'import_positions', etc.",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Operation status: 'success', 'failed', or 'partial'",
    )

    records_processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of records successfully processed",
    )

    records_failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of records that failed to process",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if operation failed",
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        PortableJSON,
        nullable=True,
        comment="Additional metadata about the operation (parameters, file names, etc.)",
    )

    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Batch identifier for grouping related operations",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<IntegrationLog(type={self.integration_type}, "
            f"action={self.action}, status={self.status})>"
        )


class IntegrationSettings(BaseModel):
    """
    Configuration settings for external integrations.

    Stores connection details and configuration for each integration type.
    Sensitive data (passwords, API keys) should be encrypted before storage.
    """

    __tablename__ = "integration_settings"

    integration_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Type of integration: 'odoo', 'skolengo', or 'aefe'",
    )

    config: Mapped[dict[str, Any]] = mapped_column(
        PortableJSON,
        nullable=False,
        default=dict,
        comment="Integration configuration (URLs, credentials, etc.). Sensitive data should be encrypted.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this integration is currently active",
    )

    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful sync",
    )

    auto_sync_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether automatic syncing is enabled",
    )

    auto_sync_interval_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Interval in minutes for automatic syncing (if enabled)",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<IntegrationSettings(type={self.integration_type}, "
            f"active={self.is_active})>"
        )
