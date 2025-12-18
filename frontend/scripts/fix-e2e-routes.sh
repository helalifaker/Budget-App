#!/bin/bash

# E2E Test Route Fix Script
# Automatically updates old route paths to new 10-module architecture
# Run from frontend/ directory: bash scripts/fix-e2e-routes.sh

set -e

echo "🔧 Fixing E2E test routes for 10-module architecture..."
echo ""

cd "$(dirname "$0")/.."

# Backup tests directory first
echo "📦 Creating backup..."
cp -r tests/e2e tests/e2e.backup.$(date +%Y%m%d_%H%M%S)

echo "✅ Backup created"
echo ""

# Fix 1: kpis.spec.ts (15 tests)
echo "🔄 Fixing kpis.spec.ts..."
sed -i '' "s|'/analysis/kpis'|'/insights/kpis'|g" tests/e2e/kpis.spec.ts
sed -i '' "s|'/analysis/variance'|'/insights/variance'|g" tests/e2e/kpis.spec.ts
sed -i '' 's|"/analysis/kpis"|"/insights/kpis"|g' tests/e2e/kpis.spec.ts
sed -i '' 's|"/analysis/variance"|"/insights/variance"|g' tests/e2e/kpis.spec.ts
echo "  ✅ Updated /analysis/* → /insights/*"

# Fix 2: dhg.spec.ts (11 tests)
echo "🔄 Fixing dhg.spec.ts..."
sed -i '' "s|'/planning/dhg'|'/workforce/dhg'|g" tests/e2e/dhg.spec.ts
sed -i '' "s|'/planning/classes'|'/enrollment/class-structure'|g" tests/e2e/dhg.spec.ts
sed -i '' "s|'/configuration/subject-hours'|'/workforce/settings/subject-hours'|g" tests/e2e/dhg.spec.ts
echo "  ✅ Updated /planning/dhg → /workforce/dhg"
echo "  ✅ Updated /planning/classes → /enrollment/class-structure"
echo "  ✅ Updated /configuration/subject-hours → /workforce/settings/subject-hours"

# Fix 3: revenue.spec.ts (14 tests)
echo "🔄 Fixing revenue.spec.ts..."
sed -i '' "s|'/planning/revenue'|'/revenue/tuition'|g" tests/e2e/revenue.spec.ts
sed -i '' "s|'/configuration/fees'|'/revenue/settings'|g" tests/e2e/revenue.spec.ts
sed -i '' "s|'/finance/revenue'|'/revenue/tuition'|g" tests/e2e/revenue.spec.ts
sed -i '' "s|'/finance/settings'|'/revenue/settings'|g" tests/e2e/revenue.spec.ts
echo "  ✅ Updated /planning/revenue → /revenue/tuition"
echo "  ✅ Updated /configuration/fees → /revenue/settings"

# Fix 4: budget-workflow.spec.ts (8 tests)
echo "🔄 Fixing budget-workflow.spec.ts..."
sed -i '' "s|'/configuration/versions'|'/settings/versions'|g" tests/e2e/budget-workflow.spec.ts
echo "  ✅ Updated /configuration/versions → /settings/versions"

# Fix 5: consolidation.spec.ts (7 tests)
echo "🔄 Fixing consolidation.spec.ts..."
sed -i '' "s|'/finance/statements'|'/consolidation/statements'|g" tests/e2e/consolidation.spec.ts
echo "  ✅ Updated /finance/statements → /consolidation/statements"

# Fix 6: accessibility.spec.ts (4 tests)
echo "🔄 Fixing accessibility.spec.ts..."
sed -i '' "s|'/planning/enrollment'|'/enrollment/projections'|g" tests/e2e/accessibility.spec.ts
sed -i '' "s|'/planning/dhg'|'/workforce/dhg'|g" tests/e2e/accessibility.spec.ts
sed -i '' "s|'/analysis/kpis'|'/insights/kpis'|g" tests/e2e/accessibility.spec.ts
sed -i '' "s|'/configuration/versions'|'/settings/versions'|g" tests/e2e/accessibility.spec.ts
echo "  ✅ Updated multiple route paths"

# Fix 7: subject-hours.spec.ts (3 tests)
echo "🔄 Fixing subject-hours.spec.ts..."
sed -i '' "s|'/configuration/subject-hours'|'/workforce/settings/subject-hours'|g" tests/e2e/subject-hours.spec.ts
echo "  ✅ Updated /configuration/subject-hours → /workforce/settings/subject-hours"

# Fix 8: auth.spec.ts (2 tests)
echo "🔄 Fixing auth.spec.ts..."
sed -i '' "s|'/configuration/versions'|'/settings/versions'|g" tests/e2e/auth.spec.ts
echo "  ✅ Updated /configuration/versions → /settings/versions"

# Fix 9: integrations.spec.ts (1 test)
echo "🔄 Fixing integrations.spec.ts..."
sed -i '' "s|'/planning/enrollment'|'/enrollment/projections'|g" tests/e2e/integrations.spec.ts
echo "  ✅ Updated /planning/enrollment → /enrollment/projections"

# Fix 10: historical-import.spec.ts (2 tests)
echo "🔄 Fixing historical-import.spec.ts..."
sed -i '' "s|'/planning/revenue'|'/revenue/tuition'|g" tests/e2e/historical-import.spec.ts
echo "  ✅ Updated /planning/revenue → /revenue/tuition"

# Fix 11: Update Page Objects
echo "🔄 Fixing page objects..."
sed -i '' "s|'/configuration/versions'|'/settings/versions'|g" tests/e2e/pages/VersionPage.ts 2>/dev/null || true
sed -i '' "s|'/planning/enrollment'|'/enrollment/projections'|g" tests/e2e/pages/EnrollmentPage.ts 2>/dev/null || true
echo "  ✅ Updated page object paths"

echo ""
echo "✨ Route fixes complete!"
echo ""
echo "📊 Expected improvements:"
echo "  • kpis.spec.ts: ~15 tests fixed"
echo "  • dhg.spec.ts: ~11 tests fixed"
echo "  • revenue.spec.ts: ~14 tests fixed"
echo "  • budget-workflow.spec.ts: ~8 tests fixed"
echo "  • consolidation.spec.ts: ~7 tests fixed"
echo "  • Other files: ~10 tests fixed"
echo "  • Total: ~65 tests fixed (97% of failures)"
echo ""
echo "🧪 Next steps:"
echo "  1. Run: pnpm test:e2e"
echo "  2. Check for remaining failures"
echo "  3. Review logs at: playwright-report/"
echo ""
echo "📝 If something went wrong, restore from backup:"
echo "  rm -rf tests/e2e && mv tests/e2e.backup.* tests/e2e"
echo ""
