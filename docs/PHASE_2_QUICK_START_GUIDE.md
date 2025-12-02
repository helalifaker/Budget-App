# Phase 2: Test Coverage Quick Start Guide

**For:** Developers implementing Phase 2 test coverage
**Goal:** 95% coverage in 5 weeks
**Start Date:** Immediately after Phase 1 completion

---

## Day 1: Setup & First Tests (8 hours)

### Morning: Fix Test Infrastructure (4 hours)

**1. Fix Backend Database Setup** (2h)

```bash
cd backend

# 1. Update conftest.py with auth schema setup
# File: backend/tests/conftest.py
# Add the auth schema creation code from the plan

# 2. Update pytest.ini
# Add: asyncio_default_fixture_loop_scope = function

# 3. Run tests to verify fix
pytest tests/services/test_configuration_service_TEMPLATE.py -v

# Expected: Errors should be gone
```

**2. Fix Frontend Test Config** (2h)

```bash
cd frontend

# 1. Separate Vitest and Playwright configs
# Edit vitest.config.ts to exclude E2E tests
# Edit playwright.config.ts for E2E only

# 2. Fix act() warnings in App.test.tsx
# Wrap async operations in waitFor()

# 3. Run tests to verify
pnpm test

# Expected: No act() warnings
```

### Afternoon: First DHG Service Tests (4 hours)

**1. Implement First Test Class** (2h)

```bash
# File: backend/tests/services/test_dhg_service.py (already created)

# Implement: TestDHGSubjectHoursCalculation
# - test_calculate_dhg_subject_hours_standard_case
# - test_calculate_dhg_subject_hours_zero_classes
```

**2. Run and Verify** (1h)

```bash
# Run specific test
pytest tests/services/test_dhg_service.py::TestDHGSubjectHoursCalculation -v

# Check coverage
pytest tests/services/test_dhg_service.py --cov=app.services.dhg_service --cov-report=term
```

**3. Commit Progress** (1h)

```bash
git add tests/services/test_dhg_service.py
git add tests/conftest.py
git commit -m "test: Add DHG service test infrastructure and first tests

- Fix database auth schema setup
- Add comprehensive DHG service test fixtures
- Implement subject hours calculation tests
- Current DHG service coverage: XX%"

git push
```

---

## Week 1: Backend P0 Services

### Daily Routine

**Morning (9am-12pm):**
1. Check coverage report from previous day
2. Review failing tests (if any)
3. Write tests for assigned module
4. Aim for 30-40 new test cases

**Afternoon (1pm-5pm):**
1. Run tests and fix failures
2. Check coverage improvement
3. Refactor if needed
4. Commit passing tests
5. Update progress report

### Daily Targets

| Day | Module | Start % | Target % | Tests to Write |
|-----|--------|---------|----------|----------------|
| 1 | DHG Service + Setup | 15.6% | 40% | 8-10 tests |
| 2 | DHG Service | 40% | 95% | 15-20 tests |
| 3 | Consolidation Service | 16.6% | 50% | 12-15 tests |
| 4 | Consolidation Service | 50% | 95% | 10-15 tests |
| 5 | Revenue + Cost Services | 14% | 95% | 20-25 tests |

### Running Tests

**Run all tests:**
```bash
cd backend
pytest
```

**Run specific module:**
```bash
pytest tests/services/test_dhg_service.py -v
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

**Run failed tests only:**
```bash
pytest --lf  # Last failed
```

**Run changed tests:**
```bash
pytest --ff  # Failed first
```

---

## Week 2: Frontend P0 Components

### Setup Day (Day 1)

**Morning: Fix Playwright (4h)**

```bash
cd frontend

# 1. Create separate playwright.config.ts
# 2. Update vitest.config.ts to exclude E2E
# 3. Move E2E tests to tests/e2e/
# 4. Run E2E tests separately

pnpm test:e2e
```

**Afternoon: Component Test Setup (4h)**

```bash
# 1. Create test fixtures
# File: frontend/tests/fixtures/index.ts (create similar to backend)

# 2. Update setupTests.ts with helpers

# 3. Run existing test
pnpm test src/App.test.tsx

# 4. Check coverage
pnpm test -- --coverage
```

### Daily Component Tests

| Day | Component/Hook | Tests to Write |
|-----|----------------|----------------|
| 2 | BudgetVersionSelector | 15-20 tests |
| 3 | DataTable (AG Grid) | 20-25 tests |
| 4 | useBudgetVersions | 10-12 tests |
| 5 | useDHG | 10-12 tests |

### Running Frontend Tests

**Run all unit tests:**
```bash
pnpm test
```

**Run with coverage:**
```bash
pnpm test -- --coverage
```

**Run specific file:**
```bash
pnpm test src/components/BudgetVersionSelector.test.tsx
```

**Run in watch mode:**
```bash
pnpm test -- --watch
```

**Run E2E tests:**
```bash
pnpm test:e2e
```

---

## Common Commands Reference

### Backend

```bash
# Activate virtual environment
cd backend
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .[dev]

# Run tests
pytest                                    # All tests
pytest -v                                 # Verbose
pytest --cov=app                          # With coverage
pytest --cov=app --cov-report=html        # HTML report
pytest -k "test_dhg"                      # Match pattern
pytest tests/services/                    # Specific directory
pytest --lf                               # Last failed
pytest --maxfail=1                        # Stop on first fail

# Coverage reports
coverage report                           # Terminal report
coverage html                             # Generate HTML
open htmlcov/index.html                   # View HTML

# Linting
ruff check .                              # Check
ruff check . --fix                        # Fix
mypy .                                    # Type check
```

### Frontend

```bash
# Install dependencies
cd frontend
pnpm install

# Run tests
pnpm test                                 # All unit tests
pnpm test -- --coverage                   # With coverage
pnpm test src/components/                 # Specific dir
pnpm test -- --watch                      # Watch mode
pnpm test:e2e                             # E2E tests
pnpm test:e2e -- --headed                 # E2E with browser

# Coverage
pnpm test -- --coverage
open coverage/index.html                  # View report

# Linting
pnpm lint                                 # Check
pnpm lint:fix                             # Fix
pnpm typecheck                            # Type check
```

---

## Troubleshooting

### Backend Issues

**Problem:** Foreign key errors
```bash
# Solution: Check auth schema exists
# File: backend/tests/conftest.py
# Ensure setup_test_db fixture is called
```

**Problem:** Async tests not running
```bash
# Solution: Add pytest marker
@pytest.mark.asyncio
async def test_something():
    ...
```

**Problem:** Fixtures not found
```bash
# Solution: Check conftest.py imports
# Ensure fixtures are in scope
```

### Frontend Issues

**Problem:** act() warnings
```bash
# Solution: Use waitFor()
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})
```

**Problem:** Mock not working
```bash
# Solution: Ensure vi.mock() is at top of file
vi.mock('@/hooks/api/useBudgetVersions', () => ({
  useBudgetVersions: vi.fn(),
}))
```

**Problem:** E2E tests hanging
```bash
# Solution: Check Playwright config
# Ensure correct testDir and baseURL
```

---

## Daily Checklist

### Before Starting

- [ ] Pull latest changes from main
- [ ] Check coverage report from previous day
- [ ] Review any failing tests
- [ ] Read test plan for today's module

### During Development

- [ ] Write tests following templates
- [ ] Run tests frequently (after each test)
- [ ] Check coverage incrementally
- [ ] Fix failures immediately
- [ ] Document any blockers

### Before Committing

- [ ] All tests passing
- [ ] Coverage increased
- [ ] No linting errors
- [ ] No type errors
- [ ] Code reviewed against EFIR standards

### Before End of Day

- [ ] Commit and push work
- [ ] Update progress in weekly report
- [ ] Note any blockers for team
- [ ] Plan next day's work

---

## Weekly Progress Tracking

### Week 1 Report Template

```markdown
# Test Coverage Progress - Week 1

## Summary
- **Overall Backend Coverage:** XX% (target: 70%)
- **DHG Service:** XX% (target: 95%)
- **Consolidation Service:** XX% (target: 95%)
- **Tests Written:** XX
- **Tests Passing:** XX

## Completed
- [x] Database setup fixed
- [x] DHG service tests (XX%)
- [ ] Consolidation service tests (in progress)

## Blockers
- None / [Issue description]

## Next Week
- Complete Consolidation service
- Start Revenue service
- Start Frontend setup
```

---

## Resources

### Documentation

**In Repository:**
- `/docs/PHASE_2_TEST_COVERAGE_PLAN.md` - Detailed plan
- `/docs/PHASE_2_TEST_IMPLEMENTATION_SUMMARY.md` - Overview
- `CLAUDE.md` - Development standards
- `EFIR_Module_Technical_Specification.md` - Business logic

**Test Templates:**
- `/backend/tests/services/test_dhg_service.py`
- `/frontend/tests/components/BudgetVersionSelector.test.tsx`
- `/backend/tests/fixtures/__init__.py`

### External Resources

**Backend Testing:**
- pytest: https://docs.pytest.org
- pytest-asyncio: https://pytest-asyncio.readthedocs.io
- pytest-cov: https://pytest-cov.readthedocs.io

**Frontend Testing:**
- Vitest: https://vitest.dev
- Testing Library: https://testing-library.com/docs/react-testing-library/intro
- Playwright: https://playwright.dev

**Best Practices:**
- AAA Pattern (Arrange, Act, Assert)
- Test behavior, not implementation
- One assertion per test (when possible)
- Clear test names
- Comprehensive fixtures

---

## Quick Tips

### Writing Effective Tests

**DO:**
- ✅ Use descriptive test names
- ✅ Test one thing per test
- ✅ Use fixtures for setup
- ✅ Test edge cases
- ✅ Test error conditions
- ✅ Use realistic data

**DON'T:**
- ❌ Test implementation details
- ❌ Skip error cases
- ❌ Use magic numbers
- ❌ Copy-paste tests
- ❌ Ignore warnings
- ❌ Skip documentation

### Coverage Tips

**Increase Coverage:**
1. Test all public methods
2. Test all branches (if/else)
3. Test error handling
4. Test edge cases
5. Test async operations

**Don't Chase 100%:**
- Focus on business logic
- Skip trivial getters/setters
- Skip generated code
- Skip external integrations (mock them)

---

## Getting Help

### Internal

**Documentation:**
1. Read test plan
2. Check templates
3. Review existing tests

**Team:**
1. Ask in team chat
2. Pair with another developer
3. Request code review

### External

**Stack Overflow:**
- pytest async
- vitest react hooks
- testing library best practices

**GitHub Issues:**
- pytest-asyncio
- vitest
- playwright

---

## Success Metrics

### Daily Metrics

Track in spreadsheet or project board:

| Date | Module | Tests Added | Tests Passing | Coverage % | Notes |
|------|--------|-------------|---------------|------------|-------|
| Day 1 | DHG | 8 | 8 | 40% | Setup complete |
| Day 2 | DHG | 15 | 23 | 95% | ✅ Complete |

### Weekly Metrics

| Week | Backend % | Frontend % | Overall % | On Track? |
|------|-----------|------------|-----------|-----------|
| 1 | 70% | 5% | 45% | ✅ Yes |
| 2 | 75% | 60% | 68% | ✅ Yes |

### Milestone Tracking

- [ ] Milestone 1: Backend P0 at 95% (End of Week 1)
- [ ] Milestone 2: Frontend P0 at 95% (End of Week 2)
- [ ] Milestone 3: P1 services at 95% (End of Week 3)
- [ ] Milestone 4: API layer at 95% (End of Week 4)
- [ ] Milestone 5: Overall 95% (End of Week 5)

---

**Good luck! Let's achieve 95% coverage!**

**Remember:**
- Quality over quantity
- Test behavior, not implementation
- Fix failures immediately
- Commit often
- Document as you go

**Questions?** Check the full test plan or ask the team!
