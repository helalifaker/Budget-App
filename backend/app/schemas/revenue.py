"""API schemas for Revenue endpoints."""

from app.engine.revenue.models import (
    TuitionInput,
    StudentRevenueResult,
)

# Reuse engine models for API layer
RevenueCalculationRequest = TuitionInput
RevenueCalculationResponse = StudentRevenueResult
