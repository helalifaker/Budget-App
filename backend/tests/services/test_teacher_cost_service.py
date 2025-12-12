"""
Comprehensive tests for TeacherCostParametersService.

Tests all teacher cost parameter operations including:
- Retrieval of teacher cost parameters
- Creation and update (upsert) operations
- Validation of social_charges_rate, hsa_hourly_rate, max_hsa_hours
- Category-specific vs cycle-specific parameters
- AEFE vs Local teacher cost handling
- Soft delete functionality
"""

import uuid
from decimal import Decimal

import pytest
from app.models.configuration import AcademicCycle, TeacherCategory
from app.services.exceptions import ValidationError
from app.services.teacher_cost_service import TeacherCostParametersService
from sqlalchemy.ext.asyncio import AsyncSession


class TestTeacherCostParametersServiceInitialization:
    """Tests for TeacherCostParametersService initialization."""

    def test_service_initialization(self, db_session: AsyncSession):
        """Test service initializes with session."""
        service = TeacherCostParametersService(db_session)
        assert service.session == db_session
        assert service._base_service is not None


class TestGetTeacherCostParams:
    """Tests for retrieving teacher cost parameters."""

    @pytest.mark.asyncio
    async def test_get_teacher_cost_params_empty(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving params when none exist."""
        service = TeacherCostParametersService(db_session)
        params = await service.get_teacher_cost_params(test_budget_version.id)
        assert params == []

    @pytest.mark.asyncio
    async def test_get_teacher_cost_params_returns_all_for_version(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test retrieving all teacher cost params for a budget version."""
        service = TeacherCostParametersService(db_session)

        # Create a teacher cost param
        aefe_cat = teacher_categories["AEFE_DETACHED"]
        param = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=aefe_cat.id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41863.00"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("0.00"),
            hsa_hourly_rate_sar=Decimal("200.00"),
            max_hsa_hours=Decimal("4.0"),
        )

        # Retrieve all params
        params = await service.get_teacher_cost_params(test_budget_version.id)
        assert len(params) >= 1
        assert any(p.id == param.id for p in params)


class TestGetTeacherCostParamByCriteria:
    """Tests for retrieving params by specific criteria."""

    @pytest.mark.asyncio
    async def test_get_param_by_criteria_not_found(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving param with non-matching criteria returns None."""
        service = TeacherCostParametersService(db_session)
        param = await service.get_teacher_cost_param_by_criteria(
            version_id=test_budget_version.id,
            category_id=uuid.uuid4(),
            cycle_id=None,
        )
        assert param is None

    @pytest.mark.asyncio
    async def test_get_param_by_criteria_global(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test retrieving global param (cycle_id=None)."""
        service = TeacherCostParametersService(db_session)

        aefe_cat = teacher_categories["AEFE_DETACHED"]
        created = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=aefe_cat.id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41863.00"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("0.00"),
            hsa_hourly_rate_sar=Decimal("200.00"),
            max_hsa_hours=Decimal("4.0"),
        )

        # Retrieve by criteria
        param = await service.get_teacher_cost_param_by_criteria(
            version_id=test_budget_version.id,
            category_id=aefe_cat.id,
            cycle_id=None,
        )
        assert param is not None
        assert param.id == created.id

    @pytest.mark.asyncio
    async def test_get_param_by_criteria_cycle_specific(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
    ):
        """Test retrieving cycle-specific param."""
        service = TeacherCostParametersService(db_session)

        local_cat = teacher_categories["LOCAL"]
        college_cycle = academic_cycles["college"]

        # Create cycle-specific param
        created = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=college_cycle.id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("24000.00"),
            hsa_hourly_rate_sar=Decimal("150.00"),
            max_hsa_hours=Decimal("2.0"),
        )

        # Retrieve by criteria with cycle
        param = await service.get_teacher_cost_param_by_criteria(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=college_cycle.id,
        )
        assert param is not None
        assert param.id == created.id

        # Global param for same category should not be found
        global_param = await service.get_teacher_cost_param_by_criteria(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=None,
        )
        assert global_param is None


class TestGetParamsByCategory:
    """Tests for retrieving params by category."""

    @pytest.mark.asyncio
    async def test_get_params_by_category_empty(
        self, db_session: AsyncSession, test_budget_version
    ):
        """Test retrieving params for category with no params."""
        service = TeacherCostParametersService(db_session)
        params = await service.get_params_by_category(
            test_budget_version.id, uuid.uuid4()
        )
        assert params == []

    @pytest.mark.asyncio
    async def test_get_params_by_category_returns_all(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
    ):
        """Test retrieving all params for a specific category."""
        service = TeacherCostParametersService(db_session)

        local_cat = teacher_categories["LOCAL"]
        college_cycle = academic_cycles["college"]
        lycee_cycle = academic_cycles["lycee"]

        # Create multiple params for LOCAL category (different cycles)
        await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=college_cycle.id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("24000.00"),
            hsa_hourly_rate_sar=Decimal("150.00"),
            max_hsa_hours=Decimal("2.0"),
        )
        await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=lycee_cycle.id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("200000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("30000.00"),
            hsa_hourly_rate_sar=Decimal("175.00"),
            max_hsa_hours=Decimal("2.0"),
        )

        # Retrieve params for LOCAL category
        params = await service.get_params_by_category(
            test_budget_version.id, local_cat.id
        )
        assert len(params) >= 2


class TestUpsertTeacherCostParam:
    """Tests for creating and updating teacher cost parameters."""

    @pytest.mark.asyncio
    async def test_create_aefe_detached_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test creating param for AEFE detached teacher (PRRD contribution)."""
        service = TeacherCostParametersService(db_session)

        aefe_cat = teacher_categories["AEFE_DETACHED"]
        param = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=aefe_cat.id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41863.00"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("0.00"),
            hsa_hourly_rate_sar=Decimal("200.00"),
            max_hsa_hours=Decimal("4.0"),
            notes="AEFE Detached - PRRD contribution",
        )

        assert param.id is not None
        assert param.budget_version_id == test_budget_version.id
        assert param.category_id == aefe_cat.id
        assert param.cycle_id is None
        assert param.prrd_contribution_eur == Decimal("41863.00")
        assert param.avg_salary_sar is None
        assert param.social_charges_rate == Decimal("0.12")
        assert param.hsa_hourly_rate_sar == Decimal("200.00")
        assert param.max_hsa_hours == Decimal("4.0")

    @pytest.mark.asyncio
    async def test_create_local_teacher_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
    ):
        """Test creating param for local teacher (direct salary in SAR)."""
        service = TeacherCostParametersService(db_session)

        local_cat = teacher_categories["LOCAL"]
        college_cycle = academic_cycles["college"]

        param = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=college_cycle.id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("24000.00"),
            hsa_hourly_rate_sar=Decimal("150.00"),
            max_hsa_hours=Decimal("2.0"),
            notes="Local secondary teacher",
        )

        assert param.prrd_contribution_eur is None
        assert param.avg_salary_sar == Decimal("180000.00")
        assert param.cycle_id == college_cycle.id
        assert param.benefits_allowance_sar == Decimal("24000.00")

    @pytest.mark.asyncio
    async def test_create_aefe_funded_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test creating param for AEFE funded teacher (no cost to school)."""
        service = TeacherCostParametersService(db_session)

        aefe_funded_cat = teacher_categories["AEFE_FUNDED"]
        param = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=aefe_funded_cat.id,
            cycle_id=None,
            prrd_contribution_eur=None,  # No cost
            avg_salary_sar=None,  # No cost
            social_charges_rate=Decimal("0.00"),
            benefits_allowance_sar=Decimal("0.00"),
            hsa_hourly_rate_sar=Decimal("0.00"),
            max_hsa_hours=Decimal("0.0"),
            notes="AEFE Funded - no cost to school",
        )

        assert param.prrd_contribution_eur is None
        assert param.avg_salary_sar is None
        assert param.social_charges_rate == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_update_existing_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test updating an existing teacher cost param."""
        service = TeacherCostParametersService(db_session)

        local_cat = teacher_categories["LOCAL"]

        # Create initial param
        param1 = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=None,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("150000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("20000.00"),
            hsa_hourly_rate_sar=Decimal("120.00"),
            max_hsa_hours=Decimal("2.0"),
        )

        # Update the same param
        param2 = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=None,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("160000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("25000.00"),
            hsa_hourly_rate_sar=Decimal("130.00"),
            max_hsa_hours=Decimal("3.0"),
            notes="Updated salary",
        )

        # Should be the same record, not a new one
        assert param2.id == param1.id
        assert param2.avg_salary_sar == Decimal("160000.00")
        assert param2.benefits_allowance_sar == Decimal("25000.00")
        assert param2.hsa_hourly_rate_sar == Decimal("130.00")
        assert param2.max_hsa_hours == Decimal("3.0")
        assert param2.notes == "Updated salary"


class TestTeacherCostParamValidation:
    """Tests for teacher cost parameter validation rules."""

    @pytest.mark.asyncio
    async def test_validation_social_charges_rate_too_low(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test validation: social_charges_rate must be >= 0."""
        service = TeacherCostParametersService(db_session)
        local_cat = teacher_categories["LOCAL"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_teacher_cost_param(
                version_id=test_budget_version.id,
                category_id=local_cat.id,
                cycle_id=None,
                prrd_contribution_eur=None,
                avg_salary_sar=Decimal("150000.00"),
                social_charges_rate=Decimal("-0.05"),  # Invalid: negative
                benefits_allowance_sar=Decimal("0.00"),
                hsa_hourly_rate_sar=Decimal("100.00"),
                max_hsa_hours=Decimal("2.0"),
            )

        assert "social_charges_rate must be between 0 and 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_social_charges_rate_too_high(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test validation: social_charges_rate must be <= 1."""
        service = TeacherCostParametersService(db_session)
        local_cat = teacher_categories["LOCAL"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_teacher_cost_param(
                version_id=test_budget_version.id,
                category_id=local_cat.id,
                cycle_id=None,
                prrd_contribution_eur=None,
                avg_salary_sar=Decimal("150000.00"),
                social_charges_rate=Decimal("1.5"),  # Invalid: > 100%
                benefits_allowance_sar=Decimal("0.00"),
                hsa_hourly_rate_sar=Decimal("100.00"),
                max_hsa_hours=Decimal("2.0"),
            )

        assert "social_charges_rate must be between 0 and 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_hsa_hourly_rate_negative(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test validation: hsa_hourly_rate_sar must be non-negative."""
        service = TeacherCostParametersService(db_session)
        local_cat = teacher_categories["LOCAL"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_teacher_cost_param(
                version_id=test_budget_version.id,
                category_id=local_cat.id,
                cycle_id=None,
                prrd_contribution_eur=None,
                avg_salary_sar=Decimal("150000.00"),
                social_charges_rate=Decimal("0.12"),
                benefits_allowance_sar=Decimal("0.00"),
                hsa_hourly_rate_sar=Decimal("-50.00"),  # Invalid: negative
                max_hsa_hours=Decimal("2.0"),
            )

        assert "hsa_hourly_rate_sar must be non-negative" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_max_hsa_hours_negative(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test validation: max_hsa_hours must be >= 0."""
        service = TeacherCostParametersService(db_session)
        local_cat = teacher_categories["LOCAL"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_teacher_cost_param(
                version_id=test_budget_version.id,
                category_id=local_cat.id,
                cycle_id=None,
                prrd_contribution_eur=None,
                avg_salary_sar=Decimal("150000.00"),
                social_charges_rate=Decimal("0.12"),
                benefits_allowance_sar=Decimal("0.00"),
                hsa_hourly_rate_sar=Decimal("100.00"),
                max_hsa_hours=Decimal("-1.0"),  # Invalid: negative
            )

        assert "max_hsa_hours must be between 0 and 10" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_max_hsa_hours_too_high(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test validation: max_hsa_hours must be <= 10."""
        service = TeacherCostParametersService(db_session)
        local_cat = teacher_categories["LOCAL"]

        with pytest.raises(ValidationError) as exc_info:
            await service.upsert_teacher_cost_param(
                version_id=test_budget_version.id,
                category_id=local_cat.id,
                cycle_id=None,
                prrd_contribution_eur=None,
                avg_salary_sar=Decimal("150000.00"),
                social_charges_rate=Decimal("0.12"),
                benefits_allowance_sar=Decimal("0.00"),
                hsa_hourly_rate_sar=Decimal("100.00"),
                max_hsa_hours=Decimal("15.0"),  # Invalid: > 10
            )

        assert "max_hsa_hours must be between 0 and 10" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_valid_params_passes(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test that valid parameters pass validation."""
        service = TeacherCostParametersService(db_session)
        local_cat = teacher_categories["LOCAL"]

        # This should not raise
        param = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=None,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("150000.00"),
            social_charges_rate=Decimal("0.12"),  # Valid: 12%
            benefits_allowance_sar=Decimal("20000.00"),
            hsa_hourly_rate_sar=Decimal("100.00"),  # Valid: positive
            max_hsa_hours=Decimal("4.0"),  # Valid: 4 hours
        )

        assert param is not None


class TestDeleteTeacherCostParam:
    """Tests for deleting teacher cost parameters."""

    @pytest.mark.asyncio
    async def test_delete_teacher_cost_param(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test soft deleting a teacher cost param."""
        service = TeacherCostParametersService(db_session)
        local_cat = teacher_categories["LOCAL"]

        # Create param
        param = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=None,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("150000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("20000.00"),
            hsa_hourly_rate_sar=Decimal("100.00"),
            max_hsa_hours=Decimal("2.0"),
        )

        # Delete it
        result = await service.delete_teacher_cost_param(param.id)
        assert result is True

        # Should not be found anymore
        found = await service.get_teacher_cost_param_by_criteria(
            test_budget_version.id, local_cat.id, None
        )
        assert found is None


class TestTeacherCostBusinessRules:
    """Tests for teacher cost business rules."""

    @pytest.mark.asyncio
    async def test_different_categories_different_params(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
    ):
        """Test that different categories can have different cost parameters."""
        service = TeacherCostParametersService(db_session)

        aefe_cat = teacher_categories["AEFE_DETACHED"]
        local_cat = teacher_categories["LOCAL"]

        # AEFE Detached - PRRD contribution
        param_aefe = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=aefe_cat.id,
            cycle_id=None,
            prrd_contribution_eur=Decimal("41863.00"),
            avg_salary_sar=None,
            social_charges_rate=Decimal("0.00"),
            benefits_allowance_sar=Decimal("0.00"),
            hsa_hourly_rate_sar=Decimal("200.00"),
            max_hsa_hours=Decimal("4.0"),
        )

        # Local Teacher - direct salary
        param_local = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=None,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("24000.00"),
            hsa_hourly_rate_sar=Decimal("150.00"),
            max_hsa_hours=Decimal("2.0"),
        )

        assert param_aefe.id != param_local.id
        assert param_aefe.prrd_contribution_eur == Decimal("41863.00")
        assert param_local.avg_salary_sar == Decimal("180000.00")

    @pytest.mark.asyncio
    async def test_same_category_different_cycles(
        self,
        db_session: AsyncSession,
        test_budget_version,
        teacher_categories: dict[str, TeacherCategory],
        academic_cycles: dict[str, AcademicCycle],
    ):
        """Test that same category can have different params per cycle."""
        service = TeacherCostParametersService(db_session)

        local_cat = teacher_categories["LOCAL"]
        elementaire = academic_cycles["elementaire"]
        college = academic_cycles["college"]

        # Primary teacher - lower salary
        param_primary = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=elementaire.id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("150000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("18000.00"),
            hsa_hourly_rate_sar=Decimal("120.00"),
            max_hsa_hours=Decimal("2.0"),
        )

        # Secondary teacher - higher salary
        param_secondary = await service.upsert_teacher_cost_param(
            version_id=test_budget_version.id,
            category_id=local_cat.id,
            cycle_id=college.id,
            prrd_contribution_eur=None,
            avg_salary_sar=Decimal("180000.00"),
            social_charges_rate=Decimal("0.12"),
            benefits_allowance_sar=Decimal("24000.00"),
            hsa_hourly_rate_sar=Decimal("150.00"),
            max_hsa_hours=Decimal("2.0"),
        )

        assert param_primary.id != param_secondary.id
        assert param_primary.avg_salary_sar < param_secondary.avg_salary_sar
        assert param_primary.cycle_id == elementaire.id
        assert param_secondary.cycle_id == college.id
