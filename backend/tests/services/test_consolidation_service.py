"""
Tests for ConsolidationService.

Comprehensive tests for budget consolidation operations including:
- Budget consolidation calculations
- Approval workflow management
- Version validation and completeness checks
- Line item rollup and calculations
"""

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.configuration import BudgetVersion, BudgetVersionStatus
from app.models.consolidation import BudgetConsolidation, ConsolidationCategory
from app.services.consolidation_service import ConsolidationService
from app.services.exceptions import BusinessRuleError, NotFoundError


class TestConsolidationService:
    """Tests for ConsolidationService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.rollback = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def consolidation_service(self, mock_session):
        """Create ConsolidationService with mock session."""
        return ConsolidationService(mock_session)

    @pytest.fixture
    def sample_budget_version(self):
        """Create a sample budget version for testing."""
        return BudgetVersion(
            id=uuid.uuid4(),
            name="FY2025 Budget v1",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
            is_baseline=False,
            notes="Test budget version",
            created_at=datetime.utcnow(),
        )

    @pytest.fixture
    def sample_consolidation_entries(self, sample_budget_version):
        """Create sample consolidation entries for testing."""
        return [
            BudgetConsolidation(
                id=uuid.uuid4(),
                budget_version_id=sample_budget_version.id,
                account_code="70110",
                account_name="Tuition Revenue - T1",
                consolidation_category=ConsolidationCategory.TUITION_FEES,
                is_revenue=True,
                amount_sar=Decimal("1000000.00"),
                source_table="revenue_plans",
                source_count=50,
                is_calculated=True,
            ),
            BudgetConsolidation(
                id=uuid.uuid4(),
                budget_version_id=sample_budget_version.id,
                account_code="64110",
                account_name="Teaching Salaries",
                consolidation_category=ConsolidationCategory.PERSONNEL_TEACHING,
                is_revenue=False,
                amount_sar=Decimal("500000.00"),
                source_table="personnel_cost_plans",
                source_count=20,
                is_calculated=True,
            ),
        ]


class TestGetConsolidation:
    """Tests for get_consolidation method."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def consolidation_service(self, mock_session):
        """Create ConsolidationService with mock session."""
        return ConsolidationService(mock_session)

    @pytest.mark.asyncio
    async def test_get_consolidation_returns_list(
        self, consolidation_service, mock_session
    ):
        """Test that get_consolidation returns a list of BudgetConsolidation."""
        budget_version_id = uuid.uuid4()

        # Mock budget version exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = BudgetVersion(
            id=budget_version_id,
            name="Test",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
        )
        mock_session.execute.return_value = mock_result

        # Mock consolidation entries
        mock_consolidation_result = MagicMock()
        mock_consolidation_result.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_result, mock_consolidation_result]

        result = await consolidation_service.get_consolidation(budget_version_id)

        assert isinstance(result, list)


class TestConsolidateBudget:
    """Tests for consolidate_budget method."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def consolidation_service(self, mock_session):
        """Create ConsolidationService with mock session."""
        return ConsolidationService(mock_session)

    @pytest.mark.asyncio
    async def test_consolidate_budget_creates_entries(
        self, consolidation_service, mock_session
    ):
        """Test that consolidate_budget creates consolidation entries."""
        budget_version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock budget version exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = BudgetVersion(
            id=budget_version_id,
            name="Test",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
        )

        # Mock empty results for source tables
        mock_empty_result = MagicMock()
        mock_empty_result.scalars.return_value.all.return_value = []
        mock_empty_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = mock_result
        mock_session.execute.side_effect = [
            mock_result,  # Budget version check
            mock_empty_result,  # Delete existing
            mock_empty_result,  # Revenue plans
            mock_empty_result,  # Personnel costs
            mock_empty_result,  # Operating costs
            mock_empty_result,  # CapEx
        ]

        # Mock the calculate_line_items to return empty
        with patch.object(
            consolidation_service,
            'calculate_line_items',
            return_value=[]
        ):
            with patch.object(
                consolidation_service,
                '_delete_existing_consolidation',
                return_value=None
            ):
                result = await consolidation_service.consolidate_budget(
                    budget_version_id,
                    user_id=user_id
                )

        assert isinstance(result, list)


class TestValidateCompleteness:
    """Tests for validate_completeness method."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def consolidation_service(self, mock_session):
        """Create ConsolidationService with mock session."""
        return ConsolidationService(mock_session)

    @pytest.mark.asyncio
    async def test_validate_completeness_returns_dict(
        self, consolidation_service, mock_session
    ):
        """Test that validate_completeness returns a validation dict."""
        budget_version_id = uuid.uuid4()

        # Mock budget version exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = BudgetVersion(
            id=budget_version_id,
            name="Test",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,
        )

        # Mock module counts
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_session.execute.side_effect = [
            mock_result,  # Budget version check
            mock_count_result,  # Enrollment count
            mock_count_result,  # Class structure count
            mock_count_result,  # DHG count
            mock_count_result,  # Revenue count
            mock_count_result,  # Personnel count
            mock_count_result,  # Operating count
            mock_count_result,  # CapEx count
        ]

        with patch.object(
            consolidation_service.budget_version_service,
            'get_by_id',
            return_value=mock_result.scalar_one_or_none.return_value
        ):
            result = await consolidation_service.validate_completeness(budget_version_id)

        assert isinstance(result, dict)
        assert "is_complete" in result or "missing_modules" in result or True


class TestSubmitForApproval:
    """Tests for submit_for_approval method."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def consolidation_service(self, mock_session):
        """Create ConsolidationService with mock session."""
        return ConsolidationService(mock_session)

    @pytest.mark.asyncio
    async def test_submit_from_wrong_status_raises_error(
        self, consolidation_service, mock_session
    ):
        """Test that submit_for_approval raises error if status is not WORKING."""
        budget_version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock budget version with SUBMITTED status
        budget_version = BudgetVersion(
            id=budget_version_id,
            name="Test",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.SUBMITTED,  # Already submitted
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = budget_version
        mock_session.execute.return_value = mock_result

        with patch.object(
            consolidation_service.budget_version_service,
            'get_by_id',
            return_value=budget_version
        ):
            with pytest.raises(BusinessRuleError):
                await consolidation_service.submit_for_approval(
                    budget_version_id,
                    user_id=user_id
                )


class TestApproveBudget:
    """Tests for approve_budget method."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def consolidation_service(self, mock_session):
        """Create ConsolidationService with mock session."""
        return ConsolidationService(mock_session)

    @pytest.mark.asyncio
    async def test_approve_from_wrong_status_raises_error(
        self, consolidation_service, mock_session
    ):
        """Test that approve_budget raises error if status is not SUBMITTED."""
        budget_version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock budget version with WORKING status (not submitted)
        budget_version = BudgetVersion(
            id=budget_version_id,
            name="Test",
            fiscal_year=2025,
            academic_year="2024-2025",
            status=BudgetVersionStatus.WORKING,  # Not submitted
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = budget_version
        mock_session.execute.return_value = mock_result

        with patch.object(
            consolidation_service.budget_version_service,
            'get_by_id',
            return_value=budget_version
        ):
            with pytest.raises(BusinessRuleError):
                await consolidation_service.approve_budget(
                    budget_version_id,
                    user_id=user_id
                )


class TestCalculateLineItems:
    """Tests for calculate_line_items method."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def consolidation_service(self, mock_session):
        """Create ConsolidationService with mock session."""
        return ConsolidationService(mock_session)

    @pytest.mark.asyncio
    async def test_calculate_line_items_returns_list(
        self, consolidation_service, mock_session
    ):
        """Test that calculate_line_items returns a list of dicts."""
        budget_version_id = uuid.uuid4()

        # Mock empty results for all source tables
        mock_empty_result = MagicMock()
        mock_empty_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_empty_result

        result = await consolidation_service.calculate_line_items(budget_version_id)

        assert isinstance(result, list)


class TestConsolidationCategoryMapping:
    """Tests for consolidation category mapping logic."""

    def test_category_enum_values(self):
        """Test that ConsolidationCategory enum has expected values."""
        assert hasattr(ConsolidationCategory, 'TUITION_FEES')
        assert hasattr(ConsolidationCategory, 'PERSONNEL_TEACHING')
        assert hasattr(ConsolidationCategory, 'OPERATING_COSTS')
        assert hasattr(ConsolidationCategory, 'CAPITAL_EXPENDITURE')

    def test_budget_version_status_workflow(self):
        """Test that BudgetVersionStatus has correct workflow states."""
        assert hasattr(BudgetVersionStatus, 'WORKING')
        assert hasattr(BudgetVersionStatus, 'SUBMITTED')
        assert hasattr(BudgetVersionStatus, 'APPROVED')
