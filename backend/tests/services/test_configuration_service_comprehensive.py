"""
Comprehensive tests for Configuration Service.

Tests cover all CRUD operations, business rules, and edge cases for:
- System configuration management
- Budget version lifecycle and state transitions
- Class size parameters
- Subject hours matrix
- Teacher cost parameters
- Fee structure
- Timetable constraints

Target: 95%+ coverage with real database operations.
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import BudgetVersionStatus
from app.services.configuration_service import ConfigurationService
from app.services.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ServiceException,
    ValidationError,
)
from sqlalchemy.ext.asyncio import AsyncSession


# ==============================================================================
# System Configuration Tests
# ==============================================================================


class TestSystemConfigurationCRUD:
    """Tests for system configuration CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_system_config_success(
        self,
        db_session: AsyncSession,
        test_system_config,
    ):
        """Test retrieving system config by key."""
        service = ConfigurationService(db_session)

        result = await service.get_system_config("eur_to_sar_rate")

        assert result is not None
        assert result.key == "eur_to_sar_rate"
        assert result.value["rate"] == 4.05

    @pytest.mark.asyncio
    async def test_get_system_config_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving non-existent system config returns None."""
        service = ConfigurationService(db_session)

        result = await service.get_system_config("non_existent_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_system_configs_empty(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving all system configs when empty."""
        service = ConfigurationService(db_session)

        result = await service.get_all_system_configs()

        # May have test data from fixtures, but should return list
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_system_configs_with_category_filter(
        self,
        db_session: AsyncSession,
        test_system_config,
    ):
        """Test retrieving system configs filtered by category."""
        service = ConfigurationService(db_session)

        result = await service.get_all_system_configs(category="exchange_rates")

        assert len(result) >= 1
        assert all(c.category == "exchange_rates" for c in result)

    @pytest.mark.asyncio
    async def test_upsert_system_config_create(
        self,
        db_session: AsyncSession,
        test_user_id: uuid.UUID,
    ):
        """Test creating new system configuration."""
        service = ConfigurationService(db_session)

        result = await service.upsert_system_config(
            key="max_students",
            value={"capacity": 1875, "target_utilization": 0.9},
            category="capacity",
            description="Maximum student capacity",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.key == "max_students"
        assert result.value["capacity"] == 1875
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_upsert_system_config_update(
        self,
        db_session: AsyncSession,
        test_system_config,
        test_user_id: uuid.UUID,
    ):
        """Test updating existing system configuration."""
        service = ConfigurationService(db_session)

        result = await service.upsert_system_config(
            key="eur_to_sar_rate",
            value={"rate": 4.10, "effective_date": "2025-02-01"},
            category="exchange_rates",
            description="Updated EUR to SAR exchange rate",
            user_id=test_user_id,
        )

        assert result.key == "eur_to_sar_rate"
        assert result.value["rate"] == 4.10


# ==============================================================================
# Budget Version Tests
# ==============================================================================


class TestBudgetVersionCRUD:
    """Tests for budget version CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_budget_version_success(
        self,
        db_session: AsyncSession,
        test_budget_version,
    ):
        """Test retrieving budget version by ID."""
        service = ConfigurationService(db_session)

        result = await service.get_budget_version(test_budget_version.id)

        assert result.id == test_budget_version.id
        assert result.fiscal_year == 2025

    @pytest.mark.asyncio
    async def test_get_budget_version_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving non-existent budget version raises error."""
        service = ConfigurationService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_budget_version(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_all_budget_versions(
        self,
        db_session: AsyncSession,
        test_budget_version,
    ):
        """Test retrieving all budget versions."""
        service = ConfigurationService(db_session)

        result = await service.get_all_budget_versions()

        assert len(result) >= 1
        assert any(v.id == test_budget_version.id for v in result)

    @pytest.mark.asyncio
    async def test_get_all_budget_versions_filtered_by_fiscal_year(
        self,
        db_session: AsyncSession,
        test_budget_version,
    ):
        """Test retrieving budget versions filtered by fiscal year."""
        service = ConfigurationService(db_session)

        result = await service.get_all_budget_versions(fiscal_year=2025)

        assert len(result) >= 1
        assert all(v.fiscal_year == 2025 for v in result)

    @pytest.mark.asyncio
    async def test_get_all_budget_versions_filtered_by_status(
        self,
        db_session: AsyncSession,
        test_budget_version,
    ):
        """Test retrieving budget versions filtered by status."""
        service = ConfigurationService(db_session)

        result = await service.get_all_budget_versions(status=BudgetVersionStatus.WORKING)

        assert len(result) >= 1
        assert all(v.status == BudgetVersionStatus.WORKING for v in result)

    @pytest.mark.asyncio
    async def test_create_budget_version_success(
        self,
        db_session: AsyncSession,
        test_user_id: uuid.UUID,
    ):
        """Test creating a new budget version."""
        service = ConfigurationService(db_session)

        result = await service.create_budget_version(
            name="FY2026 Budget v1",
            fiscal_year=2026,
            academic_year="2025-2026",
            notes="New budget for 2026",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.name == "FY2026 Budget v1"
        assert result.fiscal_year == 2026
        assert result.status == BudgetVersionStatus.WORKING

    @pytest.mark.asyncio
    async def test_create_budget_version_duplicate_working_error(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_user_id: uuid.UUID,
    ):
        """Test creating duplicate working version for same fiscal year fails."""
        service = ConfigurationService(db_session)

        with pytest.raises(ConflictError) as exc_info:
            await service.create_budget_version(
                name="FY2025 Budget v2",
                fiscal_year=2025,
                academic_year="2024-2025",
                user_id=test_user_id,
            )

        assert "working budget version already exists" in str(exc_info.value)


class TestBudgetVersionStateTransitions:
    """Tests for budget version state transition workflows."""

    @pytest.mark.asyncio
    async def test_submit_budget_version_success(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_user_id: uuid.UUID,
    ):
        """Test submitting a working budget version."""
        service = ConfigurationService(db_session)

        result = await service.submit_budget_version(
            test_budget_version.id,
            test_user_id,
        )

        assert result.status == BudgetVersionStatus.SUBMITTED
        assert result.submitted_at is not None
        assert result.submitted_by_id == test_user_id

    @pytest.mark.asyncio
    async def test_submit_budget_version_invalid_status_error(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_user_id: uuid.UUID,
    ):
        """Test submitting non-working version fails."""
        service = ConfigurationService(db_session)

        # First submit it
        await service.submit_budget_version(test_budget_version.id, test_user_id)

        # Try to submit again (now in SUBMITTED status)
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.submit_budget_version(test_budget_version.id, test_user_id)

        # The error code is the first arg to BusinessRuleError
        assert exc_info.value.error_code == "INVALID_STATUS_TRANSITION"
        assert "Only working versions can be submitted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_approve_budget_version_success(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_user_id: uuid.UUID,
    ):
        """Test approving a submitted budget version."""
        service = ConfigurationService(db_session)

        # First submit it
        await service.submit_budget_version(test_budget_version.id, test_user_id)

        # Then approve it
        result = await service.approve_budget_version(
            test_budget_version.id,
            test_user_id,
        )

        assert result.status == BudgetVersionStatus.APPROVED
        assert result.approved_at is not None
        assert result.approved_by_id == test_user_id

    @pytest.mark.asyncio
    async def test_approve_budget_version_invalid_status_error(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_user_id: uuid.UUID,
    ):
        """Test approving working version (not submitted) fails."""
        service = ConfigurationService(db_session)

        with pytest.raises(BusinessRuleError) as exc_info:
            await service.approve_budget_version(test_budget_version.id, test_user_id)

        assert exc_info.value.error_code == "INVALID_STATUS_TRANSITION"
        assert "Only submitted versions can be approved" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_supersede_budget_version_success(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_user_id: uuid.UUID,
    ):
        """Test superseding a budget version."""
        service = ConfigurationService(db_session)

        result = await service.supersede_budget_version(
            test_budget_version.id,
            test_user_id,
        )

        assert result.status == BudgetVersionStatus.SUPERSEDED


# ==============================================================================
# Academic Structure Tests
# ==============================================================================


class TestAcademicStructure:
    """Tests for academic cycles and levels retrieval."""

    @pytest.mark.asyncio
    async def test_get_academic_cycles(
        self,
        db_session: AsyncSession,
        academic_cycles: dict,
    ):
        """Test retrieving all academic cycles."""
        service = ConfigurationService(db_session)

        result = await service.get_academic_cycles()

        assert len(result) == 4
        codes = [c.code for c in result]
        assert "MATERNELLE" in codes
        assert "ELEMENTAIRE" in codes
        assert "COLLEGE" in codes
        assert "LYCEE" in codes

    @pytest.mark.asyncio
    async def test_get_academic_levels_all(
        self,
        db_session: AsyncSession,
        academic_levels: dict,
    ):
        """Test retrieving all academic levels."""
        service = ConfigurationService(db_session)

        result = await service.get_academic_levels()

        assert len(result) >= 6  # At least PS, MS, GS, CP, 6EME, 5EME

    @pytest.mark.asyncio
    async def test_get_academic_levels_filtered_by_cycle(
        self,
        db_session: AsyncSession,
        academic_levels: dict,
        academic_cycles: dict,
    ):
        """Test retrieving academic levels filtered by cycle."""
        service = ConfigurationService(db_session)

        result = await service.get_academic_levels(
            cycle_id=academic_cycles["college"].id
        )

        assert len(result) == 2  # 6EME, 5EME
        assert all(level.cycle_id == academic_cycles["college"].id for level in result)


# ==============================================================================
# Class Size Parameter Tests
# ==============================================================================


class TestClassSizeParameters:
    """Tests for class size parameter management."""

    @pytest.mark.asyncio
    async def test_get_class_size_params(
        self,
        db_session: AsyncSession,
        test_class_size_params,
        test_budget_version,
    ):
        """Test retrieving class size parameters."""
        service = ConfigurationService(db_session)

        result = await service.get_class_size_params(test_budget_version.id)

        assert len(result) == 2
        assert any(p.min_class_size == 15 for p in result)

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_create(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test creating class size parameter."""
        service = ConfigurationService(db_session)

        result = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=academic_levels["MS"].id,
            cycle_id=None,
            min_class_size=15,
            target_class_size=22,
            max_class_size=26,
            notes="Moyenne Section class size",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.min_class_size == 15
        assert result.target_class_size == 22
        assert result.max_class_size == 26

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_invalid_min_target_max(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test class size parameter validation: min < target <= max."""
        service = ConfigurationService(db_session)

        # min >= target
        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=academic_levels["MS"].id,
                cycle_id=None,
                min_class_size=25,
                target_class_size=20,
                max_class_size=30,
                user_id=test_user_id,
            )

        assert "min < target <= max" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_invalid_target_exceeds_max(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test class size parameter validation: target > max."""
        service = ConfigurationService(db_session)

        with pytest.raises(ValidationError):
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=academic_levels["MS"].id,
                cycle_id=None,
                min_class_size=15,
                target_class_size=35,
                max_class_size=30,
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_neither_level_nor_cycle(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_user_id: uuid.UUID,
    ):
        """Test class size parameter validation: must provide level_id or cycle_id."""
        service = ConfigurationService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=None,
                cycle_id=None,
                min_class_size=15,
                target_class_size=22,
                max_class_size=26,
                user_id=test_user_id,
            )

        assert "Either level_id or cycle_id must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_both_level_and_cycle(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict,
        academic_cycles: dict,
        test_user_id: uuid.UUID,
    ):
        """Test class size parameter validation: cannot provide both level_id and cycle_id."""
        service = ConfigurationService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_class_size_param(
                version_id=test_budget_version.id,
                level_id=academic_levels["MS"].id,
                cycle_id=academic_cycles["maternelle"].id,
                min_class_size=15,
                target_class_size=22,
                max_class_size=26,
                user_id=test_user_id,
            )

        assert "Cannot specify both level_id and cycle_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upsert_class_size_param_update(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_class_size_params,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test updating existing class size parameter."""
        service = ConfigurationService(db_session)

        result = await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=academic_levels["PS"].id,
            cycle_id=None,
            min_class_size=16,
            target_class_size=21,
            max_class_size=25,
            notes="Updated PS class size",
            user_id=test_user_id,
        )

        assert result.min_class_size == 16
        assert result.target_class_size == 21


# ==============================================================================
# Subject Hours Matrix Tests
# ==============================================================================


class TestSubjectHoursMatrix:
    """Tests for subject hours matrix management."""

    @pytest.mark.asyncio
    async def test_get_subjects(
        self,
        db_session: AsyncSession,
        subjects: dict,
    ):
        """Test retrieving all subjects."""
        service = ConfigurationService(db_session)

        result = await service.get_subjects()

        # subjects fixture creates the subjects, so we should have at least 4
        assert len(result) == 4
        codes = [s.code for s in result]
        assert "MATH" in codes
        assert "FRENCH" in codes
        assert "HISTORY" in codes
        assert "ENGLISH" in codes

    @pytest.mark.asyncio
    async def test_get_subject_hours_matrix(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_subject_hours_matrix,
    ):
        """Test retrieving subject hours matrix."""
        service = ConfigurationService(db_session)

        result = await service.get_subject_hours_matrix(test_budget_version.id)

        assert len(result) == 3
        assert any(h.hours_per_week == Decimal("4.5") for h in result)

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_create(
        self,
        db_session: AsyncSession,
        test_budget_version,
        subjects: dict,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test creating subject hours entry."""
        service = ConfigurationService(db_session)

        result = await service.upsert_subject_hours(
            version_id=test_budget_version.id,
            subject_id=subjects["HISTORY"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("3.5"),
            is_split=False,
            notes="History-Geography 6ème",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.hours_per_week == Decimal("3.5")

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_invalid_zero_hours(
        self,
        db_session: AsyncSession,
        test_budget_version,
        subjects: dict,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test subject hours validation: hours must be > 0."""
        service = ConfigurationService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_subject_hours(
                version_id=test_budget_version.id,
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("0"),
                user_id=test_user_id,
            )

        assert "must be between 0 and 12" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_invalid_excessive_hours(
        self,
        db_session: AsyncSession,
        test_budget_version,
        subjects: dict,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test subject hours validation: hours must be <= 12."""
        service = ConfigurationService(db_session)

        with pytest.raises(ValidationError):
            await service.upsert_subject_hours(
                version_id=test_budget_version.id,
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["6EME"].id,
                hours_per_week=Decimal("15"),
                user_id=test_user_id,
            )

    @pytest.mark.asyncio
    async def test_upsert_subject_hours_update(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_subject_hours_matrix,
        subjects: dict,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test updating existing subject hours entry."""
        service = ConfigurationService(db_session)

        result = await service.upsert_subject_hours(
            version_id=test_budget_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["6EME"].id,
            hours_per_week=Decimal("5.0"),
            is_split=False,
            notes="Updated Math hours",
            user_id=test_user_id,
        )

        assert result.hours_per_week == Decimal("5.0")


# ==============================================================================
# Teacher Cost Parameter Tests
# ==============================================================================


class TestTeacherCostParameters:
    """Tests for teacher cost parameter management."""

    @pytest.mark.asyncio
    async def test_get_teacher_categories(
        self,
        db_session: AsyncSession,
        teacher_categories: dict,
    ):
        """Test retrieving teacher categories."""
        service = ConfigurationService(db_session)

        result = await service.get_teacher_categories()

        assert len(result) == 3
        codes = [c.code for c in result]
        assert "AEFE_DETACHED" in codes
        assert "LOCAL" in codes

    @pytest.mark.asyncio
    async def test_get_teacher_cost_params(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_teacher_cost_params,
    ):
        """Test retrieving teacher cost parameters."""
        service = ConfigurationService(db_session)

        result = await service.get_teacher_cost_params(test_budget_version.id)

        assert len(result) == 2
        assert any(p.prrd_contribution_eur == Decimal("41863.00") for p in result)

    @pytest.mark.asyncio
    async def test_upsert_teacher_cost_param_create(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict,
        academic_cycles: dict,
        test_user_id: uuid.UUID,
    ):
        """Test creating teacher cost parameter."""
        service = ConfigurationService(db_session)

        result = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["elementaire"].id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("160000.00"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("20000.00"),
            hsa_hourly_rate_sar=Decimal("120.00"),
            max_hsa_hours=Decimal("2.0"),
            notes="Local Primary Teacher",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.avg_salary_sar == Decimal("160000.00")

    @pytest.mark.asyncio
    async def test_upsert_teacher_cost_param_update(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_teacher_cost_params,
        teacher_categories: dict,
        academic_cycles: dict,
        test_user_id: uuid.UUID,
    ):
        """Test updating existing teacher cost parameter."""
        service = ConfigurationService(db_session)

        result = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=teacher_categories["LOCAL"].id,
            cycle_id=academic_cycles["college"].id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("190000.00"),
            social_charges_rate=Decimal("0.21"),
            benefits_allowance_sar=Decimal("25000.00"),
            hsa_hourly_rate_sar=Decimal("160.00"),
            max_hsa_hours=Decimal("2.0"),
            notes="Updated Local Secondary Teacher",
            user_id=test_user_id,
        )

        assert result.avg_salary_sar == Decimal("190000.00")


# ==============================================================================
# Fee Structure Tests
# ==============================================================================


class TestFeeStructure:
    """Tests for fee structure management."""

    @pytest.mark.asyncio
    async def test_get_fee_categories(
        self,
        db_session: AsyncSession,
        fee_categories: dict,
    ):
        """Test retrieving fee categories."""
        service = ConfigurationService(db_session)

        result = await service.get_fee_categories()

        assert len(result) == 3
        codes = [c.code for c in result]
        assert "TUITION" in codes
        assert "DAI" in codes

    @pytest.mark.asyncio
    async def test_get_nationality_types(
        self,
        db_session: AsyncSession,
        nationality_types: dict,
    ):
        """Test retrieving nationality types."""
        service = ConfigurationService(db_session)

        result = await service.get_nationality_types()

        assert len(result) == 3
        codes = [n.code for n in result]
        assert "FRENCH" in codes
        assert "SAUDI" in codes
        assert "OTHER" in codes

    @pytest.mark.asyncio
    async def test_get_fee_structure(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_fee_structure,
    ):
        """Test retrieving fee structure."""
        service = ConfigurationService(db_session)

        result = await service.get_fee_structure(test_budget_version.id)

        assert len(result) == 3
        assert any(f.amount_sar == Decimal("25000.00") for f in result)

    @pytest.mark.asyncio
    async def test_upsert_fee_structure_create(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict,
        nationality_types: dict,
        fee_categories: dict,
        test_user_id: uuid.UUID,
    ):
        """Test creating fee structure entry."""
        service = ConfigurationService(db_session)

        result = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=academic_levels["MS"].id,
            nationality_type_id=nationality_types["SAUDI"].id,
            fee_category_id=fee_categories["TUITION"].id,
            amount_sar=Decimal("22000.00"),
            trimester=None,
            notes="MS Tuition - Saudi",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.amount_sar == Decimal("22000.00")

    @pytest.mark.asyncio
    async def test_upsert_fee_structure_update(
        self,
        db_session: AsyncSession,
        test_budget_version,
        test_fee_structure,
        academic_levels: dict,
        nationality_types: dict,
        fee_categories: dict,
        test_user_id: uuid.UUID,
    ):
        """Test updating existing fee structure entry."""
        service = ConfigurationService(db_session)

        result = await service.upsert_fee_structure(
            version_id=test_budget_version.id,
            level_id=academic_levels["PS"].id,
            nationality_type_id=nationality_types["FRENCH"].id,
            fee_category_id=fee_categories["TUITION"].id,
            amount_sar=Decimal("26000.00"),
            trimester=None,
            notes="Updated PS Tuition - French",
            user_id=test_user_id,
        )

        assert result.amount_sar == Decimal("26000.00")


# ==============================================================================
# Timetable Constraint Tests
# ==============================================================================


class TestTimetableConstraints:
    """Tests for timetable constraint management."""

    @pytest.mark.asyncio
    async def test_get_timetable_constraints_empty(
        self,
        db_session: AsyncSession,
        test_budget_version,
    ):
        """Test retrieving timetable constraints when empty."""
        service = ConfigurationService(db_session)

        result = await service.get_timetable_constraints(test_budget_version.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_upsert_timetable_constraint_create(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test creating timetable constraint."""
        service = ConfigurationService(db_session)

        result = await service.upsert_timetable_constraint(
            version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            total_hours_per_week=Decimal("28.0"),
            max_hours_per_day=Decimal("7.0"),
            days_per_week=5,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
            notes="6ème timetable constraints",
            user_id=test_user_id,
        )

        assert result.id is not None
        assert result.total_hours_per_week == Decimal("28.0")
        assert result.max_hours_per_day == Decimal("7.0")

    @pytest.mark.asyncio
    async def test_upsert_timetable_constraint_invalid_max_exceeds_total(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test timetable constraint validation: max_hours_per_day <= total_hours_per_week."""
        service = ConfigurationService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_timetable_constraint(
                version_id=test_budget_version.id,
                level_id=academic_levels["6EME"].id,
                total_hours_per_week=Decimal("28.0"),
                max_hours_per_day=Decimal("30.0"),  # > total
                days_per_week=5,
                requires_lunch_break=True,
                min_break_duration_minutes=60,
                notes="Invalid constraint",
                user_id=test_user_id,
            )

        assert "max_hours_per_day cannot exceed total_hours_per_week" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upsert_timetable_constraint_update(
        self,
        db_session: AsyncSession,
        test_budget_version,
        academic_levels: dict,
        test_user_id: uuid.UUID,
    ):
        """Test updating existing timetable constraint."""
        service = ConfigurationService(db_session)

        # First create
        await service.upsert_timetable_constraint(
            version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            total_hours_per_week=Decimal("28.0"),
            max_hours_per_day=Decimal("7.0"),
            days_per_week=5,
            requires_lunch_break=True,
            min_break_duration_minutes=60,
            notes="Initial constraint",
            user_id=test_user_id,
        )

        # Then update
        result = await service.upsert_timetable_constraint(
            version_id=test_budget_version.id,
            level_id=academic_levels["6EME"].id,
            total_hours_per_week=Decimal("30.0"),
            max_hours_per_day=Decimal("6.5"),
            days_per_week=5,
            requires_lunch_break=True,
            min_break_duration_minutes=70,
            notes="Updated constraint",
            user_id=test_user_id,
        )

        assert result.total_hours_per_week == Decimal("30.0")
        assert result.max_hours_per_day == Decimal("6.5")
