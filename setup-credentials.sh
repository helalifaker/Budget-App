#!/bin/bash

# ============================================================================
# EFIR Budget App - Supabase Credentials Setup Script
# ============================================================================
# This script helps you set up your Supabase credentials safely

set -e

echo "=========================================="
echo "🔐 EFIR Supabase Credentials Setup"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Validate we're in the right directory
if [ ! -f "CLAUDE.md" ]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    echo "Please run this script from: /Users/fakerhelali/Coding/Budget App"
    exit 1
fi

echo -e "${YELLOW}Step 1: Get Your New Supabase Credentials${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Follow these steps in your Supabase Dashboard:"
echo "1. Go to: https://supabase.com/dashboard"
echo "2. Select your project: ssxwmxqvafesyldycqzy"
echo "3. Go to Settings → Database"
echo "4. Click 'Reset Password' and save the new password"
echo "5. Go to Settings → API"
echo "6. Rotate the 'service_role' key and copy it"
echo "7. Rotate the 'anon' key and copy it"
echo ""

read -p "Press ENTER when you've completed these steps..."
echo ""

# Step 2: Get credentials from user
echo -e "${YELLOW}Step 2: Enter Your New Credentials${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -sp "Enter your NEW database password (will be hidden): " DB_PASSWORD
echo ""
echo ""

read -sp "Enter your NEW service_role key (starts with sb_secret_): " SERVICE_ROLE_KEY
echo ""
echo ""

read -sp "Enter your NEW anon key (starts with sb_anon_): " ANON_KEY
echo ""
echo ""

# Step 3: Validate inputs
if [ -z "$DB_PASSWORD" ] || [ -z "$SERVICE_ROLE_KEY" ] || [ -z "$ANON_KEY" ]; then
    echo -e "${RED}❌ Error: One or more credentials are empty${NC}"
    exit 1
fi

# Step 4: Update backend/.env.local
echo -e "${YELLOW}Step 3: Updating Backend Configuration${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BACKEND_ENV_PATH="backend/.env.local"

# Escape special characters for sed
DB_PASSWORD_ESCAPED=$(printf '%s\n' "$DB_PASSWORD" | sed -e 's/[\/&]/\\&/g')
SERVICE_ROLE_ESCAPED=$(printf '%s\n' "$SERVICE_ROLE_KEY" | sed -e 's/[\/&]/\\&/g')

# Update DATABASE_URL
sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=\"postgresql+asyncpg://postgres.ssxwmxqvafesyldycqzy:${DB_PASSWORD_ESCAPED}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true\"|" "$BACKEND_ENV_PATH"

# Update DIRECT_URL
sed -i '' "s|DIRECT_URL=.*|DIRECT_URL=\"postgresql+asyncpg://postgres.ssxwmxqvafesyldycqzy:${DB_PASSWORD_ESCAPED}@db.ssxwmxqvafesyldycqzy.supabase.co:5432/postgres\"|" "$BACKEND_ENV_PATH"

# Update SUPABASE_SERVICE_ROLE_KEY
sed -i '' "s|SUPABASE_SERVICE_ROLE_KEY=.*|SUPABASE_SERVICE_ROLE_KEY=\"${SERVICE_ROLE_ESCAPED}\"|" "$BACKEND_ENV_PATH"

echo -e "${GREEN}✓ Updated $BACKEND_ENV_PATH${NC}"
echo ""

# Step 5: Update frontend/.env
echo -e "${YELLOW}Step 4: Updating Frontend Configuration${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FRONTEND_ENV_PATH="frontend/.env"

ANON_KEY_ESCAPED=$(printf '%s\n' "$ANON_KEY" | sed -e 's/[\/&]/\\&/g')

sed -i '' "s|VITE_SUPABASE_ANON_KEY=.*|VITE_SUPABASE_ANON_KEY=${ANON_KEY_ESCAPED}|" "$FRONTEND_ENV_PATH"

echo -e "${GREEN}✓ Updated $FRONTEND_ENV_PATH${NC}"
echo ""

# Step 6: Verification
echo -e "${YELLOW}Step 5: Verification${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Checking backend configuration..."
if grep -q "postgresql+asyncpg://postgres.ssxwmxqvafesyldycqzy:" "$BACKEND_ENV_PATH"; then
    echo -e "${GREEN}✓ Backend database URL updated${NC}"
else
    echo -e "${RED}❌ Backend database URL not updated correctly${NC}"
    exit 1
fi

if grep -q "SUPABASE_SERVICE_ROLE_KEY=sb_secret_" "$BACKEND_ENV_PATH"; then
    echo -e "${GREEN}✓ Backend service role key updated${NC}"
else
    echo -e "${RED}❌ Backend service role key not updated correctly${NC}"
    exit 1
fi

echo ""
echo "Checking frontend configuration..."
if grep -q "VITE_SUPABASE_ANON_KEY=sb_anon_" "$FRONTEND_ENV_PATH"; then
    echo -e "${GREEN}✓ Frontend anon key updated${NC}"
else
    echo -e "${RED}❌ Frontend anon key not updated correctly${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "✅ All credentials updated successfully!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Start the backend: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "2. Start the frontend: cd frontend && pnpm dev"
echo "3. Test your app at http://localhost:5173"
echo ""
