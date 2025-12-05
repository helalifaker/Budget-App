# Week 1 Action Plan: Quick Wins in Test Coverage

**Goal:** +3.5% coverage (from 30% to 33.5%)
**Effort:** 7-9 hours
**Tests to Write:** 70-90
**Outcome:** 11 Frontend services fully tested + Toast/Error utilities

---

## Quick Start: 30-Minute Setup

### Step 1: Create Directory Structure (2 minutes)

```bash
mkdir -p /home/user/Budget-App/frontend/tests/services
```

### Step 2: Copy-Paste Template Files (10 minutes)

Create the base test file that can be adapted for all services.

**File:** `/home/user/Budget-App/frontend/tests/services/service.test.template.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiRequest } from '@/lib/api-client'

// REPLACE WITH ACTUAL SERVICE
// import { [serviceApi] } from '@/services/[service-file]'

vi.mock('@/lib/api-client', () => ({
  apiRequest: vi.fn(),
}))

describe('[SERVICE_NAME]', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('GET Operations', () => {
    it('should fetch successfully', async () => {
      const mockData = { /* mock response */ }
      vi.mocked(apiRequest).mockResolvedValueOnce(mockData)

      // const result = await [serviceApi].get()

      // expect(result).toEqual(mockData)
      // expect(apiRequest).toHaveBeenCalledWith({
      //   method: 'GET',
      //   url: '/expected/endpoint',
      // })
    })

    it('should handle errors gracefully', async () => {
      const error = new Error('Network error')
      vi.mocked(apiRequest).mockRejectedValueOnce(error)

      // await expect([serviceApi].get()).rejects.toThrow('Network error')
    })
  })

  describe('POST Operations', () => {
    it('should create successfully', async () => {
      const mockData = { id: '123', /* fields */ }
      vi.mocked(apiRequest).mockResolvedValueOnce(mockData)

      // const result = await [serviceApi].create({ /* input */ })

      // expect(result).toEqual(mockData)
      // expect(apiRequest).toHaveBeenCalledWith({
      //   method: 'POST',
      //   url: '/expected/endpoint',
      //   data: { /* expected */ },
      // })
    })

    it('should handle validation errors', async () => {
      const error = new Error('Validation failed')
      vi.mocked(apiRequest).mockRejectedValueOnce(error)

      // await expect([serviceApi].create({})).rejects.toThrow()
    })
  })

  describe('PUT Operations', () => {
    it('should update successfully', async () => {
      const mockData = { id: '123', /* updated fields */ }
      vi.mocked(apiRequest).mockResolvedValueOnce(mockData)

      // const result = await [serviceApi].update('123', { /* changes */ })

      // expect(result).toEqual(mockData)
    })
  })

  describe('DELETE Operations', () => {
    it('should delete successfully', async () => {
      vi.mocked(apiRequest).mockResolvedValueOnce({ success: true })

      // await [serviceApi].delete('123')

      // expect(apiRequest).toHaveBeenCalledWith({
      //   method: 'DELETE',
      //   url: '/expected/endpoint/123',
      // })
    })

    it('should handle not found errors', async () => {
      const error = new Error('Not found')
      vi.mocked(apiRequest).mockRejectedValueOnce(error)

      // await expect([serviceApi].delete('invalid-id')).rejects.toThrow()
    })
  })
})
```

### Step 3: View Actual Service Files (5 minutes)

Let's look at one real service to understand the pattern:

```bash
cat /home/user/Budget-App/frontend/src/services/configuration.ts
```

This will show the actual API methods you need to test.

---

## Detailed Week 1 Plan: Service by Service

### Day 1: Setup + Smallest Services (4 hours)

#### Task 1.1: Create configuration.test.ts (45 minutes)

**File:** `/home/user/Budget-App/frontend/tests/services/configuration.test.ts`

Copy this exact content and adapt for the actual service methods:

```typescript
/**
 * Tests for Configuration Service
 *
 * Tests API calls for managing system configuration:
 * - Academic cycles (Maternelle, Élémentaire, Collège, Lycée)
 * - Academic levels (PS, MS, GS, CP, ..., Terminale)
 * - Subjects (Mathématiques, Français, etc.)
 * - Fee structure and nationality categories
 *
 * Coverage Target: 95%
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiRequest } from '@/lib/api-client'
import { configurationApi } from '@/services/configuration'

vi.mock('@/lib/api-client', () => ({
  apiRequest: vi.fn(),
}))

describe('Configuration Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Academic Cycles', () => {
    it('should fetch academic cycles successfully', async () => {
      const mockCycles = {
        items: [
          { id: '1', name_fr: 'Maternelle', code: 'MATERNELLE' },
          { id: '2', name_fr: 'Élémentaire', code: 'ELEMENTAIRE' },
          { id: '3', name_fr: 'Collège', code: 'COLLEGE' },
          { id: '4', name_fr: 'Lycée', code: 'LYCEE' },
        ],
        total: 4,
      }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockCycles)

      const result = await configurationApi.getAcademicCycles('budget-version-1')

      expect(result).toEqual(mockCycles)
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: '/configuration/academic-cycles/budget-version-1',
      })
    })

    it('should handle errors when fetching cycles', async () => {
      vi.mocked(apiRequest).mockRejectedValueOnce(new Error('Network error'))

      await expect(configurationApi.getAcademicCycles('budget-version-1')).rejects.toThrow(
        'Network error'
      )
    })

    it('should handle empty cycles list', async () => {
      const mockEmpty = { items: [], total: 0 }
      vi.mocked(apiRequest).mockResolvedValueOnce(mockEmpty)

      const result = await configurationApi.getAcademicCycles('budget-version-1')

      expect(result.items).toHaveLength(0)
      expect(result.total).toBe(0)
    })
  })

  describe('Academic Levels', () => {
    it('should fetch academic levels successfully', async () => {
      const mockLevels = {
        items: [
          { id: '1', code: '6ème', name_fr: 'Sixième', cycle_id: 'college' },
          { id: '2', code: '5ème', name_fr: 'Cinquième', cycle_id: 'college' },
        ],
        total: 2,
      }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockLevels)

      const result = await configurationApi.getAcademicLevels('budget-version-1', 'college')

      expect(result).toEqual(mockLevels)
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: '/configuration/academic-levels/budget-version-1?cycle_id=college',
      })
    })

    it('should filter by cycle', async () => {
      const mockLevels = {
        items: [{ id: '1', code: 'PS', name_fr: 'Petite Section' }],
        total: 1,
      }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockLevels)

      await configurationApi.getAcademicLevels('budget-version-1', 'maternelle')

      expect(apiRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: '/configuration/academic-levels/budget-version-1?cycle_id=maternelle',
      })
    })
  })

  describe('Subject Management', () => {
    it('should fetch subjects', async () => {
      const mockSubjects = {
        items: [
          { id: '1', name_fr: 'Mathématiques', code: 'MATH' },
          { id: '2', name_fr: 'Français', code: 'FR' },
        ],
        total: 2,
      }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockSubjects)

      const result = await configurationApi.getSubjects('budget-version-1')

      expect(result).toEqual(mockSubjects)
    })

    it('should create a subject', async () => {
      const mockResponse = {
        id: '123',
        name_fr: 'Anglais',
        code: 'EN',
      }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockResponse)

      const result = await configurationApi.createSubject('budget-version-1', {
        name_fr: 'Anglais',
        code: 'EN',
      })

      expect(result).toEqual(mockResponse)
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'POST',
        url: '/configuration/subjects',
        data: expect.objectContaining({
          version_id: 'budget-version-1',
          name_fr: 'Anglais',
          code: 'EN',
        }),
      })
    })

    it('should update a subject', async () => {
      const mockResponse = { id: '123', name_fr: 'Anglais Updated' }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockResponse)

      const result = await configurationApi.updateSubject('123', {
        name_fr: 'Anglais Updated',
      })

      expect(result).toEqual(mockResponse)
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'PUT',
        url: '/configuration/subjects/123',
        data: expect.objectContaining({
          name_fr: 'Anglais Updated',
        }),
      })
    })

    it('should delete a subject', async () => {
      vi.mocked(apiRequest).mockResolvedValueOnce({ success: true })

      await configurationApi.deleteSubject('123')

      expect(apiRequest).toHaveBeenCalledWith({
        method: 'DELETE',
        url: '/configuration/subjects/123',
      })
    })

    it('should handle subject not found error', async () => {
      vi.mocked(apiRequest).mockRejectedValueOnce(
        new Error('Subject not found')
      )

      await expect(configurationApi.updateSubject('invalid', {})).rejects.toThrow()
    })
  })

  describe('Fee Structure', () => {
    it('should fetch fee structure', async () => {
      const mockFees = {
        id: '1',
        tuition: 35000,
        dai: 1000,
        registration: 500,
      }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockFees)

      const result = await configurationApi.getFeeStructure('budget-version-1')

      expect(result).toEqual(mockFees)
    })

    it('should update fee structure', async () => {
      const mockResponse = {
        id: '1',
        tuition: 36000,
        dai: 1000,
      }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockResponse)

      const result = await configurationApi.updateFeeStructure('budget-version-1', {
        tuition: 36000,
      })

      expect(result.tuition).toBe(36000)
    })
  })
})
```

**Time:** 45 minutes

#### Task 1.2: Create class-structure.test.ts (45 minutes)

Same pattern, simpler file. Copy the template and adapt to the actual methods in `/home/user/Budget-App/frontend/src/services/class-structure.ts`

#### Task 1.3: Review and Run Tests (30 minutes)

```bash
cd /home/user/Budget-App/frontend

# Run tests
pnpm test configuration

# Should see output:
# ✓ Configuration Service (6 suites, 18 tests)
```

---

### Day 2: More Frontend Services (4 hours)

#### Task 2.1: enrollment.test.ts (1 hour)

Test methods for:
- `getEnrollmentData()`
- `createEnrollmentPlan()`
- `updateEnrollmentPlan()`
- `deleteEnrollmentPlan()`
- Error handling

#### Task 2.2: budget-versions.test.ts (1 hour)

Test methods for:
- `getVersions()`
- `createVersion()`
- `updateVersion()`
- `deleteVersion()`

#### Task 2.3: capex.test.ts (1 hour)

Test capital expenditure API methods

#### Task 2.4: Run All and Document (1 hour)

```bash
pnpm test services
```

---

### Day 3: Toast Messages & Consolidation (4 hours)

#### Task 3.1: Enhance toast-messages.test.ts (1.5 hours)

The test file likely exists partially. Add tests for:

```typescript
// Add these test cases to existing /frontend/src/lib/__tests__/toast-messages.test.ts

describe('Toast Messages - Error Handling', () => {
  it('should handle 401 unauthorized errors', () => {
    const error = {
      response: { status: 401 },
    }

    handleAPIErrorToast(error)

    // Verify auth error toast called
    expect(mockToastError).toHaveBeenCalledWith('Session expirée - Veuillez vous reconnecter')
  })

  it('should handle 403 forbidden errors', () => {
    const error = {
      response: { status: 403 },
    }

    handleAPIErrorToast(error)

    expect(mockToastError).toHaveBeenCalledWith("Vous n'avez pas les permissions nécessaires")
  })

  it('should handle 422 validation errors with detail message', () => {
    const error = {
      response: {
        status: 422,
        data: { detail: 'Email already exists' },
      },
    }

    handleAPIErrorToast(error)

    expect(mockToastError).toHaveBeenCalledWith('Validation échouée: Email already exists')
  })

  it('should handle 409 conflict errors', () => {
    const error = {
      response: {
        status: 409,
        data: { detail: 'Version mismatch' },
      },
    }

    handleAPIErrorToast(error)

    expect(mockToastError).toHaveBeenCalledWith('Conflit: Version mismatch')
  })

  it('should handle 500 server errors', () => {
    const error = {
      response: { status: 500 },
    }

    handleAPIErrorToast(error)

    expect(mockToastError).toHaveBeenCalledWith('Erreur serveur - Réessayez plus tard')
  })

  it('should handle network errors (no response)', () => {
    const error = new Error('Network error')

    handleAPIErrorToast(error)

    expect(mockToastError).toHaveBeenCalledWith('Erreur réseau - Vérifiez votre connexion')
  })

  it('should use custom message if provided', () => {
    const error = new Error('Some error')

    handleAPIErrorToast(error, 'Désolé, quelque chose s\'est mal passé')

    expect(mockToastError).toHaveBeenCalledWith('Désolé, quelque chose s\'est mal passé')
  })
})
```

#### Task 3.2: Create errors.test.ts (1.5 hours)

```typescript
// /home/user/Budget-App/frontend/tests/lib/errors.test.ts

import { describe, it, expect } from 'vitest'
import {
  isAPIError,
  isUnauthorizedError,
  isForbiddenError,
  isNotFoundError,
  isValidationError,
} from '@/lib/errors'

describe('Error Type Detection', () => {
  describe('isAPIError', () => {
    it('should detect axios error', () => {
      const error = {
        response: { status: 400, data: {} },
        isAxiosError: true,
      }

      expect(isAPIError(error)).toBe(true)
    })

    it('should return false for generic error', () => {
      expect(isAPIError(new Error('Generic error'))).toBe(false)
    })
  })

  describe('isUnauthorizedError', () => {
    it('should detect 401 errors', () => {
      const error = {
        response: { status: 401 },
        isAxiosError: true,
      }

      expect(isUnauthorizedError(error)).toBe(true)
    })
  })

  describe('isForbiddenError', () => {
    it('should detect 403 errors', () => {
      const error = {
        response: { status: 403 },
        isAxiosError: true,
      }

      expect(isForbiddenError(error)).toBe(true)
    })
  })

  describe('isNotFoundError', () => {
    it('should detect 404 errors', () => {
      const error = {
        response: { status: 404 },
        isAxiosError: true,
      }

      expect(isNotFoundError(error)).toBe(true)
    })
  })

  describe('isValidationError', () => {
    it('should detect 422 errors', () => {
      const error = {
        response: { status: 422, data: { detail: 'Validation failed' } },
        isAxiosError: true,
      }

      expect(isValidationError(error)).toBe(true)
    })
  })
})
```

#### Task 3.3: Remaining Services (1 hour)

Quick test creation for:
- costs.test.ts
- revenue.test.ts
- consolidation.test.ts
- analysis.test.ts
- strategic.test.ts
- dhg.test.ts

---

### Running Tests and Verification

After each day, run:

```bash
cd /home/user/Budget-App/frontend

# Run all tests in watch mode
pnpm test

# Generate coverage report
pnpm test -- --coverage

# Check linting
pnpm lint

# Type check
pnpm typecheck
```

---

## Checklist for Week 1

### Monday (Day 1)
- [ ] Create `/frontend/tests/services` directory
- [ ] Create `configuration.test.ts` with 6 test suites
- [ ] Create `class-structure.test.ts` with 5 test suites
- [ ] All tests passing: `pnpm test`
- [ ] No lint errors: `pnpm lint`

### Tuesday (Day 2)
- [ ] Create `enrollment.test.ts`
- [ ] Create `budget-versions.test.ts`
- [ ] Create `capex.test.ts`
- [ ] All 3 files passing tests
- [ ] Total: 3+ services tested

### Wednesday (Day 3)
- [ ] Create tests for remaining 6 services:
  - [ ] `costs.test.ts`
  - [ ] `revenue.test.ts`
  - [ ] `consolidation.test.ts`
  - [ ] `analysis.test.ts`
  - [ ] `strategic.test.ts`
  - [ ] `dhg.test.ts`
- [ ] Add toast messages tests
- [ ] Create `errors.test.ts`

### Thursday (Day 4)
- [ ] Review all tests
- [ ] Fix any failing tests
- [ ] Run full test suite: `pnpm test`
- [ ] Generate coverage: `pnpm test -- --coverage`
- [ ] Document results

### Friday (Day 5 - Review & Plan)
- [ ] All 11 services tested
- [ ] ~70-90 new tests written
- [ ] Coverage increase verified
- [ ] Review code quality
- [ ] Plan Phase 2

---

## Success Criteria for Week 1

✅ **Completion Checklist:**
- [ ] All 11 frontend services have test files
- [ ] Each service has 6-10 tests
- [ ] All tests passing (0 failures)
- [ ] Toast messages tests enhanced
- [ ] Error utilities tested
- [ ] No lint errors in tests
- [ ] Test files follow EFIR standards (clear descriptions, real data, comprehensive)
- [ ] Coverage increased from ~30% to ~33-34%

---

## Tips for Success

### 1. Use the Service Files as Guide
Before writing tests, read the actual service file to understand:
- Function signatures
- Parameters
- Return types
- Error cases

### 2. Mock `apiRequest` Consistently
All frontend services use `apiRequest`, so mocking is simple:
```typescript
vi.mocked(apiRequest).mockResolvedValueOnce(mockData)
```

### 3. Test Real Scenarios
Use realistic EFIR data in tests:
```typescript
// Good - realistic EFIR data
const mockEnrollment = {
  items: [
    { level: 'PS', students: 100 },
    { level: 'MS', students: 105 },
    { level: 'GS', students: 95 },
  ],
}

// Bad - nonsense data
const mockEnrollment = {
  items: [{ x: 'foo', y: 'bar' }],
}
```

### 4. Test Error Paths
Don't just test happy path - test errors:
```typescript
it('should handle errors', () => {
  vi.mocked(apiRequest).mockRejectedValueOnce(new Error('Network error'))
  await expect(service.fetch()).rejects.toThrow('Network error')
})
```

### 5. Keep Tests DRY
Use `beforeEach` to clear mocks:
```typescript
beforeEach(() => {
  vi.clearAllMocks()
})
```

---

## Phase 2 Preparation

After completing Week 1, you'll be ready for backend services. Start preparing:
- Read `test_dhg_service.py` to understand backend test patterns
- Review `conftest.py` fixtures available
- Identify which backend services to test first

**Next:** See `TEST_COVERAGE_ROADMAP.md` for Phase 2 detailed plan.
