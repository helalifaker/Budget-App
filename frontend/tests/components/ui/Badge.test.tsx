import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/ui/badge'

describe('Badge', () => {
  it('renders with default variant', () => {
    render(<Badge>Default Badge</Badge>)

    const badge = screen.getByText('Default Badge')
    expect(badge).toBeInTheDocument()
    // Sahara Luxe Theme: Gold-based default styling
    expect(badge.className).toMatch(/bg-gold-50/)
    expect(badge.className).toMatch(/text-gold-800/)
  })

  describe('Variants', () => {
    it('renders default variant with gold background', () => {
      render(<Badge variant="default">Default</Badge>)

      const badge = screen.getByText('Default')
      expect(badge.className).toMatch(/bg-gold-50/)
      expect(badge.className).toMatch(/text-gold-800/)
      expect(badge.className).toMatch(/border-gold-200/)
    })

    it('renders secondary variant with sand background', () => {
      render(<Badge variant="secondary">Secondary</Badge>)

      const badge = screen.getByText('Secondary')
      expect(badge.className).toMatch(/bg-sand-100/)
      expect(badge.className).toMatch(/text-brown-800/)
    })

    it('renders destructive variant with error styling', () => {
      render(<Badge variant="destructive">Error</Badge>)

      const badge = screen.getByText('Error')
      expect(badge.className).toMatch(/bg-error-50/)
      expect(badge.className).toMatch(/text-error-800/)
    })

    it('renders outline variant with border only', () => {
      render(<Badge variant="outline">Outline</Badge>)

      const badge = screen.getByText('Outline')
      expect(badge.className).toMatch(/text-brown-800/)
      expect(badge.className).toMatch(/bg-transparent/)
      expect(badge.className).toMatch(/border-sand-300/)
    })

    it('renders success variant with success styling', () => {
      render(<Badge variant="success">Success</Badge>)

      const badge = screen.getByText('Success')
      expect(badge.className).toMatch(/bg-success-50/)
      expect(badge.className).toMatch(/text-success-800/)
    })

    it('renders warning variant with warning styling', () => {
      render(<Badge variant="warning">Warning</Badge>)

      const badge = screen.getByText('Warning')
      expect(badge.className).toMatch(/bg-warning-50/)
      expect(badge.className).toMatch(/text-warning-800/)
    })

    it('renders info variant with info styling', () => {
      render(<Badge variant="info">Info</Badge>)

      const badge = screen.getByText('Info')
      expect(badge.className).toMatch(/bg-info-50/)
      expect(badge.className).toMatch(/text-info-800/)
    })
  })

  describe('Styling', () => {
    it('has rounded-full shape', () => {
      render(<Badge>Round Badge</Badge>)

      const badge = screen.getByText('Round Badge')
      expect(badge.className).toMatch(/rounded-full/)
    })

    it('has border styling', () => {
      render(<Badge>Border Badge</Badge>)

      const badge = screen.getByText('Border Badge')
      expect(badge.className).toMatch(/border/)
    })

    it('has correct padding', () => {
      render(<Badge>Padded</Badge>)

      const badge = screen.getByText('Padded')
      expect(badge.className).toMatch(/px-2\.5/)
      expect(badge.className).toMatch(/py-0\.5/)
    })

    it('has correct text size', () => {
      render(<Badge>Small text</Badge>)

      const badge = screen.getByText('Small text')
      expect(badge.className).toMatch(/text-xs/)
      expect(badge.className).toMatch(/font-semibold/)
    })

    it('has focus ring styling', () => {
      render(<Badge>Focus Badge</Badge>)

      const badge = screen.getByText('Focus Badge')
      expect(badge.className).toMatch(/focus:outline-none/)
      expect(badge.className).toMatch(/focus:ring-2/)
      expect(badge.className).toMatch(/focus:ring-gold-500/)
    })
  })

  describe('Custom className', () => {
    it('applies custom className alongside default classes', () => {
      render(<Badge className="custom-badge">Custom</Badge>)

      const badge = screen.getByText('Custom')
      expect(badge.className).toMatch(/custom-badge/)
      // Still has default variant (gold-based)
      expect(badge.className).toMatch(/bg-gold-50/)
    })

    it('allows overriding background with custom class', () => {
      render(<Badge className="bg-purple-500">Purple</Badge>)

      const badge = screen.getByText('Purple')
      expect(badge.className).toMatch(/bg-purple-500/)
    })
  })

  describe('Content types', () => {
    it('renders text content', () => {
      render(<Badge>Text Badge</Badge>)

      expect(screen.getByText('Text Badge')).toBeInTheDocument()
    })

    it('renders numeric content', () => {
      render(<Badge>42</Badge>)

      expect(screen.getByText('42')).toBeInTheDocument()
    })

    it('renders with icon and text', () => {
      render(
        <Badge>
          <span className="icon">★</span>
          <span>Featured</span>
        </Badge>
      )

      expect(screen.getByText('★')).toBeInTheDocument()
      expect(screen.getByText('Featured')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('renders as a div element', () => {
      render(<Badge data-testid="badge">Badge</Badge>)

      const badge = screen.getByTestId('badge')
      expect(badge.tagName).toBe('DIV')
    })

    it('supports aria-label for screen readers', () => {
      render(<Badge aria-label="New notification">3</Badge>)

      const badge = screen.getByLabelText('New notification')
      expect(badge).toBeInTheDocument()
    })

    it('supports role attribute', () => {
      render(<Badge role="status">Live</Badge>)

      const badge = screen.getByRole('status')
      expect(badge).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('displays status badge for budget version', () => {
      render(<Badge variant="success">APPROVED</Badge>)

      const badge = screen.getByText('APPROVED')
      expect(badge.className).toMatch(/bg-success-50/)
    })

    it('displays count badge for notifications', () => {
      render(<Badge variant="destructive">5</Badge>)

      const badge = screen.getByText('5')
      expect(badge.className).toMatch(/bg-error-50/)
    })

    it('displays category tag', () => {
      render(<Badge variant="secondary">Planning</Badge>)

      expect(screen.getByText('Planning')).toBeInTheDocument()
    })

    it('displays KPI status indicator', () => {
      render(<Badge variant="warning">WARNING</Badge>)

      const badge = screen.getByText('WARNING')
      expect(badge.className).toMatch(/bg-warning-50/)
    })
  })
})
