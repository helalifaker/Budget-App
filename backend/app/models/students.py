"""
SQLAlchemy Models for Students Module (students_* tables).

This module contains all enrollment and class structure models for the
EFIR Budget Planning Application. Students module is the PRIMARY DRIVER
for all budget calculations - changes cascade through:
- Class structure -> DHG hours -> Teacher FTE -> Personnel costs
- Revenue (tuition fees based on enrollment)
- Facility needs

Tables (ACTIVE):
- students_enrollment_plans: Enrollment projections per level and nationality
- students_nationality_distributions: Nationality percentage breakdowns per level
- students_class_structures: Calculated class formations (OUTPUT table)
- students_lateral_entry_defaults: Base lateral entry per academic level
- students_enrollment_projections: Cached projection results (OUTPUT table)
- students_configs: Unified projection config + scenario settings (Phase 4A)
- students_data: Unified enrollment data with nationality (Phase 4A)
- students_overrides: Unified override layers (Phase 4A)
- students_calibration: Calibration parameters + manual overrides (Phase 4A)

Tables (LEGACY - marked deprecated):
- students_projection_configs: Old projection config -> use StudentsConfig
- students_global_overrides: Old global overrides -> use StudentsOverride (scope=global)
- students_level_overrides: Old cycle overrides -> use StudentsOverride (scope=cycle)
- students_grade_overrides: Old grade overrides -> use StudentsOverride (scope=level)
- students_derived_parameters: Old derived params -> use StudentsCalibration
- students_parameter_overrides: Old param overrides -> use StudentsCalibration
- students_scenario_multipliers: Old scenario mult -> use StudentsConfig.lateral_multiplier

Author: Claude Code
Date: 2025-12-16
"""

from __future__ import annotations

import os
import uuid
import warnings
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import (
    BaseModel,
    PortableJSON,
    ReferenceDataModel,
    VersionedMixin,
    get_fk_target,
    get_table_args,
)

if TYPE_CHECKING:
    from app.models.reference import AcademicCycle, AcademicLevel, NationalityType


# =============================================================================
# ENUMS
# =============================================================================


class OverrideScope(str, PyEnum):
    """Scope type for enrollment overrides."""

    GLOBAL = "global"
    CYCLE = "cycle"
    LEVEL = "level"


class CalibrationOrigin(str, PyEnum):
    """Origin of calibration data."""

    CALCULATED = "calculated"
    MANUAL_OVERRIDE = "manual_override"


class DataSourceType(str, PyEnum):
    """Source of enrollment data."""

    MANUAL = "manual"
    PROJECTED = "projected"
    ACTUAL = "actual"
    IMPORTED = "imported"


# =============================================================================
# ACTIVE MODELS - Enrollment Planning
# =============================================================================


class EnrollmentPlan(BaseModel, VersionedMixin):
    """
    Enrollment projections per level, nationality, and version.

    This is the PRIMARY DRIVER for all budget calculations.
    Changes to enrollment cascade through:
    - Class structure -> DHG hours -> Teacher FTE -> Personnel costs
    - Revenue (tuition fees)
    - Facility needs

    Business Rule: Total enrollment capped at ~1,875 students (facility capacity).
    """

    __tablename__ = "students_enrollment_plans"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "level_id",
            "nationality_type_id",
            name="uk_enrollment_version_level_nat",
        ),
        CheckConstraint("student_count >= 0", name="ck_enrollment_non_negative"),
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

    student_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Projected number of students",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Enrollment notes and assumptions",
    )

    # Relationships
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")
    nationality_type: Mapped["NationalityType"] = relationship("NationalityType")

    def __repr__(self) -> str:
        return f"<EnrollmentPlan(level={self.level_id}, students={self.student_count})>"


class NationalityDistribution(BaseModel, VersionedMixin):
    """
    Per-level nationality distribution percentages.

    Used for enrollment planning when user knows total students per level
    but estimates nationality breakdown via percentages.

    Business Rules:
    - french_pct + saudi_pct + other_pct must equal 100%
    - Each percentage must be between 0 and 100
    - One distribution record per level per budget version

    Usage Flow:
    1. User enters total students per level in EnrollmentTotalsGrid
    2. User sets nationality percentages per level in DistributionGrid
    3. System calculates breakdown: total x percentage = students per nationality
    4. Breakdown stored in enrollment_plans for downstream revenue calculations
    """

    __tablename__ = "students_nationality_distributions"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "level_id",
            name="uk_distribution_version_level",
        ),
        CheckConstraint(
            "french_pct >= 0 AND french_pct <= 100",
            name="ck_distribution_french_range",
        ),
        CheckConstraint(
            "saudi_pct >= 0 AND saudi_pct <= 100",
            name="ck_distribution_saudi_range",
        ),
        CheckConstraint(
            "other_pct >= 0 AND other_pct <= 100",
            name="ck_distribution_other_range",
        ),
        CheckConstraint(
            "french_pct + saudi_pct + other_pct = 100",
            name="ck_distribution_sum_100",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
        comment="Academic level (per-level distribution)",
    )

    french_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="French nationality percentage (0-100)",
    )

    saudi_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Saudi nationality percentage (0-100)",
    )

    other_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Other nationalities percentage (0-100)",
    )

    # Relationships
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    @validates("french_pct", "saudi_pct", "other_pct")
    def validate_percentage(self, key: str, value: Decimal) -> Decimal:
        """Validate percentage is within valid range."""
        if value < 0 or value > 100:
            raise ValueError(f"{key} must be between 0 and 100")
        return value

    def __repr__(self) -> str:
        return f"<NationalityDistribution(level={self.level_id})>"


# =============================================================================
# ACTIVE MODELS - Class Structure (OUTPUT)
# =============================================================================


class ClassStructure(BaseModel, VersionedMixin):
    """
    Calculated class formations based on enrollment and class size parameters.

    This is an OUTPUT table - results are computed by the class structure engine.

    Calculation Logic:
    1. Sum enrollment by level (across all nationalities)
    2. Divide by target_class_size to get number of classes
    3. Verify avg_class_size doesn't exceed max_class_size
    4. For Maternelle, calculate ATSEM needs (1 per class)

    This drives:
    - DHG hours calculation (classes x hours per subject)
    - Facility needs (classroom count)
    - Support staff needs (ATSEM)
    """

    __tablename__ = "students_class_structures"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "level_id",
            name="uk_class_structure_version_level",
        ),
        CheckConstraint("total_students >= 0", name="ck_class_structure_students_non_negative"),
        CheckConstraint("number_of_classes > 0", name="ck_class_structure_classes_positive"),
        CheckConstraint(
            "avg_class_size > 0 AND avg_class_size <= 35",
            name="ck_class_structure_avg_size_realistic",
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

    total_students: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Total students at this level (sum of enrollment)",
    )

    number_of_classes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of classes formed",
    )

    avg_class_size: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Average class size (total_students / number_of_classes)",
    )

    requires_atsem: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether ATSEM (classroom assistant) is required",
    )

    atsem_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of ATSEM needed (typically 1 per Maternelle class)",
    )

    calculation_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="target",
        comment="Method used (target, min, max, custom)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Class formation notes",
    )

    # Lineage columns for OUTPUT table
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When these results were computed",
    )
    computed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who triggered the computation",
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Unique ID for this computation run",
    )
    inputs_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of inputs for cache invalidation",
    )

    @validates("avg_class_size")
    def validate_avg_class_size(self, key: str, value: Decimal | None) -> Decimal | None:
        """Validate that avg_class_size is within realistic bounds."""
        if value is not None:
            if value <= 0 or value > 50:
                raise ValueError(
                    f"Average class size {value} is unrealistic. "
                    f"Must be between 1 and 50 students."
                )
        return value

    # Relationships
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    def __repr__(self) -> str:
        return f"<ClassStructure(level={self.level_id}, classes={self.number_of_classes})>"


# =============================================================================
# ACTIVE MODELS - Lateral Entry Defaults
# =============================================================================


class EnrollmentLateralEntryDefault(ReferenceDataModel):
    """
    Historical base lateral entry per academic level.

    Provides default lateral entry values based on historical patterns.
    Used as baseline for projection calculations when no override exists.
    """

    __tablename__ = "students_lateral_entry_defaults"
    __table_args__ = get_table_args(
        UniqueConstraint("level_id", name="uk_lateral_defaults_level"),
        CheckConstraint("base_lateral_entry >= 0", name="ck_lateral_defaults_non_negative"),
        comment=__doc__,
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
    )
    base_lateral_entry: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    def __repr__(self) -> str:
        return f"<EnrollmentLateralEntryDefault(level={self.level_id}, base={self.base_lateral_entry})>"


# =============================================================================
# ACTIVE MODELS - Enrollment Projections (OUTPUT)
# =============================================================================


class EnrollmentProjection(BaseModel):
    """
    Cached projection results per school year and level.

    This is an OUTPUT table - results are computed by the enrollment projection engine.
    Stores projected enrollment for multiple years ahead, tracking retained and
    lateral students separately for audit purposes.
    """

    __tablename__ = "students_enrollment_projections"
    __table_args__ = get_table_args(
        UniqueConstraint(
            "projection_config_id",
            "school_year",
            "level_id",
            name="uk_projections_config_year_level",
        ),
        CheckConstraint(
            "projected_students >= 0",
            name="ck_projections_projected_students_non_negative",
        ),
        CheckConstraint(
            "divisions >= 0",
            name="ck_projections_divisions_non_negative",
        ),
        comment=__doc__,
    )

    projection_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "students_projection_configs", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    school_year: Mapped[str] = mapped_column(String(9), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
    )

    projected_students: Mapped[int] = mapped_column(Integer, nullable=False)
    retained_students: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lateral_students: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    divisions: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_class_size: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)

    fiscal_year_weighted_students: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 1), nullable=True
    )

    was_capacity_constrained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_projection: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reduction_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reduction_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    calculation_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Lineage columns for OUTPUT table
    computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When these results were computed (mirrors calculation_timestamp)",
    )
    computed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who triggered the computation",
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Unique ID for this computation run",
    )
    inputs_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of inputs for cache invalidation",
    )

    projection_config: Mapped["EnrollmentProjectionConfig"] = relationship(
        "EnrollmentProjectionConfig", back_populates="projections"
    )
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    def __repr__(self) -> str:
        return f"<EnrollmentProjection(year={self.school_year}, level={self.level_id}, students={self.projected_students})>"


# =============================================================================
# ACTIVE MODELS - Phase 4A Unified Tables
# =============================================================================


class StudentsConfig(BaseModel, VersionedMixin):
    """
    Unified projection configuration and scenario settings (Phase 4A).

    Consolidates:
    - students_projection_configs (projection years, capacity, class size)
    - students_scenario_multipliers (lateral multiplier per scenario)

    Each budget version can have multiple configs for different scenarios
    (worst, base, best), each with its own lateral multiplier.
    """

    __tablename__ = "students_configs"
    __table_args__ = get_table_args(
        UniqueConstraint(
            "version_id",
            "scenario_code",
            name="uk_students_configs_version_scenario",
        ),
        CheckConstraint(
            "projection_years BETWEEN 1 AND 10",
            name="ck_students_configs_projection_years_range",
        ),
        CheckConstraint(
            "school_max_capacity > 0",
            name="ck_students_configs_capacity_positive",
        ),
        CheckConstraint(
            "default_class_size BETWEEN 15 AND 40",
            name="ck_students_configs_class_size_range",
        ),
        CheckConstraint(
            "lateral_multiplier BETWEEN 0.1 AND 3.0",
            name="ck_students_configs_lateral_mult_range",
        ),
        CheckConstraint(
            "status IN ('draft', 'validated')",
            name="ck_students_configs_status_valid",
        ),
        comment=__doc__,
    )

    # Scenario identification
    scenario_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="base",
        comment="Scenario code: worst, base, best",
    )

    # From projection_configs
    base_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Starting year for projections",
    )
    projection_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="Number of years to project (1-10)",
    )
    school_max_capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1850,
        comment="Maximum school student capacity",
    )
    default_class_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=25,
        comment="Default target class size (15-40)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        comment="Validation status: draft or validated",
    )
    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the config was validated",
    )
    validated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who validated this config",
    )

    # From scenario_multipliers
    lateral_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1.00"),
        comment="Lateral entry multiplier for scenario (0.1-3.0)",
    )

    # Relationships
    overrides: Mapped[list["StudentsOverride"]] = relationship(
        "StudentsOverride",
        back_populates="config",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<StudentsConfig(scenario={self.scenario_code}, status={self.status})>"


class StudentsData(BaseModel, VersionedMixin):
    """
    Unified enrollment data with nationality breakdown (Phase 4A).

    Consolidates:
    - students_enrollment_plans (student counts, class counts)
    - students_nationality_distributions (french/saudi/other percentages)

    Stores enrollment data per version, fiscal year, and academic level,
    with integrated nationality breakdown percentages.
    """

    __tablename__ = "students_data"
    __table_args__ = get_table_args(
        CheckConstraint(
            "student_count >= 0",
            name="ck_students_data_count_non_negative",
        ),
        CheckConstraint(
            "french_pct >= 0 AND french_pct <= 100",
            name="ck_students_data_french_pct_range",
        ),
        CheckConstraint(
            "saudi_pct >= 0 AND saudi_pct <= 100",
            name="ck_students_data_saudi_pct_range",
        ),
        CheckConstraint(
            "other_pct >= 0 AND other_pct <= 100",
            name="ck_students_data_other_pct_range",
        ),
        comment=__doc__,
    )

    # Location identifiers
    fiscal_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Fiscal year (starting year convention)",
    )
    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
        comment="Reference to academic level",
    )

    # Enrollment counts
    student_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of students",
    )
    number_of_classes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of classes/divisions",
    )
    avg_class_size: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Average class size",
    )

    # Nationality breakdown (integrated from nationality_distributions)
    french_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="French nationality percentage",
    )
    saudi_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Saudi nationality percentage",
    )
    other_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Other nationalities percentage",
    )

    # Backward compatibility with old nationality_type_id
    nationality_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_nationality_types", "id")),
        nullable=True,
        comment="Legacy nationality type reference (deprecated)",
    )

    # Data source tracking
    data_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
        comment="Data source: manual, projected, actual, imported",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about this data",
    )

    # Relationships
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    def __repr__(self) -> str:
        return f"<StudentsData(year={self.fiscal_year}, level={self.level_id}, count={self.student_count})>"


class StudentsOverride(BaseModel):
    """
    Unified override layers for enrollment projections (Phase 4A).

    Consolidates:
    - students_global_overrides (ps_entry_adjustment, retention_adjustment)
    - students_level_overrides (cycle-level class size ceiling, max divisions)
    - students_grade_overrides (level-specific retention, lateral entry)
    - students_lateral_entry_defaults (base lateral entry by level)

    Uses scope_type to differentiate:
    - 'global': Organization-wide overrides (scope_id is NULL)
    - 'cycle': Academic cycle overrides (scope_id is cycle_id)
    - 'level': Academic level/grade overrides (scope_id is level_id)
    """

    __tablename__ = "students_overrides"
    __table_args__ = get_table_args(
        UniqueConstraint(
            "config_id",
            "scope_type",
            "scope_id",
            name="uk_students_overrides_config_scope",
        ),
        CheckConstraint(
            "ps_entry_adjustment IS NULL OR ps_entry_adjustment BETWEEN -50 AND 50",
            name="ck_students_overrides_ps_entry_range",
        ),
        CheckConstraint(
            "retention_adjustment IS NULL OR retention_adjustment BETWEEN -0.1 AND 0.1",
            name="ck_students_overrides_retention_adj_range",
        ),
        CheckConstraint(
            "retention_rate IS NULL OR retention_rate BETWEEN 0.5 AND 1.0",
            name="ck_students_overrides_retention_rate_range",
        ),
        CheckConstraint(
            "lateral_entry IS NULL OR lateral_entry BETWEEN 0 AND 100",
            name="ck_students_overrides_lateral_entry_range",
        ),
        CheckConstraint(
            "lateral_multiplier_override IS NULL OR lateral_multiplier_override BETWEEN 0.1 AND 3.0",
            name="ck_students_overrides_lateral_mult_range",
        ),
        CheckConstraint(
            "min_class_size IS NULL OR min_class_size BETWEEN 5 AND 30",
            name="ck_students_overrides_min_class_range",
        ),
        CheckConstraint(
            "max_class_size IS NULL OR max_class_size BETWEEN 15 AND 40",
            name="ck_students_overrides_max_class_range",
        ),
        CheckConstraint(
            "target_class_size IS NULL OR target_class_size BETWEEN 15 AND 35",
            name="ck_students_overrides_target_class_range",
        ),
        CheckConstraint(
            "max_divisions IS NULL OR max_divisions BETWEEN 1 AND 10",
            name="ck_students_overrides_max_divisions_range",
        ),
        CheckConstraint(
            "class_size_ceiling IS NULL OR class_size_ceiling BETWEEN 15 AND 40",
            name="ck_students_overrides_ceiling_range",
        ),
        comment=__doc__,
    )

    # Parent reference
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            get_fk_target("efir_budget", "students_configs", "id"),
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="Reference to parent config",
    )

    # Scope definition
    scope_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Override scope: global, cycle, or level",
    )
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="NULL for global, cycle_id for cycle, level_id for level",
    )

    # Override values (from global_overrides)
    ps_entry_adjustment: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="PS entry count adjustment",
    )
    retention_adjustment: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Retention rate adjustment factor",
    )

    # Override values (from grade_overrides)
    retention_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Override retention rate",
    )
    lateral_entry: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Fixed lateral entry count",
    )
    lateral_multiplier_override: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Override lateral multiplier",
    )

    # Class size constraints (from level/grade overrides + class_size_params)
    min_class_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Minimum class size",
    )
    max_class_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum class size",
    )
    target_class_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Target class size",
    )
    max_divisions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum number of divisions/classes",
    )
    class_size_ceiling: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Absolute ceiling for class size",
    )

    # Documentation
    override_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for this override",
    )

    # Relationships
    config: Mapped[StudentsConfig] = relationship(
        "StudentsConfig",
        back_populates="overrides",
    )

    # Property to get the scope entity
    @property
    def is_global(self) -> bool:
        """Check if this is a global override."""
        return self.scope_type == OverrideScope.GLOBAL.value

    @property
    def is_cycle_override(self) -> bool:
        """Check if this is a cycle-level override."""
        return self.scope_type == OverrideScope.CYCLE.value

    @property
    def is_level_override(self) -> bool:
        """Check if this is a level/grade override."""
        return self.scope_type == OverrideScope.LEVEL.value

    def __repr__(self) -> str:
        return f"<StudentsOverride(config={self.config_id}, scope={self.scope_type})>"


class StudentsCalibration(BaseModel):
    """
    Unified calibration parameters with manual override support (Phase 4A).

    Consolidates:
    - students_derived_parameters (auto-calculated from historical data)
    - students_parameter_overrides (user manual overrides)

    Each organization has one calibration record per grade, containing:
    - Calculated parameters (progression_rate, lateral_entry_rate, retention_rate)
    - Quality indicators (confidence, std_deviation, years_used)
    - Manual override flags and values

    The data_origin field tracks whether values are calculated or overridden.
    """

    __tablename__ = "students_calibration"
    __table_args__ = get_table_args(
        UniqueConstraint(
            "organization_id",
            "grade_code",
            name="uk_students_calibration_org_grade",
        ),
        CheckConstraint(
            "confidence IN ('high', 'medium', 'low')",
            name="ck_students_calibration_confidence_valid",
        ),
        CheckConstraint(
            "progression_rate IS NULL OR progression_rate BETWEEN 0 AND 3",
            name="ck_students_calibration_progression_range",
        ),
        CheckConstraint(
            "lateral_entry_rate IS NULL OR lateral_entry_rate BETWEEN 0 AND 1",
            name="ck_students_calibration_lateral_rate_range",
        ),
        CheckConstraint(
            "retention_rate IS NULL OR retention_rate BETWEEN 0 AND 1",
            name="ck_students_calibration_retention_range",
        ),
        CheckConstraint(
            "manual_lateral_rate IS NULL OR manual_lateral_rate BETWEEN 0 AND 1",
            name="ck_students_calibration_manual_lateral_range",
        ),
        CheckConstraint(
            "manual_retention_rate IS NULL OR manual_retention_rate BETWEEN 0.5 AND 1",
            name="ck_students_calibration_manual_retention_range",
        ),
        CheckConstraint(
            "manual_fixed_lateral IS NULL OR manual_fixed_lateral BETWEEN 0 AND 100",
            name="ck_students_calibration_manual_fixed_range",
        ),
        CheckConstraint(
            "years_used >= 0",
            name="ck_students_calibration_years_non_negative",
        ),
        comment=__doc__,
    )

    # Organization and grade identification
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            get_fk_target("efir_budget", "admin_organizations", "id"),
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="Reference to organization",
    )
    grade_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Grade code (PS, MS, GS, CP, CE1, etc.)",
    )

    # Data origin tracking
    data_origin: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="calculated",
        comment="Origin: calculated or manual_override",
    )

    # Derived parameters (from students_derived_parameters)
    progression_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Calculated progression rate (e.g., 1.1410 = 114.10%)",
    )
    lateral_entry_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Calculated lateral entry rate (0-1)",
    )
    retention_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Calculated retention rate (0-1)",
    )

    # Quality indicators
    confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="low",
        comment="Confidence level: high, medium, low",
    )
    std_deviation: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="Standard deviation of calculated values",
    )
    years_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of historical years used",
    )
    source_years: Mapped[list] = mapped_column(
        PortableJSON,
        nullable=False,
        default=list,
        comment="List of source years used in calculation",
    )
    calculated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When parameters were last calculated",
    )

    # Manual override flags and values (from students_parameter_overrides)
    override_lateral_rate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether lateral rate is manually overridden",
    )
    manual_lateral_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Manual lateral entry rate (0-1)",
    )
    override_retention_rate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether retention rate is manually overridden",
    )
    manual_retention_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Manual retention rate (0.5-1)",
    )
    override_fixed_lateral: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether to use fixed lateral count instead of rate",
    )
    manual_fixed_lateral: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Fixed lateral entry count (0-100)",
    )
    override_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for manual overrides",
    )

    # Helper properties for effective values
    @property
    def effective_lateral_rate(self) -> Decimal | None:
        """Get effective lateral rate (manual if overridden, else calculated)."""
        if self.override_lateral_rate and self.manual_lateral_rate is not None:
            return self.manual_lateral_rate
        return self.lateral_entry_rate

    @property
    def effective_retention_rate(self) -> Decimal | None:
        """Get effective retention rate (manual if overridden, else calculated)."""
        if self.override_retention_rate and self.manual_retention_rate is not None:
            return self.manual_retention_rate
        return self.retention_rate

    @property
    def is_overridden(self) -> bool:
        """Check if any values are manually overridden."""
        return (
            self.override_lateral_rate
            or self.override_retention_rate
            or self.override_fixed_lateral
        )

    def __repr__(self) -> str:
        return f"<StudentsCalibration(org={self.organization_id}, grade={self.grade_code})>"


# =============================================================================
# LEGACY MODELS - Deprecated, kept for backward compatibility
# =============================================================================


class EnrollmentProjectionConfig(BaseModel, VersionedMixin):
    """
    Per budget version projection configuration.

    .. deprecated::
        This model is DEPRECATED as part of Phase 4A consolidation.
        Use StudentsConfig instead, which merges projection config with scenario multipliers.
        This model is kept for backward compatibility during migration.
    """

    __tablename__ = "students_projection_configs"
    __table_args__ = get_table_args(
        UniqueConstraint("version_id", name="uk_projection_configs_version"),
        CheckConstraint("projection_years BETWEEN 1 AND 10", name="ck_projection_configs_years_range"),
        CheckConstraint("school_max_capacity > 0", name="ck_projection_configs_capacity_positive"),
        CheckConstraint(
            "default_class_size BETWEEN 15 AND 40",
            name="ck_projection_configs_default_class_size_range",
        ),
        CheckConstraint(
            "status IN ('draft', 'validated')",
            name="ck_projection_configs_status_valid",
        ),
        comment=__doc__,
    )

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "EnrollmentProjectionConfig is deprecated. Use StudentsConfig instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_enrollment_scenarios", "id")),
        nullable=False,
        index=True,
    )
    base_year: Mapped[int] = mapped_column(Integer, nullable=False)
    projection_years: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    school_max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1850)
    default_class_size: Mapped[int] = mapped_column(Integer, nullable=False, default=25)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    validated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who validated this projection config",
    )

    scenario: Mapped["EnrollmentScenario"] = relationship("EnrollmentScenario")
    global_overrides: Mapped["EnrollmentGlobalOverride | None"] = relationship(
        "EnrollmentGlobalOverride",
        back_populates="projection_config",
        uselist=False,
        cascade="all, delete-orphan",
    )
    level_overrides: Mapped[list["EnrollmentLevelOverride"]] = relationship(
        "EnrollmentLevelOverride",
        back_populates="projection_config",
        cascade="all, delete-orphan",
    )
    grade_overrides: Mapped[list["EnrollmentGradeOverride"]] = relationship(
        "EnrollmentGradeOverride",
        back_populates="projection_config",
        cascade="all, delete-orphan",
    )
    projections: Mapped[list["EnrollmentProjection"]] = relationship(
        "EnrollmentProjection",
        back_populates="projection_config",
        cascade="all, delete-orphan",
    )


# Forward reference for EnrollmentScenario (defined in reference.py)
from app.models.reference import EnrollmentScenario  # noqa: E402


class EnrollmentGlobalOverride(BaseModel):
    """
    Layer 2 global overrides for a projection config.

    .. deprecated::
        This model is DEPRECATED as part of Phase 4A consolidation.
        Use StudentsOverride with scope_type='global' instead.
    """

    __tablename__ = "students_global_overrides"
    __table_args__ = get_table_args(
        UniqueConstraint("projection_config_id", name="uk_global_overrides_config"),
        CheckConstraint(
            "ps_entry_adjustment BETWEEN -20 AND 20",
            name="ck_global_overrides_ps_entry_adjustment_range",
        ),
        CheckConstraint(
            "retention_adjustment BETWEEN -0.05 AND 0.05",
            name="ck_global_overrides_retention_adjustment_range",
        ),
        CheckConstraint(
            "lateral_multiplier_override BETWEEN 0.5 AND 1.5",
            name="ck_global_overrides_lateral_multiplier_range",
        ),
        CheckConstraint(
            "class_size_override BETWEEN 20 AND 30",
            name="ck_global_overrides_class_size_range",
        ),
        comment=__doc__,
    )

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "EnrollmentGlobalOverride is deprecated. Use StudentsOverride with scope_type='global' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    projection_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "students_projection_configs", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ps_entry_adjustment: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retention_adjustment: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    lateral_multiplier_override: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    class_size_override: Mapped[int | None] = mapped_column(Integer, nullable=True)

    projection_config: Mapped[EnrollmentProjectionConfig] = relationship(
        "EnrollmentProjectionConfig", back_populates="global_overrides"
    )


class EnrollmentLevelOverride(BaseModel):
    """
    Layer 3 overrides per academic cycle.

    .. deprecated::
        This model is DEPRECATED as part of Phase 4A consolidation.
        Use StudentsOverride with scope_type='cycle' instead.
    """

    __tablename__ = "students_level_overrides"
    __table_args__ = get_table_args(
        UniqueConstraint(
            "projection_config_id",
            "cycle_id",
            name="uk_level_overrides_config_cycle",
        ),
        CheckConstraint(
            "class_size_ceiling BETWEEN 20 AND 30",
            name="ck_level_overrides_class_size_ceiling_range",
        ),
        CheckConstraint(
            "max_divisions BETWEEN 2 AND 10",
            name="ck_level_overrides_max_divisions_range",
        ),
        comment=__doc__,
    )

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "EnrollmentLevelOverride is deprecated. Use StudentsOverride with scope_type='cycle' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    projection_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "students_projection_configs", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=False,
        index=True,
    )
    class_size_ceiling: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_divisions: Mapped[int | None] = mapped_column(Integer, nullable=True)

    projection_config: Mapped[EnrollmentProjectionConfig] = relationship(
        "EnrollmentProjectionConfig", back_populates="level_overrides"
    )
    cycle: Mapped["AcademicCycle"] = relationship("AcademicCycle")

    @property
    def cycle_code(self) -> str:
        return self.cycle.code if self.cycle else ""

    @property
    def cycle_name(self) -> str:
        if not self.cycle:
            return ""
        return self.cycle.name_fr or self.cycle.name_en or self.cycle.code


class EnrollmentGradeOverride(BaseModel):
    """
    Layer 4 overrides per academic level (grade).

    .. deprecated::
        This model is DEPRECATED as part of Phase 4A consolidation.
        Use StudentsOverride with scope_type='level' instead.
    """

    __tablename__ = "students_grade_overrides"
    __table_args__ = get_table_args(
        UniqueConstraint(
            "projection_config_id",
            "level_id",
            name="uk_grade_overrides_config_level",
        ),
        CheckConstraint(
            "retention_rate BETWEEN 0.85 AND 1.00",
            name="ck_grade_overrides_retention_range",
        ),
        CheckConstraint(
            "lateral_entry BETWEEN 0 AND 50",
            name="ck_grade_overrides_lateral_entry_range",
        ),
        CheckConstraint(
            "max_divisions BETWEEN 2 AND 8",
            name="ck_grade_overrides_max_divisions_range",
        ),
        CheckConstraint(
            "class_size_ceiling BETWEEN 20 AND 30",
            name="ck_grade_overrides_class_size_ceiling_range",
        ),
        comment=__doc__,
    )

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "EnrollmentGradeOverride is deprecated. Use StudentsOverride with scope_type='level' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    projection_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "students_projection_configs", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_levels", "id")),
        nullable=False,
        index=True,
    )
    retention_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    lateral_entry: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_divisions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    class_size_ceiling: Mapped[int | None] = mapped_column(Integer, nullable=True)

    projection_config: Mapped[EnrollmentProjectionConfig] = relationship(
        "EnrollmentProjectionConfig", back_populates="grade_overrides"
    )
    level: Mapped["AcademicLevel"] = relationship("AcademicLevel")

    @property
    def level_code(self) -> str:
        return self.level.code if self.level else ""

    @property
    def level_name(self) -> str:
        if not self.level:
            return ""
        return self.level.name_fr or self.level.name_en or self.level.code


class EnrollmentDerivedParameter(BaseModel):
    """
    Auto-calculated enrollment parameters from rolling 4-year historical window.

    .. deprecated::
        This model is DEPRECATED as part of Phase 4A consolidation.
        Use StudentsCalibration instead, which merges derived parameters with manual overrides.
    """

    __tablename__ = "students_derived_parameters"
    __table_args__ = get_table_args(
        UniqueConstraint("organization_id", "grade_code", name="uk_derived_params_org_grade"),
        CheckConstraint("confidence IN ('high', 'medium', 'low')", name="ck_derived_params_confidence"),
        CheckConstraint(
            "progression_rate >= 0 AND progression_rate <= 3",
            name="ck_derived_params_progression_range",
        ),
        CheckConstraint(
            "lateral_entry_rate >= 0 AND lateral_entry_rate <= 1",
            name="ck_derived_params_lateral_range",
        ),
        CheckConstraint(
            "retention_rate >= 0 AND retention_rate <= 1",
            name="ck_derived_params_retention_range",
        ),
        CheckConstraint("years_used >= 0", name="ck_derived_params_years_non_negative"),
        comment=__doc__,
    )

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "EnrollmentDerivedParameter is deprecated. Use StudentsCalibration instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "admin_organizations", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grade_code: Mapped[str] = mapped_column(String(10), nullable=False)

    # Derived values
    progression_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    lateral_entry_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    retention_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )

    # Quality indicators
    confidence: Mapped[str] = mapped_column(String(10), nullable=False, default="low")
    std_deviation: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    years_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Metadata
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    source_years: Mapped[list[str]] = mapped_column(
        PortableJSON,
        nullable=False,
        default=list,
    )


class EnrollmentParameterOverride(BaseModel):
    """
    User overrides for enrollment parameters (lateral entry and retention rates).

    .. deprecated::
        This model is DEPRECATED as part of Phase 4A consolidation.
        Use StudentsCalibration instead, which merges derived parameters with manual overrides.
    """

    __tablename__ = "students_parameter_overrides"
    __table_args__ = get_table_args(
        UniqueConstraint("organization_id", "grade_code", name="uk_param_overrides_org_grade"),
        CheckConstraint(
            "manual_lateral_rate IS NULL OR (manual_lateral_rate >= 0 AND manual_lateral_rate <= 1)",
            name="ck_param_overrides_lateral_range",
        ),
        CheckConstraint(
            "manual_retention_rate IS NULL OR (manual_retention_rate >= 0.5 AND manual_retention_rate <= 1)",
            name="ck_param_overrides_retention_range",
        ),
        CheckConstraint(
            "manual_fixed_lateral IS NULL OR (manual_fixed_lateral >= 0 AND manual_fixed_lateral <= 100)",
            name="ck_param_overrides_fixed_lateral_range",
        ),
        comment=__doc__,
    )

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "EnrollmentParameterOverride is deprecated. Use StudentsCalibration instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "admin_organizations", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grade_code: Mapped[str] = mapped_column(String(10), nullable=False)

    # Override flags and values
    override_lateral_rate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_lateral_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )

    override_retention_rate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_retention_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )

    override_fixed_lateral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_fixed_lateral: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # Metadata
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who last updated this override",
    )
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class EnrollmentScenarioMultiplier(BaseModel):
    """
    Scenario-specific lateral entry multipliers.

    .. deprecated::
        This model is DEPRECATED as part of Phase 4A consolidation.
        Use StudentsConfig.lateral_multiplier instead.
    """

    __tablename__ = "students_scenario_multipliers"
    __table_args__ = get_table_args(
        UniqueConstraint("organization_id", "scenario_code", name="uk_scenario_mult_org_scenario"),
        CheckConstraint(
            "lateral_multiplier >= 0.1 AND lateral_multiplier <= 3.0",
            name="ck_scenario_mult_range",
        ),
        comment=__doc__,
    )

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "EnrollmentScenarioMultiplier is deprecated. Use StudentsConfig.lateral_multiplier instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "admin_organizations", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenario_code: Mapped[str] = mapped_column(String(20), nullable=False)

    # Single multiplier per scenario
    lateral_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, default=Decimal("1.00")
    )


# =============================================================================
# END OF STUDENTS MODELS
# =============================================================================
