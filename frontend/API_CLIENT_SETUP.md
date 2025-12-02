# API Client & React Query Setup

## Overview

This document describes the API client and React Query setup implemented for the EFIR Budget App frontend.

## Files Created

### Core Configuration

1. **`src/lib/supabase.ts`**
   - Supabase client initialization
   - Authentication configuration
   - Session management

2. **`src/lib/api-client.ts`**
   - Axios instance with base configuration
   - Request interceptor for JWT token injection
   - Response interceptor for 401 handling
   - Generic `apiRequest<T>` function for type-safe requests

3. **`src/lib/query-client.ts`**
   - React Query client configuration
   - Default options for queries and mutations
   - Cache settings (5min staleTime, 10min gcTime)

4. **`src/lib/errors.ts`**
   - Error handling utilities
   - `handleAPIError()` for consistent error formatting
   - Type guards for error checking

### Type Definitions

5. **`src/types/api.ts`**
   - Zod schemas for API responses
   - TypeScript types inferred from schemas
   - Models: BudgetVersion, Enrollment, ClassStructure, Level, NationalityType, DHGEntry
   - Generic PaginatedResponse<T> type

### API Services

6. **`src/services/budget-versions.ts`**
   - CRUD operations for budget versions
   - Submit, approve, clone operations
   - Type-safe request/response handling

7. **`src/services/enrollment.ts`**
   - Enrollment data management
   - Bulk update operations
   - Projection calculations

8. **`src/services/class-structure.ts`**
   - Class structure CRUD
   - Auto-calculation from enrollment

9. **`src/services/configuration.ts`**
   - Levels, nationality types, cycles
   - Configuration data fetching

### React Query Hooks

10. **`src/hooks/api/useBudgetVersions.ts`**
    - Query hooks: `useBudgetVersions()`, `useBudgetVersion(id)`
    - Mutation hooks: `useCreateBudgetVersion()`, `useUpdateBudgetVersion()`, etc.
    - Query key factory: `budgetVersionKeys`

11. **`src/hooks/api/useEnrollment.ts`**
    - Enrollment queries and mutations
    - Bulk update and projection calculations
    - Cache invalidation on updates

12. **`src/hooks/api/useClassStructure.ts`**
    - Class structure management
    - Auto-calculation hooks

13. **`src/hooks/api/useConfiguration.ts`**
    - Configuration data queries
    - Extended staleTime (30 minutes) for rarely-changing data

14. **`src/hooks/api/index.ts`**
    - Centralized export of all hooks
    - Simplified imports

### UI Components

15. **`src/components/LoadingState.tsx`**
    - `LoadingState` - Full loading spinner
    - `LoadingSpinner` - Sized spinner (sm/md/lg)
    - `ErrorState` - Error message display
    - `EmptyState` - Empty data state
    - `SkeletonLoader` - Animated skeleton rows

### Authentication

16. **`src/contexts/AuthContext.tsx`**
    - AuthProvider component
    - useAuth hook
    - Supabase auth integration
    - Sign in/up/out methods

### Main Application

17. **`src/main.tsx`** (Updated)
    - QueryClientProvider with configured client
    - ReactQueryDevtools integration
    - AuthProvider wrapping

### Configuration

18. **`.env.example`**
    - Environment variable template
    - Supabase configuration
    - API base URL

## Dependencies Installed

```json
{
  "@tanstack/react-query": "5.80.0",
  "@tanstack/react-query-devtools": "5.80.0",
  "axios": "1.9.0",
  "zod": "3.24.0"
}
```

## Usage Examples

### Fetching Budget Versions

```typescript
import { useBudgetVersions } from '@/hooks/api'

function BudgetVersionsList() {
  const { data, isLoading, error } = useBudgetVersions(1, 50)

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState error={getErrorMessage(error)} />

  return (
    <div>
      {data?.items.map(version => (
        <div key={version.id}>{version.name}</div>
      ))}
    </div>
  )
}
```

### Creating a Budget Version

```typescript
import { useCreateBudgetVersion } from '@/hooks/api'
import { getErrorMessage } from '@/lib/errors'

function CreateBudgetForm() {
  const createVersion = useCreateBudgetVersion()

  const handleSubmit = async (formData) => {
    try {
      await createVersion.mutateAsync({
        name: formData.name,
        fiscal_year: formData.fiscal_year,
        academic_year: formData.academic_year,
      })
      // Success - cache will be automatically invalidated
    } catch (error) {
      console.error(getErrorMessage(error))
    }
  }

  return <form onSubmit={handleSubmit}>...</form>
}
```

### Using Configuration Data

```typescript
import { useLevels, useNationalityTypes } from '@/hooks/api'

function EnrollmentForm() {
  const { data: levels } = useLevels()
  const { data: nationalityTypes } = useNationalityTypes()

  // Configuration data is cached for 30 minutes
  return (
    <form>
      <select>
        {levels?.map(level => (
          <option key={level.id} value={level.id}>{level.name}</option>
        ))}
      </select>
    </form>
  )
}
```

### Optimistic Updates

```typescript
import { useUpdateEnrollment } from '@/hooks/api'
import { useQueryClient } from '@tanstack/react-query'
import { enrollmentKeys } from '@/hooks/api'

function EnrollmentEditor() {
  const queryClient = useQueryClient()
  const updateEnrollment = useUpdateEnrollment()

  const handleUpdate = async (id: string, studentCount: number) => {
    // Optimistic update
    queryClient.setQueryData(
      enrollmentKeys.detail(id),
      (old) => old ? { ...old, student_count: studentCount } : old
    )

    try {
      await updateEnrollment.mutateAsync({ id, data: { student_count: studentCount } })
    } catch (error) {
      // Rollback on error
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.detail(id) })
    }
  }

  return <div>...</div>
}
```

## Query Key Factories

Each hook module exports a query key factory for consistent cache management:

```typescript
// Budget Versions
budgetVersionKeys.all               // ['budget-versions']
budgetVersionKeys.lists()           // ['budget-versions', 'list']
budgetVersionKeys.list(filters)     // ['budget-versions', 'list', { filters }]
budgetVersionKeys.detail(id)        // ['budget-versions', 'detail', id]

// Enrollment
enrollmentKeys.byVersion(versionId) // ['enrollments', 'by-version', versionId]

// Configuration
configurationKeys.levels()          // ['configuration', 'levels']
configurationKeys.level(id)         // ['configuration', 'levels', id]
```

## Cache Invalidation Strategy

Mutations automatically invalidate related queries:

- **Create**: Invalidates list queries
- **Update**: Invalidates detail and list queries
- **Delete**: Invalidates list queries
- **Submit/Approve**: Invalidates detail and list queries

## Error Handling

All API errors are handled consistently:

```typescript
import { handleAPIError, getErrorMessage, isValidationError } from '@/lib/errors'

try {
  await apiRequest(...)
} catch (error) {
  const apiError = handleAPIError(error)
  console.log(apiError.message)
  console.log(apiError.code)
  
  if (isValidationError(error)) {
    // Handle validation errors (422)
  }
}
```

## Authentication Flow

1. User signs in via `useAuth().signIn(email, password)`
2. Supabase stores session in local storage
3. API client intercepts requests and adds JWT token
4. On 401 response, user is logged out and redirected to /login

## React Query Devtools

Devtools are available in development mode:
- Floating button in bottom-right corner
- Inspect queries, mutations, and cache
- Manually trigger refetches
- View query timeline

## Type Safety

All API calls are fully type-safe:

```typescript
// TypeScript knows the exact shape of the response
const { data } = useBudgetVersions()
// data is PaginatedResponse<BudgetVersion> | undefined

const version = await budgetVersionsApi.getById(id)
// version is BudgetVersion

// Mutations are also type-safe
const create = useCreateBudgetVersion()
create.mutate({
  name: "Budget 2025",
  fiscal_year: 2025,
  academic_year: "2024-2025",
  // notes: optional
})
```

## Environment Variables

Required environment variables (see `.env.example`):

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Next Steps

1. Create feature-specific UI components using these hooks
2. Implement forms with react-hook-form and zod validation
3. Add toast notifications for success/error states
4. Create data tables with AG Grid for bulk editing
5. Implement real-time subscriptions with Supabase Realtime

## Performance Considerations

- **StaleTime**: 5 minutes for regular data, 30 minutes for configuration
- **GcTime**: 10 minutes (data stays in cache after component unmount)
- **Retry**: 1 retry for queries, 0 for mutations
- **RefetchOnWindowFocus**: Disabled to prevent excessive requests

## Testing

To test the API client:

```typescript
// Mock the API client in tests
import { apiRequest } from '@/lib/api-client'

jest.mock('@/lib/api-client', () => ({
  apiRequest: jest.fn(),
}))

// Mock React Query
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

// Wrap component in provider
<QueryClientProvider client={queryClient}>
  <YourComponent />
</QueryClientProvider>
```

## Troubleshooting

### 401 Unauthorized
- Check Supabase session is valid
- Verify API base URL is correct
- Ensure backend is running

### CORS Errors
- Add frontend URL to backend CORS configuration
- Check API_BASE_URL environment variable

### Stale Data
- Use React Query Devtools to inspect cache
- Check staleTime configuration
- Manually invalidate queries if needed

### TypeScript Errors
- Ensure all API responses match Zod schemas
- Update schemas when backend changes
- Use schema validation in development
