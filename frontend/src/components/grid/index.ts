/**
 * Grid Components - Excel-like Data Tables
 *
 * This module provides premium AG Grid wrappers with Excel-like functionality:
 * - Copy/paste support compatible with Excel
 * - Keyboard navigation (Tab, Enter, Arrow keys)
 * - Selection statistics (Sum, Average, Count)
 * - Undo/redo support
 * - Accessibility features
 */

// Main Excel-like DataTable
export { ExcelDataTable, type ExcelDataTableProps } from './ExcelDataTable'

// Status bar showing selection stats
export { ExcelStatusBar } from './ExcelStatusBar'

// Cell renderers
export { AccountCodeRenderer } from './AccountCodeRenderer'
export { CurrencyRenderer } from './CurrencyRenderer'
export { StatusBadgeRenderer } from './StatusBadgeRenderer'

// Accessibility wrapper
export { AccessibleGridWrapper, type AccessibleGridWrapperRef } from './AccessibleGridWrapper'
