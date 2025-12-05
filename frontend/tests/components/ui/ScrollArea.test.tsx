import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ScrollArea } from '@/components/ui/scroll-area'

describe('ScrollArea', () => {
  it('renders children content', () => {
    render(
      <ScrollArea>
        <div>Scrollable content</div>
      </ScrollArea>
    )

    expect(screen.getByText('Scrollable content')).toBeInTheDocument()
  })

  describe('Basic functionality', () => {
    it('renders viewport with children', () => {
      render(
        <ScrollArea data-testid="scroll-area">
          <p>Content inside viewport</p>
        </ScrollArea>
      )

      expect(screen.getByText('Content inside viewport')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <ScrollArea className="custom-scroll" data-testid="scroll-area">
          <div>Content</div>
        </ScrollArea>
      )

      const scrollArea = screen.getByTestId('scroll-area')
      expect(scrollArea.className).toMatch(/custom-scroll/)
    })

    it('renders with custom height', () => {
      render(
        <ScrollArea className="h-96" data-testid="scroll-area">
          <div>Content</div>
        </ScrollArea>
      )

      const scrollArea = screen.getByTestId('scroll-area')
      expect(scrollArea.className).toMatch(/h-96/)
    })
  })

  describe('Scrollbar orientation', () => {
    it('renders vertical scrollbar by default', () => {
      const { container } = render(
        <ScrollArea>
          <div style={{ height: '1000px' }}>Tall content</div>
        </ScrollArea>
      )

      const scrollbar = container.querySelector('[data-orientation="vertical"]')
      expect(scrollbar).toBeInTheDocument()
    })

    it('supports horizontal scrollbar', () => {
      const { container } = render(
        <ScrollArea orientation="horizontal">
          <div style={{ width: '2000px' }}>Wide content</div>
        </ScrollArea>
      )

      const scrollbar = container.querySelector('[data-orientation="horizontal"]')
      expect(scrollbar).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('has default styling classes', () => {
      render(
        <ScrollArea data-testid="scroll-area">
          <div>Content</div>
        </ScrollArea>
      )

      const scrollArea = screen.getByTestId('scroll-area')
      expect(scrollArea.className).toMatch(/relative/)
      expect(scrollArea.className).toMatch(/overflow-hidden/)
    })

    it('scrollbar has transition classes', () => {
      const { container } = render(
        <ScrollArea>
          <div style={{ height: '1000px' }}>Content</div>
        </ScrollArea>
      )

      const scrollbar = container.querySelector('[data-radix-scroll-area-scrollbar]')
      const classes = scrollbar?.getAttribute('class') || ''
      expect(classes).toMatch(/transition-colors/)
    })
  })

  describe('Real-world use cases', () => {
    it('renders budget version list', () => {
      render(
        <ScrollArea className="h-[400px]" data-testid="version-list">
          <div>
            <p>2025-2026 Working Version</p>
            <p>2025-2026 Submitted</p>
            <p>2025-2026 Approved</p>
            <p>2024-2025 Approved</p>
            <p>2024-2025 Forecast</p>
          </div>
        </ScrollArea>
      )

      expect(screen.getByText('2025-2026 Working Version')).toBeInTheDocument()
      expect(screen.getByText('2024-2025 Forecast')).toBeInTheDocument()
    })

    it('renders enrollment data table', () => {
      render(
        <ScrollArea className="h-[600px] w-full">
          <table>
            <thead>
              <tr>
                <th>Level</th>
                <th>Students</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>PS</td>
                <td>45</td>
              </tr>
              <tr>
                <td>MS</td>
                <td>50</td>
              </tr>
              <tr>
                <td>GS</td>
                <td>52</td>
              </tr>
            </tbody>
          </table>
        </ScrollArea>
      )

      expect(screen.getByText('PS')).toBeInTheDocument()
      expect(screen.getByText('45')).toBeInTheDocument()
    })

    it('renders DHG allocation details', () => {
      render(
        <ScrollArea className="h-[500px]">
          <div className="space-y-2 p-4">
            <h3>DHG Allocation - Mathématiques</h3>
            <p>6ème: 4.5h × 6 classes = 27h</p>
            <p>5ème: 3.5h × 6 classes = 21h</p>
            <p>4ème: 3.5h × 5 classes = 17.5h</p>
            <p>3ème: 3.5h × 4 classes = 14h</p>
            <p>Total: 79.5 hours/week</p>
            <p>Required FTE: 4.42 teachers</p>
          </div>
        </ScrollArea>
      )

      expect(screen.getByText('DHG Allocation - Mathématiques')).toBeInTheDocument()
      expect(screen.getByText('Total: 79.5 hours/week')).toBeInTheDocument()
    })

    it('renders financial statement with long account list', () => {
      render(
        <ScrollArea className="h-[800px]">
          <div>
            <h3>Plan Comptable Général (PCG)</h3>
            <p>64110 - Teaching Salaries AEFE</p>
            <p>64120 - Teaching Salaries Local</p>
            <p>64210 - Administrative Salaries</p>
            <p>64300 - Social Contributions</p>
            <p>70110 - Tuition T1 French</p>
            <p>70120 - Tuition T2 French</p>
            <p>70210 - Enrollment Fees (DAI)</p>
          </div>
        </ScrollArea>
      )

      expect(screen.getByText('Plan Comptable Général (PCG)')).toBeInTheDocument()
      expect(screen.getByText('64110 - Teaching Salaries AEFE')).toBeInTheDocument()
    })

    it('renders KPI dashboard with multiple metrics', () => {
      render(
        <ScrollArea className="h-[600px] w-full">
          <div className="grid grid-cols-3 gap-4 p-4">
            <div>H/E Ratio: 1.52</div>
            <div>E/D Ratio: 23.5</div>
            <div>Operating Margin: 12.5%</div>
            <div>DHG Coverage: 95%</div>
            <div>Enrollment Rate: 98%</div>
            <div>Cost per Student: 45,300 SAR</div>
          </div>
        </ScrollArea>
      )

      expect(screen.getByText('H/E Ratio: 1.52')).toBeInTheDocument()
      expect(screen.getByText('Operating Margin: 12.5%')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('supports ARIA attributes', () => {
      render(
        <ScrollArea aria-label="Budget versions list">
          <div>Content</div>
        </ScrollArea>
      )

      const scrollArea = screen.getByLabelText('Budget versions list')
      expect(scrollArea).toBeInTheDocument()
    })

    it('scrollbar has proper orientation attribute', () => {
      const { container } = render(
        <ScrollArea orientation="vertical">
          <div style={{ height: '1000px' }}>Content</div>
        </ScrollArea>
      )

      const scrollbar = container.querySelector('[data-orientation="vertical"]')
      expect(scrollbar).toHaveAttribute('data-orientation', 'vertical')
    })
  })

  describe('Content overflow', () => {
    it('handles long text content', () => {
      const longText = 'Lorem ipsum '.repeat(100)

      render(
        <ScrollArea className="h-[200px]">
          <p>{longText}</p>
        </ScrollArea>
      )

      expect(screen.getByText(longText, { exact: false })).toBeInTheDocument()
    })

    it('handles wide content with horizontal scroll', () => {
      render(
        <ScrollArea className="w-[400px]" orientation="horizontal">
          <div style={{ width: '1200px' }}>
            <p>Very wide content that requires horizontal scrolling</p>
          </div>
        </ScrollArea>
      )

      expect(
        screen.getByText('Very wide content that requires horizontal scrolling')
      ).toBeInTheDocument()
    })

    it('handles both vertical and horizontal overflow', () => {
      render(
        <ScrollArea className="h-[300px] w-[400px]">
          <div style={{ height: '1000px', width: '1200px' }}>
            <p>Content that overflows in both directions</p>
          </div>
        </ScrollArea>
      )

      expect(screen.getByText('Content that overflows in both directions')).toBeInTheDocument()
    })
  })
})
