"""Health check endpoints for FastAPI application monitoring.

This module provides health and readiness check endpoints that can be used
for monitoring, load balancer health checks, and application status verification.
"""
from src.runtimes.fastapi.routers.helpers import create_success_response, create_router

router = create_router(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Basic health status indicating the service is running.
    """
    return create_success_response({"status": "healthy"})


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint.
    
    This endpoint can be extended to check database connectivity,
    external service availability, and other readiness criteria.
    
    Returns:
        Readiness status indicating the service is ready to handle requests.
    """
    # TODO: Add database/redis checks here when needed
    # For now, return basic readiness status
    return create_success_response({"status": "ready"})
