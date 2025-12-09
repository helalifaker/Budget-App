"""
Tests for KPI (Key Performance Indicator) Service.

Covers:
- KPI definition retrieval
- KPI calculation for all types
- KPI value storage and retrieval
- Trend analysis across versions
- AEFE benchmark comparison
- Error handling

Target Coverage: 90%+
"""

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.analysis import KPICategory, KPIDefinition, KPIValue
from app.models.configuration import AcademicLevel, BudgetVersion, BudgetVersionStatus, Subject
from app.models.planning import DHGSubjectHours
from app.services.exceptions import NotFoundError, ValidationError
from app.services.kpi_service import KPIService
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    """Create mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def kpi_service(mock_session):
    """Create KPI service instance."""
    return KPIService(mock_session)


@pytest.fixture
def mock_budget_version():
    """Create mock budget version."""
    version = MagicMock(spec=BudgetVersion)
    version.id = uuid.uuid4()
    version.name = "Budget 2024"
    version.fiscal_year = 2024
    version.academic_year = "2024-2025"
    version.status = BudgetVersionStatus.WORKING
    return version


@pytest.fixture
def mock_kpi_definitions():
    """Create mock KPI definitions for all types."""
    definitions = []

    # Educational KPIs
    h_e_primary = MagicMock(spec=KPIDefinition)
    h_e_primary.id = uuid.uuid4()
    h_e_primary.code = "H_E_PRIMARY"
    h_e_primary.name_en = "Hours per Student (Primary)"
    h_e_primary.name_fr = "H/E Primaire"
    h_e_primary.category = KPICategory.EDUCATIONAL
    h_e_primary.unit = "hours"
    h_e_primary.target_value = Decimal("1.1")
    h_e_primary.is_active = True
    definitions.append(h_e_primary)

    h_e_secondary = MagicMock(spec=KPIDefinition)
    h_e_secondary.id = uuid.uuid4()
    h_e_secondary.code = "H_E_SECONDARY"
    h_e_secondary.name_en = "Hours per Student (Secondary)"
    h_e_secondary.name_fr = "H/E Secondaire"
    h_e_secondary.category = KPICategory.EDUCATIONAL
    h_e_secondary.unit = "hours"
    h_e_secondary.target_value = Decimal("2.0")
    h_e_secondary.is_active = True
    definitions.append(h_e_secondary)

    e_d_primary = MagicMock(spec=KPIDefinition)
    e_d_primary.id = uuid.uuid4()
    e_d_primary.code = "E_D_PRIMARY"
    e_d_primary.name_en = "Students per Class (Primary)"
    e_d_primary.name_fr = "E/D Primaire"
    e_d_primary.category = KPICategory.EDUCATIONAL
    e_d_primary.unit = "students"
    e_d_primary.target_value = Decimal("22.5")
    e_d_primary.is_active = True
    definitions.append(e_d_primary)

    e_d_secondary = MagicMock(spec=KPIDefinition)
    e_d_secondary.id = uuid.uuid4()
    e_d_secondary.code = "E_D_SECONDARY"
    e_d_secondary.name_en = "Students per Class (Secondary)"
    e_d_secondary.name_fr = "E/D Secondaire"
    e_d_secondary.category = KPICategory.EDUCATIONAL
    e_d_secondary.unit = "students"
    e_d_secondary.target_value = Decimal("26")
    e_d_secondary.is_active = True
    definitions.append(e_d_secondary)

    # Financial KPIs
    cost_per_student = MagicMock(spec=KPIDefinition)
    cost_per_student.id = uuid.uuid4()
    cost_per_student.code = "COST_PER_STUDENT"
    cost_per_student.name_en = "Cost per Student"
    cost_per_student.name_fr = "Coût par Élève"
    cost_per_student.category = KPICategory.FINANCIAL
    cost_per_student.unit = "SAR"
    cost_per_student.target_value = None
    cost_per_student.is_active = True
    definitions.append(cost_per_student)

    revenue_per_student = MagicMock(spec=KPIDefinition)
    revenue_per_student.id = uuid.uuid4()
    revenue_per_student.code = "REVENUE_PER_STUDENT"
    revenue_per_student.name_en = "Revenue per Student"
    revenue_per_student.name_fr = "Revenu par Élève"
    revenue_per_student.category = KPICategory.FINANCIAL
    revenue_per_student.unit = "SAR"
    revenue_per_student.target_value = None
    revenue_per_student.is_active = True
    definitions.append(revenue_per_student)

    staff_cost_pct = MagicMock(spec=KPIDefinition)
    staff_cost_pct.id = uuid.uuid4()
    staff_cost_pct.code = "STAFF_COST_PCT"
    staff_cost_pct.name_en = "Staff Cost Percentage"
    staff_cost_pct.name_fr = "% Charges de Personnel"
    staff_cost_pct.category = KPICategory.FINANCIAL
    staff_cost_pct.unit = "%"
    staff_cost_pct.target_value = Decimal("67.5")
    staff_cost_pct.is_active = True
    definitions.append(staff_cost_pct)

    operating_margin = MagicMock(spec=KPIDefinition)
    operating_margin.id = uuid.uuid4()
    operating_margin.code = "OPERATING_MARGIN"
    operating_margin.name_en = "Operating Margin"
    operating_margin.name_fr = "Marge Opérationnelle"
    operating_margin.category = KPICategory.FINANCIAL
    operating_margin.unit = "%"
    operating_margin.target_value = Decimal("7.5")
    operating_margin.is_active = True
    definitions.append(operating_margin)

    capacity_util = MagicMock(spec=KPIDefinition)
    capacity_util.id = uuid.uuid4()
    capacity_util.code = "CAPACITY_UTILIZATION"
    capacity_util.name_en = "Capacity Utilization"
    capacity_util.name_fr = "Utilisation de Capacité"
    capacity_util.category = KPICategory.OPERATIONAL
    capacity_util.unit = "%"
    capacity_util.target_value = Decimal("90")
    capacity_util.is_active = True
    definitions.append(capacity_util)

    return definitions


@pytest.fixture
def mock_kpi_calculation_data():
    """Create mock data for KPI calculations."""
    return {
        "total_students": 1500,
        "primary_students": 600,
        "secondary_students": 900,
        "total_classes": 60,
        "primary_classes": 24,
        "secondary_classes": 36,
        "total_teaching_hours": Decimal("2400"),
        "primary_teaching_hours": Decimal("720"),
        "secondary_teaching_hours": Decimal("1680"),
        "total_teacher_fte": Decimal("100"),
        "primary_teacher_fte": Decimal("30"),
        "secondary_teacher_fte": Decimal("70"),
        "total_revenue_sar": Decimal("75000000"),
        "total_costs_sar": Decimal("70000000"),
        "personnel_costs_sar": Decimal("50000000"),
        "max_capacity": 1875,
    }


# ==============================================================================
# Test: KPI Definition Retrieval
# ==============================================================================


class TestKPIDefinitionRetrieval:
    """Tests for KPI definition retrieval."""

    @pytest.mark.asyncio
    async def test_get_kpi_definition_success(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_kpi_definitions,
    ):
        """Test successful retrieval of KPI definition by code."""
        definition = mock_kpi_definitions[0]  # H_E_PRIMARY

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = definition
        mock_session.execute.return_value = mock_result

        result = await kpi_service.get_kpi_definition("H_E_PRIMARY")

        assert result.code == "H_E_PRIMARY"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_kpi_definition_not_found(
        self,
        kpi_service: KPIService,
        mock_session,
    ):
        """Test NotFoundError when KPI definition doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(NotFoundError):
            await kpi_service.get_kpi_definition("NONEXISTENT_KPI")

    @pytest.mark.asyncio
    async def test_get_all_kpi_definitions(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_kpi_definitions,
    ):
        """Test retrieval of all KPI definitions."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_kpi_definitions
        mock_session.execute.return_value = mock_result

        result = await kpi_service.get_all_kpi_definitions()

        assert len(result) == len(mock_kpi_definitions)

    @pytest.mark.asyncio
    async def test_get_all_kpi_definitions_by_category(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_kpi_definitions,
    ):
        """Test retrieval of KPI definitions filtered by category."""
        educational_defs = [d for d in mock_kpi_definitions if d.category == KPICategory.EDUCATIONAL]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = educational_defs
        mock_session.execute.return_value = mock_result

        result = await kpi_service.get_all_kpi_definitions(
            category=KPICategory.EDUCATIONAL
        )

        assert all(d.category == KPICategory.EDUCATIONAL for d in result)


# ==============================================================================
# Test: KPI Calculation
# ==============================================================================


class TestKPICalculation:
    """Tests for KPI calculation logic."""

    @pytest.mark.asyncio
    async def test_calculate_kpis_success(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """Test successful calculation of all KPIs."""
        # Mock budget version lookup
        version_result = MagicMock()
        version_result.scalar_one_or_none.return_value = mock_budget_version
        mock_session.execute.return_value = version_result

        with patch.object(
            kpi_service,
            "_get_kpi_calculation_data",
            return_value=mock_kpi_calculation_data,
        ):
            with patch.object(
                kpi_service,
                "get_all_kpi_definitions",
                return_value=mock_kpi_definitions,
            ):
                result = await kpi_service.calculate_kpis(
                    budget_version_id=mock_budget_version.id
                )

                assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_calculate_h_e_primary(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test H/E Primary calculation.

        Formula: primary_teaching_hours / primary_students
        Example: 720 / 600 = 1.2 hours per student
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # 720 / 600 = 1.2
        assert result["calculated_value"] == Decimal("1.2")
        assert "primary_teaching_hours" in result["calculation_inputs"]
        assert "primary_students" in result["calculation_inputs"]

    @pytest.mark.asyncio
    async def test_calculate_h_e_secondary(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test H/E Secondary calculation.

        Formula: secondary_teaching_hours / secondary_students
        Example: 1680 / 900 = 1.867 hours per student
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "H_E_SECONDARY")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # 1680 / 900 = 1.8666...
        assert abs(result["calculated_value"] - Decimal("1.867")) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_calculate_e_d_primary(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test E/D Primary (students per class) calculation.

        Formula: primary_students / primary_classes
        Example: 600 / 24 = 25 students per class
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "E_D_PRIMARY")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # 600 / 24 = 25
        assert result["calculated_value"] == Decimal("25")

    @pytest.mark.asyncio
    async def test_calculate_e_d_secondary(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test E/D Secondary (students per class) calculation.

        Formula: secondary_students / secondary_classes
        Example: 900 / 36 = 25 students per class
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "E_D_SECONDARY")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # 900 / 36 = 25
        assert result["calculated_value"] == Decimal("25")

    @pytest.mark.asyncio
    async def test_calculate_cost_per_student(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test cost per student calculation.

        Formula: total_costs_sar / total_students
        Example: 70,000,000 / 1500 = 46,666.67 SAR per student
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "COST_PER_STUDENT")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # 70,000,000 / 1500 = 46,666.67
        expected = Decimal("70000000") / Decimal("1500")
        assert abs(result["calculated_value"] - expected) < Decimal("1")

    @pytest.mark.asyncio
    async def test_calculate_revenue_per_student(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test revenue per student calculation.

        Formula: total_revenue_sar / total_students
        Example: 75,000,000 / 1500 = 50,000 SAR per student
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "REVENUE_PER_STUDENT")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # 75,000,000 / 1500 = 50,000
        assert result["calculated_value"] == Decimal("50000")

    @pytest.mark.asyncio
    async def test_calculate_staff_cost_percentage(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test staff cost percentage calculation.

        Formula: (personnel_costs_sar / total_revenue_sar) × 100
        Example: (50,000,000 / 75,000,000) × 100 = 66.67%
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "STAFF_COST_PCT")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # 50,000,000 / 75,000,000 × 100 = 66.67%
        expected = Decimal("50000000") / Decimal("75000000") * Decimal("100")
        assert abs(result["calculated_value"] - expected) < Decimal("0.1")

    @pytest.mark.asyncio
    async def test_calculate_operating_margin(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test operating margin calculation.

        Formula: ((total_revenue - total_costs) / total_revenue) × 100
        Example: ((75M - 70M) / 75M) × 100 = 6.67%
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "OPERATING_MARGIN")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # (75M - 70M) / 75M × 100 = 6.67%
        margin = Decimal("75000000") - Decimal("70000000")
        expected = (margin / Decimal("75000000")) * Decimal("100")
        assert abs(result["calculated_value"] - expected) < Decimal("0.1")

    @pytest.mark.asyncio
    async def test_calculate_capacity_utilization(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """
        Test capacity utilization calculation.

        Formula: (total_students / max_capacity) × 100
        Example: (1500 / 1875) × 100 = 80%
        """
        definition = next(d for d in mock_kpi_definitions if d.code == "CAPACITY_UTILIZATION")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # 1500 / 1875 × 100 = 80%
        expected = Decimal("1500") / Decimal("1875") * Decimal("100")
        assert abs(result["calculated_value"] - expected) < Decimal("0.1")

    @pytest.mark.asyncio
    async def test_calculate_with_zero_students(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
    ):
        """Test calculation handles zero students gracefully."""
        zero_data = {
            "total_students": 0,
            "primary_students": 0,
            "secondary_students": 0,
            "total_classes": 0,
            "primary_classes": 0,
            "secondary_classes": 0,
            "total_teaching_hours": Decimal("0"),
            "primary_teaching_hours": Decimal("0"),
            "secondary_teaching_hours": Decimal("0"),
            "total_teacher_fte": Decimal("0"),
            "total_revenue_sar": Decimal("0"),
            "total_costs_sar": Decimal("0"),
            "personnel_costs_sar": Decimal("0"),
            "max_capacity": 1875,
        }

        definition = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        result = await kpi_service._calculate_single_kpi(definition, zero_data)

        # Should return 0 instead of raising division error
        assert result["calculated_value"] == Decimal("0")

    @pytest.mark.asyncio
    async def test_calculate_specific_kpis(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """Test calculation of specific KPIs by code list."""
        version_result = MagicMock()
        version_result.scalar_one_or_none.return_value = mock_budget_version
        mock_session.execute.return_value = version_result

        h_e_def = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        with patch.object(
            kpi_service,
            "_get_kpi_calculation_data",
            return_value=mock_kpi_calculation_data,
        ):
            with patch.object(
                kpi_service,
                "get_kpi_definition",
                return_value=h_e_def,
            ):
                result = await kpi_service.calculate_kpis(
                    budget_version_id=mock_budget_version.id,
                    kpi_codes=["H_E_PRIMARY"],
                )

                assert "H_E_PRIMARY" in result

    @pytest.mark.asyncio
    async def test_calculate_budget_version_not_found(
        self,
        kpi_service: KPIService,
        mock_session,
    ):
        """Test error when budget version doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(NotFoundError):
            await kpi_service.calculate_kpis(budget_version_id=uuid.uuid4())


# ==============================================================================
# Test: KPI Calculation Data (DHG splits)
# ==============================================================================


class TestKpiCalculationDataWithDhg:
    """Tests for DHG-driven KPI data aggregation."""

    @pytest.mark.asyncio
    async def test_teacher_fte_split_by_level(
        self,
        db_session: AsyncSession,
        test_budget_version: BudgetVersion,
        subjects: dict[str, Subject],
        academic_levels: dict[str, AcademicLevel],
        test_user_id: uuid.UUID,
        test_dhg_data: dict,
    ):
        """Verify primary/secondary teacher FTE are split from DHG hours."""
        # Add primary DHG hours to drive primary FTE (secondary covered by test_dhg_data)
        db_session.add(
            DHGSubjectHours(
                id=uuid.uuid4(),
                budget_version_id=test_budget_version.id,
                subject_id=subjects["MATH"].id,
                level_id=academic_levels["PS"].id,
                number_of_classes=2,
                hours_per_class_per_week=Decimal("6.0"),
                total_hours_per_week=Decimal("12.0"),
                is_split=False,
                created_by_id=test_user_id,
            )
        )
        await db_session.flush()

        service = KPIService(db_session)
        kpi_data = await service._get_kpi_calculation_data(test_budget_version.id)

        assert kpi_data["primary_teacher_fte"] == Decimal("0.50")
        # Secondary hours from test_dhg_data: 13.5 + 15.0 = 28.5 → 28.5/18 = 1.58
        assert kpi_data["secondary_teacher_fte"] == Decimal("1.58")


# ==============================================================================
# Test: KPI Value Storage
# ==============================================================================


class TestKPIValueStorage:
    """Tests for KPI value storage and retrieval."""

    @pytest.mark.asyncio
    async def test_save_kpi_values_create_new(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test saving new KPI values."""
        kpi_results = {
            "H_E_PRIMARY": {
                "calculated_value": Decimal("1.2"),
                "variance_from_target": Decimal("0.1"),
                "variance_percent": Decimal("9.09"),
                "calculation_inputs": {"hours": "720", "students": "600"},
            }
        }

        h_e_def = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        # Mock no existing value
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch.object(
            kpi_service,
            "get_kpi_definition",
            return_value=h_e_def,
        ):
            await kpi_service.save_kpi_values(
                budget_version_id=mock_budget_version.id,
                kpi_results=kpi_results,
            )

            # Should have added new KPI value
            mock_session.add.assert_called()
            mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_save_kpi_values_update_existing(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test updating existing KPI values."""
        kpi_results = {
            "H_E_PRIMARY": {
                "calculated_value": Decimal("1.3"),
                "variance_from_target": Decimal("0.2"),
                "variance_percent": Decimal("18.18"),
                "calculation_inputs": {"hours": "780", "students": "600"},
            }
        }

        h_e_def = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        # Mock existing value
        existing_value = MagicMock(spec=KPIValue)
        existing_value.id = uuid.uuid4()
        existing_value.calculated_value = Decimal("1.2")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_value
        mock_session.execute.return_value = mock_result

        with patch.object(
            kpi_service,
            "get_kpi_definition",
            return_value=h_e_def,
        ):
            await kpi_service.save_kpi_values(
                budget_version_id=mock_budget_version.id,
                kpi_results=kpi_results,
            )

            # Should have updated existing value
            assert existing_value.calculated_value == Decimal("1.3")

    @pytest.mark.asyncio
    async def test_get_kpi_by_type(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test retrieval of specific KPI value."""
        h_e_def = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        kpi_value = MagicMock(spec=KPIValue)
        kpi_value.calculated_value = Decimal("1.2")
        kpi_value.kpi_definition = h_e_def

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = kpi_value
        mock_session.execute.return_value = mock_result

        with patch.object(
            kpi_service,
            "get_kpi_definition",
            return_value=h_e_def,
        ):
            result = await kpi_service.get_kpi_by_type(
                budget_version_id=mock_budget_version.id,
                kpi_code="H_E_PRIMARY",
            )

            assert result.calculated_value == Decimal("1.2")

    @pytest.mark.asyncio
    async def test_get_all_kpis(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test retrieval of all KPIs for a budget version."""
        kpi_values = []
        for i, definition in enumerate(mock_kpi_definitions[:3]):
            value = MagicMock(spec=KPIValue)
            value.calculated_value = Decimal(str(i + 1))
            value.kpi_definition = definition
            kpi_values.append(value)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = kpi_values
        mock_session.execute.return_value = mock_result

        result = await kpi_service.get_all_kpis(
            budget_version_id=mock_budget_version.id
        )

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_all_kpis_by_category(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test retrieval of KPIs filtered by category."""
        educational_defs = [d for d in mock_kpi_definitions if d.category == KPICategory.EDUCATIONAL]
        kpi_values = []
        for definition in educational_defs:
            value = MagicMock(spec=KPIValue)
            value.kpi_definition = definition
            kpi_values.append(value)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = kpi_values
        mock_session.execute.return_value = mock_result

        result = await kpi_service.get_all_kpis(
            budget_version_id=mock_budget_version.id,
            category=KPICategory.EDUCATIONAL,
        )

        assert all(v.kpi_definition.category == KPICategory.EDUCATIONAL for v in result)


# ==============================================================================
# Test: KPI Trends
# ==============================================================================


class TestKPITrends:
    """Tests for KPI trend analysis."""

    @pytest.mark.asyncio
    async def test_get_kpi_trends(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_kpi_definitions,
    ):
        """Test retrieval of KPI trends across versions."""
        h_e_def = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        # Create multiple budget versions
        versions = []
        kpi_values = []
        for i in range(3):
            version = MagicMock(spec=BudgetVersion)
            version.id = uuid.uuid4()
            version.name = f"Budget 202{i+3}"
            version.fiscal_year = 2023 + i
            version.status = MagicMock()
            version.status.value = "APPROVED"
            versions.append(version)

            kpi_value = MagicMock(spec=KPIValue)
            kpi_value.calculated_value = Decimal(str(1.0 + i * 0.1))
            kpi_value.variance_from_target = Decimal(str(-0.1 + i * 0.1))
            kpi_value.calculated_at = datetime.utcnow()
            kpi_value.kpi_definition = h_e_def
            kpi_values.append(kpi_value)

        # Track execute calls to return alternating version/kpi results
        call_count = 0

        def mock_execute_side_effect(query):
            nonlocal call_count
            result = MagicMock()
            # For each version, we have 2 calls: first for version, then for kpi
            version_index = call_count // 2
            is_version_query = call_count % 2 == 0

            if version_index < len(versions):
                if is_version_query:
                    result.scalar_one_or_none.return_value = versions[version_index]
                else:
                    result.scalar_one_or_none.return_value = kpi_values[version_index]
            else:
                result.scalar_one_or_none.return_value = None

            call_count += 1
            return result

        mock_session.execute.side_effect = mock_execute_side_effect

        with patch.object(
            kpi_service,
            "get_kpi_definition",
            return_value=h_e_def,
        ):
            version_ids = [v.id for v in versions]
            result = await kpi_service.get_kpi_trends(
                version_ids=version_ids,
                kpi_code="H_E_PRIMARY",
            )

            assert len(result) == 3
            assert all("version_id" in r for r in result)
            assert all("calculated_value" in r for r in result)


# ==============================================================================
# Test: AEFE Benchmark Comparison
# ==============================================================================


class TestAEFEBenchmarkComparison:
    """Tests for AEFE benchmark comparison."""

    @pytest.mark.asyncio
    async def test_get_benchmark_comparison_within_range(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test benchmark comparison when value is within range."""
        h_e_def = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        # Value within range: 1.1 (target) with range [1.0, 1.2]
        kpi_value = MagicMock(spec=KPIValue)
        kpi_value.calculated_value = Decimal("1.1")
        kpi_value.kpi_definition = h_e_def

        with patch.object(
            kpi_service,
            "get_all_kpis",
            return_value=[kpi_value],
        ):
            result = await kpi_service.get_benchmark_comparison(
                budget_version_id=mock_budget_version.id
            )

            assert "H_E_PRIMARY" in result
            assert result["H_E_PRIMARY"]["status"] == "within_range"

    @pytest.mark.asyncio
    async def test_get_benchmark_comparison_below_range(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test benchmark comparison when value is below range."""
        h_e_def = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        # Value below range: 0.9 (min is 1.0)
        kpi_value = MagicMock(spec=KPIValue)
        kpi_value.calculated_value = Decimal("0.9")
        kpi_value.kpi_definition = h_e_def

        with patch.object(
            kpi_service,
            "get_all_kpis",
            return_value=[kpi_value],
        ):
            result = await kpi_service.get_benchmark_comparison(
                budget_version_id=mock_budget_version.id
            )

            assert "H_E_PRIMARY" in result
            assert result["H_E_PRIMARY"]["status"] == "below_range"

    @pytest.mark.asyncio
    async def test_get_benchmark_comparison_above_range(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test benchmark comparison when value is above range."""
        h_e_def = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        # Value above range: 1.3 (max is 1.2)
        kpi_value = MagicMock(spec=KPIValue)
        kpi_value.calculated_value = Decimal("1.3")
        kpi_value.kpi_definition = h_e_def

        with patch.object(
            kpi_service,
            "get_all_kpis",
            return_value=[kpi_value],
        ):
            result = await kpi_service.get_benchmark_comparison(
                budget_version_id=mock_budget_version.id
            )

            assert "H_E_PRIMARY" in result
            assert result["H_E_PRIMARY"]["status"] == "above_range"

    @pytest.mark.asyncio
    async def test_get_benchmark_comparison_no_benchmark(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test benchmark comparison for KPI without benchmark."""
        cost_def = next(d for d in mock_kpi_definitions if d.code == "COST_PER_STUDENT")

        kpi_value = MagicMock(spec=KPIValue)
        kpi_value.calculated_value = Decimal("46666.67")
        kpi_value.kpi_definition = cost_def

        with patch.object(
            kpi_service,
            "get_all_kpis",
            return_value=[kpi_value],
        ):
            result = await kpi_service.get_benchmark_comparison(
                budget_version_id=mock_budget_version.id
            )

            assert "COST_PER_STUDENT" in result
            assert result["COST_PER_STUDENT"]["status"] == "no_benchmark"


# ==============================================================================
# Test: Variance Calculation
# ==============================================================================


class TestVarianceCalculation:
    """Tests for variance from target calculation."""

    @pytest.mark.asyncio
    async def test_variance_positive(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """Test positive variance (above target)."""
        definition = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")
        # Target is 1.1, calculated will be 1.2

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # Variance should be positive (1.2 - 1.1 = 0.1)
        assert result["variance_from_target"] > 0

    @pytest.mark.asyncio
    async def test_variance_negative(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
    ):
        """Test negative variance (below target)."""
        low_data = {
            "total_students": 1500,
            "primary_students": 600,
            "secondary_students": 900,
            "total_classes": 60,
            "primary_classes": 24,
            "secondary_classes": 36,
            "total_teaching_hours": Decimal("1200"),  # Lower hours
            "primary_teaching_hours": Decimal("480"),  # 480/600 = 0.8
            "secondary_teaching_hours": Decimal("720"),
            "total_teacher_fte": Decimal("100"),
            "total_revenue_sar": Decimal("75000000"),
            "total_costs_sar": Decimal("70000000"),
            "personnel_costs_sar": Decimal("50000000"),
            "max_capacity": 1875,
        }

        definition = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")
        # Target is 1.1, calculated will be 0.8

        result = await kpi_service._calculate_single_kpi(definition, low_data)

        # Variance should be negative (0.8 - 1.1 = -0.3)
        assert result["variance_from_target"] < 0

    @pytest.mark.asyncio
    async def test_variance_percent_calculation(
        self,
        kpi_service: KPIService,
        mock_kpi_definitions,
        mock_kpi_calculation_data,
    ):
        """Test variance percentage calculation."""
        definition = next(d for d in mock_kpi_definitions if d.code == "H_E_PRIMARY")

        result = await kpi_service._calculate_single_kpi(
            definition, mock_kpi_calculation_data
        )

        # Variance percent = (variance / target) × 100
        if result["variance_from_target"] and definition.target_value:
            expected_pct = (
                result["variance_from_target"] / definition.target_value * 100
            )
            assert abs(result["variance_percent"] - expected_pct) < Decimal("0.1")


# ==============================================================================
# Test: Error Handling
# ==============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_calculation_error_handling(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
    ):
        """Test error handling during KPI calculation."""
        version_result = MagicMock()
        version_result.scalar_one_or_none.return_value = mock_budget_version
        mock_session.execute.return_value = version_result

        with patch.object(
            kpi_service,
            "_get_kpi_calculation_data",
            side_effect=Exception("Database error"),
        ):
            with pytest.raises(Exception):
                await kpi_service.calculate_kpis(
                    budget_version_id=mock_budget_version.id
                )

    @pytest.mark.asyncio
    async def test_single_kpi_calculation_error(
        self,
        kpi_service: KPIService,
        mock_session,
        mock_budget_version,
        mock_kpi_definitions,
    ):
        """Test error handling for single KPI calculation failure."""
        version_result = MagicMock()
        version_result.scalar_one_or_none.return_value = mock_budget_version
        mock_session.execute.return_value = version_result

        with patch.object(
            kpi_service,
            "_get_kpi_calculation_data",
            return_value={},  # Empty data will cause calculation issues
        ):
            with patch.object(
                kpi_service,
                "get_all_kpi_definitions",
                return_value=mock_kpi_definitions,
            ):
                with patch.object(
                    kpi_service,
                    "_calculate_single_kpi",
                    side_effect=Exception("Calculation failed"),
                ):
                    with pytest.raises(ValidationError) as exc_info:
                        await kpi_service.calculate_kpis(
                            budget_version_id=mock_budget_version.id
                        )

                    assert "Failed to calculate KPI" in str(exc_info.value)
