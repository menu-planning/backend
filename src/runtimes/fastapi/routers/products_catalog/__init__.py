"""FastAPI routers for products catalog context."""

from .search import router as search_router
from .get import router as get_router
from .create import router as create_router
from .similar_names import router as similar_names_router
from .sources import router as sources_router
from .source_get import router as source_get_router

# Combine all product routers
from fastapi import APIRouter

router = APIRouter()
router.include_router(search_router)
router.include_router(create_router)
router.include_router(similar_names_router)
router.include_router(sources_router)
router.include_router(source_get_router)
router.include_router(get_router)

__all__ = ["router"]
