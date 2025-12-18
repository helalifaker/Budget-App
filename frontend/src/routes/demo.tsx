/**
 * Demo Page - "Sahara Luxe" Design System Showcase
 *
 * A comprehensive demonstration of the EFIR Budget Planning application's
 * premium design system, featuring:
 * - Hero landing section with animated gradients
 * - Color palette showcase
 * - Typography scale
 * - Component gallery
 * - Feature highlights
 * - Live KPI preview
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import {
  Sparkles,
  TrendingUp,
  Users,
  DollarSign,
  ArrowRight,
  Globe,
  Zap,
  Shield,
} from 'lucide-react'

export const Route = createFileRoute('/demo')({
  component: DemoPage,
})

function DemoPage() {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <HeroSection />

      {/* Color Palette */}
      <ColorPaletteSection />

      {/* Typography */}
      <TypographySection />

      {/* Components Gallery */}
      <ComponentsSection />

      {/* Feature Highlights */}
      <FeaturesSection />

      {/* Live KPI Preview */}
      <KPIPreviewSection />
    </div>
  )
}

// ============================================================================
// Hero Section
// ============================================================================

function HeroSection() {
  return (
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-cream-50 via-sand-100 to-gold-50 p-12">
      {/* Animated background shapes */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-gold-200/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-subtle/40 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative text-center space-y-6">
        {/* Badge */}
        <Badge className="bg-gold-100 text-gold-800 border-gold-200 px-3 py-1">
          <Sparkles className="w-3 h-3 mr-1" />
          Sahara Luxe Design System
        </Badge>

        {/* Main headline */}
        <h1 className="font-display text-5xl md:text-6xl font-bold text-text-primary tracking-tight">
          Budget Planning
          <span className="block text-gold-600">Reimagined</span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg text-text-secondary max-w-2xl mx-auto">
          A premium, enterprise-grade financial planning experience with thoughtful design,
          intuitive navigation, and real-time insights.
        </p>

        {/* Animated metrics */}
        <div className="flex justify-center gap-8 mt-8">
          <MetricPill icon={DollarSign} value="52M" label="Revenue" />
          <MetricPill icon={Users} value="42.5" label="FTE" />
          <MetricPill icon={TrendingUp} value="+5.8%" label="Margin" />
        </div>

        {/* CTA */}
        <div className="pt-4">
          <Button
            size="lg"
            className={cn(
              'bg-gradient-to-r from-gold-500 to-gold-600',
              'hover:from-gold-600 hover:to-gold-700',
              'text-white font-semibold',
              'shadow-lg shadow-gold-200',
              'transition-all duration-300',
              'hover:scale-105 hover:shadow-xl'
            )}
          >
            Explore the Experience
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </section>
  )
}

function MetricPill({
  icon: Icon,
  value,
  label,
}: {
  icon: typeof DollarSign
  value: string
  label: string
}) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 px-4 py-2 rounded-full',
        'bg-white/80 backdrop-blur-sm',
        'border border-border-light',
        'shadow-sm'
      )}
    >
      <Icon className="w-4 h-4 text-gold-600" />
      <span className="font-mono font-bold text-text-primary">{value}</span>
      <span className="text-sm text-text-tertiary">{label}</span>
    </div>
  )
}

// ============================================================================
// Color Palette Section
// ============================================================================

function ColorPaletteSection() {
  const colorGroups = [
    {
      name: 'Gold (Primary Accent)',
      colors: [
        { name: 'gold-50', bg: 'bg-gold-50', hex: '#FFFBF0' },
        { name: 'gold-100', bg: 'bg-gold-100', hex: '#FFF4D6' },
        { name: 'gold-200', bg: 'bg-gold-200', hex: '#FFE8AD' },
        { name: 'gold-400', bg: 'bg-gold-400', hex: '#F5C842' },
        { name: 'gold-500', bg: 'bg-gold-500', hex: '#EDAD3E' },
        { name: 'gold-600', bg: 'bg-gold-600', hex: '#D4AF37' },
      ],
    },
    {
      name: 'Sand & Cream (Backgrounds)',
      colors: [
        { name: 'cream-50', bg: 'bg-cream-50', hex: '#FDFBF7' },
        { name: 'sand-50', bg: 'bg-subtle', hex: '#FBF8F3' },
        { name: 'sand-100', bg: 'bg-subtle', hex: '#F5EFE6' },
        { name: 'sand-200', bg: 'bg-subtle', hex: '#EBE3D6' },
        { name: 'sand-300', bg: 'bg-subtle', hex: '#D9CFC0' },
      ],
    },
    {
      name: 'Brown (Text & Headings)',
      colors: [
        { name: 'brown-700', bg: 'bg-brown-700', hex: '#5C4130' },
        { name: 'brown-800', bg: 'bg-brown-800', hex: '#4A3520' },
        { name: 'brown-900', bg: 'bg-brown-900', hex: '#3D2B20' },
      ],
    },
    {
      name: 'Twilight (Secondary Text)',
      colors: [
        { name: 'twilight-400', bg: 'bg-twilight-400', hex: '#9DB4C7' },
        { name: 'twilight-500', bg: 'bg-twilight-500', hex: '#8BA0B4' },
        { name: 'twilight-600', bg: 'bg-twilight-600', hex: '#7389A0' },
        { name: 'twilight-700', bg: 'bg-twilight-700', hex: '#61707F' },
      ],
    },
    {
      name: 'Status Colors',
      colors: [
        { name: 'sage-500', bg: 'bg-sage-500', hex: '#8B9D83', label: 'Success' },
        { name: 'terracotta-500', bg: 'bg-terracotta-500', hex: '#C75B39', label: 'Warning' },
        { name: 'mauve-500', bg: 'bg-mauve-500', hex: '#8B4C6F', label: 'Error' },
      ],
    },
  ]

  return (
    <section className="space-y-8">
      <div>
        <h2 className="font-display text-3xl font-bold text-text-primary">Color Palette</h2>
        <p className="text-text-secondary mt-2">
          A warm, premium palette inspired by luxury desert aesthetics
        </p>
      </div>

      <div className="space-y-6">
        {colorGroups.map((group) => (
          <div key={group.name} className="space-y-3">
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">
              {group.name}
            </h3>
            <div className="flex flex-wrap gap-3">
              {group.colors.map((color) => (
                <div key={color.name} className="group">
                  <div
                    className={cn(
                      color.bg,
                      'w-20 h-20 rounded-xl border border-border-light',
                      'shadow-sm group-hover:shadow-md transition-shadow'
                    )}
                  />
                  <p className="text-xs text-text-secondary mt-1 font-mono">{color.name}</p>
                  <p className="text-[10px] text-text-tertiary">{color.hex}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

// ============================================================================
// Typography Section
// ============================================================================

function TypographySection() {
  return (
    <section className="space-y-8">
      <div>
        <h2 className="font-display text-3xl font-bold text-text-primary">Typography</h2>
        <p className="text-text-secondary mt-2">
          Elegant type hierarchy with Playfair Display for headings and Inter for body
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Display Headings */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">
              Display Headings (Playfair Display)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="font-display text-4xl font-bold text-text-primary">Display XL</p>
            <p className="font-display text-3xl font-bold text-text-primary">Display LG</p>
            <p className="font-display text-2xl font-bold text-text-primary">Display MD</p>
            <p className="font-display text-xl font-semibold text-text-primary">Display SM</p>
          </CardContent>
        </Card>

        {/* Body Text */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">
              Body Text (Inter)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-lg text-text-primary">Large body text - 18px</p>
            <p className="text-base text-text-secondary">Regular body text - 16px</p>
            <p className="text-sm text-text-secondary">Small text - 14px</p>
            <p className="text-xs text-text-tertiary">Caption text - 12px</p>
          </CardContent>
        </Card>

        {/* Monospace Numbers */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">
              Monospace Numbers (Space Mono)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="font-mono text-2xl font-bold text-text-primary">SAR 8,247,500.00</p>
            <p className="font-mono text-xl text-text-primary">+12.5% YoY</p>
            <p className="font-mono text-lg text-text-secondary">FTE 42.50</p>
          </CardContent>
        </Card>

        {/* Font Weights */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">Font Weights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="font-light text-text-primary">Light (300)</p>
            <p className="font-normal text-text-primary">Regular (400)</p>
            <p className="font-medium text-text-primary">Medium (500)</p>
            <p className="font-semibold text-text-primary">Semibold (600)</p>
            <p className="font-bold text-text-primary">Bold (700)</p>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}

// ============================================================================
// Components Section
// ============================================================================

function ComponentsSection() {
  const [selectValue, setSelectValue] = useState('')

  return (
    <section className="space-y-8">
      <div>
        <h2 className="font-display text-3xl font-bold text-text-primary">Component Gallery</h2>
        <p className="text-text-secondary mt-2">
          Premium components with gold accents and warm interactions
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Buttons */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">Buttons</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full bg-gold-500 hover:bg-gold-600 text-white">
              Primary Action
            </Button>
            <Button variant="outline" className="w-full border-border-medium text-text-secondary">
              Secondary
            </Button>
            <Button variant="ghost" className="w-full text-text-secondary hover:bg-subtle">
              Ghost
            </Button>
            <Button variant="destructive" className="w-full">
              Destructive
            </Button>
          </CardContent>
        </Card>

        {/* Badges */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">Badges</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Badge variant="default">Default</Badge>
            <Badge variant="info">Info</Badge>
            <Badge variant="success">Success</Badge>
            <Badge variant="warning">Warning</Badge>
            <Badge className="bg-mauve-100 text-mauve-800 border-mauve-200">Error</Badge>
            <Badge className="bg-gold-100 text-gold-800 border-gold-200">Gold</Badge>
          </CardContent>
        </Card>

        {/* Form Inputs */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">Form Inputs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="demo-input" className="text-text-secondary">
                Text Input
              </Label>
              <Input
                id="demo-input"
                placeholder="Enter value..."
                className="mt-1 border-border-medium focus:border-gold-500 focus:ring-gold-500/20"
              />
            </div>
            <div>
              <Label className="text-text-secondary">Select</Label>
              <Select value={selectValue} onValueChange={setSelectValue}>
                <SelectTrigger className="mt-1 border-border-medium">
                  <SelectValue placeholder="Choose option..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="opt1">Option 1</SelectItem>
                  <SelectItem value="opt2">Option 2</SelectItem>
                  <SelectItem value="opt3">Option 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Cards */}
        <Card className="bg-white border-border-light hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="text-text-primary">Interactive Card</CardTitle>
            <CardDescription>With hover elevation effect</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-text-secondary">
              Cards lift on hover with a premium shadow effect.
            </p>
          </CardContent>
        </Card>

        {/* Status Badges */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">
              Budget Status Badges
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-secondary">Working</span>
              <Badge variant="info">Working</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-secondary">Submitted</span>
              <Badge variant="warning">Submitted</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-secondary">Approved</span>
              <Badge variant="success">Approved</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Loading States */}
        <Card className="bg-white border-border-light">
          <CardHeader>
            <CardTitle className="text-sm text-text-secondary font-normal">
              Loading States
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="h-4 bg-subtle rounded animate-pulse" />
            <div className="h-4 bg-subtle rounded animate-pulse w-3/4" />
            <div className="h-4 bg-subtle rounded animate-pulse w-1/2" />
            <div className="flex gap-2 mt-4">
              <div className="w-12 h-12 bg-subtle rounded-lg animate-pulse" />
              <div className="flex-1 space-y-2">
                <div className="h-3 bg-subtle rounded animate-pulse" />
                <div className="h-3 bg-subtle rounded animate-pulse w-2/3" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}

// ============================================================================
// Features Section
// ============================================================================

function FeaturesSection() {
  const features = [
    {
      icon: Globe,
      title: 'Global Context',
      description: 'Your version follows you everywhere. Select once, work seamlessly.',
      color: 'gold',
    },
    {
      icon: Zap,
      title: 'Smart Navigation',
      description: 'Press Cmd+K to instantly jump anywhere. Related information, one destination.',
      color: 'sage',
    },
    {
      icon: Shield,
      title: 'Real-time Insights',
      description: 'Live metrics at a glance. Know your numbers without switching screens.',
      color: 'twilight',
    },
  ]

  return (
    <section className="space-y-8">
      <div className="text-center">
        <h2 className="font-display text-3xl font-bold text-text-primary">Feature Highlights</h2>
        <p className="text-text-secondary mt-2">Designed for efficiency, built for delight</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {features.map((feature) => (
          <Card
            key={feature.title}
            className={cn(
              'bg-white border-border-light',
              'hover:shadow-xl hover:-translate-y-1',
              'transition-all duration-300'
            )}
          >
            <CardContent className="pt-6">
              <div
                className={cn(
                  'w-12 h-12 rounded-xl flex items-center justify-center mb-4',
                  feature.color === 'gold' && 'bg-gold-100 text-gold-600',
                  feature.color === 'sage' && 'bg-sage-100 text-sage-600',
                  feature.color === 'twilight' && 'bg-twilight-100 text-text-secondary'
                )}
              >
                <feature.icon className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-text-primary mb-2">{feature.title}</h3>
              <p className="text-sm text-text-secondary">{feature.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  )
}

// ============================================================================
// KPI Preview Section
// ============================================================================

function KPIPreviewSection() {
  const kpis = [
    { label: 'Total Revenue', value: 'SAR 52.4M', change: '+8.2%', trend: 'up' },
    { label: 'Total Costs', value: 'SAR 49.1M', change: '+6.1%', trend: 'up' },
    { label: 'Net Income', value: 'SAR 3.3M', change: '+12.5%', trend: 'up' },
    { label: 'Operating Margin', value: '5.8%', change: '+0.4pp', trend: 'up' },
  ]

  return (
    <section className="space-y-8">
      <div>
        <h2 className="font-display text-3xl font-bold text-text-primary">Live KPI Dashboard</h2>
        <p className="text-text-secondary mt-2">Real-time financial metrics at your fingertips</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <Card
            key={kpi.label}
            className={cn(
              'bg-white border-border-light',
              'hover:border-gold-300 hover:shadow-md',
              'transition-all duration-200'
            )}
          >
            <CardContent className="pt-6">
              <p className="text-sm text-text-secondary mb-1">{kpi.label}</p>
              <p className="text-2xl font-mono font-bold text-text-primary">{kpi.value}</p>
              <div className="flex items-center gap-1 mt-2">
                <TrendingUp className="w-4 h-4 text-sage-600" />
                <span className="text-sm font-medium text-sage-600">{kpi.change}</span>
                <span className="text-xs text-text-tertiary">vs. prior year</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Keyboard shortcut hint */}
      <div className="flex justify-center">
        <div
          className={cn(
            'inline-flex items-center gap-3 px-4 py-2 rounded-full',
            'bg-subtle border border-border-light',
            'text-sm text-text-secondary'
          )}
        >
          <span>Try the command palette:</span>
          <kbd className="px-2 py-0.5 bg-white rounded border border-border-medium font-mono text-xs">
            ⌘K
          </kbd>
        </div>
      </div>
    </section>
  )
}
