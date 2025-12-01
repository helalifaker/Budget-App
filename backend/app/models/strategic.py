"""
EFIR Budget Planning Application - Strategic Layer Models

This module contains SQLAlchemy models for Module 18:
- Module 18: 5-Year Strategic Planning (strategic_plans, strategic_plan_scenarios,
  strategic_plan_projections, strategic_initiatives)

The Strategic Layer enables multi-year financial forecasting and scenario modeling
for EFIR's 5-year strategic planning cycle, supporting budget projections under
different growth assumptions and tracking major strategic initiatives.

Author: Claude Code
Date: 2025-12-01
Version: 5.0.0
"""

from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


# ============================================================================
# Module 18: 5-Year Strategic Planning - Enums
# ============================================================================


class ScenarioType(str, enum.Enum):
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


# ============================================================================
# Module 18: 5-Year Strategic Planning - Models
# ============================================================================


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
    Plan: "EFIR Strategic Plan 2025-2030"
    Base Year: 2025 (Year 1 of 5)
    Status: approved
    Description: "5-year strategic plan with enrollment growth to 1,500 students
                  and new secondary campus in Year 4"
    """

    __tablename__ = "strategic_plans"
    __table_args__ = (
        UniqueConstraint("name", name="uk_strategic_plan_name"),
        CheckConstraint(
            "base_year >= 2000 AND base_year <= 2100",
            name="ck_strategic_plan_year_range",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Plan Identification
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

    # Timeline
    base_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Starting year of 5-year plan (e.g., 2025 for 2025-2030 plan)",
    )

    # Status
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


class StrategicPlanScenario(BaseModel):
    """
    Strategic plan scenario with growth assumptions and parameters.

    Each strategic plan contains 3-4 scenarios representing different
    growth trajectories and market conditions. Scenarios differ by
    their underlying assumptions for enrollment growth, fee increases,
    and cost inflation rates.

    Scenario Types:
    ---------------
    1. Conservative: Slower enrollment growth (0-2%), minimal fee increases
       - Use for: Risk planning, minimum viable budget
       - Example: Economic downturn, increased competition

    2. Base Case: Expected trajectory (3-5% enrollment growth)
       - Use for: Primary budget planning, most likely outcome
       - Example: Current market conditions continue

    3. Optimistic: Expansion scenario (6-8% enrollment growth)
       - Use for: Growth planning, investment justification
       - Example: New campus, increased demand

    4. New Campus: Major capital investment scenario
       - Use for: Facility expansion planning
       - Example: Second campus opens in Year 4

    Growth Assumptions:
    -------------------
    Each scenario defines annual growth rates for key drivers:
    - Enrollment Growth: -50% to +100% (typically 0-8%)
    - Fee Increase Rate: -20% to +50% (typically 2-6%)
    - Salary Inflation: -20% to +50% (typically 2-5%)
    - Operating Inflation: -20% to +50% (typically 2-4%)

    Example:
    --------
    Plan: "EFIR Strategic Plan 2025-2030"
    Scenario: BASE_CASE
    Enrollment Growth: 4.0% per year (1,234 → 1,502 students over 5 years)
    Fee Increase: 3.0% per year (maintaining purchasing power)
    Salary Inflation: 3.5% per year (AEFE + local market)
    Operating Inflation: 2.5% per year (CPI-based)
    """

    __tablename__ = "strategic_plan_scenarios"
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
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Foreign Keys
    strategic_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.strategic_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Strategic plan this scenario belongs to",
    )

    # Scenario Identification
    scenario_type: Mapped[ScenarioType] = mapped_column(
        Enum(ScenarioType, schema="efir_budget"),
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

    # Growth Assumptions (Annual Rates as Decimals)
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

    # Additional Assumptions (JSONB for flexibility)
    additional_assumptions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional scenario-specific assumptions (exchange rates, capacity, etc.)",
    )

    # Relationships
    strategic_plan: Mapped["StrategicPlan"] = relationship(
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


class StrategicPlanProjection(BaseModel):
    """
    Multi-year financial projections by category and year.

    Stores projected financial amounts for each year (1-5) of the strategic plan,
    broken down by category (revenue, costs, capex). Projections are calculated
    based on the scenario's growth assumptions and stored for reporting and
    scenario comparison.

    Projection Categories:
    ----------------------
    1. REVENUE: Total operating revenue (tuition + fees + ancillary)
    2. PERSONNEL_COSTS: All personnel expenses (teaching + admin + support)
    3. OPERATING_COSTS: Operating expenses excluding personnel
    4. CAPEX: Capital expenditures (equipment, facilities, IT)
    5. DEPRECIATION: Depreciation expense

    Calculation Method:
    -------------------
    Year 1: Base year actual/budget amounts
    Year 2: Year 1 × (1 + growth_rate)
    Year 3: Year 2 × (1 + growth_rate)
    ... and so on

    Example:
    --------
    Scenario: BASE_CASE (4% enrollment growth, 3% fee increase)
    Year 1 (2025): Revenue = 55,515,000 SAR (current budget)
    Year 2 (2026): Revenue = 55,515,000 × 1.04 × 1.03 = 59,462,000 SAR
    Year 3 (2027): Revenue = 59,462,000 × 1.04 × 1.03 = 63,657,000 SAR
    Year 4 (2028): Revenue = 63,657,000 × 1.04 × 1.03 = 68,116,000 SAR
    Year 5 (2029): Revenue = 68,116,000 × 1.04 × 1.03 = 72,858,000 SAR

    Financial Summary for BASE_CASE over 5 years:
    -----------------------------------------------
    Total Revenue: 319.6M SAR (compound annual growth: 7.0%)
    Total Costs: 287.6M SAR (personnel + operating)
    Total CapEx: 12.5M SAR (equipment + facilities)
    Net Result: 32.0M SAR surplus (10% margin maintained)
    """

    __tablename__ = "strategic_plan_projections"
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
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Foreign Keys
    strategic_plan_scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.strategic_plan_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Scenario this projection belongs to",
    )

    # Projection Period
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Year in strategic plan (1-5, where 1 = base_year)",
    )

    # Category
    category: Mapped[ProjectionCategory] = mapped_column(
        Enum(ProjectionCategory, schema="efir_budget"),
        nullable=False,
        index=True,
        comment="Projection category (revenue, personnel_costs, operating_costs, capex, depreciation)",
    )

    # Projected Amount
    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Projected amount in SAR for this year and category",
    )

    # Calculation Metadata (JSONB for transparency)
    calculation_inputs: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Inputs used in projection calculation (base amount, growth rates, enrollment, etc.)",
    )

    # Relationships
    scenario: Mapped["StrategicPlanScenario"] = relationship(
        "StrategicPlanScenario",
        back_populates="projections",
        lazy="selectin",
    )


class StrategicInitiative(BaseModel):
    """
    Strategic initiative or major project within the 5-year plan.

    Tracks major capital investments, facility expansions, program launches,
    and other strategic projects planned over the 5-year horizon. Each initiative
    has a planned year, capital expenditure requirement, and ongoing operating
    cost impact.

    Initiative Types:
    -----------------
    - Facility Expansion: New campus, building renovation
    - Technology Investment: ERP system, learning platforms
    - Program Launch: New curriculum, IB program, extracurricular
    - Capacity Increase: Additional classrooms, laboratories
    - Infrastructure: HVAC upgrade, solar panels, security systems

    Example Initiatives:
    --------------------
    1. New Science Laboratory (Year 2)
       - CapEx: 2,500,000 SAR (construction, equipment)
       - Operating Impact: +150,000 SAR/year (maintenance, supplies)
       - Status: approved

    2. ERP System Implementation (Year 1)
       - CapEx: 800,000 SAR (software licenses, implementation)
       - Operating Impact: +200,000 SAR/year (subscriptions, support)
       - Status: in_progress

    3. Secondary Campus Expansion (Year 4)
       - CapEx: 15,000,000 SAR (land, construction, equipment)
       - Operating Impact: +3,500,000 SAR/year (personnel, operations)
       - Status: planned

    Impact on Strategic Projections:
    ---------------------------------
    CapEx amounts are added to the capex projection category in the
    planned year. Operating impacts are added to operating_costs
    projections from the planned year onwards (recurring).

    Example:
    --------
    Initiative: "New Science Lab"
    Planned Year: 2 (2026)
    CapEx: 2,500,000 SAR (one-time in Year 2)
    Operating Impact: 150,000 SAR (recurring from Year 2 onwards)

    Projection Impact:
    Year 1: No impact
    Year 2: +2,500,000 SAR capex, +150,000 SAR operating
    Year 3: +150,000 SAR operating (recurring)
    Year 4: +150,000 SAR operating (recurring)
    Year 5: +150,000 SAR operating (recurring)
    """

    __tablename__ = "strategic_initiatives"
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
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Foreign Keys
    strategic_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.strategic_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Strategic plan this initiative belongs to",
    )

    # Initiative Identification
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

    # Timeline
    planned_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Year in strategic plan when initiative is planned (1-5)",
    )

    # Financial Impact
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

    # Status Tracking
    status: Mapped[InitiativeStatus] = mapped_column(
        Enum(InitiativeStatus, schema="efir_budget"),
        nullable=False,
        default=InitiativeStatus.PLANNED,
        index=True,
        comment="Initiative status (planned, approved, in_progress, completed, cancelled)",
    )

    # Additional Details (JSONB for flexibility)
    additional_details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional initiative details (milestones, dependencies, risks, etc.)",
    )

    # Relationships
    strategic_plan: Mapped["StrategicPlan"] = relationship(
        "StrategicPlan",
        back_populates="initiatives",
        lazy="selectin",
    )
