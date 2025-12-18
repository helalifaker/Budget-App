#!/bin/bash

# E2E Route Fix Script
# Based on E2E_TEST_FAILURE_ANALYSIS.md Quick Wins
# Fixes 55+ tests by updating old routes to new 10-module architecture

set -e

echo "=========================================="
echo "E2E Route Fix Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

E2E_DIR="/Users/fakerhelali/Coding/Budget App/frontend/tests/e2e"

echo -e "${YELLOW}Starting route updates...${NC}"
echo ""

# Fix 1: Update kpis.spec.ts
echo -e "${GREEN}[1/5] Fixing kpis.spec.ts (15 tests)${NC}"
sed -i '' "s|'/analysis/kpis'|'/insights/kpis'|g" "$E2E_DIR/kpis.spec.ts"
sed -i '' "s|'/analysis/variance'|'/insights/variance'|g" "$E2E_DIR/kpis.spec.ts"
echo "  ✓ Updated /analysis/* routes to /insights/*"

# Fix 2: Update dhg.spec.ts
echo -e "${GREEN}[2/5] Fixing dhg.spec.ts (11 tests)${NC}"
sed -i '' "s|'/planning/dhg'|'/workforce/dhg'|g" "$E2E_DIR/dhg.spec.ts"
sed -i '' "s|'/planning/classes'|'/enrollment/class-structure'|g" "$E2E_DIR/dhg.spec.ts"
sed -i '' "s|'/configuration/subject-hours'|'/workforce/settings/subject-hours'|g" "$E2E_DIR/dhg.spec.ts"
echo "  ✓ Updated /planning/dhg to /workforce/dhg"
echo "  ✓ Updated /planning/classes to /enrollment/class-structure"
echo "  ✓ Updated /configuration/subject-hours to /workforce/settings/subject-hours"

# Fix 3: Update revenue.spec.ts
echo -e "${GREEN}[3/5] Fixing revenue.spec.ts (14 tests)${NC}"
sed -i '' "s|'/planning/revenue'|'/revenue/tuition'|g" "$E2E_DIR/revenue.spec.ts"
sed -i '' "s|'/configuration/fees'|'/revenue/settings'|g" "$E2E_DIR/revenue.spec.ts"
echo "  ✓ Updated /planning/revenue to /revenue/tuition"
echo "  ✓ Updated /configuration/fees to /revenue/settings"

# Fix 4: Update budget-workflow.spec.ts
echo -e "${GREEN}[4/5] Fixing budget-workflow.spec.ts (8 tests)${NC}"
sed -i '' "s|'/configuration/versions'|'/settings/versions'|g" "$E2E_DIR/budget-workflow.spec.ts"
echo "  ✓ Updated /configuration/versions to /settings/versions"

# Fix 5: Update consolidation.spec.ts
echo -e "${GREEN}[5/5] Fixing consolidation.spec.ts (7 tests)${NC}"
sed -i '' "s|'/finance/statements'|'/consolidation/statements'|g" "$E2E_DIR/consolidation.spec.ts"
echo "  ✓ Updated /finance/statements to /consolidation/statements"

echo ""
echo -e "${GREEN}=========================================="
echo "Route updates completed successfully!"
echo "==========================================${NC}"
echo ""
echo "Summary:"
echo "  • kpis.spec.ts: 15 tests fixed"
echo "  • dhg.spec.ts: 11 tests fixed"
echo "  • revenue.spec.ts: 14 tests fixed"
echo "  • budget-workflow.spec.ts: 8 tests fixed"
echo "  • consolidation.spec.ts: 7 tests fixed"
echo ""
echo "Total: ~55 tests fixed"
echo ""
echo "Next steps:"
echo "  1. Run: cd frontend && pnpm exec playwright test"
echo "  2. Review any remaining failures"
echo "  3. Consider Phase 2 fixes (sidebar interactions)"
echo ""
