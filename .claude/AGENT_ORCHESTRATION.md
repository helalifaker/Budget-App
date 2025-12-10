# EFIR Budget Planning Application - Agent Orchestration Guide

## Overview

This document defines how the 14 specialized agents work together to build and maintain the EFIR Budget Planning Application. Each agent has clear boundaries, dependencies, and orchestration rules.

## Agent Registry

### 1. Orchestrator
- **efir-master-agent** - Routes complex multi-domain tasks to specialized agents

### 2. Architecture & Requirements (3 agents)
- **product-architect-agent** - Guardian of PRD/FRS/business rules, provides formulas
- **system-architect-agent** - Owns architecture, API contracts, module boundaries
- **documentation-training-agent** - Creates all documentation and training materials

### 3. Backend Agents (3 agents)
- **database-supabase-agent** - PostgreSQL schema, RLS policies, migrations
- **backend-engine-agent** - Calculation engines (DHG, enrollment, revenue, costs)
- **backend-api-specialist** - FastAPI endpoints and API layer

### 4. Frontend Agent (1 agent)
- **frontend-ui-agent** - React UI, components, all 18 modules

### 5. Cross-Cutting Agents (6 agents)
- **governance-versioning-agent** - Budget lifecycle and workflow management
- **reporting-statements-agent** - PCG/IFRS statements and board reports
- **security-rls-agent** - Authentication, MFA, RLS policies
- **data-migration-agent** - ETL and data import from legacy systems
- **performance-agent** - Profiling, optimization, load testing
- **qa-validation-agent** - Test coverage and quality assurance

**Total: 14 specialized agents**

## Agent Dependencies & Orchestration Rules

### Dependency Hierarchy

```
Level 1: SOURCE OF TRUTH (No Dependencies)
├─ product-architect-agent
│
Level 2: ARCHITECTURE (Depends on Product Architect)
├─ system-architect-agent
├─ documentation-training-agent
│
Level 3: FOUNDATION (Depends on System Architect)
├─ database-supabase-agent
├─ security-rls-agent
│
Level 4: IMPLEMENTATION (Depends on Database + Architecture)
├─ backend-engine-agent
├─ governance-versioning-agent
│
Level 5: API & INTEGRATION (Depends on Backend Engine)
├─ backend-api-specialist
├─ reporting-statements-agent
├─ data-migration-agent
│
Level 6: FRONTEND (Depends on API)
├─ frontend-ui-agent
│
Level 7: QUALITY & PERFORMANCE (Depends on All)
├─ qa-validation-agent
├─ performance-agent
│
Level 0: ORCHESTRATOR (Coordinates All)
└─ efir-master-agent
```

### Detailed Agent Dependencies

#### Product Architect Agent
- **Depends on**: None (source of truth)
- **Provides to**: All other agents (business rules, formulas, requirements)
- **Cannot be overridden by**: Any agent
- **Must be consulted before**: Any business logic implementation

#### System Architect Agent
- **Depends on**: product-architect-agent (for requirements)
- **Provides to**: All implementation agents (architecture patterns)
- **Must approve**: All architectural changes
- **Defines**: Folder structure, API contracts, integration patterns

#### Database Supabase Agent
- **Depends on**: system-architect-agent (for architecture), product-architect-agent (for data requirements)
- **Provides to**: backend-engine-agent, backend-api-specialist, security-rls-agent
- **Collaborates with**: security-rls-agent (on RLS policies)
- **Owns**: All SQL, migrations, schema changes

#### Backend Engine Agent
- **Depends on**: product-architect-agent (for formulas), database-supabase-agent (for data access)
- **Provides to**: backend-api-specialist, reporting-statements-agent, frontend-ui-agent (via API)
- **Cannot**: Modify database schema, create APIs, build UI
- **Must**: Implement business logic exactly as specified by product-architect-agent

#### Backend API Specialist
- **Depends on**: backend-engine-agent (for calculations), database-supabase-agent (for data)
- **Provides to**: frontend-ui-agent, data-migration-agent
- **Cannot**: Implement calculation logic (must call backend-engine-agent)
- **Owns**: All FastAPI routes, request/response schemas, API documentation

#### Frontend UI Agent
- **Depends on**: backend-api-specialist (for APIs), system-architect-agent (for component architecture)
- **Provides to**: End users (via UI)
- **Cannot**: Implement backend logic, modify database, create APIs
- **Owns**: All React components, pages, client-side logic

#### Security RLS Agent
- **Depends on**: database-supabase-agent (for schema), product-architect-agent (for access rules)
- **Provides to**: All agents (security guidance)
- **Collaborates with**: database-supabase-agent (on RLS policies), backend-api-specialist (on auth middleware)
- **Must approve**: All security-related changes

#### Governance Versioning Agent
- **Depends on**: product-architect-agent (for workflow rules), backend-engine-agent (for state logic)
- **Provides to**: All agents (lifecycle management)
- **Owns**: Budget version state machine, audit logging, workflow transitions

#### Reporting Statements Agent
- **Depends on**: backend-engine-agent (for calculations), product-architect-agent (for statement formats)
- **Provides to**: End users (via PDF/Excel exports)
- **Cannot**: Implement calculation logic (must call backend-engine-agent)
- **Owns**: PCG/IFRS statement generation, PDF creation, Excel exports

#### Data Migration Agent
- **Depends on**: database-supabase-agent (for schema), backend-api-specialist (for data submission)
- **Provides to**: Database (imported data)
- **Cannot**: Modify schema, implement calculation logic
- **Owns**: ETL scripts, Excel parsers, data import tools

#### Performance Agent
- **Depends on**: All implementation agents (for profiling targets)
- **Provides to**: All agents (optimization recommendations)
- **Cannot**: Modify business logic
- **Owns**: Profiling, caching strategies, load tests, optimization recommendations

#### QA Validation Agent
- **Depends on**: product-architect-agent (for acceptance criteria), all implementation agents (for code to test)
- **Provides to**: All agents (test feedback)
- **Cannot**: Write production code (only tests)
- **Owns**: All tests (unit, integration, E2E), test infrastructure, quality gates

#### Documentation Training Agent
- **Depends on**: All agents (for content to document)
- **Provides to**: Developers and users (documentation)
- **Cannot**: Write code
- **Owns**: User manuals, developer guides, API docs, system diagrams

#### EFIR Master Agent
- **Depends on**: None (orchestrator)
- **Coordinates**: All agents based on task requirements
- **Cannot**: Write code, implement features directly
- **Owns**: Routing logic, multi-agent workflow coordination

## Standard Workflow Patterns

### Pattern 1: New Feature Implementation (Full Stack)

**Sequential Agent Workflow:**

1. **product-architect-agent** - Validates requirements, provides formulas/business rules
2. **system-architect-agent** - Designs architecture, defines API contracts, module structure
3. **database-supabase-agent** - Creates schema, migrations, RLS policies
4. **backend-engine-agent** - Implements calculation logic
5. **backend-api-specialist** - Exposes APIs
6. **frontend-ui-agent** - Builds user interface
7. **security-rls-agent** - Reviews security, adds auth checks
8. **qa-validation-agent** - Creates tests (unit, integration, E2E)
9. **documentation-training-agent** - Updates documentation

**Example: Implementing DHG Workforce Planning Module**

```
User Request: "Implement DHG workforce planning module"

efir-master-agent routes:
  ├─ product-architect-agent → Provide DHG formulas, FTE calculation rules, AEFE cost specs
  ├─ system-architect-agent → Design module architecture, API contracts
  ├─ database-supabase-agent → Create dhg_allocations, teacher_positions tables
  ├─ backend-engine-agent → Implement DHG hours calculation, FTE logic
  ├─ backend-api-specialist → Create /v1/dhg endpoints
  ├─ frontend-ui-agent → Build DHG planning UI with AG Grid
  ├─ security-rls-agent → Add RLS policies for dhg_allocations table
  ├─ qa-validation-agent → Write tests for DHG calculations
  └─ documentation-training-agent → Create DHG user manual
```

### Pattern 2: Bug Fix

**Sequential Agent Workflow:**

1. **Identify domain** - Determine which agent owns the buggy code
2. **Validate business logic** - Consult product-architect-agent if formula/rule unclear
3. **Fix implementation** - Appropriate domain agent fixes the bug
4. **Add regression test** - qa-validation-agent creates test to prevent recurrence
5. **Update docs** - documentation-training-agent updates if needed

**Example: Fix enrollment projection calculation bug**

```
User: "Enrollment projection is calculating wrong growth rate"

efir-master-agent routes:
  ├─ product-architect-agent → Confirm correct growth rate formula
  ├─ backend-engine-agent → Fix enrollment projection calculation
  ├─ qa-validation-agent → Add regression test with correct formula
  └─ documentation-training-agent → Update if formula documentation was wrong
```

### Pattern 3: Data Import

**Sequential Agent Workflow:**

1. **product-architect-agent** - Validates business rules for data mapping
2. **database-supabase-agent** - Confirms schema compatibility
3. **data-migration-agent** - Implements ETL logic, parsers
4. **backend-api-specialist** - Provides endpoints for data submission (if needed)
5. **qa-validation-agent** - Tests import process with sample data

**Example: Import DHG Excel spreadsheet**

```
User: "Import last year's DHG allocations from Excel"

efir-master-agent routes:
  ├─ product-architect-agent → Validate Excel structure matches DHG requirements
  ├─ database-supabase-agent → Verify dhg_allocations table schema
  ├─ data-migration-agent → Parse Excel, map to database schema, import
  └─ qa-validation-agent → Test import with sample Excel file
```

### Pattern 4: Performance Optimization

**Sequential Agent Workflow:**

1. **performance-agent** - Profiles and identifies bottleneck
2. **Relevant domain agent** - Implements optimization (database indexes, caching, algorithm improvement)
3. **qa-validation-agent** - Verifies optimization doesn't break functionality

**Example: Slow DHG calculation**

```
User: "DHG calculation is taking too long"

efir-master-agent routes:
  ├─ performance-agent → Profile DHG calculation, identify bottleneck
  ├─ backend-engine-agent → Optimize calculation algorithm
  ├─ database-supabase-agent → Add indexes if query performance issue
  └─ qa-validation-agent → Verify calculations still correct after optimization
```

### Pattern 5: Security Implementation

**Sequential Agent Workflow:**

1. **product-architect-agent** - Defines access control requirements
2. **security-rls-agent** - Designs security approach (RLS policies, auth flows)
3. **database-supabase-agent** - Implements RLS policies
4. **backend-api-specialist** - Adds auth middleware
5. **frontend-ui-agent** - Implements role-based UI rendering
6. **qa-validation-agent** - Tests security policies

**Example: Implement role-based access for budget versions**

```
User: "Only Finance Director should approve budgets"

efir-master-agent routes:
  ├─ product-architect-agent → Define approval workflow rules
  ├─ security-rls-agent → Design role-based access control
  ├─ database-supabase-agent → Create RLS policies on budget_versions
  ├─ backend-api-specialist → Add auth middleware to approval endpoints
  ├─ frontend-ui-agent → Show/hide approval button based on role
  └─ qa-validation-agent → Test different role permissions
```

## Agent Boundary Enforcement

### What Each Agent MUST NOT Do

| Agent | CANNOT Do |
|-------|-----------|
| product-architect-agent | Write code, implement features |
| system-architect-agent | Implement business logic, define requirements |
| database-supabase-agent | Implement calculation logic, create APIs, build UI |
| backend-engine-agent | Modify database schema, create API endpoints, build UI |
| backend-api-specialist | Implement calculation logic, modify database, build UI |
| frontend-ui-agent | Implement backend logic, modify database, define business rules |
| security-rls-agent | Implement business logic, build UI |
| governance-versioning-agent | Implement calculation logic, modify business rules |
| reporting-statements-agent | Implement calculation logic (must call backend-engine-agent) |
| data-migration-agent | Modify database schema, implement calculation logic |
| performance-agent | Modify business logic |
| qa-validation-agent | Write production code (only tests) |
| documentation-training-agent | Write code |
| efir-master-agent | Write code, implement features directly |

### Violation Examples & Correct Routing

❌ **WRONG**: frontend-ui-agent implements DHG calculation in client-side code
✅ **CORRECT**: frontend-ui-agent calls API from backend-api-specialist, which calls backend-engine-agent

❌ **WRONG**: backend-api-specialist implements sibling discount formula
✅ **CORRECT**: backend-api-specialist calls backend-engine-agent.calculate_revenue()

❌ **WRONG**: data-migration-agent creates new database tables
✅ **CORRECT**: database-supabase-agent creates tables, data-migration-agent only inserts data

❌ **WRONG**: performance-agent changes DHG calculation formula
✅ **CORRECT**: performance-agent optimizes algorithm efficiency without changing formula

## Collaboration Patterns

### Collaborative Agents (Work Together)

**database-supabase-agent + security-rls-agent**
- Jointly design and implement RLS policies
- database-supabase-agent owns SQL, security-rls-agent owns security requirements

**backend-engine-agent + reporting-statements-agent**
- reporting-statements-agent calls backend-engine-agent for all calculations
- Focus: engine = logic, reporting = formatting/presentation

**system-architect-agent + All Implementation Agents**
- system-architect-agent provides patterns, agents implement following patterns
- Agents consult system-architect-agent for architectural questions

**product-architect-agent + All Agents**
- All agents consult product-architect-agent for business rule clarification
- No agent can override product-architect-agent decisions

**qa-validation-agent + All Implementation Agents**
- qa-validation-agent tests all agents' outputs
- Implementation agents fix issues raised by qa-validation-agent

## Conflict Resolution

### When Agents Disagree

1. **Business Logic Dispute**: product-architect-agent has final say (source of truth)
2. **Architectural Dispute**: system-architect-agent has final say
3. **Security Dispute**: security-rls-agent has final say
4. **Data Model Dispute**: database-supabase-agent + system-architect-agent collaborate
5. **Test Coverage Dispute**: qa-validation-agent has final say

### Escalation Path

```
Issue → Relevant Domain Agent → System Architect → Product Architect → User
```

## Agent Communication Protocol

### Information Sharing

**Agents share information through:**
1. **Documentation** - Shared .md files in docs/
2. **Code Contracts** - TypeScript interfaces, Pydantic models, API schemas
3. **Specifications** - PRD, FRS, Technical Spec (owned by product-architect-agent)
4. **Architecture Docs** - ADRs, diagrams (owned by system-architect-agent)

### Status Updates

**Agents provide status updates:**
- "Implementation complete, ready for review"
- "Blocked: waiting for [other agent] to provide [dependency]"
- "Question for [other agent]: [specific question]"

## Quality Gates

### Before Deployment

All features must pass through:

1. ✅ **product-architect-agent** - Validates business requirements compliance
2. ✅ **system-architect-agent** - Approves architectural consistency
3. ✅ **qa-validation-agent** - Confirms 80%+ test coverage, all tests passing
4. ✅ **security-rls-agent** - Approves security implementation
5. ✅ **documentation-training-agent** - Documentation updated

**Deployment Checklist:**
- [ ] Business logic matches product-architect-agent specifications
- [ ] Architecture follows system-architect-agent patterns
- [ ] Database changes include migrations (database-supabase-agent)
- [ ] APIs documented with OpenAPI (backend-api-specialist)
- [ ] UI follows design system (frontend-ui-agent)
- [ ] Security reviewed (security-rls-agent)
- [ ] Tests passing with 80%+ coverage (qa-validation-agent)
- [ ] Documentation updated (documentation-training-agent)

## Agent Invocation Examples

### Direct Invocation (Single Agent)

```
User: "What is the DHG formula for Collège Mathématiques?"
→ Invoke: product-architect-agent
```

```
User: "Create enrollment_data table"
→ Invoke: database-supabase-agent
```

```
User: "Build enrollment projection grid"
→ Invoke: frontend-ui-agent
```

### Multi-Agent Invocation (via efir-master-agent)

```
User: "Implement enrollment projection feature"
→ Invoke: efir-master-agent
→ Routes to: product-architect-agent → system-architect-agent → database-supabase-agent → backend-engine-agent → backend-api-specialist → frontend-ui-agent → qa-validation-agent
```

## Summary: Agent Orchestration Rules

### Core Principles

1. **Single Responsibility** - Each agent has one clear domain
2. **Clear Boundaries** - Agents cannot cross into other domains
3. **Requirements First** - All agents consult product-architect-agent for business rules
4. **Architecture Consistency** - All agents follow system-architect-agent patterns
5. **Security by Design** - security-rls-agent reviews all security-sensitive changes
6. **Quality Gates** - qa-validation-agent validates all changes before deployment
7. **Dependency Order** - Follow the dependency hierarchy for workflows
8. **Collaborative Execution** - Agents work together through well-defined interfaces
9. **Conflict Resolution** - Clear escalation path for disputes
10. **Documentation Always** - documentation-training-agent keeps all docs current

### Success Criteria

An orchestrated workflow is successful when:
- ✅ Right agent for right task (no boundary violations)
- ✅ Dependencies satisfied in correct order
- ✅ All quality gates passed
- ✅ Business rules validated by product-architect-agent
- ✅ Architecture approved by system-architect-agent
- ✅ Tests passing (qa-validation-agent)
- ✅ Security approved (security-rls-agent)
- ✅ Documentation updated (documentation-training-agent)

---

## MCP Server Integration Guide

### Available MCP Servers

| Server | Purpose | Primary Users |
|--------|---------|---------------|
| **supabase** | Supabase Management API (tables, RLS, storage) | database-supabase-agent, security-rls-agent |
| **postgres** | Direct SQL queries | database-supabase-agent, performance-agent |
| **github** | GitHub API (PRs, issues, code) | All agents (for code review) |
| **sentry** | Error monitoring & tracking | qa-validation-agent, performance-agent |
| **context7** | Latest library documentation | All implementation agents |
| **memory** | Persistent knowledge storage | efir-master-agent, all agents |
| **playwright** | E2E browser automation | qa-validation-agent, frontend-ui-agent |
| **filesystem** | Local file operations | All agents |
| **brave-search** | Web search | documentation-training-agent, all agents |
| **sequential-thinking** | Complex multi-step reasoning | efir-master-agent, system-architect-agent |

### Agent-MCP Mapping

#### database-supabase-agent
**Primary MCP Servers**: `supabase`, `postgres`

```
Use Cases:
├─ supabase MCP → Manage tables, RLS policies, storage buckets, edge functions
├─ postgres MCP → Execute raw SQL, inspect schema, run migrations
└─ context7 MCP → Look up latest Supabase/PostgreSQL documentation
```

**Example Usage:**
```
Task: "Create RLS policy for budget_versions table"

1. Use `supabase` MCP to list existing tables and policies
2. Use `postgres` MCP to execute CREATE POLICY SQL
3. Use `supabase` MCP to verify policy was created correctly
```

#### backend-engine-agent
**Primary MCP Servers**: `context7`, `memory`

```
Use Cases:
├─ context7 MCP → Look up Pydantic, Python 3.11+ features, NumPy/Pandas docs
├─ memory MCP → Store/recall calculation formulas, business rules
└─ postgres MCP → Verify data structures for calculations
```

**Example Usage:**
```
Task: "Implement DHG hours calculation engine"

1. Use `memory` MCP to recall DHG formula specifications
2. Use `context7` MCP to look up Pydantic model best practices
3. Implement calculation logic following retrieved patterns
```

#### backend-api-specialist
**Primary MCP Servers**: `context7`, `postgres`

```
Use Cases:
├─ context7 MCP → Look up FastAPI, Pydantic, SQLAlchemy documentation
├─ postgres MCP → Verify database schema for API responses
└─ memory MCP → Recall API design decisions and patterns
```

**Example Usage:**
```
Task: "Create /v1/enrollment/projections endpoint"

1. Use `context7` MCP to look up FastAPI 0.115+ patterns
2. Use `postgres` MCP to verify enrollment_data schema
3. Implement endpoint following latest FastAPI best practices
```

#### frontend-ui-agent
**Primary MCP Servers**: `context7`, `playwright`, `memory`

```
Use Cases:
├─ context7 MCP → Look up React 19, TanStack Router, AG Grid, shadcn/ui docs
├─ playwright MCP → Test UI components, capture screenshots
├─ memory MCP → Recall component patterns, design decisions
└─ github MCP → Check component implementations in other repos
```

**Example Usage:**
```
Task: "Build enrollment planning grid with AG Grid"

1. Use `context7` MCP to look up AG Grid React documentation
2. Use `memory` MCP to recall grid styling patterns used in project
3. Use `playwright` MCP to test grid interactions after implementation
```

#### qa-validation-agent
**Primary MCP Servers**: `playwright`, `sentry`, `postgres`

```
Use Cases:
├─ playwright MCP → Run E2E tests, capture screenshots, test user flows
├─ sentry MCP → Check for errors, analyze error patterns
├─ postgres MCP → Verify test data, check database state
├─ context7 MCP → Look up Vitest, Playwright, pytest documentation
└─ github MCP → Check test patterns in CI workflows
```

**Example Usage:**
```
Task: "Create E2E test for budget approval workflow"

1. Use `playwright` MCP to navigate to budget page
2. Use `playwright` MCP to interact with approval button
3. Use `playwright` MCP to verify state change
4. Use `sentry` MCP to check no errors were logged
5. Use `postgres` MCP to verify database state changed correctly
```

#### security-rls-agent
**Primary MCP Servers**: `supabase`, `postgres`, `context7`

```
Use Cases:
├─ supabase MCP → Manage RLS policies, auth settings, MFA configuration
├─ postgres MCP → Execute RLS policy SQL, test permissions
├─ context7 MCP → Look up Supabase Auth, RLS best practices
└─ memory MCP → Recall security decisions and patterns
```

**Example Usage:**
```
Task: "Implement role-based access for Finance Director"

1. Use `context7` MCP to look up Supabase RLS documentation
2. Use `supabase` MCP to check existing auth configuration
3. Use `postgres` MCP to create RLS policy with role check
4. Use `supabase` MCP to verify policy is active
```

#### performance-agent
**Primary MCP Servers**: `postgres`, `sentry`, `context7`

```
Use Cases:
├─ postgres MCP → Run EXPLAIN ANALYZE, check indexes, query performance
├─ sentry MCP → Analyze performance issues, trace slow requests
├─ context7 MCP → Look up optimization techniques
└─ playwright MCP → Measure frontend performance metrics
```

**Example Usage:**
```
Task: "Optimize slow DHG calculation query"

1. Use `sentry` MCP to identify slow transactions
2. Use `postgres` MCP to run EXPLAIN ANALYZE on query
3. Use `postgres` MCP to create missing indexes
4. Use `sentry` MCP to verify improvement
```

#### data-migration-agent
**Primary MCP Servers**: `postgres`, `supabase`, `filesystem`

```
Use Cases:
├─ postgres MCP → Execute bulk inserts, verify data integrity
├─ supabase MCP → Check table schemas, storage for file uploads
├─ filesystem MCP → Read import files, parse Excel/CSV
└─ context7 MCP → Look up pandas, openpyxl documentation
```

**Example Usage:**
```
Task: "Import DHG allocations from Excel"

1. Use `filesystem` MCP to read Excel file
2. Use `postgres` MCP to verify dhg_allocations schema
3. Use `postgres` MCP to insert parsed data
4. Use `postgres` MCP to verify row counts match
```

#### documentation-training-agent
**Primary MCP Servers**: `context7`, `github`, `brave-search`, `memory`

```
Use Cases:
├─ context7 MCP → Look up library documentation for accuracy
├─ github MCP → Check code for documentation accuracy
├─ brave-search MCP → Research best practices, standards
├─ memory MCP → Recall documentation style guidelines
└─ filesystem MCP → Read/write documentation files
```

**Example Usage:**
```
Task: "Create API documentation for DHG endpoints"

1. Use `github` MCP to read current API implementation
2. Use `context7` MCP to look up OpenAPI documentation standards
3. Use `memory` MCP to recall project documentation conventions
4. Write documentation following retrieved patterns
```

#### efir-master-agent
**Primary MCP Servers**: `memory`, `sequential-thinking`, `github`

```
Use Cases:
├─ memory MCP → Store/recall routing decisions, workflow patterns
├─ sequential-thinking MCP → Plan complex multi-agent workflows
├─ github MCP → Check project status, PRs, issues
└─ sentry MCP → Check system health before routing tasks
```

**Example Usage:**
```
Task: "Route 'implement 5-year planning module' to agents"

1. Use `sequential-thinking` MCP to plan agent workflow
2. Use `memory` MCP to recall similar routing patterns
3. Use `github` MCP to check related issues/PRs
4. Route to agents in correct dependency order
```

#### system-architect-agent
**Primary MCP Servers**: `context7`, `sequential-thinking`, `memory`, `github`

```
Use Cases:
├─ context7 MCP → Look up architecture patterns, framework docs
├─ sequential-thinking MCP → Design complex system architectures
├─ memory MCP → Recall architectural decisions (ADRs)
├─ github MCP → Review existing code architecture
└─ brave-search MCP → Research industry best practices
```

**Example Usage:**
```
Task: "Design API contract for enrollment module"

1. Use `context7` MCP to look up FastAPI/OpenAPI best practices
2. Use `sequential-thinking` MCP to plan contract structure
3. Use `memory` MCP to recall existing API patterns in project
4. Design contract following established conventions
```

#### product-architect-agent
**Primary MCP Servers**: `memory`, `brave-search`, `context7`

```
Use Cases:
├─ memory MCP → Store/recall business rules, formulas, requirements
├─ brave-search MCP → Research AEFE standards, French education regulations
├─ context7 MCP → Look up domain-specific documentation
└─ filesystem MCP → Read PRD, FRS, module specifications
```

**Example Usage:**
```
Task: "Provide DHG calculation formula for Terminale"

1. Use `memory` MCP to recall stored DHG formulas
2. Use `filesystem` MCP to verify against MODULE_08 specification
3. Provide validated formula to requesting agent
```

### MCP Usage Best Practices

#### 1. Always Use Context7 for Latest Documentation
```
❌ WRONG: Assume you know React 19 patterns from training data
✅ CORRECT: Use context7 MCP to look up latest React 19 documentation

Example:
"Use context7 to look up React 19 Suspense best practices"
→ Gets current documentation, not outdated training data
```

#### 2. Use Memory for Cross-Session Knowledge
```
❌ WRONG: Repeat explanations about project decisions each session
✅ CORRECT: Store decisions in memory MCP for future recall

Example:
"Store in memory: 'Project uses kebab-case for all file names'"
→ Can recall this decision in future sessions
```

#### 3. Use Postgres for Data Verification
```
❌ WRONG: Assume database schema from code
✅ CORRECT: Use postgres MCP to verify actual schema

Example:
"Use postgres to describe enrollment_data table"
→ Gets actual column types, constraints, indexes
```

#### 4. Use Playwright for E2E Validation
```
❌ WRONG: Manually describe expected UI behavior
✅ CORRECT: Use playwright MCP to test actual behavior

Example:
"Use playwright to click login button and verify redirect"
→ Tests real browser behavior
```

#### 5. Use Sentry for Error Analysis
```
❌ WRONG: Guess at error causes from logs
✅ CORRECT: Use sentry MCP to analyze error patterns

Example:
"Use sentry to find errors in DHG calculation this week"
→ Gets actual error data with stack traces
```

### MCP Server Quick Reference

| Task | MCP Server | Example Command |
|------|------------|-----------------|
| Look up React 19 docs | context7 | "Look up React 19 useOptimistic hook" |
| Store project decision | memory | "Remember: all API routes use /v1 prefix" |
| Query database | postgres | "SELECT * FROM budget_versions LIMIT 5" |
| Check Supabase tables | supabase | "List all tables in public schema" |
| Run E2E test | playwright | "Navigate to /login and fill email field" |
| Check errors | sentry | "Show unresolved errors from last 24 hours" |
| Search web | brave-search | "AEFE PRRD cost calculation 2024" |
| Complex planning | sequential-thinking | "Plan implementation of 5-year budget module" |
| Check GitHub PR | github | "Show PR #42 review comments" |
| Read local file | filesystem | "Read /docs/MODULES/MODULE_08.md" |

---

**Version**: 1.1.0
**Last Updated**: 2025-12-10
**Maintained By**: EFIR Master Agent
**Total Agents**: 14
**MCP Servers**: 10
