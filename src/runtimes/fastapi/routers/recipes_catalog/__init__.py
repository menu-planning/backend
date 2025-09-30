"""FastAPI routers for recipes catalog context."""

from .recipe import router as recipe_router
from .meal import router as meal_router
from .client import router as client_router
from .tag import router as tag_router
from .shopping_list import router as shopping_list_router

__all__ = [
    "recipe_router",
    "meal_router", 
    "client_router",
    "tag_router",
    "shopping_list_router",
]
