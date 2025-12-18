"""
Strategic module schemas.

This module will contain schemas for:
- Long-term planning (multi-year projections)
- Scenario management (what-if analysis)
- Strategic targets and KPI goals
- Board reporting and executive summaries

Currently a placeholder - schemas will be added as features are implemented.
"""

from app.schemas.strategic.strategic import (
    StrategicScenarioBase,
    StrategicTargetBase,
)

__all__ = [
    "StrategicScenarioBase",
    "StrategicTargetBase",
]
