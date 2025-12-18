# EFIR Budget App - Detailed Implementation Plan

**Date**: 2025-12-01 (Updated: 2025-12-02)
**Status**: Phases 1-3 Complete | Phases 4-6 Remaining
**Purpose**: Actionable, step-by-step implementation guide

> **Schema naming (Phase 3+)**: Use `version_id` (not `budget_version_id`) and `settings_versions` (not `budget_versions`).
> Tables are prefixed under the single `efir_budget` schema (`ref_*`, `settings_*`, `students_*`, `teachers_*`, `finance_*`, `insights_*`, `admin_*`).

> **📌 IMPORTANT UPDATE (Dec 2, 2025)**:
>
> A new **[FOCUSED_ENHANCEMENT_ROADMAP.md](./FOCUSED_ENHANCEMENT_ROADMAP.md)** has been created for production-ready enhancements.
>
> **Recommended Approach**:
> 1. **First**: Complete core modules (Phases 4-9 below) - Get working app to production
> 2. **Then**: Implement focused enhancements (FOCUSED_ENHANCEMENT_ROADMAP.md) - Add performance, real-time collaboration, observability
>
> This two-phase approach ensures:
> - ✅ Core features working first (users can start using the app)
> - ✅ Validate assumptions with real users before enhancing
> - ✅ Lower risk (don't build infrastructure for unknown needs)
> - ✅ Faster initial value delivery

---

## Table of Contents

1. [Phase 4: Analysis & Strategic Database Layer](#phase-4-analysis--strategic-database-layer)
2. [Phase 5: Backend Business Logic Services](#phase-5-backend-business-logic-services)
3. [Phase 6: Backend API Endpoints](#phase-6-backend-api-endpoints)
4. [Phase 7: Frontend Components & Pages](#phase-7-frontend-components--pages)
5. [Phase 8: Integration & Testing](#phase-8-integration--testing)
6. [Phase 9: Documentation & Go-Live](#phase-9-documentation--go-live)

---

## Phase 4: Analysis & Strategic Database Layer

**Priority**: 🔴 Critical  
**Estimated Duration**: 2-3 days  
**Dependencies**: None (can start immediately)

### Task 4.1: Module 15 - Statistical Analysis (KPIs) Models

**File**: `backend/app/models/analysis.py`

#### 4.1.1 Create KPIDefinition Model

```python
class KPICategory(str, enum.Enum):
    """KPI category classification."""
    EDUCATIONAL = "educational"  # Student/teacher ratio, class size, etc.
    FINANCIAL = "financial"      # Cost ratios, margins, revenue per student
    OPERATIONAL = "operational"  # Utilization, efficiency metrics


class KPIDefinition(BaseModel):
    """
    KPI catalog - defines all available KPIs.
    
    Examples:
    - Student/Teacher Ratio (Educational)
    - Staff Cost Ratio (Financial)
    - Average Class Size (Educational)
    - Operating Margin (Financial)
    """
    
    __tablename__ = "kpi_definitions"
    
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique KPI code (e.g., 'STUDENT_TEACHER_RATIO')"
    )
    
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable KPI name"
    )
    
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the KPI"
    )
    
    category: Mapped[KPICategory] = mapped_column(
        Enum(KPICategory, native_enum=False),
        nullable=False,
        comment="KPI category"
    )
    
    formula: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Formula description (e.g., 'Total Students ÷ Teaching FTE')"
    )
    
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unit of measurement (e.g., 'ratio', 'SAR', '%')"
    )
    
    target_min: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Minimum target value (for benchmarking)"
    )
    
    target_max: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Maximum target value (for benchmarking)"
    )
    
    is_higher_better: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="True if higher values are better (e.g., operating margin)"
    )
    
    __table_args__ = (
        CheckConstraint("target_max IS NULL OR target_min IS NULL OR target_max >= target_min", name="kpi_target_range_check"),
    )
```

**Acceptance Criteria**:
- [ ] Model created with all fields
- [ ] Enum type `KPICategory` defined
- [ ] Check constraint for target range
- [ ] Unique constraint on `code`
- [ ] Comprehensive docstring with examples

#### 4.1.2 Create KPICalculation Model

```python
class KPICalculation(BaseModel, VersionedMixin):
    """
    Calculated KPI values per budget version.
    
    Example:
    - Budget Version: "2025-2026 Working"
    - KPI: "STUDENT_TEACHER_RATIO"
    - Value: 8.5
    - Status: "within_target" (if 8 <= 8.5 <= 12)
    """
    
    __tablename__ = "kpi_calculations"
    
    kpi_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.kpi_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to KPI definition"
    )
    
    calculated_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Calculated KPI value"
    )
    
    status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Status: 'within_target', 'below_target', 'above_target', 'no_target'"
    )
    
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="When the KPI was calculated"
    )
    
    calculation_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional calculation details (source data, intermediate values)"
    )
    
    kpi_definition: Mapped["KPIDefinition"] = relationship(
        "KPIDefinition",
        foreign_keys=[kpi_definition_id],
        lazy="select"
    )
    
    __table_args__ = (
        UniqueConstraint("version_id", "kpi_definition_id", name="kpi_calculation_unique"),
        CheckConstraint("calculated_value >= 0", name="kpi_value_non_negative"),
    )
```

**Acceptance Criteria**:
- [ ] Model inherits `VersionedMixin` for budget version tracking
- [ ] Foreign key to `KPIDefinition`
- [ ] Unique constraint on (version_id, kpi_definition_id)
- [ ] JSONB field for calculation metadata
- [ ] Relationship to `KPIDefinition`

#### 4.1.3 Create KPIBenchmark Model

```python
class KPIBenchmark(BaseModel):
    """
    Historical benchmarks and targets for KPIs.
    
    Example:
    - KPI: "STAFF_COST_RATIO"
    - Year: 2024
    - Value: 52.6%
    - Source: "EFIR Actual"
    - Benchmark: 60-75% (AEFE norm)
    """
    
    __tablename__ = "kpi_benchmarks"
    
    kpi_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.kpi_definitions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Fiscal year"
    )
    
    value: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Benchmark value"
    )
    
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Source of benchmark (e.g., 'EFIR Actual 2024', 'AEFE Norm')"
    )
    
    is_target: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if this is a target value (vs historical actual)"
    )
    
    kpi_definition: Mapped["KPIDefinition"] = relationship(
        "KPIDefinition",
        foreign_keys=[kpi_definition_id],
        lazy="select"
    )
    
    __table_args__ = (
        UniqueConstraint("kpi_definition_id", "year", "source", name="kpi_benchmark_unique"),
        CheckConstraint("year >= 2000 AND year <= 2100", name="kpi_benchmark_year_check"),
    )
```

**Acceptance Criteria**:
- [ ] Model tracks historical benchmarks
- [ ] Unique constraint on (kpi_definition_id, year, source)
- [ ] Year validation constraint
- [ ] Relationship to `KPIDefinition`

### Task 4.2: Module 16 - Dashboards & Reporting Models

#### 4.2.1 Create Dashboard Model

```python
class Dashboard(BaseModel):
    """
    Dashboard definitions for role-based views.
    
    Example:
    - Name: "Executive Dashboard"
    - Role: "admin"
    - Widgets: [KPI Summary, Budget Status, Revenue Trend]
    """
    
    __tablename__ = "dashboards"
    
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Dashboard name"
    )
    
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Dashboard description"
    )
    
    role_filter: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Role required to view (NULL = all roles)"
    )
    
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if this is the default dashboard for the role"
    )
    
    layout_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Layout configuration (grid positions, sizes)"
    )
    
    __table_args__ = (
        UniqueConstraint("name", name="dashboard_name_unique"),
    )
```

#### 4.2.2 Create DashboardWidget Model

```python
class WidgetType(str, enum.Enum):
    """Widget type classification."""
    KPI_CARD = "kpi_card"              # Single KPI display
    KPI_CHART = "kpi_chart"            # KPI trend chart
    REVENUE_CHART = "revenue_chart"    # Revenue visualization
    COST_CHART = "cost_chart"          # Cost breakdown
    VARIANCE_TABLE = "variance_table"  # Budget vs actual table
    BUDGET_STATUS = "budget_status"    # Approval workflow status


class DashboardWidget(BaseModel):
    """
    Widget configuration for dashboards.
    
    Example:
    - Dashboard: "Executive Dashboard"
    - Type: "KPI_CARD"
    - Config: {"kpi_code": "OPERATING_MARGIN", "format": "percentage"}
    """
    
    __tablename__ = "dashboard_widgets"
    
    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.dashboards.id", ondelete="CASCADE"),
        nullable=False
    )
    
    widget_type: Mapped[WidgetType] = mapped_column(
        Enum(WidgetType, native_enum=False),
        nullable=False,
        comment="Type of widget"
    )
    
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Widget title"
    )
    
    position_x: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Grid X position"
    )
    
    position_y: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Grid Y position"
    )
    
    width: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Widget width (grid units)"
    )
    
    height: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Widget height (grid units)"
    )
    
    config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Widget-specific configuration"
    )
    
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order on dashboard"
    )
    
    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard",
        foreign_keys=[dashboard_id],
        lazy="select"
    )
    
    __table_args__ = (
        CheckConstraint("width > 0 AND width <= 12", name="widget_width_check"),
        CheckConstraint("height > 0 AND height <= 12", name="widget_height_check"),
        CheckConstraint("position_x >= 0", name="widget_position_x_check"),
        CheckConstraint("position_y >= 0", name="widget_position_y_check"),
    )
```

#### 4.2.3 Create ReportTemplate Model

```python
class ReportType(str, enum.Enum):
    """Report type classification."""
    MONTHLY_SUMMARY = "monthly_summary"
    VARIANCE_ANALYSIS = "variance_analysis"
    CASH_FLOW_FORECAST = "cash_flow_forecast"
    BOARD_PACK = "board_pack"
    AEFE_REPORTING = "aefe_reporting"


class ReportFormat(str, enum.Enum):
    """Report export format."""
    PDF = "pdf"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    CSV = "csv"


class ReportTemplate(BaseModel):
    """
    Report templates for standardized reporting.
    
    Example:
    - Name: "Monthly Budget Summary"
    - Type: "MONTHLY_SUMMARY"
    - Format: "PDF"
    - Template: JSON configuration for report structure
    """
    
    __tablename__ = "report_templates"
    
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Report template name"
    )
    
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, native_enum=False),
        nullable=False,
        comment="Type of report"
    )
    
    default_format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, native_enum=False),
        nullable=False,
        default=ReportFormat.PDF,
        comment="Default export format"
    )
    
    template_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Report template configuration (sections, data sources, formatting)"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="True if template is active"
    )
    
    __table_args__ = (
        UniqueConstraint("name", name="report_template_name_unique"),
    )
```

#### 4.2.4 Create ReportExecution Model

```python
class ReportExecution(BaseModel, VersionedMixin):
    """
    Report execution history for audit trail.
    
    Tracks when reports were generated, by whom, and in what format.
    """
    
    __tablename__ = "report_executions"
    
    report_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.report_templates.id", ondelete="SET NULL"),
        nullable=True,
        comment="Report template used (NULL if custom report)"
    )
    
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of report generated"
    )
    
    export_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Export format (PDF, Excel, etc.)"
    )
    
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to generated report file (if stored)"
    )
    
    file_size_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Size of generated report file in bytes"
    )
    
    execution_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Execution details (parameters, filters, etc.)"
    )
    
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="When the report was generated"
    )
    
    report_template: Mapped["ReportTemplate | None"] = relationship(
        "ReportTemplate",
        foreign_keys=[report_template_id],
        lazy="select"
    )
```

### Task 4.3: Module 17 - Budget vs Actual Models

#### 4.3.1 Create ActualTransaction Model

```python
class ActualTransaction(BaseModel):
    """
    Imported actual transactions from Odoo accounting system.
    
    Example:
    - Account Code: "64110"
    - Amount: -125,000 SAR (negative = expense)
    - Period: "2025-01"
    - Source: "Odoo Import"
    """
    
    __tablename__ = "actual_transactions"
    
    account_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Chart of accounts code (e.g., '64110')"
    )
    
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Transaction date"
    )
    
    period: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Period in YYYY-MM format"
    )
    
    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Transaction amount in SAR (negative for expenses)"
    )
    
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Transaction description"
    )
    
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Odoo",
        comment="Source system (e.g., 'Odoo', 'Manual Entry')"
    )
    
    source_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Reference from source system (e.g., Odoo invoice number)"
    )
    
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="When the transaction was imported"
    )
    
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Batch ID for grouping imports"
    )
    
    __table_args__ = (
        Index("idx_actual_transactions_period", "period"),
        Index("idx_actual_transactions_account", "account_code"),
        Index("idx_actual_transactions_date", "transaction_date"),
    )
```

#### 4.3.2 Create BudgetVariance Model

```python
class BudgetVariance(BaseModel, VersionedMixin):
    """
    Calculated budget vs actual variances.
    
    Example:
    - Account Code: "64110"
    - Budget: 125,000 SAR
    - Actual: 130,000 SAR
    - Variance: -5,000 SAR (unfavorable for expense)
    - Variance %: -4.0%
    """
    
    __tablename__ = "budget_variances"
    
    account_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Chart of accounts code"
    )
    
    period: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Period in YYYY-MM format"
    )
    
    budget_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Budgeted amount"
    )
    
    actual_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Actual amount"
    )
    
    variance_amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Variance (budget - actual)"
    )
    
    variance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Variance percentage"
    )
    
    is_revenue: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="True if revenue account (affects favorability logic)"
    )
    
    is_favorable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="True if variance is favorable (under budget for expense, over budget for revenue)"
    )
    
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="When variance was calculated"
    )
    
    __table_args__ = (
        UniqueConstraint("version_id", "account_code", "period", name="budget_variance_unique"),
        Index("idx_budget_variances_period", "period"),
        Index("idx_budget_variances_account", "account_code"),
    )
```

#### 4.3.3 Create ForecastRevision Model

```python
class ForecastRevision(BaseModel, VersionedMixin):
    """
    Revised forecasts based on YTD actuals.
    
    Example:
    - Original Budget: 1,500,000 SAR
    - YTD Actual: 600,000 SAR (4 months)
    - Remaining Budget: 900,000 SAR
    - Trend Factor: 1.1 (10% increase)
    - Revised Forecast: 600,000 + (900,000 × 1.1) = 1,590,000 SAR
    """
    
    __tablename__ = "forecast_revisions"
    
    account_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Chart of accounts code"
    )
    
    original_budget_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Original budget amount"
    )
    
    ytd_actual_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Year-to-date actual amount"
    )
    
    remaining_budget_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Remaining budget (original - YTD actual)"
    )
    
    trend_factor: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("1.0"),
        comment="Trend factor applied to remaining budget"
    )
    
    revised_forecast_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Revised forecast amount"
    )
    
    revision_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for revision"
    )
    
    revised_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="When forecast was revised"
    )
    
    __table_args__ = (
        UniqueConstraint("version_id", "account_code", name="forecast_revision_unique"),
    )
```

#### 4.3.4 Create VarianceExplanation Model

```python
class VarianceExplanation(BaseModel, VersionedMixin):
    """
    Explanations for significant variances.
    
    Example:
    - Variance ID: [reference]
    - Explanation: "Higher than expected teacher salaries due to HSA overtime"
    - Action Plan: "Review HSA allocation and consider additional recruitment"
    """
    
    __tablename__ = "variance_explanations"
    
    budget_variance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.budget_variances.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to budget variance"
    )
    
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Explanation for the variance"
    )
    
    action_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Action plan to address variance"
    )
    
    budget_variance: Mapped["BudgetVariance"] = relationship(
        "BudgetVariance",
        foreign_keys=[budget_variance_id],
        lazy="select"
    )
    
    __table_args__ = (
        UniqueConstraint("budget_variance_id", name="variance_explanation_unique"),
    )
```

### Task 4.4: Module 18 - 5-Year Strategic Plan Models

#### 4.4.1 Create StrategicPlan Model

```python
class StrategicPlan(BaseModel):
    """
    5-year strategic plan header.
    
    Example:
    - Name: "EFIR Strategic Plan 2025-2030"
    - Base Year: 2025
    - Status: "draft"
    """
    
    __tablename__ = "strategic_plans"
    
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Strategic plan name"
    )
    
    base_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Base year (Year 1 of 5-year plan)"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        comment="Status: 'draft', 'approved', 'archived'"
    )
    
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Strategic plan description"
    )
    
    __table_args__ = (
        UniqueConstraint("name", name="strategic_plan_name_unique"),
        CheckConstraint("base_year >= 2000 AND base_year <= 2100", name="strategic_plan_year_check"),
    )
```

#### 4.4.2 Create StrategicPlanScenario Model

```python
class ScenarioType(str, enum.Enum):
    """Strategic scenario types."""
    BASE_CASE = "base_case"           # Current trajectory
    CONSERVATIVE = "conservative"     # Slower growth
    OPTIMISTIC = "optimistic"          # Expansion
    NEW_CAMPUS = "new_campus"          # Major investment


class StrategicPlanScenario(BaseModel):
    """
    Scenario definitions for strategic planning.
    
    Example:
    - Strategic Plan: "EFIR Strategic Plan 2025-2030"
    - Type: "BASE_CASE"
    - Enrollment Growth: 3% per year
    - Fee Increase: 4% per year
    """
    
    __tablename__ = "strategic_plan_scenarios"
    
    strategic_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.strategic_plans.id", ondelete="CASCADE"),
        nullable=False
    )
    
    scenario_type: Mapped[ScenarioType] = mapped_column(
        Enum(ScenarioType, native_enum=False),
        nullable=False,
        comment="Type of scenario"
    )
    
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Scenario name"
    )
    
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Scenario description"
    )
    
    enrollment_growth_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual enrollment growth rate (e.g., 0.03 = 3%)"
    )
    
    fee_increase_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual fee increase rate (e.g., 0.04 = 4%)"
    )
    
    salary_inflation_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual salary inflation rate (e.g., 0.035 = 3.5%)"
    )
    
    operating_inflation_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Annual operating cost inflation rate (e.g., 0.025 = 2.5%)"
    )
    
    strategic_plan: Mapped["StrategicPlan"] = relationship(
        "StrategicPlan",
        foreign_keys=[strategic_plan_id],
        lazy="select"
    )
    
    __table_args__ = (
        UniqueConstraint("strategic_plan_id", "scenario_type", name="strategic_plan_scenario_unique"),
        CheckConstraint("enrollment_growth_rate >= -0.5 AND enrollment_growth_rate <= 1.0", name="enrollment_growth_range"),
        CheckConstraint("fee_increase_rate >= -0.2 AND fee_increase_rate <= 0.5", name="fee_increase_range"),
    )
```

#### 4.4.3 Create StrategicPlanProjection Model

```python
class StrategicPlanProjection(BaseModel):
    """
    Multi-year projections for strategic plan scenarios.
    
    Example:
    - Scenario: "BASE_CASE"
    - Year: 2026 (Year 2)
    - Category: "revenue"
    - Amount: 52,500,000 SAR
    """
    
    __tablename__ = "strategic_plan_projections"
    
    strategic_plan_scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.strategic_plan_scenarios.id", ondelete="CASCADE"),
        nullable=False
    )
    
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Year of projection (1-5)"
    )
    
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Projection category: 'revenue', 'personnel_costs', 'operating_costs', 'capex', 'depreciation'"
    )
    
    amount_sar: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Projected amount in SAR"
    )
    
    strategic_plan_scenario: Mapped["StrategicPlanScenario"] = relationship(
        "StrategicPlanScenario",
        foreign_keys=[strategic_plan_scenario_id],
        lazy="select"
    )
    
    __table_args__ = (
        UniqueConstraint("strategic_plan_scenario_id", "year", "category", name="strategic_plan_projection_unique"),
        CheckConstraint("year >= 1 AND year <= 5", name="strategic_plan_year_range"),
    )
```

#### 4.4.4 Create StrategicInitiative Model

```python
class StrategicInitiative(BaseModel):
    """
    Strategic initiatives/projects within 5-year plan.
    
    Example:
    - Name: "New Science Lab"
    - Strategic Plan: "EFIR Strategic Plan 2025-2030"
    - Year: 2027
    - CapEx: 2,500,000 SAR
    """
    
    __tablename__ = "strategic_initiatives"
    
    strategic_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("efir_budget.strategic_plans.id", ondelete="CASCADE"),
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Initiative name"
    )
    
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Initiative description"
    )
    
    planned_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Year when initiative is planned (1-5)"
    )
    
    capex_amount_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Capital expenditure required"
    )
    
    operating_impact_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Annual operating cost impact"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="planned",
        comment="Status: 'planned', 'approved', 'in_progress', 'completed', 'cancelled'"
    )
    
    strategic_plan: Mapped["StrategicPlan"] = relationship(
        "StrategicPlan",
        foreign_keys=[strategic_plan_id],
        lazy="select"
    )
    
    __table_args__ = (
        CheckConstraint("planned_year >= 1 AND planned_year <= 5", name="strategic_initiative_year_range"),
    )
```

### Task 4.5: Create Alembic Migration

**File**: `backend/alembic/versions/YYYYMMDD_HHMM_analysis_strategic_layer.py`

**Migration Steps**:
1. Create enum types:
   - `kpi_category` (educational, financial, operational)
   - `widget_type` (kpi_card, kpi_chart, revenue_chart, etc.)
   - `report_type` (monthly_summary, variance_analysis, etc.)
   - `report_format` (pdf, excel, powerpoint, csv)
   - `scenario_type` (base_case, conservative, optimistic, new_campus)

2. Create tables in dependency order:
   - `kpi_definitions`
   - `kpi_calculations`
   - `kpi_benchmarks`
   - `dashboards`
   - `dashboard_widgets`
   - `report_templates`
   - `report_executions`
   - `actual_transactions`
   - `budget_variances`
   - `forecast_revisions`
   - `variance_explanations`
   - `strategic_plans`
   - `strategic_plan_scenarios`
   - `strategic_plan_projections`
   - `strategic_initiatives`

3. Add foreign keys
4. Add check constraints
5. Add unique constraints
6. Add indexes
7. Apply `updated_at` triggers
8. Create downgrade path

**Acceptance Criteria**:
- [ ] Migration creates all 15 tables
- [ ] All enum types created
- [ ] All constraints added
- [ ] All indexes created
- [ ] Triggers applied
- [ ] Downgrade path works

### Task 4.6: Add RLS Policies

**File**: `docs/database/sql/rls_policies.sql` (append)

**Policy Pattern** (same as existing):
- Admin: Full access
- Manager: Read/write working versions, read-only others
- Viewer: Read-only approved versions

**Tables to Secure**:
- All 15 Analysis & Strategic Layer tables

**Acceptance Criteria**:
- [ ] RLS enabled on all tables
- [ ] Policies follow existing pattern
- [ ] Test queries provided

### Task 4.7: Update Models Package

**File**: `backend/app/models/__init__.py`

**Add Exports**:
```python
from app.models.analysis import (
    KPIDefinition,
    KPICalculation,
    KPIBenchmark,
    KPICategory,
    Dashboard,
    DashboardWidget,
    WidgetType,
    ReportTemplate,
    ReportExecution,
    ReportType,
    ReportFormat,
    ActualTransaction,
    BudgetVariance,
    ForecastRevision,
    VarianceExplanation,
)

from app.models.strategic import (
    StrategicPlan,
    StrategicPlanScenario,
    StrategicPlanProjection,
    StrategicInitiative,
    ScenarioType,
)
```

**Acceptance Criteria**:
- [ ] All models exported
- [ ] All enums exported
- [ ] `__all__` list updated

---

## Phase 5: Backend Business Logic Services

**Priority**: 🔴 Critical  
**Estimated Duration**: 10-15 days  
**Dependencies**: Phase 4 complete

### Task 5.1: Create Services Directory Structure

**Directory**: `backend/app/services/`

```
services/
├── __init__.py
├── configuration_service.py
├── enrollment_service.py
├── class_structure_service.py
├── dhg_service.py          # CORE CALCULATION ENGINE
├── revenue_service.py
├── cost_service.py
├── capex_service.py
├── consolidation_service.py
├── financial_statement_service.py
├── kpi_service.py
├── dashboard_service.py
├── variance_service.py
└── strategic_plan_service.py
```

### Task 5.2: DHG Service (Highest Priority)

**File**: `backend/app/services/dhg_service.py`

#### 5.2.1 Calculate DHG Subject Hours

**Function**: `calculate_dhg_subject_hours()`

**Input**:
- `class_structure_id: UUID` - Class structure to calculate for
- `db: AsyncSession` - Database session

**Logic**:
```python
async def calculate_dhg_subject_hours(
    class_structure_id: UUID,
    version_id: UUID,
    db: AsyncSession
) -> list[DHGSubjectHours]:
    """
    Calculate total DHG hours per subject per level.
    
    Formula:
    total_hours = number_of_classes × hours_per_class_per_week
    
    If split (half-size groups):
    total_hours = total_hours × 2
    
    Example:
    - Mathématiques in 6ème: 6 classes × 4.5h = 27h/week
    - If split: 27h × 2 = 54h/week
    """
    # 1. Get class structure
    # 2. Get subject hours matrix for each level
    # 3. For each (subject, level) combination:
    #    - Get number of classes from class_structure
    #    - Get hours per class from subject_hours_matrix
    #    - Calculate: total_hours = classes × hours
    #    - If split: total_hours × 2
    # 4. Create/update DHGSubjectHours records
    # 5. Return list of records
```

**Acceptance Criteria**:
- [ ] Function calculates hours correctly
- [ ] Handles split classes (×2 multiplier)
- [ ] Creates/updates database records
- [ ] Returns list of DHGSubjectHours
- [ ] Unit tests with real EFIR data

#### 5.2.2 Calculate Teacher FTE Requirements

**Function**: `calculate_teacher_requirements()`

**Input**:
- `dhg_subject_hours: list[DHGSubjectHours]` - Subject hours to calculate for
- `db: AsyncSession` - Database session

**Logic**:
```python
async def calculate_teacher_requirements(
    dhg_subject_hours: list[DHGSubjectHours],
    version_id: UUID,
    db: AsyncSession
) -> list[DHGTeacherRequirement]:
    """
    Calculate teacher FTE requirements from DHG hours.
    
    Formula:
    simple_fte = total_hours / standard_hours
    rounded_fte = CEILING(simple_fte)
    hsa_hours = MAX(0, total_hours - (rounded_fte × standard_hours))
    
    Standard hours:
    - Primary (Maternelle, Élémentaire): 24h/week
    - Secondary (Collège, Lycée): 18h/week
    
    Example:
    - Mathématiques total: 96h/week
    - Standard: 18h/week (Secondary)
    - simple_fte = 96 / 18 = 5.33
    - rounded_fte = 6
    - hsa_hours = 96 - (6 × 18) = 96 - 108 = 0 (no HSA needed)
    
    If total = 100h:
    - simple_fte = 100 / 18 = 5.56
    - rounded_fte = 6
    - hsa_hours = 100 - 108 = -8 → 0 (no HSA, actually overallocated)
    """
    # 1. Group hours by subject and cycle
    # 2. Determine standard hours (24h for Primary, 18h for Secondary)
    # 3. For each subject:
    #    - Calculate simple_fte = total_hours / standard_hours
    #    - Calculate rounded_fte = CEILING(simple_fte)
    #    - Calculate hsa_hours = MAX(0, total_hours - (rounded_fte × standard_hours))
    # 4. Create/update DHGTeacherRequirement records
    # 5. Return list of records
```

**Acceptance Criteria**:
- [ ] Function calculates FTE correctly
- [ ] Handles Primary (24h) vs Secondary (18h)
- [ ] Calculates HSA hours correctly
- [ ] Creates/updates database records
- [ ] Unit tests with real EFIR data

#### 5.2.3 Calculate TRMD Gap Analysis

**Function**: `calculate_trmd_gap_analysis()`

**Input**:
- `version_id: UUID` - Version id
- `db: AsyncSession` - Database session

**Logic**:
```python
async def calculate_trmd_gap_analysis(
    version_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Calculate TRMD (Tableau de Répartition des Moyens par Discipline) gap analysis.
    
    Formula:
    Besoins (Need) = dhg_teacher_requirements.rounded_fte
    Moyens (Available) = SUM(teacher_allocations.fte_count)
    Déficit = Besoins - Moyens
    
    Returns:
    {
        "subject_id": {
            "needs": 6.0,
            "available": 5.5,
            "deficit": 0.5,
            "status": "deficit"  # or "surplus" or "balanced"
        }
    }
    """
    # 1. Get all teacher requirements (Besoins)
    # 2. Get all teacher allocations (Moyens)
    # 3. Group by subject
    # 4. Calculate deficit = needs - available
    # 5. Determine status
    # 6. Return dictionary
```

**Acceptance Criteria**:
- [ ] Function calculates gap correctly
- [ ] Groups by subject
- [ ] Determines deficit/surplus status
- [ ] Returns structured dictionary
- [ ] Unit tests with real EFIR data

### Task 5.3: Revenue Service

**File**: `backend/app/services/revenue_service.py`

#### 5.3.1 Calculate Revenue from Enrollment

**Function**: `calculate_revenue_from_enrollment()`

**Logic**:
```python
async def calculate_revenue_from_enrollment(
    version_id: UUID,
    db: AsyncSession
) -> list[RevenuePlan]:
    """
    Calculate revenue from enrollment × fee structure.
    
    Formula:
    revenue = enrollment × fee_amount
    
    Trimester split:
    - T1 (Sep-Dec): 40%
    - T2 (Jan-Mar): 30%
    - T3 (Apr-Jun): 30%
    
    Sibling discount:
    - 25% discount on tuition for 3rd+ child
    - Applies only to tuition (not DAI, registration fees)
    
    Example:
    - Enrollment: 50 students (French, CP level)
    - Tuition: 45,000 SAR/year
    - T1: 50 × 45,000 × 0.40 = 900,000 SAR
    - T2: 50 × 45,000 × 0.30 = 675,000 SAR
    - T3: 50 × 45,000 × 0.30 = 675,000 SAR
    """
    # 1. Get enrollment plans
    # 2. Get fee structure
    # 3. For each (level, nationality, fee_category):
    #    - Calculate base revenue = enrollment × fee
    #    - Apply trimester split
    #    - Apply sibling discount (if tuition)
    #    - Create RevenuePlan records
    # 4. Return list of records
```

**Acceptance Criteria**:
- [ ] Calculates revenue correctly
- [ ] Applies trimester split (40/30/30)
- [ ] Applies sibling discount correctly
- [ ] Creates database records
- [ ] Unit tests with real EFIR data

### Task 5.4: Cost Service

**File**: `backend/app/services/cost_service.py`

#### 5.4.1 Calculate Personnel Costs

**Function**: `calculate_personnel_costs()`

**Logic**:
```python
async def calculate_personnel_costs(
    version_id: UUID,
    db: AsyncSession
) -> list[PersonnelCostPlan]:
    """
    Calculate personnel costs from teacher allocations.
    
    AEFE Detached:
    cost = fte_count × prrd_contribution_eur × eur_to_sar_rate
    
    AEFE Funded:
    cost = 0 (fully funded by AEFE)
    
    Local:
    cost = fte_count × (salary + social_charges + benefits + hsa_cost)
    where:
    - social_charges = salary × 0.21 (21%)
    - hsa_cost = hsa_hours × hsa_hourly_rate
    
    Example (AEFE Detached):
    - FTE: 2.0
    - PRRD: 41,863 EUR
    - EUR/SAR: 4.05
    - Cost: 2.0 × 41,863 × 4.05 = 339,090 SAR
    
    Example (Local):
    - FTE: 1.0
    - Salary: 120,000 SAR/year
    - Social charges: 120,000 × 0.21 = 25,200 SAR
    - Benefits: 15,000 SAR
    - HSA: 50h × 200 SAR/h = 10,000 SAR
    - Total: 120,000 + 25,200 + 15,000 + 10,000 = 170,200 SAR
    """
    # 1. Get teacher allocations
    # 2. Get teacher cost parameters
    # 3. Get system config (EUR/SAR rate)
    # 4. For each allocation:
    #    - Determine category (AEFE Detached, AEFE Funded, Local)
    #    - Calculate cost based on category
    #    - Create PersonnelCostPlan records
    # 5. Return list of records
```

**Acceptance Criteria**:
- [ ] Calculates AEFE costs correctly (EUR → SAR)
- [ ] Calculates Local costs correctly (salary + social + benefits + HSA)
- [ ] Handles AEFE Funded (cost = 0)
- [ ] Creates database records
- [ ] Unit tests with real EFIR data

### Task 5.5: Consolidation Service

**File**: `backend/app/services/consolidation_service.py`

#### 5.5.1 Aggregate Budget Data

**Function**: `aggregate_budget_data()`

**Logic**:
```python
async def aggregate_budget_data(
    version_id: UUID,
    db: AsyncSession
) -> list[BudgetConsolidation]:
    """
    Aggregate all Planning Layer data into BudgetConsolidation.
    
    Sources:
    - revenue_plans → budget_consolidations (70xxx accounts)
    - personnel_cost_plans → budget_consolidations (64xxx accounts)
    - operating_cost_plans → budget_consolidations (60xxx-68xxx accounts)
    - capex_plans → budget_consolidations (20xxx-21xxx accounts)
    
    Groups by:
    - account_code
    - consolidation_category
    
    Example:
    - Account: "70110" (Tuition T1)
    - Source: revenue_plans
    - Amount: 45,678,000 SAR
    - Category: revenue_tuition
    """
    # 1. Aggregate revenue_plans by account_code
    # 2. Aggregate personnel_cost_plans by account_code
    # 3. Aggregate operating_cost_plans by account_code
    # 4. Aggregate capex_plans by account_code
    # 5. Map to consolidation_category
    # 6. Create/update BudgetConsolidation records
    # 7. Return list of records
```

**Acceptance Criteria**:
- [ ] Aggregates all sources correctly
- [ ] Groups by account_code
- [ ] Maps to consolidation_category
- [ ] Tracks source_table and source_count
- [ ] Creates database records
- [ ] Unit tests

### Task 5.6: Financial Statement Service

**File**: `backend/app/services/financial_statement_service.py`

#### 5.6.1 Generate Income Statement

**Function**: `generate_income_statement()`

**Logic**:
```python
async def generate_income_statement(
    version_id: UUID,
    format: StatementFormat,
    db: AsyncSession
) -> FinancialStatement:
    """
    Generate Income Statement (Compte de résultat) from budget consolidation.
    
    Structure (French PCG):
    PRODUITS D'EXPLOITATION (Section Header, indent=0)
      70 - Ventes (Account Group, indent=1)
        701 - Scolarité (Account Line, indent=2)
          70110 - Scolarité T1: 45,678,000 (Account Line, indent=3)
      Total Produits: 48,878,000 (Subtotal, indent=1)
    
    CHARGES D'EXPLOITATION (Section Header, indent=0)
      64 - Charges de personnel (Account Group, indent=1)
        641 - Rémunérations (Account Line, indent=2)
          64110 - Salaires enseignants: 28,500,000 (Account Line, indent=3)
      Total Charges: 35,785,000 (Subtotal, indent=1)
    
    RÉSULTAT D'EXPLOITATION: 13,093,000 (Total, indent=0, bold, underlined)
    """
    # 1. Get budget_consolidations
    # 2. Group by account code hierarchy
    # 3. Create FinancialStatement header
    # 4. Create FinancialStatementLine records with hierarchy
    # 5. Apply formatting (bold, underlined, indent)
    # 6. Return FinancialStatement with lines
```

**Acceptance Criteria**:
- [ ] Generates correct French PCG structure
- [ ] Creates hierarchical lines
- [ ] Applies formatting correctly
- [ ] Calculates subtotals and totals
- [ ] Creates database records
- [ ] Unit tests

---

## Phase 6: Backend API Endpoints

**Priority**: 🔴 Critical  
**Estimated Duration**: 8-12 days  
**Dependencies**: Phase 5 complete

### Task 6.1: Create API Router Structure

**Directory**: `backend/app/routes/`

```
routes/
├── __init__.py
├── auth.py
├── configuration.py
├── enrollment.py
├── class_structure.py
├── dhg.py
├── revenue.py
├── costs.py
├── capex.py
├── consolidation.py
├── financial_statements.py
├── kpis.py
├── dashboards.py
├── variance.py
└── strategic_plan.py
```

### Task 6.2: Authentication Middleware

**File**: `backend/app/middleware/auth.py`

**Function**: `get_current_user()`

**Logic**:
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Verify JWT token from Supabase and return user info.
    
    Returns:
    {
        "id": UUID,
        "email": str,
        "role": "admin" | "manager" | "viewer"
    }
    """
    # 1. Verify token with Supabase
    # 2. Extract user info
    # 3. Get role from raw_user_meta_data
    # 4. Return user dict
```

**Acceptance Criteria**:
- [ ] Verifies JWT token
- [ ] Extracts user role
- [ ] Returns user info
- [ ] Handles invalid tokens
- [ ] Unit tests

### Task 6.3: DHG API Endpoints

**File**: `backend/app/routes/dhg.py`

**Endpoints**:
- `GET /api/v1/dhg/subject-hours/{version_id}` - Get DHG subject hours
- `POST /api/v1/dhg/subject-hours/{version_id}/calculate` - Calculate DHG hours
- `GET /api/v1/dhg/teacher-requirements/{version_id}` - Get teacher FTE requirements
- `POST /api/v1/dhg/teacher-requirements/{version_id}/calculate` - Calculate teacher FTE
- `GET /api/v1/dhg/allocations/{version_id}` - Get teacher allocations
- `POST /api/v1/dhg/allocations/{version_id}` - Update teacher allocations
- `GET /api/v1/dhg/trmd/{version_id}` - Get TRMD gap analysis

**Example Endpoint**:
```python
@router.post("/subject-hours/{version_id}/calculate")
async def calculate_dhg_hours(
    version_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate DHG subject hours from class structure.
    
    Requires: manager or admin role
    """
    # 1. Check permissions
    # 2. Call dhg_service.calculate_dhg_subject_hours()
    # 3. Return results
```

**Acceptance Criteria**:
- [ ] All endpoints implemented
- [ ] Authentication required
- [ ] Role-based access control
- [ ] Error handling
- [ ] OpenAPI documentation
- [ ] Integration tests

---

## Phase 7: Frontend Components & Pages

**Priority**: 🔴 Critical  
**Estimated Duration**: 20-30 days  
**Dependencies**: Phase 6 complete

### Task 7.1: Core Infrastructure

**Files**:
- `frontend/src/lib/supabase.ts` - Supabase client
- `frontend/src/lib/api.ts` - API client with React Query
- `frontend/src/hooks/useAuth.ts` - Authentication hook
- `frontend/src/hooks/useBudgetVersion.ts` - Budget version hook

### Task 7.2: Layout Components

**Files**:
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/Header.tsx`

### Task 7.3: DHG Planning Page (Priority)

**File**: `frontend/src/pages/planning/DHG.tsx`

**Features**:
- AG Grid for subject hours
- AG Grid for teacher requirements
- TRMD gap analysis table
- Teacher allocation interface
- Real-time calculations

**Acceptance Criteria**:
- [ ] Displays DHG data in AG Grid
- [ ] Supports inline editing
- [ ] Triggers calculations on change
- [ ] Shows TRMD gap analysis
- [ ] Responsive design
- [ ] E2E tests

---

## Phase 8: Integration & Testing

**Priority**: 🟡 High  
**Estimated Duration**: 15-20 days  
**Dependencies**: Phases 5-7 complete

### Task 8.1: Odoo Integration

**File**: `backend/app/integrations/odoo.py`

**Functions**:
- `import_actuals_from_odoo()` - Import GL transactions
- `map_account_codes()` - Map Odoo accounts to EFIR accounts

### Task 8.2: Testing

**Backend Tests**:
- Unit tests for all services (80%+ coverage)
- Integration tests for all APIs
- Database integration tests

**Frontend Tests**:
- Unit tests for components
- Integration tests for pages
- E2E tests with Playwright

---

## Phase 9: Documentation & Go-Live

**Priority**: 🟢 Medium  
**Estimated Duration**: 3-5 days  
**Dependencies**: All phases complete

### Task 9.1: Module Documentation

**Files**:
- `docs/modules/Module_15_Statistical_Analysis.md`
- `docs/modules/Module_16_Dashboards.md`
- `docs/modules/Module_17_Budget_Vs_Actual.md`
- `docs/modules/Module_18_Strategic_Plan.md`

### Task 9.2: User Documentation

- User guides
- Training materials
- Workflow documentation

---

## Implementation Checklist

### Phase 4: Database (2-3 days)
- [ ] Module 15 models (3 models)
- [ ] Module 16 models (4 models)
- [ ] Module 17 models (4 models)
- [ ] Module 18 models (4 models)
- [ ] Alembic migration
- [ ] RLS policies
- [ ] Models package update

### Phase 5: Services (10-15 days)
- [ ] DHG service (highest priority)
- [ ] Revenue service
- [ ] Cost service
- [ ] Consolidation service
- [ ] Financial statement service
- [ ] KPI service
- [ ] Variance service
- [ ] Strategic plan service

### Phase 6: APIs (8-12 days)
- [ ] Authentication middleware
- [ ] Configuration APIs
- [ ] Planning APIs
- [ ] Consolidation APIs
- [ ] Analysis APIs
- [ ] Strategic APIs

### Phase 7: Frontend (20-30 days)
- [ ] Core infrastructure
- [ ] Layout components
- [ ] Configuration pages
- [ ] Planning pages
- [ ] Consolidation pages
- [ ] Analysis pages
- [ ] Strategic pages

### Phase 8: Integration & Testing (15-20 days)
- [ ] Odoo integration
- [ ] Skolengo integration
- [ ] Backend tests
- [ ] Frontend tests
- [ ] E2E tests

### Phase 9: Documentation (3-5 days)
- [ ] Module documentation
- [ ] API documentation
- [ ] User documentation

---

**Total Estimated Duration**: 58-87 days

**Last Updated**: 2025-12-01


