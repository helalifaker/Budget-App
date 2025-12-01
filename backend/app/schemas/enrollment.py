"""API schemas for Enrollment endpoints."""

from app.engine.enrollment.models import (
    EnrollmentInput,
    EnrollmentProjectionResult,
)

# Reuse engine models for API layer
EnrollmentProjectionRequest = EnrollmentInput
EnrollmentProjectionResponse = EnrollmentProjectionResult
