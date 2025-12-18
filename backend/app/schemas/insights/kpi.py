"""API schemas for KPI endpoints."""

from app.engine.insights.kpi.models import (
    KPICalculationResult,
    KPIInput,
)

# Reuse engine models for API layer
KPICalculationRequest = KPIInput
KPICalculationResponse = KPICalculationResult
