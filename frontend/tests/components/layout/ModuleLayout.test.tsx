/**
 * ModuleLayout Unit Tests
 *
 * Tests for the main layout composition component (Phase 2 UI Redesign).
 *
 * Test coverage:
 * - Rendering with all child components
 * - Provider wrapping
 * - Skip navigation links
 * - Main content area
 * - Settings tab auto-detection
 * - Description override
 * - Accessibility features
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ModuleLayout } from '@/components/layout/ModuleLayout'

// Mock TanStack Router
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => vi.fn(),
  useLocation: () => ({ pathname: '/enrollment/planning' }),
}))

// Mock ModuleContext
vi.mock('@/contexts/ModuleContext', () => ({
  ModuleProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useActiveModule: () => ({
    activeModule: 'enrollment',
    definition: {
      id: 'enrollment',
      label: 'Enrollment',
      basePath: '/enrollment',
      color: 'sage',
      subpages: [{ id: 'planning', label: 'Planning', path: '/enrollment/planning' }],
      hasSettings: true,
    },
    activeSubpage: null,
  }),
  useModule: () => ({
    activeModule: 'enrollment',
    activeModuleDefinition: {
      id: 'enrollment',
      label: 'Enrollment',
      basePath: '/enrollment',
      color: 'sage',
      subpages: [],
      hasSettings: true,
    },
    isModuleActive: vi.fn(),
    getModuleColors: () => ({ bg: 'bg-sage-500', text: 'text-sage-600' }),
    allModules: ['enrollment'],
  }),
  useActiveSubpages: () => ({
    subpages: [{ id: 'planning', label: 'Planning', path: '/enrollment/planning' }],
    hasSubpages: true,
    moduleColor: 'sage',
    hasSettings: true,
  }),
  MODULE_COLORS: {
    sage: { bg: 'bg-sage-500', text: 'text-sage-600' },
    neutral: { bg: 'bg-text-tertiary', text: 'text-text-secondary' },
  },
  MODULES: {},
  ALL_MODULES: ['enrollment'],
}))

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { email: 'test@efir.edu.sa' },
    signOut: vi.fn(),
  }),
}))

// Mock child components to simplify testing - use full paths for vi.mock
vi.mock('@/components/layout/AppSidebar', () => ({
  AppSidebar: () => <aside data-testid="app-sidebar">AppSidebar</aside>,
}))

vi.mock('@/components/layout/ModuleHeader', () => ({
  ModuleHeader: () => <header data-testid="module-header">ModuleHeader</header>,
}))

vi.mock('@/components/layout/WorkflowTabs', () => ({
  WorkflowTabs: ({
    showSettingsTab,
    settingsPath,
  }: {
    showSettingsTab?: boolean
    settingsPath?: string
  }) => (
    <nav
      data-testid="workflow-tabs"
      data-settings={showSettingsTab}
      data-settings-path={settingsPath}
    >
      WorkflowTabs
    </nav>
  ),
}))

vi.mock('@/components/layout/TaskDescription', () => ({
  TaskDescription: ({ description }: { description?: string }) => (
    <div data-testid="task-description" data-description={description}>
      {description || 'Auto description'}
    </div>
  ),
}))

vi.mock('@/components/layout/MobileBottomNav', () => ({
  MobileBottomNav: () => <nav data-testid="mobile-bottom-nav">MobileBottomNav</nav>,
}))

// Mock CommandPalette
vi.mock('@/components/CommandPalette', () => ({
  CommandPalette: () => <div data-testid="command-palette">CommandPalette</div>,
}))

// Mock accessibility components
vi.mock('@/components/accessibility', () => ({
  SkipNavigation: ({ links }: { links: Array<{ id: string; label: string }> }) => (
    <div data-testid="skip-navigation">
      {links.map((link) => (
        <a key={link.id} href={`#${link.id}`}>
          {link.label}
        </a>
      ))}
    </div>
  ),
  SkipTarget: ({
    children,
    id,
    as: Component = 'div',
    ...props
  }: {
    children: React.ReactNode
    id: string
    as?: React.ElementType
  } & React.HTMLAttributes<HTMLElement>) => (
    <Component data-testid={`skip-target-${id}`} id={id} {...props}>
      {children}
    </Component>
  ),
  LiveRegionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useKeyboardShortcuts: () => ({
    KeyboardShortcutsHelp: <div data-testid="keyboard-shortcuts-help">Keyboard Help</div>,
  }),
  FocusVisibleStyles: () => null,
  ReducedMotionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  ReducedMotionStyles: () => null,
  HighContrastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  HighContrastStyles: () => null,
  RouteAnnouncer: () => <div data-testid="route-announcer" />,
  PatternStyles: () => null,
}))

// Mock GlobalVersionSelector
vi.mock('@/components/GlobalVersionSelector', () => ({
  GlobalVersionSelector: () => <div data-testid="version-selector">Version</div>,
}))

// Mock typography
vi.mock('@/styles/typography', () => ({
  getTypographyClasses: () => 'text-module-title',
  LAYOUT: { sidebarAnimationDuration: '200ms' },
}))

describe('ModuleLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders children content', () => {
      render(
        <ModuleLayout>
          <div data-testid="test-content">Test Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('test-content')).toBeInTheDocument()
    })

    it('renders AppSidebar component', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('app-sidebar')).toBeInTheDocument()
    })

    it('renders ModuleHeader component', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('module-header')).toBeInTheDocument()
    })

    it('renders WorkflowTabs component', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('workflow-tabs')).toBeInTheDocument()
    })

    it('renders TaskDescription component', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('task-description')).toBeInTheDocument()
    })

    it('renders MobileBottomNav component', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('mobile-bottom-nav')).toBeInTheDocument()
    })

    it('renders CommandPalette component', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('command-palette')).toBeInTheDocument()
    })
  })

  describe('Skip Navigation', () => {
    it('renders skip navigation component', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('skip-navigation')).toBeInTheDocument()
    })

    it('skip navigation has main content link', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByText('Skip to main content')).toBeInTheDocument()
    })

    it('skip navigation has module navigation link', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByText('Skip to module navigation')).toBeInTheDocument()
    })

    it('skip navigation has data grid link', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByText('Skip to data grid')).toBeInTheDocument()
    })
  })

  describe('Skip Targets', () => {
    it('renders main-content skip target', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('skip-target-main-content')).toBeInTheDocument()
    })

    it('renders module-navigation skip target', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('skip-target-module-navigation')).toBeInTheDocument()
    })

    it('renders data-grid skip target', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('skip-target-data-grid')).toBeInTheDocument()
    })
  })

  describe('Settings Tab Auto-Detection', () => {
    it('passes showSettingsTab to WorkflowTabs for enrollment module', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      const workflowTabs = screen.getByTestId('workflow-tabs')
      expect(workflowTabs).toHaveAttribute('data-settings', 'true')
    })

    it('passes correct settingsPath to WorkflowTabs', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      const workflowTabs = screen.getByTestId('workflow-tabs')
      expect(workflowTabs).toHaveAttribute('data-settings-path', '/enrollment/settings')
    })

    it('allows override of showSettingsTab prop', () => {
      render(
        <ModuleLayout showSettingsTab={false}>
          <div>Content</div>
        </ModuleLayout>
      )

      const workflowTabs = screen.getByTestId('workflow-tabs')
      expect(workflowTabs).toHaveAttribute('data-settings', 'false')
    })

    it('allows override of settingsPath prop', () => {
      render(
        <ModuleLayout settingsPath="/custom/settings">
          <div>Content</div>
        </ModuleLayout>
      )

      const workflowTabs = screen.getByTestId('workflow-tabs')
      expect(workflowTabs).toHaveAttribute('data-settings-path', '/custom/settings')
    })
  })

  describe('Description Override', () => {
    it('passes description prop to TaskDescription', () => {
      render(
        <ModuleLayout description="Custom task description">
          <div>Content</div>
        </ModuleLayout>
      )

      const taskDescription = screen.getByTestId('task-description')
      expect(taskDescription).toHaveAttribute('data-description', 'Custom task description')
    })
  })

  describe('Accessibility Features', () => {
    it('renders keyboard shortcuts help', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('keyboard-shortcuts-help')).toBeInTheDocument()
    })

    it('renders route announcer for screen readers', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      expect(screen.getByTestId('route-announcer')).toBeInTheDocument()
    })
  })

  describe('Layout Structure', () => {
    it('has min-h-screen on main container', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      const container = screen.getByTestId('skip-target-main-content').parentElement
      expect(container?.className).toMatch(/min-h-screen/)
    })

    it('has sidebar margin offset on content area', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      const contentArea = screen.getByTestId('skip-target-main-content').parentElement
      expect(contentArea?.className).toMatch(/md:ml-\[var\(--sidebar-width-collapsed\)\]/)
    })

    it('main content has correct role', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      const main = screen.getByTestId('skip-target-main-content')
      expect(main).toHaveAttribute('role', 'main')
    })

    it('main content has aria-label', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      const main = screen.getByTestId('skip-target-main-content')
      expect(main).toHaveAttribute('aria-label', 'Main content')
    })
  })

  describe('Mobile Support', () => {
    it('has bottom padding for mobile nav', () => {
      render(
        <ModuleLayout>
          <div>Content</div>
        </ModuleLayout>
      )

      const main = screen.getByTestId('skip-target-main-content')
      expect(main.className).toMatch(/pb-20/)
      expect(main.className).toMatch(/md:pb-0/)
    })
  })

  describe('Complex Children', () => {
    it('renders nested children correctly', () => {
      render(
        <ModuleLayout>
          <div>
            <h2>Section Title</h2>
            <p>Section content</p>
            <table>
              <tbody>
                <tr>
                  <td>Data</td>
                </tr>
              </tbody>
            </table>
          </div>
        </ModuleLayout>
      )

      expect(screen.getByText('Section Title')).toBeInTheDocument()
      expect(screen.getByText('Section content')).toBeInTheDocument()
      expect(screen.getByText('Data')).toBeInTheDocument()
    })
  })
})
