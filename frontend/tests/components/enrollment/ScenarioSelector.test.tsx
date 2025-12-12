/**
 * Tests for ScenarioSelector component.
 *
 * This component displays scenario selection cards for enrollment projections.
 * School directors can choose between Conservative, Base Case, and Optimistic
 * scenarios, each with human-friendly explanations of assumptions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ScenarioSelector } from '@/components/enrollment/ScenarioSelector'
import type { EnrollmentScenario } from '@/types/enrollmentProjection'

// Helper to create mock scenarios
const createMockScenarios = (
  overrides: Partial<EnrollmentScenario>[] = []
): EnrollmentScenario[] => {
  const baseScenarios: EnrollmentScenario[] = [
    {
      id: 'scenario-worst',
      code: 'worst_case',
      name_en: 'Conservative',
      name_fr: 'Conservateur',
      description_en: 'Prepare for challenges',
      description_fr: 'Se préparer aux défis',
      ps_entry: 45,
      entry_growth_rate: -0.02,
      default_retention: 0.93,
      terminal_retention: 0.9,
      lateral_multiplier: 0.3,
      color_code: '#FF6B6B',
      sort_order: 1,
    },
    {
      id: 'scenario-base',
      code: 'base',
      name_en: 'Base Case',
      name_fr: 'Cas de base',
      description_en: 'Expected typical year',
      description_fr: 'Année typique attendue',
      ps_entry: 50,
      entry_growth_rate: 0.0,
      default_retention: 0.96,
      terminal_retention: 0.95,
      lateral_multiplier: 1.0,
      color_code: '#4CAF50',
      sort_order: 2,
    },
    {
      id: 'scenario-best',
      code: 'best_case',
      name_en: 'Optimistic',
      name_fr: 'Optimiste',
      description_en: 'Growth opportunity',
      description_fr: 'Opportunité de croissance',
      ps_entry: 55,
      entry_growth_rate: 0.02,
      default_retention: 0.98,
      terminal_retention: 0.97,
      lateral_multiplier: 1.5,
      color_code: '#FFD700',
      sort_order: 3,
    },
  ]

  return baseScenarios.map((scenario, index) => ({
    ...scenario,
    ...(overrides[index] || {}),
  }))
}

describe('ScenarioSelector', () => {
  let mockOnSelect: ReturnType<typeof vi.fn>
  let scenarios: EnrollmentScenario[]

  beforeEach(() => {
    mockOnSelect = vi.fn()
    scenarios = createMockScenarios()
  })

  describe('rendering', () => {
    it('renders section header', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      expect(screen.getByText('Select Your Scenario')).toBeInTheDocument()
      expect(
        screen.getByText(/Choose the projection scenario that best matches/)
      ).toBeInTheDocument()
    })

    it('renders all three scenario cards', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      expect(screen.getByText('Conservative')).toBeInTheDocument()
      expect(screen.getByText('Base Case')).toBeInTheDocument()
      expect(screen.getByText('Optimistic')).toBeInTheDocument()
    })

    it('renders scenario subtitles', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      expect(screen.getByText('Prepare for challenges')).toBeInTheDocument()
      expect(screen.getByText('Expected typical year')).toBeInTheDocument()
      expect(screen.getByText('Growth opportunity')).toBeInTheDocument()
    })

    it('renders "Most Common" badge on base case', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      expect(screen.getByText('Most Common')).toBeInTheDocument()
    })
  })

  describe('scenario content', () => {
    it('displays "This Scenario Assumes" section', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      // Should have "This Scenario Assumes" headers for each scenario
      const headers = screen.getAllByText('This Scenario Assumes')
      expect(headers).toHaveLength(3)
    })

    it('displays "Use This When" section', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      // Should have "Use This When" headers for each scenario
      const headers = screen.getAllByText('Use This When')
      expect(headers).toHaveLength(3)
    })

    it('displays conservative assumptions', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      expect(screen.getByText(/Fewer new preschool students than average/)).toBeInTheDocument()
      expect(
        screen.getByText(/Lower student retention \(more families leaving\)/)
      ).toBeInTheDocument()
    })

    it('displays base case assumptions', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      expect(screen.getByText(/New enrollments matching historical average/)).toBeInTheDocument()
      expect(screen.getByText(/Typical retention rates \(most students stay\)/)).toBeInTheDocument()
    })

    it('displays optimistic assumptions', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      expect(screen.getByText(/More new enrollments than average/)).toBeInTheDocument()
      expect(screen.getByText(/Higher retention \(fewer families leaving\)/)).toBeInTheDocument()
    })
  })

  describe('selection behavior', () => {
    it('calls onSelect when scenario card is clicked', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      // Click on base case card
      const baseCard = screen.getByText('Base Case').closest('div[class*="cursor-pointer"]')
      if (baseCard) {
        fireEvent.click(baseCard)
        expect(mockOnSelect).toHaveBeenCalledWith('scenario-base')
      }
    })

    it('calls onSelect when button is clicked', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      // Click the first "Select This Scenario" button
      const selectButtons = screen.getAllByRole('button', {
        name: /Select This Scenario/i,
      })
      fireEvent.click(selectButtons[0])

      expect(mockOnSelect).toHaveBeenCalledWith('scenario-worst')
    })

    it('shows checkmark when scenario is selected', () => {
      render(
        <ScenarioSelector
          scenarios={scenarios}
          selectedScenarioId="scenario-base"
          onSelect={mockOnSelect}
        />
      )

      // Selected button should show "Selected"
      expect(screen.getByRole('button', { name: /Selected/i })).toBeInTheDocument()
    })

    it('hides "Most Common" badge when base case is selected', () => {
      render(
        <ScenarioSelector
          scenarios={scenarios}
          selectedScenarioId="scenario-base"
          onSelect={mockOnSelect}
        />
      )

      // Badge should be hidden when selected (checkmark shown instead)
      // The badge only shows when not selected
      expect(screen.queryByText('Most Common')).not.toBeInTheDocument()
    })

    it('applies selected styling to chosen scenario', () => {
      const { container } = render(
        <ScenarioSelector
          scenarios={scenarios}
          selectedScenarioId="scenario-base"
          onSelect={mockOnSelect}
        />
      )

      // Should have border-sage class on selected card
      const selectedCard = container.querySelector('.border-sage')
      expect(selectedCard).toBeInTheDocument()
    })
  })

  describe('disabled state', () => {
    it('does not call onSelect when disabled', () => {
      render(
        <ScenarioSelector
          scenarios={scenarios}
          selectedScenarioId={null}
          onSelect={mockOnSelect}
          disabled={true}
        />
      )

      // Try to click the button
      const selectButtons = screen.getAllByRole('button', {
        name: /Select This Scenario/i,
      })
      fireEvent.click(selectButtons[0])

      expect(mockOnSelect).not.toHaveBeenCalled()
    })

    it('disables all buttons when disabled prop is true', () => {
      render(
        <ScenarioSelector
          scenarios={scenarios}
          selectedScenarioId={null}
          onSelect={mockOnSelect}
          disabled={true}
        />
      )

      const selectButtons = screen.getAllByRole('button', {
        name: /Select This Scenario/i,
      })
      selectButtons.forEach((button) => {
        expect(button).toBeDisabled()
      })
    })
  })

  describe('technical parameters (details)', () => {
    it('renders technical parameters in details element', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      // Check for the summary elements
      const detailsSummaries = screen.getAllByText('View technical parameters')
      expect(detailsSummaries).toHaveLength(3)
    })

    it('displays PS Entry value for base scenario', () => {
      render(
        <ScenarioSelector scenarios={scenarios} selectedScenarioId={null} onSelect={mockOnSelect} />
      )

      // PS Entry should show the value from scenario
      expect(screen.getByText('50')).toBeInTheDocument()
    })
  })

  describe('fallback for unknown scenario codes', () => {
    it('handles unknown scenario code gracefully', () => {
      const unknownScenario: EnrollmentScenario = {
        id: 'scenario-custom',
        code: 'custom' as EnrollmentScenario['code'], // Test unknown code handling
        name_en: 'Custom Scenario',
        name_fr: 'Scénario personnalisé',
        description_en: 'Custom description',
        description_fr: 'Description personnalisée',
        ps_entry: 48,
        entry_growth_rate: 0.01,
        default_retention: 0.95,
        terminal_retention: 0.93,
        lateral_multiplier: 0.8,
        color_code: '#888888',
        sort_order: 4,
      }

      render(
        <ScenarioSelector
          scenarios={[unknownScenario]}
          selectedScenarioId={null}
          onSelect={mockOnSelect}
        />
      )

      // Should fall back to name_en
      expect(screen.getByText('Custom Scenario')).toBeInTheDocument()
    })
  })
})
