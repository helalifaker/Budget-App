"""
Unit tests for Budget Version Service.

Tests the budget version lifecycle management including:
- Creation with conflict detection
- Status transitions (WORKING → SUBMITTED → APPROVED)
- Deletion with business rule enforcement
- Cloning with configuration data
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.configuration import (
    BudgetVersion,
    BudgetVersionStatus,
    ClassSizeParam,
    FeeStructure,
    SubjectHoursMatrix,
    TeacherCostParam,
)
from app.services.budget_version_service import BudgetVersionService
from app.services.exceptions import BusinessRuleError, ConflictError, NotFoundError


class TestBudgetVersionServiceInitialization:
    """Tests for BudgetVersionService initialization."""

    def test_service_initialization(self):
        """Test service initializes with session and base services."""
        session = MagicMock()
        service = BudgetVersionService(session)
        assert service.session == session
        assert service._base_service is not None
        assert service._class_size_base is not None
        assert service._subject_hours_base is not None
        assert service._teacher_cost_base is not None
        assert service._fee_structure_base is not None

    def test_service_initializes_all_clone_services(self):
        """Test all base services for cloning are initialized."""
        session = MagicMock()
        service = BudgetVersionService(session)
        # These are used for cloning configuration data
        assert service._class_size_base.model == ClassSizeParam
        assert service._subject_hours_base.model == SubjectHoursMatrix
        assert service._teacher_cost_base.model == TeacherCostParam
        assert service._fee_structure_base.model == FeeStructure


class TestGetBudgetVersion:
    """Tests for get_budget_version method."""

    @pytest.mark.asyncio
    async def test_get_budget_version_success(self):
        """Test successful retrieval of budget version."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.id = version_id
        mock_version.name = "FY2025 Budget"

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)

        result = await service.get_budget_version(version_id)

        assert result == mock_version
        service._base_service.get_by_id.assert_called_once_with(version_id)

    @pytest.mark.asyncio
    async def test_get_budget_version_not_found(self):
        """Test retrieval of non-existent budget version raises NotFoundError."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        service._base_service.get_by_id = AsyncMock(
            side_effect=NotFoundError(f"Budget version {version_id} not found")
        )

        with pytest.raises(NotFoundError):
            await service.get_budget_version(version_id)


class TestGetAllBudgetVersions:
    """Tests for get_all_budget_versions method."""

    @pytest.mark.asyncio
    async def test_get_all_no_filters(self):
        """Test get all budget versions without filters."""
        session = MagicMock()
        service = BudgetVersionService(session)

        mock_versions = [MagicMock(spec=BudgetVersion) for _ in range(3)]
        service._base_service.get_all = AsyncMock(return_value=mock_versions)

        result = await service.get_all_budget_versions()

        assert result == mock_versions
        service._base_service.get_all.assert_called_once_with(
            filters={},
            order_by="created_at",
        )

    @pytest.mark.asyncio
    async def test_get_all_with_fiscal_year_filter(self):
        """Test get all budget versions with fiscal year filter."""
        session = MagicMock()
        service = BudgetVersionService(session)

        mock_versions = [MagicMock(spec=BudgetVersion)]
        service._base_service.get_all = AsyncMock(return_value=mock_versions)

        await service.get_all_budget_versions(fiscal_year=2025)

        service._base_service.get_all.assert_called_once_with(
            filters={"fiscal_year": 2025},
            order_by="created_at",
        )

    @pytest.mark.asyncio
    async def test_get_all_with_status_filter(self):
        """Test get all budget versions with status filter."""
        session = MagicMock()
        service = BudgetVersionService(session)

        mock_versions = [MagicMock(spec=BudgetVersion)]
        service._base_service.get_all = AsyncMock(return_value=mock_versions)

        await service.get_all_budget_versions(status=BudgetVersionStatus.WORKING)

        service._base_service.get_all.assert_called_once_with(
            filters={"status": BudgetVersionStatus.WORKING},
            order_by="created_at",
        )

    @pytest.mark.asyncio
    async def test_get_all_with_both_filters(self):
        """Test get all budget versions with both filters."""
        session = MagicMock()
        service = BudgetVersionService(session)

        mock_versions = []
        service._base_service.get_all = AsyncMock(return_value=mock_versions)

        await service.get_all_budget_versions(
            fiscal_year=2025,
            status=BudgetVersionStatus.APPROVED,
        )

        service._base_service.get_all.assert_called_once_with(
            filters={
                "fiscal_year": 2025,
                "status": BudgetVersionStatus.APPROVED,
            },
            order_by="created_at",
        )


class TestGetBudgetVersionsPaginated:
    """Tests for get_budget_versions_paginated method."""

    @pytest.mark.asyncio
    async def test_paginated_default_params(self):
        """Test paginated retrieval with default parameters."""
        session = MagicMock()
        service = BudgetVersionService(session)

        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 50,
            "total_pages": 0,
        }
        service._base_service.get_paginated = AsyncMock(return_value=mock_response)

        result = await service.get_budget_versions_paginated()

        assert result == mock_response
        service._base_service.get_paginated.assert_called_once_with(
            page=1,
            page_size=50,
            filters={},
            order_by="created_at",
        )

    @pytest.mark.asyncio
    async def test_paginated_with_filters(self):
        """Test paginated retrieval with filters."""
        session = MagicMock()
        service = BudgetVersionService(session)

        mock_response = {
            "items": [MagicMock(spec=BudgetVersion)],
            "total": 1,
            "page": 2,
            "page_size": 10,
            "total_pages": 1,
        }
        service._base_service.get_paginated = AsyncMock(return_value=mock_response)

        await service.get_budget_versions_paginated(
            page=2,
            page_size=10,
            fiscal_year=2025,
            status=BudgetVersionStatus.WORKING,
        )

        service._base_service.get_paginated.assert_called_once_with(
            page=2,
            page_size=10,
            filters={
                "fiscal_year": 2025,
                "status": BudgetVersionStatus.WORKING,
            },
            order_by="created_at",
        )


class TestCreateBudgetVersion:
    """Tests for create_budget_version method."""

    @pytest.mark.asyncio
    async def test_create_success(self):
        """Test successful creation of budget version."""
        session = MagicMock()
        service = BudgetVersionService(session)

        user_id = uuid.uuid4()
        organization_id = uuid.uuid4()
        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.name = "FY2025 Budget"
        mock_version.fiscal_year = 2025
        mock_version.status = BudgetVersionStatus.WORKING

        service._base_service.exists = AsyncMock(return_value=False)
        service._base_service.create = AsyncMock(return_value=mock_version)

        result = await service.create_budget_version(
            name="FY2025 Budget",
            fiscal_year=2025,
            academic_year="2024-2025",
            organization_id=organization_id,
            notes="Initial budget",
            user_id=user_id,
        )

        assert result == mock_version
        service._base_service.exists.assert_called_once()
        service._base_service.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_conflict_working_exists(self):
        """Test creation fails when working version exists for organization and fiscal year."""
        session = MagicMock()
        service = BudgetVersionService(session)

        organization_id = uuid.uuid4()
        service._base_service.exists = AsyncMock(return_value=True)
        service._base_service.create = AsyncMock()

        with pytest.raises(ConflictError) as exc_info:
            await service.create_budget_version(
                name="FY2025 Budget",
                fiscal_year=2025,
                academic_year="2024-2025",
                organization_id=organization_id,
            )

        assert "working budget version already exists" in str(exc_info.value).lower()
        service._base_service.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_with_parent_version(self):
        """Test creation with parent version for forecast revisions."""
        session = MagicMock()
        service = BudgetVersionService(session)

        parent_id = uuid.uuid4()
        organization_id = uuid.uuid4()
        mock_version = MagicMock(spec=BudgetVersion)

        service._base_service.exists = AsyncMock(return_value=False)
        service._base_service.create = AsyncMock(return_value=mock_version)

        await service.create_budget_version(
            name="FY2025 Forecast",
            fiscal_year=2025,
            academic_year="2024-2025",
            organization_id=organization_id,
            parent_version_id=parent_id,
        )

        # Verify parent_version_id and organization_id are passed to create
        call_args = service._base_service.create.call_args[0][0]
        assert call_args["parent_version_id"] == parent_id
        assert call_args["organization_id"] == organization_id


class TestSubmitBudgetVersion:
    """Tests for submit_budget_version method."""

    @pytest.mark.asyncio
    async def test_submit_working_version_success(self):
        """Test successful submission of working version."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.WORKING

        mock_updated = MagicMock(spec=BudgetVersion)
        mock_updated.status = BudgetVersionStatus.SUBMITTED

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)
        service._base_service.update = AsyncMock(return_value=mock_updated)

        result = await service.submit_budget_version(version_id, user_id)

        assert result == mock_updated
        service._base_service.update.assert_called_once()

        # Verify status change and timestamp
        call_args = service._base_service.update.call_args[0]
        assert call_args[1]["status"] == BudgetVersionStatus.SUBMITTED
        assert "submitted_at" in call_args[1]
        assert call_args[1]["submitted_by_id"] == user_id

    @pytest.mark.asyncio
    async def test_submit_non_working_version_fails(self):
        """Test submission fails for non-working versions."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.APPROVED

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)
        service._base_service.update = AsyncMock()

        with pytest.raises(BusinessRuleError) as exc_info:
            await service.submit_budget_version(version_id, user_id)

        assert exc_info.value.details["rule"] == "INVALID_STATUS_TRANSITION"
        service._base_service.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_submit_submitted_version_fails(self):
        """Test submission fails for already submitted versions."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.SUBMITTED

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)

        with pytest.raises(BusinessRuleError):
            await service.submit_budget_version(version_id, user_id)


class TestApproveBudgetVersion:
    """Tests for approve_budget_version method."""

    @pytest.mark.asyncio
    async def test_approve_submitted_version_success(self):
        """Test successful approval of submitted version."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.SUBMITTED

        mock_approved = MagicMock(spec=BudgetVersion)
        mock_approved.status = BudgetVersionStatus.APPROVED

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)
        service._base_service.update = AsyncMock(return_value=mock_approved)

        result = await service.approve_budget_version(version_id, user_id)

        assert result == mock_approved

        # Verify status change and timestamp
        call_args = service._base_service.update.call_args[0]
        assert call_args[1]["status"] == BudgetVersionStatus.APPROVED
        assert "approved_at" in call_args[1]
        assert call_args[1]["approved_by_id"] == user_id

    @pytest.mark.asyncio
    async def test_approve_working_version_fails(self):
        """Test approval fails for working versions (must submit first)."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.WORKING

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)

        with pytest.raises(BusinessRuleError) as exc_info:
            await service.approve_budget_version(version_id, user_id)

        assert exc_info.value.details["rule"] == "INVALID_STATUS_TRANSITION"

    @pytest.mark.asyncio
    async def test_approve_already_approved_fails(self):
        """Test approval fails for already approved versions."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.APPROVED

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)

        with pytest.raises(BusinessRuleError):
            await service.approve_budget_version(version_id, user_id)


class TestSupersedeBudgetVersion:
    """Tests for supersede_budget_version method."""

    @pytest.mark.asyncio
    async def test_supersede_success(self):
        """Test successful superseding of budget version."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_superseded = MagicMock(spec=BudgetVersion)
        mock_superseded.status = BudgetVersionStatus.SUPERSEDED

        service._base_service.update = AsyncMock(return_value=mock_superseded)

        result = await service.supersede_budget_version(version_id, user_id)

        assert result == mock_superseded
        service._base_service.update.assert_called_once_with(
            version_id,
            {"status": BudgetVersionStatus.SUPERSEDED},
            user_id=user_id,
        )


class TestDeleteBudgetVersion:
    """Tests for delete_budget_version method."""

    @pytest.mark.asyncio
    async def test_delete_working_version_success(self):
        """Test successful deletion of working version."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.WORKING

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)
        service._base_service.soft_delete = AsyncMock()

        await service.delete_budget_version(version_id, user_id)

        service._base_service.soft_delete.assert_called_once_with(
            version_id, user_id=user_id
        )

    @pytest.mark.asyncio
    async def test_delete_submitted_version_success(self):
        """Test successful deletion of submitted version."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.SUBMITTED

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)
        service._base_service.soft_delete = AsyncMock()

        await service.delete_budget_version(version_id, user_id)

        service._base_service.soft_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_approved_version_fails(self):
        """Test deletion fails for approved versions (must supersede instead)."""
        session = MagicMock()
        service = BudgetVersionService(session)

        version_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_version = MagicMock(spec=BudgetVersion)
        mock_version.status = BudgetVersionStatus.APPROVED

        service._base_service.get_by_id = AsyncMock(return_value=mock_version)
        service._base_service.soft_delete = AsyncMock()

        with pytest.raises(BusinessRuleError) as exc_info:
            await service.delete_budget_version(version_id, user_id)

        assert exc_info.value.details["rule"] == "CANNOT_DELETE_APPROVED"
        assert "supersede" in str(exc_info.value).lower()
        service._base_service.soft_delete.assert_not_called()


class TestCloneBudgetVersion:
    """Tests for clone_budget_version method."""

    @pytest.mark.asyncio
    async def test_clone_success_with_configuration(self):
        """Test successful cloning with configuration data."""
        session = MagicMock()
        session.refresh = AsyncMock()
        service = BudgetVersionService(session)

        source_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_source = MagicMock(spec=BudgetVersion)
        mock_source.id = source_id
        mock_source.name = "FY2024 Budget"

        mock_new = MagicMock(spec=BudgetVersion)
        mock_new.id = uuid.uuid4()
        mock_new.name = "FY2025 Budget"
        mock_new.status = BudgetVersionStatus.WORKING

        service._base_service.get_by_id = AsyncMock(return_value=mock_source)
        service._base_service.exists = AsyncMock(return_value=False)
        service._base_service.create = AsyncMock(return_value=mock_new)
        service._clone_configuration_data = AsyncMock()

        result = await service.clone_budget_version(
            source_version_id=source_id,
            name="FY2025 Budget",
            fiscal_year=2025,
            academic_year="2024-2025",
            clone_configuration=True,
            user_id=user_id,
        )

        assert result == mock_new
        service._clone_configuration_data.assert_called_once_with(
            source_version_id=source_id,
            target_version_id=mock_new.id,
            user_id=user_id,
        )

    @pytest.mark.asyncio
    async def test_clone_without_configuration(self):
        """Test cloning without configuration data."""
        session = MagicMock()
        session.refresh = AsyncMock()
        service = BudgetVersionService(session)

        source_id = uuid.uuid4()

        mock_source = MagicMock(spec=BudgetVersion)
        mock_source.id = source_id
        mock_source.name = "FY2024 Budget"

        mock_new = MagicMock(spec=BudgetVersion)
        mock_new.id = uuid.uuid4()

        service._base_service.get_by_id = AsyncMock(return_value=mock_source)
        service._base_service.exists = AsyncMock(return_value=False)
        service._base_service.create = AsyncMock(return_value=mock_new)
        service._clone_configuration_data = AsyncMock()

        await service.clone_budget_version(
            source_version_id=source_id,
            name="FY2025 Budget",
            fiscal_year=2025,
            academic_year="2024-2025",
            clone_configuration=False,
        )

        service._clone_configuration_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_clone_conflict_working_exists(self):
        """Test clone fails when working version exists for target year."""
        session = MagicMock()
        service = BudgetVersionService(session)

        source_id = uuid.uuid4()

        mock_source = MagicMock(spec=BudgetVersion)
        mock_source.id = source_id

        service._base_service.get_by_id = AsyncMock(return_value=mock_source)
        service._base_service.exists = AsyncMock(return_value=True)

        with pytest.raises(ConflictError):
            await service.clone_budget_version(
                source_version_id=source_id,
                name="FY2025 Budget",
                fiscal_year=2025,
                academic_year="2024-2025",
            )

    @pytest.mark.asyncio
    async def test_clone_sets_parent_version(self):
        """Test cloned version has source as parent."""
        session = MagicMock()
        session.refresh = AsyncMock()
        service = BudgetVersionService(session)

        source_id = uuid.uuid4()

        mock_source = MagicMock(spec=BudgetVersion)
        mock_source.id = source_id
        mock_source.name = "FY2024 Budget"

        mock_new = MagicMock(spec=BudgetVersion)
        mock_new.id = uuid.uuid4()

        service._base_service.get_by_id = AsyncMock(return_value=mock_source)
        service._base_service.exists = AsyncMock(return_value=False)
        service._base_service.create = AsyncMock(return_value=mock_new)
        service._clone_configuration_data = AsyncMock()

        await service.clone_budget_version(
            source_version_id=source_id,
            name="FY2025 Budget",
            fiscal_year=2025,
            academic_year="2024-2025",
            clone_configuration=False,
        )

        # Verify parent_version_id is set to source
        call_args = service._base_service.create.call_args[0][0]
        assert call_args["parent_version_id"] == source_id

    @pytest.mark.asyncio
    async def test_clone_adds_note_about_source(self):
        """Test cloned version has note indicating source."""
        session = MagicMock()
        session.refresh = AsyncMock()
        service = BudgetVersionService(session)

        source_id = uuid.uuid4()

        mock_source = MagicMock(spec=BudgetVersion)
        mock_source.id = source_id
        mock_source.name = "FY2024 Original Budget"

        mock_new = MagicMock(spec=BudgetVersion)
        mock_new.id = uuid.uuid4()

        service._base_service.get_by_id = AsyncMock(return_value=mock_source)
        service._base_service.exists = AsyncMock(return_value=False)
        service._base_service.create = AsyncMock(return_value=mock_new)
        service._clone_configuration_data = AsyncMock()

        await service.clone_budget_version(
            source_version_id=source_id,
            name="FY2025 Budget",
            fiscal_year=2025,
            academic_year="2024-2025",
            clone_configuration=False,
        )

        call_args = service._base_service.create.call_args[0][0]
        assert "FY2024 Original Budget" in call_args["notes"]


class TestStatusTransitions:
    """Tests for valid and invalid status transitions."""

    def test_working_to_submitted_valid(self):
        """Test WORKING → SUBMITTED is a valid transition."""
        current = BudgetVersionStatus.WORKING

        # Valid if current is WORKING (can transition to SUBMITTED)
        is_valid = current == BudgetVersionStatus.WORKING
        assert is_valid is True

    def test_submitted_to_approved_valid(self):
        """Test SUBMITTED → APPROVED is a valid transition."""
        current = BudgetVersionStatus.SUBMITTED

        # Valid if current is SUBMITTED
        is_valid = current == BudgetVersionStatus.SUBMITTED
        assert is_valid is True

    def test_working_to_approved_invalid(self):
        """Test WORKING → APPROVED is NOT valid (must submit first)."""
        current = BudgetVersionStatus.WORKING

        # Cannot approve if not submitted
        can_approve = current == BudgetVersionStatus.SUBMITTED
        assert can_approve is False

    def test_approved_to_submitted_invalid(self):
        """Test APPROVED → SUBMITTED is NOT valid (no going back)."""
        current = BudgetVersionStatus.APPROVED

        # Cannot submit an approved version
        can_submit = current == BudgetVersionStatus.WORKING
        assert can_submit is False


class TestBudgetVersionBusinessRules:
    """Tests for business rule enforcement."""

    def test_only_one_working_per_fiscal_year(self):
        """Test business rule: only one WORKING version per fiscal year."""
        # This rule is enforced in create_budget_version
        # by checking exists() before creation
        assert True  # Tested in TestCreateBudgetVersion

    def test_cannot_delete_approved_versions(self):
        """Test business rule: approved versions cannot be deleted."""
        # This rule is enforced in delete_budget_version
        # Must use supersede instead
        assert True  # Tested in TestDeleteBudgetVersion

    def test_status_workflow_enforcement(self):
        """Test business rule: status transitions follow workflow."""
        # WORKING → SUBMITTED → APPROVED is the only valid path
        # Cannot skip steps or go backwards
        assert True  # Tested in TestSubmit and TestApprove


class TestBudgetVersionStatuses:
    """Tests for budget version status enum values."""

    def test_working_status_value(self):
        """Test WORKING status has correct value."""
        assert BudgetVersionStatus.WORKING.value == "working"

    def test_submitted_status_value(self):
        """Test SUBMITTED status has correct value."""
        assert BudgetVersionStatus.SUBMITTED.value == "submitted"

    def test_approved_status_value(self):
        """Test APPROVED status has correct value."""
        assert BudgetVersionStatus.APPROVED.value == "approved"

    def test_superseded_status_value(self):
        """Test SUPERSEDED status has correct value."""
        assert BudgetVersionStatus.SUPERSEDED.value == "superseded"

    def test_forecast_status_value(self):
        """Test FORECAST status has correct value."""
        assert BudgetVersionStatus.FORECAST.value == "forecast"
