"""
SQLAlchemy Models for Enrollment Projection subsystem (Module 7 upgrade).

Implements the 4-layer override architecture and cached projections described in
ENROLLMENT_PROJECTION_IMPLEMENTATION_PLAN.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    BaseModel,
    PortableJSON,
    ReferenceDataModel,
    VersionedMixin,
    get_fk_target,
    get_table_args,
)

if TYPE_CHECKING:
    from app.models.configuration import AcademicCycle, AcademicLevel
    # Note: BudgetVersion is inherited from VersionedMixin
    # Note: User model not imported - query auth.users directly when needed


class EnrollmentScenario(ReferenceDataModel):
    """Scenario defaults (Worst/Base/Best) for projections."""

    __tablename__ = "enrollment_scenarios"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_enrollment_scenarios_code"),
        comment=__doc__,
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)

    ps_entry: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_growth_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    default_retention: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    terminal_retention: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    lateral_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)

    color_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class EnrollmentLateralEntryDefault(ReferenceDataModel):
    """Historical base lateral entry per academic level."""

    __tablename__ = "enrollment_lateral_entry_defaults"
    __table_args__ = get_table_args(
        UniqueConstraint("level_id", name="uk_lateral_defaults_level"),
        CheckConstraint("base_lateral_entry >= 0", name="ck_lateral_defaults_non_negative"),
        comment=__doc__,
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
        nullable=False,
        index=True,
    )
    base_lateral_entry: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    level: Mapped[AcademicLevel] = relationship("AcademicLevel")


class EnrollmentProjectionConfig(BaseModel, VersionedMixin):
    """Per budget version projection configuration."""

    __tablename__ = "enrollment_projection_configs"
    __table_args__ = get_table_args(
        UniqueConstraint("budget_version_id", name="uk_projection_configs_version"),
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

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "enrollment_scenarios", "id")),
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
    # Note: No ForeignKey constraint at ORM level because auth.users is managed
    # by Supabase. The database FK constraint is managed via migrations.
    validated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who validated this projection config",
    )

    scenario: Mapped[EnrollmentScenario] = relationship("EnrollmentScenario")
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

    # Note: budget_version relationship is inherited from VersionedMixin
    # Note: No relationship to User model - query auth.users directly when needed


class EnrollmentGlobalOverride(BaseModel):
    """Layer 2 global overrides for a projection config."""

    __tablename__ = "enrollment_global_overrides"
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

    projection_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "enrollment_projection_configs", "id"), ondelete="CASCADE"),
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
    """Layer 3 overrides per academic cycle."""

    __tablename__ = "enrollment_level_overrides"
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

    projection_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "enrollment_projection_configs", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_cycles", "id")),
        nullable=False,
        index=True,
    )
    class_size_ceiling: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_divisions: Mapped[int | None] = mapped_column(Integer, nullable=True)

    projection_config: Mapped[EnrollmentProjectionConfig] = relationship(
        "EnrollmentProjectionConfig", back_populates="level_overrides"
    )
    cycle: Mapped[AcademicCycle] = relationship("AcademicCycle")

    @property
    def cycle_code(self) -> str:
        return self.cycle.code if self.cycle else ""

    @property
    def cycle_name(self) -> str:
        if not self.cycle:
            return ""
        return self.cycle.name_fr or self.cycle.name_en or self.cycle.code


class EnrollmentGradeOverride(BaseModel):
    """Layer 4 overrides per academic level (grade)."""

    __tablename__ = "enrollment_grade_overrides"
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

    projection_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "enrollment_projection_configs", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
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
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")

    @property
    def level_code(self) -> str:
        return self.level.code if self.level else ""

    @property
    def level_name(self) -> str:
        if not self.level:
            return ""
        return self.level.name_fr or self.level.name_en or self.level.code


class EnrollmentProjection(BaseModel):
    """Cached projection results per school year and level."""

    __tablename__ = "enrollment_projections"
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
        ForeignKey(get_fk_target("efir_budget", "enrollment_projection_configs", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    school_year: Mapped[str] = mapped_column(String(9), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
        nullable=False,
        index=True,
    )

    projected_students: Mapped[int] = mapped_column(Integer, nullable=False)
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

    projection_config: Mapped[EnrollmentProjectionConfig] = relationship(
        "EnrollmentProjectionConfig", back_populates="projections"
    )
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")


# =============================================================================
# NEW: Enrollment Derived Parameters & Settings Tables
# =============================================================================


class EnrollmentDerivedParameter(BaseModel):
    """Auto-calculated enrollment parameters from rolling 4-year historical window."""

    __tablename__ = "enrollment_derived_parameters"
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

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "organizations", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grade_code: Mapped[str] = mapped_column(String(10), nullable=False)

    # Derived values
    progression_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )  # e.g., 1.1410 = 114.10%
    lateral_entry_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )  # e.g., 0.1410 = 14.10%
    retention_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )  # e.g., 0.9600 = 96.00%

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

    # Note: organization relationship omitted since Organization model not defined in SQLAlchemy
    # Database FK constraint exists via migration


class EnrollmentParameterOverride(BaseModel):
    """User overrides for enrollment parameters (lateral entry and retention rates)."""

    __tablename__ = "enrollment_parameter_overrides"
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

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "organizations", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grade_code: Mapped[str] = mapped_column(String(10), nullable=False)

    # Override flags and values
    override_lateral_rate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_lateral_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )  # 0.0000 to 1.0000

    override_retention_rate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_retention_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )  # 0.5000 to 1.0000

    override_fixed_lateral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_fixed_lateral: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0 to 100

    # Metadata
    # Note: No ForeignKey constraint at ORM level because auth.users is managed
    # by Supabase. The database FK constraint is managed via migrations.
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who last updated this override",
    )
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Note: No relationship to User model - query auth.users directly when needed
    # This follows the pattern established in base.py AuditMixin


class EnrollmentScenarioMultiplier(BaseModel):
    """Scenario-specific lateral entry multipliers."""

    __tablename__ = "enrollment_scenario_multipliers"
    __table_args__ = get_table_args(
        UniqueConstraint("organization_id", "scenario_code", name="uk_scenario_mult_org_scenario"),
        CheckConstraint(
            "lateral_multiplier >= 0.1 AND lateral_multiplier <= 3.0",
            name="ck_scenario_mult_range",
        ),
        comment=__doc__,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "organizations", "id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenario_code: Mapped[str] = mapped_column(String(20), nullable=False)

    # Single multiplier per scenario
    lateral_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, default=Decimal("1.00")
    )

    # Note: organization relationship omitted since Organization model not defined in SQLAlchemy
