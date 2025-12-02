# Phase 3.1: Cell-Level Writeback Schema Implementation

**Migration:** `009_planning_cells_writeback`
**Date:** December 2, 2025
**Status:** ✅ Complete
**Dependencies:** Migration `bfc62faea07a` (materialized views)

## Overview

This migration implements the foundational database schema for **real-time cell-level writeback** with multi-user collaboration support. It transforms the EFIR Budget App from aggregate-based storage to Excel-like cell-level storage, enabling instant save, unlimited undo/redo, and real-time collaboration.

## Business Value

### Current State (Aggregate Storage)
- One record per entity (e.g., one enrollment record per level)
- "Save" button required for persistence
- No undo/redo functionality
- Limited audit trail
- No multi-user conflict detection
- No cell-level comments

### New Capabilities (Cell-Level Storage)
✅ **Excel-like Instant Save**: No "Save" button - changes persist immediately
✅ **Multi-User Collaboration**: Conflict detection via optimistic locking
✅ **Unlimited Undo/Redo**: Complete change history with session grouping
✅ **Cell-Level Comments**: Annotations and discussions on individual cells
✅ **Real-time Sync**: Supabase Realtime for instant updates across users
✅ **Audit Trail**: Every change tracked with who/when/what

## Schema Design

### Table 1: `planning_cells` (Cell-Level Storage)

**Purpose:** Store individual cell values for all planning modules

**Key Fields:**
- `id`: UUID primary key
- `budget_version_id`: FK to budget version (CASCADE delete)
- `module_code`: Planning module identifier (enrollment, dhg, revenue, costs, capex)
- `entity_id`: FK to source entity (enrollment_plans.id, revenue_plans.id, etc.)
- `field_name`: Field identifier (student_count, tuition_rate_sar, fte_count)
- `period_code`: Period identifier (2025-01, P1, T1) or NULL for non-periodic fields
- `value_numeric`: Numeric value (NUMERIC(18,4) for precision)
- `value_text`: Text value (for enums, status, notes)
- `value_type`: Source of value (input, calculated, imported)
- `is_locked`: Prevents edits during calculation or approval
- `lock_reason`: Why cell is locked (e.g., "Under approval")
- `modified_by`: UUID FK to auth.users
- `modified_at`: Timestamp of last modification
- `version`: Optimistic locking version (increment on update)
- `created_at`: Timestamp of creation

**Constraints:**
- Unique constraint on `(budget_version_id, module_code, entity_id, field_name, period_code)`
- Ensures one value per cell

**Example Row:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "budget_version_id": "abc123...",
  "module_code": "enrollment",
  "entity_id": "def456...",
  "field_name": "student_count",
  "period_code": "2025-09",
  "value_numeric": 150,
  "value_text": null,
  "value_type": "input",
  "is_locked": false,
  "lock_reason": null,
  "modified_by": "user123...",
  "modified_at": "2025-12-02T10:30:00Z",
  "version": 3,
  "created_at": "2025-12-01T09:00:00Z"
}
```

### Table 2: `cell_changes` (Complete Audit Trail)

**Purpose:** Track every change to planning cells for undo/redo and audit compliance

**Key Fields:**
- `id`: UUID primary key
- `cell_id`: FK to planning_cells (CASCADE delete)
- `budget_version_id`: Denormalized for fast queries
- `module_code`: Denormalized for fast queries
- `entity_id`: Denormalized for fast queries
- `field_name`: Denormalized for fast queries
- `period_code`: Denormalized for fast queries
- `old_value`: Previous numeric value
- `new_value`: New numeric value
- `change_type`: Type of change (manual, spread, import, undo, redo, calculation)
- `session_id`: Groups related changes (bulk operations, undo/redo)
- `sequence_number`: Order within session (for replay)
- `changed_by`: UUID FK to auth.users
- `changed_at`: Timestamp of change

**Change Types:**
- `manual`: User edit via UI
- `spread`: Auto-fill operation (copy down, spread across periods)
- `import`: External data import (Odoo, Skolengo, AEFE)
- `undo`: Undo operation
- `redo`: Redo operation
- `calculation`: Automated calculation update

**Example Row (Manual Change):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "cell_id": "550e8400-e29b-41d4-a716-446655440000",
  "budget_version_id": "abc123...",
  "module_code": "enrollment",
  "entity_id": "def456...",
  "field_name": "student_count",
  "period_code": "2025-09",
  "old_value": 145,
  "new_value": 150,
  "change_type": "manual",
  "session_id": "xyz789...",
  "sequence_number": 1,
  "changed_by": "user123...",
  "changed_at": "2025-12-02T10:30:00Z"
}
```

**Example Usage (Undo Last 3 Changes):**
```sql
-- Get last 3 changes for a user session
SELECT * FROM cell_changes
WHERE session_id = 'xyz789...'
ORDER BY sequence_number DESC
LIMIT 3;

-- Revert each change (update planning_cells.value_numeric = old_value)
-- Insert new change records with change_type = 'undo'
```

### Table 3: `cell_comments` (Cell-Level Annotations)

**Purpose:** Enable cell-level comments for collaboration and documentation

**Key Fields:**
- `id`: UUID primary key
- `cell_id`: FK to planning_cells (CASCADE delete)
- `comment_text`: Comment content
- `is_resolved`: Discussion status (false = open, true = resolved)
- `created_by`: UUID FK to auth.users
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update

**Example Row:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "cell_id": "550e8400-e29b-41d4-a716-446655440000",
  "comment_text": "Increased enrollment assumption based on new marketing campaign",
  "is_resolved": false,
  "created_by": "user456...",
  "created_at": "2025-12-02T11:00:00Z",
  "updated_at": "2025-12-02T11:00:00Z"
}
```

## Performance Optimization

### 14 Specialized Indexes

#### planning_cells (5 indexes)
1. **idx_cells_version**: Fast lookups by budget version (most common filter)
2. **idx_cells_module**: Composite index for module-specific queries
3. **idx_cells_modified**: Time-based queries (recent changes, audit reports)
4. **idx_cells_locked**: Partial index for locked cells (small subset)
5. **idx_cells_lookup**: Covering index for cell lookups (index-only scans)

#### cell_changes (6 indexes)
6. **idx_changes_cell**: Fast lookups by cell_id
7. **idx_changes_session**: Session-based queries (undo/redo)
8. **idx_changes_entity**: Entity-level change history
9. **idx_changes_time**: Time-based queries (audit reports)
10. **idx_changes_user**: User activity tracking
11. **idx_changes_type**: Change type filtering

#### cell_comments (3 indexes)
12. **idx_comments_cell**: Fast lookups by cell_id
13. **idx_comments_unresolved**: Partial index for unresolved comments
14. **idx_comments_user**: User activity tracking

### Index Strategy
- **CONCURRENTLY**: All indexes support concurrent creation (production-safe)
- **Partial Indexes**: For is_locked=true and is_resolved=false (small subsets)
- **Covering Indexes**: Include commonly-selected columns for index-only scans
- **Composite Indexes**: Match common query patterns (version+module+entity)

### Expected Performance
- Cell lookups: **<10ms** (index-only scans)
- Change history queries: **<50ms** (covering indexes)
- Session-based undo: **<100ms** (session+sequence composite index)
- Comment queries: **<20ms** (partial indexes on unresolved)

## Row Level Security (RLS)

### Multi-Tenant Isolation Pattern

All three tables use organization-based isolation via `budget_versions`:

```sql
-- Example policy (planning_cells)
CREATE POLICY planning_cells_org_isolation
ON planning_cells
FOR ALL
USING (
    budget_version_id IN (
        SELECT id FROM budget_versions
        WHERE organization_id = (
            SELECT organization_id FROM user_profiles
            WHERE user_id = auth.uid()
        )
        AND deleted_at IS NULL
    )
);
```

### RLS Policies (3 total)
1. **planning_cells_org_isolation**: Users access only their org's cells
2. **cell_changes_org_isolation**: Users access only their org's change history
3. **cell_comments_org_isolation**: Users access only their org's comments (via planning_cells FK)

### Security Guarantees
✅ Users cannot view/edit cells from other organizations
✅ Change history isolated by organization
✅ Comments isolated by organization
✅ Enforced at database level (not application logic)
✅ Supabase Auth integration via auth.uid()

## Supabase Realtime Integration

### Enabled Tables
- ✅ **planning_cells**: Instant sync of cell value changes
- ✅ **cell_comments**: Real-time comment notifications
- ❌ **cell_changes**: Not published (audit trail, queried on-demand)

### Realtime Configuration
```sql
ALTER PUBLICATION supabase_realtime ADD TABLE planning_cells;
ALTER PUBLICATION supabase_realtime ADD TABLE cell_comments;
```

### Use Cases
1. **Multi-User Collaboration**: User A sees User B's changes instantly
2. **Conflict Detection**: User A warned if User B modifies same cell
3. **Comment Notifications**: User A notified when User B adds comment
4. **Optimistic Locking**: Version field prevents lost updates

### Frontend Integration (Example)
```typescript
// Subscribe to cell changes
const cellSubscription = supabase
  .channel('planning_cells_changes')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'efir_budget',
      table: 'planning_cells',
      filter: `budget_version_id=eq.${budgetVersionId}`
    },
    (payload) => {
      // Update local cache with new cell value
      // Check version for conflict detection
      // Show notification to user
    }
  )
  .subscribe();
```

## Migration Validation

### Upgrade Steps
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

### Expected Output
```
INFO  [alembic.runtime.migration] Running upgrade bfc62faea07a -> 009_planning_cells_writeback, planning_cells_writeback
```

### Validation Queries

**1. Verify tables created:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'efir_budget'
  AND table_name IN ('planning_cells', 'cell_changes', 'cell_comments');
```

**2. Verify indexes created:**
```sql
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'efir_budget'
  AND tablename IN ('planning_cells', 'cell_changes', 'cell_comments')
ORDER BY indexname;
```

**Expected:** 14 indexes

**3. Verify RLS enabled:**
```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'efir_budget'
  AND tablename IN ('planning_cells', 'cell_changes', 'cell_comments');
```

**Expected:** All `rowsecurity = true`

**4. Verify RLS policies:**
```sql
SELECT tablename, policyname
FROM pg_policies
WHERE schemaname = 'efir_budget'
  AND tablename IN ('planning_cells', 'cell_changes', 'cell_comments');
```

**Expected:** 3 policies

**5. Verify Realtime publication:**
```sql
SELECT schemaname, tablename
FROM pg_publication_tables
WHERE pubname = 'supabase_realtime'
  AND tablename IN ('planning_cells', 'cell_comments');
```

**Expected:** 2 tables

### Downgrade Testing
```bash
alembic downgrade -1
```

**Expected:**
- All 3 tables dropped (CASCADE)
- All 14 indexes dropped
- All 3 RLS policies dropped
- Realtime publication updated

## Data Migration Strategy

### Phase 1: Dual Write (Backward Compatible)
1. Keep existing aggregate tables (enrollment_plans, revenue_plans, etc.)
2. Write to both aggregate and cell tables
3. Read from aggregate tables (existing logic)
4. Cell tables accumulate change history

### Phase 2: Dual Read (Transition)
1. Read from cell tables for modules with cell-level UI
2. Fall back to aggregate tables for other modules
3. Validate cell data matches aggregate data

### Phase 3: Cell-Only (Final State)
1. All modules read from cell tables
2. Aggregate tables deprecated (or converted to materialized views)
3. Cell tables become source of truth

### Initial Data Population (Future Migration)

**Example: Populate enrollment cells from existing data**
```sql
INSERT INTO efir_budget.planning_cells (
    budget_version_id,
    module_code,
    entity_id,
    field_name,
    period_code,
    value_numeric,
    value_type,
    modified_by,
    modified_at,
    version
)
SELECT
    ep.budget_version_id,
    'enrollment' as module_code,
    ep.id as entity_id,
    'student_count' as field_name,
    NULL as period_code,  -- Non-periodic field
    ep.student_count as value_numeric,
    'imported' as value_type,
    ep.created_by as modified_by,
    ep.created_at as modified_at,
    1 as version
FROM efir_budget.enrollment_plans ep
WHERE ep.deleted_at IS NULL;
```

## Next Steps (Phase 3.2+)

### Phase 3.2: Cell Service Layer
- [ ] Create `CellService` with CRUD operations
- [ ] Implement optimistic locking (version check)
- [ ] Add bulk operations (batch insert/update)
- [ ] Add session management for grouped changes

### Phase 3.3: Undo/Redo Engine
- [ ] Create `UndoRedoService`
- [ ] Implement stack-based undo/redo
- [ ] Add session grouping for multi-cell operations
- [ ] Add keyboard shortcuts (Ctrl+Z, Ctrl+Y)

### Phase 3.4: Real-time Collaboration
- [ ] Create Supabase Realtime hooks
- [ ] Implement conflict detection UI
- [ ] Add user presence indicators
- [ ] Add optimistic UI updates

### Phase 3.5: Comment System
- [ ] Create `CommentService`
- [ ] Add comment UI component
- [ ] Implement real-time comment notifications
- [ ] Add comment resolution workflow

## Testing Requirements

### Unit Tests (Backend)
```python
# backend/tests/services/test_cell_service.py

async def test_create_cell():
    """Test creating a new planning cell"""

async def test_update_cell_optimistic_locking():
    """Test version conflict detection"""

async def test_bulk_cell_update():
    """Test batch operations with session grouping"""

async def test_cell_locking():
    """Test locked cell prevents updates"""
```

### Integration Tests
```python
# backend/tests/integration/test_cell_writeback.py

async def test_cell_change_audit_trail():
    """Test change history is recorded"""

async def test_undo_redo_flow():
    """Test undo reverts changes and creates undo record"""

async def test_rls_policy_enforcement():
    """Test users cannot access other org's cells"""
```

### E2E Tests (Frontend)
```typescript
// frontend/tests/e2e/cell-writeback.spec.ts

test('cell value changes persist immediately', async ({ page }) => {
  // Edit cell value
  // Verify cell_changes record created
  // Verify planning_cells updated
});

test('optimistic locking prevents conflicts', async ({ page }) => {
  // User A and User B edit same cell
  // User B's save fails with version conflict
  // User B sees conflict resolution UI
});

test('undo reverts last change', async ({ page }) => {
  // Edit cell value
  // Press Ctrl+Z
  // Verify cell reverted
  // Verify cell_changes has undo record
});
```

## Documentation

### API Endpoints (Phase 3.2)
```
POST   /v1/cells                    # Create cell
GET    /v1/cells                    # Get cells (filtered)
PATCH  /v1/cells/{id}               # Update cell (with version)
DELETE /v1/cells/{id}               # Delete cell
POST   /v1/cells/bulk               # Bulk operations
GET    /v1/cells/{id}/changes       # Get change history
POST   /v1/cells/{id}/undo          # Undo last change
POST   /v1/cells/{id}/redo          # Redo last undone change
GET    /v1/cells/{id}/comments      # Get comments
POST   /v1/cells/{id}/comments      # Add comment
PATCH  /v1/comments/{id}/resolve    # Resolve comment
```

### Frontend Hooks (Phase 3.4)
```typescript
// Real-time collaboration hooks
usePlanningCell(cellId)             // Subscribe to cell changes
useCellComments(cellId)             // Subscribe to comments
useUndoRedo(sessionId)              // Undo/redo stack management
useCellLocking(cellId)              // Cell lock status
```

## Quality Checklist

### Migration Quality
- [x] All requirements implemented (3 tables, 14 indexes, RLS, Realtime)
- [x] Upgrade function complete
- [x] Downgrade function complete (reverses upgrade)
- [x] Ruff linting passed
- [x] mypy type checking passed
- [x] Comprehensive inline documentation
- [x] No TODO comments
- [x] No placeholders or incomplete features

### Database Design Quality
- [x] Proper normalization (one value per cell)
- [x] Foreign keys with CASCADE delete
- [x] Unique constraints on natural keys
- [x] Indexes match query patterns
- [x] RLS policies for multi-tenancy
- [x] Realtime enabled for collaboration

### Documentation Quality
- [x] Business purpose clear
- [x] Schema design explained
- [x] Examples with real data
- [x] Performance considerations documented
- [x] Testing requirements defined
- [x] Next steps outlined

## Success Metrics

### Performance Targets
- Cell lookup: **<10ms** p95
- Change history query: **<50ms** p95
- Undo operation: **<100ms** p95
- Realtime latency: **<200ms** p95

### Scalability Targets
- Support **1M+ cells** per budget version
- Support **10M+ change records** (5 years of history)
- Support **100K+ comments**
- Support **50+ concurrent users** per budget version

### Availability Targets
- Migration downtime: **0 minutes** (CONCURRENTLY indexes)
- Query performance: **No regression** vs aggregate tables
- RLS overhead: **<5ms** per query

## Conclusion

Migration `009_planning_cells_writeback` successfully implements the foundational schema for real-time cell-level writeback with multi-user collaboration. All 3 tables, 14 indexes, RLS policies, and Realtime configuration are complete and production-ready.

**Next Phase:** Phase 3.2 - Cell Service Layer implementation

---

**Metadata:**
- **Author:** Database & Supabase Agent
- **Date:** December 2, 2025
- **Migration Revision:** 009_planning_cells_writeback
- **Dependencies:** bfc62faea07a (materialized views)
- **Quality Status:** ✅ All checks passed
- **Production Ready:** ✅ Yes (after validation testing)
