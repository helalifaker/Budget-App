"""
Tests for MaterializedViewService.

Tests cover:
- Refreshing all materialized views
- Refreshing individual views
- View information retrieval
- Error handling (invalid views, database errors)
- Concurrent refresh handling
- SQLite fallback behavior
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.admin.materialized_view_service import MaterializedViewService
from sqlalchemy.ext.asyncio import AsyncSession


class TestMaterializedViewServiceRefreshAll:
    """Tests for refresh_all() method."""

    @pytest.mark.asyncio
    async def test_refresh_all_success(
        self,
        db_session: AsyncSession,
    ):
        """Test refreshing all materialized views successfully."""
        # Mock successful execution for both views
        mock_result = MagicMock()
        mock_result.rowcount = 1

        db_session.execute = AsyncMock(return_value=mock_result)  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        results = await MaterializedViewService.refresh_all(db_session)

        # Verify results structure
        assert isinstance(results, dict)
        assert len(results) == 2  # Two views defined in VIEWS

        for view_name in MaterializedViewService.VIEWS:
            assert view_name in results
            assert results[view_name]["status"] == "success"
            assert "duration_seconds" in results[view_name]
            assert isinstance(results[view_name]["duration_seconds"], (int, float))
            assert results[view_name]["duration_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_refresh_all_handles_error_gracefully(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_all handles errors gracefully."""
        # Mock execute to raise error for one view and succeed for another
        call_count = [0]

        async def mock_execute(_sql):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call fails
                raise Exception("Database error: view not found")
            # Second call succeeds
            return MagicMock()

        db_session.execute = AsyncMock(side_effect=mock_execute)  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        results = await MaterializedViewService.refresh_all(db_session)

        # Should have entries for all views
        assert len(results) == 2

        # First view should have error status
        first_view = MaterializedViewService.VIEWS[0]
        assert results[first_view]["status"] == "error"
        assert "error" in results[first_view]
        assert "Database error" in results[first_view]["error"]

        # Second view should have success status
        second_view = MaterializedViewService.VIEWS[1]
        assert results[second_view]["status"] == "success"
        assert "duration_seconds" in results[second_view]

    @pytest.mark.asyncio
    async def test_refresh_all_returns_duration(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_all returns duration information."""
        # Mock successful execution
        db_session.execute = AsyncMock(return_value=MagicMock())  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        results = await MaterializedViewService.refresh_all(db_session)

        for _view_name, result in results.items():
            assert result["status"] == "success"
            assert "duration_seconds" in result
            assert isinstance(result["duration_seconds"], (int, float))
            assert result["duration_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_refresh_all_commits_transaction(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_all commits after each view refresh."""
        # Mock successful execution
        db_session.execute = AsyncMock(return_value=MagicMock())  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        results = await MaterializedViewService.refresh_all(db_session)

        # Verify commit was called once per view
        assert db_session.commit.call_count == len(MaterializedViewService.VIEWS)
        assert isinstance(results, dict)
        assert len(results) == len(MaterializedViewService.VIEWS)

    @pytest.mark.asyncio
    async def test_refresh_all_logs_success(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_all logs successful refreshes."""
        # Mock successful execution
        db_session.execute = AsyncMock(return_value=MagicMock())  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        with patch('app.services.admin.materialized_view_service.logger') as mock_logger:
            results = await MaterializedViewService.refresh_all(db_session)

            # Verify logging was called for each successful refresh
            assert mock_logger.info.call_count == len(MaterializedViewService.VIEWS)

            # Verify no errors were logged
            assert mock_logger.error.call_count == 0

            # Verify all views succeeded
            for view_name in MaterializedViewService.VIEWS:
                assert results[view_name]["status"] == "success"

    @pytest.mark.asyncio
    async def test_refresh_all_logs_errors(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_all logs errors."""
        # Mock execution to always fail
        db_session.execute = AsyncMock(side_effect=Exception("Test error"))  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        with patch('app.services.admin.materialized_view_service.logger') as mock_logger:
            results = await MaterializedViewService.refresh_all(db_session)

            # Verify error logging was called for each failed refresh
            assert mock_logger.error.call_count == len(MaterializedViewService.VIEWS)

            # Verify no success logs
            assert mock_logger.info.call_count == 0

            # Verify all views failed
            for view_name in MaterializedViewService.VIEWS:
                assert results[view_name]["status"] == "error"


class TestMaterializedViewServiceRefreshView:
    """Tests for refresh_view() method."""

    @pytest.mark.asyncio
    async def test_refresh_view_success(
        self,
        db_session: AsyncSession,
    ):
        """Test refreshing a specific view successfully."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock successful execution
        db_session.execute = AsyncMock(return_value=MagicMock())  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        result = await MaterializedViewService.refresh_view(db_session, view_name)

        assert result["status"] == "success"
        assert result["view"] == view_name
        assert "duration_seconds" in result
        assert isinstance(result["duration_seconds"], (int, float))
        assert result["duration_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_refresh_view_invalid_view_name(
        self,
        db_session: AsyncSession,
    ):
        """Test refresh_view with invalid view name raises ValueError."""
        with pytest.raises(ValueError, match="is not managed by this service"):
            await MaterializedViewService.refresh_view(
                db_session, "invalid.view_name"
            )

    @pytest.mark.asyncio
    async def test_refresh_view_handles_database_error(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_view handles database errors gracefully."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock execution to fail
        db_session.execute = AsyncMock(side_effect=Exception("Database connection lost"))  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        result = await MaterializedViewService.refresh_view(db_session, view_name)

        # Should return error status
        assert result["status"] == "error"
        assert "error" in result
        assert result["view"] == view_name
        assert "Database connection lost" in result["error"]

    @pytest.mark.asyncio
    async def test_refresh_view_all_managed_views(
        self,
        db_session: AsyncSession,
    ):
        """Test refreshing each managed view individually."""
        # Mock successful execution
        db_session.execute = AsyncMock(return_value=MagicMock())  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        for view_name in MaterializedViewService.VIEWS:
            result = await MaterializedViewService.refresh_view(
                db_session, view_name
            )

            assert result["status"] == "success"
            assert result["view"] == view_name
            assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_refresh_view_uses_concurrent_refresh(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_view uses CONCURRENT refresh."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock execution and capture the SQL
        executed_sql = []

        async def capture_execute(sql):
            executed_sql.append(str(sql))
            return MagicMock()

        db_session.execute = AsyncMock(side_effect=capture_execute)  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        await MaterializedViewService.refresh_view(db_session, view_name)

        # Verify CONCURRENT keyword is used
        assert len(executed_sql) == 1
        assert "CONCURRENTLY" in executed_sql[0]
        assert view_name in executed_sql[0]

    @pytest.mark.asyncio
    async def test_refresh_view_logs_success(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_view logs successful refresh."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock successful execution
        db_session.execute = AsyncMock(return_value=MagicMock())  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        with patch('app.services.admin.materialized_view_service.logger') as mock_logger:
            result = await MaterializedViewService.refresh_view(db_session, view_name)

            # Verify success logging
            mock_logger.info.assert_called_once()
            mock_logger.error.assert_not_called()

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_refresh_view_logs_error(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_view logs errors."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock execution to fail
        db_session.execute = AsyncMock(side_effect=Exception("Test error"))  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        with patch('app.services.admin.materialized_view_service.logger') as mock_logger:
            result = await MaterializedViewService.refresh_view(db_session, view_name)

            # Verify error logging
            mock_logger.error.assert_called_once()
            mock_logger.info.assert_not_called()

            assert result["status"] == "error"


class TestMaterializedViewServiceGetViewInfo:
    """Tests for get_view_info() method."""

    @pytest.mark.asyncio
    async def test_get_view_info_success_postgresql(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving view information successfully in PostgreSQL."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock PostgreSQL bind
        mock_bind = MagicMock()
        mock_bind.dialect.name = "postgresql"
        db_session.get_bind = MagicMock(return_value=mock_bind)  # type: ignore[method-assign]

        # Mock query result
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, i: ["efir_budget", "mv_kpi_dashboard", 150, 8192][i]

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        db_session.execute = AsyncMock(return_value=mock_result)  # type: ignore[method-assign]

        info = await MaterializedViewService.get_view_info(db_session, view_name)

        assert info["view_name"] == view_name
        assert info["row_count"] == 150
        assert info["size_bytes"] == 8192
        assert info["size_mb"] == 0.01  # 8192 / (1024 * 1024) rounded to 2 decimals
        assert isinstance(info["row_count"], int)
        assert isinstance(info["size_bytes"], int)
        assert isinstance(info["size_mb"], (int, float))

    @pytest.mark.asyncio
    async def test_get_view_info_sqlite_fallback(
        self,
        db_session: AsyncSession,
    ):
        """Test get_view_info falls back to synthetic data for SQLite."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock SQLite bind
        mock_bind = MagicMock()
        mock_bind.dialect.name = "sqlite"
        db_session.get_bind = MagicMock(return_value=mock_bind)  # type: ignore[method-assign]

        info = await MaterializedViewService.get_view_info(db_session, view_name)

        # Should return synthetic data for SQLite
        assert info["view_name"] == view_name
        assert info["row_count"] == 0
        assert info["size_bytes"] == 0
        assert info["size_mb"] == 0.0

    @pytest.mark.asyncio
    async def test_get_view_info_invalid_view_name(
        self,
        db_session: AsyncSession,
    ):
        """Test get_view_info with invalid view name raises ValueError."""
        with pytest.raises(ValueError, match="is not managed by this service"):
            await MaterializedViewService.get_view_info(
                db_session, "invalid.view_name"
            )

    @pytest.mark.asyncio
    async def test_get_view_info_nonexistent_view_postgresql(
        self,
        db_session: AsyncSession,
    ):
        """Test get_view_info raises ValueError for non-existent PostgreSQL view."""
        # Mock PostgreSQL bind
        mock_bind = MagicMock()
        mock_bind.dialect.name = "postgresql"
        db_session.get_bind = MagicMock(return_value=mock_bind)  # type: ignore[method-assign]

        # Mock query result with no rows
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        db_session.execute = AsyncMock(return_value=mock_result)  # type: ignore[method-assign]

        # Temporarily add a view to the managed list
        original_views = MaterializedViewService.VIEWS.copy()
        MaterializedViewService.VIEWS.append("efir_budget.nonexistent_view")

        try:
            with pytest.raises(ValueError, match="does not exist"):
                await MaterializedViewService.get_view_info(
                    db_session, "efir_budget.nonexistent_view"
                )
        finally:
            MaterializedViewService.VIEWS[:] = original_views

    @pytest.mark.asyncio
    async def test_get_view_info_parses_view_name(
        self,
        db_session: AsyncSession,
    ):
        """Test that get_view_info correctly parses schema.table format."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock SQLite bind for simple test
        mock_bind = MagicMock()
        mock_bind.dialect.name = "sqlite"
        db_session.get_bind = MagicMock(return_value=mock_bind)  # type: ignore[method-assign]

        info = await MaterializedViewService.get_view_info(db_session, view_name)

        # Verify view_name is correctly stored
        assert info["view_name"] == view_name
        assert "." in info["view_name"]

        # Verify it was split correctly (schema, table)
        parts = view_name.split(".")
        assert len(parts) == 2
        assert parts[0] == "efir_budget"
        assert parts[1] == "mv_kpi_dashboard"

    @pytest.mark.asyncio
    async def test_get_view_info_all_managed_views(
        self,
        db_session: AsyncSession,
    ):
        """Test retrieving info for all managed views."""
        # Mock SQLite bind for simple test
        mock_bind = MagicMock()
        mock_bind.dialect.name = "sqlite"
        db_session.get_bind = MagicMock(return_value=mock_bind)  # type: ignore[method-assign]

        for view_name in MaterializedViewService.VIEWS:
            info = await MaterializedViewService.get_view_info(
                db_session, view_name
            )

            assert info["view_name"] == view_name
            assert "row_count" in info
            assert "size_bytes" in info
            assert "size_mb" in info

    @pytest.mark.asyncio
    async def test_get_view_info_queries_postgresql_catalog(
        self,
        db_session: AsyncSession,
    ):
        """Test that get_view_info queries pg_matviews for PostgreSQL."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock PostgreSQL bind
        mock_bind = MagicMock()
        mock_bind.dialect.name = "postgresql"
        db_session.get_bind = MagicMock(return_value=mock_bind)  # type: ignore[method-assign]

        # Mock query result
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, i: ["efir_budget", "mv_kpi_dashboard", 100, 4096][i]

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        executed_queries = []

        async def capture_execute(query, params=None):
            executed_queries.append((str(query), params))
            return mock_result

        db_session.execute = AsyncMock(side_effect=capture_execute)  # type: ignore[method-assign]

        await MaterializedViewService.get_view_info(db_session, view_name)

        # Verify the query was executed with correct parameters
        assert len(executed_queries) == 1
        query_str, params = executed_queries[0]

        # Verify pg_matviews is queried
        assert "pg_matviews" in query_str
        assert "schemaname" in query_str
        assert "matviewname" in query_str

        # Verify parameters were passed
        assert params is not None
        assert params["schema"] == "efir_budget"
        assert params["table"] == "mv_kpi_dashboard"


class TestMaterializedViewServiceEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_views_list_is_defined(
        self,
    ):
        """Test that VIEWS list is properly defined."""
        assert hasattr(MaterializedViewService, "VIEWS")
        assert isinstance(MaterializedViewService.VIEWS, list)
        assert len(MaterializedViewService.VIEWS) > 0

    @pytest.mark.asyncio
    async def test_views_list_contains_expected_views(
        self,
    ):
        """Test that VIEWS list contains expected materialized views."""
        expected_views = [
            "efir_budget.mv_kpi_dashboard",
            "efir_budget.mv_budget_consolidation",
        ]

        for view in expected_views:
            assert view in MaterializedViewService.VIEWS

    @pytest.mark.asyncio
    async def test_refresh_view_with_empty_string(
        self,
        db_session: AsyncSession,
    ):
        """Test refresh_view with empty string raises ValueError."""
        with pytest.raises(ValueError):
            await MaterializedViewService.refresh_view(db_session, "")

    @pytest.mark.asyncio
    async def test_get_view_info_with_malformed_view_name(
        self,
        db_session: AsyncSession,
    ):
        """Test get_view_info with malformed view name (missing schema)."""
        # First add to managed views to bypass that check
        original_views = MaterializedViewService.VIEWS.copy()
        MaterializedViewService.VIEWS.append("no_schema")

        try:
            # Mock SQLite to avoid PostgreSQL query
            mock_bind = MagicMock()
            mock_bind.dialect.name = "sqlite"
            db_session.get_bind = MagicMock(return_value=mock_bind)  # type: ignore[method-assign]

            # This should raise ValueError when trying to split by "."
            with pytest.raises(ValueError):
                await MaterializedViewService.get_view_info(db_session, "no_schema")
        finally:
            MaterializedViewService.VIEWS[:] = original_views

    @pytest.mark.asyncio
    async def test_refresh_all_empty_views_list(
        self,
        db_session: AsyncSession,
    ):
        """Test refresh_all with empty VIEWS list returns empty dict."""
        original_views = MaterializedViewService.VIEWS.copy()
        MaterializedViewService.VIEWS.clear()

        try:
            results = await MaterializedViewService.refresh_all(db_session)
            assert results == {}
        finally:
            MaterializedViewService.VIEWS[:] = original_views

    @pytest.mark.asyncio
    async def test_refresh_all_partial_failure(
        self,
        db_session: AsyncSession,
    ):
        """Test refresh_all continues after partial failures."""
        # Create a mock that fails on first call, succeeds on second
        call_count = [0]

        async def mock_execute_partial_fail(_sql):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First view failed")
            return MagicMock()

        db_session.execute = AsyncMock(side_effect=mock_execute_partial_fail)  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        results = await MaterializedViewService.refresh_all(db_session)

        # Should have results for all views
        assert len(results) == 2

        # First should fail
        first_view = MaterializedViewService.VIEWS[0]
        assert results[first_view]["status"] == "error"

        # Second should succeed
        second_view = MaterializedViewService.VIEWS[1]
        assert results[second_view]["status"] == "success"

    @pytest.mark.asyncio
    async def test_refresh_view_rounds_duration(
        self,
        db_session: AsyncSession,
    ):
        """Test that refresh_view rounds duration to 2 decimal places."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock successful execution
        db_session.execute = AsyncMock(return_value=MagicMock())  # type: ignore[method-assign]
        db_session.commit = AsyncMock()  # type: ignore[method-assign]

        result = await MaterializedViewService.refresh_view(db_session, view_name)

        # Verify duration is rounded to 2 decimal places
        assert "duration_seconds" in result
        duration_str = str(result["duration_seconds"])
        if "." in duration_str:
            decimal_places = len(duration_str.split(".")[1])
            assert decimal_places <= 2

    @pytest.mark.asyncio
    async def test_service_is_stateless(
        self,
    ):
        """Test that MaterializedViewService is stateless (all class methods)."""
        # Verify all public methods are class methods
        assert callable(MaterializedViewService.refresh_all)
        assert callable(MaterializedViewService.refresh_view)
        assert callable(MaterializedViewService.get_view_info)

        # Service should be usable directly from the class without instantiation
        # Verify methods are not instance methods by checking if they're bound
        import inspect
        assert inspect.ismethod(MaterializedViewService.refresh_all)
        assert inspect.ismethod(MaterializedViewService.refresh_view)
        assert inspect.ismethod(MaterializedViewService.get_view_info)

    @pytest.mark.asyncio
    async def test_get_view_info_size_mb_calculation(
        self,
        db_session: AsyncSession,
    ):
        """Test that size_mb is correctly calculated from size_bytes."""
        view_name = "efir_budget.mv_kpi_dashboard"

        # Mock PostgreSQL bind
        mock_bind = MagicMock()
        mock_bind.dialect.name = "postgresql"
        db_session.get_bind = MagicMock(return_value=mock_bind)  # type: ignore[method-assign]

        # Mock query result with known size
        size_bytes = 1048576  # Exactly 1 MB
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, i: ["efir_budget", "mv_kpi_dashboard", 100, size_bytes][i]

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        db_session.execute = AsyncMock(return_value=mock_result)  # type: ignore[method-assign]

        info = await MaterializedViewService.get_view_info(db_session, view_name)

        # Verify size_mb calculation
        assert info["size_bytes"] == size_bytes
        assert info["size_mb"] == 1.0  # 1048576 / (1024 * 1024) = 1.0
