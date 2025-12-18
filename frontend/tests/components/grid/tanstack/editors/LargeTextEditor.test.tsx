/**
 * LargeTextEditor Tests
 *
 * Tests for the inline large text/JSON editor component used in TanStack Table cells.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LargeTextEditor } from '@/components/grid/tanstack/editors/LargeTextEditor'

describe('LargeTextEditor', () => {
  const defaultProps = {
    value: 'initial value',
    onCommit: vi.fn(),
    onCancel: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders a textarea element', () => {
      render(<LargeTextEditor {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toBeInTheDocument()
      expect(textarea.tagName).toBe('TEXTAREA')
    })

    it('displays the initial value', () => {
      render(<LargeTextEditor {...defaultProps} value="test value" />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveValue('test value')
    })

    it('displays empty string for null value', () => {
      render(<LargeTextEditor {...defaultProps} value={null} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveValue('')
    })

    it('displays empty string for undefined value', () => {
      render(<LargeTextEditor {...defaultProps} value={undefined} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveValue('')
    })

    it('applies custom className', () => {
      render(<LargeTextEditor {...defaultProps} className="custom-class" />)

      const textarea = screen.getByRole('textbox')
      expect(textarea.className).toContain('custom-class')
    })

    it('shows placeholder when provided', () => {
      render(<LargeTextEditor {...defaultProps} value="" placeholder="Enter JSON" />)

      const textarea = screen.getByPlaceholderText('Enter JSON')
      expect(textarea).toBeInTheDocument()
    })

    it('uses default placeholder when not provided', () => {
      render(<LargeTextEditor {...defaultProps} value="" />)

      const textarea = screen.getByPlaceholderText('Enter text...')
      expect(textarea).toBeInTheDocument()
    })

    it('respects rows prop', () => {
      render(<LargeTextEditor {...defaultProps} rows={10} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveAttribute('rows', '10')
    })

    it('uses default rows when not provided', () => {
      render(<LargeTextEditor {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveAttribute('rows', '6')
    })

    it('displays keyboard hint', () => {
      render(<LargeTextEditor {...defaultProps} />)

      expect(screen.getByText('Ctrl+Enter to save')).toBeInTheDocument()
    })
  })

  describe('Auto-focus', () => {
    it('auto-focuses on mount', async () => {
      render(<LargeTextEditor {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await waitFor(() => {
        expect(document.activeElement).toBe(textarea)
      })
    })

    it('selects all text on mount when no initial key', async () => {
      render(<LargeTextEditor {...defaultProps} value="select me" />)

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      await waitFor(() => {
        expect(textarea.selectionStart).toBe(0)
        expect(textarea.selectionEnd).toBe(9) // length of "select me"
      })
    })
  })

  describe('Type-to-edit', () => {
    it('starts with initial key when provided', () => {
      render(<LargeTextEditor {...defaultProps} initialKey="a" />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveValue('a')
    })

    it('clears value when initial key is empty string (delete/backspace)', () => {
      render(<LargeTextEditor {...defaultProps} initialKey="" />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveValue('')
    })

    it('uses existing value when initial key is null', () => {
      render(<LargeTextEditor {...defaultProps} value="existing" initialKey={null} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveValue('existing')
    })
  })

  describe('Keyboard shortcuts', () => {
    it('commits value on Ctrl+Enter', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onCommit={onCommit} />)

      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'new value')
      await user.keyboard('{Control>}{Enter}{/Control}')

      expect(onCommit).toHaveBeenCalledWith('new value')
    })

    it('commits value on Cmd+Enter (Mac)', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onCommit={onCommit} />)

      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'mac value')
      await user.keyboard('{Meta>}{Enter}{/Meta}')

      expect(onCommit).toHaveBeenCalledWith('mac value')
    })

    it('allows plain Enter to create newlines (not commit)', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onCommit={onCommit} />)

      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'line1{Enter}line2')

      // Enter should create a newline, not commit
      expect(onCommit).not.toHaveBeenCalled()
      expect(textarea).toHaveValue('line1\nline2')
    })

    it('cancels on Escape', async () => {
      const onCancel = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onCancel={onCancel} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, '{Escape}')

      expect(onCancel).toHaveBeenCalled()
    })

    it('navigates to next cell on Tab', async () => {
      const onCommit = vi.fn()
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onCommit={onCommit} onNavigate={onNavigate} />)

      screen.getByRole('textbox') // Element exists; Tab navigates focus
      await user.tab()

      expect(onCommit).toHaveBeenCalled()
      expect(onNavigate).toHaveBeenCalledWith('next')
    })

    it('navigates to previous cell on Shift+Tab', async () => {
      const onCommit = vi.fn()
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onCommit={onCommit} onNavigate={onNavigate} />)

      screen.getByRole('textbox') // Element exists; Shift+Tab navigates focus
      await user.keyboard('{Shift>}{Tab}{/Shift}')

      expect(onCommit).toHaveBeenCalled()
      expect(onNavigate).toHaveBeenCalledWith('prev')
    })

    it('navigates down on Ctrl+Enter', async () => {
      const onNavigateRow = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onNavigateRow={onNavigateRow} />)

      screen.getByRole('textbox') // Element exists; Ctrl+Enter navigates row
      await user.keyboard('{Control>}{Enter}{/Control}')

      expect(onNavigateRow).toHaveBeenCalledWith('down')
    })

    it('navigates up on Ctrl+Shift+Enter', async () => {
      const onNavigateRow = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onNavigateRow={onNavigateRow} />)

      screen.getByRole('textbox') // Element exists; Ctrl+Shift+Enter navigates row
      await user.keyboard('{Control>}{Shift>}{Enter}{/Shift}{/Control}')

      expect(onNavigateRow).toHaveBeenCalledWith('up')
    })
  })

  describe('Blur behavior', () => {
    it('commits value on blur', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(
        <div>
          <LargeTextEditor {...defaultProps} onCommit={onCommit} />
          <button>Other</button>
        </div>
      )

      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'blur value')
      await user.click(screen.getByRole('button'))

      expect(onCommit).toHaveBeenCalledWith('blur value')
    })
  })

  describe('Input constraints', () => {
    it('respects maxLength prop', async () => {
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} value="" maxLength={10} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, '12345678901234567890')

      expect(textarea).toHaveValue('1234567890')
    })
  })

  describe('Value transformation', () => {
    it('trims whitespace on commit', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} onCommit={onCommit} value="  spaces  " />)

      screen.getByRole('textbox') // Element exists; Ctrl+Enter commits trimmed value
      await user.keyboard('{Control>}{Enter}{/Control}')

      expect(onCommit).toHaveBeenCalledWith('spaces')
    })
  })

  describe('JSON validation', () => {
    it('does not show error for valid JSON when validateJson is enabled', async () => {
      render(<LargeTextEditor {...defaultProps} value="" validateJson={true} />)

      const textarea = screen.getByRole('textbox')
      // Use fireEvent.change for JSON strings with curly braces (userEvent interprets {} as special keys)
      fireEvent.change(textarea, { target: { value: '{"key": "value"}' } })

      // Should not show any error message
      await waitFor(() => {
        expect(screen.queryByText(/invalid/i)).not.toBeInTheDocument()
      })
    })

    it('shows error for invalid JSON when validateJson is enabled', async () => {
      render(<LargeTextEditor {...defaultProps} value="" validateJson={true} />)

      const textarea = screen.getByRole('textbox')
      // Use fireEvent.change for JSON strings with curly braces
      fireEvent.change(textarea, { target: { value: '{invalid json}' } })

      // Should show an error message
      await waitFor(() => {
        // The error message should be shown (contains some error text)
        const errorElement = document.querySelector('.text-terracotta-600')
        expect(errorElement).toBeInTheDocument()
      })
    })

    it('blocks commit when JSON is invalid', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} value="" validateJson={true} onCommit={onCommit} />)

      const textarea = screen.getByRole('textbox')
      // Use fireEvent.change for JSON strings with curly braces
      fireEvent.change(textarea, { target: { value: '{invalid}' } })

      // Wait for validation to run
      await waitFor(() => {
        const errorElement = document.querySelector('.text-terracotta-600')
        expect(errorElement).toBeInTheDocument()
      })

      // Try to commit with Ctrl+Enter
      await user.keyboard('{Control>}{Enter}{/Control}')

      // Should NOT commit because JSON is invalid
      expect(onCommit).not.toHaveBeenCalled()
    })

    it('allows commit when JSON is valid', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} value="" validateJson={true} onCommit={onCommit} />)

      const textarea = screen.getByRole('textbox')
      // Use fireEvent.change for JSON strings with curly braces
      fireEvent.change(textarea, { target: { value: '{"valid": true}' } })

      // Commit with Ctrl+Enter
      await user.keyboard('{Control>}{Enter}{/Control}')

      // Should commit because JSON is valid
      expect(onCommit).toHaveBeenCalledWith('{"valid": true}')
    })

    it('does not validate JSON when validateJson is false', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(
        <LargeTextEditor {...defaultProps} value="" validateJson={false} onCommit={onCommit} />
      )

      const textarea = screen.getByRole('textbox')
      // Use fireEvent.change for JSON strings with curly braces
      fireEvent.change(textarea, { target: { value: '{not valid json}' } })

      // Commit with Ctrl+Enter
      await user.keyboard('{Control>}{Enter}{/Control}')

      // Should commit because validation is disabled
      expect(onCommit).toHaveBeenCalledWith('{not valid json}')
    })

    it('validates empty string as valid JSON', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} value="" validateJson={true} onCommit={onCommit} />)

      // Commit empty value with Ctrl+Enter
      await user.keyboard('{Control>}{Enter}{/Control}')

      // Empty string should be allowed (commits as empty)
      expect(onCommit).toHaveBeenCalledWith('')
    })
  })

  describe('Required field', () => {
    it('cancels instead of committing when required and empty', async () => {
      const onCommit = vi.fn()
      const onCancel = vi.fn()
      const user = userEvent.setup()

      render(
        <LargeTextEditor
          {...defaultProps}
          value=""
          required={true}
          onCommit={onCommit}
          onCancel={onCancel}
        />
      )

      // Try to commit empty value
      await user.keyboard('{Control>}{Enter}{/Control}')

      expect(onCommit).not.toHaveBeenCalled()
      expect(onCancel).toHaveBeenCalled()
    })

    it('commits when required and has value', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(
        <LargeTextEditor {...defaultProps} value="has value" required={true} onCommit={onCommit} />
      )

      await user.keyboard('{Control>}{Enter}{/Control}')

      expect(onCommit).toHaveBeenCalledWith('has value')
    })
  })

  describe('Styling', () => {
    it('uses monospace font', () => {
      render(<LargeTextEditor {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea.className).toContain('font-mono')
    })

    it('has focus ring styling', () => {
      render(<LargeTextEditor {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea.className).toContain('ring')
    })

    it('has minimum width for popup display', () => {
      render(<LargeTextEditor {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea.className).toContain('min-w-')
    })

    it('has error styling when JSON is invalid', async () => {
      render(<LargeTextEditor {...defaultProps} value="" validateJson={true} />)

      const textarea = screen.getByRole('textbox')
      // Use fireEvent.change for JSON strings with curly braces
      fireEvent.change(textarea, { target: { value: '{invalid}' } })

      await waitFor(() => {
        // The textarea should have error styling
        expect(textarea.className).toContain('terracotta')
      })
    })
  })

  describe('Multiline support', () => {
    it('preserves newlines in value', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<LargeTextEditor {...defaultProps} value="" onCommit={onCommit} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'line1{Enter}line2{Enter}line3')
      await user.keyboard('{Control>}{Enter}{/Control}')

      expect(onCommit).toHaveBeenCalledWith('line1\nline2\nline3')
    })

    it('displays existing multiline content correctly', () => {
      render(<LargeTextEditor {...defaultProps} value={'line1\nline2\nline3'} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveValue('line1\nline2\nline3')
    })
  })
})
