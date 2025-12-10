import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Textarea } from '@/components/ui/textarea'

describe('Textarea', () => {
  it('renders basic textarea', () => {
    render(<Textarea placeholder="Enter text" />)

    const textarea = screen.getByPlaceholderText('Enter text')
    expect(textarea).toBeInTheDocument()
  })

  describe('Styling', () => {
    it('has correct default styling', () => {
      render(<Textarea data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea.className).toMatch(/rounded-button/)
      expect(textarea.className).toMatch(/border/)
      expect(textarea.className).toMatch(/border-border-medium/)
      expect(textarea.className).toMatch(/bg-white/)
      expect(textarea.className).toMatch(/min-h-\[80px\]/)
      expect(textarea.className).toMatch(/w-full/)
    })

    it('has focus styles', () => {
      render(<Textarea data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea.className).toMatch(/focus-visible:outline-none/)
      expect(textarea.className).toMatch(/focus-visible:ring-2/)
      expect(textarea.className).toMatch(/focus-visible:ring-gold-500/)
      expect(textarea.className).toMatch(/focus-visible:border-gold-500/)
    })

    it('has transition-colors animation', () => {
      render(<Textarea data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea.className).toMatch(/transition-colors/)
      expect(textarea.className).toMatch(/duration-200/)
    })

    it('has placeholder styling', () => {
      render(<Textarea data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea.className).toMatch(/placeholder:text-text-muted/)
    })

    it('applies custom className', () => {
      render(<Textarea className="custom-textarea" data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea.className).toMatch(/custom-textarea/)
      expect(textarea.className).toMatch(/rounded-button/) // Still has default classes
    })
  })

  describe('Interactive behavior', () => {
    it('accepts user input', async () => {
      const user = userEvent.setup()
      render(<Textarea data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
      await user.type(textarea, 'Hello World')

      expect(textarea.value).toBe('Hello World')
    })

    it('accepts multiline input', async () => {
      const user = userEvent.setup()
      render(<Textarea data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
      await user.type(textarea, 'Line 1{Enter}Line 2{Enter}Line 3')

      expect(textarea.value).toBe('Line 1\nLine 2\nLine 3')
    })

    it('calls onChange handler', async () => {
      const handleChange = vi.fn()
      const user = userEvent.setup()

      render(<Textarea onChange={handleChange} data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      await user.type(textarea, 'Test')

      expect(handleChange).toHaveBeenCalled()
    })

    it('respects value prop (controlled textarea)', () => {
      render(<Textarea value="Controlled value" onChange={() => {}} data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
      expect(textarea.value).toBe('Controlled value')
    })

    it('respects defaultValue prop (uncontrolled textarea)', () => {
      render(<Textarea defaultValue="Default value" data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
      expect(textarea.value).toBe('Default value')
    })
  })

  describe('Disabled state', () => {
    it('renders as disabled', () => {
      render(<Textarea disabled data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toBeDisabled()
    })

    it('has disabled styling', () => {
      render(<Textarea disabled data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea.className).toMatch(/disabled:cursor-not-allowed/)
      expect(textarea.className).toMatch(/disabled:opacity-50/)
    })

    it('does not accept input when disabled', async () => {
      const user = userEvent.setup()
      render(<Textarea disabled data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
      await user.type(textarea, 'Should not type')

      expect(textarea.value).toBe('')
    })

    it('does not call onChange when disabled', async () => {
      const handleChange = vi.fn()
      const user = userEvent.setup()

      render(<Textarea disabled onChange={handleChange} data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      await user.type(textarea, 'Test')

      expect(handleChange).not.toHaveBeenCalled()
    })
  })

  describe('Attributes', () => {
    it('supports placeholder', () => {
      render(<Textarea placeholder="Enter comments" data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('placeholder', 'Enter comments')
    })

    it('supports required', () => {
      render(<Textarea required data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toBeRequired()
    })

    it('supports name attribute', () => {
      render(<Textarea name="description" data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('name', 'description')
    })

    it('supports id attribute', () => {
      render(<Textarea id="budget-notes" data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('id', 'budget-notes')
    })

    it('supports aria-label', () => {
      render(<Textarea aria-label="Budget description" data-testid="textarea" />)

      const textarea = screen.getByLabelText('Budget description')
      expect(textarea).toBeInTheDocument()
    })

    it('supports maxLength', () => {
      render(<Textarea maxLength={500} data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('maxLength', '500')
    })

    it('supports rows attribute', () => {
      render(<Textarea rows={10} data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('rows', '10')
    })

    it('supports cols attribute', () => {
      render(<Textarea cols={50} data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('cols', '50')
    })
  })

  describe('Real-world use cases', () => {
    it('renders budget version notes textarea', () => {
      render(
        <Textarea
          placeholder="Enter notes about this budget version..."
          rows={5}
          data-testid="textarea"
        />
      )

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('placeholder', 'Enter notes about this budget version...')
      expect(textarea).toHaveAttribute('rows', '5')
    })

    it('renders DHG justification textarea', () => {
      render(
        <Textarea
          placeholder="Explain DHG allocation decisions..."
          maxLength={1000}
          data-testid="textarea"
        />
      )

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('maxLength', '1000')
    })

    it('renders change log textarea', () => {
      render(
        <Textarea
          placeholder="Describe changes made to the budget..."
          required
          data-testid="textarea"
        />
      )

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toBeRequired()
    })

    it('renders comment textarea for collaboration', () => {
      render(<Textarea placeholder="Add a comment..." rows={3} data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('rows', '3')
    })

    it('renders approval notes textarea', () => {
      render(
        <Textarea placeholder="Approval notes or conditions..." rows={4} data-testid="textarea" />
      )

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('placeholder', 'Approval notes or conditions...')
    })
  })

  describe('Accessibility', () => {
    it('is keyboard accessible', async () => {
      const user = userEvent.setup()
      render(<Textarea data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      await user.tab()

      expect(textarea).toHaveFocus()
    })

    it('supports aria-describedby for help text', () => {
      render(
        <>
          <Textarea aria-describedby="help-text" data-testid="textarea" />
          <span id="help-text">Maximum 500 characters</span>
        </>
      )

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('aria-describedby', 'help-text')
    })

    it('supports aria-invalid for validation states', () => {
      render(<Textarea aria-invalid="true" data-testid="textarea" />)

      const textarea = screen.getByTestId('textarea')
      expect(textarea).toHaveAttribute('aria-invalid', 'true')
    })

    it('integrates with label', () => {
      render(
        <>
          <label htmlFor="notes">Notes</label>
          <Textarea id="notes" />
        </>
      )

      const textarea = screen.getByLabelText('Notes')
      expect(textarea).toBeInTheDocument()
    })
  })

  describe('Form integration', () => {
    it('works within a complete form field', () => {
      render(
        <div className="space-y-2">
          <label htmlFor="description">
            Budget Description <span className="text-red-500">*</span>
          </label>
          <Textarea
            id="description"
            placeholder="Provide a detailed description..."
            required
            rows={5}
            maxLength={1000}
          />
          <p className="text-sm text-gray-500">Maximum 1000 characters</p>
        </div>
      )

      expect(screen.getByLabelText(/Budget Description/)).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Provide a detailed description...')).toBeInTheDocument()
      expect(screen.getByText('Maximum 1000 characters')).toBeInTheDocument()
    })

    it('integrates with error messages', () => {
      render(
        <div>
          <label htmlFor="notes">Notes</label>
          <Textarea id="notes" aria-invalid="true" aria-describedby="notes-error" />
          <span id="notes-error" className="text-red-500 text-sm">
            Notes are required
          </span>
        </div>
      )

      expect(screen.getByLabelText('Notes')).toBeInTheDocument()
      expect(screen.getByText('Notes are required')).toBeInTheDocument()
    })
  })
})
