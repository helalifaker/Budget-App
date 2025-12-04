import * as React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

describe('Dialog', () => {
  it('renders dialog trigger', () => {
    render(
      <Dialog>
        <DialogTrigger asChild>
          <Button>Open Dialog</Button>
        </DialogTrigger>
      </Dialog>
    )

    expect(screen.getByRole('button', { name: /open dialog/i })).toBeInTheDocument()
  })

  it('opens dialog when trigger is clicked', async () => {
    const user = userEvent.setup()

    render(
      <Dialog>
        <DialogTrigger asChild>
          <Button>Open</Button>
        </DialogTrigger>
        <DialogContent>
          <DialogTitle>Test Dialog</DialogTitle>
        </DialogContent>
      </Dialog>
    )

    const trigger = screen.getByRole('button', { name: /open/i })
    await user.click(trigger)

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Test Dialog')).toBeInTheDocument()
  })

  it('closes dialog when close button is clicked', async () => {
    const user = userEvent.setup()

    render(
      <Dialog>
        <DialogTrigger asChild>
          <Button>Open</Button>
        </DialogTrigger>
        <DialogContent>
          <DialogTitle>Test Dialog</DialogTitle>
        </DialogContent>
      </Dialog>
    )

    await user.click(screen.getByRole('button', { name: /open/i }))

    const dialog = screen.getByRole('dialog')
    const closeButton = within(dialog).getByRole('button', { name: /close/i })

    await user.click(closeButton)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  describe('DialogContent', () => {
    it('renders dialog content with children', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <p>Dialog content</p>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))

      expect(screen.getByText('Dialog content')).toBeInTheDocument()
    })

    it('has close button with X icon', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Test</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))

      const closeButton = screen.getByRole('button', { name: /close/i })
      expect(closeButton).toBeInTheDocument()
    })
  })

  describe('DialogHeader', () => {
    it('renders dialog header', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader data-testid="dialog-header">
              <DialogTitle>Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))

      expect(screen.getByTestId('dialog-header')).toBeInTheDocument()
    })
  })

  describe('DialogTitle', () => {
    it('renders dialog title', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Budget Version</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))

      expect(screen.getByText('Budget Version')).toBeInTheDocument()
    })
  })

  describe('DialogDescription', () => {
    it('renders dialog description', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Confirm Action</DialogTitle>
            <DialogDescription>Are you sure you want to proceed?</DialogDescription>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))

      expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument()
    })
  })

  describe('DialogFooter', () => {
    it('renders dialog footer with buttons', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Confirm</DialogTitle>
            <DialogFooter>
              <Button variant="outline">Cancel</Button>
              <Button>Confirm</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument()
    })
  })

  describe('Complete dialog composition', () => {
    it('renders full dialog with all parts', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Submit Budget</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Submit Budget Version</DialogTitle>
              <DialogDescription>
                This action will submit the budget for approval. You will not be able to edit it
                after submission.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <p>Budget: 2025-2026 Working Version</p>
            </div>
            <DialogFooter>
              <Button variant="outline">Cancel</Button>
              <Button>Submit</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /submit budget/i }))

      expect(screen.getByText('Submit Budget Version')).toBeInTheDocument()
      expect(
        screen.getByText(/This action will submit the budget for approval/)
      ).toBeInTheDocument()
      expect(screen.getByText('Budget: 2025-2026 Working Version')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
    })
  })

  describe('Real-world use cases', () => {
    it('renders confirmation dialog for budget deletion', async () => {
      const handleDelete = vi.fn()
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="destructive">Delete Budget</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Budget Version</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this budget version? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline">Cancel</Button>
              <Button variant="destructive" onClick={handleDelete}>
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /delete budget/i }))

      expect(screen.getByText('Delete Budget Version')).toBeInTheDocument()
      expect(screen.getByText(/This action cannot be undone/)).toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: /^delete$/i }))
      expect(handleDelete).toHaveBeenCalledTimes(1)
    })

    it('renders form dialog for adding enrollment data', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Add Enrollment Data</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Enrollment Data</DialogTitle>
              <DialogDescription>
                Enter enrollment projections for the academic level
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <p>Form fields would go here</p>
            </div>
            <DialogFooter>
              <Button variant="outline">Cancel</Button>
              <Button>Add</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /add enrollment data/i }))

      const dialog = screen.getByRole('dialog')
      expect(within(dialog).getByText('Add Enrollment Data')).toBeInTheDocument()
      expect(
        within(dialog).getByText('Enter enrollment projections for the academic level')
      ).toBeInTheDocument()
      expect(within(dialog).getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(within(dialog).getByRole('button', { name: /add/i })).toBeInTheDocument()
    })

    it('renders DHG allocation details dialog', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="ghost">View DHG Details</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>DHG Allocation - Mathematics</DialogTitle>
              <DialogDescription>Detailed breakdown of teaching hours allocation</DialogDescription>
            </DialogHeader>
            <div className="space-y-2">
              <p>Total Hours: 96 hours/week</p>
              <p>Required FTE: 5.33 teachers</p>
              <p>AEFE Positions: 4</p>
              <p>Local Positions: 2</p>
            </div>
            <DialogFooter>
              <Button>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /view dhg details/i }))

      expect(screen.getByText('DHG Allocation - Mathematics')).toBeInTheDocument()
      expect(screen.getByText('Total Hours: 96 hours/week')).toBeInTheDocument()
      expect(screen.getByText('Required FTE: 5.33 teachers')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Accessible Dialog</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))

      const dialog = screen.getByRole('dialog')
      expect(dialog).toBeInTheDocument()
    })

    it('close button has sr-only text', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Test</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))

      const closeButton = screen.getByRole('button', { name: /close/i })
      expect(closeButton).toBeInTheDocument()
    })

    it('keyboard navigation with escape key', async () => {
      const user = userEvent.setup()

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Test Dialog</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      await user.click(screen.getByRole('button', { name: /open/i }))
      expect(screen.getByRole('dialog')).toBeInTheDocument()

      await user.keyboard('{Escape}')
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  describe('Controlled state', () => {
    it('can be controlled externally', async () => {
      const TestComponent = () => {
        const [open, setOpen] = React.useState(false)

        return (
          <>
            <Button onClick={() => setOpen(true)}>External Open</Button>
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogContent>
                <DialogTitle>Controlled Dialog</DialogTitle>
              </DialogContent>
            </Dialog>
          </>
        )
      }

      const user = userEvent.setup()
      render(<TestComponent />)

      await user.click(screen.getByRole('button', { name: /external open/i }))
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })
})
