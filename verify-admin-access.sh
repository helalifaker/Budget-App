#!/bin/bash
# Verify admin user access to planning operations
# Usage: ./verify-admin-access.sh

set -e

echo "🔍 Verifying Admin Access to Planning Operations"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env.local exists
if [ ! -f "backend/.env.local" ]; then
    echo -e "${RED}❌ backend/.env.local not found${NC}"
    echo "Please create it from backend/.env.example"
    exit 1
fi

# Source environment variables
source backend/.env.local

echo -e "${BLUE}1️⃣ Checking Supabase Connection${NC}"
echo "   SUPABASE_URL: ${VITE_SUPABASE_URL:0:30}..."
echo "   DATABASE_URL: ${DATABASE_URL:0:50}..."
echo ""

echo -e "${BLUE}2️⃣ Verifying RLS Policies in Database${NC}"
cd backend

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Create temporary Python script to check RLS policies
cat > /tmp/verify_rls.py << 'EOF'
import os
import asyncio
from sqlalchemy import text
from app.database import engine

async def verify_admin_policies():
    """Verify admin RLS policies exist."""
    async with engine.begin() as conn:
        # Check RLS is enabled on planning tables
        result = await conn.execute(text("""
            SELECT schemaname, tablename, policyname
            FROM pg_policies
            WHERE schemaname = 'efir_budget'
            AND policyname LIKE '%admin_all'
            ORDER BY tablename;
        """))

        policies = result.fetchall()

        print("\n✅ Admin RLS Policies Found:")
        print("   " + "="*50)

        planning_tables = {
            'enrollment_plans', 'class_structures', 'dhg_subject_hours',
            'dhg_teacher_requirements', 'teacher_allocations', 'revenue_plans',
            'personnel_cost_plans', 'operating_cost_plans', 'capex_plans'
        }

        found_tables = set()
        for schema, table, policy in policies:
            if table in planning_tables:
                print(f"   ✅ {table}.{policy}")
                found_tables.add(table)

        missing = planning_tables - found_tables
        if missing:
            print(f"\n   ❌ Missing policies for: {', '.join(missing)}")
            return False
        else:
            print(f"\n   ✅ All {len(found_tables)} planning tables have admin policies")
            return True

if __name__ == "__main__":
    success = asyncio.run(verify_admin_policies())
    exit(0 if success else 1)
EOF

python /tmp/verify_rls.py
rm /tmp/verify_rls.py

echo ""
echo -e "${BLUE}3️⃣ Checking User Role in Supabase${NC}"
echo "   To verify your admin role, check Supabase Dashboard:"
echo "   → Authentication > Users > [Your User] > User Metadata"
echo "   → Should contain: { \"role\": \"admin\" }"
echo ""

echo -e "${BLUE}4️⃣ Testing JWT Token Role Extraction${NC}"
echo "   Run this query in Supabase SQL Editor to verify:"
echo ""
echo "   SELECT email, raw_user_meta_data->>'role' as role"
echo "   FROM auth.users"
echo "   WHERE email = 'your-email@example.com';"
echo ""

echo -e "${GREEN}✅ Verification Complete${NC}"
echo ""
echo "If all checks pass, your admin user has full rights to:"
echo "  • All CRUD operations on planning tables"
echo "  • Access to all budget version statuses"
echo "  • View soft-deleted records"
echo "  • Bypass all RLS restrictions"
