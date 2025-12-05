import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from '@/components/ui/select'

describe('Select', () => {
  it('renders select trigger', () => {
    render(
      <Select>
        <SelectTrigger data-testid="select-trigger">
          <SelectValue placeholder="Select option" />
        </SelectTrigger>
      </Select>
    )

    expect(screen.getByTestId('select-trigger')).toBeInTheDocument()
    expect(screen.getByText('Select option')).toBeInTheDocument()
  })

  describe('SelectTrigger', () => {
    it('has correct default styling', () => {
      render(
        <Select>
          <SelectTrigger data-testid="trigger">
            <SelectValue />
          </SelectTrigger>
        </Select>
      )

      const trigger = screen.getByTestId('trigger')
      expect(trigger.className).toMatch(/flex/)
      expect(trigger.className).toMatch(/items-center/)
      expect(trigger.className).toMatch(/justify-between/)
      expect(trigger.className).toMatch(/rounded-button/)
      expect(trigger.className).toMatch(/border/)
      expect(trigger.className).toMatch(/bg-white/)
    })

    it('renders ChevronDown icon', () => {
      const { container } = render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
        </Select>
      )

      const icon = container.querySelector('svg.lucide-chevron-down')
      expect(icon).toBeInTheDocument()
    })

    it('disabled state has correct styling', () => {
      render(
        <Select disabled>
          <SelectTrigger data-testid="trigger">
            <SelectValue />
          </SelectTrigger>
        </Select>
      )

      const trigger = screen.getByTestId('trigger')
      expect(trigger.className).toMatch(/disabled:cursor-not-allowed/)
      expect(trigger.className).toMatch(/disabled:opacity-50/)
      expect(trigger).toBeDisabled()
    })

    it('applies custom className', () => {
      render(
        <Select>
          <SelectTrigger className="custom-trigger" data-testid="trigger">
            <SelectValue />
          </SelectTrigger>
        </Select>
      )

      const trigger = screen.getByTestId('trigger')
      expect(trigger.className).toMatch(/custom-trigger/)
    })
  })

  describe('SelectContent', () => {
    it('opens content when trigger is clicked', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Option 1</SelectItem>
            <SelectItem value="2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByRole('option', { name: 'Option 1' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Option 2' })).toBeInTheDocument()
    })

    it('has correct styling', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent data-testid="content">
            <SelectItem value="1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const content = screen.getByTestId('content')
      expect(content.className).toMatch(/overflow-hidden/)
      expect(content.className).toMatch(/rounded-button/)
      expect(content.className).toMatch(/border/)
      expect(content.className).toMatch(/bg-white/)
      expect(content.className).toMatch(/shadow-md/)
    })
  })

  describe('SelectItem', () => {
    it('renders item with correct text', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="test">Test Item</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByRole('option', { name: 'Test Item' })).toBeInTheDocument()
    })

    it('has correct styling', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1" data-testid="item">
              Item
            </SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const item = screen.getByTestId('item')
      expect(item.className).toMatch(/relative/)
      expect(item.className).toMatch(/flex/)
      expect(item.className).toMatch(/cursor-default/)
      expect(item.className).toMatch(/select-none/)
      expect(item.className).toMatch(/items-center/)
    })

    it('shows check icon for selected item', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <Select defaultValue="selected">
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="selected">Selected Item</SelectItem>
            <SelectItem value="other">Other Item</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const checkIcon = container.querySelector('svg.lucide-check')
      expect(checkIcon).toBeInTheDocument()
    })

    it('disabled item has correct styling', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1" disabled data-testid="disabled-item">
              Disabled Item
            </SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const item = screen.getByTestId('disabled-item')
      expect(item.className).toMatch(/data-\[disabled\]:pointer-events-none/)
      expect(item.className).toMatch(/data-\[disabled\]:opacity-50/)
    })
  })

  describe('SelectGroup and SelectLabel', () => {
    it('renders grouped items with labels', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Group 1</SelectLabel>
              <SelectItem value="1">Item 1</SelectItem>
              <SelectItem value="2">Item 2</SelectItem>
            </SelectGroup>
            <SelectGroup>
              <SelectLabel>Group 2</SelectLabel>
              <SelectItem value="3">Item 3</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByText('Group 1')).toBeInTheDocument()
      expect(screen.getByText('Group 2')).toBeInTheDocument()
    })

    it('label has correct styling', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel data-testid="label">Label</SelectLabel>
              <SelectItem value="1">Item</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const label = screen.getByTestId('label')
      expect(label.className).toMatch(/px-2/)
      expect(label.className).toMatch(/py-1\.5/)
      expect(label.className).toMatch(/text-sm/)
      expect(label.className).toMatch(/font-semibold/)
    })
  })

  describe('SelectSeparator', () => {
    it('renders separator between groups', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item 1</SelectItem>
            <SelectSeparator data-testid="separator" />
            <SelectItem value="2">Item 2</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const separator = screen.getByTestId('separator')
      expect(separator).toBeInTheDocument()
      expect(separator.className).toMatch(/-mx-1/)
      expect(separator.className).toMatch(/my-1/)
      expect(separator.className).toMatch(/h-px/)
      expect(separator.className).toMatch(/bg-sand-200/)
    })
  })

  describe('Interactive behavior', () => {
    it('selects item when clicked', async () => {
      const handleValueChange = vi.fn()
      const user = userEvent.setup()

      render(
        <Select onValueChange={handleValueChange}>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectItem value="option2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const option = screen.getByRole('option', { name: 'Option 1' })
      await user.click(option)

      expect(handleValueChange).toHaveBeenCalledWith('option1')
    })

    it('closes after selecting an item', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const option = screen.getByRole('option', { name: 'Option 1' })
      await user.click(option)

      // Content should close after selection
      expect(screen.queryByRole('option')).not.toBeInTheDocument()
    })

    it('does not select disabled items', async () => {
      const handleValueChange = vi.fn()
      const user = userEvent.setup()

      render(
        <Select onValueChange={handleValueChange}>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="disabled" disabled>
              Disabled Option
            </SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const option = screen.getByText('Disabled Option')
      await user.click(option)

      expect(handleValueChange).not.toHaveBeenCalled()
    })
  })

  describe('Keyboard navigation', () => {
    it('opens on Enter key', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      trigger.focus()
      await user.keyboard('{Enter}')

      expect(screen.getByRole('option', { name: 'Option 1' })).toBeInTheDocument()
    })

    it('navigates options with arrow keys', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Option 1</SelectItem>
            <SelectItem value="2">Option 2</SelectItem>
            <SelectItem value="3">Option 3</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      await user.keyboard('{ArrowDown}')
      await user.keyboard('{ArrowDown}')

      // Radix handles keyboard navigation internally
      expect(screen.getByRole('option', { name: 'Option 2' })).toBeInTheDocument()
    })

    it('closes on Escape key', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByRole('option', { name: 'Option 1' })).toBeInTheDocument()

      await user.keyboard('{Escape}')

      expect(screen.queryByRole('option')).not.toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('renders fiscal year selector', async () => {
      const user = userEvent.setup()

      render(
        <Select defaultValue="2025-2026">
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select fiscal year" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="2025-2026">2025-2026</SelectItem>
            <SelectItem value="2024-2025">2024-2025</SelectItem>
            <SelectItem value="2023-2024">2023-2024</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('2025-2026')).toBeInTheDocument()

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByRole('option', { name: '2024-2025' })).toBeInTheDocument()
    })

    it('renders budget version status selector', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="working">Working</SelectItem>
            <SelectItem value="submitted">Submitted</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="forecast">Forecast</SelectItem>
            <SelectItem value="superseded">Superseded</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByRole('option', { name: 'Working' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Approved' })).toBeInTheDocument()
    })

    it('renders academic level selector with groups', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select academic level" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Maternelle</SelectLabel>
              <SelectItem value="PS">PS (Petite Section)</SelectItem>
              <SelectItem value="MS">MS (Moyenne Section)</SelectItem>
              <SelectItem value="GS">GS (Grande Section)</SelectItem>
            </SelectGroup>
            <SelectSeparator />
            <SelectGroup>
              <SelectLabel>Élémentaire</SelectLabel>
              <SelectItem value="CP">CP</SelectItem>
              <SelectItem value="CE1">CE1</SelectItem>
              <SelectItem value="CE2">CE2</SelectItem>
              <SelectItem value="CM1">CM1</SelectItem>
              <SelectItem value="CM2">CM2</SelectItem>
            </SelectGroup>
            <SelectSeparator />
            <SelectGroup>
              <SelectLabel>Collège</SelectLabel>
              <SelectItem value="6">6ème</SelectItem>
              <SelectItem value="5">5ème</SelectItem>
              <SelectItem value="4">4ème</SelectItem>
              <SelectItem value="3">3ème</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByText('Maternelle')).toBeInTheDocument()
      expect(screen.getByText('Élémentaire')).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'PS (Petite Section)' })).toBeInTheDocument()
    })

    it('renders nationality selector for fee calculation', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select nationality" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="french">French</SelectItem>
            <SelectItem value="saudi">Saudi</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByRole('option', { name: 'French' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Saudi' })).toBeInTheDocument()
    })

    it('renders teacher category selector', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select teacher category" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>AEFE</SelectLabel>
              <SelectItem value="aefe-detached">AEFE Detached</SelectItem>
              <SelectItem value="aefe-funded">AEFE Funded (Full)</SelectItem>
            </SelectGroup>
            <SelectSeparator />
            <SelectGroup>
              <SelectLabel>Local</SelectLabel>
              <SelectItem value="local-teacher">Local Teacher</SelectItem>
              <SelectItem value="local-assistant">Local Assistant (ATSEM)</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByText('AEFE')).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'AEFE Detached' })).toBeInTheDocument()
    })

    it('renders currency selector', async () => {
      const user = userEvent.setup()

      render(
        <Select defaultValue="SAR">
          <SelectTrigger className="w-[100px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="SAR">SAR</SelectItem>
            <SelectItem value="EUR">EUR</SelectItem>
            <SelectItem value="USD">USD</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('SAR')).toBeInTheDocument()

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.getByRole('option', { name: 'EUR' })).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('trigger is accessible', () => {
      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      expect(trigger).toBeInTheDocument()
      expect(trigger).toHaveAttribute('role', 'button')
    })

    it('items have option role when open', async () => {
      const user = userEvent.setup()

      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Option 1</SelectItem>
            <SelectItem value="2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(2)
    })

    it('supports aria-label', () => {
      render(
        <Select>
          <SelectTrigger aria-label="Budget version">
            <SelectValue />
          </SelectTrigger>
        </Select>
      )

      expect(screen.getByLabelText('Budget version')).toBeInTheDocument()
    })

    it('disabled trigger is not interactive', async () => {
      const user = userEvent.setup()

      render(
        <Select disabled>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      expect(screen.queryByRole('option')).not.toBeInTheDocument()
    })
  })

  describe('Controlled state', () => {
    it('can be controlled with value and onValueChange', async () => {
      const handleValueChange = vi.fn()
      const user = userEvent.setup()

      const { rerender } = render(
        <Select value="option1" onValueChange={handleValueChange}>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectItem value="option2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('Option 1')).toBeInTheDocument()

      const trigger = screen.getByTestId('select-trigger')
      await user.click(trigger)

      const option2 = screen.getByRole('option', { name: 'Option 2' })
      await user.click(option2)

      expect(handleValueChange).toHaveBeenCalledWith('option2')

      // Rerender with new value
      rerender(
        <Select value="option2" onValueChange={handleValueChange}>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectItem value="option2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('Option 2')).toBeInTheDocument()
    })
  })
})
