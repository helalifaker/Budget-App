# Type Contract: OpenAPI Type Generation

> Technical decision document defining how frontend types are kept in sync with backend schemas.

**Date**: 2025-12-16
**Status**: Approved
**Authors**: Development Team

---

## Overview

The EFIR Budget App uses **OpenAPI type generation** to maintain a single source of truth for API types. Backend Pydantic schemas automatically generate OpenAPI specifications, which are then converted to TypeScript types for the frontend.

```
Backend (FastAPI/Pydantic)
         ↓
    OpenAPI Spec (/openapi.json)
         ↓
    openapi-typescript
         ↓
Frontend (TypeScript types)
```

---

## How It Works

### Backend: Schema Definition

Pydantic models in `backend/app/schemas/` define the API contract:

```python
# backend/app/schemas/enrollment.py
from pydantic import BaseModel

class EnrollmentProjectionResponse(BaseModel):
    id: str
    version_id: str
    academic_year: str
    total_students: int

    model_config = ConfigDict(from_attributes=True)
```

FastAPI automatically generates OpenAPI spec from these models.

### Frontend: Type Generation

Run the generation command:

```bash
# From frontend directory
pnpm generate:types

# Or with local file (for CI/offline)
pnpm generate:types:file
```

This produces `src/types/generated-api.ts`:

```typescript
// AUTO-GENERATED - DO NOT EDIT
export interface components {
  schemas: {
    EnrollmentProjectionResponse: {
      id: string;
      version_id: string;
      academic_year: string;
      total_students: number;
    };
  };
}
```

---

## Type Organization

### Directory Structure

```
frontend/src/types/
├── generated-api.ts        # AUTO-GENERATED - DO NOT EDIT
├── api.ts                  # Re-exports + Zod runtime validation
├── enrollment-projection.ts # Domain-specific extensions
├── enrollment-settings.ts   # Domain-specific extensions
├── workforce.ts             # Domain-specific extensions
├── historical.ts            # Domain-specific extensions
├── writeback.ts             # Domain-specific extensions
└── index.ts                 # Barrel export (optional)
```

### File Purposes

| File | Purpose | Editable? |
|------|---------|-----------|
| `generated-api.ts` | Raw OpenAPI types | NO - auto-generated |
| `api.ts` | Re-exports with friendly names + Zod schemas | YES |
| `{domain}.ts` | Domain-specific extensions, UI-only fields | YES |

### Pattern for Domain Files

```typescript
// enrollment-projection.ts
import type { components } from './generated-api';

// Re-export with friendly name
export type EnrollmentProjection = components['schemas']['EnrollmentProjectionResponse'];
export type EnrollmentProjectionCreate = components['schemas']['EnrollmentProjectionCreate'];

// Frontend-only extensions (not in API)
export interface EnrollmentProjectionUI extends EnrollmentProjection {
  isEditing?: boolean;
  isDirty?: boolean;
  validationErrors?: string[];
}

// Form state types
export interface EnrollmentProjectionFormData {
  academicYear: string;
  gradeOverrides: Record<string, number>;
}
```

---

## Workflow

### Development Workflow

1. **Backend developer** modifies Pydantic schema
2. **Backend developer** runs `uv run uvicorn app.main:app --reload`
3. **Frontend developer** runs `pnpm generate:types`
4. **TypeScript compiler** reports any breaking changes
5. **Frontend developer** updates code to match new types

### CI/CD Workflow

```yaml
# .github/workflows/type-check.yml
- name: Start backend
  run: |
    cd backend
    uv run uvicorn app.main:app &
    sleep 5

- name: Generate types
  run: |
    cd frontend
    pnpm generate:types

- name: Check for uncommitted changes
  run: |
    git diff --exit-code frontend/src/types/generated-api.ts
```

---

## Commands

### Package.json Scripts

```json
{
  "scripts": {
    "generate:types": "openapi-typescript http://localhost:8000/openapi.json -o src/types/generated-api.ts",
    "generate:types:file": "openapi-typescript openapi.json -o src/types/generated-api.ts"
  }
}
```

### When to Regenerate

- After modifying any `backend/app/schemas/*.py`
- After adding new API endpoints
- After changing response models
- Before committing frontend changes that depend on API types

---

## Best Practices

### DO

- Always regenerate types after backend schema changes
- Use generated types as the base, extend for UI-only fields
- Keep domain extension files organized by module
- Use Zod for runtime validation when needed

### DON'T

- Never manually edit `generated-api.ts`
- Don't duplicate types that exist in generated file
- Don't add backend fields to extension interfaces
- Don't skip type regeneration before commits

---

## Troubleshooting

### Types not matching API response

1. Ensure backend is running: `uv run uvicorn app.main:app --reload`
2. Regenerate types: `pnpm generate:types`
3. Check OpenAPI spec: http://localhost:8000/openapi.json

### Generation fails

```bash
# Check backend is responding
curl http://localhost:8000/openapi.json

# Use file-based generation if backend unavailable
curl http://localhost:8000/openapi.json > openapi.json
pnpm generate:types:file
```

### Type errors after regeneration

1. Check if backend renamed/removed fields
2. Update domain extension files to match
3. Update component code using affected types

---

## Tool Configuration

### openapi-typescript

Version: `^7.10.1` (as of 2025-12)

The tool automatically handles:
- Nullable types → `| null`
- Optional fields → `?:`
- Enum types → string unions
- Nested objects → nested interfaces

### Alternative: Zod for Runtime Validation

For cases requiring runtime type checking:

```typescript
// api.ts
import { z } from 'zod';

export const EnrollmentProjectionSchema = z.object({
  id: z.string().uuid(),
  version_id: z.string().uuid(),
  academic_year: z.string(),
  total_students: z.number().int().min(0),
});

export type EnrollmentProjection = z.infer<typeof EnrollmentProjectionSchema>;
```

---

## References

- [openapi-typescript docs](https://openapi-ts.dev/)
- [FastAPI OpenAPI docs](https://fastapi.tiangolo.com/features/#automatic-docs)
- [DOMAIN_BOUNDARIES.md](./DOMAIN_BOUNDARIES.md) - Module naming conventions
