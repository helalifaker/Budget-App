"""
Redis caching layer for EFIR Budget Application.

Provides TTL-based caching with dependency tracking for cascading invalidation.
Implements smart cache invalidation following the calculation dependency graph:

Enrollment → Class Structure → DHG → Personnel Costs → Budget Consolidation
         ↓                      ↓              ↓                ↓
      Revenue              Facility Needs    KPIs         Financial Statements

When enrollment changes, all dependent caches are automatically invalidated.
"""

import asyncio
import os
from collections.abc import Callable
from typing import Any, TypeVar

import redis.asyncio as redis
from cashews import cache

from app.core.logging import logger

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])

# ============================================================================
# Redis Client Configuration
# ============================================================================

_TESTING = bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("PYTEST_RUNNING"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true" and not _TESTING

# New configuration variables for resilience
REDIS_REQUIRED = os.getenv("REDIS_REQUIRED", "false").lower() == "true"
REDIS_CONNECT_TIMEOUT = float(os.getenv("REDIS_CONNECT_TIMEOUT", "5"))
REDIS_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
REDIS_MAX_RETRIES = int(os.getenv("REDIS_MAX_RETRIES", "3"))

# Cache initialization state
_cache_initialized: bool = False
_cache_initialization_lock: asyncio.Lock | None = None
_cache_initialization_error: Exception | None = None

# Redis client for manual operations (cache stats, invalidation)
redis_client: redis.Redis | None = None


def _get_initialization_lock() -> asyncio.Lock:
    """Get or create asyncio lock for cache initialization (lazy)."""
    global _cache_initialization_lock
    if _cache_initialization_lock is None:
        _cache_initialization_lock = asyncio.Lock()
    return _cache_initialization_lock


async def initialize_cache() -> bool:
    """
    Initialize Redis cache with timeout and error handling.

    This is called during application startup, not at module import time.
    Supports graceful degradation if Redis is unavailable.

    Returns:
        True if cache initialized successfully, False otherwise

    Raises:
        RuntimeError: If REDIS_REQUIRED=true and Redis unavailable
    """
    global _cache_initialized, _cache_initialization_error

    if not REDIS_ENABLED:
        logger.info("cache_initialization_skipped", reason="redis_disabled")
        return False

    if _cache_initialized:
        logger.debug("cache_already_initialized")
        return True

    async with _get_initialization_lock():
        # Double-check after acquiring lock
        if _cache_initialized:
            return True

        try:
            # Configure cashews (synchronous but fast - no I/O)
            cache.setup(REDIS_URL, client_side_cache=False)
            logger.info("cache_setup_configured", url=REDIS_URL)

            # Verify connection with timeout
            test_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
            )

            # Test connectivity
            await asyncio.wait_for(
                test_client.ping(),
                timeout=REDIS_SOCKET_TIMEOUT,
            )

            await test_client.close()

            _cache_initialized = True
            logger.info("cache_initialization_success", url=REDIS_URL)
            return True

        except TimeoutError as exc:
            _cache_initialization_error = exc
            logger.error(
                "cache_initialization_timeout",
                url=REDIS_URL,
                connect_timeout=REDIS_CONNECT_TIMEOUT,
            )
            if REDIS_REQUIRED:
                raise RuntimeError(
                    f"Redis connection timeout after {REDIS_CONNECT_TIMEOUT}s. "
                    f"Set REDIS_REQUIRED=false to allow graceful degradation."
                ) from exc
            return False

        except redis.ConnectionError as exc:
            _cache_initialization_error = exc
            logger.error(
                "cache_initialization_connection_error",
                url=REDIS_URL,
                error=str(exc),
            )
            if REDIS_REQUIRED:
                raise RuntimeError(
                    f"Redis connection failed: {exc}. "
                    f"Ensure Redis is running: brew services start redis"
                ) from exc
            return False

        except Exception as exc:
            _cache_initialization_error = exc
            logger.error(
                "cache_initialization_failed",
                url=REDIS_URL,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            if REDIS_REQUIRED:
                raise RuntimeError(f"Redis initialization failed: {exc}") from exc
            return False


def get_cache_status() -> dict[str, Any]:
    """
    Get cache initialization status for health checks.

    Returns:
        dict with status, initialized flag, and error info
    """
    if not REDIS_ENABLED:
        return {
            "status": "disabled",
            "enabled": False,
            "initialized": False,
            "message": "Redis caching is disabled via REDIS_ENABLED=false",
        }

    if _cache_initialized:
        return {
            "status": "ok",
            "enabled": True,
            "initialized": True,
            "url": REDIS_URL.split("@")[-1] if "@" in REDIS_URL else REDIS_URL,
        }

    if _cache_initialization_error:
        return {
            "status": "error",
            "enabled": True,
            "initialized": False,
            "error": str(_cache_initialization_error),
            "error_type": type(_cache_initialization_error).__name__,
        }

    return {
        "status": "not_initialized",
        "enabled": True,
        "initialized": False,
        "message": "Cache not yet initialized",
    }


def validate_redis_config() -> list[str]:
    """
    Validate Redis configuration at startup.

    Returns:
        List of configuration errors (empty if valid)
    """
    errors = []

    if REDIS_ENABLED and not REDIS_URL:
        errors.append("REDIS_ENABLED=true but REDIS_URL not set")

    if REDIS_CONNECT_TIMEOUT <= 0:
        errors.append(f"REDIS_CONNECT_TIMEOUT must be positive (got {REDIS_CONNECT_TIMEOUT})")

    if REDIS_SOCKET_TIMEOUT <= 0:
        errors.append(f"REDIS_SOCKET_TIMEOUT must be positive (got {REDIS_SOCKET_TIMEOUT})")

    if REDIS_REQUIRED and not REDIS_ENABLED:
        errors.append("REDIS_REQUIRED=true requires REDIS_ENABLED=true")

    return errors


async def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client for manual operations.

    Returns:
        Redis client instance with decode_responses=True

    Raises:
        redis.ConnectionError: If Redis is unreachable
    """
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
        )
        logger.info("redis_client_created", url=REDIS_URL)
    return redis_client


async def close_redis_client() -> None:
    """
    Close Redis connection gracefully.

    Should be called on application shutdown.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("redis_client_closed")
        redis_client = None


# ============================================================================
# Cache Decorators by Domain
# ============================================================================


def cache_dhg_calculation(ttl: str = "1h") -> Callable[[F], F]:
    """
    Cache DHG workforce calculations.

    Args:
        ttl: Time-to-live (e.g., "1h", "30m", "1d")

    Returns:
        Decorator function

    Example:
        @cache_dhg_calculation(ttl="1h")
        async def calculate_dhg(budget_version_id: str, level_id: str) -> dict:
            # Expensive DHG calculation
            return result
    """
    if not REDIS_ENABLED:
        return lambda f: f

    return cache(ttl=ttl, key="dhg:{budget_version_id}:{level_id}")


def cache_kpi_dashboard(ttl: str = "5m") -> Callable[[F], F]:
    """
    Cache KPI dashboard aggregations.

    Short TTL since dashboards need near-real-time data.

    Args:
        ttl: Time-to-live (default: 5 minutes)

    Returns:
        Decorator function
    """
    if not REDIS_ENABLED:
        return lambda f: f

    return cache(ttl=ttl, key="kpi:dashboard:{budget_version_id}")


def cache_revenue_projection(ttl: str = "30m") -> Callable[[F], F]:
    """
    Cache revenue projection calculations.

    Args:
        ttl: Time-to-live (default: 30 minutes)

    Returns:
        Decorator function
    """
    if not REDIS_ENABLED:
        return lambda f: f

    return cache(ttl=ttl, key="revenue:{budget_version_id}")


def cache_class_structure(ttl: str = "1h") -> Callable[[F], F]:
    """
    Cache class structure calculations (enrollment → classes).

    Args:
        ttl: Time-to-live (default: 1 hour)

    Returns:
        Decorator function
    """
    if not REDIS_ENABLED:
        return lambda f: f

    return cache(ttl=ttl, key="class_structure:{budget_version_id}:{level_id}")


def cache_cost_calculation(ttl: str = "30m") -> Callable[[F], F]:
    """
    Cache operational cost calculations.

    Args:
        ttl: Time-to-live (default: 30 minutes)

    Returns:
        Decorator function
    """
    if not REDIS_ENABLED:
        return lambda f: f

    return cache(ttl=ttl, key="costs:{budget_version_id}:{cost_category}")


def cache_capex_calculation(ttl: str = "1h") -> Callable[[F], F]:
    """
    Cache capital expenditure calculations.

    Args:
        ttl: Time-to-live (default: 1 hour)

    Returns:
        Decorator function
    """
    if not REDIS_ENABLED:
        return lambda f: f

    return cache(ttl=ttl, key="capex:{budget_version_id}")


def cache_consolidation(ttl: str = "10m") -> Callable[[F], F]:
    """
    Cache budget consolidation results.

    Args:
        ttl: Time-to-live (default: 10 minutes)

    Returns:
        Decorator function
    """
    if not REDIS_ENABLED:
        return lambda f: f

    return cache(ttl=ttl, key="consolidation:{budget_version_id}")


# ============================================================================
# Cache Dependency Graph
# ============================================================================

# Maps entity types to their downstream dependencies
# When an entity changes, all dependencies must be invalidated
CACHE_DEPENDENCY_GRAPH: dict[str, list[str]] = {
    "enrollment": ["class_structure", "revenue"],
    "class_structure": ["dhg_calculations", "facility_needs"],
    "dhg_calculations": ["personnel_costs", "kpi_dashboard"],
    "personnel_costs": ["budget_consolidation", "kpi_dashboard"],
    "revenue": ["budget_consolidation", "kpi_dashboard"],
    "operational_costs": ["budget_consolidation", "kpi_dashboard"],
    "capex": ["budget_consolidation", "kpi_dashboard"],
    "budget_consolidation": ["financial_statements"],
}

# Maps entity names to cache key prefixes
# This handles cases where entity name != cache key prefix
# Example: "dhg_calculations" entity → "dhg" cache key prefix
ENTITY_TO_CACHE_PREFIX: dict[str, str] = {
    "enrollment": "enrollment",
    "class_structure": "class_structure",
    "dhg_calculations": "dhg",
    "personnel_costs": "costs",
    "revenue": "revenue",
    "operational_costs": "costs",
    "capex": "capex",
    "budget_consolidation": "consolidation",
    "kpi_dashboard": "kpi:dashboard",
    "facility_needs": "facility",
    "financial_statements": "statements",
}


# ============================================================================
# Cache Invalidation
# ============================================================================


class CacheInvalidator:
    """
    Handles cascading cache invalidation for EFIR Budget App.

    Implements dependency-aware invalidation:
    - When enrollment changes → invalidate class_structure, revenue, and all dependents
    - When DHG changes → invalidate personnel_costs, KPIs, consolidation
    - When costs change → invalidate consolidation, KPIs

    Example:
        await CacheInvalidator.invalidate(budget_version_id, "enrollment")
        # This will cascade to: class_structure, revenue, dhg, costs, consolidation, KPIs
    """

    @classmethod
    async def invalidate(
        cls, budget_version_id: str, entity: str, _visited: set[str] | None = None
    ) -> int:
        """
        Invalidate entity cache and all dependent caches recursively.

        Args:
            budget_version_id: UUID of budget version
            entity: Entity type (e.g., 'enrollment', 'dhg_calculations')
            _visited: Internal tracking set to prevent duplicate processing

        Returns:
            Total number of cache keys deleted

        Example:
            deleted = await CacheInvalidator.invalidate(
                budget_version_id="abc-123",
                entity="enrollment"
            )
            # Returns: 15 (deleted 15 cache keys across all dependents)
        """
        # FIX Issue #2: Deduplication - prevent processing same entity multiple times
        # Before: enrollment → revenue → kpi_dashboard processed 3-4x (11+ SCAN ops)
        # After: Each entity processed exactly once (6 SCAN ops)
        if _visited is None:
            _visited = set()

        if entity in _visited:
            logger.debug(
                "cache_invalidation_skipped_duplicate",
                entity=entity,
                budget_version_id=budget_version_id,
            )
            return 0

        _visited.add(entity)

        if not REDIS_ENABLED:
            logger.debug("cache_invalidation_skipped", reason="redis_disabled", entity=entity)
            return 0

        try:
            client = await get_redis_client()
        except Exception as exc:  # pragma: no cover - safety fallback for tests
            logger.warning(
                "cache_invalidation_skipped",
                reason="redis_unavailable",
                error=str(exc),
                entity=entity,
            )
            return 0

        # Get cache key prefix for this entity
        # If entity not in mapping, use entity name as-is (for custom entities)
        cache_prefix = ENTITY_TO_CACHE_PREFIX.get(entity, entity)

        # Invalidate this entity's cache
        # Cache keys are stored as: {cache_prefix}:{budget_version_id}:*
        # Example: dhg:abc-123:level-6eme or revenue:abc-123
        pattern = f"{cache_prefix}:{budget_version_id}*"
        logger.info(
            "cache_invalidation_started",
            budget_version_id=budget_version_id,
            entity=entity,
            cache_prefix=cache_prefix,
            pattern=pattern,
        )

        deleted_count = 0
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)
            deleted_count += 1

        logger.info(
            "cache_invalidation_direct",
            budget_version_id=budget_version_id,
            entity=entity,
            cache_prefix=cache_prefix,
            deleted_keys=deleted_count,
        )

        # Recursively invalidate dependents (passing _visited to prevent duplicates)
        dependents = CACHE_DEPENDENCY_GRAPH.get(entity, [])
        for dependent in dependents:
            dependent_deleted = await cls.invalidate(budget_version_id, dependent, _visited)
            deleted_count += dependent_deleted

        return deleted_count

    @classmethod
    def invalidate_background(cls, budget_version_id: str, entity: str) -> None:
        """
        Fire-and-forget cache invalidation.

        Schedules cache invalidation as a background task without blocking the caller.
        This is the RECOMMENDED method for use in API endpoints to avoid blocking
        the response while Redis SCAN operations complete (which can take 2-3s).

        The invalidation will complete asynchronously. If it fails, the cache keys
        will eventually expire via TTL (graceful degradation).

        Args:
            budget_version_id: UUID of budget version
            entity: Entity type to invalidate (e.g., 'enrollment')

        Example:
            # In API endpoint - returns immediately, invalidation happens in background
            CacheInvalidator.invalidate_background(str(version_id), "enrollment")
            return config  # Response sent before invalidation completes
        """
        import asyncio

        async def _background_invalidate() -> None:
            """Wrapper to handle exceptions in background task."""
            try:
                deleted = await cls.invalidate(budget_version_id, entity)
                logger.debug(
                    "cache_invalidation_background_complete",
                    budget_version_id=budget_version_id,
                    entity=entity,
                    deleted_keys=deleted,
                )
            except Exception as exc:
                # Log but don't raise - cache will expire via TTL
                logger.warning(
                    "cache_invalidation_background_failed",
                    budget_version_id=budget_version_id,
                    entity=entity,
                    error=str(exc),
                )

        try:
            loop = asyncio.get_running_loop()
            # Fire-and-forget: we intentionally don't await this task
            # RUF006 suppressed - this is the correct pattern for background cache invalidation
            loop.create_task(_background_invalidate())  # noqa: RUF006
            logger.debug(
                "cache_invalidation_background_scheduled",
                budget_version_id=budget_version_id,
                entity=entity,
            )
        except RuntimeError:
            # No event loop running - skip invalidation (graceful degradation)
            logger.warning(
                "cache_invalidation_skipped_no_loop",
                budget_version_id=budget_version_id,
                entity=entity,
            )

    @classmethod
    async def invalidate_all(cls, budget_version_id: str) -> int:
        """
        Invalidate ALL caches for a budget version.

        Use this when a budget version is deleted or major structural changes occur.

        Args:
            budget_version_id: UUID of budget version

        Returns:
            Number of cache keys deleted

        Example:
            await CacheInvalidator.invalidate_all("abc-123")
        """
        if not REDIS_ENABLED:
            logger.debug(
                "cache_invalidation_all_skipped",
                reason="redis_disabled",
                budget_version_id=budget_version_id,
            )
            return 0

        try:
            client = await get_redis_client()
        except Exception as exc:  # pragma: no cover - safety fallback for tests
            logger.warning(
                "cache_invalidation_all_skipped",
                reason="redis_unavailable",
                budget_version_id=budget_version_id,
                error=str(exc),
            )
            return 0
        pattern = f"*:{budget_version_id}:*"

        deleted_count = 0
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)
            deleted_count += 1

        logger.info(
            "cache_invalidation_all",
            budget_version_id=budget_version_id,
            deleted_keys=deleted_count,
        )

        return deleted_count

    @classmethod
    async def invalidate_pattern(cls, pattern: str) -> int:
        """
        Invalidate caches matching a custom pattern.

        Args:
            pattern: Redis key pattern (e.g., "revenue:*", "*:kpi:*")

        Returns:
            Number of cache keys deleted

        Warning:
            Use carefully - overly broad patterns can impact performance
        """
        if not REDIS_ENABLED:
            logger.debug("cache_invalidation_pattern_skipped", reason="redis_disabled")
            return 0

        try:
            client = await get_redis_client()
        except Exception as exc:  # pragma: no cover - safety fallback for tests
            logger.warning(
                "cache_invalidation_pattern_skipped",
                reason="redis_unavailable",
                error=str(exc),
            )
            return 0

        deleted_count = 0
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)
            deleted_count += 1

        logger.info("cache_invalidation_pattern", pattern=pattern, deleted_keys=deleted_count)

        return deleted_count


# ============================================================================
# Cache Statistics
# ============================================================================


async def get_cache_stats() -> dict[str, Any]:
    """
    Get Redis cache statistics and performance metrics.

    Returns:
        dict: Cache statistics including:
            - connected_clients: Number of active connections
            - used_memory: Human-readable memory usage (e.g., "12.5M")
            - total_keys: Total number of cached keys
            - hits: Number of successful cache lookups
            - misses: Number of cache misses
            - hit_rate: Cache hit rate percentage (0-100)
            - uptime_seconds: Redis server uptime

    Example:
        stats = await get_cache_stats()
        # {
        #     "connected_clients": 5,
        #     "used_memory": "12.5M",
        #     "total_keys": 1234,
        #     "hits": 98765,
        #     "misses": 1235,
        #     "hit_rate": 98.76,
        #     "uptime_seconds": 86400
        # }

    Raises:
        redis.ConnectionError: If Redis is unreachable
    """
    if not REDIS_ENABLED:
        return {
            "status": "disabled",
            "message": "Redis caching is disabled via REDIS_ENABLED=false",
        }

    client = await get_redis_client()
    info = await client.info()

    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total_requests = hits + misses

    return {
        "status": "enabled",
        "connected_clients": info.get("connected_clients", 0),
        "used_memory": info.get("used_memory_human", "0B"),
        "total_keys": await client.dbsize(),
        "hits": hits,
        "misses": misses,
        "hit_rate": round((hits / total_requests * 100) if total_requests > 0 else 0, 2),
        "uptime_seconds": info.get("uptime_in_seconds", 0),
        "redis_version": info.get("redis_version", "unknown"),
    }


# ============================================================================
# Utility Functions
# ============================================================================


async def warm_cache(budget_version_id: str, entities: list[str]) -> None:
    """
    Pre-warm cache for specific entities (placeholder for future optimization).

    Args:
        budget_version_id: UUID of budget version
        entities: List of entity types to pre-cache

    Note:
        This is a placeholder for Phase 3 when we implement predictive caching.
        Currently does nothing.
    """
    if not entities:
        logger.debug(
            "cache_warming_skipped",
            reason="no_entities",
            budget_version_id=budget_version_id,
        )
        return

    if not REDIS_ENABLED:
        logger.debug(
            "cache_warming_skipped",
            reason="redis_disabled",
            budget_version_id=budget_version_id,
            entities=entities,
        )
        return

    try:
        client = await get_redis_client()
    except Exception as exc:  # pragma: no cover - safety fallback
        logger.warning(
            "cache_warming_skipped",
            reason="redis_unavailable",
            budget_version_id=budget_version_id,
            error=str(exc),
        )
        return

    for entity in entities:
        cache_prefix = ENTITY_TO_CACHE_PREFIX.get(entity, entity)
        key = f"warm:{cache_prefix}:{budget_version_id}"
        # Store a simple marker with short TTL to indicate warm-up attempted
        await client.set(key, "1", ex=300)
        logger.info(
            "cache_warm_marker_set",
            budget_version_id=budget_version_id,
            entity=entity,
            key=key,
        )


async def clear_all_caches() -> int:
    """
    DANGER: Clear ALL Redis caches (for testing/maintenance only).

    Returns:
        Number of keys deleted

    Warning:
        This will clear ALL application caches. Only use in development/testing.
    """
    if not REDIS_ENABLED:
        return 0

    client = await get_redis_client()
    await client.flushdb()
    logger.warning("all_caches_cleared", message="ALL Redis caches have been cleared")
    return 1  # flushdb returns OK, we return 1 to indicate success
