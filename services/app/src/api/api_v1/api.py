from fastapi import APIRouter
from src.contexts.food_tracker.fastapi.routes.houses import (
    router as food_tracker_houses,
)
from src.contexts.food_tracker.fastapi.routes.items import router as food_tracker_items
from src.contexts.iam.fastapi.routes import router as iam
from src.contexts.products_catalog.fastapi.routes.classification import (
    router as products_catalog_tags,
)
from src.contexts.products_catalog.fastapi.routes.products import (
    router as products_catalog_products,
)
from src.contexts.recipes_catalog.fastapi.routes.recipes import (
    router as recipes_catalog_recipes,
)

from . import liveness

api_router = APIRouter()
api_router.include_router(iam, tags=["iam"])
api_router.include_router(liveness.router, tags=["liveness"])
api_router.include_router(food_tracker_houses, tags=["food_tracker_houses"])
api_router.include_router(food_tracker_items, tags=["food_tracker_items"])
api_router.include_router(products_catalog_products, tags=["products_catalog_products"])
api_router.include_router(products_catalog_tags, tags=["products_catalog_tags"])
api_router.include_router(recipes_catalog_recipes, tags=["recipes_catalog_recipes"])
