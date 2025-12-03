# EFIR Budget Planning Application - Developer Guide

**Version**: 1.0
**Last Updated**: December 2025
**Target Audience**: Developers, DevOps engineers, technical leads

## Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [Development Environment Setup](#2-development-environment-setup)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Database Design](#5-database-design)
6. [Adding a New Module](#6-adding-a-new-module)
7. [Testing Strategy](#7-testing-strategy)
8. [Deployment](#8-deployment)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Project Architecture

### 1.1 High-Level Architecture

```
┌─────────────────┐
│   Web Browser   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Frontend       │  React 19.2.0 + TypeScript 5.9.3 + Vite 7.2.6
│  (Port 5173)    │  Tailwind CSS 4.1.17 + AG Grid 34.3.1
└────────┬────────┘
         │ REST API
         ▼
┌─────────────────┐
│  Backend        │  FastAPI 0.123.4 + Python 3.14.0
│  (Port 8000)    │  Calculation Engines
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Supabase       │  PostgreSQL 17
│  Database       │  Row Level Security (RLS)
│                 │  Auth + Realtime
└─────────────────┘

External Integrations:
- Odoo (Accounting)
- Skolengo (SIS)
- AEFE (Positions)
```

### 1.2 Technology Stack

**Frontend**:
- React 19.2.0 (Server Components, Actions)
- TypeScript 5.9.3 (strict mode)
- Vite 7.2.6 (build tool, 5x faster with Environment API)
- Tailwind CSS 4.1.17 (@tailwindcss/vite plugin)
- shadcn/ui (component library)
- AG Grid Community 34.3.1 (data grid, MIT license)
- Recharts 3.4.1 (charting)
- TanStack Router 1.139.12 (routing)
- TanStack Query 5.90.11 (data fetching/caching)
- React Hook Form 7.67.0 (forms)
- Zod 3.24.x (validation)

**Backend**:
- FastAPI 0.123.4 (async web framework)
- Python 3.14.0 (Free-threaded Python, Template String Literals)
- Pydantic 2.12.5 (data validation)
- SQLAlchemy 2.0.44 (ORM)
- Alembic 1.17.2 (migrations)
- Uvicorn 0.38.0 (ASGI server)

**Database**:
- PostgreSQL 17.x (via Supabase)
- Supabase (BaaS: Auth, Realtime, Edge Functions)

**Testing**:
- Frontend: Vitest 4.0.0 + Testing Library + Playwright 1.57.0
- Backend: pytest 9.0.1 + coverage

**Code Quality**:
- ESLint 9.39.1 (frontend linting)
- Ruff 0.14.3 (backend linting, 10-100x faster than Flake8)
- mypy 1.19.0 (Python type checking)
- Prettier 3.7.0 (code formatting)
- Husky 9.1.7 + lint-staged 15.5.2 (pre-commit hooks)

### 1.3 Directory Structure

```
/Users/fakerhelali/Coding/Budget App/
├── frontend/                   # React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── ui/             # shadcn/ui primitives
│   │   │   ├── forms/          # Form components
│   │   │   ├── grids/          # AG Grid components
│   │   │   └── charts/         # Recharts components
│   │   ├── routes/             # TanStack Router pages
│   │   │   ├── __root.tsx      # Root layout
│   │   │   ├── index.tsx       # Home page
│   │   │   ├── login.tsx       # Login page
│   │   │   ├── dashboard.tsx   # Dashboard
│   │   │   ├── configuration/  # Configuration pages
│   │   │   ├── planning/       # Planning pages
│   │   │   ├── consolidation/  # Consolidation pages
│   │   │   ├── analysis/       # Analysis pages
│   │   │   └── settings/       # Settings pages
│   │   ├── lib/                # Utilities and helpers
│   │   │   ├── api/            # API client
│   │   │   ├── hooks/          # Custom React hooks
│   │   │   ├── utils/          # Helper functions
│   │   │   ├── types/          # TypeScript types
│   │   │   └── validations/    # Zod schemas
│   │   ├── contexts/           # React contexts
│   │   └── main.tsx            # Application entry point
│   ├── tests/
│   │   ├── unit/               # Vitest unit tests
│   │   └── e2e/                # Playwright E2E tests
│   ├── public/                 # Static assets
│   ├── package.json
│   ├── playwright.config.ts
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── api/                # API routes
│   │   │   └── v1/             # API version 1
│   │   │       ├── configuration/
│   │   │       ├── planning/
│   │   │       ├── consolidation/
│   │   │       ├── analysis/
│   │   │       └── integrations/
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── base.py
│   │   │   ├── configuration.py
│   │   │   ├── planning.py
│   │   │   └── ...
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── configuration.py
│   │   │   ├── planning.py
│   │   │   └── ...
│   │   ├── services/           # Business logic
│   │   │   ├── configuration/
│   │   │   ├── planning/
│   │   │   └── ...
│   │   ├── engine/             # Calculation engines
│   │   │   ├── dhg.py          # DHG calculator
│   │   │   ├── enrollment.py  # Enrollment calculator
│   │   │   ├── revenue.py      # Revenue calculator
│   │   │   └── kpi.py          # KPI calculator
│   │   ├── core/               # Core utilities
│   │   │   ├── config.py       # Configuration
│   │   │   ├── security.py     # Auth/security
│   │   │   ├── database.py     # DB connection
│   │   │   └── dependencies.py # FastAPI dependencies
│   │   └── utils/              # Helper functions
│   ├── alembic/                # Database migrations
│   │   ├── versions/           # Migration files
│   │   └── env.py
│   ├── tests/
│   │   ├── unit/               # pytest unit tests
│   │   ├── integration/        # Integration tests
│   │   └── conftest.py         # pytest fixtures
│   ├── pyproject.toml
│   ├── pytest.ini
│   └── alembic.ini
│
├── docs/                       # Documentation
│   ├── MODULES/                # Module specifications
│   ├── DATABASE/               # Database docs
│   ├── USER_GUIDE.md           # User guide
│   ├── DEVELOPER_GUIDE.md      # This file
│   ├── API_DOCUMENTATION.md    # API reference
│   └── INTEGRATION_GUIDE.md    # Integration guide
│
├── .github/
│   └── workflows/              # GitHub Actions CI/CD
│       ├── frontend-ci.yml
│       └── backend-ci.yml
│
├── .claude/                    # Claude Code agents
│   └── agents/                 # 14 specialized agents
│
├── .env.example                # Environment template
├── docker-compose.yml          # Docker Compose config
├── README.md
└── CLAUDE.md                   # Development guidelines
```

---

## 2. Development Environment Setup

### 2.1 Prerequisites

Install the following:

```bash
# Node.js 20+ (use nvm for version management)
nvm install 20
nvm use 20

# Python 3.14.0
# On macOS with Homebrew:
brew install python@3.14

# On Ubuntu/Debian:
sudo apt update
sudo apt install python3.14 python3.14-venv

# PostgreSQL 17 (optional if using local DB)
brew install postgresql@17  # macOS
# or use Supabase cloud

# Git
brew install git  # macOS
sudo apt install git  # Ubuntu/Debian
```

### 2.2 Clone Repository

```bash
git clone https://github.com/your-org/efir-budget-app.git
cd efir-budget-app
```

### 2.3 Frontend Setup

```bash
cd frontend

# Install pnpm if not already installed
npm install -g pnpm

# Install dependencies
pnpm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your values
# VITE_API_BASE_URL=http://localhost:8000/api/v1
# VITE_SUPABASE_URL=your_supabase_url
# VITE_SUPABASE_ANON_KEY=your_anon_key

# Start development server
pnpm dev

# Open http://localhost:5173
```

**Available Scripts**:
```bash
pnpm dev            # Start dev server
pnpm build          # Build for production
pnpm preview        # Preview production build
pnpm test           # Run Vitest tests
pnpm test:ui        # Run tests with UI
pnpm test:e2e       # Run Playwright E2E tests
pnpm test:e2e:ui    # Run E2E tests with UI
pnpm lint           # Run ESLint
pnpm lint:fix       # Fix ESLint errors
pnpm format         # Format with Prettier
pnpm typecheck      # TypeScript type check
```

### 2.4 Backend Setup

```bash
cd backend

# Create virtual environment
python3.14 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your values
# DATABASE_URL=postgresql://user:pass@localhost:5432/efir_budget
# DIRECT_URL=postgresql://user:pass@localhost:5432/efir_budget
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_service_key
# JWT_SECRET=your_secret_key

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Open http://localhost:8000/docs (Swagger UI)
```

**Available Scripts**:
```bash
# Testing
pytest                     # Run all tests
pytest --cov              # Run with coverage
pytest -v                 # Verbose output
pytest tests/unit/        # Run specific directory

# Linting & Type Checking
ruff check .              # Run Ruff linter
ruff check --fix .        # Auto-fix issues
mypy .                    # Type check with mypy

# Database Migrations
alembic revision --autogenerate -m "Description"  # Create migration
alembic upgrade head      # Apply migrations
alembic downgrade -1      # Rollback one migration
alembic history          # View migration history
```

### 2.5 Database Setup (Supabase)

1. **Create Supabase Project**:
   - Go to https://supabase.com
   - Click "New Project"
   - Enter project name and password
   - Wait for provisioning (~2 minutes)

2. **Get Credentials**:
   - Navigate to Project Settings > API
   - Copy:
     - Project URL
     - Anon/Public Key (for frontend)
     - Service Role Key (for backend)

3. **Configure Database**:
   - Go to Database > Tables
   - Run migrations from backend:
     ```bash
     alembic upgrade head
     ```

4. **Set Up Row Level Security (RLS)**:
   - See `docs/DATABASE/RLS_POLICIES.md` for policies
   - Apply via Supabase SQL Editor

### 2.6 Running Full Stack

**Option 1: Separate Terminals**

Terminal 1 (Backend):
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
pnpm dev
```

**Option 2: Docker Compose** (recommended for production-like environment)

```bash
docker-compose up --build
```

This starts:
- Frontend on port 3000
- Backend on port 8000
- PostgreSQL on port 5432

---

## 3. Frontend Architecture

### 3.1 Technology Choices

**React 19.2**:
- Server Components for better performance
- Actions for server mutations
- Activity API for pending states

**TypeScript 5.9**:
- Strict mode enabled
- All components fully typed
- No `any` types allowed

**Vite 7.2**:
- 5x faster builds with Baseline browser targeting
- Environment API for better plugin system
- Native ESM support

**Tailwind CSS 4.1**:
- @tailwindcss/vite plugin for instant builds
- 5x faster than v3
- OKLCH color space for better color

**TanStack Router**:
- Type-safe routing
- File-based routing
- Nested layouts

**TanStack Query**:
- Data fetching and caching
- Automatic background refetching
- Optimistic updates

**AG Grid Community 34.3**:
- Enterprise-grade data grid
- Cell editing, sorting, filtering
- High performance with virtualization
- MIT license (free)

### 3.2 Component Architecture

**Component Types**:

1. **Page Components** (`routes/`):
   - Route-level components
   - Fetch data with TanStack Query
   - Compose layout with smaller components

2. **Feature Components** (`components/features/`):
   - Business logic components
   - Module-specific (e.g., EnrollmentForm, DHGCalculator)

3. **UI Components** (`components/ui/`):
   - Reusable primitives from shadcn/ui
   - Button, Input, Dialog, etc.
   - Fully typed with TypeScript

4. **Grid Components** (`components/grids/`):
   - AG Grid wrappers
   - Custom cell renderers
   - Column definitions

**Example Component Structure**:

```typescript
// routes/planning/enrollment.tsx
import { useBudgetVersion } from '@/lib/hooks/useBudgetVersion';
import { EnrollmentGrid } from '@/components/grids/EnrollmentGrid';
import { useQuery } from '@tanstack/react-query';
import { getEnrollmentPlans } from '@/lib/api/enrollment';

export function EnrollmentPage() {
  const { selectedVersion } = useBudgetVersion();

  const { data: enrollments, isLoading } = useQuery({
    queryKey: ['enrollments', selectedVersion?.id],
    queryFn: () => getEnrollmentPlans(selectedVersion!.id),
    enabled: !!selectedVersion,
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <PageHeader title="Enrollment Planning" />
      <VersionSelector />
      <EnrollmentGrid data={enrollments} />
    </div>
  );
}
```

### 3.3 State Management

**TanStack Query** (for server state):
```typescript
// lib/api/enrollment.ts
import { apiClient } from './client';
import type { EnrollmentPlan } from '@/lib/types';

export async function getEnrollmentPlans(versionId: string): Promise<EnrollmentPlan[]> {
  const response = await apiClient.get(`/planning/enrollment/${versionId}`);
  return response.data;
}

export async function createEnrollmentPlan(data: CreateEnrollmentPlanInput) {
  const response = await apiClient.post('/planning/enrollment', data);
  return response.data;
}

// In component
const { data, isLoading, error } = useQuery({
  queryKey: ['enrollments', versionId],
  queryFn: () => getEnrollmentPlans(versionId),
});

const mutation = useMutation({
  mutationFn: createEnrollmentPlan,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['enrollments'] });
  },
});
```

**React Context** (for UI state):
```typescript
// contexts/BudgetVersionContext.tsx
import { createContext, useContext, useState } from 'react';
import type { BudgetVersion } from '@/lib/types';

interface BudgetVersionContextType {
  selectedVersion: BudgetVersion | null;
  setSelectedVersion: (version: BudgetVersion | null) => void;
}

const BudgetVersionContext = createContext<BudgetVersionContextType | undefined>(undefined);

export function BudgetVersionProvider({ children }: { children: React.ReactNode }) {
  const [selectedVersion, setSelectedVersion] = useState<BudgetVersion | null>(null);

  return (
    <BudgetVersionContext.Provider value={{ selectedVersion, setSelectedVersion }}>
      {children}
    </BudgetVersionContext.Provider>
  );
}

export function useBudgetVersion() {
  const context = useContext(BudgetVersionContext);
  if (!context) throw new Error('useBudgetVersion must be used within BudgetVersionProvider');
  return context;
}
```

### 3.4 Routing

TanStack Router with file-based routing:

```typescript
// routes/__root.tsx
import { Outlet, createRootRoute } from '@tanstack/react-router';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

// routes/planning/enrollment.tsx
import { createFileRoute } from '@tanstack/react-router';
import { EnrollmentPage } from '@/pages/EnrollmentPage';

export const Route = createFileRoute('/planning/enrollment')({
  component: EnrollmentPage,
});
```

### 3.5 Form Handling

React Hook Form + Zod validation:

```typescript
// lib/validations/enrollment.ts
import { z } from 'zod';

export const enrollmentSchema = z.object({
  level_id: z.string().min(1, 'Level is required'),
  nationality: z.enum(['French', 'Saudi', 'Other']),
  student_count: z.number().int().positive('Must be positive').max(1000, 'Too many students'),
  period: z.enum(['P1', 'P2']),
});

export type EnrollmentFormData = z.infer<typeof enrollmentSchema>;

// components/forms/EnrollmentForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { enrollmentSchema, type EnrollmentFormData } from '@/lib/validations/enrollment';

export function EnrollmentForm({ onSubmit }: { onSubmit: (data: EnrollmentFormData) => void }) {
  const form = useForm<EnrollmentFormData>({
    resolver: zodResolver(enrollmentSchema),
    defaultValues: {
      nationality: 'French',
      period: 'P2',
    },
  });

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      <Select {...form.register('level_id')}>
        {/* options */}
      </Select>

      <Input
        type="number"
        {...form.register('student_count', { valueAsNumber: true })}
      />

      {form.formState.errors.student_count && (
        <p className="text-red-500">{form.formState.errors.student_count.message}</p>
      )}

      <Button type="submit">Save</Button>
    </form>
  );
}
```

### 3.6 AG Grid Integration

```typescript
// components/grids/EnrollmentGrid.tsx
import { AgGridReact } from 'ag-grid-react';
import type { ColDef } from 'ag-grid-community';
import type { EnrollmentPlan } from '@/lib/types';

export function EnrollmentGrid({ data }: { data: EnrollmentPlan[] }) {
  const columnDefs: ColDef<EnrollmentPlan>[] = [
    { field: 'level_name', headerName: 'Level', sortable: true, filter: true },
    { field: 'nationality', headerName: 'Nationality', sortable: true, filter: true },
    { field: 'student_count', headerName: 'Students', sortable: true, editable: true },
    {
      field: 'actions',
      headerName: 'Actions',
      cellRenderer: (params: any) => (
        <div className="flex gap-2">
          <Button size="sm" onClick={() => handleEdit(params.data)}>Edit</Button>
          <Button size="sm" variant="destructive" onClick={() => handleDelete(params.data)}>Delete</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="ag-theme-alpine" style={{ height: 600 }}>
      <AgGridReact
        rowData={data}
        columnDefs={columnDefs}
        pagination={true}
        paginationPageSize={20}
        animateRows={true}
      />
    </div>
  );
}
```

---

## 4. Backend Architecture

### 4.1 FastAPI Application Structure

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as api_router
from app.core.config import settings

app = FastAPI(
    title="EFIR Budget Planning API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 4.2 API Endpoints

**Router Structure**:

```python
# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.configuration import router as config_router
from app.api.v1.planning import router as planning_router
from app.api.v1.consolidation import router as consolidation_router
from app.api.v1.analysis import router as analysis_router

router = APIRouter()
router.include_router(config_router, prefix="/configuration", tags=["Configuration"])
router.include_router(planning_router, prefix="/planning", tags=["Planning"])
router.include_router(consolidation_router, prefix="/consolidation", tags=["Consolidation"])
router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
```

**Example Endpoint**:

```python
# app/api/v1/planning/enrollment.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.enrollment import EnrollmentPlanCreate, EnrollmentPlanResponse
from app.services.enrollment import EnrollmentService

router = APIRouter()

@router.get("/{version_id}", response_model=List[EnrollmentPlanResponse])
async def get_enrollment_plans(
    version_id: str,
    db: Session = Depends(get_db)
):
    """Get all enrollment plans for a budget version."""
    service = EnrollmentService(db)
    return service.get_by_version(version_id)

@router.post("/", response_model=EnrollmentPlanResponse, status_code=201)
async def create_enrollment_plan(
    data: EnrollmentPlanCreate,
    db: Session = Depends(get_db)
):
    """Create a new enrollment plan."""
    service = EnrollmentService(db)
    return service.create(data)

@router.put("/{plan_id}", response_model=EnrollmentPlanResponse)
async def update_enrollment_plan(
    plan_id: str,
    data: EnrollmentPlanCreate,
    db: Session = Depends(get_db)
):
    """Update an enrollment plan."""
    service = EnrollmentService(db)
    return service.update(plan_id, data)

@router.delete("/{plan_id}", status_code=204)
async def delete_enrollment_plan(
    plan_id: str,
    db: Session = Depends(get_db)
):
    """Delete an enrollment plan."""
    service = EnrollmentService(db)
    service.delete(plan_id)
    return None
```

### 4.3 Models (SQLAlchemy)

```python
# app/models/enrollment.py
from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum

class NationalityEnum(enum.Enum):
    FRENCH = "French"
    SAUDI = "Saudi"
    OTHER = "Other"

class PeriodEnum(enum.Enum):
    P1 = "P1"
    P2 = "P2"

class EnrollmentPlan(Base, TimestampMixin):
    __tablename__ = "enrollment_plans"

    id = Column(String, primary_key=True)
    budget_version_id = Column(String, ForeignKey("budget_versions.id"), nullable=False)
    level_id = Column(String, ForeignKey("levels.id"), nullable=False)
    nationality = Column(Enum(NationalityEnum), nullable=False)
    student_count = Column(Integer, nullable=False)
    period = Column(Enum(PeriodEnum), nullable=False)

    # Relationships
    budget_version = relationship("BudgetVersion", back_populates="enrollment_plans")
    level = relationship("Level")
```

### 4.3 Schemas (Pydantic)

```python
# app/schemas/enrollment.py
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class EnrollmentPlanBase(BaseModel):
    level_id: str = Field(..., description="Level ID")
    nationality: Literal["French", "Saudi", "Other"]
    student_count: int = Field(..., gt=0, le=1000, description="Number of students")
    period: Literal["P1", "P2"]

class EnrollmentPlanCreate(EnrollmentPlanBase):
    budget_version_id: str

class EnrollmentPlanResponse(EnrollmentPlanBase):
    id: str
    budget_version_id: str
    level_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 4.5 Services (Business Logic)

```python
# app/services/enrollment.py
from sqlalchemy.orm import Session
from typing import List
from app.models.enrollment import EnrollmentPlan
from app.schemas.enrollment import EnrollmentPlanCreate
from app.engine.enrollment import EnrollmentEngine

class EnrollmentService:
    def __init__(self, db: Session):
        self.db = db
        self.engine = EnrollmentEngine()

    def get_by_version(self, version_id: str) -> List[EnrollmentPlan]:
        return self.db.query(EnrollmentPlan).filter(
            EnrollmentPlan.budget_version_id == version_id
        ).all()

    def create(self, data: EnrollmentPlanCreate) -> EnrollmentPlan:
        # Validation
        self._validate_capacity(data)

        # Create
        plan = EnrollmentPlan(
            id=str(uuid.uuid4()),
            **data.dict()
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)

        # Trigger downstream calculations
        self._trigger_class_calculation(data.budget_version_id)

        return plan

    def _validate_capacity(self, data: EnrollmentPlanCreate):
        """Validate total enrollment doesn't exceed capacity."""
        total = self.engine.calculate_total_enrollment(data.budget_version_id)
        if total + data.student_count > 1875:
            raise ValueError("Total enrollment exceeds school capacity (1,875)")

    def _trigger_class_calculation(self, version_id: str):
        """Trigger automatic class structure calculation."""
        # This would call ClassStructureService
        pass
```

### 4.6 Calculation Engines

```python
# app/engine/dhg.py
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DHGCalculationInput:
    class_structure: Dict[str, int]  # level_id -> class_count
    subject_hours: Dict[tuple, float]  # (subject_id, level_id) -> hours
    standard_hours: Dict[str, int]  # cycle -> standard_hours (18 or 24)

@dataclass
class DHGCalculationResult:
    total_hours: float
    simple_fte: float
    recommended_teachers: int
    hsa_hours: float
    h_e_ratio: float

class DHGEngine:
    """
    DHG (Dotation Horaire Globale) Calculation Engine

    Calculates teacher requirements for secondary education using French methodology.
    """

    def calculate(self, input: DHGCalculationInput) -> DHGCalculationResult:
        """
        Calculate DHG for secondary education.

        Formula:
            Total Hours = Σ (classes × hours_per_subject_per_level)
            Simple FTE = Total Hours ÷ Standard Hours (18h for secondary)
            Recommended Teachers = CEILING(Simple FTE)
            HSA Hours = Total Hours - (Recommended Teachers - 1) × Standard Hours
        """
        total_hours = 0.0

        # Calculate total hours
        for (subject_id, level_id), hours_per_class in input.subject_hours.items():
            class_count = input.class_structure.get(level_id, 0)
            total_hours += class_count * hours_per_class

        # Get standard hours for cycle (18h for secondary)
        standard_hours = input.standard_hours.get("secondary", 18)

        # Calculate FTE
        simple_fte = total_hours / standard_hours
        recommended_teachers = int(simple_fte) + (1 if simple_fte % 1 > 0 else 0)

        # Calculate HSA (overtime hours)
        hsa_hours = total_hours - (recommended_teachers - 1) * standard_hours
        if hsa_hours > standard_hours:
            hsa_hours = standard_hours  # Cap at standard hours for one teacher

        # Calculate H/E ratio (hours per student)
        # This would need student count from enrollment
        h_e_ratio = 0.0  # Placeholder

        return DHGCalculationResult(
            total_hours=total_hours,
            simple_fte=simple_fte,
            recommended_teachers=recommended_teachers,
            hsa_hours=hsa_hours,
            h_e_ratio=h_e_ratio,
        )

    def validate_h_e_ratio(self, h_e_ratio: float, cycle: str) -> bool:
        """
        Validate H/E ratio against AEFE benchmarks.

        Benchmarks:
            Collège: 1.35 - 1.45 H/E
            Lycée: 1.45 - 1.55 H/E
        """
        benchmarks = {
            "college": (1.35, 1.45),
            "lycee": (1.45, 1.55),
        }

        min_h_e, max_h_e = benchmarks.get(cycle, (1.0, 2.0))
        return min_h_e <= h_e_ratio <= max_h_e
```

---

## 5. Database Design

### 5.1 Core Tables

**Budget Versions**:
```sql
CREATE TABLE budget_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    academic_year VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('WORKING', 'SUBMITTED', 'APPROVED', 'BASELINE', 'FORECAST')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    description TEXT,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_budget_versions_status ON budget_versions(status);
CREATE INDEX idx_budget_versions_fiscal_year ON budget_versions(fiscal_year);
```

**Enrollment Plans**:
```sql
CREATE TABLE enrollment_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_version_id UUID REFERENCES budget_versions(id) ON DELETE CASCADE,
    level_id UUID REFERENCES levels(id),
    nationality VARCHAR(20) CHECK (nationality IN ('French', 'Saudi', 'Other')),
    student_count INTEGER CHECK (student_count > 0),
    period VARCHAR(10) CHECK (period IN ('P1', 'P2')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(budget_version_id, level_id, nationality, period)
);

CREATE INDEX idx_enrollment_version ON enrollment_plans(budget_version_id);
```

### 5.2 Database Migrations

Using Alembic:

```python
# alembic/versions/001_create_budget_versions.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'budget_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('fiscal_year', sa.Integer, nullable=False),
        sa.Column('academic_year', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now()),
    )

    op.create_index('idx_budget_versions_status', 'budget_versions', ['status'])

def downgrade():
    op.drop_index('idx_budget_versions_status')
    op.drop_table('budget_versions')
```

**Create Migration**:
```bash
alembic revision --autogenerate -m "Create budget versions table"
```

**Apply Migrations**:
```bash
alembic upgrade head
```

### 5.3 Row Level Security (RLS)

Example RLS policies for Supabase:

```sql
-- Enable RLS
ALTER TABLE budget_versions ENABLE ROW LEVEL SECURITY;

-- Users can view all budget versions
CREATE POLICY "Users can view budget versions"
ON budget_versions FOR SELECT
TO authenticated
USING (true);

-- Users can create budget versions
CREATE POLICY "Users can create budget versions"
ON budget_versions FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = created_by);

-- Only managers can approve budgets
CREATE POLICY "Managers can approve budgets"
ON budget_versions FOR UPDATE
TO authenticated
USING (
    status = 'SUBMITTED' AND
    (SELECT role FROM profiles WHERE id = auth.uid()) = 'manager'
)
WITH CHECK (status = 'APPROVED');
```

---

## 6. Adding a New Module

### Step-by-Step Guide

**Example**: Adding a "Equipment Tracking" module

**Step 1: Database Models**

```python
# backend/app/models/equipment.py
from sqlalchemy import Column, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Equipment(Base, TimestampMixin):
    __tablename__ = "equipment"

    id = Column(String, primary_key=True)
    budget_version_id = Column(String, ForeignKey("budget_versions.id"))
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    purchase_cost = Column(Numeric(12, 2), nullable=False)
    purchase_date = Column(Date)
    useful_life_years = Column(Integer, default=5)

    budget_version = relationship("BudgetVersion")
```

**Step 2: Create Migration**

```bash
alembic revision --autogenerate -m "Add equipment table"
alembic upgrade head
```

**Step 3: Pydantic Schemas**

```python
# backend/app/schemas/equipment.py
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal

class EquipmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str
    purchase_cost: Decimal = Field(..., gt=0)
    purchase_date: date
    useful_life_years: int = Field(default=5, ge=1, le=20)

class EquipmentCreate(EquipmentBase):
    budget_version_id: str

class EquipmentResponse(EquipmentBase):
    id: str
    budget_version_id: str

    class Config:
        from_attributes = True
```

**Step 4: Service Layer**

```python
# backend/app/services/equipment.py
from sqlalchemy.orm import Session
from typing import List
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentCreate

class EquipmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_version(self, version_id: str) -> List[Equipment]:
        return self.db.query(Equipment).filter(
            Equipment.budget_version_id == version_id
        ).all()

    def create(self, data: EquipmentCreate) -> Equipment:
        equipment = Equipment(id=str(uuid.uuid4()), **data.dict())
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment
```

**Step 5: API Endpoints**

```python
# backend/app/api/v1/planning/equipment.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.equipment import EquipmentCreate, EquipmentResponse
from app.services.equipment import EquipmentService

router = APIRouter()

@router.get("/{version_id}", response_model=List[EquipmentResponse])
async def get_equipment(version_id: str, db: Session = Depends(get_db)):
    service = EquipmentService(db)
    return service.get_by_version(version_id)

@router.post("/", response_model=EquipmentResponse, status_code=201)
async def create_equipment(data: EquipmentCreate, db: Session = Depends(get_db)):
    service = EquipmentService(db)
    return service.create(data)
```

**Step 6: Frontend Types**

```typescript
// frontend/src/lib/types/equipment.ts
export interface Equipment {
  id: string;
  budget_version_id: string;
  name: string;
  category: string;
  purchase_cost: number;
  purchase_date: string;
  useful_life_years: number;
}

export interface CreateEquipmentInput {
  budget_version_id: string;
  name: string;
  category: string;
  purchase_cost: number;
  purchase_date: string;
  useful_life_years: number;
}
```

**Step 7: API Client**

```typescript
// frontend/src/lib/api/equipment.ts
import { apiClient } from './client';
import type { Equipment, CreateEquipmentInput } from '@/lib/types/equipment';

export async function getEquipment(versionId: string): Promise<Equipment[]> {
  const response = await apiClient.get(`/planning/equipment/${versionId}`);
  return response.data;
}

export async function createEquipment(data: CreateEquipmentInput): Promise<Equipment> {
  const response = await apiClient.post('/planning/equipment', data);
  return response.data;
}
```

**Step 8: Frontend Component**

```typescript
// frontend/src/routes/planning/equipment.tsx
import { createFileRoute } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { getEquipment } from '@/lib/api/equipment';
import { EquipmentGrid } from '@/components/grids/EquipmentGrid';

export const Route = createFileRoute('/planning/equipment')({
  component: EquipmentPage,
});

function EquipmentPage() {
  const { data: equipment, isLoading } = useQuery({
    queryKey: ['equipment'],
    queryFn: () => getEquipment(versionId),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <PageHeader title="Equipment Tracking" />
      <EquipmentGrid data={equipment} />
    </div>
  );
}
```

**Step 9: Documentation**

Create `docs/MODULES/MODULE_19_EQUIPMENT.md` with:
- Overview
- Inputs
- Calculations (depreciation)
- Business rules
- Examples
- Testing scenarios

**Step 10: Tests**

```python
# backend/tests/unit/test_equipment.py
def test_create_equipment(db_session):
    service = EquipmentService(db_session)
    data = EquipmentCreate(
        budget_version_id="version-123",
        name="Laptop",
        category="IT",
        purchase_cost=5000.00,
        purchase_date=date(2025, 1, 1),
        useful_life_years=5,
    )
    equipment = service.create(data)
    assert equipment.id is not None
    assert equipment.name == "Laptop"
```

```typescript
// frontend/tests/unit/equipment.test.ts
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EquipmentPage } from '@/routes/planning/equipment';

describe('EquipmentPage', () => {
  it('renders equipment list', async () => {
    render(<EquipmentPage />);
    expect(await screen.findByText('Equipment Tracking')).toBeInTheDocument();
  });
});
```

---

## 7. Testing Strategy

### 7.1 Frontend Testing

**Unit Tests** (Vitest):
```typescript
// tests/unit/utils/calculations.test.ts
import { describe, it, expect } from 'vitest';
import { calculateClasses } from '@/lib/utils/calculations';

describe('calculateClasses', () => {
  it('calculates correct number of classes', () => {
    const enrollment = 76;
    const targetSize = 25;
    const result = calculateClasses(enrollment, targetSize);
    expect(result).toBe(4);
  });

  it('handles edge cases', () => {
    expect(calculateClasses(0, 25)).toBe(0);
    expect(calculateClasses(1, 25)).toBe(1);
    expect(calculateClasses(25, 25)).toBe(1);
    expect(calculateClasses(26, 25)).toBe(2);
  });
});
```

**Component Tests**:
```typescript
// tests/unit/components/EnrollmentForm.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EnrollmentForm } from '@/components/forms/EnrollmentForm';

describe('EnrollmentForm', () => {
  it('submits form with valid data', async () => {
    const onSubmit = vi.fn();
    render(<EnrollmentForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText('Level'), { target: { value: 'level-1' } });
    fireEvent.change(screen.getByLabelText('Student Count'), { target: { value: '25' } });
    fireEvent.click(screen.getByText('Save'));

    expect(onSubmit).toHaveBeenCalledWith({
      level_id: 'level-1',
      student_count: 25,
      // ...
    });
  });

  it('shows validation errors', async () => {
    render(<EnrollmentForm onSubmit={vi.fn()} />);

    fireEvent.click(screen.getByText('Save'));

    expect(await screen.findByText('Level is required')).toBeInTheDocument();
  });
});
```

**E2E Tests** (Playwright):
See [tests/e2e/*.spec.ts] for full E2E test suites.

### 7.2 Backend Testing

**Unit Tests** (pytest):
```python
# tests/unit/test_dhg_engine.py
import pytest
from app.engine.dhg import DHGEngine, DHGCalculationInput

def test_dhg_calculation():
    engine = DHGEngine()

    input_data = DHGCalculationInput(
        class_structure={"6eme": 5, "5eme": 5, "4eme": 4, "3eme": 4},
        subject_hours={
            ("math", "6eme"): 4.5,
            ("math", "5eme"): 3.5,
            ("math", "4eme"): 3.5,
            ("math", "3eme"): 3.5,
        },
        standard_hours={"secondary": 18},
    )

    result = engine.calculate(input_data)

    # 5*4.5 + 5*3.5 + 4*3.5 + 4*3.5 = 22.5 + 17.5 + 14 + 14 = 68 hours
    assert result.total_hours == 68.0

    # 68 / 18 = 3.78 FTE
    assert result.simple_fte == pytest.approx(3.78, 0.01)

    # Should recommend 4 teachers
    assert result.recommended_teachers == 4

    # HSA: 68 - (3 * 18) = 14 hours
    assert result.hsa_hours == 14.0

def test_h_e_ratio_validation():
    engine = DHGEngine()

    # Valid ratio for Collège
    assert engine.validate_h_e_ratio(1.40, "college") is True

    # Too low
    assert engine.validate_h_e_ratio(1.20, "college") is False

    # Too high
    assert engine.validate_h_e_ratio(1.60, "college") is False
```

**Integration Tests**:
```python
# tests/integration/test_enrollment_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_enrollment_plan(db_session, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    data = {
        "budget_version_id": "version-123",
        "level_id": "level-6eme",
        "nationality": "French",
        "student_count": 120,
        "period": "P2",
    }

    response = client.post("/api/v1/planning/enrollment", json=data, headers=headers)

    assert response.status_code == 201
    assert response.json()["student_count"] == 120

def test_enrollment_over_capacity(db_session, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    data = {
        "budget_version_id": "version-123",
        "level_id": "level-6eme",
        "nationality": "French",
        "student_count": 2000,  # Exceeds capacity
        "period": "P2",
    }

    response = client.post("/api/v1/planning/enrollment", json=data, headers=headers)

    assert response.status_code == 400
    assert "capacity" in response.json()["detail"].lower()
```

**Running Tests**:
```bash
# Backend
pytest                        # Run all tests
pytest --cov                 # With coverage
pytest -k test_dhg           # Run specific test
pytest tests/unit/           # Run unit tests only

# Frontend
pnpm test                    # Run Vitest
pnpm test:e2e                # Run Playwright
pnpm test:e2e:ui             # Playwright with UI
```

---

## 8. Deployment

### 8.1 Docker Deployment

See `/docker-compose.yml` and Docker files created in deployment section.

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop
docker-compose down
```

### 8.2 Environment Variables

**Production** (`.env.production`):
```env
# Backend
DATABASE_URL=postgresql://user:pass@db:5432/efir_budget
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key
JWT_SECRET=production-secret-key-change-me
ENVIRONMENT=production

# Frontend
VITE_API_BASE_URL=https://api.efir-budget.com/api/v1
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 8.3 CI/CD with GitHub Actions

See `.github/workflows/` for full CI/CD pipelines.

**Deployment Steps**:
1. Push to `main` branch
2. GitHub Actions triggers:
   - Run tests
   - Build Docker images
   - Push to container registry
   - Deploy to production
3. Automated smoke tests
4. Slack/email notification

---

## 9. Troubleshooting

### 9.1 Common Development Issues

**Issue**: `Cannot find module '@/components/...'`

**Solution**: Check `tsconfig.json` paths configuration:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

**Issue**: Database connection fails

**Solution**:
1. Check `.env.local` has correct `DATABASE_URL`
2. Verify PostgreSQL is running: `pg_isready`
3. Test connection: `psql $DATABASE_URL`
4. Check Supabase project status

---

**Issue**: CORS errors in browser

**Solution**: Add origin to backend CORS config:
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

**Issue**: Hot reload not working (Vite)

**Solution**:
1. Check file watcher limits: `ulimit -n` (should be >1024)
2. Increase limit: `ulimit -n 4096`
3. Restart Vite: `pnpm dev`

---

**Issue**: Type errors in backend

**Solution**: Run mypy and fix reported issues:
```bash
mypy app/
```

Common fixes:
- Add type hints to function parameters and return values
- Use `Optional[Type]` for nullable values
- Import types from `typing` module

---

### 9.2 Performance Optimization

**Frontend**:
- Use `React.memo()` for expensive components
- Implement virtual scrolling for large lists (AG Grid handles this)
- Lazy load routes with `React.lazy()`
- Optimize images (WebP format, lazy loading)
- Use TanStack Query's `staleTime` for caching

**Backend**:
- Add database indexes on frequently queried columns
- Use `select_related()` and `prefetch_related()` to avoid N+1 queries
- Implement Redis caching for expensive calculations
- Use async database operations
- Profile with `cProfile` to identify bottlenecks

---

### 9.3 Security Best Practices

- Never commit `.env` files to Git
- Use environment variables for secrets
- Implement Row Level Security (RLS) on all tables
- Validate all user inputs (Pydantic/Zod)
- Use parameterized queries (SQLAlchemy protects against SQL injection)
- Keep dependencies updated: `pip list --outdated`, `pnpm outdated`
- Implement rate limiting on API endpoints
- Use HTTPS in production
- Set secure headers (HSTS, CSP, X-Frame-Options)

---

## Appendix A: Useful Commands

**Frontend**:
```bash
pnpm install                 # Install dependencies
pnpm dev                     # Start dev server
pnpm build                   # Build for production
pnpm preview                 # Preview production build
pnpm test                    # Run unit tests
pnpm test:e2e                # Run E2E tests
pnpm lint                    # Run linter
pnpm lint:fix                # Fix linting errors
pnpm format                  # Format code with Prettier
pnpm typecheck               # TypeScript type check
```

**Backend**:
```bash
pip install -e ".[dev]"      # Install with dev dependencies
uvicorn app.main:app --reload  # Start dev server
pytest                       # Run tests
pytest --cov                 # Run tests with coverage
ruff check .                 # Run linter
ruff check --fix .           # Fix linting errors
mypy .                       # Type check
alembic upgrade head         # Run migrations
alembic revision --autogenerate -m "Message"  # Create migration
```

**Docker**:
```bash
docker-compose up --build    # Build and start
docker-compose down          # Stop and remove containers
docker-compose logs -f       # View logs
docker ps                    # List running containers
docker exec -it <container> bash  # Access container shell
```

---

**End of Developer Guide**
