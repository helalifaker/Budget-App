/**
 * OpenAPI TypeScript Configuration
 *
 * This configuration file controls how TypeScript types are generated
 * from the backend's OpenAPI specification.
 *
 * Usage:
 *   pnpm generate:types        # From running backend server
 *   pnpm generate:types:file   # From saved openapi.json file
 *
 * The generated types in src/types/generated-api.ts should be used
 * as a reference to keep hand-written Zod schemas in sync with the backend.
 */

import { defineConfig } from 'openapi-typescript'

export default defineConfig({
  // Generate TypeScript interfaces (not types) for better IDE support
  exportType: true,

  // Add JSDoc comments from OpenAPI descriptions
  // This helps developers understand the purpose of each field
  // Note: openapi-typescript v7+ generates comments by default

  // Transform date strings to Date objects
  // Disabled by default since we handle dates as ISO strings
  // transform: (schemaObject) => { ... }

  // Path parameters are always required
  pathParamsAsTypes: true,
})
