# Module 2: Class Size Parameters - Future Enhancements

**Document Version**: 1.0
**Date**: December 5, 2025
**Status**: Planned Future Improvements
**Priority**: Medium to High
**Estimated Effort**: 3-4 weeks (phased implementation)

---

## Executive Summary

This document outlines four advanced features planned for Module 2 (Class Size Parameters) that will transform it from a parameter management tool into an intelligent, interactive planning platform. These enhancements leverage existing infrastructure (calculation engines, Supabase Realtime, Recharts) to provide scenario modeling, optimization recommendations, visual analytics, and real-time collaboration.

**Current State**: Module 2 core functionality is 100% complete with full CRUD operations, validation, and testing.

**Future Vision**: Interactive what-if analysis, AI-powered recommendations, rich visualizations, and collaborative real-time editing.

---

## Table of Contents

1. [Feature 1: Visual Distribution](#feature-1-visual-distribution-)
2. [Feature 2: Scenario Modeling](#feature-2-scenario-modeling-)
3. [Feature 3: Optimization Calculator](#feature-3-optimization-calculator-)
4. [Feature 4: Real-time Integration](#feature-4-real-time-integration-)
5. [Implementation Roadmap](#implementation-roadmap)
6. [Technical Architecture](#technical-architecture)
7. [Success Metrics](#success-metrics)
8. [Dependencies](#dependencies)

---

## Feature 1: Visual Distribution 📊

### Overview
Interactive charts and visualizations showing how students are distributed across classes, cost breakdowns by cycle, and comparisons against AEFE benchmarks.

### Business Value
- **Better Planning**: Visual feedback helps planners understand capacity constraints
- **Cost Transparency**: See immediate cost impacts of parameter changes
- **Benchmark Compliance**: Easy comparison with AEFE standards
- **Stakeholder Communication**: Export-ready charts for board presentations

### Functional Requirements

#### FR-1.1: Student Distribution Chart
- **Type**: Bar Chart (Recharts)
- **Data**: Students per class by academic level (PS, MS, GS, CP, CE1, ...)
- **Features**:
  - X-axis: Academic levels
  - Y-axis: Student count
  - Color-coded bars by utilization:
    - Green: 85-100% utilization (optimal)
    - Yellow: 70-84% utilization (warning)
    - Red: <70% or >100% utilization (critical)
  - Custom tooltip showing:
    - Level name
    - Number of classes
    - Avg class size
    - Utilization percentage
    - Min/target/max parameters

#### FR-1.2: Cost Breakdown Chart
- **Type**: Stacked Bar Chart
- **Data**: Personnel costs by cycle (Maternelle, Élémentaire, Collège, Lycée)
- **Categories**:
  - Teacher costs (blue)
  - ATSEM costs (orange, Maternelle only)
  - Administrative overhead (gray)
- **Features**:
  - Summary card showing total cost
  - Cost per student metric
  - Hover tooltip with detailed breakdown

#### FR-1.3: AEFE Comparison Chart
- **Type**: Line Chart with dual Y-axes
- **Data**: Current class sizes vs AEFE benchmarks
- **Features**:
  - Line 1: Current average class sizes (solid blue)
  - Line 2: AEFE recommended class sizes (dashed red)
  - Shaded area showing acceptable range (±10%)
  - Indicators where school exceeds or falls below standards

#### FR-1.4: Trend Chart
- **Type**: Multi-year Line Chart
- **Data**: Historical class size trends across budget versions
- **Features**:
  - Compare up to 5 budget years
  - Show projection overlay for future years
  - Toggle between cycles (Maternelle, Élémentaire, etc.)

#### FR-1.5: Export Capabilities
- **Formats**: PNG, PDF, Excel
- **Features**:
  - High-resolution chart exports (300dpi)
  - Multi-chart PDF reports with header/footer
  - Excel with raw data tables + embedded charts

### Technical Design

#### Backend Components

**New Calculation Engine**: `backend/app/engine/class_distribution/`
```python
# Pure function pattern
def calculate_class_distribution(
    enrollment: EnrollmentData,
    class_size_params: List[ClassSizeParam]
) -> ClassDistributionResult:
    """
    Calculate how students are distributed across classes.

    For each level:
    1. student_count ÷ target_class_size = estimated_classes
    2. Distribute students evenly across classes
    3. Calculate avg_class_size, utilization %
    4. Calculate ATSEM requirements (Maternelle only)

    Returns:
    - LevelDistribution for each academic level
    - Total class counts by cycle
    - Cost breakdown (teacher FTE, ATSEM)
    - Utilization metrics
    """
```

**API Endpoints**: `backend/app/api/v1/configuration.py`
```
GET /api/v1/class-distribution/{budget_version_id}
  → Returns distribution data, cost breakdown, utilization

GET /api/v1/aefe-benchmarks
  → Returns AEFE standard benchmarks for comparison
  → H/E ratios, class size ranges, cost per student targets
```

**Pydantic Schemas**: `backend/app/schemas/configuration.py`
- `ClassDistributionResponse`
- `LevelDistributionData`
- `CostBreakdownData`
- `AEFEBenchmarksResponse`

#### Frontend Components

**New Route**: `frontend/src/routes/configuration/class-distribution.tsx`

Layout:
```
┌──────────────────────────────────────────────┐
│  Budget Version Selector                     │
├──────────────────────────────────────────────┤
│  Summary Cards (Grid 1 md:3)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────┐│
│  │Total Classes│ │Avg Class    │ │ATSEM    ││
│  │     45      │ │Size: 24.5   │ │Needed:10││
│  └─────────────┘ └─────────────┘ └─────────┘│
├──────────────────────────────────────────────┤
│  Charts Section (Grid 2 columns)             │
│  ┌─────────────────────┐ ┌─────────────────┐│
│  │ Distribution Chart  │ │ Cost Breakdown  ││
│  │  (Bar Chart)        │ │ (Stacked Bar)   ││
│  └─────────────────────┘ └─────────────────┘│
│  ┌─────────────────────┐ ┌─────────────────┐│
│  │ AEFE Comparison     │ │ Trend Chart     ││
│  │  (Line Chart)       │ │ (Multi-year)    ││
│  └─────────────────────┘ └─────────────────┘│
├──────────────────────────────────────────────┤
│  [Export PNG] [Export PDF] [Export Excel]    │
└──────────────────────────────────────────────┘
```

**Chart Components**: `frontend/src/components/charts/class-distribution/`
- `ClassDistributionChart.tsx` - Bar chart with utilization colors
- `CostBreakdownChart.tsx` - Stacked bar by cycle
- `AEFEComparisonChart.tsx` - Line chart with benchmark overlay
- `TrendChart.tsx` - Multi-year historical view

**Hooks**: `frontend/src/hooks/api/useConfiguration.ts`
```typescript
export function useClassDistribution(budgetVersionId: string) {
  return useQuery({
    queryKey: ['class-distribution', budgetVersionId],
    queryFn: () => api.getClassDistribution(budgetVersionId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useAEFEBenchmarks() {
  return useQuery({
    queryKey: ['aefe-benchmarks'],
    queryFn: () => api.getAEFEBenchmarks(),
    staleTime: 60 * 60 * 1000, // 1 hour (static data)
  })
}
```

### Testing Requirements

**Backend Tests** (200+ lines):
- `backend/tests/engine/test_class_distribution.py`
  - Test distribution calculation (68 students → 3 classes of 23, 23, 22)
  - Test ATSEM calculation (Maternelle only)
  - Test utilization percentage (85%, 95%, 105%)
  - Test edge cases (zero students, exact multiples)
  - Test cost breakdown accuracy

**API Tests** (100+ lines):
- `backend/tests/api/test_configuration_api.py`
  - Test GET /class-distribution endpoint
  - Test AEFE benchmarks endpoint
  - Test 404 for invalid version ID
  - Test authorization (viewer vs admin)

**Frontend Tests** (50+ lines):
- `frontend/tests/components/charts/ClassDistributionChart.test.tsx`
- `frontend/tests/components/charts/CostBreakdownChart.test.tsx`

**E2E Tests** (50+ lines):
- `frontend/tests/e2e/class-distribution.spec.ts`
  - Navigate to distribution page
  - Verify all 4 charts render with real data
  - Export chart to PNG
  - Verify export file downloaded

### Implementation Estimate

- **Backend**: 2 days (engine + API + tests)
- **Frontend**: 2 days (components + page + hooks)
- **Testing**: 1 day (E2E + integration)
- **Total**: 5 days

### Dependencies
- Existing DHG calculation engine (for FTE estimates)
- Existing enrollment data (Module 7)
- Recharts library (already installed)

---

## Feature 2: Scenario Modeling 🎯

### Overview
What-if analysis tool allowing users to create multiple class size parameter "scenarios" and compare them side-by-side to understand cost, FTE, and capacity impacts.

### Business Value
- **Risk Planning**: Compare conservative vs optimistic sizing strategies
- **Budget Flexibility**: Model multiple budget scenarios before committing
- **Decision Support**: Data-driven parameter selection
- **Cost Optimization**: Identify optimal balance between quality and cost

### Functional Requirements

#### FR-2.1: Scenario Management
- **Create Scenarios**:
  - Name (e.g., "Cost Optimization 2026", "Quality Focus")
  - Description (optional)
  - Scenario type: Conservative, Base, Optimistic, Custom
  - Copy from existing scenario or current parameters

- **Scenario Types**:
  - **Conservative**: Min class sizes closer to lower bounds (higher quality, higher cost)
  - **Base**: Target class sizes (balanced approach)
  - **Optimistic**: Max class sizes closer to upper bounds (lower cost, larger classes)
  - **Custom**: User-defined parameters

- **CRUD Operations**:
  - Create new scenario
  - Edit scenario parameters (AG Grid interface)
  - Copy scenario as template
  - Delete scenario
  - Set scenario as "active" for comparison

#### FR-2.2: Scenario Comparison
- **Side-by-Side Table**:
  - Compare 2-4 scenarios simultaneously
  - Metrics shown:
    - Total classes
    - Average class size
    - Teacher FTE required
    - ATSEM count
    - Total personnel cost (SAR)
    - Cost per student
  - Variance columns:
    - Absolute difference from baseline
    - Percentage change
    - Color-coded (green = savings, red = increase)

- **Comparison Visualizations**:
  - Bar chart: Total cost by scenario
  - Grouped bar chart: FTE breakdown (teachers + ATSEM)
  - Line chart: Class size distribution across levels
  - Waterfall chart: Cost variance from baseline

#### FR-2.3: Impact Analysis
- **Downstream Calculations**:
  - Automatically recalculate class structures
  - Update teacher FTE via DHG engine
  - Calculate revenue impact (if enrollment changes)
  - Project 5-year costs with growth assumptions

- **Sensitivity Analysis**:
  - "What if enrollment increases 10%?"
  - "What if we hire 2 fewer teachers?"
  - Show breaking points (when constraints violated)

### Technical Design

#### Database Schema

**New Tables**:
```sql
-- Scenario headers
CREATE TABLE class_size_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_version_id UUID NOT NULL REFERENCES budget_versions(id),
    scenario_name VARCHAR(100) NOT NULL,
    description TEXT,
    scenario_type VARCHAR(50), -- 'conservative', 'base', 'optimistic', 'custom'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_id UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    updated_by_id UUID REFERENCES users(id),
    CONSTRAINT uk_scenario_name UNIQUE(budget_version_id, scenario_name)
);

-- Scenario parameters (one row per level/cycle per scenario)
CREATE TABLE class_size_scenario_params (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id UUID NOT NULL REFERENCES class_size_scenarios(id) ON DELETE CASCADE,
    level_id UUID REFERENCES academic_levels(id),
    cycle_id UUID REFERENCES academic_cycles(id),
    min_class_size INT NOT NULL CHECK (min_class_size > 0),
    target_class_size INT NOT NULL CHECK (target_class_size > min_class_size),
    max_class_size INT NOT NULL CHECK (max_class_size >= target_class_size),
    notes TEXT,
    CONSTRAINT ck_scenario_param_level_or_cycle CHECK (
        (level_id IS NOT NULL AND cycle_id IS NULL) OR
        (level_id IS NULL AND cycle_id IS NOT NULL)
    ),
    CONSTRAINT uk_scenario_param_level UNIQUE(scenario_id, level_id),
    CONSTRAINT uk_scenario_param_cycle UNIQUE(scenario_id, cycle_id)
);

-- Indexes
CREATE INDEX idx_scenarios_budget_version ON class_size_scenarios(budget_version_id);
CREATE INDEX idx_scenario_params_scenario ON class_size_scenario_params(scenario_id);

-- RLS Policies (same as class_size_params)
ALTER TABLE class_size_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE class_size_scenario_params ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view scenarios in their organization's budget versions
CREATE POLICY scenarios_select_policy ON class_size_scenarios
    FOR SELECT USING (
        budget_version_id IN (
            SELECT id FROM budget_versions
            WHERE organization_id = current_setting('app.current_org_id')::uuid
        )
    );

-- Similar policies for INSERT, UPDATE, DELETE
```

**Migration**: `backend/alembic/versions/20251205_xxxx_class_size_scenarios.py`

#### Backend Components

**Models**: `backend/app/models/configuration.py` (extend existing)
```python
class ClassSizeScenario(Base, VersionedMixin, AuditMixin):
    """Scenario for what-if analysis of class size parameters."""
    __tablename__ = "class_size_scenarios"

    scenario_name = Column(String(100), nullable=False)
    description = Column(Text)
    scenario_type = Column(String(50))  # conservative, base, optimistic, custom
    is_active = Column(Boolean, default=True)

    # Relationships
    parameters = relationship(
        "ClassSizeScenarioParam",
        back_populates="scenario",
        cascade="all, delete-orphan"
    )

class ClassSizeScenarioParam(Base):
    """Individual parameter within a scenario."""
    __tablename__ = "class_size_scenario_params"

    scenario_id = Column(UUID, ForeignKey("class_size_scenarios.id"), nullable=False)
    level_id = Column(UUID, ForeignKey("academic_levels.id"))
    cycle_id = Column(UUID, ForeignKey("academic_cycles.id"))
    min_class_size = Column(Integer, nullable=False)
    target_class_size = Column(Integer, nullable=False)
    max_class_size = Column(Integer, nullable=False)
    notes = Column(Text)

    # Relationships
    scenario = relationship("ClassSizeScenario", back_populates="parameters")
    level = relationship("AcademicLevel")
    cycle = relationship("AcademicCycle")
```

**Calculation Engine**: `backend/app/engine/scenario_comparison/calculator.py`
```python
def compare_scenarios(
    enrollment: EnrollmentData,
    scenarios: List[ScenarioWithParams]
) -> ScenarioComparisonResult:
    """
    Compare multiple scenarios side-by-side.

    For each scenario:
    1. Calculate class counts using distribution engine
    2. Calculate teacher FTE using DHG engine
    3. Calculate ATSEM requirements (Maternelle)
    4. Calculate total personnel costs
    5. Calculate cost per student

    Returns:
    - Metrics table (scenarios × metrics)
    - Variance analysis (vs baseline)
    - Recommended scenario based on optimization goals
    - Constraint violations (if any)
    """
```

**Service**: `backend/app/services/scenario_service.py` (NEW)
```python
class ScenarioService(BaseService):
    """Service for scenario management and comparison."""

    async def create_scenario(self, data: dict) -> ClassSizeScenario:
        """Create new scenario with parameters."""

    async def create_default_scenarios(self, budget_version_id: str):
        """Create 3 default scenarios: Conservative, Base, Optimistic."""

    async def copy_scenario(self, scenario_id: str, new_name: str) -> ClassSizeScenario:
        """Deep copy scenario with all parameters."""

    async def compare_scenarios(self, scenario_ids: List[str]) -> dict:
        """Run scenario comparison calculation."""

    async def calculate_scenario_impact(self, scenario_id: str) -> dict:
        """Calculate downstream impacts (classes, FTE, costs)."""
```

**API Endpoints**: `backend/app/api/v1/configuration.py`
```python
# Scenario CRUD
@router.post("/scenarios", response_model=ScenarioResponse, status_code=201)
async def create_scenario(
    req: ScenarioCreateRequest,
    current_user: UserDep
):
    """Create new class size scenario."""

@router.get("/scenarios/{budget_version_id}", response_model=List[ScenarioResponse])
async def list_scenarios(
    budget_version_id: str,
    current_user: UserDep
):
    """List all scenarios for a budget version."""

@router.get("/scenarios/detail/{scenario_id}", response_model=ScenarioDetailResponse)
async def get_scenario(
    scenario_id: str,
    current_user: UserDep
):
    """Get scenario with all parameters."""

@router.put("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: str,
    req: ScenarioUpdateRequest,
    current_user: ManagerDep
):
    """Update scenario metadata or parameters."""

@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: str,
    current_user: ManagerDep
):
    """Delete scenario and all parameters."""

@router.post("/scenarios/{scenario_id}/copy", response_model=ScenarioResponse)
async def copy_scenario(
    scenario_id: str,
    new_name: str,
    current_user: UserDep
):
    """Create a copy of existing scenario."""

# Comparison
@router.post("/scenarios/compare", response_model=ScenarioComparisonResponse)
async def compare_scenarios(
    req: CompareRequest,
    current_user: UserDep
):
    """
    Compare multiple scenarios side-by-side.

    Request:
    - scenario_ids: List[str] (2-4 scenarios)
    - baseline_scenario_id: Optional[str] (for variance calculation)

    Response:
    - Metrics table
    - Variance analysis
    - Cost breakdown
    - Recommended scenario
    """

@router.post("/scenarios/default/{budget_version_id}")
async def create_default_scenarios(
    budget_version_id: str,
    current_user: ManagerDep
):
    """Create 3 default scenarios for a budget version."""
```

**Schemas**: `backend/app/schemas/configuration.py`
```python
class ScenarioCreateRequest(BaseModel):
    budget_version_id: str
    scenario_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    scenario_type: Literal['conservative', 'base', 'optimistic', 'custom']
    parameters: List[ScenarioParamCreate]

class ScenarioParamCreate(BaseModel):
    level_id: Optional[str] = None
    cycle_id: Optional[str] = None
    min_class_size: int = Field(..., ge=1, le=50)
    target_class_size: int = Field(..., ge=1, le=50)
    max_class_size: int = Field(..., ge=1, le=50)
    notes: Optional[str] = None

    @validator('target_class_size')
    def target_must_exceed_min(cls, v, values):
        if 'min_class_size' in values and v <= values['min_class_size']:
            raise ValueError('target_class_size must be greater than min_class_size')
        return v

class ScenarioResponse(BaseModel):
    id: str
    budget_version_id: str
    scenario_name: str
    description: Optional[str]
    scenario_type: str
    is_active: bool
    created_at: datetime
    created_by_id: str

class ScenarioDetailResponse(ScenarioResponse):
    parameters: List[ScenarioParamResponse]

class CompareRequest(BaseModel):
    scenario_ids: List[str] = Field(..., min_items=2, max_items=4)
    baseline_scenario_id: Optional[str] = None

class ScenarioComparisonResponse(BaseModel):
    scenarios: List[ScenarioMetrics]
    variance_analysis: Optional[VarianceAnalysis]
    recommended_scenario_id: Optional[str]
    warnings: List[str]

class ScenarioMetrics(BaseModel):
    scenario_id: str
    scenario_name: str
    total_classes: int
    avg_class_size: float
    teacher_fte: float
    atsem_count: int
    total_cost_sar: Decimal
    cost_per_student: Decimal
```

#### Frontend Components

**New Route**: `frontend/src/routes/configuration/scenarios.tsx`

Layout:
```
┌──────────────────────────────────────────────┐
│  Budget Version: [Selector ▼]                │
│  [+ Create Scenario] [Compare Selected]      │
├──────────────────────────────────────────────┤
│  Scenarios List (AG Grid)                    │
│  ☑ Name          Type        Classes  Cost   │
│  ☐ Conservative  Conservative   52    4.2M   │
│  ☑ Base Case     Base           48    3.9M   │
│  ☑ Optimistic    Optimistic     44    3.6M   │
│  ☐ Custom 2026   Custom         46    3.7M   │
│                                               │
│  Actions: [Edit] [Copy] [Delete]             │
├──────────────────────────────────────────────┤
│  Selected Scenario: Base Case                │
│  Parameters Editor (AG Grid)                 │
│  Level     Min  Target  Max  Notes           │
│  PS         15    20    25   Maternelle      │
│  MS         15    22    28   Maternelle      │
│  ...                                          │
└──────────────────────────────────────────────┘
```

**Comparison Dialog**: `frontend/src/components/ScenarioComparisonDialog.tsx`

Features:
- Select 2-4 scenarios for comparison
- Side-by-side metrics table
- Variance highlights (color-coded)
- Chart visualizations:
  - Bar chart: Total cost comparison
  - Grouped bar chart: FTE breakdown
  - Line chart: Class size distribution
- Export to Excel/PDF
- "Accept as Budget" action (applies scenario to main budget)

**Hooks**: `frontend/src/hooks/api/useScenarios.ts` (NEW)
```typescript
export function useScenarios(budgetVersionId: string) {
  return useQuery({
    queryKey: ['scenarios', budgetVersionId],
    queryFn: () => api.getScenarios(budgetVersionId),
    staleTime: 2 * 60 * 1000,
  })
}

export function useScenarioDetail(scenarioId: string) {
  return useQuery({
    queryKey: ['scenario-detail', scenarioId],
    queryFn: () => api.getScenarioDetail(scenarioId),
    enabled: !!scenarioId,
  })
}

export function useCreateScenario() {
  return useMutation({
    mutationFn: api.createScenario,
    onSuccess: () => {
      queryClient.invalidateQueries(['scenarios'])
      toast.success('Scenario created successfully')
    },
  })
}

export function useCopyScenario() {
  return useMutation({
    mutationFn: ({ scenarioId, newName }: CopyParams) =>
      api.copyScenario(scenarioId, newName),
    onSuccess: () => {
      queryClient.invalidateQueries(['scenarios'])
      toast.success('Scenario copied successfully')
    },
  })
}

export function useCompareScenarios() {
  return useMutation({
    mutationFn: (scenarioIds: string[]) => api.compareScenarios(scenarioIds),
  })
}
```

### Testing Requirements

**Backend Tests** (400+ lines):
- `backend/tests/models/test_scenario_models.py` - Model validation and constraints
- `backend/tests/engine/test_scenario_comparison.py` - Comparison algorithm
- `backend/tests/services/test_scenario_service.py` - CRUD operations, copy logic
- `backend/tests/api/test_scenario_api.py` - API endpoints, authorization

**Frontend Tests** (150+ lines):
- `frontend/tests/components/ScenarioComparisonDialog.test.tsx`
- `frontend/tests/routes/scenarios.test.tsx`
- `frontend/tests/e2e/scenario-modeling.spec.ts` - Full workflow

### Implementation Estimate

- **Backend**: 3 days (migration + models + engine + service + API + tests)
- **Frontend**: 2 days (components + page + hooks + tests)
- **Testing**: 1 day (E2E + integration)
- **Total**: 6-7 days

### Dependencies
- Feature 1 (Visual Distribution) - for impact visualization
- DHG calculation engine - for FTE estimates
- Enrollment data - for distribution calculations

---

## Feature 3: Optimization Calculator 🤖

### Overview
AI-powered recommendation engine that analyzes enrollment projections and suggests optimal class size parameters to minimize costs while respecting AEFE benchmarks and quality standards.

### Business Value
- **Cost Savings**: Data-driven parameter recommendations can reduce personnel costs by 5-15%
- **Time Savings**: Eliminate manual trial-and-error parameter tuning
- **AEFE Compliance**: Ensure recommendations stay within accreditation standards
- **Objective Decision-Making**: Remove bias from parameter selection

### Functional Requirements

#### FR-3.1: Optimization Goals
Users can select one of three optimization objectives:

1. **Minimize Cost** 🎯
   - Maximize class sizes (within max limits)
   - Reduce teacher FTE required
   - Minimize ATSEM count
   - Target: Lowest total personnel cost

2. **Maximize Quality** 🌟
   - Minimize class sizes (above min limits)
   - Improve student-teacher ratios
   - Increase individual attention
   - Target: Best learning environment (higher cost acceptable)

3. **Balanced Approach** ⚖️
   - Target class sizes (middle of range)
   - Balance cost and quality
   - Maintain AEFE H/E ratios
   - Target: Optimal cost-quality tradeoff

#### FR-3.2: Constraint Configuration
- **AEFE Benchmarks**:
  - H/E ratios by cycle (Secondary: 1.2-1.5)
  - Class size ranges (e.g., Maternelle: 20-25, Élémentaire: 22-28)
  - Cost per student targets (15,000-20,000 SAR)

- **Custom Constraints**:
  - Absolute min/max overrides (e.g., "Never exceed 30 students")
  - Budget ceiling (e.g., "Total cost < 5M SAR")
  - FTE limits (e.g., "Max 60 teachers")
  - Cycle-specific rules (e.g., "Maternelle priority: quality over cost")

#### FR-3.3: Recommendation Output
- **Parameter Recommendations**:
  - Suggested min/target/max for each level
  - Current vs recommended comparison
  - Per-parameter rationale (why this value)

- **Impact Analysis**:
  - **Current State**:
    - Current class counts
    - Current teacher FTE
    - Current total cost
  - **Recommended State**:
    - Projected class counts
    - Projected teacher FTE
    - Projected total cost
  - **Savings**:
    - Absolute savings (SAR)
    - Percentage reduction
    - FTE reduction
    - Cost per student change

- **Confidence Score** (0.0 - 1.0):
  - **High (0.8-1.0)**: Large savings, no constraint violations, stable enrollment
  - **Medium (0.5-0.79)**: Moderate savings, minor violations, enrollment uncertainty
  - **Low (0.0-0.49)**: Small savings, multiple violations, high enrollment volatility

- **Warnings**:
  - AEFE benchmark violations (e.g., "H/E ratio 1.6 exceeds AEFE max 1.5")
  - Quality concerns (e.g., "Class sizes exceed 30 in 3 levels")
  - Cost constraints not met (e.g., "Total cost exceeds budget ceiling")

#### FR-3.4: Recommendation Actions
- **Accept**: Create new scenario from recommendations
- **Adjust**: Modify recommendations and re-run optimization
- **Reject**: Discard recommendations
- **History**: View past optimization runs for reference

### Technical Design

#### Database Schema

**New Table**:
```sql
CREATE TABLE optimization_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_version_id UUID NOT NULL REFERENCES budget_versions(id),
    optimization_goal VARCHAR(50) NOT NULL, -- 'minimize_cost', 'maximize_quality', 'balanced'
    constraints JSONB, -- Constraint configuration
    current_total_cost DECIMAL(15,2),
    recommended_total_cost DECIMAL(15,2),
    estimated_savings DECIMAL(15,2),
    fte_reduction DECIMAL(5,2),
    confidence_score DECIMAL(5,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    recommendations JSONB, -- Array of {level_id, min, target, max, rationale}
    warnings JSONB, -- Array of warning messages
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_id UUID REFERENCES users(id)
);

CREATE INDEX idx_optimization_recommendations_version
    ON optimization_recommendations(budget_version_id);
CREATE INDEX idx_optimization_recommendations_goal
    ON optimization_recommendations(optimization_goal);
```

**Migration**: `backend/alembic/versions/20251205_xxxx_optimization_recommendations.py`

#### Backend Components

**Optimization Algorithm**: `backend/app/engine/optimization/calculator.py`

```python
from enum import Enum
from typing import List, Dict

class OptimizationGoal(str, Enum):
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_QUALITY = "maximize_quality"
    BALANCED = "balanced"

def optimize_class_sizes(
    enrollment: EnrollmentData,
    current_params: List[ClassSizeParam],
    goal: OptimizationGoal,
    constraints: OptimizationConstraints
) -> OptimizationResult:
    """
    Optimize class size parameters based on goal and constraints.

    Algorithm:

    1. For each level, calculate optimal class count:

       if goal == MINIMIZE_COST:
           # Maximize class sizes (fewer classes, fewer teachers)
           optimal_classes = ceil(students / max_class_size)
           recommended_target = students / optimal_classes
           recommended_max = min(max_class_size, recommended_target + 3)

       elif goal == MAXIMIZE_QUALITY:
           # Minimize class sizes (more classes, more teachers)
           reasonable_min = max(min_class_size, 15)  # Never below 15
           optimal_classes = ceil(students / reasonable_min)
           recommended_target = students / optimal_classes
           recommended_min = max(min_class_size, recommended_target - 3)

       elif goal == BALANCED:
           # Target middle of range
           optimal_classes = ceil(students / target_class_size)
           recommended_target = students / optimal_classes
           # Keep current min/max, adjust target

    2. Apply AEFE H/E ratio constraints:

       For secondary levels (Collège + Lycée):
           total_hours = sum(classes × hours_per_subject)
           teacher_fte = total_hours / 18
           h_e_ratio = teacher_fte / total_students

           if h_e_ratio < 1.2:
               # Too few teachers, increase class sizes
               adjust_classes_downward()
           elif h_e_ratio > 1.5:
               # Too many teachers, decrease class sizes
               adjust_classes_upward()

    3. Apply custom constraints:

       if total_cost > budget_ceiling:
           # Iteratively increase class sizes until within budget
           increase_class_sizes_by_priority()

       if teacher_fte > max_fte:
           # Merge classes or increase class sizes
           consolidate_classes()

       for level in levels:
           if level.recommended_max > absolute_max_override:
               level.recommended_max = absolute_max_override

    4. Calculate cost impact:

       current_cost = calculate_dhg_cost(current_params, enrollment)
       recommended_cost = calculate_dhg_cost(recommended_params, enrollment)
       savings = current_cost - recommended_cost
       fte_reduction = current_fte - recommended_fte

    5. Compute confidence score:

       factors = [
           savings_magnitude_factor,      # Large savings → higher confidence
           constraint_violation_factor,   # No violations → higher confidence
           enrollment_stability_factor,   # Stable enrollment → higher confidence
           aefe_compliance_factor,        # Within AEFE benchmarks → higher confidence
       ]

       confidence = weighted_average(factors)

    6. Generate warnings:

       if h_e_ratio > aefe_max:
           warnings.append("H/E ratio exceeds AEFE maximum")

       if any(class_size > 30):
           warnings.append("Some classes exceed 30 students (quality concern)")

       if savings < 0:
           warnings.append("Optimization increases cost (not recommended)")

    Returns:
    - List[ParameterRecommendation] with level-specific suggestions
    - CostImpactAnalysis (current vs recommended)
    - confidence_score: float (0.0-1.0)
    - warnings: List[str]
    """
```

**Models**: `backend/app/engine/optimization/models.py`

```python
class OptimizationConstraints(BaseModel):
    """Constraints for optimization algorithm."""
    aefe_he_ratio_min: float = 1.2
    aefe_he_ratio_max: float = 1.5
    absolute_min_class_size: int = 15
    absolute_max_class_size: int = 35
    budget_ceiling_sar: Optional[Decimal] = None
    max_teacher_fte: Optional[int] = None
    cycle_priorities: Dict[str, str] = {}  # cycle_id → 'cost' | 'quality'

class ParameterRecommendation(BaseModel):
    """Recommendation for a single level."""
    level_id: str
    level_name: str
    current_min: int
    current_target: int
    current_max: int
    recommended_min: int
    recommended_target: int
    recommended_max: int
    rationale: str
    change_magnitude: Literal['minor', 'moderate', 'major']

class CostImpactAnalysis(BaseModel):
    """Cost comparison between current and recommended."""
    current_total_cost: Decimal
    current_teacher_fte: float
    current_atsem_count: int
    recommended_total_cost: Decimal
    recommended_teacher_fte: float
    recommended_atsem_count: int
    estimated_savings: Decimal
    savings_percentage: float
    fte_reduction: float

class OptimizationResult(BaseModel):
    """Complete optimization result."""
    recommendations: List[ParameterRecommendation]
    cost_impact: CostImpactAnalysis
    confidence_score: float = Field(ge=0.0, le=1.0)
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}  # goal, constraints, timestamp
```

**Validators**: `backend/app/engine/optimization/validators.py`

```python
def validate_optimization_input(
    enrollment: EnrollmentData,
    current_params: List[ClassSizeParam],
    constraints: OptimizationConstraints
) -> None:
    """
    Validate inputs before running optimization.

    Checks:
    - Enrollment data completeness (all levels have data)
    - Current params exist for all levels
    - Constraint ranges are reasonable (min < max)
    - AEFE ratios are positive
    """

def validate_aefe_compliance(
    recommended_params: List[ClassSizeParam],
    enrollment: EnrollmentData
) -> List[str]:
    """
    Check if recommended parameters comply with AEFE standards.

    Returns list of compliance warnings.
    """
```

**Service**: `backend/app/services/optimization_service.py` (NEW)

```python
class OptimizationService:
    """Service for class size optimization."""

    async def run_optimization(
        self,
        budget_version_id: str,
        goal: OptimizationGoal,
        constraints: Dict
    ) -> OptimizationResult:
        """
        Run optimization algorithm and save recommendation.

        Steps:
        1. Load current parameters
        2. Load enrollment data
        3. Parse constraints
        4. Run optimization engine
        5. Save recommendation to database
        6. Return result
        """

    async def get_optimization_history(
        self,
        budget_version_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get past optimization runs."""

    async def accept_recommendation(
        self,
        recommendation_id: str,
        scenario_name: str
    ) -> ClassSizeScenario:
        """
        Create new scenario from accepted recommendation.

        Converts OptimizationRecommendation into ClassSizeScenario.
        """
```

**API Endpoints**: `backend/app/api/v1/configuration.py`

```python
@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_class_sizes(
    req: OptimizationRequest,
    current_user: UserDep
):
    """
    Run class size optimization.

    Request:
    - budget_version_id: str
    - optimization_goal: 'minimize_cost' | 'maximize_quality' | 'balanced'
    - constraints: OptimizationConstraints

    Response:
    - recommendation_id: str
    - recommendations: List[ParameterRecommendation]
    - cost_impact: CostImpactAnalysis
    - confidence_score: float
    - warnings: List[str]
    """

@router.post("/optimize/{recommendation_id}/accept", response_model=ScenarioResponse)
async def accept_recommendation(
    recommendation_id: str,
    scenario_name: str,
    current_user: ManagerDep
):
    """
    Accept optimization recommendation and create scenario.

    Creates a new ClassSizeScenario with recommended parameters.
    """

@router.get("/optimization-history/{budget_version_id}", response_model=List[OptimizationHistoryItem])
async def get_optimization_history(
    budget_version_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: UserDep
):
    """
    Get optimization history for a budget version.

    Returns list of past optimization runs with metadata.
    """

@router.delete("/optimize/{recommendation_id}", status_code=204)
async def delete_recommendation(
    recommendation_id: str,
    current_user: ManagerDep
):
    """Delete optimization recommendation."""
```

**Schemas**: `backend/app/schemas/configuration.py`

```python
class OptimizationRequest(BaseModel):
    budget_version_id: str
    optimization_goal: Literal['minimize_cost', 'maximize_quality', 'balanced']
    constraints: OptimizationConstraintsSchema

class OptimizationConstraintsSchema(BaseModel):
    aefe_he_ratio_min: float = Field(default=1.2, ge=0.5, le=2.0)
    aefe_he_ratio_max: float = Field(default=1.5, ge=0.5, le=2.0)
    absolute_min_class_size: int = Field(default=15, ge=10, le=30)
    absolute_max_class_size: int = Field(default=35, ge=20, le=50)
    budget_ceiling_sar: Optional[Decimal] = None
    max_teacher_fte: Optional[int] = None

class OptimizationResponse(BaseModel):
    recommendation_id: str
    recommendations: List[ParameterRecommendationSchema]
    cost_impact: CostImpactAnalysisSchema
    confidence_score: float
    warnings: List[str]

class ParameterRecommendationSchema(BaseModel):
    level_id: str
    level_name: str
    current_min: int
    current_target: int
    current_max: int
    recommended_min: int
    recommended_target: int
    recommended_max: int
    rationale: str
    change_magnitude: Literal['minor', 'moderate', 'major']

class CostImpactAnalysisSchema(BaseModel):
    current_total_cost: Decimal
    current_teacher_fte: float
    recommended_total_cost: Decimal
    recommended_teacher_fte: float
    estimated_savings: Decimal
    savings_percentage: float
    fte_reduction: float
```

#### Frontend Components

**Optimization Dialog**: `frontend/src/components/OptimizationDialog.tsx`

Layout:
```
┌──────────────────────────────────────────────┐
│  Optimize Class Size Parameters              │
│  ┌────────────────────────────────────────┐ │
│  │ Optimization Goal                      │ │
│  │ ○ Minimize Cost (fewer teachers)      │ │
│  │ ● Balanced Approach (recommended)     │ │
│  │ ○ Maximize Quality (smaller classes)  │ │
│  └────────────────────────────────────────┘ │
│                                               │
│  Constraints                                  │
│  ┌────────────────────────────────────────┐ │
│  │ AEFE H/E Ratio: [1.2] to [1.5]       │ │
│  │ Min Class Size: [15]                   │ │
│  │ Max Class Size: [35]                   │ │
│  │ Budget Ceiling: [___] SAR (optional)   │ │
│  └────────────────────────────────────────┘ │
│                                               │
│  [Run Optimization]                           │
├──────────────────────────────────────────────┤
│  Results (if available)                       │
│  ┌────────────────────────────────────────┐ │
│  │ Confidence: 87% (High) ✓              │ │
│  │ Estimated Savings: 320,000 SAR (8.2%) │ │
│  │ FTE Reduction: 3.5 teachers            │ │
│  └────────────────────────────────────────┘ │
│                                               │
│  Recommendations Table                        │
│  Level   Current      Recommended  Change    │
│  PS      15/20/25  →  18/22/28    Minor      │
│  MS      15/22/28  →  18/24/30    Moderate   │
│  ...                                          │
│                                               │
│  Warnings: ⚠️                                 │
│  • 3ème class size 31 exceeds comfort limit  │
│                                               │
│  [Accept as Scenario] [Adjust] [Cancel]      │
└──────────────────────────────────────────────┘
```

**Integration**: Modify `frontend/src/routes/configuration/class-sizes.tsx`

Add button to toolbar:
```tsx
<Button onClick={() => setOptimizationDialogOpen(true)}>
  <Sparkles className="mr-2 h-4 w-4" />
  Optimize Parameters
</Button>
```

**Hooks**: `frontend/src/hooks/api/useOptimization.ts` (NEW)

```typescript
export function useOptimizeClassSizes() {
  return useMutation({
    mutationFn: (req: OptimizationRequest) => api.optimizeClassSizes(req),
    onSuccess: (data) => {
      if (data.confidence_score >= 0.8) {
        toast.success('High-confidence recommendations generated')
      } else if (data.confidence_score >= 0.5) {
        toast.info('Moderate-confidence recommendations generated')
      } else {
        toast.warning('Low-confidence recommendations - review carefully')
      }
    },
  })
}

export function useAcceptRecommendation() {
  return useMutation({
    mutationFn: ({ recommendationId, scenarioName }: AcceptParams) =>
      api.acceptRecommendation(recommendationId, scenarioName),
    onSuccess: () => {
      queryClient.invalidateQueries(['scenarios'])
      toast.success('Scenario created from optimization')
    },
  })
}

export function useOptimizationHistory(budgetVersionId: string) {
  return useQuery({
    queryKey: ['optimization-history', budgetVersionId],
    queryFn: () => api.getOptimizationHistory(budgetVersionId),
    staleTime: 5 * 60 * 1000,
  })
}
```

### Testing Requirements

**Backend Tests** (500+ lines):
- `backend/tests/engine/test_optimization.py`
  - Test minimize_cost algorithm (68 students: 24 target → 27 target, 3 classes → 2.5 classes)
  - Test maximize_quality algorithm (68 students: 24 target → 20 target, 3 classes → 3.4 classes)
  - Test balanced algorithm (maintains target)
  - Test AEFE H/E ratio enforcement (adjust if >1.5 or <1.2)
  - Test budget ceiling constraint (iterative adjustment)
  - Test confidence score calculation
  - Test edge cases: zero students, exact multiples, single class

**API Tests** (200+ lines):
- `backend/tests/api/test_optimization_api.py`
  - Test POST /optimize endpoint
  - Test POST /optimize/{id}/accept
  - Test GET /optimization-history
  - Test authorization (viewer vs manager)
  - Test error handling (invalid constraints)

**Frontend Tests** (100+ lines):
- `frontend/tests/components/OptimizationDialog.test.tsx`
  - Test goal selection
  - Test constraint configuration
  - Test results display
  - Test accept action

**E2E Tests** (50+ lines):
- `frontend/tests/e2e/optimization.spec.ts`
  - Open optimization dialog
  - Select minimize_cost goal
  - Run optimization
  - Verify recommendations displayed
  - Accept as scenario
  - Verify scenario created

### Implementation Estimate

- **Backend**: 4 days (algorithm + engine + service + API + tests)
- **Frontend**: 2 days (dialog + integration + hooks + tests)
- **Testing**: 1 day (E2E + algorithm validation)
- **Total**: 7 days

### Dependencies
- Feature 2 (Scenario Modeling) - for accepting recommendations as scenarios
- DHG calculation engine - for FTE and cost calculations
- Enrollment data - for optimization inputs

---

## Feature 4: Real-time Integration ⚡

### Overview
Real-time synchronization of class size parameter changes, enrollment updates, and collaborative editing with presence awareness using Supabase Realtime.

### Business Value
- **Collaboration**: Multiple users can plan simultaneously
- **Data Consistency**: Instant propagation of enrollment changes to class calculations
- **Conflict Prevention**: Optimistic locking prevents conflicting edits
- **User Experience**: Live updates eliminate manual refreshes

### Functional Requirements

#### FR-4.1: Real-time Parameter Synchronization
- Subscribe to `class_size_params` table changes
- When another user updates parameters:
  - Update React Query cache automatically
  - Show toast notification: "Parameters updated by [user]"
  - Flash updated row in AG Grid (visual feedback)
  - No page reload required

#### FR-4.2: Enrollment Change Propagation
- Subscribe to `enrollment_plans` table changes
- When enrollment data changes:
  - Invalidate dependent calculations (class distribution, scenarios)
  - Trigger automatic recalculation
  - Show notification: "Enrollment updated - recalculating class sizes"
  - Update charts/metrics in real-time

#### FR-4.3: User Presence Indicators
- Show active users viewing/editing the same budget version
- Display avatars with user initials
- Show count: "3 users active"
- Broadcast user activity:
  - "Alice is editing 6ème parameters"
  - "Bob is viewing distribution charts"
  - Idle timeout after 5 minutes

#### FR-4.4: Conflict Detection & Resolution
- **Optimistic Locking**:
  - Each parameter row has a `version` field
  - Updates include version in request
  - Backend checks version before update
  - If version mismatch: HTTP 409 Conflict

- **Conflict Resolution UI**:
  - Show dialog: "This parameter was modified by another user"
  - Options:
    - "Reload and discard my changes"
    - "Force overwrite (requires admin)"
  - Highlight conflicting field in red

#### FR-4.5: Connection Status Indicator
- Show live connection badge:
  - ✅ Green: "Live" (SUBSCRIBED)
  - 🟡 Yellow: "Connecting..." (CONNECTING)
  - 🔴 Red: "Disconnected" (CHANNEL_ERROR)
- Auto-reconnect on connection loss
- Manual reconnect button

### Technical Design

#### Backend Changes (Minimal)

**No new tables required** - Uses existing `planning_cells` writeback infrastructure

**Optional: Event Triggers** (can be skipped)
```sql
-- PostgreSQL trigger to broadcast enrollment changes
CREATE OR REPLACE FUNCTION notify_enrollment_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'enrollment_change',
        json_build_object(
            'budget_version_id', NEW.budget_version_id,
            'level_id', NEW.level_id,
            'student_count', NEW.student_count
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enrollment_update_trigger
AFTER INSERT OR UPDATE ON enrollment_plans
FOR EACH ROW
EXECUTE FUNCTION notify_enrollment_change();
```

**Cache Invalidation** (extend existing): `backend/app/services/cache_invalidator.py`
```python
async def invalidate_class_size_calculations(self, budget_version_id: str):
    """Invalidate cached class size calculations."""
    await self.redis.delete(f"class_distribution:{budget_version_id}")
    await self.redis.delete(f"scenarios:{budget_version_id}")
    await self.redis.delete(f"optimization:{budget_version_id}")
```

#### Frontend Implementation

**Realtime Hook**: `frontend/src/hooks/useRealtimeClassSizes.ts` (NEW)

```typescript
import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { useUser } from '@/hooks/useUser'
import { toast } from 'sonner'

type SubscriptionStatus = 'IDLE' | 'CONNECTING' | 'SUBSCRIBED' | 'CLOSED' | 'CHANNEL_ERROR'

export function useRealtimeClassSizes(budgetVersionId: string) {
  const queryClient = useQueryClient()
  const { user } = useUser()
  const [connectionStatus, setConnectionStatus] = useState<SubscriptionStatus>('IDLE')

  useEffect(() => {
    if (!budgetVersionId || !user) return

    const channel = supabase.channel(`class-sizes:${budgetVersionId}`, {
      config: {
        broadcast: { self: false },
        presence: { key: user.id },
      },
    })

    // Subscribe to class_size_params changes
    channel
      .on('postgres_changes', {
        event: '*', // INSERT, UPDATE, DELETE
        schema: 'public',
        table: 'class_size_params',
        filter: `budget_version_id=eq.${budgetVersionId}`,
      }, (payload) => {
        const { eventType, new: newRecord, old: oldRecord } = payload

        // Update React Query cache
        if (eventType === 'UPDATE') {
          queryClient.setQueryData<ClassSizeParam[]>(
            ['class-size-params', budgetVersionId],
            (oldData) => {
              if (!oldData) return oldData
              return oldData.map((param) =>
                param.id === newRecord.id ? newRecord : param
              )
            }
          )

          // Flash updated row (via DOM manipulation or state)
          flashRow(newRecord.id)

          toast.info('Parameters updated by another user', {
            description: `${oldRecord.level_name || 'Cycle'} parameters modified`
          })
        } else if (eventType === 'INSERT') {
          queryClient.setQueryData<ClassSizeParam[]>(
            ['class-size-params', budgetVersionId],
            (oldData) => [...(oldData || []), newRecord]
          )
          toast.info('New parameters added')
        } else if (eventType === 'DELETE') {
          queryClient.setQueryData<ClassSizeParam[]>(
            ['class-size-params', budgetVersionId],
            (oldData) => oldData?.filter((p) => p.id !== oldRecord.id) || []
          )
          toast.info('Parameters deleted')
        }
      })
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'enrollment_plans',
        filter: `budget_version_id=eq.${budgetVersionId}`,
      }, (payload) => {
        // Invalidate dependent calculations
        queryClient.invalidateQueries(['class-distribution', budgetVersionId])
        queryClient.invalidateQueries(['scenarios', budgetVersionId])
        queryClient.invalidateQueries(['optimization', budgetVersionId])

        toast.info('Enrollment updated - recalculating class sizes', {
          icon: '🔄'
        })
      })
      .subscribe((status) => {
        setConnectionStatus(status as SubscriptionStatus)
      })

    return () => {
      supabase.removeChannel(channel)
    }
  }, [budgetVersionId, user, queryClient])

  const reconnect = () => {
    setConnectionStatus('CONNECTING')
    // Force reconnection by unmounting and remounting
    queryClient.invalidateQueries(['class-size-params', budgetVersionId])
  }

  return { connectionStatus, reconnect }
}

function flashRow(id: string) {
  const row = document.querySelector(`[data-row-id="${id}"]`)
  if (row) {
    row.classList.add('bg-yellow-100')
    setTimeout(() => row.classList.remove('bg-yellow-100'), 2000)
  }
}
```

**Presence Indicator Component**: `frontend/src/components/PresenceIndicator.tsx` (NEW)

```typescript
import { useUserPresence } from '@/hooks/useUserPresence'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Users } from 'lucide-react'

interface Props {
  budgetVersionId: string
}

export function PresenceIndicator({ budgetVersionId }: Props) {
  const { activeUsers, isLoading } = useUserPresence({ budgetVersionId })

  if (isLoading || activeUsers.length === 0) return null

  return (
    <div className="flex items-center gap-2">
      <Users className="h-4 w-4 text-gray-500" />
      <div className="flex -space-x-2">
        {activeUsers.slice(0, 5).map((user) => (
          <Avatar key={user.user_id} className="h-8 w-8 border-2 border-white">
            <AvatarFallback className="bg-blue-500 text-white text-xs">
              {user.user_email[0].toUpperCase()}
            </AvatarFallback>
          </Avatar>
        ))}
        {activeUsers.length > 5 && (
          <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-gray-200 text-xs">
            +{activeUsers.length - 5}
          </div>
        )}
      </div>
      <span className="text-sm text-gray-600">
        {activeUsers.length} {activeUsers.length === 1 ? 'user' : 'users'} active
      </span>
    </div>
  )
}
```

**Connection Status Badge**: `frontend/src/components/ConnectionStatusBadge.tsx` (NEW)

```typescript
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

type Status = 'IDLE' | 'CONNECTING' | 'SUBSCRIBED' | 'CLOSED' | 'CHANNEL_ERROR'

interface Props {
  status: Status
  onReconnect?: () => void
}

export function ConnectionStatusBadge({ status, onReconnect }: Props) {
  const getVariant = () => {
    if (status === 'SUBSCRIBED') return 'success'
    if (status === 'CONNECTING') return 'warning'
    return 'destructive'
  }

  const getLabel = () => {
    if (status === 'SUBSCRIBED') return 'Live'
    if (status === 'CONNECTING') return 'Connecting...'
    return 'Disconnected'
  }

  return (
    <div className="flex items-center gap-2">
      <Badge variant={getVariant()}>
        {getLabel()}
      </Badge>
      {status !== 'SUBSCRIBED' && onReconnect && (
        <Button size="sm" variant="ghost" onClick={onReconnect}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}
```

**Optimistic Locking**: Modify `frontend/src/hooks/api/useConfiguration.ts`

```typescript
export function useUpdateClassSizeParam() {
  return useMutation({
    mutationFn: async ({ id, data, version }: UpdateParams) => {
      // Include version in request
      return api.updateClassSizeParam(id, { ...data, version })
    },
    onError: (error: any) => {
      if (error.status === 409) {
        // Version conflict
        toast.error('Parameter was modified by another user', {
          description: 'Refreshing data...',
          duration: 5000,
        })
        queryClient.invalidateQueries(['class-size-params'])
      } else {
        toast.error('Failed to update parameter')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['class-size-params'])
      toast.success('Parameter updated')
    },
  })
}
```

**Integration with Existing Pages**: Modify the following files to add realtime hooks

1. `frontend/src/routes/configuration/class-sizes.tsx`
```tsx
// Add imports
import { useRealtimeClassSizes } from '@/hooks/useRealtimeClassSizes'
import { PresenceIndicator } from '@/components/PresenceIndicator'
import { ConnectionStatusBadge } from '@/components/ConnectionStatusBadge'

// Inside component
const { connectionStatus, reconnect } = useRealtimeClassSizes(budgetVersionId)

// Add to header
<div className="flex items-center gap-4">
  <PresenceIndicator budgetVersionId={budgetVersionId} />
  <ConnectionStatusBadge status={connectionStatus} onReconnect={reconnect} />
</div>
```

2. `frontend/src/routes/configuration/scenarios.tsx` (similar integration)

3. `frontend/src/routes/configuration/class-distribution.tsx` (similar integration)

### Testing Requirements

**Frontend Tests** (200+ lines):
- `frontend/tests/hooks/useRealtimeClassSizes.test.tsx`
  - Test channel subscription
  - Test parameter update handling
  - Test enrollment change handling
  - Test cache updates
  - Test notifications
  - Test cleanup on unmount

- `frontend/tests/components/PresenceIndicator.test.tsx`
  - Test user list rendering
  - Test avatar display
  - Test overflow (+N users)

- `frontend/tests/components/ConnectionStatusBadge.test.tsx`
  - Test status variants
  - Test reconnect button

**E2E Tests** (100+ lines):
- `frontend/tests/e2e/realtime-collaboration.spec.ts`
  - Open class sizes page in two browsers
  - User 1 edits parameter
  - Verify User 2 sees update
  - Verify toast notification
  - Test conflict detection:
    - User 1 and User 2 edit same row
    - User 1 saves first
    - User 2 saves → 409 Conflict
    - Verify error handling

### Implementation Estimate

- **Backend**: 1 day (optional triggers + cache invalidation)
- **Frontend**: 2 days (hooks + components + integration)
- **Testing**: 1 day (E2E + integration tests)
- **Total**: 4 days

### Dependencies
- Existing Supabase Realtime hooks (useRealtimeSync, useUserPresence)
- Existing optimistic locking in backend (version field)
- TanStack Query for cache management

---

## Implementation Roadmap

### Overall Timeline: 3-4 Weeks

```
Week 1: Visual Distribution
├── Days 1-2: Backend (engine, API, tests)
├── Days 3-4: Frontend (charts, page, hooks)
└── Day 5:    Testing & polish (E2E, docs)

Week 2: Scenario Modeling
├── Days 1-2: Backend (migration, models, service, API)
├── Days 3-4: Frontend (scenario page, comparison dialog)
└── Day 5:    Testing & polish

Week 3: Optimization Calculator
├── Days 1-3: Backend (algorithm, engine, API, tests)
├── Days 4-5: Frontend (optimization dialog, integration)

Week 4: Real-time Integration
├── Days 1-2: Implementation (hooks, components, integration)
├── Days 3-4: Testing (E2E, multi-user scenarios)
└── Day 5:    Final polish & documentation
```

### Phasing Rationale

**Phase 1 (Visual Distribution) First**:
- Lowest risk
- Immediate value for users
- No database changes
- Builds confidence in pattern

**Phase 2 (Scenario Modeling) Second**:
- Depends on visualization for comparison
- Database changes need review
- Foundation for optimization

**Phase 3 (Optimization) Third**:
- Most complex (algorithm design)
- Leverages scenario infrastructure
- Needs scenario management in place

**Phase 4 (Real-time) Last**:
- Polish feature
- Extends existing realtime hooks
- Low risk, high polish

---

## Technical Architecture Summary

### Backend Stack

**Calculation Engines**: 3 new engines
- `class_distribution` - Student distribution calculator
- `scenario_comparison` - Multi-scenario comparison
- `optimization` - Optimization algorithm

**Database**: 3 new tables
- `class_size_scenarios`
- `class_size_scenario_params`
- `optimization_recommendations`

**Services**: 2 new services
- `ScenarioService` - Scenario CRUD + comparison
- `OptimizationService` - Optimization runs

**API Endpoints**: 15+ new endpoints across features

### Frontend Stack

**Components**: 10+ new components
- 4 chart components (distribution, cost, AEFE, trend)
- Scenario management UI
- Comparison dialog
- Optimization dialog
- Presence indicators
- Connection status badge

**Hooks**: 5+ new hooks
- `useClassDistribution`
- `useScenarios`
- `useOptimizeClassSizes`
- `useRealtimeClassSizes`
- `useUserPresence` (extend existing)

**Routes**: 2-3 new pages
- Class distribution page
- Scenario modeling page
- (Optimization integrated into class-sizes page)

### Testing Strategy

**Backend Tests**: 1,000+ lines
- Calculation engine tests (300+ lines per engine)
- API integration tests (200+ lines)
- Service tests (200+ lines)

**Frontend Tests**: 500+ lines
- Component tests (300+ lines)
- E2E tests (200+ lines)

**Coverage Target**: 80%+ (enforced)

---

## Success Metrics

### Quantitative Metrics

**Usage**:
- 80% of planners use Visual Distribution monthly
- 50% of planners create scenarios for comparison
- 30% of planners run optimization at least once

**Performance**:
- <500ms API response time (p95)
- <1s realtime update latency
- <3s chart rendering time

**Quality**:
- 80%+ test coverage (enforced)
- Zero critical bugs in production
- <5% user-reported issues

### Qualitative Metrics

**User Feedback**:
- "Visual distribution saves me 30 minutes per budget cycle"
- "Scenario modeling helps justify budget decisions to the board"
- "Optimization recommendations are surprisingly accurate"
- "Real-time collaboration prevents duplicate work"

**Business Impact**:
- 5-15% cost savings from optimization recommendations
- 50% reduction in parameter tuning time
- Improved AEFE compliance scores
- Better board presentation materials

---

## Dependencies & Prerequisites

### Internal Dependencies

✅ **Already Complete**:
- Module 2 core (100% complete)
- Calculation engines (DHG, Enrollment, Revenue, KPI, Financial Statements)
- Supabase Realtime infrastructure (3 production hooks)
- Recharts library (6 chart components)
- Budget versioning system
- Strategic planning module (scenario infrastructure)

❌ **Not Required** (self-contained):
- No external API integrations
- No new third-party libraries
- No infrastructure changes

### External Dependencies

**None** - All features use existing tech stack

### Team Coordination

**Required Approvals**:
- Database migrations (DBA review)
- API endpoint documentation (API team)
- UX review for new features (design team)

**Documentation Updates**:
- Update `MODULE_02_CLASS_SIZE_PARAMETERS.md`
- Add feature-specific examples
- Create user guides with screenshots

---

## Risks & Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Optimization algorithm complexity | High | Start with simple heuristic, iterate based on feedback |
| Real-time performance at scale | Medium | Use database filters, connection pooling, rate limiting |
| Chart rendering performance | Medium | Lazy loading, virtualization, data sampling for large datasets |
| Database migration issues | High | Thorough testing in staging, rollback plan, gradual rollout |

### User Experience Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Feature overload (too complex) | High | Progressive disclosure, contextual help, guided tours |
| Optimization recommendations rejected | Medium | Explain rationale, show confidence score, allow adjustments |
| Real-time conflicts confusing | Medium | Clear conflict resolution UI, visual feedback, notifications |
| Chart overload (too many charts) | Low | Tab navigation, collapsible sections, export capability |

### Process Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep (add more features) | High | Stick to 4 features, defer enhancements to Phase 2 |
| Timeline overrun | Medium | Weekly checkpoints, buffer time, prioritize features |
| Testing gaps | High | Enforce 80% coverage, E2E tests for critical paths |
| Documentation neglected | Medium | Update docs as features are built, not at the end |

---

## Future Phase 2 Enhancements

After the 4 core features are complete, consider these additional enhancements:

1. **Machine Learning Optimization** (Phase 2.1)
   - Train ML model on historical data
   - Predict optimal parameters based on enrollment trends
   - Confidence intervals for recommendations

2. **Monte Carlo Simulation** (Phase 2.2)
   - Probabilistic enrollment scenarios
   - Risk analysis (best case / worst case)
   - Sensitivity analysis (which variables matter most)

3. **Collaborative Annotations** (Phase 2.3)
   - Comment threads on parameters
   - Change justifications
   - Approval workflows

4. **Advanced Visualizations** (Phase 2.4)
   - Heat maps (class size by level × year)
   - Sankey diagrams (enrollment flow)
   - Interactive 3D charts

5. **Scenario Templates** (Phase 2.5)
   - Save/load scenario presets
   - Share templates across organizations
   - Template marketplace

6. **Export Enhancements** (Phase 2.6)
   - PowerPoint export with charts
   - Interactive HTML reports
   - Scheduled PDF email delivery

---

## Conclusion

These four advanced features will transform Module 2 from a parameter management tool into a **strategic planning platform**. By leveraging existing infrastructure (calculation engines, Supabase Realtime, Recharts), we minimize risk while maximizing value.

**Key Success Factors**:
1. Phased implementation (reduce risk)
2. Comprehensive testing (80%+ coverage)
3. User feedback loops (iterate based on usage)
4. Clear documentation (enable self-service)

**Next Steps**:
1. Review and approve this plan
2. Schedule kickoff meeting
3. Begin Phase 1 (Visual Distribution)
4. Weekly progress reviews

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-05 | Claude Code | Initial document - all 4 features planned |

---

*End of Future Enhancements Document*
