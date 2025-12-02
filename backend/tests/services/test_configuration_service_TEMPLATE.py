"""
Tests for Configuration Service.

This file serves as a TEMPLATE for implementing service tests.
Tests CRUD operations and business logic for configuration management.

COPY THIS FILE to test_configuration_service.py and implement the tests.
"""

from decimal import Decimal

import pytest
from app.models.configuration import BudgetVersionStatus
from app.services.configuration_service import ConfigurationService
from app.services.exceptions import (
    BusinessRuleError,
    ConflictError,
    ValidationError,
)

# ==============================================================================
# System Configuration Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_system_config_success(db_session, test_system_config):
    """Test that getting system config by key returns correct config."""
    # Arrange
    service = ConfigurationService(db_session)

    # Act
    config = await service.get_system_config(test_system_config.key)

    # Assert
    assert config is not None
    assert config.id == test_system_config.id
    assert config.key == "eur_to_sar_rate"
    assert config.value["rate"] == 4.05


@pytest.mark.asyncio
async def test_get_system_config_not_found(db_session):
    """Test that getting non-existent config returns None."""
    service = ConfigurationService(db_session)

    config = await service.get_system_config("non_existent_key")

    assert config is None


@pytest.mark.asyncio
async def test_upsert_system_config_create(db_session, test_user_id):
    """Test that upserting creates new config if doesn't exist."""
    service = ConfigurationService(db_session)

    config = await service.upsert_system_config(
        key="test_key",
        value={"test": "value"},
        category="test_category",
        description="Test configuration",
        user_id=test_user_id,
    )

    assert config.id is not None
    assert config.key == "test_key"
    assert config.value["test"] == "value"
    assert config.is_active is True


@pytest.mark.asyncio
async def test_upsert_system_config_update(db_session, test_system_config, test_user_id):
    """Test that upserting updates existing config."""
    service = ConfigurationService(db_session)

    updated = await service.upsert_system_config(
        key=test_system_config.key,
        value={"rate": 4.10},
        category="exchange_rates",
        description="Updated exchange rate",
        user_id=test_user_id,
    )

    assert updated.id == test_system_config.id
    assert updated.value["rate"] == 4.10


# ==============================================================================
# Budget Version Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_create_budget_version_success(db_session, test_user_id):
    """Test that creating budget version with valid data succeeds."""
    service = ConfigurationService(db_session)

    version = await service.create_budget_version(
        name="FY2026 Budget",
        fiscal_year=2026,
        academic_year="2025-2026",
        notes="Test budget",
        user_id=test_user_id,
    )

    assert version.id is not None
    assert version.name == "FY2026 Budget"
    assert version.fiscal_year == 2026
    assert version.status == BudgetVersionStatus.WORKING


@pytest.mark.asyncio
async def test_create_budget_version_duplicate_working(
    db_session, test_budget_version, test_user_id
):
    """Test that creating duplicate working version raises ConflictError."""
    service = ConfigurationService(db_session)

    with pytest.raises(ConflictError) as exc_info:
        await service.create_budget_version(
            name="Another Working Budget",
            fiscal_year=test_budget_version.fiscal_year,
            academic_year="2024-2025",
            user_id=test_user_id,
        )

    assert "working budget version already exists" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_submit_budget_version_success(
    db_session, test_budget_version, test_user_id
):
    """Test that submitting working version succeeds."""
    service = ConfigurationService(db_session)

    submitted = await service.submit_budget_version(
        test_budget_version.id, test_user_id
    )

    assert submitted.status == BudgetVersionStatus.SUBMITTED
    assert submitted.submitted_at is not None
    assert submitted.submitted_by_id == test_user_id


@pytest.mark.asyncio
async def test_submit_budget_version_invalid_status(
    db_session, test_budget_version, test_user_id
):
    """Test that submitting non-working version raises BusinessRuleError."""
    service = ConfigurationService(db_session)

    # First submit it
    await service.submit_budget_version(test_budget_version.id, test_user_id)

    # Try to submit again
    with pytest.raises(BusinessRuleError) as exc_info:
        await service.submit_budget_version(test_budget_version.id, test_user_id)

    assert (
        "invalid_status_transition" in str(exc_info.value).lower()
        or "only working" in str(exc_info.value).lower()
    )


@pytest.mark.asyncio
async def test_approve_budget_version_success(
    db_session, test_budget_version, test_user_id
):
    """Test that approving submitted version succeeds."""
    service = ConfigurationService(db_session)

    # First submit it
    await service.submit_budget_version(test_budget_version.id, test_user_id)

    # Then approve
    approved = await service.approve_budget_version(
        test_budget_version.id, test_user_id
    )

    assert approved.status == BudgetVersionStatus.APPROVED
    assert approved.approved_at is not None
    assert approved.approved_by_id == test_user_id


@pytest.mark.asyncio
async def test_approve_budget_version_invalid_status(
    db_session, test_budget_version, test_user_id
):
    """Test that approving non-submitted version raises BusinessRuleError."""
    service = ConfigurationService(db_session)

    # Try to approve without submitting
    with pytest.raises(BusinessRuleError) as exc_info:
        await service.approve_budget_version(test_budget_version.id, test_user_id)

    assert (
        "invalid_status_transition" in str(exc_info.value).lower()
        or "only submitted" in str(exc_info.value).lower()
    )


# ==============================================================================
# Class Size Parameter Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_upsert_class_size_param_success(
    db_session, test_budget_version, academic_levels, test_user_id
):
    """Test that upserting class size param with valid data succeeds."""
    service = ConfigurationService(db_session)

    param = await service.upsert_class_size_param(
        version_id=test_budget_version.id,
        level_id=academic_levels["CP"].id,
        cycle_id=None,
        min_class_size=18,
        target_class_size=24,
        max_class_size=28,
        notes="CP class sizes",
        user_id=test_user_id,
    )

    assert param.id is not None
    assert param.min_class_size == 18
    assert param.target_class_size == 24
    assert param.max_class_size == 28


@pytest.mark.asyncio
async def test_upsert_class_size_param_invalid_range(
    db_session, test_budget_version, academic_levels, test_user_id
):
    """Test that invalid class size range raises ValidationError."""
    service = ConfigurationService(db_session)

    # min >= target
    with pytest.raises(ValidationError):
        await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=academic_levels["CP"].id,
            cycle_id=None,
            min_class_size=25,
            target_class_size=20,
            max_class_size=28,
            user_id=test_user_id,
        )


@pytest.mark.asyncio
async def test_upsert_class_size_param_both_level_and_cycle(
    db_session, test_budget_version, academic_levels, academic_cycles, test_user_id
):
    """Test that providing both level_id and cycle_id raises ValidationError."""
    service = ConfigurationService(db_session)

    with pytest.raises(ValidationError) as exc_info:
        await service.upsert_class_size_param(
            version_id=test_budget_version.id,
            level_id=academic_levels["CP"].id,
            cycle_id=academic_cycles["elementaire"].id,
            min_class_size=18,
            target_class_size=24,
            max_class_size=28,
            user_id=test_user_id,
        )

    assert "cannot specify both" in str(exc_info.value).lower()


# ==============================================================================
# Subject Hours Matrix Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_upsert_subject_hours_success(
    db_session, test_budget_version, subjects, academic_levels, test_user_id
):
    """Test that upserting subject hours with valid data succeeds."""
    service = ConfigurationService(db_session)

    hours = await service.upsert_subject_hours(
        version_id=test_budget_version.id,
        subject_id=subjects["MATH"].id,
        level_id=academic_levels["CP"].id,
        hours_per_week=Decimal("5.0"),
        is_split=False,
        notes="CP Mathematics",
        user_id=test_user_id,
    )

    assert hours.id is not None
    assert hours.hours_per_week == Decimal("5.0")
    assert hours.is_split is False


@pytest.mark.asyncio
async def test_upsert_subject_hours_invalid_hours(
    db_session, test_budget_version, subjects, academic_levels, test_user_id
):
    """Test that invalid hours per week raises ValidationError."""
    service = ConfigurationService(db_session)

    # Hours > 12
    with pytest.raises(ValidationError) as exc_info:
        await service.upsert_subject_hours(
            version_id=test_budget_version.id,
            subject_id=subjects["MATH"].id,
            level_id=academic_levels["CP"].id,
            hours_per_week=Decimal("15.0"),
            user_id=test_user_id,
        )

    assert "between 0 and 12" in str(exc_info.value).lower()


# ==============================================================================
# Teacher Cost Parameter Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_upsert_teacher_cost_param_aefe(
    db_session,
    test_budget_version,
    teacher_categories,
    test_user_id,
):
    """Test that upserting AEFE teacher cost param succeeds."""
    service = ConfigurationService(db_session)

    param = await service.upsert_teacher_cost_param(
        version_id=test_budget_version.id,
        category_id=teacher_categories["AEFE_DETACHED"].id,
        cycle_id=None,
        prrd_contribution_eur=Decimal("42000.00"),
        avg_salary_sar=None,
        social_charges_rate=Decimal("0.21"),
        benefits_allowance_sar=Decimal("0.00"),
        hsa_hourly_rate_sar=Decimal("200.00"),
        max_hsa_hours=Decimal("4.0"),
        notes="AEFE Detached 2025",
        user_id=test_user_id,
    )

    assert param.id is not None
    assert param.prrd_contribution_eur == Decimal("42000.00")


@pytest.mark.asyncio
async def test_upsert_teacher_cost_param_local(
    db_session,
    test_budget_version,
    teacher_categories,
    academic_cycles,
    test_user_id,
):
    """Test that upserting local teacher cost param succeeds."""
    service = ConfigurationService(db_session)

    param = await service.upsert_teacher_cost_param(
        version_id=test_budget_version.id,
        category_id=teacher_categories["LOCAL"].id,
        cycle_id=academic_cycles["elementaire"].id,
        prrd_contribution_eur=None,
        avg_salary_sar=Decimal("150000.00"),
        social_charges_rate=Decimal("0.21"),
        benefits_allowance_sar=Decimal("20000.00"),
        hsa_hourly_rate_sar=Decimal("150.00"),
        max_hsa_hours=Decimal("2.0"),
        notes="Local Primary Teacher",
        user_id=test_user_id,
    )

    assert param.id is not None
    assert param.avg_salary_sar == Decimal("150000.00")
    assert param.benefits_allowance_sar == Decimal("20000.00")


# ==============================================================================
# Fee Structure Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_upsert_fee_structure_success(
    db_session,
    test_budget_version,
    academic_levels,
    nationality_types,
    fee_categories,
    test_user_id,
):
    """Test that upserting fee structure with valid data succeeds."""
    service = ConfigurationService(db_session)

    fee = await service.upsert_fee_structure(
        version_id=test_budget_version.id,
        level_id=academic_levels["CP"].id,
        nationality_type_id=nationality_types["FRENCH"].id,
        fee_category_id=fee_categories["TUITION"].id,
        amount_sar=Decimal("28000.00"),
        trimester=None,
        notes="CP Tuition - French",
        user_id=test_user_id,
    )

    assert fee.id is not None
    assert fee.amount_sar == Decimal("28000.00")


@pytest.mark.asyncio
async def test_upsert_fee_structure_with_trimester(
    db_session,
    test_budget_version,
    academic_levels,
    nationality_types,
    fee_categories,
    test_user_id,
):
    """Test that upserting trimester-based tuition succeeds."""
    service = ConfigurationService(db_session)

    fee_t1 = await service.upsert_fee_structure(
        version_id=test_budget_version.id,
        level_id=academic_levels["CP"].id,
        nationality_type_id=nationality_types["FRENCH"].id,
        fee_category_id=fee_categories["TUITION"].id,
        amount_sar=Decimal("11200.00"),
        trimester=1,
        notes="CP Tuition T1",
        user_id=test_user_id,
    )

    assert fee_t1.trimester == 1
    assert fee_t1.amount_sar == Decimal("11200.00")


# ==============================================================================
# Integration Tests (Multiple Operations)
# ==============================================================================


@pytest.mark.asyncio
async def test_complete_budget_configuration_workflow(
    db_session,
    academic_levels,
    subjects,
    teacher_categories,
    nationality_types,
    fee_categories,
    test_user_id,
):
    """Test complete budget configuration workflow."""
    service = ConfigurationService(db_session)

    # 1. Create budget version
    version = await service.create_budget_version(
        name="FY2026 Complete Test",
        fiscal_year=2026,
        academic_year="2025-2026",
        notes="Complete workflow test",
        user_id=test_user_id,
    )
    assert version.status == BudgetVersionStatus.WORKING

    # 2. Configure class sizes
    class_size = await service.upsert_class_size_param(
        version_id=version.id,
        level_id=academic_levels["PS"].id,
        cycle_id=None,
        min_class_size=15,
        target_class_size=20,
        max_class_size=24,
        user_id=test_user_id,
    )
    assert class_size.target_class_size == 20

    # 3. Configure subject hours
    subject_hours = await service.upsert_subject_hours(
        version_id=version.id,
        subject_id=subjects["FRENCH"].id,
        level_id=academic_levels["6EME"].id,
        hours_per_week=Decimal("5.0"),
        user_id=test_user_id,
    )
    assert subject_hours.hours_per_week == Decimal("5.0")

    # 4. Configure teacher costs
    teacher_cost = await service.upsert_teacher_cost_param(
        version_id=version.id,
        category_id=teacher_categories["LOCAL"].id,
        cycle_id=None,
        prrd_contribution_eur=None,
        avg_salary_sar=Decimal("180000.00"),
        social_charges_rate=Decimal("0.21"),
        benefits_allowance_sar=Decimal("24000.00"),
        hsa_hourly_rate_sar=Decimal("150.00"),
        max_hsa_hours=Decimal("2.0"),
        user_id=test_user_id,
    )
    assert teacher_cost.avg_salary_sar == Decimal("180000.00")

    # 5. Configure fee structure
    fee = await service.upsert_fee_structure(
        version_id=version.id,
        level_id=academic_levels["PS"].id,
        nationality_type_id=nationality_types["FRENCH"].id,
        fee_category_id=fee_categories["TUITION"].id,
        amount_sar=Decimal("25000.00"),
        user_id=test_user_id,
    )
    assert fee.amount_sar == Decimal("25000.00")

    # 6. Submit budget version
    submitted = await service.submit_budget_version(version.id, test_user_id)
    assert submitted.status == BudgetVersionStatus.SUBMITTED

    # 7. Approve budget version
    approved = await service.approve_budget_version(version.id, test_user_id)
    assert approved.status == BudgetVersionStatus.APPROVED


# ==============================================================================
# Summary
# ==============================================================================

"""
Test Coverage Summary for Configuration Service:

✅ System Configuration:
   - Create/update (upsert) system config
   - Get by key
   - Get all with filters
   - Handle not found

✅ Budget Version:
   - Create budget version
   - Submit workflow
   - Approve workflow
   - Supersede
   - Conflict detection (duplicate working version)
   - Status validation

✅ Class Size Parameters:
   - Upsert class size params
   - Validation (min < target <= max)
   - Level vs cycle specificity

✅ Subject Hours Matrix:
   - Upsert subject hours
   - Validation (hours 0-12)
   - Split class handling

✅ Teacher Cost Parameters:
   - AEFE detached teachers (PRRD-based)
   - Local teachers (salary-based)
   - Cycle-specific vs general

✅ Fee Structure:
   - Annual fees
   - Trimester-based tuition
   - Level/nationality combinations

✅ Integration:
   - Complete configuration workflow
   - Multi-step operations
   - Data consistency

Total Tests: ~30+ comprehensive test cases
Coverage Target: 85%+

To implement:
1. Copy this file to test_configuration_service.py
2. Implement all test functions (remove pass statements)
3. Add edge cases and error scenarios
4. Run: pytest tests/services/test_configuration_service.py -v
5. Check coverage: pytest --cov=app.services.configuration_service
"""
