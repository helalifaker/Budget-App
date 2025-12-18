"""Add missing audit columns to enrollment derived parameter tables.

This migration adds the missing audit columns (created_by_id, updated_by_id, deleted_at)
to the enrollment tables created in migration 019. These columns are expected by the
BaseModel class which EnrollmentDerivedParameter, EnrollmentParameterOverride, and
EnrollmentScenarioMultiplier inherit from.

Revision ID: 020_audit_columns_enrollment
Revises: 019_enrollment_derived_parameters
Create Date: 2025-12-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "020_audit_columns_enrollment"
down_revision = "019_enrollment_derived_parameters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing audit columns to enrollment tables."""

    # =========================================================================
    # 1. enrollment_derived_parameters - Add audit columns
    # =========================================================================
    op.add_column(
        "enrollment_derived_parameters",
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="efir_budget",
    )
    op.add_column(
        "enrollment_derived_parameters",
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="efir_budget",
    )
    op.add_column(
        "enrollment_derived_parameters",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        schema="efir_budget",
    )

    # =========================================================================
    # 2. enrollment_parameter_overrides - Add audit columns
    # =========================================================================
    op.add_column(
        "enrollment_parameter_overrides",
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="efir_budget",
    )
    op.add_column(
        "enrollment_parameter_overrides",
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="efir_budget",
    )
    op.add_column(
        "enrollment_parameter_overrides",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        schema="efir_budget",
    )

    # =========================================================================
    # 3. enrollment_scenario_multipliers - Add audit columns
    # =========================================================================
    op.add_column(
        "enrollment_scenario_multipliers",
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="efir_budget",
    )
    op.add_column(
        "enrollment_scenario_multipliers",
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="efir_budget",
    )
    op.add_column(
        "enrollment_scenario_multipliers",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        schema="efir_budget",
    )


def downgrade() -> None:
    """Remove audit columns from enrollment tables."""

    # enrollment_scenario_multipliers
    op.drop_column("enrollment_scenario_multipliers", "deleted_at", schema="efir_budget")
    op.drop_column("enrollment_scenario_multipliers", "updated_by_id", schema="efir_budget")
    op.drop_column("enrollment_scenario_multipliers", "created_by_id", schema="efir_budget")

    # enrollment_parameter_overrides
    op.drop_column("enrollment_parameter_overrides", "deleted_at", schema="efir_budget")
    op.drop_column("enrollment_parameter_overrides", "updated_by_id", schema="efir_budget")
    op.drop_column("enrollment_parameter_overrides", "created_by_id", schema="efir_budget")

    # enrollment_derived_parameters
    op.drop_column("enrollment_derived_parameters", "deleted_at", schema="efir_budget")
    op.drop_column("enrollment_derived_parameters", "updated_by_id", schema="efir_budget")
    op.drop_column("enrollment_derived_parameters", "created_by_id", schema="efir_budget")
