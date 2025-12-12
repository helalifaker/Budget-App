# Backup and Disaster Recovery Strategy

> **Last Updated**: 2025-12-12
> **Owner**: System Architecture Team
> **Review Cycle**: Quarterly

This document outlines the backup strategy, disaster recovery procedures, and data protection mechanisms for the EFIR Budget Planning Application.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Recovery Objectives](#recovery-objectives)
3. [Backup Strategy](#backup-strategy)
4. [Data Protection Mechanisms](#data-protection-mechanisms)
5. [Disaster Recovery Procedures](#disaster-recovery-procedures)
6. [Cache Recovery](#cache-recovery)
7. [Testing and Validation](#testing-and-validation)
8. [Runbooks](#runbooks)
9. [Contact and Escalation](#contact-and-escalation)

---

## Architecture Overview

The EFIR Budget Planning Application uses a multi-tier architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────┐   │
│   │   Frontend  │───▶│   Backend API   │───▶│   Supabase PostgreSQL   │   │
│   │   (Vercel)  │    │  (Fly.io/Render)│    │   (Managed Database)    │   │
│   └─────────────┘    └────────┬────────┘    └─────────────────────────┘   │
│                               │                                             │
│                               ▼                                             │
│                      ┌─────────────────┐                                   │
│                      │   Redis Cache   │                                   │
│                      │   (Optional)    │                                   │
│                      └─────────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Critical Data Stores

| Component | Data Classification | Backup Responsibility |
|-----------|--------------------|-----------------------|
| Supabase PostgreSQL | **Critical** - All business data | Supabase (managed) + manual exports |
| Redis Cache | **Non-critical** - Regenerable | Not backed up (ephemeral) |
| Frontend Assets | **Version Controlled** | Git repository |
| Application Code | **Version Controlled** | Git repository |

---

## Recovery Objectives

### Recovery Time Objective (RTO)

| Scenario | Target RTO | Description |
|----------|------------|-------------|
| Minor outage (single service) | 15 minutes | Service restart, failover |
| Database corruption | 1 hour | Point-in-Time Recovery |
| Complete disaster | 4 hours | Full environment rebuild |
| Data center failure | 8 hours | Regional failover |

### Recovery Point Objective (RPO)

| Data Type | Target RPO | Backup Frequency |
|-----------|------------|------------------|
| Transactional data | 5 minutes | Supabase PITR (continuous) |
| Configuration data | 24 hours | Daily snapshots |
| Audit logs | 5 minutes | Part of transactional data |
| Cache data | N/A | No backup (regenerable) |

---

## Backup Strategy

### 1. Supabase Managed Backups (Primary)

Supabase provides automatic backup services:

#### Daily Automatic Backups
- **Frequency**: Every 24 hours
- **Retention**: 7 days (Free/Pro), 30 days (Enterprise)
- **Location**: Supabase managed storage

#### Point-in-Time Recovery (PITR)
- **Availability**: Pro plan and above
- **Granularity**: Up to 5-minute precision
- **Retention**: 7 days

**Access via Supabase Dashboard**:
1. Navigate to: Project → Settings → Database → Backups
2. View available backup points
3. Initiate restore to specific point in time

### 2. Manual Database Exports (Secondary)

For additional protection, export data periodically:

```bash
# Export full database schema and data
pg_dump "postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres" \
  --schema=efir_budget \
  --format=custom \
  --file=backup_$(date +%Y%m%d_%H%M%S).dump

# Export schema only (for disaster recovery testing)
pg_dump "postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres" \
  --schema=efir_budget \
  --schema-only \
  --file=schema_$(date +%Y%m%d).sql

# Export data only (for data migration)
pg_dump "postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres" \
  --schema=efir_budget \
  --data-only \
  --file=data_$(date +%Y%m%d).sql
```

### 3. Migration-Based Schema Recovery

All schema changes are versioned through Alembic migrations:

```
backend/alembic/versions/
├── 20251130_2340_initial_configuration_layer.py
├── 20251201_0015_planning_layer.py
├── 20251201_0030_consolidation_layer.py
├── 20251201_0045_fix_critical_issues.py
├── 20251201_0057_analysis_layer.py
├── 20251201_0100_class_structure_validation.py
├── 20251201_0138_strategic_layer.py
├── 20251202_0800_performance_indexes.py
├── 20251202_2315_materialized_views_for_kpi_dashboard.py
├── 20251202_2330_planning_cells_writeback.py
├── 20251206_0100_add_audit_columns_nationality_distributions.py
├── 20251206_1400_seed_subjects.py
├── 20251206_1800_historical_comparison.py
├── 20251206_2000_workforce_personnel.py
├── 20251205_1200_seed_reference_data_and_distributions.py
├── 20251210_1200_fix_function_security_rls_performance.py
├── 20251212_0001_enrollment_projection_tables.py
├── 20251212_0001a_add_organizations_table.py
├── 20251212_0200_enrollment_derived_parameters.py
└── 20251212_0300_add_audit_columns_enrollment_tables.py
```

**Recovery Command**:
```bash
# Recreate schema from scratch on a new database
cd backend
uv run alembic upgrade head
```

### 4. Backup Schedule Recommendation

| Backup Type | Frequency | Retention | Storage Location |
|-------------|-----------|-----------|------------------|
| Supabase PITR | Continuous | 7 days | Supabase managed |
| Supabase Daily | Daily | 7-30 days | Supabase managed |
| Manual pg_dump | Weekly | 90 days | S3/GCS bucket |
| Schema export | On deployment | Forever | Git repository |
| Reference data | On change | Forever | Seed migrations |

---

## Data Protection Mechanisms

### 1. Soft Delete Pattern

All entities use soft delete to prevent accidental data loss:

```python
# From app/models/base.py
class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    deleted_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
    )
```

**Recovery**: Soft-deleted records can be restored by setting `deleted_at = NULL`.

```sql
-- Restore a soft-deleted budget version
UPDATE efir_budget.budget_versions
SET deleted_at = NULL, deleted_by = NULL
WHERE id = 'uuid-here';
```

### 2. Audit Columns

All models include audit tracking:

```python
class AuditMixin:
    created_at: Mapped[datetime]      # Record creation timestamp
    created_by: Mapped[UUID | None]   # User who created
    updated_at: Mapped[datetime]      # Last modification timestamp
    updated_by: Mapped[UUID | None]   # User who last modified
```

### 3. Budget Version Isolation

Budget data is versioned and isolated:

```sql
-- Each budget version is a complete snapshot
SELECT * FROM efir_budget.budget_versions WHERE status = 'approved';

-- Roll back to previous version by changing status
UPDATE efir_budget.budget_versions
SET status = 'superseded'
WHERE id = 'current-version-uuid';

UPDATE efir_budget.budget_versions
SET status = 'approved'
WHERE id = 'previous-version-uuid';
```

### 4. Row Level Security (RLS)

Supabase RLS policies prevent unauthorized data access:

```sql
-- Users can only access their organization's data
CREATE POLICY "Users can view their organization's data"
ON efir_budget.budget_versions
FOR SELECT
USING (organization_id = auth.jwt()->>'organization_id');
```

### 5. Transaction Safety

All write operations use transactions:

```python
async with AsyncSessionLocal() as session:
    try:
        # Multiple operations in single transaction
        await service.create_budget(...)
        await service.create_enrollment(...)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
```

---

## Disaster Recovery Procedures

### Scenario 1: Accidental Data Deletion

**Symptoms**: User reports missing data, soft-deleted records

**Recovery Steps**:
1. Identify affected records from audit logs
2. Restore using soft-delete reversal:
   ```sql
   -- Find recently deleted records
   SELECT * FROM efir_budget.TABLE_NAME
   WHERE deleted_at > NOW() - INTERVAL '24 hours';

   -- Restore specific records
   UPDATE efir_budget.TABLE_NAME
   SET deleted_at = NULL, deleted_by = NULL
   WHERE id IN ('uuid1', 'uuid2');
   ```

**RTO**: 15 minutes | **RPO**: 0 (no data loss)

---

### Scenario 2: Database Corruption

**Symptoms**: Query errors, inconsistent data, application crashes

**Recovery Steps**:
1. **Immediate**: Stop application writes
   ```bash
   # Scale down API instances
   fly scale count 0 -a efir-budget-api
   ```

2. **Assess**: Check Supabase dashboard for issues
   - Navigate to: Project → Logs → Database
   - Review error patterns

3. **Recover**: Use Supabase PITR
   - Dashboard → Settings → Database → Backups
   - Select recovery point (before corruption)
   - Initiate restore

4. **Validate**: Run data integrity checks
   ```sql
   -- Check referential integrity
   SELECT * FROM efir_budget.enrollments e
   LEFT JOIN efir_budget.budget_versions bv ON e.budget_version_id = bv.id
   WHERE bv.id IS NULL AND e.deleted_at IS NULL;
   ```

5. **Resume**: Restart application
   ```bash
   fly scale count 2 -a efir-budget-api
   ```

**RTO**: 1 hour | **RPO**: 5 minutes (PITR granularity)

---

### Scenario 3: Complete Environment Loss

**Symptoms**: All services unavailable, infrastructure failure

**Recovery Steps**:

1. **Provision New Infrastructure**:
   ```bash
   # Create new Supabase project
   supabase projects create efir-budget-dr --region ap-southeast-1

   # Deploy backend to new region
   fly launch --config fly.toml --region sin
   ```

2. **Restore Database**:
   ```bash
   # Option A: From Supabase backup (if available)
   # Use Supabase dashboard to restore backup to new project

   # Option B: From manual backup
   pg_restore "postgresql://postgres:PASSWORD@NEW_PROJECT.supabase.co:5432/postgres" \
     --schema=efir_budget \
     backup_YYYYMMDD.dump
   ```

3. **Apply Latest Migrations**:
   ```bash
   cd backend
   DIRECT_URL="postgresql://..." uv run alembic upgrade head
   ```

4. **Restore Reference Data**:
   ```bash
   # Reference data is stored in migrations, applied automatically
   # Verify with:
   SELECT COUNT(*) FROM efir_budget.subjects;
   SELECT COUNT(*) FROM efir_budget.academic_levels;
   ```

5. **Update DNS/Environment**:
   - Update frontend environment variables
   - Update any external integrations

6. **Validate**:
   ```bash
   # Health check
   curl https://new-api-url/api/health

   # Run smoke tests
   cd frontend && pnpm test:e2e -- --grep "smoke"
   ```

**RTO**: 4 hours | **RPO**: Based on last backup

---

### Scenario 4: Redis Cache Failure

**Symptoms**: Slower response times, cache miss warnings in logs

**Recovery Steps**:
1. **Verify**: Application should continue with graceful degradation
   ```python
   # From app/core/cache.py - automatic fallback
   REDIS_REQUIRED = os.getenv("REDIS_REQUIRED", "false").lower() == "true"
   ```

2. **Restart Redis** (if self-managed):
   ```bash
   brew services restart redis  # macOS
   systemctl restart redis      # Linux
   ```

3. **Cache Warm-up**: Caches regenerate automatically on first access
   - DHG calculations
   - KPI dashboards
   - Enrollment projections

**RTO**: 5 minutes | **RPO**: N/A (cache is regenerable)

---

## Cache Recovery

Redis cache is designed as ephemeral and regenerable:

### Cache Invalidation Hierarchy

```
Enrollment Changes
       ↓
Class Structure Cache (invalidated)
       ↓
DHG Calculations Cache (invalidated)
       ↓
Personnel Costs Cache (invalidated)
       ↓
KPI Dashboard Cache (invalidated)
```

### Manual Cache Clear

```bash
# Clear all caches
redis-cli FLUSHDB

# Clear specific cache namespace
redis-cli KEYS "efir:dhg:*" | xargs redis-cli DEL
redis-cli KEYS "efir:kpi:*" | xargs redis-cli DEL
redis-cli KEYS "efir:enrollment:*" | xargs redis-cli DEL
```

### Cache Configuration

From `backend/.env.example`:
```env
REDIS_ENABLED="true"           # Enable caching
REDIS_REQUIRED="false"         # Graceful degradation if unavailable
REDIS_URL="redis://localhost:6379/0"
REDIS_CONNECT_TIMEOUT="5"
REDIS_SOCKET_TIMEOUT="5"
REDIS_MAX_RETRIES="3"
```

---

## Testing and Validation

### Monthly Backup Verification

```bash
#!/bin/bash
# backup_verification.sh

# 1. Create test database
createdb efir_backup_test

# 2. Restore from latest backup
pg_restore -d efir_backup_test latest_backup.dump

# 3. Run integrity checks
psql efir_backup_test << 'EOF'
-- Verify row counts
SELECT 'budget_versions', COUNT(*) FROM efir_budget.budget_versions
UNION ALL
SELECT 'enrollments', COUNT(*) FROM efir_budget.enrollments
UNION ALL
SELECT 'subjects', COUNT(*) FROM efir_budget.subjects;

-- Verify referential integrity
SELECT 'orphaned_enrollments', COUNT(*)
FROM efir_budget.enrollments e
LEFT JOIN efir_budget.budget_versions bv ON e.budget_version_id = bv.id
WHERE bv.id IS NULL;
EOF

# 4. Cleanup
dropdb efir_backup_test
```

### Quarterly DR Drill

1. **Preparation** (Week before):
   - Schedule maintenance window
   - Notify stakeholders
   - Prepare DR runbook

2. **Execution**:
   - Simulate failure scenario
   - Execute recovery procedures
   - Measure RTO/RPO

3. **Post-Drill**:
   - Document findings
   - Update procedures
   - Schedule remediation

### Automated Health Checks

The application includes health endpoints:

```bash
# Basic health
curl https://api.efir-budget.com/api/health

# Detailed health with dependencies
curl https://api.efir-budget.com/api/health/detailed
```

Response includes:
- Database connectivity
- Redis availability
- Migration status
- Response latency

---

## Runbooks

### Runbook 1: Emergency Database Restore

```bash
#!/bin/bash
# emergency_restore.sh
# Usage: ./emergency_restore.sh RESTORE_POINT_TIMESTAMP

set -e

RESTORE_POINT=${1:-$(date -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)}

echo "🚨 Emergency Restore Initiated"
echo "   Restore Point: $RESTORE_POINT"

# 1. Stop application
echo "📛 Stopping application..."
fly scale count 0 -a efir-budget-api

# 2. Initiate PITR restore via Supabase API
echo "🔄 Initiating database restore..."
curl -X POST "https://api.supabase.com/v1/projects/$PROJECT_REF/database/restore" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"recovery_target_time\": \"$RESTORE_POINT\"}"

# 3. Wait for restore
echo "⏳ Waiting for restore to complete..."
sleep 300  # Adjust based on database size

# 4. Verify database
echo "✅ Verifying database..."
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM efir_budget.budget_versions;"

# 5. Restart application
echo "🚀 Restarting application..."
fly scale count 2 -a efir-budget-api

echo "✅ Emergency restore complete"
```

### Runbook 2: Manual Backup Creation

```bash
#!/bin/bash
# manual_backup.sh
# Creates a manual backup and uploads to S3

set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="efir_budget_${BACKUP_DATE}.dump"

echo "📦 Creating backup: $BACKUP_FILE"

# Create backup
pg_dump "$DIRECT_URL" \
  --schema=efir_budget \
  --format=custom \
  --file="$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Upload to S3 (requires aws cli configured)
aws s3 cp "${BACKUP_FILE}.gz" "s3://efir-backups/${BACKUP_FILE}.gz"

# Verify upload
aws s3 ls "s3://efir-backups/${BACKUP_FILE}.gz"

echo "✅ Backup complete: s3://efir-backups/${BACKUP_FILE}.gz"
```

---

## Contact and Escalation

### Escalation Matrix

| Severity | Response Time | Escalation Path |
|----------|---------------|-----------------|
| P1 (Critical) | 15 minutes | On-call → Tech Lead → CTO |
| P2 (Major) | 1 hour | On-call → Tech Lead |
| P3 (Minor) | 4 hours | On-call |
| P4 (Low) | Next business day | Support ticket |

### Severity Definitions

- **P1**: Complete service outage, data loss risk
- **P2**: Major feature unavailable, degraded performance
- **P3**: Minor feature issue, workaround available
- **P4**: Cosmetic issue, enhancement request

### Key Contacts

| Role | Responsibility | Contact |
|------|----------------|---------|
| On-Call Engineer | First response | PagerDuty rotation |
| Database Admin | Database recovery | [Configure in incident management] |
| Infrastructure Lead | Cloud resources | [Configure in incident management] |
| Product Owner | Business decisions | [Configure in incident management] |

---

## Appendix: Configuration Reference

### Environment Variables for DR

```env
# Database (from backend/.env.example)
DATABASE_URL="postgresql+asyncpg://..."    # Connection pooler
DIRECT_URL="postgresql+asyncpg://..."      # Direct for migrations

# Redis (optional)
REDIS_ENABLED="true"
REDIS_REQUIRED="false"                     # Allow graceful degradation
REDIS_URL="redis://localhost:6379/0"

# Monitoring
SENTRY_DSN_BACKEND="https://..."           # Error tracking
SLOW_QUERY_THRESHOLD="0.1"                 # Log queries > 100ms
```

### Migration Commands

```bash
# View current migration status
uv run alembic current

# View migration history
uv run alembic history

# Upgrade to latest
uv run alembic upgrade head

# Downgrade one version
uv run alembic downgrade -1

# Downgrade to specific version
uv run alembic downgrade 20251201_0030
```

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-12-12 | 1.0 | System Architect | Initial document |
