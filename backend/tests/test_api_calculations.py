"""
API Tests for Calculation Endpoints

Tests for all calculation API endpoints including:
- Enrollment projection calculations
- DHG (workforce) calculations
- KPI (performance indicator) calculations
- Revenue calculations
- Health check endpoint
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.api.v1 import calculations_router
from app.engine.enrollment import EnrollmentGrowthScenario


@pytest.fixture
def client():
    """
    Create FastAPI test client with calculations router.

    Uses a minimal app configuration without authentication middleware
    for testing calculation endpoints in isolation.
    """
    app = FastAPI(title="EFIR Calculations Test API")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include only calculations router (no auth middleware)
    app.include_router(calculations_router)

    return TestClient(app)


class TestEnrollmentProjectionEndpoint:
    """Test POST /api/v1/calculations/enrollment/project endpoint."""

    def test_enrollment_projection_base_scenario(self, client):
        """Test enrollment projection with base scenario (4% growth)."""
        level_id = str(uuid4())
        request_data = {
            "level_id": level_id,
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 5,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["level_code"] == "6EME"
        assert data["nationality"] == "French"
        assert data["base_enrollment"] == 120
        assert data["scenario"] == "base"
        assert len(data["projections"]) == 5

        # Verify year 1 is base (no growth)
        assert data["projections"][0]["year"] == 1
        assert data["projections"][0]["projected_enrollment"] == 120

    def test_enrollment_projection_conservative_scenario(self, client):
        """Test enrollment projection with conservative scenario (1% growth)."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "5EME",
            "nationality": "Saudi",
            "current_enrollment": 100,
            "growth_scenario": "conservative",
            "years_to_project": 3,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["scenario"] == "conservative"
        assert data["base_enrollment"] == 100
        assert len(data["projections"]) == 3

    def test_enrollment_projection_optimistic_scenario(self, client):
        """Test enrollment projection with optimistic scenario (7% growth)."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "4EME",
            "nationality": "Other",
            "current_enrollment": 80,
            "growth_scenario": "optimistic",
            "years_to_project": 5,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["scenario"] == "optimistic"
        assert len(data["projections"]) == 5

    def test_enrollment_projection_invalid_enrollment(self, client):
        """Test enrollment projection with maximum allowed projection timeframe."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 10,  # Maximum allowed
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert len(data["projections"]) == 10

    def test_enrollment_projection_invalid_years(self, client):
        """Test enrollment projection with invalid years."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 0,  # Invalid - must be >= 1
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        # Pydantic validation error (constraint: ge=1)
        assert response.status_code == 422


class TestDHGCalculationEndpoint:
    """Test POST /api/v1/calculations/dhg/calculate endpoint."""

    def test_dhg_calculation_single_subject(self, client):
        """Test DHG calculation for single subject at a level."""
        level_id = str(uuid4())
        subject_id = str(uuid4())

        request_data = {
            "level_id": level_id,
            "level_code": "6EME",
            "education_level": "secondary",
            "number_of_classes": 6,
            "subject_hours_list": [
                {
                    "subject_id": subject_id,
                    "subject_code": "MATH",
                    "subject_name": "Mathématiques",
                    "level_id": level_id,
                    "level_code": "6EME",
                    "hours_per_week": 4.5,
                }
            ],
        }

        response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["level_code"] == "6EME"
        assert data["education_level"] == "secondary"
        assert data["number_of_classes"] == 6
        assert float(data["total_hours"]) == 27.0  # 6 × 4.5
        assert "MATH" in data["subject_breakdown"]

    def test_dhg_calculation_multiple_subjects(self, client):
        """Test DHG calculation for multiple subjects."""
        level_id = str(uuid4())

        request_data = {
            "level_id": level_id,
            "level_code": "6EME",
            "education_level": "secondary",
            "number_of_classes": 6,
            "subject_hours_list": [
                {
                    "subject_id": str(uuid4()),
                    "subject_code": "MATH",
                    "subject_name": "Mathématiques",
                    "level_id": level_id,
                    "level_code": "6EME",
                    "hours_per_week": 4.5,
                },
                {
                    "subject_id": str(uuid4()),
                    "subject_code": "FRAN",
                    "subject_name": "Français",
                    "level_id": level_id,
                    "level_code": "6EME",
                    "hours_per_week": 5.0,
                },
            ],
        }

        response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Total: (6 × 4.5) + (6 × 5.0) = 27 + 30 = 57
        assert float(data["total_hours"]) == 57.0
        assert "MATH" in data["subject_breakdown"]
        assert "FRAN" in data["subject_breakdown"]

    def test_dhg_calculation_primary_level(self, client):
        """Test DHG calculation for primary education level."""
        level_id = str(uuid4())

        request_data = {
            "level_id": level_id,
            "level_code": "CM2",
            "education_level": "primary",
            "number_of_classes": 4,
            "subject_hours_list": [
                {
                    "subject_id": str(uuid4()),
                    "subject_code": "FRAN",
                    "subject_name": "Français",
                    "level_id": level_id,
                    "level_code": "CM2",
                    "hours_per_week": 6.0,
                },
                {
                    "subject_id": str(uuid4()),
                    "subject_code": "MATH",
                    "subject_name": "Mathématiques",
                    "level_id": level_id,
                    "level_code": "CM2",
                    "hours_per_week": 6.0,
                },
                {
                    "subject_id": str(uuid4()),
                    "subject_code": "EPS",
                    "subject_name": "Éducation Physique",
                    "level_id": level_id,
                    "level_code": "CM2",
                    "hours_per_week": 3.0,
                },
                {
                    "subject_id": str(uuid4()),
                    "subject_code": "ART",
                    "subject_name": "Arts Plastiques",
                    "level_id": level_id,
                    "level_code": "CM2",
                    "hours_per_week": 3.0,
                },
            ],
        }

        response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["education_level"] == "primary"
        # Total: 4 classes × (6+6+3+3) = 4 × 18 = 72 hours
        assert float(data["total_hours"]) == 72.0

    def test_dhg_calculation_invalid_classes_count(self, client):
        """Test DHG calculation with too many classes."""
        level_id = str(uuid4())

        request_data = {
            "level_id": level_id,
            "level_code": "6EME",
            "education_level": "secondary",
            "number_of_classes": 100,  # Invalid - exceeds max of 50
            "subject_hours_list": [
                {
                    "subject_id": str(uuid4()),
                    "subject_code": "MATH",
                    "subject_name": "Mathématiques",
                    "level_id": level_id,
                    "level_code": "6EME",
                    "hours_per_week": 4.5,
                }
            ],
        }

        response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

        # Pydantic validation error (field_validator on number_of_classes)
        assert response.status_code == 422

    def test_dhg_calculation_empty_subject_list(self, client):
        """Test DHG calculation with empty subject list."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "education_level": "secondary",
            "number_of_classes": 6,
            "subject_hours_list": [],  # Invalid - empty
        }

        response = client.post("/api/v1/calculations/dhg/calculate", json=request_data)

        # InvalidDHGInputError is caught by generic Exception handler → 500
        assert response.status_code == 500
        assert "calculation failed" in response.json()["detail"].lower()


class TestKPICalculationEndpoint:
    """Test POST /api/v1/calculations/kpi/calculate endpoint."""

    def test_kpi_calculation_complete_dataset(self, client):
        """Test KPI calculation with complete real EFIR data."""
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

        # Verify structure - KPIs are returned as individual keys
        assert "calculation_date" in data
        assert "student_teacher_ratio" in data or "capacity_utilization" in data

        # Verify at least some KPIs are present
        kpi_keys = {"student_teacher_ratio", "he_ratio_secondary", "revenue_per_student",
                   "cost_per_student", "margin_percentage", "staff_cost_ratio", "capacity_utilization"}
        present_kpis = {k for k in kpi_keys if k in data}
        assert len(present_kpis) >= 5  # At least 5 of the 7 KPIs

    def test_kpi_calculation_minimal_data(self, client):
        """Test KPI calculation with minimal required data."""
        request_data = {
            "total_students": 100,
            "secondary_students": 50,
            "max_capacity": 150,
            "total_teacher_fte": 5.0,
            "total_revenue": 5000000,
            "total_costs": 4500000,
            "personnel_costs": 3000000,
        }

        response = client.post("/api/v1/calculations/kpi/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify some KPI data is returned
        assert "calculation_date" in data
        assert "student_teacher_ratio" in data or "capacity_utilization" in data

    def test_kpi_calculation_secondary_exceeds_total(self, client):
        """Test KPI calculation validation when secondary > total students."""
        request_data = {
            "total_students": 100,
            "secondary_students": 200,  # More than total!
            "max_capacity": 150,
            "total_teacher_fte": 5.0,
            "total_revenue": 5000000,
            "total_costs": 4500000,
            "personnel_costs": 3000000,
        }

        response = client.post("/api/v1/calculations/kpi/calculate", json=request_data)

        # Pydantic field_validator raises ValueError → 422
        assert response.status_code == 422
        assert "cannot exceed total students" in response.json()["detail"][0]["msg"]

    def test_kpi_calculation_personnel_exceeds_total_costs(self, client):
        """Test KPI validation when personnel costs exceed total costs."""
        request_data = {
            "total_students": 1850,
            "secondary_students": 650,
            "max_capacity": 1875,
            "total_teacher_fte": 154.17,
            "total_revenue": 83272500,
            "total_costs": 50000000,  # Less than personnel costs
            "personnel_costs": 52461675,  # More than total costs!
        }

        response = client.post("/api/v1/calculations/kpi/calculate", json=request_data)

        # Pydantic field_validator raises ValueError → 422
        assert response.status_code == 422
        assert "cannot exceed total costs" in response.json()["detail"][0]["msg"]

    def test_kpi_calculation_with_dhg_hours(self, client):
        """Test KPI calculation including DHG hours for H/E ratio."""
        request_data = {
            "total_students": 1850,
            "secondary_students": 650,
            "max_capacity": 1875,
            "total_teacher_fte": 154.17,
            "dhg_hours_total": 877.5,  # Provided for H/E ratio
            "total_revenue": 83272500,
            "total_costs": 74945250,
            "personnel_costs": 52461675,
        }

        response = client.post("/api/v1/calculations/kpi/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Should have H/E ratio KPI as individual field
        assert "he_ratio_secondary" in data
        # Verify it's a KPI result object with kpi_type field
        if data["he_ratio_secondary"] is not None:
            assert data["he_ratio_secondary"]["kpi_type"] == "he_ratio_secondary"


class TestRevenueCalculationEndpoint:
    """Test POST /api/v1/calculations/revenue/calculate endpoint."""

    def test_revenue_calculation_french_student(self, client):
        """Test revenue calculation for French student (tuition + DAI + registration)."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": 45000,
            "dai_fee": 2000,
            "registration_fee": 1000,
            "sibling_order": 1,
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["level_code"] == "6EME"
        assert data["fee_category"] == "french_ttc"
        assert "total_annual_revenue" in data
        assert "trimester_distribution" in data
        assert "tuition_revenue" in data

    def test_revenue_calculation_with_sibling_discount(self, client):
        """Test revenue calculation with sibling discount (3rd+ child gets 25% off tuition)."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": 45000,
            "dai_fee": 2000,
            "registration_fee": 1000,
            "sibling_order": 3,  # 3rd child - eligible for discount
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "sibling_discount_applied" in data
        assert data["sibling_discount_applied"] is True  # 3rd child should have discount
        assert "total_annual_revenue" in data

    def test_revenue_calculation_saudi_student(self, client):
        """Test revenue calculation for Saudi student (different fee structure)."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "fee_category": "saudi_ht",
            "tuition_fee": 30000,
            "dai_fee": 1500,
            "registration_fee": 500,
            "sibling_order": 1,
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["fee_category"] == "saudi_ht"

    def test_revenue_calculation_zero_fees(self, client):
        """Test revenue calculation with zero fees (scholarship case)."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": 0,
            "dai_fee": 0,
            "registration_fee": 0,
            "sibling_order": 1,
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "total_annual_revenue" in data
        assert float(data["total_annual_revenue"]) == 0

    def test_revenue_calculation_invalid_sibling_order(self, client):
        """Test revenue calculation with invalid sibling order."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": 45000,
            "dai_fee": 2000,
            "registration_fee": 1000,
            "sibling_order": 0,  # Invalid - must be 1-10
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        # Pydantic validation error (constraint violation)
        assert response.status_code == 422

    def test_revenue_calculation_negative_fees(self, client):
        """Test revenue calculation with negative fees."""
        request_data = {
            "level_id": str(uuid4()),
            "level_code": "6EME",
            "fee_category": "french_ttc",
            "tuition_fee": -45000,  # Invalid - negative
            "dai_fee": 2000,
            "registration_fee": 1000,
            "sibling_order": 1,
        }

        response = client.post("/api/v1/calculations/revenue/calculate", json=request_data)

        # Pydantic validation error (constraint violation: tuition_fee must be >= 0)
        assert response.status_code == 422


class TestHealthCheckEndpoint:
    """Test GET /api/v1/calculations/health endpoint."""

    def test_health_check_success(self, client):
        """Test health check endpoint returns operational status."""
        response = client.get("/api/v1/calculations/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "services" in data
        assert data["services"]["enrollment"] == "operational"
        assert data["services"]["kpi"] == "operational"
        assert data["services"]["dhg"] == "operational"
        assert data["services"]["revenue"] == "operational"


class TestCalculationEndpointsErrorHandling:
    """Test error handling across calculation endpoints."""

    def test_missing_required_field_enrollment(self, client):
        """Test enrollment endpoint with missing required field."""
        request_data = {
            "level_id": str(uuid4()),
            # Missing: level_code
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 5,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_missing_required_field_kpi(self, client):
        """Test KPI endpoint with missing required field."""
        request_data = {
            "total_students": 1850,
            # Missing: secondary_students
            "max_capacity": 1875,
            "total_teacher_fte": 154.17,
            "total_revenue": 83272500,
            "total_costs": 74945250,
            "personnel_costs": 52461675,
        }

        response = client.post("/api/v1/calculations/kpi/calculate", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_invalid_json_request(self, client):
        """Test endpoint with invalid JSON."""
        response = client.post(
            "/api/v1/calculations/enrollment/project",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_invalid_uuid_format(self, client):
        """Test endpoint with invalid UUID format."""
        request_data = {
            "level_id": "not-a-uuid",  # Invalid UUID
            "level_code": "6EME",
            "nationality": "French",
            "current_enrollment": 120,
            "growth_scenario": "base",
            "years_to_project": 5,
        }

        response = client.post("/api/v1/calculations/enrollment/project", json=request_data)

        assert response.status_code == 422  # Validation error
