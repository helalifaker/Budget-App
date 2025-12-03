# EFIR Budget Planning Application

A comprehensive, driver-based budget planning system for École Française Internationale de Riyad (EFIR), a French international school in Saudi Arabia operating under AEFE (Agence pour l'enseignement français à l'étranger) guidelines.

---

## 🤖 For AI Agents / Claude Code

**⚠️ CRITICAL: If you are an AI agent working on this codebase, read this section FIRST.**

### Primary Agent Reference Documents

1. **[CLAUDE.md](./CLAUDE.md)** - **YOUR PRIMARY REFERENCE** (1000+ lines)
   - Complete agent guidance, development standards, architecture patterns
   - Technology stack details, module specifications, calculation formulas
   - **Read this before making any code changes**

2. **[.claude/AGENT_ORCHESTRATION.md](./.claude/AGENT_ORCHESTRATION.md)** - Agent System Guide
   - 14 specialized agents and their boundaries
   - Agent dependencies and orchestration rules
   - Multi-agent workflow patterns

3. **[.claude/agents/](./.claude/agents/)** - Individual Agent Configurations
   - Your specific agent configuration file
   - Know your boundaries and responsibilities

### Agent System Overview

This codebase uses a **14-agent orchestration system**:

| Agent | Responsibility |
|-------|---------------|
| `efir-master-agent` | Orchestrator - routes multi-domain tasks |
| `product-architect-agent` | Business rules, formulas, requirements (SOURCE OF TRUTH) |
| `system-architect-agent` | Architecture, API contracts, module boundaries |
| `database-supabase-agent` | PostgreSQL schema, RLS policies, migrations |
| `backend-engine-agent` | Calculation engines (DHG, enrollment, revenue, costs) |
| `backend-api-specialist` | FastAPI endpoints and API layer |
| `frontend-ui-agent` | React UI, components, all 18 modules |
| `governance-versioning-agent` | Budget lifecycle and workflow management |
| `reporting-statements-agent` | PCG/IFRS statements and board reports |
| `security-rls-agent` | Authentication, MFA, RLS policies |
| `data-migration-agent` | ETL and data import from legacy systems |
| `performance-agent` | Profiling, optimization, load testing |
| `qa-validation-agent` | Test coverage and quality assurance |
| `documentation-training-agent` | Documentation and training materials |

### Quick Agent Routing Reference

**Route requests to the correct agent:**

- **Business Rules/Formulas/Requirements** → `product-architect-agent` (SOURCE OF TRUTH)
- **Database/Schema/RLS/Migrations** → `database-supabase-agent`
- **Calculation Logic (DHG, FTE, Revenue, Costs)** → `backend-engine-agent`
- **FastAPI Routes/Endpoints** → `backend-api-specialist`
- **React Components/UI** → `frontend-ui-agent`
- **Architecture/Interfaces** → `system-architect-agent`
- **Security/Auth/RLS** → `security-rls-agent`
- **Tests/QA** → `qa-validation-agent`
- **Multi-domain tasks** → `efir-master-agent` (orchestrator)

**See [Agent Orchestration Guide](./.claude/AGENT_ORCHESTRATION.md) for complete routing logic and boundaries.**

### Agent Development Standards

All agents MUST follow the **EFIR Development Standards System** (4 Non-Negotiables):

1. **Complete Implementation**: No TODOs, no placeholders, all edge cases handled
2. **Best Practices**: Type-safe code, SOLID principles, 80%+ test coverage
3. **Documentation**: Every module has a `.md` file with formulas, examples, business rules
4. **Review & Testing**: All tests pass, linting passes, type checking passes

**See [CLAUDE.md](./CLAUDE.md) "EFIR Development Standards System" section for details.**

### Agent Boundary Enforcement

**CRITICAL RULES:**
- ❌ **NEVER** cross agent boundaries (e.g., frontend-ui-agent cannot modify database)
- ✅ **ALWAYS** consult `product-architect-agent` for business rules
- ✅ **ALWAYS** follow `system-architect-agent` for architecture patterns
- ✅ **ALWAYS** route multi-domain tasks through `efir-master-agent`

**See [Agent Orchestration Guide](./.claude/AGENT_ORCHESTRATION.md) "Agent Boundary Enforcement" section for complete rules.**

---

## Overview

This application provides integrated workforce planning through annual budget and 5-year strategic planning, built around the French education system's **DHG (Dotation Horaire Globale)** methodology. It transforms complex, manual budget processes into an automated system with real-time calculations, scenario analysis, and comprehensive reporting.

### Key Features

- **Driver-Based Calculations**: Enrollment projections automatically cascade through class formation, DHG hours, teacher FTE requirements, and financial planning
- **DHG Workforce Planning**: Automated calculation of teacher requirements using French education system standards
- **Multi-Period Budgeting**: Supports dual-period structure (Jan-Jun / Sep-Dec) spanning two academic years
- **AEFE Integration**: Manages AEFE teacher costs with EUR/SAR currency considerations
- **Scenario Analysis**: Side-by-side comparison of budget scenarios (conservative, base, optimistic)
- **Real-Time Validation**: Business rules enforcement and constraint validation
- **Comprehensive Reporting**: Financial statements (French PCG + IFRS formats), KPIs, and dashboards

## Technology Stack

### Frontend
- **Framework**: React 19.2.0 (Server Components, Actions, Activity API)
- **Language**: TypeScript 5.9.3
- **Build Tool**: Vite 7.2.6
- **Styling**: Tailwind CSS 4.1.17
- **Components**: shadcn/ui (TW v4 compatible)
- **Data Grid**: AG Grid Community 34.3.1
- **Charts**: Recharts 3.4.1

### Backend
- **Runtime**: Python 3.14.0 (Free-threaded Python, Template String Literals)
- **API Framework**: FastAPI 0.123.4
- **Validation**: Pydantic 2.12.5
- **Server**: Uvicorn 0.38.0

### Database & Infrastructure
- **Database**: PostgreSQL 17.x (via Supabase)
- **Backend-as-a-Service**: Supabase (Auth, Realtime, Edge Functions)
- **Security**: Row Level Security (RLS)

### Development Tools
- **Frontend**: ESLint 9.39.1, Prettier 3.7.0, Vitest 4.0.0, Playwright 1.57.0
- **Backend**: Ruff 0.14.3, mypy 1.19.0, pytest 9.0.1
- **Git Hooks**: Husky 9.1.7, lint-staged 15.5.2

## Project Structure

```
.
├── frontend/              # React 19 + TypeScript + Vite application
├── backend/               # FastAPI application with calculation engines
│   ├── app/               # Application code
│   │   ├── api/           # FastAPI routes
│   │   ├── engine/        # Calculation engines (DHG, KPI, Revenue, Enrollment)
│   │   ├── models/        # SQLAlchemy models (18 modules)
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic services
│   ├── alembic/           # Database migrations (7 migrations)
│   └── tests/             # Pytest tests
├── docs/                  # Documentation (COMPLETE)
│   ├── MODULES/           # 18 module specifications (100% complete)
│   └── DATABASE/          # Database design and setup guides
├── .claude/               # Agent configuration
│   └── agents/            # 14 specialized agents
├── .github/
│   └── workflows/         # CI/CD workflows
└── README.md              # This file
```

## Quickstart

### Prerequisites

- **Node.js**: 20.x or higher
- **Python**: 3.14.0 or higher
- **PostgreSQL**: 17.x (or Supabase account)
- **Git**: Latest version

### Frontend Setup

```bash
cd frontend
npm install
npm run dev          # Start development server (http://localhost:5173)
npm run test         # Run tests
npm run lint         # Run ESLint
npm run test:e2e     # Run E2E tests (Playwright)
```

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
uvicorn backend.app.main:app --reload  # Start API server (http://localhost:8000)
pytest                 # Run tests
ruff check .          # Run linter
mypy .                # Type check
```

### Environment Variables

Create `.env.local` files in both `frontend/` and `backend/` directories with your configuration:

**Frontend** (`.env.local`):
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Backend** (`.env.local`):
```env
DATABASE_URL=your_database_url
DIRECT_URL=your_direct_database_url
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
```

> **Note**: When using Supabase, remember to import both `DATABASE_URL` (pgBouncer) and `DIRECT_URL` (direct connection) with `sslmode=require`.

## Development Workflow

### Code Quality

This project follows the **EFIR Development Standards System** with 4 Non-Negotiables:

1. **Complete Implementation**: No TODOs, no placeholders, all edge cases handled
2. **Best Practices**: Type-safe code, SOLID principles, 80%+ test coverage
3. **Documentation**: Every module has a `.md` file with formulas, examples, and business rules
4. **Review & Testing**: All tests pass, linting passes, type checking passes

### Pre-commit Hooks

Pre-commit hooks (via Husky + lint-staged) automatically run:
- ESLint (code quality)
- Prettier (code formatting)
- TypeScript type checking
- Vitest (affected tests)

### CI/CD Pipeline

GitHub Actions automatically runs on push/PR:
- **Frontend**: ESLint → TypeScript check → Vitest
- **Backend**: Ruff → mypy → pytest

## Documentation

### For AI Agents
- **[CLAUDE.md](./CLAUDE.md)**: **PRIMARY AGENT REFERENCE** - Complete development guidelines, architecture, standards (1000+ lines)
- **[.claude/AGENT_ORCHESTRATION.md](./.claude/AGENT_ORCHESTRATION.md)**: 14-agent system, orchestration rules, boundaries
- **[.claude/agents/](./.claude/agents/)**: Individual agent configuration files

### For All Developers
- **[PRD v1.2](./EFIR_Budget_App_PRD_v1_2.md)**: Product Requirements Document
- **[TSD v1.2](./EFIR_Budget_App_TSD_v1_2.md)**: Technical Specification Document
- **[Module Specifications](./EFIR_Module_Technical_Specification.md)**: Detailed module specifications and formulas
- **[Workforce Planning Logic](./EFIR_Workforce_Planning_Logic.md)**: DHG methodology and calculations
- **[Data Summary](./EFIR_Data_Summary_v2.md)**: Historical data and reference information

## Key Concepts

### DHG (Dotation Horaire Globale)

The core calculation engine for secondary teacher workforce planning:

```
Total Subject Hours = Σ(Number of Classes × Hours per Subject per Level)
Teacher FTE Required = Total Subject Hours ÷ Standard Hours (18h/week for secondary)
```

### Module Architecture

The application is organized into 18 modules across 5 layers:
1. **Configuration** (Modules 1-6): Master data and parameters
2. **Planning** (Modules 7-12): Enrollment → Class Structure → DHG → Financial Planning
3. **Consolidation** (Modules 13-14): Budget consolidation and financial statements
4. **Analysis** (Modules 15-17): KPIs, dashboards, budget vs actual
5. **Strategic** (Module 18): 5-year strategic planning

## Contributing

1. Create a feature branch from `develop`
2. Follow the EFIR Development Standards (see [CLAUDE.md](./CLAUDE.md))
3. Write tests (80%+ coverage minimum)
4. Update documentation
5. Ensure all checks pass (lint, type, test)
6. Submit a pull request

## License

Internal use only - EFIR School Budget Planning Application

## Support

For questions or issues, please refer to the documentation or contact the development team.
