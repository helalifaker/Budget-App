"""API schemas for KPI endpoints."""

from app.engine.kpi.models import (
    KPIInput,
    KPICalculationResult,
)

# Reuse engine models for API layer
KPICalculationRequest = KPIInput
KPICalculationResponse = KPICalculationResult
