"""
Tests for Calculations API endpoints.

Covers:
- Enrollment projection calculations
- KPI calculations
- DHG hours calculations
- Revenue calculations
- Input validation
- Error handling

Target Coverage: 90%+
"""

import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from app.schemas.enrollment import EnrollmentProjectionResponse
from app.schemas.insights import KPIEngineResponse as KPICalculationResponse
from app.schemas.revenue import RevenueCalculationResponse
from app.schemas.workforce import DHGCalculationResponse

# Note: `client` fixture is defined in conftest.py with proper engine dependency


class TestEnrollmentCalculation:
    """Test enrollment projection calculation endpoint."""

    @patch("app.api.v1.calculations.calculate_enrollment_projection")
    def test_calculate_enrollment_success(
        self, mock_calculate, client
    ):
        """Test successful enrollment projection calculation."""
        mock_result = EnrollmentProjectionResponse(
            level_id=uuid.uuid4(),
            level_code="6EME",
            nationality="French",
            base_enrollment=120,
            scenario="base",
            projections=[
                {
                    "year": 1,
                    "projected_enrollment": 120,
                    "growth_rate_applied": Decimal("0.00"),
                    "cumulative_growth": Decimal("0.00"),
                },
                {
                    "year": 2,
                    "projected_enrollment": 126,
                    "growth_rate_applied": Decimal("0.05"),
                    "cumulative_growth": Decimal("0.05"),
                },
                {
                    "year": 3,
                    "projected_enrollment": 132,
                    "growth_rate_applied": Decimal("0.05"),
                    "cumulative_growth": Decimal("0.099"),
                },
            ],
            total_growth_students=12,
            total_growth_percent=Decimal("0.10"),
            capacity_exceeded=False,
        )
        mock_calculate.return_value = mock_result

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 3,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["level_code"] == "6EME"
        assert len(data["projections"]) == 3
        assert data["projections"][0]["projected_enrollment"] == 120

    @patch("app.api.v1.calculations.calculate_enrollment_projection")
    def test_calculate_enrollment_validation_error(
        self, mock_calculate, client
    ):
        """Test enrollment calculation with invalid input."""
        mock_calculate.side_effect = ValueError("Invalid enrollment value")

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": -10,  # Invalid
            "growth_scenario": "base",
            "years_to_project": 3,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "greater_than_equal"

    @patch("app.api.v1.calculations.calculate_enrollment_projection")
    def test_calculate_enrollment_unexpected_error(
        self, mock_calculate, client
    ):
        """Test enrollment calculation with unexpected error."""
        mock_calculate.side_effect = Exception("Unexpected error")

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 3,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 400


class TestKPICalculation:
    """Test KPI calculation endpoint."""

    @patch("app.api.v1.calculations.validate_kpi_input")
    @patch("app.api.v1.calculations.calculate_all_kpis")
    def test_calculate_kpis_success(
        self, mock_calculate, mock_validate, client
    ):
        """Test successful KPI calculation."""
        mock_result = KPICalculationResponse(
            student_teacher_ratio={
                "kpi_type": "student_teacher_ratio",
                "value": Decimal("12.0"),
                "target_value": Decimal("12.0"),
                "unit": "ratio",
                "variance_from_target": Decimal("0.0"),
                "performance_status": "on_target",
            },
            revenue_per_student={
                "kpi_type": "revenue_per_student",
                "value": Decimal("45000.00"),
                "target_value": Decimal("45000.00"),
                "unit": "sar",
                "variance_from_target": Decimal("0.00"),
                "performance_status": "on_target",
            },
        )
        mock_calculate.return_value = mock_result

        request_data = {
            "total_students": 1850,
            "secondary_students": 650,
            "max_capacity": 1875,
            "total_teacher_fte": 154.17,
            "dhg_hours_total": 877.5,
            "total_revenue": 83272500,
            "total_costs": 74945250,
            "personnel_costs": 52461675,
        }

        response = client.post("/api/v1/calculations/kpi/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "student_teacher_ratio" in data
        assert float(data["student_teacher_ratio"]["value"]) == pytest.approx(12.0, abs=0.01)

    @patch("app.api.v1.calculations.validate_kpi_input")
    def test_calculate_kpis_validation_error(
        self, mock_validate, client
    ):
        """Test KPI calculation with invalid input."""
        mock_validate.side_effect = ValueError("Total students must be positive")

        request_data = {
            "total_students": -100,  # Invalid
            "secondary_students": 650,
            "max_capacity": 1875,
            "total_teacher_fte": 154.17,
            "dhg_hours_total": 877.5,
            "total_revenue": 83272500,
            "total_costs": 74945250,
            "personnel_costs": 52461675,
        }

        response = client.post("/api/v1/calculations/kpi/calculate", json=request_data)

        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "greater_than_equal"

    @patch("app.api.v1.calculations.validate_kpi_input")
    @patch("app.api.v1.calculations.calculate_all_kpis")
    def test_calculate_kpis_calculation_error(
        self, mock_calculate, mock_validate, client
    ):
        """Test KPI calculation with calculation error."""
        mock_validate.return_value = None
        mock_calculate.side_effect = Exception("Division by zero")

        request_data = {
            "total_students": 1850,
            "secondary_students": 650,
            "max_capacity": 1875,
            "total_teacher_fte": 154.17,
            "dhg_hours_total": 877.5,
            "total_revenue": 83272500,
            "total_costs": 74945250,
            "personnel_costs": 52461675,
        }

        response = client.post("/api/v1/calculations/kpi/calculate", json=request_data)

        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()


class TestDHGCalculation:
    """Test DHG hours calculation endpoint."""

    @patch("app.api.v1.calculations.validate_dhg_input")
    @patch("app.api.v1.calculations.calculate_dhg_hours")
    def test_calculate_dhg_success(
        self, mock_calculate, mock_validate, client
    ):
        """Test successful DHG hours calculation."""
        mock_result = DHGCalculationResponse(
            level_id=uuid.uuid4(),
            level_code="6EME",
            education_level="secondary",
            number_of_classes=6,
            total_hours=Decimal("90.0"),
            subject_breakdown={
                "MATH": Decimal("27.0"),
                "FRENCH": Decimal("30.0"),
            },
        )
        mock_calculate.return_value = mock_result

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "education_level": "secondary",
            "number_of_classes": 6,
            "subject_hours_list": [
                {
                    "subject_id": str(uuid.uuid4()),
                    "subject_code": "MATH",
                    "subject_name": "Mathématiques",
                    "level_id": str(uuid.uuid4()),
                    "level_code": "6EME",
                    "hours_per_week": 4.5,
                },
                {
                    "subject_id": str(uuid.uuid4()),
                    "subject_code": "FRENCH",
                    "subject_name": "Français",
                    "level_id": str(uuid.uuid4()),
                    "level_code": "6EME",
                    "hours_per_week": 5.0,
                },
            ],
        }

        response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["level_code"] == "6EME"
        assert float(data["total_hours"]) == pytest.approx(90.0, abs=0.1)
        assert set(data["subject_breakdown"].keys()) == {"MATH", "FRENCH"}

    @patch("app.api.v1.calculations.validate_dhg_input")
    def test_calculate_dhg_validation_error(
        self, mock_validate, client
    ):
        """Test DHG calculation with invalid input."""
        mock_validate.side_effect = ValueError("Number of classes must be positive")

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "education_level": "secondary",
            "number_of_classes": -1,  # Invalid
            "subject_hours_list": [],
        }

        response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "greater_than_equal"

    @patch("app.api.v1.calculations.validate_dhg_input")
    @patch("app.api.v1.calculations.calculate_dhg_hours")
    def test_calculate_dhg_calculation_error(
        self, mock_calculate, mock_validate, client
    ):
        """Test DHG calculation with calculation error."""
        mock_validate.return_value = None
        mock_calculate.side_effect = Exception("Calculation error")

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "education_level": "secondary",
            "number_of_classes": 6,
            "subject_hours_list": [
                {
                    "subject_id": str(uuid.uuid4()),
                    "subject_code": "MATH",
                    "subject_name": "Mathématiques",
                    "level_id": str(uuid.uuid4()),
                    "level_code": "6EME",
                    "hours_per_week": 4.5,
                },
            ],
        }

        response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()


class TestRevenueCalculation:
    """Test revenue calculation endpoint."""

    @patch("app.api.v1.calculations.validate_tuition_input")
    @patch("app.api.v1.calculations.calculate_total_student_revenue")
    def test_calculate_revenue_success(
        self, mock_calculate, mock_validate, client
    ):
        """Test successful revenue calculation."""
        mock_result = RevenueCalculationResponse(
            student_id=uuid.uuid4(),
            level_code="6EME",
            fee_category="french_ttc",
            tuition_revenue={
                "student_id": None,
                "level_code": "6EME",
                "fee_category": "french_ttc",
                "base_tuition": Decimal("40000.00"),
                "base_dai": Decimal("3000.00"),
                "base_registration": Decimal("2000.00"),
                "sibling_discount_amount": Decimal("0.00"),
                "sibling_discount_rate": Decimal("0.00"),
                "net_tuition": Decimal("40000.00"),
                "net_dai": Decimal("3000.00"),
                "net_registration": Decimal("2000.00"),
                "total_revenue": Decimal("45000.00"),
            },
            trimester_distribution={
                "total_revenue": Decimal("45000.00"),
                "trimester_1": Decimal("18000.00"),
                "trimester_2": Decimal("13500.00"),
                "trimester_3": Decimal("13500.00"),
            },
            total_annual_revenue=Decimal("45000.00"),
            sibling_discount_applied=False,
        )
        mock_calculate.return_value = mock_result

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": 40000,
            "dai_fee": 3000,
            "registration_fee": 2000,
            "sibling_order": 1,
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["fee_category"] == "french_ttc"
        assert float(data["total_annual_revenue"]) == pytest.approx(45000.0, abs=0.01)
        assert "trimester_distribution" in data

    @patch("app.api.v1.calculations.validate_tuition_input")
    @patch("app.api.v1.calculations.calculate_total_student_revenue")
    def test_calculate_revenue_with_sibling_discount(
        self, mock_calculate, mock_validate, client
    ):
        """Test revenue calculation with sibling discount."""
        mock_result = RevenueCalculationResponse(
            student_id=uuid.uuid4(),
            level_code="6EME",
            fee_category="french_ttc",
            tuition_revenue={
                "student_id": None,
                "level_code": "6EME",
                "fee_category": "french_ttc",
                "base_tuition": Decimal("40000.00"),
                "base_dai": Decimal("3000.00"),
                "base_registration": Decimal("2000.00"),
                "sibling_discount_amount": Decimal("10000.00"),
                "sibling_discount_rate": Decimal("0.25"),
                "net_tuition": Decimal("30000.00"),
                "net_dai": Decimal("3000.00"),
                "net_registration": Decimal("2000.00"),
                "total_revenue": Decimal("35000.00"),
            },
            trimester_distribution={
                "total_revenue": Decimal("35000.00"),
                "trimester_1": Decimal("13500.00"),
                "trimester_2": Decimal("10500.00"),
                "trimester_3": Decimal("10500.00"),
            },
            total_annual_revenue=Decimal("35000.00"),
            sibling_discount_applied=True,
        )
        mock_calculate.return_value = mock_result

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": 40000,
            "dai_fee": 3000,
            "registration_fee": 2000,
            "sibling_order": 3,  # 3rd child gets discount
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["sibling_discount_applied"] is True
        assert float(data["tuition_revenue"]["net_tuition"]) == pytest.approx(30000.0, abs=0.01)

    @patch("app.api.v1.calculations.validate_tuition_input")
    def test_calculate_revenue_validation_error(
        self, mock_validate, client
    ):
        """Test revenue calculation with invalid input."""
        mock_validate.side_effect = ValueError("Tuition fee must be positive")

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": -1000,  # Invalid
            "dai_fee": 3000,
            "registration_fee": 2000,
            "sibling_order": 1,
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "greater_than_equal"

    @patch("app.api.v1.calculations.validate_tuition_input")
    @patch("app.api.v1.calculations.calculate_total_student_revenue")
    def test_calculate_revenue_calculation_error(
        self, mock_calculate, mock_validate, client
    ):
        """Test revenue calculation with calculation error."""
        mock_validate.return_value = None
        mock_calculate.side_effect = Exception("Calculation error")

        request_data = {
            "level_id": str(uuid.uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": 40000,
            "dai_fee": 3000,
            "registration_fee": 2000,
            "sibling_order": 1,
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()


class TestCalculationsHealthCheck:
    """Test calculations health check endpoint."""

    def test_health_check_success(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/calculations/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "enrollment" in data["services"]
        assert "kpi" in data["services"]
        assert "dhg" in data["services"]
        assert "revenue" in data["services"]


class TestCalculationsEdgeCases:
    """Test edge cases and error scenarios."""

    def test_missing_required_fields(self, client):
        """Test calculation endpoints with missing required fields."""
        response = client.post("/api/v1/calculations/enrollment/project", json={})

        assert response.status_code == 422  # Validation error

    def test_invalid_uuid_format(self, client):
        """Test calculation endpoints with invalid UUID format."""
        request_data = {
            "level_id": "invalid-uuid",
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 3,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_empty_subject_hours_list(self, client):
        """Test DHG calculation with empty subject hours list."""
        with patch("app.api.v1.calculations.validate_dhg_input") as mock_validate:
            mock_validate.side_effect = ValueError("Subject hours list cannot be empty")

            request_data = {
                "level_id": str(uuid.uuid4()),
                "level_code": "6EME",
                "education_level": "secondary",
                "number_of_classes": 6,
                "subject_hours_list": [],
            }

            response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

            assert response.status_code == 400

    def test_zero_enrollment(self, client):
        """Test enrollment calculation with zero enrollment."""
        with patch("app.api.v1.calculations.calculate_enrollment_projection") as mock_calculate:
            mock_result = EnrollmentProjectionResponse(
                level_id=uuid.uuid4(),
                level_code="6EME",
                nationality="French",
                base_enrollment=0,
                scenario="base",
                projections=[
                    {
                        "year": 1,
                        "projected_enrollment": 0,
                        "growth_rate_applied": Decimal("0.00"),
                        "cumulative_growth": Decimal("0.00"),
                    }
                ],
                total_growth_students=0,
                total_growth_percent=Decimal("0.00"),
                capacity_exceeded=False,
            )
            mock_calculate.return_value = mock_result

            request_data = {
                "level_id": str(uuid.uuid4()),
                "level_code": "6EME",
                "nationality": "French",
                "current_enrollment": 0,
                "growth_scenario": "base",
                "years_to_project": 1,
            }

            response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["base_enrollment"] == 0
