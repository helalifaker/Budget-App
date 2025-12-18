"""
EFIR Budget Planning Application - Admin Module Models.

This module contains all admin_* prefixed tables for administrative
operations, user management, and system-level auditing.

Table Categories:
-----------------
1. User Management:
   - admin_users: User stub for local development (production uses Supabase auth)
   - admin_organizations: Multi-tenant organization support

2. System Auditing:
   - admin_integration_logs: Audit log for integration operations

Note: IntegrationSettings (settings_integration) has been moved to settings.py
as it represents configuration data, not audit/admin data.

Module Architecture:
--------------------
This module supports the Admin EFIR module:
- Module: Admin
- Route: /admin/*
- Color: neutral
- Primary Role: Admin only
- Purpose: Data uploads, historical imports, system configuration

Integration Types:
------------------
- ODOO: Accounting system for actuals import
- SKOLENGO: Student information system for enrollment data
- AEFE: French education agency for position management

Multi-Tenancy:
--------------
The Organization model supports future multi-school deployments:
- Each organization has isolated data
- Users belong to one organization
- All version_id-scoped data is implicitly organization-scoped

Author: Claude Code
Date: 2025-12-16
Version: 1.0.0
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from sqlalchemy import UUID, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseModel, PortableJSON

# Check if running in test mode
PYTEST_RUNNING = os.environ.get("PYTEST_RUNNING")

# ==============================================================================
# User Management Models
# ==============================================================================


class User(Base):
    """
    Stub user model for local SQLite development.

    In production, this table is managed by Supabase Auth (auth.users schema).
    This stub model allows foreign key relationships to work during local
    development and testing.

    Production Note:
    ----------------
    In production (Supabase), the actual user data comes from:
    - auth.users: Supabase managed authentication table
    - Profile data: Can be extended via Supabase profiles

    This stub exists to:
    1. Enable SQLite-based local development without Supabase
    2. Provide FK targets for other models (e.g., dashboard ownership)
    3. Support testing with predictable user data

    Example Usage (Local Development):
    ----------------------------------
    # Create test user
    user = User(
        id=uuid.uuid4(),
        email="test@efir.edu.sa"
    )
    session.add(user)

    # Reference in other models
    dashboard = DashboardConfig(
        owner_user_id=user.id,
        name="My Dashboard",
        ...
    )
    """

    __tablename__ = "admin_users"

    # Conditional schema: PostgreSQL uses efir_budget, SQLite uses default
    if not PYTEST_RUNNING:
        __table_args__ = {"schema": "efir_budget"}

    # Primary fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user identifier (UUID)",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="User email address (unique)",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email})>"


class Organization(Base):
    """
    Multi-tenant organization model.

    Supports future multi-school deployments where each organization
    has isolated data. Currently, single-tenant but designed for scale.

    Multi-Tenancy Design:
    ---------------------
    1. Each organization has a unique ID
    2. All versioned data is scoped to organization via version_id
    3. Users belong to exactly one organization
    4. RLS policies enforce organization-level isolation

    Production Note:
    ----------------
    In production (Supabase), this table is managed via migrations.
    This stub model allows local development and testing.

    Example Organizations:
    ----------------------
    - EFIR Riyadh (current)
    - EFIR Jeddah (future expansion)
    - EFIR Dammam (future expansion)

    Example Usage:
    --------------
    org = Organization(
        id=uuid.uuid4(),
        name="EFIR Riyadh",
        is_active=True
    )
    """

    __tablename__ = "admin_organizations"

    # Conditional schema: PostgreSQL uses efir_budget, SQLite uses default
    if not PYTEST_RUNNING:
        __table_args__ = {"schema": "efir_budget"}

    # Primary fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique organization identifier (UUID)",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Organization name",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the organization is active",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Organization(id={self.id}, name={self.name})>"


# ==============================================================================
# Integration Audit Models
# ==============================================================================


class IntegrationLog(BaseModel):
    """
    Audit log for integration operations.

    Tracks all import/export operations with external systems (Odoo, Skolengo, AEFE).
    Provides audit trail for troubleshooting, compliance, and debugging.

    Integration Types:
    ------------------
    ODOO: Accounting system integration
        - import_actuals: Import actual financial data from GL
        - export_budget: Export budget data to Odoo
        - sync_accounts: Synchronize chart of accounts

    SKOLENGO: Student information system
        - import_enrollment: Import student enrollment data
        - import_grades: Import grade/level assignments
        - sync_students: Full student data sync

    AEFE: French education agency
        - import_positions: Import AEFE position allocations
        - sync_prrd: Synchronize PRRD contribution data
        - export_report: Export annual AEFE reporting

    Status Values:
    --------------
    - success: Operation completed successfully
    - failed: Operation failed completely
    - partial: Some records processed, some failed

    Example Log Entry:
    ------------------
    IntegrationLog(
        integration_type="odoo",
        action="import_actuals",
        status="success",
        records_processed=1250,
        records_failed=0,
        batch_id=uuid4(),
        metadata_json={
            "fiscal_year": 2025,
            "period": 10,
            "import_date": "2025-11-01T02:00:00Z"
        }
    )

    Querying Logs:
    --------------
    # Find failed operations in last 7 days
    SELECT * FROM admin_integration_logs
    WHERE status = 'failed'
    AND created_at > NOW() - INTERVAL '7 days'
    ORDER BY created_at DESC;

    # Get summary by integration type
    SELECT integration_type,
           COUNT(*) as total_ops,
           SUM(records_processed) as total_records,
           SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count
    FROM admin_integration_logs
    GROUP BY integration_type;
    """

    __tablename__ = "admin_integration_logs"

    if not PYTEST_RUNNING:
        __table_args__ = {"schema": "efir_budget"}

    # Integration Identification
    integration_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of integration: 'odoo', 'skolengo', or 'aefe'",
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Action performed: 'import_actuals', 'export_enrollment', etc.",
    )

    # Operation Status
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

    # Error Details
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if operation failed",
    )

    # Additional Metadata
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        PortableJSON,
        nullable=True,
        comment="Additional metadata (parameters, file names, etc.)",
    )

    # Batch Tracking
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
            f"action={self.action}, status={self.status}, "
            f"processed={self.records_processed})>"
        )

    @property
    def is_success(self) -> bool:
        """Check if operation was fully successful."""
        return self.status == "success"

    @property
    def has_failures(self) -> bool:
        """Check if any records failed."""
        return self.records_failed > 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total = self.records_processed + self.records_failed
        if total == 0:
            return 0.0
        return (self.records_processed / total) * 100


# ==============================================================================
# Backward Compatibility Aliases
# ==============================================================================

# No aliases needed - model names are already canonical
