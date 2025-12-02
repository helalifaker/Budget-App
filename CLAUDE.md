# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **EFIR School Budget Planning Application** - an integrated planning system for École Française Internationale de Riyad (EFIR), a French international school in Saudi Arabia operating under AEFE (Agence pour l'enseignement français à l'étranger) guidelines.

The application provides workforce planning through annual budget and 5-year strategic planning, built around the French education system's DHG (Dotation Horaire Globale) methodology.

## Technology Stack

**Version:** PRD v1.2 (November 2025) - Latest stable versions for maximum performance and developer experience.

### Frontend
- **Framework**: React 19.2.0 (with Server Components, Actions, Activity API)
- **Language**: TypeScript 5.9.x (deferred imports, enhanced type narrowing)
- **Build Tool**: Vite 7.2.x (Environment API, ESM-only, Baseline browser targeting)
- **Styling**: Tailwind CSS 4.1.x (with @tailwindcss/vite plugin, 5x faster builds)
- **Components**: shadcn/ui (Latest, TW v4 compatible, data-slot attributes, OKLCH colors)
- **Data Grid**: AG Grid Community 34.3.x (MIT license) - Enterprise-grade spreadsheet interface
- **Charts**: Recharts 2.15.x (React charting library)

**AG Grid Community Features** (Free - MIT License):
- Sorting, filtering, pagination, cell editing out-of-the-box
- Custom components and cell renderers for specialized displays
- New Theming API with themeQuartz for modern styling
- React 19.2 full support with native component rendering
- High performance with virtualized rendering for large datasets
- No third-party dependencies, battle-tested (J.P. Morgan, MongoDB, NASA)

### Backend
- **Runtime**: Python 3.12+ (improved performance and error messages)
- **API Framework**: FastAPI 0.123.x (high-performance async with Pydantic v2)
- **Validation**: Pydantic 2.12+ (data validation with JSON Schema support)
- **Server**: Uvicorn 0.34+ (ASGI server for production deployment)

### Database & Infrastructure
- **Database**: PostgreSQL 17.x (via Supabase)
- **Backend-as-a-Service**: Supabase (Auth, Realtime, Edge Functions)
- **Security**: Row Level Security (RLS)
- **Real-time**: Supabase Realtime (WebSocket subscriptions for auto-save and collaboration)
- **Auth**: Supabase Auth (role-based access control)

### Development Tools & Quality Assurance

**Best-in-class tooling for code quality, consistency, and developer experience:**

**Frontend Tools:**
- **ESLint** 9.x - Code linting with flat config (eslint.config.js)
- **Prettier** 3.4.x - Opinionated code formatting for consistency
- **Husky** 9.x - Git hooks for pre-commit validation
- **lint-staged** 15.x - Run linters on staged files only
- **Vitest** 3.x - Vite-native testing framework with instant HMR
- **Playwright** 1.49.x - End-to-end testing across browsers
- **@typescript-eslint** 8.x - TypeScript-specific ESLint rules
- **eslint-plugin-react-hooks** 5.x - React hooks linting rules
- **eslint-plugin-tailwindcss** 3.x - Tailwind CSS class ordering and best practices

**Backend Tools:**
- **Ruff** 0.8.x - Python linter (10-100x faster than Flake8)
- **mypy** 1.14.x - Python static type checker
- **pytest** 8.x - Python testing framework

**Pre-commit Hooks** (via Husky + lint-staged):
1. ESLint: Check for code quality issues
2. Prettier: Auto-format staged files
3. TypeScript: Type check with `tsc --noEmit`
4. Vitest: Run affected tests

**CI/CD Pipeline:**
1. Lint check (ESLint + Ruff)
2. Type check (TypeScript + mypy)
3. Unit tests (Vitest + pytest)
4. E2E tests (Playwright)
5. Build verification

### Integration Points
- **Odoo**: Accounting system (for actuals import via API)
- **Skolengo**: Student information system (export/import for enrollment data)
- **AEFE**: Position data (manual/export)

## Key Architectural Concepts

### Module-Based Architecture

The application is organized into 18 modules across 5 layers:

1. **Configuration Layer (Modules 1-6)**: Master data and parameters
   - System Configuration, Class Size Parameters, Subject Hours, Teacher Costs, Fee Structure, Timetable Constraints

2. **Planning Layer (Modules 7-12)**: Operational planning
   - Enrollment Planning → Class Structure → DHG (Workforce) → Revenue/Cost/CapEx Planning
   - **Critical Flow**: Enrollment projections drive class formation, which drives DHG hours calculation, which determines teacher FTE requirements

3. **Consolidation Layer (Modules 13-14)**: Financial integration
   - Budget Consolidation with version management and approval workflow
   - Financial Statements (French PCG + IFRS formats)

4. **Analysis Layer (Modules 15-17)**: Monitoring and reporting
   - Statistical Analysis (KPIs), Dashboards, Budget vs Actual

5. **Strategic Layer (Module 18)**: Multi-year planning
   - 5-Year Strategic Plan with scenario modeling

### DHG (Dotation Horaire Globale) Methodology

**This is the core calculation engine** for secondary teacher workforce planning:

```
Total Subject Hours = Σ(Number of Classes × Hours per Subject per Level)
Teacher FTE Required = Total Subject Hours ÷ Standard Hours (18h/week for secondary)
```

**Gap Analysis (TRMD)**:
- Besoins (Needs): Hours required from DHG
- Available: AEFE positions + Local staff positions
- Deficit: Filled by recruitment or HSA (overtime, max 2-4 hours per teacher)

### Data Flow Pattern

```
Enrollment → Class Structure → DHG Hours → Teacher FTE → Personnel Costs
     ↓              ↓              ↓             ↓              ↓
  Revenue    Facility Needs   Curriculum    AEFE/Local    Cost Planning
     ↓              ↓              ↓             ↓              ↓
     └──────────────┴──────────────┴─────────────┴──────────────┘
                                  ↓
                       Budget Consolidation
                                  ↓
                       Financial Statements
```

**Key Principle**: Enrollment is the primary driver. Changes cascade through all dependent calculations.

### Currency and Accounting

- **Primary Currency**: SAR (Saudi Riyal)
- **Accounting Standard**: French Plan Comptable Général (PCG) with IFRS mapping
- **Revenue Recognition**: Trimester-based (T1: 40%, T2: 30%, T3: 30%)
- **Account Code Pattern**:
  - 60xxx-68xxx: Expenses
  - 70xxx-77xxx: Revenue
  - Example: 64110 = Teaching salaries, 70110 = Tuition T1

### French Education System Specifics

**Academic Structure**:
- **Maternelle** (Preschool): PS, MS, GS
- **Élémentaire** (Elementary): CP, CE1, CE2, CM1, CM2
- **Collège** (Middle School): 6ème, 5ème, 4ème, 3ème
- **Lycée** (High School): 2nde, 1ère, Terminale

**Staff Categories**:
- **AEFE Detached Teachers**: French nationals, school pays PRRD contribution (~41,863 EUR/teacher)
- **AEFE Funded Teachers**: Fully funded by AEFE (no school cost)
- **Local Teachers**: Recruited locally, paid in SAR
- **ATSEM**: Classroom assistants for Maternelle (1 per class)

**Teaching Hours**:
- Primary: 24 hours/week
- Secondary: 18 hours/week
- HSA (Overtime): Max 2-4 hours/week per teacher

### Budget Period Structure

- **Period 1**: January-June (current academic year continuation)
- **Summer**: July-August (minimal operations)
- **Period 2**: September-December (new academic year start)
- **Fiscal Year**: January-December
- **Academic Year**: September-June

## Domain-Specific Terminology

**Critical Acronyms**:
- **DHG**: Dotation Horaire Globale (Global Hours Allocation)
- **H/E**: Heures/Élève (Hours per Student ratio - used for staffing benchmarks)
- **E/D**: Élèves/Division (Students per Class)
- **TRMD**: Tableau de Répartition des Moyens par Discipline (Gap Analysis)
- **HSA**: Heures Supplémentaires Annuelles (Annual Overtime Hours)
- **PRRD**: Participation à la Rémunération des Résidents Détachés (School contribution to AEFE teacher costs)
- **DAI**: Droit Annuel d'Inscription (Annual Enrollment Fee)
- **ATSEM**: Agent Territorial Spécialisé des Écoles Maternelles (Preschool Assistant)

## Implementation Approach

### Development Phases

The project should be developed in 6 phases:

1. **Phase 1 (Weeks 1-4)**: Foundation - System config, database schema, class size & subject hours configuration
2. **Phase 2 (Weeks 5-10)**: Core Planning - Enrollment, DHG workforce planning, fee structure
3. **Phase 3 (Weeks 11-16)**: Financial - Revenue, cost, CapEx, budget consolidation
4. **Phase 4 (Weeks 17-22)**: Reporting - Financial statements, KPIs, dashboards
5. **Phase 5 (Weeks 23-28)**: Advanced - Budget vs Actual, forecast revision, 5-year planning
6. **Phase 6 (Weeks 29-30)**: Integration & Go-Live

### Key Design Principles

1. **Driver-Based Calculations**: Most costs should be automatically calculated from drivers (enrollment, FTE, square meters, etc.)
2. **Version Management**: Support Working, Submitted, Approved, Forecast, and Superseded budget versions
3. **Real-time Updates**: Changes to enrollment should trigger immediate recalculation of dependent modules
4. **Audit Trail**: All parameter changes and calculations must be auditable
5. **Constraint Validation**: Enforce business rules (e.g., max class size, HSA limits, account code patterns)

## EFIR Development Standards

This project follows the **EFIR Development Standards System** - a comprehensive framework ensuring consistent, high-quality development. All code must adhere to the **4 Non-Negotiables**:

### 1. Complete Implementation
- ✅ All requirements implemented (no shortcuts, no deferred work)
- ✅ No TODO comments in production code
- ✅ All edge cases handled
- ✅ Error cases properly managed
- ❌ No placeholders or incomplete features
- ❌ No "we'll fix this later" comments

### 2. Best Practices
- ✅ Type-safe code (TypeScript strict mode, Python type hints)
- ✅ Organized structure following SOLID principles
- ✅ Well-tested with 80%+ coverage minimum
- ✅ Clean code (no console.log, no debugging statements)
- ✅ Proper error handling with user-friendly messages
- ❌ No `any` types in TypeScript
- ❌ No untyped Python functions

### 3. Documentation
- ✅ .md file created/updated for every module
- ✅ Formulas explained with mathematical notation
- ✅ Business rules clearly enumerated
- ✅ Real EFIR data examples included
- ✅ Version history tracked
- ✅ API endpoints documented
- ❌ No undocumented features
- ❌ No missing examples

### 4. Review & Testing
- ✅ Self-reviewed against development checklist
- ✅ All tests pass (Vitest + pytest)
- ✅ Linting passes (ESLint + Ruff)
- ✅ Type checking passes (tsc --noEmit + mypy)
- ✅ 80%+ test coverage achieved
- ✅ E2E tests for critical user flows (Playwright)
- ❌ No skipped tests without justification
- ❌ No disabled linting rules without documentation

### Code Quality Standards

**TypeScript/React:**
```typescript
// ✅ GOOD: Type-safe, well-structured
interface EnrollmentData {
  levelId: string;
  nationality: 'French' | 'Saudi' | 'Other';
  studentCount: number;
}

function calculateClasses(enrollment: EnrollmentData, params: ClassSizeParams): number {
  // Implementation with error handling
}

// ❌ BAD: Using 'any', no error handling
function calculateClasses(enrollment: any) {
  return enrollment.students / 25;
}
```

**Python/FastAPI:**
```python
# ✅ GOOD: Type hints, validation, error handling
from pydantic import BaseModel, Field

class EnrollmentData(BaseModel):
    level_id: str = Field(..., description="Academic level identifier")
    nationality: Literal['French', 'Saudi', 'Other']
    student_count: int = Field(gt=0, description="Number of students")

def calculate_classes(enrollment: EnrollmentData, params: ClassSizeParams) -> int:
    """Calculate number of classes needed for enrollment."""
    # Implementation with proper error handling

# ❌ BAD: No types, no validation
def calculate_classes(enrollment):
    return enrollment['students'] / 25
```

### Testing Requirements

**Unit Tests (80%+ Coverage Minimum):**
- Test all business logic functions
- Test edge cases (empty data, maximum values, invalid inputs)
- Test error conditions
- Use real EFIR data for test cases

**Integration Tests:**
- Test module interactions
- Test database operations
- Test API endpoints

**E2E Tests (Critical Flows):**
- Enrollment → Class Structure → DHG calculation
- Revenue calculation with different fee structures
- Budget consolidation workflow

### Documentation Standards

Every module must have a corresponding .md file in `docs/MODULES/` containing:

1. **Overview**: Purpose and context
2. **Inputs**: Data structures with types
3. **Calculations**: Formulas with mathematical notation and examples
4. **Business Rules**: Enumerated list with validation logic
5. **Outputs**: Return values and side effects
6. **Examples**: Using real EFIR data
7. **Testing**: Test scenarios covered
8. **Version History**: Changes and dates

**Example Documentation Structure:**
```markdown
# Module 8: Teacher Workforce Planning (DHG)

## Overview
Calculates teacher requirements using DHG (Dotation Horaire Globale) methodology...

## Inputs
- `classStructure`: Map<LevelId, ClassCount>
- `subjectHoursMatrix`: Map<(SubjectId, LevelId), Hours>
- `teacherCostParams`: TeacherCostParameters

## Calculations

### Secondary Workforce (DHG Hours-Based Model)
```
Total Hours = Σ(classes × hours_per_subject_per_level)
Simple FTE = Total Hours ÷ 18 (standard teaching hours)
```

**Example (Mathématiques in Collège):**
```
Classes: 6ème(6) + 5ème(6) + 4ème(5) + 3ème(4) = 21 classes
Hours: (6×4.5) + (6×3.5) + (5×3.5) + (4×3.5) = 96 hours/week
FTE: 96 ÷ 18 = 5.33 → 6 teachers needed
```

## Business Rules
1. Standard hours: Primary = 24h/week, Secondary = 18h/week
2. HSA (overtime) capped at 2-4 hours per teacher
3. AEFE costs calculated in EUR, then converted to SAR
...
```

### Red Flags (Work is NOT Complete If You See)

🚨 **Stop and fix immediately:**
- [ ] TODO or FIXME comments in code
- [ ] console.log() or print() debugging statements
- [ ] Type `any` in TypeScript
- [ ] Unhandled error cases
- [ ] Tests not passing
- [ ] Coverage below 80%
- [ ] Linting failures
- [ ] Type checking failures
- [ ] .md documentation not updated
- [ ] No examples with real EFIR data
- [ ] Incomplete requirements
- [ ] Skipped edge cases

### Definition of Done

A feature/module is **DONE** when:
1. ✅ All requirements from specification implemented
2. ✅ Code follows best practices (type-safe, organized, clean)
3. ✅ Tests written and passing (80%+ coverage)
4. ✅ Linting passes (ESLint/Ruff)
5. ✅ Type checking passes (tsc/mypy)
6. ✅ Documentation updated (.md file with examples)
7. ✅ Self-reviewed against checklist
8. ✅ No red flags present
9. ✅ Ready for production deployment

**Quality takes time. No shortcuts. Complete implementation required.**

### Business Rules to Enforce

**Class Formation**:
- `min_class_size < target_class_size ≤ max_class_size`
- Level-specific parameters override cycle defaults
- Maternelle requires ATSEM (1 per class)

**Workforce Planning**:
- Secondary teachers: 18h standard, max 22h with HSA
- Primary teachers: 24h standard
- AEFE costs calculated in EUR, then converted to SAR
- HSA capped at configured maximum per teacher

**Financial**:
- Sibling discount (25% on tuition for 3rd+ child) not applicable to DAI or registration fees
- Fee nationality categories: French (TTC), Saudi (HT), Other (TTC)
- Total enrollment cannot exceed capacity (~1,875 students)

## Reference Data Location

Key reference documents (to be migrated into the application):

**Core Specifications:**
- `EFIR_Module_Technical_Specification.md`: Complete module specifications and formulas (18 modules)
- `EFIR_Data_Summary_v2.md`: Historical enrollment, fee structure, personnel data
- `EFIR_Workforce_Planning_Logic.md`: DHG methodology, H/E ratio tables, AEFE cost structure

**Product Requirements:**
- `EFIR_Budget_App_PRD_v1_2.md`: Product requirements, technology stack (PRD v1.2 - November 2025)
- `EFIR_Budget_Planning_Requirements_v1.2.md`: Functional requirements, EFIR school profile, glossary

## Common Development Commands

### Frontend Commands

**Setup & Development:**
```bash
cd frontend
pnpm install                    # Install dependencies (uses pnpm workspaces)
pnpm dev                        # Start Vite dev server (http://localhost:5173)
pnpm build                      # Build for production
pnpm preview                    # Preview production build locally
```

**Testing & Quality:**
```bash
pnpm test                       # Run Vitest (watch mode)
pnpm test:ui                    # Vitest with UI dashboard
pnpm test:e2e                   # Run Playwright E2E tests
pnpm test:e2e:ui                # Playwright with UI
pnpm test:e2e:headed            # Playwright with browser visible
pnpm test:e2e:debug             # Playwright debug mode
pnpm test:all                   # Run all tests (unit + E2E)
pnpm lint                       # Run ESLint
pnpm lint:fix                   # Auto-fix ESLint issues
pnpm format                     # Format code with Prettier
pnpm typecheck                  # TypeScript type checking
```

### Backend Commands

**Setup & Development:**
```bash
cd backend
python3 -m venv .venv           # Create virtual environment
source .venv/bin/activate       # Activate venv (Linux/Mac)
# OR: .venv\Scripts\activate    # Windows
pip install -e .[dev]           # Install with dev dependencies
uvicorn app.main:app --reload   # Start FastAPI server (http://localhost:8000)
```

**Testing & Quality:**
```bash
pytest                          # Run pytest (watch mode)
pytest --cov=app                # Run with coverage report
pytest -v                       # Verbose output
pytest tests/engine/            # Run specific test directory
pytest -k test_dhg              # Run tests matching pattern
.venv/bin/ruff check .          # Lint with Ruff
.venv/bin/ruff check . --fix    # Auto-fix Ruff issues
.venv/bin/mypy .                # Type check with mypy
```

**Database & Migrations:**
```bash
alembic upgrade head            # Apply all pending migrations
alembic downgrade -1            # Rollback last migration
alembic current                 # Show current revision
alembic history                 # Show migration history
alembic revision --autogenerate -m "description"  # Create new migration
```

### Monorepo Commands

**From project root:**
```bash
pnpm install                    # Install all workspaces
pnpm -r build                   # Build all workspaces
pnpm -r test                    # Test all workspaces
pnpm run lint                   # Lint frontend only
pnpm run format                 # Format frontend only
```

## Development Notes

- **Preserve DHG Logic**: The existing DHG calculation methodology is proven and should be implemented exactly as documented
- **H/E Ratio Tables**: Import these as reference data for validation (Module 8 in spec)
- **AG Grid Community Integration**: Grid-based data entry is critical for user adoption - users are familiar with Excel-like interfaces. AG Grid Community (MIT license) provides enterprise-grade spreadsheet functionality with sorting, filtering, cell editing, and custom renderers
- **Scenario Modeling**: Support side-by-side comparison of budget scenarios (conservative, base, optimistic)
- **Route Architecture**: Routes are organized by module layer:
  - `frontend/src/routes/dashboard.tsx` - Main dashboard
  - `frontend/src/routes/configuration/` - Configuration layer modules
  - `frontend/src/routes/planning/` - Planning layer modules
  - `frontend/src/routes/consolidation/` - Consolidation layer modules
  - `frontend/src/routes/analysis/` - Analysis layer modules
  - `frontend/src/routes/strategic/` - Strategic layer modules
- **API Endpoints**: Backend routes registered in `backend/app/api/v1/` with controllers for each domain
- **Backend Models**: All 18 modules have corresponding SQLAlchemy models in `backend/app/models/`
- **Calculation Engines**: Pure Python engines in `backend/app/engine/` (DHG, KPI, Revenue, Enrollment)
- **Services Layer**: Business logic in `backend/app/services/` (base service, integrations, exceptions)
- **Schemas**: Pydantic request/response models in `backend/app/schemas/`
- **Database Migrations**: Alembic migrations in `backend/alembic/versions/` (linear chain: 001→002→...→007)

## MCP Tool Orchestration & Intelligence Rules

This project has **6 active MCP (Model Context Protocol) servers** providing specialized capabilities. Use these tools intelligently based on context and task requirements.

### Available MCP Tools

1. **filesystem** - File operations in project directory
2. **github** - GitHub repository integration
3. **context7** - Up-to-date library documentation lookup
4. **brave-search** - Web search for current information
5. **sequential-thinking** - Structured problem-solving and analysis
6. **supabase** - Supabase project management (OAuth-authenticated)

### Tool Selection Rules by Context

#### 🔍 Research & Learning Tasks

**Use Context7** when:
- Looking up documentation for libraries/frameworks (React, TypeScript, FastAPI, Supabase, etc.)
- Checking latest API syntax or method signatures
- Understanding best practices for a specific library version
- Verifying deprecated features or migration guides
- Example: "What's the latest syntax for React Server Components in React 19?"

**Use Brave Search** when:
- Researching general concepts or architectural patterns
- Finding solutions to specific error messages
- Comparing different approaches or tools
- Looking up industry standards (AEFE guidelines, French education system)
- Finding recent blog posts, tutorials, or documentation updates
- Example: "Best practices for PostgreSQL Row Level Security in multi-tenant apps"

**Use Sequential Thinking** when:
- Breaking down complex problems (DHG calculation logic, multi-module workflows)
- Analyzing multiple implementation approaches
- Planning architectural decisions
- Debugging complex issues spanning multiple systems
- Scenario analysis (comparing conservative vs optimistic budget projections)
- Example: "Design approach for implementing real-time budget collaboration with Supabase Realtime"

#### 💾 Data & Database Tasks

**Use Supabase MCP** when:
- Managing database schemas, tables, or RLS policies
- Querying project data directly
- Setting up Edge Functions or Auth rules
- Configuring real-time subscriptions
- Managing Supabase project settings
- Example: "Create RLS policies for budget version access control"

**Use Filesystem** when:
- Reading/writing local configuration files
- Managing migration scripts
- Accessing seed data or test fixtures
- Working with local environment files
- Example: "Read the Prisma schema to understand current data model"

#### 🔧 Development & Code Tasks

**Use GitHub MCP** when:
- Creating or managing issues
- Opening pull requests
- Reviewing code changes
- Managing project boards
- Accessing repository metadata
- Example: "Create an issue for implementing Module 8 (DHG Workforce Planning)"

**Use Filesystem** when:
- Reading source code files
- Implementing new features or modules
- Updating configuration files
- Managing test files
- Example: "Read existing enrollment planning module to understand data flow"

#### 🧠 Complex Problem-Solving

**Use Sequential Thinking + Context7** when:
- Implementing complex business logic (DHG calculations, TRMD gap analysis)
- Designing new module architecture
- Optimizing performance-critical code
- Refactoring large sections of code
- Example: "Design the DHG hours calculation engine with proper TypeScript types"

**Use Sequential Thinking + Brave Search** when:
- Researching unfamiliar domains (French education system, AEFE guidelines)
- Comparing multiple technical approaches
- Troubleshooting production issues
- Planning multi-phase implementations
- Example: "Understand French PCG accounting standards for budget consolidation"

### Workflow-Specific Tool Combinations

#### Module Implementation Workflow

1. **Context7**: Look up latest library documentation for dependencies
2. **Sequential Thinking**: Break down module requirements and design approach
3. **Filesystem**: Read related modules and specification documents
4. **Supabase**: Design database schema and RLS policies
5. **Filesystem**: Implement code following EFIR Development Standards
6. **GitHub**: Create PR and document changes

#### Bug Investigation Workflow

1. **Sequential Thinking**: Analyze the problem systematically
2. **Filesystem**: Read relevant source files
3. **Brave Search**: Search for similar issues or error messages
4. **Context7**: Verify API usage and library behavior
5. **Filesystem**: Implement fix
6. **GitHub**: Document fix in issue/PR

#### Documentation Lookup Workflow

1. **Context7** (Primary): For library-specific documentation
2. **Brave Search** (Fallback): If Context7 doesn't have information or for general concepts
3. **Sequential Thinking** (Analysis): To synthesize information and make decisions

#### Database Design Workflow

1. **Sequential Thinking**: Plan schema design considering business rules
2. **Brave Search**: Research best practices for multi-tenant apps, RLS patterns
3. **Supabase**: Implement schema, migrations, and RLS policies
4. **Filesystem**: Update Prisma schema or migration files
5. **GitHub**: Document database changes

### Tool Priority Guidelines

**For TypeScript/React/Frontend Tasks:**
1. Context7 (for React 19, TypeScript 5.9, Vite 7 docs)
2. Sequential Thinking (for complex component design)
3. Filesystem (for reading/writing code)
4. Brave Search (for general patterns/solutions)

**For Python/FastAPI/Backend Tasks:**
1. Context7 (for FastAPI 0.123, Pydantic 2.12 docs)
2. Sequential Thinking (for API design)
3. Filesystem (for reading/writing code)
4. Brave Search (for architectural patterns)

**For Database/Supabase Tasks:**
1. Supabase MCP (for direct project management)
2. Context7 (for Supabase library docs)
3. Sequential Thinking (for schema design)
4. Brave Search (for RLS patterns, multi-tenancy)

**For Business Logic/Domain-Specific Tasks:**
1. Sequential Thinking (for DHG calculations, French education rules)
2. Filesystem (for reading specifications)
3. Brave Search (for AEFE guidelines, PCG standards)
4. Context7 (for implementation libraries)

### Integration Best Practices

**Combine Tools Intelligently:**
- Don't search the web for library docs that Context7 can provide
- Use Sequential Thinking for complex multi-step planning before implementation
- Always verify current library syntax with Context7 before implementing
- Use Brave Search for domain knowledge (AEFE, French education, accounting standards)
- Leverage Supabase MCP for database operations instead of manual SQL

**Avoid Tool Misuse:**
- ❌ Don't use Brave Search for library documentation (use Context7)
- ❌ Don't skip Sequential Thinking for complex problems
- ❌ Don't manually write database queries when Supabase MCP can help
- ❌ Don't search the web for syntax that Context7 already knows

**Performance Considerations:**
- Context7 is faster than web search for library docs
- Sequential Thinking adds overhead but prevents mistakes in complex tasks
- Use Filesystem for local operations instead of external tools
- Batch related MCP calls when possible

### Domain-Specific Tool Usage

**For EFIR Budget App Specifically:**

**DHG Workforce Planning (Module 8):**
- Sequential Thinking: Break down the complex DHG methodology
- Context7: Look up TypeScript utility types for calculations
- Filesystem: Read workforce planning specifications
- Brave Search: Research French education system hours/week standards

**Financial Consolidation (Modules 13-14):**
- Sequential Thinking: Design multi-version budget consolidation
- Context7: AG Grid API for displaying financial data
- Brave Search: French PCG and IFRS accounting standards
- Supabase: Design RLS for budget version access control

**Real-time Collaboration:**
- Context7: Supabase Realtime API documentation
- Sequential Thinking: Design conflict resolution strategy
- Supabase: Configure realtime subscriptions and broadcast
- Filesystem: Implement client-side sync logic

**Data Import/Export (Odoo, Skolengo):**
- Sequential Thinking: Design ETL pipeline
- Context7: FastAPI async patterns for data processing
- Brave Search: Odoo/Skolengo API documentation
- Filesystem: Implement integration adapters

### Emergency Fallback Rules

If a tool fails or is unavailable:
1. **Context7 down** → Use Brave Search for documentation
2. **Brave Search down** → Use Context7 + Sequential Thinking
3. **Supabase MCP down** → Use Filesystem for SQL scripts
4. **Sequential Thinking unneeded** → Proceed with simpler direct implementation
5. **GitHub MCP down** → Use git commands via bash

### Tool Usage Metrics & Optimization

**Track your tool usage:**
- Favor Context7 for any library/framework documentation
- Use Sequential Thinking for problems requiring >3 steps
- Prefer Supabase MCP over manual database operations
- Reserve Brave Search for domain knowledge and error troubleshooting

**Continuous Improvement:**
- If Context7 lacks information, note the gap and use Brave Search
- Document repeated patterns to optimize future tool selection
- Share successful tool combinations in team documentation

## Frontend Architecture Deep Dive

### TanStack Router Integration

The application uses **TanStack Router** for client-side routing with the following structure:

**Route File Organization:**
- Each route is a `.tsx` file in `frontend/src/routes/`
- Routes are lazy-loaded and automatically code-split by Vite
- The `routeTree.gen.ts` file is auto-generated from file structure
- Type-safe navigation with `useNavigate()` hook

**Layout Hierarchy:**
```
__root.tsx (main layout)
├── index.tsx (login page)
├── dashboard.tsx (main app dashboard)
├── configuration/ (module routes)
├── planning/ (module routes)
├── consolidation/ (module routes)
├── analysis/ (module routes)
└── strategic/ (module routes)
```

### Data Fetching & State Management

**TanStack Query (React Query):**
- All API calls through custom hooks in `frontend/src/hooks/api/`
- Hooks use `useQuery()` for fetching, `useMutation()` for mutations
- Automatic caching, deduplication, and background synchronization
- Example: `useBudgetVersions()`, `useEnrollmentData()`, `useDHGCalculation()`

**State Management Pattern:**
- Global state: TanStack Query (server state)
- UI state: React hooks + context (loading, filters, selected items)
- Form state: React Hook Form + Zod validation
- No Redux/Zustand needed - Query handles server sync

### Component Architecture

**Component Organization:**
- **UI Components** (`frontend/src/components/`): Reusable shadcn/ui components (Button, Dialog, Select, etc.)
- **Feature Components** (`frontend/src/routes/*/`): Page-level components per route
- **Custom Hooks** (`frontend/src/hooks/`): Business logic extraction (useBudgetVersions, useAutoSave, etc.)

**AG Grid Integration:**
```tsx
// Example: Data grid for enrollment planning
<AgGridReact
  columnDefs={columns}
  rowData={enrollmentData}
  onCellValueChanged={handleCellChange}
  editType="fullRow"
  defaultColDef={{ sortable: true, filter: true, editable: true }}
/>
```

**Styling Approach:**
- Tailwind CSS for utility classes + shadcn/ui for components
- No CSS modules or Styled Components (Tailwind + shadcn only)
- Slot styling pattern for component customization
- Dark mode support via `dark:` prefix (configured via system preference)

### Form Handling

**React Hook Form + Zod:**
```tsx
const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
  resolver: zodResolver(enrollmentSchema)
});
```

All form schemas in `frontend/src/schemas/` using Zod for validation

### Testing Strategy

**Unit Tests (Vitest):**
- Components in `frontend/tests/components/`
- Hooks in `frontend/tests/hooks/`
- Utilities in `frontend/tests/utils/`
- Use `@testing-library/react` for component testing

**E2E Tests (Playwright):**
- Tests in `frontend/tests/e2e/`
- Critical user flows: enrollment entry, calculation verification, report generation
- Run with `pnpm test:e2e` (headed mode with `--headed`)

## Backend Architecture Deep Dive

### FastAPI Structure

**Project Layout:**
```
backend/app/
├── main.py           # FastAPI app initialization, middleware, CORS
├── api/              # API routes organized by domain
│   └── v1/
│       ├── __init__.py (router registration)
│       ├── planning.py (planning modules 7-12)
│       ├── costs.py (cost calculation)
│       ├── revenue.py (revenue calculation)
│       ├── consolidation.py (budget consolidation)
│       ├── analysis.py (KPI & analysis)
│       ├── strategic.py (5-year planning)
│       └── calculations.py (general calculation endpoints)
├── models/           # SQLAlchemy ORM models (18 modules)
├── schemas/          # Pydantic request/response models
├── engine/           # Pure Python calculation engines
│   ├── dhg_calculator.py (DHG/workforce)
│   ├── kpi_calculator.py (KPI calculations)
│   ├── revenue_calculator.py (revenue/fee calculations)
│   └── enrollment_engine.py (enrollment projections)
├── services/         # Business logic & external integrations
│   ├── base.py (base service class with CRUD patterns)
│   ├── exceptions.py (custom exception definitions)
│   ├── odoo_integration.py (Odoo/XERO connector)
│   ├── skolengo_integration.py (Skolengo enrollment import)
│   └── aefe_integration.py (AEFE position data)
└── tests/            # Pytest tests organized by domain
```

### Calculation Engine Pattern

All calculation engines use this pattern:

```python
from pydantic import BaseModel, Field

class DHGInputModel(BaseModel):
    class_structure: Dict[str, int] = Field(..., description="Classes per level")
    subject_hours: Dict[str, float] = Field(..., description="Hours per subject")

class DHGOutputModel(BaseModel):
    total_fte: float
    gap_analysis: Dict[str, float]
    costs_sar: Decimal

def calculate_dhg(inputs: DHGInputModel) -> DHGOutputModel:
    """Pure function - no side effects, fully testable"""
    # Implementation
    return DHGOutputModel(...)
```

**Key Principles:**
- Pure functions (no database access, no side effects)
- Pydantic models for input validation and type safety
- Comprehensive error messages with context
- 80%+ test coverage requirement

### API Endpoint Pattern

```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas import EnrollmentRequest, EnrollmentResponse
from app.services import EnrollmentService

router = APIRouter(prefix="/v1/enrollment", tags=["enrollment"])

@router.post("/calculate", response_model=EnrollmentResponse)
async def calculate_enrollment(
    req: EnrollmentRequest,
    service: EnrollmentService = Depends()
) -> EnrollmentResponse:
    """Calculate enrollment projections"""
    try:
        result = await service.calculate(req)
        return EnrollmentResponse(**result.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Database & Migrations

**Alembic Migration Chain:**
```
001_initial_config → 002_planning_layer → 003_consolidation_layer →
004_fix_critical_issues → 005_analysis_layer → 006_class_structure_validation →
007_strategic_layer
```

Each migration:
- Created with `alembic revision --autogenerate -m "description"`
- Tracks schema changes automatically
- Includes down migrations for rollback capability
- Linear chain (each migration's `down_revision` points to previous)

**RLS Policies:**
- User-level isolation: Each user can only access their organization's data
- Role-based: Admin, Finance Director, HR, Academic, Viewer roles
- Implemented via Supabase RLS on public schema tables

## Working with This Codebase

When starting development:
1. Read the complete technical specification (`EFIR_Module_Technical_Specification.md`) to understand the calculation formulas
2. Review the workforce planning logic (`EFIR_Workforce_Planning_Logic.md`) before implementing Module 8
3. Use the data summary (`EFIR_Data_Summary_v2.md`) for realistic test data
4. Implement modules in dependency order (Configuration → Planning → Consolidation → Analysis)
5. Test calculations against the reference data in the specification documents
6. **Leverage MCP tools intelligently** - Use Context7 for library docs, Sequential Thinking for complex problems, and Supabase MCP for database operations

### Frontend Workflow Example

```bash
# 1. Start dev server
cd frontend && pnpm dev

# 2. Create new route for a module
# File: frontend/src/routes/planning/enrollment-planning.tsx

# 3. Add hook for API data fetching
# File: frontend/src/hooks/api/useEnrollmentData.ts
# Uses: TanStack Query for server state + React Hook Form for local state

# 4. Create AG Grid with enrollment data
# Component with columns, cell editors, and onCellValueChanged handler

# 5. Write tests
pnpm test                    # Unit tests for components/hooks
pnpm test:e2e                # E2E test for user workflow

# 6. Lint & format
pnpm lint:fix && pnpm format

# 7. Commit with conventional commits
git add . && git commit -m "feat: enrollment planning module with DHG integration"
```

### Backend Workflow Example

```bash
# 1. Start dev server
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# 2. Create new calculation engine
# File: backend/app/engine/new_calculator.py
# Pattern: Pure functions with Pydantic models

# 3. Create API endpoint
# File: backend/app/api/v1/planning.py
# Dependency inject service, validate input, return response

# 4. Create database model
# File: backend/app/models/planning.py
# SQLAlchemy ORM model with columns matching schema

# 5. Write comprehensive tests
pytest tests/engine/          # Test calculation logic (mock-free)
pytest tests/api/             # Test endpoint validation & errors
pytest tests/integration/     # Test full flow with database

# 6. Run quality checks
.venv/bin/ruff check . --fix   # Auto-fix linting issues
.venv/bin/mypy .               # Type checking

# 7. Create migration if schema changed
alembic revision --autogenerate -m "add enrollment table"

# 8. Commit
git add . && git commit -m "feat: enrollment calculation engine with RLS"
```

## Debugging & Troubleshooting

**Frontend Issues:**
- Check browser console for React warnings/errors
- Use `pnpm test:ui` to run tests interactively
- Check Playwright test reports with `pnpm test:e2e:report`
- TanStack Query DevTools (built-in) shows all queries/mutations

**Backend Issues:**
- Check console output from `uvicorn` for stack traces
- Use `pytest -v --tb=short` for detailed test failures
- Check Ruff/mypy output for code quality issues
- Database migrations: Check `alembic current` vs expected state

**Type Checking Issues:**
- Frontend: `pnpm typecheck` shows TypeScript errors
- Backend: `.venv/bin/mypy .` shows type errors
- Read error messages carefully - they're specific and actionable
