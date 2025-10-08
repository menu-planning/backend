"""Pydantic models for shopping list data endpoint."""

from pydantic import BaseModel, Field

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import (
    ApiMenu,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)


class ApiShoppingListDataRequest(BaseModel):
    """Request model for fetching shopping list data."""

    menu_ids: list[str] = Field(..., description="List of menu IDs to fetch data for.")


class ApiShoppingListDataResponse(BaseModel):
    """Response model for aggregated shopping list data."""

    clients: list[ApiClient]
    menus: list[ApiMenu]
    meals: list[ApiMeal]
    products: list[ApiProduct]
