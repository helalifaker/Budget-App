import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { TanStackRouterVite } from '@tanstack/router-vite-plugin'
import { visualizer } from 'rollup-plugin-visualizer'
import path from 'path'

// Vite configuration aligned with React 19 and TypeScript 5.9
// Enhanced with advanced code splitting and lazy loading optimizations
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    TanStackRouterVite(),
    // Bundle analyzer (only in analyze mode)
    process.env.ANALYZE === 'true' &&
      visualizer({
        filename: './dist/stats.html',
        open: true,
        gzipSize: true,
        brotliSize: true,
        template: 'treemap', // 'treemap', 'sunburst', 'network'
      }),
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Advanced manual chunks strategy for optimal code splitting
        manualChunks: (id) => {
          // Vendor chunks strategy - split by library for better caching
          if (id.includes('node_modules')) {
            // React core (critical - load first)
            if (id.includes('react') || id.includes('react-dom')) {
              if (id.includes('react-dom')) return 'react-vendor'
              if (id.includes('react/')) return 'react-vendor'
              return 'react-vendor'
            }

            // TanStack libraries (critical - load early)
            if (id.includes('@tanstack/react-query') || id.includes('@tanstack/react-router')) {
              return 'tanstack'
            }

            // AG Grid (heavy - lazy load on demand)
            if (id.includes('ag-grid')) {
              return 'ag-grid'
            }

            // Charts (heavy - lazy load on demand)
            if (id.includes('recharts')) {
              return 'charts'
            }

            // Framer Motion (animations - can be lazy loaded)
            if (id.includes('framer-motion')) {
              return 'animations'
            }

            // Supabase (auth/data - load early)
            if (id.includes('@supabase')) {
              return 'supabase'
            }

            // Sentry (monitoring - defer)
            if (id.includes('@sentry')) {
              return 'sentry'
            }

            // UI components (shadcn/radix)
            if (id.includes('@radix-ui') || id.includes('lucide-react')) {
              return 'ui'
            }

            // Form libraries (load with forms)
            if (
              id.includes('react-hook-form') ||
              id.includes('zod') ||
              id.includes('@hookform/resolvers')
            ) {
              return 'forms'
            }

            // Toast notifications
            if (id.includes('sonner')) {
              return 'ui'
            }

            // Error boundary
            if (id.includes('react-error-boundary')) {
              return 'react-vendor'
            }

            // Utilities
            if (
              id.includes('clsx') ||
              id.includes('tailwind-merge') ||
              id.includes('class-variance-authority')
            ) {
              return 'utils'
            }

            // Axios (API client)
            if (id.includes('axios')) {
              return 'vendor'
            }

            // Remaining vendors
            return 'vendor'
          }

          // App chunks by route layer (lazy load by module)
          if (id.includes('src/routes/planning/')) {
            return 'routes-planning'
          }
          if (id.includes('src/routes/consolidation/')) {
            return 'routes-consolidation'
          }
          if (id.includes('src/routes/analysis/')) {
            return 'routes-analysis'
          }
          if (id.includes('src/routes/strategic/')) {
            return 'routes-strategic'
          }
          if (id.includes('src/routes/configuration/')) {
            return 'routes-configuration'
          }

          // Grid components (lazy load with planning routes)
          if (id.includes('src/components/grid/')) {
            return 'grid-components'
          }

          // Chart components (lazy load with analysis routes)
          if (id.includes('src/components/charts/')) {
            return 'chart-components'
          }
        },
      },
    },

    // Target modern browsers for smaller bundles
    target: 'esnext',

    // Use terser for better minification and tree-shaking
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug'], // Remove specific console methods
        passes: 2, // Multiple passes for better compression
      },
      format: {
        comments: false, // Remove all comments
      },
    },

    // Generate source maps for production debugging (external for smaller bundles)
    sourcemap: true,

    // Chunk size warnings
    chunkSizeWarningLimit: 600, // KB

    // CSS code splitting
    cssCodeSplit: true,
  },

  // Optimize dependencies (pre-bundle common libs)
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@tanstack/react-query',
      '@tanstack/react-router',
      'react-error-boundary',
      'sonner',
    ],
    exclude: [
      'ag-grid-community', // Lazy load
      'ag-grid-react',
      'framer-motion',
      // Note: recharts is NOT excluded - let Vite handle it and its dependencies (es-toolkit)
    ],
    // Force proper ES module resolution
    esbuildOptions: {
      target: 'esnext',
    },
  },
})
