"""FastAPI routers for recipes catalog context."""

from .recipe import router as recipe_router
from .meal import router as meal_router
from .client import router as client_router
from .tag import router as tag_router
from .menu_view import router as menu_view_router

__all__ = [
    "recipe_router",
    "meal_router", 
    "client_router",
    "tag_router",
    "menu_view_router",
]
