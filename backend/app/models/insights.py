"""
EFIR Budget Planning Application - Insights Module Models.

This module contains all insights_* prefixed tables for analytics,
dashboards, and variance analysis.

Table Categories:
-----------------
1. KPI & Analytics:
   - insights_kpi_values: Calculated KPI values per budget version

2. Dashboard Configuration:
   - insights_dashboard_configs: Dashboard definitions (system + user)
   - insights_dashboard_widgets: Widget configurations within dashboards
   - insights_user_preferences: User-specific settings and preferences

3. Budget vs Actual Analysis:
   - insights_actual_data: Actual financial data from Odoo GL
   - insights_budget_vs_actual: Variance analysis (budget vs actual)
   - insights_variance_explanations: User explanations for variances

4. Historical Comparison:
   - insights_historical_actuals: Historical data for N-2, N-1 comparison

Note: KPIDefinition (ref_kpi_definitions) is in the reference.py module
since it's reference data, not calculated insights.

Module Architecture:
--------------------
This module supports the Insights EFIR module:
- Module: Insights
- Route: /insights/*
- Color: slate
- Primary Role: All users (read access)
- Purpose: KPIs, variance, trends, reports

Data Flow:
----------
Budget Consolidation → KPI Values → Dashboard Widgets
Actual Data (Odoo) → Budget vs Actual → Variance Explanations
Historical Actuals → Planning Comparison

KPI Categories:
---------------
- EDUCATIONAL: Student/teacher ratios, class sizes (H/E, E/D)
- FINANCIAL: Revenue, cost, margin ratios
- OPERATIONAL: Enrollment, capacity, utilization
- STRATEGIC: Long-term trends, benchmarks

Dashboard Role Templates:
-------------------------
- EXECUTIVE: Board, Director (high-level KPIs)
- FINANCE_MANAGER: DAF/CFO (detailed financial analysis)
- DEPARTMENT: Cost center heads (department-specific)
- OPERATIONS: School Director (operational metrics)

Author: Claude Code
Date: 2025-12-16
Version: 1.0.0
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    BaseModel,
    PortableJSON,
    VersionedMixin,
    get_fk_target,
    get_schema,
)

if TYPE_CHECKING:
    from app.models.reference import KPIDefinition

# ==============================================================================
# Enums - Dashboard Configuration
# ==============================================================================


class WidgetType(str, PyEnum):
    """
    Dashboard widget type.

    Types:
    ------
    KPI_CARD: Single metric with target and variance
        - Shows KPI value, target, variance %, trend indicator
        - Threshold zones (red/yellow/green)

    CHART: Line, bar, area, pie charts (Recharts)
        - Time series, comparisons, distributions
        - Interactive with zoom and legend

    TABLE: Data grid (AG Grid)
        - Sortable, filterable data tables
        - Export capability

    VARIANCE_TABLE: Budget vs actual with variance
        - Account-level or summary view
        - Color-coded variance highlighting

    WATERFALL: Revenue/cost waterfall chart
        - Shows progression from revenue to net result
        - Identifies major contributors

    GAUGE: KPI gauge with threshold zones
        - Circular gauge visualization
        - Red/yellow/green zones

    TIMELINE: Approval workflow timeline
        - Budget version status history
        - Approval stages

    HEATMAP: Cost center performance heatmap
        - Multi-dimensional analysis
        - Color intensity by variance
    """

    KPI_CARD = "kpi_card"
    CHART = "chart"
    TABLE = "table"
    VARIANCE_TABLE = "variance_table"
    WATERFALL = "waterfall"
    GAUGE = "gauge"
    TIMELINE = "timeline"
    HEATMAP = "heatmap"


class DashboardRole(str, PyEnum):
    """
    Dashboard role for pre-defined templates.

    Roles:
    ------
    EXECUTIVE: Board members, School Director
        - High-level KPIs: net income, operating margin, enrollment
        - Trend charts: year-over-year comparison
        - Key alerts and notifications

    FINANCE_MANAGER: DAF/CFO
        - Detailed financial analysis
        - Budget vs actual by account
        - Cash flow projections
        - Variance explanations

    DEPARTMENT: Cost center heads (Proviseur, etc.)
        - Department-specific budgets
        - Personnel costs by category
        - Operating expenses

    OPERATIONS: School Director
        - Enrollment metrics by level
        - Class structure and capacity
        - Teacher allocation (DHG)
        - Facility utilization
    """

    EXECUTIVE = "executive"
    FINANCE_MANAGER = "finance_manager"
    DEPARTMENT = "department"
    OPERATIONS = "operations"


# ==============================================================================
# Enums - Budget vs Actual Analysis
# ==============================================================================


class VarianceStatus(str, PyEnum):
    """
    Variance favorability status.

    Status Logic:
    -------------
    For Expenses (60xxx-68xxx):
        FAVORABLE: Under budget (actual < budget)
        UNFAVORABLE: Over budget (actual > budget)

    For Revenue (70xxx-77xxx):
        FAVORABLE: Over budget (actual > budget)
        UNFAVORABLE: Under budget (actual < budget)

    NEUTRAL: Within acceptable tolerance (±5%)
    NOT_APPLICABLE: No comparison available (new account, etc.)
    """

    FAVORABLE = "favorable"
    UNFAVORABLE = "unfavorable"
    NEUTRAL = "neutral"
    NOT_APPLICABLE = "not_applicable"


class ActualDataSource(str, PyEnum):
    """
    Source of actual financial data.

    Sources:
    --------
    ODOO_IMPORT: Imported from Odoo General Ledger
        - Nightly batch import
        - ETL transformation to PCG codes

    MANUAL_ENTRY: Manually entered by user
        - For adjustments or corrections
        - Requires approval workflow

    SYSTEM_CALC: System-calculated aggregations
        - Monthly totals from transactions
        - YTD calculations
    """

    ODOO_IMPORT = "odoo_import"
    MANUAL_ENTRY = "manual_entry"
    SYSTEM_CALC = "system_calc"


# ==============================================================================
# Enums - Historical Comparison
# ==============================================================================


class HistoricalModuleCode(str, PyEnum):
    """
    Module code for historical data categorization.

    Modules:
    --------
    ENROLLMENT: Student counts by level
        - Dimension: level
        - Value: annual_count

    CLASS_STRUCTURE: Class counts by level
        - Dimension: level
        - Value: annual_classes

    DHG: Teacher FTE/hours by subject
        - Dimension: subject, teacher_category
        - Values: annual_fte, annual_hours

    REVENUE: Revenue by account code
        - Dimension: account_code, fee_type
        - Value: annual_amount_sar

    COSTS: Costs by account code and category
        - Dimension: account_code, cost_category
        - Value: annual_amount_sar

    CAPEX: Capital expenditures by category
        - Dimension: account_code
        - Value: annual_amount_sar
    """

    ENROLLMENT = "enrollment"
    CLASS_STRUCTURE = "class_structure"
    DHG = "dhg"
    REVENUE = "revenue"
    COSTS = "costs"
    CAPEX = "capex"


class HistoricalDimensionType(str, PyEnum):
    """
    Dimension type for historical data grouping.

    Types:
    ------
    LEVEL: Academic level (for enrollment)
        - dimension_code: '6EME', 'CP', 'PS', etc.

    SUBJECT: Subject (for DHG)
        - dimension_code: 'MATH', 'FRAN', 'ANGL', etc.

    ACCOUNT_CODE: PCG account (for revenue/costs/capex)
        - dimension_code: '70110', '64110', etc.

    COST_CATEGORY: Cost category (for costs breakdown)
        - dimension_code: 'personnel', 'operating', etc.

    TEACHER_CATEGORY: Teacher type (for DHG)
        - dimension_code: 'aefe_detached', 'local', etc.

    NATIONALITY: Student nationality (for enrollment)
        - dimension_code: 'french', 'saudi', 'other'

    FEE_TYPE: Fee type (for revenue)
        - dimension_code: 'tuition', 'registration', 'transport'
    """

    LEVEL = "level"
    SUBJECT = "subject"
    ACCOUNT_CODE = "account_code"
    COST_CATEGORY = "cost_category"
    TEACHER_CATEGORY = "teacher_category"
    NATIONALITY = "nationality"
    FEE_TYPE = "fee_type"


class HistoricalDataSource(str, PyEnum):
    """
    Source of historical data.

    Sources:
    --------
    ODOO_IMPORT: Imported from Odoo GL
        - Aggregated from actual_data table
        - Verified against accounting records

    MANUAL_UPLOAD: Manual Excel/CSV upload
        - Historical data not in Odoo
        - Requires admin approval

    SKOLENGO_IMPORT: Imported from Skolengo
        - Student enrollment data
        - Class structure data

    SYSTEM_AGGREGATION: System-aggregated
        - Calculated from other tables
        - For derived metrics
    """

    ODOO_IMPORT = "odoo_import"
    MANUAL_UPLOAD = "manual_upload"
    SKOLENGO_IMPORT = "skolengo_import"
    SYSTEM_AGGREGATION = "system_aggregation"


# ==============================================================================
# KPI Models
# ==============================================================================


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

    __tablename__ = "insights_kpi_values"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "kpi_definition_id",
            name="uk_kpi_value_version_definition",
        ),
        CheckConstraint(
            "calculated_value IS NOT NULL",
            name="ck_kpi_value_calculated_not_null",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    # Foreign Keys
    kpi_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_fk_target("efir_budget", "ref_kpi_definitions", "id")),
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
        PortableJSON,
        nullable=False,
        comment="Inputs used for calculation (for audit and recalc)",
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When KPI was calculated",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes or interpretation",
    )

    # Relationships
    kpi_definition: Mapped["KPIDefinition"] = relationship(
        "KPIDefinition",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<KPIValue(kpi={self.kpi_definition_id}, "
            f"value={self.calculated_value:.4f})>"
        )


# ==============================================================================
# Dashboard Configuration Models
# ==============================================================================


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
    """

    __tablename__ = "insights_dashboard_configs"
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
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
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
        Enum(
            DashboardRole,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
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
        ForeignKey(
            get_fk_target("efir_budget", "admin_users", "id"),
            ondelete="CASCADE",
        ),
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
        PortableJSON,
        nullable=False,
        comment="Grid layout configuration (12×12 grid, gap size, etc.)",
    )

    # Relationships
    widgets: Mapped[list["DashboardWidget"]] = relationship(
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
    """

    __tablename__ = "insights_dashboard_widgets"
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
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    # Foreign Keys
    dashboard_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            get_fk_target("efir_budget", "insights_dashboard_configs", "id"),
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="Parent dashboard",
    )

    # Widget Configuration
    widget_type: Mapped[WidgetType] = mapped_column(
        Enum(
            WidgetType,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
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
        PortableJSON,
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
    dashboard_config: Mapped["DashboardConfig"] = relationship(
        "DashboardConfig",
        lazy="selectin",
        overlaps="widgets",
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

    Example Display Preferences:
    -----------------------------
    {
        "number_format": "french",  // 1 234,56
        "language": "fr",
        "timezone": "Europe/Paris",
        "date_format": "DD/MM/YYYY",
        "currency_symbol": "SAR"
    }

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
    """

    __tablename__ = "insights_user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uk_user_preferences_user_id"),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
        comment="User these preferences belong to (references auth.users)",
    )

    default_dashboard_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            get_fk_target("efir_budget", "insights_dashboard_configs", "id"),
            ondelete="SET NULL",
        ),
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
        PortableJSON,
        nullable=False,
        default=dict,
        comment="Number format, language, timezone, date format",
    )

    # Notification Settings
    notification_settings: Mapped[dict] = mapped_column(
        PortableJSON,
        nullable=False,
        default=dict,
        comment="Email alerts, dashboard notifications, weekly summary",
    )

    # Relationships
    default_dashboard: Mapped["DashboardConfig | None"] = relationship(
        "DashboardConfig",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserPreferences(user_id={self.user_id}, theme={self.theme})>"


# ==============================================================================
# Budget vs Actual Models
# ==============================================================================


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
    - Fiscal year and period (month 1-12, 0 = annual)
    - French PCG account code
    - Amount in SAR (or original currency with conversion)
    - Transaction date and description
    - Import batch ID for traceability

    Example:
    --------
    Account 64110 (Teaching Salaries) - October 2025:
        fiscal_year: 2025
        period: 10
        account_code: "64110"
        amount_sar: 2,375,000
        source: odoo_import
        is_reconciled: True
    """

    __tablename__ = "insights_actual_data"
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
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
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
        Enum(
            ActualDataSource,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
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

    YTD Calculations:
    -----------------
    Year-to-date (YTD) amounts track cumulative performance:
        YTD Budget = SUM(budget) for periods 1 to current period
        YTD Actual = SUM(actual) for periods 1 to current period
        YTD Variance = YTD Actual - YTD Budget (revenue) or reverse (expense)
    """

    __tablename__ = "insights_budget_vs_actual"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
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
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

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
        Enum(
            VarianceStatus,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
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

    Root Cause Categories:
    ----------------------
    - enrollment_variance: Student numbers differ from projection
    - price_variance: Costs or fees changed from budget
    - timing_variance: Transaction timing difference (accrual mismatch)
    - procedural_change: Process or policy change
    - external_factor: External event (regulatory, economic, etc.)
    - other: Other reason (specify in text)

    Workflow:
    ---------
    1. System flags material variances (> 5% or > 100K SAR)
    2. Manager provides explanation and corrective action
    3. Finance team reviews and approves
    4. Actions tracked to completion
    5. Insights feed into next year's planning
    """

    __tablename__ = "insights_variance_explanations"
    __table_args__ = (
        CheckConstraint(
            "explanation_text IS NOT NULL AND length(explanation_text) > 10",
            name="ck_explanation_text_required",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    # Foreign Keys
    budget_vs_actual_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            get_fk_target("efir_budget", "insights_budget_vs_actual", "id"),
            ondelete="CASCADE",
        ),
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
    variance: Mapped["BudgetVsActual"] = relationship(
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


# ==============================================================================
# Historical Comparison Model
# ==============================================================================


class HistoricalActuals(BaseModel):
    """
    Historical actuals for planning comparison (N-2, N-1 data).

    Stores annual historical data by module and dimension to enable
    comparison of current budget planning against prior year actuals.
    Supports 2 years of historical data (N-2, N-1, Current).

    Module-Specific Usage:
    ----------------------
    1. Enrollment (module_code='enrollment'):
       - dimension_type: 'level'
       - dimension_code: Level code (e.g., '6EME', 'CP')
       - annual_count: Student count

    2. DHG (module_code='dhg'):
       - dimension_type: 'subject' or 'teacher_category'
       - dimension_code: Subject code (e.g., 'MATH', 'FRAN')
       - annual_fte: Teacher FTE
       - annual_hours: Teaching hours

    3. Revenue (module_code='revenue'):
       - dimension_type: 'account_code' or 'fee_type'
       - dimension_code: PCG account code (e.g., '70110')
       - annual_amount_sar: Revenue amount

    4. Costs (module_code='costs'):
       - dimension_type: 'account_code' or 'cost_category'
       - dimension_code: PCG account code (e.g., '64110')
       - annual_amount_sar: Cost amount

    5. CapEx (module_code='capex'):
       - dimension_type: 'account_code'
       - dimension_code: PCG account code (e.g., '21500')
       - annual_amount_sar: CapEx amount

    Import Sources:
    ---------------
    - manual_upload: Excel/CSV file uploaded by admin
    - odoo_import: Aggregated from actual_data table
    - skolengo_import: Student data from Skolengo system
    - system_aggregation: Calculated from other tables
    """

    __tablename__ = "insights_historical_actuals"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_year",
            "module_code",
            "dimension_type",
            "dimension_code",
            name="uk_historical_year_module_dim",
        ),
        CheckConstraint(
            "fiscal_year >= 2020 AND fiscal_year <= 2099",
            name="ck_historical_fiscal_year_range",
        ),
        CheckConstraint(
            "(annual_amount_sar IS NOT NULL) OR (annual_count IS NOT NULL) OR "
            "(annual_fte IS NOT NULL) OR (annual_hours IS NOT NULL) OR (annual_classes IS NOT NULL)",
            name="ck_historical_has_value",
        ),
        Index(
            "ix_historical_lookup",
            "fiscal_year",
            "module_code",
            "dimension_type",
        ),
        {} if os.environ.get("PYTEST_RUNNING") else {"schema": "efir_budget"},
    )

    # Period Information
    fiscal_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Fiscal year of historical data (e.g., 2024 for FY 2024-2025)",
    )

    # Module & Dimension
    module_code: Mapped[HistoricalModuleCode] = mapped_column(
        Enum(
            HistoricalModuleCode,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
        comment="Module identifier: enrollment, dhg, revenue, costs, capex",
    )

    dimension_type: Mapped[HistoricalDimensionType] = mapped_column(
        Enum(
            HistoricalDimensionType,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="Type of dimension: level, subject, account_code, etc.",
    )

    dimension_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Reference UUID (level_id, subject_id, etc.) if applicable",
    )

    dimension_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Human-readable code (level_code, account_code, subject_code)",
    )

    dimension_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Human-readable name for display purposes",
    )

    # Value Columns (use appropriate one based on module)
    annual_amount_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Annual monetary amount in SAR (for revenue, costs, capex)",
    )

    annual_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Annual count value (for enrollment student counts)",
    )

    annual_fte: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Annual FTE value (for DHG teacher allocations)",
    )

    annual_hours: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Annual hours value (for DHG subject hours)",
    )

    annual_classes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Annual class count (for class_structure)",
    )

    # Metadata
    data_source: Mapped[HistoricalDataSource] = mapped_column(
        Enum(
            HistoricalDataSource,
            schema=get_schema("efir_budget"),
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=HistoricalDataSource.MANUAL_UPLOAD,
        comment="Source of historical data (odoo_import, manual_upload, etc.)",
    )

    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Batch identifier for grouped imports",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes about this historical data point",
    )

    def __repr__(self) -> str:
        """String representation."""
        value = (
            f"{self.annual_amount_sar:,.2f} SAR"
            if self.annual_amount_sar
            else f"{self.annual_count or self.annual_fte or self.annual_hours or self.annual_classes}"
        )
        return (
            f"<HistoricalActuals(FY{self.fiscal_year}, "
            f"{self.module_code.value}/{self.dimension_code}, {value})>"
        )


# ==============================================================================
# KPI Helpers
# ==============================================================================


@dataclass
class KPICalculation:
    """
    Lightweight KPI calculation result model used by export endpoints.

    This is a dataclass (not an ORM model) used for in-memory KPI
    calculation results before persisting to KPIValue table.
    """

    __allow_unmapped__ = True

    kpi_definition: "KPIDefinition"
    calculated_value: Decimal
    variance_from_target: Decimal


# ==============================================================================
# Backward Compatibility Aliases
# ==============================================================================

# No aliases needed - model names are already canonical
