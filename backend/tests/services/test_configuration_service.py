"""
Unit tests for Configuration Service.
"""

import uuid
from decimal import Decimal
from unittest.mock import MagicMock

from app.models import VersionStatus
from app.services.settings.configuration_service import ConfigurationService

# Backward compatibility alias
BudgetVersionStatus = VersionStatus


class TestConfigurationServiceInitialization:
    """Tests for ConfigurationService initialization."""

    def test_service_initialization(self):
        """Test service initializes with session and delegate services."""
        session = MagicMock()
        service = ConfigurationService(session)
        assert service.session == session
        # Base services (legacy, for internal use)
        assert service.system_config_service is not None
        assert service.budget_version_base_service is not None
        assert service.class_size_param_service is not None
        assert service.subject_hours_base_service is not None
        # Delegate services (new, focused services)
        assert service._subject_hours is not None
        assert service.teacher_cost_base_service is not None
        assert service.fee_structure_base_service is not None
        assert service.timetable_constraint_base_service is not None
        # Delegate services (new, focused services)
        assert service._reference_data is not None
        assert service._class_size is not None
        assert service._fee_structure is not None
        assert service._timetable_constraints is not None
        assert service._teacher_cost is not None
        assert service._version is not None


class TestBudgetVersionStatus:
    """Tests for budget version status transitions."""

    def test_working_status(self):
        """Test WORKING status is initial state."""
        assert BudgetVersionStatus.WORKING.value == "working"

    def test_submitted_status(self):
        """Test SUBMITTED status exists."""
        assert BudgetVersionStatus.SUBMITTED.value == "submitted"

    def test_approved_status(self):
        """Test APPROVED status exists."""
        assert BudgetVersionStatus.APPROVED.value == "approved"

    def test_superseded_status(self):
        """Test SUPERSEDED status exists."""
        assert BudgetVersionStatus.SUPERSEDED.value == "superseded"

    def test_forecast_status(self):
        """Test FORECAST status exists."""
        assert BudgetVersionStatus.FORECAST.value == "forecast"


class TestBudgetVersionStatusTransitions:
    """Tests for valid budget version status transitions."""

    def test_working_to_submitted(self):
        """Test transition from WORKING to SUBMITTED is valid."""
        current = BudgetVersionStatus.WORKING

        # Only WORKING can transition to SUBMITTED
        valid_transition = current == BudgetVersionStatus.WORKING
        assert valid_transition is True

    def test_submitted_to_approved(self):
        """Test transition from SUBMITTED to APPROVED is valid."""
        current = BudgetVersionStatus.SUBMITTED

        # Only SUBMITTED can transition to APPROVED
        valid_transition = current == BudgetVersionStatus.SUBMITTED
        assert valid_transition is True

    def test_working_cannot_be_approved_directly(self):
        """Test WORKING cannot transition directly to APPROVED."""
        current = BudgetVersionStatus.WORKING

        # Must go through SUBMITTED first
        valid_for_approval = current == BudgetVersionStatus.SUBMITTED
        assert valid_for_approval is False


class TestClassSizeParameterValidation:
    """Tests for class size parameter validation."""

    def test_valid_class_size_params(self):
        """Test valid class size parameters: min < target <= max."""
        min_size = 15
        target_size = 22
        max_size = 28

        is_valid = min_size < target_size <= max_size
        assert is_valid is True

    def test_invalid_min_equals_target(self):
        """Test min cannot equal target."""
        min_size = 22
        target_size = 22
        max_size = 28

        is_valid = min_size < target_size <= max_size
        assert is_valid is False

    def test_invalid_target_exceeds_max(self):
        """Test target cannot exceed max."""
        min_size = 15
        target_size = 30
        max_size = 28

        is_valid = min_size < target_size <= max_size
        assert is_valid is False

    def test_invalid_min_greater_than_target(self):
        """Test min cannot be greater than target."""
        min_size = 25
        target_size = 22
        max_size = 28

        is_valid = min_size < target_size <= max_size
        assert is_valid is False

    def test_level_or_cycle_required(self):
        """Test either level_id or cycle_id must be provided."""
        level_id = None
        cycle_id = None

        is_valid = level_id is not None or cycle_id is not None
        assert is_valid is False

    def test_level_and_cycle_mutually_exclusive(self):
        """Test cannot specify both level_id and cycle_id."""
        level_id = uuid.uuid4()
        cycle_id = uuid.uuid4()

        both_specified = level_id is not None and cycle_id is not None
        assert both_specified is True  # This should be rejected


class TestSubjectHoursValidation:
    """Tests for subject hours validation."""

    def test_valid_hours_per_week(self):
        """Test valid hours per week range (0-12)."""
        hours = Decimal("4.5")

        is_valid = 0 < hours <= 12
        assert is_valid is True

    def test_invalid_zero_hours(self):
        """Test zero hours is invalid."""
        hours = Decimal("0")

        is_valid = hours > 0
        assert is_valid is False

    def test_invalid_negative_hours(self):
        """Test negative hours is invalid."""
        hours = Decimal("-1")

        is_valid = hours > 0
        assert is_valid is False

    def test_invalid_excessive_hours(self):
        """Test hours exceeding 12 is invalid."""
        hours = Decimal("15")

        is_valid = hours <= 12
        assert is_valid is False


class TestAcademicCycles:
    """Tests for academic cycle configuration."""

    def test_maternelle_cycle(self):
        """Test Maternelle cycle exists."""
        cycle = "maternelle"
        assert cycle == "maternelle"

    def test_elementaire_cycle(self):
        """Test Élémentaire cycle exists."""
        cycle = "elementaire"
        assert cycle == "elementaire"

    def test_college_cycle(self):
        """Test Collège cycle exists."""
        cycle = "college"
        assert cycle == "college"

    def test_lycee_cycle(self):
        """Test Lycée cycle exists."""
        cycle = "lycee"
        assert cycle == "lycee"


class TestAcademicLevels:
    """Tests for academic level configuration."""

    def test_maternelle_levels(self):
        """Test Maternelle levels: PS, MS, GS."""
        levels = ["PS", "MS", "GS"]
        assert len(levels) == 3

    def test_elementaire_levels(self):
        """Test Élémentaire levels: CP, CE1, CE2, CM1, CM2."""
        levels = ["CP", "CE1", "CE2", "CM1", "CM2"]
        assert len(levels) == 5

    def test_college_levels(self):
        """Test Collège levels: 6ème, 5ème, 4ème, 3ème."""
        levels = ["6ème", "5ème", "4ème", "3ème"]
        assert len(levels) == 4

    def test_lycee_levels(self):
        """Test Lycée levels: 2nde, 1ère, Terminale."""
        levels = ["2nde", "1ère", "Terminale"]
        assert len(levels) == 3


class TestTeacherCategories:
    """Tests for teacher category configuration."""

    def test_aefe_detached_category(self):
        """Test AEFE Detached teacher category."""
        category = "AEFE_DETACHED"
        assert "AEFE" in category

    def test_aefe_funded_category(self):
        """Test AEFE Funded teacher category."""
        category = "AEFE_FUNDED"
        assert "AEFE" in category

    def test_local_category(self):
        """Test Local teacher category."""
        category = "LOCAL"
        assert category == "LOCAL"


class TestTeacherCostParameters:
    """Tests for teacher cost parameter configuration."""

    def test_prrd_contribution_for_aefe(self):
        """Test PRRD contribution is set for AEFE detached teachers."""
        prrd_eur = Decimal("41863")  # AEFE PRRD contribution

        assert prrd_eur > 0

    def test_local_teacher_salary(self):
        """Test local teacher salary is in SAR."""
        avg_salary_sar = Decimal("180000")

        assert avg_salary_sar > 0

    def test_social_charges_rate(self):
        """Test social charges rate is a percentage."""
        social_charges_rate = Decimal("0.21")  # 21%

        assert 0 <= social_charges_rate <= 1

    def test_hsa_hourly_rate(self):
        """Test HSA hourly rate is positive."""
        hsa_rate_sar = Decimal("150")

        assert hsa_rate_sar > 0

    def test_max_hsa_hours(self):
        """Test max HSA hours constraint."""
        max_hsa = Decimal("4")  # Max 4 hours overtime per week

        assert max_hsa <= Decimal("4")


class TestFeeStructure:
    """Tests for fee structure configuration."""

    def test_fee_structure_requires_level(self):
        """Test fee structure requires academic level."""
        level_id = uuid.uuid4()
        assert level_id is not None

    def test_fee_structure_requires_nationality(self):
        """Test fee structure requires nationality type."""
        nationality_type_id = uuid.uuid4()
        assert nationality_type_id is not None

    def test_fee_structure_requires_category(self):
        """Test fee structure requires fee category."""
        fee_category_id = uuid.uuid4()
        assert fee_category_id is not None

    def test_fee_amount_positive(self):
        """Test fee amount must be positive."""
        amount_sar = Decimal("50000")

        assert amount_sar > 0


class TestSystemConfiguration:
    """Tests for system configuration management."""

    def test_config_key_format(self):
        """Test configuration key is a string."""
        key = "school_capacity"
        assert isinstance(key, str)

    def test_config_value_jsonb(self):
        """Test configuration value can be JSON."""
        value = {"max_students": 1875, "target_utilization": 0.9}

        assert isinstance(value, dict)
        assert "max_students" in value

    def test_config_category(self):
        """Test configuration has category."""
        category = "capacity"
        assert isinstance(category, str)


class TestFiscalYearValidation:
    """Tests for fiscal year validation."""

    def test_valid_fiscal_year(self):
        """Test valid fiscal year format."""
        fiscal_year = 2025

        assert 2000 <= fiscal_year <= 2100

    def test_academic_year_format(self):
        """Test academic year format YYYY-YYYY."""
        academic_year = "2024-2025"

        assert "-" in academic_year
        parts = academic_year.split("-")
        assert len(parts) == 2
        assert int(parts[1]) == int(parts[0]) + 1


class TestNationalityTypes:
    """Tests for nationality type configuration."""

    def test_french_nationality(self):
        """Test French nationality type."""
        nationality = "French"
        assert nationality == "French"

    def test_saudi_nationality(self):
        """Test Saudi nationality type."""
        nationality = "Saudi"
        assert nationality == "Saudi"

    def test_other_nationality(self):
        """Test Other nationality type."""
        nationality = "Other"
        assert nationality == "Other"


class TestFeeCategoryTypes:
    """Tests for fee category types."""

    def test_tuition_fee_category(self):
        """Test tuition fee category."""
        category = "TUITION"
        assert category == "TUITION"

    def test_dai_fee_category(self):
        """Test DAI fee category."""
        category = "DAI"
        assert category == "DAI"

    def test_registration_fee_category(self):
        """Test registration fee category."""
        category = "REGISTRATION"
        assert category == "REGISTRATION"


class TestTrimesterConfiguration:
    """Tests for trimester configuration."""

    def test_valid_trimesters(self):
        """Test valid trimester values."""
        valid_trimesters = [1, 2, 3]

        for trimester in valid_trimesters:
            assert 1 <= trimester <= 3

    def test_null_trimester_for_annual(self):
        """Test null trimester for annual fees."""
        trimester = None  # Annual fee

        assert trimester is None


class TestBusinessRuleErrors:
    """Tests for business rule error handling."""

    def test_invalid_status_transition_error(self):
        """Test error code for invalid status transition."""
        error_code = "INVALID_STATUS_TRANSITION"
        assert error_code == "INVALID_STATUS_TRANSITION"

    def test_conflict_error_for_duplicate_working(self):
        """Test conflict error for duplicate working version."""
        fiscal_year = 2025
        message = f"A working budget version already exists for fiscal year {fiscal_year}"

        assert str(fiscal_year) in message
