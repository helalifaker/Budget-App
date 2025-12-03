"""
Health check endpoints for EFIR Budget Planning Application.

Provides comprehensive health monitoring for:
- Liveness: Basic server availability
- Readiness: Dependency health (Database, Redis, Supabase Auth)
- Metrics: Placeholder for Prometheus metrics (Phase 2)
"""

import os
import time
from datetime import UTC, datetime
from typing import Any, cast

import httpx
from app.core.logging import logger
from app.database import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Main health check endpoint.

    Returns:
        dict: Health status of the application

    Status Codes:
        200: Application is running
    """
    return {"status": "healthy", "service": "EFIR Budget Planning API"}


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """
    Liveness probe endpoint - Kubernetes/container orchestration.

    Checks if the server process is running and can handle requests.
    Does not check external dependencies.

    Returns:
        dict: Basic liveness status

    Status Codes:
        200: Server is alive and responding
    """
    return {"status": "ok", "service": "efir-budget-api"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness probe endpoint - Comprehensive dependency health check.

    Checks all critical dependencies before allowing traffic:
    - PostgreSQL database connectivity (via Supabase)
    - Supabase Auth API availability
    - Redis connectivity (placeholder for Phase 2)

    Args:
        db: Database session dependency injection

    Returns:
        dict: Detailed health status with component checks
            - status: Overall health ("ok" or "degraded")
            - checks: Individual component health details
            - timestamp: ISO 8601 formatted UTC timestamp

    Status Codes:
        200: All dependencies healthy or degraded (still serving traffic)
        503: Critical failure (not yet implemented - returns 200 with degraded status)

    Example Response:
        {
            "status": "ok",
            "checks": {
                "database": {"status": "ok", "latency_ms": 12.5},
                "supabase_auth": {"status": "ok"},
                "redis": {"status": "not_configured"}
            },
            "timestamp": "2025-12-02T19:45:30.123456Z"
        }
    """
    checks: dict[str, Any] = {}
    overall_status = "ok"

    # 1. Check PostgreSQL database connectivity
    try:
        start_time = time.perf_counter()
        await db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        checks["database"] = {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}
        overall_status = "degraded"

    # 2. Check Supabase Auth API availability
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        if supabase_url:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{supabase_url}/auth/v1/health")
                # 200 = healthy, 401 = service requires auth (also healthy)
                # 404+ or timeout = service down (degraded)
                if response.status_code in (200, 401):
                    note = None
                    if response.status_code == 401:
                        note = "Service reachable (requires auth)"
                    checks["supabase_auth"] = {"status": "ok", "note": note}
                else:
                    checks["supabase_auth"] = {
                        "status": "error",
                        "http_code": response.status_code,
                    }
                    overall_status = "degraded"
        else:
            checks["supabase_auth"] = {
                "status": "not_configured",
                "note": "SUPABASE_URL environment variable not set",
            }
    except httpx.TimeoutException:
        checks["supabase_auth"] = {"status": "error", "error": "Request timeout (5s)"}
        overall_status = "degraded"
    except Exception as e:
        checks["supabase_auth"] = {"status": "error", "error": str(e)}
        overall_status = "degraded"

    # 3. Check Redis connectivity
    try:
        from app.core.cache import REDIS_ENABLED, get_redis_client

        if REDIS_ENABLED:
            redis_client = await get_redis_client()
            start_time = time.perf_counter()
            # Cast to Awaitable for async Redis client (ping returns Union[Awaitable[bool], bool])
            await cast("Any", redis_client.ping())
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            checks["redis"] = {"status": "ok", "latency_ms": latency_ms}
        else:
            checks["redis"] = {
                "status": "disabled",
                "note": "Redis caching is disabled via REDIS_ENABLED=false",
            }
    except Exception as e:
        checks["redis"] = {"status": "error", "error": str(e)}
        overall_status = "degraded"

    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/metrics")
async def metrics() -> dict[str, Any]:
    """
    Prometheus metrics endpoint (placeholder).

    Will expose application metrics in Prometheus format in Phase 2:
    - Request counts and latencies
    - Database connection pool stats
    - Cache hit/miss rates
    - Business metrics (active budgets, calculations/sec)

    Returns:
        dict: Placeholder response with planned metrics list

    Status Codes:
        200: Metrics endpoint available (not yet implemented)

    Note:
        Prometheus metrics will be implemented in Phase 2 using prometheus-client library.
    """
    return {
        "status": "not_implemented",
        "note": "Prometheus metrics will be implemented in Phase 2",
        "planned_metrics": [
            "http_requests_total",
            "http_request_duration_seconds",
            "db_connections_active",
            "cache_hits_total",
            "budget_calculations_total",
        ],
    }


@router.get("/health/cache")
async def cache_statistics() -> dict[str, Any]:
    """
    Get Redis cache statistics and performance metrics.

    Returns detailed cache health information including:
    - Connected clients
    - Memory usage
    - Total cached keys
    - Hit/miss rates
    - Cache effectiveness (hit rate percentage)

    Returns:
        dict: Cache statistics and performance metrics

    Status Codes:
        200: Cache statistics retrieved successfully
        503: Redis unavailable (returns degraded status)

    Example Response:
        {
            "status": "enabled",
            "connected_clients": 5,
            "used_memory": "12.5M",
            "total_keys": 1234,
            "hits": 98765,
            "misses": 1235,
            "hit_rate": 98.76,
            "uptime_seconds": 86400,
            "redis_version": "7.0.0"
        }
    """
    try:
        from app.core.cache import get_cache_stats

        stats = await get_cache_stats()
        return stats
    except Exception as e:
        logger.error("cache_stats_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve cache statistics",
        }


@router.get("/health/sentry-test")
async def sentry_test() -> dict[str, str]:
    """
    Test Sentry error capture and structured logging.

    This endpoint deliberately raises an exception to verify:
    1. Sentry integration is working and capturing errors
    2. Structured logging is properly configured
    3. Correlation IDs are being tracked

    Returns:
        Never returns - always raises an exception

    Raises:
        ValueError: Test error for Sentry verification

    Status Codes:
        500: Always returns 500 due to deliberate error

    Warning:
        This endpoint should only be used in development/staging.
        Consider removing or protecting in production.
    """
    logger.error(
        "sentry_integration_test",
        test_type="deliberate",
        message="Testing Sentry integration with structured logging",
    )
    raise ValueError("This is a test error for Sentry integration verification")
