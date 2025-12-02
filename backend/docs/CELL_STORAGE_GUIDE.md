# Cell-Level Storage Developer Guide

**Quick Reference for Working with Planning Cells**

## Table of Contents
1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Common Patterns](#common-patterns)
4. [Query Examples](#query-examples)
5. [Best Practices](#best-practices)

## Quick Start

### Basic Cell Operations

**Create a cell:**
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
    version
) VALUES (
    'abc123...',            -- budget_version_id
    'enrollment',           -- module_code
    'def456...',            -- entity_id
    'student_count',        -- field_name
    '2025-09',              -- period_code
    150,                    -- value_numeric
    'input',                -- value_type
    auth.uid(),             -- modified_by
    1                       -- version
);
```

**Update a cell (with optimistic locking):**
```sql
UPDATE efir_budget.planning_cells
SET
    value_numeric = 155,
    version = version + 1,
    modified_by = auth.uid(),
    modified_at = NOW()
WHERE id = 'cell-uuid'
  AND version = 3  -- ⚠️ CRITICAL: Check current version
RETURNING *;

-- If UPDATE returns 0 rows → version conflict (cell modified by another user)
```

**Get cell value:**
```sql
SELECT value_numeric, value_type, version, modified_at, modified_by
FROM efir_budget.planning_cells
WHERE budget_version_id = 'abc123...'
  AND module_code = 'enrollment'
  AND entity_id = 'def456...'
  AND field_name = 'student_count'
  AND period_code = '2025-09';
```

## Core Concepts

### 1. Cell Identification (5-Part Key)

Every cell is uniquely identified by:
```typescript
interface CellIdentifier {
  budgetVersionId: string;  // Which budget version
  moduleCode: string;       // Which planning module (enrollment, dhg, revenue, etc.)
  entityId: string;         // Which record (enrollment_plans.id, etc.)
  fieldName: string;        // Which field (student_count, tuition_rate_sar, etc.)
  periodCode: string | null; // Which period (2025-09, P1, T1) or NULL
}
```

**Example:**
```json
{
  "budgetVersionId": "550e8400-e29b-41d4-a716-446655440000",
  "moduleCode": "enrollment",
  "entityId": "660e8400-e29b-41d4-a716-446655440001",
  "fieldName": "student_count",
  "periodCode": "2025-09"
}
```

### 2. Value Types

| Type | Description | Example |
|------|-------------|---------|
| `input` | User entered value | User types 150 in cell |
| `calculated` | Formula result | DHG hours = classes × hours/class |
| `imported` | External system | Skolengo enrollment import |

### 3. Cell Locking

Cells can be locked to prevent edits during:
- Budget approval workflow
- Automated calculation runs
- Data import operations
- Financial consolidation

```sql
-- Lock cells during calculation
UPDATE planning_cells
SET is_locked = true, lock_reason = 'DHG calculation in progress'
WHERE budget_version_id = 'abc123...' AND module_code = 'dhg';

-- Unlock after calculation
UPDATE planning_cells
SET is_locked = false, lock_reason = NULL
WHERE budget_version_id = 'abc123...' AND module_code = 'dhg';
```

### 4. Optimistic Locking

Prevents lost updates when multiple users edit same cell:

```typescript
// Frontend pattern
async function updateCell(cellId: string, newValue: number, currentVersion: number) {
  const result = await supabase
    .from('planning_cells')
    .update({
      value_numeric: newValue,
      version: currentVersion + 1,
      modified_at: new Date().toISOString()
    })
    .eq('id', cellId)
    .eq('version', currentVersion)  // ⚠️ Critical: Check version hasn't changed
    .select();

  if (result.data.length === 0) {
    // Version conflict - another user modified this cell
    throw new ConflictError('Cell was modified by another user. Please refresh.');
  }

  return result.data[0];
}
```

## Common Patterns

### Pattern 1: Bulk Cell Insert (Initial Data Population)

```sql
-- Populate enrollment cells from existing enrollment_plans
INSERT INTO efir_budget.planning_cells (
    budget_version_id,
    module_code,
    entity_id,
    field_name,
    period_code,
    value_numeric,
    value_type,
    modified_by,
    version
)
SELECT
    ep.budget_version_id,
    'enrollment',
    ep.id,
    'student_count',
    NULL,  -- Non-periodic field
    ep.student_count,
    'imported',
    ep.created_by,
    1
FROM efir_budget.enrollment_plans ep
WHERE ep.budget_version_id = 'abc123...'
  AND ep.deleted_at IS NULL
ON CONFLICT (budget_version_id, module_code, entity_id, field_name, period_code)
DO UPDATE SET
    value_numeric = EXCLUDED.value_numeric,
    version = planning_cells.version + 1,
    modified_at = NOW();
```

### Pattern 2: Session-Based Change Tracking

```sql
-- Start session (generate UUID)
SELECT gen_random_uuid() AS session_id;  -- Returns: xyz789...

-- Make multiple changes (same session_id)
INSERT INTO efir_budget.cell_changes (
    cell_id, budget_version_id, module_code, entity_id, field_name, period_code,
    old_value, new_value, change_type, session_id, sequence_number, changed_by
) VALUES
    ('cell1', 'bv1', 'enrollment', 'ent1', 'student_count', '2025-09', 145, 150, 'manual', 'xyz789...', 1, auth.uid()),
    ('cell2', 'bv1', 'enrollment', 'ent1', 'student_count', '2025-10', 148, 152, 'manual', 'xyz789...', 2, auth.uid()),
    ('cell3', 'bv1', 'enrollment', 'ent1', 'student_count', '2025-11', 150, 155, 'manual', 'xyz789...', 3, auth.uid());

-- All 3 changes can be undone together as one operation
```

### Pattern 3: Undo Last Change

```sql
-- Get last change for a cell
WITH last_change AS (
    SELECT *
    FROM efir_budget.cell_changes
    WHERE cell_id = 'cell-uuid'
      AND change_type IN ('manual', 'spread', 'import')
    ORDER BY changed_at DESC
    LIMIT 1
)
-- Revert cell to old value
UPDATE efir_budget.planning_cells pc
SET
    value_numeric = (SELECT old_value FROM last_change),
    version = pc.version + 1,
    modified_by = auth.uid(),
    modified_at = NOW()
FROM last_change
WHERE pc.id = last_change.cell_id;

-- Record undo action
INSERT INTO efir_budget.cell_changes (
    cell_id, budget_version_id, module_code, entity_id, field_name, period_code,
    old_value, new_value, change_type, changed_by
)
SELECT
    cell_id, budget_version_id, module_code, entity_id, field_name, period_code,
    new_value, old_value, 'undo', auth.uid()
FROM last_change;
```

### Pattern 4: Get Cell Change History

```sql
-- Get all changes for a specific cell
SELECT
    cc.changed_at,
    u.email AS changed_by_email,
    cc.old_value,
    cc.new_value,
    cc.change_type
FROM efir_budget.cell_changes cc
LEFT JOIN auth.users u ON u.id = cc.changed_by
WHERE cc.cell_id = 'cell-uuid'
ORDER BY cc.changed_at DESC;
```

### Pattern 5: Add Cell Comment

```sql
-- Add comment
INSERT INTO efir_budget.cell_comments (
    cell_id,
    comment_text,
    is_resolved,
    created_by
) VALUES (
    'cell-uuid',
    'Increased enrollment assumption based on new marketing campaign',
    false,
    auth.uid()
);

-- Get unresolved comments for a cell
SELECT
    cc.comment_text,
    u.email AS created_by_email,
    cc.created_at
FROM efir_budget.cell_comments cc
LEFT JOIN auth.users u ON u.id = cc.created_by
WHERE cc.cell_id = 'cell-uuid'
  AND cc.is_resolved = false
ORDER BY cc.created_at DESC;
```

### Pattern 6: Real-time Subscription (Frontend)

```typescript
// Subscribe to cell changes for a budget version
const cellSubscription = supabase
  .channel('planning_cells_changes')
  .on(
    'postgres_changes',
    {
      event: '*',  // INSERT, UPDATE, DELETE
      schema: 'efir_budget',
      table: 'planning_cells',
      filter: `budget_version_id=eq.${budgetVersionId}`
    },
    (payload) => {
      console.log('Cell changed:', payload);

      // Check for version conflict
      if (payload.eventType === 'UPDATE') {
        const updatedCell = payload.new;
        const localCell = getCellFromCache(updatedCell.id);

        if (localCell && localCell.version !== updatedCell.version) {
          // Another user modified this cell
          showConflictWarning(updatedCell);
        } else {
          // Update local cache
          updateCellInCache(updatedCell);
        }
      }
    }
  )
  .subscribe();

// Subscribe to comments for a specific cell
const commentSubscription = supabase
  .channel(`cell_comments_${cellId}`)
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'efir_budget',
      table: 'cell_comments',
      filter: `cell_id=eq.${cellId}`
    },
    (payload) => {
      console.log('New comment:', payload.new);
      showCommentNotification(payload.new);
    }
  )
  .subscribe();
```

## Query Examples

### Get All Cells for a Module

```sql
SELECT
    pc.id,
    pc.entity_id,
    pc.field_name,
    pc.period_code,
    pc.value_numeric,
    pc.value_text,
    pc.value_type,
    pc.is_locked,
    pc.version,
    pc.modified_at,
    u.email AS modified_by_email
FROM efir_budget.planning_cells pc
LEFT JOIN auth.users u ON u.id = pc.modified_by
WHERE pc.budget_version_id = 'abc123...'
  AND pc.module_code = 'enrollment'
ORDER BY pc.entity_id, pc.field_name, pc.period_code;
```

### Get Cells with Unresolved Comments

```sql
SELECT DISTINCT
    pc.id,
    pc.field_name,
    pc.value_numeric,
    COUNT(cc.id) AS comment_count
FROM efir_budget.planning_cells pc
INNER JOIN efir_budget.cell_comments cc ON cc.cell_id = pc.id
WHERE pc.budget_version_id = 'abc123...'
  AND cc.is_resolved = false
GROUP BY pc.id, pc.field_name, pc.value_numeric
ORDER BY comment_count DESC;
```

### Get Recently Modified Cells

```sql
SELECT
    pc.module_code,
    pc.field_name,
    pc.value_numeric,
    pc.modified_at,
    u.email AS modified_by_email
FROM efir_budget.planning_cells pc
LEFT JOIN auth.users u ON u.id = pc.modified_by
WHERE pc.budget_version_id = 'abc123...'
  AND pc.modified_at > NOW() - INTERVAL '1 hour'
ORDER BY pc.modified_at DESC;
```

### Get User Activity Summary

```sql
SELECT
    u.email,
    COUNT(*) AS total_changes,
    COUNT(*) FILTER (WHERE cc.change_type = 'manual') AS manual_changes,
    COUNT(*) FILTER (WHERE cc.change_type = 'undo') AS undo_count,
    MAX(cc.changed_at) AS last_activity
FROM efir_budget.cell_changes cc
LEFT JOIN auth.users u ON u.id = cc.changed_by
WHERE cc.budget_version_id = 'abc123...'
  AND cc.changed_at > NOW() - INTERVAL '7 days'
GROUP BY u.email
ORDER BY total_changes DESC;
```

## Best Practices

### 1. Always Use Optimistic Locking
```typescript
// ✅ GOOD: Check version before update
await updateCellWithVersion(cellId, newValue, currentVersion);

// ❌ BAD: Update without version check (lost update risk)
await updateCellDirectly(cellId, newValue);
```

### 2. Group Related Changes in Sessions
```typescript
// ✅ GOOD: Group bulk operation with session_id
const sessionId = uuidv4();
await bulkUpdateCells(changes, sessionId);

// ❌ BAD: Individual changes without session (can't undo as group)
for (const change of changes) {
  await updateCell(change);
}
```

### 3. Record Change History for All Updates
```typescript
// ✅ GOOD: Insert cell_changes record
await recordCellChange({
  cellId,
  oldValue,
  newValue,
  changeType: 'manual',
  sessionId,
  sequenceNumber
});

// ❌ BAD: Update planning_cells without audit trail
await updateCellWithoutHistory(cellId, newValue);
```

### 4. Use Partial Indexes for Filtering
```sql
-- ✅ GOOD: Query uses partial index (idx_cells_locked)
SELECT * FROM planning_cells
WHERE budget_version_id = 'abc123...'
  AND is_locked = true;  -- Index scan on partial index

-- ✅ GOOD: Query uses partial index (idx_comments_unresolved)
SELECT * FROM cell_comments
WHERE cell_id = 'cell-uuid'
  AND is_resolved = false;  -- Index scan on partial index
```

### 5. Lock Cells During Calculations
```typescript
// ✅ GOOD: Lock cells before calculation, unlock after
await lockCells(budgetVersionId, 'dhg', 'DHG calculation in progress');
try {
  await calculateDHG(budgetVersionId);
} finally {
  await unlockCells(budgetVersionId, 'dhg');
}

// ❌ BAD: Allow edits during calculation (data inconsistency)
await calculateDHG(budgetVersionId);
```

### 6. Handle Version Conflicts Gracefully
```typescript
// ✅ GOOD: Show user-friendly conflict resolution
try {
  await updateCell(cellId, newValue, currentVersion);
} catch (error) {
  if (error instanceof ConflictError) {
    // Show dialog: "Cell was modified by another user. Refresh and try again?"
    const shouldRefresh = await showConflictDialog();
    if (shouldRefresh) {
      await refreshCell(cellId);
    }
  }
}

// ❌ BAD: Silent failure or generic error
try {
  await updateCell(cellId, newValue, currentVersion);
} catch (error) {
  console.error('Update failed');  // User has no idea what happened
}
```

### 7. Use Covering Indexes for Common Queries
```sql
-- ✅ GOOD: Query uses covering index (idx_cells_lookup) - index-only scan
SELECT value_numeric, value_text, value_type, version
FROM planning_cells
WHERE budget_version_id = 'abc123...'
  AND module_code = 'enrollment'
  AND entity_id = 'def456...'
  AND field_name = 'student_count'
  AND period_code = '2025-09';

-- Index includes: budget_version_id, module_code, entity_id, field_name, period_code
-- Plus INCLUDE: value_numeric, value_text, value_type, version
-- Result: No table access needed (index-only scan)
```

### 8. Denormalize for Audit Queries
```sql
-- ✅ GOOD: cell_changes denormalizes cell metadata for fast queries
SELECT * FROM cell_changes
WHERE budget_version_id = 'abc123...'  -- No JOIN needed
  AND module_code = 'enrollment'       -- No JOIN needed
  AND entity_id = 'def456...';         -- No JOIN needed

-- ❌ BAD: Always JOIN to planning_cells (slower)
SELECT cc.* FROM cell_changes cc
JOIN planning_cells pc ON pc.id = cc.cell_id
WHERE pc.budget_version_id = 'abc123...'  -- Expensive JOIN
  AND pc.module_code = 'enrollment';
```

## Performance Tips

### 1. Batch Operations
```typescript
// ✅ GOOD: Batch insert (1 query)
await supabase
  .from('planning_cells')
  .insert(cellsArray);

// ❌ BAD: Individual inserts (N queries)
for (const cell of cellsArray) {
  await supabase.from('planning_cells').insert(cell);
}
```

### 2. Use Index Hints
```sql
-- Query planner usually chooses correct index, but you can force it
SELECT * FROM planning_cells
WHERE budget_version_id = 'abc123...'
  AND module_code = 'enrollment';

-- Index: idx_cells_version (budget_version_id)
-- OR: idx_cells_module (module_code, entity_id)
-- Planner chooses based on selectivity
```

### 3. Limit Change History Queries
```sql
-- ✅ GOOD: Limit history to recent changes
SELECT * FROM cell_changes
WHERE cell_id = 'cell-uuid'
  AND changed_at > NOW() - INTERVAL '30 days'
ORDER BY changed_at DESC
LIMIT 100;

-- ❌ BAD: Query all history (potentially millions of rows)
SELECT * FROM cell_changes
WHERE cell_id = 'cell-uuid';
```

## Troubleshooting

### Problem: Slow Cell Queries
**Solution:** Ensure indexes are used
```sql
EXPLAIN ANALYZE
SELECT * FROM planning_cells
WHERE budget_version_id = 'abc123...'
  AND module_code = 'enrollment';

-- Look for: "Index Scan using idx_cells_version"
-- Avoid: "Seq Scan on planning_cells"
```

### Problem: Version Conflicts Frequent
**Solution:** Implement optimistic UI updates + conflict resolution
```typescript
// Update UI immediately (optimistic)
updateCellInUI(cellId, newValue);

// Send update to server
try {
  await updateCellOnServer(cellId, newValue, version);
} catch (ConflictError) {
  // Revert UI + show conflict dialog
  revertCellInUI(cellId, oldValue);
  showConflictDialog();
}
```

### Problem: Too Many Change Records
**Solution:** Archive old changes (beyond retention period)
```sql
-- Archive changes older than 5 years
INSERT INTO cell_changes_archive
SELECT * FROM cell_changes
WHERE changed_at < NOW() - INTERVAL '5 years';

DELETE FROM cell_changes
WHERE changed_at < NOW() - INTERVAL '5 years';
```

## References

- Migration: `009_planning_cells_writeback`
- Full Documentation: `PHASE_3.1_WRITEBACK_SCHEMA.md`
- API Endpoints: (Phase 3.2 - Coming Soon)
- Frontend Hooks: (Phase 3.4 - Coming Soon)

---

**Last Updated:** December 2, 2025
**Author:** Database & Supabase Agent
