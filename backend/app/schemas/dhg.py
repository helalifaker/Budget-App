"""API schemas for DHG endpoints."""

from app.engine.dhg.models import (
    DHGHoursResult,
    DHGInput,
)

# Reuse engine models for API layer
DHGCalculationRequest = DHGInput
DHGCalculationResponse = DHGHoursResult
