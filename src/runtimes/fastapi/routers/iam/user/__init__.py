"""FastAPI router for user endpoints."""

from .create import router as create_router
from .assign_role import router as assign_role_router

# Combine all user routers
from fastapi import APIRouter

router = APIRouter()
router.include_router(create_router)
router.include_router(assign_role_router)

__all__ = ["router"]
