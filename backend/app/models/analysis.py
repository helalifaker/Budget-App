"""
EFIR Budget Planning Application - Analysis Layer Models

This module contains SQLAlchemy models for Modules 15-17:
- Module 15: Statistical Analysis (kpi_definitions, kpi_values)
- Module 16: Dashboard Configuration (dashboard_configs, dashboard_widgets, user_preferences)
- Module 17: Budget vs Actual Analysis (actual_data, budget_vs_actual, variance_explanations)

Author: Claude Code
Date: 2025-12-01
Version: 4.0.0
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, VersionedMixin

if TYPE_CHECKING:
    from app.models.configuration import BudgetVersion


# ============================================================================
# Module 15: Statistical Analysis - Enums
# ============================================================================


class KPICategory(str, enum.Enum):
    """KPI category for grouping and filtering."""

    EDUCATIONAL = "educational"  # Student/teacher ratios, class sizes
    FINANCIAL = "financial"  # Revenue, cost, margin ratios
    OPERATIONAL = "operational"  # Enrollment, capacity, utilization
    STRATEGIC = "strategic"  # Long-term trends, benchmarks


# ============================================================================
# Module 16: Dashboard Configuration - Enums
# ============================================================================


class WidgetType(str, enum.Enum):
    """Dashboard widget type."""

    KPI_CARD = "kpi_card"  # Single metric with target and variance
    CHART = "chart"  # Line, bar, area, pie charts
    TABLE = "table"  # Data grid
    VARIANCE_TABLE = "variance_table"  # Budget vs actual with variance
    WATERFALL = "waterfall"  # Revenue/cost waterfall chart
    GAUGE = "gauge"  # KPI gauge with threshold zones
    TIMELINE = "timeline"  # Approval workflow timeline
    HEATMAP = "heatmap"  # Cost center performance heatmap


class DashboardRole(str, enum.Enum):
    """Dashboard role for pre-defined templates."""

    EXECUTIVE = "executive"  # Board, Director
    FINANCE_MANAGER = "finance_manager"  # DAF/CFO
    DEPARTMENT = "department"  # Cost center heads
    OPERATIONS = "operations"  # School Director


# ============================================================================
# Module 17: Budget vs Actual Analysis - Enums
# ============================================================================


class VarianceStatus(str, enum.Enum):
    """Variance favorability status."""

    FAVORABLE = "favorable"  # Under budget (expense) or over budget (revenue)
    UNFAVORABLE = "unfavorable"  # Over budget (expense) or under budget (revenue)
    NEUTRAL = "neutral"  # Within acceptable tolerance (±5%)
    NOT_APPLICABLE = "not_applicable"  # No comparison available


class ActualDataSource(str, enum.Enum):
    """Source of actual financial data."""

    ODOO_IMPORT = "odoo_import"  # Imported from Odoo GL
    MANUAL_ENTRY = "manual_entry"  # Manually entered
    SYSTEM_CALC = "system_calc"  # System-calculated (aggregations)


# ============================================================================
# Module 15: Statistical Analysis - Models
# ============================================================================


class KPIDefinition(BaseModel):
    """
    KPI metadata catalog with formulas and targets.

    Defines all KPIs calculated for budget analysis, including formulas,
    targets, and benchmarks. Acts as configuration for KPI calculations.

    Standard KPIs:
    --------------
    Educational:
    - H/E Ratio: (Teaching FTE × 18h × 52 weeks) ÷ Total Students
    - E/D Ratio: Total Students ÷ Total Classes
    - Student/Teacher Ratio: Total Students ÷ Teaching FTE
    - Average Class Size: Total Students ÷ Total Classes

    Financial:
    - Staff Cost %: (Personnel Costs ÷ Revenue) × 100
    - Operating Margin: ((Revenue - Costs) ÷ Revenue) × 100
    - Revenue per Student: Total Revenue ÷ Total Students
    - Cost per Student: Total Costs ÷ Total Students
    - Rent Ratio: (Rent Costs ÷ Revenue) × 100
    - Teaching Staff %: (Teaching Costs ÷ Total Personnel Costs) × 100

    EFIR 2024 Benchmarks:
    ---------------------
    - Staff Cost Ratio: 52.6% (AEFE benchmark: 60-75%)
    - Operating Margin: 9.6% (AEFE benchmark: 5-10%)
    - Student/Teacher: 7.6 (AEFE benchmark: 8-12)
    - Average Class Size: 21-25 (AEFE benchmark: 20-26)

    Example:
    --------
    KPI: Staff Cost Ratio
    Code: STAFF_COST_PCT
    Formula: (Total Personnel Costs ÷ Total Revenue) × 100
    Target: 60% (AEFE benchmark)
    Unit: percentage
    """

    __tablename__ = "kpi_definitions"
    __table_args__ = (
        UniqueConstraint("code", name="uk_kpi_definition_code"),
        CheckConstraint("target_value >= 0", name="ck_kpi_target_positive"),
        {"schema": "efir_budget", "comment": __doc__},
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
        Enum(KPICategory, schema="efir_budget"),
        nullable=False,
        index=True,
        comment="KPI category for grouping",
    )

    # Formula & Calculation
    formula_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable formula (e.g., '(Personnel Costs ÷ Revenue) × 100')",
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
        """String representation."""
        return f"<KPIDefinition(code={self.code}, category={self.category.value})>"


class KPIValue(BaseModel, VersionedMixin):
    """
    KPI calculated values per budget version.

    Pre-calculated when budget version status changes to 'approved'.
    Stores calculation inputs for audit trail and recalculation.

    Calculation Timing:
    -------------------
    KPIs are calculated automatically when:
    1. Budget version status changes to 'approved'
    2. User manually triggers recalculation
    3. Consolidation data is updated

    Example KPI Calculations:
    -------------------------
    H/E Ratio (EFIR 2025-2026):
        Teaching FTE: 95.5
        Standard Hours: 18 hours/week
        Weeks per Year: 52
        Total Students: 1,250
        H/E = (95.5 × 18 × 52) ÷ 1,250 = 71.59 hours/student

    Staff Cost Ratio:
        Personnel Costs: 28,500,000 SAR
        Total Revenue: 54,200,000 SAR
        Ratio = (28,500,000 ÷ 54,200,000) × 100 = 52.6%
        Variance from Target (60%): -7.4% (favorable)

    Revenue per Student:
        Total Revenue: 54,200,000 SAR
        Total Students: 1,250
        Revenue/Student = 54,200,000 ÷ 1,250 = 43,360 SAR

    Audit Trail:
    ------------
    calculation_inputs stores:
    {
        "total_students": 1250,
        "teaching_fte": 95.5,
        "personnel_costs_sar": 28500000,
        "total_revenue_sar": 54200000,
        "calculation_date": "2025-12-01T10:30:00Z"
    }
    """

    __tablename__ = "kpi_values"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "kpi_definition_id",
            name="uk_kpi_value_version_definition",
        ),
        CheckConstraint(
            "calculated_value IS NOT NULL",
            name="ck_kpi_value_calculated_not_null",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Note: budget_version_id is inherited from VersionedMixin

    # Foreign Keys
    kpi_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.kpi_definitions.id"),
        nullable=False,
        index=True,
        comment="KPI being calculated",
    )

    # Calculated Values
    calculated_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Calculated KPI value",
    )
    variance_from_target: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Variance from target (calculated - target)",
    )
    variance_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Variance as percentage ((variance ÷ target) × 100)",
    )

    # Audit Trail
    calculation_inputs: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Inputs used for calculation (for audit and recalc)",
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When KPI was calculated",
    )

    # Optional Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes or interpretation",
    )

    # Relationships
    kpi_definition: Mapped[KPIDefinition] = relationship(
        "KPIDefinition",
        lazy="selectin",
    )
    budget_version: Mapped[BudgetVersion] = relationship(
        "BudgetVersion",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<KPIValue(kpi={self.kpi_definition_id}, "
            f"value={self.calculated_value:.4f})>"
        )


# ============================================================================
# Module 16: Dashboard Configuration - Models
# ============================================================================


class DashboardConfig(BaseModel):
    """
    Dashboard definitions (system templates + user custom dashboards).

    Supports both pre-defined role-based dashboards and user-customizable
    personal dashboards.

    Dashboard Types:
    ----------------
    1. System Templates (is_system_template=True, owner_user_id=NULL):
       - Executive Dashboard (Board, Director)
       - Finance Manager Dashboard (DAF/CFO)
       - Department Dashboard (Cost center heads)
       - Operations Dashboard (School Director)

    2. User Custom Dashboards (is_system_template=False, owner_user_id set):
       - Personal dashboards created by users
       - Can be made public for sharing
       - Can override system defaults

    Layout System:
    --------------
    12×12 responsive grid layout:
    - Grid columns: 12
    - Widget positions: (position_x, position_y)
    - Widget sizes: width (1-12), height (1-10)
    - Gap size: 16px default

    Example Layout Config:
    ----------------------
    {
        "grid_columns": 12,
        "gap_size": 16,
        "auto_refresh_enabled": true,
        "refresh_interval_seconds": 300
    }

    Executive Dashboard Example:
    ----------------------------
    - Net Income card (2×1, position 0,0)
    - Revenue vs Budget chart (6×3, position 2,0)
    - Key KPI cards (2×1 each, position 8,0-2)
    - Enrollment trend (6×3, position 0,1)
    - Budget variance table (6×3, position 6,1)
    - Alert panel (12×2, position 0,4)
    """

    __tablename__ = "dashboard_configs"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id",
            "name",
            name="uk_dashboard_owner_name",
        ),
        UniqueConstraint(
            "dashboard_role",
            name="uk_dashboard_role_template",
        ),
        CheckConstraint(
            "((is_system_template = true) AND dashboard_role IS NOT NULL AND owner_user_id IS NULL) "
            "OR ((is_system_template = false) AND dashboard_role IS NULL AND owner_user_id IS NOT NULL)",
            name="ck_dashboard_system_or_user",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Dashboard Identification
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Dashboard name",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Dashboard purpose and contents",
    )

    # Classification
    dashboard_role: Mapped[DashboardRole | None] = mapped_column(
        Enum(DashboardRole, schema="efir_budget"),
        nullable=True,
        index=True,
        comment="Role for system templates (NULL for user custom)",
    )
    is_system_template: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True for pre-defined templates, False for user custom",
    )

    # Ownership
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Owner user (NULL for system templates)",
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether dashboard is visible to other users",
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Default dashboard for role or user",
    )

    # Layout Configuration
    layout_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Grid layout configuration (12×12 grid, gap size, etc.)",
    )

    # Relationships
    widgets: Mapped[list[DashboardWidget]] = relationship(
        "DashboardWidget",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DashboardWidget.sort_order",
    )

    def __repr__(self) -> str:
        """String representation."""
        owner = f"user={self.owner_user_id}" if self.owner_user_id else "system"
        return f"<DashboardConfig(name='{self.name}', {owner})>"


class DashboardWidget(BaseModel):
    """
    Widget definitions within dashboards.

    Widgets are the building blocks of dashboards - individual components
    displaying specific data (KPIs, charts, tables, etc.).

    Widget Types:
    -------------
    1. KPI Card: Single metric with target, variance, trend
    2. Chart: Line, bar, area, pie charts (Recharts)
    3. Table: Data grid (AG Grid)
    4. Variance Table: Budget vs actual with variance highlighting
    5. Waterfall: Revenue/cost waterfall chart
    6. Gauge: KPI gauge with threshold zones (red/yellow/green)
    7. Timeline: Approval workflow timeline
    8. Heatmap: Cost center performance heatmap

    Widget Configuration Examples:
    -------------------------------
    KPI Card Config:
    {
        "kpi_code": "STAFF_COST_PCT",
        "show_target": true,
        "show_trend": true,
        "show_variance": true,
        "threshold_zones": {
            "critical": [75, 100],
            "warning": [60, 75],
            "good": [0, 60]
        }
    }

    Chart Config:
    {
        "chart_type": "line",
        "data_source": "enrollment_trend",
        "period_months": 12,
        "show_legend": true,
        "enable_zoom": true
    }

    Variance Table Config:
    {
        "account_level": "summary",
        "period_type": "month",
        "show_variance_pct": true,
        "highlight_threshold": 5.0
    }

    Grid Positioning:
    -----------------
    - position_x: 0-11 (12 columns)
    - position_y: 0+ (unlimited rows)
    - width: 1-12 (span columns)
    - height: 1-10 (span rows)

    Example: Executive Dashboard KPI Card
    - Position: (0, 0)
    - Size: 2×1 (2 columns × 1 row)
    - Type: kpi_card
    - Refresh: 300 seconds (5 minutes)
    """

    __tablename__ = "dashboard_widgets"
    __table_args__ = (
        CheckConstraint(
            "position_x >= 0 AND position_x < 12",
            name="ck_widget_position_x",
        ),
        CheckConstraint(
            "position_y >= 0",
            name="ck_widget_position_y",
        ),
        CheckConstraint(
            "width > 0 AND width <= 12",
            name="ck_widget_width",
        ),
        CheckConstraint(
            "height > 0 AND height <= 10",
            name="ck_widget_height",
        ),
        CheckConstraint(
            "position_x + width <= 12",
            name="ck_widget_position_within_grid",
        ),
        CheckConstraint(
            "refresh_interval_seconds >= 0",
            name="ck_widget_refresh_positive",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Foreign Keys
    dashboard_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.dashboard_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent dashboard",
    )

    # Widget Configuration
    widget_type: Mapped[WidgetType] = mapped_column(
        Enum(WidgetType, schema="efir_budget"),
        nullable=False,
        index=True,
        comment="Type of widget",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Widget title displayed to user",
    )

    # Data Source
    data_source_query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Query identifier or API endpoint for data",
    )
    widget_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Widget-specific configuration (type-dependent)",
    )

    # Grid Layout
    position_x: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Grid position X (0-11, left to right)",
    )
    position_y: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Grid position Y (0+, top to bottom)",
    )
    width: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Widget width in grid columns (1-12)",
    )
    height: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Widget height in grid rows (1-10)",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order within dashboard",
    )

    # Refresh Settings
    refresh_interval_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Auto-refresh interval in seconds (NULL = no auto-refresh)",
    )

    # Relationships
    dashboard_config: Mapped[DashboardConfig] = relationship(
        "DashboardConfig",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DashboardWidget(type={self.widget_type.value}, "
            f"title='{self.title}', pos=({self.position_x},{self.position_y}), "
            f"size={self.width}×{self.height})>"
        )


class UserPreferences(BaseModel):
    """
    User-specific preferences and settings.

    Stores personalized settings for each user including default dashboard,
    theme, display preferences, and notification settings.

    Preference Categories:
    ----------------------
    1. Default Views:
       - Default dashboard
       - Default fiscal year
       - Default budget version

    2. Display Preferences:
       - Theme (light/dark/auto)
       - Number format (French vs International)
       - Language (French/English)
       - Timezone

    3. Notification Settings:
       - Email alerts for budget approvals
       - Dashboard refresh notifications
       - Variance threshold alerts
       - Weekly summary reports

    Example Notification Settings:
    -------------------------------
    {
        "email_alerts": {
            "budget_approval": true,
            "variance_threshold": true,
            "threshold_pct": 10.0
        },
        "dashboard_notifications": false,
        "weekly_summary": true,
        "summary_day": "monday"
    }

    Example Display Preferences:
    -----------------------------
    {
        "number_format": "french",  // 1 234,56
        "language": "fr",
        "timezone": "Europe/Paris",
        "date_format": "DD/MM/YYYY",
        "currency_symbol": "SAR"
    }
    """

    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uk_user_preferences_user_id"),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="User these preferences belong to",
    )
    default_dashboard_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.dashboard_configs.id", ondelete="SET NULL"),
        nullable=True,
        comment="User's default dashboard (overrides role default)",
    )

    # Display Preferences
    theme: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="light",
        comment="UI theme (light, dark, auto)",
    )
    default_fiscal_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="User's default fiscal year filter",
    )
    display_preferences: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Number format, language, timezone, date format",
    )

    # Notification Settings
    notification_settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Email alerts, dashboard notifications, weekly summary",
    )

    # Relationships
    default_dashboard: Mapped[DashboardConfig | None] = relationship(
        "DashboardConfig",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserPreferences(user_id={self.user_id}, theme={self.theme})>"


# ============================================================================
# Module 17: Budget vs Actual Analysis - Models
# ============================================================================


class ActualData(BaseModel):
    """
    Actual financial data imported from Odoo GL.

    Stores actual transactions from Odoo accounting system for variance
    analysis and budget vs actual reporting.

    Import Process:
    ---------------
    1. Nightly batch import from Odoo GL
    2. ETL transformation to match PCG account codes
    3. Validation and reconciliation
    4. Import batch tracking for audit

    Data Structure:
    ---------------
    Each record represents a transaction or aggregated monthly total:
    - Fiscal year and period (month 1-12)
    - French PCG account code
    - Amount in SAR (or original currency with conversion)
    - Transaction date and description
    - Import batch ID for traceability

    Example Import Batch (October 2025):
    -------------------------------------
    Batch ID: 550e8400-e29b-41d4-a716-446655440000
    Import Date: 2025-11-01 02:00:00
    Source: Odoo GL Export
    Records: 1,250 transactions

    Account 64110 (Teaching Salaries):
        Fiscal Year: 2025
        Period: 10 (October)
        Amount: 2,375,000 SAR
        Currency: SAR
        Source: odoo_import
        Reconciled: True

    Account 70110 (Tuition T1):
        Fiscal Year: 2025
        Period: 10
        Amount: 15,226,000 SAR
        Currency: SAR
        Source: odoo_import
        Reconciled: True

    Reconciliation:
    ---------------
    is_reconciled flag indicates whether the actual data has been
    matched/validated against source documents and budget accounts.
    """

    __tablename__ = "actual_data"
    __table_args__ = (
        CheckConstraint(
            "period >= 0 AND period <= 12",
            name="ck_actual_period_range",
        ),
        CheckConstraint(
            "fiscal_year >= 2020 AND fiscal_year <= 2099",
            name="ck_actual_fiscal_year_range",
        ),
        CheckConstraint(
            "amount_sar IS NOT NULL",
            name="ck_actual_amount_not_null",
        ),
        Index(
            "ix_actual_data_fy_period_account",
            "fiscal_year",
            "period",
            "account_code",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Period Information
    fiscal_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Fiscal year (e.g., 2025 for FY 2025-2026)",
    )
    period: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Month (0-12, 0 = annual total)",
    )

    # Account Information
    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="French PCG account code",
    )
    account_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Account name from Odoo",
    )

    # Amounts
    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Actual amount in SAR",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="SAR",
        comment="Original currency code (SAR, EUR, etc.)",
    )

    # Import Metadata
    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Batch import identifier for traceability",
    )
    import_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When data was imported from Odoo",
    )
    source: Mapped[ActualDataSource] = mapped_column(
        Enum(ActualDataSource, schema="efir_budget"),
        nullable=False,
        default=ActualDataSource.ODOO_IMPORT,
        index=True,
        comment="Source of actual data",
    )

    # Transaction Details
    transaction_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Original transaction date (if single transaction)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Transaction description from Odoo",
    )

    # Reconciliation
    is_reconciled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether actual data has been validated/reconciled",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ActualData(FY{self.fiscal_year}-P{self.period}, "
            f"account={self.account_code}, "
            f"amount={self.amount_sar:,.2f} SAR)>"
        )


class BudgetVsActual(BaseModel, VersionedMixin):
    """
    Variance analysis comparing budget to actual.

    Calculates and stores variance between budgeted amounts and actual
    results from Odoo GL, with favorability assessment.

    Variance Formulas:
    ------------------
    For Expenses (60xxx-68xxx):
        Variance = Budget - Actual
        Favorable if Variance > 0 (under budget)
        Unfavorable if Variance < 0 (over budget)

    For Revenue (70xxx-77xxx):
        Variance = Actual - Budget
        Favorable if Variance > 0 (over budget)
        Unfavorable if Variance < 0 (under budget)

    Variance %:
        Variance % = (Variance ÷ Budget) × 100

    Materiality Threshold:
        Material if |Variance %| > 5% OR |Variance| > 100,000 SAR

    Example Variance Analysis (October 2025):
    ------------------------------------------
    Account 64110 (Teaching Salaries):
        Budget: 2,400,000 SAR
        Actual: 2,375,000 SAR
        Variance: 25,000 SAR (budget - actual)
        Variance %: 1.04% ((25,000 ÷ 2,400,000) × 100)
        Status: FAVORABLE (under budget)
        Is Material: No (< 5%)

    Account 70110 (Tuition T1):
        Budget: 15,000,000 SAR
        Actual: 15,226,000 SAR
        Variance: 226,000 SAR (actual - budget, for revenue)
        Variance %: 1.51% ((226,000 ÷ 15,000,000) × 100)
        Status: FAVORABLE (over budget)
        Is Material: Yes (> 100,000 SAR)

    YTD Calculations:
    -----------------
    Year-to-date (YTD) amounts track cumulative performance:
        YTD Budget = SUM(budget) for periods 1 to current period
        YTD Actual = SUM(actual) for periods 1 to current period
        YTD Variance = YTD Actual - YTD Budget (for revenue)
                    or YTD Budget - YTD Actual (for expenses)

    Example YTD (January-October 2025):
        YTD Budget: 24,000,000 SAR (10 months × 2,400,000)
        YTD Actual: 23,750,000 SAR
        YTD Variance: 250,000 SAR (favorable for expenses)
        YTD Variance %: 1.04%
    """

    __tablename__ = "budget_vs_actual"
    __table_args__ = (
        UniqueConstraint(
            "budget_version_id",
            "account_code",
            "period",
            name="uk_variance_version_account_period",
        ),
        CheckConstraint(
            "period >= 1 AND period <= 12",
            name="ck_variance_period_range",
        ),
        CheckConstraint(
            "budget_amount_sar IS NOT NULL AND actual_amount_sar IS NOT NULL",
            name="ck_variance_amounts_not_null",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Note: budget_version_id is inherited from VersionedMixin

    # Period & Account
    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="French PCG account code",
    )
    period: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Month (1-12)",
    )

    # Amounts (Monthly)
    budget_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Budgeted amount from budget_consolidations",
    )
    actual_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Actual amount from actual_data (Odoo)",
    )
    variance_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Variance (budget - actual for expenses; actual - budget for revenue)",
    )
    variance_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        comment="Variance as percentage ((variance ÷ budget) × 100)",
    )
    variance_status: Mapped[VarianceStatus] = mapped_column(
        Enum(VarianceStatus, schema="efir_budget"),
        nullable=False,
        index=True,
        comment="Favorability status",
    )

    # YTD Amounts
    ytd_budget_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Year-to-date budget (cumulative from period 1)",
    )
    ytd_actual_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Year-to-date actual (cumulative from period 1)",
    )
    ytd_variance_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Year-to-date variance",
    )

    # Materiality
    is_material: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Variance exceeds materiality threshold (5% or 100K SAR)",
    )

    # Relationships
    budget_version: Mapped[BudgetVersion] = relationship(
        "BudgetVersion",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<BudgetVsActual(account={self.account_code}, period={self.period}, "
            f"variance={self.variance_sar:,.2f} SAR, status={self.variance_status.value})>"
        )


class VarianceExplanation(BaseModel):
    """
    User-provided explanations for variances.

    Captures business context and corrective actions for significant
    budget vs actual variances, supporting accountability and planning.

    Explanation Categories:
    -----------------------
    Root Causes:
    - enrollment_variance: Student numbers differ from projection
    - price_variance: Costs or fees changed from budget
    - timing_variance: Transaction timing difference (accrual mismatch)
    - procedural_change: Process or policy change
    - external_factor: External event (regulatory, economic, etc.)
    - other: Other reason (specify in text)

    Example Explanation:
    --------------------
    Variance: Teaching Salaries over budget by 125,000 SAR (5.2%)

    Explanation:
    "Hired 2 additional teachers mid-semester due to higher than
    expected 6ème enrollment (projected 120, actual 135 students).
    Also, one teacher on medical leave required replacement at
    higher hourly rate."

    Root Cause: enrollment_variance
    Corrective Action: "Adjust Q2 budget forecast to reflect new
    staffing levels. Review enrollment projection methodology for
    next fiscal year planning."
    Deadline: 2025-12-15
    Status: Resolved

    Workflow:
    ---------
    1. System flags material variances (> 5% or > 100K SAR)
    2. Manager provides explanation and corrective action
    3. Finance team reviews and approves
    4. Actions tracked to completion
    5. Insights feed into next year's planning
    """

    __tablename__ = "variance_explanations"
    __table_args__ = (
        CheckConstraint(
            "explanation_text IS NOT NULL AND length(explanation_text) > 10",
            name="ck_explanation_text_required",
        ),
        {"schema": "efir_budget", "comment": __doc__},
    )

    # Foreign Keys
    budget_vs_actual_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.budget_vs_actual.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Variance being explained",
    )

    # Explanation
    explanation_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed explanation of variance (minimum 10 characters)",
    )
    root_cause: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Root cause category (enrollment_variance, price_variance, etc.)",
    )

    # Corrective Action
    corrective_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Planned corrective action to address variance",
    )
    action_deadline: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Deadline for completing corrective action",
    )
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether variance issue has been resolved",
    )

    # Relationships
    variance: Mapped[BudgetVsActual] = relationship(
        "BudgetVsActual",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        status = "resolved" if self.is_resolved else "pending"
        return (
            f"<VarianceExplanation(variance_id={self.budget_vs_actual_id}, "
            f"cause={self.root_cause}, status={status})>"
        )


# ============================================================================
# End of Analysis Layer Models
# ============================================================================
