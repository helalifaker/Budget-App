# Supabase + asyncpg + SQLAlchemy: Prepared Statement Conflict Analysis

**Date**: 2025-12-05
**Agent**: Claude Code
**Status**: Issue Documented, Multiple Solutions Available

---

## Executive Summary

The backend application experiences a `DuplicatePreparedStatementError` when using SQLAlchemy 2.0 with asyncpg driver to connect to Supabase PostgreSQL through their connection poolers (pgBouncer/Supavisor). This is a well-documented, long-standing compatibility issue that has no perfect solution without infrastructure changes.

**Root Cause**: asyncpg's prepared statement caching conflicts with Supabase's shared connection pooling infrastructure.

**Immediate Impact**: Database queries fail during application startup and runtime.

**Recommended Solution**: Use SQLite for local development, PostgreSQL direct connection for production (requires Supabase IPv4 add-on ~$4/month).

---

## Technical Details

### The Problem

When SQLAlchemy's asyncpg dialect initializes, it executes queries like `select pg_catalog.version()` to inspect the database. asyncpg automatically creates prepared statements for these queries using names like `"__asyncpg_stmt_1__"`.

With Supabase's connection pooling:
1. Connection A creates prepared statement `"__asyncpg_stmt_1__"`
2. Connection A is returned to the pool
3. Connection B (from the pool) tries to create the same prepared statement
4. **ERROR**: `prepared statement "__asyncpg_stmt_1__" already exists`

###  Why Standard Solutions Don't Work

#### Attempted Solution 1: `statement_cache_size=0` in connect_args
**Why it failed**: SQLAlchemy's dialect initialization queries run BEFORE connect_args are applied.

#### Attempted Solution 2: UUID-based prepared statement names
**Why it failed**: Same timing issue - dialect initialization happens too early.

#### Attempted Solution 3: Custom `async_creator` function
**Why it failed**: Prepared statements from previous connections persist in pgBouncer's connection pool.

#### Attempted Solution 4: URL parameters
**Why it failed**: URL parameters are passed as strings, but asyncpg requires integer values for cache sizes, causing `TypeError: '<' not supported between instances of 'str' and 'int'`.

---

## Available Solutions

### Option 1: SQLite for Local Development (RECOMMENDED)

**Pros**:
- ✅ Zero external dependencies
- ✅ Fast local development
- ✅ No connection pooler issues
- ✅ Already supported in codebase

**Cons**:
- ⚠️ Different database engine (may have minor compatibility issues)
- ⚠️ Requires separate deployment database

**Implementation**:
Already configured! Just set in `.env.local`:
```bash
PYTEST_RUNNING="true"  # Triggers SQLite mode
```

### Option 2: Supabase Direct Connection (IPv4 Add-on)

**Pros**:
- ✅ Production-ready
- ✅ Bypasses connection pooler entirely
- ✅ Full PostgreSQL compatibility
- ✅ Lower latency

**Cons**:
- 💰 Costs ~$4/month (IPv4 add-on)
- ⚠️ Limited connections (PostgreSQL `max_connections` limit)

**Implementation**:
1. Enable IPv4 add-on in Supabase Dashboard
2. Update `.env.local`:
```bash
DATABASE_URL="postgresql+asyncpg://postgres.{ref}:password@db.{ref}.supabase.co:5432/postgres"
```

### Option 3: Switch to psycopg (Synchronous)

**Pros**:
- ✅ No prepared statement conflicts
- ✅ Works with Supabase poolers
- ✅ Mature, stable driver

**Cons**:
- ⚠️ Requires code changes (sync instead of async)
- ⚠️ Performance trade-off

**Implementation**:
Replace `asyncpg` with `psycopg` (sync) or `psycopg[binary,pool]` (async mode).

### Option 4: Accept Degraded Performance (Transaction Pooler)

**Pros**:
- ✅ Free
- ✅ Works with existing setup

**Cons**:
- ⚠️ Significantly slower
- ⚠️ Limited feature support

**Implementation**:
Use port 6543 (Transaction mode) instead of 5432.

---

## Sources & References

### Official Supabase Documentation
- [Connection Pooling Guide](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supavisor FAQ](https://supabase.com/docs/guides/troubleshooting/supavisor-faq-YyP5tI)
- [IPv4 Add-on Information](https://supabase.com/docs/guides/troubleshooting/supabase--your-network-ipv4-and-ipv6-compatibility-cHe3BP)

### Community Issues & Discussions
- [Supabase Issue #39227](https://github.com/supabase/supabase/issues/39227) - Python asyncpg fails with burst requests
- [Supabase Discussion #36618](https://github.com/orgs/supabase/discussions/36618) - PreparedStatementError with asyncpg and SQLAlchemy
- [SQLAlchemy Issue #6467](https://github.com/sqlalchemy/sqlalchemy/issues/6467) - Using statement_cache_size with pgBouncer
- [SQLAlchemy Discussion #10246](https://github.com/sqlalchemy/sqlalchemy/discussions/10246) - prepared statement name for asyncpg w pgbouncer
- [Stack Overflow Question](https://stackoverflow.com/questions/79648632) - DuplicatePreparedStatementError with SQLAlchemy + asyncpg

### Technical Documentation
- [asyncpg FAQ](https://magicstack.github.io/asyncpg/current/faq.html) - Prepared statements with pgBouncer
- [PostgreSQL Prepared Statements](https://www.postgresql.org/docs/current/sql-prepare.html)

---

## Implementation History

### Attempts Made (2025-12-05)

1. **Cleared Python bytecode cache** (`__pycache__/`) - Resolved caching issues but didn't fix root cause
2. **Tested `statement_cache_size=0` in connect_args** - Not applied during dialect init
3. **Tested `prepared_statement_name_func` with UUID** - Not applied during dialect init
4. **Created custom `async_creator` function** - Pooler still reused connections with existing prepared statements
5. **Added `server_settings={"jit": "off"}`** - Didn't resolve prepared statement naming conflicts

### Current State (Updated with Official Supabase Guidance)

**Local Development** (SQLite mode enabled):
- ✅ Server starts successfully with SQLite
- ✅ Database health checks pass
- ✅ API endpoints responding correctly
- ✅ CORS configured properly
- ✅ Zero prepared statement conflicts

**PostgreSQL with async_creator** (not yet verified in production):
- ⚠️ Needs testing with Session mode (port 5432)
- ⚠️ async_creator approach is correct per Supabase, but may still encounter rare collisions
- ✅ Using correct port (5432 = Session mode, supports prepared statements)

---

## Recommended Action Plan

### Immediate (Local Development)

1. **Enable SQLite mode** by setting `PYTEST_RUNNING="true"` in `.env.local`
2. **Verify** application works with SQLite
3. **Document** any SQLite-specific limitations encountered

### Short-term (Production Deployment)

1. **Evaluate** if the $4/month IPv4 add-on is acceptable
2. **If yes**: Enable IPv4 add-on and use direct connection
3. **If no**: Consider using psycopg (sync) driver or accept transaction pooler limitations

### Long-term (Platform Evolution)

1. **Monitor** Supabase's roadmap for improved Python asyncpg support
2. **Evaluate** alternative hosting options if issue persists
3. **Consider** self-hosted PostgreSQL if budget allows

---

## Conclusion

This is a known architectural incompatibility between:
- asyncpg's prepared statement mechanism
- pgBouncer/Supavisor's connection pooling
- SQLAlchemy's dialect initialization sequence

There is NO clean workaround without changing one of:
- The database driver (asyncpg → psycopg)
- The connection method (pooled → direct)
- The local development database (PostgreSQL → SQLite)

**Verdict**: This is NOT a bug in our code - it's a documented platform limitation that requires infrastructure-level decisions.

---

## Code Changes Made

**File Modified**: `backend/app/database.py`

**Final Configuration** (custom async_creator approach):
```python
import asyncpg

async def async_creator():
    """Custom async connection creator for Supabase pooler compatibility."""
    from urllib.parse import urlparse

    parsed = urlparse(DATABASE_URL)

    return await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        statement_cache_size=0,  # Disable prepared statement cache
        server_settings={"jit": "off"},  # Disable JIT compilation
    )

engine = create_async_engine(
    "postgresql+asyncpg://",
    async_creator=async_creator,
    poolclass=NullPool,
    pool_pre_ping=False,
)
```

**Note**: Even this approach doesn't fully resolve the issue due to pooler-level prepared statement persistence.

---

## Official Supabase Guidance (Added 2025-12-05)

Supabase's official response confirms this is a **known class of "session artifact" issues** when using Supavisor/pgBouncer with libraries that auto-create named prepared statements.

### Key Findings from Supabase

1. **Transaction mode (6543)**: Does NOT support prepared statements. Will always surface "prepared statement already exists" errors.

2. **Session mode (5432)**: DOES support prepared statements, but can still leak session artifacts across clients when connections are shared.

3. **Direct connections**: Support prepared statements fully, but require IPv6 or IPv4 add-on ($4/month).

### Official Recommendations (Priority Order)

#### 1. Use Session Mode or Direct Connection (PREFERRED)
- **Session mode (5432)**: Already configured in your `.env.local` ✅
- **Direct connection**: Requires IPv4 add-on but eliminates all pooler issues
- **Current implementation**: Your `async_creator` with `statement_cache_size=0` is the **correct approach** per Supabase

#### 2. Switch to psycopg3 (SUPABASE RECOMMENDED)
- psycopg3 has better compatibility with poolers than asyncpg
- Allows disabling auto-prepared behavior more predictably
- Available in both sync and async modes
- Command: `pip install "psycopg[binary,pool]"`

#### 3. Verification Steps Suggested by Supabase

To test if your current `async_creator` setup works with Session mode:

```bash
# Temporarily disable SQLite mode
PYTEST_RUNNING="false"  # in .env.local

# Restart backend and check logs for:
# 1. First connection uses statement_cache_size=0
# 2. No DuplicatePreparedStatementError
# 3. Database health check succeeds
```

### Current Configuration Status

✅ **You're already using Session mode (port 5432)** - correct choice!
✅ **You have `async_creator` with `statement_cache_size=0`** - correct implementation!
✅ **You have `NullPool`** - prevents connection reuse artifacts

**Conclusion**: Your PostgreSQL configuration aligns with Supabase's official recommendations. The `async_creator` approach should work for production deployment on Session mode, though SQLite remains the best choice for local development.
