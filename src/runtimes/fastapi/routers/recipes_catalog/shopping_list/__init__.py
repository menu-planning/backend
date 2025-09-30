"""FastAPI router for shopping list endpoints."""

from .recipes import router as recipes_router

# Export the recipes router as the main router
router = recipes_router

__all__ = ["router"]
