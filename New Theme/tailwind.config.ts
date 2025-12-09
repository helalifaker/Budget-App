// ============================================================================
// EFIR BUDGET APP - TAILWIND CONFIGURATION
// Copy this configuration to your tailwind.config.ts
// ============================================================================

import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // -----------------------------------------------------------------------
      // COLORS
      // -----------------------------------------------------------------------
      colors: {
        // Background Colors
        canvas: '#FAF9F7',
        paper: '#FFFFFF',
        subtle: '#F5F4F1',
        warm: '#FBF9F6',
        muted: '#F0EFEC',

        // Border Colors
        border: {
          light: '#E8E6E1',
          DEFAULT: '#E8E6E1',
          medium: '#D4D1C9',
          strong: '#C5C2B8',
        },

        // Text Colors
        'text-primary': '#1A1917',
        'text-secondary': '#5C5A54',
        'text-tertiary': '#8A877E',
        'text-muted': '#B5B2A9',
        'text-disabled': '#D4D1C9',

        // Gold Accent
        gold: {
          DEFAULT: '#A68B5B',
          50: 'rgba(166, 139, 91, 0.06)',
          100: 'rgba(166, 139, 91, 0.12)',
          200: 'rgba(166, 139, 91, 0.20)',
          300: '#D4BC8E',
          400: '#BDA474',
          500: '#A68B5B',
          600: '#8F7750',
          700: '#786345',
          800: '#614F3A',
          900: '#4A3C2F',
        },

        // Sage Accent
        sage: {
          DEFAULT: '#7D9082',
          50: 'rgba(125, 144, 130, 0.06)',
          100: 'rgba(125, 144, 130, 0.12)',
          200: 'rgba(125, 144, 130, 0.20)',
          300: '#A8B8AD',
          400: '#93A498',
          500: '#7D9082',
          600: '#6B7D70',
          700: '#596A5E',
          800: '#47564C',
          900: '#35433A',
        },

        // Terracotta Accent
        terracotta: {
          DEFAULT: '#C4785D',
          50: 'rgba(196, 120, 93, 0.06)',
          100: 'rgba(196, 120, 93, 0.12)',
          200: 'rgba(196, 120, 93, 0.20)',
          300: '#D9A08A',
          400: '#CF8C73',
          500: '#C4785D',
          600: '#B06A50',
          700: '#955A44',
          800: '#7A4A38',
          900: '#5F3A2C',
        },

        // Slate Accent
        slate: {
          DEFAULT: '#64748B',
          50: 'rgba(100, 116, 139, 0.05)',
          100: 'rgba(100, 116, 139, 0.10)',
          200: 'rgba(100, 116, 139, 0.20)',
          300: '#94A3B8',
          400: '#7C8CA2',
          500: '#64748B',
          600: '#576478',
          700: '#4A5568',
          800: '#3D4758',
          900: '#303948',
        },

        // Wine Accent
        wine: {
          DEFAULT: '#8B5C6B',
          50: 'rgba(139, 92, 107, 0.05)',
          100: 'rgba(139, 92, 107, 0.10)',
          200: 'rgba(139, 92, 107, 0.20)',
          300: '#B08595',
          400: '#9E7080',
          500: '#8B5C6B',
          600: '#7A505D',
          700: '#69444F',
          800: '#583841',
          900: '#472C33',
        },

        // Status Colors
        status: {
          success: '#7D9082',
          'success-bg': 'rgba(125, 144, 130, 0.12)',
          warning: '#B45309',
          'warning-bg': 'rgba(245, 158, 11, 0.12)',
          error: '#C4785D',
          'error-bg': 'rgba(196, 120, 93, 0.12)',
          info: '#64748B',
          'info-bg': 'rgba(100, 116, 139, 0.10)',
        },
      },

      // -----------------------------------------------------------------------
      // TYPOGRAPHY
      // -----------------------------------------------------------------------
      fontFamily: {
        display: ['Cormorant Garamond', 'Georgia', 'Times New Roman', 'serif'],
        body: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },

      fontSize: {
        // Standard sizes
        'xs': ['0.625rem', { lineHeight: '1.3' }],       // 10px
        'sm': ['0.6875rem', { lineHeight: '1.4' }],      // 11px
        'base': ['0.75rem', { lineHeight: '1.5' }],      // 12px
        'md': ['0.8125rem', { lineHeight: '1.5' }],      // 13px
        'lg': ['0.875rem', { lineHeight: '1.5' }],       // 14px
        'xl': ['0.9375rem', { lineHeight: '1.4' }],      // 15px
        '2xl': ['1rem', { lineHeight: '1.4' }],          // 16px
        '3xl': ['1.375rem', { lineHeight: '1.2' }],      // 22px
        '4xl': ['1.625rem', { lineHeight: '1.1' }],      // 26px
        '5xl': ['2rem', { lineHeight: '1.1' }],          // 32px
        '6xl': ['2.5rem', { lineHeight: '1.1' }],        // 40px

        // KPI specific sizes
        'kpi-xl': ['1.625rem', { lineHeight: '1', letterSpacing: '-0.5px' }],
        'kpi-lg': ['1.25rem', { lineHeight: '1', letterSpacing: '-0.3px' }],
        'kpi-md': ['1rem', { lineHeight: '1' }],
        'kpi-sm': ['0.875rem', { lineHeight: '1' }],
      },

      letterSpacing: {
        tighter: '-0.5px',
        tight: '-0.3px',
        normal: '0',
        wide: '0.3px',
        wider: '0.5px',
        widest: '1px',
      },

      // -----------------------------------------------------------------------
      // SPACING
      // -----------------------------------------------------------------------
      spacing: {
        '0.5': '0.125rem',   // 2px
        '1': '0.25rem',      // 4px
        '1.5': '0.375rem',   // 6px
        '2': '0.5rem',       // 8px
        '2.5': '0.625rem',   // 10px
        '3': '0.75rem',      // 12px
        '3.5': '0.875rem',   // 14px
        '4': '1rem',         // 16px
        '5': '1.25rem',      // 20px
        '6': '1.5rem',       // 24px
        '7': '1.75rem',      // 28px
        '8': '2rem',         // 32px
        '9': '2.25rem',      // 36px
        '10': '2.5rem',      // 40px
        '11': '2.75rem',     // 44px
        '12': '3rem',        // 48px
        '14': '3.5rem',      // 56px
        '16': '4rem',        // 64px
        '20': '5rem',        // 80px
        '24': '6rem',        // 96px
      },

      // -----------------------------------------------------------------------
      // BORDER RADIUS
      // -----------------------------------------------------------------------
      borderRadius: {
        'none': '0',
        'sm': '3px',
        'md': '6px',
        'lg': '8px',
        'xl': '10px',
        '2xl': '12px',
        '3xl': '14px',
        '4xl': '16px',
        'full': '9999px',
      },

      // -----------------------------------------------------------------------
      // SHADOWS
      // -----------------------------------------------------------------------
      boxShadow: {
        'xs': '0 1px 2px rgba(26, 25, 23, 0.04)',
        'sm': '0 2px 8px rgba(26, 25, 23, 0.06)',
        'md': '0 4px 16px rgba(26, 25, 23, 0.08)',
        'lg': '0 8px 32px rgba(26, 25, 23, 0.10)',
        'xl': '0 12px 48px rgba(26, 25, 23, 0.12)',
        '2xl': '0 24px 64px rgba(26, 25, 23, 0.16)',
        'inner': 'inset 0 2px 4px rgba(26, 25, 23, 0.06)',
        'gold-glow': '0 0 0 3px rgba(166, 139, 91, 0.15)',
        'sage-glow': '0 0 0 3px rgba(125, 144, 130, 0.15)',
        'terracotta-glow': '0 0 0 3px rgba(196, 120, 93, 0.15)',
        'focus': '0 0 0 3px rgba(166, 139, 91, 0.20)',
      },

      // -----------------------------------------------------------------------
      // TRANSITIONS
      // -----------------------------------------------------------------------
      transitionDuration: {
        'fast': '150ms',
        'normal': '200ms',
        'slow': '300ms',
        'slower': '500ms',
      },

      transitionTimingFunction: {
        'ease': 'ease',
        'ease-in-out': 'ease-in-out',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },

      // -----------------------------------------------------------------------
      // Z-INDEX
      // -----------------------------------------------------------------------
      zIndex: {
        'behind': '-1',
        'base': '0',
        'docked': '10',
        'dropdown': '100',
        'sticky': '200',
        'banner': '250',
        'overlay': '300',
        'modal': '400',
        'popover': '500',
        'tooltip': '600',
        'toast': '700',
        'max': '9999',
      },

      // -----------------------------------------------------------------------
      // ANIMATION
      // -----------------------------------------------------------------------
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
};

export default config;
