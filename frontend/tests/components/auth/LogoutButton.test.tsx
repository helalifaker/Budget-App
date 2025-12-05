import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LogoutButton } from '@/components/auth/LogoutButton'

// Mock dependencies
const mockSignOut = vi.fn()

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    signOut: mockSignOut,
  }),
}))

describe('LogoutButton', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sign out button', () => {
    render(<LogoutButton />)

    expect(screen.getByText('Sign Out')).toBeInTheDocument()
  })

  describe('Button styling', () => {
    it('has correct classes', () => {
      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')
      expect(button).toBeInTheDocument()
      expect(button.className).toMatch(/rounded-md/)
      expect(button.className).toMatch(/bg-red-600/)
      expect(button.className).toMatch(/text-white/)
      expect(button.className).toMatch(/hover:bg-red-700/)
    })

    it('has padding', () => {
      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')
      expect(button.className).toMatch(/px-4/)
      expect(button.className).toMatch(/py-2/)
    })
  })

  describe('Click behavior', () => {
    it('calls signOut when clicked', async () => {
      const user = userEvent.setup()

      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')
      await user.click(button)

      expect(mockSignOut).toHaveBeenCalledTimes(1)
    })

    it('calls signOut on multiple clicks', async () => {
      const user = userEvent.setup()

      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')
      await user.click(button)
      await user.click(button)
      await user.click(button)

      expect(mockSignOut).toHaveBeenCalledTimes(3)
    })
  })

  describe('Keyboard accessibility', () => {
    it('can be activated with Enter key', async () => {
      const user = userEvent.setup()

      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')
      button.focus()
      await user.keyboard('{Enter}')

      expect(mockSignOut).toHaveBeenCalled()
    })

    it('can be activated with Space key', async () => {
      const user = userEvent.setup()

      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')
      button.focus()
      await user.keyboard(' ')

      expect(mockSignOut).toHaveBeenCalled()
    })

    it('is keyboard focusable', () => {
      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')
      button.focus()

      expect(button).toHaveFocus()
    })
  })

  describe('Real-world use cases', () => {
    it('renders in header', () => {
      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')
      expect(button).toBeInTheDocument()
      expect(button.tagName).toBe('BUTTON')
    })

    it('renders in navigation menu', () => {
      render(
        <div data-testid="nav">
          <LogoutButton />
        </div>
      )

      const nav = screen.getByTestId('nav')
      const button = screen.getByText('Sign Out')

      expect(nav).toContainElement(button)
    })

    it('handles rapid clicking', async () => {
      const user = userEvent.setup()

      render(<LogoutButton />)

      const button = screen.getByText('Sign Out')

      // Rapid clicks
      await user.tripleClick(button)

      // Should have called signOut multiple times
      expect(mockSignOut.mock.calls.length).toBeGreaterThan(0)
    })
  })
})
