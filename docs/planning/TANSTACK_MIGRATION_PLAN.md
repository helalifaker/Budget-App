# AG Grid to TanStack Table Migration Plan

> **Document**: TANSTACK_MIGRATION_PLAN.md
> **Created**: 2025-12-14
> **Updated**: 2025-12-15 (Post-Implementation Cleanup)
> **Status**: ✅ Implemented
> **Audit Report**: [2025-12-13_frontend-ui_tanstack-migration-audit.md](docs/agent-work/2025-12-13_frontend-ui_tanstack-migration-audit.md)

---

## Implementation Status (2025-12-15)

This migration is already implemented in the codebase:

- AG Grid dependencies removed from `frontend/package.json`
- No AG Grid imports in `frontend/src`
- TanStack Table components live under `frontend/src/components/grid/tanstack/`
- Excel-like keyboard behavior uses `frontend/src/hooks/useGridExcelKeyboard.ts` + `frontend/src/lib/grid/TanStackAdapter.ts`
- Cleanup completed:
  - Removed AG Grid-only CSS from `frontend/src/index.css`
  - Removed AG Grid-only focus CSS from `frontend/src/components/accessibility/FocusManager.tsx`
  - Removed AG Grid chunking/excludes from `frontend/vite.config.ts`

Local verification:

- `pnpm --filter efir-budget-frontend typecheck`
- `pnpm --filter efir-budget-frontend test -- --run`

The remainder of this document is kept as the original phased plan/audit record for historical context.

## Executive Summary

| Metric | Value |
|--------|-------|
| **Goal** | Replace AG Grid Community with TanStack Table |
| **Bundle Savings** | ~905 KB raw / ~255 KB gzipped (39% of JS bundle) |
| **Timeline** | **7-10 weeks** (revised after full audit) |
| **Risk Level** | **VERY HIGH** (19 grids, dynamic columns, CSS coupling) |
| **Design Priority** | Premium executive aesthetic with compact data density |
| **Feature Parity** | **ROW-BASED Excel-like features** (not true cell-range) |
| **Total Grids** | **19** (11 wrapper + 8 direct) |
| **Highest Risk** | SubjectHoursMatrix (dynamic columns + applyTransaction) |

### Before/After Bundle Comparison

| Library | Current | After Migration |
|---------|---------|-----------------|
| AG Grid | 955 KB (270 KB gzip) | 0 KB |
| TanStack Table | 0 KB | ~50 KB (15 KB gzip) |
| **Net Savings** | - | **~905 KB (~255 KB gzip)** |

### Alternative Considered and Rejected

**Selective AG Grid Module Import**: Could save 50-100 KB gzipped (1-2%) by removing unused modules (PaginationModule, InfiniteRowModelModule, etc.). **REJECTED** because:
- Minimal savings vs. maintenance burden
- User explicitly wants full migration
- Bundle size improvement is the primary goal

---

## Table of Contents

1. [Design Requirements](#design-requirements)
2. [Current State Analysis](#current-state-analysis)
3. [Architecture Design](#architecture-design)
4. [Migration Phases](#migration-phases)
5. [Risk Mitigation](#risk-mitigation)
6. [Success Criteria](#success-criteria)
7. [Safety Checkpoints](#safety-checkpoints)
8. [File Structure](#file-structure)

---

## Design Requirements

### Design System Integration (MANDATORY from Day 1)

The new tables MUST use the existing EFIR design system CSS variables from `frontend/src/index.css`:

```css
/* Background Colors */
--color-canvas: #FAF9F7;        /* Page background */
--color-paper: #FFFFFF;         /* Card/table background */
--color-subtle: #F5F4F1;        /* Alternating rows */
--color-warm: #FBF9F6;          /* Hover state */
--color-muted: #F0EFEC;         /* Selected row */

/* Borders */
--color-border-light: #E8E6E1;  /* Cell borders */
--color-border-medium: #D4D1C9; /* Header border */
--color-border-strong: #C5C2B8; /* Focus ring */

/* Text */
--color-text-primary: #1A1917;  /* Primary text */
--color-text-secondary: #5C5A54; /* Secondary text */
--color-text-tertiary: #8A877E; /* Tertiary text */

/* Accent Colors by Module */
--color-gold: #A68B5B;          /* Finance, primary CTA */
--color-sage: #7D9082;          /* Enrollment, success */
--color-terracotta: #C4785D;    /* Warnings, deficits */
--color-slate: #64748B;         /* Analysis */
--color-wine: #8B5C6B;          /* Workforce */
```

### Compact Table Specifications

| Property | Value | Notes |
|----------|-------|-------|
| Row height | 36px (compact) / 44px (default) | Configurable per table |
| Header height | 40px | Slightly taller for visual hierarchy |
| Cell padding | 8px 12px | Compact but readable |
| Font size | 13px body, 12px header | Smaller than default |
| Font family | Lato, system-ui | Matches design system |
| Border radius | 8px outer, 0 inner | Rounded container only |

### Visual States

```
┌────────────────────────────────────────────────────────────────┐
│ HEADER ROW (40px)                                              │
│ bg: --color-paper | border-bottom: --color-border-medium       │
│ font: 12px semibold uppercase tracking-wide                    │
├────────────────────────────────────────────────────────────────┤
│ DATA ROW (36px) - Normal                                       │
│ bg: --color-paper | border-bottom: --color-border-light        │
├────────────────────────────────────────────────────────────────┤
│ DATA ROW (36px) - Alternating                                  │
│ bg: --color-subtle                                             │
├────────────────────────────────────────────────────────────────┤
│ DATA ROW (36px) - Hover                                        │
│ bg: --color-warm | transition: 150ms ease-out                  │
├────────────────────────────────────────────────────────────────┤
│ DATA ROW (36px) - Selected                                     │
│ bg: --color-gold-lighter | border-left: 3px --color-gold       │
├────────────────────────────────────────────────────────────────┤
│ CELL - Focused                                                 │
│ ring: 2px --color-gold | ring-offset: 1px                      │
├────────────────────────────────────────────────────────────────┤
│ CELL - Editing                                                 │
│ bg: white | ring: 2px --color-gold | shadow-sm                 │
├────────────────────────────────────────────────────────────────┤
│ STATUS BAR (32px)                                              │
│ bg: --color-subtle | border-top: --color-border-light          │
└────────────────────────────────────────────────────────────────┘
```

### Cell Type Styling

| Cell Type | Alignment | Font | Color |
|-----------|-----------|------|-------|
| Text | Left | Normal | --color-text-primary |
| Number | Right | Tabular nums | --color-text-primary |
| Currency | Right | Tabular nums | --color-text-primary |
| Percentage | Right | Tabular nums | --color-text-primary |
| Negative number | Right | Tabular nums | --color-terracotta |
| Positive delta | Right | Tabular nums | --color-sage |
| Boolean | Center | - | Checkbox or ✓/✗ |
| Status badge | Left | 11px semibold | Module color |
| Read-only | - | Normal | --color-text-tertiary |
| Calculated | - | Italic | --color-text-secondary |

### Animations

```css
/* Row hover */
transition: background-color 150ms ease-out;

/* Focus ring */
transition: box-shadow 100ms ease-out;

/* Cell editing */
transition: transform 100ms ease-out, box-shadow 100ms ease-out;

/* Sorting indicator */
transition: transform 200ms ease-out;

/* Loading skeleton */
animation: pulse 1.5s ease-in-out infinite;
```

### Shadows

```css
/* Table container */
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);

/* Sticky header */
box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);

/* Editing cell */
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

/* Dropdown/popover */
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
```

### Accessibility Requirements

- Focus visible on all interactive elements (2px ring)
- Color contrast ≥ 4.5:1 for text
- Keyboard navigation fully functional
- Screen reader announcements for sort/selection/edit changes

---

## Current State Analysis

### Inventory Summary (FINAL AUDIT - 2025-12-13)

| Metric | Count |
|--------|-------|
| Files importing AG Grid | **28** |
| **Total working grids** | **19** |
| Wrapper-based grids | **11** |
| Direct AgGridReact grids | **8** (in 4 routes) |
| Editable grids | 12 |
| Read-only grids | 7 |
| Grids with clipboard support | 4 |
| Custom hooks lines | ~830 |
| AG Grid API methods used | 23 distinct |

### ⚠️ CRITICAL AUDIT FINDINGS

1. **Undo/Redo is NOT implemented** - Despite documentation, `useExcelKeyboard.ts` has no Ctrl+Z/Y logic
2. **Copy/paste is ROW-BASED** - Not true cell-range selection (this is the current behavior to match)
3. **SubjectHoursMatrix is highest-risk** - Dynamic columns + valueSetter + applyTransaction + paste
4. **AG Grid CSS coupling** - `index.css` and `FocusManager.tsx` have AG Grid-specific styles

### Working Grids (COMPLETE 19-Grid Inventory from Audit)

#### Wrapper-Based Grids (11 total)

| Priority | Location | Component | Editable | Clipboard | Notable Features |
|----------|----------|-----------|----------|-----------|------------------|
| **P1** | `/workforce/dhg/gap-analysis` | ExcelDataTableLazy | No | No | Pinned L/R, action buttons |
| **P1** | `/workforce/employees` | ExcelDataTableLazy | No | No | Pinned left, badges, single selection |
| **P1** | `/workforce/aefe-positions` | DataTableLazy | No | No | Pinned L/R, action buttons, badges |
| **P2** | `/configuration/system` | DataTableLazy | Yes (JSON) | No | **autoHeight + wrapText** (special) |
| **P2** | `/configuration/timetable` | DataTableLazy | Yes | No | Cross-field validation, computed capacity |
| **P3** | `/enrollment/settings` | ExcelDataTableLazy | Yes | **Yes** | Conditional cell styles, validation |
| **P3** | `/enrollment/class-structure` | ExcelDataTableLazy | Yes | **Yes** | valueGetter + **historical columns** |
| **P3** | `/finance/settings` | ExcelDataTableLazy | Yes | **Yes** | Numeric editors, paste/clear writeback |
| **P6** | `components/configuration/SubjectHoursMatrix.tsx` | DataTableLazy | Yes | **Yes** | ⚠️ **HIGHEST RISK**: Dynamic columns, valueSetter, applyTransaction |
| **P6** | `components/enrollment/GradeOverridesGrid.tsx` | DataTableLazy | Yes | No | Numeric editors, tooltips |
| **P6** | `components/enrollment/NationalityDistributionPanel.tsx` | DataTableLazy | Yes | No | Computed sum + validity UI |

#### Direct AgGridReact Grids (8 total)

| Priority | Location | Grid Count | Editable | Clipboard | Notable Features |
|----------|----------|------------|----------|-----------|------------------|
| **P4** | `/finance/revenue` | 1 | Partial | No | Pinned left, custom renderers, conditional editability |
| **P4** | `/finance/costs` | 2 | Partial | No | Pinned left, custom renderers, conditional editability |
| **P4** | `/finance/capex` | 1 | Yes | No | Pinned L/R, ActionsCellRenderer (dialog trigger) |
| **P5** | `/planning/dhg` | 4 | Yes | No | Checkboxes, valueGetter, number editors, **4 tabs** |

### Additional Migration Dependencies (NOT Grids)

| File | Type | Description | Priority |
|------|------|-------------|----------|
| `frontend/src/index.css` | CSS | `.ag-theme-quartz*` customization, Excel-mode styles | **REQUIRED** |
| `frontend/src/components/accessibility/FocusManager.tsx` | Component | `.ag-cell*` focus rules injection | **REQUIRED** |
| `frontend/src/components/grid/AccessibleGridWrapper.tsx` | Component | ARIA/live-region wrapper for AG Grid | **REQUIRED** |
| `frontend/src/components/grid/HistoricalColumns.tsx` | Factory | Historical comparison column definitions | **REQUIRED** |
| `frontend/src/components/grid/CurrencyRenderer.tsx` | Renderer | Currency formatting | Port to TanStack |
| `frontend/src/components/grid/AccountCodeRenderer.tsx` | Renderer | Account code display | Port to TanStack |
| `frontend/src/components/grid/StatusBadgeRenderer.tsx` | Renderer | Status badge display | Port to TanStack |

### Must-Match Features (MANDATORY for Parity)

These features MUST be implemented in TanStack Table to achieve feature parity:

#### Column Features
| Feature | Current Status | Priority | Complexity |
|---------|---------------|----------|------------|
| **Column Pinning** (left/right) | ✅ Used in 6+ grids | REQUIRED | HIGH |
| **Column Resizing** | ✅ All grids | REQUIRED | MEDIUM |
| **Column Sorting** | ✅ All grids | REQUIRED | LOW |
| **Column Filtering** | ✅ All grids | REQUIRED | MEDIUM |
| **Column Virtualization** | ⚠️ Not explicit but may be needed | OPTIONAL | HIGH |

#### Cell Features
| Feature | Current Status | Priority | Complexity |
|---------|---------------|----------|------------|
| **valueGetter** | ✅ Used in DHG grids | REQUIRED | MEDIUM |
| **valueFormatter** | ✅ Used in finance/DHG | REQUIRED | MEDIUM |
| **cellStyle (dynamic)** | ✅ All editable grids | REQUIRED | MEDIUM |
| **Custom Cell Renderers** | ✅ 5+ custom renderers | REQUIRED | HIGH |
| **Custom Cell Editors** | ✅ agNumberCellEditor | REQUIRED | HIGH |
| **Function-based editable** | ✅ All conditional edits | REQUIRED | MEDIUM |

#### Selection Features
| Feature | Current Status | Priority | Complexity |
|---------|---------------|----------|------------|
| **Row Selection (multi)** | ✅ Implemented | REQUIRED | MEDIUM |
| **Cell Focus Model** | ✅ Via getFocusedCell | REQUIRED | HIGH |
| **True Cell-Range Selection** | ❌ NOT implemented | NICE-TO-HAVE | VERY HIGH |

#### Keyboard & Clipboard
| Feature | Current Status | Priority | Complexity |
|---------|---------------|----------|------------|
| **Ctrl+C/V** (Excel format) | ✅ Implemented (ROW-BASED) | REQUIRED | HIGH |
| **Ctrl+Z/Y** (Undo/Redo) | ⚠️ **NOT IMPLEMENTED** (audit finding) | NICE-TO-HAVE | HIGH |
| **Ctrl+D** (Fill Down) | ✅ Implemented | REQUIRED | MEDIUM |
| **Ctrl+R** (Fill Right) | ❌ NOT implemented | NICE-TO-HAVE | MEDIUM |
| **Delete/Backspace** | ✅ Implemented | REQUIRED | LOW |
| **Tab/Shift+Tab** | ✅ Implemented | REQUIRED | MEDIUM |
| **Enter/Shift+Enter** | ✅ Implemented | REQUIRED | MEDIUM |
| **F2** (Enter edit) | ✅ Implemented | REQUIRED | LOW |
| **Type-to-edit** | ✅ Implemented | REQUIRED | HIGH |
| **Escape** (Cancel) | ✅ Implemented | REQUIRED | LOW |

> **Audit Correction**: The original plan incorrectly stated undo/redo was implemented via AG Grid's `undoRedoCellEditing`. The actual codebase has NO undo/redo logic in `useExcelKeyboard.ts`.

#### UI Features
| Feature | Current Status | Priority | Complexity |
|---------|---------------|----------|------------|
| **Sticky Header** | ✅ All grids | REQUIRED | MEDIUM |
| **Row Virtualization** | ✅ For large datasets | REQUIRED | HIGH |
| **Status Bar** (Sum/Avg/Count) | ✅ ExcelDataTable | REQUIRED | MEDIUM |
| **Pagination** | ✅ Optional per grid | REQUIRED | LOW |
| **Loading Overlay** | ✅ DataTable | REQUIRED | LOW |

#### NOT Required (Not Currently Used)
- ❌ Master-detail rows
- ❌ Tree data/grouping
- ❌ Pinned rows (footer rows)
- ❌ Context menus (AG Grid Enterprise only)
- ❌ Excel export (using backend reportlab)

### Critical Files to Modify (EXPANDED)

```
frontend/src/
├── hooks/
│   ├── useExcelKeyboard.ts      # 684 lines - MAJOR REFACTOR
│   └── useCustomClipboard.ts    # 147 lines - MAJOR REFACTOR
├── components/
│   ├── DataTable.tsx            # 242 lines - REPLACE
│   ├── DataTableLazy.tsx        # Lazy wrapper - REPLACE
│   ├── EnhancedDataTable.tsx    # 500 lines - REPLACE
│   └── grid/
│       ├── ExcelDataTable.tsx   # 307 lines - REPLACE
│       └── ExcelDataTableLazy.tsx # Lazy wrapper - REPLACE
├── main.tsx                     # Remove ModuleRegistry
├── routes/_authenticated/
│   ├── workforce/               # 3 grids - UPDATE
│   ├── configuration/           # 2 grids - UPDATE
│   ├── enrollment/              # 2 grids - UPDATE
│   ├── finance/
│   │   ├── revenue.tsx          # 1 grid - MAJOR (direct AG Grid)
│   │   ├── costs.tsx            # 2 grids - MAJOR (direct AG Grid)
│   │   ├── capex.tsx            # 1 grid - MAJOR (direct AG Grid)
│   │   └── settings.tsx         # 1 grid - UPDATE
│   └── planning/
│       └── dhg.tsx              # 4 grids - MAJOR (direct AG Grid)
```

---

## Architecture Design

### GridAdapter Abstraction Layer (CORRECTED per Codex Review)

**Key Design Decision**: Focus/selection keyed by `rowId + columnId`, NOT `rowIndex`.
Using rowIndex breaks when sorting/filtering/virtualization changes row order.

```typescript
// frontend/src/lib/grid/GridAdapter.ts

/** Cell identifier - stable across sorting/filtering */
interface CellId {
  rowId: string      // From getRowId callback, NOT index
  columnId: string   // Column field name
}

/** Row node with stable ID */
interface RowNode<TData> {
  id: string         // Stable row ID
  data: TData        // Row data
  rowIndex: number   // Current display index (may change)
}

/** Column definition adapter */
interface ColumnAdapter {
  id: string                           // Field name
  editable: boolean | ((row: RowNode<unknown>) => boolean)
  pinned?: 'left' | 'right'
  width?: number
  valueGetter?: (row: RowNode<unknown>) => unknown
  valueFormatter?: (value: unknown) => string
}

interface GridAdapter<TData> {
  // Selection (keyed by rowId, not index)
  getSelectedRows(): TData[]
  getSelectedRowIds(): string[]
  getSelectedNodes(): RowNode<TData>[]
  selectRows(rowIds: string[]): void
  selectAll(): void
  deselectAll(): void

  // Focus (keyed by rowId + columnId)
  getFocusedCell(): CellId | null
  setFocusedCell(cellId: CellId): void

  // Convert between ID and index (for display purposes only)
  getRowIndexById(rowId: string): number | null
  getRowIdByIndex(index: number): string | null

  // Data Access
  getVisibleColumns(): ColumnAdapter[]
  getRowById(rowId: string): RowNode<TData> | null
  getRowByIndex(index: number): RowNode<TData> | null
  getRowCount(): number
  getVisibleRowIds(): string[]  // Current row model after sort/filter

  // Mutations
  updateCellValue(cellId: CellId, value: unknown): void
  getCellValue(cellId: CellId): unknown

  // Editing (keyed by rowId + columnId)
  isEditing(): boolean
  getEditingCell(): CellId | null
  startEditing(cellId: CellId, initialKey?: string): void
  stopEditing(cancel: boolean): void

  // Scrolling (can use either ID or index)
  scrollToRow(rowId: string): void
  scrollToColumn(columnId: string): void
  scrollToCell(cellId: CellId): void

  // Events
  onSelectionChange(callback: (selectedIds: string[]) => void): () => void
  onFocusChange(callback: (cellId: CellId | null) => void): () => void
  onCellValueChange(callback: (cellId: CellId, oldValue: unknown, newValue: unknown) => void): () => void
}
```

### Why rowId + columnId (Codex Insight)

| Scenario | rowIndex | rowId |
|----------|----------|-------|
| User sorts column A-Z | ❌ Index 5 now shows different data | ✅ "row-123" still same data |
| User filters rows | ❌ Index 5 may not exist | ✅ "row-123" still valid |
| Virtual scroll unmounts rows | ❌ Index changes | ✅ ID stable |
| Paste to filtered grid | ❌ Wrong rows updated | ✅ Correct rows updated |
| Restore focus after re-render | ❌ Focus wrong cell | ✅ Focus correct cell |

### Implementation Strategy

```
┌─────────────────────────────────────────┐
│   ExcelDataTable / DataTable (Props)    │  ← Same public API
├─────────────────────────────────────────┤
│   useGridAdapter() hook                 │  ← Returns GridAdapter
├────────────────────┬────────────────────┤
│   AGGridAdapter    │   TanStackAdapter  │  ← Feature flag selects
│   (existing)       │   (new)            │
└────────────────────┴────────────────────┘

Focus State Management:
┌─────────────────────────────────────────┐
│   focusedCell: { rowId, columnId }      │  ← Stored in React state
│   selectedRowIds: Set<string>           │  ← Not indices
│   editingCell: { rowId, columnId }      │  ← Or null
└─────────────────────────────────────────┘
```

---

## Migration Phases

### Phase 0: Preparation (1 day)

**Goal**: Create abstraction without breaking existing functionality

**Tasks**:
1. Create `GridAdapter` interface in `frontend/src/lib/grid/GridAdapter.ts`
2. Create `AGGridAdapter` class wrapping existing `GridApi` usage
3. Refactor `useExcelKeyboard` to use `GridAdapter` instead of `GridApi`
4. Refactor `useCustomClipboard` to use `GridAdapter`
5. Verify all 8 grids still work identically

**Files Created**:
- `frontend/src/lib/grid/GridAdapter.ts` (interface)
- `frontend/src/lib/grid/AGGridAdapter.ts` (AG Grid implementation)
- `frontend/src/lib/grid/index.ts` (exports)

**Verification**:
- [ ] All existing grid tests pass
- [ ] Manual verification of all 8 grids

---

### Phase 1: TanStack Foundation (2-3 days)

**Goal**: Install TanStack Table and create base infrastructure

**Tasks**:
1. Install dependencies:
   ```bash
   pnpm add @tanstack/react-table @tanstack/react-virtual
   ```
2. Create feature flag in `frontend/src/lib/feature-flags.ts`
3. Create `TanStackAdapter` implementing `GridAdapter`
4. Create `BaseTable` component (read-only, no editing)
5. Create `useTableState` hook for focus/selection state
6. Create virtualization wrapper using `@tanstack/react-virtual`

**Files Created**:
- `frontend/src/lib/grid/TanStackAdapter.ts`
- `frontend/src/components/grid/tanstack/BaseTable.tsx`
- `frontend/src/components/grid/tanstack/useTableState.ts`
- `frontend/src/components/grid/tanstack/VirtualizedTable.tsx`
- `frontend/src/lib/feature-flags.ts`

**Verification**:
- [ ] Unit tests for TanStackAdapter
- [ ] Render test for BaseTable with mock data
- [ ] Virtual scroll performance test (1000 rows)

---

### Phase 2: Read-Only Grid Migration (2 days)

**Goal**: Migrate 3 lowest-risk grids

**Grids**: P1 priority (workforce module)

**Tasks per Grid**:
1. Create TanStack column definitions matching AG Grid ColDefs
2. Map cell renderers (StatusBadgeRenderer, CurrencyRenderer)
3. Implement sorting/filtering
4. Implement pagination
5. Test visual parity with AG Grid version
6. Test keyboard navigation (Tab, Arrow keys)

**Files Modified**:
- `frontend/src/routes/_authenticated/workforce/dhg/gap-analysis.tsx`
- `frontend/src/routes/_authenticated/workforce/employees.tsx`
- `frontend/src/routes/_authenticated/workforce/aefe-positions.tsx`

**Verification**:
- [ ] Visual regression tests (screenshots)
- [ ] Sorting/filtering tests
- [ ] Pagination tests
- [ ] Accessibility tests (ARIA)

---

### Phase 3: Editing Infrastructure (3-4 days)

**Goal**: Build cell editing system for TanStack Table

**Tasks**:
1. Create `EditableCell` component with:
   - Click-to-edit
   - Type-to-edit (auto-start on keypress)
   - F2 to edit
   - Enter to confirm
   - Escape to cancel
2. Create cell editors:
   - `NumberCellEditor` (with min/max/step/precision)
   - `TextCellEditor`
   - `CheckboxCellEditor`
   - `LargeTextCellEditor` (for JSON)
3. Create edit state management hook
4. Implement focus ring styling
5. Implement cell validation feedback

**Files Created**:
- `frontend/src/components/grid/tanstack/EditableCell.tsx`
- `frontend/src/components/grid/tanstack/editors/NumberEditor.tsx`
- `frontend/src/components/grid/tanstack/editors/TextEditor.tsx`
- `frontend/src/components/grid/tanstack/editors/CheckboxEditor.tsx`
- `frontend/src/components/grid/tanstack/editors/LargeTextEditor.tsx`
- `frontend/src/components/grid/tanstack/useEditState.ts`

**Verification**:
- [ ] Unit tests for each editor
- [ ] Integration test for edit flow
- [ ] Keyboard navigation during edit
- [ ] Validation feedback tests

---

### Phase 4: Simple Editable Grid Migration (2 days)

**Goal**: Migrate 2 editable grids without clipboard features

**Grids**: P2 priority (configuration module)

**Tasks per Grid**:
1. Map column definitions with editable flags
2. Implement `onCellValueChanged` equivalent
3. Test inline editing
4. Test validation (min/max constraints)
5. Test undo/redo integration

**Files Modified**:
- `frontend/src/routes/_authenticated/configuration/system.tsx`
- `frontend/src/routes/_authenticated/configuration/timetable.tsx`

**Verification**:
- [ ] Edit and save tests
- [ ] Validation rejection tests
- [ ] Undo/redo tests
- [ ] Cross-field validation tests

---

### Phase 5: Keyboard & Clipboard (3-4 days)

**Goal**: Full Excel-like keyboard experience with TanStack Table

**Keyboard Shortcuts**:
| Shortcut | Action |
|----------|--------|
| Ctrl+C | Copy selected cells to clipboard |
| Ctrl+V | Paste from clipboard |
| Ctrl+A | Select all |
| Ctrl+D | Fill down |
| Delete/Backspace | Clear cells |
| Tab/Shift+Tab | Navigate cells horizontally |
| Enter/Shift+Enter | Navigate cells vertically |
| F2 | Enter edit mode |
| Escape | Cancel edit |
| Any printable key | Start editing (type-to-edit) |

**Tasks**:
1. Adapt `useExcelKeyboard` for TanStackAdapter
2. Adapt `useCustomClipboard` for TanStackAdapter
3. Test Excel copy/paste compatibility
4. Test selection statistics (sum, average, min, max)

**Files Modified**:
- `frontend/src/hooks/useExcelKeyboard.ts` (use GridAdapter)
- `frontend/src/hooks/useCustomClipboard.ts` (use GridAdapter)

**Verification**:
- [ ] Test each keyboard shortcut individually
- [ ] Test copy from AG Grid, paste to TanStack
- [ ] Test copy from TanStack, paste to Excel
- [ ] Test multi-row selection operations
- [ ] Test status bar statistics accuracy

---

### Phase 6: Complex Editable Grid Migration (3-4 days)

**Goal**: Migrate final 3 grids with full clipboard support

**Grids**: P3 priority (enrollment, finance)

**Tasks per Grid**:
1. Full column definition migration
2. Clipboard integration testing
3. Delete key cell clearing
4. Fill down testing
5. Historical data columns (class-structure)
6. Validation rules

**Files Modified**:
- `frontend/src/routes/_authenticated/enrollment/settings.tsx`
- `frontend/src/routes/_authenticated/enrollment/class-structure.tsx`
- `frontend/src/routes/_authenticated/finance/settings.tsx`

**Verification**:
- [ ] Complete E2E test for each grid
- [ ] Paste from Excel tests
- [ ] Delete and fill down tests
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

---

### Phase 7: Direct AG Grid Routes - Finance (4-5 days) ⚠️ NEW

**Goal**: Migrate 4 direct AgGridReact grids in finance module

**Grids** (P4 priority - complex features):
1. `/finance/revenue` - Revenue Grid
2. `/finance/costs` - Personnel Costs Grid
3. `/finance/costs` - Operating Costs Grid
4. `/finance/capex` - CapEx Grid

**Challenges**:
- Pinned columns (left AND right in capex)
- Function-based `editable` conditions
- Custom `cellStyle` with conditional styling
- Multiple custom renderers (CurrencyRenderer, AccountCodeRenderer, ActionsCellRenderer)
- `valueFormatter` for numbers/dates

**Tasks per Grid**:
1. Map pinned column configuration to TanStack
2. Implement custom cell renderers
3. Port conditional editable logic
4. Port cellStyle conditions
5. Test all cell types render correctly
6. Test editing flows

**Files Modified**:
- `frontend/src/routes/_authenticated/finance/revenue.tsx`
- `frontend/src/routes/_authenticated/finance/costs.tsx`
- `frontend/src/routes/_authenticated/finance/capex.tsx`

**Verification**:
- [ ] Pinned columns work (left and right)
- [ ] CurrencyRenderer displays correctly
- [ ] Conditional editing works (is_auto_calculated, is_calculated)
- [ ] cellStyle applies correctly
- [ ] ActionsCellRenderer in capex works (dialog trigger)

---

### Phase 8: DHG Multi-Grid Page (3-4 days) ⚠️ NEW

**Goal**: Migrate 4 grids in the DHG planning page (most complex page)

**Grids** (P5 priority - highest complexity):
1. Subject Hours tab - valueGetter for Total Hours
2. Teacher FTE tab - valueFormatter for FTE/hours
3. TRMD tab - Deficit/Surplus renderer with icons
4. HSA tab - agNumberCellEditor with constraints

**Unique Challenges**:
- **4 grids in 1 page** with tab switching
- **valueGetter** usage (computed columns)
- **Custom validation** (HSA max hours)
- **Icon rendering** in Deficit/Surplus column
- **Draft tracking** via `onCellValueChanged`

**Tasks**:
1. Create shared column definition utilities for DHG
2. Implement valueGetter support in TanStack
3. Port agNumberCellEditor with min/max constraints
4. Create Deficit/Surplus renderer with icons
5. Test tab switching doesn't break grid state
6. Test validation warnings display

**Files Modified**:
- `frontend/src/routes/_authenticated/planning/dhg.tsx`

**Verification**:
- [ ] All 4 tabs render correctly
- [ ] valueGetter computes Total Hours correctly
- [ ] HSA validation shows warning on exceed
- [ ] Deficit/Surplus shows correct icon/color
- [ ] Tab switching preserves draft state
- [ ] FTE formatting displays correctly

---

### Phase 9: Cleanup & Verification (2-3 days)

**Goal**: Remove AG Grid, finalize bundle savings, comprehensive testing

**Tasks**:
1. Remove feature flag (all routes use TanStack)
2. Delete AG Grid adapter
3. Remove AG Grid from package.json:
   ```bash
   pnpm remove ag-grid-community ag-grid-react
   ```
4. Remove `ModuleRegistry.registerModules()` from main.tsx
5. Delete unused AG Grid components
6. Run bundle analysis to verify savings
7. Update documentation
8. **Cross-browser testing** (Chrome, Firefox, Safari)
9. **Performance profiling** (scroll FPS, memory)

**Files Deleted**:
- `frontend/src/lib/grid/AGGridAdapter.ts`
- Old DataTable components (replaced)

**Files Modified**:
- `frontend/package.json` (remove ag-grid)
- `frontend/src/main.tsx` (remove ModuleRegistry)
- `frontend/tests/components/EnhancedDataTable.test.tsx` (remove ag-grid)

**Verification**:
- [ ] `pnpm build:analyze` shows AG Grid removed
- [ ] Bundle size reduced by ~900 KB
- [ ] All 12+ grids render correctly
- [ ] All E2E tests pass
- [ ] Performance benchmarks acceptable (≥30 FPS scroll)
- [ ] Cross-browser testing complete

---

## Timeline Summary (FINAL - Post Full Audit)

| Phase | Duration | Cumulative | Status | Grids | Risk |
|-------|----------|------------|--------|-------|------|
| Phase 0: Preparation + Wrapper Refactor | 2-3 days | 2-3 days | ⬜ Not Started | 0 | LOW |
| Phase 1: Foundation + CSS Migration | 4-5 days | 6-8 days | ⬜ Not Started | 0 | MEDIUM |
| Phase 2: Read-only grids (P1) | 2-3 days | 8-11 days | ⬜ Not Started | 3 | LOW |
| Phase 3: Editing infrastructure | 4-5 days | 12-16 days | ⬜ Not Started | 0 | HIGH |
| Phase 4: Simple editable grids (P2) | 2-3 days | 14-19 days | ⬜ Not Started | 2 | MEDIUM |
| Phase 5: Keyboard & clipboard | 4-5 days | 18-24 days | ⬜ Not Started | 0 | HIGH |
| Phase 6: Complex wrapper grids (P3) | 3-4 days | 21-28 days | ⬜ Not Started | 3 | MEDIUM |
| Phase 7: Finance routes (P4) | 4-5 days | 25-33 days | ⬜ Not Started | 4 | MEDIUM |
| Phase 8: DHG multi-grid (P5) | 3-4 days | 28-37 days | ⬜ Not Started | 4 | HIGH |
| **Phase 9: SubjectHoursMatrix (P6)** | **3-4 days** | 31-41 days | ⬜ Not Started | **1** | **VERY HIGH** |
| **Phase 10: Enrollment side-panels (P6)** | **2-3 days** | 33-44 days | ⬜ Not Started | **2** | MEDIUM |
| Phase 11: Cleanup & verification | 3-4 days | 36-48 days | ⬜ Not Started | 0 | LOW |

**Total: 7-10 weeks** (revised from 5-6 weeks after full audit)

### Why Timeline Increased Again

| Factor | Previous Estimate | Final Estimate | Reason |
|--------|-------------------|----------------|--------|
| Grid count | 12+ grids | **19 grids** | Full audit found 8 more |
| SubjectHoursMatrix | Not identified | **Separate track** | Highest-risk: dynamic cols + applyTransaction |
| CSS/Accessibility | Not scoped | **Included** | index.css + FocusManager + AccessibleGridWrapper |
| Enrollment panels | Not scoped | **Added** | GradeOverridesGrid + NationalityDistributionPanel |
| Undo/redo | "Implemented" | **Not implemented** | Plan was incorrect |
| Testing time | 30% | **40%** | 19 grids requires more verification |

---

## Risk Mitigation

### High Risk Areas

| Risk | Impact | Mitigation |
|------|--------|------------|
| Type-to-edit feature breaks | UX degradation | Test extensively, fallback to F2-only |
| Selection stats incorrect during scroll | Wrong sum/average | Track in state, not DOM |
| Paste to wrong rows (filtered grid) | Data corruption | Use table.getRowModel().rows |
| Focus lost during re-render | Poor keyboard UX | Store focus in state, restore after render |

### Testing Strategy

1. **Unit Tests**: Each adapter method, each editor
2. **Integration Tests**: Edit flows, keyboard shortcuts
3. **E2E Tests**: Complete workflows per grid
4. **Regression Tests**: Compare AG Grid vs TanStack output
5. **Performance Tests**: Scroll FPS, render time, memory

### Rollback Plan

Every phase has a rollback path:
- **Phase 0-1**: Revert to direct GridApi usage
- **Phase 2-6**: Feature flag = false per route
- **Phase 7**: Git revert (keep AG Grid in dependency until verified)

---

## Success Criteria (UPDATED for 19 grids - Post Audit)

### Functional (ROW-BASED Excel-like features)
- [ ] All **19 grids** render correctly
- [ ] All keyboard shortcuts work (Ctrl+C/V/A/D, Tab, Enter, F2, Delete, Escape)
- [ ] Paste from Excel works (ROW-BASED, not cell-range)
- [ ] Copy to Excel works (ROW-BASED, not cell-range)
- [ ] Selection statistics accurate (Sum, Avg, Count, Min, Max)
- [ ] ~~Undo/redo works~~ **NOT IN SCOPE** (was never implemented)
- [ ] Validation works (including HSA constraints)
- [ ] Type-to-edit works (start editing on keypress)

### Column Features
- [ ] Column pinning works (left AND right)
- [ ] Column resizing works
- [ ] Column sorting/filtering works
- [ ] valueGetter computes correctly (DHG Total Hours)
- [ ] valueFormatter displays correctly (FTE, currency, dates)

### Cell Features
- [ ] Function-based editable conditions work
- [ ] Dynamic cellStyle applies correctly
- [ ] Custom cell renderers work (CurrencyRenderer, StatusBadge, etc.)
- [ ] Custom cell editors work (NumberEditor with constraints)

### Performance
- [ ] Initial load time ≤ AG Grid version
- [ ] Scroll performance ≥ 30 FPS with 1000 rows
- [ ] Edit latency ≤ 100ms
- [ ] Tab switching in DHG page is responsive

### Bundle
- [ ] AG Grid removed from bundle
- [ ] Bundle size reduced by ≥ 800 KB (raw)
- [ ] Gzipped JS reduced by ≥ 200 KB

### Quality
- [ ] All existing tests pass
- [ ] New tests for TanStack implementation
- [ ] No accessibility regressions
- [ ] No TypeScript errors
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

---

## Safety Checkpoints (NO MISTAKES Policy)

### Before Each Phase

1. **Git checkpoint**: Create branch `feat/tanstack-table-phase-N`
2. **Verify baseline**: All existing tests pass
3. **Manual verification**: Test all 8 grids manually
4. **Bundle baseline**: Record current bundle size

### During Each Phase

1. **Incremental commits**: Commit after each working feature
2. **No force pushes**: Preserve git history for rollback
3. **Test after each change**: Run relevant tests immediately
4. **TypeScript strict**: No `any` types, no `@ts-ignore`
5. **Lint clean**: `pnpm lint` must pass at all times

### After Each Phase

1. **Visual comparison**: Screenshot comparison with AG Grid version
2. **Keyboard test**: Test ALL shortcuts
3. **Paste test**: Copy from Excel, paste into grid
4. **Performance test**: Measure scroll FPS with 500+ rows
5. **A11y test**: Keyboard-only navigation verification
6. **Cross-browser**: Test Chrome, Firefox, Safari
7. **Document**: Update migration status in this plan

### Phase Completion Checklist

```
[ ] All TypeScript errors resolved
[ ] All lint warnings resolved
[ ] Unit tests pass
[ ] Integration tests pass
[ ] E2E tests pass (if applicable)
[ ] Visual design matches specification
[ ] Keyboard shortcuts functional
[ ] Clipboard operations functional
[ ] Performance acceptable (≥30 FPS scroll)
[ ] Accessibility verified
[ ] Feature flag tested (both ON and OFF)
[ ] Documentation updated
```

---

## File Structure (To Be Created)

```
frontend/src/
├── lib/
│   └── grid/
│       ├── index.ts                    # Public exports
│       ├── GridAdapter.ts              # Interface definition
│       ├── AGGridAdapter.ts            # AG Grid implementation (temporary)
│       ├── TanStackAdapter.ts          # TanStack implementation
│       └── types.ts                    # Shared types
├── components/
│   └── grid/
│       └── tanstack/
│           ├── index.ts                # Public exports
│           ├── DataTable.tsx           # Main table component
│           ├── DataTableCompact.tsx    # Compact variant
│           ├── VirtualizedTable.tsx    # With virtualization
│           ├── EditableTable.tsx       # With editing support
│           ├── ExcelTable.tsx          # Full Excel-like features
│           ├── TableHeader.tsx         # Header with sorting
│           ├── TableBody.tsx           # Body with virtualization
│           ├── TableRow.tsx            # Row with selection
│           ├── TableCell.tsx           # Cell component
│           ├── EditableCell.tsx        # Editable cell wrapper
│           ├── StatusBar.tsx           # Excel status bar
│           ├── editors/
│           │   ├── index.ts
│           │   ├── NumberEditor.tsx
│           │   ├── TextEditor.tsx
│           │   ├── CheckboxEditor.tsx
│           │   └── LargeTextEditor.tsx
│           ├── renderers/
│           │   ├── index.ts
│           │   ├── CurrencyCell.tsx
│           │   ├── StatusBadgeCell.tsx
│           │   ├── PercentageCell.tsx
│           │   └── BooleanCell.tsx
│           ├── hooks/
│           │   ├── useTableState.ts    # Focus, selection state
│           │   ├── useEditState.ts     # Editing state
│           │   └── useVirtualization.ts # Virtual scroll
│           └── styles/
│               └── table.css           # Table-specific styles
└── hooks/
    ├── useExcelKeyboard.ts             # Adapted for GridAdapter
    └── useCustomClipboard.ts           # Adapted for GridAdapter
```

---

## Decision Record

**✅ FULL MIGRATION TO TANSTACK TABLE - CONFIRMED**

| Aspect | Decision |
|--------|----------|
| User confirmed | Yes |
| Design priority | Premium executive aesthetic with compact tables |
| Safety priority | Zero breaking changes, rollback at every phase |
| Timeline | 3-4 weeks |
| Start date | Ready to begin |

---

## Quick Reference Commands

```bash
# Install TanStack dependencies (Phase 1)
pnpm add @tanstack/react-table @tanstack/react-virtual

# Remove AG Grid (Phase 7)
pnpm remove ag-grid-community ag-grid-react

# Bundle analysis
pnpm build:analyze

# Run tests
pnpm test -- --run
pnpm test:e2e
```

---

*Document maintained by: Development Team*
*Last updated: 2025-12-14*
