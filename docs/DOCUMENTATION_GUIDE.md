# EFIR Documentation Guide

**Version**: 1.0
**Last Updated**: 2025-12-05
**Status**: Active
**Owner**: documentation-training-agent + tech lead

---

## Purpose

This document defines the complete documentation governance system for the EFIR Budget Planning Application. It establishes standards, naming conventions, lifecycle policies, and maintenance processes to ensure documentation remains organized, discoverable, and sustainable.

**Scope**: All markdown documentation files across the entire codebase.

**Audience**: All developers, AI agents, and documentation contributors.

---

## Documentation Structure

```
/
├── README.md                           # Project overview
├── CLAUDE.md                           # Primary development reference
├── DOCUMENTATION_INDEX.md              # Master navigation hub
│
├── foundation/                         # Foundation documents (7 files)
│   ├── README.md
│   ├── EFIR_Budget_App_PRD_v1.2.md
│   ├── EFIR_Budget_App_TSD_v1.2.md
│   ├── EFIR_Module_Technical_Specification.md
│   ├── EFIR_Budget_Planning_Requirements_v1.2.md
│   ├── EFIR_Workforce_Planning_Logic.md
│   └── EFIR_Data_Summary_v2.md
│
├── docs/
│   ├── README.md
│   ├── DOCUMENTATION_GUIDE.md          # This document
│   ├── AGENT_DOCUMENTATION_STANDARDS.md
│   │
│   ├── MODULES/                        # 18 module specifications
│   ├── user-guides/                    # User-facing documentation
│   ├── developer-guides/               # Developer documentation
│   ├── database/                       # Database documentation
│   ├── agent-work/                     # Agent reports (dated snapshots)
│   ├── status/                         # Living status docs
│   ├── roadmaps/                       # Future planning
│   ├── testing/                        # Test documentation
│   ├── technical-decisions/            # ADRs and tech choices
│   ├── templates/                      # Document templates
│   └── archive/                        # Historical documents
│       ├── phases/
│       ├── implementation-reports/
│       └── status-reports/
│
├── backend/docs/                       # Backend-specific docs
├── frontend/                           # Frontend-specific docs
└── .claude/                           # Agent system
    ├── AGENT_ORCHESTRATION.md
    └── agents/                         # 9 agent configs
```

---

## Document Taxonomy

### 1. Living Documents
**Definition**: Always-current documents updated frequently with timestamps.

**Characteristics**:
- No dates in filename
- Timestamp header in content
- Versioned (semantic: major.minor)
- Updated in-place

**Examples**:
- `docs/status/CURRENT_STATUS.md`
- `docs/status/REMAINING_WORK.md`
- `docs/status/CODEBASE_REVIEW.md`

### 2. Snapshot Documents
**Definition**: Point-in-time documents that never change after creation.

**Characteristics**:
- YYYY-MM-DD prefix in filename
- Never updated after creation
- Archived when superseded

**Examples**:
- `docs/agent-work/2025-12-05_agent-13_final-coverage-analysis.md`
- `docs/archive/phases/2025-12-05_phase-1-completion.md`

### 3. Reference Documents
**Definition**: Stable specifications and guides updated only on major changes.

**Characteristics**:
- Versioned suffix (v1_2) or unversioned
- Updated when requirements change
- Old versions archived

**Examples**:
- `foundation/EFIR_Budget_App_PRD_v1.2.md`
- `docs/modules/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md`
- `docs/developer-guides/DEVELOPER_GUIDE.md`

---

## Naming Conventions

### Living Documents
**Format**: `{DESCRIPTIVE_NAME}.md`

**Rules**:
- All caps with underscores
- No dates in filename
- Clear, descriptive name

**Examples**:
- ✅ `CURRENT_STATUS.md`
- ✅ `REMAINING_WORK.md`
- ✅ `PRODUCTION_READINESS.md`
- ❌ `STATUS_DEC_5.md` (has date)
- ❌ `status.md` (lowercase)

### Snapshot Documents

#### Agent Reports
**Format**: `YYYY-MM-DD_agent-{number}_{purpose}.md`

**Examples**:
- `2025-12-05_agent-13_final-coverage-analysis.md`
- `2025-12-03_agent-12_api-coverage-final.md`

#### Phase Summaries
**Format**: `YYYY-MM-DD_phase-{number}-{description}.md`

**Examples**:
- `2025-12-05_phase-1-completion.md`
- `2025-11-20_phase-3-testing-guide.md`

#### Implementation Reports
**Format**: `YYYY-MM-DD_{implementation-name}.md`

**Examples**:
- `2025-12-03_database-schema-fix.md`
- `2025-12-02_api-test-implementation.md`

### Reference Documents

#### Versioned
**Format**: `{NAME}_v{major}_{minor}.md`

**Examples**:
- `EFIR_Budget_App_PRD_v1.2.md`
- `EFIR_Data_Summary_v2.md`

#### Unversioned Guides
**Format**: `{NAME}_GUIDE.md` or `{NAME}.md`

**Examples**:
- `USER_GUIDE.md`
- `DEVELOPER_GUIDE.md`
- `DEPLOYMENT_GUIDE.md`

---

## Document Lifecycle

### Living Documents

**Update Frequency**:
| Document | Frequency | Responsibility |
|----------|-----------|----------------|
| CURRENT_STATUS.md | Multiple times daily | Last developer/agent working |
| REMAINING_WORK.md | Daily (EOD) | Last developer/agent working |
| CODEBASE_REVIEW.md | Weekly | qa-validation-agent |
| PRODUCTION_READINESS.md | Weekly | tech lead |

**Update Process**:
1. Add timestamp header for update
2. Update content sections
3. Increment version number (major.minor)
4. Add entry to change log at bottom

**Example Header**:
```markdown
# Current Status

**Last Updated**: 2025-12-05 14:30 UTC
**Updated By**: qa-validation-agent
**Version**: 1.2

---

## Recent Updates

### [2025-12-05 14:30] - qa-validation-agent
- Completed test coverage expansion
- Updated coverage metrics to 88.88%

### [2025-12-05 09:00] - frontend-ui-agent
- Implemented new UI components
- Updated component documentation

---

[Content]

---

**Change Log**:
- v1.2 (2025-12-05 14:30): Added coverage metrics
- v1.1 (2025-12-05 09:00): API endpoints update
- v1.0 (2025-12-04): Initial version
```

### Snapshot Documents

**Creation**:
- Always create with YYYY-MM-DD prefix
- Use appropriate template
- Never update after creation

**Archive Timeline**:
| Document Type | Archive After | Condition |
|---------------|---------------|-----------|
| Agent reports | 30 days | If superseded by newer report |
| Phase summaries | Immediate | Upon phase completion |
| Implementation reports | Upon validation | After implementation verified |
| Status snapshots | 90 days | After quarterly review |

**Archive Process**:
1. Move to appropriate `docs/archive/` subdirectory
2. Update any cross-references
3. Add archive date to document header
4. Update archive README.md index

### Reference Documents

**Update Frequency**:
- Module specs: On business rule changes only
- Foundation docs: Versioned updates (v1.2 → v1.3)
- Guides: As needed, versioned on major changes

**Versioning**:
- Keep old versions in `docs/archive/` when new version created
- Update version suffix (v1_2 → v1_3)
- Update cross-references to new version

---

## Maintenance Processes

### Daily (End of Day)
**Time**: 5-10 minutes
**Responsibility**: Last developer/agent working that day

**Checklist**:
- [ ] Update `docs/status/CURRENT_STATUS.md` with timestamp
- [ ] Update `docs/status/REMAINING_WORK.md`
- [ ] Review any new agent reports in `docs/agent-work/`
- [ ] Ensure all work is documented

### Weekly (Friday EOD)
**Time**: 15-20 minutes
**Responsibility**: qa-validation-agent or lead developer

**Checklist**:
- [ ] Review all agent reports from the week
- [ ] Consolidate related reports if appropriate
- [ ] Update `docs/status/CODEBASE_REVIEW.md`
- [ ] Update `docs/status/PRODUCTION_READINESS.md`
- [ ] Archive completed agent reports >30 days old
- [ ] Check for broken links in documentation

### Monthly (First Monday)
**Time**: 30-45 minutes
**Responsibility**: documentation-training-agent or tech lead

**Checklist**:
- [ ] Archive completed work >30 days old to `docs/archive/`
- [ ] Review and update all living documents
- [ ] Consolidate redundant documentation
- [ ] Update `DOCUMENTATION_INDEX.md` if structure changed
- [ ] Review cross-references, update if broken
- [ ] Create monthly snapshot of status docs for archive

### Quarterly (First Monday of Q1/Q2/Q3/Q4)
**Time**: 2-3 hours
**Responsibility**: documentation-training-agent + tech lead

**Checklist**:
- [ ] Full documentation audit (all files reviewed)
- [ ] Archive old status snapshots >90 days
- [ ] Consolidate related reports and guides
- [ ] Review and update templates if needed
- [ ] Update `DOCUMENTATION_GUIDE.md` if standards changed
- [ ] Prune archive (delete truly obsolete docs if any)
- [ ] Update roadmaps based on completed work

---

## Document Templates

Templates are located in `docs/templates/`. Available templates:

1. **Agent Coverage Report** - For test coverage and QA reports
2. **Living Status Document** - For frequently updated status docs
3. **Phase Completion Summary** - For phase completion reports
4. **Implementation Report** - For technical implementation docs
5. **Technical Decision Record (ADR)** - For architecture decisions

**Usage**: See [docs/templates/README.md](templates/README.md) for details on each template.

---

## Agent Documentation Standards

**Summary**: Each agent has specific rules for where and how to create documentation.

**Full Details**: See [docs/AGENT_DOCUMENTATION_STANDARDS.md](AGENT_DOCUMENTATION_STANDARDS.md)

**Quick Reference**:
| Agent | Creates | Location | Format |
|-------|---------|----------|--------|
| qa-validation-agent | Coverage reports | docs/agent-work/ | YYYY-MM-DD_agent-{N}_coverage-{scope}.md |
| Plan | ADRs, Implementation plans | docs/technical-decisions/, docs/planning/ | ADR-{NN}_{DECISION}.md |
| frontend-ui-agent | Implementation reports | docs/agent-work/ | YYYY-MM-DD_frontend-ui_{implementation}.md |
| performance-agent | Performance reports | docs/agent-work/ | YYYY-MM-DD_performance_{scope}.md |
| documentation-training-agent | Guides | docs/user-guides/ or docs/developer-guides/ | {NAME}_GUIDE.md |
| product-architect-agent | Module specs | docs/modules/ | MODULE_{NN}_{NAME}.md |
| general-purpose | Research reports | docs/agent-work/ | YYYY-MM-DD_research_{topic}.md |

---

## Archive Policies

### What to Archive
- Completed phase summaries (immediate)
- Superseded agent reports (30 days after new version)
- Old implementation reports (after validation complete)
- Historical status snapshots (90 days old)

### Archive Organization
```
docs/archive/
├── phases/                     # Phase completion summaries
├── implementation-reports/     # Technical implementation reports
└── status-reports/             # Historical status snapshots
```

### Archive Process
1. Move file to appropriate subdirectory
2. Ensure YYYY-MM-DD prefix in filename
3. Add "Archived: YYYY-MM-DD" header to document
4. Update any cross-references to point to archive location
5. Update archive README.md index

---

## Cross-Reference Management

### Critical Reference Points
These files contain cross-references that must be updated when docs move:

1. **CLAUDE.md** (lines 239-246) - "Key Documentation" table
2. **README.md** - Quick navigation links
3. **DOCUMENTATION_INDEX.md** - Comprehensive index
4. **docs/README.md** - Documentation directory navigation

### Update Process
When moving a document:
1. Search for references to old path: `grep -r "old/path.md" .`
2. Update all references to new path
3. Test links in key documents (CLAUDE.md, README.md, DOCUMENTATION_INDEX.md)
4. Commit reference updates with file moves

---

## Quality Standards

### Document Quality Checklist
All documents must:
- [ ] Have clear, descriptive title
- [ ] Include purpose/overview section
- [ ] Use proper markdown formatting
- [ ] Include table of contents if >100 lines
- [ ] Have no broken internal links
- [ ] Follow naming conventions
- [ ] Include last updated timestamp (if living doc)
- [ ] Use appropriate template (if snapshot doc)

### Review Process
- **New documents**: Review by documentation-training-agent before commit
- **Updated documents**: Self-review against quality checklist
- **Major changes**: Tech lead review required

---

## Troubleshooting

### Common Issues

**Issue**: Can't find a document
**Solution**: Check `DOCUMENTATION_INDEX.md` or use `grep -r "search term" docs/`

**Issue**: Don't know where to create a new document
**Solution**: See `AGENT_DOCUMENTATION_STANDARDS.md` or ask documentation-training-agent

**Issue**: Broken link in documentation
**Solution**: Update link to new location, run `grep -r "broken/link" .` to find all references

**Issue**: Outdated snapshot document
**Solution**: Create new snapshot with current date, archive old one

**Issue**: Living document becoming stale
**Solution**: Update with timestamp header, increment version number

---

## Future Enhancements

### Planned Improvements
1. Automated link checking in CI/CD
2. Full-text search across documentation
3. Agent compliance pre-commit hooks
4. Documentation freshness monitoring
5. Interactive documentation site (Docusaurus)

### Suggesting Changes
To suggest changes to this governance system:
1. Create issue describing the problem
2. Propose solution with examples
3. Discuss with documentation-training-agent or tech lead
4. Update this document if approved
5. Announce changes to all agents

---

## References

- [AGENT_DOCUMENTATION_STANDARDS.md](AGENT_DOCUMENTATION_STANDARDS.md) - Agent-specific rules
- [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - Master navigation
- [templates/](templates/) - Document templates
- [archive/README.md](archive/README.md) - Archive organization

---

**Version History**:
- v1.0 (2025-12-05): Initial comprehensive governance document
