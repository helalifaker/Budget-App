"""
SQLAlchemy Models for Configuration Layer (Modules 1-6).

These modules provide master data and parameters that drive budget calculations:
- Module 1: System Configuration
- Module 2: Class Size Parameters
- Module 3: Subject Hours Configuration
- Module 4: Teacher Costs Configuration
- Module 5: Fee Structure Configuration
- Module 6: Timetable Constraints

All configuration data is versioned to support multiple budget scenarios.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
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
    ReferenceDataModel,
    VersionedMixin,
    get_fk_target,
    get_schema,
)

if TYPE_CHECKING:
    from app.models.auth import Organization

# ==============================================================================
# Module 1: System Configuration
# ==============================================================================


class SystemConfig(BaseModel):
    """
    Global system configuration parameters.

    Stores flexible key-value configuration using JSONB for values.
    Examples: currency settings, exchange rates, academic year dates, etc.
    """

    __tablename__ = "system_configs"

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


class BudgetVersionStatus(str, PyEnum):
    """Budget version status enum."""

    WORKING = "working"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    FORECAST = "forecast"
    SUPERSEDED = "superseded"


class BudgetVersion(BaseModel):
    """
    Budget version control.

    Supports multiple versions of budgets for comparison and historical tracking.
    Only one 'working' version per fiscal year allowed.
    """

    __tablename__ = "budget_versions"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Version name (e.g., 'Budget 2025-2026')",
    )

    fiscal_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Fiscal year (e.g., 2026 for 2025-2026)",
    )

    academic_year: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Academic year (e.g., '2025-2026')",
    )

    status: Mapped[BudgetVersionStatus] = mapped_column(
        Enum(BudgetVersionStatus, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BudgetVersionStatus.WORKING,
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
        ForeignKey(get_fk_target("efir_budget", "users", "id")),
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
        ForeignKey(get_fk_target("efir_budget", "users", "id")),
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

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "organizations", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this budget version belongs to",
    )

    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "budget_versions", "id")),
        nullable=True,
        comment="Parent version (for forecast revisions)",
    )

    # Business Rules (enforced at database level via migration 004_fix_critical_issues)
    __table_args__ = (
        # Note: Constraints are created in migration, documented here for reference:
        # 1. Unique partial index: only one 'working' per fiscal year (WHERE status='working' AND deleted_at IS NULL)
        # 2. Check constraint: forecast versions must have parent (status != 'forecast' OR parent_version_id IS NOT NULL)
        # 3. Trigger: prevent edits to approved versions (prevent_approved_version_edit)
        {"comment": __doc__} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget", "comment": __doc__},
    )

    # Relationships
    parent_version: Mapped[BudgetVersion] = relationship(
        "BudgetVersion",
        remote_side="BudgetVersion.id",
        foreign_keys=[parent_version_id],
        back_populates="child_versions",
    )

    child_versions: Mapped[list[BudgetVersion]] = relationship(
        "BudgetVersion",
        back_populates="parent_version",
        foreign_keys="BudgetVersion.parent_version_id",
    )

    organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        lazy="select",
    )


# ==============================================================================
# Module 2: Class Size Parameters
# ==============================================================================


class AcademicCycle(ReferenceDataModel):
    """
    Academic cycle definitions.

    Represents major educational divisions in French system:
    - Maternelle (Preschool)
    - Élémentaire (Elementary)
    - Collège (Middle School)
    - Lycée (High School)
    """

    __tablename__ = "academic_cycles"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Cycle code (MAT, ELEM, COLL, LYC)",
    )

    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="French name (e.g., 'Maternelle')",
    )

    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="English name (e.g., 'Preschool')",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Display order (1=MAT, 2=ELEM, 3=COLL, 4=LYC)",
    )

    requires_atsem: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether ATSEM (classroom assistant) is required",
    )

    # Relationships
    levels: Mapped[list[AcademicLevel]] = relationship(
        "AcademicLevel",
        back_populates="cycle",
        order_by="AcademicLevel.sort_order",
    )


class AcademicLevel(ReferenceDataModel):
    """
    Academic level definitions.

    Represents individual grade levels within each cycle:
    - Maternelle: PS, MS, GS
    - Élémentaire: CP, CE1, CE2, CM1, CM2
    - Collège: 6ème, 5ème, 4ème, 3ème
    - Lycée: 2nde, 1ère, Terminale
    """

    __tablename__ = "academic_levels"

    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_cycles", "id")),
        nullable=False,
        index=True,
        comment="Parent academic cycle",
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Level code (PS, MS, GS, CP, CE1, etc.)",
    )

    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="French name (e.g., 'Petite Section')",
    )

    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="English name (e.g., 'Preschool - Small Section')",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Display order within cycle",
    )

    is_secondary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this is secondary level (DHG applicable)",
    )

    # Relationships
    cycle: Mapped[AcademicCycle] = relationship(
        "AcademicCycle",
        back_populates="levels",
    )


class ClassSizeParam(BaseModel, VersionedMixin):
    """
    Class size parameters per level and version.

    Defines min/target/max class sizes used for class formation calculations.
    Level-specific parameters override cycle defaults.
    """

    __tablename__ = "class_size_params"
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
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
        nullable=True,
        index=True,
        comment="Specific academic level (NULL for cycle default)",
    )

    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_cycles", "id")),
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
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")
    cycle: Mapped[AcademicCycle] = relationship("AcademicCycle")


# ==============================================================================
# Module 3: Subject Hours Configuration
# ==============================================================================


class Subject(ReferenceDataModel):
    """
    Subject catalog for DHG calculations.

    Represents academic subjects taught (Mathématiques, Français, Anglais, etc.).
    Used for secondary level DHG (Dotation Horaire Globale) calculations.
    """

    __tablename__ = "subjects"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Subject code (MATH, FRAN, ANGL, etc.)",
    )

    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="French name (e.g., 'Mathématiques')",
    )

    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="English name (e.g., 'Mathematics')",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Subject category (core, specialty, elective)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether subject is currently active",
    )


class SubjectHoursMatrix(BaseModel, VersionedMixin):
    """
    Subject hours per level configuration (DHG matrix).

    Defines hours per week per class for each subject at each level.
    Example: Mathématiques in 6ème = 4.5 hours/week per class.
    Used to calculate total DHG hours and teacher FTE requirements.
    """

    __tablename__ = "subject_hours_matrix"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
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
        ForeignKey(get_fk_target("efir_budget", "subjects", "id")),
        nullable=False,
        index=True,
        comment="Subject being taught",
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
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
    subject: Mapped[Subject] = relationship("Subject")
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")


# ==============================================================================
# Module 4: Teacher Costs Configuration
# ==============================================================================


class TeacherCategory(ReferenceDataModel):
    """
    Teacher employment categories.

    Categories:
    - AEFE_DETACHED: AEFE detached teachers (school pays PRRD contribution)
    - AEFE_FUNDED: AEFE fully funded teachers (no school cost)
    - LOCAL: Locally recruited teachers
    """

    __tablename__ = "teacher_categories"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Category code",
    )

    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="French name",
    )

    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="English name",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Category description",
    )

    is_aefe: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether AEFE-affiliated",
    )


class TeacherCostParam(BaseModel, VersionedMixin):
    """
    Teacher cost parameters per category and version.

    Defines salary, benefits, and contribution costs for each teacher category.
    AEFE teachers: PRRD contribution in EUR (converted to SAR).
    Local teachers: Salary and benefits in SAR.
    """

    __tablename__ = "teacher_cost_params"

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "teacher_categories", "id")),
        nullable=False,
        index=True,
        comment="Teacher category",
    )

    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_cycles", "id")),
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
    category: Mapped[TeacherCategory] = relationship("TeacherCategory")
    cycle: Mapped[AcademicCycle] = relationship("AcademicCycle")


# ==============================================================================
# Module 5: Fee Structure Configuration
# ==============================================================================


class FeeCategory(ReferenceDataModel):
    """
    Fee category definitions.

    Categories:
    - TUITION: Tuition fees (by trimester)
    - DAI: Droit Annuel d'Inscription (enrollment fee)
    - REGISTRATION: One-time registration fee
    - TRANSPORT: Transportation fees
    - CANTEEN: Canteen/lunch fees
    """

    __tablename__ = "fee_categories"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Category code",
    )

    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="French name",
    )

    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="English name",
    )

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="PCG account code (70xxx revenue)",
    )

    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether charged annually",
    )

    allows_sibling_discount: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether sibling discount applies (tuition only)",
    )


class NationalityType(ReferenceDataModel):
    """
    Nationality-based fee tier definitions.

    Tiers:
    - FRENCH: French nationals (TTC - including VAT)
    - SAUDI: Saudi nationals (HT - no VAT)
    - OTHER: Other nationalities (TTC - including VAT)
    """

    __tablename__ = "nationality_types"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Nationality code",
    )

    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="French name",
    )

    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="English name",
    )

    vat_applicable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether VAT applies (Saudi: no, Others: yes)",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Display order",
    )


class FeeStructure(BaseModel, VersionedMixin):
    """
    Fee amounts per level, nationality, and category.

    Defines fee matrix used for revenue calculations.
    Tuition split: T1=40%, T2=30%, T3=30%.
    Sibling discount (25%) applies from 3rd child onward (tuition only).
    """

    __tablename__ = "fee_structure"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
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
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
        nullable=False,
        index=True,
        comment="Academic level",
    )

    nationality_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "nationality_types", "id")),
        nullable=False,
        index=True,
        comment="Nationality type (French, Saudi, Other)",
    )

    fee_category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "fee_categories", "id")),
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
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")
    nationality_type: Mapped[NationalityType] = relationship("NationalityType")
    fee_category: Mapped[FeeCategory] = relationship("FeeCategory")


# ==============================================================================
# Module 6: Timetable Constraints
# ==============================================================================


class TimetableConstraint(BaseModel, VersionedMixin):
    """
    Timetable scheduling constraints per level.

    Defines total hours per week, max hours per day, and break requirements.
    Used to validate DHG hours don't exceed realistic scheduling limits.
    """

    __tablename__ = "timetable_constraints"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "level_id",
            name="uk_timetable_constraint_version_level",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
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
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")
