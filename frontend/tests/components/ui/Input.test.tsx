import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from '@/components/ui/input'

describe('Input', () => {
  it('renders basic input', () => {
    render(<Input placeholder="Enter text" />)

    const input = screen.getByPlaceholderText('Enter text')
    expect(input).toBeInTheDocument()
  })

  describe('Input types', () => {
    it('renders as input element', () => {
      render(<Input data-testid="text-input" />)

      const input = screen.getByTestId('text-input')
      expect(input.tagName).toBe('INPUT')
      // Note: type attribute defaults to "text" in browsers but may not be explicitly set
    })

    it('renders email input', () => {
      render(<Input type="email" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('type', 'email')
    })

    it('renders password input', () => {
      render(<Input type="password" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('type', 'password')
    })

    it('renders number input', () => {
      render(<Input type="number" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('type', 'number')
    })

    it('renders date input', () => {
      render(<Input type="date" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('type', 'date')
    })

    it('renders search input', () => {
      render(<Input type="search" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('type', 'search')
    })
  })

  describe('Styling', () => {
    it('has correct default styling', () => {
      render(<Input data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input.className).toMatch(/rounded-button/)
      expect(input.className).toMatch(/border/)
      expect(input.className).toMatch(/border-sand-300/)
      expect(input.className).toMatch(/bg-white/)
      expect(input.className).toMatch(/h-10/)
      expect(input.className).toMatch(/w-full/)
    })

    it('has focus styles', () => {
      render(<Input data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input.className).toMatch(/focus-visible:outline-none/)
      expect(input.className).toMatch(/focus-visible:ring-2/)
      expect(input.className).toMatch(/focus-visible:ring-gold-500/)
      expect(input.className).toMatch(/focus-visible:border-gold-500/)
    })

    it('has placeholder styling', () => {
      render(<Input data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input.className).toMatch(/placeholder:text-twilight-400/)
    })

    it('applies custom className', () => {
      render(<Input className="custom-input" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input.className).toMatch(/custom-input/)
      expect(input.className).toMatch(/rounded-button/) // Still has default classes
    })
  })

  describe('Interactive behavior', () => {
    it('accepts user input', async () => {
      const user = userEvent.setup()
      render(<Input data-testid="input" />)

      const input = screen.getByTestId('input') as HTMLInputElement
      await user.type(input, 'Hello World')

      expect(input.value).toBe('Hello World')
    })

    it('calls onChange handler', async () => {
      const handleChange = vi.fn()
      const user = userEvent.setup()

      render(<Input onChange={handleChange} data-testid="input" />)

      const input = screen.getByTestId('input')
      await user.type(input, 'Test')

      expect(handleChange).toHaveBeenCalled()
    })

    it('respects value prop (controlled input)', () => {
      render(<Input value="Controlled value" onChange={() => {}} data-testid="input" />)

      const input = screen.getByTestId('input') as HTMLInputElement
      expect(input.value).toBe('Controlled value')
    })

    it('respects defaultValue prop (uncontrolled input)', () => {
      render(<Input defaultValue="Default value" data-testid="input" />)

      const input = screen.getByTestId('input') as HTMLInputElement
      expect(input.value).toBe('Default value')
    })
  })

  describe('Disabled state', () => {
    it('renders as disabled', () => {
      render(<Input disabled data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toBeDisabled()
    })

    it('has disabled styling', () => {
      render(<Input disabled data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input.className).toMatch(/disabled:cursor-not-allowed/)
      expect(input.className).toMatch(/disabled:opacity-50/)
    })

    it('does not accept input when disabled', async () => {
      const user = userEvent.setup()
      render(<Input disabled data-testid="input" />)

      const input = screen.getByTestId('input') as HTMLInputElement
      await user.type(input, 'Should not type')

      expect(input.value).toBe('')
    })

    it('does not call onChange when disabled', async () => {
      const handleChange = vi.fn()
      const user = userEvent.setup()

      render(<Input disabled onChange={handleChange} data-testid="input" />)

      const input = screen.getByTestId('input')
      await user.type(input, 'Test')

      expect(handleChange).not.toHaveBeenCalled()
    })
  })

  describe('Attributes', () => {
    it('supports placeholder', () => {
      render(<Input placeholder="Enter email" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('placeholder', 'Enter email')
    })

    it('supports required', () => {
      render(<Input required data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toBeRequired()
    })

    it('supports name attribute', () => {
      render(<Input name="username" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('name', 'username')
    })

    it('supports id attribute', () => {
      render(<Input id="email-input" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('id', 'email-input')
    })

    it('supports aria-label', () => {
      render(<Input aria-label="Email address" data-testid="input" />)

      const input = screen.getByLabelText('Email address')
      expect(input).toBeInTheDocument()
    })

    it('supports maxLength', () => {
      render(<Input maxLength={10} data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('maxLength', '10')
    })

    it('supports min and max for number inputs', () => {
      render(<Input type="number" min={0} max={100} data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('min', '0')
      expect(input).toHaveAttribute('max', '100')
    })

    it('supports step for number inputs', () => {
      render(<Input type="number" step={0.01} data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('step', '0.01')
    })

    it('supports pattern for validation', () => {
      render(<Input pattern="[0-9]{3}-[0-9]{4}" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('pattern', '[0-9]{3}-[0-9]{4}')
    })
  })

  describe('Real-world use cases', () => {
    it('renders enrollment count input', () => {
      render(
        <Input
          type="number"
          placeholder="Enter student count"
          min={0}
          max={2000}
          data-testid="input"
        />
      )

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('type', 'number')
      expect(input).toHaveAttribute('placeholder', 'Enter student count')
    })

    it('renders budget amount input', () => {
      render(
        <Input
          type="number"
          placeholder="Enter amount in SAR"
          step={0.01}
          min={0}
          data-testid="input"
        />
      )

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('step', '0.01')
    })

    it('renders fiscal year input', () => {
      render(
        <Input
          type="text"
          placeholder="2025-2026"
          pattern="[0-9]{4}-[0-9]{4}"
          data-testid="input"
        />
      )

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('pattern', '[0-9]{4}-[0-9]{4}')
    })

    it('renders search filter input', () => {
      render(<Input type="search" placeholder="Search budget versions..." data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('type', 'search')
    })

    it('renders email input for user invitation', () => {
      render(
        <Input type="email" placeholder="colleague@efir.edu.sa" required data-testid="input" />
      )

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('type', 'email')
      expect(input).toBeRequired()
    })
  })

  describe('Accessibility', () => {
    it('is keyboard accessible', async () => {
      const user = userEvent.setup()
      render(<Input data-testid="input" />)

      const input = screen.getByTestId('input')
      await user.tab()

      expect(input).toHaveFocus()
    })

    it('supports aria-describedby for error messages', () => {
      render(
        <>
          <Input aria-describedby="error-msg" data-testid="input" />
          <span id="error-msg">This field is required</span>
        </>
      )

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('aria-describedby', 'error-msg')
    })

    it('supports aria-invalid for validation states', () => {
      render(<Input aria-invalid="true" data-testid="input" />)

      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('aria-invalid', 'true')
    })
  })
})
