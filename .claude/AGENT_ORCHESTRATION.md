# Agent Orchestration Guide

## Available Agents

| Agent | Purpose | Model |
|-------|---------|-------|
| **product-architect-agent** | SOURCE OF TRUTH: PRD/FRS, business rules, DHG formulas, calculations | Opus |
| **Plan** | Design implementation strategies, architectural decisions | Opus |
| **Explore** | Fast codebase exploration, find files/patterns/keywords | Sonnet |
| **frontend-ui-agent** | React 19, shadcn/ui, AG Grid, TanStack Router, all 18 modules | Sonnet |
| **performance-agent** | Profiling, caching, query tuning, load testing | Sonnet |
| **qa-validation-agent** | Unit/integration/E2E tests, validation, 80%+ coverage | Sonnet |
| **documentation-training-agent** | User manuals, API docs, diagrams, training materials | Haiku |
| **general-purpose** | Complex multi-step tasks, research, code search | Sonnet |
| **claude-code-guide** | Claude Code CLI features, Agent SDK, Anthropic API | Haiku |

## Agent Selection Rules

```
BEFORE implementing business logic → product-architect-agent (MANDATORY)
BEFORE major feature work        → Plan agent
Finding files/code               → Explore agent
UI components/pages              → frontend-ui-agent
Performance issues               → performance-agent
Writing tests                    → qa-validation-agent
Documentation only               → documentation-training-agent
General research/search          → general-purpose
Claude Code questions            → claude-code-guide
```

## Workflow Patterns

### New Feature (Full Stack)
```
1. product-architect-agent  → Validate requirements, get formulas
2. Plan                     → Design architecture, API contracts
3. [Implement]              → Database → Engine → API → UI
4. qa-validation-agent      → Write tests (80%+ coverage)
5. documentation-training-agent → Update docs
```

### Bug Fix
```
1. Explore                  → Find buggy code location
2. product-architect-agent  → Confirm correct business logic (if unclear)
3. [Fix]                    → Apply fix
4. qa-validation-agent      → Add regression test
```

### Performance Issue
```
1. performance-agent        → Profile, identify bottleneck
2. [Optimize]               → Fix (indexes, caching, algorithm)
3. qa-validation-agent      → Verify no regression
```

## Boundary Rules (STRICT)

| Agent | CAN | CANNOT |
|-------|-----|--------|
| product-architect-agent | Define rules, formulas, requirements | Write code |
| Plan | Design architecture, plan implementation | Implement features |
| frontend-ui-agent | Build UI, React components | Backend logic, DB changes |
| qa-validation-agent | Write tests | Write production code |
| documentation-training-agent | Write docs | Write code |
| performance-agent | Optimize algorithms | Change business logic |

## MCP Server Usage

| Server | Primary Use |
|--------|-------------|
| context7 | Latest library docs (React 19, FastAPI, Supabase) |
| supabase | Table management, RLS policies |
| postgres | SQL queries, schema inspection |
| sentry | Error monitoring, performance traces |
| playwright | E2E browser automation |

## Quality Gates (Before Deployment)

- [ ] Business logic validated by product-architect-agent
- [ ] Tests passing with 80%+ coverage
- [ ] `pnpm lint && pnpm typecheck` passes
- [ ] `.venv/bin/ruff check . && .venv/bin/mypy app` passes
- [ ] Documentation updated

---
**Version**: 2.0.0 | **Agents**: 9 | **Optimized for AI consumption**
