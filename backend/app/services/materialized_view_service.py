"""
Service for managing materialized views.

Provides functionality to refresh materialized views for KPI dashboard
and budget consolidation performance optimization.

Business Purpose:
-----------------
1. Maintain precomputed aggregations for fast dashboard queries
2. Support scheduled and on-demand refresh of materialized views
3. Monitor refresh performance and handle errors gracefully

Performance Notes:
------------------
- REFRESH MATERIALIZED VIEW CONCURRENTLY allows queries during refresh
- Requires unique indexes on the materialized views
- Typical refresh time: 0.5-2 seconds depending on data volume
"""

import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger


class MaterializedViewService:
    """
    Manage materialized view refresh operations.

    This service handles:
    - Refreshing all materialized views
    - Refreshing individual materialized views
    - Logging refresh performance metrics
    - Error handling and recovery
    """

    # List of all materialized views managed by this service
    VIEWS: list[str] = [
        "efir_budget.mv_kpi_dashboard",
        "efir_budget.mv_budget_consolidation",
    ]

    @classmethod
    async def refresh_all(cls, db: AsyncSession) -> dict[str, dict[str, Any]]:
        """
        Refresh all materialized views.

        This method refreshes all KPI dashboard materialized views
        concurrently to minimize query disruption.

        Args:
            db: Database session

        Returns:
            Dictionary mapping view names to refresh results:
            {
                "view_name": {
                    "status": "success" | "error",
                    "duration_seconds": float,
                    "error": str (only if status is "error")
                }
            }

        Example:
            >>> results = await MaterializedViewService.refresh_all(db)
            >>> print(results["efir_budget.mv_kpi_dashboard"]["status"])
            "success"
        """
        results: dict[str, dict[str, Any]] = {}

        for view_name in cls.VIEWS:
            try:
                start_time = time.time()

                # REFRESH MATERIALIZED VIEW CONCURRENTLY allows queries during refresh
                # Requires unique index on the view (created in migration)
                await db.execute(
                    text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
                )
                await db.commit()

                duration = time.time() - start_time
                results[view_name] = {
                    "status": "success",
                    "duration_seconds": round(duration, 2),
                }

                logger.info(
                    "materialized_view_refreshed",
                    view=view_name,
                    duration_seconds=duration,
                )

            except Exception as e:
                results[view_name] = {"status": "error", "error": str(e)}

                logger.error(
                    "materialized_view_refresh_failed",
                    view=view_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

        return results

    @classmethod
    async def refresh_view(
        cls, db: AsyncSession, view_name: str
    ) -> dict[str, Any]:
        """
        Refresh a specific materialized view.

        Args:
            db: Database session
            view_name: Full view name (e.g., "efir_budget.mv_kpi_dashboard")

        Returns:
            Refresh result dictionary:
            {
                "status": "success" | "error",
                "view": str,
                "duration_seconds": float,
                "error": str (only if status is "error")
            }

        Raises:
            ValueError: If view_name is not in the managed views list

        Example:
            >>> result = await MaterializedViewService.refresh_view(
            ...     db, "efir_budget.mv_kpi_dashboard"
            ... )
            >>> print(result["duration_seconds"])
            0.87
        """
        if view_name not in cls.VIEWS:
            raise ValueError(
                f"View '{view_name}' is not managed by this service. "
                f"Managed views: {', '.join(cls.VIEWS)}"
            )

        try:
            start_time = time.time()

            await db.execute(
                text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
            )
            await db.commit()

            duration = time.time() - start_time

            logger.info(
                "materialized_view_refreshed",
                view=view_name,
                duration_seconds=duration,
            )

            return {
                "status": "success",
                "view": view_name,
                "duration_seconds": round(duration, 2),
            }

        except Exception as e:
            logger.error(
                "materialized_view_refresh_failed",
                view=view_name,
                error=str(e),
                error_type=type(e).__name__,
            )

            return {
                "status": "error",
                "view": view_name,
                "error": str(e),
            }

    @classmethod
    async def get_view_info(
        cls, db: AsyncSession, view_name: str
    ) -> dict[str, Any]:
        """
        Get information about a materialized view.

        Args:
            db: Database session
            view_name: Full view name (e.g., "efir_budget.mv_kpi_dashboard")

        Returns:
            View information dictionary:
            {
                "view_name": str,
                "row_count": int,
                "size_bytes": int,
                "last_refresh": datetime | None
            }

        Example:
            >>> info = await MaterializedViewService.get_view_info(
            ...     db, "efir_budget.mv_kpi_dashboard"
            ... )
            >>> print(info["row_count"])
            25
        """
        if view_name not in cls.VIEWS:
            raise ValueError(
                f"View '{view_name}' is not managed by this service. "
                f"Managed views: {', '.join(cls.VIEWS)}"
            )

        # Extract schema and table name
        schema, table = view_name.split(".")

        # Query view statistics from PostgreSQL system catalog
        query = text(
            f"""
            SELECT
                schemaname,
                matviewname,
                (SELECT COUNT(*) FROM {view_name}) as row_count,
                pg_total_relation_size(matviewname::regclass) as size_bytes
            FROM pg_matviews
            WHERE schemaname = :schema AND matviewname = :table
        """
        )

        result = await db.execute(query, {"schema": schema, "table": table})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Materialized view '{view_name}' does not exist")

        return {
            "view_name": view_name,
            "row_count": row[2],
            "size_bytes": row[3],
            "size_mb": round(row[3] / (1024 * 1024), 2),
        }
