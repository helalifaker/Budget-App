# EFIR Budget Planning - App Navigation Structure

## Overview

This document defines the **persona-centric navigation structure** for the EFIR Budget Planning Application. The goal is to organize the app so that each department/persona (HR, Finance, Academic) has their own logical workspace with all relevant tools and configurations.

---

## Design Principles

1. **Persona-Centric**: Each major section serves a specific user persona
2. **Self-Contained Modules**: Each module contains both working views AND configuration
3. **Logical Data Flow**: Navigation follows the natural planning flow (Enrollment → Workforce → Finance)
4. **Discoverability**: Related features are grouped together, not scattered

---

## Navigation Structure

### Current Structure (Before Migration)
```
/command-center        → Dashboard
/configuration/        → All configuration in one place
├── class-sizes
├── subject-hours
├── teacher-costs
├── fees
└── versions
/planning/             → Planning modules
├── enrollment
├── classes
├── dhg
├── revenue
├── costs
└── capex
/consolidation/        → Budget consolidation
/analysis/             → KPIs, dashboards
/strategic/            → 5-year planning
```

### Target Structure (After Migration)
```
📊 COMMAND CENTER (/command-center)
   └── Dashboard with KPIs, quick actions, approvals

📚 ENROLLMENT (/enrollment)
   ├── planning              → Student enrollment projections
   ├── class-structure       → Class formation
   └── settings/
       ├── class-sizes       → Min/max/target per level
       └── academic-levels   → Level definitions

👥 WORKFORCE (/workforce)                    ← PHASE 1 (Current Implementation)
   ├── employees             → Employee registry (Base 100 + Planned)
   ├── salaries              → KSA salary & EOS management
   ├── aefe-positions        → AEFE position allocation
   ├── dhg/
   │   ├── planning          → DHG hours calculation
   │   ├── requirements      → FTE requirements
   │   └── gap-analysis      → TRMD + Create Placeholder
   └── settings/
       ├── subject-hours     → Hours per subject per level
       ├── cost-parameters   → Category defaults
       └── hsa-rates         → Overtime configuration

💰 FINANCE (/finance)
   ├── revenue/
   │   ├── projections       → Revenue forecasts
   │   └── settings/
   │       └── fee-structure → Tuition, registration, discounts
   ├── costs/
   │   ├── personnel         → Personnel costs (from DHG)
   │   ├── operational       → Operating costs
   │   └── capex             → Capital expenditure
   ├── consolidation/
   │   ├── budget            → P&L view
   │   └── versions          → Version management
   └── statements/
       ├── pcg               → French PCG format
       └── ifrs              → IFRS format

📈 ANALYSIS (/analysis)
   ├── kpis                  → Key Performance Indicators
   ├── dashboards            → Visual dashboards
   └── variance              → Budget vs Actual

🎯 STRATEGIC (/strategic)
   └── five-year-plan        → Multi-year projections

⚙️ ADMINISTRATION (/admin)
   ├── organization          → School settings
   ├── users                 → User management
   └── reference-data        → Subjects, cycles, categories
```

---

## User Personas & Their Modules

| Persona | Primary Module | What They Find |
|---------|----------------|----------------|
| **HR Manager** | `/workforce/` | Employees, salaries, EOS, AEFE positions, DHG |
| **Academic Director** | `/enrollment/` | Student planning, class structure, levels |
| **Finance Director** | `/finance/` | Revenue, costs, consolidation, statements |
| **School Director** | `/command-center/` | Dashboard, KPIs, approvals |
| **IT Admin** | `/admin/` | System settings, users, reference data |

---

## Data Flow Between Modules

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PLANNING DATA FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

  ENROLLMENT           WORKFORCE              FINANCE
  ──────────────────────────────────────────────────────────────────►

  1. Students     →    2. Classes      →    3. DHG Hours
     projections         formed              calculated
                                                 │
                                                 ▼
                                            4. Teacher FTE
                                               required
                                                 │
                                                 ▼
                                            5. Gap Analysis
                                               (TRMD)
                                                 │
                         ┌───────────────────────┴───────────────────────┐
                         │                                               │
                         ▼                                               ▼
                    6. Current          vs              7. Required
                       Staff                               Staff
                         │                                   │
                         └───────────────┬───────────────────┘
                                         │
                                         ▼
                                    8. Deficit/Surplus
                                         │
                                         ▼
                                    9. Create Placeholder
                                       (if deficit)
                                         │
                                         ▼
                                   10. Personnel Costs
                                         │
                                         ▼
                                   11. Budget Consolidation
                                         │
                                         ▼
                                   12. Financial Statements
```

---

## Module Ownership

### `/workforce/` Module (Phase 1 - Current)

**Owner**: HR Manager

**Contains**:
- Employee registry (all staff types)
- Salary management (KSA compliance)
- EOS provision tracking
- AEFE position management
- DHG planning and gap analysis
- Subject hours configuration

**Key Features**:
- "Base 100" vs "Planned" employee distinction
- Auto-generated employee codes (EMP001, EMP002...)
- KSA labor law compliance (EOS, GOSI)
- AEFE PRRD tracking (24 detached + 4 funded)
- Create placeholder from DHG gap with validation

### `/enrollment/` Module (Phase 2 - Future)

**Owner**: Academic Director

**Contains**:
- Student enrollment projections
- Class structure formation
- Class size configuration
- Academic level management

### `/finance/` Module (Phase 3 - Future)

**Owner**: Finance Director

**Contains**:
- Revenue planning
- Cost planning (personnel, operational, CapEx)
- Budget consolidation
- Financial statements (PCG, IFRS)
- Fee structure configuration

### `/analysis/` Module (Shared)

**Owner**: Management Team

**Contains**:
- KPI dashboard
- Variance analysis
- Custom reports

### `/admin/` Module

**Owner**: IT Administrator

**Contains**:
- Organization settings
- User management
- Reference data (subjects, cycles, categories)

---

## Migration Plan

### Phase 1: Workforce Module (Current)
- Build new `/workforce/` structure
- Move DHG-related pages
- Move subject hours configuration
- Add employee management
- Keep existing pages working during migration

### Phase 2: Enrollment Module
- Create `/enrollment/` structure
- Migrate enrollment planning
- Migrate class structure
- Move class sizes configuration

### Phase 3: Finance Module
- Create `/finance/` structure
- Migrate revenue planning
- Migrate cost planning
- Migrate consolidation
- Migrate financial statements
- Move fee structure configuration

### Phase 4: Cleanup
- Remove old `/configuration/` routes (after migration)
- Update all cross-references
- Update documentation

---

## Sidebar Navigation Design

```tsx
// EnhancedSidebar.tsx structure

const navigationItems = [
  {
    title: "Command Center",
    icon: LayoutDashboard,
    href: "/command-center",
  },
  {
    title: "Enrollment",
    icon: GraduationCap,
    children: [
      { title: "Planning", href: "/enrollment/planning" },
      { title: "Class Structure", href: "/enrollment/class-structure" },
      { title: "Settings", href: "/enrollment/settings" },
    ],
  },
  {
    title: "Workforce",
    icon: Users,
    children: [
      { title: "Employees", href: "/workforce/employees" },
      { title: "Salaries & EOS", href: "/workforce/salaries" },
      { title: "AEFE Positions", href: "/workforce/aefe-positions" },
      {
        title: "DHG",
        children: [
          { title: "Planning", href: "/workforce/dhg/planning" },
          { title: "Requirements", href: "/workforce/dhg/requirements" },
          { title: "Gap Analysis", href: "/workforce/dhg/gap-analysis" },
        ],
      },
      { title: "Settings", href: "/workforce/settings" },
    ],
  },
  {
    title: "Finance",
    icon: DollarSign,
    children: [
      { title: "Revenue", href: "/finance/revenue" },
      { title: "Costs", href: "/finance/costs" },
      { title: "Consolidation", href: "/finance/consolidation" },
      { title: "Statements", href: "/finance/statements" },
    ],
  },
  {
    title: "Analysis",
    icon: BarChart3,
    children: [
      { title: "KPIs", href: "/analysis/kpis" },
      { title: "Dashboards", href: "/analysis/dashboards" },
      { title: "Variance", href: "/analysis/variance" },
    ],
  },
  {
    title: "Strategic",
    icon: Target,
    href: "/strategic/five-year-plan",
  },
  {
    title: "Administration",
    icon: Settings,
    children: [
      { title: "Organization", href: "/admin/organization" },
      { title: "Users", href: "/admin/users" },
      { title: "Reference Data", href: "/admin/reference-data" },
    ],
  },
];
```

---

## URL Conventions

| Pattern | Example | Use |
|---------|---------|-----|
| `/{module}/` | `/workforce/` | Module home/overview |
| `/{module}/{feature}` | `/workforce/employees` | Main feature page |
| `/{module}/{feature}/{sub}` | `/workforce/dhg/planning` | Sub-feature |
| `/{module}/settings/` | `/workforce/settings/` | Module configuration |
| `/{module}/settings/{config}` | `/workforce/settings/subject-hours` | Specific config |

---

## Backward Compatibility

During migration, we maintain backward compatibility:

1. **Old routes still work** - Redirects to new locations
2. **Gradual migration** - One module at a time
3. **Feature flags** - Can toggle between old/new navigation
4. **Documentation** - Clear mapping of old → new routes

### Redirect Rules (After Migration)

```
/configuration/class-sizes     → /enrollment/settings/class-sizes
/configuration/subject-hours   → /workforce/settings/subject-hours
/configuration/teacher-costs   → /workforce/employees (or salaries)
/configuration/fees            → /finance/settings/fee-structure
/planning/enrollment           → /enrollment/planning
/planning/classes              → /enrollment/class-structure
/planning/dhg                  → /workforce/dhg/planning
/planning/revenue              → /finance/revenue
/planning/costs                → /finance/costs
```

---

## Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-12-06 | 1.0 | Claude | Initial version - Workforce module design |

---

## Related Documents

- [Implementation Plan](/Users/fakerhelali/.claude/plans/delegated-moseying-anchor.md)
- [Module 08: DHG Workforce Planning](docs/MODULES/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md)
- [Module 11: Cost Planning](docs/MODULES/MODULE_11_COST_PLANNING.md)
