# EFIR Budget Planning Application

A comprehensive, driver-based budget planning system for École Française Internationale de Riyad (EFIR), a French international school in Saudi Arabia operating under AEFE (Agence pour l'enseignement français à l'étranger) guidelines.

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
- **Language**: TypeScript 5.9.x
- **Build Tool**: Vite 7.2.x
- **Styling**: Tailwind CSS 4.1.x
- **Components**: shadcn/ui (TW v4 compatible)
- **Data Grid**: AG Grid Community 34.3.x
- **Charts**: Recharts 2.15.x

### Backend
- **Runtime**: Python 3.12+
- **API Framework**: FastAPI 0.123.x
- **Validation**: Pydantic 2.12+
- **Server**: Uvicorn 0.34+

### Database & Infrastructure
- **Database**: PostgreSQL 17.x (via Supabase)
- **Backend-as-a-Service**: Supabase (Auth, Realtime, Edge Functions)
- **Security**: Row Level Security (RLS)

### Development Tools
- **Frontend**: ESLint 9.x, Prettier 3.4.x, Vitest 3.x, Playwright 1.49.x
- **Backend**: Ruff 0.8.x, mypy 1.14.x, pytest 8.x
- **Git Hooks**: Husky 9.x, lint-staged 15.x

## Project Structure

```
.
├── frontend/          # React 19 + TypeScript + Vite application
├── backend/           # FastAPI application
├── docs/              # Documentation (to be added)
│   └── MODULES/       # Module-specific documentation
├── .github/
│   └── workflows/      # CI/CD workflows
└── README.md          # This file
```

## Quickstart

### Prerequisites

- **Node.js**: 20.x or higher
- **Python**: 3.12 or higher
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

- **[CLAUDE.md](./CLAUDE.md)**: Development guidelines and project overview
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
