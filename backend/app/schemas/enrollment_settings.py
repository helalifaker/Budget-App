"""
Pydantic schemas for Enrollment Settings (Dynamic Lateral Entry Calibration).

These schemas support the Settings tab which is Step 1 of the enrollment planning workflow.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Grade Classification Constants
# =============================================================================

# Entry point grades use percentage-based lateral entry
ENTRY_POINT_GRADES = frozenset({"MS", "GS", "CP", "6EME", "2NDE"})

# Maternelle funnel grades (special entry point handling)
MATERNELLE_FUNNEL_GRADES = frozenset({"MS", "GS"})

# Cycle transition grades (structural entry points)
CYCLE_TRANSITION_GRADES = frozenset({"CP", "6EME", "2NDE"})

# All other grades use fixed lateral entry values
INCIDENTAL_LATERAL_GRADES = frozenset({
    "CE1", "CE2", "CM1", "CM2", "5EME", "4EME", "3EME", "1ERE", "TLE"
})

# Document defaults from EFIR_Enrollment_Analysis_v2.md
DOCUMENT_DEFAULTS = {
    # Entry point grades (percentage-based)
    "MS": {"lateral_rate": Decimal("0.42"), "retention_rate": Decimal("0.96")},
    "GS": {"lateral_rate": Decimal("0.27"), "retention_rate": Decimal("0.96")},
    "CP": {"lateral_rate": Decimal("0.14"), "retention_rate": Decimal("0.96")},
    "6EME": {"lateral_rate": Decimal("0.09"), "retention_rate": Decimal("0.96")},
    "2NDE": {"lateral_rate": Decimal("0.10"), "retention_rate": Decimal("0.96")},
    # Incidental lateral grades (fixed values)
    "CE1": {"fixed_lateral": 7, "retention_rate": Decimal("0.96")},
    "CE2": {"fixed_lateral": 6, "retention_rate": Decimal("0.96")},
    "CM1": {"fixed_lateral": 5, "retention_rate": Decimal("0.96")},
    "CM2": {"fixed_lateral": 7, "retention_rate": Decimal("0.96")},
    "5EME": {"fixed_lateral": 5, "retention_rate": Decimal("0.96")},
    "4EME": {"fixed_lateral": 6, "retention_rate": Decimal("0.96")},
    "3EME": {"fixed_lateral": 6, "retention_rate": Decimal("0.96")},
    "1ERE": {"fixed_lateral": 6, "retention_rate": Decimal("0.96")},
    "TLE": {"fixed_lateral": 1, "retention_rate": Decimal("0.98")},
}


# =============================================================================
# Confidence Level Type
# =============================================================================

ConfidenceLevel = Literal["high", "medium", "low"]


# =============================================================================
# Calibration Status Schemas
# =============================================================================


class CalibrationStatus(BaseModel):
    """Status of auto-calibration from historical data."""

    last_calibrated: datetime | None = None
    source_years: list[str] = Field(default_factory=list)
    overall_confidence: ConfidenceLevel = "low"
    data_quality_score: int = Field(ge=1, le=5, default=1)  # 1-5 stars
    total_years_available: int = 0
    has_sufficient_data: bool = False

    model_config = ConfigDict(from_attributes=True)


class CalibrationRequest(BaseModel):
    """Request to trigger recalibration."""

    force: bool = Field(
        default=False,
        description="Force recalculation even if cached data is fresh",
    )


class CalibrationResult(BaseModel):
    """Result of a calibration operation."""

    success: bool
    message: str
    parameters_updated: int = 0
    source_years: list[str] = Field(default_factory=list)
    calculated_at: datetime | None = None
    fallback_used: bool = False

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Derived Parameter Schemas
# =============================================================================


class DerivedParameterBase(BaseModel):
    """Base schema for a derived parameter."""

    grade_code: str
    progression_rate: Decimal | None = None
    lateral_entry_rate: Decimal | None = None
    retention_rate: Decimal | None = None
    confidence: ConfidenceLevel = "low"
    std_deviation: Decimal | None = None
    years_used: int = 0


class DerivedParameterResponse(DerivedParameterBase):
    """Response schema for derived parameters."""

    id: UUID
    organization_id: UUID
    calculated_at: datetime
    source_years: list[str]

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Entry Point Rate Schemas (Percentage-Based)
# =============================================================================


class EntryPointRateBase(BaseModel):
    """Base schema for an entry point rate configuration."""

    grade_code: str
    is_entry_point: bool = True


class EntryPointRateResponse(EntryPointRateBase):
    """Response schema for entry point rates with derived and effective values."""

    # Derived from history
    derived_rate: Decimal | None = None
    derived_retention: Decimal | None = None
    confidence: ConfidenceLevel = "low"

    # Override status
    override_enabled: bool = False
    manual_rate: Decimal | None = None
    manual_retention: Decimal | None = None

    # Effective (resolved) values
    effective_rate: Decimal
    effective_retention: Decimal

    # UI helpers
    category: Literal["maternelle_funnel", "cycle_transition"] = "cycle_transition"

    model_config = ConfigDict(from_attributes=True)


class EntryPointRateUpdate(BaseModel):
    """Request to update an entry point rate override."""

    grade_code: str
    override_enabled: bool = False
    manual_rate: Decimal | None = Field(None, ge=Decimal("0"), le=Decimal("1"))
    manual_retention: Decimal | None = Field(None, ge=Decimal("0.5"), le=Decimal("1"))
    override_reason: str | None = None


# =============================================================================
# Incidental Lateral Schemas (Fixed Values)
# =============================================================================


class IncidentalLateralBase(BaseModel):
    """Base schema for incidental lateral entry configuration."""

    grade_code: str
    is_entry_point: bool = False


class IncidentalLateralResponse(IncidentalLateralBase):
    """Response schema for incidental lateral with derived and effective values."""

    # Derived from history
    derived_value: int | None = None
    derived_retention: Decimal | None = None
    confidence: ConfidenceLevel = "low"

    # Override status
    override_enabled: bool = False
    manual_value: int | None = None
    manual_retention: Decimal | None = None

    # Effective (resolved) values
    effective_value: int
    effective_retention: Decimal

    model_config = ConfigDict(from_attributes=True)


class IncidentalLateralUpdate(BaseModel):
    """Request to update an incidental lateral override."""

    grade_code: str
    override_enabled: bool = False
    manual_value: int | None = Field(None, ge=0, le=100)
    manual_retention: Decimal | None = Field(None, ge=Decimal("0.5"), le=Decimal("1"))
    override_reason: str | None = None


# =============================================================================
# Scenario Multiplier Schemas
# =============================================================================


class ScenarioMultiplierBase(BaseModel):
    """Base schema for scenario multiplier."""

    scenario_code: str
    lateral_multiplier: Decimal = Field(
        default=Decimal("1.00"),
        ge=Decimal("0.1"),
        le=Decimal("3.0"),
    )


class ScenarioMultiplierResponse(ScenarioMultiplierBase):
    """Response schema for scenario multiplier."""

    id: UUID
    organization_id: UUID
    updated_at: datetime

    # UI helpers
    scenario_name: str | None = None
    is_default: bool = True

    model_config = ConfigDict(from_attributes=True)


class ScenarioMultiplierUpdate(BaseModel):
    """Request to update scenario multipliers."""

    scenario_code: str
    lateral_multiplier: Decimal = Field(ge=Decimal("0.1"), le=Decimal("3.0"))


class ScenarioMultipliersBulkUpdate(BaseModel):
    """Request to update all scenario multipliers at once."""

    multipliers: list[ScenarioMultiplierUpdate]


# =============================================================================
# Parameter Override Schemas
# =============================================================================


class ParameterOverrideBase(BaseModel):
    """Base schema for parameter override."""

    grade_code: str
    override_lateral_rate: bool = False
    manual_lateral_rate: Decimal | None = Field(None, ge=Decimal("0"), le=Decimal("1"))
    override_retention_rate: bool = False
    manual_retention_rate: Decimal | None = Field(None, ge=Decimal("0.5"), le=Decimal("1"))
    override_fixed_lateral: bool = False
    manual_fixed_lateral: int | None = Field(None, ge=0, le=100)
    override_reason: str | None = None


class ParameterOverrideResponse(ParameterOverrideBase):
    """Response schema for parameter override."""

    id: UUID
    organization_id: UUID
    updated_at: datetime
    updated_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ParameterOverrideUpdate(ParameterOverrideBase):
    """Request to update a parameter override."""

    pass


class ParameterOverridesBulkUpdate(BaseModel):
    """Request to update multiple parameter overrides at once."""

    overrides: list[ParameterOverrideUpdate]


# =============================================================================
# Combined Settings Response
# =============================================================================


class EnrollmentSettingsResponse(BaseModel):
    """Complete enrollment settings for the Settings tab."""

    calibration_status: CalibrationStatus
    entry_point_rates: list[EntryPointRateResponse]
    incidental_lateral: list[IncidentalLateralResponse]
    scenario_multipliers: list[ScenarioMultiplierResponse]

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Historical Data Summary
# =============================================================================


class HistoricalYearSummary(BaseModel):
    """Summary of enrollment data for a single historical year."""

    school_year: str
    total_students: int
    grades_with_data: int
    is_complete: bool


class HistoricalDataSummary(BaseModel):
    """Summary of available historical data for calibration."""

    available_years: list[HistoricalYearSummary]
    recommended_window: list[str]
    total_years: int
    has_sufficient_data: bool
    earliest_year: str | None = None
    latest_year: str | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Effective Rate Resolution Schema
# =============================================================================


class EffectiveRates(BaseModel):
    """Resolved effective rates for projection engine input."""

    grade_code: str
    retention_rate: Decimal
    lateral_entry_rate: Decimal | None = None  # For entry points
    lateral_entry_fixed: int | None = None  # For incidental
    is_percentage_based: bool

    @property
    def is_entry_point(self) -> bool:
        return self.is_percentage_based

    model_config = ConfigDict(from_attributes=True)


class AllEffectiveRates(BaseModel):
    """All effective rates for all grades."""

    rates: dict[str, EffectiveRates]
    scenario_multiplier: Decimal = Decimal("1.0")
    calibration_timestamp: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
