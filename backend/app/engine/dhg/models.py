"""
DHG Engine - Pydantic Models

Input/output models for DHG (Dotation Horaire Globale) calculations.
All models use Pydantic for validation and type safety.

French Education System Context:
- Collège (Middle School): 6ème, 5ème, 4ème, 3ème
- Lycée (High School): 2nde, 1ère, Terminale
- Standard teaching hours: 18h/week for secondary, 24h/week for primary
- HSA (Heures Supplémentaires Annuelles): Overtime, max 2-4h per teacher
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EducationLevel(str, Enum):
    """Education level categories for DHG calculations."""

    PRIMARY = "primary"  # Maternelle + Élémentaire
    SECONDARY = "secondary"  # Collège + Lycée


class SubjectHours(BaseModel):
    """
    Subject teaching hours configuration.

    Defines the hours per week allocated to a subject for a specific level.
    """

    subject_id: UUID = Field(..., description="Subject UUID")
    subject_code: str = Field(..., description="Subject code (e.g., 'MATH', 'FRAN')")
    subject_name: str = Field(..., description="Subject name (e.g., 'Mathématiques')")
    level_id: UUID = Field(..., description="Academic level UUID")
    level_code: str = Field(..., description="Level code (e.g., '6EME', 'TERMINALE')")
    hours_per_week: Decimal = Field(
        ..., ge=Decimal("0"), le=Decimal("10"), description="Hours per week for this subject"
    )

    @field_validator("hours_per_week")
    @classmethod
    def validate_hours_reasonable(cls, v: Decimal) -> Decimal:
        """Ensure hours per week is reasonable (0-10h)."""
        if not (Decimal("0") <= v <= Decimal("10")):
            raise ValueError(f"Hours per week must be between 0 and 10, got {v}")
        return v

    model_config = ConfigDict(
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "subject_id": "123e4567-e89b-12d3-a456-426614174000",
                "subject_code": "MATH",
                "subject_name": "Mathématiques",
                "level_id": "123e4567-e89b-12d3-a456-426614174001",
                "level_code": "6EME",
                "hours_per_week": 4.5,
            }
        },
    )


class DHGInput(BaseModel):
    """
    Input data for DHG hours calculation.

    Contains class counts and subject hours matrix for calculating
    total teaching hours required.
    """

    level_id: UUID = Field(..., description="Academic level UUID")
    level_code: str = Field(..., description="Level code (e.g., '6EME', 'TERMINALE')")
    education_level: EducationLevel = Field(
        ..., description="Education level (primary or secondary)"
    )
    number_of_classes: int = Field(
        ..., ge=0, le=80, description="Number of classes at this level"
    )
    subject_hours_list: list[SubjectHours] = Field(
        ..., description="List of subject hours for this level"
    )

    @field_validator("number_of_classes")
    @classmethod
    def validate_class_count_reasonable(cls, v: int) -> int:
        """Ensure class count is reasonable (0-50)."""
        if not (0 <= v <= 50):
            raise ValueError(f"Number of classes must be between 0 and 50, got {v}")
        return v

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=True,
        json_schema_extra={
            "example": {
                "level_id": "123e4567-e89b-12d3-a456-426614174001",
                "level_code": "6EME",
                "education_level": "secondary",
                "number_of_classes": 6,
                "subject_hours_list": [
                    {
                        "subject_id": "123e4567-e89b-12d3-a456-426614174000",
                        "subject_code": "MATH",
                        "subject_name": "Mathématiques",
                        "level_id": "123e4567-e89b-12d3-a456-426614174001",
                        "level_code": "6EME",
                        "hours_per_week": 4.5,
                    },
                    {
                        "subject_id": "123e4567-e89b-12d3-a456-426614174002",
                        "subject_code": "FRAN",
                        "subject_name": "Français",
                        "level_id": "123e4567-e89b-12d3-a456-426614174001",
                        "level_code": "6EME",
                        "hours_per_week": 5.0,
                    },
                ],
            }
        },
    )


class DHGHoursResult(BaseModel):
    """
    DHG hours calculation result for a single level.

    Contains the total teaching hours required for a level based on
    the number of classes and subject hours.
    """

    level_id: UUID = Field(..., description="Academic level UUID")
    level_code: str = Field(..., description="Level code")
    education_level: EducationLevel = Field(..., description="Education level")
    number_of_classes: int = Field(..., description="Number of classes")
    total_hours: Decimal = Field(..., description="Total DHG hours per week")
    subject_breakdown: dict[str, Decimal] = Field(
        default_factory=dict, description="Hours breakdown by subject code"
    )
    subjects_hours_breakdown: list[SubjectHours] = Field(
        default_factory=list,
        description="List of subject hours associated with this level",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "level_id": "123e4567-e89b-12d3-a456-426614174001",
                "level_code": "6EME",
                "education_level": "secondary",
                "number_of_classes": 6,
                "total_hours": 57.0,
                "subject_breakdown": {
                    "MATH": 27.0,  # 6 classes × 4.5h
                    "FRAN": 30.0,  # 6 classes × 5.0h
                },
            }
        },
    )


@dataclass
class TRMDGapResult:
    """Result of TRMD gap calculation for teacher coverage."""

    required_fte: Decimal
    available_aefe_fte: Decimal
    available_local_fte: Decimal
    gap_fte: Decimal
    is_overstaffed: bool
    gap_coverage_recommendation: str


class FTECalculationResult(BaseModel):
    """
    FTE (Full-Time Equivalent) calculation result.

    Converts DHG hours into teacher FTE requirements based on
    standard teaching hours (18h/week for secondary, 24h/week for primary).
    """

    level_id: UUID = Field(..., description="Academic level UUID")
    level_code: str = Field(..., description="Level code")
    education_level: EducationLevel = Field(..., description="Education level")
    total_dhg_hours: Decimal = Field(..., description="Total DHG hours per week")
    standard_hours: Decimal = Field(..., description="Standard teaching hours per week")
    simple_fte: Decimal = Field(..., description="Simple FTE (hours ÷ standard)")
    rounded_fte: int = Field(..., description="Rounded FTE (teachers needed)")
    fte_utilization: Decimal = Field(
        ..., description="FTE utilization percentage (simple ÷ rounded × 100)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "level_id": "123e4567-e89b-12d3-a456-426614174001",
                "level_code": "6EME",
                "education_level": "secondary",
                "total_dhg_hours": 96.0,
                "standard_hours": 18.0,
                "simple_fte": 5.33,
                "rounded_fte": 6,
                "fte_utilization": 88.83,
            }
        }


class TeacherRequirement(BaseModel):
    """
    Teacher workforce requirement calculation.

    Aggregates DHG hours and FTE across all levels to determine
    total teacher needs, broken down by subject.
    """

    subject_code: str = Field(..., description="Subject code")
    subject_name: str = Field(..., description="Subject name")
    total_dhg_hours: Decimal = Field(..., description="Total DHG hours across all levels")
    standard_hours: Decimal = Field(..., description="Standard teaching hours per week")
    simple_fte: Decimal = Field(..., description="Simple FTE required")
    rounded_fte: int = Field(..., description="Rounded FTE (teachers needed)")
    hsa_hours: Decimal | None = Field(
        None, description="HSA (overtime) hours needed if any"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "subject_code": "MATH",
                "subject_name": "Mathématiques",
                "total_dhg_hours": 96.0,
                "standard_hours": 18.0,
                "simple_fte": 5.33,
                "rounded_fte": 6,
                "hsa_hours": 0.0,
            }
        }


class HSAAllocation(BaseModel):
    """
    HSA (Heures Supplémentaires Annuelles) allocation.

    Overtime hours allocation when DHG hours exceed available positions.
    Business Rule: Max 2-4 hours per teacher per week.
    """

    subject_code: str = Field(..., description="Subject code")
    subject_name: str = Field(..., description="Subject name")
    dhg_hours_needed: Decimal = Field(..., description="Total DHG hours needed")
    available_fte: int = Field(..., description="Available full-time positions")
    available_hours: Decimal = Field(
        ..., description="Hours covered by available FTE (FTE × 18h)"
    )
    hsa_hours_needed: Decimal = Field(
        ..., description="Additional hours needed (DHG - available)"
    )
    hsa_within_limit: bool = Field(
        ..., description="Whether HSA is within max limit (2-4h per teacher)"
    )
    max_hsa_per_teacher: Decimal = Field(
        default=Decimal("4.0"), description="Maximum HSA hours per teacher (default: 4h)"
    )

    @field_validator("max_hsa_per_teacher")
    @classmethod
    def validate_max_hsa_range(cls, v: Decimal) -> Decimal:
        """Ensure max HSA is within allowed range (2-4h)."""
        if not (Decimal("2.0") <= v <= Decimal("4.0")):
            raise ValueError(f"Max HSA per teacher must be between 2 and 4, got {v}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "subject_code": "MATH",
                "subject_name": "Mathématiques",
                "dhg_hours_needed": 96.0,
                "available_fte": 5,
                "available_hours": 90.0,
                "hsa_hours_needed": 6.0,
                "hsa_within_limit": True,
                "max_hsa_per_teacher": 4.0,
            }
        }
