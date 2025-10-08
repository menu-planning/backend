"""FastAPI router for shopping list data endpoint."""

from typing import Annotated

from fastapi import Depends, Query

from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.fastapi.dependencies import get_products_bus
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.value_objects.api_shopping_list_data import (
    ApiShoppingListDataRequest,
    ApiShoppingListDataResponse,
)
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import get_logger
from src.runtimes.fastapi.routers.helpers import create_router, create_success_response
from fastapi.responses import JSONResponse


logger = get_logger(__name__)

router = create_router(prefix="/menu-view")

@router.get("/data", response_model=None)
async def get_shopping_list_data(
    params: Annotated[ApiShoppingListDataRequest, Query()],
    recipes_bus: MessageBus = Depends(get_recipes_bus),
    products_bus: MessageBus = Depends(get_products_bus),
) -> JSONResponse:
    """Fetch all data needed for the shopping list frontend view."""
    from src.contexts.recipes_catalog.core.services.uow import UnitOfWork as RecipesUnitOfWork
    from src.contexts.products_catalog.core.services.uow import UnitOfWork as ProductsUnitOfWork

    # 1. Fetch clients and menus from recipes_catalog
    recipes_uow: RecipesUnitOfWork
    clients: list[Client]

    async with recipes_bus.uow_factory() as recipes_uow:
        clients = await recipes_uow.clients.query(filters={"menu_id": params.menu_ids})
        logger.error(f"Fetched {len(clients)} clients for menu IDs: {params.menu_ids}")

    menus = [menu for client in clients for menu in client.menus if menu.id in params.menu_ids]

    # 2. Fetch meals from recipes_catalog
    meal_ids = {meal.meal_id for menu in menus for meal in menu.meals}
    meals: list[Meal] = []
    if meal_ids:
        async with recipes_bus.uow_factory() as recipes_uow:
            meals = await recipes_uow.meals.query(filters={"id": list(meal_ids)})

    # 3. Fetch products from products_catalog
    product_ids = {product_id for meal in meals for product_id in meal.products_ids}
    products: list[Product] = []
    if product_ids:
        products_uow: ProductsUnitOfWork
        async with products_bus.uow_factory() as products_uow:
            products = await products_uow.products.query(filters={"id": list(product_ids)})

    # 4. Convert to API models and return
    from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import ApiProduct
    from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import ApiClient
    from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import ApiMenu
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal

    response = ApiShoppingListDataResponse(
        clients=[ApiClient.from_domain(c) for c in clients],
        menus=[ApiMenu.from_domain(m) for m in menus],
        meals=[ApiMeal.from_domain(m) for m in meals],
        products=[ApiProduct.from_domain(p) for p in products],
    ).model_dump_json()

    return create_success_response(response)
