"""
EFIR Budget Planning Application - Calculation Engines

Module Structure (10 modules matching frontend):
- enrollment: Enrollment projection, calibration, class structure
- workforce: DHG, EOS, GOSI calculations
- revenue: Tuition, subsidies, other revenue
- costs: Personnel costs, operating costs (placeholder)
- investments: CapEx, project cash flow (placeholder)
- consolidation: Financial statements, budget rollup
- insights: KPI calculations
- strategic: Scenario planning, long-term projections (placeholder)
- settings: Version calculations (placeholder)
- admin: Import/export calculations (placeholder)

All engines follow the pure function pattern with Pydantic I/O models.
See engine_golden_rules.md for design principles.

Design Principles:
- Pure functions: No side effects, no database I/O
- Explicit types: Pydantic models for inputs and outputs
- Testable: Easy to unit test with known inputs/outputs
- Transparent: All calculations documented with formulas
"""

__all__: list[str] = []
