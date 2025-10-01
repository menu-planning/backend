"""FastAPI router for recipe search endpoint."""

from fastapi import Depends, Query
from typing import Annotated, Any
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.fastapi.dependencies import get_recipes_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.runtimes.fastapi.routers.deps import get_recipes_user
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_router,
)

router = create_router(prefix="/recipes")

RecipeListTypeAdapter = TypeAdapter(list[ApiRecipe])

@router.get("/search")
async def search_recipes(
    filters: Annotated[ApiRecipeFilter, Query()],
    current_user: Annotated[Any, Depends(get_recipes_user)],
    bus: MessageBus = Depends(get_recipes_bus),
) -> Any:
    """Search recipes with pagination and filtering.
    
    This endpoint replaces the problematic /recipes/query path to avoid conflicts
    with /recipes/{recipe_id}. Uses the same filtering approach as the Lambda implementation.
    
    Args:
        filters: Recipe filter criteria (auto-converted from query params)
        bus: Message bus for business logic
        current_user: Current authenticated user
        
    Returns:
        List of recipes matching filters
        
    Raises:
        HTTPException: If query parameters are invalid or database error occurs
    """
    filter_dict = filters.model_dump(exclude_none=True)
    
    if current_user:
        if filter_dict.get("tags"):
            filter_dict["tags"] = [
                (k, v, current_user.id) for k, vs in filter_dict["tags"].items() for v in vs
            ]
        if filter_dict.get("tags_not_exists"):
            filter_dict["tags_not_exists"] = [
                (k, v, current_user.id)
                for k, vs in filter_dict["tags_not_exists"].items()
                for v in vs
            ]
    
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        result: list = await uow.recipes.query(filters=filter_dict)
    
    api_recipes = []
    for recipe in result:
        api_recipe = ApiRecipe.from_domain(recipe)
        api_recipes.append(api_recipe)
    
    response_body = RecipeListTypeAdapter.dump_json(api_recipes)
    
    return create_success_response(response_body)
