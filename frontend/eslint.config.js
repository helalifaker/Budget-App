import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      // Prevent hardcoded hex colors in Tailwind bracket notation
      // Use theme color classes instead (bg-subtle, text-text-primary, border-border-light, etc.)
      'no-restricted-syntax': [
        'warn',
        {
          selector: 'Literal[value=/bg-\\[#[0-9A-Fa-f]{3,8}\\]/]',
          message: 'Avoid hardcoded hex colors. Use semantic theme classes like bg-subtle, bg-canvas, bg-paper, bg-bg-muted instead.',
        },
        {
          selector: 'Literal[value=/text-\\[#[0-9A-Fa-f]{3,8}\\]/]',
          message: 'Avoid hardcoded hex colors. Use semantic theme classes like text-text-primary, text-text-secondary, text-text-tertiary instead.',
        },
        {
          selector: 'Literal[value=/border-\\[#[0-9A-Fa-f]{3,8}\\]/]',
          message: 'Avoid hardcoded hex colors. Use semantic theme classes like border-border-light, border-border-medium, border-border-strong instead.',
        },
        {
          selector: 'TemplateLiteral:has(TemplateElement[value.raw=/bg-\\[#[0-9A-Fa-f]{3,8}\\]/])',
          message: 'Avoid hardcoded hex colors in template literals. Use semantic theme classes instead.',
        },
        {
          selector: 'TemplateLiteral:has(TemplateElement[value.raw=/text-\\[#[0-9A-Fa-f]{3,8}\\]/])',
          message: 'Avoid hardcoded hex colors in template literals. Use semantic theme classes instead.',
        },
        {
          selector: 'TemplateLiteral:has(TemplateElement[value.raw=/border-\\[#[0-9A-Fa-f]{3,8}\\]/])',
          message: 'Avoid hardcoded hex colors in template literals. Use semantic theme classes instead.',
        },
      ],
    },
  },
)
