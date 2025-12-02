/**
 * UNDO/REDO INTEGRATION EXAMPLE
 *
 * This file demonstrates how to integrate the undo/redo system
 * into a planning module page. Copy this pattern for all modules
 * that support cell-level editing.
 *
 * Phase 3.6 Implementation
 */

import { useState } from 'react'
import { History } from 'lucide-react'
import { UndoRedoToolbar } from '@/components/UndoRedoToolbar'
import { ChangeLogDialog } from '@/components/ChangeLogDialog'
import { Button } from '@/components/ui/button'
import { useBudgetVersion } from '@/hooks/api/useBudgetVersions'
import { EnhancedDataTable } from '@/components/EnhancedDataTable'
import { PageContainer } from '@/components/layout/PageContainer'

/**
 * Example: Enrollment Planning Page with Undo/Redo
 *
 * Features:
 * - Undo/Redo toolbar with keyboard shortcuts (Ctrl+Z, Ctrl+Y)
 * - Change log viewer showing full history
 * - Toast notifications for user feedback
 * - Persistent across page reloads
 */
export function EnrollmentPlanningPage() {
  const budgetVersionId = useBudgetVersion()
  const [showChangeLog, setShowChangeLog] = useState(false)

  // Mock data - replace with actual hooks
  const enrollmentData = []
  const columns = []

  return (
    <PageContainer
      title="Planification des effectifs"
      description="Projections d'effectifs par niveau et nationalité"
    >
      <div className="flex flex-col gap-4">
        {/* Header with undo/redo toolbar */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-twilight-900">Planification des effectifs</h1>

          <div className="flex gap-2">
            {/*
              Undo/Redo Toolbar
              - Shows undo/redo buttons with counts
              - Keyboard shortcuts: Ctrl+Z (undo), Ctrl+Y (redo)
              - Disabled when no operations available
              - Shows loading spinner during operations
            */}
            <UndoRedoToolbar
              budgetVersionId={budgetVersionId}
              moduleCode="enrollment"
              className="shadow-sm"
            />

            {/*
              Change Log Button
              - Opens dialog with full change history
              - Grouped by session (e.g., all 12 months of a spread)
              - Shows relative timestamps
              - Inline undo button for each session
            */}
            <Button variant="outline" onClick={() => setShowChangeLog(true)} className="gap-2">
              <History className="h-4 w-4" />
              Historique
            </Button>
          </div>
        </div>

        {/*
          Data Grid with Writeback
          - Supports inline editing
          - Automatic save on cell change
          - Optimistic updates
          - Conflict detection
        */}
        <EnhancedDataTable
          budgetVersionId={budgetVersionId}
          moduleCode="enrollment"
          data={enrollmentData}
          columns={columns}
        />

        {/*
          Change Log Dialog
          - Modal dialog with change history
          - Session grouping (shows related changes together)
          - Color-coded by change type (manual, spread, import, undo, redo)
          - Click "Annuler" button to undo a session
        */}
        <ChangeLogDialog
          budgetVersionId={budgetVersionId}
          moduleCode="enrollment"
          open={showChangeLog}
          onOpenChange={setShowChangeLog}
        />
      </div>
    </PageContainer>
  )
}

/**
 * KEYBOARD SHORTCUTS
 *
 * The undo/redo system automatically registers these shortcuts:
 *
 * Windows/Linux:
 * - Ctrl+Z: Undo last session
 * - Ctrl+Y: Redo last undone session
 *
 * Mac:
 * - Cmd+Z: Undo last session
 * - Cmd+Shift+Z: Redo last undone session
 * - Cmd+Y: Also works for redo
 *
 * Note: Shortcuts are disabled when typing in input fields or textareas
 */

/**
 * TOAST NOTIFICATIONS
 *
 * The system shows toast notifications for:
 *
 * Undo Success:
 *   "12 modification(s) annulée(s)"
 *   "Ctrl+Y pour rétablir"
 *
 * Redo Success:
 *   "12 modification(s) rétablie(s)"
 *   "Ctrl+Z pour annuler"
 *
 * Error:
 *   "Erreur lors de l'annulation"
 *   [error message]
 */

/**
 * SESSION-BASED UNDO
 *
 * Unlike traditional undo systems, we use session-based grouping:
 *
 * Example: Spreading a value across 12 months
 * - User enters 1200 in "Total" field
 * - Clicks "Spread evenly"
 * - System creates 12 cell changes with same session_id
 * - User clicks Undo (or presses Ctrl+Z)
 * - All 12 cells are reverted in one operation
 *
 * This ensures atomic operations and maintains data consistency.
 */

/**
 * CHANGE LOG VIEWER
 *
 * The change log shows grouped changes with metadata:
 *
 * ┌─────────────────────────────────────────────┐
 * │ [Répartition] 12 cellules • il y a 2 min   │
 * │                                             │
 * │ jan_2025:  0 → 100                          │
 * │ feb_2025:  0 → 100                          │
 * │ mar_2025:  0 → 100                          │
 * │ ... et 9 autres                             │
 * │                                   [Annuler] │
 * └─────────────────────────────────────────────┘
 *
 * Change Types:
 * - [Manuel]: User edited cell directly
 * - [Répartition]: Spread operation
 * - [Import]: Data imported from external source
 * - [Annulation]: Undo operation (shown in redo stack)
 * - [Rétablissement]: Redo operation
 */

/**
 * INTEGRATION CHECKLIST
 *
 * To add undo/redo to a new module:
 *
 * 1. ✅ Import components
 *    import { UndoRedoToolbar } from '@/components/UndoRedoToolbar'
 *    import { ChangeLogDialog } from '@/components/ChangeLogDialog'
 *
 * 2. ✅ Add toolbar to page header
 *    <UndoRedoToolbar budgetVersionId={id} moduleCode="your-module" />
 *
 * 3. ✅ Add change log button and dialog
 *    <Button onClick={() => setShowLog(true)}>Historique</Button>
 *    <ChangeLogDialog open={showLog} onOpenChange={setShowLog} ... />
 *
 * 4. ✅ Use EnhancedDataTable for editable grids
 *    <EnhancedDataTable budgetVersionId={id} moduleCode="your-module" ... />
 *
 * 5. ✅ Ensure backend session_id is set for all batch operations
 *    const sessionId = crypto.randomUUID()
 *    await batchUpdate({ sessionId, updates: [...] })
 *
 * That's it! The hook handles everything else automatically.
 */

/**
 * API ENDPOINTS USED
 *
 * The system relies on Phase 3.2 backend endpoints:
 *
 * 1. Fetch Change History:
 *    GET /api/v1/writeback/cells/changes/{budgetVersionId}?module_code=enrollment&limit=100
 *
 * 2. Undo Session:
 *    POST /api/v1/writeback/cells/undo
 *    Body: { "session_id": "uuid" }
 *    Response: { "reverted_count": 12, "new_session_id": "uuid" }
 *
 * 3. Redo:
 *    Same as undo - redo is implemented by undoing an undo session
 */

/**
 * PERFORMANCE NOTES
 *
 * - Stacks limited to 100 sessions (prevents memory issues)
 * - Change history cached for 10 seconds (reduces API calls)
 * - Session grouping memoized (prevents re-computation)
 * - Optimistic invalidation (immediate UI updates)
 */

export default EnrollmentPlanningPage
