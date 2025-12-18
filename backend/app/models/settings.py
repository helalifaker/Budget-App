"""
SQLAlchemy Models for Settings Module (settings_* tables).

This module contains all configuration and settings tables that drive
budget calculations and system behavior:

Tables:
- settings_system_configs: Global system configuration key-value pairs
- settings_versions: Budget version control (formerly budget_versions)
- settings_class_size_params: Class size parameters per level
- settings_subject_hours_matrix: Subject hours per level (DHG matrix)
- settings_teacher_cost_params: Teacher cost parameters per category
- settings_fee_structure: Fee amounts per level/nationality/category
- settings_timetable_constraints: Scheduling constraints per level
- settings_integration: External integration configuration
- settings_strategic_plans: 5-year strategic plan headers
- settings_strategic_scenarios: Strategic plan scenarios with growth assumptions
- settings_strategic_projections: Multi-year financial projections
- settings_strategic_initiatives: Major strategic projects/initiatives

Author: Claude Code
Date: 2025-12-16
"""

from __future__ import annotations

import enum
import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    BaseModel,
    PortableJSON,
    VersionedMixin,
    get_fk_target,
    get_schema,
)

if TYPE_CHECKING:
    from app.models.admin import Organization
    from app.models.reference import (
        AcademicCycle,
        AcademicLevel,
        FeeCategory,
        NationalityType,
        Subject,
        TeacherCategory,
    )


# =============================================================================
# ENUMS
# =============================================================================


class VersionStatus(str, enum.Enum):
    """Version status enum for budget version lifecycle."""

    WORKING = "working"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    FORECAST = "forecast"
    SUPERSEDED = "superseded"


# Backward compatibility alias
BudgetVersionStatus = VersionStatus


class ScenarioType(str, enum.Enum):
    """
    Scenario type for budget versions.

    Different scenario types have different workflow rules and purposes:
    - ACTUAL: Imported actuals from Odoo GL (validated -> locked)
    - BUDGET: Annual budget planning (working -> submitted -> approved -> locked)
    - FORECAST: Rolling forecast revisions (working -> submitted -> approved -> superseded)
    - STRATEGIC: 5-year strategic plans (working -> submitted -> approved -> superseded)
    - WHAT_IF: Scenario analysis / sandbox (working -> superseded only)
    """

    ACTUAL = "ACTUAL"
    BUDGET = "BUDGET"
    FORECAST = "FORECAST"
    STRATEGIC = "STRATEGIC"
    WHAT_IF = "WHAT_IF"


class StrategicScenarioType(str, enum.Enum):
    """Strategic plan scenario types for multi-year modeling."""

    BASE_CASE = "base_case"  # Current trajectory (3-5% enrollment growth)
    CONSERVATIVE = "conservative"  # Slower growth (0-2% enrollment growth)
    OPTIMISTIC = "optimistic"  # Expansion scenario (6-8% enrollment growth)
    NEW_CAMPUS = "new_campus"  # Major capital investment (new facility)


class InitiativeStatus(str, enum.Enum):
    """Strategic initiative status for project tracking."""

    PLANNED = "planned"  # Initiative planned but not yet approved
    APPROVED = "approved"  # Approved but not yet started
    IN_PROGRESS = "in_progress"  # Currently being executed
    COMPLETED = "completed"  # Successfully completed
    CANCELLED = "cancelled"  # Cancelled or deferred


class ProjectionCategory(str, enum.Enum):
    """Financial projection categories for multi-year planning."""

    REVENUE = "revenue"  # Total operating revenue
    PERSONNEL_COSTS = "personnel_costs"  # All personnel expenses
    OPERATING_COSTS = "operating_costs"  # Operating expenses (non-personnel)
    CAPEX = "capex"  # Capital expenditures
    DEPRECIATION = "depreciation"  # Depreciation expense


# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================


class SystemConfig(BaseModel):
    """
    Global system configuration parameters.

    Stores flexible key-value configuration using JSONB for values.
    Examples: currency settings, exchange rates, academic year dates, etc.

    Categories:
    -----------
    - currency: Currency codes, exchange rates
    - locale: Date formats, number formats, language
    - academic: School year dates, trimester dates
    - integration: External system URLs, credentials
    - calculation: Rounding rules, precision settings

    Example:
    --------
    key: "exchange_rate_eur_sar"
    value: {"rate": 4.15, "effective_date": "2025-01-01"}
    category: "currency"
    """

    __tablename__ = "settings_system_configs"

    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Configuration key (unique identifier)",
    )

    value: Mapped[dict] = mapped_column(
        PortableJSON,
        nullable=False,
        comment="Configuration value (flexible JSON structure)",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Configuration category (currency, locale, academic, etc.)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable description of configuration",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether configuration is active",
    )

    def __repr__(self) -> str:
        return f"<SystemConfig(key={self.key}, category={self.category})>"


# =============================================================================
# VERSION CONTROL
# =============================================================================


class Version(BaseModel):
    """
    Budget version control for planning scenarios.

    Supports multiple versions for comparison and historical tracking.
    Only one 'working' version per fiscal year allowed.

    Version Lifecycle:
    ------------------
    1. WORKING: Active editing phase
    2. SUBMITTED: Submitted for approval
    3. APPROVED: Approved and locked
    4. FORECAST: Rolling forecast revision
    5. SUPERSEDED: Replaced by newer version

    Scenario Types:
    ---------------
    - ACTUAL: Historical actuals imported from Odoo
    - BUDGET: Annual budget (primary planning)
    - FORECAST: In-year forecast revisions
    - STRATEGIC: 5-year strategic projections
    - WHAT_IF: Scenario analysis sandbox

    Example:
    --------
    name: "Budget 2025-2026"
    fiscal_year: 2025
    academic_year: "2025-2026"
    status: WORKING
    scenario_type: BUDGET
    """

    __tablename__ = "settings_versions"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Version name (e.g., 'Budget 2025-2026')",
    )

    fiscal_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Starting year of target academic year (e.g., 2026 for 2026-2027)",
    )

    academic_year: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Academic year (e.g., '2025-2026')",
    )

    status: Mapped[VersionStatus] = mapped_column(
        Enum(VersionStatus, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=VersionStatus.WORKING,
        index=True,
        comment="Version status (working, submitted, approved, forecast, superseded)",
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When version was submitted for approval",
    )

    submitted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "admin_users", "id")),
        nullable=True,
        comment="User who submitted version",
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When version was approved",
    )

    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "admin_users", "id")),
        nullable=True,
        comment="User who approved version",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Version notes and comments",
    )

    is_baseline: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this is the baseline version for comparison",
    )

    scenario_type: Mapped[ScenarioType] = mapped_column(
        Enum(ScenarioType, name="scenario_type", schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ScenarioType.BUDGET,
        index=True,
        comment="Scenario type (ACTUAL, BUDGET, FORECAST, STRATEGIC, WHAT_IF)",
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "admin_organizations", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this budget version belongs to",
    )

    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "settings_versions", "id")),
        nullable=True,
        comment="Parent version (for forecast revisions)",
    )

    # Business Rules (enforced at database level via migration)
    __table_args__ = (
        # Constraints created in migration:
        # 1. Unique partial index: only one 'working' per fiscal year
        # 2. Check constraint: forecast versions must have parent
        # 3. Trigger: prevent edits to approved versions
        {"comment": __doc__} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget", "comment": __doc__},
    )

    # Relationships
    parent_version: Mapped["Version | None"] = relationship(
        "Version",
        remote_side="Version.id",
        foreign_keys=[parent_version_id],
        back_populates="child_versions",
    )

    child_versions: Mapped[list["Version"]] = relationship(
        "Version",
        back_populates="parent_version",
        foreign_keys="Version.parent_version_id",
    )

    organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        lazy="select",
    )

    # =========================================================================
    # Helper Properties for Academic Year Handling
    # =========================================================================

    @property
    def target_school_year(self) -> str:
        """
        Target school year string for this version.

        The fiscal_year is the STARTING year of the academic year.
        Example: fiscal_year=2026 -> "2026/2027"
        """
        return f"{self.fiscal_year}/{self.fiscal_year + 1}"

    @property
    def historical_n1_year(self) -> int:
        """
        N-1 fiscal year for historical comparison.

        This is the most recent complete year of historical data.
        Example: fiscal_year=2026 -> 2025 (representing 2025-2026)
        """
        return self.fiscal_year - 1

    @property
    def historical_n2_year(self) -> int:
        """
        N-2 fiscal year for historical comparison.

        This is the second most recent year of historical data.
        Example: fiscal_year=2026 -> 2024 (representing 2024-2025)
        """
        return self.fiscal_year - 2

    def __repr__(self) -> str:
        return f"<Version(name={self.name}, status={self.status.value})>"


# Backward compatibility alias
BudgetVersion = Version


# =============================================================================
# CLASS SIZE PARAMETERS
# =============================================================================


class ClassSizeParam(BaseModel, VersionedMixin):
    """
    Class size parameters per level and version.

    Defines min/target/max class sizes used for class formation calculations.
    Level-specific parameters override cycle defaults.

    Parameters:
    -----------
    - min_class_size: Minimum viable class size (typically 15-18)
    - target_class_size: Target/optimal size (typically 22-25)
    - max_class_size: Maximum allowed size (typically 28-30)

    Example:
    --------
    For 6eme (College level):
    - min_class_size: 18
    - target_class_size: 24
    - max_class_size: 28
    """

    __tablename__ = "settings_class_size_params"
    __table_args__ = (
        # Only one of level_id or cycle_id should be set
        CheckConstraint(
            "(level_id IS NOT NULL AND cycle_id IS NULL) OR "
            "(level_id IS NULL AND cycle_id IS NOT NULL)",
            name="ck_class_size_params_level_or_cycle",
        ),
        # min < target <= max
        CheckConstraint(
            "min_class_size < target_class_size AND "
            "target_class_size <= max_class_size",
            name="ck_class_size_params_valid_range",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    level_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=True,
        index=True,
        comment="Specific academic level (NULL for cycle default)",
    )

    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Academic cycle (NULL if level-specific)",
    )

    min_class_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Minimum viable class size",
    )

    target_class_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Target/optimal class size",
    )

    max_class_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Maximum allowed class size",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Parameter notes",
    )

    # Relationships
    level: Mapped["AcademicLevel | None"] = relationship("AcademicLevel")
    cycle: Mapped["AcademicCycle | None"] = relationship("AcademicCycle")

    def __repr__(self) -> str:
        target = self.level_id or self.cycle_id
        return f"<ClassSizeParam(target={target}, min={self.min_class_size}, max={self.max_class_size})>"


# =============================================================================
# SUBJECT HOURS MATRIX
# =============================================================================


class SubjectHoursMatrix(BaseModel, VersionedMixin):
    """
    Subject hours per level configuration (DHG matrix).

    Defines hours per week per class for each subject at each level.
    Used to calculate total DHG hours and teacher FTE requirements.

    Example:
    --------
    Subject: Mathematics (MATH)
    Level: 6eme
    Hours per week: 4.5
    Is split: False (full class, not half-groups)

    DHG Calculation:
    ----------------
    Total DHG Hours = Sum(hours_per_week * num_classes * (2 if is_split else 1))
    """

    __tablename__ = "settings_subject_hours_matrix"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "subject_id",
            "level_id",
            name="uk_subject_hours_version_subject_level",
        ),
        CheckConstraint(
            "hours_per_week > 0 AND hours_per_week <= 12",
            name="ck_subject_hours_realistic_range",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_subjects", "id")),
        nullable=False,
        index=True,
        comment="Subject being taught",
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
        comment="Academic level",
    )

    hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Hours per week per class",
    )

    is_split: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether classes are split (half-size groups, counts as double hours)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Configuration notes",
    )

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject")
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    def __repr__(self) -> str:
        return f"<SubjectHoursMatrix(subject={self.subject_id}, level={self.level_id}, hours={self.hours_per_week})>"


# =============================================================================
# TEACHER COST PARAMETERS
# =============================================================================


class TeacherCostParam(BaseModel, VersionedMixin):
    """
    Teacher cost parameters per category and version.

    Defines salary, benefits, and contribution costs for each teacher category.
    AEFE teachers: PRRD contribution in EUR (converted to SAR).
    Local teachers: Salary and benefits in SAR.

    Cost Components:
    ----------------
    - PRRD contribution (AEFE detached): ~41,863 EUR/year
    - Average salary (local): 180,000-350,000 SAR/year
    - Social charges: 21% (GOSI: 12% employer + 9% employee)
    - Benefits allowance: Variable (housing, transport, etc.)
    - HSA hourly rate: Overtime payment rate

    Example:
    --------
    Category: LOCAL_CDI (Local permanent)
    Avg Salary: 280,000 SAR
    Social Charges: 21%
    Benefits: 45,000 SAR
    HSA Rate: 200 SAR/hour
    """

    __tablename__ = "settings_teacher_cost_params"

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_teacher_categories", "id")),
        nullable=False,
        index=True,
        comment="Teacher category",
    )

    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Academic cycle (NULL for all cycles)",
    )

    prrd_contribution_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="PRRD contribution per teacher (EUR, for AEFE detached)",
    )

    avg_salary_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Average salary for local teachers (SAR/year)",
    )

    social_charges_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.21"),
        comment="Social charges rate (e.g., 0.21 for 21%)",
    )

    benefits_allowance_sar: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Benefits/allowances per teacher (SAR/year)",
    )

    hsa_hourly_rate_sar: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        comment="HSA (overtime) hourly rate (SAR)",
    )

    max_hsa_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("4.00"),
        comment="Maximum HSA hours per teacher per week",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Parameter notes",
    )

    # Relationships
    category: Mapped["TeacherCategory"] = relationship("TeacherCategory")
    cycle: Mapped["AcademicCycle | None"] = relationship("AcademicCycle")

    def __repr__(self) -> str:
        return f"<TeacherCostParam(category={self.category_id}, cycle={self.cycle_id})>"


# =============================================================================
# FEE STRUCTURE
# =============================================================================


class FeeStructure(BaseModel, VersionedMixin):
    """
    Fee amounts per level, nationality, and category.

    Defines fee matrix used for revenue calculations.
    Tuition split: T1=40%, T2=30%, T3=30%.
    Sibling discount (25%) applies from 3rd child onward (tuition only).

    Fee Categories:
    ---------------
    - TUITION: Tuition fees (by trimester T1, T2, T3)
    - DAI: Droit Annuel d'Inscription (enrollment fee)
    - REGISTRATION: One-time registration fee
    - TRANSPORT: Transportation fees
    - CANTEEN: Canteen/lunch fees

    Nationality Tiers:
    ------------------
    - FRENCH: French nationals (TTC with VAT)
    - SAUDI: Saudi nationals (HT no VAT)
    - OTHER: Other nationalities (TTC with VAT)

    Example:
    --------
    Level: 6eme
    Nationality: FRENCH
    Category: TUITION
    Trimester: 1 (T1)
    Amount: 18,000 SAR
    """

    __tablename__ = "settings_fee_structure"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "level_id",
            "nationality_type_id",
            "fee_category_id",
            "trimester",
            name="uk_fee_structure_version_level_nat_cat_trim",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
        comment="Academic level",
    )

    nationality_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_nationality_types", "id")),
        nullable=False,
        index=True,
        comment="Nationality type (French, Saudi, Other)",
    )

    fee_category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_fee_categories", "id")),
        nullable=False,
        index=True,
        comment="Fee category (tuition, DAI, etc.)",
    )

    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Fee amount in SAR",
    )

    trimester: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Trimester (1-3) for tuition, NULL for annual fees",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Fee notes",
    )

    # Relationships
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")
    nationality_type: Mapped["NationalityType"] = relationship("NationalityType")
    fee_category: Mapped["FeeCategory"] = relationship("FeeCategory")

    def __repr__(self) -> str:
        return f"<FeeStructure(level={self.level_id}, amount={self.amount_sar} SAR)>"


# =============================================================================
# TIMETABLE CONSTRAINTS
# =============================================================================


class TimetableConstraint(BaseModel, VersionedMixin):
    """
    Timetable scheduling constraints per level.

    Defines total hours per week, max hours per day, and break requirements.
    Used to validate DHG hours don't exceed realistic scheduling limits.

    Parameters:
    -----------
    - total_hours_per_week: Maximum student contact hours (25-35)
    - max_hours_per_day: Maximum daily hours (6-8)
    - days_per_week: School days (typically 5)
    - requires_lunch_break: Whether lunch break is mandatory
    - min_break_duration_minutes: Minimum break length (60-90)

    Example:
    --------
    Level: 6eme
    Total hours/week: 27
    Max hours/day: 6.5
    Days/week: 5
    Requires lunch: Yes
    Min break: 60 minutes
    """

    __tablename__ = "settings_timetable_constraints"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "level_id",
            name="uk_timetable_constraint_version_level",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
        comment="Academic level",
    )

    total_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Total student hours per week",
    )

    max_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Maximum hours per day",
    )

    days_per_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="School days per week (typically 5)",
    )

    requires_lunch_break: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether lunch break is required",
    )

    min_break_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        comment="Minimum break duration (minutes)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Constraint notes",
    )

    # Relationships
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    def __repr__(self) -> str:
        return f"<TimetableConstraint(level={self.level_id}, hours/week={self.total_hours_per_week})>"


# =============================================================================
# INTEGRATION SETTINGS
# =============================================================================


class IntegrationSettings(BaseModel):
    """
    Configuration settings for external integrations.

    Stores connection details and configuration for each integration type.
    Sensitive data (passwords, API keys) should be encrypted before storage.

    Integration Types:
    ------------------
    - odoo: Odoo ERP for GL actuals import
    - skolengo: Student information system
    - aefe: AEFE network reporting

    Example:
    --------
    integration_type: "odoo"
    config: {"url": "https://odoo.efir.sa", "database": "efir_prod"}
    is_active: True
    auto_sync_enabled: True
    auto_sync_interval_minutes: 60
    """

    __tablename__ = "settings_integration"

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
        return f"<IntegrationSettings(type={self.integration_type}, active={self.is_active})>"


# =============================================================================
# STRATEGIC PLANNING
# =============================================================================


class StrategicPlan(BaseModel):
    """
    5-year strategic plan header with metadata and timeline.

    Represents the master plan document for EFIR's multi-year strategic cycle,
    typically spanning 5 fiscal years. Each plan contains multiple scenarios
    (base case, conservative, optimistic) and tracks major strategic initiatives.

    Strategic planning enables:
    - Multi-year enrollment and revenue projections
    - Long-term financial sustainability analysis
    - Capital investment planning
    - Scenario comparison (best case vs worst case)
    - Board-level strategic decision support

    Example:
    --------
    name: "EFIR Strategic Plan 2025-2030"
    base_year: 2025 (Year 1 of 5)
    status: "approved"
    """

    __tablename__ = "settings_strategic_plans"
    __table_args__ = (
        UniqueConstraint("name", name="uk_strategic_plan_name"),
        CheckConstraint(
            "base_year >= 2000 AND base_year <= 2100",
            name="ck_strategic_plan_year_range",
        ),
        {"comment": __doc__} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget", "comment": __doc__},
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique strategic plan name (e.g., 'EFIR Strategic Plan 2025-2030')",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Plan description and key objectives",
    )

    base_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Starting year of 5-year plan (e.g., 2025 for 2025-2030 plan)",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
        comment="Plan status: draft, approved, archived",
    )

    # Relationships
    scenarios: Mapped[list["StrategicPlanScenario"]] = relationship(
        "StrategicPlanScenario",
        back_populates="strategic_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    initiatives: Mapped[list["StrategicInitiative"]] = relationship(
        "StrategicInitiative",
        back_populates="strategic_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StrategicPlan(name={self.name}, base_year={self.base_year})>"


class StrategicPlanScenario(BaseModel):
    """
    Strategic plan scenario with growth assumptions and parameters.

    Each strategic plan contains 3-4 scenarios representing different
    growth trajectories and market conditions.

    Scenario Types:
    ---------------
    - CONSERVATIVE: Slower growth (0-2% enrollment growth)
    - BASE_CASE: Expected trajectory (3-5% enrollment growth)
    - OPTIMISTIC: Expansion scenario (6-8% enrollment growth)
    - NEW_CAMPUS: Major capital investment scenario

    Growth Parameters:
    ------------------
    - enrollment_growth_rate: -50% to +100% (typically 0-8%)
    - fee_increase_rate: -20% to +50% (typically 2-6%)
    - salary_inflation_rate: -20% to +50% (typically 2-5%)
    - operating_inflation_rate: -20% to +50% (typically 2-4%)

    Example:
    --------
    scenario_type: BASE_CASE
    enrollment_growth_rate: 0.04 (4%)
    fee_increase_rate: 0.03 (3%)
    salary_inflation_rate: 0.035 (3.5%)
    operating_inflation_rate: 0.025 (2.5%)
    """

    __tablename__ = "settings_strategic_scenarios"
    __table_args__ = (
        UniqueConstraint(
            "strategic_plan_id",
            "scenario_type",
            name="uk_strategic_scenario_plan_type",
        ),
        CheckConstraint(
            "enrollment_growth_rate >= -0.50 AND enrollment_growth_rate <= 1.00",
            name="ck_scenario_enrollment_growth_range",
        ),
        CheckConstraint(
            "fee_increase_rate >= -0.20 AND fee_increase_rate <= 0.50",
            name="ck_scenario_fee_increase_range",
        ),
        CheckConstraint(
            "salary_inflation_rate >= -0.20 AND salary_inflation_rate <= 0.50",
            name="ck_scenario_salary_inflation_range",
        ),
        CheckConstraint(
            "operating_inflation_rate >= -0.20 AND operating_inflation_rate <= 0.50",
            name="ck_scenario_operating_inflation_range",
        ),
        Index(
            "ix_strategic_scenario_plan_type",
            "strategic_plan_id",
            "scenario_type",
        ),
        {"comment": __doc__} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget", "comment": __doc__},
    )

    strategic_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "settings_strategic_plans", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Strategic plan this scenario belongs to",
    )

    scenario_type: Mapped[StrategicScenarioType] = mapped_column(
        Enum(StrategicScenarioType, name="strategic_scenario_type", schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Scenario type (base_case, conservative, optimistic, new_campus)",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="User-friendly scenario name (e.g., 'Base Case - Steady Growth')",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Scenario description and key assumptions",
    )

    enrollment_growth_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual enrollment growth rate (e.g., 0.04 = 4% per year)",
    )

    fee_increase_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual fee increase rate (e.g., 0.03 = 3% per year)",
    )

    salary_inflation_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual salary inflation rate (e.g., 0.035 = 3.5% per year)",
    )

    operating_inflation_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual operating cost inflation rate (e.g., 0.025 = 2.5% per year)",
    )

    additional_assumptions: Mapped[dict | None] = mapped_column(
        PortableJSON,
        nullable=True,
        comment="Additional scenario-specific assumptions (exchange rates, capacity, etc.)",
    )

    # Relationships
    strategic_plan: Mapped[StrategicPlan] = relationship(
        "StrategicPlan",
        back_populates="scenarios",
        lazy="selectin",
    )
    projections: Mapped[list["StrategicPlanProjection"]] = relationship(
        "StrategicPlanProjection",
        back_populates="scenario",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StrategicPlanScenario(type={self.scenario_type.value}, plan={self.strategic_plan_id})>"


class StrategicPlanProjection(BaseModel):
    """
    Multi-year financial projections by category and year.

    Stores projected financial amounts for each year (1-5) of the strategic plan,
    broken down by category (revenue, costs, capex).

    Projection Categories:
    ----------------------
    - REVENUE: Total operating revenue
    - PERSONNEL_COSTS: All personnel expenses
    - OPERATING_COSTS: Operating expenses excluding personnel
    - CAPEX: Capital expenditures
    - DEPRECIATION: Depreciation expense

    Calculation Method:
    -------------------
    Year 1: Base year actual/budget amounts
    Year N: Year (N-1) x (1 + growth_rate)

    Example:
    --------
    Year 1 (2025): Revenue = 55,515,000 SAR
    Year 2 (2026): Revenue = 55,515,000 x 1.04 x 1.03 = 59,462,000 SAR
    """

    __tablename__ = "settings_strategic_projections"
    __table_args__ = (
        UniqueConstraint(
            "strategic_plan_scenario_id",
            "year",
            "category",
            name="uk_strategic_projection_scenario_year_category",
        ),
        CheckConstraint(
            "year >= 1 AND year <= 5",
            name="ck_projection_year_range",
        ),
        CheckConstraint(
            "amount_sar >= 0",
            name="ck_projection_amount_positive",
        ),
        Index(
            "ix_strategic_projection_scenario_year",
            "strategic_plan_scenario_id",
            "year",
        ),
        {"comment": __doc__} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget", "comment": __doc__},
    )

    strategic_plan_scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "settings_strategic_scenarios", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Scenario this projection belongs to",
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Year in strategic plan (1-5, where 1 = base_year)",
    )

    category: Mapped[ProjectionCategory] = mapped_column(
        Enum(ProjectionCategory, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Projection category (revenue, personnel_costs, operating_costs, capex, depreciation)",
    )

    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Projected amount in SAR for this year and category",
    )

    calculation_inputs: Mapped[dict | None] = mapped_column(
        PortableJSON,
        nullable=True,
        comment="Inputs used in projection calculation (base amount, growth rates, enrollment, etc.)",
    )

    # Relationships
    scenario: Mapped[StrategicPlanScenario] = relationship(
        "StrategicPlanScenario",
        back_populates="projections",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StrategicPlanProjection(year={self.year}, category={self.category.value}, amount={self.amount_sar})>"


class StrategicInitiative(BaseModel):
    """
    Strategic initiative or major project within the 5-year plan.

    Tracks major capital investments, facility expansions, program launches,
    and other strategic projects planned over the 5-year horizon.

    Initiative Types:
    -----------------
    - Facility Expansion: New campus, building renovation
    - Technology Investment: ERP system, learning platforms
    - Program Launch: New curriculum, IB program
    - Capacity Increase: Additional classrooms, labs
    - Infrastructure: HVAC upgrade, solar panels

    Status Lifecycle:
    -----------------
    PLANNED -> APPROVED -> IN_PROGRESS -> COMPLETED
                       -> CANCELLED

    Example:
    --------
    name: "New Science Laboratory"
    planned_year: 2 (2026)
    capex_amount_sar: 2,500,000
    operating_impact_sar: 150,000 (recurring from year 2)
    status: APPROVED
    """

    __tablename__ = "settings_strategic_initiatives"
    __table_args__ = (
        CheckConstraint(
            "planned_year >= 1 AND planned_year <= 5",
            name="ck_initiative_year_range",
        ),
        CheckConstraint(
            "capex_amount_sar >= 0",
            name="ck_initiative_capex_positive",
        ),
        Index(
            "ix_strategic_initiative_plan_year",
            "strategic_plan_id",
            "planned_year",
        ),
        Index(
            "ix_strategic_initiative_status",
            "status",
        ),
        {"comment": __doc__} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget", "comment": __doc__},
    )

    strategic_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "settings_strategic_plans", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Strategic plan this initiative belongs to",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Initiative name (e.g., 'New Science Laboratory')",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Initiative description, objectives, and deliverables",
    )

    planned_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Year in strategic plan when initiative is planned (1-5)",
    )

    capex_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="One-time capital expenditure in SAR (equipment, construction, etc.)",
    )

    operating_impact_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Annual operating cost impact in SAR (recurring from planned year onwards)",
    )

    status: Mapped[InitiativeStatus] = mapped_column(
        Enum(InitiativeStatus, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=InitiativeStatus.PLANNED,
        index=True,
        comment="Initiative status (planned, approved, in_progress, completed, cancelled)",
    )

    additional_details: Mapped[dict | None] = mapped_column(
        PortableJSON,
        nullable=True,
        comment="Additional initiative details (milestones, dependencies, risks, etc.)",
    )

    # Relationships
    strategic_plan: Mapped[StrategicPlan] = relationship(
        "StrategicPlan",
        back_populates="initiatives",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StrategicInitiative(name={self.name}, year={self.planned_year}, status={self.status.value})>"


# =============================================================================
# END OF SETTINGS MODELS
# =============================================================================
