# SQLite Integration & Foreign Key Dependency Issue

**Date**: 2025-12-05  
**Agent**: Claude Code  
**Status**: ⚠️ Foreign Key Limitation Identified

---

## Summary

Successfully implemented SQLite fallback for local development, resolving the Supabase + asyncpg prepared statement issue. However, discovered a structural limitation: SQLite cannot create tables with foreign keys referencing the `users` table (from Supabase Auth).

---

## Progress Made

### ✅ Completed Tasks

1. **Fixed SQLite Schema Creation**:
   - Modified `init_db()` to skip `CREATE SCHEMA` for SQLite
   - Added conditional logic: PostgreSQL gets schema, SQLite doesn't
   - **File**: [backend/app/database.py](backend/app/database.py:215-216)

2. **Added Database Initialization to Startup**:
   - Integrated `init_db()` call in `startup_event()`
   - Only runs for SQLite (PostgreSQL uses Alembic migrations)
   - **File**: [backend/app/main.py](backend/app/main.py:164-174)

3. **Server Status**:
   - ✅ Backend starts successfully (with SQLite enabled)
   - ✅ Health endpoint working: `http://localhost:8000/health`
   - ✅ Frontend running: `http://localhost:5173/`
   - ✅ No more `DuplicatePreparedStatementError`

---

## Current Blocker: Foreign Key Dependencies

### Error Message
```
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 
'kpi_definitions.updated_by_id' could not find table 'users' with which to 
generate a foreign key to target column 'id'
```

### Root Cause

All application models inherit from `BaseModelWithAudit` which has:
```python
created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
updated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
```

**Problem**: The `users` table is part of Supabase Auth (`auth.users` schema in PostgreSQL), not our application models. SQLite doesn't have access to this external table.

**Impact**: SQLAlchemy cannot create tables that reference non-existent `users` table.

---

## Solutions

### Option 1: Create Stub Users Model (Quickest)

Create minimal `users` table for local development:

**File**: `backend/app/models/auth.py` (new file)
```python
from sqlalchemy import Column, String
from app.models.base import Base
from app.database import DATABASE_URL
import uuid

class User(Base):
    """Stub user model for local SQLite development."""
    __tablename__ = "users"
    
    # Conditional schema: PostgreSQL uses efir_budget, SQLite uses default
    if not DATABASE_URL.startswith("sqlite"):
        __table_args__ = {"schema": "efir_budget"}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    # Add minimal fields as needed
```

**Then import in** `backend/app/models/__init__.py`:
```python
from app.models.auth import User  # Add this line
```

**Pros**:
- Minimal code changes
- Allows full local development
- All tables can be created

**Cons**:
- Doesn't match Supabase auth.users schema exactly
- Needs to be maintained separately

---

### Option 2: Make Foreign Keys Nullable (Moderate Effort)

Modify `BaseModelWithAudit` to make user foreign keys optional:

**File**: `backend/app/models/base.py`
```python
created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
updated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
```

**Pros**:
- Tables can be created without `users` table
- Less code to maintain

**Cons**:
- Weakens data integrity
- Audit trail incomplete without user IDs
- Not production-safe

---

### Option 3: Use PostgreSQL Direct Connection (Recommended for Full Testing)

Enable Supabase IPv4 add-on and connect directly:

**Setup**:
1. Go to Supabase Dashboard → Settings → Add-ons → IPv4
2. Enable IPv4 address ($4/month)
3. Update `.env.local`:
   ```bash
   PYTEST_RUNNING="false"
   DATABASE_URL="postgresql+asyncpg://postgres.{ref}:{password}@db.{ref}.supabase.co:5432/postgres"
   ```
4. Run migrations: `alembic upgrade head`

**Pros**:
- Full Supabase integration
- Real `auth.users` table available
- Production parity

**Cons**:
- Requires paid add-on ($4/month)
- Needs network connection
- Still may hit prepared statement issues (mitigated by `async_creator`)

---

## Recommendation

**For Immediate Local Development**: Implement **Option 1** (Stub Users Model)
- Fast to implement (~5 minutes)
- Unblocks local development
- Can be replaced later with Option 3 for production testing

**For Production Testing**: Use **Option 3** (PostgreSQL Direct Connection)
- Full feature parity
- Real Supabase Auth integration
- Worth the $4/month for serious development

---

## Files Modified

1. **[backend/app/main.py](backend/app/main.py:162-174)**
   - Added SQLite schema initialization in `startup_event()`
   
2. **[backend/app/database.py](backend/app/database.py:200-219)**
   - Modified `init_db()` to skip schema creation for SQLite
   
3. **[backend/.env.local](backend/.env.local)**
   - Set `PYTEST_RUNNING="true"` to enable SQLite mode

---

## Next Steps

Choose one path forward:

### Path A: Quick Local Development (Recommended)
1. Create `backend/app/models/auth.py` with stub `User` model (Option 1)
2. Import in `backend/app/models/__init__.py`
3. Restart backend
4. Verify tables created: `curl http://localhost:8000/api/v1/budget-versions`

### Path B: Full Production Testing
1. Enable Supabase IPv4 add-on
2. Update `.env.local` with direct connection URL
3. Run `alembic upgrade head`
4. Verify full integration

---

## Verification

After implementing Option 1, verify with:
```bash
# Start backend with SQLite
cd backend && PYTEST_RUNNING="true" uvicorn app.main:app --reload

# In another terminal, test API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/budget-versions?page=1&page_size=5

# Expected: Empty list [] (no data), not 500 error
```

---

## References

- Original Issue: [2025-12-05_supabase-asyncpg-prepared-statement-issue.md](2025-12-05_supabase-asyncpg-prepared-statement-issue.md)
- Supabase Auth Schema: https://supabase.com/docs/guides/auth/managing-user-data
- SQLAlchemy Foreign Keys: https://docs.sqlalchemy.org/en/20/core/constraints.html#foreign-key-constraint

---

**Agent**: Claude Code  
**Outcome**: SQLite integration successful, foreign key dependency identified and documented
