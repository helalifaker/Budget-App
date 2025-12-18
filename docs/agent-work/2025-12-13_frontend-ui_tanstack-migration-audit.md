# TanStack Table Migration Audit (AG Grid → TanStack)

**Date**: 2025-12-13  
**Owner**: frontend-ui (audit)  
**Input Plan**: `TANSTACK_MIGRATION_PLAN.md`  
**Repo**: EFIR Budget App (`frontend/`)

## Executive Summary

Your migration plan is well-phased, but the **actual migration surface is larger than the “8 working grids” list** and there are **AG Grid-specific styling/accessibility dependencies** that must be migrated too.

**Key findings**
- **28 files import AG Grid** in `frontend/src/` (includes routes, components, hooks, global setup).
- **19 active grid instances**:
  - **11 wrapper-based** (`DataTableLazy` / `ExcelDataTableLazy`)
  - **8 direct `<AgGridReact>`** usages across Finance + Planning routes
- **Several grids/features are missing from the plan’s scope** (notably `SubjectHoursMatrix`, `planning/dhg`, and Enrollment panels).
- The app has **AG Grid–specific CSS and focus styles** that must be replaced (`frontend/src/index.css`, `frontend/src/components/accessibility/FocusManager.tsx`).
- “Excel-like” behavior in current code is **row-selection-based**, not true cell-range selection. Also, **undo/redo is documented but not implemented** in `useExcelKeyboard`.

## Inventory (What Uses AG Grid Today)

### Global Setup + Styling Dependencies
- `frontend/src/main.tsx` registers `ModuleRegistry.registerModules([AllCommunityModule])` (bundles all Community modules).
- `frontend/src/index.css` contains `.ag-theme-quartz*` customization and Excel-mode styles.
- `frontend/src/components/accessibility/FocusManager.tsx` injects CSS targeting `.ag-cell` / `.ag-cell-focus`.

### Hooks (Excel/Clipboard)
- `frontend/src/hooks/useExcelKeyboard.ts` (keyboard, copy/paste, selection stats; **row selection** + focused cell; no undo/redo logic).
- `frontend/src/hooks/useCustomClipboard.ts` (React `onPaste` handler that maps clipboard cells to visible columns).

### Core Grid Wrappers
- `frontend/src/components/DataTable.tsx` + `frontend/src/components/DataTableLazy.tsx` (accessible wrapper; sorting/filtering/resizing, pagination defaults, announcements).
- `frontend/src/components/grid/ExcelDataTable.tsx` + `frontend/src/components/ExcelDataTableLazy.tsx` (Excel-ish keyboard + paste + status bar).
- `frontend/src/components/grid/AccessibleGridWrapper.tsx` (ARIA/live-region wrapper around AG Grid).

### AG Grid Renderers / Column Factories
- `frontend/src/components/grid/CurrencyRenderer.tsx`
- `frontend/src/components/grid/AccountCodeRenderer.tsx`
- `frontend/src/components/grid/StatusBadgeRenderer.tsx`
- `frontend/src/components/grid/HistoricalColumns.tsx` (historical comparison column definitions + group)

## Active Grid Instances (19 total)

### Wrapper-based grids (11)

| Location | Component | Editable | Clipboard | Notable Features |
|---|---|---:|---:|---|
| `frontend/src/routes/_authenticated/workforce/dhg/gap-analysis.tsx` | `ExcelDataTableLazy` (aliased as `DataTable`) | No | No | Pinned L/R columns, action button per row |
| `frontend/src/routes/_authenticated/workforce/employees.tsx` | `ExcelDataTableLazy` | No | No | Pinned left, custom badges, rowSelection `"single"` |
| `frontend/src/routes/_authenticated/enrollment/settings.tsx` | `ExcelDataTableLazy` | Yes | **Yes** | Conditional cell styles, validation, local dirty state |
| `frontend/src/routes/_authenticated/enrollment/class-structure.tsx` | `ExcelDataTableLazy` | Yes | **Yes** | `valueGetter` computed column + **historical columns** |
| `frontend/src/routes/_authenticated/finance/settings.tsx` | `ExcelDataTableLazy` | Yes | **Yes** | Numeric editors, value formatting, paste/clear writeback |
| `frontend/src/routes/_authenticated/configuration/system.tsx` | `DataTableLazy` | Yes | No | Large JSON editor, wrapText, autoHeight rows |
| `frontend/src/routes/_authenticated/configuration/timetable.tsx` | `DataTableLazy` | Yes | No | Cross-field validation, computed “capacity” via `valueGetter` |
| `frontend/src/routes/_authenticated/workforce/aefe-positions.tsx` | `DataTableLazy` (aliased as `DataTable`) | No | No | Pinned L/R, action buttons, badges |
| `frontend/src/components/configuration/SubjectHoursMatrix.tsx` | `DataTableLazy` | Yes | **Yes** | **Dynamic columns per level**, `valueSetter`, `applyTransaction`, custom checkbox renderer |
| `frontend/src/components/enrollment/GradeOverridesGrid.tsx` | `DataTableLazy` | Yes | No | Numeric editors, tooltips |
| `frontend/src/components/enrollment/NationalityDistributionPanel.tsx` | `DataTableLazy` | Yes | No | Computed sum + validity UI |

### Direct `<AgGridReact>` grids (8)

| Location | Count | Editable | Clipboard | Notable Features |
|---|---:|---:|---:|---|
| `frontend/src/routes/_authenticated/finance/revenue.tsx` | 1 | Partial | No | Pinned left, custom renderers, conditional editability |
| `frontend/src/routes/_authenticated/finance/costs.tsx` | 2 | Partial | No | Pinned left, custom renderers, conditional editability |
| `frontend/src/routes/_authenticated/finance/capex.tsx` | 1 | Likely | No | Pinned L/R, action renderers (e.g., view schedule) |
| `frontend/src/routes/_authenticated/planning/dhg.tsx` | 4 | Yes | No | Checkboxes, `valueGetter` computed cols, number editors, multiple tabs |

## Feature/Capability Matrix (What You Actually Need to Replace)

### Must-have (used broadly)
- Sorting / basic filtering / column resizing (via `defaultColDef` in many tables)
- Pinned columns (multiple pages rely on `pinned: 'left' | 'right'`)
- Cell renderers (React components in many grids)
- Editable number/text/checkbox cells (built-in AG editors used in multiple places)
- `valueGetter`-style computed columns (capacity, totals, etc.)

### High-risk (largest rebuild effort in TanStack)
- “Excel-like” keyboard + focus model (`useExcelKeyboard.ts`) and paste mapping (`useCustomClipboard.ts`)
- Sticky header + pinned columns + virtualization working together
- Dynamic “matrix” tables with many columns:
  - `SubjectHoursMatrix` (per-level dynamic columns + custom writeback path)
  - Historical comparison columns in `createHistoricalColumns`
- Auto-height + wrapped multi-line cells (System Config JSON editor)

### Hidden coupling to AG Grid (must be migrated or removed)
- Global CSS selectors: `.ag-theme-quartz*`, `.ag-cell`, `.ag-cell-focus` in:
  - `frontend/src/index.css`
  - `frontend/src/components/accessibility/FocusManager.tsx`
- Accessibility wrapper patterns built around AG Grid API (`AccessibleGridWrapper`)

## Plan Gaps vs Current Code

The current plan’s “8 working grids” list does not include:
- **All direct `<AgGridReact>` pages**:
  - `frontend/src/routes/_authenticated/planning/dhg.tsx` (4 grids)
  - `frontend/src/routes/_authenticated/finance/revenue.tsx`
  - `frontend/src/routes/_authenticated/finance/costs.tsx` (2 grids)
  - `frontend/src/routes/_authenticated/finance/capex.tsx`
- **`SubjectHoursMatrix`** (`frontend/src/components/configuration/SubjectHoursMatrix.tsx`) — arguably the most TanStack-hostile grid today (dynamic columns + valueSetter + applyTransaction + paste)
- Enrollment side-panels using `DataTableLazy`:
  - `frontend/src/components/enrollment/GradeOverridesGrid.tsx`
  - `frontend/src/components/enrollment/NationalityDistributionPanel.tsx`
- **Historical columns factory** (`frontend/src/components/grid/HistoricalColumns.tsx`) + CSS classes it references
- **AG Grid–specific styling & focus management** (`frontend/src/index.css`, `frontend/src/components/accessibility/FocusManager.tsx`)

## Accuracy Notes (Current Behavior vs Documented Behavior)

- `useExcelKeyboard.ts` **does not implement Ctrl+Z / Ctrl+Y undo/redo**, despite comments and plan text.
- Copy is based on:
  - Selected rows (`gridApi.getSelectedRows()`), otherwise focused cell
  - Visible columns (filtered via `col.isVisible()` for copy)
- Paste mapping is based on:
  - Focused cell start position
  - Column order (`gridApi.getColumns()`), not a true cell-range selection model

This matters because implementing “true Excel” range selection in TanStack is a much bigger project than matching what the app does today.

## Recommendations (Practical Next Steps Before Implementing TanStack)

### 1) Add an explicit “Phase -1: Scope Lock”
Decide (per grid) what “parity” means:
- Keep current **row-based** copy/paste semantics, or build true range selection?
- Is “autoHeight + wrapText JSON editor” required, or can editing move to a modal?
- Do we need column pinning everywhere, or only where currently used?

### 2) Reduce surface area before swapping engines
Refactor the **8 direct `<AgGridReact>` instances** to go through a single wrapper (even if still AG Grid underneath). This gives you one migration seam and makes feature-flagging real.

### 3) Treat `SubjectHoursMatrix` as its own track
It’s dynamic-columns + custom writeback + paste. Budget it separately, and don’t assume it’s “similar” to the other grids.

### 4) Plan for CSS/accessibility migration explicitly
Create a checklist for removing/rewriting:
- `.ag-theme-quartz*` CSS rules in `frontend/src/index.css`
- `.ag-cell*` focus rules in `frontend/src/components/accessibility/FocusManager.tsx`
- `AccessibleGridWrapper`-style announcements for the new table

### 5) Timeline reality check
Given the above, **3–4 weeks is plausible only if you keep parity narrowly scoped** (no true range selection, minimal filtering UI, and you postpone the hardest grids).
If you want true spreadsheet parity (range selection + fill handle + robust editing + pinned+virtualization), plan for longer.

