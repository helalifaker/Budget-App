"""Lightweight coverage tests for integration schemas and models."""

from datetime import datetime
from uuid import uuid4

import pytest
from app.models import IntegrationLog, IntegrationSettings
from app.schemas.admin import integrations as schemas


def test_integration_schemas_construction_and_validation():
    """Ensure integration schemas instantiate and basic validation works."""
    connection = schemas.OdooConnectionRequest(
        url="https://odoo.example.com",
        database="school",
        username="api",
        password="secret",
    )
    assert connection.url.startswith("https://")

    actuals_req = schemas.OdooImportActualsRequest(
        version_id=uuid4(),
        period="T1",
        fiscal_year=2025,
    )
    assert actuals_req.period == "T1"

    record = schemas.OdooActualRecord(
        account_code="7011",
        amount=1250.5,
        description="Tuition",
    )
    actuals_resp = schemas.OdooImportActualsResponse(
        success=True,
        message="Imported",
        records_imported=1,
        batch_id=uuid4(),
        log_id=uuid4(),
    )
    assert actuals_resp.records_imported == 1
    assert record.account_code == "7011"

    skolengo_record = schemas.SkolengoEnrollmentRecord(
        level="CP",
        nationality="French",
        count=24,
    )
    assert skolengo_record.count == 24

    comparison = schemas.SkolengoComparisonResponse(
        variances=[
            schemas.EnrollmentVariance(
                level="CP",
                nationality="French",
                budget=24,
                actual=22,
                variance=-2,
                variance_percent=-8.33,
            )
        ],
        total_budget=24,
        total_actual=22,
        total_variance=-2,
    )
    assert comparison.variances[0].variance == -2

    settings = schemas.IntegrationSettingsCreate(
        integration_type="odoo",
        config={"url": "https://odoo.example.com"},
        auto_sync_enabled=True,
        auto_sync_interval_minutes=15,
    )
    assert settings.auto_sync_enabled is True

    response_settings = schemas.IntegrationSettingsResponse(
        id=uuid4(),
        integration_type="odoo",
        config=settings.config,
        is_active=True,
        last_sync_at=datetime.utcnow(),
        auto_sync_enabled=True,
        auto_sync_interval_minutes=15,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert response_settings.integration_type == "odoo"

    log_entry = schemas.IntegrationLogResponse(
        id=uuid4(),
        integration_type="odoo",
        action="import_actuals",
        status="success",
        records_processed=10,
        records_failed=0,
        error_message=None,
        metadata_json={"source": "test"},
        batch_id=uuid4(),
        created_at=datetime.utcnow(),
        created_by_id=None,
    )
    log_list = schemas.IntegrationLogListResponse(
        logs=[log_entry],
        total_count=1,
        page=1,
        page_size=50,
    )
    assert log_list.logs[0].integration_type == "odoo"


def test_aefe_position_record_validation():
    """Verify AEFE record enforces non-negative PRRD rate."""
    with pytest.raises(ValueError):
        schemas.AEFEPositionRecord(
            teacher_name="Test",
            category="Detached",
            cycle="Secondary",
            prrd_rate=-1,
            is_aefe=False,
        )


def test_integration_models_repr_and_defaults():
    """Basic model instantiation covers __repr__ paths."""
    log = IntegrationLog(
        integration_type="skolengo",
        action="export_enrollment",
        status="success",
        records_processed=5,
        records_failed=0,
        batch_id=uuid4(),
        metadata_json={"file": "enrollment.csv"},
    )
    assert "skolengo" in repr(log)

    settings = IntegrationSettings(
        integration_type="aefe",
        config={"endpoint": "https://aefe.example.com"},
        is_active=True,
        auto_sync_enabled=False,
        auto_sync_interval_minutes=None,
    )
    assert "aefe" in repr(settings)
