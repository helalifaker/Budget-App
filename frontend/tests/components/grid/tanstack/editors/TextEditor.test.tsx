/**
 * TextEditor Tests
 *
 * Tests for the inline text editor component used in TanStack Table cells.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TextEditor } from '@/components/grid/tanstack/editors/TextEditor'

describe('TextEditor', () => {
  const defaultProps = {
    value: 'initial value',
    onCommit: vi.fn(),
    onCancel: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders an input element', () => {
      render(<TextEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      expect(input).toBeInTheDocument()
    })

    it('displays the initial value', () => {
      render(<TextEditor {...defaultProps} value="test value" />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('test value')
    })

    it('displays empty string for null value', () => {
      render(<TextEditor {...defaultProps} value={null} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('')
    })

    it('displays empty string for undefined value', () => {
      render(<TextEditor {...defaultProps} value={undefined} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('')
    })

    it('applies custom className', () => {
      render(<TextEditor {...defaultProps} className="custom-class" />)

      const input = screen.getByRole('textbox')
      expect(input.className).toContain('custom-class')
    })

    it('shows placeholder when provided', () => {
      render(<TextEditor {...defaultProps} value="" placeholder="Enter text" />)

      const input = screen.getByPlaceholderText('Enter text')
      expect(input).toBeInTheDocument()
    })
  })

  describe('Auto-focus', () => {
    it('auto-focuses on mount', async () => {
      render(<TextEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      await waitFor(() => {
        expect(document.activeElement).toBe(input)
      })
    })

    it('selects all text on mount when no initial key', async () => {
      render(<TextEditor {...defaultProps} value="select me" />)

      const input = screen.getByRole('textbox') as HTMLInputElement
      await waitFor(() => {
        expect(input.selectionStart).toBe(0)
        expect(input.selectionEnd).toBe(9) // length of "select me"
      })
    })
  })

  describe('Type-to-edit', () => {
    it('starts with initial key when provided', () => {
      render(<TextEditor {...defaultProps} initialKey="a" />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('a')
    })

    it('clears value when initial key is empty string (delete/backspace)', () => {
      render(<TextEditor {...defaultProps} initialKey="" />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('')
    })

    it('uses existing value when initial key is null', () => {
      render(<TextEditor {...defaultProps} value="existing" initialKey={null} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('existing')
    })
  })

  describe('Keyboard shortcuts', () => {
    it('commits value on Enter', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<TextEditor {...defaultProps} onCommit={onCommit} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, 'new value{Enter}')

      expect(onCommit).toHaveBeenCalledWith('new value')
    })

    it('cancels on Escape', async () => {
      const onCancel = vi.fn()
      const user = userEvent.setup()

      render(<TextEditor {...defaultProps} onCancel={onCancel} />)

      const input = screen.getByRole('textbox')
      await user.type(input, '{Escape}')

      expect(onCancel).toHaveBeenCalled()
    })

    it('navigates to next cell on Tab', async () => {
      const onCommit = vi.fn()
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(<TextEditor {...defaultProps} onCommit={onCommit} onNavigate={onNavigate} />)

      screen.getByRole('textbox') // Element exists; Tab navigates focus
      await user.tab()

      expect(onCommit).toHaveBeenCalled()
      expect(onNavigate).toHaveBeenCalledWith('next')
    })

    it('navigates to previous cell on Shift+Tab', async () => {
      const onCommit = vi.fn()
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(<TextEditor {...defaultProps} onCommit={onCommit} onNavigate={onNavigate} />)

      screen.getByRole('textbox') // Element exists; Shift+Tab navigates focus
      await user.keyboard('{Shift>}{Tab}{/Shift}')

      expect(onCommit).toHaveBeenCalled()
      expect(onNavigate).toHaveBeenCalledWith('prev')
    })

    it('navigates down on Enter', async () => {
      const onNavigateRow = vi.fn()
      const user = userEvent.setup()

      render(<TextEditor {...defaultProps} onNavigateRow={onNavigateRow} />)

      const input = screen.getByRole('textbox')
      await user.type(input, '{Enter}')

      expect(onNavigateRow).toHaveBeenCalledWith('down')
    })

    it('navigates up on Shift+Enter', async () => {
      const onNavigateRow = vi.fn()
      const user = userEvent.setup()

      render(<TextEditor {...defaultProps} onNavigateRow={onNavigateRow} />)

      screen.getByRole('textbox') // Element exists; Shift+Enter navigates row
      await user.keyboard('{Shift>}{Enter}{/Shift}')

      expect(onNavigateRow).toHaveBeenCalledWith('up')
    })
  })

  describe('Blur behavior', () => {
    it('commits value on blur', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(
        <div>
          <TextEditor {...defaultProps} onCommit={onCommit} />
          <button>Other</button>
        </div>
      )

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, 'blur value')
      await user.click(screen.getByRole('button'))

      expect(onCommit).toHaveBeenCalledWith('blur value')
    })
  })

  describe('Input constraints', () => {
    it('respects maxLength prop', async () => {
      const user = userEvent.setup()

      render(<TextEditor {...defaultProps} value="" maxLength={5} />)

      const input = screen.getByRole('textbox')
      await user.type(input, '12345678')

      expect(input).toHaveValue('12345')
    })
  })

  describe('Value transformation', () => {
    it('trims whitespace on commit', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<TextEditor {...defaultProps} onCommit={onCommit} value="  spaces  " />)

      const input = screen.getByRole('textbox')
      await user.type(input, '{Enter}')

      expect(onCommit).toHaveBeenCalledWith('spaces')
    })
  })

  describe('Styling', () => {
    it('has focus ring styling', () => {
      render(<TextEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      expect(input.className).toContain('ring')
    })

    it('uses default left text alignment (no explicit class needed)', () => {
      render(<TextEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      // TextEditor uses default left alignment (no explicit class)
      // NumberEditor uses text-right for numeric content
      expect(input.className).not.toContain('text-right')
    })
  })
})
