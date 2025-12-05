# Documentation Archive

This directory contains historical documentation organized by type. Documents are archived when they become obsolete or are superseded by newer versions.

---

## Archive Organization

### phases/ (30+ files)
Phase completion summaries from project development.

- **Content**: Phase summaries from Phase 1 through Phase 10
- **Dates**: November 2025 - December 2025
- **Format**: `YYYY-MM-DD_phase-{N}-{description}.md`
- **Purpose**: Historical record of development milestones

**Examples**:
- `2025-12-05_phase-1-completion.md` - Phase 1 infrastructure completion
- `2025-11-15_phase-2.2-summary.md` - Phase 2.2 implementation summary
- `2025-11-30_phase-9-summary.md` - Phase 9 completion

### implementation-reports/ (20+ files)
Technical implementation reports and agent work products.

- **Content**: Implementation reports, agent completion reports, technical analysis
- **Dates**: November 2025 - December 2025
- **Format**: `YYYY-MM-DD_{implementation-name}.md`
- **Purpose**: Historical record of technical implementations

**Examples**:
- `2025-12-03_database-schema-fix.md` - Database schema fix report
- `2025-12-02_api-test-implementation.md` - API test implementation
- `2025-12-01_agent-11-service-layer.md` - Agent 11 service layer completion
- `2025-11-28_coverage-summary.md` - Test coverage summary

### status-reports/ (15+ files)
Historical status snapshots.

- **Content**: Old status reports, pre-deployment analysis, verification summaries
- **Dates**: November 2025 - December 2025
- **Format**: `YYYY-MM-DD_{status-type}.md`
- **Purpose**: Point-in-time snapshots of project status

**Examples**:
- `2025-12-03_pre-deployment-analysis.md` - Pre-deployment analysis report
- `2025-12-02_phase-1-quick-fixes.md` - Phase 1 quick fixes completion
- `2025-12-01_remaining-issues.md` - Remaining issues status

---

## Archive Policy

Documents are archived when:

| Document Type | Archive When | Timeline |
|---------------|--------------|----------|
| Phase summaries | Phase is completed | Immediate |
| Implementation reports | Implementation is validated | After validation |
| Agent reports | Superseded by newer version | 30 days after supersession |
| Status snapshots | Snapshot becomes historical | 90 days old |

---

## Finding Archived Documents

### By Date
Files are prefixed with `YYYY-MM-DD` for chronological browsing.

**Browse by month**:
```bash
ls -la docs/archive/phases/2025-11-*   # November 2025
ls -la docs/archive/phases/2025-12-*   # December 2025
```

### By Type
Organized into subdirectories by document type.

- **Looking for phase work?** → `phases/`
- **Looking for implementation details?** → `implementation-reports/`
- **Looking for old status?** → `status-reports/`

### By Phase
All phase-related work is in `phases/` subdirectory.

```bash
# Find all Phase 1 documents
ls -la docs/archive/phases/*phase-1*

# Find all Phase 2 documents
ls -la docs/archive/phases/*phase-2*
```

### By Topic
Use search across archive for specific topics.

```bash
# Find all documents mentioning "coverage"
grep -r "coverage" docs/archive/

# Find all documents mentioning "DHG"
grep -r "DHG" docs/archive/
```

---

## Current Documentation

For **current** (non-archived) documentation, see:

| Type | Location |
|------|----------|
| **Current status** | [docs/status/](../status/) - Living documents updated frequently |
| **Recent agent reports** | [docs/agent-work/](../agent-work/) - Reports <30 days old |
| **Module specifications** | [docs/MODULES/](../MODULES/) - Living reference documents |
| **User/Developer guides** | [docs/user-guides/](../user-guides/), [docs/developer-guides/](../developer-guides/) |
| **Testing documentation** | [docs/testing/](../testing/) |
| **Roadmaps** | [docs/roadmaps/](../roadmaps/) |

---

## Maintenance

### Monthly Cleanup (First Monday of Month)
- Archive completed agent reports (>30 days old)
- Move validated implementation reports
- Archive completed phase summaries

### Quarterly Cleanup (First Monday of Quarter)
- Archive old status snapshots (>90 days)
- Review and consolidate redundant reports
- Prune obsolete documentation (if any)

### Annual Review
- Full archive review
- Consolidation of very old archives
- Documentation of major milestones

**See [docs/DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md) for complete maintenance processes.**

---

## Archive Statistics

**Total Archived Files**: 65+

**Breakdown**:
- Phase summaries: 30+ files
- Implementation reports: 20+ files
- Status reports: 15+ files

**Date Range**: November 2025 - December 2025

**Oldest Document**: 2025-11-08 (Week 1 Action Plan)
**Newest Document**: 2025-12-05 (Phase 1 completion)

---

## Document Formats

All archived documents follow these naming conventions:

### Phase Summaries
```
YYYY-MM-DD_phase-{N}-{description}.md

Examples:
2025-12-05_phase-1-completion.md
2025-11-24_phase-5-completion.md
```

### Implementation Reports
```
YYYY-MM-DD_{implementation-name}.md

Examples:
2025-12-03_database-schema-fix.md
2025-12-02_api-test-implementation.md
```

### Agent Reports
```
YYYY-MM-DD_agent-{N}_{purpose}.md

Examples:
2025-12-01_agent-11-service-layer.md
2025-11-30_agent-10-integration-tests.md
```

### Status Reports
```
YYYY-MM-DD_{status-type}.md

Examples:
2025-12-03_pre-deployment-analysis.md
2025-12-01_remaining-issues.md
```

---

## FAQs

**Q: Why are documents archived?**
A: To maintain a clean, organized current documentation while preserving historical context. Archived documents serve as a historical record without cluttering active documentation.

**Q: Can archived documents be deleted?**
A: Generally no. Archives are kept indefinitely for historical reference. Only truly obsolete or redundant documents may be pruned during quarterly reviews, with team approval.

**Q: How do I reference archived documents?**
A: Use relative links from current docs:
```markdown
See archived [Phase 1 Completion](../archive/phases/2025-12-05_phase-1-completion.md)
```

**Q: What if I need information from an archived document?**
A: Archived documents are fully accessible. However, if you're frequently referencing archived information, consider whether it should be consolidated into current living documentation.

**Q: How do I know if a document should be archived?**
A: See [docs/DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md) "Document Lifecycle Policies" section for complete archival criteria.

---

**Archive Created**: 2025-12-05
**Last Cleanup**: 2025-12-05
**Next Review**: 2026-01-01 (monthly)
**Maintained By**: documentation-training-agent + tech lead
