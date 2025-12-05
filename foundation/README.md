# Foundation Documents

This directory contains the core specifications and requirements that define the EFIR Budget Planning Application.

---

## Documents

### Product & Technical Specifications
- **[EFIR_Budget_App_PRD_v1.2.md](EFIR_Budget_App_PRD_v1.2.md)** - Product Requirements Document (173 lines)
- **[EFIR_Budget_App_TSD_v1.2.md](EFIR_Budget_App_TSD_v1.2.md)** - Technical Specification Document (242 lines)
- **[EFIR_Module_Technical_Specification.md](EFIR_Module_Technical_Specification.md)** - Complete 18-module technical specification (1,996 lines) ⭐
- **[EFIR_Budget_Planning_Requirements_v1.2.md](EFIR_Budget_Planning_Requirements_v1.2.md)** - Detailed planning requirements (496 lines)

### Domain Knowledge
- **[EFIR_Workforce_Planning_Logic.md](EFIR_Workforce_Planning_Logic.md)** - DHG methodology and workforce formulas (425 lines) ⭐
- **[EFIR_Data_Summary_v2.md](EFIR_Data_Summary_v2.md)** - Historical data and reference information (451 lines)

---

## Purpose

These documents are the **foundation** of EFIR. They define:
- **What** the system does (PRD, Requirements)
- **How** it's built (TSD, Technical Specification)
- **Domain-specific methodology** (Workforce Planning Logic, DHG)
- **Historical context** (Data Summary)

---

## Usage

### For Product Decisions
Consult the **PRD** and **Requirements** documents for:
- Business objectives
- User stories
- Success criteria
- Product scope

### For Technical Implementation
Consult the **TSD** and **Module Technical Specification** for:
- System architecture
- Technology stack
- Module dependencies
- API contracts
- Integration patterns

### For Workforce Planning (DHG)
Consult the **Workforce Planning Logic** document for:
- DHG calculation formulas
- Gap analysis (TRMD) methodology
- Primary vs secondary staffing models
- AEFE position structure
- HSA (overtime) allocation rules

### For Historical Context
Consult the **Data Summary** for:
- 2023-2024 actual data
- Benchmark ratios (H/E, E/D)
- Fee structures
- Cost structures
- Enrollment trends

---

## Document Status

All foundation documents are:
- ✅ **Versioned** (v1.2 or v2 as indicated in filename)
- ✅ **Reviewed** and approved
- ✅ **Reference** documents (stable, updated only on major changes)
- ✅ **Source of truth** for business requirements

---

## Relationship to Module Specs

The **Module Technical Specification** (1,996 lines) in this directory is the comprehensive reference for all 18 modules.

For detailed implementation-focused specifications, see:
- **[docs/MODULES/](../docs/MODULES/)** - Individual module specifications (MODULE_01 through MODULE_18)

**Key Difference**:
- **This directory**: High-level overview, business requirements, domain knowledge
- **docs/MODULES/**: Detailed technical specs, formulas, validation rules, implementation guidance

---

## Updating Foundation Documents

Foundation documents should **rarely change**. Updates require:

1. **Business Requirement Change**: Consult [product-architect-agent](../.claude/agents/product-architect-agent.md)
2. **Version Update**: Increment version (v1.2 → v1.3)
3. **Archive Old Version**: Move old version to `docs/archive/`
4. **Update Cross-References**: Update any docs referencing the old version
5. **Announce Change**: Notify all agents and developers

**Change Frequency**: Major updates only (quarterly or less)

---

## Cross-References

Foundation documents are referenced by:
- [CLAUDE.md](../CLAUDE.md) - Primary development reference
- [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - Master navigation
- [docs/MODULES/](../docs/MODULES/) - Module specifications
- All 14 agents in [.claude/agents/](../.claude/agents/)

**Important**: When moving or renaming foundation docs, update all cross-references.

---

## Version History

- **v1.2** (November 2025): Current versions of PRD, TSD, Requirements
- **v2** (November 2025): Current version of Data Summary
- **v1.0** (October 2025): Initial specifications

---

**Last Updated**: 2025-12-05
**Next Review**: When business requirements change (consult product-architect-agent)
**Maintained By**: product-architect-agent + tech lead
