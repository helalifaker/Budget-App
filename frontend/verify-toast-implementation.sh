#!/bin/bash

# Toast Notification Standardization Verification Script
# Phase 1.4 - EFIR Budget App

echo "================================"
echo "Toast Standardization Verification"
echo "================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Success counter
SUCCESS=0
FAIL=0

# 1. Check toast-messages.ts exists
echo -n "1. Checking toast-messages.ts exists... "
if [ -f "src/lib/toast-messages.ts" ]; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

# 2. Check no direct toast calls remain (excluding toast-messages.ts and backups)
echo -n "2. Checking no direct toast calls remain... "
DIRECT_CALLS=$(grep -r "toast\.(success|error|warning|info|loading)" src --include="*.ts" --include="*.tsx" | grep -v "toast-messages.ts" | grep -v ".bak" | grep -v "backup" | wc -l)
if [ "$DIRECT_CALLS" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} (0 direct calls found)"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC} ($DIRECT_CALLS direct calls found)"
    ((FAIL++))
fi

# 3. Check toastMessages is imported in hooks
echo -n "3. Checking toastMessages imports in hooks... "
HOOKS_WITH_TOAST=$(grep -l "from '@/lib/toast-messages'" src/hooks/api/*.ts | wc -l)
if [ "$HOOKS_WITH_TOAST" -ge 5 ]; then
    echo -e "${GREEN}✓${NC} ($HOOKS_WITH_TOAST hooks updated)"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠${NC} (Only $HOOKS_WITH_TOAST hooks updated)"
    ((FAIL++))
fi

# 4. Check main.tsx has Toaster configured
echo -n "4. Checking Toaster configuration in main.tsx... "
if grep -q "closeButton" src/main.tsx && grep -q "duration={4000}" src/main.tsx; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

# 5. Check handleAPIErrorToast is exported
echo -n "5. Checking handleAPIErrorToast export... "
if grep -q "export function handleAPIErrorToast" src/lib/toast-messages.ts; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

# 6. Check entityNames is exported
echo -n "6. Checking entityNames export... "
if grep -q "export const entityNames" src/lib/toast-messages.ts; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

# 7. TypeScript type checking
echo -n "7. Running TypeScript type check... "
if pnpm typecheck > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC} (Type errors found)"
    ((FAIL++))
fi

# 8. Check French messages
echo -n "8. Checking French toast messages... "
FRENCH_MESSAGES=$(grep -c "avec succès\|Veuillez\|Erreur" src/lib/toast-messages.ts)
if [ "$FRENCH_MESSAGES" -ge 5 ]; then
    echo -e "${GREEN}✓${NC} ($FRENCH_MESSAGES French messages)"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC} (Insufficient French messages)"
    ((FAIL++))
fi

# Summary
echo ""
echo "================================"
echo "Verification Summary"
echo "================================"
echo -e "Passed: ${GREEN}$SUCCESS${NC}/8"
echo -e "Failed: ${RED}$FAIL${NC}/8"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Toast standardization is complete.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the implementation.${NC}"
    exit 1
fi
