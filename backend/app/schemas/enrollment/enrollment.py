"""API schemas for Enrollment endpoints."""

from app.engine.enrollment.projection.models import (
    EnrollmentInput,
    EnrollmentProjectionResult,
)

# Re-export engine models so API layer stays in sync with calculation engine.
EnrollmentProjectionRequest = EnrollmentInput
EnrollmentProjectionResponse = EnrollmentProjectionResult
