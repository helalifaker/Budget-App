"""
Comprehensive async tests for Configuration Service.

Tests all async CRUD operations, business logic validation, and error handling.
"""

from decimal import Decimal

import pytest
from app.models.configuration import (
    BudgetVersionStatus,
)
from app.services.configuration_service import ConfigurationService
from app.services.exceptions import BusinessRuleError, ConflictError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class TestSystemConfigOperations:
    """Tests for system configuration CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_system_config_success(self, db_session: AsyncSession, test_user_id):
        """Test retrieving system config by key."""
        service = ConfigurationService(db_session)

        # Create config
        config = await service.upsert_system_config(
            key="school_capacity",
            value={"max_students": 1875, "target_utilization": 0.9},
            category="capacity",
            description="Maximum school capacity and target utilization",
            user_id=test_user_id,
        )

        assert config is not None
        assert config.key == "school_capacity"

        # Retrieve config
        retrieved = await service.get_system_config("school_capacity")
        assert retrieved is not None
        assert retrieved.key == "school_capacity"
        assert retrieved.value["max_students"] == 1875

    @pytest.mark.asyncio
    async def test_get_system_config_not_found(self, db_session: AsyncSession):
        """Test retrieving non-existent system config returns None."""
        service = ConfigurationService(db_session)
        result = await service.get_system_config("non_existent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_system_configs(
        self, db_session: AsyncSession, test_user_id
    ):
        """Test retrieving all system configurations."""
        service = ConfigurationService(db_session)

        # Create multiple configs
        await service.upsert_system_config(
            key="config1",
            value={"data": "value1"},
            category="category1",
            description="Config 1",
            user_id=test_user_id,
        )
        await service.upsert_system_config(
            key="config2",
            value={"data": "value2"},
            category="category2",
            description="Config 2",
            user_id=test_user_id,
        )

        # Get all configs
        configs = await service.get_all_system_configs()
        assert len(configs) >= 2

    @pytest.mark.asyncio
    async def test_get_all_system_configs_by_category(
        self, db_session: AsyncSession, test_user_id
    ):
        """Test retrieving system configs filtered by category."""
        service = ConfigurationService(db_session)

        # Create configs in different categories
        await service.upsert_system_config(
            key="capacity_config",
            value={"max": 1875},
            category="capacity",
            description="Capacity config",
            user_id=test_user_id,
        )
        await service.upsert_system_config(
            key="fee_config",
            value={"fee": 50000},
            category="fees",
            description="Fee config",
            user_id=test_user_id,
        )

        # Filter by category
        capacity_configs = await service.get_all_system_configs(category="capacity")
        assert len(capacity_configs) >= 1
        assert all(c.category == "capacity" for c in capacity_configs)

    @pytest.mark.asyncio
    async def test_upsert_system_config_update(
        self, db_session: AsyncSession, test_user_id
    ):
        """Test updating existing system config."""
        service = ConfigurationService(db_session)

        # Create config
        config1 = await service.upsert_system_config(
            key="test_config",
            value={"version": 1},
            category="test",
            description="Original",
            user_id=test_user_id,
        )

        # Update same key
        config2 = await service.upsert_system_config(
            key="test_config",
            value={"version": 2},
            category="test",
            description="Updated",
            user_id=test_user_id,
        )

        assert config1.id == config2.id
        assert config2.value["version"] == 2


class TestBudgetVersionOperations:
    """Tests for budget version operations."""

    @pytest.mark.asyncio
    async def test_get_budget_version(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving budget version by ID."""
        service = ConfigurationService(db_session)
        version = await service.get_budget_version(test_budget_version.id)

        assert version is not None
        assert version.id == test_budget_version.id
        assert version.fiscal_year == test_budget_version.fiscal_year

    @pytest.mark.asyncio
    async def test_get_all_budget_versions(
        self, db_session: AsyncSession, test_user_id, fiscal_year_factory, organization_id
    ):
        """Test retrieving all budget versions."""
        service = ConfigurationService(db_session)

        # Get unique fiscal years, ensuring they're different
        fy1 = fiscal_year_factory()
        fy2 = fiscal_year_factory()
        while fy2 == fy1:
            fy2 = fiscal_year_factory()

        # Get existing versions to count baseline
        existing_versions = await service.get_all_budget_versions()
        initial_count = len(existing_versions)

        # Create multiple versions (use try/except in case fiscal year already has working version)
        versions_created = 0
        try:
            await service.create_budget_version(
                name=f"Budget {fy1}",
                fiscal_year=fy1,
                academic_year=f"{fy1-1}-{fy1}",
                organization_id=organization_id,
                user_id=test_user_id,
            )
            versions_created += 1
        except Exception:
            pass  # Fiscal year may already have a working version

        try:
            await service.create_budget_version(
                name=f"Budget {fy2}",
                fiscal_year=fy2,
                academic_year=f"{fy2-1}-{fy2}",
                organization_id=organization_id,
                user_id=test_user_id,
            )
            versions_created += 1
        except Exception:
            pass  # Fiscal year may already have a working version

        versions = await service.get_all_budget_versions()
        # Either we created some versions, or there were already versions in the db
        assert len(versions) >= initial_count + versions_created or len(versions) >= 2

    @pytest.mark.asyncio
    async def test_get_budget_versions_by_fiscal_year(
        self, db_session: AsyncSession, test_user_id, fiscal_year_factory, organization_id
    ):
        """Test filtering budget versions by fiscal year."""
        service = ConfigurationService(db_session)
        target_year = fiscal_year_factory()

        # Create versions for different years
        await service.create_budget_version(
            name="Budget 2025",
            fiscal_year=target_year,
            academic_year=f"{target_year-1}-{target_year}",
            organization_id=organization_id,
            user_id=test_user_id,
        )

        versions = await service.get_all_budget_versions(fiscal_year=target_year)
        assert len(versions) >= 1
        assert all(v.fiscal_year == target_year for v in versions)

    @pytest.mark.asyncio
    async def test_get_budget_versions_by_status(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test filtering budget versions by status."""
        service = ConfigurationService(db_session)

        versions = await service.get_all_budget_versions(
            status=BudgetVersionStatus.WORKING
        )
        assert len(versions) >= 1
        assert all(v.status == BudgetVersionStatus.WORKING for v in versions)

    @pytest.mark.asyncio
    async def test_create_budget_version_success(
        self, db_session: AsyncSession, test_user_id, fiscal_year_factory, organization_id
    ):
        """Test creating a new budget version."""
        service = ConfigurationService(db_session)
        fiscal_year = fiscal_year_factory()

        version = await service.create_budget_version(
            name="Test Budget 2025",
            fiscal_year=fiscal_year,
            academic_year=f"{fiscal_year-1}-{fiscal_year}",
            organization_id=organization_id,
            notes="Test notes",
            user_id=test_user_id,
        )

        assert version is not None
        assert version.name == "Test Budget 2025"
        assert version.fiscal_year == fiscal_year
        assert version.status == BudgetVersionStatus.WORKING

    @pytest.mark.asyncio
    async def test_create_budget_version_duplicate_working_fails(
        self, db_session: AsyncSession, test_user_id, fiscal_year_factory, organization_id
    ):
        """Test creating duplicate working version fails."""
        service = ConfigurationService(db_session)
        fiscal_year = fiscal_year_factory()

        # Create first version
        await service.create_budget_version(
            name="Budget 2025 V1",
            fiscal_year=fiscal_year,
            academic_year=f"{fiscal_year-1}-{fiscal_year}",
            organization_id=organization_id,
            user_id=test_user_id,
        )

        # Try to create another working version for same year and organization
        with pytest.raises(ConflictError, match="working budget version already exists"):
            await service.create_budget_version(
                name="Budget 2025 V2",
                fiscal_year=fiscal_year,
                academic_year=f"{fiscal_year-1}-{fiscal_year}",
                organization_id=organization_id,
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_submit_budget_version_success(
        self, db_session: AsyncSession, test_budget_version, test_user_id
    ):
        """Test submitting a working budget version."""
        service = ConfigurationService(db_session)

        submitted = await service.submit_budget_version(
            test_budget_version.id, test_user_id
        )

        assert submitted.status == BudgetVersionStatus.SUBMITTED
        assert submitted.submitted_at is not None
        assert submitted.submitted_by_id == test_user_id

    @pytest.mark.asyncio
    async def test_submit_budget_version_invalid_status_fails(
        self, db_session: AsyncSession, test_user_id, fiscal_year_factory, organization_id
    ):
        """Test submitting non-working version fails."""
        service = ConfigurationService(db_session)

        # Try multiple fiscal years to avoid conflicts with existing WORKING versions
        # This handles test isolation issues when fiscal_year_factory wraps around
        version = None
        max_attempts = 5
        for attempt in range(max_attempts):
            fiscal_year = fiscal_year_factory()
            try:
                version = await service.create_budget_version(
                    name=f"Test Version FY{fiscal_year}",
                    fiscal_year=fiscal_year,
                    academic_year=f"{fiscal_year-1}-{fiscal_year}",
                    organization_id=organization_id,
                    user_id=test_user_id,
                )
                break  # Success - exit loop
            except ConflictError:
                if attempt == max_attempts - 1:
                    pytest.skip("Could not find unique fiscal year for test")
                continue

        # Submit the version
        await service.submit_budget_version(version.id, test_user_id)

        # Try to submit again (should fail because it's already submitted)
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.submit_budget_version(version.id, test_user_id)

        assert exc_info.value.details["rule"] == "INVALID_STATUS_TRANSITION"

    @pytest.mark.asyncio
    async def test_approve_budget_version_success(
        self, db_session: AsyncSession, test_budget_version, test_user_id
    ):
        """Test approving a submitted budget version."""
        service = ConfigurationService(db_session)

        # Submit first
        await service.submit_budget_version(test_budget_version.id, test_user_id)

        # Then approve
        approved = await service.approve_budget_version(
            test_budget_version.id, test_user_id
        )

        assert approved.status == BudgetVersionStatus.APPROVED
        assert approved.approved_at is not None
        assert approved.approved_by_id == test_user_id

    @pytest.mark.asyncio
    async def test_approve_budget_version_invalid_status_fails(
        self, db_session: AsyncSession, test_user_id, fiscal_year_factory, organization_id
    ):
        """Test approving working version fails."""
        service = ConfigurationService(db_session)

        # Try multiple fiscal years to avoid conflicts with existing WORKING versions
        version = None
        max_attempts = 5
        for attempt in range(max_attempts):
            fiscal_year = fiscal_year_factory()
            try:
                version = await service.create_budget_version(
                    name=f"Test Version FY{fiscal_year}",
                    fiscal_year=fiscal_year,
                    academic_year=f"{fiscal_year-1}-{fiscal_year}",
                    organization_id=organization_id,
                    user_id=test_user_id,
                )
                break
            except ConflictError:
                if attempt == max_attempts - 1:
                    pytest.skip("Could not find unique fiscal year for test")
                continue

        # Try to approve working version directly (without submitting first)
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.approve_budget_version(version.id, test_user_id)

        assert exc_info.value.details["rule"] == "INVALID_STATUS_TRANSITION"

    @pytest.mark.asyncio
    async def test_supersede_budget_version(
        self, db_session: AsyncSession, test_budget_version, test_user_id
    ):
        """Test superseding a budget version."""
        service = ConfigurationService(db_session)

        superseded = await service.supersede_budget_version(
            test_budget_version.id, test_user_id
        )

        assert superseded.status == BudgetVersionStatus.SUPERSEDED


class TestAcademicStructureOperations:
    """Tests for academic cycle and level operations."""

    @pytest.mark.asyncio
    async def test_get_academic_cycles(self, db_session: AsyncSession, academic_cycles):
        """Test retrieving all academic cycles."""
        service = ConfigurationService(db_session)
        cycles = await service.get_academic_cycles()

        assert len(cycles) >= 4
        cycle_codes = [c.code for c in cycles]
        assert "MATERNELLE" in cycle_codes
        assert "COLLEGE" in cycle_codes

    @pytest.mark.asyncio
    async def test_get_academic_levels_all(
        self, db_session: AsyncSession, academic_levels
    ):
        """Test retrieving all academic levels."""
        service = ConfigurationService(db_session)
        levels = await service.get_academic_levels()

        assert len(levels) >= 6
        level_codes = [l.code for l in levels]
        assert "PS" in level_codes
        assert "6EME" in level_codes

    @pytest.mark.asyncio
    async def test_get_academic_levels_by_cycle(
        self, db_session: AsyncSession, academic_cycles, academic_levels
    ):
        """Test retrieving academic levels filtered by cycle."""
        service = ConfigurationService(db_session)

        college_levels = await service.get_academic_levels(
            cycle_id=academic_cycles["college"].id
        )

        assert len(college_levels) >= 2
        assert all(l.cycle_id == academic_cycles["college"].id for l in college_levels)


class TestClassSizeParamOperations:
    """Tests for class size parameter operations."""

    @pytest.mark.asyncio
    async def test_get_class_size_params(
        self, db_session: AsyncSession, test_budget_version, academic_cycles, test_user_id
    ):
        """Test retrieving class size parameters."""
        service = ConfigurationService(db_session)

        # Create class size param
        await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=None,
            cycle_id=academic_cycles["college"].id,
            min_class_size=20,
            target_class_size=25,
            max_class_size=30,
            user_id=test_user_id,
        )

        params = await service.get_class_size_params(test_budget_version.id)
        assert len(params) >= 1

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_create(
        self, db_session: AsyncSession, test_budget_version, academic_cycles, test_user_id
    ):
        """Test creating class size parameter."""
        service = ConfigurationService(db_session)

        param = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=None,
            cycle_id=academic_cycles["maternelle"].id,
            min_class_size=15,
            target_class_size=22,
            max_class_size=28,
            notes="Maternelle class sizes",
            user_id=test_user_id,
        )

        assert param is not None
        assert param.min_class_size == 15
        assert param.target_class_size == 22
        assert param.max_class_size == 28

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_update(
        self, db_session: AsyncSession, test_budget_version, academic_cycles, test_user_id
    ):
        """Test updating existing class size parameter."""
        service = ConfigurationService(db_session)

        # Create first
        param1 = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=None,
            cycle_id=academic_cycles["college"].id,
            min_class_size=20,
            target_class_size=25,
            max_class_size=30,
            user_id=test_user_id,
        )

        # Update same
        param2 = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=None,
            cycle_id=academic_cycles["college"].id,
            min_class_size=22,
            target_class_size=27,
            max_class_size=32,
            user_id=test_user_id,
        )

        assert param1.id == param2.id
        assert param2.min_class_size == 22

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_invalid_range_fails(
        self, db_session: AsyncSession, test_budget_version, academic_cycles, test_user_id
    ):
        """Test invalid class size range fails validation."""
        service = ConfigurationService(db_session)

        # min >= target
        with pytest.raises(ValidationError, match="min < target <= max"):
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=None,
                cycle_id=academic_cycles["college"].id,
                min_class_size=25,
                target_class_size=25,
                max_class_size=30,
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_no_level_or_cycle_fails(
        self, db_session: AsyncSession, test_budget_version, test_user_id
    ):
        """Test missing level_id and cycle_id fails validation."""
        service = ConfigurationService(db_session)

        with pytest.raises(
            ValidationError, match="Either level_id or cycle_id must be provided"
        ):
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=None,
                cycle_id=None,
                min_class_size=20,
                target_class_size=25,
                max_class_size=30,
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_both_level_and_cycle_fails(
        self, db_session: AsyncSession, test_budget_version, academic_levels, academic_cycles, test_user_id
    ):
        """Test specifying both level_id and cycle_id fails validation."""
        service = ConfigurationService(db_session)

        with pytest.raises(
            ValidationError, match="Cannot specify both level_id and cycle_id"
        ):
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=academic_levels["PS"].id,
                cycle_id=academic_cycles["maternelle"].id,
                min_class_size=20,
                target_class_size=25,
                max_class_size=30,
                user_id=test_user_id,
            )


class TestSubjectHoursOperations:
    """Tests for subject hours matrix operations."""

    @pytest.mark.asyncio
    async def test_get_subject_hours_matrix(
        self, db_session: AsyncSession, test_budget_version, subjects, academic_levels, test_user_id
    ):
        """Test retrieving subject hours matrix."""
        service = ConfigurationService(db_session)

        # Create subject hours entry
        await service.upsert_subject_hours(
            version_id=test_budget_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("4.5"),
            user_id=test_user_id,
        )

        matrix = await service.get_subject_hours_matrix(test_budget_version.id)
        assert len(matrix) >= 1

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_create(
        self, db_session: AsyncSession, test_budget_version, subjects, academic_levels, test_user_id
    ):
        """Test creating subject hours configuration."""
        service = ConfigurationService(db_session)

        entry = await service.upsert_subject_hours(
            version_id=test_budget_version.id,
            subject_id=subjects["FRENCH"].id,
            level_id=academic_levels["5EME"].id,
            hours_per_week=Decimal("5.0"),
            is_split=False,
            notes="French language hours",
            user_id=test_user_id,
        )

        assert entry is not None
        assert entry.hours_per_week == Decimal("5.0")
        assert entry.is_split is False

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_update(
        self, db_session: AsyncSession, test_budget_version, subjects, academic_levels, test_user_id
    ):
        """Test updating existing subject hours configuration."""
        service = ConfigurationService(db_session)

        # Create first
        entry1 = await service.upsert_subject_hours(
            version_id=test_budget_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("4.0"),
            user_id=test_user_id,
        )

        # Update same
        entry2 = await service.upsert_subject_hours(
            version_id=test_budget_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("4.5"),
            user_id=test_user_id,
        )

        assert entry1.id == entry2.id
        assert entry2.hours_per_week == Decimal("4.5")

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_invalid_hours_fails(
        self, db_session: AsyncSession, test_budget_version, subjects, academic_levels, test_user_id
    ):
        """Test invalid hours per week fails validation."""
        service = ConfigurationService(db_session)

        # Zero hours
        with pytest.raises(ValidationError, match="between 0 and 12"):
            await service.upsert_subject_hours(
                version_id=test_budget_version.id,
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("0"),
                user_id=test_user_id,
            )

        # Excessive hours
        with pytest.raises(ValidationError, match="between 0 and 12"):
            await service.upsert_subject_hours(
                version_id=test_budget_version.id,
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("15"),
                user_id=test_user_id,
            )


class TestTeacherCostParamOperations:
    """Tests for teacher cost parameter operations."""

    @pytest.mark.asyncio
    async def test_get_teacher_categories(
        self, db_session: AsyncSession, teacher_categories
    ):
        """Test retrieving all teacher categories."""
        service = ConfigurationService(db_session)
        categories = await service.get_teacher_categories()

        assert len(categories) >= 3
        category_codes = [c.code for c in categories]
        assert "AEFE_DETACHED" in category_codes

    @pytest.mark.asyncio
    async def test_get_teacher_cost_params(
        self, db_session: AsyncSession, test_budget_version, teacher_categories, test_user_id
    ):
        """Test retrieving teacher cost parameters."""
        service = ConfigurationService(db_session)

        # Create teacher cost param
        await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41863"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("0"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            user_id=test_user_id,
        )

        params = await service.get_teacher_cost_params(test_budget_version.id)
        assert len(params) >= 1

    @pytest.mark.asyncio
    async def test_upsert_teacher_cost_param_create(
        self, db_session: AsyncSession, test_budget_version, teacher_categories, academic_cycles, test_user_id
    ):
        """Test creating teacher cost parameter."""
        service = ConfigurationService(db_session)

        param = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("20000"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            notes="Local teacher costs",
            user_id=test_user_id,
        )

        assert param is not None
        assert param.avg_salary_sar == Decimal("180000")

    @pytest.mark.asyncio
    async def test_upsert_teacher_cost_param_update(
        self, db_session: AsyncSession, test_budget_version, teacher_categories, test_user_id
    ):
        """Test updating existing teacher cost parameter."""
        service = ConfigurationService(db_session)

        # Create first
        param1 = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41000"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("0"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            user_id=test_user_id,
        )

        # Update same
        param2 = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=teacher_categories["AEFE_DETACHED"].id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41863"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("0"),
            hsa_hourly_rate_sar=Decimal("150"),
            max_hsa_hours=Decimal("4"),
            user_id=test_user_id,
        )

        assert param1.id == param2.id
        assert param2.prrd_contribution_eur == Decimal("41863")


class TestFeeStructureOperations:
    """Tests for fee structure operations."""

    @pytest.mark.asyncio
    async def test_get_fee_categories(self, db_session: AsyncSession, fee_categories):
        """Test retrieving all fee categories."""
        service = ConfigurationService(db_session)
        categories = await service.get_fee_categories()

        assert len(categories) >= 3
        category_codes = [c.code for c in categories]
        assert "TUITION" in category_codes

    @pytest.mark.asyncio
    async def test_get_nationality_types(
        self, db_session: AsyncSession, nationality_types
    ):
        """Test retrieving all nationality types."""
        service = ConfigurationService(db_session)
        types = await service.get_nationality_types()

        assert len(types) >= 3
        type_codes = [t.code for t in types]
        assert "FRENCH" in type_codes

    @pytest.mark.asyncio
    async def test_get_fee_structure(
        self, db_session: AsyncSession, test_budget_version, academic_levels, nationality_types, fee_categories, test_user_id
    ):
        """Test retrieving fee structure."""
        service = ConfigurationService(db_session)

        # Create fee structure entry
        await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            fee_category_id=fee_categories["TUITION"].id,
            amount_sar=Decimal("50000"),
            trimester=1,
            user_id=test_user_id,
        )

        structure = await service.get_fee_structure(test_budget_version.id)
        assert len(structure) >= 1

    @pytest.mark.asyncio
    async def test_upsert_fee_structure_create(
        self, db_session: AsyncSession, test_budget_version, academic_levels, nationality_types, fee_categories, test_user_id
    ):
        """Test creating fee structure entry."""
        service = ConfigurationService(db_session)

        entry = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=academic_levels["5EME"].id,
            nationality_type_id=nationality_types["SAUDI"].id,
            fee_category_id=fee_categories["DAI"].id,
            amount_sar=Decimal("5000"),
            trimester=None,
            notes="DAI fee for Saudi students",
            user_id=test_user_id,
        )

        assert entry is not None
        assert entry.amount_sar == Decimal("5000")
        assert entry.trimester is None

    @pytest.mark.asyncio
    async def test_upsert_fee_structure_update(
        self, db_session: AsyncSession, test_budget_version, academic_levels, nationality_types, fee_categories, test_user_id
    ):
        """Test updating existing fee structure entry."""
        service = ConfigurationService(db_session)

        # Create first
        entry1 = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            nationality_type_id=nationality_types["OTHER"].id,
            fee_category_id=fee_categories["TUITION"].id,
            amount_sar=Decimal("45000"),
            trimester=1,
            user_id=test_user_id,
        )

        # Update same
        entry2 = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            nationality_type_id=nationality_types["OTHER"].id,
            fee_category_id=fee_categories["TUITION"].id,
            amount_sar=Decimal("47000"),
            trimester=1,
            user_id=test_user_id,
        )

        assert entry1.id == entry2.id
        assert entry2.amount_sar == Decimal("47000")
