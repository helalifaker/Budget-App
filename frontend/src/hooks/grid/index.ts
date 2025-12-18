/**
 * Grid-related hooks for Excel-like keyboard and clipboard behavior
 */
export { useCustomClipboardAdapter } from './useCustomClipboardAdapter'
export type { CellUpdate } from './useCustomClipboardAdapter'

export { useExcelKeyboardAdapter } from './useExcelKeyboardAdapter'
export type {
  ExcelKeyboardAdapterOptions,
  ClearedCell as AdapterClearedCell,
  FilledCell as AdapterFilledCell,
  SelectionInfo as AdapterSelectionInfo,
} from './useExcelKeyboardAdapter'

export { useGridExcelKeyboard } from './useGridExcelKeyboard'
export type {
  GridExcelKeyboardOptions,
  ClearedCell,
  FilledCell,
  SelectionInfo,
} from './useGridExcelKeyboard'
