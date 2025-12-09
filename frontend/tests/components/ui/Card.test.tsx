import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'

describe('Card', () => {
  it('renders basic card', () => {
    render(<Card data-testid="card">Card content</Card>)

    const card = screen.getByTestId('card')
    expect(card).toBeInTheDocument()
    expect(card.tagName).toBe('DIV')
  })

  it('has correct default styling', () => {
    render(<Card data-testid="card">Content</Card>)

    const card = screen.getByTestId('card')
    expect(card.className).toMatch(/rounded-xl/)
    expect(card.className).toMatch(/border/)
    expect(card.className).toMatch(/bg-white/)
    expect(card.className).toMatch(/shadow-luxe-card/)
  })

  it('applies custom className', () => {
    render(
      <Card className="custom-card" data-testid="card">
        Content
      </Card>
    )

    const card = screen.getByTestId('card')
    expect(card.className).toMatch(/custom-card/)
    expect(card.className).toMatch(/rounded-xl/) // Still has default classes
  })

  it('renders children content', () => {
    render(<Card>Test content</Card>)

    expect(screen.getByText('Test content')).toBeInTheDocument()
  })
})

describe('CardHeader', () => {
  it('renders card header', () => {
    render(<CardHeader data-testid="header">Header</CardHeader>)

    const header = screen.getByTestId('header')
    expect(header).toBeInTheDocument()
  })

  it('has correct default styling', () => {
    render(<CardHeader data-testid="header">Header</CardHeader>)

    const header = screen.getByTestId('header')
    expect(header.className).toMatch(/flex/)
    expect(header.className).toMatch(/flex-col/)
    expect(header.className).toMatch(/space-y-1\.5/)
    expect(header.className).toMatch(/px-5/)
    expect(header.className).toMatch(/py-4/)
    expect(header.className).toMatch(/border-b/)
  })

  it('applies custom className', () => {
    render(
      <CardHeader className="custom-header" data-testid="header">
        Header
      </CardHeader>
    )

    const header = screen.getByTestId('header')
    expect(header.className).toMatch(/custom-header/)
  })
})

describe('CardTitle', () => {
  it('renders as h3 element', () => {
    render(<CardTitle>Card Title</CardTitle>)

    const title = screen.getByText('Card Title')
    expect(title.tagName).toBe('H3')
  })

  it('has correct default styling', () => {
    render(<CardTitle data-testid="title">Title</CardTitle>)

    const title = screen.getByTestId('title')
    expect(title.className).toMatch(/text-lg/)
    expect(title.className).toMatch(/font-serif/)
    expect(title.className).toMatch(/font-semibold/)
    expect(title.className).toMatch(/leading-none/)
    expect(title.className).toMatch(/tracking-tight/)
    expect(title.className).toMatch(/text-brown-900/)
  })

  it('applies custom className', () => {
    render(
      <CardTitle className="text-3xl" data-testid="title">
        Title
      </CardTitle>
    )

    const title = screen.getByTestId('title')
    expect(title.className).toMatch(/text-3xl/)
  })
})

describe('CardDescription', () => {
  it('renders as p element', () => {
    render(<CardDescription>Description text</CardDescription>)

    const description = screen.getByText('Description text')
    expect(description.tagName).toBe('P')
  })

  it('has correct default styling', () => {
    render(<CardDescription data-testid="description">Description</CardDescription>)

    const description = screen.getByTestId('description')
    expect(description.className).toMatch(/text-sm/)
    expect(description.className).toMatch(/text-twilight-700/)
  })

  it('applies custom className', () => {
    render(
      <CardDescription className="custom-desc" data-testid="description">
        Desc
      </CardDescription>
    )

    const description = screen.getByTestId('description')
    expect(description.className).toMatch(/custom-desc/)
  })
})

describe('CardContent', () => {
  it('renders card content', () => {
    render(<CardContent>Main content</CardContent>)

    expect(screen.getByText('Main content')).toBeInTheDocument()
  })

  it('has correct default styling', () => {
    render(<CardContent data-testid="content">Content</CardContent>)

    const content = screen.getByTestId('content')
    expect(content.className).toMatch(/p-5/)
    expect(content.className).toMatch(/card-content/)
  })

  it('applies custom className', () => {
    render(
      <CardContent className="custom-content" data-testid="content">
        Content
      </CardContent>
    )

    const content = screen.getByTestId('content')
    expect(content.className).toMatch(/custom-content/)
  })
})

describe('CardFooter', () => {
  it('renders card footer', () => {
    render(<CardFooter>Footer content</CardFooter>)

    expect(screen.getByText('Footer content')).toBeInTheDocument()
  })

  it('has correct default styling', () => {
    render(<CardFooter data-testid="footer">Footer</CardFooter>)

    const footer = screen.getByTestId('footer')
    expect(footer.className).toMatch(/flex/)
    expect(footer.className).toMatch(/items-center/)
    expect(footer.className).toMatch(/px-5/)
    expect(footer.className).toMatch(/py-4/)
    expect(footer.className).toMatch(/border-t/)
  })

  it('applies custom className', () => {
    render(
      <CardFooter className="justify-end" data-testid="footer">
        Footer
      </CardFooter>
    )

    const footer = screen.getByTestId('footer')
    expect(footer.className).toMatch(/justify-end/)
  })
})

describe('Card composition', () => {
  it('renders complete card with all parts', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Budget Summary</CardTitle>
          <CardDescription>Overview of budget performance</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Total Budget: 2.5M SAR</p>
        </CardContent>
        <CardFooter>
          <button>View Details</button>
        </CardFooter>
      </Card>
    )

    expect(screen.getByText('Budget Summary')).toBeInTheDocument()
    expect(screen.getByText('Overview of budget performance')).toBeInTheDocument()
    expect(screen.getByText('Total Budget: 2.5M SAR')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /view details/i })).toBeInTheDocument()
  })

  it('renders card with header and content only', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Enrollment Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p>1,800 students</p>
        </CardContent>
      </Card>
    )

    expect(screen.getByText('Enrollment Data')).toBeInTheDocument()
    expect(screen.getByText('1,800 students')).toBeInTheDocument()
  })

  it('renders simple card with content only', () => {
    render(
      <Card>
        <CardContent>
          <p>Simple card content</p>
        </CardContent>
      </Card>
    )

    expect(screen.getByText('Simple card content')).toBeInTheDocument()
  })

  it('renders card with multiple content sections', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>DHG Workforce Planning</CardTitle>
          <CardDescription>Teacher allocation by subject</CardDescription>
        </CardHeader>
        <CardContent>
          <div>Mathematics: 6 FTE</div>
          <div>Sciences: 4 FTE</div>
          <div>Languages: 5 FTE</div>
        </CardContent>
        <CardFooter>
          <span>Total: 15 FTE</span>
        </CardFooter>
      </Card>
    )

    expect(screen.getByText('DHG Workforce Planning')).toBeInTheDocument()
    expect(screen.getByText('Teacher allocation by subject')).toBeInTheDocument()
    expect(screen.getByText('Mathematics: 6 FTE')).toBeInTheDocument()
    expect(screen.getByText('Sciences: 4 FTE')).toBeInTheDocument()
    expect(screen.getByText('Languages: 5 FTE')).toBeInTheDocument()
    expect(screen.getByText('Total: 15 FTE')).toBeInTheDocument()
  })
})

describe('Real-world use cases', () => {
  it('renders KPI card', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>H/E Ratio</CardTitle>
          <CardDescription>Hours per Student</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold">1.25</p>
        </CardContent>
        <CardFooter>
          <span className="text-green-600">+5% vs target</span>
        </CardFooter>
      </Card>
    )

    expect(screen.getByText('H/E Ratio')).toBeInTheDocument()
    expect(screen.getByText('1.25')).toBeInTheDocument()
    expect(screen.getByText('+5% vs target')).toBeInTheDocument()
  })

  it('renders budget version card', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Budget Version 2025-2026</CardTitle>
          <CardDescription>Status: Approved</CardDescription>
        </CardHeader>
        <CardContent>
          <div>Revenue: 15.2M SAR</div>
          <div>Expenses: 14.8M SAR</div>
          <div>Surplus: 0.4M SAR</div>
        </CardContent>
      </Card>
    )

    expect(screen.getByText('Budget Version 2025-2026')).toBeInTheDocument()
    expect(screen.getByText('Status: Approved')).toBeInTheDocument()
    expect(screen.getByText('Revenue: 15.2M SAR')).toBeInTheDocument()
  })

  it('renders dashboard summary card', () => {
    render(
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle>Total Students</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl">1,800</p>
        </CardContent>
      </Card>
    )

    expect(screen.getByText('Total Students')).toBeInTheDocument()
    expect(screen.getByText('1,800')).toBeInTheDocument()
  })
})

describe('Accessibility', () => {
  it('supports ARIA attributes', () => {
    render(
      <Card aria-label="Budget summary card" role="article">
        <CardContent>Content</CardContent>
      </Card>
    )

    const card = screen.getByRole('article', { name: /budget summary card/i })
    expect(card).toBeInTheDocument()
  })

  it('allows custom data attributes', () => {
    render(
      <Card data-testid="custom-card" data-module="planning">
        <CardContent>Content</CardContent>
      </Card>
    )

    const card = screen.getByTestId('custom-card')
    expect(card).toHaveAttribute('data-module', 'planning')
  })
})
