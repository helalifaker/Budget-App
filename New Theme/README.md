# EFIR Budget App - Luxury Theme Package

A refined, handcrafted design system for financial planning applications. Features warm, sophisticated colors, elegant typography pairing, and comprehensive component styles.

## 📦 Package Contents

```
efir-theme-package/
├── index.ts                 # Main exports
├── theme.constants.ts       # TypeScript theme definitions
├── tailwind.config.ts       # Tailwind CSS configuration
├── globals.css              # Global CSS with variables
├── components.tsx           # React component examples
└── README.md               # This file
```

## 🚀 Installation

### 1. Install Required Fonts

Add the Google Fonts link to your HTML `<head>` or import in CSS:

```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

Or in CSS/SCSS:
```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
```

### 2. Copy Theme Files

Copy the theme files to your project:

```bash
# Create theme directory
mkdir -p src/styles/theme

# Copy files
cp efir-theme-package/theme.constants.ts src/styles/theme/
cp efir-theme-package/globals.css src/styles/
```

### 3. Configure Tailwind CSS

Replace or extend your `tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss';
import efirTheme from './src/styles/theme/tailwind.config';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: efirTheme.theme,
  plugins: [],
};

export default config;
```

### 4. Import Global Styles

In your `_app.tsx` or main entry file:

```typescript
import '../styles/globals.css';
```

## 🎨 Color Palette

### Background Colors
| Name | Hex | Usage |
|------|-----|-------|
| Canvas | `#FAF9F7` | Main page background |
| Paper | `#FFFFFF` | Cards, surfaces |
| Subtle | `#F5F4F1` | Hover states, secondary backgrounds |
| Warm | `#FBF9F6` | Warm tinted areas |

### Accent Colors
| Name | Hex | Usage |
|------|-----|-------|
| Gold | `#A68B5B` | Primary actions, links |
| Sage | `#7D9082` | Success, positive states |
| Terracotta | `#C4785D` | Warnings, deficits, alerts |
| Slate | `#64748B` | Neutral accent, analysis |
| Wine | `#8B5C6B` | Secondary accent, workforce |

### Text Colors
| Name | Hex | Usage |
|------|-----|-------|
| Primary | `#1A1917` | Headlines, main text |
| Secondary | `#5C5A54` | Body text |
| Tertiary | `#8A877E` | Labels, captions |
| Muted | `#B5B2A9` | Placeholders, disabled |

## 🔤 Typography

### Font Families

- **Display**: `Cormorant Garamond` - Elegant serif for headlines & KPIs
- **Body**: `Inter` - Clean sans-serif for body text
- **Mono**: `JetBrains Mono` - Code and numbers

### Usage Examples

```tsx
// Display heading
<h1 className="font-display text-3xl font-semibold text-text-primary">
  Command Center
</h1>

// KPI value
<span className="font-display text-kpi-xl font-semibold">
  48.5M
</span>

// Body text
<p className="font-body text-base text-text-secondary">
  Budget planning overview for FY24-25
</p>

// Label
<span className="text-xs font-medium text-text-tertiary uppercase tracking-wider">
  Total Budget
</span>
```

## 🧩 Component Usage

### KPI Card

```tsx
import { KpiCard } from './components';

<KpiCard
  label="Total Budget"
  value="48.5M"
  unit="SAR"
  change="+2.3%"
  indicator="positive"
/>
```

### Module Card

```tsx
import { ModuleCard } from './components';

<ModuleCard
  type="workforce"
  title="Workforce"
  description="Employee management, salaries, DHG planning"
  status="warning"
  progress={75}
  metrics={[
    { label: 'Total Staff', value: '123', change: '↗+5', changeDirection: 'up' },
    { label: 'AEFE Filled', value: '22/28' },
  ]}
  updatedAt="2 hours ago"
/>
```

### Badge

```tsx
import { Badge } from './components';

<Badge variant="success">✓ Healthy</Badge>
<Badge variant="warning">⚠ Attention 2</Badge>
<Badge variant="error">⚠ Warning 3</Badge>
```

### Button

```tsx
import { Button } from './components';

<Button variant="primary">Save Changes</Button>
<Button variant="secondary" leftIcon="📄">No budget versions</Button>
<Button variant="gold">Create Budget</Button>
```

### Card

```tsx
import { Card } from './components';

<Card accent="gold" padding="default" hoverable>
  Card content here
</Card>
```

## 🎯 Module Theme Mapping

Use `moduleTheme` for consistent module styling:

```tsx
import { moduleTheme } from './theme.constants';

const module = moduleTheme['workforce'];
// module.bg: 'rgba(139, 92, 107, 0.10)'
// module.color: '#8B5C6B'
// module.icon: '👥'
// module.label: 'Workforce'
```

Available modules: `workforce`, `enrollment`, `finance`, `analysis`, `strategic`

## 📊 Status Theme Mapping

Use `statusTheme` for consistent status styling:

```tsx
import { statusTheme } from './theme.constants';

const status = statusTheme['healthy'];
// status.bg: 'rgba(125, 144, 130, 0.12)'
// status.color: '#7D9082'
// status.label: 'Healthy'
// status.icon: '✓'
```

Available statuses: `healthy`, `warning`, `alert`, `inactive`, `pending`

## 📈 KPI Theme Mapping

Use `kpiTheme` for consistent KPI styling:

```tsx
import { kpiTheme } from './theme.constants';

const kpi = kpiTheme['positive'];
// kpi.textColor: '#7D9082'
// kpi.barColor: '#7D9082'
// kpi.bgColor: 'rgba(125, 144, 130, 0.12)'
// kpi.icon: '↗'
```

Available indicators: `positive`, `negative`, `neutral`, `info`

## 🛠️ CSS Variables

All theme values are available as CSS custom properties:

```css
.my-component {
  background: var(--color-bg-paper);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}
```

## 📐 Tailwind Utilities

### Custom Colors

```html
<div class="bg-canvas text-text-primary border-border-light">
<div class="bg-gold-100 text-gold">
<div class="bg-sage-100 text-sage">
```

### Custom Shadows

```html
<div class="shadow-sm hover:shadow-md">
<button class="focus:shadow-focus">
<div class="shadow-gold-glow">
```

### Custom Typography

```html
<h1 class="font-display text-4xl font-semibold tracking-tight">
<span class="font-display text-kpi-xl">
<p class="font-body text-base text-text-secondary">
```

## 📱 Responsive Design

The theme uses a compact base font size (12px) optimized for data-dense applications. Adjust for different contexts:

```css
/* For standard web apps */
html { font-size: 16px; }

/* For data-dense dashboards */
html { font-size: 14px; }

/* Current EFIR setting (compact) */
html { font-size: 12px; }
```

## 🌙 Dark Mode (Future)

The theme is structured to support dark mode. CSS variables can be overridden:

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-canvas: #1A1917;
    --color-bg-paper: #242320;
    /* ... other overrides */
  }
}
```

## 📝 License

Proprietary - EFIR Budget App
