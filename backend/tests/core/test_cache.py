"""
Tests for Redis caching layer.

Verifies cache invalidation patterns, especially for:
1. Pattern matching between entity names and cache key prefixes
2. Cascading invalidation following dependency graph
3. Budget version-scoped invalidation
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from app.core.cache import (
    CACHE_DEPENDENCY_GRAPH,
    ENTITY_TO_CACHE_PREFIX,
    CacheInvalidator,
)


class TestCacheKeyPatterns:
    """Test cache key pattern generation and matching."""

    def test_entity_to_cache_prefix_mapping(self):
        """Verify entity names map to correct cache key prefixes."""
        # Critical mappings that were causing the bug
        assert ENTITY_TO_CACHE_PREFIX["dhg_calculations"] == "dhg"
        assert ENTITY_TO_CACHE_PREFIX["budget_consolidation"] == "consolidation"
        assert ENTITY_TO_CACHE_PREFIX["operational_costs"] == "costs"
        assert ENTITY_TO_CACHE_PREFIX["personnel_costs"] == "costs"

        # Direct mappings (entity name == cache prefix)
        assert ENTITY_TO_CACHE_PREFIX["enrollment"] == "enrollment"
        assert ENTITY_TO_CACHE_PREFIX["class_structure"] == "class_structure"
        assert ENTITY_TO_CACHE_PREFIX["revenue"] == "revenue"
        assert ENTITY_TO_CACHE_PREFIX["capex"] == "capex"

    def test_cache_pattern_matches_stored_keys(self):
        """Test that invalidation patterns match actual stored keys."""
        budget_version_id = "abc-123"

        # Test cases: (entity, cache_prefix, example_key)
        test_cases = [
            ("dhg_calculations", "dhg", f"dhg:{budget_version_id}:level-6eme"),
            ("budget_consolidation", "consolidation", f"consolidation:{budget_version_id}"),
            ("revenue", "revenue", f"revenue:{budget_version_id}"),
            ("class_structure", "class_structure", f"class_structure:{budget_version_id}:level-5eme"),
            ("operational_costs", "costs", f"costs:{budget_version_id}:personnel"),
            ("capex", "capex", f"capex:{budget_version_id}"),
        ]

        for entity, expected_prefix, example_key in test_cases:
            # Get cache prefix from mapping
            cache_prefix = ENTITY_TO_CACHE_PREFIX.get(entity, entity)
            assert cache_prefix == expected_prefix, f"Prefix mismatch for {entity}"

            # Verify pattern would match the example key
            pattern = f"{cache_prefix}:{budget_version_id}*"
            assert example_key.startswith(pattern.rstrip("*")), (
                f"Pattern '{pattern}' does not match key '{example_key}'"
            )

    def test_dependency_graph_completeness(self):
        """Verify dependency graph has mappings for all entities."""
        # All entities referenced in dependency graph should have cache prefix mappings
        all_entities = set(CACHE_DEPENDENCY_GRAPH.keys())
        for dependencies in CACHE_DEPENDENCY_GRAPH.values():
            all_entities.update(dependencies)

        for entity in all_entities:
            assert entity in ENTITY_TO_CACHE_PREFIX, (
                f"Entity '{entity}' in dependency graph but not in cache prefix mapping"
            )

    def test_no_old_buggy_pattern(self):
        """Ensure we're not using the old buggy pattern format."""
        budget_version_id = "test-123"
        entity = "dhg_calculations"

        # Old buggy pattern: *:{budget_version_id}:*{entity}*
        # This would try to match: *:test-123:*dhg_calculations*
        # But actual key is: dhg:test-123:level-6eme

        # New correct pattern
        cache_prefix = ENTITY_TO_CACHE_PREFIX[entity]
        new_pattern = f"{cache_prefix}:{budget_version_id}*"

        # Verify new pattern matches actual key
        actual_key = f"dhg:{budget_version_id}:level-6eme"
        assert actual_key.startswith(new_pattern.rstrip("*"))

        # Verify old pattern would NOT match (showing the bug)
        old_pattern = f"*:{budget_version_id}:*{entity}*"
        # Redis scan patterns with * at start are inefficient and this was the bug
        assert not actual_key.startswith(old_pattern.replace("*", ""))


class TestCacheInvalidation:
    """Test cache invalidation logic."""

    @pytest.mark.asyncio
    @patch("app.core.cache.REDIS_ENABLED", True)
    @patch("app.core.cache.get_redis_client")
    async def test_invalidate_single_entity(self, mock_get_redis_client):
        """Test invalidation of a single entity."""
        budget_version_id = "test-123"
        entity = "revenue"

        # Mock Redis client with proper async iterator
        mock_redis = AsyncMock()

        async def mock_scan_iter(match):
            """Mock async generator for scan_iter."""
            keys = [
                f"revenue:{budget_version_id}",
                f"revenue:{budget_version_id}:period-1",
            ]
            for key in keys:
                yield key

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete = AsyncMock()
        mock_get_redis_client.return_value = mock_redis

        # Call invalidate
        deleted_count = await CacheInvalidator.invalidate(budget_version_id, entity)

        # Verify keys were deleted
        assert deleted_count >= 2  # Direct keys + dependents

    @pytest.mark.asyncio
    @patch("app.core.cache.REDIS_ENABLED", True)
    @patch("app.core.cache.get_redis_client")
    async def test_invalidate_with_entity_name_mismatch(self, mock_get_redis_client):
        """Test invalidation when entity name != cache prefix."""
        budget_version_id = "test-456"
        entity = "dhg_calculations"  # Entity name

        # Mock Redis client with proper async iterator
        mock_redis = AsyncMock()

        async def mock_scan_iter(match):
            """Mock async generator for scan_iter."""
            keys = [
                f"dhg:{budget_version_id}:level-6eme",
                f"dhg:{budget_version_id}:level-5eme",
            ]
            for key in keys:
                yield key

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete = AsyncMock()
        mock_get_redis_client.return_value = mock_redis

        # Call invalidate
        deleted_count = await CacheInvalidator.invalidate(budget_version_id, entity)

        # Verify keys were deleted
        assert deleted_count >= 2

    @pytest.mark.asyncio
    @patch("app.core.cache.REDIS_ENABLED", True)
    @patch("app.core.cache.get_redis_client")
    async def test_cascading_invalidation(self, mock_get_redis_client):
        """Test that invalidation cascades through dependency graph."""
        budget_version_id = "test-789"
        entity = "enrollment"

        # Mock Redis client
        mock_redis = AsyncMock()

        # Setup scan_iter to return different keys for different patterns
        async def scan_iter_side_effect(match):
            """Mock async generator that returns keys based on pattern."""
            if "enrollment:" in match:
                keys = [f"enrollment:{budget_version_id}:level-6eme"]
            elif "class_structure:" in match:
                keys = [f"class_structure:{budget_version_id}:level-6eme"]
            elif "revenue:" in match:
                keys = [f"revenue:{budget_version_id}"]
            elif "dhg:" in match:
                keys = [f"dhg:{budget_version_id}:level-6eme"]
            elif "facility:" in match:
                keys = []
            elif "costs:" in match:
                keys = [f"costs:{budget_version_id}:personnel"]
            elif "consolidation:" in match:
                keys = [f"consolidation:{budget_version_id}"]
            elif "kpi:dashboard:" in match:
                keys = [f"kpi:dashboard:{budget_version_id}"]
            elif "statements:" in match:
                keys = []
            else:
                keys = []

            for key in keys:
                yield key

        mock_redis.scan_iter = scan_iter_side_effect
        mock_redis.delete = AsyncMock()
        mock_get_redis_client.return_value = mock_redis

        # Call invalidate on enrollment (root of dependency tree)
        deleted_count = await CacheInvalidator.invalidate(budget_version_id, entity)

        # Should invalidate multiple entities through cascade
        assert deleted_count >= 3  # At least enrollment + class_structure + revenue

    @pytest.mark.asyncio
    @patch("app.core.cache.REDIS_ENABLED", True)
    @patch("app.core.cache.get_redis_client")
    async def test_invalidate_all_for_budget_version(self, mock_get_redis_client):
        """Test invalidation of all caches for a budget version."""
        budget_version_id = "test-all-123"

        # Mock Redis client with proper async iterator
        mock_redis = AsyncMock()

        async def mock_scan_iter(match):
            """Mock async generator for scan_iter."""
            keys = [
                f"dhg:{budget_version_id}:level-6eme",
                f"revenue:{budget_version_id}",
                f"consolidation:{budget_version_id}",
                f"kpi:dashboard:{budget_version_id}",
            ]
            for key in keys:
                yield key

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete = AsyncMock()
        mock_get_redis_client.return_value = mock_redis

        # Call invalidate_all
        deleted_count = await CacheInvalidator.invalidate_all(budget_version_id)

        # Verify all keys were deleted
        assert deleted_count == 4

    @pytest.mark.asyncio
    @patch("app.core.cache.REDIS_ENABLED", False)
    async def test_invalidate_when_redis_disabled(self):
        """Test that invalidation gracefully handles disabled Redis."""
        budget_version_id = "test-disabled-123"
        entity = "revenue"

        # Should return 0 without error
        deleted_count = await CacheInvalidator.invalidate(budget_version_id, entity)
        assert deleted_count == 0


class TestCacheDependencyGraph:
    """Test the cache dependency graph structure."""

    def test_enrollment_triggers_class_structure_invalidation(self):
        """Enrollment changes should invalidate class structure."""
        assert "class_structure" in CACHE_DEPENDENCY_GRAPH["enrollment"]

    def test_enrollment_triggers_revenue_invalidation(self):
        """Enrollment changes should invalidate revenue."""
        assert "revenue" in CACHE_DEPENDENCY_GRAPH["enrollment"]

    def test_class_structure_triggers_dhg_invalidation(self):
        """Class structure changes should invalidate DHG calculations."""
        assert "dhg_calculations" in CACHE_DEPENDENCY_GRAPH["class_structure"]

    def test_dhg_triggers_personnel_costs_invalidation(self):
        """DHG changes should invalidate personnel costs."""
        assert "personnel_costs" in CACHE_DEPENDENCY_GRAPH["dhg_calculations"]

    def test_costs_trigger_consolidation_invalidation(self):
        """Cost changes should invalidate budget consolidation."""
        assert "budget_consolidation" in CACHE_DEPENDENCY_GRAPH["personnel_costs"]
        assert "budget_consolidation" in CACHE_DEPENDENCY_GRAPH["operational_costs"]

    def test_consolidation_triggers_financial_statements_invalidation(self):
        """Consolidation changes should invalidate financial statements."""
        assert "financial_statements" in CACHE_DEPENDENCY_GRAPH["budget_consolidation"]

    def test_no_circular_dependencies(self):
        """Ensure no circular dependencies in the graph."""

        def check_circular(entity: str, path: list[str]) -> None:
            if entity in path:
                raise ValueError(f"Circular dependency detected: {' -> '.join([*path, entity])}")

            path.append(entity)
            for dependent in CACHE_DEPENDENCY_GRAPH.get(entity, []):
                check_circular(dependent, path.copy())

        # Check all root entities
        for entity in CACHE_DEPENDENCY_GRAPH:
            check_circular(entity, [])


class TestCachePatternMatching:
    """Test that cache patterns match actual Redis key formats."""

    def test_dhg_key_pattern(self):
        """Test DHG cache key pattern."""
        budget_version_id = "test-123"
        cache_prefix = ENTITY_TO_CACHE_PREFIX["dhg_calculations"]
        pattern = f"{cache_prefix}:{budget_version_id}*"

        # Should match various DHG keys
        assert f"dhg:{budget_version_id}:level-6eme".startswith(pattern.rstrip("*"))
        assert f"dhg:{budget_version_id}:level-5eme".startswith(pattern.rstrip("*"))
        assert f"dhg:{budget_version_id}".startswith(pattern.rstrip("*"))

        # Should NOT match other entities
        assert not f"revenue:{budget_version_id}".startswith(pattern.rstrip("*"))

    def test_consolidation_key_pattern(self):
        """Test budget consolidation cache key pattern."""
        budget_version_id = "test-456"
        cache_prefix = ENTITY_TO_CACHE_PREFIX["budget_consolidation"]
        pattern = f"{cache_prefix}:{budget_version_id}*"

        # Should match consolidation keys
        assert f"consolidation:{budget_version_id}".startswith(pattern.rstrip("*"))

        # Should NOT match other entities
        assert not f"budget_consolidation:{budget_version_id}".startswith(pattern.rstrip("*"))

    def test_kpi_dashboard_key_pattern(self):
        """Test KPI dashboard cache key pattern."""
        budget_version_id = "test-789"
        cache_prefix = ENTITY_TO_CACHE_PREFIX["kpi_dashboard"]
        pattern = f"{cache_prefix}:{budget_version_id}*"

        # KPI keys use "kpi:dashboard" format
        # Pattern should match "kpi:dashboard:*"
        assert cache_prefix == "kpi:dashboard"
        assert f"kpi:dashboard:{budget_version_id}".startswith(pattern.rstrip("*"))

    def test_all_entities_have_valid_patterns(self):
        """Verify all entities produce valid Redis patterns."""
        budget_version_id = "test-all"

        for _entity, cache_prefix in ENTITY_TO_CACHE_PREFIX.items():
            pattern = f"{cache_prefix}:{budget_version_id}*"

            # Pattern should:
            # 1. Start with the cache prefix
            # 2. Contain the budget version ID
            # 3. End with wildcard
            assert pattern.startswith(cache_prefix)
            assert budget_version_id in pattern
            assert pattern.endswith("*")

            # Should not contain placeholder brackets
            assert "{" not in pattern
            assert "}" not in pattern


@pytest.mark.asyncio
async def test_warm_cache_skips_when_disabled(caplog):
    """warm_cache should no-op when Redis is disabled (test env)."""
    caplog.set_level("DEBUG")
    await warm_cache("version-123", ["enrollment", "dhg_calculations"])

    assert any("cache_warming_skipped" in rec.message for rec in caplog.records)
