# Document Templates

This directory contains standard templates for all agent-created documentation.

## Available Templates

1. **agent-coverage-report-template.md** - For test coverage and QA reports
2. **living-status-document-template.md** - For frequently updated status docs
3. **phase-completion-summary-template.md** - For phase completion reports
4. **implementation-report-template.md** - For technical implementation docs
5. **technical-decision-record-template.md** - For architecture decision records (ADRs)

## Usage

**For Agents**:
1. Choose appropriate template for your document type
2. Copy template content
3. Replace all `{placeholders}` with actual content
4. Save with proper naming convention
5. Place in correct location (see AGENT_DOCUMENTATION_STANDARDS.md)

**For Developers**:
Templates ensure consistency across all documentation. When creating snapshot documents, always use the appropriate template.

## Template Selection Guide

| Document Type | Template | Example Use Case |
|---------------|----------|------------------|
| Test coverage report | agent-coverage-report-template.md | Agent 13 creates coverage analysis |
| Status update | living-status-document-template.md | Updating CURRENT_STATUS.md |
| Phase completion | phase-completion-summary-template.md | Phase 1 completion report |
| Implementation | implementation-report-template.md | Backend API implementation report |
| Architecture decision | technical-decision-record-template.md | Choosing database technology |

## Modifying Templates

To modify a template:
1. Discuss change with documentation-training-agent
2. Ensure change adds value and doesn't reduce clarity
3. Update template file
4. Update this README if needed
5. Announce change to all agents

---

**Last Updated**: 2025-12-05
