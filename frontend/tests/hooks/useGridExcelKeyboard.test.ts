/**
 * useGridExcelKeyboard Hook Tests
 *
 * Tests for the grid-agnostic Excel-like keyboard shortcuts hook.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useGridExcelKeyboard } from '@/hooks/grid/useGridExcelKeyboard'
import type { GridAdapter, CellId, RowNode, FocusedCell } from '@/lib/grid/GridAdapter'

// ============================================================================
// Mock GridAdapter
// ============================================================================

interface TestData extends Record<string, unknown> {
  id: string
  name: string
  value: number
}

function createMockAdapter(overrides: Partial<GridAdapter<TestData>> = {}): GridAdapter<TestData> {
  const defaultSelectedRowIds: string[] = []
  const defaultFocusedCell: CellId | null = null

  const mockRows: TestData[] = [
    { id: '1', name: 'Row 1', value: 100 },
    { id: '2', name: 'Row 2', value: 200 },
    { id: '3', name: 'Row 3', value: 300 },
  ]

  return {
    // Selection
    getSelectedRows: vi.fn(() => mockRows.filter((r) => defaultSelectedRowIds.includes(r.id))),
    getSelectedRowIds: vi.fn(() => defaultSelectedRowIds),
    getSelectedNodes: vi.fn(() =>
      mockRows
        .filter((r) => defaultSelectedRowIds.includes(r.id))
        .map((data, index) => ({ id: data.id, data, rowIndex: index }))
    ),
    selectRows: vi.fn(),
    selectAll: vi.fn(),
    deselectAll: vi.fn(),

    // Focus
    getFocusedCell: vi.fn((): FocusedCell | null => {
      if (!defaultFocusedCell) return null
      const rowIndex = mockRows.findIndex((r) => r.id === defaultFocusedCell.rowId)
      return {
        cellId: defaultFocusedCell,
        rowIndex,
        columnId: defaultFocusedCell.columnId,
      }
    }),
    setFocusedCell: vi.fn(),
    setFocusedCellByIndex: vi.fn(),

    // ID/Index conversion
    getRowIndexById: vi.fn((rowId: string) => {
      const index = mockRows.findIndex((r) => r.id === rowId)
      return index === -1 ? null : index
    }),
    getRowIdByIndex: vi.fn((index: number) => mockRows[index]?.id ?? null),

    // Data Access
    getVisibleColumns: vi.fn(() => [
      { id: 'id', editable: false, visible: true },
      { id: 'name', editable: true, visible: true },
      { id: 'value', editable: true, visible: true },
    ]),
    getAllColumns: vi.fn(() => [
      { id: 'id', editable: false, visible: true },
      { id: 'name', editable: true, visible: true },
      { id: 'value', editable: true, visible: true },
    ]),
    getRowById: vi.fn((rowId: string): RowNode<TestData> | null => {
      const row = mockRows.find((r) => r.id === rowId)
      if (!row) return null
      return { id: row.id, data: row, rowIndex: mockRows.indexOf(row) }
    }),
    getRowByIndex: vi.fn((index: number): RowNode<TestData> | null => {
      const row = mockRows[index]
      if (!row) return null
      return { id: row.id, data: row, rowIndex: index }
    }),
    getDisplayedRowCount: vi.fn(() => mockRows.length),
    getVisibleRowIds: vi.fn(() => mockRows.map((r) => r.id)),

    // Cell Values
    getCellValue: vi.fn((cellId: CellId) => {
      const row = mockRows.find((r) => r.id === cellId.rowId)
      return row ? row[cellId.columnId as keyof TestData] : undefined
    }),
    updateCellValue: vi.fn(),

    // Editing
    isEditing: vi.fn(() => false),
    getEditingCell: vi.fn(() => null),
    startEditing: vi.fn(),
    startEditingByIndex: vi.fn(),
    stopEditing: vi.fn(),

    // Editability
    isCellEditable: vi.fn((cellId: CellId) => cellId.columnId !== 'id'),

    // Scrolling
    scrollToRow: vi.fn(),
    scrollToColumn: vi.fn(),
    scrollToCell: vi.fn(),

    // Event subscriptions
    onSelectionChange: vi.fn(() => vi.fn()),
    onFocusChange: vi.fn(() => vi.fn()),
    onCellValueChange: vi.fn(() => vi.fn()),

    ...overrides,
  }
}

// ============================================================================
// Tests
// ============================================================================

describe('useGridExcelKeyboard', () => {
  let containerRef: React.RefObject<HTMLDivElement>
  let container: HTMLDivElement

  beforeEach(() => {
    container = document.createElement('div')
    container.tabIndex = 0
    document.body.appendChild(container)
    containerRef = { current: container }

    // Mock clipboard API
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockResolvedValue(undefined),
        readText: vi.fn().mockResolvedValue(''),
      },
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    document.body.removeChild(container)
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('returns initial selection info with no selection', () => {
      const adapter = createMockAdapter()

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      expect(result.current.selectionInfo).toEqual({
        cellCount: 0,
        rowCount: 0,
        sum: null,
        average: null,
        min: null,
        max: null,
        numericCount: 0,
      })
    })

    it('works with null adapter', () => {
      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter: null,
          containerRef,
        })
      )

      expect(result.current.selectionInfo.cellCount).toBe(0)
    })
  })

  describe('Copy to Clipboard (Ctrl+C)', () => {
    it('copies focused cell to clipboard', async () => {
      const mockFocusedCell: CellId = { rowId: '1', columnId: 'name' }
      const adapter = createMockAdapter({
        getFocusedCell: vi.fn(() => ({
          cellId: mockFocusedCell,
          rowIndex: 0,
          columnId: 'name',
        })),
        getCellValue: vi.fn(() => 'Row 1'),
      })

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      await act(async () => {
        await result.current.copyToClipboard()
      })

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Row 1')
    })

    it('copies selected rows as tab-separated values', async () => {
      const adapter = createMockAdapter({
        getSelectedNodes: vi.fn(() => [
          { id: '1', data: { id: '1', name: 'Row 1', value: 100 }, rowIndex: 0 },
          { id: '2', data: { id: '2', name: 'Row 2', value: 200 }, rowIndex: 1 },
        ]),
        getCellValue: vi.fn((cellId: CellId) => {
          const data: Record<string, Record<string, unknown>> = {
            '1': { id: '1', name: 'Row 1', value: 100 },
            '2': { id: '2', name: 'Row 2', value: 200 },
          }
          return data[cellId.rowId]?.[cellId.columnId]
        }),
      })

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      await act(async () => {
        await result.current.copyToClipboard()
      })

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('1\tRow 1\t100\n2\tRow 2\t200')
    })

    it('responds to Ctrl+C keydown event', async () => {
      const adapter = createMockAdapter({
        getFocusedCell: vi.fn(() => ({
          cellId: { rowId: '1', columnId: 'name' },
          rowIndex: 0,
          columnId: 'name',
        })),
        getCellValue: vi.fn(() => 'Test Value'),
      })

      renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      // Dispatch Ctrl+C
      await act(async () => {
        const event = new KeyboardEvent('keydown', {
          key: 'c',
          ctrlKey: true,
          bubbles: true,
        })
        container.dispatchEvent(event)
      })

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalled()
      })
    })
  })

  describe('Paste from Clipboard (Ctrl+V)', () => {
    it('calls onPaste with parsed clipboard data', async () => {
      const onPaste = vi.fn().mockResolvedValue(undefined)
      const adapter = createMockAdapter({
        getFocusedCell: vi.fn(() => ({
          cellId: { rowId: '1', columnId: 'name' },
          rowIndex: 0,
          columnId: 'name',
        })),
      })

      // Mock clipboard with tab-separated data
      vi.spyOn(navigator.clipboard, 'readText').mockResolvedValue('New Value\t150')

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
          onPaste,
        })
      )

      await act(async () => {
        await result.current.pasteFromClipboard()
      })

      expect(onPaste).toHaveBeenCalled()
      const updates = onPaste.mock.calls[0][0]
      expect(updates.length).toBeGreaterThan(0)
      expect(updates[0].field).toBe('name')
      expect(updates[0].newValue).toBe('New Value')
    })

    it('skips non-editable columns during paste', async () => {
      const onPaste = vi.fn().mockResolvedValue(undefined)
      const adapter = createMockAdapter({
        getFocusedCell: vi.fn(() => ({
          cellId: { rowId: '1', columnId: 'id' }, // Start at non-editable column
          rowIndex: 0,
          columnId: 'id',
        })),
        isCellEditable: vi.fn((cellId: CellId) => cellId.columnId !== 'id'),
      })

      vi.spyOn(navigator.clipboard, 'readText').mockResolvedValue('ID1\tName1\t100')

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
          onPaste,
        })
      )

      await act(async () => {
        await result.current.pasteFromClipboard()
      })

      expect(onPaste).toHaveBeenCalled()
      const updates = onPaste.mock.calls[0][0]
      // The 'id' column should be skipped
      const idUpdate = updates.find((u: { field: string }) => u.field === 'id')
      expect(idUpdate).toBeUndefined()
    })

    it('does not paste when editing is disabled', async () => {
      const onPaste = vi.fn()
      const adapter = createMockAdapter()

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
          enableEditing: false,
          onPaste,
        })
      )

      await act(async () => {
        await result.current.pasteFromClipboard()
      })

      expect(onPaste).not.toHaveBeenCalled()
    })
  })

  describe('Select All (Ctrl+A)', () => {
    it('calls adapter.selectAll', () => {
      const adapter = createMockAdapter()

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      act(() => {
        result.current.selectAll()
      })

      expect(adapter.selectAll).toHaveBeenCalled()
    })

    it('responds to Ctrl+A keydown event', () => {
      const adapter = createMockAdapter()

      renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      act(() => {
        const event = new KeyboardEvent('keydown', {
          key: 'a',
          ctrlKey: true,
          bubbles: true,
        })
        container.dispatchEvent(event)
      })

      expect(adapter.selectAll).toHaveBeenCalled()
    })
  })

  describe('Fill Down (Ctrl+D)', () => {
    it('fills selected rows with first row values', () => {
      const onCellsFilled = vi.fn()
      const cellValues: Record<string, Record<string, unknown>> = {
        '1': { id: '1', name: 'Source', value: 999 },
        '2': { id: '2', name: 'Target 1', value: 100 },
        '3': { id: '3', name: 'Target 2', value: 200 },
      }

      const adapter = createMockAdapter({
        getSelectedNodes: vi.fn(() => [
          { id: '1', data: cellValues['1'] as TestData, rowIndex: 0 },
          { id: '2', data: cellValues['2'] as TestData, rowIndex: 1 },
          { id: '3', data: cellValues['3'] as TestData, rowIndex: 2 },
        ]),
        getCellValue: vi.fn((cellId: CellId) => cellValues[cellId.rowId]?.[cellId.columnId]),
      })

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
          onCellsFilled,
        })
      )

      act(() => {
        result.current.fillDown()
      })

      // Should update cells in rows 2 and 3
      expect(adapter.updateCellValue).toHaveBeenCalled()
      expect(onCellsFilled).toHaveBeenCalled()
    })

    it('does not fill with less than 2 selected rows', () => {
      const adapter = createMockAdapter({
        getSelectedNodes: vi.fn(() => [
          { id: '1', data: { id: '1', name: 'Row 1', value: 100 }, rowIndex: 0 },
        ]),
      })

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      act(() => {
        result.current.fillDown()
      })

      expect(adapter.updateCellValue).not.toHaveBeenCalled()
    })
  })

  describe('Clear Cells (Delete/Backspace)', () => {
    it('clears focused cell on Delete', () => {
      const onCellsCleared = vi.fn()
      const adapter = createMockAdapter({
        getFocusedCell: vi.fn(() => ({
          cellId: { rowId: '1', columnId: 'name' },
          rowIndex: 0,
          columnId: 'name',
        })),
        getSelectedNodes: vi.fn(() => []), // No selection
        isCellEditable: vi.fn(() => true),
        getCellValue: vi.fn(() => 'Original Value'),
      })

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
          onCellsCleared,
        })
      )

      act(() => {
        result.current.clearSelectedCells()
      })

      expect(adapter.updateCellValue).toHaveBeenCalledWith({ rowId: '1', columnId: 'name' }, null)
      expect(onCellsCleared).toHaveBeenCalled()
    })

    it('clears all editable cells in selected rows', () => {
      const onCellsCleared = vi.fn()
      const adapter = createMockAdapter({
        getSelectedNodes: vi.fn(() => [
          { id: '1', data: { id: '1', name: 'Row 1', value: 100 }, rowIndex: 0 },
        ]),
        isCellEditable: vi.fn((cellId: CellId) => cellId.columnId !== 'id'),
      })

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
          onCellsCleared,
        })
      )

      act(() => {
        result.current.clearSelectedCells()
      })

      // Should clear 'name' and 'value' columns (not 'id')
      expect(adapter.updateCellValue).toHaveBeenCalledTimes(2)
      expect(onCellsCleared).toHaveBeenCalled()
    })
  })

  describe('Selection Statistics', () => {
    it('calculates statistics for numeric selection', () => {
      const adapter = createMockAdapter({
        getSelectedNodes: vi.fn(() => [
          { id: '1', data: { id: '1', name: 'Row 1', value: 100 }, rowIndex: 0 },
          { id: '2', data: { id: '2', name: 'Row 2', value: 200 }, rowIndex: 1 },
          { id: '3', data: { id: '3', name: 'Row 3', value: 300 }, rowIndex: 2 },
        ]),
        getCellValue: vi.fn((cellId: CellId) => {
          const data: Record<string, Record<string, unknown>> = {
            '1': { id: '1', name: 'Row 1', value: 100 },
            '2': { id: '2', name: 'Row 2', value: 200 },
            '3': { id: '3', name: 'Row 3', value: 300 },
          }
          return data[cellId.rowId]?.[cellId.columnId]
        }),
      })

      const { result } = renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      act(() => {
        result.current.updateSelectionInfo()
      })

      // Check statistics (3 rows × 3 columns = 9 cells)
      // Numeric values: 100, 200, 300 (from 'value' column)
      // Plus '1', '2', '3' from 'id' column are numeric
      expect(result.current.selectionInfo.rowCount).toBe(3)
      expect(result.current.selectionInfo.cellCount).toBe(9)
      expect(result.current.selectionInfo.numericCount).toBeGreaterThan(0)
      expect(result.current.selectionInfo.sum).not.toBeNull()
    })
  })

  describe('Escape key', () => {
    it('deselects all on Escape', () => {
      const adapter = createMockAdapter()

      renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      act(() => {
        const event = new KeyboardEvent('keydown', {
          key: 'Escape',
          bubbles: true,
        })
        container.dispatchEvent(event)
      })

      expect(adapter.deselectAll).toHaveBeenCalled()
    })

    it('stops editing on Escape when editing', () => {
      const adapter = createMockAdapter({
        isEditing: vi.fn(() => true),
      })

      renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      act(() => {
        const event = new KeyboardEvent('keydown', {
          key: 'Escape',
          bubbles: true,
        })
        container.dispatchEvent(event)
      })

      expect(adapter.stopEditing).toHaveBeenCalledWith(true) // true = cancel
    })
  })

  describe('Keyboard events when editing', () => {
    it('does not trigger shortcuts when editing (except Escape)', () => {
      const adapter = createMockAdapter({
        isEditing: vi.fn(() => true),
      })

      renderHook(() =>
        useGridExcelKeyboard({
          adapter,
          containerRef,
        })
      )

      // Try Ctrl+C while editing
      act(() => {
        const event = new KeyboardEvent('keydown', {
          key: 'c',
          ctrlKey: true,
          bubbles: true,
        })
        container.dispatchEvent(event)
      })

      // Copy should NOT be triggered
      expect(navigator.clipboard.writeText).not.toHaveBeenCalled()
    })
  })
})
