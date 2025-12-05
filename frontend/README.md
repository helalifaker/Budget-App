# EFIR Budget Planning Frontend

React 19 + Vite + TypeScript 5.9 frontend for the EFIR Budget Planning Application, providing an enterprise-grade spreadsheet interface for workforce planning and budget management.

---

## 🤖 For AI Agents

**⚠️ CRITICAL: If you are an AI agent working on frontend code, read this section FIRST.**

### Relevant Agent for Frontend

| Agent | Responsibility | Boundaries |
|-------|---------------|------------|
| `frontend-ui-agent` | **All React components, pages, client-side logic, UI/UX** | ✅ CAN: Build React components, pages, hooks, UI logic<br>❌ CANNOT: Implement backend logic, modify database, create APIs, define business rules |

### Agent Boundary Rules

**CRITICAL ENFORCEMENT:**

1. **`frontend-ui-agent` MUST:**
   - Call backend APIs (via `backend-api-specialist`) for all data operations
   - NEVER implement calculation logic in client-side code
   - NEVER modify database schema or create migrations
   - NEVER create FastAPI endpoints
   - Use TanStack Query for server state management
   - Use React Hook Form + Zod for form validation

2. **`frontend-ui-agent` MUST NOT:**
   - Implement business logic (DHG calculations, revenue formulas, etc.)
   - Access database directly
   - Create backend API endpoints
   - Override business rules defined by `product-architect-agent`

### Frontend Code Organization

**Components** (`frontend/src/components/`):
- **Owner**: `frontend-ui-agent`
- **Pattern**: shadcn/ui style components with TypeScript strict mode
- **Structure**: `ui/` for base components, `features/` for feature-specific components

**Hooks** (`frontend/src/hooks/`):
- **Owner**: `frontend-ui-agent`
- **Pattern**: Custom React hooks for reusable logic
- **API Hooks**: Use TanStack Query for server state (see `hooks/api/`)

**API Client** (`frontend/src/services/`):
- **Owner**: `frontend-ui-agent`
- **Pattern**: API client functions that call `backend-api-specialist` endpoints
- **Example**: `services/api/enrollment.ts` - calls `/api/v1/planning/enrollment`

**Routes** (`frontend/src/routes/`):
- **Owner**: `frontend-ui-agent`
- **Pattern**: TanStack Router with lazy-loaded routes
- **Structure**: Organized by module layer (configuration/, planning/, consolidation/, etc.)

**State Management**:
- **Server State**: TanStack Query (calls backend APIs)
- **UI State**: React hooks (useState, useContext)
- **Form State**: React Hook Form + Zod validation

### Agent Workflow Examples

**Example 1: Building Enrollment Planning UI**
```
1. product-architect-agent → Provides enrollment business rules
2. backend-api-specialist → Creates /api/v1/planning/enrollment endpoint
3. frontend-ui-agent → Builds React component with AG Grid
4. frontend-ui-agent → Uses TanStack Query to fetch data from API
5. qa-validation-agent → Writes E2E tests with Playwright
```

**Example 2: Adding New Form Component**
```
1. frontend-ui-agent → Creates React component with React Hook Form
2. frontend-ui-agent → Uses Zod schema for validation (matches backend Pydantic schema)
3. frontend-ui-agent → Calls backend API via TanStack Query mutation
4. qa-validation-agent → Writes component tests with Vitest
```

**See [Agent Orchestration Guide](../.claude/AGENT_ORCHESTRATION.md) for complete workflow patterns.**

### Frontend Development Standards

All frontend agents MUST follow:
- **Type Safety**: TypeScript 5.9 strict mode, no `any` types
- **Component Patterns**: shadcn/ui style with `cva` for variants
- **State Management**: TanStack Query for server state, React hooks for UI state
- **Testing**: Vitest for unit tests, Playwright for E2E tests
- **Code Quality**: ESLint 9, Prettier, TypeScript strict checking

**See [CLAUDE.md](../CLAUDE.md) "EFIR Development Standards System" section for complete requirements.**

### Frontend-Backend Integration

**Data Flow Pattern:**
```
User Action → React Component → TanStack Query Hook → API Client → 
Backend API (backend-api-specialist) → Backend Engine (backend-engine-agent) → 
Database (database-supabase-agent) → Response → Frontend → UI Update
```

**CRITICAL**: Frontend NEVER implements calculation logic. All calculations happen in `backend-engine-agent` and are exposed via `backend-api-specialist`.

---

## Technology Stack

- **Framework**: React 19.2.0 (Server Components, Actions, Activity API ready)
- **Language**: TypeScript 5.9.3 (strict mode, deferred imports)
- **Build Tool**: Vite 7.2.6 (fast HMR, ESM-native, Environment API)
- **Styling**: Tailwind CSS 4.1.17 (with @tailwindcss/vite plugin)
- **Components**: shadcn/ui patterns (Radix UI primitives, TW v4 compatible)
- **Data Grid**: AG Grid Community 34.3.1 (enterprise spreadsheet UX)
- **Charts**: Recharts 3.4.1
- **Forms**: React Hook Form 7.67.0 + Zod 4.1.0 validation
- **State**: TanStack React Query 5.90.11 (server state caching)
- **Router**: TanStack Router 1.139.12 (type-safe routing)
- **Auth**: Supabase JS Client 2.49.0

## Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable UI components (shadcn/ui pattern)
│   │   ├── ui/            # Base components (Button, Input, Card, etc.)
│   │   └── features/      # Feature-specific components
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utilities and helpers
│   │   └── utils.ts       # cn() utility for Tailwind class merging
│   ├── pages/             # Route-level components (future)
│   ├── services/          # API client and data fetching
│   ├── stores/            # Global state (React Query)
│   ├── types/             # TypeScript type definitions
│   ├── App.tsx            # Root component
│   ├── main.tsx           # Entry point with providers
│   └── setupTests.ts      # Vitest/Testing Library setup
├── public/                # Static assets
├── eslint.config.js       # ESLint 9 flat config
├── vite.config.ts         # Vite configuration with path aliases
├── vitest.config.ts       # Vitest test configuration
├── tailwind.config.ts     # Tailwind 4 configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies and scripts
```

## Setup

### Prerequisites

- Node.js 20.x or higher
- pnpm (recommended) or npm

### Installation

```bash
# Install dependencies
pnpm install

# Create environment file
cp .env.example .env.local
# Edit .env.local with your Supabase credentials
```

### Environment Variables

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Development

```bash
# Start development server (http://localhost:5173)
pnpm dev

# Build for production
pnpm build

# Preview production build (http://localhost:4173)
pnpm preview
```

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start Vite dev server with HMR |
| `pnpm build` | Production build (TypeScript + Vite) |
| `pnpm preview` | Preview production build |
| `pnpm lint` | Run ESLint with flat config |
| `pnpm format` | Check Prettier formatting |
| `pnpm typecheck` | TypeScript type checking (`tsc --noEmit`) |
| `pnpm test` | Run Vitest in watch mode |
| `pnpm generate:types` | Generate TypeScript types from backend OpenAPI spec |
| `pnpm generate:types:file` | Generate types from saved `openapi.json` file |

## Code Quality

### ESLint Configuration

ESLint 9 with flat config (`eslint.config.js`):

- `@eslint/js` recommended rules
- `typescript-eslint` strict rules
- `eslint-plugin-react-hooks` for hooks rules
- Unused vars allowed with `_` prefix

### TypeScript

Strict mode enabled with:
- `strict: true`
- `noUncheckedIndexedAccess: true`
- `exactOptionalPropertyTypes: true`

### Path Aliases

Import from `@/` instead of relative paths:

```typescript
// ✅ Good
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// ❌ Avoid
import { Button } from '../../../components/ui/button';
```

## Testing

### Unit Tests (Vitest + Testing Library)

```bash
# Run tests in watch mode
pnpm test

# Run tests once (CI mode)
pnpm test -- --run

# Run with coverage
pnpm test -- --coverage

# Run with UI
pnpm test -- --ui
```

Test files use the pattern `*.test.tsx` and are co-located with source files.

### E2E Tests (Playwright)

```bash
# Install Playwright browsers
npx playwright install

# Run E2E tests
npx playwright test

# Run with UI mode
npx playwright test --ui

# Generate tests
npx playwright codegen localhost:5173
```

## Schema Synchronization (Frontend-Backend Alignment)

The frontend uses Zod schemas (`src/types/api.ts`) that must match the backend Pydantic schemas. To prevent drift, we provide automated tooling.

### Quick Reference

| Schema Change | Action Required |
|--------------|-----------------|
| Backend adds/removes fields | Run `pnpm generate:types`, update `api.ts` |
| Backend changes enum values | Update Zod enum in `api.ts` |
| Zod validation errors in console | Check schema alignment |
| React key warnings | Check `id` field mapping |

### OpenAPI Type Generation

Generate TypeScript types from the backend's OpenAPI specification:

```bash
# Start the backend server first
cd ../backend && uvicorn app.main:app --reload

# Generate types (in another terminal)
cd ../frontend
pnpm generate:types  # From running server at localhost:8000
# OR
pnpm generate:types:file  # From saved openapi.json file
```

Generated types are saved to `src/types/generated-api.ts`. Compare with hand-written Zod schemas in `api.ts` to detect drift.

### Schema Testing

Schema validation tests in `tests/schemas/api-schemas.test.ts` catch drift early:

```bash
pnpm test -- tests/schemas/api-schemas.test.ts --run
```

These tests:
- Validate all status enum values match backend (lowercase: `working`, `submitted`, etc.)
- Verify bilingual field names (`name_fr`, `name_en` not `name`)
- Check required fields exist (`is_secondary`, `requires_atsem`, etc.)
- Include drift detection tests that fail on old schema formats

### Helper Utilities

The `src/utils/schema-sync.ts` module provides:

```typescript
import { getDisplayName, isValidBudgetVersionStatus, getStatusConfig } from '@/utils/schema-sync'

// Bilingual entity display
const levelName = getDisplayName(level, 'en')  // or 'fr'

// Status validation
if (isValidBudgetVersionStatus(status)) { /* ... */ }

// Status display config
const { label, variant, canEdit } = getStatusConfig('working')
```

### Key Schema Patterns

**Bilingual Entities** (Level, Cycle, Subject, NationalityType):
```typescript
// Backend returns: { name_fr: "...", name_en: "..." }
// Use: entity.name_en (or helper for i18n)
```

**Status Enum** (BudgetVersionStatus):
```typescript
// Backend returns lowercase: "working", "submitted", "approved", "forecast", "superseded"
// Frontend must use lowercase comparisons
if (version.status === 'working') { /* ... */ }
```

**Sort Order** (not display_order):
```typescript
// Backend uses: sort_order
// NOT: display_order
items.sort((a, b) => a.sort_order - b.sort_order)
```

## AG Grid Integration

AG Grid Community 34.3.1 provides enterprise-grade spreadsheet functionality:

```tsx
import { AgGridReact } from 'ag-grid-react';
import { ColDef } from 'ag-grid-community';

const columnDefs: ColDef[] = [
  { field: 'level', headerName: 'Level', sortable: true, filter: true },
  { field: 'enrollment', headerName: 'Enrollment', editable: true },
  { field: 'classes', headerName: 'Classes', valueGetter: calculateClasses },
];

function EnrollmentGrid({ data }) {
  return (
    <div className="ag-theme-quartz h-[600px]">
      <AgGridReact
        rowData={data}
        columnDefs={columnDefs}
        defaultColDef={{ flex: 1, minWidth: 100 }}
      />
    </div>
  );
}
```

### AG Grid Features Used

- **Sorting & Filtering**: Built-in column sorting and filtering
- **Cell Editing**: Inline editing for budget data entry
- **Custom Renderers**: Custom cell components for status, actions
- **Theme**: `ag-theme-quartz` for modern styling
- **Virtualization**: Efficient rendering for large datasets

## React Query Setup

Server state management with TanStack Query:

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetch enrollment data
const { data, isLoading } = useQuery({
  queryKey: ['enrollment', budgetVersionId],
  queryFn: () => fetchEnrollment(budgetVersionId),
});

// Update enrollment
const mutation = useMutation({
  mutationFn: updateEnrollment,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['enrollment'] });
  },
});
```

## Form Handling

React Hook Form + Zod for type-safe forms:

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  levelId: z.string().min(1, 'Level is required'),
  enrollment: z.number().int().positive(),
});

type FormData = z.infer<typeof schema>;

function EnrollmentForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });
  // ...
}
```

## Component Patterns

### shadcn/ui Style Components

```tsx
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        outline: 'border border-input hover:bg-accent',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3',
        lg: 'h-11 px-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button className={cn(buttonVariants({ variant, size, className }))} {...props} />
  );
}
```

## Module Architecture

The frontend implements UI for all 18 backend modules:

| Layer | Modules | Frontend Features |
|-------|---------|-------------------|
| Configuration | 1-6 | Master data forms, parameter grids |
| Planning | 7-12 | Enrollment grid, DHG calculator, cost planning |
| Consolidation | 13-14 | Budget workflow UI, statement viewer |
| Analysis | 15-17 | KPI dashboards, charts, variance analysis |
| Strategic | 18 | 5-year planning interface |

## License

Internal use only - EFIR School Budget Planning Application
