"""FastAPI router for menu aggregated view endpoints."""

from .data import router as data_router

# Combine all shopping list routers
from fastapi import APIRouter

router = APIRouter()
router.include_router(data_router)

__all__ = ["router"]
