/**
 * EditableCell Tests
 *
 * Tests for the EditableCell component that wraps display values and inline editors.
 * This component handles edit triggers (double-click, F2, type-to-edit) and editor selection.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EditableCell } from '@/components/grid/tanstack/EditableCell'

describe('EditableCell', () => {
  const defaultProps = {
    rowId: 'row-1',
    columnId: 'col-1',
    value: 'test value',
    editorType: 'text' as const,
    isEditing: false,
    isFocused: false,
    onStartEdit: vi.fn(),
    onCommit: vi.fn(),
    onCancel: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Display Mode', () => {
    it('renders the value in display mode', () => {
      render(<EditableCell {...defaultProps} />)

      expect(screen.getByText('test value')).toBeInTheDocument()
    })

    it('renders dash for null value', () => {
      render(<EditableCell {...defaultProps} value={null} />)

      expect(screen.getByText('—')).toBeInTheDocument()
    })

    it('renders dash for undefined value', () => {
      render(<EditableCell {...defaultProps} value={undefined} />)

      expect(screen.getByText('—')).toBeInTheDocument()
    })

    it('renders checkmark for true boolean', () => {
      render(<EditableCell {...defaultProps} value={true} editorType="checkbox" />)

      expect(screen.getByText('✓')).toBeInTheDocument()
    })

    it('renders cross for false boolean', () => {
      render(<EditableCell {...defaultProps} value={false} editorType="checkbox" />)

      expect(screen.getByText('✗')).toBeInTheDocument()
    })

    it('renders number with tabular-nums class', () => {
      render(<EditableCell {...defaultProps} value={42} editorType="number" />)

      const numberDisplay = screen.getByText('42')
      expect(numberDisplay.className).toContain('tabular-nums')
    })

    it('uses custom displayRenderer when provided', () => {
      const customRenderer = (value: string) => (
        <span data-testid="custom">{value.toUpperCase()}</span>
      )

      render(<EditableCell {...defaultProps} value="hello" displayRenderer={customRenderer} />)

      expect(screen.getByTestId('custom')).toHaveTextContent('HELLO')
    })
  })

  describe('Data Attributes', () => {
    it('has correct data attributes', () => {
      render(<EditableCell {...defaultProps} />)

      const cell = screen.getByText('test value').closest('div[data-row-id]')
      expect(cell).toHaveAttribute('data-row-id', 'row-1')
      expect(cell).toHaveAttribute('data-column-id', 'col-1')
      expect(cell).toHaveAttribute('data-editable', 'true')
    })

    it('marks non-editable cells', () => {
      render(<EditableCell {...defaultProps} editable={false} />)

      const cell = screen.getByText('test value').closest('div[data-row-id]')
      expect(cell).toHaveAttribute('data-editable', 'false')
    })
  })

  describe('Focus State', () => {
    it('has tabIndex 0 when focused', () => {
      render(<EditableCell {...defaultProps} isFocused={true} />)

      const cell = screen.getByText('test value').closest('div[tabindex]')
      expect(cell).toHaveAttribute('tabindex', '0')
    })

    it('has tabIndex -1 when not focused', () => {
      render(<EditableCell {...defaultProps} isFocused={false} />)

      const cell = screen.getByText('test value').closest('div[tabindex]')
      expect(cell).toHaveAttribute('tabindex', '-1')
    })

    it('applies focus ring styling when focused', () => {
      render(<EditableCell {...defaultProps} isFocused={true} />)

      const cell = screen.getByText('test value').closest('div[tabindex]')
      expect(cell?.className).toContain('ring')
    })

    it('does not apply focus ring when editing', () => {
      render(<EditableCell {...defaultProps} isFocused={true} isEditing={true} />)

      // When editing, TextEditor should be shown instead
      const input = screen.getByRole('textbox')
      expect(input).toBeInTheDocument()
    })
  })

  describe('Edit Triggers', () => {
    describe('Double-click', () => {
      it('starts editing on double-click', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[data-row-id]')!
        await user.dblClick(cell)

        expect(onStartEdit).toHaveBeenCalledWith()
      })

      it('does not start editing when not editable', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} onStartEdit={onStartEdit} editable={false} />)

        const cell = screen.getByText('test value').closest('div[data-row-id]')!
        await user.dblClick(cell)

        expect(onStartEdit).not.toHaveBeenCalled()
      })

      it('does not start editing when already editing', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} onStartEdit={onStartEdit} isEditing={true} />)

        // When editing, the input is shown
        const input = screen.getByRole('textbox')
        await user.dblClick(input.closest('div[data-row-id]')!)

        expect(onStartEdit).not.toHaveBeenCalled()
      })
    })

    describe('F2 Key', () => {
      it('starts editing on F2 when focused', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} isFocused={true} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[tabindex]')!
        cell.focus()
        await user.keyboard('{F2}')

        expect(onStartEdit).toHaveBeenCalledWith()
      })

      it('does not start editing on F2 when already editing', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(
          <EditableCell
            {...defaultProps}
            isFocused={true}
            isEditing={true}
            onStartEdit={onStartEdit}
          />
        )

        await user.keyboard('{F2}')

        expect(onStartEdit).not.toHaveBeenCalled()
      })
    })

    describe('Enter Key', () => {
      it('starts editing on Enter when focused', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} isFocused={true} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[tabindex]')!
        cell.focus()
        await user.keyboard('{Enter}')

        expect(onStartEdit).toHaveBeenCalledWith()
      })
    })

    describe('Type-to-Edit', () => {
      it('starts editing with initial key on alphanumeric keypress', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} isFocused={true} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[tabindex]')!
        cell.focus()
        await user.keyboard('a')

        expect(onStartEdit).toHaveBeenCalledWith('a')
      })

      it('starts editing with number key', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} isFocused={true} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[tabindex]')!
        cell.focus()
        await user.keyboard('5')

        expect(onStartEdit).toHaveBeenCalledWith('5')
      })

      it('does not start editing on Ctrl+key combinations', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} isFocused={true} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[tabindex]')!
        cell.focus()
        await user.keyboard('{Control>}c{/Control}')

        expect(onStartEdit).not.toHaveBeenCalled()
      })

      it('does not start editing on Meta+key combinations', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} isFocused={true} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[tabindex]')!
        cell.focus()
        await user.keyboard('{Meta>}c{/Meta}')

        expect(onStartEdit).not.toHaveBeenCalled()
      })
    })

    describe('Backspace/Delete', () => {
      it('starts editing with empty string on Backspace', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} isFocused={true} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[tabindex]')!
        cell.focus()
        await user.keyboard('{Backspace}')

        expect(onStartEdit).toHaveBeenCalledWith('')
      })

      it('starts editing with empty string on Delete', async () => {
        const onStartEdit = vi.fn()
        const user = userEvent.setup()

        render(<EditableCell {...defaultProps} isFocused={true} onStartEdit={onStartEdit} />)

        const cell = screen.getByText('test value').closest('div[tabindex]')!
        cell.focus()
        await user.keyboard('{Delete}')

        expect(onStartEdit).toHaveBeenCalledWith('')
      })
    })
  })

  describe('Editor Rendering', () => {
    it('renders TextEditor for text type', () => {
      render(<EditableCell {...defaultProps} isEditing={true} editorType="text" />)

      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    it('renders NumberEditor for number type', () => {
      render(<EditableCell {...defaultProps} value={42} isEditing={true} editorType="number" />)

      expect(screen.getByRole('textbox')).toBeInTheDocument()
      expect(screen.getByRole('textbox')).toHaveAttribute('inputMode', 'decimal')
    })

    it('renders CheckboxEditor for checkbox type', () => {
      render(
        <EditableCell {...defaultProps} value={false} isEditing={true} editorType="checkbox" />
      )

      expect(screen.getByRole('checkbox')).toBeInTheDocument()
    })

    it('passes initial key to editor', () => {
      render(<EditableCell {...defaultProps} isEditing={true} editorType="text" initialKey="x" />)

      expect(screen.getByRole('textbox')).toHaveValue('x')
    })
  })

  describe('Editor Props', () => {
    it('passes min/max/step/precision to NumberEditor', () => {
      render(
        <EditableCell
          {...defaultProps}
          value={50}
          isEditing={true}
          editorType="number"
          min={0}
          max={100}
          step={5}
          precision={1}
        />
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('50.0') // precision=1
    })

    it('passes placeholder to TextEditor', () => {
      render(
        <EditableCell
          {...defaultProps}
          value=""
          isEditing={true}
          editorType="text"
          placeholder="Enter value"
        />
      )

      expect(screen.getByPlaceholderText('Enter value')).toBeInTheDocument()
    })

    it('passes maxLength to TextEditor', async () => {
      const user = userEvent.setup()

      render(
        <EditableCell {...defaultProps} value="" isEditing={true} editorType="text" maxLength={5} />
      )

      const input = screen.getByRole('textbox')
      await user.type(input, '12345678')

      expect(input).toHaveValue('12345')
    })
  })

  describe('Commit and Cancel', () => {
    it('calls onCommit when editor commits', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<EditableCell {...defaultProps} isEditing={true} onCommit={onCommit} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, 'new value{Enter}')

      expect(onCommit).toHaveBeenCalledWith('new value')
    })

    it('calls onCancel when editor cancels', async () => {
      const onCancel = vi.fn()
      const user = userEvent.setup()

      render(<EditableCell {...defaultProps} isEditing={true} onCancel={onCancel} />)

      await user.keyboard('{Escape}')

      expect(onCancel).toHaveBeenCalled()
    })
  })

  describe('Navigation Callbacks', () => {
    it('passes onNavigate to editor', async () => {
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(<EditableCell {...defaultProps} isEditing={true} onNavigate={onNavigate} />)

      await user.tab()

      expect(onNavigate).toHaveBeenCalledWith('next')
    })

    it('passes onNavigateRow to editor', async () => {
      const onNavigateRow = vi.fn()
      const user = userEvent.setup()

      render(<EditableCell {...defaultProps} isEditing={true} onNavigateRow={onNavigateRow} />)

      await user.keyboard('{Enter}')

      expect(onNavigateRow).toHaveBeenCalledWith('down')
    })
  })

  describe('Styling', () => {
    it('applies custom className', () => {
      render(<EditableCell {...defaultProps} className="custom-class" />)

      const cell = screen.getByText('test value').closest('div[data-row-id]')
      expect(cell?.className).toContain('custom-class')
    })

    it('has cursor-default for non-editable cells', () => {
      render(<EditableCell {...defaultProps} editable={false} />)

      const cell = screen.getByText('test value').closest('div[data-row-id]')
      expect(cell?.className).toContain('cursor-default')
    })

    it('has relative positioning for editor overlay', () => {
      render(<EditableCell {...defaultProps} isEditing={true} />)

      const cell = screen.getByRole('textbox').closest('div[data-row-id]')
      expect(cell?.className).toContain('relative')
    })
  })

  describe('Display truncation', () => {
    it('truncates long text in display mode', () => {
      render(<EditableCell {...defaultProps} value="a very long text value" />)

      const displayWrapper = screen.getByText('a very long text value').closest('div')
      expect(displayWrapper?.className).toContain('truncate')
    })
  })
})
