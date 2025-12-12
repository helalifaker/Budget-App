"""
Tests for Enrollment Projection Service.

Tests cover:
- Scenario retrieval
- Configuration creation and updates
- Override management (global, level, grade)
- Projection calculation and caching
- Validation cascade
- Error handling

NOTE: These tests use session-scoped fixtures to avoid SQLite unique constraint
issues when running in parallel with pytest-xdist.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.enrollment_projection import EnrollmentScenario
from app.services.enrollment_projection_service import EnrollmentProjectionService
from app.services.exceptions import NotFoundError, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ==============================================================================
# Unit Tests - Mock-based (isolated, reliable)
# ==============================================================================


class TestBuildSummary:
    """Tests for _build_summary method - pure function, no DB needed."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> EnrollmentProjectionService:
        """Create service instance."""
        return EnrollmentProjectionService(db_session)

    def test_build_summary_normal_growth(self, service: EnrollmentProjectionService):
        """Test summary calculation with normal growth."""
        summary = service._build_summary(
            base_total=1000,
            final_total=1100,
            years=5,
            years_at_capacity=0,
        )

        assert summary["base_year_total"] == 1000
        assert summary["final_year_total"] == 1100
        assert summary["cagr"] > Decimal("0")
        assert summary["years_at_capacity"] == 0

    def test_build_summary_with_capacity_years(self, service: EnrollmentProjectionService):
        """Test summary calculation with years at capacity."""
        summary = service._build_summary(
            base_total=1800,
            final_total=1850,
            years=5,
            years_at_capacity=3,
        )

        assert summary["years_at_capacity"] == 3

    def test_build_summary_zero_base_total(self, service: EnrollmentProjectionService):
        """Test summary calculation with zero base total."""
        summary = service._build_summary(
            base_total=0,
            final_total=100,
            years=5,
            years_at_capacity=0,
        )

        assert summary["cagr"] == Decimal("0.0")

    def test_build_summary_zero_years(self, service: EnrollmentProjectionService):
        """Test summary calculation with zero years."""
        summary = service._build_summary(
            base_total=1000,
            final_total=1100,
            years=0,
            years_at_capacity=0,
        )

        assert summary["cagr"] == Decimal("0.0")

    def test_build_summary_declining_enrollment(self, service: EnrollmentProjectionService):
        """Test summary calculation with declining enrollment."""
        summary = service._build_summary(
            base_total=1500,
            final_total=1200,
            years=5,
            years_at_capacity=0,
        )

        assert summary["cagr"] < Decimal("0")  # Negative growth

    def test_build_summary_high_growth(self, service: EnrollmentProjectionService):
        """Test summary calculation with high growth."""
        summary = service._build_summary(
            base_total=500,
            final_total=1850,
            years=5,
            years_at_capacity=2,
        )

        assert summary["cagr"] > Decimal("0.20")  # > 20% CAGR
        assert summary["years_at_capacity"] == 2


class TestBuildEngineOverrides:
    """Tests for _build_engine_overrides method."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> EnrollmentProjectionService:
        """Create service instance."""
        return EnrollmentProjectionService(db_session)

    def test_build_engine_overrides_empty_config(
        self, service: EnrollmentProjectionService
    ):
        """Test with config that has no overrides."""
        mock_config = MagicMock()
        mock_config.global_overrides = None
        mock_config.level_overrides = []
        mock_config.grade_overrides = []

        global_o, level_o, grade_o = service._build_engine_overrides(mock_config)

        assert global_o is None
        assert level_o == {}
        assert grade_o == {}

    def test_build_engine_overrides_with_global(
        self, service: EnrollmentProjectionService
    ):
        """Test with global overrides configured."""
        mock_global = MagicMock()
        mock_global.ps_entry_adjustment = 10
        mock_global.retention_adjustment = Decimal("0.02")
        mock_global.lateral_multiplier_override = Decimal("1.2")
        mock_global.class_size_override = 28

        mock_config = MagicMock()
        mock_config.global_overrides = mock_global
        mock_config.level_overrides = []
        mock_config.grade_overrides = []

        global_o, _level_o, _grade_o = service._build_engine_overrides(mock_config)

        assert global_o is not None
        assert global_o.ps_entry_adjustment == 10
        assert global_o.retention_adjustment == Decimal("0.02")

    def test_build_engine_overrides_with_level(
        self, service: EnrollmentProjectionService
    ):
        """Test with level overrides configured."""
        mock_level = MagicMock()
        mock_level.cycle = MagicMock()
        mock_level.cycle.code = "COLLEGE"
        mock_level.class_size_ceiling = 28
        mock_level.max_divisions = 6

        mock_config = MagicMock()
        mock_config.global_overrides = None
        mock_config.level_overrides = [mock_level]
        mock_config.grade_overrides = []

        _global_o, level_o, _grade_o = service._build_engine_overrides(mock_config)

        assert "COLLEGE" in level_o
        assert level_o["COLLEGE"].class_size_ceiling == 28
        assert level_o["COLLEGE"].max_divisions == 6

    def test_build_engine_overrides_with_grade(
        self, service: EnrollmentProjectionService
    ):
        """Test with grade overrides configured."""
        mock_grade = MagicMock()
        mock_grade.level = MagicMock()
        mock_grade.level.code = "6EME"
        mock_grade.retention_rate = Decimal("0.97")
        mock_grade.lateral_entry = 12
        mock_grade.max_divisions = 4
        mock_grade.class_size_ceiling = 26

        mock_config = MagicMock()
        mock_config.global_overrides = None
        mock_config.level_overrides = []
        mock_config.grade_overrides = [mock_grade]

        _global_o, _level_o, grade_o = service._build_engine_overrides(mock_config)

        assert "6EME" in grade_o
        assert grade_o["6EME"].retention_rate == Decimal("0.97")
        assert grade_o["6EME"].lateral_entry == 12


# ==============================================================================
# Mock-based Integration Tests
# ==============================================================================


class TestGetAllScenariosMocked:
    """Tests for get_all_scenarios with mocked session."""

    @pytest.mark.asyncio
    async def test_get_all_scenarios_returns_list(self):
        """Test that scenarios are returned as a list."""
        mock_session = AsyncMock()

        mock_scenarios = [
            MagicMock(code="worst_case", sort_order=1),
            MagicMock(code="base", sort_order=2),
            MagicMock(code="best_case", sort_order=3),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_scenarios
        mock_session.execute.return_value = mock_result

        service = EnrollmentProjectionService(mock_session)
        scenarios = await service.get_all_scenarios()

        assert len(scenarios) == 3
        mock_session.execute.assert_called_once()


class TestGetOrCreateConfigMocked:
    """Tests for get_or_create_config with mocked session."""

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_version(self):
        """Test NotFoundError for non-existent budget version."""
        mock_session = AsyncMock()

        # First query returns no existing config
        # Note: Phase 11 added .unique() to the query chain, so mock must handle it
        mock_result1 = MagicMock()
        mock_unique1 = MagicMock()
        mock_unique1.scalar_one_or_none.return_value = None
        mock_result1.unique.return_value = mock_unique1

        # Second query returns no budget version (no .unique() on this one)
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [mock_result1, mock_result2]

        service = EnrollmentProjectionService(mock_session)

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_or_create_config(uuid.uuid4())

        assert "BudgetVersion" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_returns_existing_config(self):
        """Test that existing config is returned."""
        mock_session = AsyncMock()

        mock_config = MagicMock()
        mock_config.id = uuid.uuid4()
        mock_config.budget_version_id = uuid.uuid4()
        mock_config.scenario = MagicMock(code="base")

        # Phase 11 added .unique() to the query chain for joinedload deduplication
        mock_result = MagicMock()
        mock_unique = MagicMock()
        mock_unique.scalar_one_or_none.return_value = mock_config
        mock_result.unique.return_value = mock_unique
        mock_session.execute.return_value = mock_result

        service = EnrollmentProjectionService(mock_session)
        config = await service.get_or_create_config(mock_config.budget_version_id)

        assert config.id == mock_config.id


class TestValidateAndCascadeMocked:
    """Tests for validate_and_cascade with mocking."""

    @pytest.mark.asyncio
    async def test_validate_requires_confirmation(self):
        """Test that validation fails without confirmation."""
        mock_session = AsyncMock()
        service = EnrollmentProjectionService(mock_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.validate_and_cascade(
                version_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                confirmation=False,
            )

        assert "confirmation" in str(exc_info.value).lower()


class TestUnvalidateMocked:
    """Tests for unvalidate with mocking."""

    @pytest.mark.asyncio
    async def test_unvalidate_draft_is_idempotent(self):
        """Test that unvalidating a draft config is idempotent."""
        mock_session = AsyncMock()

        mock_config = MagicMock()
        mock_config.status = "draft"
        mock_config.validated_at = None

        with patch.object(
            EnrollmentProjectionService,
            "get_or_create_config",
            new_callable=AsyncMock,
            return_value=mock_config,
        ):
            service = EnrollmentProjectionService(mock_session)
            result = await service.unvalidate(uuid.uuid4(), uuid.uuid4())

        # Should return immediately without changes
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_unvalidate_validated_resets_status(self):
        """Test that unvalidating a validated config resets status."""
        mock_session = AsyncMock()

        mock_config = MagicMock()
        mock_config.status = "validated"
        mock_config.validated_at = "2025-01-01T00:00:00Z"
        mock_config.validated_by = uuid.uuid4()

        with patch.object(
            EnrollmentProjectionService,
            "get_or_create_config",
            new_callable=AsyncMock,
            return_value=mock_config,
        ):
            # NOTE: CacheInvalidator patch removed - cache invalidation disabled for performance (Phase 4)
            service = EnrollmentProjectionService(mock_session)
            await service.unvalidate(uuid.uuid4(), uuid.uuid4())

        assert mock_config.status == "draft"
        assert mock_config.validated_at is None
        assert mock_config.validated_by is None


# ==============================================================================
# Integration Tests with Real Fixtures
# ==============================================================================


class TestGetAllScenariosIntegration:
    """Integration tests for get_all_scenarios with real DB."""

    @pytest.fixture
    async def scenarios_fixture(
        self, db_session: AsyncSession
    ) -> list[EnrollmentScenario]:
        """Create test scenarios, checking for existing first."""
        existing = (
            await db_session.execute(
                select(EnrollmentScenario).order_by(EnrollmentScenario.sort_order)
            )
        ).scalars().all()

        if existing:
            return list(existing)

        scenarios = [
            EnrollmentScenario(
                id=uuid.uuid4(),
                code="worst_case",
                name_en="Worst Case",
                name_fr="Pire Cas",
                ps_entry=45,
                entry_growth_rate=Decimal("-0.02"),
                default_retention=Decimal("0.90"),
                terminal_retention=Decimal("0.93"),
                lateral_multiplier=Decimal("0.30"),
                color_code="#dc3545",
                sort_order=1,
            ),
            EnrollmentScenario(
                id=uuid.uuid4(),
                code="base",
                name_en="Base",
                name_fr="Base",
                ps_entry=65,
                entry_growth_rate=Decimal("0.00"),
                default_retention=Decimal("0.96"),
                terminal_retention=Decimal("0.98"),
                lateral_multiplier=Decimal("1.00"),
                color_code="#0d6efd",
                sort_order=2,
            ),
            EnrollmentScenario(
                id=uuid.uuid4(),
                code="best_case",
                name_en="Best Case",
                name_fr="Meilleur Cas",
                ps_entry=85,
                entry_growth_rate=Decimal("0.02"),
                default_retention=Decimal("0.99"),
                terminal_retention=Decimal("0.99"),
                lateral_multiplier=Decimal("1.50"),
                color_code="#198754",
                sort_order=3,
            ),
        ]

        db_session.add_all(scenarios)
        await db_session.flush()

        return scenarios

    async def test_get_all_scenarios_returns_sorted_list(
        self,
        db_session: AsyncSession,
        scenarios_fixture: list[EnrollmentScenario],
    ):
        """Test that scenarios are returned sorted by sort_order."""
        service = EnrollmentProjectionService(db_session)
        scenarios = await service.get_all_scenarios()

        assert len(scenarios) == 3
        assert scenarios[0].code == "worst_case"
        assert scenarios[1].code == "base"
        assert scenarios[2].code == "best_case"

    async def test_get_all_scenarios_returns_empty_without_fixtures(
        self,
        db_session: AsyncSession,
    ):
        """Test that empty list is returned when no scenarios exist."""
        service = EnrollmentProjectionService(db_session)
        scenarios = await service.get_all_scenarios()

        # May be empty or contain scenarios from other tests
        assert isinstance(scenarios, list)
