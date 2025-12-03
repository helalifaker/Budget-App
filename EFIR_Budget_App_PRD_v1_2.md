# EFIR Budget Planning Application
## Product Requirements Document

**Version:** 1.2  
**Date:** November 2025  
**Document Status:** Draft  
**Prepared For:** École Française Internationale de Riyad (EFIR)  
**AEFE Status:** Conventionné  
**Primary Currency:** SAR (Saudi Riyal)  
**Confidentiality:** Internal Use Only

---

## 1. Executive Summary

### 1.1 Product Vision

A comprehensive, driver-based budget planning system designed specifically for French international schools operating under AEFE guidelines. The application transforms complex, manual budget processes into an integrated, automated system that delivers accuracy, transparency, and powerful scenario analysis capabilities.

### 1.2 Problem Statement

Current budget planning at EFIR faces significant challenges:

- Manual, spreadsheet-based processes prone to errors and version control issues
- Complex DHG (Dotation Horaire Globale) calculations requiring specialized knowledge
- Dual-period budget structure (Jan-Jun / Sep-Dec) spanning two academic years
- AEFE teacher cost management with EUR/SAR currency considerations
- Limited ability to perform scenario analysis and what-if planning
- No integration between enrollment, workforce, and financial planning

### 1.3 Solution Overview

An integrated web application providing driver-based budgeting where operational inputs (enrollment, curriculum hours, class structures) automatically cascade through to financial outputs. The system features a modern, spreadsheet-like interface familiar to finance professionals while delivering automated calculations, real-time validation, and comprehensive reporting.

### 1.4 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Budget cycle time reduction | 50% | Days from start to approval |
| Calculation accuracy | 99.9% | Variance from manual check |
| User adoption | 100% | Finance team active usage |
| Scenario analysis time | < 5 minutes | Time to generate scenario |
| Report generation | < 30 seconds | Time to generate report |

---

## 7. Technology Stack (v1.2 - Updated November 2025)

The technology stack has been updated to use the latest stable versions and best-in-class development tools for maximum performance, developer experience, and maintainability.

### 7.1 Frontend Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **React** | 19.2.0 | UI library with Server Components, Actions, Activity API |
| **TypeScript** | 5.9.x | Type-safe development, deferred imports, enhanced type narrowing |
| **Vite** | 7.2.x | Build tool with Environment API, ESM-only, Baseline browser targeting |
| **Tailwind CSS** | 4.1.x | Utility-first CSS with @tailwindcss/vite plugin, 5x faster builds |
| **shadcn/ui** | Latest (TW v4) | Accessible UI components with data-slot attributes, OKLCH colors |
| **AG Grid Community** | 34.3.x | Enterprise-grade data grid (MIT license) - Replaces Handsontable |
| **Recharts** | 2.15.x | React charting library for dashboards and visualizations |

#### AG Grid Community Features (Free - MIT License)

- Sorting, filtering, pagination, and cell editing out-of-the-box
- Custom components and cell renderers for specialized displays
- New Theming API with themeQuartz for modern styling
- React 19.2 full support with native component rendering
- High performance with virtualized rendering for large datasets
- No third-party dependencies, used by J.P. Morgan, MongoDB, NASA

### 7.2 Backend Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.14.0 | Runtime with improved performance and error messages |
| **FastAPI** | 0.123.x | High-performance async API framework with Pydantic v2 |
| **Pydantic** | 2.12+ | Data validation with JSON Schema support |
| **Uvicorn** | 0.34+ | ASGI server for production deployment |

### 7.3 Database & Infrastructure

| Component | Version | Purpose |
|-----------|---------|---------|
| **Supabase** | Latest | Backend-as-a-Service with Auth, Realtime, Edge Functions |
| **PostgreSQL** | 17.x | Primary database with Row Level Security (RLS) |
| **Supabase Auth** | Latest | Authentication with role-based access control |
| **Supabase Realtime** | Latest | WebSocket subscriptions for auto-save and collaboration |

### 7.4 Development Tools & Quality Assurance

Best-in-class tooling for code quality, consistency, and developer experience:

| Tool | Version | Purpose |
|------|---------|---------|
| **ESLint** | 9.x | Code linting with flat config (eslint.config.js) |
| **Prettier** | 3.4.x | Opinionated code formatting for consistency |
| **Husky** | 9.x | Git hooks for pre-commit validation |
| **lint-staged** | 15.x | Run linters on staged files only |
| **Vitest** | 3.x | Vite-native testing framework with instant HMR |
| **Playwright** | 1.49.x | End-to-end testing across browsers |
| **@typescript-eslint** | 8.x | TypeScript-specific ESLint rules |
| **eslint-plugin-react-hooks** | 5.x | React hooks linting rules |
| **eslint-plugin-tailwindcss** | 3.x | Tailwind CSS class ordering and best practices |
| **Ruff** | 0.8.x | Python linter (10-100x faster than Flake8) |
| **mypy** | 1.14.x | Python static type checker |
| **pytest** | 8.x | Python testing framework |

#### Development Workflow Configuration

**Pre-commit hooks (via Husky + lint-staged):**

1. ESLint: Check for code quality issues
2. Prettier: Auto-format staged files
3. TypeScript: Type check with `tsc --noEmit`
4. Vitest: Run affected tests

**CI/CD Pipeline:**

1. Lint check (ESLint + Ruff)
2. Type check (TypeScript + mypy)
3. Unit tests (Vitest + pytest)
4. E2E tests (Playwright)
5. Build verification

### 7.5 Version Summary Table

Complete technology stack with versions as of November 2025:

| Category | Technology | Version |
|----------|------------|---------|
| **Framework** | React | 19.2.0 |
| **Language** | TypeScript | 5.9.x |
| **Build Tool** | Vite | 7.2.x |
| **Styling** | Tailwind CSS | 4.1.x |
| **UI Components** | shadcn/ui | Latest (TW v4 compatible) |
| **Data Grid** | AG Grid Community | 34.3.x (MIT) |
| **Charts** | Recharts | 2.15.x |
| **Backend Runtime** | Python | 3.14.0 |
| **API Framework** | FastAPI | 0.123.x |
| **Database** | PostgreSQL (Supabase) | 17.x |
| **Linting** | ESLint + Ruff | 9.x / 0.8.x |
| **Formatting** | Prettier | 3.4.x |
| **Git Hooks** | Husky + lint-staged | 9.x / 15.x |
| **Testing** | Vitest + Playwright + pytest | 3.x / 1.49.x / 8.x |

### 7.6 Key Changes from v1.1

1. **Data Grid:** Replaced Handsontable with AG Grid Community (MIT license, better performance, React 19 support)
2. **Build Tool:** Upgraded to Vite 7.2 with Environment API and ESM-only distribution
3. **React:** Upgraded to React 19.2 with Activity API and useEffectEvent
4. **TypeScript:** Upgraded to TypeScript 5.9 with deferred module evaluation
5. **Tailwind CSS:** Upgraded to v4.1 with dedicated Vite plugin, 5x faster builds
6. **Dev Tools:** Added comprehensive tooling (ESLint 9, Prettier, Husky, lint-staged, Vitest, Playwright, Ruff)
7. **PostgreSQL:** Upgraded to PostgreSQL 17 via Supabase

---

## Appendix B: Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | November 2025 | Planning Team | Initial PRD creation |
| 1.1 | November 2025 | Planning Team | Corrected KSA calendar (Friday-Saturday weekend) |
| **1.2** | November 2025 | Planning Team | Major stack update: AG Grid (replaces Handsontable), Vite 7, React 19.2, TypeScript 5.9, Tailwind 4.1, added dev tools (ESLint, Prettier, Husky, Vitest) |

---

*Document prepared for EFIR Budget Planning Application development*  
*Confidentiality: Internal Use Only*
