"""
SQLAlchemy Models for Reference Data (ref_* tables).

This module contains all reference/lookup tables that provide master data
for the EFIR Budget Planning Application. These tables are:
- Mostly read-only after initial setup
- Used for dropdowns, lookups, and foreign key references
- Shared across all budget versions (not versioned)

Tables:
- ref_academic_cycles: Academic cycles (Maternelle, Elementaire, College, Lycee)
- ref_academic_levels: Academic levels/grades (PS, MS, GS, CP, CE1, etc.)
- ref_subjects: Subjects taught (Mathematics, French, etc.)
- ref_teacher_categories: Teacher employment categories (AEFE, Local, etc.)
- ref_fee_categories: Fee categories (Tuition, Registration, etc.)
- ref_nationality_types: Nationality groups for fee calculation
- ref_enrollment_scenarios: Enrollment projection scenarios (Worst, Base, Best)
- ref_kpi_definitions: KPI metadata and formulas

Author: Claude Code
Date: 2025-12-16
"""

from __future__ import annotations

import enum
import os
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    BaseModel,
    ReferenceDataModel,
    get_fk_target,
    get_schema,
    get_table_args,
)


# =============================================================================
# ENUMS
# =============================================================================


class KPICategory(str, enum.Enum):
    """KPI category for grouping and filtering."""

    EDUCATIONAL = "educational"  # Student/teacher ratios, class sizes
    FINANCIAL = "financial"  # Revenue, cost, margin ratios
    OPERATIONAL = "operational"  # Enrollment, capacity, utilization
    STRATEGIC = "strategic"  # Long-term trends, benchmarks


# =============================================================================
# ACADEMIC STRUCTURE REFERENCE TABLES
# =============================================================================


class AcademicCycle(ReferenceDataModel):
    """
    Academic cycles (Maternelle, Elementaire, College, Lycee).

    AEFE/French System Cycles:
    - Cycle 1: Maternelle (PS, MS, GS) - Ages 3-5
    - Cycle 2: Elementaire (CP, CE1, CE2) - Ages 6-8
    - Cycle 3: Elementaire/College (CM1, CM2, 6eme) - Ages 9-11
    - Cycle 4: College (5eme, 4eme, 3eme) - Ages 12-14
    - Lycee: Lycee (2nde, 1ere, Terminale) - Ages 15-17

    Example:
    --------
    code: "MATERNELLE"
    name_en: "Preschool"
    name_fr: "Maternelle"
    sort_order: 1
    """

    __tablename__ = "ref_academic_cycles"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_academic_cycles_code"),
        comment=__doc__,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique cycle code (e.g., 'MATERNELLE', 'COLLEGE')",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Cycle name in English",
    )
    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Cycle name in French",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order",
    )
    requires_atsem: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether ATSEM (classroom assistant) is required",
    )

    # Relationships
    levels: Mapped[list["AcademicLevel"]] = relationship(
        "AcademicLevel",
        back_populates="cycle",
        order_by="AcademicLevel.sort_order",
    )

    def __repr__(self) -> str:
        return f"<AcademicCycle(code={self.code})>"


class AcademicLevel(ReferenceDataModel):
    """
    Academic levels/grades within cycles.

    French System Levels:
    ---------------------
    Maternelle: PS (Petite Section), MS (Moyenne Section), GS (Grande Section)
    Elementaire: CP, CE1, CE2, CM1, CM2
    College: 6eme, 5eme, 4eme, 3eme
    Lycee: 2nde, 1ere, Terminale

    Each level has:
    - Default retention rate (typically 0.95-0.98)
    - Default class size range
    - Subject hours configuration
    - Fee structure association

    Example:
    --------
    code: "6EME"
    name_en: "6th Grade"
    name_fr: "Sixième"
    cycle_id: <uuid of College cycle>
    default_retention_rate: 0.96
    """

    __tablename__ = "ref_academic_levels"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_academic_levels_code"),
        CheckConstraint(
            "default_retention_rate BETWEEN 0.80 AND 1.00",
            name="ck_academic_levels_retention_range",
        ),
        comment=__doc__,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique level code (e.g., 'PS', '6EME', '2NDE')",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Level name in English",
    )
    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Level name in French",
    )
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_academic_cycles", "id")),
        nullable=False,
        index=True,
        comment="Parent academic cycle",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order within cycle",
    )
    is_secondary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if this is a secondary level (College/Lycee)",
    )
    default_retention_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.96"),
        comment="Default retention rate (e.g., 0.9600 = 96%)",
    )

    # Relationships
    cycle: Mapped[AcademicCycle] = relationship(
        "AcademicCycle",
        back_populates="levels",
    )

    def __repr__(self) -> str:
        return f"<AcademicLevel(code={self.code})>"


# =============================================================================
# TEACHER REFERENCE TABLES
# =============================================================================


class Subject(ReferenceDataModel):
    """
    Subjects taught in the curriculum.

    Used for:
    - Subject hours matrix configuration
    - DHG (Dotation Horaire Globale) calculations
    - Teacher allocation by subject specialty

    Subject Categories:
    -------------------
    - Core: French, Mathematics, Sciences
    - Languages: English, Arabic, Spanish, German
    - Arts: Visual Arts, Music
    - Physical: PE (EPS)
    - Other: Religion, ICT, etc.

    Example:
    --------
    code: "MATH"
    name_en: "Mathematics"
    name_fr: "Mathématiques"
    category: "core"
    """

    __tablename__ = "ref_subjects"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_subjects_code"),
        comment=__doc__,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique subject code (e.g., 'MATH', 'FRAN', 'EPS')",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Subject name in English",
    )
    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Subject name in French",
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Subject category (core, language, arts, physical, other)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this subject is actively taught",
    )

    def __repr__(self) -> str:
        return f"<Subject(code={self.code})>"


class TeacherCategory(ReferenceDataModel):
    """
    Teacher employment categories.

    AEFE Network Categories:
    ------------------------
    1. RESIDENT: AEFE-funded positions (PRRD ~41,863 EUR contribution)
    2. LOCAL_CDI: Local permanent contracts
    3. LOCAL_CDD: Local fixed-term contracts
    4. EXPAT: Expatriate teachers (fully funded by AEFE)
    5. DETACHE: Seconded from French Ministry

    Each category has different:
    - Cost structures (base salary, PRRD, GOSI, housing)
    - Benefits packages
    - Contract terms

    Example:
    --------
    code: "RESIDENT"
    name_en: "AEFE Resident"
    name_fr: "Résident AEFE"
    is_aefe: True
    """

    __tablename__ = "ref_teacher_categories"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_teacher_categories_code"),
        comment=__doc__,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique category code (e.g., 'RESIDENT', 'LOCAL_CDI')",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Category name in English",
    )
    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Category name in French",
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
        comment="Whether AEFE provides PRRD contribution",
    )

    def __repr__(self) -> str:
        return f"<TeacherCategory(code={self.code})>"


# =============================================================================
# FEE STRUCTURE REFERENCE TABLES
# =============================================================================


class FeeCategory(ReferenceDataModel):
    """
    Fee categories for revenue planning.

    Standard Fee Categories:
    ------------------------
    - TUITION_T1: Primary tuition (Maternelle, Elementaire)
    - TUITION_T2: Secondary tuition (College)
    - TUITION_T3: Lycee tuition
    - REGISTRATION: Annual registration fees
    - FACILITIES: Facility usage fees
    - TRANSPORT: School transport fees
    - CANTEEN: Cafeteria fees
    - EXTRACURRICULAR: After-school activities

    Example:
    --------
    code: "TUITION_T1"
    name_en: "Primary Tuition"
    name_fr: "Frais de scolarité Primaire"
    account_code: "706000"
    """

    __tablename__ = "ref_fee_categories"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_fee_categories_code"),
        comment=__doc__,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique fee category code",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Category name in English",
    )
    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Category name in French",
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

    def __repr__(self) -> str:
        return f"<FeeCategory(code={self.code})>"


class NationalityType(ReferenceDataModel):
    """
    Nationality groups for fee calculation.

    Fee Differentiation:
    --------------------
    Different fee rates may apply based on nationality:
    - FRENCH: French nationals (may receive AEFE subsidies)
    - SAUDI: Saudi nationals (local rate)
    - OTHER: Other nationalities (international rate)

    Sibling Discounts:
    ------------------
    Different sibling discount rules may apply by nationality group.

    Example:
    --------
    code: "FRENCH"
    name_en: "French"
    name_fr: "Français"
    vat_applicable: False
    """

    __tablename__ = "ref_nationality_types"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_nationality_types_code"),
        comment=__doc__,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique nationality type code",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Nationality name in English",
    )
    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Nationality name in French",
    )
    vat_applicable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether VAT applies",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order",
    )

    def __repr__(self) -> str:
        return f"<NationalityType(code={self.code})>"


# =============================================================================
# ENROLLMENT PROJECTION REFERENCE TABLES
# =============================================================================


class EnrollmentScenario(ReferenceDataModel):
    """
    Enrollment projection scenario defaults (Worst/Base/Best).

    Scenarios provide default parameters for enrollment projections:
    - PS entry numbers
    - Growth rates
    - Retention rates
    - Lateral entry multipliers

    Standard Scenarios:
    -------------------
    - WORST: Conservative estimate (low growth, higher attrition)
    - BASE: Expected/median scenario
    - BEST: Optimistic estimate (high growth, low attrition)

    Example:
    --------
    code: "BASE"
    name_en: "Base Case"
    name_fr: "Scénario de base"
    ps_entry: 95
    entry_growth_rate: 0.0200 (2%)
    default_retention: 0.9600 (96%)
    lateral_multiplier: 1.00
    """

    __tablename__ = "ref_enrollment_scenarios"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_enrollment_scenarios_code"),
        comment=__doc__,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique scenario code (e.g., 'WORST', 'BASE', 'BEST')",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Scenario name in English",
    )
    name_fr: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Scenario name in French",
    )
    description_en: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Scenario description in English",
    )
    description_fr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Scenario description in French",
    )

    # Default projection parameters
    ps_entry: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Default PS (Petite Section) entry count",
    )
    entry_growth_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual growth rate for entry points (e.g., 0.0200 = 2%)",
    )
    default_retention: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Default retention rate (e.g., 0.9600 = 96%)",
    )
    terminal_retention: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Retention rate for terminal levels (GS, CM2, 3eme, Terminale)",
    )
    lateral_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Multiplier for lateral entry calculations",
    )

    # Display settings
    color_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Color code for UI display (hex or name)",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order",
    )

    def __repr__(self) -> str:
        return f"<EnrollmentScenario(code={self.code})>"


# =============================================================================
# KPI REFERENCE TABLES
# =============================================================================


class KPIDefinition(BaseModel):
    """
    KPI metadata catalog with formulas and targets.

    Defines all KPIs calculated for budget analysis, including formulas,
    targets, and benchmarks. Acts as configuration for KPI calculations.

    Standard KPIs:
    --------------
    Educational:
    - H/E Ratio: (Teaching FTE x 18h x 52 weeks) / Total Students
    - E/D Ratio: Total Students / Total Classes
    - Student/Teacher Ratio: Total Students / Teaching FTE
    - Average Class Size: Total Students / Total Classes

    Financial:
    - Staff Cost %: (Personnel Costs / Revenue) x 100
    - Operating Margin: ((Revenue - Costs) / Revenue) x 100
    - Revenue per Student: Total Revenue / Total Students
    - Cost per Student: Total Costs / Total Students

    EFIR 2024 Benchmarks:
    ---------------------
    - Staff Cost Ratio: 52.6% (AEFE benchmark: 60-75%)
    - Operating Margin: 9.6% (AEFE benchmark: 5-10%)
    - Student/Teacher: 7.6 (AEFE benchmark: 8-12)
    - Average Class Size: 21-25 (AEFE benchmark: 20-26)

    Example:
    --------
    code: "STAFF_COST_PCT"
    name_en: "Staff Cost Ratio"
    name_fr: "Ratio masse salariale"
    formula_text: "(Total Personnel Costs / Total Revenue) x 100"
    target_value: 60.00
    unit: "percentage"
    """

    __tablename__ = "ref_kpi_definitions"
    __table_args__ = get_table_args(
        UniqueConstraint("code", name="uk_kpi_definition_code"),
        CheckConstraint("target_value >= 0", name="ck_kpi_target_positive"),
        comment=__doc__,
    )

    # KPI Identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique KPI code (e.g., 'H_E_RATIO', 'STAFF_COST_PCT')",
    )
    name_en: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="KPI name in English",
    )
    name_fr: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="KPI name in French",
    )

    # Classification
    category: Mapped[KPICategory] = mapped_column(
        Enum(KPICategory, schema=get_schema("efir_budget"), values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="KPI category for grouping",
    )

    # Formula & Calculation
    formula_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable formula (e.g., '(Personnel Costs / Revenue) x 100')",
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unit of measure (ratio, percentage, currency, count, hours)",
    )

    # Target & Benchmarks
    target_value: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Target benchmark value (e.g., 60.00 for 60%)",
    )
    min_acceptable: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Minimum acceptable value (lower bound)",
    )
    max_acceptable: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Maximum acceptable value (upper bound)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this KPI is actively calculated",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description and interpretation guide",
    )

    def __repr__(self) -> str:
        return f"<KPIDefinition(code={self.code}, category={self.category.value})>"


# =============================================================================
# END OF REFERENCE MODELS
# =============================================================================
