"""FastAPI router for client endpoints."""

from .search import router as search_router
from .get import router as get_router
from .create import router as create_router
from .update import router as update_router
from .delete import router as delete_router
from .menu import router as menu_router

# Combine all client routers
from fastapi import APIRouter

router = APIRouter()
router.include_router(search_router)
router.include_router(get_router)
router.include_router(create_router)
router.include_router(update_router)
router.include_router(delete_router)
router.include_router(menu_router)

__all__ = ["router"]
