"""Centralized Pydantic TypeAdapters for FastAPI routers."""

from pydantic import TypeAdapter

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)

ProductListTypeAdapter = TypeAdapter(list[ApiProduct])
MealListTypeAdapter = TypeAdapter(list[ApiMeal])
RecipeListTypeAdapter = TypeAdapter(list[ApiRecipe])
TagListAdapter = TypeAdapter(list[ApiTag])
ClientListTypeAdapter = TypeAdapter(list[ApiClient])
