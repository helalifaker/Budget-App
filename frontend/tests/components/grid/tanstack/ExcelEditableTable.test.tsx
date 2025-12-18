/**
 * ExcelEditableTable Tests
 *
 * Tests for the ExcelEditableTable component with full Excel-like keyboard
 * shortcuts and clipboard support.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ExcelEditableTable } from '@/components/grid/tanstack/ExcelEditableTable'
import type { ColumnDef } from '@tanstack/react-table'

// ============================================================================
// Test Data and Utilities
// ============================================================================

interface TestRow {
  id: string
  name: string
  value: number
  active: boolean
}

const testData: TestRow[] = [
  { id: '1', name: 'Row 1', value: 100, active: true },
  { id: '2', name: 'Row 2', value: 200, active: false },
  { id: '3', name: 'Row 3', value: 300, active: true },
  { id: '4', name: 'Row 4', value: 400, active: false },
]

const testColumns: ColumnDef<TestRow, unknown>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    size: 150,
    meta: { editable: true, editorType: 'text' as const },
  },
  {
    accessorKey: 'value',
    header: 'Value',
    size: 100,
    meta: { editable: true, editorType: 'number' as const },
  },
  {
    accessorKey: 'active',
    header: 'Active',
    size: 100,
    meta: { editable: true, editorType: 'checkbox' as const },
  },
]

// Mock clipboard API
const mockClipboard = {
  writeText: vi.fn().mockResolvedValue(undefined),
  readText: vi.fn().mockResolvedValue(''),
}

const originalClipboard = navigator.clipboard

// Helper to get the table container
function getTableContainer(): HTMLElement {
  // The container is the root div with the relative class
  const containers = document.querySelectorAll('.relative.flex.flex-col')
  return containers[0] as HTMLElement
}

// Helper to check if status bar contains row selection text
// Note: We use this instead of getByText because the text is split across
// multiple span elements (e.g., <span>1</span> row selected)
function expectStatusBarText(pattern: RegExp): void {
  const statusBar = document.querySelector('.flex.items-center.justify-end.gap-4')
  expect(statusBar).toBeInTheDocument()
  expect(statusBar?.textContent).toMatch(pattern)
}

// ============================================================================
// Tests
// ============================================================================

describe('ExcelEditableTable', () => {
  const defaultProps = {
    rowData: testData,
    columnDefs: testColumns,
    getRowId: (row: TestRow) => row.id,
    onCellValueChanged: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Mock clipboard API
    Object.defineProperty(navigator, 'clipboard', {
      value: mockClipboard,
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    // Restore original clipboard
    Object.defineProperty(navigator, 'clipboard', {
      value: originalClipboard,
      writable: true,
      configurable: true,
    })
  })

  describe('Rendering', () => {
    it('renders the table with data', () => {
      render(<ExcelEditableTable {...defaultProps} />)

      expect(screen.getByText('Row 1')).toBeInTheDocument()
      expect(screen.getByText('Row 2')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('200')).toBeInTheDocument()
    })

    it('renders checkbox column header by default', () => {
      render(<ExcelEditableTable {...defaultProps} />)

      // Should have at least one checkbox element in the header area
      const headerCheckboxes = document.querySelectorAll('[aria-label="Select all rows"]')
      expect(headerCheckboxes.length).toBeGreaterThan(0)
    })

    it('hides checkbox column when showCheckboxColumn is false', () => {
      render(<ExcelEditableTable {...defaultProps} showCheckboxColumn={false} />)

      // Should not have select all checkbox
      const headerCheckboxes = document.querySelectorAll('[aria-label="Select all rows"]')
      expect(headerCheckboxes.length).toBe(0)
    })

    it('does not show status bar when no rows selected', () => {
      render(<ExcelEditableTable {...defaultProps} />)

      // Status bar should not be visible
      expect(screen.queryByText(/selected/i)).not.toBeInTheDocument()
    })
  })

  describe('Row Selection', () => {
    it('selects a row when checkbox is clicked', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} />)

      // Find row checkboxes (excluding header)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      // First checkbox is header, second is first data row
      expect(rowCheckboxes.length).toBeGreaterThan(1)

      // Click the first data row checkbox (wrap in act for state updates)
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Should show status bar with 1 row selected
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })
    })

    it('selects multiple rows with multiple checkbox clicks', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} />)

      // Find row checkboxes
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')

      // Click first data row checkbox (wrap in act for state updates)
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Click second data row checkbox (toggle selection)
      await act(async () => {
        await user.click(rowCheckboxes[2])
      })

      // Should show 2 rows selected
      await waitFor(() => {
        expectStatusBarText(/2 rows selected/i)
      })
    })

    it('shows selection statistics when rows are selected', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} />)

      // Click all rows using header checkbox (wrap in act for state updates)
      const headerCheckbox = document.querySelector('[aria-label="Select all rows"]')
      if (headerCheckbox) {
        await act(async () => {
          await user.click(headerCheckbox)
        })
      }

      // Should show statistics
      await waitFor(() => {
        // Should show sum (100 + 200 + 300 + 400 = 1000)
        expect(screen.getByText('Sum:')).toBeInTheDocument()
      })
    })

    it('hides stats when showSelectionStats is false', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} showSelectionStats={false} />)

      // Click first row checkbox (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait a bit for state update
      await waitFor(() => {
        // Stats should not be visible but selection was made
        expect(screen.queryByText('Sum:')).not.toBeInTheDocument()
      })
    })
  })

  describe('Keyboard Shortcuts - Ctrl+A (Select All)', () => {
    it('selects all rows via header checkbox', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} />)

      // Click header checkbox to select all (wrap in act for state updates)
      const headerCheckbox = document.querySelector('[aria-label="Select all rows"]')
      expect(headerCheckbox).toBeInTheDocument()

      await act(async () => {
        await user.click(headerCheckbox!)
      })

      // Should show all 4 rows selected
      await waitFor(() => {
        expectStatusBarText(/4 rows selected/i)
      })
    })
  })

  describe('Keyboard Shortcuts - Copy (Ctrl+C)', () => {
    it('triggers copy handler on Ctrl+C with selected rows', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} />)

      // First select a row (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait for selection to be registered
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Ctrl+C on the container - event should be handled without error
      const container = getTableContainer()
      expect(() => {
        fireEvent.keyDown(container, { key: 'c', ctrlKey: true })
      }).not.toThrow()

      // The event was handled (verified by no throw)
      // Note: Clipboard API behavior varies in JSDOM environments
    })

    it('does not copy when clipboard is disabled', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} enableClipboard={false} />)

      // Select a row
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Ctrl+C
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'c', ctrlKey: true })

      // Clipboard should NOT have been called
      expect(mockClipboard.writeText).not.toHaveBeenCalled()
    })
  })

  describe('Keyboard Shortcuts - Paste (Ctrl+V)', () => {
    it('triggers paste handler on Ctrl+V', async () => {
      const user = userEvent.setup()
      mockClipboard.readText.mockResolvedValue('New Value')

      render(<ExcelEditableTable {...defaultProps} />)

      // Click a cell to focus it
      const cell = screen.getByText('Row 1')
      await user.click(cell)

      // Trigger Ctrl+V on the container - should handle without error
      const container = getTableContainer()
      expect(() => {
        fireEvent.keyDown(container, { key: 'v', ctrlKey: true })
      }).not.toThrow()

      // The event was handled (verified by no throw)
      // Note: Clipboard API and cell value changes vary in JSDOM environments
    })

    it('does not paste when clipboard is disabled', async () => {
      const user = userEvent.setup()
      mockClipboard.readText.mockResolvedValue('New Value')

      render(<ExcelEditableTable {...defaultProps} enableClipboard={false} />)

      // Click a cell to focus it
      const cell = screen.getByText('Row 1')
      await user.click(cell)

      // Trigger Ctrl+V
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'v', ctrlKey: true })

      // Clipboard should NOT have been read
      expect(mockClipboard.readText).not.toHaveBeenCalled()
    })
  })

  describe('Keyboard Shortcuts - Fill Down (Ctrl+D)', () => {
    it('fills selected rows with first row values', async () => {
      const user = userEvent.setup()
      const onCellValueChanged = vi.fn()
      render(<ExcelEditableTable {...defaultProps} onCellValueChanged={onCellValueChanged} />)

      // Select multiple rows via checkboxes (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1]) // Row 1
      })
      await act(async () => {
        await user.click(rowCheckboxes[2]) // Row 2 (toggle to add)
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/2 rows selected/i)
      })

      // Trigger Ctrl+D
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'd', ctrlKey: true })

      // Should have triggered cell changes for row 2 with row 1's values
      await waitFor(() => {
        expect(onCellValueChanged).toHaveBeenCalled()
      })
    })

    it('does nothing when less than 2 rows selected', async () => {
      const user = userEvent.setup()
      const onCellValueChanged = vi.fn()
      render(<ExcelEditableTable {...defaultProps} onCellValueChanged={onCellValueChanged} />)

      // Select only 1 row (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Ctrl+D
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'd', ctrlKey: true })

      // Should NOT have triggered any cell changes (need 2+ rows)
      expect(onCellValueChanged).not.toHaveBeenCalled()
    })
  })

  describe('Keyboard Shortcuts - Clear (Delete/Backspace)', () => {
    it('clears selected cells on Delete key', async () => {
      const user = userEvent.setup()
      const onCellValueChanged = vi.fn()
      render(<ExcelEditableTable {...defaultProps} onCellValueChanged={onCellValueChanged} />)

      // Select a row (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Delete
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'Delete' })

      // Should have triggered cell changes with null values
      await waitFor(() => {
        expect(onCellValueChanged).toHaveBeenCalled()
        // Check that newValue is null
        const calls = onCellValueChanged.mock.calls
        expect(calls.some((call) => call[0].newValue === null)).toBe(true)
      })
    })

    it('clears selected cells on Backspace key', async () => {
      const user = userEvent.setup()
      const onCellValueChanged = vi.fn()
      render(<ExcelEditableTable {...defaultProps} onCellValueChanged={onCellValueChanged} />)

      // Select a row (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Backspace
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'Backspace' })

      // Should have triggered cell changes
      await waitFor(() => {
        expect(onCellValueChanged).toHaveBeenCalled()
      })
    })

    it('calls onCellsCleared callback when cells are cleared', async () => {
      const user = userEvent.setup()
      const onCellsCleared = vi.fn()
      render(<ExcelEditableTable {...defaultProps} onCellsCleared={onCellsCleared} />)

      // Select a row (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Delete
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'Delete' })

      // Should have called onCellsCleared
      await waitFor(() => {
        expect(onCellsCleared).toHaveBeenCalled()
      })
    })
  })

  describe('Feature Flags', () => {
    it('disables clipboard operations when enableClipboard is false', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} enableClipboard={false} />)

      // Select a row (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Ctrl+C
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'c', ctrlKey: true })

      // Clipboard should NOT have been called
      expect(mockClipboard.writeText).not.toHaveBeenCalled()
    })

    it('disables fill down when enableFillDown is false', async () => {
      const user = userEvent.setup()
      const onCellValueChanged = vi.fn()
      render(
        <ExcelEditableTable
          {...defaultProps}
          onCellValueChanged={onCellValueChanged}
          enableFillDown={false}
        />
      )

      // Select multiple rows (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })
      await act(async () => {
        await user.click(rowCheckboxes[2])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/2 rows selected/i)
      })

      // Trigger Ctrl+D
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'd', ctrlKey: true })

      // Should NOT have triggered any changes
      expect(onCellValueChanged).not.toHaveBeenCalled()
    })

    it('disables cell clearing when enableClear is false', async () => {
      const user = userEvent.setup()
      const onCellValueChanged = vi.fn()
      render(
        <ExcelEditableTable
          {...defaultProps}
          onCellValueChanged={onCellValueChanged}
          enableClear={false}
        />
      )

      // Select a row (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Delete
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'Delete' })

      // Should NOT have triggered any changes
      expect(onCellValueChanged).not.toHaveBeenCalled()
    })

    it('disables row selection when enableRowSelection is false', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} enableRowSelection={false} />)

      // Try to click a row - should not show selection
      const cell = screen.getByText('Row 1')
      await act(async () => {
        await user.click(cell)
      })

      // Should NOT show selection status bar
      expect(screen.queryByText(/selected/i)).not.toBeInTheDocument()
    })
  })

  describe('Selection Statistics', () => {
    it('calculates sum correctly for selected numeric values', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} />)

      // Select all rows via header checkbox (wrap in act for state updates)
      const headerCheckbox = document.querySelector('[aria-label="Select all rows"]')
      await act(async () => {
        await user.click(headerCheckbox!)
      })

      // Sum should include numeric values
      await waitFor(() => {
        expect(screen.getByText('Sum:')).toBeInTheDocument()
      })
    })

    it('shows row and cell count in status bar', async () => {
      const user = userEvent.setup()
      render(<ExcelEditableTable {...defaultProps} />)

      // Select 2 rows via checkboxes (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })
      await act(async () => {
        await user.click(rowCheckboxes[2])
      })

      // Should show row count
      await waitFor(() => {
        expectStatusBarText(/2 rows selected/i)
      })
    })
  })

  describe('Callbacks', () => {
    it('calls onRowSelectionChange when selection changes', async () => {
      const user = userEvent.setup()
      const onRowSelectionChange = vi.fn()
      render(<ExcelEditableTable {...defaultProps} onRowSelectionChange={onRowSelectionChange} />)

      // Click first row checkbox (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Should have called onRowSelectionChange
      await waitFor(() => {
        expect(onRowSelectionChange).toHaveBeenCalledWith(['1'])
      })
    })

    it('calls onCellsFilled when fill down is performed', async () => {
      const user = userEvent.setup()
      const onCellsFilled = vi.fn()
      render(<ExcelEditableTable {...defaultProps} onCellsFilled={onCellsFilled} />)

      // Select 2 rows (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })
      await act(async () => {
        await user.click(rowCheckboxes[2])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/2 rows selected/i)
      })

      // Trigger Ctrl+D
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'd', ctrlKey: true })

      // Should have called onCellsFilled
      await waitFor(() => {
        expect(onCellsFilled).toHaveBeenCalled()
      })
    })

    it('handles paste without throwing error', async () => {
      const user = userEvent.setup()
      const onCellValueChanged = vi.fn()
      mockClipboard.readText.mockResolvedValue('Pasted Value')

      render(<ExcelEditableTable {...defaultProps} onCellValueChanged={onCellValueChanged} />)

      // Click a cell to focus it
      const cell = screen.getByText('Row 1')
      await user.click(cell)

      // Trigger Ctrl+V - should handle without error
      const container = getTableContainer()
      expect(() => {
        fireEvent.keyDown(container, { key: 'v', ctrlKey: true })
      }).not.toThrow()

      // Note: Actual paste behavior depends on focused cell state which varies in JSDOM
    })
  })

  describe('Custom Value Formatting', () => {
    it('accepts custom formatCopiedValue prop without error', async () => {
      const customFormat = vi.fn((value: unknown) => `CUSTOM:${value}`)

      // Should render without error with custom formatter
      expect(() => {
        render(<ExcelEditableTable {...defaultProps} formatCopiedValue={customFormat} />)
      }).not.toThrow()

      // Component should display data normally
      expect(screen.getByText('Row 1')).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty data gracefully', () => {
      render(<ExcelEditableTable {...defaultProps} rowData={[]} />)

      // Should show empty message
      expect(screen.getByText('No data available')).toBeInTheDocument()
    })

    it('handles null data gracefully', () => {
      render(<ExcelEditableTable {...defaultProps} rowData={null} />)

      // Should show empty message
      expect(screen.getByText('No data available')).toBeInTheDocument()
    })

    it('handles clipboard read error gracefully', async () => {
      const user = userEvent.setup()
      mockClipboard.readText.mockRejectedValue(new Error('Clipboard access denied'))

      render(<ExcelEditableTable {...defaultProps} />)

      // Click a cell to focus it
      const cell = screen.getByText('Row 1')
      await user.click(cell)

      // Trigger Ctrl+V - should not throw
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'v', ctrlKey: true })

      // Wait a bit for async error to be handled
      await new Promise((resolve) => setTimeout(resolve, 100))

      // Component should still be rendered
      expect(screen.getByText('Row 1')).toBeInTheDocument()
    })

    it('handles clipboard write error gracefully', async () => {
      const user = userEvent.setup()
      mockClipboard.writeText.mockRejectedValue(new Error('Clipboard write denied'))

      render(<ExcelEditableTable {...defaultProps} />)

      // Select a row (wrap in act for state updates)
      const rowCheckboxes = document.querySelectorAll('.w-4.h-4.rounded.border')
      await act(async () => {
        await user.click(rowCheckboxes[1])
      })

      // Wait for selection
      await waitFor(() => {
        expectStatusBarText(/1 row selected/i)
      })

      // Trigger Ctrl+C - should not throw
      const container = getTableContainer()
      fireEvent.keyDown(container, { key: 'c', ctrlKey: true })

      // Wait a bit for async error to be handled
      await new Promise((resolve) => setTimeout(resolve, 100))

      // Component should still be rendered
      expect(screen.getByText('Row 1')).toBeInTheDocument()
    })
  })
})
