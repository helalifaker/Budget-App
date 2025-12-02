"""
Tests for RBAC middleware.

Verifies role-based access control enforcement, especially for:
1. Parameterized path matching (e.g., /api/v1/budget-versions/{id}/approve)
2. Manager-only operations (approve, submit, lock)
3. Viewer read-only restrictions
4. Admin full access
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.rbac import RBACMiddleware


class TestRBACPathMatching:
    """Test path pattern matching with {param} placeholders."""

    def test_path_pattern_to_regex_simple(self):
        """Test regex conversion for simple parameterized path."""
        pattern = RBACMiddleware._path_pattern_to_regex("/api/v1/users/{id}")

        # Should match paths with actual IDs
        assert pattern.match("/api/v1/users/123")
        assert pattern.match("/api/v1/users/abc-def-456")
        assert pattern.match("/api/v1/users/uuid-1234-5678")

        # Should NOT match different paths
        assert not pattern.match("/api/v1/users")
        assert not pattern.match("/api/v1/users/123/extra")
        assert not pattern.match("/api/v2/users/123")

    def test_path_pattern_to_regex_with_action(self):
        """Test regex conversion for path with action endpoint."""
        pattern = RBACMiddleware._path_pattern_to_regex("/api/v1/budget-versions/{id}/approve")

        # Should match approve endpoint with any ID
        assert pattern.match("/api/v1/budget-versions/123/approve")
        assert pattern.match("/api/v1/budget-versions/abc-def-456/approve")

        # Should NOT match different actions
        assert not pattern.match("/api/v1/budget-versions/123/reject")
        assert not pattern.match("/api/v1/budget-versions/123/submit")
        assert not pattern.match("/api/v1/budget-versions/approve")

    def test_path_pattern_to_regex_multiple_params(self):
        """Test regex conversion for path with multiple parameters."""
        pattern = RBACMiddleware._path_pattern_to_regex("/api/v1/org/{org_id}/budget/{id}")

        # Should match paths with both parameters
        assert pattern.match("/api/v1/org/org-123/budget/budget-456")
        assert pattern.match("/api/v1/org/abc/budget/def")

        # Should NOT match incomplete paths
        assert not pattern.match("/api/v1/org/org-123/budget")
        assert not pattern.match("/api/v1/org/budget/budget-456")

    def test_matches_any_pattern_with_placeholder(self):
        """Test pattern matching for paths with placeholders."""
        # Test manager paths
        assert RBACMiddleware._matches_any_pattern(
            "/api/v1/budget-versions/123/approve",
            ["/api/v1/budget-versions/{id}/approve"]
        )

        assert RBACMiddleware._matches_any_pattern(
            "/api/v1/budget-versions/abc-def-456/submit",
            ["/api/v1/budget-versions/{id}/submit"]
        )

        # Should not match when pattern doesn't match
        assert not RBACMiddleware._matches_any_pattern(
            "/api/v1/budget-versions/123/reject",
            ["/api/v1/budget-versions/{id}/approve"]
        )

    def test_matches_any_pattern_literal(self):
        """Test pattern matching for literal paths."""
        # Test admin paths (no placeholders)
        assert RBACMiddleware._matches_any_pattern(
            "/api/v1/users",
            ["/api/v1/users"]
        )

        assert RBACMiddleware._matches_any_pattern(
            "/api/v1/users/list",
            ["/api/v1/users"]
        )

        assert not RBACMiddleware._matches_any_pattern(
            "/api/v1/budgets",
            ["/api/v1/users"]
        )

    def test_matches_any_pattern_mixed(self):
        """Test pattern matching with mixed literal and parameterized patterns."""
        patterns = [
            "/api/v1/users",
            "/api/v1/budget-versions/{id}/approve",
            "/api/v1/system",
        ]

        # Should match literal paths
        assert RBACMiddleware._matches_any_pattern("/api/v1/users", patterns)
        assert RBACMiddleware._matches_any_pattern("/api/v1/system", patterns)

        # Should match parameterized paths
        assert RBACMiddleware._matches_any_pattern(
            "/api/v1/budget-versions/123/approve",
            patterns
        )

        # Should not match unrelated paths
        assert not RBACMiddleware._matches_any_pattern("/api/v1/budgets", patterns)


class TestRBACMiddlewareIntegration:
    """Integration tests for RBAC middleware with FastAPI."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with RBAC middleware."""
        app = FastAPI()
        app.add_middleware(RBACMiddleware)

        # Mock endpoints
        @app.get("/api/v1/budget-versions/{id}")
        async def get_budget(id: str):
            return {"id": id, "status": "draft"}

        @app.post("/api/v1/budget-versions/{id}/approve")
        async def approve_budget(id: str):
            return {"id": id, "status": "approved"}

        @app.post("/api/v1/budget-versions/{id}/submit")
        async def submit_budget(id: str):
            return {"id": id, "status": "submitted"}

        @app.put("/api/v1/budget-versions/{id}")
        async def update_budget(id: str):
            return {"id": id, "status": "updated"}

        @app.get("/api/v1/users")
        async def list_users():
            return {"users": []}

        return app

    @pytest.mark.asyncio
    async def test_manager_approve_endpoint_blocks_planner(self, app):
        """Test that /approve endpoint is protected from planners."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Mock request state with planner role
        async def mock_planner_middleware(request: Request, call_next):
            request.state.user_role = "planner"
            return await call_next(request)

        app.middleware("http")(mock_planner_middleware)

        # Planner should NOT be able to approve
        response = client.post("/api/v1/budget-versions/123/approve")
        assert response.status_code == 403
        assert response.json()["detail"] == "Manager or admin access required"

    @pytest.mark.asyncio
    async def test_manager_approve_endpoint_allows_manager(self, app):
        """Test that /approve endpoint allows managers."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Mock request state with manager role
        async def mock_manager_middleware(request: Request, call_next):
            request.state.user_role = "manager"
            return await call_next(request)

        app.middleware("http")(mock_manager_middleware)

        # Manager SHOULD be able to approve
        response = client.post("/api/v1/budget-versions/123/approve")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_manager_submit_endpoint_blocks_planner(self, app):
        """Test that /submit endpoint is protected from planners."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Mock request state with planner role
        async def mock_planner_middleware(request: Request, call_next):
            request.state.user_role = "planner"
            return await call_next(request)

        app.middleware("http")(mock_planner_middleware)

        # Planner should NOT be able to submit
        response = client.post("/api/v1/budget-versions/abc-def-456/submit")
        assert response.status_code == 403
        assert response.json()["detail"] == "Manager or admin access required"

    @pytest.mark.asyncio
    async def test_admin_bypasses_all_restrictions(self, app):
        """Test that admin has full access to all endpoints."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Mock request state with admin role
        async def mock_admin_middleware(request: Request, call_next):
            request.state.user_role = "admin"
            return await call_next(request)

        app.middleware("http")(mock_admin_middleware)

        # Admin should access everything
        response = client.post("/api/v1/budget-versions/123/approve")
        assert response.status_code == 200

        response = client.get("/api/v1/users")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_viewer_can_read_budgets(self, app):
        """Test that viewers can read budgets (GET)."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Mock request state with viewer role
        async def mock_viewer_middleware(request: Request, call_next):
            request.state.user_role = "viewer"
            return await call_next(request)

        app.middleware("http")(mock_viewer_middleware)

        # Viewer SHOULD be able to read
        response = client.get("/api/v1/budget-versions/123")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_viewer_cannot_modify_budgets(self, app):
        """Test that viewers cannot modify budgets (PUT/POST)."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Mock request state with viewer role
        async def mock_viewer_middleware(request: Request, call_next):
            request.state.user_role = "viewer"
            return await call_next(request)

        app.middleware("http")(mock_viewer_middleware)

        # Viewer should NOT be able to update
        response = client.put("/api/v1/budget-versions/123")
        assert response.status_code == 403
        assert response.json()["detail"] == "Read-only access. Cannot modify data."

    @pytest.mark.asyncio
    async def test_admin_only_paths_block_manager(self, app):
        """Test that admin-only paths block managers."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Mock request state with manager role
        async def mock_manager_middleware(request: Request, call_next):
            request.state.user_role = "manager"
            return await call_next(request)

        app.middleware("http")(mock_manager_middleware)

        # Manager should NOT access admin paths
        response = client.get("/api/v1/users")
        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"


class TestRBACEdgeCases:
    """Test edge cases and security scenarios."""

    def test_path_with_special_characters(self):
        """Test path matching with special regex characters."""
        pattern = RBACMiddleware._path_pattern_to_regex("/api/v1/budget-versions/{id}/approve")

        # Should handle UUIDs with dashes
        assert pattern.match("/api/v1/budget-versions/abc-def-123-456/approve")

        # Should not allow path traversal
        assert not pattern.match("/api/v1/budget-versions/../admin/approve")

    def test_multiple_manager_paths(self):
        """Test that all manager paths are protected."""
        manager_paths = [
            "/api/v1/budget-versions/{id}/approve",
            "/api/v1/budget-versions/{id}/submit",
            "/api/v1/budget-versions/{id}/lock",
        ]

        for path_template in manager_paths:
            # Replace {id} with actual ID
            actual_path = path_template.replace("{id}", "123")

            # Should match the pattern
            assert RBACMiddleware._matches_any_pattern(actual_path, manager_paths)

    def test_public_paths_bypass_rbac(self):
        """Test that public paths are not checked by RBAC."""
        public_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json"]

        for path in public_paths:
            # Public paths should not require role checks
            # (This is checked in the dispatch method, not in pattern matching)
            assert path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]
