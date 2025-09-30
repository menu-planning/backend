"""FastAPI router for tag endpoints."""

from .search import router as search_router
from .get import router as get_router

# Combine all tag routers
from fastapi import APIRouter

router = APIRouter()
router.include_router(search_router)
router.include_router(get_router)

__all__ = ["router"]
