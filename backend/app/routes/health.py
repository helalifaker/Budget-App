from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Main health check endpoint.

    Returns:
        Health status of the application
    """
    return {"status": "healthy", "service": "EFIR Budget Planning API"}


@router.get("/health/live")
async def live() -> dict[str, str]:
    """
    Liveness probe endpoint.

    Returns:
        OK if the application is running
    """
    return {"status": "ok"}


@router.get("/health/ready")
async def ready() -> dict[str, str]:
    """
    Readiness probe endpoint.

    Returns:
        Ready status after checking dependencies
    """
    # Placeholder for future dependency checks (DB, cache, etc.)
    return {"status": "ready"}
