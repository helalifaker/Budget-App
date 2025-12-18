/**
 * CheckboxEditor Tests
 *
 * Tests for the inline checkbox/boolean editor component used in TanStack Table cells.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CheckboxEditor } from '@/components/grid/tanstack/editors/CheckboxEditor'

describe('CheckboxEditor', () => {
  const defaultProps = {
    value: false,
    onCommit: vi.fn(),
    onCancel: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Helper to get the inner checkbox button (shadcn/ui Checkbox renders a button with role="checkbox")
  const getCheckbox = () => screen.getByRole('checkbox')

  describe('Rendering', () => {
    it('renders a checkbox element', () => {
      render(<CheckboxEditor {...defaultProps} />)

      const checkbox = getCheckbox()
      expect(checkbox).toBeInTheDocument()
    })

    it('displays unchecked state for false value', () => {
      render(<CheckboxEditor {...defaultProps} value={false} />)

      const checkbox = getCheckbox()
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')
    })

    it('displays checked state for true value', () => {
      render(<CheckboxEditor {...defaultProps} value={true} />)

      const checkbox = getCheckbox()
      expect(checkbox).toHaveAttribute('data-state', 'checked')
    })

    it('displays unchecked state for null value', () => {
      render(<CheckboxEditor {...defaultProps} value={null} />)

      const checkbox = getCheckbox()
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')
    })

    it('displays unchecked state for undefined value', () => {
      render(<CheckboxEditor {...defaultProps} value={undefined} />)

      const checkbox = getCheckbox()
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')
    })

    it('applies custom className', () => {
      render(<CheckboxEditor {...defaultProps} className="custom-class" />)

      // The wrapper div should have the custom class
      const checkbox = getCheckbox()
      const wrapper = checkbox.parentElement
      expect(wrapper?.className).toContain('custom-class')
    })
  })

  describe('Auto-focus', () => {
    it('auto-focuses wrapper on mount', async () => {
      render(<CheckboxEditor {...defaultProps} />)

      const checkbox = getCheckbox()
      const wrapper = checkbox.parentElement
      await waitFor(() => {
        expect(document.activeElement).toBe(wrapper)
      })
    })
  })

  describe('Toggle behavior', () => {
    it('commits true when clicking unchecked checkbox', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<CheckboxEditor {...defaultProps} value={false} onCommit={onCommit} />)

      const checkbox = getCheckbox()
      await user.click(checkbox)

      expect(onCommit).toHaveBeenCalledWith(true)
    })

    it('commits false when clicking checked checkbox', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<CheckboxEditor {...defaultProps} value={true} onCommit={onCommit} />)

      const checkbox = getCheckbox()
      await user.click(checkbox)

      expect(onCommit).toHaveBeenCalledWith(false)
    })

    it('commits true when toggling null value', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<CheckboxEditor {...defaultProps} value={null} onCommit={onCommit} />)

      const checkbox = getCheckbox()
      await user.click(checkbox)

      expect(onCommit).toHaveBeenCalledWith(true)
    })
  })

  describe('Keyboard shortcuts', () => {
    // Helper to get wrapper (which handles keyboard events)
    const getWrapper = () => getCheckbox().parentElement!

    it('toggles value on Space', async () => {
      const onCommit = vi.fn()
      const user = userEvent.setup()

      render(<CheckboxEditor {...defaultProps} value={false} onCommit={onCommit} />)

      const wrapper = getWrapper()
      wrapper.focus()
      await user.keyboard(' ')

      expect(onCommit).toHaveBeenCalledWith(true)
    })

    it('commits current value and navigates on Enter', async () => {
      const onCommit = vi.fn()
      const onNavigateRow = vi.fn()
      const user = userEvent.setup()

      render(
        <CheckboxEditor
          {...defaultProps}
          value={false}
          onCommit={onCommit}
          onNavigateRow={onNavigateRow}
        />
      )

      const wrapper = getWrapper()
      wrapper.focus()
      await user.keyboard('{Enter}')

      expect(onCommit).toHaveBeenCalledWith(false) // Commits current value
      expect(onNavigateRow).toHaveBeenCalledWith('down')
    })

    it('cancels on Escape', async () => {
      const onCancel = vi.fn()
      const user = userEvent.setup()

      render(<CheckboxEditor {...defaultProps} onCancel={onCancel} />)

      const wrapper = getWrapper()
      wrapper.focus()
      await user.keyboard('{Escape}')

      expect(onCancel).toHaveBeenCalled()
    })

    it('navigates to next cell on Tab', async () => {
      const onCommit = vi.fn()
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(
        <CheckboxEditor
          {...defaultProps}
          value={true}
          onCommit={onCommit}
          onNavigate={onNavigate}
        />
      )

      const wrapper = getWrapper()
      wrapper.focus()
      await user.keyboard('{Tab}')

      expect(onCommit).toHaveBeenCalledWith(true)
      expect(onNavigate).toHaveBeenCalledWith('next')
    })

    it('navigates to previous cell on Shift+Tab', async () => {
      const onCommit = vi.fn()
      const onNavigate = vi.fn()
      const user = userEvent.setup()

      render(
        <CheckboxEditor
          {...defaultProps}
          value={false}
          onCommit={onCommit}
          onNavigate={onNavigate}
        />
      )

      const wrapper = getWrapper()
      wrapper.focus()
      await user.keyboard('{Shift>}{Tab}{/Shift}')

      expect(onCommit).toHaveBeenCalledWith(false)
      expect(onNavigate).toHaveBeenCalledWith('prev')
    })
  })

  describe('Styling', () => {
    it('wrapper is centered in the cell', () => {
      render(<CheckboxEditor {...defaultProps} />)

      const wrapper = getCheckbox().parentElement
      expect(wrapper?.className).toContain('justify-center')
    })

    it('checkbox has appropriate sizing', () => {
      render(<CheckboxEditor {...defaultProps} />)

      const checkbox = getCheckbox()
      expect(checkbox.className).toContain('h-4')
      expect(checkbox.className).toContain('w-4')
    })

    it('uses EFIR design system accent color', () => {
      render(<CheckboxEditor {...defaultProps} />)

      const checkbox = getCheckbox()
      expect(checkbox.className).toContain('gold')
    })

    it('wrapper has focus ring styling', () => {
      render(<CheckboxEditor {...defaultProps} />)

      const wrapper = getCheckbox().parentElement
      expect(wrapper?.className).toContain('focus:ring')
    })
  })

  describe('Accessibility', () => {
    it('checkbox is accessible by role', () => {
      render(<CheckboxEditor {...defaultProps} />)

      expect(getCheckbox()).toBeInTheDocument()
    })

    it('wrapper has aria-label', () => {
      render(<CheckboxEditor {...defaultProps} ariaLabel="Toggle active status" />)

      const wrapper = getCheckbox().parentElement
      expect(wrapper).toHaveAttribute('aria-label', 'Toggle active status')
    })
  })
})
