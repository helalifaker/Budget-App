
from app.services.exceptions import (
    ForbiddenError,
    UnauthorizedError,
    BusinessRuleError,
    IntegrationError,
)


class TestAdditionalExceptionCases:
    """Test additional exception scenarios."""

    def test_forbidden_error_custom_message(self):
        """Test ForbiddenError with custom message."""
        error = ForbiddenError("Custom forbidden message")

        assert error.message == "Custom forbidden message"
        assert error.status_code == 403

    def test_unauthorized_error_custom_message(self):
        """Test UnauthorizedError with custom message."""
        error = UnauthorizedError("Custom auth message")

        assert error.message == "Custom auth message"
        assert error.status_code == 401

    def test_business_rule_error_with_details(self):
        """Test BusinessRuleError with additional details."""
        error = BusinessRuleError(
            rule="BUDGET_LOCKED",
            message="Budget is locked for editing",
            details={"locked_by": "admin@example.com", "locked_at": "2025-01-01"}
        )

        assert error.details["rule"] == "BUDGET_LOCKED"
        assert error.details["locked_by"] == "admin@example.com"
        assert error.status_code == 422

    def test_integration_error_with_type(self):
        """Test IntegrationError with integration type."""
        error = IntegrationError(
            message="Failed to connect to Odoo",
            integration_type="odoo",
            details={"endpoint": "https://odoo.example.com/api"}
        )

        assert "Odoo" in str(error) or "odoo" in str(error) or "Failed" in str(error)
        assert error.status_code == 502
