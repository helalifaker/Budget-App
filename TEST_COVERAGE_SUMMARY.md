# Test Coverage Improvement Plan - Executive Summary

## Situation
- **Current Coverage:** ~30-35%
- **Target Coverage:** 90%
- **Gap:** 55-60 percentage points
- **Code to Test:** ~10,898 LOC (backend) + 822 LOC (frontend) = 11,720 LOC

## Solution Overview

A **5-phase, 6-week plan** to systematically improve test coverage from 30% to 90% by writing 750-950 new tests across:
- 11 frontend services (currently 0% tested)
- 14 backend services (currently 15% tested)
- 40+ frontend components (5 tested, 35+ untested)
- 16 frontend routes/pages (0% tested)

## Key Documents

### 1. TEST_COVERAGE_ROADMAP.md (Comprehensive Plan)
**Read this first** - Contains:
- Complete 5-phase breakdown
- Specific file paths for each service
- Test count estimates per file
- Real EFIR scenario examples
- Business rule validation patterns

### 2. WEEK1_ACTION_PLAN.md (Get Started Now)
**Start here immediately** - Contains:
- Ready-to-copy test templates
- Day-by-day task breakdown
- Copy-paste code examples
- Run commands and success criteria

### 3. This Document (Quick Reference)
Quick lookup for:
- File locations
- Effort estimates
- Priority order

---

## Phase Breakdown

| Phase | Focus | Effort | Tests | Coverage Gain | Timeline |
|-------|-------|--------|-------|---------------|----------|
| **1** | Frontend services & utils | 7-9h | 70-90 | +3.5% | Week 1 |
| **2** | Mid-sized backend services | 35-45h | 170-220 | +19% | Weeks 2-3 |
| **3** | Large complex services | 45-60h | 200-255 | +25% | Weeks 3-4 |
| **4** | Integration services | 25-35h | 210-270 | +26% | Weeks 4-5 |
| **5** | Components & routes | 30-40h | 100-120 | +10-12% | Weeks 5-6 |
| **TOTAL** | | **142-189h** | **750-955** | **83.5-90%** | **6 weeks** |

---

## Quick Reference: What to Test & Where

### Phase 1: Frontend Services (Week 1) - START HERE!

**Location:** `/home/user/Budget-App/frontend/tests/services/`

| Service File | LOC | Tests | Hours | Status |
|--------------|-----|-------|-------|--------|
| configuration.ts | 1.2K | 6 | 0.75 | Create |
| class-structure.ts | 1.4K | 6 | 0.75 | Create |
| enrollment.ts | 1.7K | 7 | 1.0 | Create |
| budget-versions.ts | 1.7K | 7 | 1.0 | Create |
| capex.ts | 1.8K | 7 | 1.0 | Create |
| costs.ts | 1.9K | 7 | 1.0 | Create |
| consolidation.ts | 1.9K | 7 | 1.0 | Create |
| revenue.ts | 1.9K | 7 | 1.0 | Create |
| strategic.ts | 2.0K | 8 | 1.0 | Create |
| analysis.ts | 2.2K | 8 | 1.0 | Create |
| dhg.ts | 2.7K | 10 | 1.25 | Create |
| **SUBTOTAL** | 20.3K | **81** | **10.75** | |
| Toast + errors | 400 LOC | 20 | 1 | Create |
| **PHASE 1 TOTAL** | | **~100** | **~11.75** | |

**Why Start Here?**
- Services are simple API wrappers
- No database access
- Easy to mock with `apiRequest`
- 1-2 hours per service
- High ROI (covers ~3.5% of code)

---

### Phase 2: Backend Services - Configuration Layer (Weeks 2-3)

**Location:** `/home/user/Budget-App/backend/tests/services/`

| Service | LOC | Tests | Hours | Priority | Key Complexity |
|---------|-----|-------|-------|----------|-----------------|
| **configuration_service.py** | 23.8K | 60-80 | 8-10 | **HIGH** | Business rules, validation |
| enrollment_service.py | 13.5K | 35-45 | 3-4 | HIGH | Projections, constraints |
| revenue_service.py | 15.2K | 40-50 | 4-5 | HIGH | Discounts, nationalities |
| class_structure_service.py | 15.0K | 35-45 | 3-4 | HIGH | Class formation logic |
| **PHASE 2 TOTAL** | | **170-220** | **35-45** | | |

---

### Phase 3: Large Complex Services (Weeks 3-4) - CRITICAL SERVICES

**Location:** `/home/user/Budget-App/backend/tests/services/`

| Service | LOC | Tests | Hours | Complexity | Why Important |
|---------|-----|-------|-------|------------|----------------|
| **writeback_service.py** | 36.0K | 80-100 | 12-15 | **VERY HIGH** | Core real-time editing, optimistic locking, conflicts |
| **consolidation_service.py** | 25.6K | 70-90 | 10-12 | **VERY HIGH** | Multi-module aggregation, approval workflow |
| **financial_statements_service.py** | 22.0K | 50-65 | 8-10 | HIGH | PCG/IFRS accounting, account codes |
| **PHASE 3 TOTAL** | | **200-255** | **45-60** | | |

---

### Phase 4: Integration Services (Weeks 4-5)

| Service | LOC | Tests | Hours |
|---------|-----|-------|-------|
| strategic_service.py | 23.3K | 50-65 | 6-8 |
| kpi_service.py | 22.3K | 50-65 | 6-8 |
| cost_service.py | 22.8K | 50-65 | 6-8 |
| dashboard_service.py | 18.4K | 30-40 | 4-5 |
| budget_actual_service.py | 19.8K | 30-40 | 4-5 |
| **PHASE 4 TOTAL** | | **210-270** | **25-35** |

---

### Phase 5: Frontend Components & Routes (Weeks 5-6)

| Category | Count | Tests | Hours |
|----------|-------|-------|-------|
| Data grid components | 4-5 | 30-40 | 3-4 |
| Dialog/Modal components | 4 | 20-30 | 2-3 |
| Display components | 10-15 | 20-30 | 2-3 |
| Routes/Pages | 10-14 | 20-30 | 3-4 |
| API Hooks | 15+ | 40-50 | 4-5 |
| **PHASE 5 TOTAL** | | **100-120** | **30-40** |

---

## Real EFIR Scenario Examples

Use these scenarios to ensure realistic test data:

### Enrollment Scenario (1,800 students)
```
Maternelle (PS, MS, GS): 300 students → 12 classes (25 each)
Élémentaire (CP-CM2): 450 students → 18 classes
Collège (6ème-3ème): 600 students → 24 classes
Lycée (2nde-Terminale): 450 students → 18 classes
TOTAL: 1,800 students, 72 classes
```

### Revenue Scenario
```
1,800 students × 35,000 SAR = 63,000,000 SAR annual revenue
Breakdown:
- French nationals (800): 44.4% - TTC pricing
- Saudi nationals (700): 38.9% - HT pricing
- Others (300): 16.7% - TTC pricing

Trimester split (revenue recognition):
- T1 (Sept-Nov): 40% = 25,200,000 SAR
- T2 (Dec-Feb): 30% = 18,900,000 SAR
- T3 (Mar-Jun): 30% = 18,900,000 SAR

Sibling discount (25% on tuition, not DAI):
- Child 3+: 25% off tuition only
```

### DHG Scenario (Secondary Workforce)
```
Collège Mathématiques (600 students, 4 levels):
- 6ème: 150 students, 6 classes × 4.5 hrs = 27 hours/week
- 5ème: 150 students, 6 classes × 3.5 hrs = 21 hours/week
- 4ème: 150 students, 6 classes × 3.5 hrs = 21 hours/week
- 3ème: 150 students, 6 classes × 3.5 hrs = 21 hours/week
TOTAL: 90 hours/week ÷ 18 standard hours = 5 teachers needed
```

---

## Success Indicators

### Weekly Milestones

**Week 1 (Phase 1):**
- ✅ All 11 frontend services tested (70-90 tests)
- ✅ Toast + error utilities tested
- ✅ Coverage: ~30% → 33%
- ✅ 0 test failures

**Week 2-3 (Phase 2):**
- ✅ 4 mid-sized backend services tested (170-220 tests)
- ✅ Configuration service fully covered
- ✅ Coverage: ~33% → 52%
- ✅ All tests passing

**Week 3-4 (Phase 3):**
- ✅ 3 large complex services tested (200-255 tests)
- ✅ Writeback service (critical) fully tested
- ✅ Coverage: ~52% → 77%
- ✅ All tests passing

**Week 4-5 (Phase 4):**
- ✅ 5 integration services tested (210-270 tests)
- ✅ Coverage: ~77% → 82%

**Week 5-6 (Phase 5):**
- ✅ Components and routes tested (100-120 tests)
- ✅ Coverage: ~82% → 90%
- ✅ All tests passing
- ✅ Ready for production

---

## Commands to Track Progress

```bash
# Frontend tests
cd /home/user/Budget-App/frontend
pnpm test -- --coverage                    # Run with coverage
pnpm test services                          # Run only service tests
pnpm test components                        # Run only component tests

# Backend tests
cd /home/user/Budget-App/backend
pytest --cov=app --cov-report=term-missing # Coverage report
pytest tests/services/                      # Only service tests
pytest tests/engine/                        # Only engine tests

# Code quality
pnpm lint                                   # Frontend ESLint
.venv/bin/ruff check .                      # Backend Ruff

# Type checking
pnpm typecheck                              # Frontend TypeScript
.venv/bin/mypy .                            # Backend mypy
```

---

## Critical Notes

### 1. Writeback Service is HIGHEST PRIORITY
- 36,049 LOC - largest service
- Handles all real-time editing with optimistic locking
- Most complex business logic
- 100+ tests needed
- Do in Phase 3 Week 1

### 2. Real EFIR Data in Tests
All tests should use real EFIR scenarios:
- Actual student counts (1,800)
- Real fee structures (35,000 SAR)
- Authentic teacher requirements
- Correct business rules

### 3. Follow EFIR Development Standards
Every test must have:
- Clear description of what's being tested
- Realistic EFIR scenario data
- All error cases covered
- Meaningful assertion messages

### 4. No Shortcuts
- All 80%+ coverage requirement
- No `any` types in TypeScript
- No skipped tests
- No TODO comments in code

---

## Next Steps (Right Now)

### Step 1: Read Documentation (30 minutes)
1. This summary
2. `TEST_COVERAGE_ROADMAP.md` (sections 1 & 2)
3. `WEEK1_ACTION_PLAN.md` (full)

### Step 2: Set Up Week 1 (15 minutes)
```bash
mkdir -p /home/user/Budget-App/frontend/tests/services
```

### Step 3: Start Week 1 (Start today!)
- Open `WEEK1_ACTION_PLAN.md`
- Follow Day 1 tasks
- Create first service test file
- Run `pnpm test`

### Step 4: Track Progress
- Update checklist in `WEEK1_ACTION_PLAN.md` daily
- Run coverage report at end of each day
- Report coverage gains weekly

---

## Expected Outcomes

By the end of 6 weeks:

**Quantitative:**
- 750-955 new tests written
- 90% code coverage achieved
- 0 failing tests
- All linting and type checks passing

**Qualitative:**
- Increased team confidence in code changes
- Better regression detection
- Clearer understanding of business logic
- Maintainable test suite using real EFIR scenarios
- CI/CD pipeline fully functional

**Project Health:**
- Ready for production deployment
- Refactoring with confidence
- Quick feedback on breaking changes
- Comprehensive regression testing

---

## Support & Questions

**If you encounter:**

1. **Service methods don't exist** → Check actual service file, might be named differently
2. **Mocking errors** → Review how `apiRequest` is mocked (see examples)
3. **Test failures** → Check fixture setup in conftest.py
4. **Coverage not improving** → May need more edge cases and error path tests
5. **Merge conflicts** → Tests are parallel work, coordinate with team

---

## Timeline Recommendation

**Start Date:** This week
**Phase 1 Duration:** 1 week (7-9 hours)
**Full Timeline:** 4-6 weeks (142-189 hours)

**Commit to Phase 1 first.** If it goes well and coverage increases as expected, continue with remaining phases.

---

Generated: December 3, 2025
Status: Ready for Implementation
Version: 1.0
