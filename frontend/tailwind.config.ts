/**
 * EFIR Budget Planning Application - Tailwind Configuration
 *
 * Luxury aesthetic theme with warm neutrals and refined accent colors.
 * This configuration implements the New Theme design system.
 *
 * Color Philosophy:
 * - Gold (#A68B5B)       - Finance module, primary actions, calls-to-action
 * - Sage (#7D9082)       - Enrollment module, success states
 * - Terracotta (#C4785D) - Warnings, attention, deficits
 * - Slate (#64748B)      - Analysis module, neutral accent
 * - Wine (#8B5C6B)       - Workforce module, secondary accent
 */

import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // =========================================================================
      // COLORS
      // =========================================================================
      colors: {
        // shadcn/ui base colors (CSS variable references)
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },

        // =====================================================================
        // BACKGROUND COLORS (CSS variable references for theme support)
        // =====================================================================
        /** Main page background - warm off-white */
        canvas: 'var(--color-canvas)',
        /** Card/surface background - pure white */
        paper: 'var(--color-paper)',
        /** Subtle backgrounds, hover states */
        subtle: 'var(--color-subtle)',
        /** Warm tinted backgrounds */
        warm: 'var(--color-warm)',
        /** Muted background for disabled states */
        'bg-muted': 'var(--color-muted)',

        // =====================================================================
        // BORDER COLORS (CSS variable references for theme support)
        // =====================================================================
        'border-light': 'var(--color-border-light)',
        'border-medium': 'var(--color-border-medium)',
        'border-strong': 'var(--color-border-strong)',

        // =====================================================================
        // TEXT COLORS (CSS variable references for theme support)
        // =====================================================================
        /** Primary text - warm black */
        'text-primary': 'var(--color-text-primary)',
        /** Secondary text - body text */
        'text-secondary': 'var(--color-text-secondary)',
        /** Tertiary text - labels */
        'text-tertiary': 'var(--color-text-tertiary)',
        /** Muted text - placeholders */
        'text-muted': 'var(--color-text-muted)',
        /** Disabled text */
        'text-disabled': 'var(--color-text-disabled)',

        // =====================================================================
        // GOLD - Finance module, primary accent, calls-to-action
        // DEFAULT uses CSS variable for theme support, scale values are fixed
        // =====================================================================
        gold: {
          DEFAULT: 'var(--color-gold)',
          50: '#FBF8F3', // Light warm tint (opaque)
          100: '#F5EFE3', // Lighter gold (opaque)
          200: '#EBE0CC', // Light gold (opaque)
          300: '#D4BC8E',
          400: '#BDA474',
          500: '#A68B5B',
          600: '#8F7750',
          700: '#786345',
          800: '#614F3A',
          900: '#4A3C2F',
        },

        // =====================================================================
        // SAGE - Enrollment module, success states
        // DEFAULT uses CSS variable for theme support, scale values are fixed
        // =====================================================================
        sage: {
          DEFAULT: 'var(--color-sage)',
          50: '#F2F5F3', // Light sage tint (opaque)
          100: '#E5EBE7', // Lighter sage (opaque)
          200: '#C9D5CD', // Light sage (opaque)
          300: '#A8B8AD',
          400: '#93A498',
          500: '#7D9082',
          600: '#6B7D70',
          700: '#596A5E',
          800: '#47564C',
          900: '#35433A',
        },

        // =====================================================================
        // TERRACOTTA - Warnings, attention, deficits
        // DEFAULT uses CSS variable for theme support, scale values are fixed
        // =====================================================================
        terracotta: {
          DEFAULT: 'var(--color-terracotta)',
          50: '#FDF6F3', // Light terracotta tint (opaque)
          100: '#FAE9E3', // Lighter terracotta (opaque)
          200: '#F2D4C8', // Light terracotta (opaque)
          300: '#D9A08A',
          400: '#CF8C73',
          500: '#C4785D',
          600: '#B06A50',
          700: '#955A44',
          800: '#7A4A38',
          900: '#5F3A2C',
        },

        // =====================================================================
        // SLATE - Analysis module, neutral accent
        // DEFAULT uses CSS variable for theme support, scale values are fixed
        // =====================================================================
        slate: {
          DEFAULT: 'var(--color-slate)',
          50: '#F8FAFC', // Light slate tint (opaque)
          100: '#F1F5F9', // Lighter slate (opaque)
          200: '#E2E8F0', // Light slate (opaque)
          300: '#94A3B8',
          400: '#7C8CA2',
          500: '#64748B',
          600: '#576478',
          700: '#4A5568',
          800: '#3D4758',
          900: '#303948',
        },

        // =====================================================================
        // WINE - Workforce module, secondary accent
        // DEFAULT uses CSS variable for theme support, scale values are fixed
        // =====================================================================
        wine: {
          DEFAULT: 'var(--color-wine)',
          50: '#FBF5F7', // Light wine tint (opaque)
          100: '#F5E8EC', // Lighter wine (opaque)
          200: '#EBCFD8', // Light wine (opaque)
          300: '#B08595',
          400: '#9E7080',
          500: '#8B5C6B',
          600: '#7A505D',
          700: '#69444F',
          800: '#583841',
          900: '#472C33',
        },

        // =====================================================================
        // STATUS COLORS (Flat)
        // =====================================================================
        status: {
          success: '#7D9082',
          'success-bg': '#E5EBE7', // Opaque sage-100
          warning: '#B45309',
          'warning-bg': '#FEF3C7', // Opaque amber-100
          error: '#C4785D',
          'error-bg': '#FAE9E3', // Opaque terracotta-100
          info: '#64748B',
          'info-bg': '#F1F5F9', // Opaque slate-100
        },

        // =====================================================================
        // SEMANTIC COLOR SCALES (for success/warning/error/info states)
        // =====================================================================
        /** Success states - mapped to Sage */
        success: {
          DEFAULT: '#7D9082',
          50: '#F2F5F3', // Light sage tint (opaque)
          100: '#E5EBE7', // Lighter sage (opaque)
          200: '#C9D5CD', // Light sage (opaque)
          300: '#A8B8AD',
          400: '#93A498',
          500: '#7D9082',
          600: '#6B7D70',
          700: '#596A5E',
          800: '#47564C',
          900: '#35433A',
        },
        /** Warning states - amber/orange */
        warning: {
          DEFAULT: '#B45309',
          50: '#FFFBEB', // Light amber tint (opaque)
          100: '#FEF3C7', // Lighter amber (opaque)
          200: '#FDE68A', // Light amber (opaque)
          300: '#FBBF24',
          400: '#F59E0B',
          500: '#D97706',
          600: '#B45309',
          700: '#92400E',
          800: '#78350F',
          900: '#5C2D0E',
        },
        /** Error states - mapped to Terracotta */
        error: {
          DEFAULT: '#C4785D',
          50: '#FDF6F3', // Light terracotta tint (opaque)
          100: '#FAE9E3', // Lighter terracotta (opaque)
          200: '#F2D4C8', // Light terracotta (opaque)
          300: '#D9A08A',
          400: '#CF8C73',
          500: '#C4785D',
          600: '#B06A50',
          700: '#955A44',
          800: '#7A4A38',
          900: '#5F3A2C',
        },
        /** Info states - mapped to Slate */
        info: {
          DEFAULT: '#64748B',
          50: '#F8FAFC', // Light slate tint (opaque)
          100: '#F1F5F9', // Lighter slate (opaque)
          200: '#E2E8F0', // Light slate (opaque)
          300: '#94A3B8',
          400: '#7C8CA2',
          500: '#64748B',
          600: '#576478',
          700: '#4A5568',
          800: '#3D4758',
          900: '#303948',
        },

        // =====================================================================
        // MODULE-SPECIFIC COLORS (Convenience aliases)
        // =====================================================================
        'module-finance': '#A68B5B',
        'module-enrollment': '#7D9082',
        'module-workforce': '#8B5C6B',
        'module-analysis': '#64748B',
        'module-strategic': '#8A877E',

        // =====================================================================
        // EFIR PREFIXED ALIASES (for component compatibility)
        // =====================================================================
        'efir-gold': {
          DEFAULT: '#A68B5B',
          50: '#FBF8F3', // Light warm tint (opaque)
          100: '#F5EFE3', // Lighter gold (opaque)
          200: '#EBE0CC', // Light gold (opaque)
          300: '#D4BC8E',
          400: '#BDA474',
          500: '#A68B5B',
          600: '#8F7750',
          700: '#786345',
          800: '#614F3A',
          900: '#4A3C2F',
        },
        'efir-sage': {
          DEFAULT: '#7D9082',
          50: '#F2F5F3', // Light sage tint (opaque)
          100: '#E5EBE7', // Lighter sage (opaque)
          200: '#C9D5CD', // Light sage (opaque)
          300: '#A8B8AD',
          400: '#93A498',
          500: '#7D9082',
          600: '#6B7D70',
          700: '#596A5E',
          800: '#47564C',
          900: '#35433A',
        },
        'efir-terracotta': {
          DEFAULT: '#C4785D',
          50: '#FDF6F3', // Light terracotta tint (opaque)
          100: '#FAE9E3', // Lighter terracotta (opaque)
          200: '#F2D4C8', // Light terracotta (opaque)
          300: '#D9A08A',
          400: '#CF8C73',
          500: '#C4785D',
          600: '#B06A50',
          700: '#955A44',
          800: '#7A4A38',
          900: '#5F3A2C',
        },
        'efir-slate': {
          DEFAULT: '#64748B',
          50: '#F8FAFC', // Light slate tint (opaque)
          100: '#F1F5F9', // Lighter slate (opaque)
          200: '#E2E8F0', // Light slate (opaque)
          300: '#94A3B8',
          400: '#7C8CA2',
          500: '#64748B',
          600: '#576478',
          700: '#4A5568',
          800: '#3D4758',
          900: '#303948',
        },
        'efir-wine': {
          DEFAULT: '#8B5C6B',
          50: '#FBF5F7', // Light wine tint (opaque)
          100: '#F5E8EC', // Lighter wine (opaque)
          200: '#EBCFD8', // Light wine (opaque)
          300: '#B08595',
          400: '#9E7080',
          500: '#8B5C6B',
          600: '#7A505D',
          700: '#69444F',
          800: '#583841',
          900: '#472C33',
        },

        // =====================================================================
        // LEGACY/COMPATIBILITY COLOR SCALES
        // These support older component code - prefer semantic colors above
        // =====================================================================
        /** Twilight - cool gray-blue (legacy, use slate instead) */
        twilight: {
          DEFAULT: '#8BA0B4',
          50: 'rgba(157, 180, 199, 0.10)',
          100: 'rgba(157, 180, 199, 0.20)',
          200: '#C5D3DE',
          300: '#ADBFCD',
          400: '#9DB4C7',
          500: '#8BA0B4',
          600: '#7389A0',
          700: '#61707F',
          800: '#4F5C68',
          900: '#3D4751',
        },
        /** Sand - warm beige scale (legacy, use subtle/muted instead) */
        sand: {
          DEFAULT: '#D9CFC0',
          50: '#FBF8F3',
          100: '#F5EFE6',
          200: '#EBE3D6',
          300: '#D9CFC0',
          400: '#C9BCAA',
          500: '#B9A994',
          600: '#A39580',
          700: '#8A7F6B',
          800: '#716A58',
          900: '#585447',
        },
        /** Cream - warm off-white (legacy, use canvas/warm instead) */
        cream: {
          DEFAULT: '#FAF7F2',
          50: '#FEFDFB',
          100: '#FAF7F2',
          200: '#F5F0E8',
          300: '#EBE3D6',
          400: '#DFD5C4',
          500: '#D3C7B3',
          600: '#B8AA95',
          700: '#9C8D78',
          800: '#80715C',
          900: '#655841',
        },
        /** Blue - standard blue for info states */
        blue: {
          DEFAULT: '#3B82F6',
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        /** Gray - standard neutral scale */
        gray: {
          DEFAULT: '#6B7280',
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
        },
        /** Amber - for warning states (legacy, use warning instead) */
        amber: {
          DEFAULT: '#F59E0B',
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        /** Emerald - for success states (legacy, use success instead) */
        emerald: {
          DEFAULT: '#10B981',
          50: '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          300: '#6EE7B7',
          400: '#34D399',
          500: '#10B981',
          600: '#059669',
          700: '#047857',
          800: '#065F46',
          900: '#064E3B',
        },
        /** Red - for error states (legacy, use error instead) */
        red: {
          DEFAULT: '#EF4444',
          50: '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          300: '#FCA5A5',
          400: '#F87171',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
          800: '#991B1B',
          900: '#7F1D1D',
        },
        /** Green - for success states (legacy, use success instead) */
        green: {
          DEFAULT: '#22C55E',
          50: '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#22C55E',
          600: '#16A34A',
          700: '#15803D',
          800: '#166534',
          900: '#14532D',
        },
        /** Yellow - for warning highlights (legacy, use warning instead) */
        yellow: {
          DEFAULT: '#EAB308',
          50: '#FEFCE8',
          100: '#FEF9C3',
          200: '#FEF08A',
          300: '#FDE047',
          400: '#FACC15',
          500: '#EAB308',
          600: '#CA8A04',
          700: '#A16207',
          800: '#854D0E',
          900: '#713F12',
        },
        /** Brown - warm earth tones (legacy) */
        brown: {
          DEFAULT: '#8B5C4A',
          50: '#FAF5F3',
          100: '#F5EBE6',
          200: '#E8D5CB',
          300: '#D4B8A8',
          400: '#BC9682',
          500: '#8B5C4A',
          600: '#78503F',
          700: '#654335',
          800: '#52372C',
          900: '#3F2B22',
        },
        /** Purple - for accent/highlight states (legacy) */
        purple: {
          DEFAULT: '#A855F7',
          50: '#FAF5FF',
          100: '#F3E8FF',
          200: '#E9D5FF',
          300: '#D8B4FE',
          400: '#C084FC',
          500: '#A855F7',
          600: '#9333EA',
          700: '#7E22CE',
          800: '#6B21A8',
          900: '#581C87',
        },
        /** Violet - for accent states (legacy) */
        violet: {
          DEFAULT: '#8B5CF6',
          50: '#F5F3FF',
          100: '#EDE9FE',
          200: '#DDD6FE',
          300: '#C4B5FD',
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#7C3AED',
          700: '#6D28D9',
          800: '#5B21B6',
          900: '#4C1D95',
        },
        /** Indigo - for accent states (legacy) */
        indigo: {
          DEFAULT: '#6366F1',
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
        },
        /** Orange - for warning/attention states (legacy) */
        orange: {
          DEFAULT: '#F97316',
          50: '#FFF7ED',
          100: '#FFEDD5',
          200: '#FED7AA',
          300: '#FDBA74',
          400: '#FB923C',
          500: '#F97316',
          600: '#EA580C',
          700: '#C2410C',
          800: '#9A3412',
          900: '#7C2D12',
        },
        /** Teal - for success/positive states (legacy) */
        teal: {
          DEFAULT: '#14B8A6',
          50: '#F0FDFA',
          100: '#CCFBF1',
          200: '#99F6E4',
          300: '#5EEAD4',
          400: '#2DD4BF',
          500: '#14B8A6',
          600: '#0D9488',
          700: '#0F766E',
          800: '#115E59',
          900: '#134E4A',
        },
        /** Cyan - for info/highlight states (legacy) */
        cyan: {
          DEFAULT: '#06B6D4',
          50: '#ECFEFF',
          100: '#CFFAFE',
          200: '#A5F3FC',
          300: '#67E8F9',
          400: '#22D3EE',
          500: '#06B6D4',
          600: '#0891B2',
          700: '#0E7490',
          800: '#155E75',
          900: '#164E63',
        },
      },

      // =========================================================================
      // TYPOGRAPHY
      // =========================================================================
      fontFamily: {
        /** Display headings - elegant serif for KPIs and headlines */
        display: ['Cormorant Garamond', 'Georgia', 'Times New Roman', 'serif'],
        /** Body text - clean sans-serif for labels and navigation */
        body: ['Lato', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        /** Code/monospace - for numbers, codes, data cells */
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
        /** Sans-serif alias (same as body) */
        sans: ['Lato', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        /** Serif alias (same as display) */
        serif: ['Cormorant Garamond', 'Georgia', 'Times New Roman', 'serif'],
      },

      fontSize: {
        // Standard web scale (base: 16px for optimal readability)
        xs: ['0.75rem', { lineHeight: '1.4' }], // 12px
        sm: ['0.875rem', { lineHeight: '1.5' }], // 14px
        base: ['1rem', { lineHeight: '1.5' }], // 16px
        md: ['0.9375rem', { lineHeight: '1.5' }], // 15px
        lg: ['1.125rem', { lineHeight: '1.5' }], // 18px
        xl: ['1.25rem', { lineHeight: '1.4' }], // 20px
        '2xl': ['1.5rem', { lineHeight: '1.4' }], // 24px
        '3xl': ['1.875rem', { lineHeight: '1.3' }], // 30px
        '4xl': ['2.25rem', { lineHeight: '1.2' }], // 36px
        '5xl': ['3rem', { lineHeight: '1.1' }], // 48px
        '6xl': ['3.75rem', { lineHeight: '1.1' }], // 60px

        // KPI specific sizes (scaled up proportionally)
        'kpi-xl': ['2.25rem', { lineHeight: '1', letterSpacing: '-0.5px' }], // 36px
        'kpi-lg': ['1.75rem', { lineHeight: '1', letterSpacing: '-0.3px' }], // 28px
        'kpi-md': ['1.25rem', { lineHeight: '1' }], // 20px
        'kpi-sm': ['1rem', { lineHeight: '1' }], // 16px

        // =====================================================================
        // UI REDESIGN TYPOGRAPHY (Phase 1)
        // Semantic font sizes for the new modular layout system
        // =====================================================================
        /** Module titles - 20px, semibold */
        'module-title': ['1.25rem', { lineHeight: '1.3', fontWeight: '600' }],
        /** Workflow tab labels - 14px, medium */
        'tab-label': ['0.875rem', { lineHeight: '1.5', fontWeight: '500' }],
        /** Task descriptions - 14px, regular, muted */
        description: ['0.875rem', { lineHeight: '1.5', fontWeight: '400' }],
        /** Table/grid headers - 13px, medium, uppercase */
        'table-header': ['0.8125rem', { lineHeight: '1.4', fontWeight: '500' }],
        /** Table/grid content - 14px, regular */
        'table-content': ['0.875rem', { lineHeight: '1.4', fontWeight: '400' }],
        /** Button text - 14px, medium */
        button: ['0.875rem', { lineHeight: '1', fontWeight: '500' }],
        /** Small button text - 13px, medium */
        'button-small': ['0.8125rem', { lineHeight: '1', fontWeight: '500' }],
        /** Form labels - 13px, medium */
        label: ['0.8125rem', { lineHeight: '1.4', fontWeight: '500' }],
        /** Input field text - 14px, regular */
        input: ['0.875rem', { lineHeight: '1.5', fontWeight: '400' }],
        /** Caption/helper text - 12px, regular */
        caption: ['0.75rem', { lineHeight: '1.4', fontWeight: '400' }],
        /** Sidebar navigation labels - 12px, medium */
        'sidebar-label': ['0.75rem', { lineHeight: '1.3', fontWeight: '500' }],
        /** Badge/status text - 11px, semibold, uppercase */
        badge: ['0.6875rem', { lineHeight: '1', fontWeight: '600' }],
        /** KPI display value - 28px, semibold */
        'kpi-value': ['1.75rem', { lineHeight: '1', fontWeight: '600', letterSpacing: '-0.5px' }],
        /** KPI label - 12px, medium, uppercase */
        'kpi-label': ['0.75rem', { lineHeight: '1.3', fontWeight: '500' }],
      },

      letterSpacing: {
        tighter: '-0.5px',
        tight: '-0.3px',
        normal: '0',
        wide: '0.3px',
        wider: '0.5px',
        widest: '1px',
      },

      // =========================================================================
      // SPACING (Compact for data-dense layouts)
      // =========================================================================
      spacing: {
        '0.5': '0.125rem', // 2px
        '1': '0.25rem', // 4px
        '1.5': '0.375rem', // 6px
        '2': '0.5rem', // 8px
        '2.5': '0.625rem', // 10px
        '3': '0.75rem', // 12px
        '3.5': '0.875rem', // 14px
        '4': '1rem', // 16px
        '5': '1.25rem', // 20px
        '6': '1.5rem', // 24px
        '7': '1.75rem', // 28px
        '8': '2rem', // 32px
        '9': '2.25rem', // 36px
        '10': '2.5rem', // 40px
        '11': '2.75rem', // 44px
        '12': '3rem', // 48px
        '14': '3.5rem', // 56px
        '16': '4rem', // 64px
        '20': '5rem', // 80px
        '24': '6rem', // 96px
      },

      // =========================================================================
      // BORDER RADIUS
      // =========================================================================
      borderRadius: {
        none: '0',
        sm: '3px',
        DEFAULT: '6px',
        md: '6px',
        lg: '8px',
        xl: '10px',
        '2xl': '12px',
        '3xl': '14px',
        '4xl': '16px',
        full: '9999px',
      },

      // =========================================================================
      // SHADOWS (Warm undertone using #1A1917)
      // =========================================================================
      boxShadow: {
        xs: '0 1px 2px rgba(26, 25, 23, 0.04)',
        sm: '0 2px 8px rgba(26, 25, 23, 0.06)',
        md: '0 4px 16px rgba(26, 25, 23, 0.08)',
        lg: '0 8px 32px rgba(26, 25, 23, 0.10)',
        xl: '0 12px 48px rgba(26, 25, 23, 0.12)',
        '2xl': '0 24px 64px rgba(26, 25, 23, 0.16)',
        inner: 'inset 0 2px 4px rgba(26, 25, 23, 0.06)',
        // Accent color glows
        'gold-glow': '0 0 0 3px rgba(166, 139, 91, 0.15)',
        'sage-glow': '0 0 0 3px rgba(125, 144, 130, 0.15)',
        'terracotta-glow': '0 0 0 3px rgba(196, 120, 93, 0.15)',
        'slate-glow': '0 0 0 3px rgba(100, 116, 139, 0.15)',
        'wine-glow': '0 0 0 3px rgba(139, 92, 107, 0.15)',
        // Focus ring
        focus: '0 0 0 3px rgba(166, 139, 91, 0.20)',
        'focus-gold': '0 0 0 3px rgba(166, 139, 91, 0.20)',
        // EFIR prefixed aliases (for component compatibility)
        'efir-xs': '0 1px 2px rgba(26, 25, 23, 0.04)',
        'efir-sm': '0 2px 8px rgba(26, 25, 23, 0.06)',
        'efir-md': '0 4px 16px rgba(26, 25, 23, 0.08)',
        'efir-lg': '0 8px 32px rgba(26, 25, 23, 0.10)',
        'efir-xl': '0 12px 48px rgba(26, 25, 23, 0.12)',
      },

      // =========================================================================
      // TRANSITIONS
      // =========================================================================
      transitionDuration: {
        fast: '150ms',
        normal: '200ms',
        slow: '300ms',
        slower: '500ms',
      },

      transitionTimingFunction: {
        ease: 'ease',
        'ease-in-out': 'ease-in-out',
        smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },

      // =========================================================================
      // Z-INDEX
      // =========================================================================
      zIndex: {
        behind: '-1',
        base: '0',
        docked: '10',
        dropdown: '100',
        sticky: '200',
        banner: '250',
        overlay: '300',
        modal: '400',
        popover: '500',
        tooltip: '600',
        toast: '700',
        max: '9999',
      },

      // =========================================================================
      // ANIMATIONS
      // =========================================================================
      animation: {
        'fade-in': 'fadeIn 200ms ease-out',
        'fade-out': 'fadeOut 200ms ease-in',
        'slide-up': 'slideUp 200ms ease-out',
        'slide-down': 'slideDown 200ms ease-out',
        'scale-in': 'scaleIn 200ms ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
    },
  },
  plugins: [],
}

export default config
