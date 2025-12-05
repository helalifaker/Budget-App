# EFIR Budget App Documentation

**Last Updated**: 2025-12-05
**Total Documents**: 146 organized files

This directory contains all documentation for the EFIR Budget Planning Application, organized by type for easy navigation and discovery.

---

## 📚 Quick Navigation

**📖 [Complete Documentation Index](../DOCUMENTATION_INDEX.md)** - Master navigation for all documentation

**For quick reference:**
- **New to EFIR?** → Start with [User Guide](user-guides/USER_GUIDE.md)
- **Developing?** → See [Developer Guide](developer-guides/DEVELOPER_GUIDE.md)
- **AI Agents?** → Read [CLAUDE.md](../CLAUDE.md) and [Agent Standards](AGENT_DOCUMENTATION_STANDARDS.md)
- **Looking for status?** → Check [Current Status](status/CURRENT_STATUS.md)

---

## Documentation Structure

### 📁 MODULES/ (18 files) - Module Specifications

Complete technical specifications for all 18 modules across 5 layers.

**Configuration Layer (Modules 1-6)**:
- [MODULE_01: System Configuration](MODULES/MODULE_01_SYSTEM_CONFIGURATION.md)
- [MODULE_02: Class Size Parameters](MODULES/MODULE_02_CLASS_SIZE_PARAMETERS.md)
- [MODULE_03: Subject Hours Configuration](MODULES/MODULE_03_SUBJECT_HOURS_CONFIGURATION.md)
- [MODULE_04: Teacher Cost Parameters](MODULES/MODULE_04_TEACHER_COST_PARAMETERS.md)
- [MODULE_05: Fee Structure Configuration](MODULES/MODULE_05_FEE_STRUCTURE_CONFIGURATION.md)
- [MODULE_06: Timetable Constraints](MODULES/MODULE_06_TIMETABLE_CONSTRAINTS.md)

**Planning Layer (Modules 7-12)**:
- [MODULE_07: Enrollment Planning](MODULES/MODULE_07_ENROLLMENT_PLANNING.md)
- [MODULE_08: DHG Workforce Planning](MODULES/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md) ⭐ Core
- [MODULE_09: Facility Planning](MODULES/MODULE_09_FACILITY_PLANNING.md)
- [MODULE_10: Revenue Planning](MODULES/MODULE_10_REVENUE_PLANNING.md)
- [MODULE_11: Cost Planning](MODULES/MODULE_11_COST_PLANNING.md)
- [MODULE_12: CapEx Planning](MODULES/MODULE_12_CAPEX_PLANNING.md)

**Consolidation Layer (Modules 13-14)**:
- [MODULE_13: Budget Consolidation](MODULES/MODULE_13_BUDGET_CONSOLIDATION.md)
- [MODULE_14: Financial Statements](MODULES/MODULE_14_FINANCIAL_STATEMENTS.md)

**Analysis Layer (Modules 15-17)**:
- [MODULE_15: KPIs & Statistical Analysis](MODULES/MODULE_15_STATISTICAL_ANALYSIS.md)
- [MODULE_16: Dashboard Configuration](MODULES/MODULE_16_DASHBOARD_CONFIGURATION.md)
- [MODULE_17: Budget vs Actual](MODULES/MODULE_17_BUDGET_VS_ACTUAL.md)

**Strategic Layer (Module 18)**:
- [MODULE_18: 5-Year Strategic Planning](MODULES/MODULE_18_STRATEGIC_PLANNING.md)

---

### 📁 user-guides/ (3 files) - User Documentation

End-user guides and deployment documentation:
- [USER_GUIDE.md](user-guides/USER_GUIDE.md) - Complete user guide for the application
- [DEPLOYMENT_GUIDE.md](user-guides/DEPLOYMENT_GUIDE.md) - Deployment procedures and setup
- [SUPABASE_SETUP_GUIDE.md](user-guides/SUPABASE_SETUP_GUIDE.md) - Database setup guide

---

### 📁 developer-guides/ (5 files) - Developer Documentation

Technical guides for developers:
- [DEVELOPER_GUIDE.md](developer-guides/DEVELOPER_GUIDE.md) - Developer setup and guidelines ⭐
- [API_DOCUMENTATION.md](developer-guides/API_DOCUMENTATION.md) - API reference and endpoints
- [INTEGRATION_GUIDE.md](developer-guides/INTEGRATION_GUIDE.md) - Integration patterns (Odoo, Skolengo, AEFE)
- [E2E_TESTING_GUIDE.md](developer-guides/E2E_TESTING_GUIDE.md) - E2E testing with Playwright
- [PERFORMANCE_OPTIMIZATIONS.md](developer-guides/PERFORMANCE_OPTIMIZATIONS.md) - Performance guide

---

### 📁 status/ (4 living documents) - Current Status

**Living documents** (updated frequently, timestamps in headers):
- [CURRENT_STATUS.md](status/CURRENT_STATUS.md) - Current work status (updated hourly)
- [REMAINING_WORK.md](status/REMAINING_WORK.md) - Outstanding tasks and issues
- [CODEBASE_REVIEW.md](status/CODEBASE_REVIEW.md) - Code quality review and ratings
- [PRODUCTION_READINESS.md](status/PRODUCTION_READINESS.md) - Production deployment checklist

**Note**: These files have NO dates in filenames - they are continuously updated with timestamp headers.

---

### 📁 testing/ (4 files) - Test Documentation

Test coverage, E2E testing, and validation:
- [TEST_COVERAGE_STRATEGY.md](testing/TEST_COVERAGE_STRATEGY.md) - Coverage goals, plan, maintenance
- [E2E_TESTING_SUMMARY.md](testing/E2E_TESTING_SUMMARY.md) - E2E test results and scenarios
- [CALCULATION_ENGINE_VALIDATION.md](testing/CALCULATION_ENGINE_VALIDATION.md) - Engine validation
- [README.md](testing/README.md) - Testing documentation overview

---

### 📁 agent-work/ (recent reports) - Agent Work Products

**Recent agent-generated reports** (dated snapshots, <30 days old):
- Agent coverage reports (YYYY-MM-DD_agent-{N}_{purpose}.md)
- Implementation progress updates
- Technical analysis reports

**Note**: Reports older than 30 days are archived to `archive/implementation-reports/`

---

### 📁 roadmaps/ (4 files) - Future Planning

Strategic planning and enhancement roadmaps:
- [PRODUCTION_READINESS_ROADMAP.md](roadmaps/PRODUCTION_READINESS_ROADMAP.md)
- [TECH_ENHANCEMENT_ROADMAP.md](roadmaps/TECH_ENHANCEMENT_ROADMAP.md)
- [FOCUSED_ENHANCEMENT_ROADMAP.md](roadmaps/FOCUSED_ENHANCEMENT_ROADMAP.md)
- [DETAILED_IMPLEMENTATION_PLAN.md](roadmaps/DETAILED_IMPLEMENTATION_PLAN.md)

---

### 📁 technical-decisions/ (5 files) - Architecture Decision Records

Technical decisions and ADRs:
- [STACK_VERSION_REVIEW.md](technical-decisions/STACK_VERSION_REVIEW.md)
- [TECH_STACK_UPGRADE_RISK_ASSESSMENT.md](technical-decisions/TECH_STACK_UPGRADE_RISK_ASSESSMENT.md)
- [ERROR_BOUNDARY_IMPLEMENTATION.md](technical-decisions/ERROR_BOUNDARY_IMPLEMENTATION.md)
- [SECURITY_AND_CACHE_FIXES.md](technical-decisions/SECURITY_AND_CACHE_FIXES.md)
- [README.md](technical-decisions/README.md)

---

### 📁 database/ (2 files) - Database Documentation

Database schema and setup:
- [schema_design.md](database/schema_design.md) - Complete database schema
- [setup_guide.md](database/setup_guide.md) - Database setup instructions

---

### 📁 archive/ (65+ files) - Historical Documentation

**Organized historical documents**:

- **[phases/](archive/phases/)** (30+ files) - Phase completion summaries
  - Format: YYYY-MM-DD_phase-{N}-{description}.md
  - Dates: November 2025 - December 2025

- **[implementation-reports/](archive/implementation-reports/)** (20+ files) - Implementation reports
  - Format: YYYY-MM-DD_{implementation-name}.md
  - Technical implementation documentation

- **[status-reports/](archive/status-reports/)** (15+ files) - Historical status snapshots
  - Format: YYYY-MM-DD_{status-type}.md
  - Old status snapshots (>90 days)

**See [archive/README.md](archive/README.md) for archive organization details.**

---

## 📋 Governance Documents

### Documentation Standards
- **[DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md)** - Complete governance (structure, templates, lifecycle)
- **[AGENT_DOCUMENTATION_STANDARDS.md](AGENT_DOCUMENTATION_STANDARDS.md)** - Agent-specific rules

### Document Templates
See [templates/](templates/) for:
- Agent coverage report template
- Living status document template
- Phase completion summary template
- Implementation report template
- Technical decision record (ADR) template

---

## 🔍 Finding Documentation

### By Audience

**End Users**:
1. [User Guide](user-guides/USER_GUIDE.md)
2. [Deployment Guide](user-guides/DEPLOYMENT_GUIDE.md)

**Developers**:
1. [Developer Guide](developer-guides/DEVELOPER_GUIDE.md)
2. [API Documentation](developer-guides/API_DOCUMENTATION.md)
3. [Module Specifications](MODULES/)

**AI Agents**:
1. [CLAUDE.md](../CLAUDE.md) - Primary reference
2. [Agent Documentation Standards](AGENT_DOCUMENTATION_STANDARDS.md)
3. [Agent Orchestration](../.claude/AGENT_ORCHESTRATION.md)

**Project Managers**:
1. [Current Status](status/CURRENT_STATUS.md)
2. [Remaining Work](status/REMAINING_WORK.md)
3. [Production Readiness](status/PRODUCTION_READINESS.md)

### By Topic

**Budget Planning Workflow**:
MODULE_07 (Enrollment) → MODULE_08 (DHG) → MODULE_11 (Costs) → MODULE_13 (Consolidation)

**Financial Reporting**:
MODULE_14 (Statements), MODULE_15 (KPIs), MODULE_16 (Dashboards)

**Configuration**:
MODULE_01-06 (System config, class sizes, subject hours, fees, etc.)

**Testing**:
[testing/](testing/), [developer-guides/E2E_TESTING_GUIDE.md](developer-guides/E2E_TESTING_GUIDE.md)

**Architecture**:
[../foundation/](../foundation/), [technical-decisions/](technical-decisions/)

---

## 📝 Document Naming Conventions

| Document Type | Format | Example |
|---------------|--------|---------|
| Living docs (no date) | `{NAME}.md` | CURRENT_STATUS.md |
| Agent reports | `YYYY-MM-DD_agent-{N}_{purpose}.md` | 2025-12-05_agent-13_coverage.md |
| Phase summaries | `YYYY-MM-DD_phase-{N}-{desc}.md` | 2025-12-05_phase-1-completion.md |
| Implementation reports | `YYYY-MM-DD_{name}.md` | 2025-12-03_database-schema-fix.md |
| Guides | `{NAME}_GUIDE.md` | USER_GUIDE.md |
| Reference (versioned) | `{NAME}_v{major}_{minor}.md` | EFIR_Budget_App_PRD_v1.2.md |

---

## 🔄 Maintenance

**Daily**: Update living status docs ([status/](status/))
**Weekly**: Review agent reports, archive old work
**Monthly**: Archive completed work (>30 days), update cross-refs
**Quarterly**: Full audit, consolidation review

**See [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) for complete maintenance processes.**

---

**Last Review**: 2025-12-05
**Next Review**: 2025-12-12 (weekly)
**Maintained By**: documentation-training-agent + tech lead
