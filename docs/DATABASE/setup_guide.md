# EFIR Budget Planning - Database Setup Guide

**Version:** 1.0
**Date:** 2025-11-30
**Target Database:** Supabase PostgreSQL 17.x with `efir_budget` schema isolation

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Supabase Project Setup](#supabase-project-setup)
3. [Database Migration](#database-migration)
4. [Row Level Security Setup](#row-level-security-setup)
5. [Authentication Configuration](#authentication-configuration)
6. [Seed Data](#seed-data)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- Python 3.12+ with pip
- Node.js 18+ and pnpm
- Supabase account (free tier is sufficient for development)
- Git

### Environment Setup

1. **Backend Virtual Environment**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Install Alembic** (included in backend dependencies)
   ```bash
   pip list | grep alembic
   # Should show: alembic==1.14.0
   ```

---

## Supabase Project Setup

### Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign in or create an account
3. Click "New Project"
4. Fill in project details:
   - **Name**: `efir-budget-dev` (or your preferred name)
   - **Database Password**: Generate a strong password and **save it securely**
   - **Region**: Choose closest to Riyadh (e.g., `eu-west-2` London)
5. Wait for project provisioning (~2 minutes)

### Step 2: Get Connection Strings

1. In Supabase Dashboard, go to **Settings** → **Database**
2. Copy the following connection strings:

   **Connection String (Transaction Mode)** - For application use:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:6543/postgres
   ```

   **Connection String (Session Mode)** - For migrations:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres
   ```

3. Also note:
   - **Project URL**: `https://[YOUR-PROJECT-ID].supabase.co`
   - **anon/public key**: Found in Settings → API

### Step 3: Configure Environment Variables

1. **Root `.env.local`** (for frontend):
   ```bash
   cp .env.example .env.local
   ```

   Edit `.env.local`:
   ```env
   # Supabase
   VITE_SUPABASE_URL=https://[YOUR-PROJECT-ID].supabase.co
   VITE_SUPABASE_ANON_KEY=[YOUR-ANON-KEY]

   # Database (Session Mode - for direct connection)
   DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres
   DIRECT_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres

   # Currency & Locale
   DEFAULT_CURRENCY=SAR
   DEFAULT_LOCALE=fr-FR
   EUR_TO_SAR_RATE=4.05
   ```

2. **Backend `.env.local`**:
   ```bash
   cd backend
   echo 'DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres' > .env.local
   ```

---

## Database Migration

### Step 1: Verify Alembic Configuration

Check `backend/alembic.ini`:
```ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s
```

Check `backend/alembic/env.py` imports models:
```python
from app.models import Base
target_metadata = Base.metadata
```

### Step 2: Run Migration

```bash
cd backend
source .venv/bin/activate

# Review the migration first
alembic show 001_initial_config

# Run the migration
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_config, Initial Configuration Layer migration (Modules 1-6)
```

### Step 3: Verify Schema Creation

Connect to Supabase using SQL Editor or psql:

```sql
-- Check schema exists
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'efir_budget';

-- List all tables in efir_budget schema
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'efir_budget'
ORDER BY table_name;

-- Expected tables (13 total):
-- academic_cycles, academic_levels, budget_versions, class_size_params,
-- fee_categories, fee_structure, nationality_types, subject_hours_matrix,
-- subjects, system_configs, teacher_categories, teacher_cost_params,
-- timetable_constraints

-- Check alembic version
SELECT version_num FROM efir_budget.alembic_version;
-- Expected: 001_initial_config
```

---

## Row Level Security Setup

### Step 1: Apply RLS Policies

In Supabase SQL Editor, run:

```sql
-- Load and execute RLS policies
-- (Copy content from docs/DATABASE/sql/rls_policies.sql)
```

Or using psql:

```bash
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres" \
  -f docs/DATABASE/sql/rls_policies.sql
```

### Step 2: Verify RLS is Enabled

```sql
-- Check RLS is enabled on all tables
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'efir_budget';

-- All tables should show rowsecurity = true
```

### Step 3: Test RLS Policies

```sql
-- View all policies
SELECT tablename, policyname, permissive, roles, cmd
FROM pg_policies
WHERE schemaname = 'efir_budget'
ORDER BY tablename, policyname;

-- Should see policies like:
-- budget_versions: admin_all, manager_insert, manager_working, etc.
```

---

## Authentication Configuration

### Step 1: Configure Supabase Auth

1. Go to **Authentication** → **Providers** in Supabase Dashboard
2. Enable **Email** provider:
   - ✅ Enable Email provider
   - ✅ Confirm email (recommended for production)
   - ✅ Secure email change (recommended)

### Step 2: Create User Roles

Supabase doesn't have built-in roles beyond the authenticated user. We store roles in `raw_user_meta_data`.

**Option A: Via Supabase Dashboard**

1. Go to **Authentication** → **Users**
2. Click "Invite User"
3. Enter email
4. After user signs up, click on the user
5. Click "Edit" → "User Metadata (raw_user_meta_data)"
6. Add:
   ```json
   {
     "role": "admin"
   }
   ```

**Option B: Via SQL (After User Creation)**

```sql
-- Update user role to admin
UPDATE auth.users
SET raw_user_meta_data = jsonb_set(
  COALESCE(raw_user_meta_data, '{}'::jsonb),
  '{role}',
  '"admin"'
)
WHERE email = 'admin@efir.local';

-- Update user role to manager
UPDATE auth.users
SET raw_user_meta_data = jsonb_set(
  COALESCE(raw_user_meta_data, '{}'::jsonb),
  '{role}',
  '"manager"'
)
WHERE email = 'manager@efir.local';

-- Update user role to viewer
UPDATE auth.users
SET raw_user_meta_data = jsonb_set(
  COALESCE(raw_user_meta_data, '{}'::jsonb),
  '{role}',
  '"viewer"'
)
WHERE email = 'viewer@efir.local';
```

### Step 3: Test User Creation

Create test users for each role:

```bash
# From frontend application or Supabase Dashboard
# 1. admin@efir.local (role: admin)
# 2. manager@efir.local (role: manager)
# 3. viewer@efir.local (role: viewer)
```

---

## Seed Data

### Step 1: Create Seed Data Script

Reference data needs to be populated for the application to function.

**Run Seed Script** (when created):

```bash
cd backend
source .venv/bin/activate
python scripts/seed_reference_data.py
```

**Or manually via SQL**:

```sql
-- Insert academic cycles
INSERT INTO efir_budget.academic_cycles (id, code, name_fr, name_en, sort_order, requires_atsem)
VALUES
  (gen_random_uuid(), 'MAT', 'Maternelle', 'Preschool', 1, true),
  (gen_random_uuid(), 'ELEM', 'Élémentaire', 'Elementary', 2, false),
  (gen_random_uuid(), 'COLL', 'Collège', 'Middle School', 3, false),
  (gen_random_uuid(), 'LYC', 'Lycée', 'High School', 4, false);

-- Insert academic levels (sample for Maternelle)
WITH cycle AS (
  SELECT id FROM efir_budget.academic_cycles WHERE code = 'MAT'
)
INSERT INTO efir_budget.academic_levels (id, cycle_id, code, name_fr, name_en, sort_order, is_secondary)
SELECT
  gen_random_uuid(),
  cycle.id,
  level_code,
  level_name_fr,
  level_name_en,
  level_order,
  false
FROM cycle, (VALUES
  ('PS', 'Petite Section', 'Preschool - Small Section', 1),
  ('MS', 'Moyenne Section', 'Preschool - Middle Section', 2),
  ('GS', 'Grande Section', 'Preschool - Large Section', 3)
) AS levels(level_code, level_name_fr, level_name_en, level_order);

-- Continue for other cycles (ELEM, COLL, LYC)...

-- Insert subjects (sample)
INSERT INTO efir_budget.subjects (id, code, name_fr, name_en, category, is_active)
VALUES
  (gen_random_uuid(), 'MATH', 'Mathématiques', 'Mathematics', 'core', true),
  (gen_random_uuid(), 'FRAN', 'Français', 'French', 'core', true),
  (gen_random_uuid(), 'ANGL', 'Anglais', 'English', 'core', true),
  (gen_random_uuid(), 'HIST', 'Histoire-Géographie', 'History-Geography', 'core', true),
  (gen_random_uuid(), 'SVT', 'Sciences de la Vie et de la Terre', 'Life and Earth Sciences', 'core', true);

-- Insert teacher categories
INSERT INTO efir_budget.teacher_categories (id, code, name_fr, name_en, description, is_aefe)
VALUES
  (gen_random_uuid(), 'AEFE_DETACHED', 'Enseignant détaché AEFE', 'AEFE Detached Teacher', 'French teacher paid by AEFE with PRRD contribution from school', true),
  (gen_random_uuid(), 'AEFE_FUNDED', 'Enseignant résident AEFE', 'AEFE Funded Teacher', 'French teacher fully funded by AEFE', true),
  (gen_random_uuid(), 'LOCAL', 'Enseignant recruté localement', 'Locally Recruited Teacher', 'Teacher recruited and paid by school', false);

-- Insert fee categories
INSERT INTO efir_budget.fee_categories (id, code, name_fr, name_en, account_code, is_recurring, allows_sibling_discount)
VALUES
  (gen_random_uuid(), 'TUITION', 'Frais de scolarité', 'Tuition Fees', '70110', true, true),
  (gen_random_uuid(), 'DAI', 'Droit Annuel d''Inscription', 'Annual Enrollment Fee', '70120', true, false),
  (gen_random_uuid(), 'REGISTRATION', 'Frais d''inscription', 'Registration Fee', '70130', false, false);

-- Insert nationality types
INSERT INTO efir_budget.nationality_types (id, code, name_fr, name_en, vat_applicable, sort_order)
VALUES
  (gen_random_uuid(), 'FRENCH', 'Français', 'French', true, 1),
  (gen_random_uuid(), 'SAUDI', 'Saoudien', 'Saudi', false, 2),
  (gen_random_uuid(), 'OTHER', 'Autre', 'Other', true, 3);

-- Insert system configs
INSERT INTO efir_budget.system_configs (
  id, key, value, category, description, is_active,
  created_by_id, updated_by_id
)
SELECT
  gen_random_uuid(),
  config_key,
  config_value::jsonb,
  config_category,
  config_desc,
  true,
  (SELECT id FROM auth.users WHERE email = 'admin@efir.local' LIMIT 1),
  (SELECT id FROM auth.users WHERE email = 'admin@efir.local' LIMIT 1)
FROM (VALUES
  ('DEFAULT_CURRENCY', '{"code": "SAR", "symbol": "ر.س"}', 'currency', 'Primary currency for all financial data'),
  ('EUR_TO_SAR_RATE', '{"rate": 4.05, "effective_date": "2025-09-01"}', 'currency', 'EUR to SAR exchange rate'),
  ('STANDARD_TEACHING_HOURS_PRIMARY', '{"hours": 24}', 'academic', 'Standard teaching hours per week for primary teachers'),
  ('STANDARD_TEACHING_HOURS_SECONDARY', '{"hours": 18}', 'academic', 'Standard teaching hours per week for secondary teachers'),
  ('CURRENT_ACADEMIC_YEAR', '{"year": "2025-2026", "start": "2025-09-01", "end": "2026-06-30"}', 'academic', 'Current academic year dates')
) AS configs(config_key, config_value, config_category, config_desc);
```

### Step 2: Verify Seed Data

```sql
SELECT COUNT(*) FROM efir_budget.academic_cycles;  -- Should be 4
SELECT COUNT(*) FROM efir_budget.academic_levels;  -- Should be ~13 (PS-Terminale)
SELECT COUNT(*) FROM efir_budget.subjects;  -- Should be ~15-20
SELECT COUNT(*) FROM efir_budget.teacher_categories;  -- Should be 3
SELECT COUNT(*) FROM efir_budget.fee_categories;  -- Should be 3+
SELECT COUNT(*) FROM efir_budget.nationality_types;  -- Should be 3
SELECT COUNT(*) FROM efir_budget.system_configs;  -- Should be 5+
```

---

## Verification

### Step 1: Test Database Connection from Backend

```bash
cd backend
source .venv/bin/activate
python -c "
import asyncio
from app.database import engine
from sqlalchemy import text

async def test():
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT version_num FROM efir_budget.alembic_version'))
        print(f'Migration version: {result.scalar()}')

        result = await conn.execute(text('SELECT COUNT(*) FROM efir_budget.academic_cycles'))
        print(f'Academic cycles: {result.scalar()}')

asyncio.run(test())
"
```

**Expected Output:**
```
Migration version: 001_initial_config
Academic cycles: 4
```

### Step 2: Test RLS Policies

Create a test file `backend/scripts/test_rls.py`:

```python
"""Test RLS policies with different user roles."""
import asyncio
from app.database import AsyncSessionLocal
from app.models import BudgetVersion
from sqlalchemy import select

async def test_rls():
    async with AsyncSessionLocal() as session:
        # This should respect RLS based on current user
        result = await session.execute(select(BudgetVersion))
        versions = result.scalars().all()
        print(f"Accessible budget versions: {len(versions)}")

asyncio.run(test_rls())
```

Run:
```bash
python scripts/test_rls.py
```

### Step 3: Test Frontend Connection

```bash
cd frontend
pnpm dev
```

Open browser to `http://localhost:5173` and verify Supabase connection in DevTools console.

---

## Troubleshooting

### Issue: Migration Fails with "relation does not exist"

**Solution**: Ensure `efir_budget` schema is created:
```sql
CREATE SCHEMA IF NOT EXISTS efir_budget;
```

### Issue: RLS Policies Not Working

**Symptoms**: Users can see data they shouldn't

**Solutions**:
1. Verify RLS is enabled:
   ```sql
   ALTER TABLE efir_budget.budget_versions ENABLE ROW LEVEL SECURITY;
   ```

2. Check user role is set:
   ```sql
   SELECT email, raw_user_meta_data->>'role' as role
   FROM auth.users;
   ```

3. Verify policies exist:
   ```sql
   SELECT * FROM pg_policies WHERE schemaname = 'efir_budget';
   ```

### Issue: Cannot Connect to Database

**Check**:
1. Firewall/network allows connections to Supabase
2. Connection string is correct (check password, project ID)
3. Using Session Mode (port 5432) for migrations, not Transaction Mode (port 6543)

### Issue: "permission denied for schema efir_budget"

**Solution**: Ensure `postgres` role has proper permissions:
```sql
GRANT ALL ON SCHEMA efir_budget TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA efir_budget TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA efir_budget TO postgres;
```

---

## Next Steps

After successful setup:

1. ✅ **Phase 1 Complete** - Database schema and auth configured
2. → **Phase 2**: Implement Planning Layer models (Modules 7-12)
3. → **Phase 3**: Build frontend components for Configuration Layer
4. → **Phase 4**: Implement business logic and calculations

---

## Support & Documentation

- **Supabase Docs**: [https://supabase.com/docs](https://supabase.com/docs)
- **Alembic Docs**: [https://alembic.sqlalchemy.org](https://alembic.sqlalchemy.org)
- **SQLAlchemy 2.0 Docs**: [https://docs.sqlalchemy.org/en/20/](https://docs.sqlalchemy.org/en/20/)
- **Project Issues**: File issues in project repository

---

**Last Updated**: 2025-11-30
**Maintained By**: EFIR Development Team
