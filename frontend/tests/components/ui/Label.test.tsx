import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Label } from '@/components/ui/label'

describe('Label', () => {
  it('renders basic label', () => {
    render(<Label>Label text</Label>)

    expect(screen.getByText('Label text')).toBeInTheDocument()
  })

  describe('Styling', () => {
    it('has correct default styling', () => {
      render(<Label data-testid="label">Text</Label>)

      const label = screen.getByTestId('label')
      expect(label.className).toMatch(/text-sm/)
      expect(label.className).toMatch(/font-medium/)
      expect(label.className).toMatch(/text-twilight-700/)
      expect(label.className).toMatch(/leading-none/)
    })

    it('has peer-disabled styling', () => {
      render(<Label data-testid="label">Text</Label>)

      const label = screen.getByTestId('label')
      expect(label.className).toMatch(/peer-disabled:cursor-not-allowed/)
      expect(label.className).toMatch(/peer-disabled:opacity-70/)
    })

    it('applies custom className', () => {
      render(
        <Label className="custom-label" data-testid="label">
          Text
        </Label>
      )

      const label = screen.getByTestId('label')
      expect(label.className).toMatch(/custom-label/)
      expect(label.className).toMatch(/text-sm/) // Still has default classes
    })
  })

  describe('For attribute', () => {
    it('supports htmlFor attribute for linking to input', () => {
      render(
        <>
          <Label htmlFor="username">Username</Label>
          <input id="username" type="text" />
        </>
      )

      const label = screen.getByText('Username')
      expect(label).toHaveAttribute('for', 'username')
    })

    it('is properly linked to input with htmlFor', () => {
      render(
        <div>
          <Label htmlFor="test-email-input">Email Address</Label>
          <input id="test-email-input" type="email" data-testid="email-field" />
        </div>
      )

      const label = screen.getByText('Email Address')
      expect(label).toHaveAttribute('for', 'test-email-input')
    })
  })

  describe('Content types', () => {
    it('renders text content', () => {
      render(<Label>Simple text</Label>)

      expect(screen.getByText('Simple text')).toBeInTheDocument()
    })

    it('renders with asterisk for required fields', () => {
      render(
        <Label>
          Email <span className="text-red-500">*</span>
        </Label>
      )

      expect(screen.getByText('Email')).toBeInTheDocument()
      expect(screen.getByText('*')).toBeInTheDocument()
    })

    it('renders with help icon', () => {
      render(
        <Label>
          Budget Version <span className="text-gray-400">(?)</span>
        </Label>
      )

      expect(screen.getByText('Budget Version')).toBeInTheDocument()
      expect(screen.getByText('(?)')).toBeInTheDocument()
    })

    it('renders with nested elements', () => {
      render(
        <Label>
          <span className="font-bold">Important:</span> Enter value
        </Label>
      )

      expect(screen.getByText('Important:')).toBeInTheDocument()
      expect(screen.getByText('Enter value')).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('renders label for enrollment input', () => {
      render(
        <>
          <Label htmlFor="enrollment">Student Count</Label>
          <input id="enrollment" type="number" />
        </>
      )

      expect(screen.getByText('Student Count')).toBeInTheDocument()
    })

    it('renders label for budget amount with currency', () => {
      render(
        <>
          <Label htmlFor="amount">Amount (SAR)</Label>
          <input id="amount" type="number" />
        </>
      )

      expect(screen.getByText('Amount (SAR)')).toBeInTheDocument()
    })

    it('renders label for fiscal year select', () => {
      render(
        <>
          <Label htmlFor="fiscal-year">Fiscal Year</Label>
          <select id="fiscal-year">
            <option>2025-2026</option>
          </select>
        </>
      )

      expect(screen.getByText('Fiscal Year')).toBeInTheDocument()
    })

    it('renders required field indicator', () => {
      render(
        <>
          <Label htmlFor="email">
            Email Address <span className="text-red-500">*</span>
          </Label>
          <input id="email" type="email" required />
        </>
      )

      const label = screen.getByText('Email Address')
      const asterisk = screen.getByText('*')

      expect(label).toBeInTheDocument()
      expect(asterisk).toBeInTheDocument()
      expect(asterisk.className).toMatch(/text-red-500/)
    })

    it('renders label with description', () => {
      render(
        <div>
          <Label htmlFor="dhg-hours">
            DHG Hours
            <span className="block text-xs font-normal text-gray-500">Total hours per subject</span>
          </Label>
          <input id="dhg-hours" type="number" />
        </div>
      )

      expect(screen.getByText('DHG Hours')).toBeInTheDocument()
      expect(screen.getByText('Total hours per subject')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('is properly associated with form controls', () => {
      render(
        <>
          <Label htmlFor="test-input">Test Label</Label>
          <input id="test-input" type="text" />
        </>
      )

      const input = screen.getByLabelText('Test Label')
      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('id', 'test-input')
    })

    it('supports aria-label for screen readers', () => {
      render(<Label aria-label="Screen reader label">Visible label</Label>)

      const label = screen.getByLabelText('Screen reader label')
      expect(label).toBeInTheDocument()
    })

    it('supports custom attributes', () => {
      render(
        <Label data-testid="custom-label" data-module="planning">
          Label
        </Label>
      )

      const label = screen.getByTestId('custom-label')
      expect(label).toHaveAttribute('data-module', 'planning')
    })
  })

  describe('With disabled input (peer-disabled)', () => {
    it('demonstrates peer-disabled usage', () => {
      render(
        <div>
          <input id="disabled-input" type="text" disabled className="peer" />
          <Label htmlFor="disabled-input">Disabled Label</Label>
        </div>
      )

      const label = screen.getByText('Disabled Label')
      expect(label.className).toMatch(/peer-disabled:cursor-not-allowed/)
      expect(label.className).toMatch(/peer-disabled:opacity-70/)
    })
  })

  describe('Form integration', () => {
    it('works within a complete form field', () => {
      render(
        <div className="space-y-2">
          <Label htmlFor="budget-version">
            Budget Version <span className="text-red-500">*</span>
          </Label>
          <input
            id="budget-version"
            type="text"
            placeholder="2025-2026"
            required
            className="peer"
          />
          <p className="text-sm text-gray-500">Select the fiscal year for this budget</p>
        </div>
      )

      expect(screen.getByText('Budget Version')).toBeInTheDocument()
      expect(screen.getByText('*')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('2025-2026')).toBeInTheDocument()
      expect(screen.getByText('Select the fiscal year for this budget')).toBeInTheDocument()
    })

    it('integrates with error messages', () => {
      render(
        <div>
          <Label htmlFor="amount">Amount</Label>
          <input id="amount" type="number" aria-invalid="true" aria-describedby="amount-error" />
          <span id="amount-error" className="text-red-500 text-sm">
            Amount must be greater than 0
          </span>
        </div>
      )

      expect(screen.getByText('Amount')).toBeInTheDocument()
      expect(screen.getByText('Amount must be greater than 0')).toBeInTheDocument()
    })
  })
})
