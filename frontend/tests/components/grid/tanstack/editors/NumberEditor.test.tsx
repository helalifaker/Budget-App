/**
 * NumberEditor Tests
 *
 * Tests for the inline number editor component used in TanStack Table cells.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NumberEditor } from '@/components/grid/tanstack/editors/NumberEditor'

describe('NumberEditor', () => {
  const defaultProps = {
    value: 100,
    onCommit: vi.fn(),
    onCancel: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders an input element', () => {
      render(<NumberEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      expect(input).toBeInTheDocument()
    })

    it('displays the initial value formatted with precision', () => {
      render(<NumberEditor {...defaultProps} value={100} precision={2} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('100.00')
    })

    it('displays empty string for null value', () => {
      render(<NumberEditor {...defaultProps} value={null} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('')
    })

    it('displays empty string for undefined value', () => {
      render(<NumberEditor {...defaultProps} value={undefined} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('')
    })

    it('has decimal input mode', () => {
      render(<NumberEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('inputMode', 'decimal')
    })

    it('has right-aligned text', () => {
      render(<NumberEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      expect(input.className).toContain('text-right')
    })

    it('has tabular-nums for consistent number display', () => {
      render(<NumberEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      expect(input.className).toContain('tabular-nums')
    })
  })

  describe('Auto-focus', () => {
    it('auto-focuses on mount', async () => {
      render(<NumberEditor {...defaultProps} />)

      const input = screen.getByRole('textbox')
      await waitFor(() => {
        expect(document.activeElement).toBe(input)
      })
    })

    it('selects all text on mount when no initial key', async () => {
      render(<NumberEditor {...defaultProps} value={123} precision={0} />)

      const input = screen.getByRole('textbox') as HTMLInputElement
      await waitFor(() => {
        expect(input.selectionStart).toBe(0)
        expect(input.selectionEnd).toBe(3) // length of "123"
      })
    })
  })

  describe('Type-to-edit', () => {
    it('starts with initial digit when provided', () => {
      render(<NumberEditor {...defaultProps} initialKey="5" />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('5')
    })

    it('starts with minus sign when provided', () => {
      render(<NumberEditor {...defaultProps} initialKey="-" />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('-')
    })

    it('starts with decimal point when provided', () => {
      render(<NumberEditor {...defaultProps} initialKey="." />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('.')
    })
  })

  describe('Value parsing and validation', () => {
    it('parses valid integer', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '42{Enter}')

      expect(onCommit).toHaveBeenCalledWith(42)
    })

    it('parses valid decimal', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} precision={2} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '3.14{Enter}')

      expect(onCommit).toHaveBeenCalledWith(3.14)
    })

    it('parses negative numbers', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '-50{Enter}')

      expect(onCommit).toHaveBeenCalledWith(-50)
    })

    it('rounds to precision', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} precision={1} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '3.456{Enter}')

      expect(onCommit).toHaveBeenCalledWith(3.5)
    })

    it('cancels on invalid input', async () => {
      const onCommit = vi.fn()
      const onCancel = vi.fn()
      const user = userEvent.setup()

      render(
        <NumberEditor
          {...defaultProps}
          value={100}
          onCommit={onCommit}
          onCancel={onCancel}
          allowNull={false}
        />
      )

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, 'abc{Enter}')

      expect(onCancel).toHaveBeenCalled()
      expect(onCommit).not.toHaveBeenCalled()
    })
  })

  describe('Min/Max constraints', () => {
    it('constrains value to min', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} min={0} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '-50{Enter}')

      expect(onCommit).toHaveBeenCalledWith(0)
    })

    it('constrains value to max', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} max={100} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '200{Enter}')

      expect(onCommit).toHaveBeenCalledWith(100)
    })

    it('constrains between min and max', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} min={10} max={50} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '5{Enter}')

      expect(onCommit).toHaveBeenCalledWith(10)
    })
  })

  describe('allowNull option', () => {
    it('commits null when allowNull is true and input is empty', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} allowNull={true} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '{Enter}')

      expect(onCommit).toHaveBeenCalledWith(null)
    })

    it('uses min as default when allowNull is false and input is empty', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} allowNull={false} min={10} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '{Enter}')

      expect(onCommit).toHaveBeenCalledWith(10)
    })

    it('uses 0 as default when no min specified and allowNull is false', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} allowNull={false} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '{Enter}')

      expect(onCommit).toHaveBeenCalledWith(0)
    })
  })

  describe('Keyboard shortcuts', () => {
    it('commits value on Enter', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '42{Enter}')

      expect(onCommit).toHaveBeenCalledWith(42)
    })

    it('cancels on Escape', async () => {
      const onCancel = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCancel={onCancel} />)

      const input = screen.getByRole('textbox')
      await user.type(input, '{Escape}')

      expect(onCancel).toHaveBeenCalled()
    })

    it('navigates to next cell on Tab', async () => {
      const onCommit = vi.fn()
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} onNavigate={onNavigate} />)

      screen.getByRole('textbox') // Element exists; Tab navigates focus
      await user.tab()

      expect(onCommit).toHaveBeenCalled()
      expect(onNavigate).toHaveBeenCalledWith('next')
    })

    it('navigates to previous cell on Shift+Tab', async () => {
      const onCommit = vi.fn()
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onCommit={onCommit} onNavigate={onNavigate} />)

      screen.getByRole('textbox') // Element exists; Shift+Tab navigates focus
      await user.keyboard('{Shift>}{Tab}{/Shift}')

      expect(onCommit).toHaveBeenCalled()
      expect(onNavigate).toHaveBeenCalledWith('prev')
    })

    it('navigates down on Enter', async () => {
      const onNavigateRow = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onNavigateRow={onNavigateRow} />)

      const input = screen.getByRole('textbox')
      await user.type(input, '{Enter}')

      expect(onNavigateRow).toHaveBeenCalledWith('down')
    })

    it('navigates up on Shift+Enter', async () => {
      const onNavigateRow = vi.fn()
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} onNavigateRow={onNavigateRow} />)

      screen.getByRole('textbox') // Element exists; Shift+Enter navigates row
      await user.keyboard('{Shift>}{Enter}{/Shift}')

      expect(onNavigateRow).toHaveBeenCalledWith('up')
    })
  })

  describe('Step increment/decrement', () => {
    it('increments by step on Alt+ArrowUp', async () => {
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} value={10} step={5} precision={0} />)

      const input = screen.getByRole('textbox')
      await user.keyboard('{Alt>}{ArrowUp}{/Alt}')

      expect(input).toHaveValue('15')
    })

    it('decrements by step on Alt+ArrowDown', async () => {
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} value={10} step={5} precision={0} />)

      const input = screen.getByRole('textbox')
      await user.keyboard('{Alt>}{ArrowDown}{/Alt}')

      expect(input).toHaveValue('5')
    })

    it('respects max on increment', async () => {
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} value={98} step={5} max={100} precision={0} />)

      const input = screen.getByRole('textbox')
      await user.keyboard('{Alt>}{ArrowUp}{/Alt}')

      expect(input).toHaveValue('100')
    })

    it('respects min on decrement', async () => {
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} value={2} step={5} min={0} precision={0} />)

      const input = screen.getByRole('textbox')
      await user.keyboard('{Alt>}{ArrowDown}{/Alt}')

      expect(input).toHaveValue('0')
    })
  })

  describe('Blur behavior', () => {
    it('commits value on blur', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(
        <div>
          <NumberEditor {...defaultProps} onCommit={onCommit} />
          <button>Other</button>
        </div>
      )

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, '75')
      await user.click(screen.getByRole('button'))

      expect(onCommit).toHaveBeenCalledWith(75)
    })
  })

  describe('Visual error state', () => {
    it('shows error styling for invalid input', async () => {
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} allowNull={false} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, 'invalid')

      expect(input.className).toContain('terracotta')
    })

    it('removes error styling when input becomes valid', async () => {
      const user = userEvent.setup()

      render(<NumberEditor {...defaultProps} allowNull={false} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)
      await user.type(input, 'invalid')
      expect(input.className).toContain('terracotta')

      await user.clear(input)
      await user.type(input, '42')
      expect(input.className).not.toContain('terracotta')
    })
  })

  describe('Precision formatting', () => {
    it('formats with 0 decimal places', () => {
      render(<NumberEditor {...defaultProps} value={42} precision={0} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('42')
    })

    it('formats with 1 decimal place', () => {
      render(<NumberEditor {...defaultProps} value={42.5} precision={1} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('42.5')
    })

    it('formats with 2 decimal places (default)', () => {
      render(<NumberEditor {...defaultProps} value={42} precision={2} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('42.00')
    })

    it('formats with 4 decimal places', () => {
      render(<NumberEditor {...defaultProps} value={3.14159} precision={4} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('3.1416')
    })
  })
})
