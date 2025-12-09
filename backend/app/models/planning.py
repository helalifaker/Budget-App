"""
SQLAlchemy Models for Planning Layer (Modules 7-12).

These modules handle operational planning and budget calculations:
- Module 7: Enrollment Planning
- Module 8: Class Structure Planning
- Module 9: DHG Workforce Planning (core calculation engine)
- Module 10: Revenue Planning
- Module 11: Cost Planning (Personnel & Operating)
- Module 12: Capital Expenditure Planning

All planning data is versioned and drives financial projections.
"""

from __future__ import annotations

import os
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import BaseModel, VersionedMixin, get_fk_target

if TYPE_CHECKING:
    from app.models.configuration import (
        AcademicCycle,
        AcademicLevel,
        NationalityType,
        Subject,
        TeacherCategory,
    )

# ==============================================================================
# Module 7: Enrollment Planning
# ==============================================================================


class EnrollmentPlan(BaseModel, VersionedMixin):
    """
    Enrollment projections per level, nationality, and version.

    This is the PRIMARY DRIVER for all budget calculations.
    Changes to enrollment cascade through:
    - Class structure → DHG hours → Teacher FTE → Personnel costs
    - Revenue (tuition fees)
    - Facility needs

    Business Rule: Total enrollment capped at ~1,875 students (facility capacity).
    """

    __tablename__ = "enrollment_plans"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "level_id",
            "nationality_type_id",
            name="uk_enrollment_version_level_nat",
        ),
        CheckConstraint("student_count >= 0", name="ck_enrollment_non_negative"),
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
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")
    nationality_type: Mapped[NationalityType] = relationship("NationalityType")


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
    3. System calculates breakdown: total × percentage = students per nationality
    4. Breakdown stored in enrollment_plans for downstream revenue calculations
    """

    __tablename__ = "nationality_distributions"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
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
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
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
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")

    @validates("french_pct", "saudi_pct", "other_pct")
    def validate_percentage(self, key: str, value: Decimal) -> Decimal:
        """Validate percentage is within valid range."""
        if value < 0 or value > 100:
            raise ValueError(f"{key} must be between 0 and 100")
        return value


# ==============================================================================
# Module 8: Class Structure Planning
# ==============================================================================


class ClassStructure(BaseModel, VersionedMixin):
    """
    Calculated class formations based on enrollment and class size parameters.

    Calculation Logic:
    1. Sum enrollment by level (across all nationalities)
    2. Divide by target_class_size to get number of classes
    3. Verify avg_class_size doesn't exceed max_class_size
    4. For Maternelle, calculate ATSEM needs (1 per class)

    This drives:
    - DHG hours calculation (classes × hours per subject)
    - Facility needs (classroom count)
    - Support staff needs (ATSEM)
    """

    __tablename__ = "class_structures"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
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
        ForeignKey(get_fk_target("efir_budget", "academic_levels", "id")),
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

    @validates("avg_class_size")
    def validate_avg_class_size(self, key: str, value: Decimal | None) -> Decimal | None:
        """
        Validate that avg_class_size is within realistic bounds.

        This provides basic validation at the model level. Full validation against
        class_size_params should be performed in the service layer using the
        validators.class_structure module.

        Args:
            key: Field name being validated
            value: The avg_class_size value

        Returns:
            The validated value

        Raises:
            ValueError: If avg_class_size is unrealistic (≤0 or >50)
        """
        if value is not None:
            if value <= 0 or value > 50:
                raise ValueError(
                    f"Average class size {value} is unrealistic. "
                    f"Must be between 1 and 50 students."
                )
        return value

    # Relationships
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")


# ==============================================================================
# Module 9: DHG Workforce Planning
# ==============================================================================


class DHGSubjectHours(BaseModel, VersionedMixin):
    """
    DHG hours calculation per subject and level.

    Formula:
        total_hours_per_week = number_of_classes × hours_per_class_per_week

    If is_split = true (half-size groups):
        total_hours_per_week = number_of_classes × hours_per_class_per_week × 2

    Example:
        Mathématiques in 6ème:
        - 6 classes × 4.5 hours = 27 hours/week
    """

    __tablename__ = "dhg_subject_hours"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "subject_id",
            "level_id",
            name="uk_dhg_hours_version_subject_level",
        ),
        CheckConstraint(
            "number_of_classes > 0",
            name="ck_dhg_hours_classes_positive",
        ),
        CheckConstraint(
            "hours_per_class_per_week > 0 AND hours_per_class_per_week <= 12",
            name="ck_dhg_hours_realistic_range",
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

    number_of_classes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of classes at this level (from class_structures)",
    )

    hours_per_class_per_week: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Hours per class per week (from subject_hours_matrix)",
    )

    total_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="Total hours per week (classes × hours, ×2 if split)",
    )

    is_split: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether classes are split (counts as double hours)",
    )

    # Relationships
    subject: Mapped[Subject] = relationship("Subject")
    level: Mapped[AcademicLevel] = relationship("AcademicLevel")


class DHGTeacherRequirement(BaseModel, VersionedMixin):
    """
    Teacher FTE requirements per subject (DHG calculation result).

    Formula (Secondary):
        simple_fte = total_hours_per_week / 18  (18h = standard teaching hours)
        rounded_fte = CEILING(simple_fte)  (round up to whole teachers)
        hsa_hours = MAX(0, total_hours_per_week - (rounded_fte × 18))

    Formula (Primary):
        simple_fte = total_hours_per_week / 24  (24h = standard for primary)
        rounded_fte = CEILING(simple_fte)

    HSA (Heures Supplémentaires Annuelles):
        - Overtime hours when total doesn't divide evenly
        - Capped at max_hsa_hours (typically 2-4 hours per teacher)

    Example:
        Mathématiques across all Collège levels:
        - Total: 96 hours/week
        - Simple FTE: 96 / 18 = 5.33
        - Rounded FTE: 6 teachers
        - HSA: 96 - (6 × 18) = -12 (no overtime, teachers underutilized)
    """

    __tablename__ = "dhg_teacher_requirements"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "subject_id",
            name="uk_dhg_teacher_req_version_subject",
        ),
        CheckConstraint(
            "total_hours_per_week >= 0",
            name="ck_dhg_req_hours_non_negative",
        ),
        CheckConstraint(
            "simple_fte >= 0",
            name="ck_dhg_req_fte_non_negative",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "subjects", "id")),
        nullable=False,
        index=True,
        comment="Subject",
    )

    total_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="Sum of DHG hours for this subject across all levels",
    )

    standard_teaching_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Standard teaching hours (18h secondary, 24h primary)",
    )

    simple_fte: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Exact FTE (total_hours / standard_hours)",
    )

    rounded_fte: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Rounded up FTE (ceiling of simple_fte)",
    )

    hsa_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Overtime hours needed (or negative if underutilized)",
    )

    # Relationships
    subject: Mapped[Subject] = relationship("Subject")


class TeacherAllocation(BaseModel, VersionedMixin):
    """
    Actual teacher assignments (TRMD - Tableau de Répartition des Moyens par Discipline).

    This is the GAP ANALYSIS between needs (DHG) and available resources.

    TRMD Logic:
        Besoins (Need) = dhg_teacher_requirements.rounded_fte
        Moyens (Available) = SUM(teacher_allocations.fte_count)
        Déficit = Besoins - Moyens

    If Déficit > 0: Need to recruit or assign HSA
    If Déficit < 0: Overallocated (teachers with free hours)

    Teacher Categories:
        - AEFE_DETACHED: School pays PRRD contribution (~41,863 EUR/teacher)
        - AEFE_FUNDED: Fully funded by AEFE (no school cost)
        - LOCAL: Locally recruited (paid by school in SAR)
    """

    __tablename__ = "teacher_allocations"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "subject_id",
            "cycle_id",
            "category_id",
            name="uk_allocation_version_subject_cycle_category",
        ),
        CheckConstraint("fte_count > 0", name="ck_allocation_fte_positive"),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "subjects", "id")),
        nullable=False,
        index=True,
        comment="Subject",
    )

    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_cycles", "id")),
        nullable=False,
        index=True,
        comment="Academic cycle (primary grouping for allocations)",
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "teacher_categories", "id")),
        nullable=False,
        index=True,
        comment="Teacher category (AEFE Detached, AEFE Funded, Local)",
    )

    fte_count: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Number of FTE allocated",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Allocation notes (teacher names, constraints, etc.)",
    )

    # Relationships
    subject: Mapped[Subject] = relationship("Subject")
    cycle: Mapped[AcademicCycle] = relationship("AcademicCycle")
    category: Mapped[TeacherCategory] = relationship("TeacherCategory")


# ==============================================================================
# Module 10: Revenue Planning
# ==============================================================================


class RevenuePlan(BaseModel, VersionedMixin):
    """
    Revenue projections by account code.

    Revenue Categories:
        - 70110-70130: Tuition fees by trimester (T1=40%, T2=30%, T3=30%)
        - 70140: DAI (Droit Annuel d'Inscription)
        - 70150: Registration fees
        - 70200: Transportation fees
        - 70300: Canteen fees
        - 77xxx: Other revenue

    Calculation Methods:
        - is_calculated = true: Auto-calculated from enrollment × fee_structure
        - is_calculated = false: Manual entry

    Business Rules:
        - Tuition revenue = Σ(enrollment × fee_structure.amount_sar) - sibling_discounts
        - Sibling discount (25%) applies from 3rd child onward (tuition only)
    """

    __tablename__ = "revenue_plans"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "account_code",
            name="uk_revenue_version_account",
        ),
        CheckConstraint(
            "amount_sar >= 0",
            name="ck_revenue_non_negative",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PCG revenue account (70xxx-77xxx)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Line item description",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category (tuition, fees, other)",
    )

    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Revenue amount in SAR",
    )

    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether auto-calculated from drivers",
    )

    calculation_driver: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Driver reference (e.g., 'enrollment', 'fee_structure')",
    )

    trimester: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Trimester (1-3) for tuition, NULL for annual",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Revenue notes and assumptions",
    )


# ==============================================================================
# Module 11: Cost Planning
# ==============================================================================


class PersonnelCostPlan(BaseModel, VersionedMixin):
    """
    Personnel cost projections (salaries, benefits, social charges).

    Cost Categories:
        - 64110: Teaching salaries
        - 64120: Administrative salaries
        - 64130: Support staff salaries
        - 64500: Social charges (21% of gross salary)
        - 64600: Benefits and allowances

    Calculation Methods:
        - is_calculated = true: Auto-calculated from teacher_allocations × teacher_cost_params
        - is_calculated = false: Manual entry (for admin, support staff)

    Teacher Costs:
        AEFE Detached:
            - PRRD contribution (EUR) × EUR_TO_SAR_RATE
            - Example: 41,863 EUR × 4.05 = 169,545 SAR/teacher

        Local:
            - Base salary (SAR)
            - Social charges (salary × 0.21)
            - Benefits/allowances
            - HSA (overtime hours × hourly_rate)
    """

    __tablename__ = "personnel_cost_plans"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "account_code",
            "cycle_id",
            "category_id",
            name="uk_personnel_cost_version_account_cycle_category",
        ),
        CheckConstraint(
            "fte_count >= 0",
            name="ck_personnel_fte_non_negative",
        ),
        CheckConstraint(
            "unit_cost_sar >= 0 AND total_cost_sar >= 0",
            name="ck_personnel_costs_non_negative",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PCG expense account (64xxx)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Cost description",
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "teacher_categories", "id")),
        nullable=True,
        index=True,
        comment="Teacher category (NULL for non-teaching staff)",
    )

    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "academic_cycles", "id")),
        nullable=True,
        index=True,
        comment="Academic cycle (NULL for admin/support)",
    )

    fte_count: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Number of FTE",
    )

    unit_cost_sar: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Cost per FTE (SAR/year)",
    )

    total_cost_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Total cost (FTE × unit_cost)",
    )

    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether auto-calculated from drivers",
    )

    calculation_driver: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Driver (e.g., 'dhg_allocation', 'class_structure')",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Cost notes",
    )

    # Relationships
    category: Mapped[TeacherCategory] = relationship("TeacherCategory")
    cycle: Mapped[AcademicCycle] = relationship("AcademicCycle")


class OperatingCostPlan(BaseModel, VersionedMixin):
    """
    Operating expense projections (non-personnel).

    Cost Categories:
        - 60xxx: Purchases (supplies, books, equipment)
        - 61xxx: External services (maintenance, cleaning, security)
        - 62xxx: Other external expenses (insurance, legal)
        - 63xxx: Taxes and duties
        - 65xxx: Other operating expenses
        - 66xxx: Financial expenses
        - 68xxx: Exceptional expenses

    Calculation Methods:
        - is_calculated = true: Driver-based (enrollment, square meters, etc.)
        - is_calculated = false: Manual entry

    Common Drivers:
        - Enrollment: Books, supplies, student services
        - Square meters: Utilities, maintenance, cleaning
        - Fixed: Insurance, legal, subscriptions
    """

    __tablename__ = "operating_cost_plans"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "account_code",
            name="uk_operating_cost_version_account",
        ),
        CheckConstraint(
            "amount_sar >= 0",
            name="ck_operating_cost_non_negative",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PCG expense account (60xxx-68xxx)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Expense description",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category (supplies, utilities, maintenance, insurance, etc.)",
    )

    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Expense amount in SAR",
    )

    is_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether auto-calculated from driver",
    )

    calculation_driver: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Driver (e.g., 'enrollment', 'square_meters', 'fixed')",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Expense notes",
    )


# ==============================================================================
# Module 12: Capital Expenditure Planning
# ==============================================================================


class CapExPlan(BaseModel, VersionedMixin):
    """
    Capital expenditure projections (asset purchases).

    Asset Categories (PCG):
        - 20xxx: Intangible assets (software, licenses)
        - 21xxx: Tangible assets
            - 2131: Buildings
            - 2135: Installations (HVAC, electrical)
            - 2154: Equipment and furniture
            - 2155: IT equipment
            - 2158: Other tangible assets

    Depreciation:
        - Buildings: 20-40 years
        - Installations: 10-20 years
        - Equipment: 5-10 years
        - IT equipment: 3-5 years
        - Software: 3-5 years

    Business Rules:
        - Total cost = quantity × unit_cost_sar
        - Acquisition date tracks when asset will be purchased
        - Useful life determines depreciation schedule
    """

    __tablename__ = "capex_plans"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "account_code",
            "description",
            name="uk_capex_version_account_description",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_capex_quantity_positive",
        ),
        CheckConstraint(
            "unit_cost_sar >= 0 AND total_cost_sar >= 0",
            name="ck_capex_costs_non_negative",
        ),
        CheckConstraint(
            "useful_life_years > 0 AND useful_life_years <= 50",
            name="ck_capex_life_realistic",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PCG account code (20xxx-21xxx assets)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Asset description",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category (equipment, IT, furniture, building, software)",
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of units",
    )

    unit_cost_sar: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Cost per unit (SAR)",
    )

    total_cost_sar: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Total cost (quantity × unit_cost)",
    )

    acquisition_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Expected acquisition date",
    )

    useful_life_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Depreciation life (years)",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="CapEx notes and justification",
    )
