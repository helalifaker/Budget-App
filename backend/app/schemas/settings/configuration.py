"""
Pydantic schemas for configuration endpoints.

Request and response models for configuration API operations.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import ScenarioType, VersionStatus

# Backward compatibility alias for imports
BudgetVersionStatus = VersionStatus

# ==============================================================================
# System Configuration Schemas
# ==============================================================================


class SystemConfigBase(BaseModel):
    """Base schema for system configuration."""

    key: str = Field(..., max_length=100, description="Configuration key")
    value: dict[str, Any] = Field(..., description="Configuration value (JSONB)")
    category: str = Field(..., max_length=50, description="Configuration category")
    description: str = Field(..., description="Configuration description")
    is_active: bool = Field(default=True, description="Whether configuration is active")


class SystemConfigCreate(SystemConfigBase):
    """Schema for creating system configuration."""

    pass


class SystemConfigUpdate(BaseModel):
    """Schema for updating system configuration."""

    value: dict[str, Any] | None = None
    category: str | None = Field(None, max_length=50)
    description: str | None = None
    is_active: bool | None = None


class SystemConfigResponse(SystemConfigBase):
    """Schema for system configuration response."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Version Schemas
# ==============================================================================


class VersionBase(BaseModel):
    """Base schema for version.

    Year Convention:
    - fiscal_year is the STARTING year of the academic year
    - fiscal_year=2026 means academic year 2026-2027
    - academic_year must match: "{fiscal_year}-{fiscal_year+1}"

    School Period (within a fiscal year):
    - P1 (Jan-Aug): End of previous academic year (e.g., Jan-Aug 2026 → AY 2025-2026)
    - P2 (Sep-Dec): Start of next academic year (e.g., Sep-Dec 2026 → AY 2026-2027)
    - NULL: Full Year (both periods combined)
    """

    name: str = Field(..., max_length=100, description="Version name")
    fiscal_year: int = Field(
        ...,
        ge=2020,
        le=2100,
        description="Starting year of target academic year (e.g., 2026 for 2026-2027)",
    )
    academic_year: str = Field(
        ...,
        max_length=20,
        description="Academic year display (must match fiscal_year, e.g., '2026-2027' for fiscal_year=2026)",
    )
    scenario_type: ScenarioType = Field(
        default=ScenarioType.BUDGET,
        description="Scenario type (ACTUAL, BUDGET, FORECAST, STRATEGIC, WHAT_IF)",
    )
    notes: str | None = Field(None, description="Version notes")

    @model_validator(mode="after")
    def validate_academic_year_matches_fiscal_year(self) -> "VersionBase":
        """Ensure academic_year matches the STARTING year convention.

        fiscal_year is the STARTING year, so:
        - fiscal_year=2026 should have academic_year="2026-2027"
        """
        expected = f"{self.fiscal_year}-{self.fiscal_year + 1}"
        if self.academic_year != expected:
            raise ValueError(
                f"academic_year must be '{expected}' for fiscal_year {self.fiscal_year}. "
                f"The fiscal_year is the STARTING year of the academic year."
            )
        return self


# Backward compatibility alias
BudgetVersionBase = VersionBase


class VersionCreate(VersionBase):
    """Schema for creating version."""

    organization_id: uuid.UUID | None = Field(
        None,
        description="Organization this version belongs to. If not provided, defaults to the user's organization or the default organization for single-tenant deployments.",
    )
    parent_version_id: uuid.UUID | None = Field(None, description="Parent version for forecast revisions")


# Backward compatibility alias
BudgetVersionCreate = VersionCreate


class VersionUpdate(BaseModel):
    """Schema for updating version."""

    name: str | None = Field(None, max_length=100)
    notes: str | None = None


# Backward compatibility alias
BudgetVersionUpdate = VersionUpdate


class VersionClone(BaseModel):
    """Schema for cloning version.

    Year Convention:
    - fiscal_year is the STARTING year of the academic year
    - fiscal_year=2026 means academic year 2026-2027
    - academic_year must match: "{fiscal_year}-{fiscal_year+1}"

    School Period (within a fiscal year):
    - P1 (Jan-Aug): End of previous academic year (e.g., Jan-Aug 2026 → AY 2025-2026)
    - P2 (Sep-Dec): Start of next academic year (e.g., Sep-Dec 2026 → AY 2026-2027)
    - NULL: Full Year (both periods combined)
    """

    name: str = Field(..., max_length=100, description="New version name")
    fiscal_year: int = Field(
        ...,
        ge=2020,
        le=2100,
        description="Starting year of target academic year (e.g., 2026 for 2026-2027)",
    )
    academic_year: str = Field(
        ...,
        max_length=20,
        description="Academic year display (must match fiscal_year, e.g., '2026-2027' for fiscal_year=2026)",
    )
    scenario_type: ScenarioType = Field(
        default=ScenarioType.BUDGET,
        description="Scenario type for the cloned version (ACTUAL, BUDGET, FORECAST, STRATEGIC, WHAT_IF)",
    )
    clone_configuration: bool = Field(
        default=True,
        description="Whether to clone configuration data (class sizes, subjects, costs, fees)",
    )

    @model_validator(mode="after")
    def validate_academic_year_matches_fiscal_year(self) -> "VersionClone":
        """Ensure academic_year matches the STARTING year convention."""
        expected = f"{self.fiscal_year}-{self.fiscal_year + 1}"
        if self.academic_year != expected:
            raise ValueError(
                f"academic_year must be '{expected}' for fiscal_year {self.fiscal_year}. "
                f"The fiscal_year is the STARTING year of the academic year."
            )
        return self


# Backward compatibility alias
BudgetVersionClone = VersionClone


class VersionResponse(VersionBase):
    """Schema for version response."""

    id: uuid.UUID
    status: VersionStatus
    submitted_at: datetime | None = None
    submitted_by_id: uuid.UUID | None = None
    approved_at: datetime | None = None
    approved_by_id: uuid.UUID | None = None
    is_baseline: bool
    parent_version_id: uuid.UUID | None = None
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def convert_types_from_sqlite(cls, data: Any) -> Any:
        """
        Convert SQLite integer types to proper Python types.

        Handles edge cases where SQLite returns:
        - Timestamps as integers instead of datetime objects
        - UUIDs as integers instead of UUID objects

        This causes AttributeError when Pydantic tries to call .replace()
        during serialization.

        Args:
            data: Raw data (dict or SQLAlchemy model)

        Returns:
            Data with properly typed fields
        """
        # Handle both dict and SQLAlchemy model instances
        if hasattr(data, '__dict__'):
            data_dict = {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
        elif isinstance(data, dict):
            data_dict = data.copy()
        else:
            return data

        # Convert datetime fields from integers to datetime objects
        datetime_fields = ['created_at', 'updated_at', 'submitted_at', 'approved_at']
        for field in datetime_fields:
            value = data_dict.get(field)
            if value is not None and isinstance(value, int):
                try:
                    data_dict[field] = datetime.fromtimestamp(value, tz=UTC)
                except (ValueError, OSError):
                    # If conversion fails, use current time for required fields
                    if field in ('created_at', 'updated_at'):
                        data_dict[field] = datetime.now(UTC)
                    else:
                        data_dict[field] = None

        # Convert UUID fields from integers to UUID objects
        uuid_fields = ['id', 'submitted_by_id', 'approved_by_id', 'parent_version_id', 'organization_id']
        for field in uuid_fields:
            value = data_dict.get(field)
            if value is not None and isinstance(value, int):
                try:
                    # Convert integer to UUID (zero-padded hex string)
                    data_dict[field] = uuid.UUID(int=value)
                except (ValueError, TypeError):
                    # If conversion fails, keep as-is (will fail validation if required)
                    pass

        return data_dict


# Backward compatibility alias
BudgetVersionResponse = VersionResponse


# ==============================================================================
# Academic Reference Data Schemas
# ==============================================================================


class AcademicCycleResponse(BaseModel):
    """Schema for academic cycle response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class AcademicLevelResponse(BaseModel):
    """Schema for academic level response."""

    id: uuid.UUID
    cycle_id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    sort_order: int
    is_secondary: bool

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Class Size Parameters Schemas
# ==============================================================================


class ClassSizeParamBase(BaseModel):
    """Base schema for class size parameters."""

    level_id: uuid.UUID | None = Field(None, description="Academic level (None for cycle default)")
    cycle_id: uuid.UUID | None = Field(None, description="Academic cycle (None for level-specific)")
    min_class_size: int = Field(..., ge=1, le=50, description="Minimum class size")
    target_class_size: int = Field(..., ge=1, le=50, description="Target class size")
    max_class_size: int = Field(..., ge=1, le=50, description="Maximum class size")
    notes: str | None = None

    @field_validator("target_class_size")
    @classmethod
    def validate_target(cls, v: int, info) -> int:
        """Validate target is greater than min."""
        min_size = info.data.get("min_class_size")
        if min_size and v <= min_size:
            raise ValueError("target_class_size must be greater than min_class_size")
        return v

    @field_validator("max_class_size")
    @classmethod
    def validate_max(cls, v: int, info) -> int:
        """Validate max is greater than or equal to target."""
        target_size = info.data.get("target_class_size")
        if target_size and v < target_size:
            raise ValueError("max_class_size must be greater than or equal to target_class_size")
        return v


class ClassSizeParamCreate(ClassSizeParamBase):
    """Schema for creating class size parameter."""

    version_id: uuid.UUID


class ClassSizeParamUpdate(BaseModel):
    """Schema for updating class size parameter."""

    min_class_size: int | None = Field(None, ge=1, le=50)
    target_class_size: int | None = Field(None, ge=1, le=50)
    max_class_size: int | None = Field(None, ge=1, le=50)
    notes: str | None = None


class ClassSizeParamResponse(ClassSizeParamBase):
    """Schema for class size parameter response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Class Size Parameters Batch Schemas (for optimistic locking)
# ==============================================================================


class ClassSizeParamBatchEntry(BaseModel):
    """Single entry for batch class size operations."""

    level_id: uuid.UUID = Field(..., description="Academic level ID")
    min_class_size: int = Field(..., ge=1, le=50, description="Minimum class size")
    target_class_size: int = Field(..., ge=1, le=50, description="Target class size")
    max_class_size: int = Field(..., ge=1, le=50, description="Maximum class size")
    notes: str | None = None
    updated_at: datetime | None = Field(
        None,
        description="Expected updated_at for optimistic locking (None for new entries)",
    )

    @field_validator("target_class_size")
    @classmethod
    def validate_target(cls, v: int, info) -> int:
        """Validate target is greater than min."""
        min_size = info.data.get("min_class_size")
        if min_size and v <= min_size:
            raise ValueError("target_class_size must be greater than min_class_size")
        return v

    @field_validator("max_class_size")
    @classmethod
    def validate_max(cls, v: int, info) -> int:
        """Validate max is greater than or equal to target."""
        target_size = info.data.get("target_class_size")
        if target_size and v < target_size:
            raise ValueError("max_class_size must be >= target_class_size")
        return v


class ClassSizeParamBatchRequest(BaseModel):
    """Request schema for batch class size params save."""

    version_id: uuid.UUID = Field(..., description="Budget version ID")
    entries: list[ClassSizeParamBatchEntry] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Class size entries to upsert (max 50, typically 14-15 levels)",
    )


class ClassSizeParamBatchResponseEntry(BaseModel):
    """Single entry in batch response."""

    level_id: uuid.UUID
    id: uuid.UUID | None = Field(None, description="Record ID (None if conflict)")
    status: Literal["created", "updated", "conflict"] = Field(
        ..., description="Operation status"
    )
    error: str | None = Field(None, description="Error message if conflict")
    updated_at: datetime | None = Field(
        None, description="New updated_at timestamp (for subsequent optimistic locking)"
    )


class ClassSizeParamBatchResponse(BaseModel):
    """Response schema for batch class size params save."""

    created_count: int = Field(..., description="Number of new records created")
    updated_count: int = Field(..., description="Number of existing records updated")
    conflict_count: int = Field(
        ..., description="Number of records with optimistic locking conflicts"
    )
    entries: list[ClassSizeParamBatchResponseEntry] = Field(
        ..., description="Per-entry results"
    )


# ==============================================================================
# Subject Hours Matrix Schemas
# ==============================================================================


class SubjectResponse(BaseModel):
    """Schema for subject response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    category: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SubjectHoursBase(BaseModel):
    """Base schema for subject hours."""

    subject_id: uuid.UUID
    level_id: uuid.UUID
    hours_per_week: Decimal = Field(..., ge=0, le=12, decimal_places=2, description="Hours per week per class")
    is_split: bool = Field(default=False, description="Whether classes are split (half-size groups)")
    notes: str | None = None


class SubjectHoursCreate(SubjectHoursBase):
    """Schema for creating subject hours."""

    version_id: uuid.UUID


class SubjectHoursUpdate(BaseModel):
    """Schema for updating subject hours."""

    hours_per_week: Decimal | None = Field(None, ge=0, le=12, decimal_places=2)
    is_split: bool | None = None
    notes: str | None = None


class SubjectHoursResponse(SubjectHoursBase):
    """Schema for subject hours response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Teacher Cost Parameters Schemas
# ==============================================================================


class TeacherCategoryResponse(BaseModel):
    """Schema for teacher category response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    description: str | None
    is_aefe: bool

    model_config = ConfigDict(from_attributes=True)


class TeacherCostParamBase(BaseModel):
    """Base schema for teacher cost parameters."""

    category_id: uuid.UUID
    cycle_id: uuid.UUID | None = Field(None, description="Academic cycle (None for all cycles)")
    prrd_contribution_eur: Decimal | None = Field(
        None,
        ge=0,
        decimal_places=2,
        description="PRRD contribution per teacher (EUR, for AEFE detached)",
    )
    avg_salary_sar: Decimal | None = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Average salary (SAR/year, for local teachers)",
    )
    social_charges_rate: Decimal = Field(
        default=Decimal("0.21"),
        ge=0,
        le=1,
        decimal_places=4,
        description="Social charges rate (e.g., 0.21 for 21%)",
    )
    benefits_allowance_sar: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
        description="Benefits/allowances per teacher (SAR/year)",
    )
    hsa_hourly_rate_sar: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="HSA (overtime) hourly rate (SAR)",
    )
    max_hsa_hours: Decimal = Field(
        default=Decimal("4.00"),
        ge=0,
        le=10,
        decimal_places=2,
        description="Maximum HSA hours per teacher per week",
    )
    notes: str | None = None


class TeacherCostParamCreate(TeacherCostParamBase):
    """Schema for creating teacher cost parameter."""

    version_id: uuid.UUID


class TeacherCostParamUpdate(BaseModel):
    """Schema for updating teacher cost parameter."""

    prrd_contribution_eur: Decimal | None = Field(None, ge=0, decimal_places=2)
    avg_salary_sar: Decimal | None = Field(None, ge=0, decimal_places=2)
    social_charges_rate: Decimal | None = Field(None, ge=0, le=1, decimal_places=4)
    benefits_allowance_sar: Decimal | None = Field(None, ge=0, decimal_places=2)
    hsa_hourly_rate_sar: Decimal | None = Field(None, ge=0, decimal_places=2)
    max_hsa_hours: Decimal | None = Field(None, ge=0, le=10, decimal_places=2)
    notes: str | None = None


class TeacherCostParamResponse(TeacherCostParamBase):
    """Schema for teacher cost parameter response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Fee Structure Schemas
# ==============================================================================


class FeeCategoryResponse(BaseModel):
    """Schema for fee category response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    account_code: str
    is_recurring: bool
    allows_sibling_discount: bool

    model_config = ConfigDict(from_attributes=True)


class NationalityTypeResponse(BaseModel):
    """Schema for nationality type response."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    vat_applicable: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class FeeStructureBase(BaseModel):
    """Base schema for fee structure."""

    level_id: uuid.UUID
    nationality_type_id: uuid.UUID
    fee_category_id: uuid.UUID
    amount_sar: Decimal = Field(..., ge=0, decimal_places=2, description="Fee amount in SAR")
    trimester: int | None = Field(None, ge=1, le=3, description="Trimester (1-3) for tuition, None for annual fees")
    notes: str | None = None


class FeeStructureCreate(FeeStructureBase):
    """Schema for creating fee structure."""

    version_id: uuid.UUID


class FeeStructureUpdate(BaseModel):
    """Schema for updating fee structure."""

    amount_sar: Decimal | None = Field(None, ge=0, decimal_places=2)
    notes: str | None = None


class FeeStructureResponse(FeeStructureBase):
    """Schema for fee structure response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Timetable Constraints Schemas (Module 6)
# ============================================================================


class TimetableConstraintBase(BaseModel):
    """Base schema for timetable constraints."""

    level_id: uuid.UUID = Field(..., description="Academic level")
    total_hours_per_week: Decimal = Field(
        ..., ge=0, le=60, decimal_places=2, description="Total student hours per week"
    )
    max_hours_per_day: Decimal = Field(
        ..., ge=0, le=12, decimal_places=2, description="Maximum hours per day"
    )
    days_per_week: int = Field(..., ge=4, le=6, description="School days per week")
    requires_lunch_break: bool = Field(
        True, description="Whether lunch break is required"
    )
    min_break_duration_minutes: int = Field(
        60, ge=30, le=120, description="Minimum break duration (minutes)"
    )
    notes: str | None = None


class TimetableConstraintCreate(TimetableConstraintBase):
    """Schema for creating timetable constraint."""

    version_id: uuid.UUID = Field(..., description="Budget version")

    @model_validator(mode="after")
    def validate_max_hours(self) -> "TimetableConstraintCreate":
        """Validate max_hours_per_day ≤ total_hours_per_week."""
        if self.max_hours_per_day > self.total_hours_per_week:
            raise ValueError(
                "max_hours_per_day cannot exceed total_hours_per_week"
            )
        return self


class TimetableConstraintUpdate(BaseModel):
    """Schema for updating timetable constraint."""

    version_id: uuid.UUID | None = None
    level_id: uuid.UUID | None = None
    total_hours_per_week: Decimal | None = Field(
        None, ge=0, le=60, decimal_places=2
    )
    max_hours_per_day: Decimal | None = Field(None, ge=0, le=12, decimal_places=2)
    days_per_week: int | None = Field(None, ge=4, le=6)
    requires_lunch_break: bool | None = None
    min_break_duration_minutes: int | None = Field(None, ge=30, le=120)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_max_hours(self) -> "TimetableConstraintUpdate":
        """Validate max_hours_per_day ≤ total_hours_per_week if both provided."""
        if (
            self.max_hours_per_day is not None
            and self.total_hours_per_week is not None
            and self.max_hours_per_day > self.total_hours_per_week
        ):
            raise ValueError(
                "max_hours_per_day cannot exceed total_hours_per_week"
            )
        return self


class TimetableConstraintResponse(TimetableConstraintBase):
    """Schema for timetable constraint response."""

    id: uuid.UUID
    version_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Subject Hours Matrix - Batch Operations & Templates
# ==============================================================================


class SubjectHoursEntry(BaseModel):
    """Single entry for batch subject hours operations."""

    subject_id: uuid.UUID
    level_id: uuid.UUID
    hours_per_week: Decimal | None = Field(
        None,
        ge=0,
        le=12,
        decimal_places=2,
        description="Hours per week (None = delete entry)",
    )
    is_split: bool = False
    notes: str | None = None


class SubjectHoursBatchRequest(BaseModel):
    """Request schema for batch subject hours save."""

    version_id: uuid.UUID
    entries: list[SubjectHoursEntry] = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Subject hours entries (max 200 per request)",
    )


class SubjectHoursBatchResponse(BaseModel):
    """Response schema for batch subject hours save."""

    created_count: int
    updated_count: int
    deleted_count: int
    errors: list[str] = Field(default_factory=list)


class LevelInfo(BaseModel):
    """Level information for matrix response."""

    id: uuid.UUID
    code: str
    name_en: str
    name_fr: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class SubjectLevelHours(BaseModel):
    """Hours configuration for a specific subject-level combination."""

    hours_per_week: Decimal | None
    is_split: bool
    notes: str | None


class SubjectWithHours(BaseModel):
    """Subject with hours data for matrix response."""

    id: uuid.UUID
    code: str
    name_en: str
    name_fr: str
    category: str
    is_applicable: bool = True
    hours: dict[str, SubjectLevelHours] = Field(
        default_factory=dict,
        description="Hours keyed by level_id",
    )

    model_config = ConfigDict(from_attributes=True)


class SubjectHoursMatrixResponse(BaseModel):
    """Response schema for subject hours matrix."""

    cycle_id: uuid.UUID
    cycle_code: str
    cycle_name: str
    levels: list[LevelInfo]
    subjects: list[SubjectWithHours]


class TemplateInfo(BaseModel):
    """Information about an available curriculum template."""

    code: str
    name: str
    description: str
    cycle_codes: list[str]


class ApplyTemplateRequest(BaseModel):
    """Request schema for applying curriculum template."""

    version_id: uuid.UUID
    template_code: str = Field(..., description="Template code (e.g., AEFE_STANDARD_COLL)")
    cycle_codes: list[str] = Field(
        ...,
        min_length=1,
        description="Cycles to apply template to (e.g., ['COLL', 'LYC'])",
    )
    overwrite_existing: bool = Field(
        default=False,
        description="Whether to overwrite existing values",
    )


class ApplyTemplateResponse(BaseModel):
    """Response schema for applying curriculum template."""

    applied_count: int
    skipped_count: int
    template_name: str


class SubjectCreateRequest(BaseModel):
    """Request schema for creating a custom subject."""

    code: str = Field(
        ...,
        min_length=2,
        max_length=6,
        pattern=r"^[A-Z0-9]+$",
        description="Subject code (2-6 uppercase alphanumeric)",
    )
    name_fr: str = Field(..., max_length=100, description="French name")
    name_en: str = Field(..., max_length=100, description="English name")
    category: Literal["core", "elective", "specialty", "local"] = Field(
        ..., description="Subject category"
    )
    applicable_cycles: list[str] = Field(
        ...,
        min_length=1,
        description="Applicable cycle codes (e.g., ['COLL', 'LYC'])",
    )
