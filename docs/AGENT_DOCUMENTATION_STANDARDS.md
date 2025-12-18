# Agent Documentation Standards

**Version**: 1.0
**Last Updated**: 2025-12-05
**Authority**: documentation-training-agent
**Enforcement**: All AI agents must follow these standards

---

## Purpose

This document defines exactly where and how each of the 9 specialized agents should create documentation. These standards prevent documentation chaos and ensure consistency across all agent-generated work products.

**Critical Rule**: All agents MUST follow these standards. Deviations will be corrected immediately.

---

## Agent Documentation Matrix

| Agent | Creates What | Where | Naming Pattern | Archive After |
|-------|--------------|-------|----------------|---------------|
| product-architect-agent | Module spec updates | docs/modules/ | MODULE_{NN}_{NAME}.md (update existing) | Old version to archive |
| product-architect-agent | Requirements updates | foundation/ | {REQUIREMENT_DOC}_v{version}.md | Old version to archive |
| Plan | Architecture decisions | docs/technical-decisions/ | ADR-{NN}_{DECISION}.md | Never (reference doc) |
| Plan | Implementation plans | docs/planning/ | {PLAN_NAME}.md | Never (reference doc) |
| Explore | N/A (read-only agent) | N/A | N/A | N/A |
| frontend-ui-agent | Implementation reports | docs/agent-work/ | YYYY-MM-DD_frontend-ui_{implementation}.md | 30 days after validation |
| frontend-ui-agent | Component documentation | Update existing docs | frontend/README.md, component comments | Never |
| performance-agent | Performance reports | docs/agent-work/ | YYYY-MM-DD_performance_{scope}.md | 30 days after optimization |
| performance-agent | Optimization guides | docs/developer-guides/ | Update PERFORMANCE_OPTIMIZATIONS.md | Never (living doc) |
| qa-validation-agent | Coverage reports | docs/agent-work/ | YYYY-MM-DD_agent-{N}_coverage-{scope}.md | 30 days if superseded |
| qa-validation-agent | Phase summaries | Create in docs/agent-work/, then archive | YYYY-MM-DD_phase-{N}-{description}.md | Immediate upon completion |
| qa-validation-agent | Coverage strategy updates | docs/testing/ | TEST_COVERAGE_STRATEGY.md (update existing) | Never (living doc) |
| documentation-training-agent | User guides | docs/user-guides/ | {NAME}_GUIDE.md | Never (reference doc) |
| documentation-training-agent | Developer guides | docs/developer-guides/ | {NAME}_GUIDE.md | Never (reference doc) |
| documentation-training-agent | API documentation | docs/developer-guides/ | API_DOCUMENTATION.md (update existing) | Never (living reference) |
| general-purpose | Research reports | docs/agent-work/ | YYYY-MM-DD_research_{topic}.md | 30 days after completion |
| claude-code-guide | N/A (guidance only) | N/A | N/A | N/A |

---

## Agent-Specific Guidelines

### qa-validation-agent

**Primary Responsibility**: Test coverage reports and quality assurance

**Creates**:
1. **Coverage Reports** (Snapshot)
   - **Location**: `docs/agent-work/`
   - **Naming**: `YYYY-MM-DD_agent-{N}_coverage-{scope}.md`
   - **Template**: Use Agent Coverage Report template
   - **Frequency**: After major test expansions
   - **Archive**: 30 days if superseded by newer coverage report

2. **Phase Completion Summaries** (Snapshot)
   - **Location**: Create in `docs/agent-work/`, then move to `docs/archive/phases/`
   - **Naming**: `YYYY-MM-DD_phase-{N}-{description}.md`
   - **Template**: Use Phase Completion Summary template
   - **Frequency**: At end of each development phase
   - **Archive**: Immediately upon phase completion

3. **Coverage Strategy Updates** (Living)
   - **Location**: `docs/testing/`
   - **File**: `TEST_COVERAGE_STRATEGY.md` (update existing)
   - **Frequency**: Monthly or after major coverage changes
   - **Archive**: Never (living document)

**Examples**:
- ✅ `docs/agent-work/2025-12-05_agent-13_final-coverage-analysis.md`
- ✅ `docs/archive/phases/2025-12-05_phase-1-completion.md`
- ✅ Update `docs/testing/TEST_COVERAGE_STRATEGY.md` with timestamp header

---

### documentation-training-agent

**Primary Responsibility**: User and developer guides, training materials

**Creates**:
1. **User Guides** (Reference)
   - **Location**: `docs/user-guides/`
   - **Naming**: `{NAME}_GUIDE.md`
   - **Frequency**: As needed for new features
   - **Archive**: Never (maintain and version instead)

2. **Developer Guides** (Reference)
   - **Location**: `docs/developer-guides/`
   - **Naming**: `{NAME}_GUIDE.md`
   - **Frequency**: As needed for new patterns
   - **Archive**: Never (maintain and version instead)

3. **API Documentation** (Living Reference)
   - **Location**: `docs/developer-guides/`
   - **File**: `API_DOCUMENTATION.md` (update existing)
   - **Frequency**: When APIs change
   - **Archive**: Never

**Examples**:
- ✅ `docs/user-guides/USER_GUIDE.md`
- ✅ `docs/developer-guides/INTEGRATION_GUIDE.md`
- ✅ Update `docs/developer-guides/API_DOCUMENTATION.md`

---

### Plan

**Primary Responsibility**: Architecture decisions and implementation planning

**Creates**:
1. **Architecture Decision Records (ADRs)** (Reference)
   - **Location**: `docs/technical-decisions/`
   - **Naming**: `ADR-{NN}_{DECISION}.md` (sequential numbering)
   - **Template**: Use Technical Decision Record template
   - **Frequency**: For all significant architectural decisions
   - **Archive**: Never (historical record)

2. **Implementation Plans** (Reference)
   - **Location**: `docs/planning/`
   - **Naming**: `{PLAN_NAME}.md`
   - **Frequency**: When planning major features
   - **Archive**: Never (reference docs)

**Examples**:
- ✅ `docs/technical-decisions/ADR-001_MODULE_ARCHITECTURE.md`
- ✅ `docs/planning/REFACTORING_MASTER_PLAN.md`

---

### general-purpose

**Primary Responsibility**: Complex multi-step tasks, research, and code search

**Creates**:
1. **Research Reports** (Snapshot)
   - **Location**: `docs/agent-work/`
   - **Naming**: `YYYY-MM-DD_research_{topic}.md`
   - **Template**: Use Implementation Report template
   - **Frequency**: After research tasks
   - **Archive**: 30 days after completion

**Examples**:
- ✅ `docs/agent-work/2025-12-05_research_dependency-analysis.md`

---

### frontend-ui-agent

**Primary Responsibility**: Frontend implementation and UI component reports

**Creates**:
1. **Implementation Reports** (Snapshot)
   - **Location**: `docs/agent-work/`
   - **Naming**: `YYYY-MM-DD_frontend-ui_{implementation}.md`
   - **Template**: Use Implementation Report template
   - **Frequency**: After significant UI implementations
   - **Archive**: 30 days after validation

2. **Component Documentation** (Living)
   - **Location**: In-code comments + `frontend/README.md`
   - **Frequency**: When creating new components
   - **Archive**: Never (maintained in codebase)

**Examples**:
- ✅ `docs/agent-work/2025-11-28_frontend-ui_enrollment-dashboard.md`
- ✅ Update `frontend/README.md` with new component patterns

---

### product-architect-agent

**Primary Responsibility**: Business requirements and module specifications

**Creates**:
1. **Module Specification Updates** (Reference)
   - **Location**: `docs/modules/`
   - **File**: `MODULE_{NN}_{NAME}.md` (update existing)
   - **Frequency**: When business rules change
   - **Archive**: Create versioned copy before major changes
   - **Note**: SOURCE OF TRUTH for business logic

2. **Requirements Updates** (Reference)
   - **Location**: `foundation/`
   - **Naming**: `{REQUIREMENT_DOC}_v{version}.md`
   - **Frequency**: On major requirement changes
   - **Archive**: Old versions to archive/

**Examples**:
- ✅ Update `docs/modules/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md`
- ✅ Archive old version, create `foundation/EFIR_Budget_App_PRD_v1.3.md`

---

## Update vs Create New Rules

### When to Update Existing Document

**Update** (don't create new) if:
- Document is a living document (CURRENT_STATUS.md, etc.)
- Document is a reference guide (USER_GUIDE.md, API_DOCUMENTATION.md)
- Document is a module spec (MODULE_*.md)
- Document is a versioned foundation doc (create new version, not new doc)

**Process**:
1. Add timestamp header to document
2. Update content
3. Increment version number (if applicable)
4. Add change log entry

### When to Create New Document

**Create new** (don't update) if:
- Document is a snapshot (agent report, phase summary, implementation report)
- Previous document is superseded but still has historical value
- Date-specific report

**Process**:
1. Use appropriate template
2. Use YYYY-MM-DD prefix
3. Never modify after creation
4. Archive when specified in lifecycle rules

---

## Cross-Agent Handoffs

When one agent completes work and hands off to another:

1. **Create Handoff Section** in final report:
   ```markdown
   ## Agent Handoff

   **Next Agent**: {agent-name}
   **Context**: {What the next agent needs to know}
   **Dependencies Met**: {Yes/No - list}
   **Blocking Issues**: {Any issues that need resolution}
   **Recommended Next Steps**: {Specific actions}
   ```

2. **Reference Handoff** in subsequent agent's report:
   ```markdown
   ## Context from Previous Agent

   **Previous Agent**: {agent-name}
   **Handoff Report**: [Link to report](path/to/report.md)
   **Dependencies Received**: {What was ready}
   **Issues Resolved**: {Any blocking issues addressed}
   ```

3. **Update Living Status Docs** to reflect handoff

---

## Template Usage

### Available Templates

All templates are in `docs/templates/`:
1. `agent-coverage-report-template.md`
2. `living-status-document-template.md`
3. `phase-completion-summary-template.md`
4. `implementation-report-template.md`
5. `technical-decision-record-template.md`

### When to Use Each Template

| Template | Use For | Agents |
|----------|---------|--------|
| Agent Coverage Report | Test coverage reports | qa-validation-agent |
| Living Status Document | Frequently updated status | Any agent updating status docs |
| Phase Completion Summary | Phase completion reports | qa-validation-agent |
| Implementation Report | Technical implementation docs | frontend-ui-agent, performance-agent, general-purpose |
| Technical Decision Record | Architecture decisions | Plan |

### Template Compliance

**Required**: All snapshot documents MUST use appropriate template
**Enforcement**: Documentation-training-agent reviews compliance weekly
**Violation**: Non-compliant docs will be reformatted or rejected

---

## Examples by Agent Type

### Example: qa-validation-agent Creates Coverage Report

```markdown
# Agent 13 - Final Coverage Analysis

**Date**: 2025-12-05
**Agent**: qa-validation-agent
**Mission**: Achieve 88.88% test coverage across backend

## Executive Summary

**Status**: Complete
**Coverage**: 88.88% (6,577/7,455)
**Key Achievement**: Exceeded 80% coverage target, approaching 90%

[... rest of report following template ...]
```

**Filename**: `docs/agent-work/2025-12-05_agent-13_final-coverage-analysis.md`

### Example: frontend-ui-agent Creates Implementation Report

```markdown
# Enrollment Dashboard - Implementation Report

**Date**: 2025-12-03
**Agent**: frontend-ui-agent
**Scope**: Implement enrollment dashboard UI
**Status**: ✅ Complete

## Overview

**Objective**: Create React components for enrollment planning dashboard
**Approach**: TanStack Table with shadcn/ui components
**Duration**: 2 days

[... rest of report following template ...]
```

**Filename**: `docs/agent-work/2025-12-03_frontend-ui_enrollment-dashboard.md`

### Example: Plan Creates ADR

```markdown
# ADR-001: Module-Based Architecture

**Date**: 2025-11-01
**Status**: Accepted
**Deciders**: Plan agent + tech lead
**Context**: Need to organize 18 modules into coherent structure

## Decision

Organize codebase into 5-layer module-based architecture (Configuration, Planning, Consolidation, Analysis, Strategic).

[... rest of ADR following template ...]
```

**Filename**: `docs/technical-decisions/ADR-001_MODULE_ARCHITECTURE.md`

---

## Violation Handling

### Common Violations

1. **Wrong Location**: Agent creates doc in wrong directory
   - **Fix**: Move to correct location
   - **Prevent**: Update agent config to reference this document

2. **Wrong Naming**: Agent uses incorrect naming pattern
   - **Fix**: Rename file to follow standard
   - **Prevent**: Agent must review standards before creating docs

3. **No Template**: Snapshot doc created without using template
   - **Fix**: Reformat using appropriate template
   - **Prevent**: Agents must use templates for all snapshot docs

4. **Update Instead of Create**: Agent updates snapshot doc
   - **Fix**: Restore original, create new dated version
   - **Prevent**: Agents must understand living vs snapshot distinction

### Enforcement Process

1. **Weekly Review**: qa-validation-agent or documentation-training-agent reviews all new docs
2. **Violations Identified**: Create list of non-compliant docs
3. **Corrections Made**: Fix violations immediately
4. **Agent Update**: Notify agent of violation, reference standards
5. **Prevention**: Update agent config if needed

---

## Quick Reference Card

### Before Creating a Document, Ask:

1. **What type?** Living, snapshot, or reference?
2. **Who am I?** Which agent am I?
3. **Where does it go?** Check matrix above
4. **What's the name?** Follow naming convention
5. **Template?** Use appropriate template if snapshot
6. **When to archive?** Check lifecycle rules

### Checklist for New Documents

- [ ] Correct location for my agent type
- [ ] Correct naming pattern (date if snapshot)
- [ ] Used appropriate template (if snapshot)
- [ ] Added proper headers (timestamp if living)
- [ ] No cross-references to old locations
- [ ] Follows quality standards

---

## References

- [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) - Complete documentation governance
- [../templates/](templates/) - Document templates
- [.claude/AGENT_ORCHESTRATION.md](../.claude/AGENT_ORCHESTRATION.md) - Agent system overview

---

**Version History**:
- v1.0 (2025-12-05): Initial agent documentation standards
