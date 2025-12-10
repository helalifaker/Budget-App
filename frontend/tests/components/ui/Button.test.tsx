import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/ui/button'

describe('Button', () => {
  it('renders with default variant and size', () => {
    render(<Button>Click me</Button>)

    const button = screen.getByRole('button', { name: /click me/i })
    expect(button).toBeInTheDocument()
    // Uses gradient-based styling
    expect(button.className).toMatch(/bg-efir-gold-500/)
    expect(button.className).toMatch(/h-10/)
  })

  describe('Variants', () => {
    it('renders default variant with gold background', () => {
      render(<Button variant="default">Default</Button>)

      const button = screen.getByRole('button')
      // Uses solid gold styling
      expect(button.className).toMatch(/bg-efir-gold-500/)
      expect(button.className).toMatch(/text-white/)
      expect(button.className).toMatch(/hover:bg-efir-gold-600/)
    })

    it('renders destructive variant with error background', () => {
      render(<Button variant="destructive">Delete</Button>)

      const button = screen.getByRole('button')
      // Uses solid terracotta styling
      expect(button.className).toMatch(/bg-terracotta-500/)
      expect(button.className).toMatch(/text-white/)
      expect(button.className).toMatch(/hover:bg-terracotta-600/)
    })

    it('renders outline variant with border', () => {
      render(<Button variant="outline">Outline</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/border/)
      expect(button.className).toMatch(/border-border-medium/)
      expect(button.className).toMatch(/bg-paper/)
    })

    it('renders secondary variant with sand background', () => {
      render(<Button variant="secondary">Secondary</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/bg-subtle/)
      expect(button.className).toMatch(/text-text-primary/)
    })

    it('renders ghost variant with hover background only', () => {
      render(<Button variant="ghost">Ghost</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/hover:bg-subtle/)
      expect(button.className).toMatch(/text-text-secondary/)
    })

    it('renders link variant with underline', () => {
      render(<Button variant="link">Link</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/text-efir-gold-500/)
      expect(button.className).toMatch(/underline-offset-4/)
      expect(button.className).toMatch(/hover:underline/)
    })
  })

  describe('Sizes', () => {
    it('renders default size (h-10)', () => {
      render(<Button size="default">Default Size</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/h-10/)
      expect(button.className).toMatch(/px-4/)
      expect(button.className).toMatch(/py-2/)
    })

    it('renders small size (h-10 for WCAG touch target compliance)', () => {
      render(<Button size="sm">Small</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/h-10/) // Changed from h-9 to h-10 for WCAG accessibility
      expect(button.className).toMatch(/px-3/)
    })

    it('renders large size (h-11)', () => {
      render(<Button size="lg">Large</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/h-11/)
      expect(button.className).toMatch(/px-8/)
    })

    it('renders icon size (square h-10 w-10)', () => {
      render(
        <Button size="icon" aria-label="Icon button">
          X
        </Button>
      )

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/h-10/)
      expect(button.className).toMatch(/w-10/)
    })
  })

  describe('Interactive behavior', () => {
    it('calls onClick handler when clicked', async () => {
      const handleClick = vi.fn()
      const user = userEvent.setup()

      render(<Button onClick={handleClick}>Click me</Button>)

      const button = screen.getByRole('button')
      await user.click(button)

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('does not call onClick when disabled', async () => {
      const handleClick = vi.fn()
      const user = userEvent.setup()

      render(
        <Button onClick={handleClick} disabled>
          Click me
        </Button>
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(handleClick).not.toHaveBeenCalled()
    })

    it('renders as disabled with correct styling', () => {
      render(<Button disabled>Disabled</Button>)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(button.className).toMatch(/disabled:pointer-events-none/)
      expect(button.className).toMatch(/disabled:opacity-50/)
    })
  })

  describe('Custom className', () => {
    it('applies custom className alongside default classes', () => {
      render(<Button className="custom-class">Custom</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/custom-class/)
      // Still has default variant (gradient-based)
      expect(button.className).toMatch(/bg-efir-gold-500/)
    })
  })

  describe('asChild prop (Slot composition)', () => {
    it('renders as a child component when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      )

      const link = screen.getByRole('link', { name: /link button/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('href', '/test')
      // Button styles (gradient-based) applied to <a>
      expect(link.className).toMatch(/bg-efir-gold-500/)
    })
  })

  describe('Accessibility', () => {
    it('supports aria-label for icon buttons', () => {
      render(
        <Button size="icon" aria-label="Close dialog">
          ×
        </Button>
      )

      const button = screen.getByRole('button', { name: /close dialog/i })
      expect(button).toBeInTheDocument()
    })

    it('has focus-visible ring styles', () => {
      render(<Button>Focus me</Button>)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/focus-visible:outline-none/)
      expect(button.className).toMatch(/focus-visible:ring-2/)
      expect(button.className).toMatch(/focus-visible:ring-efir-gold/)
    })
  })

  describe('Combined variants and sizes', () => {
    it('renders destructive small button', () => {
      render(
        <Button variant="destructive" size="sm">
          Delete
        </Button>
      )

      const button = screen.getByRole('button')
      // Uses gradient-based styling
      expect(button.className).toMatch(/bg-terracotta-500/)
      expect(button.className).toMatch(/h-10/) // WCAG touch target minimum
    })

    it('renders outline large button', () => {
      render(
        <Button variant="outline" size="lg">
          Outline Large
        </Button>
      )

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/border/)
      expect(button.className).toMatch(/h-11/)
    })
  })

  describe('Type attribute', () => {
    it('renders without explicit type attribute (defaults to button behavior)', () => {
      render(<Button>Button</Button>)

      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
      // Note: type attribute is not explicitly set, but button defaults to "button" behavior
    })

    it('supports type="submit"', () => {
      render(<Button type="submit">Submit</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'submit')
    })

    it('supports type="reset"', () => {
      render(<Button type="reset">Reset</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'reset')
    })
  })
})
