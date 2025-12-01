"""
EFIR Budget Planning Application - Calculation Engines

This package contains pure calculation engines for budget planning modules.
All engines follow the pure function pattern with explicit Pydantic input/output models.

Engines:
- enrollment: Enrollment projection calculations (Module 7)
- dhg: Teacher workforce planning (DHG methodology) (Module 9)
- revenue: Revenue and fee calculations (Module 10)
- kpi: Key Performance Indicator calculations (Module 15)

Design Principles:
- Pure functions: No side effects, no database I/O
- Explicit types: Pydantic models for inputs and outputs
- Testable: Easy to unit test with known inputs/outputs
- Transparent: All calculations documented with formulas
"""

__all__ = []
