# EFIR Budget App - Documentation Index

**Last Updated**: 2025-12-09
**Total Documents**: 146 organized files

Welcome to the EFIR Budget Planning Application documentation. This index provides navigation to all documentation across the project.

---

## 🚀 Quick Start

**New to EFIR?** Start here:
1. [README.md](README.md) - Project overview and quickstart
2. [docs/user-guides/USER_GUIDE.md](docs/user-guides/USER_GUIDE.md) - User documentation
3. [docs/developer-guides/DEVELOPER_GUIDE.md](docs/developer-guides/DEVELOPER_GUIDE.md) - Developer setup

**Developing?** Essential references:
- [CLAUDE.md](CLAUDE.md) - **Primary development reference** (commands, patterns, rules)
- [docs/MODULES/](docs/MODULES/) - All 18 module specifications
- [.claude/AGENT_ORCHESTRATION.md](.claude/AGENT_ORCHESTRATION.md) - Agent system guide

---

## 📁 Documentation Structure

### Foundation Documents (7 files)

Core specifications and requirements that define EFIR.

| Document | Purpose | Lines |
|----------|---------|-------|
| [EFIR_Budget_App_PRD_v1.2.md](foundation/EFIR_Budget_App_PRD_v1.2.md) | Product Requirements Document | 173 |
| [EFIR_Budget_App_TSD_v1.2.md](foundation/EFIR_Budget_App_TSD_v1.2.md) | Technical Specification Document | 242 |
| [EFIR_Module_Technical_Specification.md](foundation/EFIR_Module_Technical_Specification.md) ⭐ | Complete 18-module specification | 1,996 |
| [EFIR_Budget_Planning_Requirements_v1.2.md](foundation/EFIR_Budget_Planning_Requirements_v1.2.md) | Detailed planning requirements | 496 |
| [EFIR_Workforce_Planning_Logic.md](foundation/EFIR_Workforce_Planning_Logic.md) ⭐ | DHG methodology and formulas | 425 |
| [EFIR_Data_Summary_v2.md](foundation/EFIR_Data_Summary_v2.md) | Historical data and reference | 451 |
| [README.md](foundation/README.md) | Foundation docs guide | - |

---

### Module Specifications (18 files)

Detailed specifications for each of the 18 modules across 5 layers.

**Configuration Layer (Modules 1-6)**:
- [MODULE_01: System Configuration](docs/MODULES/MODULE_01_SYSTEM_CONFIGURATION.md) - Academic cycles, levels, subjects
- [MODULE_02: Class Size Parameters](docs/MODULES/MODULE_02_CLASS_SIZE_PARAMETERS.md) - Min/max/target class sizes
- [MODULE_03: Subject Hours Configuration](docs/MODULES/MODULE_03_SUBJECT_HOURS_CONFIGURATION.md) - Hours per subject
- [MODULE_04: Teacher Cost Parameters](docs/MODULES/MODULE_04_TEACHER_COST_PARAMETERS.md) - Teacher salary configurations
- [MODULE_05: Fee Structure Configuration](docs/MODULES/MODULE_05_FEE_STRUCTURE_CONFIGURATION.md) - Tuition fees
- [MODULE_06: Timetable Constraints](docs/MODULES/MODULE_06_TIMETABLE_CONSTRAINTS.md) - Scheduling rules

**Planning Layer (Modules 7-12)**:
- [MODULE_07: Enrollment Planning](docs/MODULES/MODULE_07_ENROLLMENT_PLANNING.md) - Student projections
- [MODULE_08: DHG Workforce Planning](docs/MODULES/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md) ⭐ **Core calculation**
- [MODULE_09: Facility Planning](docs/MODULES/MODULE_09_FACILITY_PLANNING.md) - Classroom allocation
- [MODULE_10: Revenue Planning](docs/MODULES/MODULE_10_REVENUE_PLANNING.md) - Fee-based revenue projections
- [MODULE_11: Cost Planning](docs/MODULES/MODULE_11_COST_PLANNING.md) - Personnel and operational costs
- [MODULE_12: CapEx Planning](docs/MODULES/MODULE_12_CAPEX_PLANNING.md) - Capital expenditure planning

**Consolidation Layer (Modules 13-14)**:
- [MODULE_13: Budget Consolidation](docs/MODULES/MODULE_13_BUDGET_CONSOLIDATION.md) - Multi-module aggregation
- [MODULE_14: Financial Statements](docs/MODULES/MODULE_14_FINANCIAL_STATEMENTS.md) - PCG/IFRS statements

**Analysis Layer (Modules 15-17)**:
- [MODULE_15: KPIs & Statistical Analysis](docs/MODULES/MODULE_15_STATISTICAL_ANALYSIS.md) - Key performance indicators
- [MODULE_16: Dashboard Configuration](docs/MODULES/MODULE_16_DASHBOARD_CONFIGURATION.md) - Analytics dashboards
- [MODULE_17: Budget vs Actual](docs/MODULES/MODULE_17_BUDGET_VS_ACTUAL.md) - Variance analysis

**Strategic Layer (Module 18)**:
- [MODULE_18: 5-Year Strategic Planning](docs/MODULES/MODULE_18_STRATEGIC_PLANNING.md) - Long-term planning

---

### User Guides (3 files)

End-user documentation and deployment guides.

- [docs/user-guides/USER_GUIDE.md](docs/user-guides/USER_GUIDE.md) - Complete user guide
- [docs/user-guides/DEPLOYMENT_GUIDE.md](docs/user-guides/DEPLOYMENT_GUIDE.md) - Deployment procedures
- [docs/user-guides/SUPABASE_SETUP_GUIDE.md](docs/user-guides/SUPABASE_SETUP_GUIDE.md) - Database setup

---

### Developer Guides (5 files)

Developer documentation and technical guides.

- [docs/developer-guides/DEVELOPER_GUIDE.md](docs/developer-guides/DEVELOPER_GUIDE.md) ⭐ - Development setup
- [docs/developer-guides/API_DOCUMENTATION.md](docs/developer-guides/API_DOCUMENTATION.md) - API reference
- [docs/developer-guides/INTEGRATION_GUIDE.md](docs/developer-guides/INTEGRATION_GUIDE.md) - Odoo/Skolengo/AEFE integration
- [docs/developer-guides/E2E_TESTING_GUIDE.md](docs/developer-guides/E2E_TESTING_GUIDE.md) - E2E testing with Playwright
- [docs/developer-guides/PERFORMANCE_OPTIMIZATIONS.md](docs/developer-guides/PERFORMANCE_OPTIMIZATIONS.md) - Performance guide

---

### Current Status (4 living documents)

Always-current status documents (updated frequently with timestamps).

- [docs/status/CURRENT_STATUS.md](docs/status/CURRENT_STATUS.md) - Current work status (updated hourly)
- [docs/status/REMAINING_WORK.md](docs/status/REMAINING_WORK.md) - Outstanding tasks
- [docs/status/CODEBASE_REVIEW.md](docs/status/CODEBASE_REVIEW.md) - Code quality review
- [docs/status/PRODUCTION_READINESS.md](docs/status/PRODUCTION_READINESS.md) - Production checklist

**Note**: These files have **no dates in filenames** - they are living documents with timestamp headers.

---

### Testing Documentation (4 files)

Test coverage, E2E testing, and validation.

- [docs/testing/TEST_COVERAGE_STRATEGY.md](docs/testing/TEST_COVERAGE_STRATEGY.md) ⭐ - Coverage goals & plan
- [docs/testing/E2E_TESTING_SUMMARY.md](docs/testing/E2E_TESTING_SUMMARY.md) - E2E test results
- [docs/testing/CALCULATION_ENGINE_VALIDATION.md](docs/testing/CALCULATION_ENGINE_VALIDATION.md) - Engine validation
- [docs/testing/README.md](docs/testing/README.md) - Testing documentation overview

---

### Technical Decisions (5 files)

Architecture decision records and technical choices.

- [docs/technical-decisions/STACK_VERSION_REVIEW.md](docs/technical-decisions/STACK_VERSION_REVIEW.md) - Technology stack review
- [docs/technical-decisions/TECH_STACK_UPGRADE_RISK_ASSESSMENT.md](docs/technical-decisions/TECH_STACK_UPGRADE_RISK_ASSESSMENT.md) - Upgrade risk analysis
- [docs/technical-decisions/ERROR_BOUNDARY_IMPLEMENTATION.md](docs/technical-decisions/ERROR_BOUNDARY_IMPLEMENTATION.md) - Error boundary pattern
- [docs/technical-decisions/SECURITY_AND_CACHE_FIXES.md](docs/technical-decisions/SECURITY_AND_CACHE_FIXES.md) - Security improvements
- [docs/technical-decisions/README.md](docs/technical-decisions/README.md) - Technical decisions overview

---

### Roadmaps (4 files)

Future planning and enhancement roadmaps.

- [docs/roadmaps/PRODUCTION_READINESS_ROADMAP.md](docs/roadmaps/PRODUCTION_READINESS_ROADMAP.md) - Path to production
- [docs/roadmaps/TECH_ENHANCEMENT_ROADMAP.md](docs/roadmaps/TECH_ENHANCEMENT_ROADMAP.md) - Technical enhancements
- [docs/roadmaps/FOCUSED_ENHANCEMENT_ROADMAP.md](docs/roadmaps/FOCUSED_ENHANCEMENT_ROADMAP.md) - Prioritized improvements
- [docs/roadmaps/DETAILED_IMPLEMENTATION_PLAN.md](docs/roadmaps/DETAILED_IMPLEMENTATION_PLAN.md) - Implementation details

---

### Agent Work Products (Recent Reports)

Recent agent-generated reports (dated snapshots, <30 days old).

Current reports in [docs/agent-work/](docs/agent-work/):
- `2025-12-05_agent-13_final-coverage-analysis.md` - Final coverage analysis
- `2025-12-05_coverage-progress-update.md` - Coverage progress update

**Historical reports** (>30 days): See [docs/archive/implementation-reports/](docs/archive/implementation-reports/)

---

### Database Documentation (2 files)

Database schema design and setup.

- [docs/database/schema_design.md](docs/database/schema_design.md) - Complete database schema
- [docs/database/setup_guide.md](docs/database/setup_guide.md) - Database setup instructions

---

### Component Documentation

Backend and frontend specific documentation.

**Backend** ([backend/](backend/)):
- [backend/README.md](backend/README.md) - Backend architecture and API docs
- [backend/QUICK_START.md](backend/QUICK_START.md) - Quick start guide
- [backend/docs/TESTING.md](backend/docs/TESTING.md) - Testing guide
- [backend/docs/INTEGRATION_GUIDE.md](backend/docs/INTEGRATION_GUIDE.md) - Integration patterns
- [backend/docs/CELL_STORAGE_GUIDE.md](backend/docs/CELL_STORAGE_GUIDE.md) - Cell storage documentation
- [backend/docs/MATERIALIZED_VIEWS_GUIDE.md](backend/docs/MATERIALIZED_VIEWS_GUIDE.md) - Materialized views
- [backend/tests/README.md](backend/tests/README.md) - Test suite documentation
- [backend/tests/README_TEST_HELPERS.md](backend/tests/README_TEST_HELPERS.md) - Test helper utilities

**Frontend** ([frontend/](frontend/)):
- [frontend/README.md](frontend/README.md) - Frontend architecture
- [frontend/BUNDLE_ARCHITECTURE.md](frontend/BUNDLE_ARCHITECTURE.md) - Bundle analysis
- [frontend/BUNDLE_OPTIMIZATION_QUICK_REFERENCE.md](frontend/BUNDLE_OPTIMIZATION_QUICK_REFERENCE.md) - Bundle optimization

---

### Agent System (15 documents)

14 specialized agents + orchestration guide.

- [.claude/AGENT_ORCHESTRATION.md](.claude/AGENT_ORCHESTRATION.md) ⭐ - Master orchestration guide
- [.claude/agents/backend-api-specialist.md](.claude/agents/backend-api-specialist.md) - FastAPI specialist
- [.claude/agents/backend-engine-agent.md](.claude/agents/backend-engine-agent.md) - Calculation engines
- [.claude/agents/data-migration-agent.md](.claude/agents/data-migration-agent.md) - Data imports
- [.claude/agents/database-supabase-agent.md](.claude/agents/database-supabase-agent.md) - Database & RLS
- [.claude/agents/documentation-training-agent.md](.claude/agents/documentation-training-agent.md) - Documentation
- [.claude/agents/efir-master-agent.md](.claude/agents/efir-master-agent.md) - Orchestrator
- [.claude/agents/frontend-ui-agent.md](.claude/agents/frontend-ui-agent.md) - React UI
- [.claude/agents/governance-versioning-agent.md](.claude/agents/governance-versioning-agent.md) - Budget lifecycle
- [.claude/agents/performance-agent.md](.claude/agents/performance-agent.md) - Performance optimization
- [.claude/agents/product-architect-agent.md](.claude/agents/product-architect-agent.md) - Business rules (SOURCE OF TRUTH)
- [.claude/agents/qa-validation-agent.md](.claude/agents/qa-validation-agent.md) - Testing & QA
- [.claude/agents/reporting-statements-agent.md](.claude/agents/reporting-statements-agent.md) - PCG/IFRS statements
- [.claude/agents/security-rls-agent.md](.claude/agents/security-rls-agent.md) - Security & auth
- [.claude/agents/system-architect-agent.md](.claude/agents/system-architect-agent.md) - Architecture

---

### Archive (65+ historical documents)

Historical documents organized by type.

- **[docs/archive/phases/](docs/archive/phases/)** (30+ files) - Phase completion summaries
  - Format: `YYYY-MM-DD_phase-{N}-{description}.md`
  - Dates: November 2025 - December 2025

- **[docs/archive/implementation-reports/](docs/archive/implementation-reports/)** (20+ files) - Implementation reports
  - Format: `YYYY-MM-DD_{implementation-name}.md`
  - Technical implementation documentation

- **[docs/archive/status-reports/](docs/archive/status-reports/)** (15+ files) - Historical status snapshots
  - Format: `YYYY-MM-DD_{status-type}.md`
  - Old status snapshots (>90 days)

**See [docs/archive/README.md](docs/archive/README.md) for archive navigation guide.**

---

## 📚 Documentation by Audience

### For End Users
1. [User Guide](docs/user-guides/USER_GUIDE.md) - How to use the application
2. [Deployment Guide](docs/user-guides/DEPLOYMENT_GUIDE.md) - How to deploy

### For Developers
1. [Developer Guide](docs/developer-guides/DEVELOPER_GUIDE.md) ⭐ - **Start here**
2. [CLAUDE.md](CLAUDE.md) - **Daily reference** (commands, patterns, standards)
3. [API Documentation](docs/developer-guides/API_DOCUMENTATION.md) - API reference
4. [Module Specifications](docs/MODULES/) - Business logic reference
5. [Backend README](backend/README.md) - Backend setup
6. [Frontend README](frontend/README.md) - Frontend setup

### For AI Agents
1. [CLAUDE.md](CLAUDE.md) ⭐ - **Primary reference** (1000+ lines)
2. [Agent Orchestration](.claude/AGENT_ORCHESTRATION.md) - Agent system rules
3. [Agent Documentation Standards](docs/AGENT_DOCUMENTATION_STANDARDS.md) - Where to create docs
4. [Module Specifications](docs/MODULES/) - Business rules (**SOURCE OF TRUTH**)
5. [Individual Agent Configs](.claude/agents/) - Your specific agent file

### For Project Managers
1. [Current Status](docs/status/CURRENT_STATUS.md) - What's happening now
2. [Remaining Work](docs/status/REMAINING_WORK.md) - What's left to do
3. [Production Readiness](docs/status/PRODUCTION_READINESS.md) - Production checklist
4. [Roadmaps](docs/roadmaps/) - Future plans

### For QA/Testing
1. [Test Coverage Strategy](docs/testing/TEST_COVERAGE_STRATEGY.md) - Coverage goals
2. [E2E Testing Guide](docs/developer-guides/E2E_TESTING_GUIDE.md) - E2E testing
3. [Calculation Engine Validation](docs/testing/CALCULATION_ENGINE_VALIDATION.md) - Engine validation
4. [Backend Testing Guide](backend/docs/TESTING.md) - Backend tests

---

## 🔍 Finding Documents

### By Topic

**Budget Planning Workflow**:
[MODULE_07](docs/MODULES/MODULE_07_ENROLLMENT_PLANNING.md) (Enrollment) →
[MODULE_08](docs/MODULES/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md) (DHG) →
[MODULE_11](docs/MODULES/MODULE_11_COST_PLANNING.md) (Costs) →
[MODULE_13](docs/MODULES/MODULE_13_BUDGET_CONSOLIDATION.md) (Consolidation)

**Financial Reporting**:
- [MODULE_14](docs/MODULES/MODULE_14_FINANCIAL_STATEMENTS.md) (PCG/IFRS Statements)
- [MODULE_15](docs/MODULES/MODULE_15_STATISTICAL_ANALYSIS.md) (KPIs)
- [MODULE_16](docs/MODULES/MODULE_16_DASHBOARD_CONFIGURATION.md) (Dashboards)

**Configuration**:
[MODULE_01-06](docs/MODULES/) - System config, class sizes, subject hours, teacher costs, fees, timetable

**Testing**:
- [docs/testing/](docs/testing/) - Test coverage and strategy
- [backend/docs/TESTING.md](backend/docs/TESTING.md) - Backend testing
- [docs/developer-guides/E2E_TESTING_GUIDE.md](docs/developer-guides/E2E_TESTING_GUIDE.md) - E2E testing

**Architecture**:
- [foundation/](foundation/) - Core specifications
- [.claude/AGENT_ORCHESTRATION.md](.claude/AGENT_ORCHESTRATION.md) - Agent architecture
- [docs/technical-decisions/](docs/technical-decisions/) - ADRs and tech choices

**Status & Progress**:
- [docs/status/](docs/status/) - Current status (living docs)
- [docs/archive/status-reports/](docs/archive/status-reports/) - Historical snapshots

### By File Type

- **Root .md files**: Only 3 essential files (README.md, CLAUDE.md, DOCUMENTATION_INDEX.md)
- **Foundation docs** (foundation/): Core specifications (PRD, TSD, Requirements, etc.)
- **User/Developer guides** (docs/): Organized by audience and type
- **Module specs** (docs/MODULES/): All 18 module specifications
- **Backend/Frontend docs** (backend/, frontend/): Component-specific documentation
- **Agent configs** (.claude/): Agent system documentation
- **Archive** (docs/archive/): Historical documentation

---

## 📋 Documentation Governance

### Standards & Processes
- [docs/DOCUMENTATION_GUIDE.md](docs/DOCUMENTATION_GUIDE.md) - Complete governance document
- [docs/AGENT_DOCUMENTATION_STANDARDS.md](docs/AGENT_DOCUMENTATION_STANDARDS.md) - Agent-specific rules

### Document Templates
See [docs/templates/](docs/templates/) for:
- Agent coverage report template
- Living status document template
- Phase completion summary template
- Implementation report template
- Technical decision record (ADR) template

### Document Naming Conventions

| Document Type | Format | Example |
|---------------|--------|---------|
| Living docs (no date) | `{NAME}.md` | CURRENT_STATUS.md |
| Agent reports | `YYYY-MM-DD_agent-{N}_{purpose}.md` | 2025-12-05_agent-13_coverage.md |
| Phase summaries | `YYYY-MM-DD_phase-{N}-{desc}.md` | 2025-12-05_phase-1-completion.md |
| Implementation reports | `YYYY-MM-DD_{name}.md` | 2025-12-03_database-schema-fix.md |
| Guides | `{NAME}_GUIDE.md` | USER_GUIDE.md |
| Reference (versioned) | `{NAME}_v{major}_{minor}.md` | EFIR_Budget_App_PRD_v1.2.md |

### Maintenance Schedule
- **Daily**: Update living status docs
- **Weekly**: Review agent reports, archive old work
- **Monthly**: Archive completed work, update cross-refs
- **Quarterly**: Full audit, consolidation review

**See [docs/DOCUMENTATION_GUIDE.md](docs/DOCUMENTATION_GUIDE.md) for complete maintenance processes.**

---

## 🎯 Quick Reference Tables

### Essential Files for Development

| Purpose | File |
|---------|------|
| **Daily reference** | [CLAUDE.md](CLAUDE.md) |
| **Agent system** | [.claude/AGENT_ORCHESTRATION.md](.claude/AGENT_ORCHESTRATION.md) |
| **Setup guide** | [docs/developer-guides/DEVELOPER_GUIDE.md](docs/developer-guides/DEVELOPER_GUIDE.md) |
| **API reference** | [docs/developer-guides/API_DOCUMENTATION.md](docs/developer-guides/API_DOCUMENTATION.md) |
| **Business rules** | [docs/MODULES/](docs/MODULES/) (18 module specs) |
| **DHG calculation** | [MODULE_08](docs/MODULES/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md) |
| **Current status** | [docs/status/CURRENT_STATUS.md](docs/status/CURRENT_STATUS.md) |

### Where Agents Create Documentation

| Agent | Document Type | Location |
|-------|---------------|----------|
| qa-validation-agent | Coverage reports | `docs/agent-work/` |
| efir-master-agent | Coordination reports | `docs/agent-work/` |
| backend-*-agent | Implementation reports | `docs/agent-work/` |
| system-architect-agent | ADRs | `docs/technical-decisions/` |
| documentation-training-agent | User/Dev guides | `docs/user-guides/` or `docs/developer-guides/` |
| product-architect-agent | Module specs | `docs/MODULES/` |

**See [docs/AGENT_DOCUMENTATION_STANDARDS.md](docs/AGENT_DOCUMENTATION_STANDARDS.md) for complete agent rules.**

---

**Last Updated**: 2025-12-09
**Next Review**: 2025-12-16 (weekly)
**Maintained By**: documentation-training-agent + tech lead
