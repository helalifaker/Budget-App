import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeToggle } from '@/components/ui/theme-toggle'

// Mock useTheme hook
const mockToggleTheme = vi.fn()
const mockSetTheme = vi.fn()
let mockResolvedTheme: 'light' | 'dark' = 'light'
let mockTheme: 'light' | 'dark' | 'system' = 'light'

vi.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    theme: mockTheme,
    resolvedTheme: mockResolvedTheme,
    setTheme: mockSetTheme,
    toggleTheme: mockToggleTheme,
  }),
}))

describe('ThemeToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockTheme = 'light'
    mockResolvedTheme = 'light'
  })

  it('renders theme toggle button', () => {
    render(<ThemeToggle />)

    const button = screen.getByRole('button', { name: /switch to dark mode/i })
    expect(button).toBeInTheDocument()
  })

  describe('Icon display', () => {
    it('shows Moon icon when theme is light (to switch to dark)', () => {
      mockResolvedTheme = 'light'
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      const moonIcon = button.querySelector('svg.lucide-moon')
      expect(moonIcon).toBeInTheDocument()
    })

    it('shows Sun icon when theme is dark (to switch to light)', () => {
      mockResolvedTheme = 'dark'
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      const sunIcon = button.querySelector('svg.lucide-sun')
      expect(sunIcon).toBeInTheDocument()
    })

    it('Moon icon has correct styling', () => {
      mockResolvedTheme = 'light'
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      const moonIcon = button.querySelector('svg.lucide-moon')
      // SVG className might be object, use getAttribute
      expect(moonIcon?.getAttribute('class')).toMatch(/h-5/)
      expect(moonIcon?.getAttribute('class')).toMatch(/w-5/)
    })

    it('Sun icon has correct styling', () => {
      mockResolvedTheme = 'dark'
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      const sunIcon = button.querySelector('svg.lucide-sun')
      expect(sunIcon?.getAttribute('class')).toMatch(/h-5/)
      expect(sunIcon?.getAttribute('class')).toMatch(/w-5/)
    })
  })

  describe('Interactive behavior', () => {
    it('calls toggleTheme when clicked', async () => {
      mockResolvedTheme = 'light'
      const user = userEvent.setup()

      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockToggleTheme).toHaveBeenCalledTimes(1)
    })

    it('calls toggleTheme when dark theme is active', async () => {
      mockResolvedTheme = 'dark'
      const user = userEvent.setup()

      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockToggleTheme).toHaveBeenCalledTimes(1)
    })

    it('handles multiple clicks', async () => {
      mockResolvedTheme = 'light'
      const user = userEvent.setup()

      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      await user.click(button)
      await user.click(button)
      await user.click(button)

      expect(mockToggleTheme).toHaveBeenCalledTimes(3)
    })
  })

  describe('Styling', () => {
    it('button has ghost variant styling', () => {
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      // Ghost variant renders with hover:bg-sand-100 and text-brown-700
      expect(button.className).toMatch(/hover:bg-sand-100/)
      expect(button.className).toMatch(/text-brown-700/)
    })

    it('button has icon size styling', () => {
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      // Icon size renders as h-10 w-10
      expect(button.className).toMatch(/h-10/)
      expect(button.className).toMatch(/w-10/)
    })

    it('has transition classes on button', () => {
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      expect(button.className).toMatch(/transition-colors/)
    })
  })

  describe('Accessibility', () => {
    it('has accessible name when light theme', () => {
      mockResolvedTheme = 'light'
      render(<ThemeToggle />)

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      expect(button).toBeInTheDocument()
    })

    it('has accessible name when dark theme', () => {
      mockResolvedTheme = 'dark'
      render(<ThemeToggle />)

      const button = screen.getByRole('button', { name: /switch to light mode/i })
      expect(button).toBeInTheDocument()
    })

    it('has sr-only text for light theme', () => {
      mockResolvedTheme = 'light'
      render(<ThemeToggle />)

      expect(screen.getByText('Switch to dark mode')).toHaveClass('sr-only')
    })

    it('has sr-only text for dark theme', () => {
      mockResolvedTheme = 'dark'
      render(<ThemeToggle />)

      expect(screen.getByText('Switch to light mode')).toHaveClass('sr-only')
    })

    it('is keyboard accessible', async () => {
      const user = userEvent.setup()
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      await user.tab()

      expect(button).toHaveFocus()
    })

    it('can be activated with Enter key', async () => {
      const user = userEvent.setup()
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      button.focus()
      await user.keyboard('{Enter}')

      expect(mockToggleTheme).toHaveBeenCalledTimes(1)
    })

    it('can be activated with Space key', async () => {
      const user = userEvent.setup()
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      button.focus()
      await user.keyboard(' ')

      expect(mockToggleTheme).toHaveBeenCalledTimes(1)
    })
  })

  describe('Real-world use cases', () => {
    it('renders in main navigation header', () => {
      mockResolvedTheme = 'light'
      render(
        <header className="flex items-center justify-between p-4">
          <div>EFIR Budget Planning</div>
          <ThemeToggle />
        </header>
      )

      expect(screen.getByText('EFIR Budget Planning')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /switch to dark mode/i })).toBeInTheDocument()
    })

    it('allows switching theme while viewing budget data', async () => {
      mockResolvedTheme = 'light'
      const user = userEvent.setup()

      render(
        <div>
          <ThemeToggle />
          <div className="p-4">
            <h2>Budget 2025-2026</h2>
            <p>Total: 2,500,000 SAR</p>
          </div>
        </div>
      )

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      await user.click(button)

      expect(mockToggleTheme).toHaveBeenCalledTimes(1)
      expect(screen.getByText('Budget 2025-2026')).toBeInTheDocument()
    })

    it('works in sidebar', () => {
      mockResolvedTheme = 'dark'
      render(
        <aside className="w-64 border-r">
          <nav className="p-4">
            <ul>
              <li>Dashboard</li>
              <li>Planning</li>
              <li>Analysis</li>
            </ul>
          </nav>
          <div className="p-4">
            <ThemeToggle />
          </div>
        </aside>
      )

      expect(screen.getByRole('button', { name: /switch to light mode/i })).toBeInTheDocument()
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    it('calls toggleTheme when clicked in navigation', async () => {
      mockResolvedTheme = 'dark'
      const user = userEvent.setup()

      render(
        <div>
          <ThemeToggle />
          <nav>
            <a href="/planning/enrollment">Enrollment</a>
            <a href="/planning/dhg">DHG</a>
          </nav>
        </div>
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(mockToggleTheme).toHaveBeenCalledTimes(1)
    })
  })

  describe('Theme states', () => {
    it('handles system theme preference', () => {
      mockTheme = 'system'
      mockResolvedTheme = 'light'

      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })
  })

  describe('Icon transitions', () => {
    it('Sun icon has transition and rotation classes', () => {
      mockResolvedTheme = 'dark'
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      const sunIcon = button.querySelector('svg.lucide-sun')
      const classes = sunIcon?.getAttribute('class') || ''
      expect(classes).toMatch(/transition-transform/)
      expect(classes).toMatch(/hover:rotate-45/)
    })

    it('Moon icon has transition and rotation classes', () => {
      mockResolvedTheme = 'light'
      render(<ThemeToggle />)

      const button = screen.getByRole('button')
      const moonIcon = button.querySelector('svg.lucide-moon')
      const classes = moonIcon?.getAttribute('class') || ''
      expect(classes).toMatch(/transition-transform/)
      expect(classes).toMatch(/hover:-rotate-12/)
    })
  })
})
