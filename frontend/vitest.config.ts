import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@tanstack/react-router-devtools': '@tanstack/router-devtools',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['tests/setup.ts', 'src/setupTests.ts'],
    globals: true,
    include: ['tests/**/*.{test,spec}.{ts,tsx}', 'src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules/**', 'tests/e2e/**/*.{ts,tsx}'],
    env: {
      VITE_SUPABASE_URL: 'https://test-project.supabase.co',
      VITE_SUPABASE_ANON_KEY: 'test-anon-key-for-testing',
      VITE_E2E_TEST_MODE: 'false', // Disable E2E mode for unit tests (use Supabase mocks instead)
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/**',
        'dist/**',
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/routeTree.gen.ts',
        'src/setupTests.ts',
        'eslint.config.js',
        'vite.config.ts',
        'vitest.config.ts',
      ],
      thresholds: {
        lines: 95,
        functions: 95,
        branches: 95,
        statements: 95,
      },
    },
  },
})
