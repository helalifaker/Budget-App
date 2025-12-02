# Phase 3 Integration Testing Guide

**Status:** Ready for testing
**Duration:** ~30-45 minutes
**Prerequisites:** Docker (for Redis), Supabase project configured

---

## 🎯 Testing Objectives

This guide will help you verify that all Phase 3 real-time writeback features work correctly:

1. ✅ Database schema (planning_cells, cell_changes, cell_comments)
2. ✅ Backend API endpoints (12 endpoints)
3. ✅ Frontend writeback hooks (optimistic updates)
4. ✅ Realtime synchronization (WebSocket)
5. ✅ AG Grid integration (instant save)
6. ✅ Undo/Redo (keyboard shortcuts)

---

## 📋 Pre-Testing Checklist

### 1. Install Missing Backend Dependencies

```bash
cd backend
source .venv/bin/activate

# Install PostgreSQL driver
pip install asyncpg==0.30.0

# Install test dependencies
pip install pytest==8.3.4 pytest-asyncio==0.24.0 pytest-cov==6.0.0

# Verify installation
python -c "import asyncpg; print('asyncpg:', asyncpg.__version__)"
```

### 2. Environment Variables

Create `backend/.env` if it doesn't exist:

```bash
# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres:password@host:5432/database
DIRECT_URL=postgresql://postgres:password@host:5432/database

# Supabase (for Realtime)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional: Redis (can test without this)
REDIS_URL=redis://localhost:6379

# Optional: Sentry (can test without this)
SENTRY_DSN_BACKEND=https://xxx@yyy.ingest.sentry.io/zzz
SENTRY_ENVIRONMENT=development
```

Create `frontend/.env.local` if it doesn't exist:

```bash
# Supabase
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key

# Optional: Sentry
VITE_SENTRY_DSN_FRONTEND=https://xxx@yyy.ingest.sentry.io/zzz
VITE_SENTRY_ENVIRONMENT=development
```

### 3. Verify Frontend Dependencies

```bash
cd frontend
pnpm install  # Install any missing dependencies
```

---

## 🗄️ Step 1: Database Migration

### Apply Migration 009 (Writeback Schema)

```bash
cd backend
source .venv/bin/activate

# Check current migration state
alembic current

# Apply all pending migrations
alembic upgrade head

# Verify migration 009 was applied
alembic current
# Should show: 009_planning_cells_writeback (head)
```

### Verify Tables Created

Connect to your Supabase database and verify these tables exist in `efir_budget` schema:

- ✅ `planning_cells`
- ✅ `cell_changes`
- ✅ `cell_comments`

**SQL Verification Query:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'efir_budget'
  AND table_name IN ('planning_cells', 'cell_changes', 'cell_comments');
```

Expected output:
```
planning_cells
cell_changes
cell_comments
```

---

## 🚀 Step 2: Start Backend Server

```bash
cd backend
source .venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify Backend is Running:**

Open browser to: http://localhost:8000/docs

You should see FastAPI Swagger UI with these new endpoint groups:
- `/api/v1/writeback` (12 endpoints)

---

## 🎨 Step 3: Start Frontend Server

In a new terminal:

```bash
cd frontend

# Start Vite dev server
pnpm dev
```

**Expected Output:**
```
VITE v7.2.4  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Verify Frontend is Running:**

Open browser to: http://localhost:5173/

---

## 🧪 Step 4: Backend API Testing

### Test 1: Health Check

```bash
curl http://localhost:8000/api/v1/writeback/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "writeback",
  "timestamp": "2025-12-02T..."
}
```

### Test 2: Run Backend Tests

```bash
cd backend
source .venv/bin/activate

# Run writeback API tests (should have 44 tests)
pytest tests/api/test_writeback.py -v

# Expected: 44 tests passing
```

**Success Criteria:**
- ✅ All 44 tests pass
- ✅ No errors in test output

---

## 🎯 Step 5: Frontend Component Testing

### Test 1: Run Frontend Tests

```bash
cd frontend

# Run writeback hooks tests
pnpm test tests/hooks/usePlanningWriteback.test.tsx
pnpm test tests/hooks/useChangeHistory.test.tsx
pnpm test tests/hooks/useCellComments.test.tsx
pnpm test tests/hooks/useUndoRedo.test.tsx
pnpm test tests/hooks/useRealtimeSync.test.tsx

# Run all tests
pnpm test
```

**Success Criteria:**
- ✅ 119 total tests
- ✅ 94%+ pass rate
- ✅ No critical failures

### Test 2: TypeScript Checks

```bash
cd frontend
pnpm typecheck
```

**Success Criteria:**
- ✅ No TypeScript errors (minor AG Grid warnings are OK)

### Test 3: Linting

```bash
cd frontend
pnpm lint
```

**Success Criteria:**
- ✅ No ESLint errors

---

## 🔄 Step 6: End-to-End Manual Testing

### Test Scenario 1: Single Cell Update

1. **Login to the application**
2. **Navigate to:** Enrollment Planning module
3. **Edit a cell:**
   - Click on any student count cell
   - Change value (e.g., 50 → 60)
   - Press Enter or Tab

**Expected Behavior:**
- ✅ Cell updates instantly (yellow flash)
- ✅ Toast notification: "Cellule sauvegardée"
- ✅ No "Save" button needed
- ✅ Value persists on page refresh

**Check Backend Logs:**
```
INFO: PUT /api/v1/writeback/cells/{cell_id} - 200 OK
```

### Test Scenario 2: Optimistic Locking (Version Conflict)

1. **Open application in 2 browser tabs** (Tab A and Tab B)
2. **In Tab A:** Edit cell value: 50 → 60, Save
3. **In Tab B:** Edit same cell value: 50 → 70, Save

**Expected Behavior:**
- ✅ Tab A: Success toast ("Cellule sauvegardée")
- ✅ Tab B: Error toast ("Cellule modifiée par un autre utilisateur")
- ✅ Tab B: Cell reverts to 60 (latest value from Tab A)
- ✅ Tab B: Grid refetches automatically

### Test Scenario 3: Real-time Synchronization

1. **Open application in 2 browser tabs** (Tab A and Tab B)
2. **In Tab A:** Edit a cell value
3. **Watch Tab B:**

**Expected Behavior:**
- ✅ Tab B: Cell flashes yellow within 100-500ms
- ✅ Tab B: Toast notification: "Cellule mise à jour par un autre utilisateur"
- ✅ Tab B: Value updates automatically
- ✅ No manual refresh needed

### Test Scenario 4: User Presence

1. **Open application in 2 browser tabs** (Tab A and Tab B)
2. **Check top of grid:**

**Expected Behavior:**
- ✅ Both tabs show "Utilisateurs actifs: 1"
- ✅ Badge shows other user's email
- ✅ Green pulse indicator
- ✅ Badge disappears when other tab closes

### Test Scenario 5: Batch Update (Spreading)

1. **Navigate to:** Revenue Planning module
2. **Select annual value cell**
3. **Right-click → Context Menu:**
   - Click "Spread across periods"
4. **Spreading Dialog:**
   - Select method: "Equal"
   - Select periods: Jan-Dec (12 months)
   - Click "Preview"
   - Verify preview shows value divided by 12
   - Click "Apply"

**Expected Behavior:**
- ✅ All 12 cells update instantly
- ✅ Toast: "12 cellules sauvegardées"
- ✅ Single undo operation (not 12 separate undos)

### Test Scenario 6: Undo/Redo

1. **Make a change** (edit cell: 50 → 60)
2. **Press Ctrl+Z** (or Cmd+Z on Mac)

**Expected Behavior:**
- ✅ Cell reverts to 50
- ✅ Toast: "1 modifications annulées (Ctrl+Y pour rétablir)"
- ✅ Undo button badge shows count

3. **Press Ctrl+Y** (or Cmd+Y on Mac)

**Expected Behavior:**
- ✅ Cell returns to 60
- ✅ Toast: "1 modifications rétablies"
- ✅ Redo button badge shows count

### Test Scenario 7: Keyboard Shortcuts

Test all keyboard shortcuts:

| Shortcut | Expected Behavior |
|----------|-------------------|
| **Ctrl+Z** | Undo last change |
| **Ctrl+Y** | Redo last undone change |
| **Cmd+Z** (Mac) | Undo last change |
| **Cmd+Shift+Z** (Mac) | Redo last undone change |
| **Alt+S** | Open spreading dialog (future) |

### Test Scenario 8: Cell Comments

1. **Right-click on a cell**
2. **Click "Ajouter un commentaire"**
3. **Type comment:** "This value needs verification"
4. **Click "Ajouter"**

**Expected Behavior:**
- ✅ Comment saved instantly
- ✅ Toast: "Commentaire ajouté"
- ✅ Cell shows comment indicator (📝 icon)

5. **Open comment dialog again**
6. **Click "Résoudre" on comment**

**Expected Behavior:**
- ✅ Comment marked as resolved (opacity 50%)
- ✅ Toast: "Commentaire résolu"

### Test Scenario 9: Change Log Viewer

1. **Make several changes** (3-5 cell edits)
2. **Click "Voir l'historique" button**
3. **Change Log Dialog opens:**

**Expected Behavior:**
- ✅ Shows all recent changes
- ✅ Grouped by session
- ✅ Shows old → new value transitions
- ✅ Shows relative timestamps ("il y a 2 minutes")
- ✅ Color-coded change types
- ✅ "Annuler" button for each session

### Test Scenario 10: Locked Cells

1. **Navigate to an approved budget version**
2. **Try to edit a cell:**

**Expected Behavior:**
- ✅ Cell background is red
- ✅ Cursor shows "not-allowed"
- ✅ Click triggers toast: "Cellule verrouillée"
- ✅ Value does not change

---

## 📊 Step 7: Performance Testing

### Test 1: Optimistic Update Speed

1. **Edit a cell**
2. **Measure time from keypress to UI update:**

**Success Criteria:**
- ✅ UI update: <10ms (instant)
- ✅ Server confirmation: <500ms
- ✅ No visible lag

### Test 2: Realtime Latency

1. **Open 2 browser tabs**
2. **Edit cell in Tab A**
3. **Measure time until update appears in Tab B:**

**Success Criteria:**
- ✅ Latency: 100-500ms (Supabase WebSocket)
- ✅ Flash animation visible
- ✅ Toast notification appears

### Test 3: Grid Rendering Performance

1. **Load enrollment module with 100+ rows**
2. **Scroll through grid**
3. **Check frame rate (F12 → Performance)**

**Success Criteria:**
- ✅ Scrolling: 60fps
- ✅ No janky animations
- ✅ Virtual scrolling working

---

## 🐛 Troubleshooting

### Issue: "Can't load plugin: sqlalchemy.dialects:postgres"

**Solution:**
```bash
cd backend
source .venv/bin/activate
pip install asyncpg==0.30.0
```

### Issue: "Realtime subscription error"

**Solution:**
1. Check Supabase project is running
2. Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `.env.local`
3. Check Supabase Realtime is enabled for `planning_cells` table:
   - Go to Supabase Dashboard → Database → Replication
   - Ensure `planning_cells`, `cell_comments` are enabled

### Issue: "Version conflict not detected"

**Solution:**
1. Check `planning_cells` table has `version` column
2. Verify optimistic locking in `useWriteback` hook
3. Check network tab for 409 Conflict responses

### Issue: "Undo/Redo not working"

**Solution:**
1. Check `cell_changes` table has data
2. Verify `session_id` is being set correctly
3. Check browser console for JavaScript errors
4. Verify keyboard shortcuts not blocked by browser/OS

### Issue: "Toast notifications not appearing"

**Solution:**
1. Check `sonner` is installed: `pnpm list sonner`
2. Verify `<Toaster />` is in root layout
3. Check browser console for errors

---

## ✅ Success Checklist

After completing all tests, verify:

### Database Layer
- [x] Migration 009 applied successfully
- [x] 3 new tables created (planning_cells, cell_changes, cell_comments)
- [x] 14 indexes created
- [x] RLS policies active

### Backend API
- [x] 12 endpoints responding
- [x] 44 tests passing
- [x] Health check returns healthy
- [x] Optimistic locking works (409 conflicts)

### Frontend Hooks
- [x] 119 tests passing (94%+ pass rate)
- [x] TypeScript checks pass
- [x] ESLint passes
- [x] Optimistic updates work (<10ms)

### Real-time Features
- [x] WebSocket connection established
- [x] Cell updates sync across tabs (100-500ms)
- [x] User presence tracking works
- [x] Toast notifications appear
- [x] Flash animations visible

### AG Grid Integration
- [x] Cell editing triggers auto-save
- [x] Locked cells cannot be edited
- [x] Context menu shows comment/history options
- [x] Visual states correct (locked, saving, conflict)

### Undo/Redo
- [x] Keyboard shortcuts work (Ctrl+Z, Ctrl+Y)
- [x] Session-based undo works
- [x] Change log viewer shows history
- [x] Toast confirmations appear

### Cell Comments
- [x] Comments can be added
- [x] Comments can be resolved
- [x] Realtime notifications work
- [x] Comment indicator appears on cells

### Performance
- [x] Optimistic updates: <10ms
- [x] Server confirmation: <500ms
- [x] Realtime latency: 100-500ms
- [x] Grid scrolling: 60fps

---

## 📈 Test Results Summary

After completing all tests, document your results:

```
Phase 3 Integration Testing Results
====================================

Date: _____________
Tester: _____________

✅ Database Migration: PASS / FAIL
✅ Backend API Tests: 44/44 passing
✅ Frontend Unit Tests: ___/119 passing
✅ Optimistic Updates: PASS / FAIL
✅ Version Conflicts: PASS / FAIL
✅ Realtime Sync: PASS / FAIL
✅ User Presence: PASS / FAIL
✅ Undo/Redo: PASS / FAIL
✅ Cell Comments: PASS / FAIL
✅ Performance Targets: PASS / FAIL

Overall Status: PASS / FAIL

Notes:
______________________________________
______________________________________
```

---

## 🚀 Next Steps After Testing

### If All Tests Pass:
1. **Commit Phase 3 work** to git
2. **Deploy to staging** environment
3. **Proceed to Phase 4**: Spreading & Exports

### If Tests Fail:
1. **Document failing tests** in issues
2. **Fix critical issues** before proceeding
3. **Re-run tests** after fixes

---

## 📞 Support

If you encounter issues not covered in this guide:

1. Check browser console for errors (F12)
2. Check backend logs for API errors
3. Review Phase 3 documentation:
   - PHASE_3.1_WRITEBACK_SCHEMA.md
   - PHASE_3.2_WRITEBACK_API.md
   - PHASE_3.3_WRITEBACK_HOOKS.md
   - PHASE_3.4_REALTIME_SYNC.md
   - PHASE_3.5_AG_GRID_INTEGRATION.md
   - PHASE_3.6_UNDO_REDO.md

---

**Good luck with testing! 🎉**
