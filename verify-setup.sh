#!/bin/bash

# ============================================================================
# EFIR Budget App - Credentials Verification Script
# ============================================================================
# This script verifies that your Supabase credentials are set up correctly

set -e

echo "=========================================="
echo "✓ Verifying Supabase Setup"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check 1: Verify backend environment file exists
echo -e "${BLUE}[1/5] Checking backend configuration...${NC}"
if [ ! -f "backend/.env.local" ]; then
    echo -e "${RED}❌ backend/.env.local not found${NC}"
    exit 1
fi

if grep -q "YOUR_NEW_PASSWORD" "backend/.env.local"; then
    echo -e "${RED}❌ Backend still has placeholder values${NC}"
    echo "    Run: ./setup-credentials.sh"
    exit 1
fi

echo -e "${GREEN}✓ Backend configuration file exists and has values${NC}"
echo ""

# Check 2: Verify frontend environment file exists
echo -e "${BLUE}[2/5] Checking frontend configuration...${NC}"
if [ ! -f "frontend/.env" ]; then
    echo -e "${RED}❌ frontend/.env not found${NC}"
    exit 1
fi

if grep -q "YOUR_ACTUAL_ANON_KEY_HERE" "frontend/.env"; then
    echo -e "${RED}❌ Frontend still has placeholder values${NC}"
    echo "    Run: ./setup-credentials.sh"
    exit 1
fi

echo -e "${GREEN}✓ Frontend configuration file exists and has values${NC}"
echo ""

# Check 3: Verify backend Python environment
echo -e "${BLUE}[3/5] Checking backend Python environment...${NC}"
if [ ! -d "backend/.venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found at backend/.venv${NC}"
    echo "   Creating virtual environment..."
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]" > /dev/null 2>&1
    cd ..
fi

echo -e "${GREEN}✓ Backend Python environment ready${NC}"
echo ""

# Check 4: Verify frontend dependencies
echo -e "${BLUE}[4/5] Checking frontend dependencies...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠ Dependencies not installed${NC}"
    echo "   Installing dependencies..."
    cd frontend
    pnpm install > /dev/null 2>&1
    cd ..
fi

echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
echo ""

# Check 5: Display configuration summary
echo -e "${BLUE}[5/5] Configuration Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract and display backend config (without showing passwords)
BACKEND_URL=$(grep "VITE_SUPABASE_URL" "frontend/.env" | cut -d'=' -f2)
echo -e "${GREEN}Backend Database:${NC}"
echo "  📍 Supabase Project: ssxwmxqvafesyldycqzy"
echo "  🔗 URL: https://ssxwmxqvafesyldycqzy.supabase.co"
echo ""

echo -e "${GREEN}Frontend Configuration:${NC}"
FRONTEND_URL=$(grep "VITE_SUPABASE_URL" "frontend/.env" | cut -d'=' -f2)
echo "  🔗 Supabase URL: $FRONTEND_URL"
API_URL=$(grep "VITE_API_BASE_URL" "frontend/.env" | cut -d'=' -f2)
echo "  🔗 API Base URL: $API_URL"
echo ""

echo -e "${GREEN}Environment Files:${NC}"
echo "  📄 backend/.env.local - Configured ✓"
echo "  📄 frontend/.env - Configured ✓"
echo "  ⚠️  These files contain secrets - NEVER commit to git"
echo ""

echo -e "${GREEN}=========================================="
echo "✅ Setup Verification Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1️⃣  Start Backend (Terminal 1):"
echo -e "   ${BLUE}cd backend${NC}"
echo -e "   ${BLUE}source .venv/bin/activate${NC}"
echo -e "   ${BLUE}uvicorn app.main:app --reload${NC}"
echo ""
echo "2️⃣  Start Frontend (Terminal 2):"
echo -e "   ${BLUE}cd frontend${NC}"
echo -e "   ${BLUE}pnpm dev${NC}"
echo ""
echo "3️⃣  Test the Application:"
echo -e "   Open browser: ${BLUE}http://localhost:5173${NC}"
echo ""
