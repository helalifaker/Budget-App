"""
In-Memory Reference Data Cache

Caches immutable reference data to eliminate database queries for data that never changes:
- AcademicCycle (4 records) - MAT, ELEM, COLL, LYC
- AcademicLevel (15 records) - PS, MS, GS, CP, CE1, CE2, CM1, CM2, 6EME, 5EME, 4EME, 3EME, 2NDE, 1ERE, TLE
- EnrollmentScenario (3 records) - pessimistic, base, optimistic

Performance Impact:
- Before: Each query adds 150-500ms network latency to Supabase
- After: Zero latency memory lookup (~1ms)
- Savings: ~200-300ms per calculation

Usage:
    from app.core.reference_cache import reference_cache

    # Get all levels (instant)
    levels = reference_cache.get_levels()

    # Get level by code (instant)
    level = reference_cache.get_level_by_code("6EME")

    # Get all scenarios (instant)
    scenarios = reference_cache.get_scenarios()
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CachedCycle:
    """Immutable cached academic cycle data."""

    id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    sort_order: int
    requires_atsem: bool


@dataclass(frozen=True)
class CachedLevel:
    """Immutable cached academic level data."""

    id: uuid.UUID
    cycle_id: uuid.UUID
    code: str
    name_fr: str
    name_en: str
    sort_order: int
    is_secondary: bool
    cycle_code: str  # Denormalized for fast lookup


@dataclass(frozen=True)
class CachedScenario:
    """Immutable cached enrollment scenario data."""

    id: uuid.UUID
    code: str
    name_en: str
    name_fr: str
    description_en: str | None
    description_fr: str | None
    ps_entry: int
    entry_growth_rate: Decimal
    default_retention: Decimal
    terminal_retention: Decimal
    lateral_multiplier: Decimal
    color_code: str | None
    sort_order: int


@dataclass
class ReferenceDataCache:
    """
    In-memory cache for immutable reference data.

    This singleton cache is loaded once at application startup and provides
    zero-latency access to frequently-queried reference data.

    Thread Safety:
    - Data is immutable (frozen dataclasses)
    - Cache is loaded once at startup
    - Safe for concurrent read access
    """

    _cycles: list[CachedCycle] = field(default_factory=list)
    _levels: list[CachedLevel] = field(default_factory=list)
    _scenarios: list[CachedScenario] = field(default_factory=list)

    # Lookup dictionaries for O(1) access
    _cycles_by_code: dict[str, CachedCycle] = field(default_factory=dict)
    _cycles_by_id: dict[uuid.UUID, CachedCycle] = field(default_factory=dict)
    _levels_by_code: dict[str, CachedLevel] = field(default_factory=dict)
    _levels_by_id: dict[uuid.UUID, CachedLevel] = field(default_factory=dict)
    _scenarios_by_code: dict[str, CachedScenario] = field(default_factory=dict)
    _scenarios_by_id: dict[uuid.UUID, CachedScenario] = field(default_factory=dict)

    _is_loaded: bool = False

    async def load(self, session: AsyncSession) -> None:
        """
        Load reference data from database into memory.

        Called once at application startup via lifespan event.
        Subsequent calls are no-ops unless force_reload=True.
        """
        if self._is_loaded:
            logger.debug("reference_cache_already_loaded")
            return

        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.models import AcademicCycle, AcademicLevel, EnrollmentScenario

        logger.info("reference_cache_loading")

        # Load cycles
        cycles_result = await session.execute(
            select(AcademicCycle).order_by(AcademicCycle.sort_order)
        )
        cycles = cycles_result.scalars().all()
        self._cycles = [
            CachedCycle(
                id=c.id,
                code=c.code,
                name_fr=c.name_fr,
                name_en=c.name_en,
                sort_order=c.sort_order,
                requires_atsem=c.requires_atsem,
            )
            for c in cycles
        ]
        self._cycles_by_code = {c.code: c for c in self._cycles}
        self._cycles_by_id = {c.id: c for c in self._cycles}

        # Load levels with cycle relationship
        levels_result = await session.execute(
            select(AcademicLevel)
            .options(selectinload(AcademicLevel.cycle))
            .order_by(AcademicLevel.sort_order)
        )
        levels = levels_result.scalars().all()
        self._levels = [
            CachedLevel(
                id=lv.id,
                cycle_id=lv.cycle_id,
                code=lv.code,
                name_fr=lv.name_fr,
                name_en=lv.name_en,
                sort_order=lv.sort_order,
                is_secondary=lv.is_secondary,
                cycle_code=lv.cycle.code if lv.cycle else "",
            )
            for lv in levels
        ]
        self._levels_by_code = {lv.code: lv for lv in self._levels}
        self._levels_by_id = {lv.id: lv for lv in self._levels}

        # Load scenarios
        scenarios_result = await session.execute(
            select(EnrollmentScenario).order_by(EnrollmentScenario.sort_order)
        )
        scenarios = scenarios_result.scalars().all()
        self._scenarios = [
            CachedScenario(
                id=s.id,
                code=s.code,
                name_en=s.name_en,
                name_fr=s.name_fr,
                description_en=s.description_en,
                description_fr=s.description_fr,
                ps_entry=s.ps_entry,
                entry_growth_rate=s.entry_growth_rate,
                default_retention=s.default_retention,
                terminal_retention=s.terminal_retention,
                lateral_multiplier=s.lateral_multiplier,
                color_code=s.color_code,
                sort_order=s.sort_order,
            )
            for s in scenarios
        ]
        self._scenarios_by_code = {s.code: s for s in self._scenarios}
        self._scenarios_by_id = {s.id: s for s in self._scenarios}

        self._is_loaded = True
        logger.info(
            "reference_cache_loaded",
            cycles=len(self._cycles),
            levels=len(self._levels),
            scenarios=len(self._scenarios),
        )

    @property
    def is_loaded(self) -> bool:
        """Check if cache has been loaded."""
        return self._is_loaded

    # ==========================================================================
    # Cycles
    # ==========================================================================

    def get_cycles(self) -> list[CachedCycle]:
        """Get all cycles (sorted by sort_order)."""
        return self._cycles

    def get_cycle_by_code(self, code: str) -> CachedCycle | None:
        """Get cycle by code (O(1) lookup)."""
        return self._cycles_by_code.get(code)

    def get_cycle_by_id(self, cycle_id: uuid.UUID) -> CachedCycle | None:
        """Get cycle by ID (O(1) lookup)."""
        return self._cycles_by_id.get(cycle_id)

    # ==========================================================================
    # Levels
    # ==========================================================================

    def get_levels(self) -> list[CachedLevel]:
        """Get all levels (sorted by sort_order)."""
        return self._levels

    def get_level_by_code(self, code: str) -> CachedLevel | None:
        """Get level by code (O(1) lookup)."""
        return self._levels_by_code.get(code)

    def get_level_by_id(self, level_id: uuid.UUID) -> CachedLevel | None:
        """Get level by ID (O(1) lookup)."""
        return self._levels_by_id.get(level_id)

    def get_levels_by_cycle(self, cycle_code: str) -> list[CachedLevel]:
        """Get levels filtered by cycle code."""
        return [lv for lv in self._levels if lv.cycle_code == cycle_code]

    def get_secondary_levels(self) -> list[CachedLevel]:
        """Get only secondary levels (Collège + Lycée)."""
        return [lv for lv in self._levels if lv.is_secondary]

    def get_primary_levels(self) -> list[CachedLevel]:
        """Get only primary levels (Maternelle + Élémentaire)."""
        return [lv for lv in self._levels if not lv.is_secondary]

    # ==========================================================================
    # Scenarios
    # ==========================================================================

    def get_scenarios(self) -> list[CachedScenario]:
        """Get all scenarios (sorted by sort_order)."""
        return self._scenarios

    def get_scenario_by_code(self, code: str) -> CachedScenario | None:
        """Get scenario by code (O(1) lookup)."""
        return self._scenarios_by_code.get(code)

    def get_scenario_by_id(self, scenario_id: uuid.UUID) -> CachedScenario | None:
        """Get scenario by ID (O(1) lookup)."""
        return self._scenarios_by_id.get(scenario_id)

    def get_base_scenario(self) -> CachedScenario | None:
        """Get the 'base' scenario (most commonly used)."""
        return self._scenarios_by_code.get("base")


# Global singleton instance
reference_cache = ReferenceDataCache()
